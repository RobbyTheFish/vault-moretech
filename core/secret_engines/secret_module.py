from abc import ABC, abstractmethod
from os import urandom

from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class EncryptionStrategy(ABC):
    """Базовый интерфейс для стратегий шифрования."""

    @abstractmethod
    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        raise NotImplementedError


class AESEncryptionStrategy(EncryptionStrategy):
    """Стратегия шифрования для AES-GCM."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        nonce = urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return nonce + ciphertext + encryptor.tag

    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        nonce = ciphertext[:12]
        tag = ciphertext[-16:]
        encrypted_data = ciphertext[12:-16]
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()


class ChaCha20EncryptionStrategy(EncryptionStrategy):
    """Стратегия шифрования для ChaCha20-Poly1305."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        nonce = urandom(16)
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return nonce + ciphertext

    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        nonce = ciphertext[:16]
        encrypted_data = ciphertext[16:]
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()


class RSAEncryptionStrategy(EncryptionStrategy):
    """Стратегия шифрования для RSA."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        """Использует приватный ключ для шифрования данных (для хранения)."""
        private_key = serialization.load_pem_private_key(key, password=None)
        public_key = private_key.public_key()
        return public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        """Расшифровывает данные, используя приватный ключ."""
        private_key = serialization.load_pem_private_key(key, password=None)
        return private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )


class HMACStrategy(EncryptionStrategy):
    """Стратегия для HMAC."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        h = hmac.HMAC(key, hashes.SHA256())
        h.update(plaintext)
        return h.finalize()

    def decrypt(self, key: bytes, ciphertext: bytes) -> bool:
        h = hmac.HMAC(key, hashes.SHA256())
        h.update(ciphertext)
        return h.finalize()


class SecretEngineModule:
    def __init__(self):
        self._encryption_strategies = {
            "aes128-gcm96": AESEncryptionStrategy(),
            "aes256-gcm96": AESEncryptionStrategy(),
            "chacha20-poly1305": ChaCha20EncryptionStrategy(),
            "rsa-2048": RSAEncryptionStrategy(),
            "rsa-3072": RSAEncryptionStrategy(),
            "rsa-4096": RSAEncryptionStrategy(),
            # "ed25519": Ed25519KeyEncryptionStrategy(),
            # "ecdsa-p256": ECDSAKeyEncryptionStrategy(),
            # "ecdsa-p384": ECDSAKeyEncryptionStrategy(),
            # "ecdsa-p521": ECDSAKeyEncryptionStrategy(),
            # "hmac": HMACStrategy(),
        }

    async def encrypt(self, algorithm: str, key: bytes, value: bytes) -> bytes:
        """Шифрование данных и возврат их."""
        strategy = self._encryption_strategies.get(algorithm)
        if not strategy:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        return strategy.encrypt(key, value)

    async def decrypt(
        self, algorithm: str, key: bytes, encrypted_value: bytes
    ) -> bytes:
        """Дешифрование данных и отдача их пользователю."""
        strategy = self._encryption_strategies.get(algorithm)
        if not strategy:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        return strategy.decrypt(key, encrypted_value)
