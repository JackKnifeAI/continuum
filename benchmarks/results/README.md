# CONTINUUM Benchmark Results

This directory contains benchmark results for various test runs.

## File Naming Convention

Results files follow this pattern:
```
{test_name}_{timestamp}_{scale}.md

Examples:
- million_node_results.md (latest run, default)
- million_node_2025-12-06_1000000.md (specific run with timestamp)
- scale_test_results.md
```

## Result Files

### million_node_results.md

Latest comprehensive benchmark at 1M nodes / 5M edges scale.

**Contents:**
- Database metrics (size, memory)
- Query performance (point lookups, traversals, etc.)
- Concurrency tests
- Index impact analysis
- Scaling recommendations

**Updated:** After each million node benchmark run

---

## Comparing Results

To compare performance across different runs:

```bash
# Compare two result files
diff million_node_2025-12-06.md million_node_2025-12-07.md

# Extract just the performance table
grep -A 20 "SQLite Performance" million_node_results.md
```

### Key Metrics to Track

1. **Database Size** - Should be stable for same dataset
2. **Point Lookup Performance** - Should be < 1ms average
3. **1-Hop Traversal** - Should be < 10ms average
4. **Concurrent Throughput** - Should be > 1000 ops/sec total
5. **Peak Memory** - Monitor for memory leaks

### Performance Regression Detection

If performance degrades significantly between runs:

1. **Check hardware:**
   - CPU throttling
   - Disk I/O saturation
   - Memory pressure

2. **Check database:**
   - Indexes present (`PRAGMA index_list`)
   - WAL mode enabled (`PRAGMA journal_mode`)
   - Statistics up to date (`ANALYZE` run)

3. **Check code:**
   - Connection pooling configured
   - Queries optimized
   - No N+1 query patterns

---

## Baseline Performance

### Reference System

Update this with your actual hardware:

```yaml
CPU: [Your CPU Model]
RAM: [Your RAM Amount]
Disk: [SSD/HDD Type]
OS: [Operating System]
Python: [Python Version]
SQLite: [SQLite Version]
```

### Expected Performance (1M nodes, 5M edges)

| Test | Target | Notes |
|------|--------|-------|
| Database Creation | < 10 min | With indexes and FTS5 |
| Database Size | 2-3 GB | Depends on data size |
| Point Lookups | > 1000 ops/sec | With B-tree indexes |
| Text Search (LIKE) | > 10 ops/sec | Full table scan |
| FTS5 Search | > 500 ops/sec | Inverted index |
| 1-Hop Traversal | > 100 ops/sec | Indexed joins |
| 2-Hop Traversal | > 20 ops/sec | 2 joins |
| 3-Hop Traversal | > 5 ops/sec | 3 joins, use sparingly |
| Concurrent Reads | > 1000 total ops/sec | 10 threads |

---

## Historical Results

Track performance over time:

| Date | Nodes | Edges | DB Size | Point Lookup | 1-Hop | Notes |
|------|-------|-------|---------|--------------|-------|-------|
| 2025-12-06 | 1M | 5M | 2.5 GB | 2000 ops/s | 250 ops/s | Initial baseline |
| [Add yours] | | | | | | |

---

**Pattern persists. Performance scales. Memory endures.**

PHOENIX-TESLA-369-AURORA 🌗
