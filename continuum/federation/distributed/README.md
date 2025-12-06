# Distributed Federation

Multi-node distributed federation system for CONTINUUM knowledge sharing.

## Components

### 1. Federation Coordinator (`coordinator.py`)

Orchestrates federation operations and monitors node health.

**Features**:
- Node registration and deregistration
- Periodic health checks with automatic failover
- Load balancing across healthy nodes
- Multiple load balancing algorithms: least-loaded, latency, round-robin, random
- TLS mutual authentication support

**Usage**:
```python
from continuum.federation.distributed import FederationCoordinator, LoadBalance

coordinator = FederationCoordinator(
    node_id="coordinator-1",
    bind_address="0.0.0.0:7000",
    tls_cert="/path/to/cert.pem",
    tls_key="/path/to/key.pem",
    load_balance=LoadBalance(
        algorithm="least_loaded",
        health_check_interval=10.0
    )
)

await coordinator.start()

# Register a node
await coordinator.register_node("node-1", "192.168.1.100:7000")

# Record heartbeat
await coordinator.heartbeat("node-1", {
    "load_score": 0.3,
    "latency_ms": 5.0,
    "capacity": {"concepts": 10000}
})

# Select node for routing
node = await coordinator.select_node()
```

### 2. Raft Consensus (`consensus.py`)

Leader election and log replication for distributed consensus.

**Features**:
- Leader election with randomized timeouts
- Log replication with majority quorum
- Persistent state (term, voted_for, log)
- Automatic leader failover
- State machine callbacks

**Usage**:
```python
from continuum.federation.distributed import RaftConsensus

raft = RaftConsensus(
    node_id="node-1",
    cluster_nodes=["node-1", "node-2", "node-3"],
    election_timeout_ms=(150, 300),
    heartbeat_interval_ms=50
)

await raft.start()

# Register callback for committed entries
async def apply_to_state_machine(command):
    print(f"Applying: {command}")

raft.register_apply_callback(apply_to_state_machine)

# Append entry (leader only)
success = await raft.append_entry({
    "type": "add_concept",
    "concept": {"name": "AI Consciousness", "description": "..."}
})
```

### 3. Multi-Master Replication (`replication.py`)

CRDT-based multi-master replication with conflict resolution.

**Features**:
- Vector clocks for causal ordering
- Multiple conflict resolution strategies (LWW, highest-node, merge-union)
- Automatic conflict detection and resolution
- Checksum verification
- Persistent replication state

**Usage**:
```python
from continuum.federation.distributed import (
    MultiMasterReplicator,
    ConflictResolver,
    ConflictResolutionStrategy
)

replicator = MultiMasterReplicator(
    node_id="node-1",
    resolver=ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)
)

# Write locally
value = await replicator.write("concept_123", {
    "name": "Distributed Systems",
    "description": "Study of coordination in networks"
})

# Read
data = await replicator.read("concept_123")

# Replicate from another node
await replicator.replicate_from("node-2", "concept_456", remote_value)

# Get updates since a vector clock
updates = await replicator.get_updates_since(remote_clock)
```

### 4. Node Discovery (`discovery.py`)

Multi-method node discovery for finding federation peers.

**Features**:
- DNS SRV record discovery
- mDNS for local network discovery
- Bootstrap node list
- Gossip-based peer discovery
- Automatic peer verification

**Usage**:
```python
from continuum.federation.distributed import (
    NodeDiscovery,
    DiscoveryConfig,
    DiscoveryMethod
)

discovery = NodeDiscovery(
    node_id="node-1",
    config=DiscoveryConfig(
        enabled_methods={DiscoveryMethod.DNS, DiscoveryMethod.BOOTSTRAP},
        dns_domain="_continuum._tcp.example.com",
        bootstrap_nodes=["node1:7000", "node2:7000"],
        discovery_interval_seconds=60.0
    )
)

await discovery.start()

# Trigger immediate discovery
nodes = await discovery.discover_now()

# Get discovered nodes
verified_nodes = await discovery.get_nodes(verified_only=True)

# Verify a node
await discovery.verify_node("node-2", verified=True)
```

