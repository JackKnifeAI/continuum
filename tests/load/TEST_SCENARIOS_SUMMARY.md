# CONTINUUM Load Test Scenarios - Summary

## Overview

Comprehensive load testing suite designed to validate CONTINUUM's performance under production workloads before launch.

**Total Test Coverage:**
- 4 major scenarios (Memory, Search, Federation, API)
- 6 user types with varying behavior patterns
- 50+ individual test tasks
- Custom load shapes (Step, Spike)
- Real-time metrics collection

---

## Test Scenarios Breakdown

### 1. Memory Operations (`memory_operations.py`)

**Purpose:** Test CRUD operations on the memory system

**Workload Distribution:**
```
READ Operations  (60%):
├── recall_memory (60%) - Memory context retrieval
├── get_stats (5%) - Statistics monitoring
└── list_entities (3%) - Entity browsing

WRITE Operations (35%):
├── learn_new_memory (20%) - Create new memories
├── update_memory (15%) - Update existing concepts
└── process_turn (2%) - Combined recall+learn

Mixed (5%):
└── Various verification operations
```

**Performance Targets:**
- 1,000 creates/minute
- 10,000 reads/minute
- 500 updates/minute
- 100 deletes/minute
- P95 latency: <100ms
- P99 latency: <500ms
- Error rate: <1%

**Key Metrics:**
- `concepts_extracted` - New concepts learned per request
- `concepts_found` - Concepts retrieved per recall
- `query_time_ms` - Database query performance

**Run Command:**
```bash
./run_load_tests.sh --scenario memory --users 500 --time 10m
```

---

### 2. Search Operations (`search.py`)

**Purpose:** Test search and retrieval capabilities under load

**Workload Distribution:**
```
Semantic Search (50%):
└── semantic_search - Context-aware search via /recall

Complex Queries (30%):
└── complex_semantic_search - Multi-concept queries

Entity Search (15%):
└── entity_search - Filtered entity retrieval by type

Pagination (5%):
└── pagination_search - Large result set handling

Targeted Recall (10%):
└── targeted_recall - Variable concept limits
```

**Performance Targets:**
- 1,000 semantic searches/minute
- 500 graph traversals/minute
- 2,000 full-text searches/minute
- P95 latency: <200ms
- P99 latency: <1000ms
- Error rate: <1%

**Key Metrics:**
- `concepts_found` - Search result quality
- `relationships_found` - Graph traversal depth
- `query_time_ms` - Search performance

**Run Command:**
```bash
./run_load_tests.sh --scenario search --users 300 --time 5m
```

---

### 3. Federation Operations (`federation.py`)

**Purpose:** Test peer-to-peer synchronization and distributed operations

**Workload Distribution:**
```
Contribution (40%):
└── contribute_memory - Share memories with federation

Sync Requests (30%):
└── request_sync - Request updates from peers

Discovery (20%):
└── discover_peers - Find and connect to peers

Conflict Resolution (10%):
└── simulate_conflict - Handle competing updates

Heartbeat (5%):
└── send_heartbeat - Keepalive messages
```

**Performance Targets:**
- 100 syncs/second
- 10 concurrent peer connections
- Graceful conflict handling
- P95 latency: <500ms
- P99 latency: <2000ms
- Error rate: <5% (higher tolerance for distributed systems)

**Key Metrics:**
- `sync_operations` - Total successful syncs
- `conflicts_detected` - Conflict resolution events
- `peer_count` - Active peer connections

**Run Command:**
```bash
./run_load_tests.sh --scenario federation --users 200 --time 5m
```

**Note:** Federation endpoints may return 404 if not yet implemented. Tests validate load patterns rather than functionality.

---

### 4. Full API Workload (`api.py`)

**Purpose:** Simulate realistic production usage with mixed operations

**Workload Distribution:**
```
READ Operations (60%):
├── recall_context (35%) - Context retrieval
├── check_stats (15%) - Statistics monitoring
├── browse_entities (10%) - Entity browsing
└── health_check (5%) - Health monitoring

WRITE Operations (30%):
├── learn_from_conversation (20%) - Learning new memories
└── process_full_turn (10%) - Turn processing

SEARCH Operations (10%):
├── semantic_search (8%) - Semantic queries
└── complex_search (2%) - Complex multi-concept search

User-Specific (5%):
└── user_specific_behavior - Based on user type
```

