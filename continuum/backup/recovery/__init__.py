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
Recovery Procedures

Point-in-time recovery, full restore, and selective restore capabilities.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..types import BackupConfig, BackupMetadata, RestoreResult, RestoreStatus, RestoreTarget

logger = logging.getLogger(__name__)


async def full_restore(
    backup_id: str,
    metadata: BackupMetadata,
    target: RestoreTarget,
    config: BackupConfig,
) -> RestoreResult:
    """
    Perform full restore from backup.

    Args:
        backup_id: Backup to restore
        metadata: Backup metadata
        target: Restore target configuration
        config: Backup configuration

    Returns:
        RestoreResult with status
    """
    logger.info(f"Starting full restore: {backup_id}")

    result = RestoreResult(
        success=False,
        status=RestoreStatus.PENDING,
    )

    try:
        # Download backup
        result.status = RestoreStatus.DOWNLOADING
        from ..storage import get_storage_backend
        storage = get_storage_backend(config.primary_storage)
        backup_data = await storage.download(backup_id)

        result.bytes_restored = len(backup_data)
        logger.info(f"Downloaded {len(backup_data)} bytes")

        # Decrypt if encrypted
        if metadata.encrypted:
            result.status = RestoreStatus.DECRYPTING
            from ..encryption import get_encryption_handler
            encryption = get_encryption_handler(config.encryption)
            backup_data = await encryption.decrypt(
                backup_data,
                metadata.encryption_key_id
            )
            logger.info("Backup decrypted")

        # Decompress if compressed
        if metadata.compressed:
            result.status = RestoreStatus.DECOMPRESSING
            from ..compression import get_compression_handler
            compression = get_compression_handler(metadata.compression_algorithm)
            backup_data = await compression.decompress(backup_data)
            logger.info("Backup decompressed")

        # Restore to target
        result.status = RestoreStatus.RESTORING

        if metadata.strategy.value == 'full':
            # Full backup - restore complete database
            await _restore_full_database(backup_data, target, result)
        else:
            # Incremental/differential - restore changes
            await _restore_incremental_changes(backup_data, target, result)

        # Verify if requested
        if target.verify_after_restore:
            result.status = RestoreStatus.VERIFYING
            verified = await _verify_restored_data(target)
            result.verified = verified

            if not verified:
                result.verification_errors.append("Restore verification failed")

        # Success
        result.status = RestoreStatus.COMPLETED
        result.success = True

        logger.info(f"Restore completed successfully: {backup_id}")
        return result

    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        result.status = RestoreStatus.FAILED
        result.error = str(e)
        return result


async def _restore_full_database(
    backup_data: bytes,
    target: RestoreTarget,
    result: RestoreResult,
):
    """Restore complete database from full backup"""
    if not target.database_path:
        raise ValueError("database_path required for restore")

    # Check if target exists
    if target.database_path.exists() and not target.overwrite:
        raise FileExistsError(
            f"Target database exists and overwrite=False: {target.database_path}"
        )

    # Write database file
    def _write():
        target.database_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target.database_path, 'wb') as f:
            f.write(backup_data)

    await asyncio.to_thread(_write)

    # Count records
    def _count():
        conn = sqlite3.connect(str(target.database_path))
        cursor = conn.cursor()

        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        total_records = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count

        conn.close()
        return len(tables), total_records

    tables_count, records_count = await asyncio.to_thread(_count)

    result.tables_restored = tables_count
    result.records_restored = records_count

    logger.info(f"Restored {tables_count} tables, {records_count} records")


async def _restore_incremental_changes(
    backup_data: bytes,
    target: RestoreTarget,
    result: RestoreResult,
):
    """Restore incremental/differential changes"""
    # Parse changes JSON
    changes = json.loads(backup_data.decode('utf-8'))

    if not target.database_path:
        raise ValueError("database_path required for restore")

    if not target.database_path.exists():
        raise FileNotFoundError(
            f"Base database required for incremental restore: {target.database_path}"
        )

    # Apply changes to database
    def _apply_changes():
        conn = sqlite3.connect(str(target.database_path))
        cursor = conn.cursor()

        total_records = 0

        for table_name, table_changes in changes.get('tables', {}).items():
            rows = table_changes.get('rows', [])

            for row in rows:
                # Upsert row (insert or replace)
                columns = list(row.keys())
                placeholders = ','.join(['?' for _ in columns])
                column_names = ','.join(columns)

                query = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
                values = [row[col] for col in columns]

                cursor.execute(query, values)
                total_records += 1

        conn.commit()
        conn.close()

        return total_records

    records_restored = await asyncio.to_thread(_apply_changes)

    result.records_restored = records_restored
    result.tables_restored = len(changes.get('tables', {}))

    logger.info(f"Applied {records_restored} incremental changes")


async def _verify_restored_data(target: RestoreTarget) -> bool:
    """Verify restored database integrity"""
    try:
        if not target.database_path:
            return False

        def _verify():
            conn = sqlite3.connect(str(target.database_path))
            cursor = conn.cursor()

            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            conn.close()

            return result[0] == 'ok'

        return await asyncio.to_thread(_verify)

    except Exception as e:
        logger.error(f"Restore verification failed: {e}")
        return False


