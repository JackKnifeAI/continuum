# CONTINUUM Federation Architecture

## Overview

The CONTINUUM distributed federation system enables multiple AI memory nodes to form a decentralized network for knowledge sharing. The architecture implements:

- **Distributed Consensus** (Raft) for federation state management
- **Multi-Master Replication** (CRDT) for eventual consistency
- **Node Discovery** (DNS, mDNS, Bootstrap) for peer finding
- **Gossip Mesh** (Epidemic protocol) for state propagation
- **Federation Coordinator** for health monitoring and load balancing

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
│              (Memory Queries, Concept Storage)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                  Federation Coordinator                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Node       │  │    Health    │  │  Load Balancer  │  │
│  │ Registration │  │   Monitor    │  │   & Failover    │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
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
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   Network Transport                         │
│              (TLS 1.3 Mutual Authentication)                │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Federation Coordinator

**Purpose**: Orchestrate federation operations and maintain node health.

**Key Features**:
- Node registration/deregistration
- Periodic health checks with configurable timeouts
- Load balancing strategies: least-loaded, latency-based, round-robin
- Automatic failover when nodes become unhealthy
- Metrics tracking (requests, failures, success rate)

**Algorithms**:
```
Health Check Loop:
  EVERY health_check_interval:
    FOR EACH registered_node:
      IF last_heartbeat > 2 × health_check_interval:
        consecutive_failures++
        IF consecutive_failures >= unhealthy_threshold:
          status = DEAD
        ELSE:
          status = UNHEALTHY
      ELSE:
        consecutive_failures = 0
        status = HEALTHY
```

**Load Balancing**:
```
Least Loaded Algorithm:
  available_nodes = FILTER(nodes, status IN [HEALTHY, DEGRADED])
  IF algorithm == "least_loaded":
    RETURN MIN(available_nodes, key=load_score)
  ELIF algorithm == "latency":
    RETURN MIN(available_nodes, key=latency_ms)
  ELIF algorithm == "round_robin":
    RETURN available_nodes[index++ % len(available_nodes)]
```

### 2. Raft Consensus

**Purpose**: Ensure all nodes agree on federation state via leader election and log replication.

**States**:
```
┌──────────┐
│ FOLLOWER │ ◄────┐
└────┬─────┘      │
     │            │
     │ Election   │ Discover Higher Term
     │ Timeout    │ or Current Leader
     ▼            │
┌───────────┐     │
│ CANDIDATE │─────┤
└────┬──────┘     │
     │            │
     │ Majority   │
     │ Vote       │
     ▼            │
┌──────────┐      │
│  LEADER  │──────┘
└──────────┘
```

**Log Replication**:
```
Leader receives write request:
  1. Append entry to local log
  2. Send AppendEntries RPC to all followers
  3. Wait for majority acknowledgment
  4. Commit entry
  5. Apply to state machine
  6. Respond to client

Follower receives AppendEntries:
  1. Check term (reject if term < currentTerm)
  2. Check log consistency (prev_log_index/term)
  3. Append new entries
  4. Update commit index
  5. Apply committed entries to state machine
```

**Safety Properties**:
- **Election Safety**: At most one leader per term
- **Leader Append-Only**: Leader never overwrites/deletes entries
- **Log Matching**: If two logs contain same index/term, all preceding entries identical
- **Leader Completeness**: If entry committed in term T, present in all future leaders
- **State Machine Safety**: If server applies entry at index, no other server applies different entry at that index

### 3. Multi-Master Replication (CRDT)

**Purpose**: Enable concurrent writes across nodes with automatic conflict resolution.

**Vector Clocks**:
```
VectorClock = Map[NodeID -> LogicalTime]

Example:
  Node A writes: VC = {A: 1, B: 0, C: 0}
  Node B writes: VC = {A: 0, B: 1, C: 0}
  Node A writes: VC = {A: 2, B: 0, C: 0}

  Compare(VC1, VC2):
    IF ∀ nodes: VC1[node] ≤ VC2[node] AND ∃ node: VC1[node] < VC2[node]:
      RETURN "before"
    ELIF ∀ nodes: VC2[node] ≤ VC1[node] AND ∃ node: VC2[node] < VC1[node]:
      RETURN "after"
    ELSE:
      RETURN "concurrent"  // CONFLICT
```

