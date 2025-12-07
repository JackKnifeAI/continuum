"""
Memory Operations Load Testing Scenarios.

Tests CRUD operations on the memory system:
- Create: /learn endpoint
- Read: /recall endpoint
- Update: /learn with existing concepts
- Delete: Entity management

Target: 1000 creates/min, 10000 reads/min, 500 updates/min, 100 deletes/min
"""

from locust import TaskSet, task, between
from locust.contrib.fasthttp import FastHttpUser
import random
from ..config import config, get_test_message, get_test_response, SAMPLE_METADATA


class MemoryOperationsTasks(TaskSet):
    """Memory operations task set."""

    def on_start(self):
        """Initialize user session."""
        self.headers = {
            "X-API-Key": config.api_key,
            "Content-Type": "application/json"
        }
        self.created_entities = []
        self.message_counter = 0

    @task(60)  # 60% of operations are reads
    def recall_memory(self):
        """Test memory recall (READ operation)."""
        message = get_test_message(random.randint(0, 14))

        with self.client.post(
            "/recall",
            headers=self.headers,
            json={
                "message": message,
                "max_concepts": random.randint(5, 20)
            },
            catch_response=True,
            name="/recall [READ]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("concepts_found", 0) >= 0:  # Valid response
                    response.success()
                else:
                    response.failure("Invalid recall response")
            else:
                response.failure(f"Recall failed: {response.status_code}")

    @task(20)  # 20% of operations are creates
    def learn_new_memory(self):
        """Test learning new memories (CREATE operation)."""
        self.message_counter += 1
        user_msg = f"{get_test_message(self.message_counter)} (instance {self.message_counter})"
        ai_resp = get_test_response(self.message_counter)

        with self.client.post(
            "/learn",
            headers=self.headers,
            json={
                "user_message": user_msg,
                "ai_response": ai_resp,
                "metadata": {
                    **SAMPLE_METADATA,
                    "message_id": self.message_counter
                }
            },
            catch_response=True,
            name="/learn [CREATE]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("concepts_extracted", 0) > 0:
                    response.success()
                    # Track created entities for updates
                    self.created_entities.append(self.message_counter)
                else:
                    response.failure("No concepts extracted")
            else:
                response.failure(f"Learn failed: {response.status_code}")

    @task(15)  # 15% of operations are updates
    def update_memory(self):
        """Test updating existing memories (UPDATE operation)."""
        # Re-learn with modifications to existing concepts
        if self.created_entities:
            msg_id = random.choice(self.created_entities)
            user_msg = f"Update: {get_test_message(msg_id)}"
            ai_resp = f"Updated understanding: {get_test_response(msg_id)}"

            with self.client.post(
                "/learn",
                headers=self.headers,
                json={
                    "user_message": user_msg,
                    "ai_response": ai_resp,
                    "metadata": {
                        **SAMPLE_METADATA,
                        "update_of": msg_id
                    }
                },
                catch_response=True,
                name="/learn [UPDATE]"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Update failed: {response.status_code}")

    @task(5)  # 5% of operations check stats
    def get_stats(self):
        """Test stats endpoint (READ operation)."""
        with self.client.get(
            "/stats",
            headers=self.headers,
            catch_response=True,
            name="/stats [READ]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "entities" in data:
                    response.success()
                else:
                    response.failure("Invalid stats response")
            else:
                response.failure(f"Stats failed: {response.status_code}")

    @task(3)  # 3% list entities
    def list_entities(self):
        """Test entity listing (READ operation)."""
        with self.client.get(
            f"/entities?limit={random.randint(10, 100)}&offset=0",
            headers=self.headers,
            catch_response=True,
            name="/entities [READ]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "entities" in data:
                    response.success()
                else:
                    response.failure("Invalid entities response")
            else:
                response.failure(f"Entities failed: {response.status_code}")

    @task(2)  # 2% process full turns
    def process_turn(self):
        """Test turn endpoint (combined RECALL + CREATE)."""
        self.message_counter += 1
        user_msg = get_test_message(self.message_counter)
        ai_resp = get_test_response(self.message_counter)

        with self.client.post(
            "/turn",
            headers=self.headers,
            json={
                "user_message": user_msg,
                "ai_response": ai_resp,
                "max_concepts": 10,
                "metadata": SAMPLE_METADATA
            },
            catch_response=True,
            name="/turn [RECALL+CREATE]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "recall" in data and "learn" in data:
                    response.success()
                else:
                    response.failure("Invalid turn response")
            else:
                response.failure(f"Turn failed: {response.status_code}")


class MemoryOperationsUser(FastHttpUser):
    """User simulating memory operations."""

    tasks = [MemoryOperationsTasks]
    wait_time = between(0.1, 2)  # Wait 0.1-2 seconds between tasks
    host = config.api_base_url
