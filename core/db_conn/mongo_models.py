from datetime import datetime, timedelta

from pydantic import BaseModel


class Secret_Mongo(BaseModel):
    application_id: str
    secret_key: str
    secret_value: bytes
    is_deleted: bool = False
    is_destoyed: bool = False
    version: int = 1
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    deleted_at: datetime = datetime.utcnow() + timedelta(days=10 * 365.25)
