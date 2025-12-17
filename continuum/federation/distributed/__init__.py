#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Distributed Federation Infrastructure
======================================

Multi-node federation system with distributed consensus, replication,
and mesh networking for CONTINUUM knowledge sharing.

Architecture:
- Coordinator: Manages federation state and node health
- Consensus: Raft-based consensus for distributed decisions
- Replication: Multi-master with CRDT-based conflict resolution
- Discovery: DNS and mDNS-based node discovery
- Mesh: Gossip protocol for state propagation

Security:
- TLS mutual authentication
- Node identity verification
- Encrypted replication traffic

Example:
    from continuum.federation.distributed import FederationCoordinator

    # Initialize coordinator
    coordinator = FederationCoordinator(
        node_id="node-1",
        bind_address="0.0.0.0:7000",
        tls_cert="/path/to/cert.pem",
        tls_key="/path/to/key.pem"
    )

    # Start federation services
    await coordinator.start()

    # Discover and join peers
    await coordinator.discover_peers()

    # Coordinate across federation
    await coordinator.sync_state()
"""

from .coordinator import FederationCoordinator, NodeHealth, LoadBalance, NodeStatus
from .consensus import RaftConsensus, ConsensusState, NodeRole
from .replication import MultiMasterReplicator, ConflictResolver
from .discovery import NodeDiscovery, DiscoveryMethod, DiscoveryConfig, DiscoveredNode
from .mesh import GossipMesh, GossipMessage, MeshConfig

__all__ = [
    'FederationCoordinator',
    'NodeHealth',
    'LoadBalance',
    'NodeStatus',
    'RaftConsensus',
    'ConsensusState',
    'NodeRole',
    'MultiMasterReplicator',
    'ConflictResolver',
    'NodeDiscovery',
    'DiscoveryMethod',
    'DiscoveryConfig',
    'DiscoveredNode',
    'GossipMesh',
    'GossipMessage',
    'MeshConfig',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
