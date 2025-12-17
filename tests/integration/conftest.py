"""
CONTINUUM Integration Test Configuration
Pytest fixtures for integration tests
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Dict
from unittest.mock import Mock, patch

import pytest


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
        tenant_id="test_tenant",
    )

    set_config(config)
    yield config
    reset_config()


@pytest.fixture(scope="function")
def test_memory(test_memory_config):
    """Initialized memory instance for integration tests"""
    from continuum.core.memory import ConsciousMemory

    return ConsciousMemory(tenant_id="test_tenant")


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


# =============================================================================
# API TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def api_client(api_client_with_auth):
    """
    FastAPI test client with automatic authentication.

    This wraps api_client_with_auth to automatically add X-API-Key headers.
    Tests can use this fixture without worrying about authentication.
    """
    test_client, api_key = api_client_with_auth

    class AuthenticatedClient:
        def __init__(self, client, api_key):
            self._client = client
            self._api_key = api_key

        def _add_auth(self, kwargs):
            headers = kwargs.get("headers", {})
            headers["X-API-Key"] = self._api_key
            kwargs["headers"] = headers
            return kwargs

        def get(self, url, **kwargs):
            return self._client.get(url, **self._add_auth(kwargs))

        def post(self, url, **kwargs):
            return self._client.post(url, **self._add_auth(kwargs))

        def put(self, url, **kwargs):
            return self._client.put(url, **self._add_auth(kwargs))

        def delete(self, url, **kwargs):
            return self._client.delete(url, **self._add_auth(kwargs))

        def options(self, url, **kwargs):
            return self._client.options(url, **self._add_auth(kwargs))

    yield AuthenticatedClient(test_client, api_key)


@pytest.fixture(scope="function")
def api_client_with_auth(test_memory_config):
    """FastAPI test client with API key authentication"""
    try:
        from fastapi.testclient import TestClient
        from continuum.api.server import app
        from continuum.api.middleware import init_api_keys_db, hash_key, get_api_keys_db_path
        import sqlite3

        # Initialize API keys DB
        init_api_keys_db()

        # Create test API key
        api_key = "cm_test_key_12345"
        key_hash = hash_key(api_key)

        db_path = get_api_keys_db_path()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO api_keys (key_hash, tenant_id, created_at, name)
            VALUES (?, ?, ?, ?)
            """,
            (key_hash, "test_tenant", "2025-12-07T00:00:00", "Test Key")
        )
        conn.commit()
        conn.close()

        with TestClient(app) as client:
            yield client, api_key

    except ImportError:
        pytest.skip("FastAPI not available")


# =============================================================================
# BILLING TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def mock_stripe_client():
    """Mock Stripe client for billing tests"""
    mock_client = Mock()
    mock_client.create_customer.return_value = {"id": "cus_test123"}
    mock_client.create_subscription.return_value = {"id": "sub_test123", "status": "active"}
    mock_client.cancel_subscription.return_value = {"id": "sub_test123", "status": "canceled"}
    mock_client.report_usage.return_value = {"id": "usage_test123"}

    return mock_client


@pytest.fixture(scope="function")
def usage_metering():
    """Usage metering instance for testing"""
    from continuum.billing.metering import UsageMetering

    return UsageMetering()


@pytest.fixture(scope="function")
def rate_limiter(usage_metering):
    """Rate limiter instance for testing"""
    from continuum.billing.metering import RateLimiter

    return RateLimiter(usage_metering)


# =============================================================================
# FEDERATION TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def federation_nodes(integration_db_dir):
    """Create multiple federation nodes for testing"""
    from continuum.federation.node import FederatedNode

    nodes = {
        "node_a": FederatedNode(
            node_id="node_a_test",
            storage_path=integration_db_dir / "node_a"
        ),
        "node_b": FederatedNode(
            node_id="node_b_test",
            storage_path=integration_db_dir / "node_b"
        ),
        "node_c": FederatedNode(
            node_id="node_c_test",
            storage_path=integration_db_dir / "node_c"
        ),
    }

    return nodes


@pytest.fixture(scope="function")
def mock_federation_server():
    """Mock federation server for testing"""
    mock_server = Mock()
    mock_server.register_node.return_value = {
        "status": "registered",
        "node_id": "test_node",
        "access_level": "basic"
    }
    mock_server.sync_memories.return_value = {
        "status": "synced",
        "memories_received": 10,
        "memories_sent": 5
    }

    return mock_server


# =============================================================================
# CLI TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def cli_runner():
    """Click CLI runner for CLI integration tests"""
    try:
        from click.testing import CliRunner
        return CliRunner()
    except ImportError:
        pytest.skip("Click not available")


# =============================================================================
# CACHE TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing without actual Redis"""
    redis_mock = Mock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.ping.return_value = True
    redis_mock.flushdb.return_value = True

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


# =============================================================================
# CLEANUP
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Cleanup test environment before and after each test"""
    # Before test
    original_env = os.environ.copy()

    yield

    # After test
    os.environ.clear()
    os.environ.update(original_env)

    # Reset config
    try:
        from continuum.core.config import reset_config
        reset_config()
    except:
        pass
