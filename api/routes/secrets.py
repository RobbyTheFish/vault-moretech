from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import get_current_user
from auth.models import Application, UserGroupRole, RoleEnum, User, Group
from api.models.secrets import SecretRequest, SecretQuery
from auth.db import AsyncSessionLocal
from sqlalchemy.future import select
from core.master.master_module import SecretManagerModule


router = APIRouter()
secret_manager_module = SecretManagerModule()


@router.post("/applications/{application_id}/secrets")
async def store_secrets(
    application_id: int,
    secrets: SecretRequest,
    current_user: User = Depends(get_current_user),
):
    async with AsyncSessionLocal() as session:
        # Проверяем, что пользователь имеет доступ к приложению через группу
        result = await session.execute(
            select(Application)
            .select_from(Group)
            .join(UserGroupRole)
            .where(
                Application.id == application_id, UserGroupRole.user_id == current_user
            )
        )
        app_data = result.first()[0]
        if not app_data:
            raise HTTPException(status_code=403, detail="Not authorized")

        await secret_manager_module.process_request(app_data.uuid, secrets.secrets)

        return {"status": "success"}


@router.get("/applications/{application_id}/secrets/{secret_key}")
async def retrieve_secret(
    application_id: int,
    secret_key: str,
    # secrets_keys: SecretQuery,
    current_user: User = Depends(get_current_user),
):
    async with AsyncSessionLocal() as session:
        # Проверяем, что пользователь имеет доступ к приложению через группу
        result = await session.execute(
            select(Application)
            .select_from(Group)
            .join(UserGroupRole)
            .where(
                Application.id == application_id, UserGroupRole.user_id == current_user
            )
        )
        app_data = result.first()[0]
        if not app_data:
            raise HTTPException(status_code=403, detail="Not authorized")

        secret = await secret_manager_module.process_request(app_data.uuid, secret_key)

    return {"status": "success", "secret": secret}
