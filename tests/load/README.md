# CONTINUUM Load Testing Suite

Comprehensive load testing framework for CONTINUUM using [Locust](https://locust.io).

## Overview

This suite tests CONTINUUM's performance under realistic production loads, identifying bottlenecks and validating scalability targets before launch.

### Performance Targets

| Category | Target | P95 Latency | P99 Latency | Error Rate |
|----------|--------|-------------|-------------|------------|
| **Memory Operations** | 1,000 creates/min<br>10,000 reads/min<br>500 updates/min | <100ms | <500ms | <1% |
| **Search** | 1,000 semantic/min<br>2,000 fulltext/min | <200ms | <1000ms | <1% |
| **Federation** | 100 syncs/sec<br>10 concurrent peers | <500ms | <2000ms | <5% |
| **Full API** | 50,000 requests/min<br>1,000 concurrent users | <200ms | <500ms | <1% |

## Quick Start

### Prerequisites

```bash
# Install Locust
pip install locust

# Verify installation
locust --version
```

### Run Tests

```bash
# Quick smoke test (2 minutes, 50 users)
./run_load_tests.sh --scenario quick

# Full API test (10 minutes, 1000 users)
./run_load_tests.sh --scenario api --users 1000 --time 10m

# Interactive web UI
./run_load_tests.sh --web
# Then open http://localhost:8089
```

## Test Scenarios

### 1. Memory Operations (`--scenario memory`)

Tests CRUD operations on the memory system.

**Operations:**
- **CREATE** (20%): `/learn` endpoint - save new memories
- **READ** (60%): `/recall` endpoint - retrieve context
- **UPDATE** (15%): `/learn` endpoint - modify existing concepts
- **DELETE** (5%): Entity management

**Targets:**
- 1,000 creates/minute
- 10,000 reads/minute
- 500 updates/minute
- 100 deletes/minute

**Run:**
```bash
./run_load_tests.sh --scenario memory --users 500 --time 10m
```

### 2. Search Operations (`--scenario search`)

Tests search and retrieval under load.

**Operations:**
- **Semantic search** (50%): Context-aware search via `/recall`
- **Complex queries** (30%): Multi-concept searches
- **Entity search** (15%): Filtered entity retrieval
- **Pagination** (5%): Large result set handling

**Targets:**
- 1,000 semantic searches/minute
- 500 graph traversals/minute
- 2,000 full-text searches/minute

**Run:**
```bash
./run_load_tests.sh --scenario search --users 300 --time 5m
```

### 3. Federation (`--scenario federation`)

Tests peer-to-peer synchronization and distributed operations.

**Operations:**
- **Memory contribution** (40%): Share memories with federation
- **Sync requests** (30%): Request updates from peers
- **Peer discovery** (20%): Find and connect to peers
- **Conflict resolution** (10%): Handle competing updates

**Targets:**
- 100 syncs/second
- 10 concurrent peer connections
- Graceful conflict handling

**Run:**
```bash
./run_load_tests.sh --scenario federation --users 200 --time 5m
```

### 4. Full API (`--scenario api`)

Realistic mixed workload simulating production usage.

**Workload Distribution:**
- **Read operations** (60%): Recall, stats, entity browsing
- **Write operations** (30%): Learning, turn processing
- **Search operations** (10%): Semantic and complex searches

**User Types:**
- **Heavy readers** (33%): 80% read, 20% write
- **Balanced users** (33%): 60% read, 40% write
- **Content creators** (33%): 40% read, 60% write

**Targets:**
- 1,000 concurrent users
- 50,000 requests/minute
- P95 <200ms, P99 <500ms

**Run:**
```bash
./run_load_tests.sh --scenario api --users 1000 --time 10m
```

## Advanced Usage

### Custom Load Patterns

#### Step Load (Find Breaking Point)

Gradually increases load to identify system limits.

```bash
# Uncomment StepLoadShape in locustfile.py
locust -f locustfile.py --host http://localhost:8000 --headless
```

**Pattern:**
- Step 1 (0-60s): 100 users
- Step 2 (60-120s): 200 users
- Step 3 (120-180s): 300 users
- ... continues until failure or 10 minutes

#### Spike Load (Test Resilience)

Tests system recovery from sudden traffic spikes.

```bash
# Uncomment SpikeLoadShape in locustfile.py
locust -f locustfile.py --host http://localhost:8000 --headless
```

**Pattern:**
- Warm up: 100 users (0-60s)
- Spike 1: 1,000 users (60-120s)
- Cool down: 200 users (120-180s)
- Spike 2: 1,500 users (180-240s)
- Final cool down: 100 users (240-300s)

### Web UI Mode

Interactive testing with real-time charts.

```bash
./run_load_tests.sh --web
```

1. Open http://localhost:8089
2. Set number of users and spawn rate
3. Click "Start swarming"
4. Monitor real-time statistics and charts
5. Download reports when complete

### Tag-Based Testing

Run specific test groups using tags.

```bash
# Memory CRUD only
locust -f locustfile.py --tags crud --users 100

# All read operations
locust -f locustfile.py --tags read --users 500

# Federation sync only
locust -f locustfile.py --tags sync --users 200
```

**Available Tags:**
- `memory` - Memory operations
- `crud` - Create/Read/Update/Delete
- `search` - Search operations
- `read` - Read-only operations
- `federation` - Federation operations
- `sync` - Synchronization operations
- `api` - Full API tests
- `realistic` - Realistic usage patterns
- `burst` - Burst traffic patterns

## Metrics and Analysis

### Collected Metrics

**Standard Metrics:**
- **Response time**: Min, median, average, max, P95, P99
- **Throughput**: Requests/second, requests/minute
- **Error rate**: Percentage of failed requests
- **Concurrent users**: Active users over time

**Custom Metrics:**
- **Concepts extracted**: Average per request
- **Concepts found**: Average per search
- **Query times**: Distribution and percentiles
- **Sync operations**: Total federation syncs
- **Conflicts detected**: Number of resolution events

### Result Files

Each test run generates:

```
results/
├── load_test_20251206_120000.html      # Interactive HTML report
├── load_test_20251206_120000_stats.csv # Request statistics
├── load_test_20251206_120000_exceptions.csv # Error details
├── load_test_20251206_120000_stats_history.csv # Time series data
└── load_test_20251206_120000.log       # Full test log
```

### Analyzing Results

#### View HTML Report
```bash
# Opens in default browser
open results/load_test_*.html
```

#### Analyze CSV Data
```bash
# View statistics
column -t -s, results/load_test_*_stats.csv | less -S

# Extract P95 times
awk -F',' 'NR>1 {print $1, $9}' results/load_test_*_stats.csv
```

#### Check for Errors
```bash
# View exception log
cat results/load_test_*_exceptions.csv

# Count error types
awk -F',' 'NR>1 {print $2}' results/load_test_*_exceptions.csv | sort | uniq -c
```

## Configuration

### Edit Test Parameters

Edit `config.py` to customize:

```python
@dataclass
class LoadTestConfig:
    # API Configuration
    api_base_url: str = "http://localhost:8000"
    api_key: str = "cm_test_key_for_load_testing"

    # Test Duration
    duration_seconds: int = 300

    # User Simulation
    users_min: int = 10
    users_max: int = 1000
    spawn_rate: int = 10

    # Performance Targets
    targets: Dict[str, Dict[str, Any]] = ...
```

### Test Data

Sample messages and queries are defined in `config.py`:

```python
SAMPLE_MESSAGES = [
    "What is quantum computing?",
    "Explain machine learning algorithms",
    # ... add more
]

SAMPLE_RESPONSES = [
    "Quantum computing uses quantum bits...",
    # ... add more
]
```

## Best Practices

### Before Running Tests

1. **Start the API server**
   ```bash
   continuum serve --host 0.0.0.0 --port 8000
   ```

2. **Create test API key**
   ```bash
   curl -X POST http://localhost:8000/keys \
     -H "Content-Type: application/json" \
     -d '{"tenant_id": "load_test_tenant", "name": "Load Test Key"}'
   ```

3. **Warm up the system**
   ```bash
   ./run_load_tests.sh --scenario quick
   ```

4. **Monitor system resources**
   ```bash
   # In separate terminal
   htop
   # or
   docker stats  # if running in container
   ```

### During Tests

1. **Monitor API logs**
   ```bash
   tail -f /path/to/continuum.log
   ```

2. **Watch database performance**
   ```bash
   # For SQLite
   watch -n 1 'ls -lh /path/to/continuum.db'

   # For PostgreSQL
   watch -n 1 'psql -c "SELECT * FROM pg_stat_activity;"'
   ```

3. **Check system resources**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network bandwidth

### After Tests

1. **Analyze results** (see Metrics and Analysis)
2. **Identify bottlenecks**
   - Slowest endpoints
   - High error rates
   - Resource constraints
3. **Optimize and retest**
4. **Document findings**

## Troubleshooting

### Tests Fail Immediately

**Problem:** API not running or unreachable

**Solution:**
```bash
# Check API health
curl http://localhost:8000/health

# Start API if needed
continuum serve
```

### High Error Rates

**Problem:** API overloaded or misconfigured

**Solutions:**
- Reduce user count: `--users 50`
- Increase spawn rate delay: `--spawn-rate 5`
- Check API logs for errors
- Verify database connections
- Check resource limits (ulimit, max connections)

### Slow Response Times

**Problem:** Performance bottleneck

**Investigation:**
1. Check which endpoints are slow (HTML report)
2. Enable database query logging
3. Profile the API server
4. Check for missing indexes
5. Monitor resource usage

### Connection Errors

**Problem:** Too many connections

**Solutions:**
```bash
# Increase system limits
ulimit -n 10000

# For PostgreSQL, increase max_connections
# In postgresql.conf:
# max_connections = 200
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install locust
          pip install -r requirements.txt
      - name: Start API
        run: |
          continuum serve &
          sleep 5
      - name: Run load tests
        run: |
          cd tests/load
          ./run_load_tests.sh --scenario quick
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: tests/load/results/
```

## Performance Tuning Tips

### API Server

1. **Enable caching**
   ```python
   # In config
   CACHE_ENABLED = True
   CACHE_TTL = 300  # 5 minutes
   ```

2. **Use connection pooling**
   ```python
   # For PostgreSQL
   pool_size = 20
   max_overflow = 10
   ```

3. **Optimize database queries**
   - Add indexes on frequently queried fields
   - Use EXPLAIN ANALYZE to find slow queries
   - Enable query result caching

4. **Scale horizontally**
   - Run multiple API instances
   - Use load balancer (nginx, HAProxy)
   - Distribute database reads (replicas)

### Database

1. **SQLite optimizations**
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   PRAGMA cache_size = 10000;
   ```

2. **PostgreSQL optimizations**
   ```sql
   -- Increase shared buffers
   shared_buffers = 256MB

   -- Tune work memory
   work_mem = 16MB

   -- Enable parallel queries
   max_parallel_workers_per_gather = 4
   ```

3. **Indexes**
   ```sql
   CREATE INDEX idx_entities_tenant ON entities(tenant_id);
   CREATE INDEX idx_messages_timestamp ON messages(created_at);
   CREATE INDEX idx_concepts_name ON concepts(name);
   ```

### System

1. **Increase file descriptors**
   ```bash
   ulimit -n 65535
   ```

2. **Tune TCP settings**
   ```bash
   # /etc/sysctl.conf
   net.core.somaxconn = 1024
   net.ipv4.tcp_max_syn_backlog = 2048
   ```

3. **Use production ASGI server**
   ```bash
   # Use uvicorn with workers
   uvicorn continuum.api.server:app --workers 4 --host 0.0.0.0
   ```

## Contributing

To add new test scenarios:

1. Create new file in `scenarios/`
2. Define TaskSet and User classes
3. Import in `locustfile.py`
4. Add to documentation

Example:
```python
# scenarios/my_test.py
from locust import TaskSet, task, between
from locust.contrib.fasthttp import FastHttpUser

class MyTasks(TaskSet):
    @task
    def my_test(self):
        # Your test logic
        pass

class MyUser(FastHttpUser):
    tasks = [MyTasks]
    wait_time = between(1, 3)
    tags = {"my_scenario"}
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [CONTINUUM API Documentation](../../docs/API.md)
- [Performance Tuning Guide](../../docs/PERFORMANCE.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/continuum/continuum/issues
- Documentation: https://continuum.dev/docs
- Community: https://discord.gg/continuum