**User Types:**
```
1. Heavy Readers (33% of users):
   - 80% read operations
   - 20% write operations
   - Pattern: Browse → Recall → Stats

2. Balanced Users (33% of users):
   - 60% read operations
   - 40% write operations
   - Pattern: Recall → Learn → Search

3. Content Creators (33% of users):
   - 40% read operations
   - 60% write operations
   - Pattern: Learn → Learn → Recall
```

**Performance Targets:**
- 1,000 concurrent users
- 50,000 requests/minute
- P50 latency: <50ms
- P95 latency: <200ms
- P99 latency: <500ms
- Error rate: <1%
- Read/Write ratio: 60/40

**Key Metrics:**
- `total_rps` - Overall throughput
- `concurrent_users` - Active user count
- `response_time_percentiles` - Latency distribution

**Run Command:**
```bash
./run_load_tests.sh --scenario api --users 1000 --time 10m
```

---

## User Behavior Patterns

### RealisticAPIUser
- **Wait time:** 1-5 seconds between requests
- **Pattern:** Normal user think time
- **Usage:** Production simulation

### BurstTrafficUser
- **Wait time:** 0.1-0.5 seconds between requests
- **Pattern:** Rapid-fire requests
- **Usage:** Stress testing, traffic spikes

### SlowUser
- **Wait time:** 5-15 seconds between requests
- **Pattern:** Deliberate, thoughtful usage
- **Usage:** Long-term stability testing

---

## Load Shapes (Advanced)

### Step Load Pattern
**Purpose:** Find system breaking point

```
Step 1 (0-60s):    100 users
Step 2 (60-120s):  200 users
Step 3 (120-180s): 300 users
...continues until failure or 10 minutes
```

**Usage:**
```python
# Uncomment in locustfile.py:
users = StepLoadShape
```

### Spike Load Pattern
**Purpose:** Test resilience to traffic spikes

```
Warm up (0-60s):        100 users
Spike 1 (60-120s):    1,000 users
Cool down (120-180s):   200 users
Spike 2 (180-240s):   1,500 users
Recovery (240-300s):    100 users
```

**Usage:**
```python
# Uncomment in locustfile.py:
users = SpikeLoadShape
```

---

## Metrics Collection

### Standard Locust Metrics
- Request count (total, successful, failed)
- Response time (min, max, avg, median, p95, p99)
- Requests per second (RPS)
- Failure rate
- Response size

### Custom CONTINUUM Metrics
- `concepts_extracted` - Concepts learned per request
- `concepts_found` - Concepts retrieved per search
- `query_times` - Database query performance
- `sync_operations` - Federation sync count
- `conflicts_detected` - Conflict resolution events

### Collection Points
- Per-request hook: `@events.request.add_listener`
- Test start: `@events.test_start.add_listener`
- Test stop: `@events.test_stop.add_listener`

---

## Results Analysis

### Output Files
```
results/
├── load_test_TIMESTAMP.html           # Interactive HTML report
├── load_test_TIMESTAMP_stats.csv      # Request statistics
├── load_test_TIMESTAMP_exceptions.csv # Error details
├── load_test_TIMESTAMP_stats_history.csv # Time series
└── load_test_TIMESTAMP.log            # Full test log
```

### Analysis Tools

**1. Built-in HTML Report**
- Real-time charts
- Endpoint breakdown
- Error analysis
- Download as HTML

**2. Custom Analyzer**
```bash
./analyze_results.py results/load_test_TIMESTAMP_stats.csv
```

Provides:
- Overall summary
- Endpoint breakdown
- Top endpoints (most requested, slowest, highest errors)
- Performance analysis vs. targets
- Optimization recommendations

**3. Manual CSV Analysis**
```bash
# View statistics
column -t -s, results/load_test_*_stats.csv | less -S

# Extract P95 times
awk -F',' 'NR>1 {print $1, $9}' results/load_test_*_stats.csv

# Count error types
awk -F',' 'NR>1 {print $2}' results/load_test_*_exceptions.csv | sort | uniq -c
```

---

## Expected Test Results

### Quick Smoke Test (2 min, 50 users)
```
✓ Requests: ~5,000-10,000
✓ RPS: ~50-100
✓ P95: <200ms
✓ Error rate: <1%
```

