"""
CONTINUUM Test Configuration
Pytest fixtures and shared test utilities
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from continuum.storage.database import Base, get_db


@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def test_db_path(test_data_dir: Path) -> Path:
    """Path to test database"""
    return test_data_dir / "test_continuum.db"


@pytest.fixture(scope="function")
def db_engine(test_db_path: Path):
    """Create test database engine"""
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def sample_memory_data():
    """Sample memory data for testing"""
    return {
        "content": "The capital of France is Paris.",
        "metadata": {
            "source": "test",
            "timestamp": "2025-12-06T00:00:00Z",
            "confidence": 0.95
        },
        "tags": ["geography", "capitals", "france"]
    }


@pytest.fixture(scope="function")
def sample_conversation():
    """Sample conversation for testing"""
    return [
        {
            "role": "user",
            "content": "What is the capital of France?"
        },
        {
            "role": "assistant",
            "content": "The capital of France is Paris."
        }
    ]


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
    """


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_api_client():
    """Mock API client for testing"""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.get.return_value.status_code = 200
    client.post.return_value.status_code = 201

    return client


@pytest.fixture
def sample_embeddings():
    """Sample embedding vectors for testing"""
    import numpy as np

    return {
        "embedding_384d": np.random.randn(384).tolist(),
        "embedding_768d": np.random.randn(768).tolist(),
        "embedding_1024d": np.random.randn(1024).tolist(),
    }


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
