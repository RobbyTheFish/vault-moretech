"""
Что модуль должен делать:
Получать из модуля аутентификации некоторые даные (т.е. должен быть stateless) 
получает uuid приложения и данные (ключ:значение или просто ключ)
Передаёт в key_access информацию о приложении, тот генерирует ключ приложения и возвращает его, ключ приложения хранится в отдельной коллекции
Передаёт ключ приложения в secret_engine (на выбор)
Получает ответ от secret engine
"""
import asyncio
...
...


class SecretManagerModule:
    def __init__(self):
        """
        Init key_access and secret_engine
        """
        #self.key_access = KeyAccessModule()
        #self.secret_engine = SecretEngineModule()

    async def process_request(self, app_uuid, data):
        """
        Processing request from another module

        :param app_uuid: UUID app.
        :param data: data is key.
        :return: Secret_engine result.
        """

        app_key = await self.key_access.get_or_generate_app_key(app_uuid)

        if isinstance(data, dict):
            result = await self.save_secrets(app_uuid, app_key, data)
        else:
            result = await self.retrieve_secret(app_uuid, app_key, data)

        return result

    async def save_secrets(self, app_uuid, app_key, secrets):
        """
        Save secrets with secret_engine

        :param app_uuid: UUID app.
        :param app_key: Key of app
        :param secrets: dict with keys and values
        :return: status
        """
        for key, value in secrets.items():
            encrypted_key_value = await self.secret_engine.encrypt(app_key, key, value)
            await self.db_module.save_data(app_uuid, encrypted_key_value["key"], encrypted_key_value["encrypted_value"])
        
        return {"status": "success"}

    async def retrieve_secret(self, app_uuid, app_key, key):
        """
        Retrieve secrets grom secret engine

        :param app_uuid: UUID app.
        :param app_key: Key of app.
        :param key: dict with keys and values.
        :return: Decrypted message
        """
        encrypted_value = await self.db_module.get_data(app_uuid, key)
        if encrypted_value:
            decrypted_value = await self.secret_engine.decrypt(app_key, key, encrypted_value)
            return {key: decrypted_value}
        else:
            return {"error": "Secret not found"}