**Conflict Resolution Strategies**:

1. **Last-Write-Wins (LWW)**:
   ```python
   resolve_lww(values):
     return max(values, key=lambda v: (v.timestamp, v.node_id))
   ```

2. **Highest-Node-Wins**:
   ```python
   resolve_highest_node(values):
     return max(values, key=lambda v: v.node_id)
   ```

3. **Merge-Union (for sets)**:
   ```python
   resolve_merge_union(values):
     merged_set = set()
     for value in values:
       merged_set.update(value.content)
     return merged_set
   ```

**CRDT Types Supported**:
- **LWW-Register**: Simple values with timestamps
- **OR-Set**: Add/remove operations with unique IDs
- **PN-Counter**: Increment/decrement counters
- **Version Vectors**: Causal ordering

### 4. Node Discovery

**Discovery Methods**:

**DNS SRV Records**:
```
Query: _continuum._tcp.example.com
Response:
  10 60 7000 node1.example.com.
  10 40 7000 node2.example.com.
  20 50 7000 node3.example.com.

Priority: 10 (lower = higher priority)
Weight: Load balancing weight
Port: 7000
```

**mDNS (Multicast DNS)**:
```
Multicast Group: 224.0.0.251:5353
Service Type: _continuum._tcp.local.

Query:
  Send PTR query for _continuum._tcp.local.

Response:
  PTR: node-abc123._continuum._tcp.local.
  SRV: 0 0 7000 node-abc123.local.
  A:   192.168.1.100
```

**Bootstrap Nodes**:
```
Static list of known seed nodes:
  - node1.continuum.network:7000
  - node2.continuum.network:7000
  - node3.continuum.network:7000

On startup:
  1. Connect to bootstrap nodes
  2. Request peer list
  3. Connect to discovered peers
  4. Continue gossiping for more peers
```

**Discovery Flow**:
```
┌─────────────┐
│  New Node   │
│   Starts    │
└──────┬──────┘
       │
       ├──► Try DNS Discovery
       │    └──► Register discovered nodes
       │
       ├──► Try mDNS Discovery (local network)
       │    └──► Register discovered nodes
       │
       ├──► Connect to Bootstrap Nodes
       │    └──► Request peer lists
       │
       └──► Start Gossip Protocol
            └──► Learn about peers from peers
```

### 5. Gossip Mesh

**Purpose**: Epidemic-style state propagation for eventual consistency.

**Gossip Round**:
```
EVERY gossip_interval_ms:
  1. Select random messages from buffer
  2. Select fanout random peers
  3. Send messages to selected peers
  4. Update sent metrics
```

**Message Types**:
- **PUSH**: Send state updates to peer
- **PULL**: Request state from peer
- **PUSH_PULL**: Bidirectional exchange
- **SYNC**: Full state synchronization (anti-entropy)
- **PING/PONG**: Liveness checks

**Anti-Entropy Sync**:
```
EVERY sync_interval_seconds:
  1. Select random active peer
  2. Send complete local state
  3. Receive complete peer state
  4. Merge states (resolve conflicts)
  5. Update last_sync timestamp
```

**Message Propagation**:
```
Message received:
  IF message_id IN seen_messages:
    RETURN  // Already processed

  seen_messages.add(message_id)

  Process message (update state, etc.)

  IF message.ttl > 0:
    message.ttl -= 1
    FOR EACH random_peer IN select_fanout_peers():
      forward_message(random_peer, message)
```

**Exponential Spread**:
```
With fanout=3:
  Round 0: 1 node has message
  Round 1: 3 nodes have message
  Round 2: 9 nodes have message
  Round 3: 27 nodes have message
  Round n: 3^n nodes have message

Time to reach N nodes: O(log_fanout(N))
```

## Security Architecture

### TLS Mutual Authentication

