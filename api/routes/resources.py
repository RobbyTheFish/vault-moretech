from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, status

from api.models.resources import (
    AddUserToGroup,
    AddUserToNamespace,
    ApplicationCreate,
    ApplicationResponse,
    GrantAccess,
    GroupCreate,
    GroupResponse,
    NamespaceCreate,
    NamespaceResponse,
)
from auth.db import db
from auth.dependencies import get_current_user
from auth.models import AlgorithmEnum, Application, User

router = APIRouter(prefix="/api", tags=["Resources"], dependencies=[Depends(get_current_user)])


# Вспомогательные функции для проверки прав
async def is_admin_of_namespace(user: User, namespace_id: str) -> bool:
    namespace = await db.namespaces.find_one({"_id": ObjectId(namespace_id)})
    if not namespace:
        return False
    return ObjectId(user.id) in namespace.get("admin_ids", [])


async def is_admin_of_group(user: User, group_id: str) -> bool:
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        return False
    return ObjectId(user.id) in group.get("admin_ids", [])


async def is_engineer_of_group(user: User, group_id: str) -> bool:
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        return False
    return ObjectId(user.id) in group.get("engineer_ids", [])


async def is_admin_or_engineer_of_application(user: User, application: Application) -> bool:
    # Проверяем, является ли пользователь админом или инженером хотя бы одной группы,
    # имеющей доступ к приложению
    for group_id in application.group_ids:
        group = await db.groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            continue
        if ObjectId(user.id) in group.get("admin_ids", []) or ObjectId(user.id) in group.get(
            "engineer_ids", []
        ):
            return True
    return False


# --- Неймспейсы ---


@router.post("/namespaces", response_model=NamespaceResponse, status_code=status.HTTP_201_CREATED)
async def create_namespace(
    namespace: NamespaceCreate, current_user: User = Depends(get_current_user)
):
    existing_namespace = await db.namespaces.find_one({"name": namespace.name})
    if existing_namespace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Namespace with this name already exists.",
        )
    namespace_dict = namespace.model_dump()
    namespace_dict["admin_ids"] = [ObjectId(current_user.id)]
    namespace_dict["group_ids"] = []
    namespace_dict["user_ids"] = []
    result = await db.namespaces.insert_one(namespace_dict)
    created_namespace = await db.namespaces.find_one({"_id": result.inserted_id})
    return NamespaceResponse(id=str(created_namespace["_id"]), name=created_namespace["name"])


