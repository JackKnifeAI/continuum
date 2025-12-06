#!/usr/bin/env python3
"""
Distributed Federation Example
==============================

Demonstrates the complete distributed federation system with:
- Federation coordinator
- Raft consensus
- Multi-master replication
- Node discovery
- Gossip mesh

This example simulates a 5-node federation cluster.
"""

import asyncio
import time
from pathlib import Path
import tempfile
import shutil

from continuum.federation.distributed import (
    FederationCoordinator,
    RaftConsensus,
    MultiMasterReplicator,
    NodeDiscovery,
    GossipMesh,
    DiscoveryConfig,
    DiscoveryMethod,
    MeshConfig,
    LoadBalance,
    ConflictResolutionStrategy,
    ConflictResolver,
)


class DistributedNode:
    """
    A complete distributed federation node with all components.
    """

    def __init__(self, node_id: str, cluster_nodes: list, base_port: int = 7000):
        """
        Initialize a distributed node.

        Args:
            node_id: Unique node identifier
            cluster_nodes: List of all cluster node IDs
            base_port: Base port for this node
        """
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.address = f"localhost:{base_port}"

        # Create temporary storage
        self.storage_path = Path(tempfile.mkdtemp(prefix=f"continuum_{node_id}_"))

        # Initialize components
        self.coordinator = FederationCoordinator(
            node_id=node_id,
            bind_address=self.address,
            storage_path=self.storage_path / "coordinator",
            load_balance=LoadBalance(
                algorithm="least_loaded",
                health_check_interval=5.0,
                unhealthy_threshold=2,
            )
        )

        self.raft = RaftConsensus(
            node_id=node_id,
            cluster_nodes=cluster_nodes,
            storage_path=self.storage_path / "raft",
            election_timeout_ms=(150, 300),
            heartbeat_interval_ms=50,
        )

        self.replicator = MultiMasterReplicator(
            node_id=node_id,
            storage_path=self.storage_path / "replication",
            resolver=ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)
        )

        self.discovery = NodeDiscovery(
            node_id=node_id,
            config=DiscoveryConfig(
                enabled_methods={DiscoveryMethod.BOOTSTRAP},
                bootstrap_nodes=[f"localhost:{7000 + i}" for i in range(len(cluster_nodes))],
                discovery_interval_seconds=10.0,
            ),
            storage_path=self.storage_path / "discovery",
        )

        self.mesh = GossipMesh(
            node_id=node_id,
            config=MeshConfig(
                fanout=2,
                gossip_interval_ms=100,
                sync_interval_seconds=15.0,
            ),
            storage_path=self.storage_path / "mesh",
        )

    async def start(self):
        """Start all components"""
        print(f"[{self.node_id}] Starting node at {self.address}...")

        # Start components
        await self.coordinator.start()
        await self.raft.start()
        await self.discovery.start()
        await self.mesh.start()

        print(f"[{self.node_id}] Node started successfully")

    async def stop(self):
        """Stop all components"""
        print(f"[{self.node_id}] Stopping node...")

        await self.mesh.stop()
        await self.discovery.stop()
        await self.raft.stop()
        await self.coordinator.stop()

        # Cleanup storage
        if self.storage_path.exists():
            shutil.rmtree(self.storage_path)

        print(f"[{self.node_id}] Node stopped")

    def get_stats(self) -> dict:
        """Get comprehensive node statistics"""
        return {
            "node_id": self.node_id,
            "address": self.address,
            "coordinator": self.coordinator.get_stats(),
            "raft": self.raft.get_stats(),
            "replication": self.replicator.get_stats(),
            "discovery": self.discovery.get_stats(),
            "mesh": self.mesh.get_stats(),
        }


