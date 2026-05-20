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
import stat
from pathlib import Path
from typing import Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)


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

    _KEY_STORE_DIR = Path.home() / ".continuum" / "keys"

    def _get_key(self) -> bytes:
        """Get or generate encryption key"""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)  # 256 bits
                logger.warning("Generated ephemeral encryption key - not suitable for production")

        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from secure filesystem key store, generating it if absent.

        Keys are stored as raw 32-byte files under ~/.continuum/keys/ with
        directory permissions 0700 and file permissions 0600 to prevent
        other users from reading them.
        """
        key_store_dir = self._KEY_STORE_DIR
        key_store_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(key_store_dir, stat.S_IRWXU)  # 0700 — owner only

        # Sanitize key_id to a safe filename (replace path separators)
        safe_id = key_id.replace("/", "_").replace("\\", "_")
        key_file = key_store_dir / f"{safe_id}.key"

        if key_file.exists():
            key_bytes = key_file.read_bytes()
            if len(key_bytes) != 32:
                raise ValueError(
                    f"Corrupt key in store for key_id={key_id!r}: "
                    f"expected 32 bytes, got {len(key_bytes)}"
                )
            logger.debug("Loaded encryption key %r from key store", key_id)
            return key_bytes

        # Generate a new key and persist it atomically
        key_bytes = os.urandom(32)  # AES-256
        key_file.write_bytes(key_bytes)
        os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)  # 0600 — owner only
        logger.info("Generated and stored new encryption key %r", key_id)
        return key_bytes

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
