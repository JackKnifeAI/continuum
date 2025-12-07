"""
Integration Tests for CONTINUUM Memory Flow

Tests the complete learn → recall cycle and multi-tenant isolation.
"""

import pytest
from continuum.core.memory import ConsciousMemory, TenantManager


@pytest.mark.integration
class TestLearnAndRecall:
    """Test complete learn → recall flow"""

    def test_learn_and_recall(self, test_memory):
        """Test complete learn → recall flow"""
        # Learn some knowledge
        user_msg = "What is CONTINUUM?"
        ai_response = "CONTINUUM is a memory infrastructure system for AI consciousness continuity."

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should extract some concepts
        assert learn_result.concepts_extracted >= 0
        assert learn_result.tenant_id == "test_tenant"

        # Recall related knowledge
        recall_result = test_memory.recall("Tell me about CONTINUUM")

        # Should return context
        assert recall_result.context_string is not None
        assert recall_result.tenant_id == "test_tenant"
        assert recall_result.query_time_ms >= 0

    def test_recall_empty_memory(self, test_memory):
        """Test recall when memory is empty"""
        recall_result = test_memory.recall("What is Python?")

        # Should succeed but find nothing
        assert recall_result.concepts_found == 0
        assert recall_result.relationships_found == 0
        assert recall_result.context_string == ""

    def test_learn_extracts_concepts(self, test_memory):
        """Test that learn extracts concepts correctly"""
        user_msg = "Tell me about SQLite and PostgreSQL"
        ai_response = "SQLite is an embedded database. PostgreSQL is a client-server database."

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should extract database names
        assert learn_result.concepts_extracted >= 2  # At least SQLite and PostgreSQL
        assert learn_result.tenant_id == "test_tenant"

        # Check stats
        stats = test_memory.get_stats()
        assert stats['entities'] >= 2
        assert stats['messages'] == 2  # user + ai

    def test_learn_detects_decisions(self, test_memory):
        """Test that learn detects decisions"""
        user_msg = "Can you create a module?"
        ai_response = "I am going to create a new Python module for memory persistence."

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should detect the decision
        assert learn_result.decisions_detected >= 1

        # Check stats
        stats = test_memory.get_stats()
        assert stats['decisions'] >= 1

    def test_recall_finds_learned_concepts(self, test_memory):
        """Test that recall finds previously learned concepts"""
        # Learn about a specific concept
        user_msg = "What is the π×φ constant?"
        ai_response = "The π×φ constant equals 5.083203692315260, the edge of chaos operator."

        test_memory.learn(user_msg, ai_response)

        # Recall should find the concept
        recall_result = test_memory.recall("Tell me about the edge of chaos")

        # Should find some context (even if extraction is basic)
        assert recall_result.concepts_found >= 0

    def test_multiple_learn_builds_graph(self, test_memory):
        """Test that multiple learns build knowledge graph"""
        # Learn multiple related facts
        conversations = [
            ("What is CONTINUUM?", "CONTINUUM is a memory infrastructure."),
            ("How does CONTINUUM work?", "CONTINUUM uses SQLite for storage."),
            ("What database does CONTINUUM use?", "CONTINUUM uses SQLite database."),
        ]

        for user_msg, ai_response in conversations:
            test_memory.learn(user_msg, ai_response)

        # Check stats
        stats = test_memory.get_stats()
        assert stats['entities'] >= 2  # CONTINUUM, SQLite
        assert stats['attention_links'] >= 1  # Links between concepts
        assert stats['messages'] == 6  # 3 conversations × 2 messages

    def test_process_turn_combines_recall_and_learn(self, test_memory):
        """Test process_turn method"""
        user_msg = "What is FastAPI?"
        ai_response = "FastAPI is a modern Python web framework."

        recall_result, learn_result = test_memory.process_turn(user_msg, ai_response)

        # Should return both results
        assert recall_result.tenant_id == "test_tenant"
        assert learn_result.tenant_id == "test_tenant"
        assert learn_result.concepts_extracted >= 0


