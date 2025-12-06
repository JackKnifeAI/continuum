#!/usr/bin/env python3
"""
PostgreSQL Migration Example
=============================

Complete example of migrating CONTINUUM from SQLite to PostgreSQL.

Usage:
    python postgres_migration.py --sqlite /path/to/memory.db --postgres postgresql://user:pass@host/db
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from continuum.storage import (
    migrate_sqlite_to_postgres,
    get_backend,
    PostgresBackend,
    SQLiteBackend,
    MigrationResult
)


def show_progress(msg: str):
    """Progress callback for migration"""
    print(f"  {msg}")


def compare_backends(sqlite_path: str, postgres_conn: str):
    """Compare data between SQLite and PostgreSQL backends"""
    print("\n=== Comparing Backends ===")

    sqlite = SQLiteBackend(db_path=sqlite_path)
    postgres = PostgresBackend(connection_string=postgres_conn)

    # Get backend info
    sqlite_info = sqlite.get_backend_info()
    postgres_info = postgres.get_backend_info()

    print(f"\nSQLite:")
    print(f"  Version: {sqlite_info['version']}")
    print(f"  Features: {', '.join(sqlite_info['features'])}")

    print(f"\nPostgreSQL:")
    print(f"  Version: {postgres_info['version']}")
    print(f"  Features: {', '.join(postgres_info['features'])}")

    # Compare row counts
    print("\n=== Row Counts ===")
    tables = ['entities', 'auto_messages', 'decisions', 'attention_links', 'compound_concepts', 'tenants']

    for table in tables:
        try:
            sqlite_count = sqlite.execute(f"SELECT COUNT(*) FROM {table}")[0][0]
            postgres_count = postgres.execute(f"SELECT COUNT(*) FROM {table}")[0][0]

            status = "✓" if sqlite_count == postgres_count else "✗"
            print(f"{status} {table:20s}: SQLite={sqlite_count:6d}, PostgreSQL={postgres_count:6d}")
        except Exception as e:
            print(f"✗ {table:20s}: Error - {e}")

    # Health checks
    print("\n=== Health Checks ===")
    print(f"SQLite:     {'✓ Healthy' if sqlite.is_healthy() else '✗ Unhealthy'}")
    print(f"PostgreSQL: {'✓ Healthy' if postgres.is_healthy() else '✗ Unhealthy'}")

    # Connection stats
    print("\n=== Connection Stats ===")
    sqlite_stats = sqlite.get_stats()
    postgres_stats = postgres.get_stats()

    print(f"SQLite:")
    print(f"  Created: {sqlite_stats['created']}, Open: {sqlite_stats['current_open']}, Pool: {sqlite_stats['pool_size']}")

    print(f"PostgreSQL:")
    print(f"  Created: {postgres_stats['created']}, Open: {postgres_stats['current_open']}, Pool: {postgres_stats['pool_size']}")
    print(f"  Hits: {postgres_stats['pool_hits']}, Misses: {postgres_stats['pool_misses']}")


def main():
    parser = argparse.ArgumentParser(description="Migrate CONTINUUM from SQLite to PostgreSQL")
    parser.add_argument("--sqlite", required=True, help="Path to SQLite database file")
    parser.add_argument("--postgres", required=True, help="PostgreSQL connection string")
    parser.add_argument("--batch-size", type=int, default=1000, help="Migration batch size")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation after migration")
    parser.add_argument("--compare", action="store_true", help="Compare backends after migration")

    args = parser.parse_args()

    print("=" * 60)
    print("CONTINUUM: SQLite → PostgreSQL Migration")
    print("=" * 60)

    print(f"\nSource:      {args.sqlite}")
    print(f"Destination: {args.postgres}")
    print(f"Batch size:  {args.batch_size}")
    print(f"Validation:  {'Disabled' if args.no_validate else 'Enabled'}")

    # Check if SQLite file exists
    if not Path(args.sqlite).exists():
        print(f"\n✗ Error: SQLite file not found: {args.sqlite}")
        return 1

    # Run migration
    print("\n" + "=" * 60)
    print("Starting Migration")
    print("=" * 60 + "\n")

    result = migrate_sqlite_to_postgres(
        sqlite_path=args.sqlite,
        postgres_connection=args.postgres,
        batch_size=args.batch_size,
        validate=not args.no_validate,
        progress_callback=show_progress
    )

    # Show results
    print("\n" + "=" * 60)
    print("Migration Results")
    print("=" * 60)

    if result.success:
        print("\n✓ Migration completed successfully!")
    else:
        print("\n✗ Migration failed!")

    print(f"\nDuration: {result.duration_seconds:.2f} seconds")
    print(f"Started:  {result.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished: {result.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\nRows Migrated:")
    total_rows = 0
    for table, count in result.rows_migrated.items():
        print(f"  {table:20s}: {count:6d} rows")
        total_rows += count
    print(f"  {'TOTAL':20s}: {total_rows:6d} rows")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  ✗ {error}")

    # Compare backends if requested
    if args.compare and result.success:
        compare_backends(args.sqlite, args.postgres)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
