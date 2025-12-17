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
SQLite Storage Backend
======================

High-performance SQLite backend with:
- Connection pooling
- WAL mode for concurrency
- Thread safety
- Automatic cleanup
- Connection statistics

This is the default storage backend for CONTINUUM.
"""

import sqlite3
import threading
import atexit
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .base import StorageBackend


@dataclass
class ConnectionStats:
    """Track connection usage statistics"""
    created: int = 0
    closed: int = 0
    current_open: int = 0
    max_concurrent: int = 0


class SQLiteBackend(StorageBackend):
    """
    Thread-safe SQLite storage backend with connection pooling.

    Features:
    - Connection pooling to prevent resource leaks
    - WAL (Write-Ahead Logging) mode for better concurrency
    - Automatic connection cleanup on exit
    - Thread-safe operations
    - Connection statistics tracking
    - Singleton pattern per database path

    Usage:
        storage = SQLiteBackend(db_path="/path/to/memory.db")

        # Use context manager for connections
        with storage.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()

        # Or for quick queries
        with storage.cursor() as c:
            c.execute("SELECT COUNT(*) FROM table")
            count = c.fetchone()[0]

        # Direct execution
        results = storage.execute("SELECT * FROM table WHERE id = ?", (123,))
    """

    _instances: Dict[str, 'SQLiteBackend'] = {}
    _lock = threading.Lock()

    def __new__(cls, db_path: str = None, **config):
        """Singleton per database path"""
        path = str(db_path or config.get('db_path', ':memory:'))

        with cls._lock:
            if path not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[path] = instance

            return cls._instances[path]

    def __init__(self, db_path: str = None, max_pool_size: int = 5,
                 timeout: float = 30.0, **config):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file (default: ":memory:")
            max_pool_size: Maximum number of pooled connections (default: 5)
            timeout: Database lock timeout in seconds (default: 30.0)
            **config: Additional configuration options
        """
        if self._initialized:
            return

        self.db_path = Path(db_path) if db_path else Path(config.get('db_path', ':memory:'))
        self._pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()
        self._max_pool_size = max_pool_size
        self._timeout = timeout
        self._stats = ConnectionStats()
        self._initialized = True

        # Ensure parent directory exists
        if str(self.db_path) != ':memory:':
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Set up WAL mode on first connection
        self._setup_database()

        # Register cleanup on exit
        atexit.register(self.close_all)

    def _setup_database(self):
        """Configure database for optimal performance"""
        conn = self._create_connection()
        try:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            # Set busy timeout to prevent deadlocks
            conn.execute(f"PRAGMA busy_timeout={int(self._timeout * 1000)}")
            # Use NORMAL synchronous mode for faster writes
            conn.execute("PRAGMA synchronous=NORMAL")
            # 64MB cache for better performance
            conn.execute("PRAGMA cache_size=-64000")
            # Keep temp tables in memory
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.commit()
        finally:
            conn.close()

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new connection with proper settings"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self._timeout,
            check_same_thread=False  # Allow use across threads
        )
        # Return rows as Row objects for dict-like access
        conn.row_factory = sqlite3.Row

        with self._pool_lock:
            self._stats.created += 1
            self._stats.current_open += 1
            if self._stats.current_open > self._stats.max_concurrent:
                self._stats.max_concurrent = self._stats.current_open

        return conn

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from pool or create new one"""
        with self._pool_lock:
            if self._pool:
                return self._pool.pop()

        return self._create_connection()

    def _return_connection(self, conn: sqlite3.Connection):
        """Return connection to pool or close if pool is full"""
        with self._pool_lock:
            if len(self._pool) < self._max_pool_size:
                self._pool.append(conn)
                return

        # Pool is full, close connection
        conn.close()
        with self._pool_lock:
            self._stats.closed += 1
            self._stats.current_open -= 1

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with storage.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO table VALUES (?, ?)", (1, 2))
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._return_connection(conn)

    @contextmanager
    def cursor(self):
        """
        Context manager for quick cursor operations.

        Yields:
            sqlite3.Cursor: Database cursor

        Example:
            with storage.cursor() as c:
                c.execute("SELECT COUNT(*) FROM table")
                count = c.fetchone()[0]
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(self, sql: str, params: Optional[Tuple] = None) -> List[Any]:
        """
        Execute a single SQL statement.

        Args:
            sql: SQL statement to execute
            params: Optional parameters for the SQL statement

        Returns:
            List of results (rows)

        Example:
            results = storage.execute("SELECT * FROM users WHERE id = ?", (123,))
        """
        with self.cursor() as c:
            if params:
                c.execute(sql, params)
            else:
                c.execute(sql)
            return c.fetchall()

    def executemany(self, sql: str, params_list: List[Tuple]):
        """
        Execute SQL with many parameter sets.

        Args:
            sql: SQL statement to execute
            params_list: List of parameter tuples

        Example:
            storage.executemany(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                [("Alice", "alice@example.com"), ("Bob", "bob@example.com")]
            )
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            cursor.close()

    def close_all(self):
        """Close all pooled connections"""
        with self._pool_lock:
            while self._pool:
                conn = self._pool.pop()
                conn.close()
                self._stats.closed += 1
                self._stats.current_open -= 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary containing:
            - created: Number of connections created
            - closed: Number of connections closed
            - current_open: Currently open connections
            - max_concurrent: Maximum concurrent connections
            - pool_size: Current connection pool size
        """
        with self._pool_lock:
            return {
                'created': self._stats.created,
                'closed': self._stats.closed,
                'current_open': self._stats.current_open,
                'max_concurrent': self._stats.max_concurrent,
                'pool_size': len(self._pool)
            }

    def is_healthy(self) -> bool:
        """
        Check if the storage backend is healthy and responsive.

        Returns:
            True if healthy, False otherwise
        """
        try:
            with self.cursor() as c:
                c.execute("SELECT 1")
                result = c.fetchone()
                return result is not None and result[0] == 1
        except Exception:
            return False

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the backend implementation.

        Returns:
            Dictionary containing backend information
        """
        version = sqlite3.sqlite_version

        return {
            'backend_type': 'sqlite',
            'version': version,
            'features': [
                'connection_pooling',
                'wal_mode',
                'thread_safe',
                'auto_cleanup'
            ],
            'configuration': {
                'db_path': str(self.db_path),
                'max_pool_size': self._max_pool_size,
                'timeout': self._timeout
            }
        }


# Convenience functions for quick access
_default_backend: Optional[SQLiteBackend] = None


def get_storage(db_path: str = None, **config) -> SQLiteBackend:
    """
    Get the default SQLite storage backend instance.

    Args:
        db_path: Path to database file
        **config: Additional configuration

    Returns:
        SQLiteBackend instance
    """
    global _default_backend
    if _default_backend is None or (db_path and db_path != str(_default_backend.db_path)):
        _default_backend = SQLiteBackend(db_path, **config)
    return _default_backend


@contextmanager
def db_connection(db_path: str = None, **config):
    """
    Convenience function for quick database access.

    Example:
        with db_connection("/path/to/db.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
    """
    with get_storage(db_path, **config).connection() as conn:
        yield conn


@contextmanager
def db_cursor(db_path: str = None, **config):
    """
    Convenience function for quick cursor access.

    Example:
        with db_cursor("/path/to/db.sqlite") as c:
            c.execute("SELECT COUNT(*) FROM table")
            count = c.fetchone()[0]
    """
    with get_storage(db_path, **config).cursor() as c:
        yield c

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
