import enum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MongoBaseModel(BaseModel):
    id: ObjectId | None = Field(alias="_id")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        allow_population_by_field_name=True,
    )

class User(MongoBaseModel):
    name: str
    email: EmailStr
    password: str  # Хешированный пароль
    group_ids: list[ObjectId] = Field(default_factory=list)

class Namespace(MongoBaseModel):
    name: str
    group_ids: list[ObjectId] = Field(default_factory=list)
    admin_ids: list[ObjectId] = Field(default_factory=list)
    user_ids: list[ObjectId] = Field(default_factory=list)

class Group(MongoBaseModel):
    name: str
    namespace_id: ObjectId
    application_ids: list[ObjectId] = Field(default_factory=list)
    admin_ids: list[ObjectId] = Field(default_factory=list)
    engineer_ids: list[ObjectId] = Field(default_factory=list)
    user_ids: list[ObjectId] = Field(default_factory=list)

class AlgorithmEnum(enum.Enum):
    aes128_gcm96 = "aes128-gcm96"
    aes256_gcm96 = "aes256-gcm96"
    chacha2 = "chacha2"
    rsa_2048 = "rsa-2048"
    rsa_3072 = "rsa-3072"
    rsa_4096 = "rsa-4096"

class Application(MongoBaseModel):
    name: str
    algorithm: str
    group_id: ObjectId
    group_ids: list[ObjectId] = Field(default_factory=list)
