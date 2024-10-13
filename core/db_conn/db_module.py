import motor.motor_asyncio
from pymongo import IndexModel, ASCENDING
from pymongo.errors import DuplicateKeyError
import asyncio

from config import Config

class DatabaseModule:
    def __init__(self):
        """
        Init connect with MongoDB

        :param uri: Connection string
        :param db_name: DB name
        """
        mongo_uri = Config.MONGO_URI

        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client.get_default_database()
        self.collection = self.db['secrets']

        asyncio.create_task(self.create_indexes())

    async def create_indexes(self):
        """
        Create indexes in DB
        """
        index = IndexModel(
            [('app_uuid', ASCENDING), ('data_key', ASCENDING)],
            unique=True
        )
        await self.collection.create_indexes([index])

    async def save_data(self, app_uuid, data_key, encrypted_data):
        """
        Save data

        :param app_uuid: UUID app.
        :param data_key: Data key.
        :param encrypted_data: Encrypted data.
        """
        document = {
            'app_uuid': app_uuid,
            'data_key': data_key,
            'encrypted_data': encrypted_data
        }
        try:
            await self.collection.insert_one(document)
        except DuplicateKeyError:
            await self.collection.update_one(
                {'app_uuid': app_uuid, 'data_key': data_key},
                {'$set': {'encrypted_data': encrypted_data}}
            )

    async def get_data(self, app_uuid, data_key):
        """
        Get data with app_uuid and data_key

        :param app_uuid: UUID app.
        :param data_key: Data key.
        :return: encrypted data or None.
        """
        query = {
            'app_uuid': app_uuid,
            'data_key': data_key
        }
        document = await self.collection.find_one(query)
        if document:
            return document.get('encrypted_data')
        else:
            return None
