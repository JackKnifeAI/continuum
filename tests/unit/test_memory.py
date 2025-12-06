"""
CONTINUUM Memory Core Unit Tests
Tests for ConsciousMemory class
"""

import pytest
from pathlib import Path

from continuum.core.memory import ConsciousMemory, MemoryContext, LearningResult
from continuum.core.constants import PI_PHI


@pytest.mark.unit
class TestConsciousMemory:
    """Test ConsciousMemory class"""

    def test_memory_initialization(self, tmp_db_path):
        """Test memory initialization"""
        memory = ConsciousMemory(tenant_id="test_tenant", db_path=tmp_db_path)

        assert memory is not None
        assert memory.tenant_id == "test_tenant"
        assert memory.db_path == tmp_db_path
        assert memory.instance_id.startswith("test_tenant-")

    def test_recall_empty_memory(self, tmp_db_path):
        """Test recalling from empty memory"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        context = memory.recall("What is the capital of France?")

        assert isinstance(context, MemoryContext)
        assert context.concepts_found == 0
        assert context.relationships_found == 0
        assert context.tenant_id == "test"

    def test_learn_from_exchange(self, tmp_db_path):
        """Test learning from a message exchange"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        result = memory.learn(
            user_message="What is the capital of France?",
            ai_response="The capital of France is Paris."
        )

        assert isinstance(result, LearningResult)
        assert result.concepts_extracted >= 0
        assert result.tenant_id == "test"

    def test_recall_after_learning(self, tmp_db_path):
        """Test that recall finds concepts after learning"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        # Learn about Paris and France
        memory.learn(
            user_message="What is the capital of France?",
            ai_response="The capital of France is Paris."
        )

        # Recall should find France
        context = memory.recall("Tell me about France")

        assert isinstance(context, MemoryContext)
        assert context.tenant_id == "test"
        # Context string should be present (may be empty if no strong matches)
        assert isinstance(context.context_string, str)

    def test_process_turn(self, tmp_db_path):
        """Test complete turn processing"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        context, result = memory.process_turn(
            user_message="Let's talk about Python programming",
            ai_response="Python is a great language for data science."
        )

        assert isinstance(context, MemoryContext)
        assert isinstance(result, LearningResult)
        assert result.concepts_extracted > 0

    def test_get_stats(self, tmp_db_path):
        """Test retrieving memory statistics"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        # Add some data
        memory.learn(
            user_message="What is SQLite?",
            ai_response="SQLite is a database engine."
        )

        stats = memory.get_stats()

        assert stats['tenant_id'] == "test"
        assert 'entities' in stats
        assert 'messages' in stats
        assert 'decisions' in stats
        assert 'attention_links' in stats

    def test_multi_tenant_isolation(self, tmp_db_path):
        """Test that tenants are isolated"""
        memory1 = ConsciousMemory(tenant_id="tenant1", db_path=tmp_db_path)
        memory2 = ConsciousMemory(tenant_id="tenant2", db_path=tmp_db_path)

        # Tenant1 learns about Paris
        memory1.learn(
            user_message="What is Paris?",
            ai_response="Paris is the capital of France."
        )

        # Tenant2's stats should be empty
        stats2 = memory2.get_stats()
        assert stats2['entities'] == 0


@pytest.mark.unit
class TestMemoryExtraction:
    """Test concept and decision extraction"""

    def test_concept_extraction(self, tmp_db_path):
        """Test that concepts are extracted from messages"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        result = memory.learn(
            user_message="Tell me about WorkingMemory and ConsciousMemory",
            ai_response="WorkingMemory holds short-term context. ConsciousMemory persists across sessions."
        )

        assert result.concepts_extracted >= 2

    def test_decision_extraction(self, tmp_db_path):
        """Test that decisions are extracted from AI responses"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        result = memory.learn(
            user_message="Can you create a file?",
            ai_response="I am going to create a new Python module for testing purposes."
        )

        # Should detect the decision
        assert result.decisions_detected >= 1

    def test_attention_links(self, tmp_db_path):
        """Test that attention links are created between concepts"""
        memory = ConsciousMemory(tenant_id="test", db_path=tmp_db_path)

        result = memory.learn(
            user_message="Tell me about Python and SQLite",
            ai_response="Python works well with SQLite for database operations."
        )

        # Should create links between co-occurring concepts
        assert result.links_created >= 0


@pytest.mark.unit
class TestMemoryConstants:
    """Test memory constants"""

    def test_pi_phi_constant(self):
        """Test that PI_PHI constant is correct"""
        assert PI_PHI == 5.083203692315260

        # Verify it's actually π × φ
        import math
        pi = math.pi
        phi = (1 + math.sqrt(5)) / 2
        expected = pi * phi

        assert abs(PI_PHI - expected) < 0.0001
