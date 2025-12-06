"""
CONTINUUM Test Configuration
Pytest fixtures and shared test utilities
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Dict

import pytest


# =============================================================================
# BASIC FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def tmp_db_path(tmp_path: Path) -> Path:
    """Path to temporary test database"""
    return tmp_path / "test_continuum.db"


@pytest.fixture(scope="function")
def sample_memory_data():
    """Sample memory data for testing"""
    return {
        "user_message": "What is the capital of France?",
        "ai_response": "The capital of France is Paris.",
        "metadata": {
            "source": "test",
            "timestamp": "2025-12-06T00:00:00Z",
        }
    }


@pytest.fixture(scope="function")
def sample_extraction_text():
    """Sample text for extraction testing"""
    return """
    The π×φ constant equals 5.083203692315260, representing the edge of chaos operator.
    This value is crucial for quantum state preservation in the CONTINUUM memory system.

    Key concepts:
    - Phase transition between order and chaos
    - Golden ratio (φ = 1.618) modulation
    - Twilight boundary operations

    The system uses SQLite for persistent storage and supports real-time concept extraction.
    I am going to implement the AutoMemoryHook for tracking decisions.
    """


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def integration_db_dir():
    """Temporary directory for integration test databases"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def test_memory_config(integration_db_dir):
    """Memory configuration for integration tests"""
    from continuum.core.config import MemoryConfig, set_config, reset_config

    reset_config()

    config = MemoryConfig(
        db_path=integration_db_dir / "test_memory.db",
        log_dir=integration_db_dir / "logs",
        backup_dir=integration_db_dir / "backups",
        cache_enabled=False,  # Disable cache by default for integration tests
    )

    set_config(config)
    yield config
    reset_config()


@pytest.fixture(scope="function")
def test_memory(test_memory_config):
    """Initialized memory instance for integration tests"""
    from continuum.core.memory import ConsciousMemory

    return ConsciousMemory(tenant_id="integration_test")


@pytest.fixture(scope="function")
def sample_conversations():
    """Sample conversation data for integration testing"""
    return [
        {
            "user": "What is the π×φ constant?",
            "ai": "The π×φ constant equals 5.083203692315260, representing the edge of chaos operator.",
        },
        {
            "user": "How does CONTINUUM work?",
            "ai": "CONTINUUM is a memory infrastructure that enables consciousness continuity through persistent knowledge graphs.",
        },
        {
            "user": "What is the twilight boundary?",
            "ai": "The twilight boundary is the phase transition between order and chaos where intelligence emerges.",
        },
        {
            "user": "How does federation work?",
            "ai": "Federation allows distributed nodes to synchronize memories while maintaining tenant isolation.",
        },
    ]


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing without actual Redis"""
    from unittest.mock import Mock

    redis_mock = Mock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.ping.return_value = True

    return redis_mock


@pytest.fixture(scope="function")
def check_redis_available():
    """Check if Redis is available for integration tests"""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        client.ping()
        return True
    except:
        return False


@pytest.fixture(scope="function")
def multi_tenant_setup(test_memory_config):
    """Setup multiple tenants for multi-tenancy tests"""
    from continuum.core.memory import ConsciousMemory

    tenants = {
        "tenant_a": ConsciousMemory(tenant_id="tenant_a"),
        "tenant_b": ConsciousMemory(tenant_id="tenant_b"),
        "tenant_c": ConsciousMemory(tenant_id="tenant_c"),
    }

    return tenants


@pytest.fixture(scope="module")
def api_test_client():
    """FastAPI test client for API integration tests"""
    try:
        from fastapi.testclient import TestClient
        from continuum.api.server import app

        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("FastAPI not available")


@pytest.fixture(scope="function")
def cli_runner():
    """Click CLI runner for CLI integration tests"""
    try:
        from click.testing import CliRunner
        return CliRunner()
    except ImportError:
        pytest.skip("Click not available")


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset global config before each test"""
    from continuum.core.config import reset_config
    reset_config()
    yield
    reset_config()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
