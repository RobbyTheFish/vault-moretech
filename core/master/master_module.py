from core.db_conn.storage_backend import SecretStorage
from core.key_access.key_access_module import KeyAccessModule
from core.secret_engines.secret_module import SecretEngineModule


class SecretManagerModule:
    def __init__(self):
        """
        Initialize the SecretManagerModule.

        This sets up the necessary components:
        - SecretStorage for managing secret data.
        - KeyAccessModule for generating and managing application keys.
        - SecretEngineModule for encrypting and decrypting secret values.
        """
        self.secret_storage = SecretStorage()
        self.key_access = KeyAccessModule()
        self.secret_engine = SecretEngineModule()

    async def process_request(
        self, app_id: str, data: dict[str, str] | str, algorithm: str = None
    ) -> dict[str, str]:
        """
        Process a request from another module.

        Parameters
        ----------
        app_id : str
            ID of the application making the request.
        data : dict[str, str] | str
            Secret data to be processed. Can be a dictionary for saving secrets or a string for
            retrieving a secret.
        algorithm : str, optional
            The encryption algorithm to use (default is None).

        Returns
        -------
        dict[str, str]
            Result from the secret engine, either a success status or the retrieved secret.
        """

        app_key = await self.secret_storage._read_key_app(app_id)

        if not app_key:
            algorithm, app_key = await self.key_access.generate_app_key(algorithm=algorithm)
            await self.secret_storage._write_key_app(app_id, app_key)

        if isinstance(data, dict):
            try:
                # Attempt to save all secrets
                result = await self.save_secrets(app_id, app_key, data, algorithm)
            except Exception as e:
                # If there is an error, you might want to handle a rollback
                await self.rollback_secrets(app_id, data)
                return {"error": str(e)}
        else:
            result = await self.retrieve_secret(app_id, app_key, data, algorithm)

        return result

    async def rollback_secrets(self, app_id: str, secrets: dict[str, str]) -> None:
        """Rollback the changes made during a save operation.

        Parameters
        ----------
        app_id : str
            ID of the application.
        secrets : dict[str, str]
            The secrets that were attempted to be saved.
        """
        for key in secrets.keys():
            await self.secret_storage.delete_data(app_id, key)

    async def save_secrets(
        self, app_id: str, app_key: bytes, secrets: dict[str, str], algorithm: str
    ) -> dict[str, str]:
        """
        Save secrets using the secret engine.

        Parameters
        ----------
        app_id : str
            ID of the application.
        app_key : bytes
            Key associated with the application.
        secrets : dict[str, str]
            Dictionary containing keys and their corresponding secret values.
        algorithm : str
            The encryption algorithm to use for encrypting the secrets.

        Returns
        -------
        dict[str, str]
            Status indicating the success of the operation.
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
        Retrieve a secret from the secret engine.

        Parameters
        ----------
        app_id : str
            ID of the application.
        app_key : bytes
            Key associated with the application.
        key : str
            The key for the secret to be retrieved.
        algorithm : str
            The encryption algorithm used for decrypting the secret.

        Returns
        -------
        dict[str, str]
            The decrypted secret or an error message if the secret is not found.
        """
        encrypted_value = await self.secret_storage.read_data(app_id, key)

        if encrypted_value:
            decrypted_value = await self.secret_engine.decrypt(
                algorithm=algorithm, key=app_key, encrypted_value=encrypted_value
            )
            return {key: decrypted_value.decode()}
        else:
            return {"error": "Secret not found"}

    async def delete_secret(self, app_id: str, key: str):
        await self.secret_storage.delete_data(app_id, key)
