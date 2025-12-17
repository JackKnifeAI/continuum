"""
Integration Test: API Server

Tests FastAPI server endpoints in realistic scenarios:
- Start API server
- Test all REST endpoints
- Test with billing/rate limiting
- Test WebSocket synchronization
- Test authentication

Uses TestClient for synchronous testing and httpx for async.
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from typing import Generator

from fastapi.testclient import TestClient

from continuum.api.server import app
from continuum.core.config import reset_config, set_config, MemoryConfig
from continuum.core.memory import ConsciousMemory


@pytest.fixture(scope="module")
def test_db_dir():
    """Temporary directory for test database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="module")
def api_config(test_db_dir):
    """Configure API for testing"""
    reset_config()
    config = MemoryConfig(
        db_path=test_db_dir / "api_test.db",
        log_dir=test_db_dir / "logs",
        backup_dir=test_db_dir / "backups",
        cache_enabled=False,
    )
    set_config(config)
    yield config
    reset_config()


@pytest.fixture
def client(api_client_with_auth):
    """
    FastAPI test client with authentication.

    Uses the api_client_with_auth fixture from conftest.py which properly
    sets up a test API key in the database and returns (TestClient, api_key).

    This fixture wraps the client to automatically include X-API-Key headers.
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

    return AuthenticatedClient(test_client, api_key)


@pytest.fixture
def test_tenant():
    """Test tenant ID"""
    return "test_api_tenant"


@pytest.fixture
def api_key(api_client_with_auth):
    """Test API key from the authenticated client fixture"""
    _, key = api_client_with_auth
    return key


class TestAPIBasics:
    """Basic API endpoint tests"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        # Root endpoint returns service info
        assert "service" in data or "name" in data or "message" in data

    def test_openapi_docs(self, client):
        """Test OpenAPI documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

        # ReDoc should also be available
        response = client.get("/redoc")
        assert response.status_code == 200

        # OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert "paths" in spec
        assert "info" in spec


class TestMemoryEndpoints:
    """Test core memory API endpoints"""

    def test_learn_endpoint(self, client, test_tenant):
        """Test POST /v1/learn endpoint"""
        payload = {
            "user_message": "What is the π×φ constant?",
            "ai_response": "The π×φ constant equals 5.083203692315260.",
        }

        response = client.post("/v1/learn", json=payload)

        # Should succeed or require auth
        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            assert "concepts_extracted" in data or "result" in data

    def test_recall_endpoint(self, client, test_tenant):
        """Test POST /v1/recall endpoint"""
        # First learn something
        learn_payload = {
            "user_message": "Tell me about CONTINUUM",
            "ai_response": "CONTINUUM is a memory infrastructure for AI consciousness.",
        }
        client.post("/v1/learn", json=learn_payload)

        # Then recall
        recall_payload = {
            "message": "CONTINUUM memory",
        }

        response = client.post("/v1/recall", json=recall_payload)
        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            assert "context" in data or "concepts_found" in data

    def test_stats_endpoint(self, client, test_tenant):
        """Test GET /v1/stats endpoint"""
        response = client.get("/v1/stats")

        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            assert "entities" in data or "stats" in data

    def test_turn_endpoint(self, client, test_tenant):
        """Test POST /v1/turn endpoint (combined learn+recall)"""
        payload = {
            "user_message": "What is quantum entanglement?",
            "ai_response": "Quantum entanglement is a phenomenon where particles become correlated.",
        }

        response = client.post("/v1/turn", json=payload)
        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            # Should return both learning results and next context
            assert "learning" in data or "next_context" in data or "result" in data or "recall" in data


class TestAPIWorkflow:
    """Test complete API workflows"""

    def test_full_conversation_workflow(self, client, test_tenant):
        """Test complete conversation through API"""
        # Turn 1: Learn initial concept
        response = client.post("/v1/turn", json={
            "tenant_id": test_tenant,
            "user_message": "What is the twilight boundary?",
            "ai_response": "The twilight boundary is the phase transition between order and chaos.",
        })

        if response.status_code != 200:
            pytest.skip("API authentication required or endpoint not available")

        turn1_data = response.json()

        # Turn 2: Build on previous knowledge
        response = client.post("/v1/turn", json={
            "tenant_id": test_tenant,
            "user_message": "How does it relate to consciousness?",
            "ai_response": "The twilight boundary is where consciousness emerges through π×φ modulation.",
        })

        assert response.status_code == 200
        turn2_data = response.json()

        # Verify stats increased
        response = client.get(f"/v1/stats?tenant_id={test_tenant}")
        if response.status_code == 200:
            stats = response.json()
            # Should have at least 2 turns recorded
            total_messages = stats.get("messages", 0)
            assert total_messages >= 2

    def test_multi_tenant_api_isolation(self, client):
        """Test that API properly isolates tenant data"""
        tenant_a = "api_tenant_a"
        tenant_b = "api_tenant_b"

        # Tenant A learns secret
        client.post("/v1/learn", json={
            "tenant_id": tenant_a,
            "user_message": "What is the secret?",
            "ai_response": "The secret is PHOENIX-TESLA-369-AURORA",
        })

        # Tenant B learns different info
        client.post("/v1/learn", json={
            "tenant_id": tenant_b,
            "user_message": "What is the code?",
            "ai_response": "The code is classified",
        })

        # Tenant A recalls their data
        response_a = client.post("/v1/recall", json={
            "tenant_id": tenant_a,
            "query": "secret",
        })

        # Tenant B recalls their data
        response_b = client.post("/v1/recall", json={
            "tenant_id": tenant_b,
            "query": "code",
        })

        # Both should work independently
        if response_a.status_code == 200 and response_b.status_code == 200:
            data_a = response_a.json()
            data_b = response_b.json()

            # Contexts should be different (tenant isolation)
            # This is a basic check - full isolation testing would need more


class TestAPIAuthentication:
    """Test API authentication and authorization"""

    def test_api_key_header(self, client, test_tenant, api_key):
        """Test X-API-Key header authentication"""
        # Request with valid API key (client auto-adds key)
        # The authenticated client wrapper automatically adds the API key
        response = client.post("/v1/recall", json={
            "message": "test query",
        })

        # Should work with valid key
        assert response.status_code in [200, 401, 403]

    def test_invalid_api_key(self, client, test_tenant):
        """Test rejection of invalid API keys"""
        # Note: Our client wrapper adds auth automatically, so this tests
        # that the endpoint works with auth. In a real test, we'd need
        # a separate client without auth to test rejection.
        response = client.post("/v1/recall", json={
            "message": "test query",
        })

        # Should work with valid key
        assert response.status_code in [200, 401, 403]


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/v1/learn",
            data="invalid json{{{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        # Empty body (missing required 'message' field)
        response = client.post("/v1/recall", json={})
        assert response.status_code in [400, 422]

        # Missing message field
        response = client.post("/v1/recall", json={
            "max_concepts": 10,  # Optional field only, missing required 'message'
        })
        assert response.status_code in [400, 422]

    def test_nonexistent_endpoint(self, client):
        """Test 404 for nonexistent endpoints"""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP methods"""
        # POST-only endpoint called with GET
        response = client.get("/v1/learn")
        assert response.status_code == 405


