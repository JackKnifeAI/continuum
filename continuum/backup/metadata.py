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
Backup Metadata Store

SQLite-based storage for backup metadata and history.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from .types import (
    BackupMetadata,
    BackupStrategy,
    BackupStatus,
    StorageBackend,
    CompressionAlgorithm,
)

logger = logging.getLogger(__name__)


class MetadataStore:
    """
    Backup metadata storage.

    Stores backup metadata in SQLite database:
    - Backup details and status
    - Storage locations
    - Checksums and verification status
    - Dependencies (for incremental backups)
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize metadata database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                backup_id TEXT PRIMARY KEY,
                strategy TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,

                original_size_bytes INTEGER DEFAULT 0,
                compressed_size_bytes INTEGER DEFAULT 0,

                tables TEXT,
                record_count INTEGER DEFAULT 0,

                storage_backend TEXT,
                storage_path TEXT,

                encrypted INTEGER DEFAULT 0,
                encryption_key_id TEXT,

                compressed INTEGER DEFAULT 0,
                compression_algorithm TEXT,
                compression_ratio REAL,

                checksum_sha256 TEXT,
                verified INTEGER DEFAULT 0,
                verified_at TEXT,

                base_backup_id TEXT,

                tenant_id TEXT DEFAULT 'default',
                instance_id TEXT,
                tags TEXT,

                FOREIGN KEY (base_backup_id) REFERENCES backups(backup_id)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON backups(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy ON backups(strategy)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON backups(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant ON backups(tenant_id)')

        conn.commit()
        conn.close()

    def save_metadata(self, metadata: BackupMetadata):
        """Save or update backup metadata"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO backups (
                backup_id, strategy, status, created_at, completed_at,
                original_size_bytes, compressed_size_bytes,
                tables, record_count,
                storage_backend, storage_path,
                encrypted, encryption_key_id,
                compressed, compression_algorithm, compression_ratio,
                checksum_sha256, verified, verified_at,
                base_backup_id,
                tenant_id, instance_id, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata.backup_id,
            metadata.strategy.value,
            metadata.status.value,
            metadata.created_at.isoformat(),
            metadata.completed_at.isoformat() if metadata.completed_at else None,
            metadata.original_size_bytes,
            metadata.compressed_size_bytes,
            json.dumps(metadata.tables),
            metadata.record_count,
            metadata.storage_backend.value if metadata.storage_backend else None,
            metadata.storage_path,
            1 if metadata.encrypted else 0,
            metadata.encryption_key_id,
            1 if metadata.compressed else 0,
            metadata.compression_algorithm.value if metadata.compression_algorithm else None,
            metadata.compression_ratio,
            metadata.checksum_sha256,
            1 if metadata.verified else 0,
            metadata.verified_at.isoformat() if metadata.verified_at else None,
            metadata.base_backup_id,
            metadata.tenant_id,
            metadata.instance_id,
            json.dumps(metadata.tags),
        ))

        conn.commit()
        conn.close()

        logger.debug(f"Saved metadata for backup: {metadata.backup_id}")

    def get_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get backup metadata by ID"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM backups WHERE backup_id = ?', (backup_id,))
        row = cursor.fetchone()

        conn.close()

        if not row:
            return None

        return self._row_to_metadata(row)

    def list_backups(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy: Optional[BackupStrategy] = None,
        verified_only: bool = False,
        tenant_id: Optional[str] = None,
    ) -> List[BackupMetadata]:
        """List backups with optional filters"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM backups WHERE 1=1'
        params = []

        if start_date:
            query += ' AND created_at >= ?'
            params.append(start_date.isoformat())

        if end_date:
            query += ' AND created_at <= ?'
            params.append(end_date.isoformat())

        if strategy:
            query += ' AND strategy = ?'
            params.append(strategy.value)

        if verified_only:
            query += ' AND verified = 1'

        if tenant_id:
            query += ' AND tenant_id = ?'
            params.append(tenant_id)

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        return [self._row_to_metadata(row) for row in rows]

    def delete_metadata(self, backup_id: str):
        """Delete backup metadata"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('DELETE FROM backups WHERE backup_id = ?', (backup_id,))

        conn.commit()
        conn.close()

        logger.debug(f"Deleted metadata for backup: {backup_id}")

    def _row_to_metadata(self, row: sqlite3.Row) -> BackupMetadata:
        """Convert database row to BackupMetadata"""
        return BackupMetadata(
            backup_id=row['backup_id'],
            strategy=BackupStrategy(row['strategy']),
            status=BackupStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            original_size_bytes=row['original_size_bytes'],
            compressed_size_bytes=row['compressed_size_bytes'],
            tables=json.loads(row['tables']) if row['tables'] else [],
            record_count=row['record_count'],
            storage_backend=StorageBackend(row['storage_backend']) if row['storage_backend'] else StorageBackend.LOCAL,
            storage_path=row['storage_path'],
            encrypted=bool(row['encrypted']),
            encryption_key_id=row['encryption_key_id'],
            compressed=bool(row['compressed']),
            compression_algorithm=CompressionAlgorithm(row['compression_algorithm']) if row['compression_algorithm'] else None,
            compression_ratio=row['compression_ratio'],
            checksum_sha256=row['checksum_sha256'],
            verified=bool(row['verified']),
            verified_at=datetime.fromisoformat(row['verified_at']) if row['verified_at'] else None,
            base_backup_id=row['base_backup_id'],
            tenant_id=row['tenant_id'],
            instance_id=row['instance_id'],
            tags=json.loads(row['tags']) if row['tags'] else {},
        )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