async def point_in_time_restore(
    backup_id: str,
    target_time: datetime,
    target: RestoreTarget,
    config: BackupConfig,
) -> RestoreResult:
    """
    Perform point-in-time recovery (PITR).

    Restores database to exact state at specified time.

    Strategy:
    1. Find last full backup before target time
    2. Apply all incrementals up to target time
    3. Restore to target database

    Args:
        backup_id: Base backup (usually full backup)
        target_time: Time to restore to
        target: Restore target configuration
        config: Backup configuration

    Returns:
        RestoreResult with status
    """
    logger.info(f"Point-in-time restore to {target_time}")

    result = RestoreResult(
        success=False,
        status=RestoreStatus.PENDING,
    )

    try:
        from ..catalog import BackupCatalog
        from ..storage import get_storage_backend

        get_storage_backend(config.primary_storage)
        catalog = BackupCatalog(config.catalog_path)

        # 1. Find last full backup before target_time
        all_backups = await catalog.list_backups()
        full_backups = [
            b for b in all_backups
            if b.strategy.value == 'full' and b.timestamp <= target_time
        ]

        if not full_backups:
            result.error = "No full backup found before target time"
            return result

        # Sort by timestamp descending to get most recent
        full_backups.sort(key=lambda x: x.timestamp, reverse=True)
        base_backup = full_backups[0]
        logger.info(f"Base full backup: {base_backup.backup_id} ({base_backup.timestamp})")

        # 2. Find all incrementals between full backup and target_time
        incrementals = [
            b for b in all_backups
            if b.strategy.value == 'incremental'
            and base_backup.timestamp < b.timestamp <= target_time
        ]
        incrementals.sort(key=lambda x: x.timestamp)
        logger.info(f"Found {len(incrementals)} incremental backups to apply")

        # 3. Restore full backup first
        result.status = RestoreStatus.RESTORING
        base_result = await full_restore(
            base_backup.backup_id,
            base_backup,
            target,
            config
        )

        if not base_result.success:
            result.error = f"Failed to restore base backup: {base_result.error}"
            return result

        result.bytes_restored = base_result.bytes_restored

        # 4. Apply incrementals in order
        for inc in incrementals:
            logger.info(f"Applying incremental: {inc.backup_id} ({inc.timestamp})")
            inc_result = await full_restore(
                inc.backup_id,
                inc,
                target,
                config
            )
            if not inc_result.success:
                result.error = f"Failed to apply incremental {inc.backup_id}: {inc_result.error}"
                return result
            result.bytes_restored += inc_result.bytes_restored

        result.success = True
        result.status = RestoreStatus.COMPLETED
        result.timestamp = datetime.utcnow()
        logger.info(f"Point-in-time restore complete: {result.bytes_restored} bytes")

    except Exception as e:
        result.error = str(e)
        result.status = RestoreStatus.FAILED
        logger.error(f"Point-in-time restore failed: {e}")

    return result


async def selective_restore(
    backup_id: str,
    tables: list[str],
    target: RestoreTarget,
    config: BackupConfig,
) -> RestoreResult:
    """
    Selective restore of specific tables only.

    Downloads the backup, applies decryption/decompression when metadata is
    available, detects whether the payload is a full SQLite database or an
    incremental JSON changeset, then copies only the requested tables into
    the target database.

    Args:
        backup_id: Backup to restore from
        tables: List of table names to restore
        target: Restore target configuration
        config: Backup configuration

    Returns:
        RestoreResult with status
    """
    logger.info(f"Selective restore of {len(tables)} tables from backup {backup_id}")

    result = RestoreResult(
        success=False,
        status=RestoreStatus.PENDING,
    )

    try:
        # Download backup
        result.status = RestoreStatus.DOWNLOADING
        from ..storage import get_storage_backend
        storage = get_storage_backend(config.primary_storage)
        backup_data = await storage.download(backup_id)
        result.bytes_restored = len(backup_data)
        logger.info(f"Downloaded {len(backup_data)} bytes")

        # Try to load metadata for encryption/compression hints
        metadata: Optional[BackupMetadata] = None
        try:
            from ..catalog import BackupCatalog
            catalog_path = getattr(config, "catalog_path", config.metadata_db_path)
            catalog = BackupCatalog(catalog_path)
            metadata = await catalog.get_backup(backup_id)
        except Exception as meta_err:
            logger.warning(f"Could not load backup metadata, proceeding without it: {meta_err}")

        # Decrypt if encrypted
        if metadata and metadata.encrypted:
            result.status = RestoreStatus.DECRYPTING
            from ..encryption import get_encryption_handler
            encryption = get_encryption_handler(config.encryption)
            backup_data = await encryption.decrypt(backup_data, metadata.encryption_key_id)
            logger.info("Backup decrypted")

        # Decompress if compressed
        if metadata and metadata.compressed:
            result.status = RestoreStatus.DECOMPRESSING
            from ..compression import get_compression_handler
            compression = get_compression_handler(metadata.compression_algorithm)
            backup_data = await compression.decompress(backup_data)
            logger.info("Backup decompressed")

        result.status = RestoreStatus.RESTORING

        # Detect payload format: SQLite magic bytes vs JSON incremental changeset
        _SQLITE_MAGIC = b"SQLite format 3\x00"
        is_full_sqlite = backup_data[:16] == _SQLITE_MAGIC
        if metadata is not None:
            is_full_sqlite = metadata.strategy.value == "full"

        if is_full_sqlite:
            await _selective_restore_from_sqlite(backup_data, tables, target, result, config)
        else:
            await _selective_restore_from_incremental_selective(backup_data, tables, target, result)

        # Verify if requested
        if target.verify_after_restore:
            result.status = RestoreStatus.VERIFYING
            verified = await _verify_restored_data(target)
            result.verified = verified
            if not verified:
                result.verification_errors.append("Restore verification failed")

        result.status = RestoreStatus.COMPLETED
        result.success = True
        logger.info(
            f"Selective restore complete: {result.tables_restored} tables, "
            f"{result.records_restored} records"
        )

    except Exception as e:
        logger.error(f"Selective restore failed: {e}", exc_info=True)
        result.status = RestoreStatus.FAILED
        result.error = str(e)

    return result


