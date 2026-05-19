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

    def _get_key_store_path(self) -> Path:
        """Return path to the filesystem key store directory."""
        store = os.environ.get('CONTINUUM_KEY_STORE_PATH', os.path.expanduser('~/.continuum/keys'))
        return Path(store)

    def _save_key(self, key_id: str, key: bytes) -> None:
        """Persist a key to the filesystem key store with owner-only permissions."""
        key_store = self._get_key_store_path()
        key_store.mkdir(parents=True, exist_ok=True)
        key_file = key_store / key_id
        key_file.write_bytes(key)
        key_file.chmod(0o600)
        logger.info(f"Stored encryption key '{key_id}' at {key_file}")

    def _load_key(self, key_id: str) -> bytes:
        """Load a 256-bit AES key from env var or filesystem key store.

        Lookup order:
        1. Environment variable ``CONTINUUM_KEY_<KEY_ID>`` (hex-encoded 32 bytes)
        2. File ``<key_store_path>/<key_id>`` (raw 32 bytes)

        Raises:
            KeyError: if the key cannot be found in either location.
            ValueError: if the located key is not exactly 32 bytes.
        """
        env_var = f"CONTINUUM_KEY_{key_id.upper().replace('-', '_')}"
        env_value = os.environ.get(env_var)
        if env_value:
            try:
                key = bytes.fromhex(env_value)
            except ValueError as exc:
                raise ValueError(f"Key in {env_var} must be a hex-encoded 32-byte value") from exc
            if len(key) != 32:
                raise ValueError(f"Key in {env_var} must be 32 bytes (256-bit), got {len(key)}")
            return key

        key_file = self._get_key_store_path() / key_id
        if key_file.exists():
            key = key_file.read_bytes()
            if len(key) != 32:
                raise ValueError(f"Key file {key_file} must contain 32 bytes, got {len(key)}")
            return key

        raise KeyError(
            f"Encryption key '{key_id}' not found. "
            f"Set {env_var} (hex) or place 32 raw bytes at {self._get_key_store_path() / key_id}"
        )

    def _get_key(self) -> bytes:
        """Return the active encryption key, generating and persisting one if needed."""
        if self._current_key is None:
            if self.config.key_id:
                try:
                    self._current_key = self._load_key(self.config.key_id)
                except KeyError:
                    # First use: generate, then persist for future sessions.
                    self._current_key = os.urandom(32)
                    self._save_key(self.config.key_id, self._current_key)
                    logger.info(f"Generated and persisted new encryption key '{self.config.key_id}'")
            else:
                self._current_key = os.urandom(32)
                logger.warning("Generated ephemeral encryption key - not suitable for production")

        return self._current_key

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
