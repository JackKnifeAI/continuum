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
import base64
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

    def _get_key(self) -> bytes:
        """Get or generate encryption key, persisting to key store when possible."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)  # 256 bits
                logger.warning("Generated ephemeral encryption key - not suitable for production")

        return self._current_key

    def _key_store_path(self) -> Path:
        """Return the directory used for filesystem key storage."""
        key_dir = os.environ.get("CONTINUUM_KEY_DIR")
        if key_dir:
            return Path(key_dir)
        return Path.home() / ".continuum" / "keys"

    def _load_key(self, key_id: str) -> bytes:
        """Load a 256-bit key from env var or filesystem key store.

        Resolution order:
        1. Environment variable ``CONTINUUM_KEY_<KEY_ID>`` (base64-encoded 32 bytes)
        2. File ``<CONTINUUM_KEY_DIR>/<key_id>.key`` (raw 32 bytes, mode 0o600)
        """
        # 1. Environment variable (base64-encoded)
        env_var = "CONTINUUM_KEY_" + key_id.upper().replace("-", "_").replace(".", "_")
        env_val = os.environ.get(env_var)
        if env_val:
            try:
                key = base64.b64decode(env_val)
                if len(key) == 32:
                    return key
                logger.warning("Key from %s is not 32 bytes (%d), skipping", env_var, len(key))
            except Exception:
                logger.warning("Failed to base64-decode key from %s, skipping", env_var)

        # 2. Filesystem key store
        key_path = self._key_store_path() / f"{key_id}.key"
        if key_path.exists():
            try:
                file_mode = key_path.stat().st_mode & 0o777
                if file_mode & 0o077:
                    logger.warning("Key file %s has loose permissions (%o) - tighten to 0o600", key_path, file_mode)
                key = key_path.read_bytes()
                if len(key) == 32:
                    return key
                logger.warning("Key file %s is not 32 bytes (%d), skipping", key_path, len(key))
            except OSError as e:
                logger.warning("Failed to read key from %s: %s", key_path, e)

        # No secure key found - generate and persist so subsequent calls are consistent
        logger.warning(
            "No key found for key_id=%r via %s or %s; generating and storing a new key",
            key_id, env_var, key_path,
        )
        return self._generate_and_store_key(key_id)

    def _generate_and_store_key(self, key_id: str) -> bytes:
        """Generate a new 256-bit key and persist it to the filesystem key store."""
        key = os.urandom(32)
        key_dir = self._key_store_path()
        try:
            key_dir.mkdir(parents=True, exist_ok=True)
            key_dir.chmod(0o700)
            key_path = key_dir / f"{key_id}.key"
            # Write with restricted permissions from the start
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(key)
            logger.info("Stored new encryption key for key_id=%r at %s", key_id, key_path)
        except OSError as e:
            logger.error("Could not persist key for key_id=%r to %s: %s", key_id, key_dir, e)
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