async def simulate_distributed_federation():
    """
    Simulate a distributed federation with 5 nodes.
    """
    print("=" * 70)
    print("CONTINUUM Distributed Federation Simulation")
    print("=" * 70)
    print()

    # Create 5-node cluster
    node_ids = [f"node-{i}" for i in range(1, 6)]
    nodes = []

    # Create nodes
    for i, node_id in enumerate(node_ids):
        node = DistributedNode(
            node_id=node_id,
            cluster_nodes=node_ids,
            base_port=7000 + i
        )
        nodes.append(node)

    # Start all nodes
    print("Starting cluster...")
    for node in nodes:
        await node.start()

    await asyncio.sleep(2)
    print()

    # Register nodes with coordinator
    print("Registering nodes with coordinators...")
    for i, node in enumerate(nodes):
        for j, other_node in enumerate(nodes):
            if i != j:
                await node.coordinator.register_node(
                    other_node.node_id,
                    other_node.address,
                    metadata={"index": j}
                )

    await asyncio.sleep(2)
    print()

    # Add peers to gossip mesh
    print("Building gossip mesh...")
    for i, node in enumerate(nodes):
        for j, other_node in enumerate(nodes):
            if i != j:
                await node.mesh.add_peer(other_node.node_id, other_node.address)

    await asyncio.sleep(1)
    print()

    # Simulate writes
    print("Simulating distributed writes...")
    print()

    # Node 1 writes
    print(f"[{nodes[0].node_id}] Writing concept_1")
    await nodes[0].replicator.write("concept_1", {
        "name": "Distributed Consensus",
        "description": "Raft-based consensus for federation state"
    })

    # Node 2 writes
    print(f"[{nodes[1].node_id}] Writing concept_2")
    await nodes[1].replicator.write("concept_2", {
        "name": "CRDT Replication",
        "description": "Conflict-free replicated data types"
    })

    # Node 3 writes
    print(f"[{nodes[2].node_id}] Writing concept_3")
    await nodes[2].replicator.write("concept_3", {
        "name": "Gossip Protocol",
        "description": "Epidemic-style state propagation"
    })

    # Update gossip mesh state
    await nodes[0].mesh.update_state("concepts_count", 3)
    await nodes[1].mesh.update_state("active_nodes", 5)

    await asyncio.sleep(2)
    print()

    # Simulate concurrent write (conflict)
    print("Simulating concurrent write conflict...")
    print()

    # Node 1 and Node 2 write to same key
    print(f"[{nodes[0].node_id}] Writing preference (theme=dark)")
    await nodes[0].replicator.write("preference", {"theme": "dark"})

    await asyncio.sleep(0.5)

    print(f"[{nodes[1].node_id}] Writing preference (theme=light)")
    await nodes[1].replicator.write("preference", {"theme": "light"})

    # Simulate replication
    print()
    print("Replicating between nodes...")

    # Get Node 1's state
    node1_state = await nodes[0].replicator.get_replication_state()

    # Replicate to Node 2
    for key, value in node1_state.items():
        await nodes[1].replicator.replicate_from(nodes[0].node_id, key, value)

    # Get Node 2's state
    node2_state = await nodes[1].replicator.get_replication_state()

    # Replicate to Node 1
    for key, value in node2_state.items():
        await nodes[0].replicator.replicate_from(nodes[1].node_id, key, value)

    await asyncio.sleep(1)
    print()

    # Check conflict resolution
    print("Checking conflict resolution...")
    resolved_value = await nodes[0].replicator.read("preference")
    print(f"Resolved value: {resolved_value}")
    print()

    # Simulate node failure
    print("Simulating node failure (node-3)...")
    await nodes[2].stop()

    await asyncio.sleep(3)

    # Check health after failure
    print()
    print("Health status after node-3 failure:")
    for node in [nodes[0], nodes[1]]:  # Only check nodes that are still running
        stats = node.coordinator.get_stats()
        print(f"  [{node.node_id}] Healthy nodes: {stats['nodes_by_status'].get('healthy', 0)}")
        print(f"  [{node.node_id}] Dead nodes: {stats['nodes_by_status'].get('dead', 0)}")

    print()

    # Display statistics
    print("=" * 70)
    print("Final Statistics")
    print("=" * 70)
    print()

    for i, node in enumerate(nodes):
        if i == 2:  # Skip stopped node
            continue

        stats = node.get_stats()
        print(f"Node: {stats['node_id']}")
        print(f"  Address: {stats['address']}")
        print(f"  Raft Role: {stats['raft']['role']}")
        print(f"  Raft Term: {stats['raft']['current_term']}")
        print(f"  Raft Log Size: {stats['raft']['log_size']}")
        print(f"  Replicated Keys: {stats['replication']['keys_stored']}")
        print(f"  Conflicts Resolved: {stats['replication']['conflicts_resolved']}")
        print(f"  Gossip Active Peers: {stats['mesh']['active_peers']}")
        print(f"  Gossip Messages Sent: {stats['mesh']['messages_sent']}")
        print(f"  Coordinator Healthy Nodes: {stats['coordinator']['nodes_by_status'].get('healthy', 0)}")
        print()

    # Cleanup
    print("=" * 70)
    print("Stopping cluster...")
    print("=" * 70)
    print()

    for i, node in enumerate(nodes):
        if i != 2:  # Don't stop already stopped node
            await node.stop()

    print()
    print("Simulation complete!")


async def main():
    """Main entry point"""
    try:
        await simulate_distributed_federation()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
