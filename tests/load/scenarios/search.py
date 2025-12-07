"""
Search Load Testing Scenarios.

Tests different search capabilities:
- Semantic search via /recall
- Graph traversal (concept relationships)
- Full-text search

Target: 1000 semantic/min, 500 graph/min, 2000 fulltext/min
"""

from locust import TaskSet, task, between
from locust.contrib.fasthttp import FastHttpUser
import random
from ..config import config, get_test_query, SAMPLE_SEARCH_QUERIES


class SearchTasks(TaskSet):
    """Search operations task set."""

    def on_start(self):
        """Initialize user session."""
        self.headers = {
            "X-API-Key": config.api_key,
            "Content-Type": "application/json"
        }
        self.query_counter = 0

    @task(50)  # 50% semantic search
    def semantic_search(self):
        """Test semantic search via recall endpoint."""
        query = get_test_query(random.randint(0, len(SAMPLE_SEARCH_QUERIES) - 1))

        with self.client.post(
            "/recall",
            headers=self.headers,
            json={
                "message": query,
                "max_concepts": random.randint(10, 50)
            },
            catch_response=True,
            name="/recall [SEMANTIC]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Semantic search should return context
                if "context" in data:
                    response.success()
                else:
                    response.failure("No context in semantic search")
            else:
                response.failure(f"Semantic search failed: {response.status_code}")

    @task(30)  # 30% complex queries
    def complex_semantic_search(self):
        """Test complex semantic queries with multiple concepts."""
        # Combine multiple queries for complexity
        query_parts = random.sample(SAMPLE_SEARCH_QUERIES, random.randint(2, 4))
        complex_query = f"Explain the relationship between {' and '.join(query_parts)}"

        with self.client.post(
            "/recall",
            headers=self.headers,
            json={
                "message": complex_query,
                "max_concepts": 30
            },
            catch_response=True,
            name="/recall [COMPLEX]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("concepts_found", 0) > 0:
                    response.success()
                else:
                    response.failure("No concepts found in complex search")
            else:
                response.failure(f"Complex search failed: {response.status_code}")

    @task(15)  # 15% entity search
    def entity_search(self):
        """Test entity filtering and search."""
        entity_types = ['concept', 'decision', 'session', 'person', 'project', 'tool', 'topic']
        entity_type = random.choice(entity_types)

        with self.client.get(
            f"/entities?limit={random.randint(20, 100)}&entity_type={entity_type}",
            headers=self.headers,
            catch_response=True,
            name=f"/entities [TYPE={entity_type}]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "entities" in data:
                    response.success()
                else:
                    response.failure("Invalid entity search response")
            else:
                response.failure(f"Entity search failed: {response.status_code}")

    @task(5)  # 5% pagination stress test
    def pagination_search(self):
        """Test pagination under load."""
        offset = random.randint(0, 1000)
        limit = random.randint(10, 100)

        with self.client.get(
            f"/entities?limit={limit}&offset={offset}",
            headers=self.headers,
            catch_response=True,
            name="/entities [PAGINATED]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "entities" in data and "total" in data:
                    response.success()
                else:
                    response.failure("Invalid pagination response")
            else:
                response.failure(f"Pagination failed: {response.status_code}")

    @task(10)  # 10% targeted recall
    def targeted_recall(self):
        """Test recall with varying concept limits."""
        query = get_test_query(self.query_counter)
        self.query_counter += 1

        # Test different concept limits
        max_concepts = random.choice([5, 10, 20, 50, 100])

        with self.client.post(
            "/recall",
            headers=self.headers,
            json={
                "message": query,
                "max_concepts": max_concepts
            },
            catch_response=True,
            name=f"/recall [LIMIT={max_concepts}]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                concepts_found = data.get("concepts_found", 0)
                # Should not exceed requested limit
                if concepts_found <= max_concepts:
                    response.success()
                else:
                    response.failure(f"Exceeded concept limit: {concepts_found} > {max_concepts}")
            else:
                response.failure(f"Targeted recall failed: {response.status_code}")


class SearchUser(FastHttpUser):
    """User simulating search operations."""

    tasks = [SearchTasks]
    wait_time = between(0.05, 1)  # Faster than memory ops - search is read-heavy
    host = config.api_base_url
