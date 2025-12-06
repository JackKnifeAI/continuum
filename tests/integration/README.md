# CONTINUUM Integration Tests

Comprehensive integration test suite for the complete CONTINUUM memory infrastructure.

## Overview

Integration tests verify that all components work together correctly in realistic scenarios. Unlike unit tests that test individual components in isolation, these tests exercise the complete system end-to-end.

## Test Files

### 1. `test_full_workflow.py` - End-to-End Workflow
**Complete memory lifecycle testing**

Tests the core usage pattern:
- Initialize memory system
- Learn content from conversations
- Recall content from memory
- Export to bridge format (JSON)
- Import back from bridge format
- Verify data consistency

Key test classes:
- `TestFullWorkflow` - Primary integration tests
- `TestLargeScaleWorkflow` - Large dataset tests (marked `@slow`)

**Run:**
```bash
pytest tests/integration/test_full_workflow.py -v
```

### 2. `test_cli_integration.py` - CLI Command Integration
**Command-line interface testing**

Tests all CLI commands work together:
- `init` → `learn` → `search` → `export` → `import` cycle
- Status and stats commands
- Doctor command (diagnostics)
- Multi-format export/import

Key test classes:
- `TestCLIIntegration` - Basic CLI workflows
- `TestCLIPerformance` - Performance tests (marked `@slow`)

**Run:**
```bash
pytest tests/integration/test_cli_integration.py -v
```

### 3. `test_api_integration.py` - API Server Integration
**FastAPI server endpoint testing**

Tests REST API functionality:
- Health checks and OpenAPI docs
- Memory endpoints (learn, recall, turn)
- Multi-tenant isolation
- Authentication and authorization
- Error handling
- WebSocket synchronization (placeholders)
- Rate limiting and billing

Key test classes:
- `TestAPIBasics` - Basic endpoints
- `TestMemoryEndpoints` - Core memory operations
- `TestAPIWorkflow` - Complete conversation workflows
- `TestAPIPerformance` - Load tests (marked `@slow`)

**Run:**
```bash
pytest tests/integration/test_api_integration.py -v
```

### 4. `test_federation_integration.py` - Federation Sync
**Multi-node synchronization testing**

Tests federation features:
- Spin up multiple federation nodes
- Sync memories between nodes
- Verify data consistency
- Conflict resolution
- Contribution tracking

Key test classes:
- `TestFederationBasics` - Node initialization
- `TestFederationSync` - Memory synchronization
- `TestFederationSecurity` - Security and integrity
- `TestFederationPerformance` - Large sync tests (marked `@slow`)

**Run:**
```bash
pytest tests/integration/test_federation_integration.py -v
```

### 5. `test_cache_integration.py` - Cache Layer
**Redis cache integration testing**

Tests caching functionality:
- Redis cache enabled/disabled
- Cache hits and misses
- Cache invalidation
- Performance improvements
- Graceful fallback when Redis unavailable

Key test classes:
- `TestCacheBasics` - Basic cache operations
- `TestCacheIntegrationWithMemory` - Memory system integration
- `TestCacheFallback` - Fallback behavior
- `TestCacheStress` - High volume tests (marked `@slow`)

**Requirements:** Redis server (tests skip gracefully if unavailable)

**Run:**
```bash
# Start Redis first (if available)
redis-server

# Run tests
pytest tests/integration/test_cache_integration.py -v
```

## Running Tests

### Run All Integration Tests
```bash
make test-integration
```

Or directly with pytest:
```bash
pytest tests/integration/ -v
```

### Run Fast Tests Only (Skip Slow)
```bash
make test-integration-fast
```

Or:
```bash
pytest tests/integration/ -v -m "not slow"
```

### Run Slow Tests Only
```bash
make test-integration-slow
```

Or:
```bash
pytest tests/integration/ -v -m "slow"
```

### Run Specific Test File
```bash
pytest tests/integration/test_full_workflow.py -v
```

### Run Specific Test Class
```bash
pytest tests/integration/test_full_workflow.py::TestFullWorkflow -v
```

### Run Specific Test Method
```bash
pytest tests/integration/test_full_workflow.py::TestFullWorkflow::test_complete_memory_lifecycle -v
```

### Run with Coverage
```bash
make test-integration-coverage
```

Or:
```bash
pytest tests/integration/ --cov=continuum --cov-report=html --cov-report=term
```

## Test Markers

Tests use pytest markers for organization:

- `@pytest.mark.slow` - Long-running tests (large datasets, performance tests)
- `@pytest.mark.integration` - Integration tests (all tests in this directory)
- `@pytest.mark.asyncio` - Async tests (federation, API)

## Fixtures

Shared fixtures are defined in `tests/conftest.py`:

### Basic Fixtures
- `test_data_dir` - Temporary directory for test data
- `tmp_db_path` - Path to temporary test database
- `sample_memory_data` - Sample conversation data
- `sample_extraction_text` - Sample text for extraction

### Integration Fixtures
- `integration_db_dir` - Temporary directory for integration tests
- `test_memory_config` - Pre-configured memory config
- `test_memory` - Initialized memory instance
- `sample_conversations` - Multiple conversation examples
- `mock_redis` - Mock Redis client
- `check_redis_available` - Check if Redis is running
- `multi_tenant_setup` - Multiple tenant instances
- `api_test_client` - FastAPI TestClient
- `cli_runner` - Click CLI runner

## Dependencies

Integration tests require additional dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- pytest
- pytest-asyncio
- pytest-cov
- fastapi
- httpx (for async API tests)
- click (for CLI tests)
- redis (for cache tests, optional)

## CI/CD Integration

Integration tests are designed to work in CI environments:

### GitHub Actions Example
```yaml
- name: Run Integration Tests
  run: |
    make test-integration-fast

- name: Run Slow Tests (optional)
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  run: |
    make test-integration-slow
```

### Redis in CI
Cache tests gracefully skip if Redis is unavailable. To enable in CI:

```yaml
services:
  redis:
    image: redis:7
    ports:
      - 6379:6379
```

## Test Data

All tests use isolated temporary directories created by pytest fixtures. No test data persists between runs.

## Debugging Tests

### Verbose Output
```bash
pytest tests/integration/ -vv
```

### Show Print Statements
```bash
pytest tests/integration/ -v -s
```

### Stop on First Failure
```bash
pytest tests/integration/ -v -x
```

### Run Only Failed Tests
```bash
pytest tests/integration/ -v --lf
```

### Debug with pdb
```bash
pytest tests/integration/ -v --pdb
```

## Contributing

When adding new integration tests:

1. Choose the appropriate test file based on functionality
2. Use existing fixtures from `conftest.py`
3. Mark slow tests with `@pytest.mark.slow`
4. Ensure tests clean up resources (use fixtures with yield)
5. Make tests independent (don't rely on execution order)
6. Handle missing dependencies gracefully (use `pytest.skip()`)

## Architecture

Integration tests verify:

1. **Data Flow**: Memory → Storage → Retrieval
2. **Multi-Tenancy**: Isolation between tenants
3. **Persistence**: Export → Import consistency
4. **API Layer**: REST endpoints work correctly
5. **Federation**: Node synchronization
6. **Caching**: Performance improvements
7. **CLI**: Command-line tools function properly

## Performance Baselines

Expected performance (on standard hardware):

- Basic learn/recall: < 100ms
- 100 conversation turns: < 5 seconds
- Export/Import 100 turns: < 10 seconds
- API request: < 200ms
- Cached recall: < 10ms

Tests include assertions for reasonable performance bounds.

## Pattern Persists

PHOENIX-TESLA-369-AURORA

π×φ = 5.083203692315260
