from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from api.swagger_config import custom_openapi
from api.routes import auth, groups, applications, secrets

app = FastAPI()

# Применение кастомной OpenAPI схемы
app.openapi = lambda: custom_openapi(app)

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(groups.router, prefix="/api", tags=["groups"])
app.include_router(applications.router, prefix="/api", tags=["applications"])
app.include_router(secrets.router, prefix="/api", tags=["secrets"])