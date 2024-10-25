from abc import ABC, abstractmethod
from os import urandom

from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from core.config import Config


class EncryptionStrategy(ABC):
    """Base interface for encryption strategies."""

    @abstractmethod
    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        """Encrypts plaintext using the specified key.

        Parameters
        ----------
        key : bytes
            The key used for encryption.
        plaintext : bytes
            The data to be encrypted.

        Returns
        -------
        bytes
            The encrypted data (ciphertext).
        """
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        """Decrypts ciphertext using the specified key.

        Parameters
        ----------
        key : bytes
            The key used for decryption.
        ciphertext : bytes
            The data to be decrypted.

        Returns
        -------
        bytes
            The decrypted data (plaintext).
        """
        raise NotImplementedError


class AESEncryptionStrategy(EncryptionStrategy):
    """Encryption strategy for AES-GCM."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        """Encrypts plaintext using AES-GCM.

        Parameters
        ----------
        key : bytes
            The AES key used for encryption.
        plaintext : bytes
            The data to be encrypted.

        Returns
        -------
        bytes
            The encrypted data, consisting of nonce, ciphertext, and authentication tag.
        """
        nonce = urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return nonce + ciphertext + encryptor.tag

    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        """Decrypts ciphertext using AES-GCM.

        Parameters
        ----------
        key : bytes
            The AES key used for decryption.
        ciphertext : bytes
            The data to be decrypted, consisting of nonce, ciphertext, and authentication tag.

        Returns
        -------
        bytes
            The decrypted data (plaintext).
        """
        nonce = ciphertext[:12]
        tag = ciphertext[-16:]
        encrypted_data = ciphertext[12:-16]
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()


class ChaCha20EncryptionStrategy(EncryptionStrategy):
    """Encryption strategy for ChaCha20-Poly1305."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        """Encrypts plaintext using ChaCha20-Poly1305.

        Parameters
        ----------
        key : bytes
            The ChaCha20 key used for encryption.
        plaintext : bytes
            The data to be encrypted.

        Returns
        -------
        bytes
            The encrypted data, including the nonce.
        """
        nonce = urandom(16)
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return nonce + ciphertext

    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        """Decrypts ciphertext using ChaCha20-Poly1305.

        Parameters
        ----------
        key : bytes
            The ChaCha20 key used for decryption.
        ciphertext : bytes
            The data to be decrypted, including the nonce.

        Returns
        -------
        bytes
            The decrypted data (plaintext).
        """
        nonce = ciphertext[:16]
        encrypted_data = ciphertext[16:]
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()


class RSAEncryptionStrategy(EncryptionStrategy):
    """Encryption strategy for RSA."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        """Encrypts plaintext using RSA with the public key.

        Parameters
        ----------
        key : bytes
            The PEM encoded RSA private key used for encryption.
        plaintext : bytes
            The data to be encrypted.

        Returns
        -------
        bytes
            The encrypted data (ciphertext).
        """
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
        """Decrypts ciphertext using RSA with the private key.

        Parameters
        ----------
        key : bytes
            The PEM encoded RSA private key used for decryption.
        ciphertext : bytes
            The data to be decrypted.

        Returns
        -------
        bytes
            The decrypted data (plaintext).
        """
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
    """Strategy for HMAC."""

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        """Generates an HMAC for the given plaintext.

        Parameters
        ----------
        key : bytes
            The key used for HMAC generation.
        plaintext : bytes
            The data for which to generate HMAC.

        Returns
        -------
        bytes
            The generated HMAC.
        """
        h = hmac.HMAC(key, hashes.SHA256())
        h.update(plaintext)
        return h.finalize()

    def decrypt(self, key: bytes, ciphertext: bytes) -> bool:
        """Validates the HMAC for the given ciphertext.

        Parameters
        ----------
        key : bytes
            The key used for HMAC validation.
        ciphertext : bytes
            The HMAC to validate.

        Returns
        -------
        bool
            True if the HMAC is valid, False otherwise.
        """
        h = hmac.HMAC(key, hashes.SHA256())
        h.update(ciphertext)
        return h.finalize()


class SecretEngineModule:
    """Module for managing secrets with different encryption strategies."""

    def __init__(self):
        """Initializes the SecretEngineModule and loads encryption strategies."""
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
        self.__master_key = bytes.fromhex(Config().MASTER_KEY.strip())
        self.__master_encrypt_decrypt = self._encryption_strategies.get(Config().TYPE_ENCRYPT)

    async def encrypt(self, algorithm: str, key: bytes, value: bytes) -> bytes:
        """Encrypts data using the specified algorithm and returns the encrypted value.

        Parameters
        ----------
        algorithm : str
            The encryption algorithm to use.
        key : bytes
            The key used for the encryption strategy.
        value : bytes
            The data to be encrypted.

        Returns
        -------
        bytes
            The encrypted data.
        """
        strategy = self._encryption_strategies.get(algorithm)
        if not strategy:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        return self.__master_encrypt_decrypt.encrypt(
            self.__master_key, strategy.encrypt(key, value)
        )

    async def decrypt(self, algorithm: str, key: bytes, encrypted_value: bytes) -> bytes:
        """Decrypts the encrypted value using the specified algorithm and returns
        the decrypted data.

        Parameters
        ----------
        algorithm : str
            The encryption algorithm to use.
        key : bytes
            The key used for the decryption strategy.
        encrypted_value : bytes
            The encrypted data to be decrypted.

        Returns
        -------
        bytes
            The decrypted data (plaintext).
        """
        strategy = self._encryption_strategies.get(algorithm)
        if not strategy:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        return strategy.decrypt(
            key, self.__master_encrypt_decrypt.decrypt(self.__master_key, encrypted_value)
        )
