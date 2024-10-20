import datetime
from abc import ABC, abstractmethod

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from core.db_conn.config import Config
from core.db_conn.mongo_models import Secret_Mongo
from core.db_conn.rdb_models import Base, Secret


class AsyncStorageBackend(ABC):
    @abstractmethod
    async def read(self, key: str, application_id: str) -> bytes:
        """Асинхронное чтение данных по ключу"""
        pass

    @abstractmethod
    async def write(self, key: str, value: bytes, application_id: str):
        """Асинхронная запись данных по ключу"""
        pass

    @abstractmethod
    async def update(self, key: str, value: bytes, application_id: str):
        """Асинхронное обновление данных по ключу"""
        pass

    @abstractmethod
    async def delete(self, key: str, application_id: str):
        """Асинхронное удаление данных по ключу"""
        pass


class RDBStorageBackend(AsyncStorageBackend):
    def __init__(self, db_config: dict[str, str | int]):
        db_url = f"postgresql+asyncpg://{db_config['db_user']}:{db_config['db_password']}@{db_config['db_host']}:{db_config['db_port']}/{db_config['db_name']}"
        self.engine = create_async_engine(db_url, echo=True)
        self.session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Проверка подключения к базе данных
        # self.check_connection()

    # async def check_connection(self):
    #     try:
    #         async with self.engine.begin() as conn:
    #             await conn.execute("SELECT 1")
    #     except SQLAlchemyError as e:
    #         raise RuntimeError(f"Ошибка подключения к базе данных: {e}")

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def read(self, key: str, application_id: str) -> bytes:
        async with self.session() as session:
            try:
                result = await session.execute(
                    select(Secret).filter(
                        Secret.secret_key == key,
                        Secret.is_deleted.is_(False),
                        Secret.application_id == application_id,
                    )
                )
                secret = result.scalars().first()
                return secret.secret_value if secret else None
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка чтения данных: {e}")

    async def write(self, key: str, value: bytes, application_id: str):
        async with self.session() as session:
            try:
                new_secret = Secret(
                    secret_key=key, secret_value=value, application_id=application_id
                )
                session.add(new_secret)
                await session.commit()
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка записи данных: {e}")

    async def update(self, key: str, value: bytes, application_id: str):
        async with self.session() as session:
            try:
                stmt = (
                    update(Secret)
                    .where(
                        Secret.secret_key == key,
                        Secret.application_id == application_id,
                    )
                    .values(
                        secret_value=value,
                        updated_at=datetime.datetime.utcnow(),
                        version=Secret.version + 1,
                    )
                )
                result = await session.execute(stmt)
                await session.commit()

                if result.rowcount == 0:
                    raise ValueError(f"Секрет с ключом '{key}' не найден.")
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка обновления данных: {e}")

    async def delete(self, key: str, application_id: str):
        async with self.session() as session:
            try:
                stmt = (
                    update(Secret)
                    .where(
                        Secret.secret_key == key,
                        Secret.application_id == application_id,
                    )
                    .values(is_deleted=True, deleted_at=datetime.datetime.utcnow())
                )
                result = await session.execute(stmt)
                await session.commit()

                if result.rowcount == 0:
                    raise ValueError(f"Секрет с ключом '{key}' не найден.")
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка удаления данных: {e}")


class MongoDBStorageBackend(AsyncStorageBackend):
    def __init__(self, db_config: dict[str, str | int]):
        try:
            self.client = AsyncIOMotorClient(
                host=db_config["db_host"],
                port=db_config["db_port"],
                username=db_config["db_user"],
                password=db_config["db_password"],
                authSource=db_config["db_user"],
            )
            self.db = self.client[db_config["db_name"]]
            self.collection = self.db["secrets"]
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка подключения к MongoDB: {e}")

    async def read(self, key: str, application_id: str) -> bytes:
        try:
            secret = await self.collection.find_one(
                {
                    "secret_key": key,
                    "is_deleted": False,
                    "application_id": application_id,
                }
            )
            return secret["secret_value"] if secret else None
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка чтения из MongoDB: {e}")

    async def write(self, key: str, value: bytes, application_id: str):
        try:
            new_secret = Secret_Mongo(
                application_id=application_id, secret_key=key, secret_value=value
            )
            await self.collection.insert_one(new_secret.model_dump())
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка записи в MongoDB: {e}")

    async def update(self, key: str, value: bytes):
        try:
            result = await self.collection.update_one(
                {"secret_key": key, "is_deleted": False},
                {
                    "$set": {
                        "secret_value": value,
                        "updated_at": datetime.datetime.utcnow(),
                        "version": {"$add": ["$version", 1]},
                    }
                },
            )
            if result.matched_count == 0:
                raise ValueError(f"Секрет с ключом '{key}' не найден или удален.")
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка обновления в MongoDB: {e}")

    async def delete(self, key: str, application_id: str):
        try:
            result = await self.collection.update_one(
                {
                    "secret_key": key,
                    "is_deleted": False,
                    "application_id": application_id,
                },
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.datetime.utcnow(),
                    }
                },
            )
            if result.matched_count == 0:
                raise ValueError(f"Секрет с ключом '{key}' не найден или уже удален.")
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка удаления в MongoDB: {e}")


class SecretStorage:
    @staticmethod
    async def create_storage(storage_type: str, /) -> AsyncStorageBackend:
        config = Config().model_dump()
        if storage_type == "relational":
            storage = RDBStorageBackend(config)
            await storage.create_tables()
        elif storage_type == "mongo":
            storage = MongoDBStorageBackend(config)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

        return storage
