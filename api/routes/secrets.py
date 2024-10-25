from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from api.models.secrets import SecretRequest
from auth.db import db
from auth.dependencies import get_current_user
from auth.models import User
from core.master.master_module import SecretManagerModule

router = APIRouter(prefix="/api", tags=["Secrets"], dependencies=[Depends(get_current_user)])

secret_manager_module = SecretManagerModule()


@router.post("/applications/{application_id}/secrets")
async def store_secrets(
    application_id: str,
    secrets: SecretRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        obj_application_id = ObjectId(application_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application ID format.")

    application = await db.applications.find_one({"_id": obj_application_id})
    application_groups = application.get("group_ids", [])
    if (
        not set(application_groups).intersection(current_user.group_ids)
        and application.get("group_id") not in current_user.group_ids
    ):
        raise HTTPException(status_code=403, detail="Access from group is not permitted.")

    await secret_manager_module.process_request(
        application.get("_id"), application.get("algorithm"), secrets.secrets
    )

    return {"status": "success"}


@router.get("/applications/{application_id}/secrets/{secret_key}")
async def retrieve_secret(
    application_id: str,
    secret_key: str,
    # secrets_keys: SecretQuery,
    current_user: User = Depends(get_current_user),
):
    try:
        obj_application_id = ObjectId(application_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application ID format.")

    application = await db.applications.find_one({"_id": obj_application_id})
    application_groups = application.get("group_ids", [])
    if (
        not set(application_groups).intersection(current_user.group_ids)
        and application.get("group_id") not in current_user.group_ids
    ):
        raise HTTPException(status_code=403, detail="Access from group is not permitted.")

    secret = await secret_manager_module.process_request(
        application.get("_id"), application.get("algorithm"), secret_key
    )

    return {"status": "success", "secret": secret}


@router.delete("/applications/{application_id}/secrets/{secret_key}")
async def delete_secret(
    application_id: str,
    secret_key: str,
    current_user: User = Depends(get_current_user),
):
    try:
        obj_application_id = ObjectId(application_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application ID format.")

    application = await db.applications.find_one({"_id": obj_application_id})
    application_groups = application.get("group_ids", [])
    if (
        not set(application_groups).intersection(current_user.group_ids)
        and application.get("group_id") not in current_user.group_ids
    ):
        raise HTTPException(status_code=403, detail="Access from group is not permitted.")
    try:
        await secret_manager_module.delete_secret(application.get("_id"), secret_key)

    except NotImplemented:
        raise HTTPException(status_code=501, detail="Failed to delete secret.")

    return {"status": "success"}
