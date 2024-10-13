from fastapi import APIRouter, HTTPException
from auth.auth_manager import AuthManager
from api.models.auth import (
    RoleCreateRequest, RoleCreateResponse,
    TokenCreateRequest, TokenResponse,
    TokenRefreshRequest
)

router = APIRouter()
auth_manager = AuthManager()

@router.post("/roles", response_model=RoleCreateResponse)
async def create_role(request: RoleCreateRequest):
    try:
        role = await auth_manager.create_role(request.name)
        return {
            "status": "success",
            "role": {"id": role.id, "name": role.name},
            "master_token": role.master_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tokens", response_model=TokenResponse)
async def create_tokens(request: TokenCreateRequest):
    try:
        tokens = await auth_manager.create_tokens(request.master_token)
        return {
            "status": "success",
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/tokens/refresh", response_model=TokenResponse)
async def refresh_tokens(request: TokenRefreshRequest):
    try:
        tokens = await auth_manager.refresh_tokens(request.refresh_token)
        return {
            "status": "success",
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
