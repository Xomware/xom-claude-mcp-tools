"""Encryption utilities for secure data handling."""

import os
import base64
from typing import Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from loguru import logger


class EncryptionManager:
    """Manages encryption/decryption of sensitive data."""

    def __init__(self, key: Union[str, bytes] = None):
        """Initialize encryption manager.

        Args:
            key: Encryption key (bytes) or master key string
        """
        if key is None:
            key = os.getenv("ENCRYPTION_KEY", "default-key")

        if isinstance(key, str):
            # Derive a proper key from the provided string
            self.key = self._derive_key(key)
        else:
            self.key = key

        self.cipher = Fernet(self.key)

    def _derive_key(self, master_key: str) -> bytes:
        """Derive encryption key from master key using PBKDF2.

        Args:
            master_key: Master key string

        Returns:
            Derived encryption key bytes
        """
        # Use a fixed salt for deterministic derivation
        salt = b"xomware-mcp-salt"

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        derived = kdf.derive(master_key.encode())
        return base64.urlsafe_b64encode(derived)

    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data.

        Args:
            data: Data to encrypt (str or bytes)

        Returns:
            Base64-encoded encrypted data
        """
        try:
            if isinstance(data, str):
                data = data.encode()

            encrypted = self.cipher.encrypt(data)
            return base64.b64encode(encrypted).decode()

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data.

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            Decrypted string
        """
        try:
            encrypted = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2.

        Args:
            password: Password to hash

        Returns:
            Hashed password
        """
        salt = b"xomware-pw-salt"
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        hashed = kdf.derive(password.encode())
        return base64.b64encode(hashed).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against a hash.

        Args:
            password: Password to verify
            hashed: Hashed password

        Returns:
            True if password matches hash
        """
        return self.hash_password(password) == hashed

    def mask_sensitive(self, value: str, show_chars: int = 4) -> str:
        """Mask sensitive data for logging.

        Args:
            value: Value to mask
            show_chars: Number of characters to show at start/end

        Returns:
            Masked string (e.g., "abc...xyz")
        """
        if len(value) <= show_chars * 2:
            return "*" * len(value)

        return (
            value[:show_chars]
            + "*" * (len(value) - show_chars * 2)
            + value[-show_chars:]
        )
