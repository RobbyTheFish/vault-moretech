from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import get_current_user
from auth.models import Application, Group, UserGroupRole, RoleEnum, User
from auth.db import AsyncSessionLocal
from sqlalchemy.future import select
from sqlalchemy import insert, delete
from uuid import UUID
router = APIRouter()


@router.post("/groups/{group_uuid}/applications")
async def create_application(group_uuid: str, name: str, current_user: User = Depends(get_current_user)):
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Group).where(Group.uuid == group_uuid))
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        result = await session.execute(
            select(UserGroupRole).where(
                UserGroupRole.user_id == current_user,
                UserGroupRole.group_id == group.id,
                UserGroupRole.role.in_([RoleEnum.admin, RoleEnum.engineer])
            )
        )
        user_role = result.scalars().first()
        if not user_role:
            raise HTTPException(status_code=403, detail="Not authorized")

        new_application = Application(name=name, group_id=group.id)
        session.add(new_application)
        await session.commit()
        await session.refresh(new_application)

        return {"status": "success", "application": {"uuid": new_application.uuid, "name": new_application.name}}



@router.delete("/groups/{group_uuid}/applications/{application_id}")
async def delete_application(group_uuid: str, application_uuid: str, current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Group).where(Group.uuid == group_uuid))
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        result = await session.execute(select(Application).where(Application.uuid == application_uuid, Application.group_id == group.id))
        application = result.scalars().first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        result = await session.execute(select(Group).where(Group.uuid == group_uuid))
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        result = await session.execute(select(Application).where(Application.uuid == application_uuid, Application.group_id == group.id))
        application = result.scalars().first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        result = await session.execute(
            select(UserGroupRole).where(
                UserGroupRole.user_id == current_user,
                UserGroupRole.group_id == group.id,
                ((UserGroupRole.role == RoleEnum.admin) or (UserGroupRole.role == RoleEnum.engineer)) 
            )
        )

        # Удаляем приложение
        await session.execute(
            delete(Application).where(
                Application.id == application_id,
                Application.group_id == group.id
            )
        )
        await session.commit()

        return {"status": "success"}
