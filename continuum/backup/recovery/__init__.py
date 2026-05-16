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
import os
import sqlite3
import tempfile
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

    Args:
        backup_id: Backup to restore from
        tables: List of tables to restore
        target: Restore target configuration
        config: Backup configuration

    Returns:
        RestoreResult with status
    """
    logger.info(f"Selective restore of {len(tables)} tables from {backup_id}")

    result = RestoreResult(
        success=False,
        status=RestoreStatus.PENDING,
    )

    if not tables:
        result.error = "No tables specified for selective restore"
        return result

    if not target.database_path:
        result.error = "database_path required for selective restore"
        return result

    try:
        # Download backup
        result.status = RestoreStatus.DOWNLOADING
        from ..storage import get_storage_backend
        storage = get_storage_backend(config.primary_storage)
        backup_data = await storage.download(backup_id)
        result.bytes_restored = len(backup_data)
        logger.info(f"Downloaded {len(backup_data)} bytes")

        _SQLITE_MAGIC = b"SQLite format 3\x00"

        # Decrypt if encrypted (detect by absence of known plaintext magic)
        if (
            config.encryption.enabled
            and not backup_data.startswith(_SQLITE_MAGIC)
            and backup_data[:1] not in (b"{", b"[")
        ):
            result.status = RestoreStatus.DECRYPTING
            from ..encryption import get_encryption_handler
            encryption = get_encryption_handler(config.encryption)
            backup_data = await encryption.decrypt(backup_data, config.encryption.key_id)
            logger.info("Backup decrypted")

        # Decompress if still not recognisable plaintext
        if (
            config.compression_enabled
            and not backup_data.startswith(_SQLITE_MAGIC)
            and backup_data[:1] not in (b"{", b"[")
        ):
            result.status = RestoreStatus.DECOMPRESSING
            from ..compression import get_compression_handler
            compression = get_compression_handler(config.compression_algorithm)
            backup_data = await compression.decompress(backup_data)
            logger.info("Backup decompressed")

        # Selectively restore only the requested tables
        result.status = RestoreStatus.RESTORING
        if backup_data.startswith(_SQLITE_MAGIC):
            await _selective_restore_from_sqlite(backup_data, tables, target, result)
        else:
            await _selective_restore_from_json(backup_data, tables, target, result)

        # Verify if requested
        if target.verify_after_restore:
            result.status = RestoreStatus.VERIFYING
            verified = await _verify_restored_data(target)
            result.verified = verified
            if not verified:
                result.verification_errors.append("Selective restore verification failed")

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
) -> None:
    """Extract and restore specific tables from a full SQLite backup."""
    target.database_path.parent.mkdir(parents=True, exist_ok=True)

    def _restore() -> tuple[int, int]:
        fd, tmp_path = tempfile.mkstemp(suffix=".db")
        try:
            os.write(fd, backup_data)
            os.close(fd)

            src = sqlite3.connect(tmp_path)
            dst = sqlite3.connect(str(target.database_path))
            src_cur = src.cursor()
            dst_cur = dst.cursor()

            total_records = 0
            tables_restored = 0

            for table in tables:
                src_cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                if not src_cur.fetchone():
                    logger.warning(f"Table not found in backup, skipping: {table}")
                    continue

                dst_cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                exists_in_dst = dst_cur.fetchone() is not None

                if exists_in_dst and not target.overwrite:
                    raise FileExistsError(
                        f"Table already exists and overwrite=False: {table}"
                    )

                if exists_in_dst:
                    dst_cur.execute(f"DROP TABLE IF EXISTS {table}")

                src_cur.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                create_sql = src_cur.fetchone()[0]
                dst_cur.execute(create_sql)

                src_cur.execute(f"SELECT * FROM {table}")
                rows = src_cur.fetchall()
                if rows:
                    placeholders = ",".join(["?" for _ in range(len(rows[0]))])
                    dst_cur.executemany(
                        f"INSERT OR REPLACE INTO {table} VALUES ({placeholders})",
                        rows,
                    )

                total_records += len(rows)
                tables_restored += 1
                logger.info(f"Restored table {table}: {len(rows)} records")

            dst.commit()
            src.close()
            dst.close()
            return tables_restored, total_records
        finally:
            os.unlink(tmp_path)

    tables_restored, total_records = await asyncio.to_thread(_restore)
    result.tables_restored = tables_restored
    result.records_restored = total_records


async def _selective_restore_from_json(
    backup_data: bytes,
    tables: list[str],
    target: RestoreTarget,
    result: RestoreResult,
) -> None:
    """Apply incremental JSON changes for only the specified tables."""
    changes = json.loads(backup_data.decode("utf-8"))
    tables_set = set(tables)

    if not target.database_path.exists():
        raise FileNotFoundError(
            f"Base database required for incremental selective restore: {target.database_path}"
        )

    def _apply() -> tuple[int, int]:
        conn = sqlite3.connect(str(target.database_path))
        cursor = conn.cursor()

        total_records = 0
        tables_restored = 0

        for table_name, table_changes in changes.get("tables", {}).items():
            if table_name not in tables_set:
                continue

            rows = table_changes.get("rows", [])
            for row in rows:
                columns = list(row.keys())
                placeholders = ",".join(["?" for _ in columns])
                column_names = ",".join(columns)
                cursor.execute(
                    f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})",
                    [row[col] for col in columns],
                )
                total_records += 1

            tables_restored += 1
            logger.info(f"Applied {len(rows)} changes to table {table_name}")

        conn.commit()
        conn.close()
        return tables_restored, total_records

    tables_restored, total_records = await asyncio.to_thread(_apply)
    result.tables_restored = tables_restored
    result.records_restored = total_records

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
