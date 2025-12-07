"""
CONTINUUM Load Testing Suite

Main Locust configuration for load testing CONTINUUM API.

Usage:
    # Web UI mode (recommended)
    locust -f locustfile.py --host http://localhost:8000

    # Headless mode
    locust -f locustfile.py --headless --users 1000 --spawn-rate 10 --run-time 5m

    # Specific scenario
    locust -f locustfile.py --headless --tags memory --users 100 --spawn-rate 5

Test Scenarios:
    - memory: Memory CRUD operations
    - search: Search and retrieval operations
    - federation: Peer sync and federation
    - api: Full API realistic workload

Performance Targets:
    - Memory Ops: 1000 creates/min, 10000 reads/min
    - Search: 1000 semantic/min, 2000 fulltext/min
    - Federation: 100 syncs/sec, 10 concurrent peers
    - API: 50000 requests/min, 1000 concurrent users
    - P95 latency: <200ms for most endpoints
    - P99 latency: <500ms for most endpoints
    - Error rate: <1% (5% for federation)
"""

import logging
from locust import events, HttpUser
from locust.env import Environment

# Import all scenario users
from scenarios.memory_operations import MemoryOperationsUser
from scenarios.search import SearchUser
from scenarios.federation import FederationUser
from scenarios.api import RealisticAPIUser, BurstTrafficUser, SlowUser
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM METRICS AND MONITORING
# =============================================================================

