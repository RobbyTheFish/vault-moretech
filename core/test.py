from secret_engines.secret_module import SecretEngineModule
from key_access.key_access_module import KeyAccessModule
import asyncio


async def main():
    secret_engine_module = SecretEngineModule()
    key_access_module = KeyAccessModule()
    strategy = "chacha20-poly1305"

    test = b"Hello_world"
    app_key = await key_access_module.generate_app_key(strategy)
    test_encrypt = await secret_engine_module.encrypt(strategy, app_key, test)
    decrypt_test = await secret_engine_module.decrypt(strategy, app_key, test_encrypt)

    print(decrypt_test)


asyncio.run(main())
