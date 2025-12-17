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
Backup Manager - Central Orchestration

Coordinates backup operations, storage, encryption, and recovery.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from .types import (
    BackupStrategy,
    BackupResult,
    BackupMetadata,
    RestoreResult,
    RestoreTarget,
    VerificationResult,
    RetentionResult,
    StorageConfig,
    EncryptionConfig,
    RetentionPolicy,
    BackupSchedule,
    BackupHealth,
    BackupStatus,
    StorageBackend,
    CompressionAlgorithm,
    BackupConfig,
)

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Central backup and recovery orchestrator.

    Manages the complete lifecycle of backups:
    - Creating backups with various strategies
    - Storing to multiple destinations
    - Encrypting and compressing data
    - Verifying backup integrity
    - Restoring from backups
    - Applying retention policies
    - Monitoring and alerting
    """

    def __init__(self, config: BackupConfig):
        self.config = config
        self.config.ensure_directories()

        # Initialize components (lazy loaded)
        self._storage = None
        self._encryption = None
        self._compression = None
        self._metadata_store = None

        # Lock for preventing concurrent backups
        self._backup_lock = asyncio.Lock()

        logger.info(f"BackupManager initialized for tenant {config.tenant_id}")

    def _get_storage(self):
        """Lazy load storage backend"""
        if self._storage is None:
            from .storage import get_storage_backend
            self._storage = get_storage_backend(self.config.primary_storage)
        return self._storage

    def _get_encryption(self):
        """Lazy load encryption handler"""
        if self._encryption is None:
            from .encryption import get_encryption_handler
            self._encryption = get_encryption_handler(self.config.encryption)
        return self._encryption

    def _get_compression(self):
        """Lazy load compression handler"""
        if self._compression is None:
            from .compression import get_compression_handler
            self._compression = get_compression_handler(
                self.config.compression_algorithm
            )
        return self._compression

    def _get_metadata_store(self):
        """Lazy load metadata store"""
        if self._metadata_store is None:
            from .metadata import MetadataStore
            self._metadata_store = MetadataStore(self.config.metadata_db_path)
        return self._metadata_store

    async def create_backup(
        self,
        strategy: BackupStrategy = BackupStrategy.INCREMENTAL,
        tables: Optional[List[str]] = None,
        compress: Optional[bool] = None,
        encrypt: Optional[bool] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> BackupResult:
        """
        Create a new backup.

        Args:
            strategy: Backup strategy to use
            tables: Specific tables to backup (None = all)
            compress: Override compression setting
            encrypt: Override encryption setting
            tags: Additional metadata tags

        Returns:
            BackupResult with status and metadata
        """
        start_time = time.time()
        backup_id = self._generate_backup_id(strategy)

        logger.info(f"Starting {strategy} backup: {backup_id}")

        # Use defaults if not specified
        if compress is None:
            compress = self.config.compression_enabled
        if encrypt is None:
            encrypt = self.config.encryption.enabled

        try:
            # Ensure only one backup runs at a time
            async with self._backup_lock:
                # Create backup metadata
                metadata = BackupMetadata(
                    backup_id=backup_id,
                    strategy=strategy,
                    status=BackupStatus.IN_PROGRESS,
                    created_at=datetime.utcnow(),
                    tables=tables or [],
                    tenant_id=self.config.tenant_id,
                    encrypted=encrypt,
                    compressed=compress,
                    compression_algorithm=self.config.compression_algorithm if compress else None,
                    tags=tags or {},
                )

                # Save initial metadata
                self._get_metadata_store().save_metadata(metadata)

                # Execute backup strategy
                from .strategies import get_backup_strategy
                strategy_impl = get_backup_strategy(strategy)

                backup_data = await strategy_impl.execute(
                    db_path=self.config.db_path,
                    tables=tables,
                    temp_dir=self.config.temp_dir,
                )

                # Update metadata with backup details
                metadata.original_size_bytes = len(backup_data)
                metadata.record_count = await self._count_records(tables)

                # Compress if requested
                if compress:
                    logger.info(f"Compressing backup {backup_id}")
                    compression_handler = self._get_compression()
                    backup_data = await compression_handler.compress(backup_data)
                    metadata.compressed_size_bytes = len(backup_data)
                    metadata.compression_ratio = (
                        1 - len(backup_data) / metadata.original_size_bytes
                    )
                else:
                    metadata.compressed_size_bytes = metadata.original_size_bytes

                # Encrypt if requested
                if encrypt:
                    logger.info(f"Encrypting backup {backup_id}")
                    encryption_handler = self._get_encryption()
                    backup_data, key_id = await encryption_handler.encrypt(backup_data)
                    metadata.encryption_key_id = key_id

                # Calculate checksum
                metadata.checksum_sha256 = hashlib.sha256(backup_data).hexdigest()

                # Upload to storage
                logger.info(f"Uploading backup {backup_id}")
                storage = self._get_storage()
                storage_path = await storage.upload(
                    backup_id=backup_id,
                    data=backup_data,
                    metadata=metadata,
                )
                metadata.storage_path = storage_path
                metadata.storage_backend = self.config.primary_storage.backend

                # Upload to secondary storage if configured
                if self.config.secondary_storage:
                    logger.info(f"Uploading to secondary storage: {backup_id}")
                    from .storage import get_storage_backend
                    secondary = get_storage_backend(self.config.secondary_storage)
                    await secondary.upload(backup_id, backup_data, metadata)

                # Mark as completed
                metadata.status = BackupStatus.COMPLETED
                metadata.completed_at = datetime.utcnow()

                # Verify if requested
                if self.config.verify_after_backup:
                    logger.info(f"Verifying backup {backup_id}")
                    metadata.status = BackupStatus.VERIFYING
                    verification = await self.verify_backup(backup_id)
                    if verification.success:
                        metadata.verified = True
                        metadata.verified_at = datetime.utcnow()
                        metadata.status = BackupStatus.VERIFIED
                    else:
                        logger.error(f"Backup verification failed: {backup_id}")

                # Save final metadata
                self._get_metadata_store().save_metadata(metadata)

                duration = time.time() - start_time
                logger.info(f"Backup completed: {backup_id} in {duration:.2f}s")

                return BackupResult(
                    success=True,
                    backup_id=backup_id,
                    metadata=metadata,
                    duration_seconds=duration,
                    bytes_backed_up=metadata.original_size_bytes,
                    records_backed_up=metadata.record_count,
                    tables_backed_up=len(metadata.tables) if metadata.tables else 0,
                )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Backup failed: {backup_id}: {e}", exc_info=True)

            # Update metadata
            metadata.status = BackupStatus.FAILED
            self._get_metadata_store().save_metadata(metadata)

            return BackupResult(
                success=False,
                backup_id=backup_id,
                duration_seconds=duration,
                error=str(e),
            )

    async def restore(
        self,
        backup_id: str,
        target: RestoreTarget,
        point_in_time: Optional[datetime] = None,
    ) -> RestoreResult:
        """
        Restore from a backup.

        Args:
            backup_id: ID of backup to restore
            target: Restore target configuration
            point_in_time: Optional PITR target (for incremental backups)

        Returns:
            RestoreResult with status
        """
        start_time = time.time()
        logger.info(f"Starting restore from backup: {backup_id}")

        try:
            # Get backup metadata
            metadata = self._get_metadata_store().get_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup not found: {backup_id}")

            # Point-in-time restore if requested
            if point_in_time:
                from .recovery import point_in_time_restore
                return await point_in_time_restore(
                    backup_id=backup_id,
                    target_time=point_in_time,
                    target=target,
                    config=self.config,
                )

            # Standard restore
            from .recovery import full_restore
            result = await full_restore(
                backup_id=backup_id,
                metadata=metadata,
                target=target,
                config=self.config,
            )

            duration = time.time() - start_time
            result.duration_seconds = duration
            logger.info(f"Restore completed in {duration:.2f}s")

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Restore failed: {e}", exc_info=True)

            from .types import RestoreStatus
            return RestoreResult(
                success=False,
                status=RestoreStatus.FAILED,
                duration_seconds=duration,
                error=str(e),
            )

    async def list_backups(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy: Optional[BackupStrategy] = None,
        verified_only: bool = False,
    ) -> List[BackupMetadata]:
        """
        List available backups.

        Args:
            start_date: Filter backups after this date
            end_date: Filter backups before this date
            strategy: Filter by backup strategy
            verified_only: Only return verified backups

        Returns:
            List of backup metadata
        """
        metadata_store = self._get_metadata_store()
        backups = metadata_store.list_backups(
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            verified_only=verified_only,
        )
        return backups

    async def verify_backup(self, backup_id: str) -> VerificationResult:
        """
        Verify backup integrity.

        Args:
            backup_id: ID of backup to verify

        Returns:
            VerificationResult with status
        """
        from .verification import verify_backup
        return await verify_backup(backup_id, self.config)

    async def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.

        Args:
            backup_id: ID of backup to delete

        Returns:
            True if deleted successfully
        """
        logger.info(f"Deleting backup: {backup_id}")

        try:
            # Get metadata
            metadata = self._get_metadata_store().get_metadata(backup_id)
            if not metadata:
                logger.warning(f"Backup not found: {backup_id}")
                return False

            # Delete from storage
            storage = self._get_storage()
            await storage.delete(backup_id)

            # Delete from secondary storage if configured
            if self.config.secondary_storage:
                from .storage import get_storage_backend
                secondary = get_storage_backend(self.config.secondary_storage)
                await secondary.delete(backup_id)

            # Delete metadata
            self._get_metadata_store().delete_metadata(backup_id)

            logger.info(f"Backup deleted: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False

    async def apply_retention_policy(self) -> RetentionResult:
        """
        Apply retention policy to old backups.

        Returns:
            RetentionResult with statistics
        """
        from .retention import apply_retention_policy
        return await apply_retention_policy(self.config, self)

    async def get_health(self) -> BackupHealth:
        """
        Get backup system health status.

        Returns:
            BackupHealth with system status
        """
        from .monitoring import get_backup_health
        return await get_backup_health(self.config)

    def _generate_backup_id(self, strategy: BackupStrategy) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return f"backup-{strategy.value}-{timestamp}-{self.config.tenant_id}"

    async def _count_records(self, tables: Optional[List[str]] = None) -> int:
        """Count total records in backup"""
        # TODO: Implement actual record counting from database
        return 0

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
