import os
from typing import Optional, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
from abc import ABC, abstractmethod


class KeyGenerationStrategy(ABC):
    """Базовый интерфейс для генерации ключей."""

    @abstractmethod
    def generate_key(self) -> Any:
        raise NotImplementedError


class AESKeyGenerationStrategy(KeyGenerationStrategy):
    """Генерация ключа для AES-GCM."""

    def __init__(self, key_length: int):
        self.key_length = key_length

    def generate_key(self) -> bytes:
        return os.urandom(self.key_length)


class ChaCha20KeyGenerationStrategy(KeyGenerationStrategy):
    """Генерация ключа для ChaCha20-Poly1305."""

    def generate_key(self) -> bytes:
        return os.urandom(32)


class RSAKeyGenerationStrategy(KeyGenerationStrategy):
    """Генерация ключа для RSA."""

    def __init__(self, key_size: int):
        self.key_size = key_size

    def generate_key(self) -> rsa.RSAPrivateKey:
        return rsa.generate_private_key(public_exponent=65537, key_size=self.key_size)

    def serialize_key(self, key: rsa.RSAPrivateKey) -> bytes:
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )


class ECDSAKeyGenerationStrategy(KeyGenerationStrategy):
    """Генерация ключа для ECDSA."""

    def __init__(self, curve: ec.EllipticCurve):
        self.curve = curve

    def generate_key(self) -> ec.EllipticCurvePrivateKey:
        return ec.generate_private_key(self.curve)

    def serialize_key(self, key: ec.EllipticCurvePrivateKey) -> bytes:
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )


class Ed25519KeyGenerationStrategy(KeyGenerationStrategy):
    """Генерация ключа для Ed25519."""

    def generate_key(self) -> ed25519.Ed25519PrivateKey:
        return ed25519.Ed25519PrivateKey.generate()


class HMACKeyGenerationStrategy(KeyGenerationStrategy):
    """Генерация ключа для HMAC."""

    def generate_key(self) -> bytes:
        return os.urandom(32)


class KeyAccessModule:
    _default_algorithm = "aes256-gcm96"
    _strategies = {
        "aes128-gcm96": AESKeyGenerationStrategy(16),
        "aes256-gcm96": AESKeyGenerationStrategy(32),
        "chacha20-poly1305": ChaCha20KeyGenerationStrategy(),
        "rsa-2048": RSAKeyGenerationStrategy(2048),
        "rsa-3072": RSAKeyGenerationStrategy(3072),
        "rsa-4096": RSAKeyGenerationStrategy(4096),
        # "ed25519": Ed25519KeyGenerationStrategy(),
        # "ecdsa-p256": ECDSAKeyGenerationStrategy(ec.SECP256R1()),
        # "ecdsa-p384": ECDSAKeyGenerationStrategy(ec.SECP384R1()),
        # "ecdsa-p521": ECDSAKeyGenerationStrategy(ec.SECP521R1()),
        # "hmac": HMACKeyGenerationStrategy(),
    }

    @staticmethod
    async def generate_app_key(algorithm: Optional[str] = None) -> Any:
        """Генерация ключа шифрования на основе указанного алгоритма."""
        algorithm = algorithm or KeyAccessModule._default_algorithm
        strategy = KeyAccessModule._strategies.get(algorithm)
        if not strategy:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Генерируем ключ
        key = strategy.generate_key()
        return key
