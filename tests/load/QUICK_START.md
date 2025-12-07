# Load Testing Quick Start

## Installation

```bash
cd tests/load
pip install -r requirements.txt
```

## Common Commands

```bash
# Quick smoke test (2 min, 50 users)
./run_load_tests.sh --scenario quick

# Memory operations (10 min, 500 users)
./run_load_tests.sh --scenario memory --users 500 --time 10m

# Search operations (5 min, 300 users)
./run_load_tests.sh --scenario search --users 300 --time 5m

# Federation (5 min, 200 users)
./run_load_tests.sh --scenario federation --users 200 --time 5m

# Full API test (10 min, 1000 users)
./run_load_tests.sh --scenario api --users 1000 --time 10m

# Interactive web UI
./run_load_tests.sh --web
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| **Throughput** | 50,000 req/min | 40,000 req/min |
| **P95 Latency** | <200ms | <500ms |
| **P99 Latency** | <500ms | <1000ms |
| **Error Rate** | <1% | <5% |
| **Concurrent Users** | 1,000 | 500 |

## Quick Analysis

```bash
# View latest HTML report
open results/$(ls -t results/*.html | head -1)

# Check P95 latency
awk -F',' 'NR>1 {print $1, $9}' results/*_stats.csv | tail -10

# Count errors
wc -l results/*_exceptions.csv

# Success rate
awk -F',' 'NR>1 {total+=$4; fail+=$5} END {print "Success:", (total-fail)/total*100"%"}' results/*_stats.csv
```

## Troubleshooting

**Problem: Tests fail immediately**
```bash
# Check API is running
curl http://localhost:8000/health

# Start API
continuum serve
```

**Problem: High error rates**
```bash
# Reduce load
./run_load_tests.sh --scenario quick --users 25

# Check API logs
tail -f /path/to/continuum.log
```

**Problem: Slow responses**
```bash
# Profile slowest endpoints
awk -F',' 'NR>1 {print $9, $1}' results/*_stats.csv | sort -rn | head -10
```

## Test Scenarios

- `quick` - 2 min smoke test
- `memory` - Memory CRUD operations
- `search` - Search and retrieval
- `federation` - Peer synchronization
- `api` - Full realistic workload
- `all` - Complete test suite

## Results

After each test:
- `*.html` - Interactive report
- `*_stats.csv` - Request statistics
- `*_exceptions.csv` - Error details
- `*.log` - Full test log

## Next Steps

See [README.md](README.md) for comprehensive documentation.
