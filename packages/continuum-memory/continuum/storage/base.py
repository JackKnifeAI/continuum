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
Abstract Storage Backend Interface
===================================

Defines the contract that all storage backends must implement.
Allows CONTINUUM to support multiple database backends (SQLite, PostgreSQL, etc.)
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    All storage implementations must inherit from this class and implement
    the required methods. This ensures consistent behavior across different
    database backends.

    Example:
        class MyCustomBackend(StorageBackend):
            def __init__(self, config: Dict[str, Any]):
                self.config = config
                self._setup()

            def _setup(self):
                # Initialize connection pool, etc.
                pass

            @contextmanager
            def connection(self):
                conn = self._get_connection()
                try:
                    yield conn
                    self._commit(conn)
                finally:
                    self._return_connection(conn)

            # ... implement other methods
    """

    @abstractmethod
    def __init__(self, **config):
        """
        Initialize the storage backend with configuration.

        Args:
            **config: Backend-specific configuration parameters
        """
        pass

    @abstractmethod
    @contextmanager
    def connection(self):
        """
        Get a connection context manager.

        Yields:
            Connection object (backend-specific)

        Example:
            with storage.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        pass

    @abstractmethod
    @contextmanager
    def cursor(self):
        """
        Get a cursor context manager for quick operations.

        Yields:
            Cursor object (backend-specific)

        Example:
            with storage.cursor() as c:
                c.execute("SELECT COUNT(*) FROM table")
                count = c.fetchone()[0]
        """
        pass

    @abstractmethod
    def execute(self, sql: str, params: Optional[Tuple] = None) -> List[Any]:
        """
        Execute a single SQL statement.

        Args:
            sql: SQL statement to execute
            params: Optional parameters for the SQL statement

        Returns:
            List of results (rows)

        Example:
            results = storage.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def close_all(self):
        """
        Close all connections and clean up resources.

        This is called during shutdown to ensure proper cleanup.
        Should close connection pools, release locks, etc.
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get backend statistics.

        Returns:
            Dictionary containing statistics like:
            - created: Number of connections created
            - closed: Number of connections closed
            - current_open: Currently open connections
            - max_concurrent: Maximum concurrent connections
            - pool_size: Current connection pool size

        Example:
            stats = storage.get_stats()
            print(f"Open connections: {stats['current_open']}")
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the storage backend is healthy and responsive.

        Returns:
            True if healthy, False otherwise

        Example:
            if not storage.is_healthy():
                logger.error("Storage backend is unhealthy")
        """
        pass

    @abstractmethod
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the backend implementation.

        Returns:
            Dictionary containing:
            - backend_type: Type of backend (e.g., "sqlite", "postgresql")
            - version: Backend version
            - features: List of supported features
            - configuration: Current configuration (sanitized)

        Example:
            info = storage.get_backend_info()
            print(f"Using {info['backend_type']} v{info['version']}")
        """
        pass

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
