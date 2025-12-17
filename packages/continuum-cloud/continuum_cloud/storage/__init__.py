"""
CONTINUUM Storage Module
=========================

Pluggable storage backends for memory persistence.

Supported backends:
- SQLite (default, file-based)
- PostgreSQL (production, distributed)
- Custom backends via StorageBackend interface

Usage:
    from continuum.storage import SQLiteBackend, PostgresBackend

    # SQLite backend
    storage = SQLiteBackend(db_path="/path/to/memory.db")

    # PostgreSQL backend
    storage = PostgresBackend(
        connection_string="postgresql://user:pass@localhost:5432/continuum"
    )

    # Auto-detect from connection string
    storage = get_backend("postgresql://user:pass@localhost/db")  # PostgreSQL
    storage = get_backend("/path/to/memory.db")  # SQLite

    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entities")
        results = cursor.fetchall()

Migration:
    from continuum.storage import migrate_sqlite_to_postgres

    migrate_sqlite_to_postgres(
        sqlite_path="/path/to/memory.db",
        postgres_connection="postgresql://user:pass@localhost/continuum"
    )
"""

from .base import StorageBackend
from .sqlite_backend import SQLiteBackend
from .postgres_backend import PostgresBackend
from .migrations import (
    migrate_sqlite_to_postgres,
    create_postgres_schema,
    get_schema_version,
    rollback_migration,
    MigrationResult,
    MigrationError,
    SCHEMA_VERSION
)

__all__ = [
    'StorageBackend',
    'SQLiteBackend',
    'PostgresBackend',
    'get_backend',
    'migrate_sqlite_to_postgres',
    'create_postgres_schema',
    'get_schema_version',
    'rollback_migration',
    'MigrationResult',
    'MigrationError',
    'SCHEMA_VERSION'
]


def get_backend(connection_string: str, **config) -> StorageBackend:
    """
    Auto-detect and return appropriate storage backend based on connection string.

    Args:
        connection_string: Database connection string or file path
            - "postgresql://..." or "postgres://..." → PostgresBackend
            - "/path/to/file.db" or "file.db" → SQLiteBackend
            - ":memory:" → SQLiteBackend (in-memory)
        **config: Additional backend-specific configuration

    Returns:
        Appropriate StorageBackend instance

    Examples:
        # PostgreSQL
        storage = get_backend("postgresql://user:pass@localhost/continuum")

        # SQLite file
        storage = get_backend("/var/lib/continuum/memory.db")

        # SQLite in-memory
        storage = get_backend(":memory:")
    """
    conn_str = connection_string.lower()

    if conn_str.startswith('postgresql://') or conn_str.startswith('postgres://'):
        return PostgresBackend(connection_string=connection_string, **config)
    else:
        # Treat as SQLite path (file or :memory:)
        return SQLiteBackend(db_path=connection_string, **config)
