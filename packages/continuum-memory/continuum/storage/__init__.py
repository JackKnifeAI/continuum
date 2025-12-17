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
CONTINUUM Storage Module (OSS Tier)
====================================

Pluggable storage backends for memory persistence.

Supported backends (OSS):
- SQLite (default, file-based)
- Async SQLite (async operations)

For PostgreSQL and enterprise backends, see continuum-cloud.

Usage:
    from continuum.storage import SQLiteBackend

    # SQLite backend
    storage = SQLiteBackend(db_path="/path/to/memory.db")

    # In-memory SQLite
    storage = SQLiteBackend(db_path=":memory:")

    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entities")
        results = cursor.fetchall()
"""

from .base import StorageBackend
from .sqlite_backend import SQLiteBackend
from .async_backend import AsyncSQLiteBackend

__all__ = [
    'StorageBackend',
    'SQLiteBackend',
    'AsyncSQLiteBackend',
    'get_backend',
]


def get_backend(connection_string: str, **config) -> StorageBackend:
    """
    Auto-detect and return appropriate storage backend.

    Args:
        connection_string: Database connection string or file path
            - "/path/to/file.db" or "file.db" → SQLiteBackend
            - ":memory:" → SQLiteBackend (in-memory)
        **config: Additional backend-specific configuration

    Returns:
        SQLiteBackend instance

    Note:
        For PostgreSQL support, upgrade to continuum-cloud.

    Examples:
        # SQLite file
        storage = get_backend("/var/lib/continuum/memory.db")

        # SQLite in-memory
        storage = get_backend(":memory:")
    """
    conn_str = connection_string.lower()

    if conn_str.startswith('postgresql://') or conn_str.startswith('postgres://'):
        raise ImportError(
            "PostgreSQL backend requires continuum-cloud. "
            "Install with: pip install continuum-cloud[postgres]"
        )
    else:
        # Treat as SQLite path (file or :memory:)
        return SQLiteBackend(db_path=connection_string, **config)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
