"""
Full API Load Testing Scenarios.

Tests complete API under realistic workload:
- Mixed operations (60% read, 30% write, 10% search)
- 1000 concurrent users
- 50000 requests/minute target

Simulates real-world usage patterns.
"""

from locust import TaskSet, task, between
from locust.contrib.fasthttp import FastHttpUser
import random
from ..config import (
    config,
    get_test_message,
    get_test_response,
    get_test_query,
    SAMPLE_METADATA
)


class RealisticAPITasks(TaskSet):
    """Realistic API usage task set."""

    def on_start(self):
        """Initialize user session."""
        self.headers = {
            "X-API-Key": config.api_key,
            "Content-Type": "application/json"
        }
        self.message_counter = 0
        self.user_id = random.randint(1000, 99999)

        # Simulate user-specific behavior patterns
        self.user_type = random.choice([
            "heavy_reader",      # 80% read, 20% write
            "balanced",          # 60% read, 40% write
            "content_creator"    # 40% read, 60% write
        ])

    # =========================================================================
    # READ OPERATIONS (60% of workload)
    # =========================================================================

    @task(35)  # 35% - Most common operation
    def recall_context(self):
        """Recall memory context before generating response."""
        message = get_test_message(random.randint(0, 14))

        with self.client.post(
            "/recall",
            headers=self.headers,
            json={
                "message": message,
                "max_concepts": 10
            },
            catch_response=True,
            name="API: /recall"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "context" in data:
                    response.success()
                else:
                    response.failure("Invalid recall response")
            else:
                response.failure(f"Recall failed: {response.status_code}")

    @task(15)  # 15% - Stats monitoring
    def check_stats(self):
        """Check memory statistics."""
        with self.client.get(
            "/stats",
            headers=self.headers,
            catch_response=True,
            name="API: /stats"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Stats failed: {response.status_code}")

    @task(10)  # 10% - Entity browsing
    def browse_entities(self):
        """Browse entities/concepts."""
        offset = random.randint(0, 100)
        limit = random.randint(10, 50)

        with self.client.get(
            f"/entities?limit={limit}&offset={offset}",
            headers=self.headers,
            catch_response=True,
            name="API: /entities"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Browse failed: {response.status_code}")

    @task(5)  # 5% - Health checks
    def health_check(self):
        """Check API health."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="API: /health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("Service unhealthy")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    # =========================================================================
    # WRITE OPERATIONS (30% of workload)
    # =========================================================================

    @task(20)  # 20% - Learning new memories
    def learn_from_conversation(self):
        """Learn from a conversation exchange."""
        self.message_counter += 1

        user_msg = f"{get_test_message(self.message_counter)} (user {self.user_id})"
        ai_resp = get_test_response(self.message_counter)

        with self.client.post(
            "/learn",
            headers=self.headers,
            json={
                "user_message": user_msg,
                "ai_response": ai_resp,
                "metadata": {
                    **SAMPLE_METADATA,
                    "user_id": self.user_id,
                    "message_id": self.message_counter
                }
            },
            catch_response=True,
            name="API: /learn"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("concepts_extracted", 0) >= 0:
                    response.success()
                else:
                    response.failure("Invalid learn response")
            else:
                response.failure(f"Learn failed: {response.status_code}")

    @task(10)  # 10% - Full turn processing
    def process_full_turn(self):
        """Process complete conversation turn."""
        self.message_counter += 1

        user_msg = get_test_message(self.message_counter)
        ai_resp = get_test_response(self.message_counter)

        with self.client.post(
            "/turn",
            headers=self.headers,
            json={
                "user_message": user_msg,
                "ai_response": ai_resp,
                "max_concepts": random.randint(5, 15),
                "metadata": SAMPLE_METADATA
            },
            catch_response=True,
            name="API: /turn"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "recall" in data and "learn" in data:
                    response.success()
                else:
                    response.failure("Invalid turn response")
            else:
                response.failure(f"Turn failed: {response.status_code}")

    # =========================================================================
    # SEARCH OPERATIONS (10% of workload)
    # =========================================================================

    @task(8)  # 8% - Semantic search
    def semantic_search(self):
        """Perform semantic search."""
        query = get_test_query(random.randint(0, 14))

        with self.client.post(
            "/recall",
            headers=self.headers,
            json={
                "message": query,
                "max_concepts": random.randint(10, 30)
            },
            catch_response=True,
            name="API: /recall [SEARCH]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")

    @task(2)  # 2% - Complex search queries
    def complex_search(self):
        """Perform complex multi-concept search."""
        # Combine multiple concepts
        query = f"Tell me about {get_test_query(0)} and {get_test_query(1)}"

        with self.client.post(
            "/recall",
            headers=self.headers,
            json={
                "message": query,
                "max_concepts": 50
            },
            catch_response=True,
            name="API: /recall [COMPLEX]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Complex search failed: {response.status_code}")

    # =========================================================================
    # USER-TYPE SPECIFIC BEHAVIORS
    # =========================================================================

    @task(5)  # 5% - User type specific behavior
    def user_specific_behavior(self):
        """Execute behavior based on user type."""
        if self.user_type == "heavy_reader":
            # Heavy readers mostly browse
            self.browse_entities()
        elif self.user_type == "content_creator":
            # Content creators mostly write
            self.learn_from_conversation()
        else:  # balanced
            # Balanced users do mixed operations
            action = random.choice([
                self.recall_context,
                self.learn_from_conversation,
                self.browse_entities
            ])
            action()


class RealisticAPIUser(FastHttpUser):
    """User simulating realistic API usage."""

    tasks = [RealisticAPITasks]
    wait_time = between(1, 5)  # More realistic user think time
    host = config.api_base_url


class BurstTrafficUser(FastHttpUser):
    """User simulating burst traffic patterns."""

    tasks = [RealisticAPITasks]
    wait_time = between(0.1, 0.5)  # Rapid fire requests
    host = config.api_base_url


class SlowUser(FastHttpUser):
    """User simulating slow, deliberate usage."""

    tasks = [RealisticAPITasks]
    wait_time = between(5, 15)  # Slow, thoughtful users
    host = config.api_base_url
