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

    def _get_key_path(self, key_id: str) -> Path:
        """Resolve filesystem path for a key file."""
        key_dir = Path(os.environ.get("CONTINUUM_KEY_DIR", str(Path.home() / ".continuum" / "keys")))
        return key_dir / f"{key_id}.key"

    def _store_key(self, key_id: str, key: bytes) -> None:
        """Persist a 256-bit key to the key store with owner-only permissions."""
        key_path = self._get_key_path(key_id)
        key_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        key_path.write_bytes(key)
        key_path.chmod(0o600)
        logger.info(f"Stored encryption key '{key_id}' at {key_path}")

    def _load_key(self, key_id: str) -> bytes:
        """Load key from secure key store.

        Resolution order:
        1. Env var CONTINUUM_KEY_<KEY_ID> (base64-encoded 32 bytes)
        2. Key file in CONTINUUM_KEY_DIR (default: ~/.continuum/keys/)
        """
        env_var = f"CONTINUUM_KEY_{key_id.upper().replace('-', '_')}"
        key_b64 = os.environ.get(env_var)
        if key_b64:
            key = base64.b64decode(key_b64)
            if len(key) != 32:
                raise ValueError(f"Key from {env_var} must be exactly 32 bytes (256 bits)")
            return key

        key_path = self._get_key_path(key_id)
        if key_path.exists():
            key = key_path.read_bytes()
            if len(key) != 32:
                raise ValueError(f"Key file {key_path} must contain exactly 32 bytes")
            return key

        raise KeyError(
            f"Encryption key '{key_id}' not found. "
            f"Set {env_var} (base64) or place a 32-byte key file at {key_path}"
        )

    def _get_key(self) -> bytes:
        """Get or generate encryption key."""
        if self._current_key is None:
            if self.config.key_id:
                try:
                    self._current_key = self._load_key(self.config.key_id)
                except KeyError:
                    self._current_key = os.urandom(32)
                    self._store_key(self.config.key_id, self._current_key)
                    logger.info(f"Generated and stored new encryption key: {self.config.key_id}")
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
