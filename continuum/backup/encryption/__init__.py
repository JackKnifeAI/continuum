#!/usr/bin/env python3
"""
Encryption Handlers

AES-256-GCM encryption with optional KMS integration.
"""

from .aes import AESEncryptionHandler
from .kms import KMSEncryptionHandler
from ..types import EncryptionConfig


def get_encryption_handler(config: EncryptionConfig):
    """
    Get encryption handler based on configuration.

    Args:
        config: Encryption configuration

    Returns:
        Encryption handler instance
    """
    if not config.enabled:
        from .none import NoEncryptionHandler
        return NoEncryptionHandler()

    if config.use_kms:
        return KMSEncryptionHandler(config)
    else:
        return AESEncryptionHandler(config)


__all__ = [
    'AESEncryptionHandler',
    'KMSEncryptionHandler',
    'get_encryption_handler',
]