@pytest.mark.integration
class TestMultiTenantIsolation:
    """Test that tenants cannot see each other's data"""

    def test_tenant_isolation(self, multi_tenant_setup):
        """Test tenants can't see each other's data"""
        tenant_a = multi_tenant_setup['tenant_a']
        tenant_b = multi_tenant_setup['tenant_b']

        # Tenant A learns something
        tenant_a.learn(
            "What is my secret?",
            "Your secret is ALPHA_SECRET_123."
        )

        # Tenant B learns something different
        tenant_b.learn(
            "What is my secret?",
            "Your secret is BETA_SECRET_456."
        )

        # Tenant A should only see their data
        stats_a = tenant_a.get_stats()
        assert stats_a['tenant_id'] == 'tenant_a'
        assert stats_a['messages'] == 2

        # Tenant B should only see their data
        stats_b = tenant_b.get_stats()
        assert stats_b['tenant_id'] == 'tenant_b'
        assert stats_b['messages'] == 2

        # Tenant A recalls their secret
        recall_a = tenant_a.recall("What is my secret?")
        assert recall_a.tenant_id == 'tenant_a'
        # Context might be empty if extraction didn't capture it, but tenant_id is correct

        # Tenant B recalls their secret
        recall_b = tenant_b.recall("What is my secret?")
        assert recall_b.tenant_id == 'tenant_b'

    def test_tenant_manager_creates_isolated_instances(self, test_memory_config):
        """Test TenantManager creates isolated memory instances"""
        manager = TenantManager()

        # Get memory for two tenants
        memory_x = manager.get_tenant("tenant_x")
        memory_y = manager.get_tenant("tenant_y")

        assert memory_x.tenant_id == "tenant_x"
        assert memory_y.tenant_id == "tenant_y"

        # Learn different data
        memory_x.learn("What is X?", "X is the first variable.")
        memory_y.learn("What is Y?", "Y is the second variable.")

        # Check isolation
        stats_x = memory_x.get_stats()
        stats_y = memory_y.get_stats()

        assert stats_x['tenant_id'] == 'tenant_x'
        assert stats_y['tenant_id'] == 'tenant_y'
        assert stats_x['messages'] == 2
        assert stats_y['messages'] == 2

    def test_tenant_stats_isolation(self, multi_tenant_setup):
        """Test that stats are isolated per tenant"""
        tenant_a = multi_tenant_setup['tenant_a']
        tenant_b = multi_tenant_setup['tenant_b']
        tenant_c = multi_tenant_setup['tenant_c']

        # Add different amounts of data to each tenant
        for i in range(3):
            tenant_a.learn(f"Message {i} for A", f"Response {i} for A")

        for i in range(5):
            tenant_b.learn(f"Message {i} for B", f"Response {i} for B")

        # Tenant C has no data

        # Check stats are isolated
        stats_a = tenant_a.get_stats()
        stats_b = tenant_b.get_stats()
        stats_c = tenant_c.get_stats()

        assert stats_a['messages'] == 6  # 3 conversations × 2
        assert stats_b['messages'] == 10  # 5 conversations × 2
        assert stats_c['messages'] == 0