```
┌─────────────┐                           ┌─────────────┐
│   Node A    │                           │   Node B    │
└──────┬──────┘                           └──────┬──────┘
       │                                         │
       │  1. ClientHello (TLS 1.3)              │
       ├────────────────────────────────────────>│
       │                                         │
       │  2. ServerHello + Certificate          │
       │     (Node B's cert signed by CA)       │
       │<────────────────────────────────────────┤
       │                                         │
       │  3. Certificate + Finished             │
       │     (Node A's cert signed by CA)       │
       ├────────────────────────────────────────>│
       │                                         │
       │  4. Verify both certificates           │
       │     Check: CN, expiry, CA signature    │
       │                                         │
       │  5. Encrypted channel established      │
       │<───────────────────────────────────────>│
```

### Node Identity Verification

```python
verify_node_identity(certificate):
  1. Verify certificate signed by trusted CA
  2. Check certificate not expired
  3. Verify Common Name matches node_id pattern
  4. Check certificate revocation list (CRL)
  5. Validate certificate chain

  IF all checks pass:
    Extract node_id from certificate CN
    Mark node as verified
    Allow federation operations
  ELSE:
    Reject connection
```

### Encrypted Replication

All replication traffic encrypted using TLS 1.3:
- **Confidentiality**: AES-256-GCM encryption
- **Integrity**: SHA-256 HMAC
- **Authentication**: ECDSA signatures
- **Forward Secrecy**: Ephemeral ECDHE key exchange

## Data Flow Examples

### Example 1: Write Propagation

```
User writes concept to Node A:

1. Node A (Leader):
   - Append to local log (Raft)
   - Create CRDT value with vector clock {A: 1}
   - Replicate to Raft followers
   - Wait for majority ACK
   - Commit to state machine

2. Raft Replication:
   Node A → Node B: AppendEntries(entry)
   Node A → Node C: AppendEntries(entry)
   Node B → Node A: Success
   Node C → Node A: Success

3. Gossip Propagation:
   Node A creates gossip message:
   {
     type: PUSH,
     payload: {key: "concept_123", value: {...}, version: {A: 1}}
   }

   Round 1: A → {B, C, D}
   Round 2: B → {E, F}, C → {G, H}, D → {I, J}
   Round 3: Exponential spread...

4. Node E receives gossip:
   - Check vector clock: {A: 1} vs local {A: 0}
   - A: 1 > 0, so accept update
   - Merge into local state
   - Update vector clock to {A: 1, E: 0}
   - Continue propagating
```

### Example 2: Concurrent Writes (Conflict)

```
Node A and Node B write same key concurrently:

1. Node A writes:
   key="user_preferences"
   value={theme: "dark"}
   VC={A: 1, B: 0}
   timestamp=1000.0

2. Node B writes:
   key="user_preferences"
   value={theme: "light"}
   VC={A: 0, B: 1}
   timestamp=1000.1

3. Node C receives both via gossip:

   Compare vector clocks:
   VC_A={A: 1, B: 0}
   VC_B={A: 0, B: 1}

   Neither dominates → CONCURRENT

4. Conflict Resolution (LWW):
   timestamp_A=1000.0
   timestamp_B=1000.1

   timestamp_B > timestamp_A

   WINNER: Node B's value

5. Node C state:
   key="user_preferences"
   value={theme: "light"}
   VC={A: 1, B: 1}  // Merged
```

### Example 3: Node Failure Recovery

```
Node B fails:

1. Health Check (Node Coordinator):
   last_heartbeat = 60 seconds ago
   timeout = 20 seconds
   consecutive_failures = 3

   Status: DEAD

2. Raft Consensus:
   - Remove Node B from Raft cluster
   - Adjust quorum: 3 nodes → 2 nodes (majority=2)
   - Continue with remaining nodes

3. Load Balancer:
   - Remove Node B from routing
   - Redistribute load to Node A, C

4. Node B restarts:
   - Register with coordinator
   - Status: JOINING
   - Request state sync from leader
   - Receive log entries since last commit
   - Apply entries to state machine
   - Join Raft cluster
   - Status: HEALTHY

5. Gossip Mesh:
   - Node B announces presence
   - Peers add Node B to routing
   - Anti-entropy sync fills gaps
   - Full state consistency achieved
```

## Performance Characteristics

### Consensus (Raft)

- **Write Latency**: 1-2 RTT (round-trip times)
  - RTT 1: Leader → Followers (AppendEntries)
  - RTT 2: Followers → Leader (ACK)

