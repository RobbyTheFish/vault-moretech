from pydantic import BaseModel


class SecretRequest(BaseModel):
    secrets: dict


class SecretQuery(BaseModel):
    app_id: str
    secret_key: str
