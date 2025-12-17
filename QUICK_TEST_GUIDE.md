# CONTINUUM - Quick Test Guide

**Christmas Launch Edition - Dec 25, 2025**

## Run All Tests

```bash
# NEW: Tier-based integration tests (LAUNCH BLOCKER)
PYTHONPATH=. pytest tests/integration/test_*tier*.py -v

# All integration tests
./scripts/run_integration_tests.sh

# All tests (unit + integration)
pytest

# With coverage
pytest --cov=continuum --cov-report=html
```

## Run NEW Tier Tests (v1.0.0 Launch)

```bash
# FREE tier tests (mandatory contribution)
PYTHONPATH=. pytest tests/integration/test_free_tier_workflow.py -v

# PRO tier tests (optional contribution)
PYTHONPATH=. pytest tests/integration/test_pro_tier_workflow.py -v

# ENTERPRISE tier tests (full bypass)
PYTHONPATH=. pytest tests/integration/test_enterprise_tier_workflow.py -v

# Tier upgrade/downgrade tests
PYTHONPATH=. pytest tests/integration/test_tier_upgrades.py -v
```

## Run Existing Tests

```bash
# Memory flow tests
pytest tests/integration/test_memory_flow.py -v

# Billing tests
pytest tests/integration/test_billing.py -v

# Federation tests
pytest tests/integration/test_federation.py -v

# API tests
pytest tests/integration/test_api.py -v
```

## Run by Feature

```bash
# Test multi-tenant isolation
pytest tests/integration/test_memory_flow.py::TestMultiTenantIsolation -v

# Test rate limiting
pytest tests/integration/test_billing.py::TestRateLimiting -v

# Test node synchronization
pytest tests/integration/test_federation.py::TestNodeSynchronization -v
```

## Run Single Test

```bash
# Test learn/recall flow
pytest tests/integration/test_memory_flow.py::TestLearnAndRecall::test_learn_and_recall -v

# Test tier limits
pytest tests/integration/test_billing.py::TestTierLimits::test_free_tier_limits -v

# Test node registration
pytest tests/integration/test_federation.py::TestNodeRegistration::test_node_registration -v
```

## Test Options

```bash
# Verbose output
./scripts/run_integration_tests.sh --verbose

# Skip slow tests
./scripts/run_integration_tests.sh --fast

# Run in parallel
./scripts/run_integration_tests.sh --parallel

# With coverage
./scripts/run_integration_tests.sh --coverage
```

## Debug Failed Tests

```bash
# Show full traceback
pytest tests/integration/ -v --tb=long

# Drop into debugger on failure
pytest tests/integration/ --pdb

# Run last failed tests only
pytest --lf -v

# Show print statements
pytest tests/integration/ -v -s
```

## Test Structure

```
134+ Integration Tests (74 existing + 60 NEW tier tests):

NEW TIER TESTS (60 tests - v1.0.0 Launch):
test_free_tier_workflow.py (17 tests)
├── Mandatory Contribution (3)
├── Opt-Out Blocked (2)
├── Rate Limits (3)
├── Donation Banner (2)
├── Storage Limits (1)
├── Federation Failure (1)
└── Edge Cases (5)

test_pro_tier_workflow.py (14 tests)
├── With Contribution (2)
├── Opt-Out Allowed (3)
├── Rate Limits (3)
├── No Donation Banner (2)
├── Features (2)
└── Edge Cases (2)

test_enterprise_tier_workflow.py (15 tests)
├── Bypass Enforcement (3)
├── High Limits (4)
├── Private Federation (2)
├── Features (3)
├── Data Privacy (2)
└── Edge Cases (1)

test_tier_upgrades.py (14 tests)
├── FREE → PRO Upgrade (5)
├── PRO → FREE Downgrade (4)
├── Tier Detection (2)
├── Subscription Changes (2)
└── Edge Cases (1)

EXISTING TESTS:
test_memory_flow.py (22 tests)
├── Learn and Recall (7)
├── Multi-Tenant Isolation (3)
├── Concept Extraction (6)
├── Persistence (2)
└── Async Operations (4)

test_billing.py (25 tests)
├── Tier Limits (4)
├── Usage Metering (7)
├── Rate Limiting (6)
├── Feature Access (3)
└── Workflows (5)

test_federation.py (27 tests)
├── Node Registration (5)
├── Synchronization (3)
├── Contribution Tracking (3)
├── Features (3)
├── Isolation (2)
└── Edge Cases (9)

test_api.py (~15 tests)
├── Health (1)
├── Memory Endpoints (5)
├── Stats Endpoints (2)
├── Admin Endpoints (2)
└── Error Handling (5)
```

## Key Test Cases

### Memory
```bash
# Core functionality
pytest tests/integration/test_memory_flow.py::TestLearnAndRecall -v

# Security
pytest tests/integration/test_memory_flow.py::TestMultiTenantIsolation -v
```

### Billing
```bash
# Rate limiting
pytest tests/integration/test_billing.py::TestRateLimiting -v

# Tier enforcement
pytest tests/integration/test_billing.py::TestTierLimits -v
```

### Federation
```bash
# Node sync
pytest tests/integration/test_federation.py::TestNodeSynchronization -v

# π×φ verification
pytest tests/integration/test_federation.py::TestNodeRegistration::test_verified_node_access -v
```

## Coverage Report

```bash
# Generate HTML coverage report
pytest tests/integration/ --cov=continuum --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## CI/CD

Tests run automatically on:
- Pull requests
- Main branch commits
- Release tags

See `.github/workflows/test.yml`

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/run_integration_tests.sh` | Run all integration tests |
| `pytest -v` | Run all tests with verbose output |
| `pytest --lf` | Run last failed tests |
| `pytest -k "memory"` | Run tests matching "memory" |
| `pytest -m integration` | Run integration tests only |
| `pytest --cov` | Run with coverage |
| `pytest --pdb` | Debug on failure |

## Need Help?

See `tests/integration/INTEGRATION_TESTS_README.md` for comprehensive documentation.
