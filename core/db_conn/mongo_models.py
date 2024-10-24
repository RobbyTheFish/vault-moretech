from datetime import UTC, datetime, timedelta

from pydantic import BaseModel


class SecretVersion(BaseModel):
    secret_key: str
    secret_value: bytes
    is_deleted: bool = False
    is_destoyed: bool = False
    version: int = 1
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
    deleted_at: datetime = datetime.now(UTC) + timedelta(days=10 * 365.25)


class SecretMongo(BaseModel):
    application_id: str
    secrets: list[SecretVersion]


class AppsKeyMongo(BaseModel):
    application_id: str
    app_key: bytes
    version: int = 1
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
