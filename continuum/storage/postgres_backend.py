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
PostgreSQL Storage Backend
===========================

Production-grade PostgreSQL backend with:
- Connection pooling (psycopg2.pool)
- Thread safety
- Automatic connection cleanup
- Connection statistics
- Health monitoring
- Drop-in replacement for SQLiteBackend

This backend uses PostgreSQL for distributed, multi-tenant deployments.
"""

import threading
import atexit
from urllib.parse import urlparse
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .base import StorageBackend

# Optional psycopg2 import
try:
    import psycopg2
    import psycopg2.pool
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None


@dataclass
class ConnectionStats:
    """Track connection usage statistics"""
    created: int = 0
    closed: int = 0
    current_open: int = 0
    max_concurrent: int = 0
    pool_hits: int = 0
    pool_misses: int = 0


class PostgresBackend(StorageBackend):
    """
    Thread-safe PostgreSQL storage backend with connection pooling.

    Features:
    - Connection pooling using psycopg2.pool.ThreadedConnectionPool
    - Configurable pool size (min 2, max 10 by default)
    - Automatic connection cleanup on exit
    - Thread-safe operations
    - Connection statistics tracking
    - Singleton pattern per connection string
    - Support for both sync and connection string formats

    Usage:
        # Using connection string
        storage = PostgresBackend(
            connection_string="postgresql://user:pass@localhost:5432/continuum"
        )

        # Using individual parameters
        storage = PostgresBackend(
            host="localhost",
            port=5432,
            database="continuum",
            user="postgres",
            password="secret"
        )

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
        results = storage.execute("SELECT * FROM table WHERE id = %s", (123,))
    """

    _instances: Dict[str, 'PostgresBackend'] = {}
    _lock = threading.Lock()

    def __new__(cls, connection_string: str = None, **config):
        """Singleton per connection string"""
        conn_str = connection_string or cls._build_connection_string(**config)

        with cls._lock:
            if conn_str not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[conn_str] = instance

            return cls._instances[conn_str]

    def __init__(self, connection_string: str = None,
                 min_pool_size: int = 2,
                 max_pool_size: int = 10,
                 timeout: float = 30.0,
                 **config):
        """
        Initialize PostgreSQL backend.

        Args:
            connection_string: PostgreSQL connection string
                              (e.g., "postgresql://user:pass@host:port/db")
            min_pool_size: Minimum number of pooled connections (default: 2)
            max_pool_size: Maximum number of pooled connections (default: 10)
            timeout: Connection timeout in seconds (default: 30.0)
            **config: Alternative to connection_string - individual parameters:
                     host, port, database, user, password, etc.
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 is required for PostgreSQL backend. "
                "Install it with: pip install psycopg2-binary"
            )

        if self._initialized:
            return

        self._connection_string = connection_string or self._build_connection_string(**config)
        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size
        self._timeout = timeout
        self._stats = ConnectionStats()
        self._pool_lock = threading.Lock()
        self._initialized = True

        # Parse connection string for metadata
        self._parse_connection_info()

        # Create connection pool
        self._create_pool()

        # Register cleanup on exit
        atexit.register(self.close_all)

    @staticmethod
    def _build_connection_string(**config) -> str:
        """
        Build PostgreSQL connection string from config parameters.

        Args:
            host: Database host (default: localhost)
            port: Database port (default: 5432)
            database: Database name (required)
            user: Database user (required)
            password: Database password (required)
            **other: Additional connection parameters

        Returns:
            PostgreSQL connection string
        """
        host = config.get('host', 'localhost')
        port = config.get('port', 5432)
        database = config.get('database') or config.get('db_name')
        user = config.get('user') or config.get('username')
        password = config.get('password')

        if not database:
            raise ValueError("database parameter is required")
        if not user:
            raise ValueError("user parameter is required")
        if not password:
            raise ValueError("password parameter is required")

        # Build base connection string
        conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        # Add additional parameters
        params = []
        for key, value in config.items():
            if key not in ['host', 'port', 'database', 'db_name', 'user', 'username', 'password']:
                params.append(f"{key}={value}")

        if params:
            conn_str += "?" + "&".join(params)

        return conn_str

    def _parse_connection_info(self):
        """Parse connection string to extract metadata"""
        parsed = urlparse(self._connection_string)
        self._host = parsed.hostname or 'localhost'
        self._port = parsed.port or 5432
        self._database = parsed.path.lstrip('/') if parsed.path else 'continuum'
        self._user = parsed.username or 'postgres'

    def _create_pool(self):
        """Create the connection pool"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self._min_pool_size,
                maxconn=self._max_pool_size,
                dsn=self._connection_string,
                connect_timeout=int(self._timeout)
            )
            # Track initial connections created
            with self._pool_lock:
                self._stats.created = self._min_pool_size
                self._stats.current_open = self._min_pool_size
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to create PostgreSQL connection pool: {e}")

    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get a connection from pool"""
        with self._pool_lock:
            try:
                conn = self._pool.getconn()
                self._stats.pool_hits += 1
                return conn
            except psycopg2.pool.PoolError:
                self._stats.pool_misses += 1
                raise

    def _return_connection(self, conn: psycopg2.extensions.connection, close: bool = False):
        """Return connection to pool"""
        with self._pool_lock:
            if close:
                self._pool.putconn(conn, close=True)
                self._stats.closed += 1
                self._stats.current_open -= 1
            else:
                self._pool.putconn(conn)

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.

        Yields:
            psycopg2.connection: Database connection

        Example:
            with storage.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO table VALUES (%s, %s)", (1, 2))
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
            psycopg2.cursor: Database cursor

        Example:
            with storage.cursor() as c:
                c.execute("SELECT COUNT(*) FROM table")
                count = c.fetchone()[0]
        """
        with self.connection() as conn:
            # Use DictCursor for dict-like row access (similar to sqlite3.Row)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(self, sql: str, params: Optional[Tuple] = None) -> List[Any]:
        """
        Execute a single SQL statement.

        Args:
            sql: SQL statement to execute (use %s for placeholders, not ?)
            params: Optional parameters for the SQL statement

        Returns:
            List of results (rows)

        Note:
            PostgreSQL uses %s for placeholders, unlike SQLite's ?
            The backend automatically handles this difference.

        Example:
            results = storage.execute("SELECT * FROM users WHERE id = %s", (123,))
        """
        # Convert SQLite-style ? placeholders to PostgreSQL-style %s
        sql = self._convert_placeholders(sql)

        with self.cursor() as c:
            if params:
                c.execute(sql, params)
            else:
                c.execute(sql)

            # Handle SELECT vs INSERT/UPDATE/DELETE
            if c.description:
                return c.fetchall()
            else:
                return []

    def executemany(self, sql: str, params_list: List[Tuple]):
        """
        Execute SQL with many parameter sets.

        Args:
            sql: SQL statement to execute
            params_list: List of parameter tuples

        Example:
            storage.executemany(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                [("Alice", "alice@example.com"), ("Bob", "bob@example.com")]
            )
        """
        # Convert SQLite-style ? placeholders to PostgreSQL-style %s
        sql = self._convert_placeholders(sql)

        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            cursor.close()

    @staticmethod
    def _convert_placeholders(sql: str) -> str:
        """
        Convert SQLite-style ? placeholders to PostgreSQL-style %s.

        This allows code written for SQLite to work with PostgreSQL
        without modification.
        """
        # Simple replacement - works for most cases
        # Note: This won't handle ? inside strings, but that's rare
        return sql.replace('?', '%s')

    def close_all(self):
        """Close all pooled connections"""
        with self._pool_lock:
            if hasattr(self, '_pool') and self._pool:
                self._pool.closeall()
                self._stats.closed += self._stats.current_open
                self._stats.current_open = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary containing:
            - created: Number of connections created
            - closed: Number of connections closed
            - current_open: Currently open connections
            - max_concurrent: Maximum concurrent connections
            - pool_size: Current pool size
            - pool_hits: Number of successful pool retrievals
            - pool_misses: Number of failed pool retrievals
        """
        with self._pool_lock:
            return {
                'created': self._stats.created,
                'closed': self._stats.closed,
                'current_open': self._stats.current_open,
                'max_concurrent': self._stats.max_concurrent,
                'pool_size': self._max_pool_size,
                'min_pool_size': self._min_pool_size,
                'pool_hits': self._stats.pool_hits,
                'pool_misses': self._stats.pool_misses
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
        try:
            with self.cursor() as c:
                c.execute("SELECT version()")
                version = c.fetchone()[0]
        except Exception:
            version = "unknown"

        return {
            'backend_type': 'postgresql',
            'version': version,
            'features': [
                'connection_pooling',
                'thread_safe',
                'auto_cleanup',
                'distributed',
                'acid_compliant',
                'multi_tenant'
            ],
            'configuration': {
                'host': self._host,
                'port': self._port,
                'database': self._database,
                'user': self._user,
                'min_pool_size': self._min_pool_size,
                'max_pool_size': self._max_pool_size,
                'timeout': self._timeout
            }
        }


# Convenience functions for quick access
_default_backend: Optional[PostgresBackend] = None


def get_storage(connection_string: str = None, **config) -> PostgresBackend:
    """
    Get the default PostgreSQL storage backend instance.

    Args:
        connection_string: PostgreSQL connection string
        **config: Alternative configuration parameters

    Returns:
        PostgresBackend instance
    """
    global _default_backend
    conn_str = connection_string or PostgresBackend._build_connection_string(**config)

    if _default_backend is None or conn_str != _default_backend._connection_string:
        _default_backend = PostgresBackend(connection_string, **config)
    return _default_backend


@contextmanager
def db_connection(connection_string: str = None, **config):
    """
    Convenience function for quick database access.

    Example:
        with db_connection("postgresql://user:pass@host/db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
    """
    with get_storage(connection_string, **config).connection() as conn:
        yield conn


@contextmanager
def db_cursor(connection_string: str = None, **config):
    """
    Convenience function for quick cursor access.

    Example:
        with db_cursor("postgresql://user:pass@host/db") as c:
            c.execute("SELECT COUNT(*) FROM table")
            count = c.fetchone()[0]
    """
    with get_storage(connection_string, **config).cursor() as c:
        yield c

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
