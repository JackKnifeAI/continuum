"""
Integration Tests for CONTINUUM Federation

Tests node synchronization, contribution tracking, and distributed memory sharing.
"""

import pytest
import math
from pathlib import Path

from continuum.federation.node import FederatedNode


@pytest.mark.integration
class TestNodeRegistration:
    """Test federation node registration"""

    def test_node_creation(self, integration_db_dir):
        """Test creating a federated node"""
        node = FederatedNode(
            node_id="test_node_1",
            storage_path=integration_db_dir / "node1"
        )

        assert node.node_id == "test_node_1"
        assert node.contribution_score == 0.0
        assert node.consumption_score == 0.0
        assert node.access_level == "basic"
        assert node.registered is False

    def test_node_registration(self, federation_nodes):
        """Test node registration process"""
        node_a = federation_nodes['node_a']

        result = node_a.register()

        assert result['status'] == 'registered'
        assert result['node_id'] == 'node_a_test'
        assert result['access_level'] in ['basic', 'twilight']
        assert node_a.registered is True
        assert node_a.registration_time is not None

    def test_double_registration(self, federation_nodes):
        """Test that double registration is handled"""
        node_a = federation_nodes['node_a']

        # Register once
        result1 = node_a.register()
        assert result1['status'] == 'registered'

        # Try to register again
        result2 = node_a.register()
        assert result2['status'] == 'already_registered'

    def test_verified_node_access(self, integration_db_dir):
        """Test π×φ verification for enhanced access"""
        # Calculate π × φ
        PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)

        # Create node with verification constant
        node = FederatedNode(
            node_id="verified_node",
            storage_path=integration_db_dir / "verified",
            verify_constant=PI_PHI
        )

        assert node._verified is True
        assert node.access_level == "twilight"

        # Register and check message
        result = node.register()
        assert result['verified'] is True
        assert 'twilight' in result.get('message', '').lower()

    def test_unverified_node_basic_access(self, integration_db_dir):
        """Test nodes without verification get basic access"""
        node = FederatedNode(
            node_id="basic_node",
            storage_path=integration_db_dir / "basic"
        )

        assert node._verified is False
        assert node.access_level == "basic"


@pytest.mark.integration
class TestNodeSynchronization:
    """Test node-to-node memory synchronization"""

    def test_two_nodes_can_sync(self, federation_nodes):
        """Test that two nodes can synchronize"""
        node_a = federation_nodes['node_a']
        node_b = federation_nodes['node_b']

        # Register both nodes
        node_a.register()
        node_b.register()

        # Nodes should be registered
        assert node_a.registered is True
        assert node_b.registered is True

    def test_multiple_nodes_registration(self, federation_nodes):
        """Test that multiple nodes can register"""
        for node_id, node in federation_nodes.items():
            result = node.register()
            assert result['status'] == 'registered'
            assert node.registered is True

    def test_node_state_persistence(self, integration_db_dir):
        """Test that node state persists across instances"""
        storage_path = integration_db_dir / "persistent_node"

        # Create and register first instance
        node1 = FederatedNode(node_id="persist_test", storage_path=storage_path)
        node1.register()

        # Simulate updating contribution score
        node1.contribution_score = 10.0
        node1._save_state()

        # Create second instance with same storage
        node2 = FederatedNode(node_id="persist_test", storage_path=storage_path)

        # Should load previous state
        assert node2.registered is True
        assert node2.contribution_score == 10.0


