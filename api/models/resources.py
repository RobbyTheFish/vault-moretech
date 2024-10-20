# models_api_resources.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID
from pydantic import ConfigDict


# Модели для Неймспейсов
class NamespaceCreate(BaseModel):
    name: str = Field(..., example="Development")

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "name": "Development"
            }
        }
    )

class NamespaceResponse(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(
        orm_mode=True,
        schema_extra={
            "example": {
                "id": "60c72b2f9b1d4e3a5c8e4b7a",
                "name": "Development"
            }
        }
    )

# Модели для Групп
class GroupCreate(BaseModel):
    name: str = Field(..., example="Backend Team")
    namespace_id: str = Field(..., example="60c72b2f9b1d4e3a5c8e4b7b")

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "name": "Backend Team",
                "namespace_id": "60c72b2f9b1d4e3a5c8e4b7b"
            }
        }
    )

class GroupResponse(BaseModel):
    id: str
    name: str
    namespace_id: str

    model_config = ConfigDict(
        orm_mode=True,
        schema_extra={
            "example": {
                "id": "60c72b2f9b1d4e3a5c8e4b7c",
                "name": "Backend Team",
                "namespace_id": "60c72b2f9b1d4e3a5c8e4b7b"
            }
        }
    )

# Модели для Ролей
class RoleAssign(BaseModel):
    user_id: str = Field(..., example="60c72b2f9b1d4e3a5c8e4b7d")
    group_id: Optional[str] = Field(None, example="60c72b2f9b1d4e3a5c8e4b7c")
    namespace_id: Optional[str] = Field(None, example="60c72b2f9b1d4e3a5c8e4b7b")
    role: str = Field(..., example="admin")  # Возможные роли: admin, engineer

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "user_id": "60c72b2f9b1d4e3a5c8e4b7d",
                "group_id": "60c72b2f9b1d4e3a5c8e4b7c",
                "role": "admin"
            }
        }
    )

# Модели для Приложений
class ApplicationCreate(BaseModel):
    name: str = Field(..., example="Inventory Service")
    namespace_id: str = Field(..., example="60c72b2f9b1d4e3a5c8e4b7b")

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "name": "Inventory Service",
                "namespace_id": "60c72b2f9b1d4e3a5c8e4b7b"
            }
        }
    )

class ApplicationResponse(BaseModel):
    id: str
    uuid: UUID
    name: str
    namespace_id: str
    group_ids: List[str] = []

    model_config = ConfigDict(
        orm_mode=True,
        schema_extra={
            "example": {
                "id": "60c72b2f9b1d4e3a5c8e4b7e",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Inventory Service",
                "namespace_id": "60c72b2f9b1d4e3a5c8e4b7b",
                "group_ids": ["60c72b2f9b1d4e3a5c8e4b7c"]
            }
        }
    )

class GrantAccess(BaseModel):
    application_id: str = Field(..., example="60c72b2f9b1d4e3a5c8e4b7e")
    group_id: str = Field(..., example="60c72b2f9b1d4e3a5c8e4b7c")

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "application_id": "60c72b2f9b1d4e3a5c8e4b7e",
                "group_id": "60c72b2f9b1d4e3a5c8e4b7c"
            }
        }
    )
