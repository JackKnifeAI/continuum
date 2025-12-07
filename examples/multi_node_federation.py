#!/usr/bin/env python3
"""
Multi-Node Federation Example
==============================

Demonstrates running multiple CONTINUUM nodes that sync state
via gossip mesh, CRDT replication, and Raft consensus.

Usage:
    # Terminal 1 - Run node 1
    python3 examples/multi_node_federation.py --node-id node-1 --port 7000

    # Terminal 2 - Run node 2
    python3 examples/multi_node_federation.py --node-id node-2 --port 7001 --peers localhost:7000

    # Terminal 3 - Run node 3
    python3 examples/multi_node_federation.py --node-id node-3 --port 7002 --peers localhost:7000,localhost:7001
"""

import asyncio
import argparse
import sys
import json
import math
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from continuum.federation.distributed import (
    FederationCoordinator,
    RaftConsensus,
    MultiMasterReplicator,
    NodeDiscovery,
    DiscoveryConfig,
    DiscoveryMethod,
    GossipMesh,
)
from continuum.federation import FederatedNode


class FederationNode:
    """
    A complete federation node with all distributed components.
    """

    def __init__(
        self,
        node_id: str,
        bind_address: str,
        bootstrap_peers: list[str],
    ):
        self.node_id = node_id
        self.bind_address = bind_address
        self.bootstrap_peers = bootstrap_peers

        # Create components
        self.coordinator = FederationCoordinator(
            node_id=node_id,
            bind_address=bind_address,
        )

        self.replicator = MultiMasterReplicator(
            node_id=node_id,
        )

        self.discovery = NodeDiscovery(
            node_id=node_id,
            config=DiscoveryConfig(
                enabled_methods={DiscoveryMethod.BOOTSTRAP},
                bootstrap_nodes=bootstrap_peers,
            )
        )

        self.mesh = GossipMesh(
            node_id=node_id,
        )

        # Application node
        PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)
        self.app_node = FederatedNode(
            node_id=node_id,
            verify_constant=PI_PHI  # Twilight access for testing
        )

        self._running = False

    async def start(self):
        """Start all federation components."""
        print(f"\n{'='*60}")
        print(f"Starting Federation Node: {self.node_id}")
        print(f"Bind Address: {self.bind_address}")
        print(f"Bootstrap Peers: {self.bootstrap_peers}")
        print(f"{'='*60}\n")

        # Register app node
        result = self.app_node.register()
        print(f"✓ App node registered: {result}")

        # Start coordinator
        await self.coordinator.start()
        print(f"✓ Coordinator started")

        # Start discovery
        await self.discovery.start()
        print(f"✓ Discovery started")

        # Start gossip mesh
        await self.mesh.start()
        print(f"✓ Gossip mesh started")

        # Discover peers
        peers = await self.discovery.discover_now()
        print(f"✓ Discovered {len(peers)} peers")

        # Register discovered peers with coordinator
        for peer in peers:
            await self.coordinator.register_node(peer.node_id, peer.address)
            await self.mesh.add_peer(peer.node_id, peer.address)
            print(f"  - Added peer: {peer.node_id} at {peer.address}")

        self._running = True

        # Start background tasks
        asyncio.create_task(self._status_loop())
        asyncio.create_task(self._sync_loop())

        print(f"\n{'='*60}")
        print(f"Node {self.node_id} is running!")
        print(f"{'='*60}\n")

    async def stop(self):
        """Stop all federation components."""
        print(f"\nStopping node {self.node_id}...")
        self._running = False

        await self.mesh.stop()
        await self.discovery.stop()
        await self.coordinator.stop()

        print(f"✓ Node {self.node_id} stopped")

    async def _status_loop(self):
        """Periodically print node status."""
        while self._running:
            try:
                await asyncio.sleep(10)

                # Get stats from all components
                coord_stats = self.coordinator.get_stats()
                mesh_stats = self.mesh.get_stats()
                repl_stats = self.replicator.get_stats()

                print(f"\n--- Node {self.node_id} Status ---")
                print(f"Coordinator: {coord_stats['total_nodes']} nodes, "
                      f"{coord_stats['nodes_by_status']['healthy']} healthy")
                print(f"Mesh: {mesh_stats['active_peers']} active peers, "
                      f"{mesh_stats['messages_sent']} msgs sent, "
                      f"{mesh_stats['messages_received']} msgs received")
                print(f"Replication: {repl_stats['keys_stored']} keys, "
                      f"{repl_stats['writes_local']} local writes, "
                      f"{repl_stats['writes_replicated']} replicated writes")
                print(f"Vector Clock: {repl_stats['vector_clock']}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in status loop: {e}")

    async def _sync_loop(self):
        """Periodically sync state with peers."""
        while self._running:
            try:
                await asyncio.sleep(5)

                # Send heartbeat to coordinator
                await self.coordinator.heartbeat(
                    self.node_id,
                    {
                        "load_score": 0.5,
                        "latency_ms": 10.0,
                        "uptime_seconds": 100.0,
                    }
                )

                # Update some state in gossip mesh
                await self.mesh.update_state(
                    "last_sync",
                    asyncio.get_event_loop().time()
                )

                # Write to CRDT (simulate activity)
                import random
                if random.random() < 0.3:  # 30% chance
                    concept_id = f"concept-{random.randint(1, 100)}"
                    await self.replicator.write(
                        concept_id,
                        {
                            "node": self.node_id,
                            "timestamp": asyncio.get_event_loop().time(),
                            "value": random.randint(1, 1000),
                        }
                    )
                    print(f"✓ Wrote {concept_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in sync loop: {e}")

    async def interactive_shell(self):
        """Run an interactive shell for testing commands."""
        print("\nInteractive Shell Commands:")
        print("  status    - Show node status")
        print("  peers     - List peers")
        print("  write     - Write a concept")
        print("  read      - Read a concept")
        print("  sync      - Trigger sync")
        print("  quit      - Exit")
        print()

        while self._running:
            try:
                # Simulate input (in real version, use aioconsole)
                await asyncio.sleep(1)
            except KeyboardInterrupt:
                break


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run a CONTINUUM federation node")
    parser.add_argument("--node-id", required=True, help="Unique node identifier")
    parser.add_argument("--port", type=int, required=True, help="Port to bind to")
    parser.add_argument(
        "--peers",
        default="",
        help="Comma-separated list of bootstrap peers (host:port)"
    )

    args = parser.parse_args()

    # Parse peers
    peers = []
    if args.peers:
        peers = [p.strip() for p in args.peers.split(",") if p.strip()]

    # Create node
    bind_address = f"localhost:{args.port}"
    node = FederationNode(
        node_id=args.node_id,
        bind_address=bind_address,
        bootstrap_peers=peers,
    )

    # Start node
    await node.start()

    # Run forever (or until Ctrl+C)
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal...")

    # Cleanup
    await node.stop()


if __name__ == "__main__":
    asyncio.run(main())
