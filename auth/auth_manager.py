from auth.models import Role, Token
from auth.db import AsyncSessionLocal
from sqlalchemy.future import select
from auth.token_utils import create_access_token, create_refresh_token, decode_token
from datetime import datetime, timedelta
from sqlalchemy import delete

class AuthManager:
    def __init__(self):
        pass

    async def create_role(self, name: str):
        """
        Создает новую роль и выдает мастер-токен без срока действия.
        """
        async with AsyncSessionLocal() as session:
            new_role = Role(name=name)
            session.add(new_role)
            await session.commit()
            await session.refresh(new_role)
            return new_role

    async def get_role_by_master_token(self, master_token: str):
        """
        Получает роль по мастер-токену.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Role).where(Role.master_token == master_token))
            role = result.scalars().first()
            return role

    async def create_tokens(self, master_token: str):
        """
        Создает активный токен и токен обновления для роли, используя мастер-токен.
        """
        role = await self.get_role_by_master_token(master_token)
        if not role:
            raise Exception("Invalid master token")

        access_token_expires = datetime.utcnow() + timedelta(minutes=15)
        refresh_token_expires = datetime.utcnow() + timedelta(days=7)

        access_token = create_access_token(data={"role_id": role.id}, expires_delta=timedelta(minutes=15))
        refresh_token = create_refresh_token(data={"role_id": role.id}, expires_delta=timedelta(days=7))

        async with AsyncSessionLocal() as session:
            # Удаляем предыдущие токены для этой роли
            await session.execute(delete(Token).where(Token.role_id == role.id))
            await session.commit()

            new_token = Token(
                role_id=role.id,
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expires_at=access_token_expires,
                refresh_token_expires_at=refresh_token_expires,
            )
            session.add(new_token)
            await session.commit()
            await session.refresh(new_token)
            return new_token

    async def refresh_tokens(self, refresh_token: str):
        """
        Обновляет активный токен и токен обновления, используя существующий токен обновления.
        """
        payload = decode_token(refresh_token)
        if not payload:
            raise Exception("Invalid refresh token")

        role_id = payload.get("role_id")
        if not role_id:
            raise Exception("Invalid refresh token")

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Token).where(Token.refresh_token == refresh_token))
            token_entry = result.scalars().first()

            if not token_entry or token_entry.refresh_token_expires_at < datetime.utcnow():
                raise Exception("Refresh token expired or invalid")

            access_token_expires = datetime.utcnow() + timedelta(minutes=15)
            refresh_token_expires = datetime.utcnow() + timedelta(days=7)

            access_token = create_access_token(data={"role_id": role_id}, expires_delta=timedelta(minutes=15))
            refresh_token = create_refresh_token(data={"role_id": role_id}, expires_delta=timedelta(days=7))

            # Обновляем токены в базе данных
            token_entry.access_token = access_token
            token_entry.refresh_token = refresh_token
            token_entry.access_token_expires_at = access_token_expires
            token_entry.refresh_token_expires_at = refresh_token_expires

            await session.commit()
            await session.refresh(token_entry)
            return token_entry

    async def authenticate(self, access_token: str):
        """
        Аутентифицирует пользователя по активному токену.
        """
        payload = decode_token(access_token)
        if not payload:
            return None

        role_id = payload.get("role_id")
        if not role_id:
            return None

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Token).where(Token.access_token == access_token))
            token_entry = result.scalars().first()

            if not token_entry or token_entry.access_token_expires_at < datetime.utcnow():
                return None

            result = await session.execute(select(Role).where(Role.id == role_id))
            role = result.scalars().first()
            return role
