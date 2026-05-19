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
import uuid
from pathlib import Path
from typing import Optional, Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)


class FileKeyStore:
    """
    Filesystem-based key store for AES-256 keys.

    Keys are stored as 32-byte binary files under a protected directory.
    Directory permissions: 700. Key file permissions: 600.
    """

    DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".continuum", "keystore")

    def __init__(self, store_path: Optional[str] = None):
        self.store_path = Path(store_path or self.DEFAULT_PATH)
        self._ensure_store_dir()

    def _ensure_store_dir(self) -> None:
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.store_path.chmod(0o700)

    def _key_path(self, key_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key_id)
        return self.store_path / f"{safe}.key"

    def load(self, key_id: str) -> Optional[bytes]:
        """Load a 32-byte key by ID, or None if not found."""
        path = self._key_path(key_id)
        if not path.exists():
            return None
        key = path.read_bytes()
        if len(key) != 32:
            raise ValueError(f"Corrupt key in store (expected 32 bytes): key_id={key_id!r}")
        return key

    def store(self, key_id: str, key: bytes) -> None:
        """Persist a 32-byte key with owner-only read/write permissions."""
        if len(key) != 32:
            raise ValueError("AES-256 key must be exactly 32 bytes")
        path = self._key_path(key_id)
        path.write_bytes(key)
        path.chmod(0o600)
        logger.debug("Stored key %r to %s", key_id, path)


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
        self._current_key: Optional[bytes] = None
        self._key_store = FileKeyStore(getattr(config, "key_store_path", None))

    def _get_key(self) -> bytes:
        """Get or generate encryption key, persisting new keys to the key store."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                # Generate key and persist it so decryption can recover it by key_id
                new_key = os.urandom(32)  # 256 bits
                key_id = str(uuid.uuid4())
                self._key_store.store(key_id, new_key)
                self.config.key_id = key_id
                self._current_key = new_key
                logger.info("Generated and stored new encryption key: key_id=%r", key_id)

        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from the filesystem key store."""
        key = self._key_store.load(key_id)
        if key is None:
            raise KeyError(f"Encryption key not found in key store: key_id={key_id!r}")
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
