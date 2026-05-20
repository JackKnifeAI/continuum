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
from typing import Optional, Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)

# Default filesystem key store; override with CONTINUUM_KEY_STORE_DIR env var
_DEFAULT_KEY_STORE_DIR = Path.home() / ".continuum" / "keys"


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
        """Get or generate encryption key"""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)  # 256 bits
                logger.warning("Generated ephemeral encryption key - not suitable for production")

        return self._current_key

    def _key_store_dir(self) -> Path:
        """Return the key store directory, respecting CONTINUUM_KEY_STORE_DIR override"""
        env_dir = os.environ.get("CONTINUUM_KEY_STORE_DIR")
        return Path(env_dir) if env_dir else _DEFAULT_KEY_STORE_DIR

    def _load_key(self, key_id: str) -> bytes:
        """Load a 32-byte AES-256 key from the secure key store.

        Lookup order:
        1. Environment variable ``CONTINUUM_KEY_<KEY_ID>`` (hex-encoded, good for CI/CD).
        2. Filesystem key store at ``<key_store_dir>/<key_id>.key`` (owner-read-only).

        Raises KeyError if the key cannot be found by either method.
        """
        # 1. Environment variable (highest priority — supports secrets injection)
        env_var = f"CONTINUUM_KEY_{key_id.upper().replace('-', '_').replace('.', '_')}"
        env_val = os.environ.get(env_var)
        if env_val:
            try:
                key_bytes = bytes.fromhex(env_val)
                if len(key_bytes) == 32:
                    logger.debug(f"Loaded encryption key '{key_id}' from env var {env_var}")
                    return key_bytes
                logger.warning(f"Key from {env_var} is not 32 bytes ({len(key_bytes)}), ignoring")
            except ValueError:
                logger.warning(f"Key from {env_var} is not valid hex, ignoring")

        # 2. Filesystem key store with permission check
        key_file = self._key_store_dir() / f"{key_id}.key"
        if key_file.exists():
            mode = key_file.stat().st_mode & 0o777
            if mode & 0o077:
                # Key is readable/writable by group or others — warn but still load
                logger.warning(
                    f"Key file {key_file} has insecure permissions {oct(mode)}; "
                    f"fix with: chmod 600 {key_file}"
                )
            key_data = key_file.read_bytes()
            if len(key_data) == 32:
                logger.debug(f"Loaded encryption key '{key_id}' from {key_file}")
                return key_data
            logger.warning(f"Key file {key_file} is not 32 bytes ({len(key_data)}), ignoring")

        raise KeyError(
            f"Encryption key '{key_id}' not found. "
            f"Options: set env var {env_var} (hex-encoded 32 bytes), "
            f"or create key file at {key_file}. "
            f"Generate a key with: python -c \"import os; print(os.urandom(32).hex())\""
        )

    def save_key(self, key_id: str, key: bytes) -> Path:
        """Persist a 32-byte key to the filesystem key store with owner-only permissions."""
        if len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes for AES-256, got {len(key)}")

        key_dir = self._key_store_dir()
        key_dir.mkdir(parents=True, exist_ok=True)
        key_dir.chmod(0o700)

        key_file = key_dir / f"{key_id}.key"
        key_file.write_bytes(key)
        key_file.chmod(0o600)

        logger.info(f"Saved encryption key '{key_id}' to {key_file}")
        return key_file

    def generate_key(self, key_id: Optional[str] = None) -> tuple[str, Path]:
        """Generate a new AES-256 key, persist it to the key store, and activate it."""
        key_id = key_id or self.config.key_id or f"continuum-{os.urandom(4).hex()}"
        key = os.urandom(32)
        key_file = self.save_key(key_id, key)
        self._current_key = key
        logger.info(f"Generated new encryption key '{key_id}'")
        return key_id, key_file

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
