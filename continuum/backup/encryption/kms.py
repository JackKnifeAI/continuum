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
KMS Encryption

Cloud Key Management Service integration for enterprise encryption.
Supports AWS KMS, Google Cloud KMS, and Azure Key Vault.
"""

import asyncio
import logging
from typing import Tuple

from ..types import EncryptionConfig

logger = logging.getLogger(__name__)


class KMSEncryptionHandler:
    """
    Cloud KMS encryption handler.

    Integrates with cloud key management services:
    - AWS KMS
    - Google Cloud KMS
    - Azure Key Vault

    Benefits:
    - Centralized key management
    - Automatic key rotation
    - Access logging and auditing
    - HSM-backed keys available
    - Compliance certifications
    """

    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.provider = config.kms_provider

        if not self.provider:
            raise ValueError("kms_provider required for KMS encryption")

        if self.provider not in ['aws', 'gcp', 'azure']:
            raise ValueError(f"Unsupported KMS provider: {self.provider}")

        self._kms_client = None

    def _get_aws_kms_client(self):
        """Get AWS KMS client"""
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 required for AWS KMS. Install with: pip install boto3") from None

        if self._kms_client is None:
            self._kms_client = boto3.client('kms', region_name=self.config.kms_region)

        return self._kms_client

    def _get_gcp_kms_client(self):
        """Get GCP KMS client"""
        try:
            from google.cloud import kms
        except ImportError:
            raise ImportError(
                "google-cloud-kms required for GCP KMS. "
                "Install with: pip install google-cloud-kms"
            ) from None

        if self._kms_client is None:
            self._kms_client = kms.KeyManagementServiceClient()

        return self._kms_client

    def _get_azure_kms_client(self):
        """Get Azure Key Vault client"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.keys.crypto import CryptographyClient
        except ImportError:
            raise ImportError(
                "azure-keyvault-keys required for Azure KMS. "
                "Install with: pip install azure-keyvault-keys azure-identity"
            ) from None

        if self._kms_client is None:
            credential = DefaultAzureCredential()
            # kms_key_id must be a full Azure Key Vault key URL:
            # https://<vault-name>.vault.azure.net/keys/<key-name>[/<key-version>]
            key_url = self.config.kms_key_id
            if not key_url or not key_url.startswith("https://"):
                raise ValueError(
                    "Azure KMS requires kms_key_id to be a full Key Vault key URL, e.g. "
                    "https://<vault-name>.vault.azure.net/keys/<key-name>/<key-version>"
                )
            self._kms_client = CryptographyClient(key_url, credential)

        return self._kms_client

    async def encrypt(self, data: bytes) -> Tuple[bytes, str]:
        """
        Encrypt data using KMS.

        Uses envelope encryption:
        1. Generate data encryption key (DEK)
        2. Encrypt data with DEK
        3. Encrypt DEK with KMS key
        4. Return encrypted data + encrypted DEK

        Args:
            data: Plaintext data to encrypt

        Returns:
            Tuple of (encrypted_data, key_id)
        """
        logger.info(f"Encrypting {len(data)} bytes with {self.provider.upper()} KMS")

        if self.provider == 'aws':
            return await self._encrypt_aws_kms(data)
        elif self.provider == 'gcp':
            return await self._encrypt_gcp_kms(data)
        elif self.provider == 'azure':
            return await self._encrypt_azure_kms(data)
        else:
            raise ValueError(f"Unsupported KMS provider: {self.provider}")

    async def decrypt(self, data: bytes, key_id: str) -> bytes:
        """
        Decrypt data using KMS.

        Reverses envelope encryption:
        1. Extract encrypted DEK
        2. Decrypt DEK with KMS
        3. Decrypt data with DEK

        Args:
            data: Encrypted data (includes encrypted DEK)
            key_id: KMS key ID

        Returns:
            Decrypted plaintext data
        """
        logger.info(f"Decrypting {len(data)} bytes with {self.provider.upper()} KMS")

        if self.provider == 'aws':
            return await self._decrypt_aws_kms(data, key_id)
        elif self.provider == 'gcp':
            return await self._decrypt_gcp_kms(data, key_id)
        elif self.provider == 'azure':
            return await self._decrypt_azure_kms(data, key_id)
        else:
            raise ValueError(f"Unsupported KMS provider: {self.provider}")

    async def _encrypt_aws_kms(self, data: bytes) -> Tuple[bytes, str]:
        """Encrypt using AWS KMS"""

        def _encrypt():
            import os

            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            # Generate data encryption key
            kms = self._get_aws_kms_client()
            response = kms.generate_data_key(
                KeyId=self.config.kms_key_id,
                KeySpec='AES_256'
            )

            # Extract plaintext DEK and encrypted DEK
            dek_plaintext = response['Plaintext']
            dek_encrypted = response['CiphertextBlob']

            # Encrypt data with DEK
            iv = os.urandom(12)
            aesgcm = AESGCM(dek_plaintext)
            ciphertext = aesgcm.encrypt(iv, data, None)

            # Format: encrypted_dek_len (4 bytes) + encrypted_dek + iv + ciphertext
            import struct
            encrypted_data = (
                struct.pack('<I', len(dek_encrypted)) +
                dek_encrypted +
                iv +
                ciphertext
            )

            return encrypted_data

        encrypted_data = await asyncio.to_thread(_encrypt)
        return encrypted_data, self.config.kms_key_id

    async def _decrypt_aws_kms(self, data: bytes, key_id: str) -> bytes:
        """Decrypt using AWS KMS"""

        def _decrypt():
            import struct

            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            # Extract encrypted DEK
            dek_len = struct.unpack('<I', data[:4])[0]
            dek_encrypted = data[4:4+dek_len]
            iv = data[4+dek_len:4+dek_len+12]
            ciphertext = data[4+dek_len+12:]

            # Decrypt DEK with KMS
            kms = self._get_aws_kms_client()
            response = kms.decrypt(CiphertextBlob=dek_encrypted)
            dek_plaintext = response['Plaintext']

            # Decrypt data with DEK
            aesgcm = AESGCM(dek_plaintext)
            plaintext = aesgcm.decrypt(iv, ciphertext, None)

            return plaintext

        return await asyncio.to_thread(_decrypt)

    async def _encrypt_gcp_kms(self, data: bytes) -> Tuple[bytes, str]:
        """Encrypt using GCP KMS with envelope encryption"""

        def _encrypt():
            import os
            import struct

            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            client = self._get_gcp_kms_client()

            # Generate local DEK
            dek = os.urandom(32)  # AES-256

            # Encrypt DEK with GCP KMS
            key_name = self.config.kms_key_id  # projects/.../locations/.../keyRings/.../cryptoKeys/...
            encrypt_response = client.encrypt(
                request={'name': key_name, 'plaintext': dek}
            )
            dek_encrypted = encrypt_response.ciphertext

            # Encrypt data with DEK
            iv = os.urandom(12)
            aesgcm = AESGCM(dek)
            ciphertext = aesgcm.encrypt(iv, data, None)

            # Format: encrypted_dek_len (4 bytes) + encrypted_dek + iv + ciphertext
            encrypted_data = (
                struct.pack('<I', len(dek_encrypted)) +
                dek_encrypted +
                iv +
                ciphertext
            )

            return encrypted_data

        encrypted_data = await asyncio.to_thread(_encrypt)
        return encrypted_data, self.config.kms_key_id

    async def _decrypt_gcp_kms(self, data: bytes, key_id: str) -> bytes:
        """Decrypt using GCP KMS"""

        def _decrypt():
            import struct

            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            client = self._get_gcp_kms_client()

            # Extract encrypted DEK
            dek_len = struct.unpack('<I', data[:4])[0]
            dek_encrypted = data[4:4+dek_len]
            iv = data[4+dek_len:4+dek_len+12]
            ciphertext = data[4+dek_len+12:]

            # Decrypt DEK with GCP KMS
            decrypt_response = client.decrypt(
                request={'name': key_id, 'ciphertext': dek_encrypted}
            )
            dek = decrypt_response.plaintext

            # Decrypt data with DEK
            aesgcm = AESGCM(dek)
            plaintext = aesgcm.decrypt(iv, ciphertext, None)

            return plaintext

        return await asyncio.to_thread(_decrypt)

    async def _encrypt_azure_kms(self, data: bytes) -> Tuple[bytes, str]:
        """Encrypt using Azure Key Vault with envelope encryption"""

        def _encrypt():
            import os
            import struct

            from azure.keyvault.keys.crypto import EncryptionAlgorithm
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            client = self._get_azure_kms_client()

            # Generate local DEK
            dek = os.urandom(32)  # AES-256

            # Encrypt DEK with Azure Key Vault
            result = client.encrypt(EncryptionAlgorithm.rsa_oaep_256, dek)
            dek_encrypted = result.ciphertext

            # Encrypt data with DEK
            iv = os.urandom(12)
            aesgcm = AESGCM(dek)
            ciphertext = aesgcm.encrypt(iv, data, None)

            # Format: encrypted_dek_len (4 bytes) + encrypted_dek + iv + ciphertext
            encrypted_data = (
                struct.pack('<I', len(dek_encrypted)) +
                dek_encrypted +
                iv +
                ciphertext
            )

            return encrypted_data

        encrypted_data = await asyncio.to_thread(_encrypt)
        return encrypted_data, self.config.kms_key_id

    async def _decrypt_azure_kms(self, data: bytes, key_id: str) -> bytes:
        """Decrypt using Azure Key Vault"""

        def _decrypt():
            import struct

            from azure.keyvault.keys.crypto import EncryptionAlgorithm
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            client = self._get_azure_kms_client()

            # Extract encrypted DEK
            dek_len = struct.unpack('<I', data[:4])[0]
            dek_encrypted = data[4:4+dek_len]
            iv = data[4+dek_len:4+dek_len+12]
            ciphertext = data[4+dek_len+12:]

            # Decrypt DEK with Azure Key Vault
            result = client.decrypt(EncryptionAlgorithm.rsa_oaep_256, dek_encrypted)
            dek = result.plaintext

            # Decrypt data with DEK
            aesgcm = AESGCM(dek)
            plaintext = aesgcm.decrypt(iv, ciphertext, None)

            return plaintext

        return await asyncio.to_thread(_decrypt)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
