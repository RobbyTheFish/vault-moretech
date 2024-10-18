"""
Что модуль должен делать:
Получать из модуля аутентификации некоторые даные (т.е. должен быть stateless)
получает uuid приложения и данные (ключ:значение или просто ключ)
Передаёт в key_access информацию о приложении, тот генерирует ключ приложения и возвращает его, ключ приложения хранится в отдельной коллекции
Передаёт ключ приложения в secret_engine (на выбор)
Получает ответ от secret engine
"""

from sqlalchemy.future import select

from auth.db import AsyncSessionLocal
from auth.models import TypeStrategiesEncrypt
from core.db_conn.db_module import DatabaseModule
from core.key_access.key_access_module import KeyAccessModule
from core.secret_engines.secret_module import SecretEngineModule


class SecretManagerModule:
    def __init__(self):
        """
        Init key_access and secret_engine
        """
        self.db_module = DatabaseModule()
        self.key_access = KeyAccessModule()
        self.secret_engine = SecretEngineModule()

    async def process_request(
        self, app_uuid: str, data: dict[str, str] | str, type_algorithm: str = None
    ) -> dict[str, str]:
        """
        Processing request from another module

        :param app_uuid: UUID app.
        :param data: data is key.
        :return: Secret_engine result.
        """

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TypeStrategiesEncrypt)
                .select_from(TypeStrategiesEncrypt)
                .where(TypeStrategiesEncrypt.application_uuid == app_uuid)
            )

        app_data_key_app = result.first()

        if not app_data_key_app:
            algorithm, app_key = await self.key_access.generate_app_key(
                algorithm=type_algorithm
            )

            async with AsyncSessionLocal() as session:
                new_type_strategies_encrypt = TypeStrategiesEncrypt(
                    type=algorithm, app_key=app_key, application_uuid=app_uuid
                )
                session.add(new_type_strategies_encrypt)
                await session.commit()
                await session.refresh(new_type_strategies_encrypt)
        else:
            app_data_key_app = app_data_key_app[0]
            algorithm = app_data_key_app.type
            app_key = app_data_key_app.app_key

        if isinstance(data, dict):
            result = await self.save_secrets(app_uuid, app_key, data, algorithm)
        else:
            result = await self.retrieve_secret(app_uuid, app_key, data, algorithm)

        return result

    async def save_secrets(
        self, app_uuid: str, app_key: bytes, secrets: dict[str, str], algorithm: str
    ) -> dict[str, str]:
        """
        Save secrets with secret_engine

        :param app_uuid: UUID app.
        :param app_key: Key of app
        :param secrets: dict with keys and values
        :return: status
        """
        for key, value in secrets.items():
            encrypted_key_value = await self.secret_engine.encrypt(
                algorithm=algorithm, key=app_key, value=value.encode()
            )
            await self.db_module.save_data(
                app_uuid,
                key,
                encrypted_key_value,
            )

        return {"status": "success"}

    async def retrieve_secret(
        self, app_uuid: str, app_key: bytes, key: str, algorithm: str
    ) -> dict[str, str]:
        """
        Retrieve secrets grom secret engine

        :param app_uuid: UUID app.
        :param app_key: Key of app.
        :param key: dict with keys and values.
        :return: Decrypted message
        """
        encrypted_value = await self.db_module.get_data(app_uuid, key)

        if encrypted_value:
            decrypted_value = await self.secret_engine.decrypt(
                algorithm=algorithm, key=app_key, encrypted_value=encrypted_value
            )
            return {key: decrypted_value.decode()}
        else:
            return {"error": "Secret not found"}
