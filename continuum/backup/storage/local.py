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
Local Filesystem Storage Backend

Stores backups on local filesystem.
Simple, fast, but limited to single machine.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List

from .base import StorageBackendBase
from ..types import BackupMetadata, StorageConfig

logger = logging.getLogger(__name__)


class LocalStorageBackend(StorageBackendBase):
    """
    Local filesystem storage backend.

    Stores backups in a local directory with organized structure:
    backups/
      ├── full/
      ├── incremental/
      ├── differential/
      └── continuous/
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not config.local_path:
            raise ValueError("local_path required for LocalStorageBackend")

        self.base_path = config.local_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_backup_path(self, backup_id: str, metadata: Optional[BackupMetadata] = None) -> Path:
        """Get full path for backup file"""
        # Organize by strategy if metadata available
        if metadata:
            strategy_dir = self.base_path / metadata.strategy.value
            strategy_dir.mkdir(exist_ok=True)
            return strategy_dir / f"{backup_id}.backup"
        else:
            # Search all strategy directories
            for strategy in ['full', 'incremental', 'differential', 'continuous']:
                path = self.base_path / strategy / f"{backup_id}.backup"
                if path.exists():
                    return path
            # Default location
            return self.base_path / f"{backup_id}.backup"

    async def upload(
        self,
        backup_id: str,
        data: bytes,
        metadata: BackupMetadata,
    ) -> str:
        """Upload backup to local filesystem"""
        backup_path = self._get_backup_path(backup_id, metadata)

        logger.info(f"Writing backup to {backup_path}")

        def _write():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, 'wb') as f:
                f.write(data)

        await asyncio.to_thread(_write)

        logger.info(f"Backup written: {backup_path} ({len(data)} bytes)")
        return str(backup_path)

    async def download(
        self,
        backup_id: str,
    ) -> bytes:
        """Download backup from local filesystem"""
        backup_path = self._get_backup_path(backup_id)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        logger.info(f"Reading backup from {backup_path}")

        def _read():
            with open(backup_path, 'rb') as f:
                return f.read()

        data = await asyncio.to_thread(_read)

        logger.info(f"Backup read: {backup_path} ({len(data)} bytes)")
        return data

    async def delete(
        self,
        backup_id: str,
    ) -> bool:
        """Delete backup from local filesystem"""
        backup_path = self._get_backup_path(backup_id)

        if not backup_path.exists():
            logger.warning(f"Backup not found for deletion: {backup_id}")
            return False

        logger.info(f"Deleting backup: {backup_path}")

        def _delete():
            backup_path.unlink()

        await asyncio.to_thread(_delete)

        logger.info(f"Backup deleted: {backup_path}")
        return True

    async def exists(
        self,
        backup_id: str,
    ) -> bool:
        """Check if backup exists"""
        backup_path = self._get_backup_path(backup_id)
        return backup_path.exists()

    async def list_backups(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """List all backups in local storage"""

        def _list():
            backups = []
            for backup_file in self.base_path.rglob("*.backup"):
                backup_id = backup_file.stem
                if prefix is None or backup_id.startswith(prefix):
                    backups.append(backup_id)
            return backups

        return await asyncio.to_thread(_list)

    async def get_size(
        self,
        backup_id: str,
    ) -> int:
        """Get backup file size"""
        backup_path = self._get_backup_path(backup_id)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        return backup_path.stat().st_size

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
