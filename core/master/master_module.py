from core.db_conn.storage_backend import SecretStorage
from core.key_access.key_access_module import KeyAccessModule
from core.secret_engines.secret_module import SecretEngineModule


class SecretManagerModule:
    def __init__(self):
        """
        Init key_access and secret_engine
        """
        self.secret_storage = SecretStorage()
        self.key_access = KeyAccessModule()
        self.secret_engine = SecretEngineModule()

    async def process_request(
        self, app_id: str, data: dict[str, str] | str, algorithm: str = None
    ) -> dict[str, str]:
        """
        Processing request from another module

        :param app_id: ID app.
        :param data: data is key.
        :return: Secret_engine result.
        """

        app_key = await self.secret_storage._read_key_app(app_id)

        if not app_key:
            algorithm, app_key = await self.key_access.generate_app_key(algorithm=algorithm)
            await self.secret_storage._write_key_app(app_id, app_key)

        if isinstance(data, dict):
            result = await self.save_secrets(app_id, app_key, data, algorithm)
        else:
            result = await self.retrieve_secret(app_id, app_key, data, algorithm)

        return result

    async def save_secrets(
        self, app_id: str, app_key: bytes, secrets: dict[str, str], algorithm: str
    ) -> dict[str, str]:
        """
        Save secrets with secret_engine

        :param app_id: ID app.
        :param app_key: Key of app
        :param secrets: dict with keys and values
        :return: status
        """
        for key, value in secrets.items():
            encrypted_key_value = await self.secret_engine.encrypt(
                algorithm=algorithm, key=app_key, value=value.encode()
            )
            await self.secret_storage.write_data(app_id, key, encrypted_key_value)

        return {"status": "success"}

    async def retrieve_secret(
        self, app_id: str, app_key: bytes, key: str, algorithm: str
    ) -> dict[str, str]:
        """
        Retrieve secrets grom secret engine

        :param app_id: ID app.
        :param app_key: Key of app.
        :param key: dict with keys and values.
        :return: Decrypted message
        """
        encrypted_value = await self.secret_storage.read_data(app_id, key)

        if encrypted_value:
            decrypted_value = await self.secret_engine.decrypt(
                algorithm=algorithm, key=app_key, encrypted_value=encrypted_value
            )
            return {key: decrypted_value.decode()}
        else:
            return {"error": "Secret not found"}
