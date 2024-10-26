from abc import ABC, abstractmethod
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from core.db_conn.config import config
from core.db_conn.mongo_models import AppsKeyMongo, SecretVersion
from core.db_conn.rdb_models import Base, Secret


class AsyncStorageBackend(ABC):
    """Abstract base class for asynchronous storage backends."""

    @abstractmethod
    async def read_data(self, application_id: str, key: str) -> bytes:
        """Asynchronously read data by key.

        Parameters
        ----------
        application_id : str
            The ID of the application.
        key : str
            The key for the data to be read.

        Returns
        -------
        bytes
            The data associated with the specified key.
        """
        pass

    @abstractmethod
    async def write_data(self, application_id: str, key: str, value: bytes) -> dict[str, str]:
        """Asynchronously write data by key.

        Parameters
        ----------
        application_id : str
            The ID of the application.
        key : str
            The key for the data to be written.
        value : bytes
            The data to be written.

        Returns
        -------
        dict[str, str]
            A dictionary containing the status of the write operation.
        """
        pass

    @abstractmethod
    async def update_data(self, application_id: str, key: str, value: bytes) -> dict[str, str]:
        """Asynchronously update data by key.

        Parameters
        ----------
        application_id : str
            The ID of the application.
        key : str
            The key for the data to be updated.
        value : bytes
            The new data to be stored.

        Returns
        -------
        dict[str, str]
            A dictionary containing the status of the update operation.
        """
        pass

    @abstractmethod
    async def delete_data(self, application_id: str, key: str) -> dict[str, str]:
        """Asynchronously delete data by key.

        Parameters
        ----------
        application_id : str
            The ID of the application.
        key : str
            The key for the data to be deleted.

        Returns
        -------
        dict[str, str]
            A dictionary containing the status of the delete operation.
        """
        pass

    @abstractmethod
    async def _read_key_app(self, application_id: str) -> bytes:
        """Asynchronously read the application key.

        Parameters
        ----------
        application_id : str
            The ID of the application.

        Returns
        -------
        bytes
            The application key associated with the specified application ID.
        """
        pass

    @abstractmethod
    async def _write_key_app(self, application_id: str, app_key: bytes) -> dict[str, str]:
        """Asynchronously write the application key.

        Parameters
        ----------
        application_id : str
            The ID of the application.
        app_key : bytes
            The application key to be stored.

        Returns
        -------
        dict[str, str]
            A dictionary containing the status of the write operation.
        """
        pass

    @abstractmethod
    async def _update_key_app(self, application_id: str, app_key: bytes) -> dict[str, str]:
        """Asynchronously update the application key.

        Parameters
        ----------
        application_id : str
            The ID of the application.
        app_key : bytes
            The new application key to be stored.

        Returns
        -------
        dict[str, str]
            A dictionary containing the status of the update operation.
        """
        pass

    @abstractmethod
    async def _delete_key_app(self, application_id: str) -> dict[str, str]:
        """Asynchronously delete the application key.

        Parameters
        ----------
        application_id : str
            The ID of the application.

        Returns
        -------
        dict[str, str]
            A dictionary containing the status of the delete operation.
        """
        pass


class RDBStorageBackend(AsyncStorageBackend):
    def __init__(self):
        self.engine = create_async_engine(config.secret_db_uri, echo=True)
        self.session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def read_data(self, application_id: str, key: str) -> bytes:
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

    async def write_data(self, application_id: str, key: str, value: bytes):
        async with self.session() as session:
            try:
                new_secret = Secret(
                    secret_key=key, secret_value=value, application_id=application_id
                )
                session.add(new_secret)
                await session.commit()
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка записи данных: {e}")

    async def update_data(self, application_id: str, key: str, value: bytes):
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
                        updated_at=datetime.datetime.now(UTC),
                        version=Secret.version + 1,
                    )
                )
                result = await session.execute(stmt)
                await session.commit()

                if result.rowcount == 0:
                    raise ValueError(f"Секрет с ключом '{key}' не найден.")
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка обновления данных: {e}")

    async def delete_data(self, application_id: str, key: str):
        async with self.session() as session:
            try:
                stmt = (
                    update(Secret)
                    .where(
                        Secret.secret_key == key,
                        Secret.application_id == application_id,
                    )
                    .values(is_deleted=True, deleted_at=datetime.datetime.now(UTC))
                )
                result = await session.execute(stmt)
                await session.commit()

                if result.rowcount == 0:
                    raise ValueError(f"Секрет с ключом '{key}' не найден.")
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка удаления данных: {e}")

    async def _read_key_app(self, application_id: str) -> bytes:
        """Асинхронное чтение ключа приложения"""
        pass

    async def _write_key_app(self, application_id: str, app_key: bytes):
        """Асинхронная запись ключа приложения"""
        pass

    async def _update_key_app(self, application_id: str, app_key: bytes):
        """Асинхронное обновление ключа приложения"""
        pass

    async def _delete_key_app(self, application_id: str):
        """Асинхронное удаление ключа приложения"""
        pass