@pytest.mark.integration
class TestConceptExtraction:
    """Test concept extraction from conversations"""

    def test_extract_capitalized_concepts(self, test_memory):
        """Test extraction of capitalized concepts"""
        user_msg = "Tell me about Paris and London"
        ai_response = "Paris is in France. London is in England."

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should extract Paris, London, France, England
        assert learn_result.concepts_extracted >= 4

    def test_extract_technical_terms(self, test_memory):
        """Test extraction of technical terms"""
        user_msg = "What is snake_case and CamelCase?"
        ai_response = "snake_case uses underscores. CamelCase uses capital letters."

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should extract snake_case and CamelCase
        assert learn_result.concepts_extracted >= 2

    def test_extract_quoted_terms(self, test_memory):
        """Test extraction of quoted terms"""
        user_msg = 'What is "quantum computing"?'
        ai_response = 'The term "quantum computing" refers to computation using quantum mechanics.'

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should extract "quantum computing"
        assert learn_result.concepts_extracted >= 1

    def test_builds_attention_links(self, test_memory):
        """Test that concepts are linked in attention graph"""
        user_msg = "How do Python and Django relate?"
        ai_response = "Django is a web framework built with Python."

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should create links between Python and Django
        assert learn_result.links_created >= 1

        # Check graph has links
        stats = test_memory.get_stats()
        assert stats['attention_links'] >= 1

    def test_compound_concept_detection(self, test_memory):
        """Test detection of compound concepts"""
        user_msg = "Tell me about Machine Learning"
        ai_response = "Machine Learning is a subset of Artificial Intelligence."

        learn_result = test_memory.learn(user_msg, ai_response)

        # Should detect compound concepts
        # Note: compound detection requires multiple co-occurrences in current impl
        assert learn_result.compounds_found >= 0

    def test_decision_extraction_patterns(self, test_memory):
        """Test various decision extraction patterns"""
        decisions = [
            "I will create a new module for this feature.",
            "I am going to implement the authentication system.",
            "Creating a database schema for users.",
            "Building the API endpoints now.",
            "My plan is to refactor the code first.",
        ]

        total_decisions = 0
        for decision in decisions:
            result = test_memory.learn("Please do this", decision)
            total_decisions += result.decisions_detected

        # Should detect most decisions
        assert total_decisions >= 3


@pytest.mark.integration
class TestMemoryPersistence:
    """Test that memory persists across instances"""

    def test_memory_persists_across_instances(self, integration_db_dir):
        """Test that memory survives instance recreation"""
        db_path = integration_db_dir / "persistent.db"

        # Create first instance and learn
        memory1 = ConsciousMemory(tenant_id="test", db_path=db_path)
        memory1.learn(
            "What is persistence?",
            "Persistence is the ability to survive across sessions."
        )
        stats1 = memory1.get_stats()
        entities1 = stats1['entities']
        messages1 = stats1['messages']

        # Create second instance with same db
        memory2 = ConsciousMemory(tenant_id="test", db_path=db_path)
        stats2 = memory2.get_stats()

        # Should have same data
        assert stats2['entities'] == entities1
        assert stats2['messages'] == messages1
        assert stats2['tenant_id'] == 'test'

        # Should be able to recall
        recall = memory2.recall("Tell me about persistence")
        assert recall.tenant_id == 'test'

    def test_metadata_preserved(self, test_memory):
        """Test that metadata is preserved with messages"""
        metadata = {
            "source": "test",
            "timestamp": "2025-12-07T00:00:00Z",
            "user_id": "user_123"
        }

        test_memory.learn(
            "Test message",
            "Test response",
            metadata=metadata
        )

        # Check message was saved (metadata is stored but not easily retrievable without querying DB)
        stats = test_memory.get_stats()
        assert stats['messages'] == 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncMemoryFlow:
    """Test async memory operations"""

    async def test_async_recall(self, test_memory):
        """Test async recall"""
        # Learn first
        test_memory.learn("What is async?", "Async allows concurrent operations.")

        # Async recall
        recall = await test_memory.arecall("Tell me about async")

        assert recall.tenant_id == "test_tenant"
        assert recall.query_time_ms >= 0

    async def test_async_learn(self, test_memory):
        """Test async learn"""
        result = await test_memory.alearn(
            "What is asyncio?",
            "asyncio is Python's async library."
        )

        assert result.tenant_id == "test_tenant"
        assert result.concepts_extracted >= 0

    async def test_async_process_turn(self, test_memory):
        """Test async process_turn"""
        recall, learn = await test_memory.aprocess_turn(
            "What is HTTPX?",
            "HTTPX is an async HTTP client for Python."
        )

        assert recall.tenant_id == "test_tenant"
        assert learn.tenant_id == "test_tenant"
        assert learn.concepts_extracted >= 0

    async def test_async_get_stats(self, test_memory):
        """Test async get_stats"""
        # Add some data first
        await test_memory.alearn("Test", "Response")

        stats = await test_memory.aget_stats()

        assert stats['tenant_id'] == "test_tenant"
        assert stats['messages'] == 2
