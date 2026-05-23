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

_DEFAULT_KEY_DIR = Path.home() / ".continuum" / "keys"


class SecureKeyStore:
    """
    File-based secure key store with environment variable support.

    Key lookup priority:
    1. Environment variable: CONTINUUM_KEY_<KEY_ID> (base64-encoded 32 bytes)
    2. Key file: <key_dir>/<key_id> (chmod 600, base64-encoded)

    The key directory defaults to ~/.continuum/keys and can be overridden
    via the CONTINUUM_KEY_STORE_DIR environment variable.
    """

    def __init__(self, key_dir: Optional[Path] = None):
        env_dir = os.environ.get("CONTINUUM_KEY_STORE_DIR")
        self.key_dir = key_dir or (Path(env_dir) if env_dir else _DEFAULT_KEY_DIR)

    def _env_var_name(self, key_id: str) -> str:
        safe = key_id.upper().replace("-", "_").replace(".", "_")
        return f"CONTINUUM_KEY_{safe}"

    def load_key(self, key_id: str) -> Optional[bytes]:
        """Load key from environment variable or key file. Returns None if not found."""
        env_value = os.environ.get(self._env_var_name(key_id))
        if env_value:
            try:
                key = base64.b64decode(env_value)
                if len(key) != 32:
                    logger.error(f"Key in env var {self._env_var_name(key_id)} must be 32 bytes (got {len(key)})")
                    return None
                return key
            except Exception:
                logger.error(f"Invalid base64 in env var {self._env_var_name(key_id)}")
                return None

        key_file = self.key_dir / key_id
        if key_file.exists():
            try:
                key = base64.b64decode(key_file.read_bytes().strip())
                if len(key) != 32:
                    logger.error(f"Key file {key_file} must contain 32 bytes (got {len(key)})")
                    return None
                return key
            except Exception:
                logger.error(f"Failed to read key file: {key_file}")
                return None

        return None

    def store_key(self, key_id: str, key: bytes) -> None:
        """Persist a 32-byte key to a mode-600 key file."""
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")
        self.key_dir.mkdir(parents=True, exist_ok=True)
        key_file = self.key_dir / key_id
        key_file.write_bytes(base64.b64encode(key))
        key_file.chmod(0o600)
        logger.info(f"Stored key '{key_id}' in {key_file}")

    def key_exists(self, key_id: str) -> bool:
        """Return True if the key is available in the store or environment."""
        return (
            os.environ.get(self._env_var_name(key_id)) is not None
            or (self.key_dir / key_id).exists()
        )


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

    def __init__(self, config: EncryptionConfig, key_store: Optional[SecureKeyStore] = None):
        self.config = config
        self._current_key: Optional[bytes] = None
        self._key_store = key_store or SecureKeyStore()

    def _get_key(self) -> bytes:
        """Get encryption key from secure key store, or generate and persist an ephemeral one."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)
                logger.warning("Generated ephemeral encryption key - not suitable for production")
        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from the secure key store, generating and persisting one if absent."""
        key = self._key_store.load_key(key_id)
        if key is not None:
            logger.debug(f"Loaded key '{key_id}' from key store")
            return key

        # Key not found: generate a new one and persist it so future calls succeed.
        logger.warning(f"Key '{key_id}' not found in store — generating new 256-bit key")
        key = os.urandom(32)
        try:
            self._key_store.store_key(key_id, key)
        except OSError as e:
            logger.error(f"Could not persist key '{key_id}': {e}. Key will be lost on restart.")
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
