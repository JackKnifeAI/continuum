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
Async SQLite Storage Backend
=============================

Async-first SQLite backend using aiosqlite for:
- Non-blocking I/O operations
- Connection pooling
- WAL mode for concurrency
- Thread safety
- Automatic cleanup
- Connection statistics

This backend is optimized for async FastAPI applications.
"""

import aiosqlite
import asyncio
import atexit
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AsyncConnectionStats:
    """Track async connection usage statistics"""
    created: int = 0
    closed: int = 0
    current_open: int = 0
    max_concurrent: int = 0


class AsyncSQLiteBackend:
    """
    Thread-safe async SQLite storage backend with connection pooling.

    Features:
    - Async connection pooling to prevent resource leaks
    - WAL (Write-Ahead Logging) mode for better concurrency
    - Automatic connection cleanup on exit
    - Thread-safe operations
    - Connection statistics tracking
    - Singleton pattern per database path

    Usage:
        storage = AsyncSQLiteBackend(db_path="/path/to/memory.db")

        # Use context manager for connections
        async with storage.connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM table")
            results = await cursor.fetchall()

        # Or for quick queries
        async with storage.cursor() as c:
            await c.execute("SELECT COUNT(*) FROM table")
            count = await c.fetchone()

        # Direct execution
        results = await storage.execute("SELECT * FROM table WHERE id = ?", (123,))
    """

    _instances: Dict[str, 'AsyncSQLiteBackend'] = {}
    _lock = asyncio.Lock()

    def __new__(cls, db_path: str = None, **config):
        """Singleton per database path"""
        path = str(db_path or config.get('db_path', ':memory:'))

        # Note: We can't use async lock in __new__, so we use a simple dict check
        # This is safe because __init__ will only run once per instance
        if path not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[path] = instance

        return cls._instances[path]

    def __init__(self, db_path: str = None, max_pool_size: int = 5,
                 timeout: float = 30.0, **config):
        """
        Initialize async SQLite backend.

        Args:
            db_path: Path to SQLite database file (default: ":memory:")
            max_pool_size: Maximum number of pooled connections (default: 5)
            timeout: Database lock timeout in seconds (default: 30.0)
            **config: Additional configuration options
        """
        if self._initialized:
            return

        self.db_path = Path(db_path) if db_path else Path(config.get('db_path', ':memory:'))
        self._pool: List[aiosqlite.Connection] = []
        self._pool_lock = asyncio.Lock()
        self._max_pool_size = max_pool_size
        self._timeout = timeout
        self._stats = AsyncConnectionStats()
        self._initialized = True
        self._setup_complete = False

        # Ensure parent directory exists
        if str(self.db_path) != ':memory:':
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Register cleanup on exit (sync wrapper for async cleanup)
        atexit.register(self._sync_close_all)

    def _sync_close_all(self):
        """Synchronous wrapper for close_all() for atexit"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the coroutine
                asyncio.ensure_future(self.close_all())
            else:
                # If no loop or not running, run it
                loop.run_until_complete(self.close_all())
        except RuntimeError:
            # Event loop is closed, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.close_all())
            loop.close()

    async def _setup_database(self):
        """Configure database for optimal performance"""
        if self._setup_complete:
            return

        conn = await self._create_connection()
        try:
            # Enable WAL mode for better concurrency
            await conn.execute("PRAGMA journal_mode=WAL")
            # Set busy timeout to prevent deadlocks
            await conn.execute(f"PRAGMA busy_timeout={int(self._timeout * 1000)}")
            # Use NORMAL synchronous mode for faster writes
            await conn.execute("PRAGMA synchronous=NORMAL")
            # 64MB cache for better performance
            await conn.execute("PRAGMA cache_size=-64000")
            # Keep temp tables in memory
            await conn.execute("PRAGMA temp_store=MEMORY")
            await conn.commit()
            self._setup_complete = True
        finally:
            await conn.close()

    async def _create_connection(self) -> aiosqlite.Connection:
        """Create a new connection with proper settings"""
        conn = await aiosqlite.connect(
            str(self.db_path),
            timeout=self._timeout
        )
        # Return rows as Row objects for dict-like access
        conn.row_factory = aiosqlite.Row

        async with self._pool_lock:
            self._stats.created += 1
            self._stats.current_open += 1
            if self._stats.current_open > self._stats.max_concurrent:
                self._stats.max_concurrent = self._stats.current_open

        return conn

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a connection from pool or create new one"""
        # Ensure database is set up
        if not self._setup_complete:
            await self._setup_database()

        async with self._pool_lock:
            if self._pool:
                return self._pool.pop()

        return await self._create_connection()

    async def _return_connection(self, conn: aiosqlite.Connection):
        """Return connection to pool or close if pool is full"""
        async with self._pool_lock:
            if len(self._pool) < self._max_pool_size:
                self._pool.append(conn)
                return

        # Pool is full, close connection
        await conn.close()
        async with self._pool_lock:
            self._stats.closed += 1
            self._stats.current_open -= 1

    @asynccontextmanager
    async def connection(self):
        """
        Context manager for database connections.

        Yields:
            aiosqlite.Connection: Database connection

        Example:
            async with storage.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute("INSERT INTO table VALUES (?, ?)", (1, 2))
        """
        conn = await self._get_connection()
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await self._return_connection(conn)

    @asynccontextmanager
    async def cursor(self):
        """
        Context manager for quick cursor operations.

        Yields:
            aiosqlite.Cursor: Database cursor

        Example:
            async with storage.cursor() as c:
                await c.execute("SELECT COUNT(*) FROM table")
                count = await c.fetchone()
        """
        async with self.connection() as conn:
            cursor = await conn.cursor()
            try:
                yield cursor
            finally:
                await cursor.close()

    async def execute(self, sql: str, params: Optional[Tuple] = None) -> List[Any]:
        """
        Execute a single SQL statement.

        Args:
            sql: SQL statement to execute
            params: Optional parameters for the SQL statement

        Returns:
            List of results (rows)

        Example:
            results = await storage.execute("SELECT * FROM users WHERE id = ?", (123,))
        """
        async with self.cursor() as c:
            if params:
                await c.execute(sql, params)
            else:
                await c.execute(sql)
            return await c.fetchall()

    async def executemany(self, sql: str, params_list: List[Tuple]):
        """
        Execute SQL with many parameter sets.

        Args:
            sql: SQL statement to execute
            params_list: List of parameter tuples

        Example:
            await storage.executemany(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                [("Alice", "alice@example.com"), ("Bob", "bob@example.com")]
            )
        """
        async with self.connection() as conn:
            cursor = await conn.cursor()
            await cursor.executemany(sql, params_list)
            await cursor.close()

    async def close_all(self):
        """Close all pooled connections"""
        async with self._pool_lock:
            while self._pool:
                conn = self._pool.pop()
                await conn.close()
                self._stats.closed += 1
                self._stats.current_open -= 1

    async def get_stats(self) -> Dict[str, Any]:
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
        async with self._pool_lock:
            return {
                'created': self._stats.created,
                'closed': self._stats.closed,
                'current_open': self._stats.current_open,
                'max_concurrent': self._stats.max_concurrent,
                'pool_size': len(self._pool)
            }

    async def is_healthy(self) -> bool:
        """
        Check if the storage backend is healthy and responsive.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with self.cursor() as c:
                await c.execute("SELECT 1")
                result = await c.fetchone()
                return result is not None and result[0] == 1
        except Exception:
            return False

    async def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the backend implementation.

        Returns:
            Dictionary containing backend information
        """
        import sqlite3
        version = sqlite3.sqlite_version

        return {
            'backend_type': 'async_sqlite',
            'version': version,
            'features': [
                'async_io',
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
_default_backend: Optional[AsyncSQLiteBackend] = None


def get_async_storage(db_path: str = None, **config) -> AsyncSQLiteBackend:
    """
    Get the default async SQLite storage backend instance.

    Args:
        db_path: Path to database file
        **config: Additional configuration

    Returns:
        AsyncSQLiteBackend instance
    """
    global _default_backend
    if _default_backend is None or (db_path and db_path != str(_default_backend.db_path)):
        _default_backend = AsyncSQLiteBackend(db_path, **config)
    return _default_backend


@asynccontextmanager
async def async_db_connection(db_path: str = None, **config):
    """
    Convenience function for quick database access.

    Example:
        async with async_db_connection("/path/to/db.sqlite") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM table")
    """
    async with get_async_storage(db_path, **config).connection() as conn:
        yield conn


@asynccontextmanager
async def async_db_cursor(db_path: str = None, **config):
    """
    Convenience function for quick cursor access.

    Example:
        async with async_db_cursor("/path/to/db.sqlite") as c:
            await c.execute("SELECT COUNT(*) FROM table")
            count = await c.fetchone()
    """
    async with get_async_storage(db_path, **config).cursor() as c:
        yield c

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