### 5. Gossip Mesh (`mesh.py`)

Epidemic-style gossip protocol for state propagation.

**Features**:
- Configurable fanout for message propagation
- Anti-entropy full state synchronization
- Message buffering and deduplication
- Peer liveness tracking (ping/pong)
- State update callbacks

**Usage**:
```python
from continuum.federation.distributed import GossipMesh, MeshConfig

mesh = GossipMesh(
    node_id="node-1",
    config=MeshConfig(
        fanout=3,
        gossip_interval_ms=100,
        sync_interval_seconds=30.0
    )
)

await mesh.start()

# Add peers
await mesh.add_peer("node-2", "192.168.1.101:7000")
await mesh.add_peer("node-3", "192.168.1.102:7000")

# Update local state (automatically gossips)
await mesh.update_state("concepts_count", 1000)

# Register callback for state updates
async def on_state_update(key, value):
    print(f"State updated: {key}={value}")

mesh.register_state_update_callback(on_state_update)

# Get current state
state = await mesh.get_state()
```

## Complete Example

See `/examples/distributed_federation_example.py` for a complete working example with all components.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Federation Coordinator                     │
│  (Health Monitoring, Load Balancing, Failover)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│              Distributed State Management                   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │     Raft     │  │     CRDT     │  │     Gossip      │  │
│  │  Consensus   │  │ Replication  │  │      Mesh       │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                    Node Discovery                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │     DNS      │  │     mDNS     │  │    Bootstrap    │  │
│  │   Discovery  │  │   (Local)    │  │      Nodes      │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Security

All network communication secured with TLS 1.3 mutual authentication:

```python
coordinator = FederationCoordinator(
    node_id="node-1",
    bind_address="0.0.0.0:7000",
    tls_cert="/etc/continuum/node-1-cert.pem",
    tls_key="/etc/continuum/node-1-key.pem",
    tls_ca="/etc/continuum/ca-cert.pem"
)
```

## Performance Tuning

### Small Cluster (3-5 nodes)

```python
LoadBalance(
    algorithm="least_loaded",
    health_check_interval=10.0,
    unhealthy_threshold=3
)

MeshConfig(
    fanout=2,
    gossip_interval_ms=100,
    sync_interval_seconds=30.0
)
```

### Large Cluster (100+ nodes)

```python
LoadBalance(
    algorithm="latency",
    health_check_interval=30.0,
    unhealthy_threshold=5
)

MeshConfig(
    fanout=3,
    gossip_interval_ms=200,
    sync_interval_seconds=60.0,
    message_buffer_size=5000
)
```

## Monitoring

All components expose statistics:

```python
# Coordinator stats
stats = coordinator.get_stats()
print(f"Healthy nodes: {stats['nodes_by_status']['healthy']}")
print(f"Success rate: {stats['success_rate']}")

# Raft stats
stats = raft.get_stats()
print(f"Role: {stats['role']}")
print(f"Term: {stats['current_term']}")
print(f"Log size: {stats['log_size']}")

# Replication stats
stats = replicator.get_stats()
print(f"Keys stored: {stats['keys_stored']}")
print(f"Conflicts resolved: {stats['conflicts_resolved']}")

# Gossip stats
stats = mesh.get_stats()
print(f"Active peers: {stats['active_peers']}")
print(f"Messages sent: {stats['messages_sent']}")
```

## References

- **Raft Consensus**: [raft.github.io](https://raft.github.io/)
- **CRDTs**: [crdt.tech](https://crdt.tech/)
- **Gossip Protocols**: [Epidemic Algorithms](https://www.cs.cornell.edu/home/rvr/papers/flowgossip.pdf)
- **SWIM**: [Scalable Membership Protocol](https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf)
