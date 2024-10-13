from pydantic import BaseModel

class RoleCreateRequest(BaseModel):
    name: str

class RoleCreateResponse(BaseModel):
    status: str
    role: dict
    master_token: str

class TokenCreateRequest(BaseModel):
    master_token: str

class TokenResponse(BaseModel):
    status: str
    access_token: str
    refresh_token: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str