async def _selective_restore_from_sqlite(
    backup_data: bytes,
    tables: list[str],
    target: RestoreTarget,
    result: RestoreResult,
    config: BackupConfig,
):
    """Copy specific tables from a full SQLite backup into the target database."""
    if not target.database_path:
        raise ValueError("database_path required for selective restore")

    temp_path = config.temp_dir / f"selective_{datetime.utcnow().strftime('%Y%m%d_%H%M%S%f')}.db"

    def _extract() -> tuple[int, int]:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(backup_data)

        src_conn = sqlite3.connect(str(temp_path))
        target.database_path.parent.mkdir(parents=True, exist_ok=True)
        dst_conn = sqlite3.connect(str(target.database_path))

        src_cur = src_conn.cursor()
        dst_cur = dst_conn.cursor()

        tables_restored = 0
        total_records = 0

        try:
            for table_name in tables:
                src_cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                if not src_cur.fetchone():
                    logger.warning(f"Table '{table_name}' not found in backup, skipping")
                    continue

                # Fetch CREATE statement from source
                src_cur.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                row = src_cur.fetchone()
                if not row or not row[0]:
                    logger.warning(f"No CREATE statement for '{table_name}', skipping")
                    continue
                create_sql: str = row[0]

                if target.overwrite:
                    dst_cur.execute(f"DROP TABLE IF EXISTS [{table_name}]")
                dst_cur.execute(create_sql)

                # Bulk-copy rows
                src_cur.execute(f"SELECT * FROM [{table_name}]")
                rows = src_cur.fetchall()
                if rows:
                    placeholders = ",".join(["?" for _ in rows[0]])
                    dst_cur.executemany(
                        f"INSERT OR REPLACE INTO [{table_name}] VALUES ({placeholders})",
                        rows,
                    )

                tables_restored += 1
                total_records += len(rows)
                logger.info(f"Restored table '{table_name}': {len(rows)} records")

            dst_conn.commit()
        finally:
            src_conn.close()
            dst_conn.close()
            try:
                temp_path.unlink()
            except OSError:
                pass

        return tables_restored, total_records

    tables_count, records_count = await asyncio.to_thread(_extract)
    result.tables_restored = tables_count
    result.records_restored = records_count


async def _selective_restore_from_incremental_selective(
    backup_data: bytes,
    tables: list[str],
    target: RestoreTarget,
    result: RestoreResult,
):
    """Apply only the requested tables from an incremental JSON changeset."""
    changes = json.loads(backup_data.decode("utf-8"))

    if not target.database_path:
        raise ValueError("database_path required for selective restore")

    if not target.database_path.exists():
        raise FileNotFoundError(
            f"Base database required for incremental selective restore: {target.database_path}"
        )

    requested = set(tables)

    def _apply() -> tuple[int, int]:
        conn = sqlite3.connect(str(target.database_path))
        cursor = conn.cursor()

        tables_restored = 0
        total_records = 0

        try:
            for table_name, table_changes in changes.get("tables", {}).items():
                if table_name not in requested:
                    continue

                rows = table_changes.get("rows", [])
                for row in rows:
                    columns = list(row.keys())
                    placeholders = ",".join(["?" for _ in columns])
                    column_names = ",".join(columns)
                    cursor.execute(
                        f"INSERT OR REPLACE INTO [{table_name}] ({column_names}) VALUES ({placeholders})",
                        [row[col] for col in columns],
                    )
                    total_records += 1

                tables_restored += 1
                logger.info(f"Applied {len(rows)} incremental changes to '{table_name}'")

            conn.commit()
        finally:
            conn.close()

        return tables_restored, total_records

    tables_count, records_count = await asyncio.to_thread(_apply)
    result.tables_restored = tables_count
    result.records_restored = records_count

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
