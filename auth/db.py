from motor.motor_asyncio import AsyncIOMotorClient
from auth.config import MONGO_URI, MONGO_DB_NAME
from auth.models import User, Namespace, Group, Application
from bson import ObjectId
import asyncio

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]

async def init_db():
    # Создание индексов для коллекции пользователей
    await db.users.create_index("email", unique=True)
    await db.users.create_index("name")

    # Создание индексов для коллекции неймспейсов
    await db.namespaces.create_index("name", unique=True)

    # Создание индексов для коллекции групп
    await db.groups.create_index("name")
    await db.groups.create_index("namespace_id")

    # Создание индексов для коллекции приложений
    await db.applications.create_index("name")
    await db.applications.create_index("group_id")
    
    print("Database initialized with necessary indexes.")

# Асинхронная инициализация базы данных при запуске
async def startup_db_client():
    await init_db()
