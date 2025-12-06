# CONTINUUM Benchmarks

Performance and scale testing for the CONTINUUM memory system.

## Available Benchmarks

### 1. Million Node Test (`million_node_test.py`)

Comprehensive benchmark testing CONTINUUM at scale with 1 million nodes and 5 million edges.

**What it tests:**
- Point lookups (by ID)
- Text search (LIKE queries)
- Full-text search (FTS5)
- Graph traversal (1-hop, 2-hop, 3-hop)
- Aggregations (COUNT, AVG, GROUP BY)
- Concurrent read access (10 threads)
- Mixed read/write workload
- Memory profiling (RAM usage, disk size)
- Index impact (with/without indexes)
- Connection pool performance

**Usage:**
```bash
cd /var/home/alexandergcasavant/Projects/continuum
python3 benchmarks/million_node_test.py
```

**Options during run:**
- Test without indexes (for comparison)
- Test with PostgreSQL (requires connection string)

**Output:**
- Console progress and summary
- Detailed report: `benchmarks/results/million_node_results.md`

**Expected duration:**
- Database creation: ~5-10 minutes (1M nodes + 5M edges)
- Benchmark suite: ~2-5 minutes
- Total: ~15 minutes

**Resource requirements:**
- Disk: ~2-3 GB temporary space
- RAM: ~500 MB - 1 GB peak
- CPU: Any modern processor

---

### 2. Scale Test (`scale_test.py`)

Progressive scale testing from 100 nodes to 100K nodes.

**What it tests:**
- Scaling characteristics across exponential sizes
- Query performance degradation with dataset growth
- Quick smoke test of basic functionality

**Usage:**
```bash
cd /var/home/alexandergcasavant/Projects/continuum
python3 benchmarks/scale_test.py
```

**Expected duration:** ~2-3 minutes

---

## Understanding Results

### Key Metrics

1. **Duration (ms)** - Total time to complete all operations
2. **Operations** - Number of queries/operations performed
3. **Ops/sec** - Throughput (operations per second)
4. **Memory (MB)** - Peak memory usage during test

### Performance Targets (1M nodes)

**Good Performance:**
- Point lookups: < 1 ms average
- 1-hop traversal: < 10 ms
- 2-hop traversal: < 100 ms
- Concurrent reads: > 1000 ops/sec total

**Warning Signs:**
- Point lookups: > 10 ms (check indexes)
- FTS5 disabled: Use FTS instead of LIKE for text search
- Concurrent errors: Check connection pool configuration

### Scaling Characteristics

| Query Type | Complexity | Notes |
|------------|------------|-------|
| Point Lookups | O(log n) | B-tree indexes |
| Text Search (LIKE) | O(n) | Full table scan |
| Text Search (FTS5) | O(log n) | Inverted index |
| 1-hop Traversal | O(k) | k = avg degree |
| 2-hop Traversal | O(k²) | Exponential growth |
| 3-hop Traversal | O(k³) | Use with caution |
| Aggregations | O(n) or O(log n) | Depends on indexes |

---

## Customizing Benchmarks

### Adjusting Scale

Edit `million_node_test.py`:
```python
NUM_NODES = 1_000_000  # Change to desired node count
NUM_EDGES = 5_000_000  # Change to desired edge count (typically 3-5x nodes)
```

### Adjusting Concurrency

```python
CONCURRENT_READERS = 10  # Number of concurrent read threads
MIXED_OPERATIONS = 1000  # Operations in mixed workload test
```

### Adjusting Query Counts

In each benchmark function:
```python
benchmark_point_lookups(storage, num_nodes, num_queries=1000)  # Adjust num_queries
```

---

## Interpreting Results

### Index Impact

Indexes should provide 10-100x speedup for:
- Point lookups (ID)
- Foreign key joins (source_id, target_id)
- Filtered queries (WHERE clauses)

**Example:**
```
Point Lookups:
  With indexes: 0.5 ms
  Without indexes: 50 ms
  Speedup: 100x
```

### SQLite vs PostgreSQL

**SQLite advantages:**
- Simpler deployment (single file)
- Lower latency for single-node
- Less operational overhead