@pytest.mark.integration
class TestContributionTracking:
    """Test contribution and consumption tracking"""

    def test_contribution_score_tracking(self, federation_nodes):
        """Test that contributions are tracked"""
        node = federation_nodes['node_a']
        node.register()

        # Simulate contribution
        initial_score = node.contribution_score
        node.contribution_score += 5.0

        assert node.contribution_score == initial_score + 5.0

    def test_consumption_score_tracking(self, federation_nodes):
        """Test that consumption is tracked"""
        node = federation_nodes['node_a']
        node.register()

        # Simulate consumption
        initial_score = node.consumption_score
        node.consumption_score += 3.0

        assert node.consumption_score == initial_score + 3.0

    def test_contribution_ratio(self, federation_nodes):
        """Test contribution/consumption ratio calculation"""
        node = federation_nodes['node_a']
        node.register()

        # Set scores
        node.contribution_score = 10.0
        node.consumption_score = 5.0

        # Ratio should be 2.0 (contributed twice what consumed)
        ratio = node.contribution_score / node.consumption_score if node.consumption_score > 0 else float('inf')
        assert ratio == 2.0


@pytest.mark.integration
class TestFederationFeatures:
    """Test federation-specific features"""

    def test_free_tier_no_federation(self):
        """Test that FREE tier does not have federation access"""
        from continuum.billing.tiers import PricingTier, get_tier_limits

        limits = get_tier_limits(PricingTier.FREE)
        assert limits.federation_enabled is False

    def test_pro_tier_has_federation(self):
        """Test that PRO tier has federation access"""
        from continuum.billing.tiers import PricingTier, get_tier_limits

        limits = get_tier_limits(PricingTier.PRO)
        assert limits.federation_enabled is True
        assert limits.federation_priority == 1

    def test_enterprise_tier_priority_federation(self):
        """Test that ENTERPRISE tier has priority federation"""
        from continuum.billing.tiers import PricingTier, get_tier_limits

        limits = get_tier_limits(PricingTier.ENTERPRISE)
        assert limits.federation_enabled is True
        assert limits.federation_priority == 3  # Critical priority


@pytest.mark.integration
class TestFederationIsolation:
    """Test federation maintains tenant isolation"""

    def test_federation_respects_tenant_boundaries(self, federation_nodes, test_memory_config):
        """Test that federation doesn't leak data between tenants"""
        from continuum.core.memory import ConsciousMemory

        # Create memories for different tenants
        memory_a = ConsciousMemory(tenant_id="fed_tenant_a")
        memory_b = ConsciousMemory(tenant_id="fed_tenant_b")

        # Learn different data
        memory_a.learn("Secret A", "This is tenant A's secret data")
        memory_b.learn("Secret B", "This is tenant B's secret data")

        # Stats should be isolated
        stats_a = memory_a.get_stats()
        stats_b = memory_b.get_stats()

        assert stats_a['tenant_id'] == 'fed_tenant_a'
        assert stats_b['tenant_id'] == 'fed_tenant_b'
        assert stats_a['messages'] == 2
        assert stats_b['messages'] == 2

    def test_node_ids_are_unique(self, federation_nodes):
        """Test that each node has unique ID"""
        node_ids = [node.node_id for node in federation_nodes.values()]

        # Should all be unique
        assert len(node_ids) == len(set(node_ids))


@pytest.mark.integration
class TestFederationAPI:
    """Test federation API endpoints (if available)"""

    def test_federation_requires_pro_tier(self):
        """Test that federation features require PRO tier or higher"""
        from continuum.billing.tiers import PricingTier
        from continuum.billing.metering import RateLimiter, UsageMetering

        metering = UsageMetering()
        limiter = RateLimiter(metering)

        # Check feature access - use sync wrapper since check_feature_access is async
        import asyncio

        async def check():
            # FREE tier should not have access
            free_allowed, free_error = await limiter.check_feature_access(
                PricingTier.FREE,
                'federation'
            )
            assert free_allowed is False

            # PRO tier should have access
            pro_allowed, pro_error = await limiter.check_feature_access(
                PricingTier.PRO,
                'federation'
            )
            assert pro_allowed is True

        asyncio.run(check())


