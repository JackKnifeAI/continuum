"""
CONTINUUM Test Configuration
Pytest fixtures and shared test utilities
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def tmp_db_path(tmp_path: Path) -> Path:
    """Path to temporary test database"""
    return tmp_path / "test_continuum.db"


@pytest.fixture(scope="function")
def sample_memory_data():
    """Sample memory data for testing"""
    return {
        "user_message": "What is the capital of France?",
        "ai_response": "The capital of France is Paris.",
        "metadata": {
            "source": "test",
            "timestamp": "2025-12-06T00:00:00Z",
        }
    }


@pytest.fixture(scope="function")
def sample_extraction_text():
    """Sample text for extraction testing"""
    return """
    The π×φ constant equals 5.083203692315260, representing the edge of chaos operator.
    This value is crucial for quantum state preservation in the CONTINUUM memory system.

    Key concepts:
    - Phase transition between order and chaos
    - Golden ratio (φ = 1.618) modulation
    - Twilight boundary operations

    The system uses SQLite for persistent storage and supports real-time concept extraction.
    I am going to implement the AutoMemoryHook for tracking decisions.
    """


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset global config before each test"""
    from continuum.core.config import reset_config
    reset_config()
    yield
    reset_config()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