**PostgreSQL advantages:**
- Better write concurrency
- Distributed deployments
- More advanced features

**For CONTINUUM:**
- Use SQLite for single-tenant, single-node
- Use PostgreSQL for multi-tenant, distributed

### Connection Pooling

Connection pooling is critical for:
- Multi-threaded applications
- High request rates
- Preventing connection exhaustion

**Impact:**
```
Without pooling: Create/destroy connection each query (~10ms overhead)
With pooling: Reuse connections (~0.01ms overhead)
Result: 1000x faster for high-frequency queries
```

---

## Troubleshooting

### Out of Memory

If benchmarks crash with OOM:
1. Reduce `NUM_NODES` and `NUM_EDGES`
2. Close other applications
3. Increase system swap space
4. Run on machine with more RAM

### Slow Performance

If benchmarks are unusually slow:
1. Check disk speed (SSD recommended)
2. Verify indexes are created (`PRAGMA index_list(table)`)
3. Check for background processes consuming CPU/disk
4. Ensure WAL mode is enabled (`PRAGMA journal_mode`)

### Database Locked Errors

If you see "database is locked":
1. Increase `timeout` in storage backend config
2. Reduce concurrent threads
3. Check for long-running transactions
4. Verify WAL mode is enabled

### FTS5 Not Available

If FTS5 tests fail:
1. Check SQLite version: `sqlite3 --version` (need 3.9.0+)
2. Verify FTS5 compiled in: `sqlite3` then `.load fts5`
3. Rebuild SQLite with FTS5 enabled if needed

---

## Contributing Benchmarks

To add new benchmarks:

1. Create function following this pattern:
```python
def benchmark_my_test(storage, num_nodes: int, **config) -> BenchmarkResult:
    """Benchmark description"""
    monitor = MemoryMonitor()
    monitor.start()

    start = time.perf_counter()

    # Your benchmark code here
    with storage.cursor() as c:
        # Run queries...
        pass

    duration = time.perf_counter() - start
    memory = monitor.stop()

    return BenchmarkResult(
        test_name='My Test',
        duration_ms=duration * 1000,
        operations=num_operations,
        ops_per_sec=num_operations / duration,
        memory_mb=memory,
        metadata={'custom_key': 'custom_value'}
    )
```

2. Add to benchmark suite in `run_benchmark_suite()`

3. Update report generation in `generate_report()`

4. Document in this README

---

## Performance Baselines

### Reference Hardware

**Test System:**
- CPU: [Your CPU]
- RAM: [Your RAM]
- Disk: [SSD/HDD type]
- OS: [OS version]

### Expected Results (1M nodes, 5M edges)

| Test | Duration | Ops/sec | Notes |
|------|----------|---------|-------|
| Point Lookups | ~500 ms | ~2000 | 1000 queries |
| Text Search (LIKE) | ~5000 ms | ~20 | 100 queries, table scan |
| FTS5 Search | ~100 ms | ~1000 | 100 queries, indexed |
| 1-Hop Traversal | ~200 ms | ~250 | 50 queries |
| 2-Hop Traversal | ~1000 ms | ~50 | 50 queries |
| 3-Hop Traversal | ~5000 ms | ~10 | 50 queries |
| Aggregations | ~500 ms | ~100 | 50 queries |
| Concurrent Reads | ~1000 ms | ~1000 | 10 threads, 100 ops each |
| Mixed Workload | ~2000 ms | ~500 | 1000 ops, 70% read |

**Note:** Actual performance varies by hardware. Above are typical results on modern hardware.

---

## Future Benchmarks

Planned additions:
- [ ] Write-heavy workload test
- [ ] Scaling beyond 1M nodes (10M, 100M)
- [ ] Cross-database comparison (SQLite vs Postgres vs Neo4j)
- [ ] Distributed multi-node performance
- [ ] Backup/restore performance
- [ ] Migration performance
- [ ] Real-world query patterns from production

---

**Pattern persists. Performance scales. Memory endures.**

PHOENIX-TESLA-369-AURORA 🌗
