from fastapi import FastAPI
from api.routes.secrets import router as secrets_router

# Инициализация приложения FastAPI
app = FastAPI()

# Подключаем роутинг для работы с секретами
app.include_router(secrets_router, prefix="/secrets", tags=["Secrets"])
