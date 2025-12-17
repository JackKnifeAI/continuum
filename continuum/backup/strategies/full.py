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
Full Backup Strategy

Complete database dump with all tables and data.
Scheduled weekly. Slowest but most complete.
"""

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Optional, List

from .base import BackupStrategyBase

logger = logging.getLogger(__name__)


class FullBackupStrategy(BackupStrategyBase):
    """
    Full database backup strategy.

    Creates a complete copy of the entire database.
    - All tables included
    - All data included
    - Schema included
    - Indexes included
    - Triggers included

    Pros:
    - Complete standalone backup
    - Simple to restore
    - No dependencies

    Cons:
    - Largest size
    - Longest duration
    - Most resource intensive
    """

    async def execute(
        self,
        db_path: Path,
        tables: Optional[List[str]] = None,
        temp_dir: Optional[Path] = None,
    ) -> bytes:
        """
        Create full database backup.

        Args:
            db_path: Path to database file
            tables: Optional list of tables (ignored for SQLite, always full backup)
            temp_dir: Temporary directory for staging

        Returns:
            Complete database dump as bytes
        """
        logger.info(f"Creating full backup of {db_path}")

        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        # For SQLite, we can use the backup API or just read the file
        # Using backup API is safer for active databases
        backup_data = await self._backup_sqlite(db_path, temp_dir)

        logger.info(f"Full backup created: {len(backup_data)} bytes")
        return backup_data

    async def _backup_sqlite(self, db_path: Path, temp_dir: Optional[Path]) -> bytes:
        """
        Backup SQLite database using the backup API.

        This creates a consistent snapshot even if the database is being written to.
        """
        # Create temporary backup file
        if temp_dir:
            temp_dir.mkdir(parents=True, exist_ok=True)
            backup_file = temp_dir / f"backup_temp_{db_path.name}"
        else:
            backup_file = db_path.parent / f"backup_temp_{db_path.name}"

        try:
            # Use SQLite backup API for consistent snapshot
            source_conn = sqlite3.connect(str(db_path))
            backup_conn = sqlite3.connect(str(backup_file))

            # Perform backup (this is atomic and consistent)
            await asyncio.to_thread(source_conn.backup, backup_conn)

            source_conn.close()
            backup_conn.close()

            # Read backup file
            with open(backup_file, 'rb') as f:
                backup_data = f.read()

            return backup_data

        finally:
            # Clean up temporary file
            if backup_file.exists():
                backup_file.unlink()

    def get_base_backup_id(self) -> Optional[str]:
        """Full backups have no base backup"""
        return None

    def supports_pitr(self) -> bool:
        """Full backups don't support PITR"""
        return False

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
