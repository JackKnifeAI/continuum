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
import json
import logging
import os
import stat
from pathlib import Path
from typing import Optional, Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)

_DEFAULT_KEYSTORE_PATH = Path(os.environ.get(
    "CONTINUUM_KEYSTORE_PATH",
    Path.home() / ".continuum" / "keystore.json"
))


class SecureKeyStore:
    """
    File-based secure key store for AES encryption keys.

    Keys are stored as base64-encoded bytes in a JSON file with
    permissions restricted to the owner (0600). The store path
    defaults to ~/.continuum/keystore.json but can be overridden
    via the CONTINUUM_KEYSTORE_PATH environment variable.
    """

    def __init__(self, path: Path = _DEFAULT_KEYSTORE_PATH):
        self._path = path

    def _ensure_store(self) -> dict:
        """Load the store, creating it securely if absent."""
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._write_store({})
        # Enforce restrictive permissions on every access
        self._path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        with self._path.open("r") as fh:
            return json.load(fh)

    def _write_store(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Write with O_CREAT|O_WRONLY and mode 0600 from the start
        fd = os.open(str(self._path), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh)

    def get(self, key_id: str) -> Optional[bytes]:
        """Return the stored key for *key_id*, or None if not found."""
        store = self._ensure_store()
        encoded = store.get(key_id)
        if encoded is None:
            return None
        return base64.b64decode(encoded)

    def put(self, key_id: str, key: bytes) -> None:
        """Persist *key* under *key_id*."""
        store = self._ensure_store()
        store[key_id] = base64.b64encode(key).decode()
        self._write_store(store)

    def generate(self, key_id: str) -> bytes:
        """Generate a fresh 256-bit key, persist it, and return it."""
        key = os.urandom(32)
        self.put(key_id, key)
        logger.info("Generated and stored new AES-256 key for key_id=%r", key_id)
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
                self._current_key = os.urandom(32)  # 256-bit ephemeral key
                logger.warning("Generated ephemeral encryption key - not suitable for production")
        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from the secure key store, generating one if absent."""
        key = self._key_store.get(key_id)
        if key is None:
            logger.info("No stored key found for key_id=%r; generating a new one", key_id)
            key = self._key_store.generate(key_id)
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
