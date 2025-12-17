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

"""Encryption at rest configuration and utilities."""

from typing import Dict, Any


class EncryptionAtRest:
    """
    Configuration for encryption at rest.

    Implements:
    - Database encryption (PostgreSQL, SQLite)
    - File system encryption
    - Object storage encryption (S3)
    """

    @staticmethod
    def get_postgres_config() -> Dict[str, Any]:
        """
        PostgreSQL encryption at rest configuration.

        Use:
        - Transparent Data Encryption (TDE) for PostgreSQL
        - pg_crypto extension for column-level encryption
        - SSL/TLS for connections
        """
        return {
            "ssl_mode": "require",
            "ssl_cert": "/path/to/client-cert.pem",
            "ssl_key": "/path/to/client-key.pem",
            "ssl_root_cert": "/path/to/server-ca.pem",
            "application_name": "continuum-compliance",
            # Enable pg_crypto extension
            "extensions": ["pgcrypto"],
        }

    @staticmethod
    def get_s3_encryption_config() -> Dict[str, Any]:
        """
        S3 encryption at rest configuration.

        Options:
        - SSE-S3: Server-side encryption with S3-managed keys
        - SSE-KMS: Server-side encryption with AWS KMS keys (recommended)
        - SSE-C: Server-side encryption with customer-provided keys
        """
        return {
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": "arn:aws:kms:region:account:key/key-id",
            "BucketKeyEnabled": True,  # Reduce KMS costs
        }

    @staticmethod
    def get_filesystem_encryption_config() -> Dict[str, Any]:
        """
        Filesystem encryption configuration.

        Recommendations:
        - Linux: LUKS (dm-crypt)
        - Windows: BitLocker
        - macOS: FileVault
        - Cloud: Provider-managed disk encryption
        """
        return {
            "method": "LUKS",
            "cipher": "aes-xts-plain64",
            "key_size": 512,  # 512-bit for XTS mode
            "hash": "sha256",
        }


# Example PostgreSQL encrypted column setup:
"""
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create table with encrypted columns
CREATE TABLE encrypted_memories (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_encrypted BYTEA NOT NULL,  -- Encrypted content
    created_at TIMESTAMPTZ NOT NULL
);

-- Insert with encryption
INSERT INTO encrypted_memories (id, user_id, content_encrypted, created_at)
VALUES (
    gen_random_uuid(),
    'user123',
    pgp_sym_encrypt('Sensitive memory content', 'encryption_key'),
    NOW()
);

-- Query with decryption
SELECT
    id,
    user_id,
    pgp_sym_decrypt(content_encrypted, 'encryption_key') as content,
    created_at
FROM encrypted_memories
WHERE user_id = 'user123';
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
