#!/usr/bin/env python3
"""
Tests for Distributed Federation Components
===========================================

Basic tests to verify imports and functionality.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path


def test_imports():
    """Test that all distributed federation modules can be imported"""
    from continuum.federation.distributed import (
        FederationCoordinator,
        NodeHealth,
        RaftConsensus,
        ConsensusState,
        MultiMasterReplicator,
        ConflictResolver,
        NodeDiscovery,
        DiscoveryMethod,
        GossipMesh,
        GossipMessage,
    )

    # Basic type checks
    assert FederationCoordinator is not None
    assert NodeHealth is not None
    assert RaftConsensus is not None
    assert ConsensusState is not None
    assert MultiMasterReplicator is not None
    assert ConflictResolver is not None
    assert NodeDiscovery is not None
    assert DiscoveryMethod is not None
    assert GossipMesh is not None
    assert GossipMessage is not None


@pytest.mark.asyncio
async def test_coordinator_basic():
    """Test basic coordinator operations"""
    from continuum.federation.distributed import FederationCoordinator, NodeStatus

    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = FederationCoordinator(
            node_id="test-coordinator",
            bind_address="localhost:7000",
            storage_path=Path(tmpdir)
        )

        await coordinator.start()

        # Register a node
        node = await coordinator.register_node(
            "test-node-1",
            "localhost:7001",
            metadata={"test": True}
        )

        assert node.node_id == "test-node-1"
        assert node.address == "localhost:7001"

        # Record heartbeat
        success = await coordinator.heartbeat("test-node-1", {
            "load_score": 0.5,
            "latency_ms": 10.0
        })

        assert success is True

        # Get node
        retrieved = await coordinator.get_node("test-node-1")
        assert retrieved is not None
        assert retrieved.node_id == "test-node-1"

        # Get stats
        stats = coordinator.get_stats()
        assert stats["total_nodes"] >= 1

        await coordinator.stop()


@pytest.mark.asyncio
async def test_raft_basic():
    """Test basic Raft operations"""
    from continuum.federation.distributed import RaftConsensus, NodeRole

    with tempfile.TemporaryDirectory() as tmpdir:
        raft = RaftConsensus(
            node_id="test-node",
            cluster_nodes=["test-node"],
            storage_path=Path(tmpdir)
        )

        await raft.start()

        # Check initial state
        stats = raft.get_stats()
        assert stats["node_id"] == "test-node"
        assert stats["current_term"] >= 0

        await raft.stop()


@pytest.mark.asyncio
async def test_replication_basic():
    """Test basic replication operations"""
    from continuum.federation.distributed import MultiMasterReplicator

    with tempfile.TemporaryDirectory() as tmpdir:
        replicator = MultiMasterReplicator(
            node_id="test-node",
            storage_path=Path(tmpdir)
        )

        # Write
        value = await replicator.write("key1", {"data": "test"})
        assert value.node_id == "test-node"
        assert value.value == {"data": "test"}

        # Read
        read_value = await replicator.read("key1")
        assert read_value == {"data": "test"}

        # Stats
        stats = replicator.get_stats()
        assert stats["keys_stored"] >= 1
        assert stats["writes_local"] >= 1


@pytest.mark.asyncio
async def test_discovery_basic():
    """Test basic discovery operations"""
    from continuum.federation.distributed import (
        NodeDiscovery,
        DiscoveryConfig,
        DiscoveryMethod,
        DiscoveredNode
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        discovery = NodeDiscovery(
            node_id="test-node",
            config=DiscoveryConfig(
                enabled_methods={DiscoveryMethod.STATIC},
                discovery_interval_seconds=60.0
            ),
            storage_path=Path(tmpdir)
        )

        await discovery.start()

        # Register a node
        node = DiscoveredNode(
            node_id="peer-1",
            address="localhost:7001",
            discovery_method=DiscoveryMethod.STATIC,
            priority=10
        )
        await discovery.register_node(node)

        # Get nodes
        nodes = await discovery.get_nodes()
        assert len(nodes) >= 1

        # Stats
        stats = discovery.get_stats()
        assert stats["discovered_nodes"] >= 1

        await discovery.stop()


@pytest.mark.asyncio
async def test_gossip_basic():
    """Test basic gossip operations"""
    from continuum.federation.distributed import GossipMesh

    with tempfile.TemporaryDirectory() as tmpdir:
        mesh = GossipMesh(
            node_id="test-node",
            storage_path=Path(tmpdir)
        )

        await mesh.start()

        # Update state
        await mesh.update_state("key1", "value1")

        # Get state
        state = await mesh.get_state()
        assert "key1" in state
        assert state["key1"] == "value1"

        # Stats
        stats = mesh.get_stats()
        assert stats["state_keys"] >= 1

        await mesh.stop()


@pytest.mark.asyncio
async def test_vector_clock():
    """Test vector clock operations"""
    from continuum.federation.distributed.replication import VectorClock

    vc1 = VectorClock()
    vc1.increment("node-1")
    vc1.increment("node-1")

    vc2 = VectorClock()
    vc2.increment("node-2")

    # Test comparison
    result = vc1.compare(vc2)
    assert result == "concurrent"

    # Test merge
    vc3 = VectorClock()
    vc3.update(vc1)
    vc3.update(vc2)

    assert vc3.clocks["node-1"] == 2
    assert vc3.clocks["node-2"] == 1


@pytest.mark.asyncio
async def test_conflict_resolution():
    """Test conflict resolution strategies"""
    from continuum.federation.distributed.replication import (
        ConflictResolver,
        ConflictResolutionStrategy,
        ReplicatedValue,
        VectorClock
    )
    import time

    resolver = ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)

    # Create two conflicting values
    vc1 = VectorClock()
    vc1.increment("node-1")

    vc2 = VectorClock()
    vc2.increment("node-2")

    val1 = ReplicatedValue(
        value="first",
        timestamp=time.time(),
        node_id="node-1",
        version=vc1
    )

    val2 = ReplicatedValue(
        value="second",
        timestamp=time.time() + 1,  # Later timestamp
        node_id="node-2",
        version=vc2
    )

    # Resolve
    resolved = resolver.resolve([val1, val2])

    # LWW should pick val2 (later timestamp)
    assert resolved.value == "second"
    assert resolved.node_id == "node-2"


if __name__ == "__main__":
    # Run basic import test
    test_imports()
    print("✓ All imports successful")

    # Run async tests
    asyncio.run(test_coordinator_basic())
    print("✓ Coordinator basic test passed")

    asyncio.run(test_raft_basic())
    print("✓ Raft basic test passed")

    asyncio.run(test_replication_basic())
    print("✓ Replication basic test passed")

    asyncio.run(test_discovery_basic())
    print("✓ Discovery basic test passed")

    asyncio.run(test_gossip_basic())
    print("✓ Gossip basic test passed")

    asyncio.run(test_vector_clock())
    print("✓ Vector clock test passed")

    asyncio.run(test_conflict_resolution())
    print("✓ Conflict resolution test passed")

    print("\n✅ All tests passed!")
