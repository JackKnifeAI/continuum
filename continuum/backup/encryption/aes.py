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
from typing import Optional, Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)


class KeyStore:
    """
    Secure local key storage for AES encryption keys.

    Key lookup order:
    1. Environment variable ``CONTINUUM_KEY_<KEY_ID>`` — base64-encoded 32 bytes.
    2. Key file ``~/.continuum/keys/<key_id>.key`` with mode 0o600.

    Storing a key in an env var is preferred in containerised environments;
    the file store is the fallback for long-lived local deployments.
    """

    _DEFAULT_DIR: Path = Path.home() / ".continuum" / "keys"

    @classmethod
    def _key_path(cls, key_id: str) -> Path:
        safe_id = key_id.replace("/", "_").replace("\\", "_")
        return cls._DEFAULT_DIR / f"{safe_id}.key"

    @classmethod
    def load(cls, key_id: str) -> Optional[bytes]:
        """Return the 32-byte key for *key_id*, or ``None`` if not found."""
        env_var = f"CONTINUUM_KEY_{key_id.upper().replace('-', '_')}"
        raw = os.environ.get(env_var)
        if raw:
            try:
                key = base64.b64decode(raw)
            except Exception as exc:
                raise ValueError(f"Cannot base64-decode {env_var}: {exc}") from exc
            if len(key) != 32:
                raise ValueError(
                    f"{env_var} must encode exactly 32 bytes (got {len(key)})"
                )
            return key

        key_path = cls._key_path(key_id)
        if key_path.exists():
            mode = key_path.stat().st_mode & 0o777
            if mode != 0o600:
                logger.warning(
                    "Key file %s has insecure permissions %04o; expected 0600",
                    key_path,
                    mode,
                )
            return key_path.read_bytes()

        return None

    @classmethod
    def store(cls, key_id: str, key: bytes) -> None:
        """Write *key* to the file store with mode 0o600."""
        cls._DEFAULT_DIR.mkdir(parents=True, exist_ok=True)
        key_path = cls._key_path(key_id)
        key_path.write_bytes(key)
        key_path.chmod(0o600)

    @classmethod
    def generate_and_store(cls, key_id: str) -> bytes:
        """Generate a fresh 256-bit key, persist it, and return it."""
        key = os.urandom(32)
        cls.store(key_id, key)
        return key


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
        """Return the active encryption key, loading or generating it on first call."""
        if self._current_key is None:
            if self.config.key_id:
                key = KeyStore.load(self.config.key_id)
                if key is None:
                    key = KeyStore.generate_and_store(self.config.key_id)
                    logger.info(
                        "Generated and stored new encryption key '%s'",
                        self.config.key_id,
                    )
                self._current_key = key
            else:
                self._current_key = os.urandom(32)  # 256 bits
                logger.warning("Generated ephemeral encryption key - not suitable for production")

        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load an existing key from the secure key store (required for decryption)."""
        key = KeyStore.load(key_id)
        if key is None:
            raise KeyError(
                f"Encryption key '{key_id}' not found. "
                "Set CONTINUUM_KEY_<KEY_ID> env var or ensure the key file exists."
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
