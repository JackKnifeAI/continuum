# CONTINUUM Load Testing Suite - Index

Complete index of all load testing files and documentation.

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[QUICK_START.md](QUICK_START.md)** | Fast setup and common commands | Everyone |
| **[README.md](README.md)** | Comprehensive documentation | Detailed reference |
| **[TEST_SCENARIOS_SUMMARY.md](TEST_SCENARIOS_SUMMARY.md)** | Test scenarios and expected results | Test planning |
| **[Makefile](Makefile)** | Quick command shortcuts | Developers |

## File Structure

```
tests/load/
│
├── Documentation
│   ├── README.md                    # Comprehensive guide (180+ lines)
│   ├── QUICK_START.md              # Quick reference (70+ lines)
│   ├── TEST_SCENARIOS_SUMMARY.md   # Detailed scenarios (600+ lines)
│   └── INDEX.md                    # This file
│
├── Configuration
│   ├── config.py                   # Test parameters and targets (150+ lines)
│   ├── requirements.txt            # Python dependencies
│   └── .gitignore                  # Git ignore rules
│
├── Test Scenarios
│   ├── locustfile.py              # Main orchestration (380+ lines)
│   └── scenarios/
│       ├── __init__.py            # Package initialization
│       ├── memory_operations.py   # Memory CRUD tests (165+ lines)
│       ├── search.py              # Search tests (145+ lines)
│       ├── federation.py          # Federation tests (165+ lines)
│       └── api.py                 # Full API tests (285+ lines)
│
├── Execution & Analysis
│   ├── run_load_tests.sh          # Test runner script (270+ lines)
│   ├── analyze_results.py         # Results analyzer (380+ lines)
│   └── Makefile                   # Convenience commands (90+ lines)
│
└── Results
    └── results/                   # Test output directory
        └── .gitkeep               # Keep directory in git
```

**Total:** 15 files, ~2,800 lines of code

## Core Components

### 1. Configuration (`config.py`)

Centralizes all test parameters:
- API endpoint URLs
- Performance targets
- Test data (sample messages, queries)
- Workload distribution settings

**Key Classes:**
- `LoadTestConfig` - Main configuration dataclass
- Helper functions: `get_test_message()`, `get_test_response()`, `get_test_query()`

### 2. Main Orchestrator (`locustfile.py`)

Coordinates all test scenarios:
- Imports all user types
- Configures logging and metrics
- Defines event listeners for custom metrics
- Implements load shapes (step, spike)
- Generates comprehensive test reports

**Key Features:**
- Tag-based scenario selection
- Real-time metrics collection
- Custom performance analysis
- Target validation

### 3. Test Scenarios

#### memory_operations.py
- **Lines:** 165+
- **User Class:** `MemoryOperationsUser`
- **Tasks:** 7 (recall, learn, update, stats, entities, turn)
- **Distribution:** 60% read, 35% write, 5% mixed
- **Target:** 1,000 creates/min, 10,000 reads/min

#### search.py
- **Lines:** 145+
- **User Class:** `SearchUser`
- **Tasks:** 5 (semantic, complex, entity, pagination, targeted)
- **Distribution:** 50% semantic, 30% complex, 20% other
- **Target:** 1,000 semantic/min, 2,000 fulltext/min

#### federation.py
- **Lines:** 165+
- **User Class:** `FederationUser`
- **Tasks:** 5 (contribute, request, discover, conflict, heartbeat)
- **Distribution:** 40% contribute, 30% request, 30% other
- **Target:** 100 syncs/sec, 10 concurrent peers

#### api.py
- **Lines:** 285+
- **User Classes:** `RealisticAPIUser`, `BurstTrafficUser`, `SlowUser`
- **Tasks:** 10+ (mixed read/write/search operations)
- **Distribution:** 60% read, 30% write, 10% search
- **Target:** 50,000 requests/min, 1,000 concurrent users

### 4. Execution Tools

#### run_load_tests.sh
Bash script for easy test execution:
- Dependency checking
- API health verification
- Multiple scenario support
- Result file management
- Colored output

**Usage Examples:**
```bash
./run_load_tests.sh --scenario quick
./run_load_tests.sh --scenario api --users 1000 --time 10m
./run_load_tests.sh --web
```

#### Makefile
Convenience shortcuts:
- `make quick` - Quick smoke test
- `make memory` - Memory operations test
- `make search` - Search test
- `make api` - Full API test
- `make analyze` - Analyze latest results
- `make all` - Run all scenarios

### 5. Analysis Tools

#### analyze_results.py
Python script for CSV analysis:
- Overall statistics summary
- Per-endpoint breakdown
- Top endpoints analysis
- Performance vs. targets
- Optimization recommendations

**Output Sections:**
1. Overall Summary
2. Endpoint Breakdown
3. Top Endpoints (most requested, slowest, errors)
4. Performance Analysis
5. Recommendations

## Performance Targets Summary

| Scenario | Throughput | P95 Latency | P99 Latency | Error Rate |
|----------|------------|-------------|-------------|------------|
| **Memory** | 1,000 creates/min<br>10,000 reads/min | <100ms | <500ms | <1% |
| **Search** | 1,000 semantic/min<br>2,000 fulltext/min | <200ms | <1000ms | <1% |
| **Federation** | 100 syncs/sec | <500ms | <2000ms | <5% |
| **Full API** | 50,000 req/min<br>1,000 concurrent users | <200ms | <500ms | <1% |

