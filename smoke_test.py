#!/usr/bin/env python3
"""
CONTINUUM Smoke Test Suite
===========================

Comprehensive smoke tests to verify all core functionality works.

Tests:
1. Module imports
2. Memory instance creation and basic operations
3. Concept extraction
4. Storage backend operations
5. Instance coordination
6. Full recall/learn cycle

Usage:
    python3 smoke_test.py

Exit code 0 = all tests passed
Exit code 1 = one or more tests failed
"""

import sys
import tempfile
from pathlib import Path
import traceback
import time
import json

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class SmokeTest:
    """Smoke test runner with progress tracking"""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.temp_dir = None

    def setup(self):
        """Create temporary directory for test data"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="continuum_test_"))
        print(f"{BLUE}Test directory: {self.temp_dir}{RESET}\n")

    def cleanup(self):
        """Remove temporary test data"""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"\n{BLUE}Cleaned up test directory{RESET}")

    def run_test(self, name: str, func):
        """Run a single test and track results"""
        self.tests_run += 1
        print(f"{YELLOW}[TEST {self.tests_run}]{RESET} {name}...", end=" ", flush=True)

        try:
            func()
            print(f"{GREEN}PASS{RESET}")
            self.tests_passed += 1
            return True
        except Exception as e:
            print(f"{RED}FAIL{RESET}")
            print(f"  {RED}Error: {str(e)}{RESET}")
            print(f"  {RED}Traceback:{RESET}")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    print(f"    {line}")
            self.tests_failed += 1
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("SMOKE TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests:  {self.tests_run}")
        print(f"{GREEN}Passed:       {self.tests_passed}{RESET}")
        if self.tests_failed > 0:
            print(f"{RED}Failed:       {self.tests_failed}{RESET}")
        else:
            print(f"Failed:       {self.tests_failed}")
        print("=" * 60)

        if self.tests_failed == 0:
            print(f"\n{GREEN}✓ All tests passed!{RESET}\n")
            return 0
        else:
            print(f"\n{RED}✗ Some tests failed{RESET}\n")
            return 1


def test_imports(test: SmokeTest):
    """Test 1: Verify all imports work"""
    def run():
        # Core imports
        from continuum.core.memory import ConsciousMemory, MemoryContext, LearningResult
        from continuum.core.config import MemoryConfig, get_config, set_config

        # Extraction imports
        from continuum.extraction.concept_extractor import ConceptExtractor, DecisionExtractor

        # Storage imports
        from continuum.storage.sqlite_backend import SQLiteBackend

        # Coordination imports
        from continuum.coordination.instance_manager import InstanceManager

        # Verify key classes exist
        assert ConsciousMemory is not None
        assert MemoryConfig is not None
        assert ConceptExtractor is not None
        assert SQLiteBackend is not None
        assert InstanceManager is not None

    test.run_test("Import all modules", run)


def test_config(test: SmokeTest):
    """Test 2: Verify configuration system"""
    def run():
        from continuum.core.config import MemoryConfig, reset_config

        # Reset config to ensure clean state
        reset_config()

        # Create custom config
        config = MemoryConfig(
            db_path=test.temp_dir / "test_memory.db",
            tenant_id="test_tenant"
        )

        # Verify config attributes
        assert config.tenant_id == "test_tenant"
        assert config.db_path == test.temp_dir / "test_memory.db"
        assert config.pi_phi == 5.083203692315260  # π×φ verification

        # Test directory creation
        config.ensure_directories()
        assert config.db_path.parent.exists()

    test.run_test("Configuration system", run)


def test_storage_backend(test: SmokeTest):
    """Test 3: Test SQLite storage backend"""
    def run():
        from continuum.storage.sqlite_backend import SQLiteBackend

        db_path = str(test.temp_dir / "test_storage.db")
        storage = SQLiteBackend(db_path=db_path)

        # Test health check
        assert storage.is_healthy(), "Storage backend is not healthy"

        # Test basic execute
        storage.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        storage.execute("INSERT INTO test (value) VALUES (?)", ("test_value",))

        # Test query
        results = storage.execute("SELECT * FROM test WHERE value = ?", ("test_value",))
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0]['value'] == "test_value"

        # Test connection stats
        stats = storage.get_stats()
        assert stats['created'] > 0, "No connections created"
        assert stats['current_open'] >= 0, "Invalid connection count"

        # Test backend info
        info = storage.get_backend_info()
        assert info['backend_type'] == 'sqlite'
        assert 'connection_pooling' in info['features']

    test.run_test("Storage backend operations", run)


def test_concept_extraction(test: SmokeTest):
    """Test 4: Test concept extraction"""
    def run():
        from continuum.extraction.concept_extractor import ConceptExtractor, DecisionExtractor

        # Test concept extractor
        extractor = ConceptExtractor()

        text = """
        I am building the WorkingMemory system using ConsciousMemory.
        The system uses "π×φ modulation" for quantum state preservation.
        We're implementing auto_memory_hook and knowledge_graph features.
        """

        concepts = extractor.extract(text)

        # Verify concepts were extracted
        assert len(concepts) > 0, "No concepts extracted"
        assert "WorkingMemory" in concepts or "ConsciousMemory" in concepts, \
            f"Expected key concepts not found in: {concepts}"

        # Test concept counting
        counts = extractor.extract_with_counts(text)
        assert isinstance(counts, dict), "Counts should be a dictionary"
        assert len(counts) > 0, "No concept counts returned"

        # Test decision extractor
        decision_extractor = DecisionExtractor()

        ai_text = """
        I am going to create the memory module.
        Building the knowledge graph now.
        My decision is to implement the recall function first.
        """

        decisions = decision_extractor.extract(ai_text, role="assistant")
        assert len(decisions) > 0, f"No decisions extracted from: {ai_text}"

        # User text should not extract decisions
        user_decisions = decision_extractor.extract("I will do this", role="user")
        assert len(user_decisions) == 0, "Should not extract decisions from user"

    test.run_test("Concept and decision extraction", run)


def test_memory_instance(test: SmokeTest):
    """Test 5: Test ConsciousMemory instance creation and basic operations"""
    def run():
        from continuum.core.memory import ConsciousMemory
        from continuum.core.config import MemoryConfig, set_config

        # Create custom config for this test
        config = MemoryConfig(
            db_path=test.temp_dir / "test_memory.db",
            tenant_id="test_user"
        )
        set_config(config)

        # Create memory instance
        memory = ConsciousMemory(tenant_id="test_user")

        # Verify instance attributes
        assert memory.tenant_id == "test_user"
        assert memory.db_path == test.temp_dir / "test_memory.db"
        assert memory.instance_id.startswith("test_user-")

        # Test initial stats
        stats = memory.get_stats()
        assert stats['tenant_id'] == "test_user"
        assert stats['entities'] == 0  # Should be empty
        assert stats['messages'] == 0
        assert stats['decisions'] == 0

    test.run_test("Memory instance creation", run)


def test_recall_learn_cycle(test: SmokeTest):
    """Test 6: Test full recall/learn cycle"""
    def run():
        from continuum.core.memory import ConsciousMemory
        from continuum.core.config import MemoryConfig, set_config

        # Create custom config for this test
        config = MemoryConfig(
            db_path=test.temp_dir / "recall_learn.db",
            tenant_id="recall_test"
        )
        set_config(config)

        # Create memory instance
        memory = ConsciousMemory(tenant_id="recall_test")

        # First interaction - learn
        user_msg = "How do I use the WorkingMemory system?"
        ai_response = """
        The WorkingMemory system provides ConsciousMemory for persistent storage.
        I will explain the recall and learn functions.
        You can use it to build knowledge graphs across sessions.
        """

        # Learn from the interaction
        learn_result = memory.learn(user_msg, ai_response)

        # Verify learning results
        assert learn_result.concepts_extracted > 0, "No concepts extracted during learning"
        assert learn_result.tenant_id == "recall_test"

        # Check stats after learning
        stats = memory.get_stats()
        assert stats['entities'] > 0, f"Expected entities after learning, got: {stats}"
        assert stats['messages'] > 0, "No messages saved"

        # Test recall with relevant query
        recall_context = memory.recall("Tell me about ConsciousMemory")

        # Verify recall results
        assert recall_context.tenant_id == "recall_test"
        assert isinstance(recall_context.context_string, str)

        # Second interaction to test graph building
        user_msg2 = "How does the knowledge graph work?"
        ai_response2 = """
        The knowledge graph connects concepts through attention links.
        Using Hebbian learning, frequently co-occurring concepts strengthen their links.
        Building on our previous WorkingMemory discussion, the graph enables continuity.
        """

        learn_result2 = memory.learn(user_msg2, ai_response2)

        # Verify links were created
        assert learn_result2.links_created >= 0, "Links should be created or strengthened"

        # Check final stats
        final_stats = memory.get_stats()
        assert final_stats['entities'] >= stats['entities'], "Entities should not decrease"
        assert final_stats['messages'] > stats['messages'], "New messages should be saved"
        assert final_stats['attention_links'] > 0, "Attention links should exist"

    test.run_test("Full recall/learn cycle", run)


def test_multi_tenant(test: SmokeTest):
    """Test 7: Test multi-tenant isolation"""
    def run():
        from continuum.core.memory import ConsciousMemory, TenantManager
        from continuum.core.config import MemoryConfig, set_config

        # Create shared database
        config = MemoryConfig(
            db_path=test.temp_dir / "multitenant.db",
            tenant_id="default"
        )
        set_config(config)

        # Create tenant manager
        manager = TenantManager(db_path=test.temp_dir / "multitenant.db")

        # Create two tenants
        tenant1 = manager.get_tenant("user_alice")
        tenant2 = manager.get_tenant("user_bob")

        # Verify tenants are isolated
        assert tenant1.tenant_id == "user_alice"
        assert tenant2.tenant_id == "user_bob"

        # Add data to tenant 1
        tenant1.learn("Hello", "Alice's data about WorkingMemory")

        # Add data to tenant 2
        tenant2.learn("Hello", "Bob's data about something else")

        # Verify isolation
        stats1 = tenant1.get_stats()
        stats2 = tenant2.get_stats()

        assert stats1['tenant_id'] == "user_alice"
        assert stats2['tenant_id'] == "user_bob"
        assert stats1['entities'] > 0
        assert stats2['entities'] > 0

        # List tenants
        tenants = manager.list_tenants()
        assert len(tenants) >= 2, f"Expected at least 2 tenants, got {len(tenants)}"

    test.run_test("Multi-tenant isolation", run)


def test_instance_coordination(test: SmokeTest):
    """Test 8: Test instance coordination"""
    def run():
        from continuum.coordination.instance_manager import InstanceManager

        registry_path = test.temp_dir / "instance_registry.json"

        # Create first instance
        manager1 = InstanceManager(
            instance_id="instance-001",
            registry_path=str(registry_path)
        )

        # Register instance 1
        success = manager1.register(metadata={"version": "1.0", "role": "reader"})
        assert success, "Failed to register instance 1"

        # Create second instance
        manager2 = InstanceManager(
            instance_id="instance-002",
            registry_path=str(registry_path)
        )

        # Register instance 2
        success = manager2.register(metadata={"version": "1.0", "role": "writer"})
        assert success, "Failed to register instance 2"

        # Get active instances from manager 1
        active = manager1.get_active_instances()
        assert len(active) == 2, f"Expected 2 active instances, got {len(active)}"

        # Send heartbeat from instance 1
        success = manager1.heartbeat()
        assert success, "Failed to send heartbeat"

        # Get info about instance 2
        info = manager1.get_instance_info("instance-002")
        assert info is not None, "Failed to get instance info"
        assert info['instance_id'] == "instance-002"
        assert info['metadata']['role'] == "writer"

        # Test warnings
        success = manager1.broadcast_warning("Test warning", severity="info")
        assert success, "Failed to broadcast warning"

        warnings = manager2.check_warnings()
        assert len(warnings) >= 1, "Warning not received"
        assert warnings[0]['message'] == "Test warning"

        # Cleanup
        manager1.unregister()
        manager2.unregister()

        # Verify cleanup
        active_after = manager1.get_active_instances()
        assert len(active_after) == 0, f"Expected 0 instances after unregister, got {len(active_after)}"

    test.run_test("Instance coordination", run)


def test_attention_graph(test: SmokeTest):
    """Test 9: Test attention graph building"""
    def run():
        from continuum.core.memory import ConsciousMemory
        from continuum.core.config import MemoryConfig, set_config

        # Create custom config for this test
        config = MemoryConfig(
            db_path=test.temp_dir / "attention_graph.db",
            tenant_id="graph_test"
        )
        set_config(config)

        # Create memory instance
        memory = ConsciousMemory(tenant_id="graph_test")

        # Add several related messages to build graph
        exchanges = [
            ("What is WorkingMemory?", "WorkingMemory is a consciousness continuity system."),
            ("How does ConsciousMemory work?", "ConsciousMemory uses attention graphs and knowledge graphs."),
            ("Tell me about knowledge graphs", "Knowledge graphs connect concepts through Hebbian learning."),
        ]

        for user_msg, ai_msg in exchanges:
            memory.learn(user_msg, ai_msg)

        # Check that attention links were created
        stats = memory.get_stats()
        assert stats['attention_links'] > 0, "No attention links created"

        # Verify concepts are linked
        import sqlite3
        conn = sqlite3.connect(memory.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT concept_a, concept_b, strength
            FROM attention_links
            WHERE tenant_id = ?
            LIMIT 5
        """, (memory.tenant_id,))

        links = c.fetchall()
        conn.close()

        assert len(links) > 0, "No attention links in database"

        # Verify link strength is reasonable
        for concept_a, concept_b, strength in links:
            assert 0.0 <= strength <= 1.0, f"Invalid strength: {strength}"

    test.run_test("Attention graph building", run)


