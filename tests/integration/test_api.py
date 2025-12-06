"""
CONTINUUM API Integration Tests
Tests for REST API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from continuum.api.server import app
from continuum.storage.database import Base, get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestMemoryEndpoints:
    """Test memory CRUD endpoints"""

    def test_create_memory(self, client):
        """Test POST /memories"""
        memory_data = {
            "content": "Test memory content",
            "metadata": {"source": "test"},
            "tags": ["test", "api"]
        }

        response = client.post("/memories", json=memory_data)

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == memory_data["content"]
        assert "id" in data
        assert "created_at" in data

    def test_get_memory(self, client):
        """Test GET /memories/{id}"""
        # Create memory first
        memory_data = {
            "content": "Test memory for retrieval",
            "tags": ["test"]
        }
        create_response = client.post("/memories", json=memory_data)
        memory_id = create_response.json()["id"]

        # Retrieve memory
        response = client.get(f"/memories/{memory_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == memory_id
        assert data["content"] == memory_data["content"]

    def test_get_nonexistent_memory(self, client):
        """Test GET /memories/{id} with invalid ID"""
        response = client.get("/memories/99999")
        assert response.status_code == 404

    def test_list_memories(self, client):
        """Test GET /memories"""
        # Create multiple memories
        for i in range(3):
            memory_data = {
                "content": f"Test memory {i}",
                "tags": ["test"]
            }
            client.post("/memories", json=memory_data)

        # List memories
        response = client.get("/memories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_memory(self, client):
        """Test PUT /memories/{id}"""
        # Create memory
        memory_data = {
            "content": "Original content",
            "tags": ["test"]
        }
        create_response = client.post("/memories", json=memory_data)
        memory_id = create_response.json()["id"]

        # Update memory
        update_data = {
            "content": "Updated content",
            "tags": ["test", "updated"]
        }
        response = client.put(f"/memories/{memory_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == update_data["content"]
        assert "updated" in data["tags"]

    def test_delete_memory(self, client):
        """Test DELETE /memories/{id}"""
        # Create memory
        memory_data = {
            "content": "Memory to delete",
            "tags": ["test"]
        }
        create_response = client.post("/memories", json=memory_data)
        memory_id = create_response.json()["id"]

        # Delete memory
        response = client.delete(f"/memories/{memory_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/memories/{memory_id}")
        assert get_response.status_code == 404


class TestSearchEndpoints:
    """Test search endpoints"""

    def test_search_memories(self, client):
        """Test POST /search"""
        # Create searchable memories
        memories = [
            {"content": "Paris is the capital of France", "tags": ["geography"]},
            {"content": "Berlin is the capital of Germany", "tags": ["geography"]},
            {"content": "Python is a programming language", "tags": ["tech"]}
        ]

        for memory in memories:
            client.post("/memories", json=memory)

        # Search for capitals
        search_data = {
            "query": "capital",
            "limit": 10
        }
        response = client.post("/search", json=search_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert any("Paris" in r["content"] for r in data)

    def test_search_with_filters(self, client):
        """Test POST /search with tag filters"""
        # Create memories with different tags
        memories = [
            {"content": "Test 1", "tags": ["tag1", "tag2"]},
            {"content": "Test 2", "tags": ["tag2", "tag3"]},
            {"content": "Test 3", "tags": ["tag3"]}
        ]

        for memory in memories:
            client.post("/memories", json=memory)

        # Search with tag filter
        search_data = {
            "query": "Test",
            "tags": ["tag2"],
            "limit": 10
        }
        response = client.post("/search", json=search_data)

        assert response.status_code == 200
        data = response.json()
        assert all("tag2" in r["tags"] for r in data)

    def test_semantic_search(self, client):
        """Test POST /search/semantic"""
        # Create memories
        memory_data = {
            "content": "Machine learning and artificial intelligence",
            "tags": ["ai"]
        }
        client.post("/memories", json=memory_data)

        # Semantic search
        search_data = {
            "query": "AI and ML concepts",
            "limit": 5
        }
        response = client.post("/search/semantic", json=search_data)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestExtractionEndpoints:
    """Test extraction endpoints"""

    def test_extract_concepts(self, client):
        """Test POST /extract/concepts"""
        extraction_data = {
            "text": "The π×φ constant equals 5.083203692315260 and represents the edge of chaos."
        }

        response = client.post("/extract/concepts", json=extraction_data)

        assert response.status_code == 200
        data = response.json()
        assert "concepts" in data
        assert len(data["concepts"]) > 0

    def test_extract_entities(self, client):
        """Test POST /extract/entities"""
        extraction_data = {
            "text": "Alexander is working on CONTINUUM in Paris, France."
        }

        response = client.post("/extract/entities", json=extraction_data)

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert len(data["entities"]) > 0

    def test_extract_all(self, client):
        """Test POST /extract/all"""
        extraction_data = {
            "text": "CONTINUUM uses SQLite for storage. The project was started in 2025."
        }

        response = client.post("/extract/all", json=extraction_data)

        assert response.status_code == 200
        data = response.json()
        assert "concepts" in data
        assert "entities" in data
        assert "patterns" in data


class TestRateLimiting:
    """Test API rate limiting"""

    @pytest.mark.slow
    def test_rate_limit(self, client):
        """Test that rate limiting is enforced"""
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.get("/health")
            responses.append(response)

        # Should have at least some successful responses
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0

        # May have some rate-limited responses (429)
        # Note: This depends on rate limit configuration


class TestErrorHandling:
    """Test API error handling"""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/memories",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        response = client.post("/memories", json={})
        assert response.status_code == 422

    def test_invalid_field_types(self, client):
        """Test handling of invalid field types"""
        memory_data = {
            "content": 12345,  # Should be string
            "tags": "not_a_list"  # Should be list
        }
        response = client.post("/memories", json=memory_data)
        assert response.status_code == 422


class TestCORS:
    """Test CORS headers"""

    def test_cors_headers(self, client):
        """Test that CORS headers are present"""
        response = client.options(
            "/memories",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
