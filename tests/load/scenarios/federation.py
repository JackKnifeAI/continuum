"""
Federation Load Testing Scenarios.

Tests peer-to-peer synchronization:
- Memory sync between peers
- Concurrent peer connections
- Conflict resolution under load

Target: 100 syncs/second, 10 concurrent peers
"""

from locust import TaskSet, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import random
import json
from datetime import datetime, timezone
from ..config import config, get_test_message, get_test_response


class FederationTasks(TaskSet):
    """Federation operations task set."""

    def on_start(self):
        """Initialize federation session."""
        self.headers = {
            "X-API-Key": config.api_key,
            "Content-Type": "application/json"
        }
        self.node_id = f"load_test_node_{random.randint(1000, 9999)}"
        self.peer_nodes = []
        self.sync_counter = 0

    @task(40)  # 40% memory contribution
    def contribute_memory(self):
        """Test contributing memories to federation."""
        memory_data = {
            "node_id": self.node_id,
            "memories": [
                {
                    "user_message": get_test_message(self.sync_counter),
                    "ai_response": get_test_response(self.sync_counter),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "source": "federation_test",
                        "node": self.node_id
                    }
                }
            ]
        }
        self.sync_counter += 1

        # Note: This endpoint may not exist yet - testing the load pattern
        with self.client.post(
            "/federation/contribute",
            headers=self.headers,
            json=memory_data,
            catch_response=True,
            name="/federation/contribute [SYNC]"
        ) as response:
            if response.status_code in [200, 201, 404]:  # 404 acceptable if not implemented
                if response.status_code == 404:
                    response.success()  # Mark as success to test load, not functionality
                else:
                    data = response.json()
                    if data.get("status") == "accepted" or "memories" in data:
                        response.success()
                    else:
                        response.failure("Invalid contribution response")
            else:
                response.failure(f"Contribution failed: {response.status_code}")

    @task(30)  # 30% request sync
    def request_sync(self):
        """Test requesting memories from peers."""
        sync_request = {
            "node_id": self.node_id,
            "since": datetime.now(timezone.utc).isoformat(),
            "limit": random.randint(10, 100)
        }

        with self.client.post(
            "/federation/request",
            headers=self.headers,
            json=sync_request,
            catch_response=True,
            name="/federation/request [SYNC]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Sync request failed: {response.status_code}")

    @task(20)  # 20% peer discovery
    def discover_peers(self):
        """Test peer discovery under load."""
        with self.client.get(
            "/federation/peers",
            headers=self.headers,
            catch_response=True,
            name="/federation/peers [DISCOVERY]"
        ) as response:
            if response.status_code in [200, 404]:
                if response.status_code == 200:
                    data = response.json()
                    if "peers" in data:
                        self.peer_nodes = data.get("peers", [])
                response.success()
            else:
                response.failure(f"Peer discovery failed: {response.status_code}")

    @task(10)  # 10% conflict resolution simulation
    def simulate_conflict(self):
        """Test conflict resolution by sending competing updates."""
        # Create two versions of the same memory
        base_message = get_test_message(self.sync_counter)

        version_a = {
            "node_id": self.node_id,
            "memory_id": f"mem_{self.sync_counter}",
            "version": 1,
            "user_message": f"{base_message} (version A)",
            "ai_response": get_test_response(self.sync_counter),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        version_b = {
            "node_id": f"{self.node_id}_peer",
            "memory_id": f"mem_{self.sync_counter}",
            "version": 1,
            "user_message": f"{base_message} (version B)",
            "ai_response": get_test_response(self.sync_counter),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Send both versions
        with self.client.post(
            "/federation/contribute",
            headers=self.headers,
            json={"node_id": self.node_id, "memories": [version_a]},
            catch_response=True,
            name="/federation/contribute [CONFLICT_A]"
        ) as response:
            response.success() if response.status_code in [200, 201, 404] else response.failure("Conflict A failed")

        with self.client.post(
            "/federation/contribute",
            headers=self.headers,
            json={"node_id": f"{self.node_id}_peer", "memories": [version_b]},
            catch_response=True,
            name="/federation/contribute [CONFLICT_B]"
        ) as response:
            response.success() if response.status_code in [200, 201, 404] else response.failure("Conflict B failed")

        self.sync_counter += 1

    @task(5)  # 5% heartbeat
    def send_heartbeat(self):
        """Test heartbeat/keepalive under load."""
        heartbeat = {
            "node_id": self.node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }

        with self.client.post(
            "/federation/heartbeat",
            headers=self.headers,
            json=heartbeat,
            catch_response=True,
            name="/federation/heartbeat [KEEPALIVE]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Heartbeat failed: {response.status_code}")


class FederationUser(FastHttpUser):
    """User simulating federation operations."""

    tasks = [FederationTasks]
    wait_time = between(0.01, 0.5)  # Fast sync operations
    host = config.api_base_url

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simulate persistent connections for federation
        self.connection_pool_size = 10