### Memory Operations (10 min, 500 users)
```
✓ Requests: ~50,000-100,000
✓ Creates: ~10,000
✓ Reads: ~30,000+
✓ Updates: ~5,000
✓ P95: <100ms
✓ Error rate: <1%
```

### Search Operations (5 min, 300 users)
```
✓ Requests: ~30,000-50,000
✓ Semantic: ~15,000
✓ Complex: ~9,000
✓ Entity: ~4,500
✓ P95: <200ms
✓ Error rate: <1%
```

### Federation (5 min, 200 users)
```
✓ Requests: ~20,000-30,000
✓ Syncs: ~8,000-12,000
✓ Discoveries: ~4,000-6,000
✓ Conflicts: ~2,000-3,000
✓ P95: <500ms
✓ Error rate: <5%
```

### Full API (10 min, 1000 users)
```
✓ Requests: ~100,000-200,000
✓ RPS: ~200-300
✓ RPM: ~12,000-18,000
✓ P50: <50ms
✓ P95: <200ms
✓ P99: <500ms
✓ Error rate: <1%
```

---

## Common Issues and Solutions

### High Error Rates (>5%)

**Symptoms:**
- Many 500 errors
- Timeouts
- Connection refused

**Solutions:**
1. Check API server is running
2. Verify database connections
3. Increase connection pool size
4. Check resource limits (ulimit)
5. Review API logs for errors

### Slow Response Times (P95 >500ms)

**Symptoms:**
- Long wait times
- Degrading performance over time
- Increasing queue depth

**Solutions:**
1. Add database indexes
2. Enable caching
3. Optimize slow queries (EXPLAIN ANALYZE)
4. Increase API workers
5. Scale horizontally

### Low Throughput (<10,000 RPM)

**Symptoms:**
- Low RPS despite high user count
- Users waiting

**Solutions:**
1. Increase spawn rate
2. Reduce user wait time
3. Optimize endpoints
4. Scale API servers
5. Check network bandwidth

### Connection Errors

**Symptoms:**
- "Too many open files"
- Connection pool exhausted
- Timeout errors

**Solutions:**
```bash
# Increase file descriptors
ulimit -n 65535

# Increase DB connections (PostgreSQL)
# postgresql.conf:
max_connections = 200

# Use connection pooling
pool_size = 20
max_overflow = 10
```

---

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/load-test.yml
name: Load Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Nightly

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          pip install -r tests/load/requirements.txt
      - name: Start API
        run: continuum serve &
      - name: Run tests
        run: |
          cd tests/load
          ./run_load_tests.sh --scenario quick
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: tests/load/results/
```

### Pre-Release Checklist
```bash
# 1. Quick smoke test
./run_load_tests.sh --scenario quick

# 2. Individual scenarios
./run_load_tests.sh --scenario memory --users 500 --time 10m
./run_load_tests.sh --scenario search --users 300 --time 5m
./run_load_tests.sh --scenario federation --users 200 --time 5m

# 3. Full API test
./run_load_tests.sh --scenario api --users 1000 --time 10m

# 4. Stress test (find limits)
# Enable StepLoadShape in locustfile.py
locust -f locustfile.py --headless --run-time 15m

# 5. Spike resilience
# Enable SpikeLoadShape in locustfile.py
locust -f locustfile.py --headless --run-time 5m

# 6. Analyze all results
for f in results/*_stats.csv; do
    ./analyze_results.py "$f"
done
```

---

## Summary

**Created Files:**
```
tests/load/
├── config.py                      # Test configuration and targets
├── locustfile.py                  # Main orchestration and metrics
├── run_load_tests.sh             # Execution script
├── analyze_results.py            # Results analyzer
├── requirements.txt              # Dependencies
├── README.md                     # Comprehensive documentation
├── QUICK_START.md               # Quick reference
├── .gitignore                   # Git ignore rules
├── scenarios/
│   ├── __init__.py
│   ├── memory_operations.py     # Memory CRUD tests
│   ├── search.py                # Search tests
│   ├── federation.py            # Federation tests
│   └── api.py                   # Full API tests
└── results/                     # Test output (gitignored)
    └── .gitkeep
```

**Total Lines of Code:** ~2,500 lines
**Total Test Tasks:** 50+ individual tasks
**Scenario Coverage:** 4 major scenarios + custom shapes
**User Types:** 6 different behavior patterns
**Performance Targets:** Comprehensive production-ready metrics

**Ready for Production Testing!** 🚀
