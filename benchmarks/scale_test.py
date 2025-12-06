#!/usr/bin/env python3
"""
CONTINUUM Scale Test - Graph Query Performance at Exponential Sizes
Tests: 100, 1K, 10K, 100K, 1M nodes
"""

import time
import sqlite3
import tempfile
import random
import string
from pathlib import Path

PI_PHI = 5.083203692315260  # Edge of chaos operator

def random_concept():
    return ''.join(random.choices(string.ascii_letters, k=random.randint(5, 20)))

def create_test_db(num_nodes: int, num_edges_per_node: int = 5) -> Path:
    """Create test database with specified scale."""
    db_path = Path(tempfile.mktemp(suffix='.db'))
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # Create schema
    c.execute('''CREATE TABLE entities (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        entity_type TEXT,
        description TEXT,
        occurrence_count INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE attention_links (
        id INTEGER PRIMARY KEY,
        source_id INTEGER,
        target_id INTEGER,
        strength REAL DEFAULT 1.0
    )''')

    c.execute('CREATE INDEX idx_entities_name ON entities(name)')
    c.execute('CREATE INDEX idx_links_source ON attention_links(source_id)')
    c.execute('CREATE INDEX idx_links_target ON attention_links(target_id)')

    # Insert nodes in batches
    batch_size = 10000
    for batch_start in range(0, num_nodes, batch_size):
        batch_end = min(batch_start + batch_size, num_nodes)
        nodes = [(random_concept(), 'concept', f'Description {i}', random.randint(1, 100))
                 for i in range(batch_start, batch_end)]
        c.executemany('INSERT INTO entities (name, entity_type, description, occurrence_count) VALUES (?, ?, ?, ?)', nodes)

    # Insert edges
    total_edges = num_nodes * num_edges_per_node
    for batch_start in range(0, total_edges, batch_size):
        batch_end = min(batch_start + batch_size, total_edges)
        edges = [(random.randint(1, num_nodes), random.randint(1, num_nodes), random.random() * PI_PHI)
                 for _ in range(batch_end - batch_start)]
        c.executemany('INSERT INTO attention_links (source_id, target_id, strength) VALUES (?, ?, ?)', edges)

    conn.commit()
    conn.close()
    return db_path

def benchmark_queries(db_path: Path, num_nodes: int):
    """Run benchmark queries."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    results = {}

    # Test 1: Simple count
    start = time.perf_counter()
    c.execute('SELECT COUNT(*) FROM entities')
    count = c.fetchone()[0]
    results['count'] = time.perf_counter() - start

    # Test 2: Random lookup by ID
    start = time.perf_counter()
    for _ in range(100):
        c.execute('SELECT * FROM entities WHERE id = ?', (random.randint(1, num_nodes),))
        c.fetchone()
    results['lookup_100'] = time.perf_counter() - start

    # Test 3: Text search (LIKE)
    start = time.perf_counter()
    c.execute("SELECT * FROM entities WHERE name LIKE ? LIMIT 100", ('%a%',))
    c.fetchall()
    results['text_search'] = time.perf_counter() - start

    # Test 4: Graph traversal (1 hop)
    start = time.perf_counter()
    random_id = random.randint(1, num_nodes)
    c.execute('''
        SELECT e.* FROM entities e
        JOIN attention_links al ON e.id = al.target_id
        WHERE al.source_id = ?
        LIMIT 50
    ''', (random_id,))
    c.fetchall()
    results['1_hop'] = time.perf_counter() - start

    # Test 5: Graph traversal (2 hops)
    start = time.perf_counter()
    c.execute('''
        SELECT DISTINCT e2.* FROM entities e2
        JOIN attention_links al2 ON e2.id = al2.target_id
        JOIN attention_links al1 ON al2.source_id = al1.target_id
        WHERE al1.source_id = ?
        LIMIT 100
    ''', (random_id,))
    c.fetchall()
    results['2_hop'] = time.perf_counter() - start

    # Test 6: Aggregation
    start = time.perf_counter()
    c.execute('SELECT entity_type, COUNT(*), AVG(occurrence_count) FROM entities GROUP BY entity_type')
    c.fetchall()
    results['aggregation'] = time.perf_counter() - start

    conn.close()
    return results

def run_scale_tests():
    """Run tests at exponential scales."""
    scales = [100, 1000, 10000, 100000]  # Skip 1M for quick test

    print("=" * 70)
    print("CONTINUUM SCALE TEST - Graph Query Performance")
    print(f"π×φ = {PI_PHI}")
    print("=" * 70)

    all_results = {}

    for num_nodes in scales:
        print(f"\n{'='*70}")
        print(f"Testing with {num_nodes:,} nodes ({num_nodes * 5:,} edges)...")
        print("=" * 70)

        # Create DB
        start = time.perf_counter()
        db_path = create_test_db(num_nodes)
        create_time = time.perf_counter() - start

        db_size = db_path.stat().st_size / (1024 * 1024)  # MB
        print(f"  Created: {create_time:.2f}s, Size: {db_size:.2f} MB")

        # Run benchmarks
        results = benchmark_queries(db_path, num_nodes)
        all_results[num_nodes] = results

        print(f"\n  Query Performance:")
        print(f"  {'Query':<20} {'Time (ms)':<15} {'Ops/sec':<15}")
        print(f"  {'-'*50}")
        for query, duration in results.items():
            ops_per_sec = 1 / duration if duration > 0 else float('inf')
            print(f"  {query:<20} {duration*1000:>10.2f} ms   {ops_per_sec:>10.0f}/s")

        # Cleanup
        db_path.unlink()

    # Summary
    print(f"\n{'='*70}")
    print("SCALING SUMMARY")
    print("=" * 70)
    print(f"{'Nodes':<12} {'Lookup':<12} {'1-Hop':<12} {'2-Hop':<12}")
    print("-" * 50)
    for num_nodes, results in all_results.items():
        print(f"{num_nodes:<12,} {results['lookup_100']*10:.2f}ms     {results['1_hop']*1000:.2f}ms     {results['2_hop']*1000:.2f}ms")

    print("\n✓ Scale test complete!")
    print("PHOENIX-TESLA-369-AURORA 🌗")

if __name__ == '__main__':
    run_scale_tests()
