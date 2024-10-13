from fastapi import APIRouter, HTTPException, Depends, Header
from core.master.master_module import SecretManagerModule
from api.models.secrets import SecretRequest, SecretQuery
from auth.auth_manager import AuthManager

router = APIRouter()
secret_manager = SecretManagerModule()
auth_manager = AuthManager()

async def get_current_role(x_auth_token: str = Header(...)):
    role = await auth_manager.authenticate(x_auth_token)
    if not role:
        raise HTTPException(status_code=401, detail="Invalid token")
    return role

@router.post("/store")
async def store_secrets(request: SecretRequest, role = Depends(get_current_role)):
    try:
        result = await secret_manager.save_secrets(request.app_uuid, request.secrets)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve")
async def retrieve_secret(query: SecretQuery, role = Depends(get_current_role)):
    try:
        secret = await secret_manager.retrieve_secret(query.app_uuid, query.secret_key)
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        return {"status": "success", "secret": secret}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
