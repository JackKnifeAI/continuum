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
Continuous Backup Strategy

Real-time Change Data Capture (CDC) for sub-minute RPO.
Streams changes as they happen.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncIterator

from .base import BackupStrategyBase

logger = logging.getLogger(__name__)


class ContinuousBackupStrategy(BackupStrategyBase):
    """
    Continuous backup strategy using Change Data Capture (CDC).

    Captures and replicates changes in near real-time.
    - Sub-minute RPO
    - Streaming replication
    - Minimal lag

    Implementation approaches:
    1. SQLite triggers to capture changes
    2. Write-Ahead Log (WAL) monitoring
    3. Polling for changes (simplest)

    For now, we implement polling-based CDC.

    Pros:
    - Near real-time replication
    - Sub-minute RPO achievable
    - Continuous protection

    Cons:
    - More complex
    - Resource overhead
    - Requires always-on process
    """

    def __init__(self, batch_size: int = 100, batch_interval: int = 60):
        """
        Initialize continuous backup strategy.

        Args:
            batch_size: Maximum changes per batch
            batch_interval: Seconds between batches
        """
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self._running = False
        self._last_timestamp: Optional[datetime] = None

    async def execute(
        self,
        db_path: Path,
        tables: Optional[List[str]] = None,
        temp_dir: Optional[Path] = None,
    ) -> bytes:
        """
        Create a single continuous backup batch.

        This captures changes since last execution.

        Args:
            db_path: Path to database file
            tables: Optional list of tables to monitor
            temp_dir: Temporary directory for staging

        Returns:
            Batch of changes as JSON bytes
        """
        logger.info(f"Creating continuous backup batch from {db_path}")

        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Get last batch timestamp
        if self._last_timestamp is None:
            # First batch - get recent changes
            from datetime import timedelta
            self._last_timestamp = datetime.utcnow() - timedelta(minutes=1)

        # Extract changes since last batch
        changes = await self._extract_batch(db_path, self._last_timestamp, tables)

        # Update timestamp for next batch
        self._last_timestamp = datetime.utcnow()

        # Serialize changes
        backup_data = json.dumps(changes, indent=2, default=str).encode('utf-8')

        logger.info(f"Continuous batch created: {len(backup_data)} bytes")
        return backup_data

    async def stream_changes(
        self,
        db_path: Path,
        tables: Optional[List[str]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream continuous changes.

        Yields batches of changes at regular intervals.

        Args:
            db_path: Path to database file
            tables: Optional list of tables to monitor

        Yields:
            Batches of changes
        """
        self._running = True
        self._last_timestamp = datetime.utcnow()

        logger.info("Starting continuous backup stream")

        try:
            while self._running:
                # Wait for batch interval
                await asyncio.sleep(self.batch_interval)

                # Extract changes
                changes = await self._extract_batch(db_path, self._last_timestamp, tables)

                if changes['tables']:
                    logger.info(f"Streaming batch with {len(changes['tables'])} tables")
                    yield changes

                # Update timestamp
                self._last_timestamp = datetime.utcnow()

        except Exception as e:
            logger.error(f"Continuous backup stream error: {e}")
            raise
        finally:
            self._running = False
            logger.info("Continuous backup stream stopped")

    def stop_stream(self):
        """Stop the continuous backup stream"""
        self._running = False

    async def _extract_batch(
        self,
        db_path: Path,
        since: datetime,
        tables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Extract a batch of changes.

        This is similar to incremental but optimized for frequent execution.
        """
        import sqlite3

        def _query_batch():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            batch = {
                'timestamp': datetime.utcnow().isoformat(),
                'since': since.isoformat(),
                'batch_size_limit': self.batch_size,
                'tables': {},
            }

            # Get list of tables to monitor
            if tables:
                table_list = tables
            else:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%'"
                )
                table_list = [row[0] for row in cursor.fetchall()]

            total_changes = 0

            # Extract changes from each table
            for table in table_list:
                if total_changes >= self.batch_size:
                    break

                # Check if table has updated_at column
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]

                if 'updated_at' not in columns:
                    continue

                # Get changed rows (limited by batch size)
                remaining = self.batch_size - total_changes
                cursor.execute(
                    f"SELECT * FROM {table} WHERE updated_at > ? LIMIT ?",
                    (since.isoformat(), remaining)
                )

                rows = []
                for row in cursor.fetchall():
                    rows.append(dict(row))

                if rows:
                    batch['tables'][table] = {
                        'rows': rows,
                        'count': len(rows),
                    }
                    total_changes += len(rows)

            batch['total_changes'] = total_changes
            conn.close()
            return batch

        return await asyncio.to_thread(_query_batch)

    def get_base_backup_id(self) -> Optional[str]:
        """Continuous backups reference the latest full backup"""
        # TODO: Track base backup
        return None

    def supports_pitr(self) -> bool:
        """Continuous backups fully support PITR"""
        return True

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
