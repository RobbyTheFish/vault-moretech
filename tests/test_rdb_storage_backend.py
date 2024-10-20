import unittest

from core.db_conn.rdb_models import Base
from core.db_conn.storage_backend import RDBStorageBackend


class TestRDBStorageBackend(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_config = {
            "db_user": "admin",
            "db_password": "superpassword",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "vaulttech",
        }
        self.backend = RDBStorageBackend(self.db_config)
        await self.backend.create_tables()

    async def asyncTearDown(self):
        async with self.backend.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.backend.engine.dispose()

    async def test_write_and_read(self):
        """
        Тест на запись и чтение
        """
        key = "test_key"
        value = b"test_value"
        application_id = 1

        await self.backend.write(key, value, application_id)
        result = await self.backend.read(key)

        self.assertEqual(result, value)

    async def test_update(self):
        """
        Тест на обновление
        """
        key = "test_key_update"
        initial_value = b"initial_value"
        updated_value = b"updated_value"
        application_id = 1

        await self.backend.write(key, initial_value, application_id)
        await self.backend.update(key, updated_value)
        result = await self.backend.read(key)

        self.assertEqual(result, updated_value)

    async def test_delete(self):
        """
        Тест на удаление
        """
        key = "test_key_delete"
        value = b"value_to_delete"
        application_id = 1

        await self.backend.write(key, value, application_id)
        await self.backend.delete(key)
        result = await self.backend.read(key)

        self.assertIsNone(result)
