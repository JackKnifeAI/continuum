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
import re
import stat
from pathlib import Path
from typing import Optional, Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)

_SAFE_KEY_ID = re.compile(r"[^a-zA-Z0-9_\-]")


class FileKeyStore:
    """
    File-based secure key store.

    Keys are written with mode 0o600 (owner read/write only) under a
    directory that is itself restricted to 0o700.  Key IDs are sanitised
    before use as filenames to prevent path traversal.
    """

    DEFAULT_PATH = Path("continuum_data/keystore")

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or self.DEFAULT_PATH

    def _key_path(self, key_id: str) -> Path:
        safe_id = _SAFE_KEY_ID.sub("_", key_id)
        return self.store_path / f"{safe_id}.key"

    def _ensure_store(self) -> None:
        self.store_path.mkdir(parents=True, exist_ok=True)
        os.chmod(self.store_path, stat.S_IRWXU)  # 0o700

    def load(self, key_id: str) -> Optional[bytes]:
        """Return key bytes, or None if not found."""
        path = self._key_path(key_id)
        if not path.exists():
            return None
        return path.read_bytes()

    def store(self, key_id: str, key_bytes: bytes) -> None:
        """Persist key bytes with restrictive permissions."""
        self._ensure_store()
        path = self._key_path(key_id)
        path.write_bytes(key_bytes)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600

    def exists(self, key_id: str) -> bool:
        return self._key_path(key_id).exists()


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

    def __init__(self, config: EncryptionConfig, key_store: Optional[FileKeyStore] = None):
        self.config = config
        self._key_store = key_store or FileKeyStore()
        self._current_key: Optional[bytes] = None

    def _get_key(self) -> bytes:
        """Return the active encryption key, loading or generating it as needed."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)  # 256-bit ephemeral key
                logger.warning("Generated ephemeral encryption key - not suitable for production")
        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from the file-based key store, generating and persisting one if absent."""
        key = self._key_store.load(key_id)
        if key is not None:
            logger.debug("Loaded encryption key '%s' from key store", key_id)
            return key

        # First use: generate a fresh 256-bit key and persist it.
        key = os.urandom(32)
        self._key_store.store(key_id, key)
        logger.info("Generated and stored new encryption key '%s'", key_id)
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