class MongoDBStorageBackend(AsyncStorageBackend):
    def __init__(self):
        try:
            self.client = AsyncIOMotorClient(config.secret_db_uri)
            self.db = self.client[config.secret_db_name]
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка подключения к MongoDB: {e}")

    async def read_data(self, application_id: str, key: str) -> bytes | None:
        try:
            # Ищем последнюю версию секрета, которая не удалена
            secret = await self.db.secrets.find_one(
                {
                    "application_id": application_id,
                    "secret_key": key,
                    "is_deleted": False,
                },
                sort=[("version", -1)],  # Сортировка по убыванию версии
            )
            if secret:
                return secret["secret_value"]
            return None
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка чтения из MongoDB: {e}")

    async def write_data(self, application_id: str, key: str, value: bytes) -> None:
        try:
            # Проверяем, существует ли уже секрет с данным ключом
            existing_secret = await self.db.secrets.find_one(
                {"application_id": application_id, "secret_key": key}
            )
            if existing_secret:
                raise ValueError(f"Секрет с ключом '{key}' уже существует.")

            # Создаем новую запись с версией 1
            new_secret = SecretVersion(
                application_id=application_id,
                secret_key=key,
                secret_value=value,
                version=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Вставляем новую запись в коллекцию
            await self.db.secrets.insert_one(new_secret.dict())
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка записи в MongoDB: {e}")

    async def update_data(self, application_id: str, key: str, value: bytes) -> None:
        try:
            # Помечаем текущую версию как удаленную
            await self.db.secrets.update_one(
                {
                    "application_id": application_id,
                    "secret_key": key,
                    "is_deleted": False,
                },
                {"$set": {"is_deleted": True}},
            )

            # Находим последнюю версию секрета
            last_version = await self.db.secrets.find_one(
                {
                    "application_id": application_id,
                    "secret_key": key,
                },
                sort=[("version", -1)],  # Сортировка по убыванию версии
            )

            # Добавляем новую версию
            new_version = last_version["version"] + 1 if last_version else 1
            new_secret = SecretVersion(
                application_id=application_id,
                secret_key=key,
                secret_value=value,
                version=new_version,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            await self.db.secrets.insert_one(new_secret.dict())
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка обновления в MongoDB: {e}")

    async def delete_data(self, application_id: str, key: str) -> None:
        try:
            # Находим последнюю версию секрета, которая не помечена как удаленная
            result = await self.db.secrets.update_one(
                {
                    "application_id": application_id,
                    "secret_key": key,
                    "is_deleted": False,
                },
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.now(UTC),
                    }
                },
            )
            if result.matched_count == 0:
                raise ValueError(f"Секрет с ключом '{key}' не найден или уже удален.")
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка удаления в MongoDB: {e}")

    async def _read_key_app(self, application_id: str) -> bytes | None:
        try:
            app_key_record = await self.db.apps_keys.find_one({"application_id": application_id})
            return app_key_record["app_key"] if app_key_record else None
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка чтения ключа приложения из MongoDB: {e}")

    async def _write_key_app(self, application_id: str, app_key: bytes):
        try:
            new_app_key = AppsKeyMongo(
                application_id=application_id,
                app_key=app_key,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            await self.db.apps_keys.insert_one(new_app_key.model_dump())
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка записи ключа приложения в MongoDB: {e}")

    async def _update_key_app(self, application_id: str, app_key: bytes):
        try:
            result = await self.db.apps_keys.update_one(
                {"application_id": application_id},
                {
                    "$set": {
                        "app_key": app_key,
                        "updated_at": datetime.now(UTC),
                    },
                    "$inc": {"version": 1},
                },
            )
            if result.matched_count == 0:
                raise ValueError(f"Ключ приложения для '{application_id}' не найден.")
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка обновления ключа приложения в MongoDB: {e}")

    async def _delete_key_app(self, application_id: str):
        try:
            result = await self.db.apps_keys.delete_one({"application_id": application_id})
            if result.deleted_count == 0:
                raise ValueError(f"Ключ приложения для '{application_id}' не найден.")
        except PyMongoError as e:
            raise RuntimeError(f"Ошибка удаления ключа приложения из MongoDB: {e}")


class SecretStorage:
    def __init__(self):
        _type_db = {"rbdstorage": RDBStorageBackend, "mongodb": MongoDBStorageBackend}
        self.db_conn = _type_db[config.secret_db_type]()

    async def read_data(self, application_id: str, key: str) -> bytes | None:
        return await self.db_conn.read_data(application_id, key)

    async def write_data(self, application_id: str, key: str, value: bytes) -> dict[str, str]:
        await self.db_conn.write_data(application_id, key, value)
        return {"status": "success"}

    async def update_data(self, application_id: str, key: str, value: bytes) -> dict[str, str]:
        await self.db_conn.update_data(application_id, key, value)
        return {"status": "success"}

    async def delete_data(self, application_id: str, key: str) -> dict[str, str]:
        await self.db_conn.delete_data(application_id, key)
        return {"status": "success"}

    async def _read_key_app(self, application_id: str) -> bytes | None:
        return await self.db_conn._read_key_app(application_id)

    async def _write_key_app(self, application_id: str, app_key: bytes) -> None:
        await self.db_conn._write_key_app(application_id, app_key)

    async def _update_key_app(self, application_id: str, app_key: bytes) -> None:
        await self.db_conn._update_key_app(application_id, app_key)

    async def _delete_key_app(self, application_id: str) -> None:
        await self.db_conn._delete_key_app(application_id)

    @staticmethod
    async def create_storage(storage_type: str, /) -> AsyncStorageBackend:
        if storage_type == "relational":
            storage = RDBStorageBackend()
            await storage.create_tables()
        elif storage_type == "mongo":
            storage = MongoDBStorageBackend()
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

        return storage
