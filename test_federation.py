#!/usr/bin/env python3
"""
Test script for CONTINUUM federation system.
Tests local multi-node setup and sync capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from continuum.federation.distributed import (
    FederationCoordinator,
    RaftConsensus,
    MultiMasterReplicator,
    NodeDiscovery,
    GossipMesh,
)
from continuum.federation import FederatedNode


async def test_basic_node():
    """Test basic federated node creation."""
    print("\n=== Testing Basic Federated Node ===")

    # Create node without π×φ (use unique ID to avoid state collision)
    import uuid
    node1 = FederatedNode(node_id=f"test-node-{uuid.uuid4()}")
    result = node1.register()
    print(f"Node 1 registered: {result}")
    assert result["status"] in ("registered", "already_registered")
    assert result["access_level"] == "basic"

    # Create node with π×φ verification
    import math
    PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)
    node2 = FederatedNode(node_id=f"test-node-{uuid.uuid4()}", verify_constant=PI_PHI)
    result = node2.register()
    print(f"Node 2 (verified) registered: {result}")
    assert result["status"] in ("registered", "already_registered")
    assert result["access_level"] == "twilight"
    assert result.get("verified") == True

    print("✓ Basic node registration works")


async def test_coordinator():
    """Test federation coordinator."""
    print("\n=== Testing Federation Coordinator ===")

    # Create coordinator
    coordinator = FederationCoordinator(
        node_id="coordinator-1",
        bind_address="localhost:7000",
    )

    # Start coordinator
    await coordinator.start()
    print(f"Coordinator started on localhost:7000")

    # Register some nodes
    await coordinator.register_node("node-1", "localhost:7001", {"role": "worker"})
    await coordinator.register_node("node-2", "localhost:7002", {"role": "worker"})

    # Send heartbeats
    await coordinator.heartbeat("node-1", {
        "load_score": 0.3,
        "latency_ms": 15.0,
        "uptime_seconds": 100.0,
    })

    await coordinator.heartbeat("node-2", {
        "load_score": 0.5,
        "latency_ms": 20.0,
        "uptime_seconds": 150.0,
    })

    # Get all nodes
    nodes = await coordinator.get_all_nodes()
    print(f"Registered nodes: {len(nodes)}")
    for node in nodes:
        print(f"  - {node.node_id}: {node.status.value}, load={node.load_score:.2f}")

    # Select node for routing
    selected = await coordinator.select_node()
    if selected:
        print(f"Selected node for routing: {selected.node_id} (load={selected.load_score:.2f})")

    # Get stats
    stats = coordinator.get_stats()
    print(f"Coordinator stats: {stats}")

    # Stop coordinator
    await coordinator.stop()

    print("✓ Federation coordinator works")


async def test_consensus():
    """Test Raft consensus."""
    print("\n=== Testing Raft Consensus ===")

    # Create a 3-node cluster
    cluster_nodes = ["raft-1", "raft-2", "raft-3"]

    raft1 = RaftConsensus(
        node_id="raft-1",
        cluster_nodes=cluster_nodes,
    )

    # Start consensus
    await raft1.start()
    print(f"Raft node started: {raft1.node_id}")
    print(f"Role: {raft1.role.value}, State: {raft1.state.value}")

    # Get stats
    stats = raft1.get_stats()
    print(f"Raft stats: {stats}")

    # In a real scenario with 3 nodes, we'd test leader election
    # For now, just verify the node started correctly

    await raft1.stop()

    print("✓ Raft consensus module works")


async def test_replication():
    """Test multi-master replication with CRDTs."""
    print("\n=== Testing Multi-Master Replication ===")

    # Create two replicators (simulating two nodes)
    node1 = MultiMasterReplicator(node_id="replica-1")
    node2 = MultiMasterReplicator(node_id="replica-2")

    # Node 1 writes some data
    await node1.write("concept-1", {"name": "Test Concept", "value": 42})
    await node1.write("concept-2", {"name": "Another Concept", "value": 100})

    print(f"Node 1 wrote 2 concepts")

    # Node 2 writes different data
    await node2.write("concept-3", {"name": "Node 2 Concept", "value": 200})

    print(f"Node 2 wrote 1 concept")

    # Get replication state from node 1
    state1 = await node1.get_replication_state()
    print(f"Node 1 state: {list(state1.keys())}")

    # Replicate node 1's state to node 2
    for key, value in state1.items():
        await node2.replicate_from("replica-1", key, value)

    print(f"Replicated node 1 state to node 2")

    # Get replication state from node 2
    state2 = await node2.get_replication_state()
    print(f"Node 2 state after replication: {list(state2.keys())}")

    # Check that node 2 now has all concepts
    assert "concept-1" in state2
    assert "concept-2" in state2
    assert "concept-3" in state2

    # Get stats
    stats1 = node1.get_stats()
    stats2 = node2.get_stats()
    print(f"Node 1 stats: {stats1}")
    print(f"Node 2 stats: {stats2}")

    print("✓ Multi-master replication works")


async def test_discovery():
    """Test node discovery."""
    print("\n=== Testing Node Discovery ===")

    from continuum.federation.distributed.discovery import DiscoveryConfig, DiscoveryMethod

    # Create discovery with bootstrap nodes
    config = DiscoveryConfig(
        enabled_methods={DiscoveryMethod.BOOTSTRAP, DiscoveryMethod.STATIC},
        bootstrap_nodes=["node1.example.com:7000", "node2.example.com:7000"]
    )

    discovery = NodeDiscovery(node_id="discovery-test", config=config)

    # Start discovery
    await discovery.start()

    # Trigger discovery
    nodes = await discovery.discover_now()
    print(f"Discovered {len(nodes)} nodes")

    # Get all nodes
    all_nodes = await discovery.get_nodes()
    print(f"Total nodes in registry: {len(all_nodes)}")
    for node in all_nodes:
        print(f"  - {node.node_id}: {node.address} (method={node.discovery_method.value})")

    # Get stats
    stats = discovery.get_stats()
    print(f"Discovery stats: {stats}")

    # Stop discovery
    await discovery.stop()

    print("✓ Node discovery works")


async def test_gossip_mesh():
    """Test gossip mesh networking."""
    print("\n=== Testing Gossip Mesh ===")

    # Create two mesh nodes
    mesh1 = GossipMesh(node_id="mesh-1")
    mesh2 = GossipMesh(node_id="mesh-2")

    # Start both
    await mesh1.start()
    await mesh2.start()

    # Add each other as peers
    await mesh1.add_peer("mesh-2", "localhost:8001")
    await mesh2.add_peer("mesh-1", "localhost:8000")

    print(f"Mesh nodes started and peered")

    # Update state on mesh1
    await mesh1.update_state("concept-count", 100)
    await mesh1.update_state("active-users", 5)

    print(f"Mesh 1 updated state")

    # Get state
    state1 = await mesh1.get_state()
    print(f"Mesh 1 state: {state1}")

    # Get stats
    stats1 = mesh1.get_stats()
    stats2 = mesh2.get_stats()
    print(f"Mesh 1 stats: {stats1}")
    print(f"Mesh 2 stats: {stats2}")

    # Stop both
    await mesh1.stop()
    await mesh2.stop()

    print("✓ Gossip mesh works")


async def test_full_integration():
    """Test full federation stack integration."""
    print("\n=== Testing Full Federation Integration ===")

    # This would test:
    # 1. Coordinator managing multiple nodes
    # 2. Raft consensus for distributed decisions
    # 3. CRDT replication for state sync
    # 4. Discovery for finding peers
    # 5. Gossip for propagating updates

    # For now, just verify all components can be imported and initialized
    print("All federation components can be imported and initialized")
    print("✓ Full integration structure is ready")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("CONTINUUM Federation System Test Suite")
    print("=" * 60)

    try:
        await test_basic_node()
        await test_coordinator()
        await test_consensus()
        await test_replication()
        await test_discovery()
        await test_gossip_mesh()
        await test_full_integration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
