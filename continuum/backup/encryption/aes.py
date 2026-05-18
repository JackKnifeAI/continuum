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
        """Get or generate encryption key."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)  # 256 bits
                logger.warning(
                    "Generated ephemeral encryption key — not suitable for production. "
                    "Set key_id in EncryptionConfig and store the key via env var "
                    "CONTINUUM_ENCRYPTION_KEY_<KEY_ID> or ~/.continuum/keys/<key_id>.key"
                )
        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load a 256-bit key from the secure key store.

        Resolution order:
        1. Env var ``CONTINUUM_ENCRYPTION_KEY_<KEY_ID>`` (base64-encoded 32 bytes)
        2. Key file ``~/.continuum/keys/<key_id>.key`` (raw 32 bytes, must be chmod 600)
        """
        # 1. Environment variable
        env_var = "CONTINUUM_ENCRYPTION_KEY_" + key_id.upper().replace("-", "_")
        env_value = os.environ.get(env_var)
        if env_value:
            try:
                key = base64.b64decode(env_value)
            except Exception as exc:
                raise ValueError(f"Cannot base64-decode key from {env_var}") from exc
            if len(key) != 32:
                raise ValueError(
                    f"Key in {env_var} must decode to exactly 32 bytes (got {len(key)})"
                )
            return key

        # 2. Key file
        key_file = Path.home() / ".continuum" / "keys" / f"{key_id}.key"
        if key_file.exists():
            mode = key_file.stat().st_mode
            if mode & 0o077:
                raise PermissionError(
                    f"Key file {key_file} has insecure permissions "
                    f"({oct(mode & 0o777)}). Run: chmod 600 {key_file}"
                )
            key = key_file.read_bytes()
            if len(key) != 32:
                raise ValueError(
                    f"Key file {key_file} must contain exactly 32 bytes (got {len(key)})"
                )
            return key

        raise FileNotFoundError(
            f"No key found for key_id '{key_id}'. "
            f"Provide it via the {env_var} environment variable "
            f"or create {key_file} (chmod 600)."
        )

    @staticmethod
    def generate_and_store_key(key_id: str) -> Path:
        """Generate a new 256-bit key and persist it to ``~/.continuum/keys/``.

        Returns the path of the written key file. The file is created with
        mode 0600 so only the owning user can read it.
        """
        key_dir = Path.home() / ".continuum" / "keys"
        key_dir.mkdir(parents=True, exist_ok=True)
        key_file = key_dir / f"{key_id}.key"

        key = os.urandom(32)
        # Write with owner-only permissions from the start
        key_file.touch(mode=0o600, exist_ok=False)
        key_file.write_bytes(key)
        key_file.chmod(0o600)

        logger.info("Stored new encryption key at %s", key_file)
        return key_file

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
