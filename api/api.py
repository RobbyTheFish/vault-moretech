from fastapi import FastAPI
from api.routes.secrets import router as secrets_router
from api.routes.auth import router as auth_router

app = FastAPI()

app.include_router(secrets_router, prefix="/secrets", tags=["Secrets"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
