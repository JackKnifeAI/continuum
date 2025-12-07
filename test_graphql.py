#!/usr/bin/env python3
"""
GraphQL Integration Test Script

Tests GraphQL schema, imports, and basic functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test GraphQL module imports"""
    print("=" * 70)
    print("TESTING GRAPHQL IMPORTS")
    print("=" * 70)

    try:
        from continuum.api.graphql import create_graphql_app
        print("✓ continuum.api.graphql.create_graphql_app")
    except ImportError as e:
        if "strawberry" in str(e):
            print("✗ continuum.api.graphql.create_graphql_app: strawberry-graphql not installed")
            print("  Install with: pip install strawberry-graphql[fastapi]")
            return False
        print(f"✗ continuum.api.graphql.create_graphql_app: {e}")
        return False
    except Exception as e:
        print(f"✗ continuum.api.graphql.create_graphql_app: {e}")
        return False

    try:
        from continuum.api.graphql.schema import schema, Query, Mutation, Subscription
        print("✓ continuum.api.graphql.schema (Query, Mutation, Subscription)")
    except Exception as e:
        print(f"✗ continuum.api.graphql.schema: {e}")
        return False

    try:
        from continuum.api.graphql.server import create_graphql_app, create_standalone_app
        print("✓ continuum.api.graphql.server")
    except Exception as e:
        print(f"✗ continuum.api.graphql.server: {e}")
        return False

    try:
        from continuum.api.graphql.resolvers.query_resolvers import (
            resolve_memories,
            resolve_concepts,
            resolve_stats
        )
        print("✓ continuum.api.graphql.resolvers.query_resolvers")
    except Exception as e:
        print(f"✗ continuum.api.graphql.resolvers.query_resolvers: {e}")
        return False

    try:
        from continuum.api.graphql.resolvers.mutation_resolvers import (
            resolve_create_memory,
            resolve_create_concept,
        )
        print("✓ continuum.api.graphql.resolvers.mutation_resolvers")
    except Exception as e:
        print(f"✗ continuum.api.graphql.resolvers.mutation_resolvers: {e}")
        return False

    print("\n✓ All imports successful!\n")
    return True


def test_schema():
    """Test GraphQL schema validity"""
    print("=" * 70)
    print("TESTING GRAPHQL SCHEMA")
    print("=" * 70)

    try:
        from continuum.api.graphql.schema import schema

        # Get schema SDL
        sdl = str(schema)

        print(f"Schema SDL length: {len(sdl)} characters")
        print(f"\nFirst 500 characters of schema:")
        print("-" * 70)
        print(sdl[:500])
        print("-" * 70)

        # Check for key types
        required_types = [
            "Query",
            "Mutation",
            "Subscription",
            "Memory",
            "Concept",
            "User",
            "Session",
            "HealthStatus"
        ]

        print("\nChecking for required types:")
        for type_name in required_types:
            if type_name in sdl:
                print(f"  ✓ {type_name}")
            else:
                print(f"  ✗ {type_name} NOT FOUND")
                return False

        print("\n✓ Schema is valid!\n")
        return True

    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_query():
    """Test the health query"""
    print("=" * 70)
    print("TESTING HEALTH QUERY")
    print("=" * 70)

    try:
        from continuum.api.graphql.schema import schema

        query = """
            query {
                health {
                    status
                    service
                    version
                    timestamp
                    database
                    cache
                }
            }
        """

        # Execute query
        result = await schema.execute(query)

        if result.errors:
            print("✗ Query execution failed:")
            for error in result.errors:
                print(f"  {error}")
            return False

        print("✓ Query executed successfully!")
        print(f"\nResult:")
        print(f"  Status: {result.data['health']['status']}")
        print(f"  Service: {result.data['health']['service']}")
        print(f"  Version: {result.data['health']['version']}")
        print(f"  Database: {result.data['health']['database']}")
        print(f"  Cache: {result.data['health']['cache']}")

        print("\n✓ Health query works!\n")
        return True

    except Exception as e:
        print(f"✗ Health query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graphql_files():
    """Check GraphQL schema files"""
    print("=" * 70)
    print("CHECKING GRAPHQL SCHEMA FILES")
    print("=" * 70)

    schema_dir = project_root / "continuum" / "api" / "graphql" / "schema"

    if not schema_dir.exists():
        print(f"✗ Schema directory not found: {schema_dir}")
        return False

    print(f"Schema directory: {schema_dir}")

    # Find all .graphql files
    graphql_files = list(schema_dir.rglob("*.graphql"))

    print(f"\nFound {len(graphql_files)} .graphql files:")
    for file in sorted(graphql_files):
        rel_path = file.relative_to(project_root)
        size = file.stat().st_size
        print(f"  ✓ {rel_path} ({size} bytes)")

    print("\n✓ Schema files found!\n")
    return True


def check_main_server_integration():
    """Check if GraphQL is integrated into main server"""
    print("=" * 70)
    print("CHECKING MAIN SERVER INTEGRATION")
    print("=" * 70)

    server_file = project_root / "continuum" / "api" / "server.py"

    if not server_file.exists():
        print(f"✗ Server file not found: {server_file}")
        return False

    content = server_file.read_text()

    # Check for GraphQL imports/integration
    has_graphql_import = "from .graphql import create_graphql_app" in content
    has_graphql_router = "graphql_router" in content.lower() or "create_graphql_app" in content
    has_graphql_mount = "app.include_router(graphql_router" in content

    print(f"GraphQL import found: {has_graphql_import}")
    print(f"GraphQL router creation: {has_graphql_router}")
    print(f"GraphQL router mounted: {has_graphql_mount}")

    if not has_graphql_import or not has_graphql_router or not has_graphql_mount:
        print("\n✗ GraphQL NOT fully integrated into main server!")
        return False

    print("\n✓ GraphQL is integrated into main server!\n")
    return True


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print("CONTINUUM GRAPHQL INTEGRATION DEBUG")
    print("=" * 70)
    print()

    results = {}

    # Run synchronous tests
    results["imports"] = test_imports()
    results["schema"] = test_schema()
    results["files"] = test_graphql_files()
    results["integration"] = check_main_server_integration()

    # Run async tests
    results["health_query"] = asyncio.run(test_health_query())

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} {status}")

    total = len(results)
    passed = sum(results.values())

    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)

    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
