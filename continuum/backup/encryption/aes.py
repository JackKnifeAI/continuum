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
from typing import Optional, Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)


class SecureKeyStore:
    """
    Secure key storage with multiple backends, checked in priority order:

    1. Environment variable: ``CONTINUUM_KEY_<KEY_ID>`` (hex-encoded)
    2. OS keyring (requires the ``keyring`` package)
    3. Key file at ``~/.continuum/keys/<key_id>`` with mode 0o600

    The store is intentionally read-only at load time; use ``store()`` to
    persist a newly generated key so it survives process restarts.
    """

    SERVICE_NAME = "continuum-backup"
    KEY_DIR = os.path.expanduser("~/.continuum/keys")

    @classmethod
    def load(cls, key_id: str) -> Optional[bytes]:
        """Return raw key bytes for *key_id*, or ``None`` if not found."""
        # 1. Environment variable (hex-encoded 32-byte key)
        env_var = f"CONTINUUM_KEY_{key_id.upper().replace('-', '_')}"
        env_val = os.environ.get(env_var)
        if env_val:
            try:
                return bytes.fromhex(env_val)
            except ValueError:
                logger.error(f"Env var {env_var} is not valid hex; ignoring")

        # 2. OS keyring (optional dependency)
        try:
            import keyring  # type: ignore[import-untyped]
            value = keyring.get_password(cls.SERVICE_NAME, key_id)
            if value:
                return bytes.fromhex(value)
        except ImportError:
            pass

        # 3. Key file
        key_file = os.path.join(cls.KEY_DIR, key_id)
        if os.path.exists(key_file):
            stat = os.stat(key_file)
            if stat.st_mode & 0o077:
                logger.warning(
                    f"Key file {key_file} has group/world-readable permissions "
                    "(expected 0o600) — fix with: chmod 600 %s",
                    key_file,
                )
            with open(key_file, "rb") as fh:
                return fh.read()

        return None

    @classmethod
    def store(cls, key_id: str, key_bytes: bytes) -> None:
        """Persist *key_bytes* for *key_id* using the best available backend."""
        # Prefer OS keyring so the key never touches the filesystem as plaintext
        try:
            import keyring  # type: ignore[import-untyped]
            keyring.set_password(cls.SERVICE_NAME, key_id, key_bytes.hex())
            logger.info("Key %s stored in OS keyring", key_id)
            return
        except ImportError:
            pass

        # Fallback: restricted key file
        os.makedirs(cls.KEY_DIR, mode=0o700, exist_ok=True)
        key_file = os.path.join(cls.KEY_DIR, key_id)
        with open(key_file, "wb") as fh:
            fh.write(key_bytes)
        os.chmod(key_file, 0o600)
        logger.info("Key %s stored in key file: %s", key_id, key_file)


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
        """Get or generate encryption key, persisting new keys via SecureKeyStore."""
        if self._current_key is None:
            if self.config.key_id:
                self._current_key = self._load_key(self.config.key_id)
            else:
                key = os.urandom(32)  # 256-bit ephemeral key
                logger.warning(
                    "No key_id configured — generated ephemeral encryption key. "
                    "Data encrypted with this key cannot be recovered after restart."
                )
                self._current_key = key

        return self._current_key

    def _load_key(self, key_id: str) -> bytes:
        """Load key from SecureKeyStore (env var → OS keyring → key file)."""
        key = SecureKeyStore.load(key_id)
        if key is not None:
            return key

        # No stored key found — generate and persist one for this key_id so that
        # subsequent restarts can decrypt data encrypted in this session.
        logger.warning(
            "Key '%s' not found in key store — generating a new key and persisting it. "
            "Set env var CONTINUUM_KEY_%s (hex) to supply a pre-existing key.",
            key_id,
            key_id.upper().replace("-", "_"),
        )
        new_key = os.urandom(32)
        SecureKeyStore.store(key_id, new_key)
        return new_key

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
