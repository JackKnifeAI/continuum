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
Multi-Destination Storage Backend

Writes backups to multiple storage backends for redundancy.
Ensures backups survive single-backend failures.
"""

import asyncio
import logging
from typing import Optional, List

from .base import StorageBackendBase
from ..types import BackupMetadata, StorageConfig

logger = logging.getLogger(__name__)


class MultiDestinationStorage(StorageBackendBase):
    """
    Multi-destination storage backend.

    Writes backups to multiple storage backends simultaneously:
    - Primary: S3 in us-east-1
    - Secondary: GCS in us-central1
    - Tertiary: Local filesystem

    This provides multi-cloud redundancy and protects against:
    - Cloud provider outages
    - Regional failures
    - Account issues
    - Accidental deletions

    Features:
    - Parallel uploads to all destinations
    - Configurable failure tolerance
    - Automatic retry on transient failures
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not config.destinations:
            raise ValueError("destinations required for MultiDestinationStorage")

        # Initialize all destination backends
        from . import get_storage_backend
        self.backends = [
            get_storage_backend(dest_config)
            for dest_config in config.destinations
        ]

        self.require_all_success = config.require_all_success

        logger.info(f"MultiDestinationStorage initialized with {len(self.backends)} backends")

    async def upload(
        self,
        backup_id: str,
        data: bytes,
        metadata: BackupMetadata,
    ) -> str:
        """Upload backup to all configured destinations"""
        logger.info(f"Uploading backup to {len(self.backends)} destinations")

        # Upload to all backends in parallel
        tasks = [
            backend.upload(backup_id, data, metadata)
            for backend in self.backends
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results
        successful = []
        failed = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Upload to destination {i} failed: {result}")
                failed.append((i, result))
            else:
                logger.info(f"Upload to destination {i} succeeded: {result}")
                successful.append((i, result))

        # Determine success
        if self.require_all_success:
            if failed:
                raise Exception(
                    f"Upload failed: {len(failed)}/{len(self.backends)} destinations failed"
                )
        else:
            if not successful:
                raise Exception("Upload failed: all destinations failed")

        logger.info(
            f"Upload completed: {len(successful)}/{len(self.backends)} destinations succeeded"
        )

        # Return primary destination path
        return successful[0][1] if successful else ""

    async def download(
        self,
        backup_id: str,
    ) -> bytes:
        """Download backup from first available destination"""
        logger.info(f"Downloading backup from {len(self.backends)} destinations")

        # Try each backend in order until one succeeds
        for i, backend in enumerate(self.backends):
            try:
                logger.info(f"Trying to download from destination {i}")
                data = await backend.download(backup_id)
                logger.info(f"Download from destination {i} succeeded")
                return data
            except Exception as e:
                logger.warning(f"Download from destination {i} failed: {e}")
                continue

        raise FileNotFoundError(f"Backup not found in any destination: {backup_id}")

    async def delete(
        self,
        backup_id: str,
    ) -> bool:
        """Delete backup from all destinations"""
        logger.info(f"Deleting backup from {len(self.backends)} destinations")

        # Delete from all backends in parallel
        tasks = [
            backend.delete(backup_id)
            for backend in self.backends
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes
        successful = sum(1 for r in results if r is True)

        logger.info(
            f"Delete completed: {successful}/{len(self.backends)} destinations succeeded"
        )

        return successful > 0

    async def exists(
        self,
        backup_id: str,
    ) -> bool:
        """Check if backup exists in any destination"""
        # Check all backends in parallel
        tasks = [
            backend.exists(backup_id)
            for backend in self.backends
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Return True if exists in at least one backend
        return any(r is True for r in results)

    async def list_backups(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """List backups from all destinations and merge"""
        # List from all backends in parallel
        tasks = [
            backend.list_backups(prefix)
            for backend in self.backends
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge and deduplicate
        all_backups = set()
        for result in results:
            if isinstance(result, list):
                all_backups.update(result)

        return sorted(all_backups)

    async def get_size(
        self,
        backup_id: str,
    ) -> int:
        """Get backup size from first available destination"""
        for backend in self.backends:
            try:
                return await backend.get_size(backup_id)
            except Exception:
                continue

        raise FileNotFoundError(f"Backup not found in any destination: {backup_id}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
