import os
from abc import ABC, abstractmethod

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa


class KeyGenerationStrategy(ABC):
    """Base interface for key generation strategies."""

    @abstractmethod
    def generate_key(self) -> bytes:
        """
        Generate a key.

        Returns
        -------
        bytes
            The generated key.
        """
        raise NotImplementedError


class AESKeyGenerationStrategy(KeyGenerationStrategy):
    """Key generation strategy for AES-GCM."""

    def __init__(self, key_length: int):
        self.key_length = key_length

    def generate_key(self) -> bytes:
        return os.urandom(self.key_length)


class ChaCha20KeyGenerationStrategy(KeyGenerationStrategy):
    """Key generation strategy for ChaCha20-Poly1305."""

    def generate_key(self) -> bytes:
        return os.urandom(32)


class RSAKeyGenerationStrategy(KeyGenerationStrategy):
    """Key generation strategy for RSA."""

    def __init__(self, key_size: int):
        """
        Parameters
        ----------
        key_size : int
            Size of the RSA key in bits.
        """
        self.key_size = key_size

    def generate_key(self) -> rsa.RSAPrivateKey:
        """Generate an RSA private key.

        Returns
        -------
        rsa.RSAPrivateKey
            The generated RSA private key.
        """
        return rsa.generate_private_key(public_exponent=65537, key_size=self.key_size)

    def serialize_key(self, key: rsa.RSAPrivateKey) -> bytes:
        """Serialize the RSA private key to PEM format.

        Parameters
        ----------
        key : rsa.RSAPrivateKey
            The RSA private key to serialize.

        Returns
        -------
        bytes
            The serialized private key in PEM format.
        """
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )


class ECDSAKeyGenerationStrategy(KeyGenerationStrategy):
    """Key generation strategy for ECDSA."""

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
    """Key generation strategy for Ed25519."""

    def generate_key(self) -> ed25519.Ed25519PrivateKey:
        return ed25519.Ed25519PrivateKey.generate()


class HMACKeyGenerationStrategy(KeyGenerationStrategy):
    """Key generation strategy for HMAC."""

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
    async def generate_app_key(algorithm: str | None = None) -> tuple[str, bytes]:
        """Generate an encryption key based on the specified algorithm.

        Parameters
        ----------
        algorithm : str, optional
            The encryption algorithm to use (default is None, which uses the default algorithm).

        Returns
        -------
        tuple[str, bytes]
            A tuple containing the algorithm name and the generated key.

        Raises
        ------
        ValueError
            If the specified algorithm is unsupported.
        """
        algorithm = algorithm or KeyAccessModule._default_algorithm
        strategy = KeyAccessModule._strategies.get(algorithm)
        if not strategy:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        key_app = strategy.generate_key()

        if hasattr(strategy, "serialize_key"):
            key_app = strategy.serialize_key(key_app)

        return algorithm, key_app