## Usage Workflows

### Quick Validation
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start API
continuum serve

# 3. Run quick test
./run_load_tests.sh --scenario quick

# 4. Check results
open results/*.html
```

### Pre-Release Testing
```bash
# Run all scenarios
make validate

# Or manually:
make quick      # Smoke test
make memory     # Memory operations
make search     # Search operations
make federation # Federation
make api        # Full API

# Analyze results
make analyze
```

### Interactive Testing
```bash
# Launch web UI
make web
# or
./run_load_tests.sh --web

# Open http://localhost:8089
# Configure users and spawn rate
# Start test
# Monitor real-time charts
```

### Custom Testing
```bash
# Custom parameters
make custom SCENARIO=memory USERS=750 TIME=8m

# Or directly
./run_load_tests.sh --scenario search --users 500 --time 15m

# Specific tags
locust -f locustfile.py --tags search,read --users 200
```

### CI/CD Integration
```bash
# GitHub Actions example in README.md
# Jenkins pipeline support
# GitLab CI configuration available
```

## Result Files

Each test generates:

```
results/load_test_TIMESTAMP.*
├── .html                 # Interactive HTML report
├── _stats.csv           # Endpoint statistics
├── _exceptions.csv      # Error details
├── _stats_history.csv   # Time series data
└── .log                 # Full test log
```

**Analysis:**
```bash
# View HTML report
open results/*.html

# Analyze CSV
./analyze_results.py results/*_stats.csv

# Quick stats
column -t -s, results/*_stats.csv | less
```

## Common Commands Reference

### Installation
```bash
pip install -r requirements.txt
locust --version
```

### Execution
```bash
# Quick tests
make quick                          # 2 min, 50 users
./run_load_tests.sh --scenario quick

# Scenario tests
make memory                         # 10 min, 500 users
make search                         # 5 min, 300 users
make federation                     # 5 min, 200 users
make api                           # 10 min, 1000 users

# Custom
./run_load_tests.sh --scenario api --users 2000 --time 20m

# Web UI
make web
./run_load_tests.sh --web
```

### Analysis
```bash
# Latest results
make analyze
make report

# Specific file
./analyze_results.py results/load_test_20251206_120000_stats.csv

# CSV manipulation
awk -F',' 'NR>1 {print $1, $9}' results/*_stats.csv  # P95 times
```

### Maintenance
```bash
# Clean old results
make clean

# Check dependencies
pip list | grep locust

# Validate configuration
python -c "from config import config; print(config.targets)"
```

## Dependencies

### Required
- **locust** (>=2.15.0) - Load testing framework
- **geventhttpclient** (>=2.0.0) - Fast HTTP client
- **Python 3.8+** - Runtime environment

### Optional
- **pandas** (>=2.0.0) - Data analysis
- **matplotlib** (>=3.7.0) - Visualization
- **psutil** (>=5.9.0) - Resource monitoring
- **prometheus-client** (>=0.17.0) - Metrics export

### Installation
```bash
pip install -r requirements.txt
```

## Troubleshooting Guide

### Tests Fail Immediately
**→** Check API is running: `curl http://localhost:8000/health`
**→** Start API: `continuum serve`

### High Error Rates
**→** Reduce load: `--users 50`
**→** Check logs: `tail -f continuum.log`
**→** Verify database connections

### Slow Responses
**→** Add database indexes
**→** Enable caching
**→** Profile slow endpoints
**→** Scale horizontally

### Connection Errors
**→** Increase file descriptors: `ulimit -n 65535`
**→** Increase DB connections
**→** Use connection pooling

## Support Resources

- **Documentation:** [README.md](README.md) - Full guide
- **Quick Start:** [QUICK_START.md](QUICK_START.md) - Fast setup
- **Scenarios:** [TEST_SCENARIOS_SUMMARY.md](TEST_SCENARIOS_SUMMARY.md) - Details
- **Locust Docs:** https://docs.locust.io/
- **CONTINUUM API:** ../../docs/API.md

## Contributing

To add new scenarios:
1. Create file in `scenarios/`
2. Define TaskSet and User classes
3. Import in `locustfile.py`
4. Add tags for filtering
5. Document in README.md
6. Update this index

## Version History

- **v1.0** (2025-12-06)
  - Initial comprehensive load testing suite
  - 4 major scenarios (Memory, Search, Federation, API)
  - 6 user types with realistic patterns
  - Custom load shapes (Step, Spike)
  - Analysis tools and documentation
  - CI/CD integration examples
  - Makefile for convenience
  - ~2,800 lines of code

## Next Steps

1. **Run quick validation:** `make quick`
2. **Review targets:** Check `config.py` matches your needs
3. **Execute full suite:** `make all`
4. **Analyze results:** `make analyze`
5. **Optimize as needed:** See recommendations
6. **Integrate with CI/CD:** See README.md examples
7. **Schedule regular tests:** Nightly or pre-release

---

**Ready for Production Load Testing!** 🚀

For questions or issues, see [README.md](README.md) or open a GitHub issue.
