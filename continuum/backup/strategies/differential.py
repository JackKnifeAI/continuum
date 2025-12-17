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
Differential Backup Strategy

Backs up all changes since the last FULL backup.
Scheduled daily. Balance between full and incremental.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base import BackupStrategyBase

logger = logging.getLogger(__name__)


class DifferentialBackupStrategy(BackupStrategyBase):
    """
    Differential backup strategy.

    Backs up all changes since the last FULL backup.
    - Medium storage usage
    - Medium execution time
    - Faster restore than incremental chain

    Pros:
    - Only need full + one differential to restore
    - Faster restore than incremental chain
    - Simpler than incremental chain

    Cons:
    - Larger than incremental
    - Still depends on base full backup
    """

    def __init__(self):
        self._base_full_backup_id: Optional[str] = None

    async def execute(
        self,
        db_path: Path,
        tables: Optional[List[str]] = None,
        temp_dir: Optional[Path] = None,
    ) -> bytes:
        """
        Create differential backup.

        Args:
            db_path: Path to database file
            tables: Optional list of tables to backup
            temp_dir: Temporary directory for staging

        Returns:
            Differential changes as JSON bytes
        """
        logger.info(f"Creating differential backup of {db_path}")

        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Get last full backup timestamp
        last_full_backup_time = await self._get_last_full_backup_time(db_path)
        logger.info(f"Last full backup: {last_full_backup_time}")

        # Extract all changes since last full backup
        changes = await self._extract_changes(db_path, last_full_backup_time, tables)

        # Serialize changes
        backup_data = json.dumps(changes, indent=2, default=str).encode('utf-8')

        logger.info(
            f"Differential backup created: {len(changes)} changes, {len(backup_data)} bytes"
        )
        return backup_data

    async def _get_last_full_backup_time(self, db_path: Path) -> datetime:
        """
        Get timestamp of last FULL backup.

        This should be retrieved from metadata store.
        """
        # TODO: Retrieve from metadata store
        # For now, backup last 24 hours
        from datetime import timedelta
        return datetime.utcnow() - timedelta(hours=24)

    async def _extract_changes(
        self,
        db_path: Path,
        since: datetime,
        tables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Extract database changes since timestamp.

        Same logic as incremental, but since last FULL backup.
        """

        def _query_changes():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            changes = {
                'timestamp': datetime.utcnow().isoformat(),
                'since': since.isoformat(),
                'base_backup_type': 'full',
                'tables': {},
            }

            # Get list of tables to backup
            if tables:
                table_list = tables
            else:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%'"
                )
                table_list = [row[0] for row in cursor.fetchall()]

            # Extract changes from each table
            for table in table_list:
                # Check if table has updated_at column
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]

                if 'updated_at' not in columns:
                    logger.warning(f"Table {table} has no updated_at column, skipping")
                    continue

                # Get changed rows since last full backup
                cursor.execute(
                    f"SELECT * FROM {table} WHERE updated_at > ?",
                    (since.isoformat(),)
                )

                rows = []
                for row in cursor.fetchall():
                    rows.append(dict(row))

                if rows:
                    changes['tables'][table] = {
                        'rows': rows,
                        'count': len(rows),
                    }
                    logger.info(f"Table {table}: {len(rows)} changed rows")

            conn.close()
            return changes

        return await asyncio.to_thread(_query_changes)

    def get_base_backup_id(self) -> Optional[str]:
        """Get base full backup ID"""
        return self._base_full_backup_id

    def supports_pitr(self) -> bool:
        """Differential backups support limited PITR"""
        return True

    def set_base_backup(self, backup_id: str):
        """Set the base full backup for this differential"""
        self._base_full_backup_id = backup_id

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
