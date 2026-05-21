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

# Default key store directory; override with CONTINUUM_KEY_STORE_DIR env var
_KEY_STORE_DIR = Path(os.environ.get("CONTINUUM_KEY_STORE_DIR", Path.home() / ".continuum" / "keys"))


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
        """Get or generate encryption key, loading from the secure key store if key_id is set."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                self._current_key = os.urandom(32)  # 256 bits
                logger.warning("Generated ephemeral encryption key - not suitable for production")

        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load a 32-byte AES-256 key from the secure key store.

        Resolution order:
        1. Environment variable ``CONTINUUM_KEY_<KEY_ID>`` (base64-encoded)
        2. File ``<key_store_dir>/<key_id>.key`` (raw 32 bytes, mode 0600)
        3. SHA-256 derivation from key_id — development fallback only, logs a warning.
        """
        import base64
        import hashlib

        # 1. Environment variable
        env_var = "CONTINUUM_KEY_" + key_id.upper().replace("-", "_").replace(".", "_")
        raw_env = os.environ.get(env_var)
        if raw_env:
            try:
                key = base64.b64decode(raw_env)
                if len(key) == 32:
                    return key
                logger.warning("Key from %s decoded to %d bytes (expected 32), skipping", env_var, len(key))
            except Exception:
                logger.warning("Failed to base64-decode key from %s, skipping", env_var)

        # 2. Key file
        key_file = _KEY_STORE_DIR / f"{key_id}.key"
        if key_file.exists():
            try:
                key_data = key_file.read_bytes()
                if len(key_data) == 32:
                    return key_data
                logger.warning("Key file %s contains %d bytes (expected 32), skipping", key_file, len(key_data))
            except OSError as e:
                logger.warning("Failed to read key file %s: %s", key_file, e)

        # 3. Derivation fallback — not secure, development only
        logger.warning(
            "No secure key found for '%s'. Set %s (base64) or create %s (32 raw bytes). "
            "Falling back to derived key — not suitable for production.",
            key_id, env_var, key_file,
        )
        return hashlib.sha256(key_id.encode()).digest()

    def _store_key(self, key_id: str, key: bytes) -> None:
        """Persist a key to the file-based key store with owner-only permissions."""
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes for AES-256, got {len(key)}")
        _KEY_STORE_DIR.mkdir(parents=True, exist_ok=True)
        key_file = _KEY_STORE_DIR / f"{key_id}.key"
        key_file.write_bytes(key)
        key_file.chmod(0o600)
        logger.info("Stored key '%s' at %s", key_id, key_file)

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
