from fastapi import FastAPI

from api.routes import auth, resources, secrets
from api.swagger_config import custom_openapi
from auth.db import db, startup_db_client

#, groups, applications, secrets

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await startup_db_client()

@app.on_event("shutdown")
async def on_shutdown():
    client = db.client
    client.close()
# Применение кастомной OpenAPI схемы
app.openapi = lambda: custom_openapi(app)

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(resources.router)
app.include_router(secrets.router)

