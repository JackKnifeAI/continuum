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
Database Migration Utilities
=============================

Tools for migrating between storage backends and managing schema versions.

Features:
- SQLite to PostgreSQL migration
- Schema version tracking
- Data integrity validation
- Progress reporting
- Rollback support

Usage:
    from continuum.storage.migrations import migrate_sqlite_to_postgres

    # Migrate from SQLite to PostgreSQL
    migrate_sqlite_to_postgres(
        sqlite_path="/path/to/memory.db",
        postgres_connection="postgresql://user:pass@host/db",
        progress_callback=lambda msg: print(msg)
    )
"""

import sqlite3
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass

# Optional psycopg2 import
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None


@dataclass
class MigrationResult:
    """Result of a migration operation"""
    success: bool
    rows_migrated: Dict[str, int]
    errors: List[str]
    duration_seconds: float
    started_at: datetime
    completed_at: datetime


class MigrationError(Exception):
    """Raised when migration fails"""
    pass


# Schema version tracking
SCHEMA_VERSION = "1.0.0"

SCHEMA_DEFINITIONS = {
    'entities': """
        CREATE TABLE IF NOT EXISTS entities (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            tenant_id TEXT DEFAULT 'default'
        )
    """,
    'auto_messages': """
        CREATE TABLE IF NOT EXISTS auto_messages (
            id SERIAL PRIMARY KEY,
            instance_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            message_number INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            tenant_id TEXT DEFAULT 'default'
        )
    """,
    'decisions': """
        CREATE TABLE IF NOT EXISTS decisions (
            id SERIAL PRIMARY KEY,
            instance_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            decision_text TEXT NOT NULL,
            context TEXT,
            extracted_from TEXT,
            tenant_id TEXT DEFAULT 'default'
        )
    """,
    'attention_links': """
        CREATE TABLE IF NOT EXISTS attention_links (
            id SERIAL PRIMARY KEY,
            concept_a TEXT NOT NULL,
            concept_b TEXT NOT NULL,
            link_type TEXT NOT NULL,
            strength REAL DEFAULT 0.5,
            created_at TEXT NOT NULL,
            tenant_id TEXT DEFAULT 'default'
        )
    """,
    'compound_concepts': """
        CREATE TABLE IF NOT EXISTS compound_concepts (
            id SERIAL PRIMARY KEY,
            compound_name TEXT NOT NULL,
            component_concepts TEXT NOT NULL,
            co_occurrence_count INTEGER DEFAULT 1,
            last_seen TEXT NOT NULL,
            tenant_id TEXT DEFAULT 'default'
        )
    """,
    'tenants': """
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            last_active TEXT,
            metadata TEXT DEFAULT '{}'
        )
    """,
    'schema_version': """
        CREATE TABLE IF NOT EXISTS schema_version (
            id SERIAL PRIMARY KEY,
            version TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """
}

# Indexes for performance
SCHEMA_INDEXES = {
    'entities': [
        "CREATE INDEX IF NOT EXISTS idx_entities_tenant ON entities(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type, tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name, tenant_id)"
    ],
    'auto_messages': [
        "CREATE INDEX IF NOT EXISTS idx_messages_tenant ON auto_messages(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_instance ON auto_messages(instance_id, tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON auto_messages(timestamp DESC)"
    ],
    'decisions': [
        "CREATE INDEX IF NOT EXISTS idx_decisions_tenant ON decisions(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_decisions_instance ON decisions(instance_id, tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp DESC)"
    ],
    'attention_links': [
        "CREATE INDEX IF NOT EXISTS idx_links_tenant ON attention_links(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_links_concepts ON attention_links(concept_a, concept_b, tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_links_type ON attention_links(link_type, tenant_id)"
    ],
    'compound_concepts': [
        "CREATE INDEX IF NOT EXISTS idx_compounds_tenant ON compound_concepts(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_compounds_name ON compound_concepts(compound_name, tenant_id)"
    ],
    'tenants': [
        "CREATE INDEX IF NOT EXISTS idx_tenants_active ON tenants(last_active DESC)"
    ]
}


def create_postgres_schema(
    connection_string: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> None:
    """
    Create CONTINUUM schema in PostgreSQL database.

    Args:
        connection_string: PostgreSQL connection string
        progress_callback: Optional callback for progress messages

    Raises:
        MigrationError: If schema creation fails
    """
    if not PSYCOPG2_AVAILABLE:
        raise MigrationError(
            "psycopg2 is required for PostgreSQL migrations. "
            "Install it with: pip install psycopg2-binary"
        )

    def log(msg: str):
        if progress_callback:
            progress_callback(msg)

    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        log("Creating PostgreSQL schema...")

        # Create tables
        for table_name, create_sql in SCHEMA_DEFINITIONS.items():
            log(f"  Creating table: {table_name}")
            cursor.execute(create_sql)

        # Create indexes
        for table_name, indexes in SCHEMA_INDEXES.items():
            for idx_sql in indexes:
                log(f"  Creating index on {table_name}")
                cursor.execute(idx_sql)

        # Record schema version
        cursor.execute(
            "INSERT INTO schema_version (version, description) VALUES (%s, %s)",
            (SCHEMA_VERSION, "Initial schema creation")
        )

        conn.commit()
        log("Schema creation complete!")

    except psycopg2.Error as e:
        raise MigrationError(f"Failed to create PostgreSQL schema: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def get_schema_version(connection_string: str) -> Optional[str]:
    """
    Get current schema version from PostgreSQL database.

    Args:
        connection_string: PostgreSQL connection string

    Returns:
        Schema version string, or None if not found
    """
    if not PSYCOPG2_AVAILABLE:
        raise MigrationError(
            "psycopg2 is required for PostgreSQL migrations. "
            "Install it with: pip install psycopg2-binary"
        )

    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
        )
        result = cursor.fetchone()

        return result[0] if result else None

    except psycopg2.Error:
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def migrate_sqlite_to_postgres(
    sqlite_path: str,
    postgres_connection: str,
    batch_size: int = 1000,
    create_schema: bool = True,
    validate: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None
) -> MigrationResult:
    """
    Migrate data from SQLite to PostgreSQL.

    Args:
        sqlite_path: Path to SQLite database file
        postgres_connection: PostgreSQL connection string
        batch_size: Number of rows to migrate per batch (default: 1000)
        create_schema: Whether to create schema first (default: True)
        validate: Whether to validate data after migration (default: True)
        progress_callback: Optional callback for progress messages

    Returns:
        MigrationResult with migration statistics

    Raises:
        MigrationError: If migration fails

    Example:
        result = migrate_sqlite_to_postgres(
            sqlite_path="/path/to/memory.db",
            postgres_connection="postgresql://user:pass@localhost/continuum",
            progress_callback=lambda msg: print(msg)
        )

        if result.success:
            print(f"Migrated {sum(result.rows_migrated.values())} total rows")
        else:
            print(f"Migration failed: {result.errors}")
    """
    if not PSYCOPG2_AVAILABLE:
        raise MigrationError(
            "psycopg2 is required for PostgreSQL migrations. "
            "Install it with: pip install psycopg2-binary"
        )

    started_at = datetime.now()
    rows_migrated = {}
    errors = []

    def log(msg: str):
        if progress_callback:
            progress_callback(msg)

    try:
        # Create PostgreSQL schema if requested
        if create_schema:
            log("Creating PostgreSQL schema...")
            create_postgres_schema(postgres_connection, progress_callback)

        # Connect to both databases
        log(f"Connecting to SQLite: {sqlite_path}")
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row

        log(f"Connecting to PostgreSQL...")
        pg_conn = psycopg2.connect(postgres_connection)
        pg_cursor = pg_conn.cursor()

        # Get list of tables to migrate (exclude schema_version)
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_version'"
        )
        tables = [row[0] for row in sqlite_cursor.fetchall()]

        log(f"Found {len(tables)} tables to migrate: {', '.join(tables)}")

        # Migrate each table
        for table_name in tables:
            log(f"\nMigrating table: {table_name}")

            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in sqlite_cursor.fetchall() if col[1] != 'id']

            # Count total rows
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = sqlite_cursor.fetchone()[0]
            log(f"  Total rows: {total_rows}")

            if total_rows == 0:
                rows_migrated[table_name] = 0
                continue

            # Migrate in batches
            offset = 0
            migrated = 0
            column_list = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))

            while offset < total_rows:
                # Fetch batch from SQLite
                sqlite_cursor.execute(
                    f"SELECT {column_list} FROM {table_name} LIMIT ? OFFSET ?",
                    (batch_size, offset)
                )
                batch = sqlite_cursor.fetchall()

                if not batch:
                    break

                # Insert batch into PostgreSQL
                insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
                batch_data = [tuple(row) for row in batch]

                try:
                    psycopg2.extras.execute_batch(pg_cursor, insert_sql, batch_data)
                    pg_conn.commit()

                    migrated += len(batch)
                    log(f"  Progress: {migrated}/{total_rows} ({migrated*100//total_rows}%)")

                except psycopg2.Error as e:
                    error_msg = f"Failed to insert batch into {table_name}: {e}"
                    log(f"  ERROR: {error_msg}")
                    errors.append(error_msg)
                    pg_conn.rollback()

                offset += batch_size

            rows_migrated[table_name] = migrated
            log(f"  Completed: {migrated} rows migrated")

        # Validate data if requested
        if validate:
            log("\nValidating migration...")
            validation_errors = _validate_migration(sqlite_conn, pg_conn, tables)
            if validation_errors:
                errors.extend(validation_errors)
                log(f"  WARNING: Found {len(validation_errors)} validation errors")
            else:
                log("  Validation passed!")

        # Close connections
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()

        log(f"\nMigration completed in {duration:.2f} seconds")
        log(f"Total rows migrated: {sum(rows_migrated.values())}")

        return MigrationResult(
            success=len(errors) == 0,
            rows_migrated=rows_migrated,
            errors=errors,
            duration_seconds=duration,
            started_at=started_at,
            completed_at=completed_at
        )

    except Exception as e:
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        error_msg = f"Migration failed: {e}"
        errors.append(error_msg)
        log(f"\nERROR: {error_msg}")

        return MigrationResult(
            success=False,
            rows_migrated=rows_migrated,
            errors=errors,
            duration_seconds=duration,
            started_at=started_at,
            completed_at=completed_at
        )


def _validate_migration(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg2.extensions.connection,
    tables: List[str]
) -> List[str]:
    """
    Validate that migration was successful by comparing row counts.

    Args:
        sqlite_conn: SQLite connection
        pg_conn: PostgreSQL connection
        tables: List of table names to validate

    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    for table_name in tables:
        # Count rows in SQLite
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = sqlite_cursor.fetchone()[0]

        # Count rows in PostgreSQL
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        pg_count = pg_cursor.fetchone()[0]

        if sqlite_count != pg_count:
            errors.append(
                f"Row count mismatch in {table_name}: "
                f"SQLite={sqlite_count}, PostgreSQL={pg_count}"
            )

    pg_cursor.close()
    return errors


def rollback_migration(
    postgres_connection: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> None:
    """
    Rollback migration by dropping all CONTINUUM tables from PostgreSQL.

    WARNING: This will delete all data in the PostgreSQL database!

    Args:
        postgres_connection: PostgreSQL connection string
        progress_callback: Optional callback for progress messages

    Raises:
        MigrationError: If rollback fails
    """
    if not PSYCOPG2_AVAILABLE:
        raise MigrationError(
            "psycopg2 is required for PostgreSQL migrations. "
            "Install it with: pip install psycopg2-binary"
        )

    def log(msg: str):
        if progress_callback:
            progress_callback(msg)

    try:
        conn = psycopg2.connect(postgres_connection)
        cursor = conn.cursor()

        log("Rolling back migration (dropping tables)...")

        # Get list of tables
        tables = list(SCHEMA_DEFINITIONS.keys())

        # Drop tables in reverse order (to handle dependencies)
        for table_name in reversed(tables):
            log(f"  Dropping table: {table_name}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")

        conn.commit()
        log("Rollback complete!")

    except psycopg2.Error as e:
        raise MigrationError(f"Failed to rollback migration: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# =============================================================================
# CLI Interface
# =============================================================================

def upgrade(connection_string: Optional[str] = None) -> None:
    """
    Run database schema upgrade/creation.

    Args:
        connection_string: PostgreSQL connection string (or from DATABASE_URL env)
    """
    import os

    conn_str = connection_string or os.getenv('DATABASE_URL')

    if not conn_str:
        print("No database connection configured. Using SQLite (no migration needed).")
        return

    print("Running database migration...")
    try:
        # Check if schema exists
        version = get_schema_version(conn_str)
        if version:
            print(f"Database already at schema version {version}")
            return

        # Create schema
        create_postgres_schema(conn_str, progress_callback=print)
        print("Migration complete!")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise SystemExit(1)


def main():
    """CLI entry point for migrations."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m continuum.storage.migrations <command>")
        print("Commands:")
        print("  upgrade    - Run database migrations")
        print("  version    - Show current schema version")
        print("  rollback   - Rollback all migrations (WARNING: deletes data)")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "upgrade":
        upgrade()
    elif command == "version":
        import os
        conn_str = os.getenv('DATABASE_URL')
        if not conn_str:
            print("No DATABASE_URL configured")
            sys.exit(0)
        version = get_schema_version(conn_str)
        print(f"Schema version: {version or 'not initialized'}")
    elif command == "rollback":
        import os
        conn_str = os.getenv('DATABASE_URL')
        if not conn_str:
            print("No DATABASE_URL configured")
            sys.exit(1)
        print("WARNING: This will delete all data!")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            rollback_migration(conn_str, progress_callback=print)
        else:
            print("Rollback cancelled")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
