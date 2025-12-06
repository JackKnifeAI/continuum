"""
CONTINUUM Storage Module
=========================

Pluggable storage backends for memory persistence.

Supported backends:
- SQLite (default, included)
- PostgreSQL (interface ready, implementation TBD)
- Custom backends via StorageBackend interface

Usage:
    from continuum.storage import SQLiteBackend

    storage = SQLiteBackend(db_path="/path/to/memory.db")

    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entities")
        results = cursor.fetchall()
"""

from .base import StorageBackend
from .sqlite_backend import SQLiteBackend

__all__ = ['StorageBackend', 'SQLiteBackend']
