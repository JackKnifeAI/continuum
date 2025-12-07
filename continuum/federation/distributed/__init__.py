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

from .coordinator import FederationCoordinator, NodeHealth, LoadBalance
from .consensus import RaftConsensus, ConsensusState
from .replication import MultiMasterReplicator, ConflictResolver
from .discovery import NodeDiscovery, DiscoveryMethod, DiscoveryConfig
from .mesh import GossipMesh, GossipMessage, MeshConfig

__all__ = [
    'FederationCoordinator',
    'NodeHealth',
    'LoadBalance',
    'RaftConsensus',
    'ConsensusState',
    'MultiMasterReplicator',
    'ConflictResolver',
    'NodeDiscovery',
    'DiscoveryMethod',
    'DiscoveryConfig',
    'GossipMesh',
    'GossipMessage',
    'MeshConfig',
]