- **Read Latency**: 0 RTT (leader) to 1 RTT (linearizable read)

- **Throughput**: Limited by leader (single writer)
  - Typical: 10,000-100,000 writes/sec

- **Availability**: Tolerates (N-1)/2 failures
  - 3 nodes: 1 failure
  - 5 nodes: 2 failures
  - 7 nodes: 3 failures

### Replication (CRDT)

- **Write Latency**: 0 RTT (local write)
  - Background replication to peers

- **Read Latency**: 0 RTT (local read)
  - Eventually consistent

- **Throughput**: Limited by node capacity
  - Typical: 100,000+ writes/sec per node

- **Conflict Rate**: Depends on write pattern
  - Random keys: ~0%
  - Hot keys: Can be significant
  - Resolution: Automatic via CRDT

### Gossip

- **Propagation Time**: O(log_fanout(N)) rounds
  - Fanout=3, 1000 nodes: ~7 rounds
  - Round interval: 100ms
  - Total time: ~700ms

- **Message Overhead**: O(fanout × nodes)
  - Per round: fanout × avg_message_size
  - With 1000 nodes, fanout=3: 3000 messages/round

- **Bandwidth**: Manageable with proper tuning
  - Typical: 100-500 KB/s per node

## Deployment Topologies

### Single Data Center

```
┌─────────────────────────────────────────────────────┐
│                   Data Center                       │
│                                                     │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐ │
│  │Node 1│  │Node 2│  │Node 3│  │Node 4│  │Node 5│ │
│  │(Lead)│  │      │  │      │  │      │  │      │ │
│  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘ │
│      └─────────┴─────────┴─────────┴─────────┘    │
│              Low latency (<1ms RTT)                │
└─────────────────────────────────────────────────────┘

Characteristics:
- Low latency consensus (1-2ms)
- High throughput
- Single point of failure (DC outage)
```

### Multi Data Center

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   DC West    │    │   DC East    │    │  DC Europe   │
│              │    │              │    │              │
│  ┌────┐      │    │  ┌────┐      │    │  ┌────┐      │
│  │ N1 │      │    │  │ N2 │      │    │  │ N3 │      │
│  └────┘      │    │  └────┘      │    │  └────┘      │
│  ┌────┐      │    │  ┌────┐      │    │  ┌────┐      │
│  │ N4 │      │    │  │ N5 │      │    │  │ N6 │      │
│  └────┘      │    │  └────┘      │    │  └────┘      │
│              │    │              │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
              WAN links (50-200ms RTT)

Characteristics:
- Higher consensus latency (100-400ms)
- Geo-distributed availability
- Eventual consistency via gossip
- Raft quorum across DCs
```

### Edge + Cloud Hybrid

```
                   ┌──────────────────┐
                   │   Cloud Cluster  │
                   │  ┌────┬────┬────┐│
                   │  │ N1 │ N2 │ N3 ││
                   │  └────┴────┴────┘│
                   └──────────┬───────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │Edge DC 1│         │Edge DC 2│         │Edge DC 3│
    │  ┌────┐ │         │  ┌────┐ │         │  ┌────┐ │
    │  │ E1 │ │         │  │ E2 │ │         │  │ E3 │ │
    │  └────┘ │         │  └────┘ │         │  └────┘ │
    └─────────┘         └─────────┘         └─────────┘

