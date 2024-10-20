# models.py
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
import uuid
from pydantic import ConfigDict, validator



class MongoBaseModel(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        allow_population_by_field_name=True,
    )

class User(MongoBaseModel):
    name: str
    email: EmailStr
    password: str  # Хешированный пароль
    group_ids: List[ObjectId] = Field(default_factory=list)
    roles: List[dict] = Field(default_factory=list)

class Namespace(MongoBaseModel):
    name: str
    group_ids: List[ObjectId] = Field(default_factory=list)
    admin_ids: List[ObjectId] = Field(default_factory=list)

class Group(MongoBaseModel):
    name: str
    namespace_id: ObjectId
    application_ids: List[ObjectId] = Field(default_factory=list)
    admin_ids: List[ObjectId] = Field(default_factory=list)
    engineer_ids: List[ObjectId] = Field(default_factory=list)

class Application(MongoBaseModel):
    name: str
    group_id: ObjectId
    group_ids: List[ObjectId] = Field(default_factory=list)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, uuid.UUID: str},
    )
