# models_api_resources.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID
from pydantic import ConfigDict
from auth.models import AlgorithmEnum

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

class AddUserToNamespace(BaseModel):
    user_id: str
    is_admin: bool = False

class AddUserToGroup(BaseModel):
    user_id: str
    role: str 

# Модели для Приложений
class ApplicationCreate(BaseModel):
    name: str = Field(..., example="Inventory Service")
    group_id: str = Field(..., example="60c72b2f9b1d4e3a5c8e4b7b")
    algorithm: str = Field(..., example=AlgorithmEnum.aes128_gcm96)

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "name": "Inventory Service",
                "group_id": "60c72b2f9b1d4e3a5c8e4b7b"
            }
        }
    )

class ApplicationResponse(BaseModel):
    id: str
    name: str
    group_id: str
    group_ids: List[str] = []

    model_config = ConfigDict(
        orm_mode=True,
        schema_extra={
            "example": {
                "id": "60c72b2f9b1d4e3a5c8e4b7e",
                "name": "Inventory Service",
                "group_id": "60c72b2f9b1d4e3a5c8e4b7b",
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