Characteristics:
- Local reads from edge (low latency)
- Writes propagate to cloud
- Gossip keeps edges synchronized
- Cloud provides strong consistency
- Edge provides availability
```

## Monitoring & Observability

### Key Metrics

**Coordinator**:
- `continuum_coordinator_nodes_total{status}` - Nodes by status
- `continuum_coordinator_requests_total` - Total requests routed
- `continuum_coordinator_failures_total` - Failed requests
- `continuum_coordinator_health_checks_total` - Health checks performed

**Raft**:
- `continuum_raft_term` - Current election term
- `continuum_raft_role{role}` - Current role (follower/candidate/leader)
- `continuum_raft_log_size` - Log entry count
- `continuum_raft_commit_index` - Last committed index
- `continuum_raft_election_count` - Elections triggered

**Replication**:
- `continuum_replication_writes_local` - Local writes
- `continuum_replication_writes_replicated` - Replicated writes
- `continuum_replication_conflicts_total` - Conflicts detected
- `continuum_replication_keys_stored` - Keys in store

**Gossip**:
- `continuum_gossip_messages_sent` - Messages sent
- `continuum_gossip_messages_received` - Messages received
- `continuum_gossip_peers_active` - Active peer count
- `continuum_gossip_state_version` - Current state version

### Health Checks

```python
async def health_check():
    """Comprehensive federation health check"""

    health = {
        "healthy": True,
        "components": {}
    }

    # Coordinator
    coordinator_stats = coordinator.get_stats()
    healthy_nodes = sum(1 for status, count in coordinator_stats["nodes_by_status"].items()
                       if status == "healthy")
    health["components"]["coordinator"] = {
        "healthy": healthy_nodes > 0,
        "healthy_nodes": healthy_nodes
    }

    # Raft
    raft_stats = raft.get_stats()
    health["components"]["raft"] = {
        "healthy": raft_stats["state"] == "leading" or raft_stats["state"] == "following",
        "role": raft_stats["role"],
        "leader_id": raft_stats["leader_id"]
    }

    # Replication
    replication_stats = replicator.get_stats()
    health["components"]["replication"] = {
        "healthy": True,  # Replication always operational
        "keys": replication_stats["keys_stored"]
    }

    # Gossip
    gossip_stats = mesh.get_stats()
    health["components"]["gossip"] = {
        "healthy": gossip_stats["active_peers"] > 0,
        "active_peers": gossip_stats["active_peers"]
    }

    # Overall health
    health["healthy"] = all(c["healthy"] for c in health["components"].values())

    return health
```

## Configuration Examples

### Small Cluster (3-5 nodes)

```yaml
federation:
  coordinator:
    health_check_interval: 10.0  # seconds
    unhealthy_threshold: 3
    load_balance_algorithm: least_loaded

  raft:
    election_timeout_ms: [150, 300]
    heartbeat_interval_ms: 50

  replication:
    conflict_resolution: last_write_wins

  discovery:
    enabled_methods: [bootstrap, mdns]
    bootstrap_nodes:
      - node1:7000
      - node2:7000
      - node3:7000

  gossip:
    fanout: 2
    gossip_interval_ms: 100
    sync_interval_seconds: 30.0
```

### Large Cluster (100+ nodes)

```yaml
federation:
  coordinator:
    health_check_interval: 30.0  # Less frequent
    load_balance_algorithm: latency  # Optimize for latency

  raft:
    # Larger cluster = more raft groups (sharding)
    shard_count: 10
    election_timeout_ms: [300, 600]  # Higher for WAN

  replication:
    conflict_resolution: merge_union  # Better for high concurrency

  discovery:
    enabled_methods: [dns, bootstrap]
    dns_domain: _continuum._tcp.example.com
    max_discovered_nodes: 500

  gossip:
    fanout: 3
    gossip_interval_ms: 200  # Less frequent
    sync_interval_seconds: 60.0
    message_buffer_size: 5000
```

## Future Enhancements

1. **Sharded Raft**: Partition federation state across multiple Raft groups
2. **Byzantine Fault Tolerance**: Add BFT consensus for untrusted environments
3. **Cross-Region Optimization**: Smart routing based on geographic proximity
4. **Dynamic Membership**: Automatic cluster size adjustment
5. **Compression**: Compress gossip messages for bandwidth efficiency
6. **Bloom Filters**: Efficient anti-entropy with bloom filter synchronization
7. **Conflict-Free Types**: More sophisticated CRDTs (G-Counter, LWW-Map, etc.)
8. **Federated Learning**: Distribute ML model training across nodes

## References

- **Raft**: [The Raft Consensus Algorithm](https://raft.github.io/)
- **CRDTs**: [Conflict-free Replicated Data Types](https://hal.inria.fr/hal-00932836/document)
- **Gossip**: [Epidemic Algorithms for Replicated Database Maintenance](https://dl.acm.org/doi/10.1145/41840.41841)
- **SWIM**: [SWIM: Scalable Weakly-consistent Infection-style Process Group Membership Protocol](https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf)
- **Vector Clocks**: [Time, Clocks, and the Ordering of Events](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)