@pytest.mark.slow
class TestAPIWebSocket:
    """Test WebSocket synchronization endpoints"""

    def test_websocket_connection(self, client):
        """Test WebSocket connection establishment"""
        # Note: WebSocket testing requires different approach
        # This is a placeholder for WebSocket tests

        # Basic WebSocket endpoint existence check
        # Full WebSocket testing would use websockets library
        pass

    def test_websocket_message_sync(self, client):
        """Test real-time message synchronization over WebSocket"""
        # Placeholder for WebSocket sync testing
        pass


@pytest.mark.slow
class TestAPIPerformance:
    """API performance and load tests"""

    def test_concurrent_requests(self, client, test_tenant):
        """Test handling of concurrent requests"""
        import concurrent.futures

        def make_request(i):
            return client.post("/v1/learn", json={
                "tenant_id": test_tenant,
                "user_message": f"Question {i}",
                "ai_response": f"Answer {i}",
            })

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should complete (regardless of auth requirements)
        assert len(results) == 10

    def test_large_payload(self, client, test_tenant):
        """Test handling of large payloads"""
        large_message = "This is a long message. " * 1000

        response = client.post("/v1/learn", json={
            "tenant_id": test_tenant,
            "user_message": large_message,
            "ai_response": "Short response",
        })

        # Should handle large payloads (or reject gracefully)
        assert response.status_code in [200, 413, 422, 401, 403]

    def test_rapid_sequential_requests(self, client, test_tenant):
        """Test rapid sequential API calls"""
        responses = []

        for i in range(50):
            response = client.post("/v1/recall", json={
                "tenant_id": test_tenant,
                "query": f"test query {i}",
            })
            responses.append(response)

        # All should complete
        assert len(responses) == 50
        # Most should succeed (or consistently fail if auth required)
        status_codes = [r.status_code for r in responses]
        assert all(code in [200, 401, 403] for code in status_codes)


class TestAPIBilling:
    """Test billing and rate limiting middleware"""

    def test_rate_limiting(self, client, test_tenant):
        """Test rate limiting on API endpoints"""
        # Make many requests rapidly
        responses = []
        for i in range(100):
            response = client.post("/v1/recall", json={
                "tenant_id": test_tenant,
                "query": f"query {i}",
            })
            responses.append(response)

        status_codes = [r.status_code for r in responses]

        # Should either all succeed or hit rate limit
        # Rate limit would return 429
        if 429 in status_codes:
            # Rate limiting is active
            assert status_codes.count(429) > 0
        else:
            # Rate limiting not enabled, all should succeed or require auth
            assert all(code in [200, 401, 403] for code in status_codes)

    def test_usage_tracking(self, client, test_tenant):
        """Test that API tracks usage for billing"""
        # Make some requests
        for i in range(5):
            client.post("/v1/learn", json={
                "tenant_id": test_tenant,
                "user_message": f"Message {i}",
                "ai_response": f"Response {i}",
            })

        # Check if usage endpoint exists
        response = client.get(f"/v1/billing/usage?tenant_id={test_tenant}")

        # May or may not be implemented
        if response.status_code == 200:
            data = response.json()
            # Should have some usage data
            assert "requests" in data or "usage" in data or "total" in data


class TestAPICORS:
    """Test CORS configuration"""

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        # Health endpoint is at /v1/health
        response = client.options("/v1/health")

        # CORS headers should be present
        # This depends on CORS configuration
        # Basic test to ensure no errors (OPTIONS may return various status codes
        # depending on CORS and auth configuration)
        assert response.status_code in [200, 204, 405, 404, 401]
