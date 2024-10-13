from pydantic import BaseModel


class SecretRequest(BaseModel):
    app_uuid: str
    secrets: dict 


class SecretQuery(BaseModel):
    app_uuid: str
    secret_key: str
