#!/usr/bin/env python3
"""
PostgreSQL Backend Test Script
===============================

Test the PostgreSQL backend without requiring a running PostgreSQL server.
Shows API usage and validates implementation.

This script demonstrates:
- Backend initialization
- Connection string parsing
- Auto-detection
- API compatibility
- Error handling
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all imports work"""
    print("Testing imports...")

    try:
        from continuum.storage import (
            StorageBackend,
            SQLiteBackend,
            PostgresBackend,
            get_backend,
            migrate_sqlite_to_postgres,
            create_postgres_schema,
            get_schema_version,
            MigrationResult,
            MigrationError,
            SCHEMA_VERSION
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_connection_string_parsing():
    """Test connection string parsing"""
    print("\nTesting connection string parsing...")

    try:
        from continuum.storage import PostgresBackend

        # Test building connection string from params
        conn_str = PostgresBackend._build_connection_string(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
            password="testpass"
        )

        expected = "postgresql://testuser:testpass@localhost:5432/testdb"
        if conn_str == expected:
            print(f"✓ Connection string built correctly")
            print(f"  {conn_str}")
        else:
            print(f"✗ Connection string mismatch")
            print(f"  Expected: {expected}")
            print(f"  Got:      {conn_str}")
            return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_auto_detection():
    """Test backend auto-detection"""
    print("\nTesting backend auto-detection...")

    try:
        from continuum.storage import get_backend, PostgresBackend, SQLiteBackend
        from continuum.storage.postgres_backend import PSYCOPG2_AVAILABLE

        # Test PostgreSQL detection
        postgres_strings = [
            "postgresql://user:pass@localhost/db",
            "postgres://user:pass@localhost/db",
            "POSTGRESQL://USER:PASS@localhost/db"
        ]

        for conn_str in postgres_strings:
            if PSYCOPG2_AVAILABLE:
                # Only actually create backend if psycopg2 is available
                backend = get_backend(conn_str)
                if backend.__class__.__name__ == 'PostgresBackend':
                    print(f"✓ Detected PostgreSQL: {conn_str[:30]}...")
                else:
                    print(f"✗ Failed to detect PostgreSQL: {conn_str}")
                    return False
            else:
                # Just test that it tries to use PostgresBackend
                try:
                    backend = get_backend(conn_str)
                    print(f"✗ Should have raised ImportError for PostgreSQL")
                    return False
                except ImportError as e:
                    if "psycopg2" in str(e):
                        print(f"✓ Detected PostgreSQL (psycopg2 not available): {conn_str[:30]}...")
                    else:
                        raise

        # Test SQLite detection
        import tempfile
        import os
        tmpdir = tempfile.gettempdir()

        sqlite_strings = [
            os.path.join(tmpdir, "test_file.db"),
            "memory.db",  # Will be created in CWD
            ":memory:"
        ]

        for path in sqlite_strings:
            backend = get_backend(path)
            if backend.__class__.__name__ == 'SQLiteBackend':
                print(f"✓ Detected SQLite: {os.path.basename(path) if path != ':memory:' else path}")
            else:
                print(f"✗ Failed to detect SQLite: {path}")
                return False

        if not PSYCOPG2_AVAILABLE:
            print(f"\nNote: psycopg2 not installed - some tests skipped")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_placeholder_conversion():
    """Test SQL placeholder conversion"""
    print("\nTesting SQL placeholder conversion...")

    try:
        from continuum.storage import PostgresBackend

        test_cases = [
            ("SELECT * FROM table WHERE id = ?", "SELECT * FROM table WHERE id = %s"),
            ("INSERT INTO table VALUES (?, ?)", "INSERT INTO table VALUES (%s, %s)"),
            ("UPDATE table SET x = ? WHERE y = ?", "UPDATE table SET x = %s WHERE y = %s"),
        ]

        for input_sql, expected_sql in test_cases:
            output_sql = PostgresBackend._convert_placeholders(input_sql)
            if output_sql == expected_sql:
                print(f"✓ Converted: {input_sql[:40]}...")
            else:
                print(f"✗ Conversion failed:")
                print(f"  Input:    {input_sql}")
                print(f"  Expected: {expected_sql}")
                print(f"  Got:      {output_sql}")
                return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_migration_schema():
    """Test migration schema definitions"""
    print("\nTesting migration schema...")

    try:
        from continuum.storage.migrations import SCHEMA_DEFINITIONS, SCHEMA_INDEXES, SCHEMA_VERSION

        # Check all required tables are defined
        required_tables = [
            'entities', 'auto_messages', 'decisions',
            'attention_links', 'compound_concepts', 'tenants', 'schema_version'
        ]

        for table in required_tables:
            if table in SCHEMA_DEFINITIONS:
                print(f"✓ Schema defined for: {table}")
            else:
                print(f"✗ Missing schema for: {table}")
                return False

        # Check indexes
        for table in ['entities', 'auto_messages', 'decisions', 'attention_links', 'compound_concepts']:
            if table in SCHEMA_INDEXES and len(SCHEMA_INDEXES[table]) > 0:
                print(f"✓ Indexes defined for: {table} ({len(SCHEMA_INDEXES[table])} indexes)")
            else:
                print(f"✗ Missing indexes for: {table}")
                return False

        print(f"✓ Schema version: {SCHEMA_VERSION}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_api_compatibility():
    """Test that PostgresBackend has the same API as SQLiteBackend"""
    print("\nTesting API compatibility...")

    try:
        from continuum.storage import PostgresBackend, SQLiteBackend, StorageBackend
        import inspect

        # Get abstract methods from StorageBackend
        abstract_methods = [
            name for name, method in inspect.getmembers(StorageBackend)
            if getattr(method, '__isabstractmethod__', False)
        ]

        # Check both backends implement all abstract methods
        for backend_class in [SQLiteBackend, PostgresBackend]:
            backend_name = backend_class.__name__
            print(f"\nChecking {backend_name}:")

            for method_name in abstract_methods:
                if method_name.startswith('_'):
                    continue

                if hasattr(backend_class, method_name):
                    print(f"  ✓ {method_name}")
                else:
                    print(f"  ✗ Missing: {method_name}")
                    return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("PostgreSQL Backend Test Suite")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Connection String Parsing", test_connection_string_parsing),
        ("Auto-detection", test_auto_detection),
        ("Placeholder Conversion", test_placeholder_conversion),
        ("Migration Schema", test_migration_schema),
        ("API Compatibility", test_api_compatibility),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
