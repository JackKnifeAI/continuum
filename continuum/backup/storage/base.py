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
Base Storage Backend

Abstract interface for all storage backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..types import BackupMetadata, StorageConfig


class StorageBackendBase(ABC):
    """Base class for storage backends"""

    def __init__(self, config: StorageConfig):
        self.config = config

    @abstractmethod
    async def upload(
        self,
        backup_id: str,
        data: bytes,
        metadata: BackupMetadata,
    ) -> str:
        """
        Upload backup data to storage.

        Args:
            backup_id: Unique backup identifier
            data: Backup data to upload
            metadata: Backup metadata

        Returns:
            Storage path where backup was uploaded
        """
        pass

    @abstractmethod
    async def download(
        self,
        backup_id: str,
    ) -> bytes:
        """
        Download backup data from storage.

        Args:
            backup_id: Unique backup identifier

        Returns:
            Backup data
        """
        pass

    @abstractmethod
    async def delete(
        self,
        backup_id: str,
    ) -> bool:
        """
        Delete backup from storage.

        Args:
            backup_id: Unique backup identifier

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def exists(
        self,
        backup_id: str,
    ) -> bool:
        """
        Check if backup exists in storage.

        Args:
            backup_id: Unique backup identifier

        Returns:
            True if backup exists
        """
        pass

    @abstractmethod
    async def list_backups(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """
        List all backups in storage.

        Args:
            prefix: Optional prefix to filter backups

        Returns:
            List of backup IDs
        """
        pass

    @abstractmethod
    async def get_size(
        self,
        backup_id: str,
    ) -> int:
        """
        Get size of backup in bytes.

        Args:
            backup_id: Unique backup identifier

        Returns:
            Size in bytes
        """
        pass

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
