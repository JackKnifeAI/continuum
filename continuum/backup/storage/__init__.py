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

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
