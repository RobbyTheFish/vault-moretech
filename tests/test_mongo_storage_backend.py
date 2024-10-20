import unittest
from core.db_conn.storage_backend import MongoDBStorageBackend


class TestMongoDBStorageBackend(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_config = {
            "db_user": "admin",
            "db_password": "secret",
            "db_host": "localhost",
            "db_port": 27017,
            "db_name": "vaulttech",
        }
        self.backend = MongoDBStorageBackend(self.db_config)

    async def asyncTearDown(self):
        await self.backend.collection.delete_many({})

    async def test_write_and_read(self):
        """
        Тест на запись и чтение
        """
        key = "test_key"
        value = b"test_value"
        application_id = 1

        await self.backend.write(key, value, application_id)
        result = await self.backend.read(key, application_id)

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
        result = await self.backend.read(key, application_id)

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
        result = await self.backend.read(key, application_id)

        self.assertIsNone(result)
