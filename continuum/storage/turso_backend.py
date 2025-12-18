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
Turso Storage Backend
=====================

Edge-distributed SQLite via Turso (libSQL).

Features:
- Global edge distribution (low latency worldwide)
- SQLite compatibility (same queries work!)
- Automatic replication
- Built-in connection pooling
- Perfect for federation sync

Requires: pip install libsql-experimental
"""

import os
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .base import StorageBackend

# Try to import libsql
try:
    import libsql_experimental as libsql
    LIBSQL_AVAILABLE = True
except ImportError:
    LIBSQL_AVAILABLE = False


@dataclass
class TursoStats:
    """Track Turso connection statistics"""
    queries_executed: int = 0
    rows_read: int = 0
    rows_written: int = 0
    sync_count: int = 0
    last_sync: Optional[str] = None


class TursoBackend(StorageBackend):
    """
    Edge-distributed SQLite backend using Turso/libSQL.

    Turso provides:
    - Global edge deployment (data close to users)
    - SQLite-compatible API (drop-in replacement)
    - Automatic replication and sync
    - Embedded replicas for offline support

    Usage:
        # Cloud-only mode
        storage = TursoBackend(
            url="libsql://your-db.turso.io",
            auth_token="your-token"
        )

        # Embedded replica mode (local + cloud sync)
        storage = TursoBackend(
            url="libsql://your-db.turso.io",
            auth_token="your-token",
            local_path="./local_replica.db",
            sync_interval=60  # Sync every 60 seconds
        )

        # Use just like SQLite!
        with storage.cursor() as c:
            c.execute("SELECT * FROM memories")
            results = c.fetchall()

    π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
    """

    def __init__(
        self,
        url: Optional[str] = None,
        auth_token: Optional[str] = None,
        local_path: Optional[str] = None,
        sync_interval: int = 60,
        **kwargs
    ):
        """
        Initialize Turso backend.

        Args:
            url: Turso database URL (libsql://...) or TURSO_DATABASE_URL env var
            auth_token: Turso auth token or TURSO_AUTH_TOKEN env var
            local_path: Optional local replica path for offline support
            sync_interval: Seconds between syncs (default: 60)
        """
        if not LIBSQL_AVAILABLE:
            raise ImportError(
                "libsql-experimental not installed. Install with: "
                "pip install libsql-experimental"
            )

        self.url = url or os.getenv("TURSO_DATABASE_URL")
        self.auth_token = auth_token or os.getenv("TURSO_AUTH_TOKEN")
        self.local_path = local_path
        self.sync_interval = sync_interval

        if not self.url:
            raise ValueError(
                "Turso URL required. Set TURSO_DATABASE_URL env var or pass url parameter."
            )

        self._lock = threading.Lock()
        self._stats = TursoStats()
        self._conn = None

        self._connect()

    def _connect(self):
        """Establish connection to Turso."""
        if self.local_path:
            # Embedded replica mode: local SQLite + cloud sync
            self._conn = libsql.connect(
                self.local_path,
                sync_url=self.url,
                auth_token=self.auth_token
            )
            # Initial sync
            self._conn.sync()
            self._stats.sync_count += 1
        else:
            # Cloud-only mode
            self._conn = libsql.connect(
                self.url,
                auth_token=self.auth_token
            )

    @contextmanager
    def connection(self):
        """
        Get a connection context manager.

        Yields:
            libSQL connection object
        """
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                raise e

    @contextmanager
    def cursor(self):
        """
        Get a cursor context manager.

        Yields:
            libSQL cursor object
        """
        with self._lock:
            cursor = self._conn.cursor()
            try:
                yield cursor
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                raise e

    def execute(self, sql: str, params: Optional[Tuple] = None) -> List[Any]:
        """
        Execute a SQL statement.

        Args:
            sql: SQL statement
            params: Optional parameters

        Returns:
            List of result rows
        """
        with self.cursor() as c:
            if params:
                c.execute(sql, params)
            else:
                c.execute(sql)
            self._stats.queries_executed += 1

            if sql.strip().upper().startswith("SELECT"):
                results = c.fetchall()
                self._stats.rows_read += len(results)
                return results
            else:
                self._stats.rows_written += c.rowcount
                return []

    def executemany(self, sql: str, params_list: List[Tuple]):
        """
        Execute SQL with multiple parameter sets.

        Args:
            sql: SQL statement
            params_list: List of parameter tuples
        """
        with self.cursor() as c:
            c.executemany(sql, params_list)
            self._stats.queries_executed += len(params_list)
            self._stats.rows_written += c.rowcount

    def sync(self) -> Dict[str, Any]:
        """
        Sync local replica with cloud.

        Only applicable in embedded replica mode.

        Returns:
            Sync result info
        """
        if not self.local_path:
            return {"synced": False, "reason": "No local replica configured"}

        with self._lock:
            self._conn.sync()
            self._stats.sync_count += 1
            from datetime import datetime
            self._stats.last_sync = datetime.now().isoformat()

        return {
            "synced": True,
            "sync_count": self._stats.sync_count,
            "last_sync": self._stats.last_sync
        }

    def close_all(self):
        """Close connection and clean up."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics."""
        return {
            "queries_executed": self._stats.queries_executed,
            "rows_read": self._stats.rows_read,
            "rows_written": self._stats.rows_written,
            "sync_count": self._stats.sync_count,
            "last_sync": self._stats.last_sync,
            "mode": "embedded_replica" if self.local_path else "cloud_only"
        }

    def is_healthy(self) -> bool:
        """Check if backend is healthy."""
        try:
            with self.cursor() as c:
                c.execute("SELECT 1")
                return True
        except Exception:
            return False

    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend information."""
        return {
            "backend_type": "turso",
            "version": "1.0.0",
            "features": [
                "edge_distributed",
                "sqlite_compatible",
                "automatic_replication",
                "embedded_replica",
                "offline_support"
            ],
            "configuration": {
                "url": self.url[:30] + "..." if self.url else None,
                "local_path": self.local_path,
                "sync_interval": self.sync_interval,
                "mode": "embedded_replica" if self.local_path else "cloud_only"
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