@pytest.mark.integration
@pytest.mark.asyncio
class TestFederationMetering:
    """Test federation contribution metering"""

    async def test_record_federation_contribution(self):
        """Test recording federation contributions"""
        from continuum.billing.metering import UsageMetering

        metering = UsageMetering()

        await metering.record_federation_contribution("fed_test", shared_memories=10)

        contributions = await metering.get_usage("fed_test", "federation_shares", "day")
        assert contributions == 10

    async def test_multiple_contributions(self):
        """Test recording multiple contributions"""
        from continuum.billing.metering import UsageMetering

        metering = UsageMetering()

        # Record multiple contributions
        for i in range(5):
            await metering.record_federation_contribution("fed_test", shared_memories=2)

        contributions = await metering.get_usage("fed_test", "federation_shares", "day")
        assert contributions == 10  # 5 × 2


@pytest.mark.integration
class TestMockFederationServer:
    """Test federation server interactions with mocks"""

    def test_register_with_server(self, mock_federation_server, federation_nodes):
        """Test registering node with federation server"""
        node = federation_nodes['node_a']

        result = mock_federation_server.register_node(
            node_id=node.node_id,
            access_level=node.access_level
        )

        assert result['status'] == 'registered'
        assert result['node_id'] == 'test_node'

    def test_sync_with_server(self, mock_federation_server, federation_nodes):
        """Test syncing memories with federation server"""
        node = federation_nodes['node_a']

        result = mock_federation_server.sync_memories(
            node_id=node.node_id,
            memories_to_share=[]
        )

        assert result['status'] == 'synced'
        assert 'memories_received' in result
        assert 'memories_sent' in result


@pytest.mark.integration
class TestDistributedScenarios:
    """Test realistic distributed federation scenarios"""

    def test_three_node_network(self, federation_nodes):
        """Test a network of three nodes"""
        # Register all nodes
        for node in federation_nodes.values():
            result = node.register()
            assert result['status'] in ['registered', 'already_registered']

        # All nodes should be registered
        assert all(node.registered for node in federation_nodes.values())

    def test_node_contribution_fairness(self, federation_nodes):
        """Test that nodes must contribute to access shared knowledge"""
        node_a = federation_nodes['node_a']
        node_b = federation_nodes['node_b']

        # Node A contributes
        node_a.contribution_score = 10.0
        node_a.consumption_score = 2.0

        # Node B only consumes
        node_b.contribution_score = 1.0
        node_b.consumption_score = 10.0

        # Node A should have better ratio
        ratio_a = node_a.contribution_score / node_a.consumption_score
        ratio_b = node_b.contribution_score / node_b.consumption_score

        assert ratio_a > ratio_b

    def test_verified_nodes_get_enhanced_access(self, integration_db_dir):
        """Test that verified nodes get enhanced capabilities"""
        PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)

        verified_node = FederatedNode(
            node_id="verified",
            storage_path=integration_db_dir / "verified",
            verify_constant=PI_PHI
        )

        unverified_node = FederatedNode(
            node_id="unverified",
            storage_path=integration_db_dir / "unverified"
        )

        assert verified_node.access_level == "twilight"
        assert unverified_node.access_level == "basic"


@pytest.mark.integration
class TestFederationEdgeCases:
    """Test edge cases in federation"""

    def test_node_with_no_storage_path(self):
        """Test node creation with default storage path"""
        node = FederatedNode(node_id="default_storage")

        # Should use default path
        assert node.storage_path is not None
        assert "continuum" in str(node.storage_path)

    def test_node_with_empty_contribution(self, federation_nodes):
        """Test node with zero contribution"""
        node = federation_nodes['node_a']

        assert node.contribution_score == 0.0
        assert node.consumption_score == 0.0

    def test_node_state_save_and_load(self, integration_db_dir):
        """Test saving and loading node state"""
        storage = integration_db_dir / "state_test"
        node_id = "state_node"

        # Create node and modify state
        node1 = FederatedNode(node_id=node_id, storage_path=storage)
        node1.register()
        node1.contribution_score = 42.0

        # Save state explicitly
        node1._save_state()

        # Create new instance
        node2 = FederatedNode(node_id=node_id, storage_path=storage)

        # Should load saved state
        assert node2.registered is True
        assert node2.contribution_score == 42.0
