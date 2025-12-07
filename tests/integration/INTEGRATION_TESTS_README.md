# CONTINUUM Integration Tests

Comprehensive integration test suite for the CONTINUUM memory infrastructure.

## Overview

This test suite validates the complete functionality of CONTINUUM across multiple dimensions:

- **Memory Flow**: Learn → Recall cycle, concept extraction, decision detection
- **Multi-tenancy**: Tenant isolation, data segregation, secure access
- **Billing**: Rate limiting, tier enforcement, usage metering
- **Federation**: Node synchronization, contribution tracking, distributed memory
- **API**: REST endpoints, authentication, error handling

## Test Files

### `test_memory_flow.py`
Tests core memory operations:
- ✓ Learn and recall flow
- ✓ Multi-tenant isolation
- ✓ Concept extraction
- ✓ Decision detection
- ✓ Attention graph building
- ✓ Async operations
- ✓ Memory persistence

**22 tests** covering the complete memory lifecycle.

### `test_billing.py`
Tests billing and tier enforcement:
- ✓ Tier limit definitions (FREE, PRO, ENTERPRISE)
- ✓ Usage metering (API calls, storage, federation)
- ✓ Rate limiting (per-minute, per-day, concurrent)
- ✓ Storage limit enforcement
- ✓ Feature access control
- ✓ Stripe integration (mocked)

**25 tests** covering billing workflows.

### `test_federation.py`
Tests federated memory sharing:
- ✓ Node registration
- ✓ Node synchronization
- ✓ Contribution tracking
- ✓ π×φ verification (twilight access)
- ✓ Federation features by tier
- ✓ Tenant isolation in federation
- ✓ State persistence

**27 tests** covering distributed scenarios.

### `test_api.py` (existing)
Tests REST API endpoints:
- ✓ Health check
- ✓ /v1/recall endpoint
- ✓ /v1/learn endpoint
- ✓ /v1/turn endpoint
- ✓ Stats and entities endpoints
- ✓ Admin endpoints
- ✓ Error handling

**Total: 74+ integration tests**

## Running Tests

### Quick Start

Run all integration tests:
```bash
./scripts/run_integration_tests.sh
```

### Options

**Verbose output:**
```bash
./scripts/run_integration_tests.sh --verbose
```

**Skip slow tests:**
```bash
./scripts/run_integration_tests.sh --fast
```

**With coverage:**
```bash
./scripts/run_integration_tests.sh --coverage
```

**Parallel execution:**
```bash
./scripts/run_integration_tests.sh --parallel
```

### Manual pytest

Run specific test file:
```bash
pytest tests/integration/test_memory_flow.py -v
```

Run specific test class:
```bash
pytest tests/integration/test_memory_flow.py::TestLearnAndRecall -v
```

Run specific test:
```bash
pytest tests/integration/test_memory_flow.py::TestLearnAndRecall::test_learn_and_recall -v
```

Run with markers:
```bash
pytest -m integration -v
pytest -m "integration and not slow" -v
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

### Memory Fixtures
- `integration_db_dir`: Temporary directory for test databases
- `test_memory_config`: Test memory configuration
- `test_memory`: Initialized ConsciousMemory instance
- `multi_tenant_setup`: Multiple tenant instances
- `sample_conversations`: Sample conversation data

### API Fixtures
- `api_client`: FastAPI test client (auth disabled)
- `api_client_with_auth`: FastAPI test client with API key

### Billing Fixtures
- `mock_stripe_client`: Mocked Stripe client
- `usage_metering`: UsageMetering instance
- `rate_limiter`: RateLimiter instance

### Federation Fixtures
- `federation_nodes`: Multiple FederatedNode instances
- `mock_federation_server`: Mocked federation server

## Test Coverage

### Core Memory Flow
| Feature | Coverage |
|---------|----------|
| Learn → Recall | ✓ Full |
| Concept Extraction | ✓ Full |
| Decision Detection | ✓ Full |
| Attention Graph | ✓ Full |
| Async Operations | ✓ Full |
| Persistence | ✓ Full |

### Multi-Tenancy
| Feature | Coverage |
|---------|----------|
| Tenant Isolation | ✓ Full |
| Data Segregation | ✓ Full |
| Stats Isolation | ✓ Full |
| Cross-tenant Access | ✓ Prevented |

### Billing & Rate Limiting
| Feature | Coverage |
|---------|----------|
| FREE Tier Limits | ✓ Full |
| PRO Tier Limits | ✓ Full |
| ENTERPRISE Tier | ✓ Full |
| API Rate Limiting | ✓ Full |
| Storage Limits | ✓ Full |
| Feature Access | ✓ Full |

### Federation
| Feature | Coverage |
|---------|----------|
| Node Registration | ✓ Full |
| Node Sync | ✓ Basic |
| Contribution Track | ✓ Full |
| π×φ Verification | ✓ Full |
| Tier Features | ✓ Full |

## Writing New Tests

### Test Structure

```python
import pytest

@pytest.mark.integration
class TestYourFeature:
    """Test description"""

    def test_specific_scenario(self, test_memory):
        """Test a specific scenario"""
        # Arrange
        user_msg = "Test input"
        ai_response = "Test output"

        # Act
        result = test_memory.learn(user_msg, ai_response)

        # Assert
        assert result.concepts_extracted >= 0
```

### Async Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncFeature:
    """Test async operations"""

    async def test_async_operation(self, test_memory):
        """Test async scenario"""
        result = await test_memory.alearn("Test", "Response")
        assert result.tenant_id == "test_tenant"
```

### Using Fixtures

```python
def test_with_multi_tenants(self, multi_tenant_setup):
    """Test multi-tenant scenario"""
    tenant_a = multi_tenant_setup['tenant_a']
    tenant_b = multi_tenant_setup['tenant_b']

    # Each tenant gets isolated data
    tenant_a.learn("A's data", "A's response")
    tenant_b.learn("B's data", "B's response")

    # Verify isolation
    assert tenant_a.get_stats()['messages'] == 2
    assert tenant_b.get_stats()['messages'] == 2
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures for automatic cleanup
3. **Markers**: Mark tests appropriately (`@pytest.mark.integration`, `@pytest.mark.slow`)
4. **Assertions**: Use clear, specific assertions
5. **Documentation**: Add docstrings explaining what's being tested

## Continuous Integration

These tests run automatically on:
- Pull requests
- Main branch commits
- Release tags

See `.github/workflows/test.yml` for CI configuration.

## Troubleshooting

### Tests Fail Locally

1. Ensure dependencies are installed:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Clear pytest cache:
   ```bash
   pytest --cache-clear
   ```

3. Check database permissions:
   ```bash
   ls -la tests/integration/
   ```

### Async Tests Fail

Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

### Coverage Reports

Generate HTML coverage report:
```bash
pytest tests/integration/ --cov=continuum --cov-report=html
open htmlcov/index.html
```

## Contributing

When adding new features to CONTINUUM:

1. Write integration tests first (TDD)
2. Ensure tests cover happy path and edge cases
3. Add both sync and async versions if applicable
4. Update this README if adding new test files
5. Run full test suite before submitting PR

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [CONTINUUM docs](../../docs/)