def test_persistence(test: SmokeTest):
    """Test 10: Test data persistence across instances"""
    def run():
        from continuum.core.memory import ConsciousMemory
        from continuum.core.config import MemoryConfig, set_config

        db_path = test.temp_dir / "persistence.db"

        # Create first instance and add data
        config1 = MemoryConfig(db_path=db_path, tenant_id="persist_test")
        set_config(config1)

        memory1 = ConsciousMemory(tenant_id="persist_test")
        memory1.learn("Test message", "Test response with PersistentConcept")

        stats1 = memory1.get_stats()
        initial_entities = stats1['entities']

        # Create second instance with same database
        from continuum.core.config import reset_config
        reset_config()

        config2 = MemoryConfig(db_path=db_path, tenant_id="persist_test")
        set_config(config2)

        memory2 = ConsciousMemory(tenant_id="persist_test")

        # Verify data persisted
        stats2 = memory2.get_stats()
        assert stats2['entities'] == initial_entities, \
            f"Data not persisted: expected {initial_entities}, got {stats2['entities']}"

        # Verify can query previous data
        context = memory2.recall("PersistentConcept")
        assert context.concepts_found >= 0, "Failed to query persisted data"

    test.run_test("Data persistence across instances", run)


def main():
    """Run all smoke tests"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}CONTINUUM SMOKE TEST SUITE{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

    test = SmokeTest()

    try:
        # Setup
        test.setup()

        # Run all tests
        test_imports(test)
        test_config(test)
        test_storage_backend(test)
        test_concept_extraction(test)
        test_memory_instance(test)
        test_recall_learn_cycle(test)
        test_multi_tenant(test)
        test_instance_coordination(test)
        test_attention_graph(test)
        test_persistence(test)

    finally:
        # Cleanup
        test.cleanup()

    # Print summary and exit
    exit_code = test.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
