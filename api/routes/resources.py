from fastapi import APIRouter, Depends, HTTPException, status, Body
from api.models.resources import (
    NamespaceCreate,
    NamespaceResponse,
    GroupCreate,
    GroupResponse,
    RoleAssign,
    ApplicationCreate,
    ApplicationResponse,
    GrantAccess
)
from auth.models import User, Group, Namespace, Application
from auth.db import db
from auth.dependencies import get_current_user
from bson import ObjectId
from typing import List
from pydantic import BaseModel

router = APIRouter(
    prefix="/api",
    tags=["Resources"],
    dependencies=[Depends(get_current_user)]
)

# Вспомогательные функции для проверки ролей
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
    # Проверяем, является ли пользователь админом или инженером хотя бы одной группы, имеющей доступ к приложению
    for group_id in application.group_ids:
        group = await db.groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            continue
        if ObjectId(user.id) in group.get("admin_ids", []) or ObjectId(user.id) in group.get("engineer_ids", []):
            return True
    return False



@router.post("/namespaces", response_model=NamespaceResponse, status_code=status.HTTP_201_CREATED)
async def create_namespace(namespace: NamespaceCreate, current_user: User = Depends(get_current_user)):
    existing_namespace = await db.namespaces.find_one({"name": namespace.name})
    if existing_namespace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Namespace with this name already exists."
        )
    namespace_dict = namespace.dict()
    namespace_dict["admin_ids"] = [ObjectId(current_user.id)]
    namespace_dict["group_ids"] = []
    result = await db.namespaces.insert_one(namespace_dict)
    created_namespace = await db.namespaces.find_one({"_id": result.inserted_id})
    return NamespaceResponse(
        id=str(created_namespace["_id"]),
        name=created_namespace["name"]
    )

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
    await db.groups.delete_many({"namespace_id": namespace_id})
    await db.applications.delete_many({"namespace_id": namespace_id})
    
    # Удаление неймспейса
    await db.namespaces.delete_one({"_id": obj_id})
    return

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
    
    existing_group = await db.groups.find_one({"name": group.name, "namespace_id": group.namespace_id})
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group with this name already exists in the namespace."
        )
    
    group_dict = group.dict()
    group_dict["admin_ids"] = [ObjectId(current_user.id)]
    group_dict["engineer_ids"] = []
    group_dict["application_ids"] = []
    result = await db.groups.insert_one(group_dict)
    created_group = await db.groups.find_one({"_id": result.inserted_id})
    return GroupResponse(
        id=str(created_group["_id"]),
        name=created_group["name"],
        namespace_id=str(created_group["namespace_id"])
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
    
    # Удаление ролей, связанных с группой
    await db.users.update_many(
        {"group_ids": obj_group_id},
        {"$pull": {"group_ids": obj_group_id}, "$pull": {"roles": {"group_id": group_id}}}
    )
    
    # Удаление группы
    await db.groups.delete_one({"_id": obj_group_id})
    return

# --- Роли ---

@router.post("/roles", status_code=status.HTTP_200_OK)
async def assign_role(role_assign: RoleAssign, current_user: User = Depends(get_current_user)):
    try:
        user_obj_id = ObjectId(role_assign.user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Проверка прав текущего пользователя
    if role_assign.group_id:
        if not await is_admin_of_group(current_user, role_assign.group_id):
            raise HTTPException(status_code=403, detail="Only group admins can assign roles.")
    if role_assign.namespace_id:
        if not await is_admin_of_namespace(current_user, role_assign.namespace_id):
            raise HTTPException(status_code=403, detail="Only namespace admins can assign roles.")
    
    update_query = {}
    if role_assign.group_id:
        update_query["group_id"] = ObjectId(role_assign.group_id)
    if role_assign.namespace_id:
        update_query["namespace_id"] = ObjectId(role_assign.namespace_id)
    
    # Добавление роли пользователю
    result = await db.users.update_one(
        {"_id": user_obj_id},
        {"$addToSet": {"roles": {"role": role_assign.role, **update_query}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Role assignment failed or role already assigned.")
    
    return {"detail": "Role assigned successfully."}

@router.delete("/roles", status_code=status.HTTP_200_OK)
async def remove_role(role_assign: RoleAssign, current_user: User = Depends(get_current_user)):
    try:
        user_obj_id = ObjectId(role_assign.user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Проверка прав текущего пользователя
    if role_assign.group_id:
        if not await is_admin_of_group(current_user, role_assign.group_id):
            raise HTTPException(status_code=403, detail="Only group admins can remove roles.")
    if role_assign.namespace_id:
        if not await is_admin_of_namespace(current_user, role_assign.namespace_id):
            raise HTTPException(status_code=403, detail="Only namespace admins can remove roles.")
    
    update_query = {}
    if role_assign.group_id:
        update_query["group_id"] = ObjectId(role_assign.group_id)
    if role_assign.namespace_id:
        update_query["namespace_id"] = ObjectId(role_assign.namespace_id)
    
    # Удаление роли у пользователя
    result = await db.users.update_one(
        {"_id": user_obj_id},
        {"$pull": {"roles": {"role": role_assign.role, **update_query}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Role removal failed or role not assigned.")
    
    return {"detail": "Role removed successfully."}

# --- Приложения ---

@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(application: ApplicationCreate, current_user: User = Depends(get_current_user)):
    try:
        obj_namespace_id = ObjectId(application.namespace_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid namespace ID format.")
    
    namespace = await db.namespaces.find_one({"_id": obj_namespace_id})
    if not namespace:
        raise HTTPException(status_code=404, detail="Namespace not found.")
    
    existing_app = await db.applications.find_one({"name": application.name, "namespace_id": application.namespace_id})
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application with this name already exists in the namespace."
        )
    
    application_dict = application.dict()
    application_dict["group_ids"] = []
    application_dict["group_id"] = ObjectId(current_user.id)  # Группа создателя (может быть уточнено)
    result = await db.applications.insert_one(application_dict)
    created_app = await db.applications.find_one({"_id": result.inserted_id})
    return ApplicationResponse(
        id=str(created_app["_id"]),
        uuid=created_app["uuid"],
        name=created_app["name"],
        namespace_id=str(created_app["namespace_id"]),
        group_ids=[str(gid) for gid in created_app.get("group_ids", [])]
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
    # 1. Админы и инженеры могут удалять приложения
    # 2. Только пользователь из группы создателя может удалять приложение
    creator_group_id = application.get("group_id")
    if creator_group_id:
        group = await db.groups.find_one({"_id": ObjectId(creator_group_id)})
        if group:
            if ObjectId(current_user.id) not in group.get("admin_ids", []) and ObjectId(current_user.id) not in group.get("engineer_ids", []):
                raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=400, detail="Application does not have a creator group.")
    
    # Удаление доступа к приложению из групп
    await db.applications.update_many(
        {"_id": obj_app_id},
        {"$set": {"group_ids": []}}
    )
    
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
    
    if group.namespace_id != application.namespace_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Проверка, что текущий пользователь является админом группы
    if not await is_admin_of_group(current_user, application.group_id):
        raise HTTPException(status_code=403, detail="Only group admins can grant access.")
    
    if grant_access.group_id in [str(gid) for gid in application.get("group_ids", [])]:
        raise HTTPException(status_code=400, detail="Access already granted to this group.")
    
    # Добавление группы в список групп с доступом к приложению
    await db.applications.update_one(
        {"_id": obj_app_id},
        {"$addToSet": {"group_ids": obj_group_id}}
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
    
    if grant_access.group_id not in [str(gid) for gid in application.get("group_ids", [])]:
        raise HTTPException(status_code=400, detail="Access not granted to this group.")
    

    # Проверка, что текущий пользователь является админом неймспейса
    if not await is_admin_of_group(current_user, application.namespace_id):
        raise HTTPException(status_code=403, detail="Only group admins can revoke access.")
    
    # Удаление группы из списка групп с доступом к приложению
    await db.applications.update_one(
        {"_id": obj_app_id},
        {"$pull": {"group_ids": obj_group_id}}
    )
    
    return {"detail": "Access revoked from the group successfully."}