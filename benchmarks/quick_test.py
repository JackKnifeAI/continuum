#!/usr/bin/env python3
"""
Quick Benchmark Test - Verify infrastructure works before running full million node test
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from million_node_test import (
    create_sqlite_database,
    benchmark_point_lookups,
    benchmark_text_search,
    benchmark_graph_traversal,
    benchmark_aggregations,
    SQLiteBackend,
    PI_PHI
)
import tempfile

def main():
    print("="*70)
    print("CONTINUUM Benchmark Infrastructure Test")
    print(f"π×φ = {PI_PHI}")
    print("="*70)

    # Create small test database
    db_path = Path(tempfile.mktemp(suffix='.db', prefix='continuum_quick_test_'))

    try:
        print("\n[1/5] Creating test database (1000 nodes, 5000 edges)...")
        metrics = create_sqlite_database(db_path, 1000, 5000, with_indexes=True, with_fts=True)
        print(f"✓ Created: {metrics.total_size_mb:.2f} MB")

        print("\n[2/5] Testing point lookups...")
        storage = SQLiteBackend(db_path=str(db_path))
        result = benchmark_point_lookups(storage, 1000, num_queries=100)
        print(f"✓ {result.test_name}: {result.ops_per_sec:,.0f} ops/sec")

        print("\n[3/5] Testing text search...")
        result = benchmark_text_search(storage, num_queries=10)
        print(f"✓ {result.test_name}: {result.ops_per_sec:,.0f} ops/sec")

        print("\n[4/5] Testing graph traversal...")
        result = benchmark_graph_traversal(storage, 1000, hops=2, num_queries=10)
        print(f"✓ {result.test_name}: {result.ops_per_sec:,.0f} ops/sec")

        print("\n[5/5] Testing aggregations...")
        result = benchmark_aggregations(storage, num_queries=10)
        print(f"✓ {result.test_name}: {result.ops_per_sec:,.0f} ops/sec")

        storage.close_all()

        print("\n" + "="*70)
        print("✓ All tests passed! Benchmark infrastructure is working.")
        print("="*70)
        print("\nReady to run full million node benchmark:")
        print("  python3 benchmarks/million_node_test.py")
        print("\nPHOENIX-TESLA-369-AURORA 🌗")

    finally:
        if db_path.exists():
            db_path.unlink()
            print(f"\nCleaned up test database")


if __name__ == '__main__':
    main()
