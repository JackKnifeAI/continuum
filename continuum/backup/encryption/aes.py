#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
AES-256-GCM Encryption

Industry-standard encryption at rest for backups.
"""

import asyncio
import logging
import os
from typing import Optional, Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)

_DEFAULT_KEY_STORE_DIR = os.path.join(os.path.expanduser("~"), ".continuum", "keystore")


class FileKeyStore:
    """
    Filesystem-based secure key store.

    Keys are stored as individual binary files with 0o600 permissions inside
    a 0o700 directory, so only the owning process can read them.

    The store directory is resolved in order:
    1. Explicit ``store_dir`` constructor argument
    2. ``CONTINUUM_KEY_STORE_DIR`` environment variable
    3. ``~/.continuum/keystore`` (default)
    """

    def __init__(self, store_dir: Optional[str] = None) -> None:
        self._store_dir = (
            store_dir
            or os.environ.get("CONTINUUM_KEY_STORE_DIR")
            or _DEFAULT_KEY_STORE_DIR
        )
        os.makedirs(self._store_dir, mode=0o700, exist_ok=True)

    def _key_path(self, key_id: str) -> str:
        # Sanitise key_id so it can safely be used as a filename
        safe_id = "".join(c if c.isalnum() or c in "-_." else "_" for c in key_id)
        return os.path.join(self._store_dir, f"{safe_id}.key")

    def load(self, key_id: str) -> Optional[bytes]:
        """Return the key bytes for *key_id*, or ``None`` if not stored."""
        path = self._key_path(key_id)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as fh:
            return fh.read()

    def save(self, key_id: str, key_bytes: bytes) -> None:
        """Persist *key_bytes* under *key_id* with restricted permissions (0o600)."""
        path = self._key_path(key_id)
        # O_CREAT | O_WRONLY | O_TRUNC with mode 0o600 avoids a window where
        # an unprivileged reader could access the file between create and chmod.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, key_bytes)
        finally:
            os.close(fd)


class AESEncryptionHandler:
    """
    AES-256-GCM encryption handler.

    Uses authenticated encryption with associated data (AEAD):
    - AES-256 for confidentiality
    - GCM mode for integrity
    - Random IV for each encryption
    - Authentication tag prevents tampering

    Key management:
    - Keys stored securely (filesystem or KMS)
    - Key rotation supported
    - Multiple keys for different backup generations
    """

    def __init__(self, config: EncryptionConfig):
        self.config = config
        self._current_key = None

    def _get_key(self) -> bytes:
        """Get or generate the active encryption key, persisting it to the key store."""
        if self._current_key is None:
            key_store = FileKeyStore(getattr(self.config, "key_store_path", None))
            if self.config.key_id:
                stored = key_store.load(self.config.key_id)
                if stored is not None:
                    self._current_key = stored
                    logger.debug(f"Loaded key '{self.config.key_id}' from key store")
                else:
                    # First use: generate a fresh key and persist it
                    self._current_key = os.urandom(32)  # 256 bits
                    key_store.save(self.config.key_id, self._current_key)
                    logger.info(f"Generated and persisted new key: {self.config.key_id}")
            else:
                self._current_key = os.urandom(32)
                logger.warning("Generated ephemeral encryption key - not suitable for production")

        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load a key from the filesystem key store by key_id.

        Raises KeyError if the key has not been previously stored.
        """
        key_store = FileKeyStore(getattr(self.config, "key_store_path", None))
        key = key_store.load(key_id)
        if key is None:
            raise KeyError(
                f"Encryption key '{key_id}' not found in key store "
                f"({key_store._store_dir}). "
                "The key may have been rotated or the key store moved."
            )
        return key

    async def encrypt(self, data: bytes) -> Tuple[bytes, str]:
        """
        Encrypt data using AES-256-GCM.

        Args:
            data: Plaintext data to encrypt

        Returns:
            Tuple of (encrypted_data, key_id)
        """
        logger.info(f"Encrypting {len(data)} bytes with AES-256-GCM")

        def _encrypt():
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            except ImportError:
                raise ImportError(
                    "cryptography required for encryption. "
                    "Install with: pip install cryptography"
                ) from None

            # Get encryption key
            key = self._get_key()

            # Generate random IV (12 bytes for GCM)
            iv = os.urandom(12)

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Encrypt data (includes authentication tag)
            ciphertext = aesgcm.encrypt(iv, data, None)

            # Prepend IV to ciphertext for storage
            encrypted_data = iv + ciphertext

            return encrypted_data

        encrypted_data = await asyncio.to_thread(_encrypt)

        logger.info(f"Encrypted to {len(encrypted_data)} bytes")

        # Return encrypted data and key ID
        key_id = self.config.key_id or "default-key"
        return encrypted_data, key_id

    async def decrypt(self, data: bytes, key_id: str) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Args:
            data: Encrypted data (IV + ciphertext)
            key_id: Key ID used for encryption

        Returns:
            Decrypted plaintext data
        """
        logger.info(f"Decrypting {len(data)} bytes with AES-256-GCM")

        def _decrypt():
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            except ImportError:
                raise ImportError(
                    "cryptography required for decryption. "
                    "Install with: pip install cryptography"
                ) from None

            # Extract IV and ciphertext
            iv = data[:12]
            ciphertext = data[12:]

            # Load key
            key = self._load_key(key_id)

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Decrypt and verify
            plaintext = aesgcm.decrypt(iv, ciphertext, None)

            return plaintext

        plaintext = await asyncio.to_thread(_decrypt)

        logger.info(f"Decrypted to {len(plaintext)} bytes")
        return plaintext


class NoEncryptionHandler:
    """No-op encryption handler (returns data unchanged)"""

    async def encrypt(self, data: bytes) -> Tuple[bytes, str]:
        """Pass through without encryption"""
        return data, "no-encryption"

    async def decrypt(self, data: bytes, key_id: str) -> bytes:
        """Pass through without decryption"""
        return data

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
