"""
CONTINUUM Memory Core Unit Tests
Tests for memory storage and retrieval
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from continuum.core.memory import Memory, MemoryStore
from continuum.storage.models import MemoryRecord


class TestMemory:
    """Test Memory class"""

    def test_memory_creation(self, sample_memory_data):
        """Test creating a memory object"""
        memory = Memory(**sample_memory_data)

        assert memory.content == sample_memory_data["content"]
        assert memory.metadata == sample_memory_data["metadata"]
        assert memory.tags == sample_memory_data["tags"]

    def test_memory_to_dict(self, sample_memory_data):
        """Test memory serialization"""
        memory = Memory(**sample_memory_data)
        memory_dict = memory.to_dict()

        assert memory_dict["content"] == sample_memory_data["content"]
        assert memory_dict["metadata"] == sample_memory_data["metadata"]
        assert memory_dict["tags"] == sample_memory_data["tags"]

    def test_memory_from_dict(self, sample_memory_data):
        """Test memory deserialization"""
        memory = Memory.from_dict(sample_memory_data)

        assert memory.content == sample_memory_data["content"]
        assert memory.metadata == sample_memory_data["metadata"]
        assert memory.tags == sample_memory_data["tags"]

    def test_memory_with_embedding(self, sample_memory_data, sample_embeddings):
        """Test memory with embedding vector"""
        memory = Memory(
            **sample_memory_data,
            embedding=sample_embeddings["embedding_384d"]
        )

        assert memory.embedding is not None
        assert len(memory.embedding) == 384


class TestMemoryStore:
    """Test MemoryStore class"""

    def test_store_initialization(self, db_session):
        """Test memory store initialization"""
        store = MemoryStore(db_session)
        assert store is not None
        assert store.session == db_session

    def test_add_memory(self, db_session, sample_memory_data):
        """Test adding a memory to the store"""
        store = MemoryStore(db_session)
        memory = Memory(**sample_memory_data)

        stored_memory = store.add(memory)

        assert stored_memory.id is not None
        assert stored_memory.content == memory.content

    def test_retrieve_memory(self, db_session, sample_memory_data):
        """Test retrieving a memory by ID"""
        store = MemoryStore(db_session)
        memory = Memory(**sample_memory_data)

        stored_memory = store.add(memory)
        retrieved_memory = store.get(stored_memory.id)

        assert retrieved_memory is not None
        assert retrieved_memory.content == memory.content

    def test_search_memories(self, db_session, sample_memory_data):
        """Test searching memories by content"""
        store = MemoryStore(db_session)

        # Add multiple memories
        memory1 = Memory(content="Paris is the capital of France", tags=["geography"])
        memory2 = Memory(content="Berlin is the capital of Germany", tags=["geography"])
        memory3 = Memory(content="Python is a programming language", tags=["programming"])

        store.add(memory1)
        store.add(memory2)
        store.add(memory3)

        # Search for geography-related memories
        results = store.search(query="capital", limit=10)

        assert len(results) >= 2
        assert any("Paris" in r.content for r in results)
        assert any("Berlin" in r.content for r in results)

    def test_filter_by_tags(self, db_session):
        """Test filtering memories by tags"""
        store = MemoryStore(db_session)

        # Add memories with different tags
        memory1 = Memory(content="Test 1", tags=["tag1", "tag2"])
        memory2 = Memory(content="Test 2", tags=["tag2", "tag3"])
        memory3 = Memory(content="Test 3", tags=["tag3", "tag4"])

        store.add(memory1)
        store.add(memory2)
        store.add(memory3)

        # Filter by tag
        results = store.filter_by_tags(["tag2"])

        assert len(results) >= 2
        assert all("tag2" in r.tags for r in results)

    def test_delete_memory(self, db_session, sample_memory_data):
        """Test deleting a memory"""
        store = MemoryStore(db_session)
        memory = Memory(**sample_memory_data)

        stored_memory = store.add(memory)
        memory_id = stored_memory.id

        # Delete memory
        store.delete(memory_id)

        # Verify deletion
        retrieved = store.get(memory_id)
        assert retrieved is None

    def test_update_memory(self, db_session, sample_memory_data):
        """Test updating a memory"""
        store = MemoryStore(db_session)
        memory = Memory(**sample_memory_data)

        stored_memory = store.add(memory)

        # Update content
        stored_memory.content = "Updated content"
        updated_memory = store.update(stored_memory)

        assert updated_memory.content == "Updated content"

        # Verify persistence
        retrieved = store.get(stored_memory.id)
        assert retrieved.content == "Updated content"

    def test_list_all_memories(self, db_session):
        """Test listing all memories"""
        store = MemoryStore(db_session)

        # Add multiple memories
        for i in range(5):
            memory = Memory(content=f"Test memory {i}", tags=[f"tag{i}"])
            store.add(memory)

        # List all
        all_memories = store.list_all(limit=10)

        assert len(all_memories) == 5

    def test_count_memories(self, db_session):
        """Test counting memories"""
        store = MemoryStore(db_session)

        # Add memories
        for i in range(3):
            memory = Memory(content=f"Test {i}", tags=["test"])
            store.add(memory)

        count = store.count()
        assert count == 3


class TestMemoryTimestamps:
    """Test memory timestamp handling"""

    def test_created_timestamp(self, db_session, sample_memory_data):
        """Test that created timestamp is set automatically"""
        store = MemoryStore(db_session)
        memory = Memory(**sample_memory_data)

        stored_memory = store.add(memory)

        assert stored_memory.created_at is not None
        assert isinstance(stored_memory.created_at, datetime)

    def test_updated_timestamp(self, db_session, sample_memory_data):
        """Test that updated timestamp is updated on modification"""
        store = MemoryStore(db_session)
        memory = Memory(**sample_memory_data)

        stored_memory = store.add(memory)
        original_updated = stored_memory.updated_at

        # Update memory
        stored_memory.content = "New content"
        updated_memory = store.update(stored_memory)

        assert updated_memory.updated_at > original_updated
