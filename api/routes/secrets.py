from fastapi import APIRouter, HTTPException
from core.master import SecretManagerModule
from api.models.secrets import SecretRequest, SecretQuery  # Импортируем модели


router = APIRouter()

secret_manager = SecretManagerModule()

@router.post("/store")
async def store_secrets(request: SecretRequest):
    try:
        result = await secret_manager.save_secrets(request.app_uuid, request.secrets)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retrieve")
async def retrieve_secret(query: SecretQuery):
    try:
        secret = await secret_manager.retrieve_secret(query.app_uuid, query.secret_key)
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        return {"status": "success", "secret": secret}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
