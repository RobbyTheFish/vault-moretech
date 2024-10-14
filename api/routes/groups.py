from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import get_current_user
from auth.models import Group, UserGroupRole, RoleEnum, User
from auth.db import AsyncSessionLocal
from sqlalchemy.future import select
from sqlalchemy import insert, delete
from sqlalchemy.orm import joinedload
from uuid import UUID

router = APIRouter()

@router.post("/groups")
async def create_group(name: str, current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        # Создаем группу
        new_group = Group(name=name)
        session.add(new_group)
        await session.commit()
        await session.refresh(new_group)

        # Добавляем текущего пользователя как admin группы
        user_group_role = UserGroupRole(user_id=current_user, group_id=new_group.id, role=RoleEnum.admin)
        session.add(user_group_role)
        await session.commit()

        return {"status": "success", "group": {"uuid": new_group.uuid, "name": new_group.name}}

@router.post("/groups/{group_name}/users")
async def add_user_to_group(group_name: str, username: str, role: RoleEnum, current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        # Проверяем, что текущий пользователь является администратором группы
        result = await session.execute(select(Group)
                                       .join(UserGroupRole, Group.id == UserGroupRole.id)
                                       .join(User, User.id == UserGroupRole.user_id)
                                       .where(Group.name == group_name, User.username == username)
                                       .options(joinloaded(Group.user_group_roles)))
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")


        result = await session.execute(select(Group).where(Group.id == group.id))
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        result = await session.execute(
            select(UserGroupRole).where(
                UserGroupRole.user_id == current_user,
                UserGroupRole.group_id == group.id,
                UserGroupRole.role == RoleEnum.admin
            )
        )
        admin_role = result.scalars().first()
        if not admin_role:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Ищем пользователя по username
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Добавляем пользователя в группу
        user_group_role = UserGroupRole(user_id=user.id, group_id=group.id, role=role)
        session.add(user_group_role)
        await session.commit()

        return {"status": "success"}

@router.delete("/groups/{group_name}/users/{username}")
async def remove_user_from_group(group_name: str, username: str, current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        # Проверяем, что текущий пользователь является администратором группы
        result = await session.execute(select(Group)
                                       .join(UserGroupRole, Group.id == UserGroupRole.group_id)
                                       .where(Group.name == group_name, UserGroupRole.user_id == current_user)
                                       .options(joinloaded(Group.user_group_roles)))
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        result = await session.execute(
            select(UserGroupRole).where(
                UserGroupRole.user_id == current_user,
                UserGroupRole.group_id == group.id,
                UserGroupRole.role == RoleEnum.admin
            )
        )

        admin_role = result.scalars().first()
        if not admin_role:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await session.execute(select(UserGroupRole)
                                       .join(User, User.id == UserGroupRole.user_id)
                                       .where(User.username == username))
        # Удаляем пользователя из группы
        user_group = result.scalars().first()
        if not user_group:
            raise  HTTPException(status_code=404, detail="User not found")

        await session.execute(
            delete(UserGroupRole).where(
                UserGroupRole.user_id == user_group.user_id,
                UserGroupRole.group_id == user_group.group_id
            )
        )
        await session.commit()

        return {"status": "success"}
