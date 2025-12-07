#!/usr/bin/env python3
"""
Storage Backends

Multiple storage backend support for backup redundancy.
"""

from .base import StorageBackendBase
from .local import LocalStorageBackend
from .s3 import S3StorageBackend
from .gcs import GCSStorageBackend
from .azure import AzureStorageBackend
from .multi import MultiDestinationStorage

from ..types import StorageBackend, StorageConfig


def get_storage_backend(config: StorageConfig) -> StorageBackendBase:
    """
    Get storage backend implementation.

    Args:
        config: Storage configuration

    Returns:
        StorageBackendBase implementation
    """
    backends = {
        StorageBackend.LOCAL: LocalStorageBackend,
        StorageBackend.S3: S3StorageBackend,
        StorageBackend.GCS: GCSStorageBackend,
        StorageBackend.AZURE: AzureStorageBackend,
        StorageBackend.MULTI: MultiDestinationStorage,
    }

    backend_class = backends.get(config.backend)
    if not backend_class:
        raise ValueError(f"Unknown storage backend: {config.backend}")

    return backend_class(config)


__all__ = [
    'StorageBackendBase',
    'LocalStorageBackend',
    'S3StorageBackend',
    'GCSStorageBackend',
    'AzureStorageBackend',
    'MultiDestinationStorage',
    'get_storage_backend',
]
