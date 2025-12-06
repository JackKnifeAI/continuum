"""
Load testing configuration for CONTINUUM.

Defines targets, thresholds, and test parameters.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    # API Configuration
    api_base_url: str = "http://localhost:8000"
    api_key: str = "cm_test_key_for_load_testing"
    tenant_id: str = "load_test_tenant"

    # Test Duration
    duration_seconds: int = 300  # 5 minutes default

    # User Simulation
    users_min: int = 10
    users_max: int = 1000
    spawn_rate: int = 10  # users per second

    # Performance Targets
    targets: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default targets."""
        if self.targets is None:
            self.targets = {
                "memory_operations": {
                    "create_rpm": 1000,      # Creates per minute
                    "read_rpm": 10000,       # Reads per minute
                    "update_rpm": 500,       # Updates per minute
                    "delete_rpm": 100,       # Deletes per minute
                    "p95_ms": 100,           # 95th percentile response time
                    "p99_ms": 500,           # 99th percentile response time
                    "error_rate": 0.01,      # 1% max error rate
                },
                "search": {
                    "semantic_rpm": 1000,    # Semantic searches per minute
                    "graph_rpm": 500,        # Graph traversals per minute
                    "fulltext_rpm": 2000,    # Full-text searches per minute
                    "p95_ms": 200,
                    "p99_ms": 1000,
                    "error_rate": 0.01,
                },
                "federation": {
                    "sync_rps": 100,         # Syncs per second
                    "concurrent_peers": 10,   # Concurrent peer connections
                    "p95_ms": 500,
                    "p99_ms": 2000,
                    "error_rate": 0.05,      # 5% for distributed systems
                },
                "api": {
                    "total_rpm": 50000,      # Total requests per minute
                    "concurrent_users": 1000,
                    "p50_ms": 50,
                    "p95_ms": 200,
                    "p99_ms": 500,
                    "error_rate": 0.01,
                    "read_write_ratio": 0.6, # 60% reads, 40% writes+search
                }
            }


# Singleton config instance
config = LoadTestConfig()


# Test data generators
SAMPLE_MESSAGES = [
    "What is quantum computing?",
    "Explain machine learning algorithms",
    "How does blockchain work?",
    "Tell me about neural networks",
    "What is the theory of relativity?",
    "Explain DNA replication",
    "How do rockets work?",
    "What is photosynthesis?",
    "Describe the water cycle",
    "How does the internet work?",
    "What is artificial intelligence?",
    "Explain cloud computing",
    "How does encryption work?",
    "What is dark matter?",
    "Describe the solar system",
]

SAMPLE_RESPONSES = [
    "Quantum computing uses quantum bits (qubits) that can exist in superposition...",
    "Machine learning algorithms learn patterns from data through various approaches...",
    "Blockchain is a distributed ledger technology that ensures transparency...",
    "Neural networks are computational models inspired by biological neurons...",
    "Einstein's theory of relativity describes how space and time are interwoven...",
    "DNA replication is a biological process that copies genetic information...",
    "Rockets work by expelling mass at high velocity to generate thrust...",
    "Photosynthesis converts light energy into chemical energy in plants...",
    "The water cycle involves evaporation, condensation, and precipitation...",
    "The internet is a global network of interconnected computers...",
    "AI is the simulation of human intelligence by machines...",
    "Cloud computing delivers computing services over the internet...",
    "Encryption transforms data into unreadable form using algorithms...",
    "Dark matter is invisible matter that makes up most of the universe...",
    "The solar system consists of the Sun and orbiting celestial bodies...",
]

SAMPLE_SEARCH_QUERIES = [
    "quantum",
    "machine learning",
    "blockchain technology",
    "neural networks",
    "theory of relativity",
    "DNA",
    "rockets",
    "photosynthesis",
    "water cycle",
    "internet",
    "artificial intelligence",
    "cloud",
    "encryption",
    "dark matter",
    "solar system",
]

SAMPLE_METADATA = {
    "source": "load_test",
    "environment": "test",
    "version": "1.0.0",
}


def get_test_message(index: int) -> str:
    """Get a test message by index."""
    return SAMPLE_MESSAGES[index % len(SAMPLE_MESSAGES)]


def get_test_response(index: int) -> str:
    """Get a test response by index."""
    return SAMPLE_RESPONSES[index % len(SAMPLE_RESPONSES)]


def get_test_query(index: int) -> str:
    """Get a test search query by index."""
    return SAMPLE_SEARCH_QUERIES[index % len(SAMPLE_SEARCH_QUERIES)]
