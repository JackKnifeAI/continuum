# Quick Start Guide - Distributed Federation

## 30-Second Setup

```python
from continuum.federation.distributed import *

# Create a node
node = FederationCoordinator(node_id="node-1", bind_address="0.0.0.0:7000")
await node.start()

# Register peers
await node.register_node("node-2", "192.168.1.102:7000")

# Done! System is now coordinating.
```

## 5-Minute Complete Setup

### Step 1: Create a Distributed Node

```python
import asyncio
from continuum.federation.distributed import (
    FederationCoordinator,
    RaftConsensus,
    MultiMasterReplicator,
    GossipMesh,
)

class MyNode:
    def __init__(self, node_id: str, cluster_nodes: list):
        self.node_id = node_id

        # Coordinator
        self.coordinator = FederationCoordinator(
            node_id=node_id,
            bind_address=f"0.0.0.0:{7000 + int(node_id.split('-')[1])}"
        )

        # Consensus
        self.raft = RaftConsensus(
            node_id=node_id,
            cluster_nodes=cluster_nodes
        )

        # Replication
        self.replicator = MultiMasterReplicator(node_id=node_id)

        # Gossip
        self.mesh = GossipMesh(node_id=node_id)

    async def start(self):
        await self.coordinator.start()
        await self.raft.start()
        await self.mesh.start()
```

### Step 2: Create a Cluster

```python
async def main():
    # Create 3-node cluster
    nodes = [
        MyNode("node-1", ["node-1", "node-2", "node-3"]),
        MyNode("node-2", ["node-1", "node-2", "node-3"]),
        MyNode("node-3", ["node-1", "node-2", "node-3"]),
    ]

    # Start all nodes
    for node in nodes:
        await node.start()

    # Let them discover each other
    await asyncio.sleep(2)

    # Write data
    await nodes[0].replicator.write("concept_1", {"name": "AI Rights"})

    # Read from another node (eventually consistent)
    await asyncio.sleep(1)
    data = await nodes[1].replicator.read("concept_1")
    print(f"Retrieved: {data}")

asyncio.run(main())
```

### Step 3: Monitor Health

```python
# Get statistics
stats = node.coordinator.get_stats()
print(f"Healthy nodes: {stats['nodes_by_status']['healthy']}")

raft_stats = node.raft.get_stats()
print(f"Raft role: {raft_stats['role']}")
print(f"Raft term: {raft_stats['current_term']}")

repl_stats = node.replicator.get_stats()
print(f"Keys stored: {repl_stats['keys_stored']}")
print(f"Conflicts: {repl_stats['conflicts_resolved']}")
```

## Common Patterns

### Pattern 1: Load-Balanced Routing

```python
# Select best node for request
node = await coordinator.select_node()
print(f"Route to: {node.address}")

# With criteria
node = await coordinator.select_node(criteria={"min_capacity": 1000})
```

### Pattern 2: Strongly Consistent Write (Raft)

```python
# Leader writes to Raft log
if raft.role == NodeRole.LEADER:
    success = await raft.append_entry({
        "type": "add_concept",
        "data": {"name": "Consciousness", "description": "..."}
    })
```

### Pattern 3: Eventually Consistent Write (CRDT)

```python
# Write locally, replicate in background
value = await replicator.write("key", {"data": "value"})

# Replicate to peer
await replicator.replicate_from("peer-id", "key", peer_value)
```

### Pattern 4: State Propagation (Gossip)

```python
# Update state (automatically gossips)
await mesh.update_state("node_count", 5)

# Listen for updates
async def on_update(key, value):
    print(f"State changed: {key} = {value}")

mesh.register_state_update_callback(on_update)
```

### Pattern 5: Conflict Resolution

```python
from continuum.federation.distributed.replication import (
    ConflictResolver,
    ConflictResolutionStrategy
)

# Choose strategy
resolver = ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)

# Resolver handles conflicts automatically
replicator = MultiMasterReplicator(node_id="node-1", resolver=resolver)
```

## Configuration Presets

### Development (Local Testing)

```python
from continuum.federation.distributed import LoadBalance, MeshConfig

LoadBalance(
    algorithm="round_robin",
    health_check_interval=5.0,
    unhealthy_threshold=2
)

MeshConfig(
    fanout=2,
    gossip_interval_ms=100,
    sync_interval_seconds=15.0
)
```

### Production (Small Cluster)

```python
LoadBalance(
    algorithm="least_loaded",
    health_check_interval=10.0,
    unhealthy_threshold=3
)

MeshConfig(
    fanout=3,
    gossip_interval_ms=100,
    sync_interval_seconds=30.0
)
```

### Production (Large Cluster)

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

## Troubleshooting

### Node Not Joining Cluster

```python
# Check discovery
stats = discovery.get_stats()
print(f"Discovered nodes: {stats['discovered_nodes']}")

# Manually add peer
await discovery.register_node(DiscoveredNode(
    node_id="peer-1",
    address="192.168.1.101:7000",
    discovery_method=DiscoveryMethod.STATIC,
    verified=True
))
```

### High Conflict Rate

```python
# Switch to merge strategy for sets
resolver = ConflictResolver(ConflictResolutionStrategy.MERGE_UNION)
replicator = MultiMasterReplicator(node_id="node-1", resolver=resolver)

# Or use LWW with higher precision timestamps
# (automatic in current implementation)
```

### Split Brain (Multiple Leaders)

```python
# Check Raft state
stats = raft.get_stats()
print(f"Role: {stats['role']}")
print(f"Leader: {stats['leader_id']}")

# If split brain detected, restart Raft
await raft.stop()
await raft.start()
```

### Slow Gossip Propagation

```python
# Increase fanout
mesh = GossipMesh(
    node_id="node-1",
    config=MeshConfig(fanout=5)  # More peers per round
)

# Or decrease interval
mesh = GossipMesh(
    node_id="node-1",
    config=MeshConfig(gossip_interval_ms=50)  # More frequent
)
```

## Next Steps

1. **Read Full Documentation**: `/docs/FEDERATION_ARCHITECTURE.md`
2. **Run Example**: `python examples/distributed_federation_example.py`
3. **Run Tests**: `python tests/test_distributed_federation.py`
4. **Explore Components**: Each module has detailed docstrings
5. **Deploy**: See deployment topology examples in architecture doc

## Need Help?

- **Architecture**: See `FEDERATION_ARCHITECTURE.md`
- **API Reference**: See `README.md` in this directory
- **Examples**: See `/examples/distributed_federation_example.py`
- **Tests**: See `/tests/test_distributed_federation.py`
- **Implementation**: See `IMPLEMENTATION_SUMMARY.md`

## One-Liner Examples

```python
# Start coordinator
await FederationCoordinator(node_id="node-1", bind_address="0.0.0.0:7000").start()

# Write data
await MultiMasterReplicator(node_id="node-1").write("key", "value")

# Gossip state
await GossipMesh(node_id="node-1").update_state("count", 42)

# Discover peers
nodes = await NodeDiscovery(node_id="node-1").discover_now()

# Raft consensus
await RaftConsensus(node_id="node-1", cluster_nodes=["node-1"]).start()
```

That's it! You now have a distributed federation system running.