# Track custom metrics
custom_metrics = {
    "concepts_extracted": [],
    "concepts_found": [],
    "query_times": [],
    "sync_operations": 0,
    "conflicts_detected": 0,
}


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Track custom metrics from requests."""
    if exception:
        # Track failures
        logger.warning(f"Request failed: {name} - {exception}")
    else:
        # Track successful requests
        custom_metrics["query_times"].append(response_time)

        # Track specific metrics if available in context
        if context and isinstance(context, dict):
            if "concepts_extracted" in context:
                custom_metrics["concepts_extracted"].append(context["concepts_extracted"])
            if "concepts_found" in context:
                custom_metrics["concepts_found"].append(context["concepts_found"])


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    logger.info("=" * 80)
    logger.info("CONTINUUM LOAD TEST STARTED")
    logger.info("=" * 80)
    logger.info(f"Target host: {config.api_base_url}")
    logger.info(f"Users: {config.users_min} to {config.users_max}")
    logger.info(f"Spawn rate: {config.spawn_rate}/sec")
    logger.info(f"Duration: {config.duration_seconds}s")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate test summary."""
    logger.info("=" * 80)
    logger.info("CONTINUUM LOAD TEST COMPLETED")
    logger.info("=" * 80)

    # Calculate summary statistics
    stats = environment.stats

    logger.info("\nOVERALL STATISTICS:")
    logger.info(f"  Total requests: {stats.total.num_requests}")
    logger.info(f"  Total failures: {stats.total.num_failures}")
    logger.info(f"  Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"  Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"  Min response time: {stats.total.min_response_time:.2f}ms")
    logger.info(f"  Max response time: {stats.total.max_response_time:.2f}ms")
    logger.info(f"  Median response time: {stats.total.median_response_time:.2f}ms")
    logger.info(f"  95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"  99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    logger.info(f"  RPS: {stats.total.total_rps:.2f}")

    # Custom metrics
    if custom_metrics["concepts_extracted"]:
        avg_concepts = sum(custom_metrics["concepts_extracted"]) / len(custom_metrics["concepts_extracted"])
        logger.info(f"\nCONCEPT EXTRACTION:")
        logger.info(f"  Average concepts/request: {avg_concepts:.2f}")
        logger.info(f"  Total extraction events: {len(custom_metrics['concepts_extracted'])}")

    if custom_metrics["concepts_found"]:
        avg_found = sum(custom_metrics["concepts_found"]) / len(custom_metrics["concepts_found"])
        logger.info(f"\nCONCEPT RECALL:")
        logger.info(f"  Average concepts found: {avg_found:.2f}")
        logger.info(f"  Total recall events: {len(custom_metrics['concepts_found'])}")

    # Performance analysis
    logger.info("\nPERFORMANCE ANALYSIS:")

    # Check against targets
    targets_met = []
    targets_failed = []

    # API targets
    api_targets = config.targets["api"]
    if stats.total.get_response_time_percentile(0.95) <= api_targets["p95_ms"]:
        targets_met.append(f"✓ P95 latency: {stats.total.get_response_time_percentile(0.95):.2f}ms <= {api_targets['p95_ms']}ms")
    else:
        targets_failed.append(f"✗ P95 latency: {stats.total.get_response_time_percentile(0.95):.2f}ms > {api_targets['p95_ms']}ms")

    if stats.total.get_response_time_percentile(0.99) <= api_targets["p99_ms"]:
        targets_met.append(f"✓ P99 latency: {stats.total.get_response_time_percentile(0.99):.2f}ms <= {api_targets['p99_ms']}ms")
    else:
        targets_failed.append(f"✗ P99 latency: {stats.total.get_response_time_percentile(0.99):.2f}ms > {api_targets['p99_ms']}ms")

    if stats.total.fail_ratio <= api_targets["error_rate"]:
        targets_met.append(f"✓ Error rate: {stats.total.fail_ratio * 100:.2f}% <= {api_targets['error_rate'] * 100}%")
    else:
        targets_failed.append(f"✗ Error rate: {stats.total.fail_ratio * 100:.2f}% > {api_targets['error_rate'] * 100}%")

    # RPM target (convert from total_rpm)
    rpm = stats.total.total_rps * 60
    if rpm >= api_targets["total_rpm"] * 0.8:  # 80% of target acceptable
        targets_met.append(f"✓ Throughput: {rpm:.0f} RPM >= {api_targets['total_rpm'] * 0.8:.0f} RPM (80% of target)")
    else:
        targets_failed.append(f"✗ Throughput: {rpm:.0f} RPM < {api_targets['total_rpm'] * 0.8:.0f} RPM (80% of target)")

    if targets_met:
        logger.info("\nTARGETS MET:")
        for target in targets_met:
            logger.info(f"  {target}")

    if targets_failed:
        logger.info("\nTARGETS FAILED:")
        for target in targets_failed:
            logger.info(f"  {target}")

    # Endpoint breakdown
    logger.info("\nENDPOINT BREAKDOWN:")
    for name, entry in stats.entries.items():
        if entry.num_requests > 0:
            logger.info(f"\n  {name}:")
            logger.info(f"    Requests: {entry.num_requests}")
            logger.info(f"    Failures: {entry.num_failures} ({entry.fail_ratio * 100:.2f}%)")
            logger.info(f"    Avg: {entry.avg_response_time:.2f}ms")
            logger.info(f"    P95: {entry.get_response_time_percentile(0.95):.2f}ms")
            logger.info(f"    P99: {entry.get_response_time_percentile(0.99):.2f}ms")

    logger.info("\n" + "=" * 80)

    # Generate pass/fail summary
    if targets_failed:
        logger.warning("RESULT: SOME TARGETS FAILED - Review performance")
    else:
        logger.info("RESULT: ALL TARGETS MET - System performing well")

    logger.info("=" * 80)


# =============================================================================
# TAG-BASED SCENARIO SELECTION
# =============================================================================

# Tag users for easy filtering
MemoryOperationsUser.tags = {"memory", "crud"}
SearchUser.tags = {"search", "read"}
FederationUser.tags = {"federation", "sync"}
RealisticAPIUser.tags = {"api", "realistic"}
BurstTrafficUser.tags = {"api", "burst"}
SlowUser.tags = {"api", "slow"}


# =============================================================================
# WEIGHT DISTRIBUTION FOR MIXED LOAD
# =============================================================================

class MixedWorkloadUser(HttpUser):
    """
    Mixed workload combining all scenarios.

    Weight distribution reflects realistic usage:
    - 40% realistic API usage
    - 30% search operations
    - 20% memory operations
    - 10% federation
    """
    # This will be populated by shape class
    pass


# Define user classes with weights
# When running without tags, this distribution is used
user_classes = [
    (RealisticAPIUser, 40),      # 40% realistic API users
    (SearchUser, 30),            # 30% search users
    (MemoryOperationsUser, 20),  # 20% memory operation users
    (FederationUser, 10),        # 10% federation users
]


# =============================================================================
# LOAD SHAPE (OPTIONAL - FOR ADVANCED TESTING)
# =============================================================================

from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern - gradually increases load.

    Useful for finding breaking points.
    """

    step_time = 60  # seconds
    step_load = 100  # users per step
    spawn_rate = 10
    time_limit = 600  # 10 minutes

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = run_time // self.step_time
        user_count = int((current_step + 1) * self.step_load)

        return (user_count, self.spawn_rate)


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern - tests system resilience to traffic spikes.
    """

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 60:
            # Warm up: 100 users
            return (100, 10)
        elif run_time < 120:
            # Spike: 1000 users
            return (1000, 50)
        elif run_time < 180:
            # Cool down: 200 users
            return (200, 10)
        elif run_time < 240:
            # Second spike: 1500 users
            return (1500, 50)
        elif run_time < 300:
            # Final cool down: 100 users
            return (100, 10)
        else:
            return None


# Uncomment to use custom load shape:
# users = StepLoadShape
# users = SpikeLoadShape
