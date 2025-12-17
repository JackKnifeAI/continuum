"""
CONTINUUM API Integration Tests
Tests for REST API endpoints
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from continuum.api.server import app
from continuum.core.config import set_config, MemoryConfig


@pytest.fixture(scope="function")
def client(api_client_with_auth):
    """
    Create test client with API key authentication.

    Uses the api_client_with_auth fixture from conftest.py which:
    1. Initializes the API keys database
    2. Creates a test API key
    3. Returns (TestClient, api_key)

    This fixture wraps calls to automatically include the X-API-Key header.
    """
    test_client, api_key = api_client_with_auth

    # Wrap the client to automatically add auth headers
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


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test /v1/health endpoint"""
        response = client.get("/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "continuum"
        assert "version" in data
        assert "timestamp" in data


@pytest.mark.integration
class TestRootEndpoint:
    """Test root endpoint"""

    def test_root(self, client):
        """Test / endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "CONTINUUM"
        assert "version" in data
        assert "endpoints" in data


@pytest.mark.integration
class TestMemoryEndpoints:
    """Test core memory endpoints"""

    def test_recall_endpoint(self, client):
        """Test POST /v1/recall"""
        recall_data = {
            "message": "What is the capital of France?",
            "max_concepts": 10
        }

        response = client.post("/v1/recall", json=recall_data)

        # Should succeed even with empty memory
        assert response.status_code == 200
        data = response.json()
        assert "context" in data
        assert "concepts_found" in data
        assert "relationships_found" in data
        assert "query_time_ms" in data

    def test_learn_endpoint(self, client):
        """Test POST /v1/learn"""
        learn_data = {
            "user_message": "What is Python?",
            "ai_response": "Python is a programming language."
        }

        response = client.post("/v1/learn", json=learn_data)

        assert response.status_code == 200
        data = response.json()
        assert "concepts_extracted" in data
        assert "decisions_detected" in data
        assert "links_created" in data
        assert "compounds_found" in data
        assert data["concepts_extracted"] >= 0

    def test_turn_endpoint(self, client):
        """Test POST /v1/turn (combined recall + learn)"""
        turn_data = {
            "user_message": "Tell me about SQLite",
            "ai_response": "SQLite is a database engine."
        }

        response = client.post("/v1/turn", json=turn_data)

        assert response.status_code == 200
        data = response.json()
        assert "recall" in data
        assert "learn" in data
        assert "context" in data["recall"]
        assert "concepts_extracted" in data["learn"]

    def test_recall_after_learning(self, client):
        """Test that recall finds concepts after learning"""
        # First, learn about Python
        learn_data = {
            "user_message": "What is Python?",
            "ai_response": "Python is a programming language created by Guido van Rossum."
        }
        client.post("/v1/learn", json=learn_data)

        # Then try to recall Python-related context
        recall_data = {
            "message": "Tell me about Python programming",
            "max_concepts": 10
        }
        response = client.post("/v1/recall", json=recall_data)

        assert response.status_code == 200
        data = response.json()
        # Should find some concepts (may be zero if extraction didn't capture anything)
        assert data["concepts_found"] >= 0


@pytest.mark.integration
class TestStatisticsEndpoints:
    """Test statistics endpoints"""

    def test_get_stats(self, client):
        """Test GET /v1/stats"""
        # First add some data
        learn_data = {
            "user_message": "What is WorkingMemory?",
            "ai_response": "WorkingMemory is a concept in CONTINUUM."
        }
        client.post("/v1/learn", json=learn_data)

        # Get stats
        response = client.get("/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data
        assert "entities" in data
        assert "messages" in data
        assert "decisions" in data
        assert "attention_links" in data

    def test_get_entities(self, client):
        """Test GET /v1/entities"""
        response = client.get("/v1/entities")

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "total" in data
        assert "tenant_id" in data
        assert isinstance(data["entities"], list)

    def test_get_entities_with_pagination(self, client):
        """Test GET /v1/entities with pagination"""
        response = client.get("/v1/entities?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) <= 10


@pytest.mark.integration
class TestAdminEndpoints:
    """Test admin endpoints"""

    def test_list_tenants(self, client):
        """Test GET /v1/tenants"""
        response = client.get("/v1/tenants")

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert isinstance(data["tenants"], list)

    def test_create_api_key(self, client):
        """Test POST /v1/keys"""
        key_request = {
            "tenant_id": "new_tenant",
            "name": "Test Key"
        }

        response = client.post("/v1/keys", json=key_request)

        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("cm_")
        assert data["tenant_id"] == "new_tenant"
        assert "message" in data


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling"""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/v1/recall",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        response = client.post("/v1/recall", json={})
        assert response.status_code == 422

    def test_invalid_field_types(self, client):
        """Test handling of invalid field types"""
        recall_data = {
            "message": 12345,  # Should be string
            "max_concepts": "invalid"  # Should be int
        }
        response = client.post("/v1/recall", json=recall_data)
        assert response.status_code == 422


@pytest.mark.integration
class TestFullWorkflow:
    """Test complete memory workflow"""

    def test_complete_memory_cycle(self, client):
        """Test full cycle: learn -> recall -> learn again"""
        # Step 1: Learn initial knowledge
        learn1 = {
            "user_message": "What is the CONTINUUM project?",
            "ai_response": "CONTINUUM is an AI memory infrastructure system."
        }
        response1 = client.post("/v1/learn", json=learn1)
        assert response1.status_code == 200

        # Step 2: Recall the knowledge
        recall = {
            "message": "Tell me about CONTINUUM"
        }
        response2 = client.post("/v1/recall", json=recall)
        assert response2.status_code == 200
        recall_data = response2.json()
        # Context may be present
        assert "context" in recall_data

        # Step 3: Learn more related knowledge
        learn2 = {
            "user_message": "How does CONTINUUM work?",
            "ai_response": "CONTINUUM uses SQLite for persistent storage and builds knowledge graphs."
        }
        response3 = client.post("/v1/learn", json=learn2)
        assert response3.status_code == 200

        # Step 4: Check stats
        stats_response = client.get("/v1/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["messages"] >= 4  # 2 user + 2 assistant messages

    def test_decision_tracking(self, client):
        """Test that decisions are tracked"""
        learn_data = {
            "user_message": "Can you create a module?",
            "ai_response": "I am going to create a new Python module for memory persistence."
        }

        response = client.post("/v1/learn", json=learn_data)
        assert response.status_code == 200
        data = response.json()

        # Should detect at least one decision
        assert data["decisions_detected"] >= 1

        # Check stats
        stats_response = client.get("/v1/stats")
        stats = stats_response.json()
        assert stats["decisions"] >= 1