@router.delete("/namespaces/{namespace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_namespace(namespace_id: str, current_user: User = Depends(get_current_user)):
    try:
        obj_id = ObjectId(namespace_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid namespace ID format.")

    namespace = await db.namespaces.find_one({"_id": obj_id})
    if not namespace:
        raise HTTPException(status_code=404, detail="Namespace not found.")

    if not await is_admin_of_namespace(current_user, namespace_id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Удаление связанных групп и приложений
    groups_cursor = db.groups.find({"namespace_id": namespace_id})
    async for group in groups_cursor:
        # Удаление группы из пользователей
        await db.users.update_many(
            {"group_ids": group["_id"]}, {"$pull": {"group_ids": group["_id"]}}
        )
        # Удаление группы
        await db.groups.delete_one({"_id": group["_id"]})

    # Удаление приложений, связанных с неймспейсом
    await db.applications.delete_many({"namespace_id": namespace_id})

    # Удаление неймспейса
    await db.namespaces.delete_one({"_id": obj_id})
    return


@router.post("/namespaces/{namespace_id}/add_user", status_code=status.HTTP_200_OK)
async def add_user_to_namespace(
    namespace_id: str, add_user: AddUserToNamespace, current_user: User = Depends(get_current_user)
):
    try:
        obj_namespace_id = ObjectId(namespace_id)
        obj_user_id = ObjectId(add_user.user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid namespace ID or user ID format.")

    namespace = await db.namespaces.find_one({"_id": obj_namespace_id})
    if not namespace:
        raise HTTPException(status_code=404, detail="Namespace not found.")

    if not await is_admin_of_namespace(current_user, namespace_id):
        raise HTTPException(status_code=403, detail="Only namespace admins can add users.")

    # Проверка существования пользователя
    user = await db.users.find_one({"_id": obj_user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    update_query = {}
    if add_user.is_admin:
        update_query = {"$addToSet": {"admin_ids": obj_user_id}}
    else:
        update_query = {"$addToSet": {"user_ids": obj_user_id}}

    result = await db.namespaces.update_one({"_id": obj_namespace_id}, update_query)

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="User already added to the namespace.")

    return {"detail": "User added to the namespace successfully."}


@router.post("/namespaces/{namespace_id}/remove_user", status_code=status.HTTP_200_OK)
async def remove_user_from_namespace(
    namespace_id: str, user_id: str = Body(...), current_user: User = Depends(get_current_user)
):
    try:
        obj_namespace_id = ObjectId(namespace_id)
        obj_user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid namespace ID or user ID format.")

    namespace = await db.namespaces.find_one({"_id": obj_namespace_id})
    if not namespace:
        raise HTTPException(status_code=404, detail="Namespace not found.")

    if not await is_admin_of_namespace(current_user, namespace_id):
        raise HTTPException(status_code=403, detail="Only namespace admins can remove users.")

    # Удаление пользователя из админов и обычных пользователей
    result = await db.namespaces.update_one(
        {"_id": obj_namespace_id}, {"$pull": {"admin_ids": obj_user_id, "user_ids": obj_user_id}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="User not found in the namespace.")

    return {"detail": "User removed from the namespace successfully."}


# --- Группы ---


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(group: GroupCreate, current_user: User = Depends(get_current_user)):
    try:
        obj_namespace_id = ObjectId(group.namespace_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid namespace ID format.")

    namespace = await db.namespaces.find_one({"_id": obj_namespace_id})
    if not namespace:
        raise HTTPException(status_code=404, detail="Namespace not found.")

    existing_group = await db.groups.find_one(
        {"name": group.name, "namespace_id": obj_namespace_id}
    )
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group with this name already exists in the namespace.",
        )

    namespace_admin_ids = namespace.get("admin_ids", [])
    group_dict = group.model_dump()
    group_dict["admin_ids"] = list(set([ObjectId(current_user.id)] + namespace_admin_ids))
    group_dict["engineer_ids"] = []
    group_dict["user_ids"] = []
    group_dict["application_ids"] = []
    result = await db.groups.insert_one(group_dict)
    created_group = await db.groups.find_one({"_id": result.inserted_id})

    await db.users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"group_ids": created_group.get("_id")}}
    )

    return GroupResponse(
        id=str(created_group["_id"]),
        name=created_group["name"],
        namespace_id=str(created_group["namespace_id"]),
    )


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, current_user: User = Depends(get_current_user)):
    try:
        obj_group_id = ObjectId(group_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid group ID format.")

    group = await db.groups.find_one({"_id": obj_group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if not await is_admin_of_group(current_user, group_id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Удаление пользователей из группы
    await db.users.update_many({"group_ids": obj_group_id}, {"$pull": {"group_ids": obj_group_id}})

    # Удаление группы
    await db.groups.delete_one({"_id": obj_group_id})
    return


@router.post("/groups/{group_id}/add_user", status_code=status.HTTP_200_OK)
async def add_user_to_group(
    group_id: str, add_user: AddUserToGroup, current_user: User = Depends(get_current_user)
):
    try:
        obj_group_id = ObjectId(group_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid group ID format.")

    group = await db.groups.find_one({"_id": obj_group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if not await is_admin_of_group(current_user, group_id):
        raise HTTPException(status_code=403, detail="Only group admins can add users.")

    # Проверка существования пользователя
    user = await db.users.find_one({"email": add_user.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Добавление пользователя в группу с указанной ролью
    obj_user_id = ObjectId(user.get("_id"))
    if add_user.role == "admin":
        update_query = {"$addToSet": {"admin_ids": obj_user_id}}
    elif add_user.role == "engineer":
        update_query = {"$addToSet": {"engineer_ids": obj_user_id}}
    elif add_user.role == "user":
        update_query = {"$addToSet": {"user_ids": obj_user_id}}
    else:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    result = await db.groups.update_one({"_id": obj_group_id}, update_query)

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="User already has this role in the group.")

    # Добавление группы в список групп пользователя, если ещё не добавлена
    await db.users.update_one({"_id": obj_user_id}, {"$addToSet": {"group_ids": obj_group_id}})

    return {"detail": "User added to the group successfully."}


@router.post("/groups/{group_id}/remove_user", status_code=status.HTTP_200_OK)
async def remove_user_from_group(
    group_id: str, email: str = Body(...), current_user: User = Depends(get_current_user)
):
    user = db.users.find_one({"email": email})
    try:
        obj_group_id = ObjectId(group_id)
        obj_user_id = ObjectId(user.get("_id"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid group ID or user ID format.")

    group = await db.groups.find_one({"_id": obj_group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if not await is_admin_of_group(current_user, group_id):
        raise HTTPException(status_code=403, detail="Only group admins can remove users.")

    # Удаление пользователя из всех ролей группы
    result = await db.groups.update_one(
        {"_id": obj_group_id},
        {
            "$pull": {
                "admin_ids": obj_user_id,
                "engineer_ids": obj_user_id,
                "user_ids": obj_user_id,
            }
        },
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="User not found in the group.")

    # Удаление группы из списка групп пользователя
    await db.users.update_one({"_id": obj_user_id}, {"$pull": {"group_ids": obj_group_id}})

    return {"detail": "User removed from the group successfully."}


@router.get("/groups/{group_id}/get_users_list", status_code=status.HTTP_200_OK)
async def get_users_list(group_id: str, current_user: User = Depends(get_current_user)):
    try:
        obj_group_id = ObjectId(group_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid group ID format.")

    group = await db.groups.find_one({"_id": obj_group_id})

    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if group.get("_id") not in current_user.group_ids:
        raise HTTPException(status_code=400, detail="User not found in the group.")
    users_list = [str(user_id) for user_id in group.get("user_ids", [])]
    engineer_list = [str(engineer_id) for engineer_id in group.get("engineer_ids", [])]
    admin_list = [str(admin_id) for admin_id in group.get("admin_ids", [])]
    return {
        "status": "success",
        "users_list": users_list,
        "engineer_ids": engineer_list,
        "admin_ids": admin_list,
    }


@router.get("/groups/{group_id}/get_applications_list", status_code=status.HTTP_200_OK)
async def get_applications_list(group_id: str, current_user: User = Depends(get_current_user)):
    try:
        obj_group_id = ObjectId(group_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid group ID format.")

    group = await db.groups.find_one({"_id": obj_group_id})

    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")
    if group.get("_id") not in current_user.group_ids:
        raise HTTPException(status_code=400, detail="User not found in the group.")
    applications_list = [
        str(application_id) for application_id in group.get("application_ids", [])
    ]
    return {"status": "success", "users_list": applications_list}


# --- Приложения ---


@router.post(
    "/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def create_application(
    application: ApplicationCreate, current_user: User = Depends(get_current_user)
):
    try:
        obj_group_id = ObjectId(application.group_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid group ID format.")

    group = await db.groups.find_one({"_id": obj_group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if group.get("_id") not in current_user.group_ids:
        raise HTTPException(status_code=400, detail="User not found in the group.")

    existing_app = await db.applications.find_one(
        {"name": application.name, "group_id": obj_group_id}
    )
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application with this name already exists in the group.",
        )

    application_dict = application.model_dump()
    if application_dict["algorithm"] not in [e.value for e in AlgorithmEnum]:
        application_dict["algorithm"] = AlgorithmEnum.aes128_gcm96.value
    application_dict["group_ids"] = []
    application_dict["group_id"] = obj_group_id  # Группа создателя
    application_dict["namespace_id"] = group["namespace_id"]  # Добавление namespace_id из группы
    result = await db.applications.insert_one(application_dict)
    created_app = await db.applications.find_one({"_id": result.inserted_id})
    return ApplicationResponse(
        id=str(created_app["_id"]),
        name=created_app["name"],
        group_id=str(created_app["group_id"]),
        group_ids=[str(gid) for gid in created_app.get("group_ids", [])],
    )


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: str, current_user: User = Depends(get_current_user)):
    try:
        obj_app_id = ObjectId(application_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application ID format.")

    application = await db.applications.find_one({"_id": obj_app_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Проверка прав:
    # 1. Администратор или инженер группы могут удалять приложение
    creator_group_id = application.get("group_id")
    if creator_group_id:
        group = await db.groups.find_one({"_id": creator_group_id})
        if group:
            if ObjectId(current_user.id) not in group.get("admin_ids", []) and ObjectId(
                current_user.id
            ) not in group.get("engineer_ids", []):
                raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=400, detail="Application does not have a creator group.")

    # Удаление доступа к приложению из групп
    await db.applications.update_one({"_id": obj_app_id}, {"$set": {"group_ids": []}})

    # Удаление приложения
    await db.applications.delete_one({"_id": obj_app_id})
    return


@router.post("/applications/grant_access", status_code=status.HTTP_200_OK)
async def grant_access(grant_access: GrantAccess, current_user: User = Depends(get_current_user)):
    try:
        obj_app_id = ObjectId(grant_access.application_id)
        obj_group_id = ObjectId(grant_access.group_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application or group ID format.")

    application = await db.applications.find_one({"_id": obj_app_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    group = await db.groups.find_one({"_id": obj_group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if group["namespace_id"] != application["namespace_id"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Проверка, что текущий пользователь является админом группы
    if not await is_admin_of_group(current_user, grant_access.group_id):
        raise HTTPException(status_code=403, detail="Only group admins can grant access.")

    if obj_group_id in application.get("group_ids", []):
        raise HTTPException(status_code=400, detail="Access already granted to this group.")

    # Добавление группы в список групп с доступом к приложению
    await db.applications.update_one(
        {"_id": obj_app_id}, {"$addToSet": {"group_ids": obj_group_id}}
    )

    return {"detail": "Access granted to the group successfully."}


@router.post("/applications/revoke_access", status_code=status.HTTP_200_OK)
async def revoke_access(grant_access: GrantAccess, current_user: User = Depends(get_current_user)):
    try:
        obj_app_id = ObjectId(grant_access.application_id)
        obj_group_id = ObjectId(grant_access.group_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application or group ID format.")

    application = await db.applications.find_one({"_id": obj_app_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if obj_group_id not in application.get("group_ids", []):
        raise HTTPException(status_code=400, detail="Access not granted to this group.")

    # Проверка, что текущий пользователь является администратором группы
    group = await db.groups.find_one({"_id": obj_group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if not await is_admin_of_group(current_user, grant_access.group_id):
        raise HTTPException(status_code=403, detail="Only group admins can revoke access.")

    # Удаление группы из списка групп с доступом к приложению
    await db.applications.update_one({"_id": obj_app_id}, {"$pull": {"group_ids": obj_group_id}})

    return {"detail": "Access revoked from the group successfully."}
