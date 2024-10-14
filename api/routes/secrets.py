from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import get_current_user
from auth.models import Application, UserGroupRole, RoleEnum, User, Group
from api.models.secrets import SecretRequest, SecretQuery
from auth.db import AsyncSessionLocal
from sqlalchemy.future import select
from core.master.master_module import SecretManagerModule

router = APIRouter()

@router.post("/applications/{application_id}/secrets")
async def store_secrets(application_id: int, secrets: SecretRequest, current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        # Проверяем, что пользователь имеет доступ к приложению через группу
        result = await session.execute(
            select(Application, UserGroupRole).join(Group).join(UserGroupRole).where(
                Application.id == application_id,
                UserGroupRole.user_id == current_user
            )
        )
        app_data = result.first()
        if not app_data:
            raise HTTPException(status_code=403, detail="Not authorized")

        ...

        return {"status": "success"}

@router.get("/applications/{application_id}/secrets/{secret_key}")
async def retrieve_secret(application_id: int, secrets_keys: SecretQuery, current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        # Проверяем, что пользователь имеет доступ к приложению через группу
        result = await session.execute(
            select(Application, UserGroupRole).join(Group).join(UserGroupRole).where(
                Application.id == application_id,
                UserGroupRole.user_id == current_user
            )
        )
        app_data = result.first()
        if not app_data:
            raise HTTPException(status_code=403, detail="Not authorized")


        return {"status": "success", "secret": "secret_value"}
