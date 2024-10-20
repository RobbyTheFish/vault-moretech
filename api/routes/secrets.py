from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import get_current_user
from auth.models import Application, User, Group
from api.models.secrets import SecretRequest, SecretQuery
from sqlalchemy.future import select
from core.master.master_module import SecretManagerModule
from auth.db import db
from bson import ObjectId

router = APIRouter(
    prefix="/api",
    tags=["Secrets"],
    dependencies=[Depends(get_current_user)]
)

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
    
    application = db.applications.find_one({"_id": obj_application_id})
    if not set(application.group_ids).intersection(current_user.group_ids):
        raise HTTPException(status_code=403, detail="Access from group is permitted.")
    
    await secret_manager_module.process_request(application.id, secrets.secrets)

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
    
    application = db.applications.find_one({"_id": obj_application_id})
    if not set(application.group_ids).intersection(current_user.group_ids):
        raise HTTPException(status_code=403, detail="Access from group is permitted.")
    
    secret = await secret_manager_module.process_request(application.id, secret_key)

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
    
    application = db.applications.find_one({"_id": obj_application_id})
    if not set(application.group_ids).intersection(current_user.group_ids):
        raise HTTPException(status_code=403, detail="Access from group is permitted.")