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
import stat
from pathlib import Path
from typing import Optional, Tuple

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
                self._current_key = os.urandom(32)
                logger.warning(
                    "No key_id configured; using ephemeral encryption key. "
                    "Data encrypted this way cannot be decrypted in future sessions."
                )
        return self._current_key

    def _load_key_from_env(self, key_id: str) -> Optional[bytes]:
        """Load a base64-encoded 32-byte key from CONTINUUM_KEY_<KEY_ID>."""
        env_var = "CONTINUUM_KEY_" + key_id.upper().replace("-", "_").replace(".", "_")
        encoded = os.environ.get(env_var)
        if encoded is None:
            return None
        try:
            key = base64.b64decode(encoded)
        except Exception as exc:
            raise ValueError(f"Cannot base64-decode key in {env_var}") from exc
        if len(key) != 32:
            raise ValueError(
                f"Key in {env_var} must decode to exactly 32 bytes (AES-256), got {len(key)}"
            )
        return key

    def _load_key_from_file(self, key_id: str) -> Optional[bytes]:
        """Load a 32-byte key from ~/.continuum/keys/<key_id> (mode 0o600 enforced)."""
        key_path = Path.home() / ".continuum" / "keys" / key_id
        if not key_path.exists():
            return None
        file_mode = key_path.stat().st_mode
        if file_mode & (stat.S_IRGRP | stat.S_IROTH):
            raise PermissionError(
                f"Key file {key_path} is group/world-readable. "
                f"Fix with: chmod 600 {key_path}"
            )
        key = key_path.read_bytes()
        if len(key) != 32:
            raise ValueError(
                f"Key file {key_path} must contain exactly 32 bytes (AES-256), got {len(key)}"
            )
        return key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from secure key store.

        Resolution order:
        1. Environment variable  CONTINUUM_KEY_<KEY_ID>  (base64-encoded 32 bytes)
        2. Key file              ~/.continuum/keys/<key_id>  (raw 32 bytes, mode 0o600)
        3. SHA-256 derivation from key_id  [insecure – development only]
        """
        key = self._load_key_from_env(key_id)
        if key is not None:
            return key

        key = self._load_key_from_file(key_id)
        if key is not None:
            return key

        # Insecure fallback: derive key from key_id string (NOT safe for production)
        import hashlib
        env_var = "CONTINUUM_KEY_" + key_id.upper().replace("-", "_").replace(".", "_")
        logger.warning(
            "Key '%s' not found in environment or key file; "
            "falling back to SHA-256 derivation – NOT secure for production. "
            "To fix: set %s=<base64-encoded 32-byte key> or "
            "write 32 raw bytes to ~/.continuum/keys/%s (chmod 600).",
            key_id, env_var, key_id,
        )
        return hashlib.sha256(key_id.encode()).digest()

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
