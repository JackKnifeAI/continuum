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


class SecureKeyStore:
    """
    Manages AES encryption keys via environment variables or filesystem.

    Resolution order per key_id:
    1. Env var CONTINUUM_KEY_<KEY_ID> (base64-encoded) — good for containers/CI
    2. Env var CONTINUUM_ENCRYPTION_KEY (base64-encoded) — generic fallback
    3. Key file at key_dir/<key_id> (raw bytes, chmod 0o600)

    If none of the above resolves, a new 256-bit key is generated, persisted to
    the key directory, and a warning is logged so the operator can back it up.
    """

    _DEFAULT_KEY_DIR = Path.home() / ".continuum" / "keys"

    def __init__(self, key_dir: Optional[Path] = None):
        self._key_dir = key_dir or self._DEFAULT_KEY_DIR

    def load(self, key_id: str) -> Optional[bytes]:
        """Return the key bytes for *key_id*, or None if not found."""
        sanitized = key_id.upper().replace("-", "_").replace(".", "_")
        for env_var in (f"CONTINUUM_KEY_{sanitized}", "CONTINUUM_ENCRYPTION_KEY"):
            value = os.environ.get(env_var)
            if value:
                return base64.b64decode(value)

        key_file = self._key_dir / key_id
        if key_file.exists():
            return key_file.read_bytes()

        return None

    def store(self, key_id: str, key: bytes) -> None:
        """Persist *key* to the key directory with owner-only permissions."""
        self._key_dir.mkdir(parents=True, exist_ok=True)
        key_file = self._key_dir / key_id
        key_file.write_bytes(key)
        key_file.chmod(0o600)
        logger.info("Stored key '%s' at %s", key_id, key_file)


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
        self._key_store = key_store or SecureKeyStore()
        self._current_key: Optional[bytes] = None

    def _get_key(self) -> bytes:
        """Return the active encryption key, loading or generating it as needed."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)
                logger.warning(
                    "No key_id configured — generated ephemeral AES-256 key. "
                    "Data encrypted with this key cannot be recovered after restart."
                )
        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from the secure key store, generating and persisting one if absent."""
        key = self._key_store.load(key_id)
        if key is not None:
            if len(key) != 32:
                raise ValueError(
                    f"Key '{key_id}' is {len(key)} bytes — AES-256 requires exactly 32 bytes."
                )
            logger.debug("Loaded encryption key '%s' from secure store", key_id)
            return key

        # Key not found — generate and persist so it survives restarts
        key = os.urandom(32)
        self._key_store.store(key_id, key)
        logger.warning(
            "Encryption key '%s' not found in store — generated and persisted a new key. "
            "Back up %s to preserve access to encrypted data.",
            key_id,
            self._key_store._key_dir / key_id,
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
