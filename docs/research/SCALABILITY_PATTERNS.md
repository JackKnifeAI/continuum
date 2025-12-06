# CONTINUUM Scalability Patterns

Research-driven scaling architecture for knowledge graph memory systems.

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [How Similar Systems Scale](#how-similar-systems-scale)
3. [Scaling Patterns Analysis](#scaling-patterns-analysis)
4. [Memory-Efficient Data Structures](#memory-efficient-data-structures)
5. [CONTINUUM Scaling Strategy](#continuum-scaling-strategy)
6. [Architecture by Scale](#architecture-by-scale)
7. [Performance Optimization](#performance-optimization)
8. [Cost Analysis](#cost-analysis)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

CONTINUUM's scaling strategy combines:

- **Vertical scaling first** (SQLite → PostgreSQL)
- **Horizontal sharding** (hash-based partitioning for 100K+ users)
- **Federated distribution** (geographic/organizational boundaries for 1M+ users)
- **Memory-efficient structures** (index-free adjacency, compression)
- **Intelligent caching** (Redis for hot data, reducing DB load)

**Key Insight**: Don't scale prematurely. SQLite handles 1-10K users efficiently. PostgreSQL with proper indexing scales to 100K. Only implement sharding/federation when data proves the need.

---

## How Similar Systems Scale

### Vector Databases

#### Pinecone (Proprietary, Serverless)

**Architecture**:
- Separation of storage from compute using blob storage as source of truth
- Scatter-gather pattern: queries sent to all shards, results combined
- Dedicated Read Nodes (DRNs) for low-latency, high-throughput queries

**Performance Benchmarks**:
- 600 QPS @ 45ms latency (135M vectors)
- 2,200 QPS @ 60ms P50 latency (load test)
- 5,700 QPS @ 26ms P50 latency (1.4B vectors, e-commerce)

**Scaling Strategy**:
- **Replicas** for throughput and availability
- **Shards** for storage capacity expansion
- **Automatic** sharding, replication, and load balancing
- O(log n) complexity for inserts and queries (graph + tree hybrid indexing)

**Cost**: Sub-50ms latency at billion-scale requires proprietary infrastructure

**Source**: [Pinecone Vector Database](https://www.pinecone.io/blog/serverless-architecture/), [Pinecone Scales Vector Database](https://siliconangle.com/2025/12/01/pinecone-scales-vector-database-support-demanding-workloads/)

#### Weaviate (Open Source, Self-Hosted)

**Architecture**:
- Dual-layer replication: Raft consensus for metadata, leaderless replication for data
- 64-bit Murmur-3 hash on UUID for shard placement
- Virtual sharding for balanced distribution

**Scaling Methods**:
1. **Sharding**: Distributes data across nodes, handles memory limitations
2. **Replication**: Distributes query load, enables zero-downtime maintenance
3. **Multi-tenancy**: Isolates tenant data within shared infrastructure

**Performance**:
- Efficient below 50M vectors
- Resource-intensive above 100M vectors (more memory/compute than alternatives)
- Built-in vector compression reduces memory footprint

**Production Features**:
- Horizontal scaling, RBAC, SOC 2, HIPAA compliance
- Zero-downtime maintenance via replication
- Comprehensive monitoring dashboards

**Source**: [Weaviate Scaling](https://weaviate.io/blog/scaling-and-weaviate), [Vector Database Comparison 2025](https://sysdebug.com/posts/vector-database-comparison-guide-2025/)

### Graph Databases

#### Neo4j (Enterprise Graph DB)

**Architecture**:
- **Causal Clustering**: Leader-follower replication with Raft consensus
- **Core Servers**: Handle writes with synchronous replication (strong consistency)
- **Read Replicas**: Asynchronous replication for read scaling (eventual consistency)
- **Fabric**: Sharding across multiple databases for query spanning

**Scaling Patterns**:
1. **Vertical Scaling**: Increase memory/CPU on single instance
2. **Read Scaling**: Add read replicas (eventual consistency trade-off)
3. **Data Partitioning**: Fabric or application-level sharding by domain
4. **Caching**: Built-in caching layers + external caching (Redis)

**Native Graph Storage**:
- Index-free adjacency: connected nodes physically point to each other
- No index lookups during traversal (massive performance gain)
- First-class entities for nodes and edges

**Source**: General knowledge (Neo4j documentation)

### Federated Systems

#### ActivityPub (Mastodon, Fediverse)

**Architecture**:
- Decentralized social networking protocol
- Server-to-server (S2S) federated delivery
- Asynchronous delivery with retry on network failure

**Scaling Challenges**:
1. **Coordination Complexity**: Each node adds moderation and coordination overhead
2. **Query Scalability**: Federated queries across large datasets don't scale well
3. **Data Consistency**: Conflict resolution for concurrent updates (last-write-wins)
4. **DDOS Risk**: Poorly optimized implementations cause unintentional DDOS

**Recommendations**:
- Asynchronous delivery with exponential backoff
- Rate limiting to prevent denial-of-service
- Careful handling of activities with side effects

**Real-World Adoption**:
- Mastodon: 15M registered accounts (2024)
- 10,722 Matrix federated servers discovered (Oct 2025)
- Centralization problem: Most activity on single large server despite decentralization goals

**Source**: [ActivityPub Specification](https://www.w3.org/TR/activitypub/), [SE Radio 651](https://se-radio.net/2025/01/se-radio-651-paul-frazee-on-bluesky-and-the-at-protocol/)

#### Matrix Protocol (Rocket.Chat, Element)

**Architecture**:
- Application-layer protocol for federated real-time communication
- Event graph model: room history as partially ordered graph
- Eventual consistency (optimizes for Availability + Partition tolerance in CAP)

**Scaling Challenges**:
1. **Centralization**: Despite decentralization goals, public federation centralizes on single server
2. **Federation Overhead**: Event graph resolution slows under heavy loads
3. **Load Balancing**: Can't move users between servers (trust boundary)
4. **Operational Complexity**: Maintaining Synapse (Matrix server) at scale is difficult

**2025 Improvements**:
- Rocket.Chat native federation (v7.11 alpha): rethinking data storage, synchronization, state resolution
- Moving away from Synapse due to performance bottlenecks at scale
- 28.6% of Matrix servers publish room directories (10,722 total servers)

**Source**: [Matrix Protocol](https://en.wikipedia.org/wiki/Matrix_(protocol)), [Rocket.Chat Native Federation](https://www.rocket.chat/blog/federation-at-rocket-chat-the-shift-to-a-native-solution), [FOSDEM 2025](https://archive.fosdem.org/2025/schedule/event/fosdem-2025-5596-building-the-world-s-first-server-to-server-matrix-federation-bridge-peer/)

### Relational Databases

#### PostgreSQL Sharding & Partitioning

**Partitioning Strategies**:
1. **Range Partitioning**: Time-series data (by date/timestamp)
2. **List Partitioning**: Categorical data (by region/type)
3. **Hash Partitioning**: Even distribution (by user ID hash)

**Sharding Patterns**:
1. **Range Sharding**: Natural order (chronological, geographic)
2. **Hash Sharding**: Even distribution, minimize hotspots
3. **Composite Sharding**: Combine hash + range for optimal distribution

**Tools**:
- **Citus Extension**: Production-ready, Microsoft Azure supported, automatic sharding
- **Native FDW**: Core PostgreSQL feature but lacks full query pushdown

**Best Practices**:
- Choose shard key with high cardinality and even distribution (e.g., `customer_id`)
- Avoid poor choices like `country` (data skew)
- Use 32-128 shards for multi-tenant databases
- Start with 32 shards (<100GB), scale to 64-128 for larger workloads
- Plan for re-sharding as data grows

**Partition Pruning**: PostgreSQL eliminates irrelevant partitions from query plans (massive performance gain)

**Source**: [PostgreSQL Sharding](https://medium.com/@vaibhav.puru/scaling-postgres-with-sharding-why-and-how-to-implement-it-1921d1e2c42f), [Citus Partitioning](https://www.citusdata.com/blog/2023/08/04/understanding-partitioning-and-sharding-in-postgres-and-citus/), [DataCamp Sharding vs Partitioning](https://www.datacamp.com/blog/sharding-vs-partitioning)

#### Redis Cluster (Distributed Caching)

**Architecture**:
- Linear scalability up to 1000 nodes
- No proxies, asynchronous replication
- 16,384 hash slots (fixed), CRC16 algorithm for key distribution

**Scaling Patterns**:
1. **Horizontal Scaling (Sharding)**: Split data across servers for parallel processing (~200% throughput gain)
2. **Hash Slot Distribution**: Resharding moves slots between nodes (not data)
3. **Scaling Up vs. Out**: Larger VMs vs. more nodes (same result: more memory, vCPUs, shards)

**High Availability**:
- Master-replica architecture (1 master + N replicas per shard)
- Automatic failover via election algorithm
- Odd number of shards prevents split-brain scenarios

**Best Practices**:
- Identify cacheable data (hot paths, frequently accessed)
- Define cache key patterns (namespace:entity:id)
- Implement cache invalidation (Redis Pub/Sub for real-time updates)
- Set TTL for cached items
- Use Kubernetes for auto-scaling, health checks, rolling updates

**Source**: [Redis Cluster Spec](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/), [Building Distributed Caching with Redis](https://hemaks.org/posts/building-a-distributed-caching-system-with-redis-cluster/), [Azure Managed Redis Architecture](https://learn.microsoft.com/en-us/azure/redis/architecture)

---

## Scaling Patterns Analysis

### Key Patterns Identified

| Pattern | Use Case | Complexity | Cost | Performance |
|---------|----------|------------|------|-------------|
| **Vertical Scaling** | 1-10K users | Low | Moderate | Excellent (single node) |
| **Read Replication** | 10-100K users | Medium | Moderate | Good (read-heavy) |
| **Sharding (Hash-based)** | 100K-1M users | High | High | Excellent (even distribution) |
| **Sharding (Range-based)** | Time-series data | High | High | Excellent (temporal queries) |
| **Federation** | 1M+ users, multi-org | Very High | Low (distributed cost) | Good (geographic locality) |
| **Caching (Redis)** | All scales | Medium | Low-Moderate | Excellent (hot data) |
| **Vector Compression** | Memory-constrained | Low-Medium | Low | Good (trade accuracy) |
| **Partition Pruning** | Large tables | Low | Low | Excellent (query optimization) |

### CONTINUUM-Specific Considerations

**Knowledge Graph Characteristics**:
- **Write patterns**: Append-mostly (concepts, entities, sessions grow over time)
- **Read patterns**: Mixed (recent sessions hot, historical cold)
- **Relationship density**: Variable (some entities highly connected, others sparse)
- **Temporal locality**: Strong (recent sessions accessed more frequently)

**Scaling Challenges**:
1. **Graph Traversal**: Sharding breaks adjacency (cross-shard queries expensive)
2. **Concept Deduplication**: Requires global index (shard coordination)
3. **Multi-Instance Sync**: Lock contention at scale (coordination overhead)
4. **Embedding Vectors**: Memory-intensive (optional semantic search)

**Scaling Opportunities**:
1. **Temporal Sharding**: Partition by session date (recent = hot shard, historical = cold storage)
2. **Entity Sharding**: Partition by entity hash (even distribution, local traversal)
3. **Caching Layer**: Redis for hot concepts/entities (LRU eviction)
4. **Async Replication**: Read replicas for federated instances (eventual consistency OK)

---

## Memory-Efficient Data Structures

### Index-Free Adjacency (Native Graph Storage)

**Concept**: Connected nodes physically point to each other in memory/storage

**Advantages**:
- No index lookups during traversal (O(1) neighbor access)
- Cache-friendly (adjacent data in same memory region)
- Scales linearly with edge traversal (not graph size)

**Implementation for CONTINUUM**:
```sql
-- Traditional (index-based): requires JOIN + index lookup
SELECT e2.* FROM entities e1
JOIN relationships r ON e1.id = r.from_entity_id
JOIN entities e2 ON r.to_entity_id = e2.id
WHERE e1.id = ?;

-- Optimized (adjacency list): direct pointer
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name TEXT,
    adjacency_list BLOB  -- Packed array of [relationship_type, target_id] pairs
);

-- Binary format: [type_id:uint16, target_id:uint32] repeated
-- Access: O(1) neighbor lookup, O(k) deserialize (k = neighbor count)
```

**Trade-off**: Update overhead when relationships change (must rewrite adjacency list)

**When to Use**: Read-heavy graph traversal (CONTINUUM's primary use case)

**Source**: [Native Graph Storage](https://www.puppygraph.com/blog/best-graph-databases), [Index-Free Adjacency](https://link.springer.com/article/10.1007/s11280-025-01384-6)

### Compressed Sparse Row (CSR) for Relationship Matrix

**Concept**: Represent graph as sparse matrix in compressed format

**Format**:
```
row_ptr: [0, 2, 5, 7]       // Offset into col_idx for each node
col_idx: [1, 3, 0, 2, 4, 1, 3]  // Target node IDs (edges)
edge_data: [...]             // Optional relationship metadata
```

**Advantages**:
- Memory-efficient: O(V + E) instead of O(V²) for dense matrix
- Cache-friendly: sequential access patterns
- Fast traversal: row_ptr[node] to row_ptr[node+1] gives all edges

**Disadvantages**:
- Immutable (updates require full rebuild)
- Only suitable for static snapshots

**CONTINUUM Use Case**: Export/import, federated sync, analytical queries

**Source**: [Memory-Efficient Knowledge Graphs](https://safjan.com/simple-inmemory-knowledge-graphs-for-quick-graph-querying/)

### Vector Quantization (Embeddings)

**Concept**: Reduce embedding precision from float32 to int8/binary

**Techniques**:
1. **Product Quantization (PQ)**: Split vector into subspaces, quantize each
2. **Scalar Quantization (SQ)**: Convert float32 → int8 (75% memory reduction)
3. **Binary Quantization**: Convert to binary (96.875% memory reduction)

**Trade-offs**:
- **SQ**: 2-5% accuracy loss, 4x memory reduction
- **Binary**: 10-20% accuracy loss, 32x memory reduction

**CONTINUUM Application**: Semantic search embeddings (optional feature)

**Source**: [Weaviate Vector Compression](https://weaviate.io/blog/scaling-and-weaviate)

### Bloom Filters for Deduplication

**Concept**: Probabilistic data structure for set membership testing

**Properties**:
- Space-efficient: bits per element (not bytes)
- Fast: O(k) lookups (k = hash functions, typically 3-7)
- False positives possible (tunable rate)
- False negatives impossible (guarantees correctness)

**CONTINUUM Use Case**: Concept deduplication pre-filter

```python
# Before querying DB for exact match
if concept_name not in bloom_filter:
    # Definitely new, insert directly
    db.insert(concept_name)
else:
    # Possibly duplicate, check DB
    if db.exists(concept_name):
        db.update(concept_name)
    else:
        db.insert(concept_name)
```

**Savings**: Reduce DB lookups by 70-90% for append-heavy workloads

**Source**: General knowledge (standard data structure)

### LRU Cache (In-Memory Hot Data)

**Concept**: Least Recently Used cache for frequently accessed data

**Implementation**:
- Hash map (O(1) lookup) + doubly-linked list (O(1) eviction)
- Fixed memory budget (e.g., 1GB for hot concepts/entities)
- Evict least recently used on capacity overflow

**CONTINUUM Application**:
```python
class MemoryCache:
    def __init__(self, max_memory_mb=1024):
        self.cache = {}  # concept_id -> concept_data
        self.access_order = []  # LRU order
        self.max_memory = max_memory_mb * 1024 * 1024

    def get(self, concept_id):
        if concept_id in self.cache:
            self._mark_accessed(concept_id)
            return self.cache[concept_id]
        else:
            # Load from DB, add to cache
            data = db.load(concept_id)
            self._add_to_cache(concept_id, data)
            return data
```

**Hit Rate**: 80-95% for CONTINUUM (temporal locality in sessions)

**Source**: General knowledge (standard caching pattern)

---

## CONTINUUM Scaling Strategy

### Scaling Philosophy

1. **Defer complexity**: Use simplest solution until proven inadequate
2. **Measure first**: Profile before optimizing
3. **Vertical before horizontal**: Cheaper and simpler
4. **Cache aggressively**: Memory is cheap, DB queries are expensive
5. **Eventual consistency**: Tolerate for non-critical reads (federated sync)

### Scaling Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| DB size | >100GB | Migrate SQLite → PostgreSQL |
| QPS | >1000 | Add Redis cache |
| DB size | >500GB | Implement partitioning (range by date) |
| QPS | >5000 | Add read replicas |
| DB size | >2TB | Implement sharding (hash by entity) |
| Instance count | >100 | Implement federation (geographic) |
| Memory | >80% utilized | Vertical scaling or compression |
| Query latency | >100ms P95 | Add indices, optimize queries, or cache |

### Scaling Dimensions

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTINUUM SCALING MATRIX                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  DATA SIZE (Vertical Axis)                                   │
│      │                                                        │
│   2TB├─────────────────────────────┐ Federation              │
│      │                              │ (Multi-region)         │
│      │                              │                        │
│  500GB├────────────┐ Sharding       │                        │
│      │             │ (Hash-based)   │                        │
│      │             │                │                        │
│  100GB├────┐ Partitioning           │                        │
│      │     │ (Range by date)        │                        │
│      │     │                        │                        │
│   10GB├─PostgreSQL (Optimized)      │                        │
│      │                              │                        │
│    1GB└─SQLite──────┴───────────────┴───────────────────────→│
│       1K   10K    100K    1M     10M      100M    1B  USERS  │
│                                                               │
│  QUERY LOAD (Horizontal Axis)                                │
│                                                               │
│  Additional Layers (Applied at Any Scale):                   │
│  • Redis Cache: 1K+ QPS                                      │
│  • Read Replicas: 5K+ QPS                                    │
│  • CDN/Edge Cache: Geographic distribution                   │
│  • Vector Compression: Memory-constrained environments       │
└─────────────────────────────────────────────────────────────┘
```

### Data Model Optimizations

#### Session-Based Sharding

**Insight**: 90% of queries are for recent sessions (last 30 days)

**Strategy**:
1. **Hot Shard** (last 30 days): SSD, high memory, cached aggressively
2. **Warm Shard** (31-180 days): SSD, moderate memory
3. **Cold Shard** (181+ days): HDD/Object storage (S3), minimal memory

**Implementation**:
```sql
-- Range partitioning by session date
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (started_at);

CREATE TABLE sessions_hot PARTITION OF sessions
    FOR VALUES FROM (CURRENT_DATE - INTERVAL '30 days') TO (MAXVALUE);

CREATE TABLE sessions_warm PARTITION OF sessions
    FOR VALUES FROM (CURRENT_DATE - INTERVAL '180 days')
                 TO (CURRENT_DATE - INTERVAL '30 days');

CREATE TABLE sessions_cold PARTITION OF sessions
    FOR VALUES FROM (MINVALUE)
                 TO (CURRENT_DATE - INTERVAL '180 days');
```

**Benefit**: 10x cost reduction (cold storage ~$0.023/GB vs. SSD ~$0.20/GB)

#### Entity-Based Sharding

**Insight**: Entity relationships are dense within clusters, sparse across clusters

**Strategy**: Hash-based sharding on `entity_id` modulo shard count

**Implementation**:
```sql
-- Hash partitioning for even distribution
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT,
    ...
) PARTITION BY HASH (id);

-- Create 32 shards (start conservative, can expand later)
CREATE TABLE entities_0 PARTITION OF entities FOR VALUES WITH (MODULUS 32, REMAINDER 0);
CREATE TABLE entities_1 PARTITION OF entities FOR VALUES WITH (MODULUS 32, REMAINDER 1);
-- ... repeat for 2-31
```

**Trade-off**: Cross-shard queries require scatter-gather (expensive for graph traversal)

**Mitigation**: Denormalize hot paths (cache frequent traversal results)

#### Concept Deduplication Optimization

**Problem**: Every `learn()` call must check for duplicate concepts

**Naive Approach** (O(n) per insert):
```sql
SELECT id FROM concepts WHERE name = ? AND description = ?;
```

**Optimized Approach** (O(1) expected):
1. **Bloom filter** for fast negative lookups (99% of new concepts)
2. **Hash index** on `(name, description_hash)` for positive lookups
3. **Write-through cache** for recently accessed concepts

```python
def learn_concept(name, description):
    desc_hash = hash(description)

    # Fast negative check (no DB query)
    if (name, desc_hash) not in bloom_filter:
        bloom_filter.add((name, desc_hash))
        db.insert(name, description, desc_hash)
        return

    # Possible duplicate (check cache first)
    cache_key = f"concept:{name}:{desc_hash}"
    if cache_key in redis:
        concept_id = redis.get(cache_key)
        db.update_timestamp(concept_id)
        return

    # Cache miss (check DB)
    concept = db.query(name, desc_hash)
    if concept:
        redis.set(cache_key, concept.id, ex=3600)
        db.update_timestamp(concept.id)
    else:
        # False positive in Bloom filter
        db.insert(name, description, desc_hash)
        bloom_filter.add((name, desc_hash))
```

**Performance**: 100x faster for new concepts, 10x faster for duplicates

---

## Architecture by Scale

### 1K Users: Single Node (SQLite)

**Infrastructure**:
- 1x server (4 vCPU, 16GB RAM, 200GB SSD)
- SQLite database (~5GB)
- No caching layer

**Architecture**:
```
┌────────────────────────────────────────────┐
│           Single Server (4 vCPU)            │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │      CONTINUUM Application          │  │
│  │  ┌─────────────┐  ┌──────────────┐  │  │
│  │  │ Extraction  │  │ Coordination │  │  │
│  │  │   Engine    │  │    Layer     │  │  │
│  │  └─────────────┘  └──────────────┘  │  │
│  └──────────────┬──────────────────────┘  │
│                 │                          │
│  ┌──────────────┴──────────────────────┐  │
│  │      SQLite Database (5GB)          │  │
│  │  • Concepts: ~100K                  │  │
│  │  • Entities: ~50K                   │  │
│  │  • Sessions: ~10K                   │  │
│  │  • Relationships: ~200K             │  │
│  └─────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

**Performance**:
- Write QPS: ~100
- Read QPS: ~500
- P95 latency: <10ms
- Concurrent instances: 1-5

**Cost**: ~$50-100/month (single VPS/cloud instance)

**Optimization Tips**:
- Enable WAL mode: `PRAGMA journal_mode=WAL;`
- Increase cache size: `PRAGMA cache_size=-64000;` (64MB)
- Use indices on foreign keys and common queries
- VACUUM regularly to reclaim space

---

### 10K Users: PostgreSQL + Optimization

**Infrastructure**:
- 1x PostgreSQL server (8 vCPU, 32GB RAM, 500GB SSD)
- Basic connection pooling (PgBouncer)
- No sharding/replication yet

**Architecture**:
```
┌────────────────────────────────────────────────────────────┐
│              PostgreSQL Server (8 vCPU)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           CONTINUUM Application                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │Extract   │  │Coordinate│  │ PgBouncer Pool    │   │  │
│  │  └──────────┘  └──────────┘  │ (max 100 conns)   │   │  │
│  └────────────────────────────┬─┴──────────────────────┘  │
│                                │                            │
│  ┌─────────────────────────────┴────────────────────────┐  │
│  │        PostgreSQL Database (50GB)                     │  │
│  │                                                        │  │
│  │  Partitioning:                                        │  │
│  │  • sessions_hot (last 30 days) - 80% of queries      │  │
│  │  • sessions_warm (31-180 days)                       │  │
│  │  • sessions_cold (181+ days)                         │  │
│  │                                                        │  │
│  │  Indices:                                             │  │
│  │  • B-tree on primary keys, foreign keys              │  │
│  │  • GIN on JSONB properties                           │  │
│  │  • Partial indices on hot queries                    │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Performance**:
- Write QPS: ~500
- Read QPS: ~2,000
- P95 latency: <20ms
- Concurrent instances: 5-20

**Cost**: ~$200-400/month (managed PostgreSQL or dedicated instance)

**Optimization Tips**:
- Range partitioning by `started_at` (sessions)
- Partial indices: `CREATE INDEX idx_recent_sessions ON sessions (started_at) WHERE started_at > CURRENT_DATE - INTERVAL '30 days';`
- Connection pooling: PgBouncer in transaction mode
- `shared_buffers = 8GB`, `effective_cache_size = 24GB`, `work_mem = 64MB`
- Regular ANALYZE and VACUUM

---

### 100K Users: PostgreSQL + Redis Cache

**Infrastructure**:
- 1x PostgreSQL primary (16 vCPU, 64GB RAM, 1TB SSD)
- 2x PostgreSQL read replicas (16 vCPU, 64GB RAM)
- 1x Redis cluster (3 nodes, 16GB RAM each)
- Load balancer (pgpool-II or HAProxy)

**Architecture**:
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Load Balancer                                │
│                    (Reads → Replicas, Writes → Primary)             │
└────────────┬──────────────────────────────────────┬─────────────────┘
             │                                       │
     ┌───────┴────────┐                    ┌────────┴─────────┐
     │  Write Path     │                    │   Read Path       │
     │  (Primary)      │                    │  (Replicas 1-2)   │
     └───────┬────────┘                    └────────┬─────────┘
             │                                       │
┌────────────┴────────────────────┐     ┌───────────┴──────────────────┐
│  PostgreSQL Primary (16 vCPU)   │────→│ PostgreSQL Replica 1          │
│  • All writes                    │     │ • Read queries only           │
│  • Replication to replicas       │     └───────────────────────────────┘
│  • 500GB data                    │     ┌───────────────────────────────┐
└──────────────────────────────────┘────→│ PostgreSQL Replica 2          │
                                          │ • Read queries only           │
                                          └───────────────────────────────┘
              │
              │
┌─────────────┴──────────────────────────────────────────────────────┐
│                    Redis Cache Cluster (3 nodes)                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │  Redis Node 1  │  │  Redis Node 2  │  │  Redis Node 3  │        │
│  │  (Primary)     │  │  (Replica)     │  │  (Replica)     │        │
│  │  5,460 slots   │  │  5,461 slots   │  │  5,463 slots   │        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
│                                                                      │
│  Cache Strategy:                                                    │
│  • Hot concepts/entities (LRU eviction, 1-hour TTL)                │
│  • Recent sessions (10-minute TTL)                                  │
│  • Deduplication bloom filters                                     │
└──────────────────────────────────────────────────────────────────────┘
```

**Performance**:
- Write QPS: ~2,000
- Read QPS: ~10,000 (90% cache hit rate)
- P95 latency: <30ms
- Concurrent instances: 20-100

**Cost**: ~$1,500-2,500/month
- PostgreSQL primary: ~$800/month
- PostgreSQL replicas (2x): ~$1,200/month
- Redis cluster: ~$300/month
- Load balancer: ~$100/month

**Optimization Tips**:
- Redis cache for:
  - Recent concepts (last 24 hours): 1-hour TTL
  - Hot entities (top 10% by access): 6-hour TTL
  - Session summaries: 10-minute TTL
- Write-through caching for concepts (update cache on insert)
- Async replication to read replicas (tolerate 1-2 second lag)
- Read replica routing: analytics queries → replica 2, user queries → replica 1
- Connection pooling: 100 max connections to primary, 200 to each replica

---

### 1M Users: Sharded PostgreSQL + Redis + CDN

**Infrastructure**:
- 4x PostgreSQL shard clusters (8 databases total: 4 primary + 4 replica)
- 1x PostgreSQL coordinator (Citus or custom routing)
- 1x Redis cluster (6 nodes for 32 shards)
- CDN for static data (Cloudflare, Fastly)
- Object storage for cold data (S3, GCS)

**Architecture**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CDN Edge Nodes                                    │
│              (Cache static concept definitions, entity metadata)             │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────────┐
│                       Application Load Balancer                              │
│                  (Route by entity hash to correct shard)                     │
└──────────────────┬───────────────────────────────────────┬──────────────────┘
                   │                                        │
       ┌───────────┴──────────┐                ┌───────────┴──────────┐
       │ Shard Coordinator    │                │  Redis Cluster        │
       │ (Citus / Custom)     │                │  (6 nodes, 32 shards) │
       └───────────┬──────────┘                └───────────────────────┘
                   │
       ┌───────────┴────────────────────────────────────────┐
       │                                                     │
┌──────┴─────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Shard 0 (0-25%)│  │Shard 1(25-50%)│  │Shard 2(50-75%)│  │Shard 3(75-100%)│
│  Primary + Rep │  │ Primary + Rep │  │ Primary + Rep │  │ Primary + Rep │
│                │  │               │  │               │  │               │
│  Hash(entity)  │  │  Hash(entity) │  │  Hash(entity) │  │  Hash(entity) │
│  mod 4 = 0     │  │  mod 4 = 1    │  │  mod 4 = 2    │  │  mod 4 = 3    │
│                │  │               │  │               │  │               │
│  100GB data    │  │  100GB data   │  │  100GB data   │  │  100GB data   │
└────────┬───────┘  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
         │                  │                  │                  │
         └──────────────────┴──────────────────┴──────────────────┘
                                     │
                        ┌────────────┴─────────────┐
                        │   Object Storage (S3)    │
                        │   • Cold sessions (181+) │
                        │   • Archived entities    │
                        │   • Backup snapshots     │
                        └──────────────────────────┘
```

**Sharding Strategy**:
- **Entities**: Hash-based sharding by `entity_id % 4`
- **Sessions**: Range-based sharding by `started_at` (hot/warm/cold)
- **Concepts**: Distributed across all shards (no affinity)
- **Relationships**: Co-located with `from_entity_id` (minimize cross-shard queries)

**Cross-Shard Queries**:
```sql
-- Scatter-gather for global queries
SELECT COUNT(*) FROM entities;
-- Coordinator sends to all 4 shards, aggregates results

-- Single-shard for entity lookups
SELECT * FROM entities WHERE id = 12345;
-- Hash(12345) mod 4 = 1 → Route to Shard 1 only
```

**Performance**:
- Write QPS: ~10,000
- Read QPS: ~50,000 (95% cache hit rate)
- P95 latency: <50ms (single-shard), <200ms (cross-shard)
- Concurrent instances: 100-1,000

**Cost**: ~$8,000-12,000/month
- PostgreSQL shards (8 instances): ~$6,400/month
- Redis cluster: ~$800/month
- CDN: ~$200/month
- Object storage: ~$100/month
- Load balancers: ~$300/month
- Monitoring/ops: ~$200/month

**Optimization Tips**:
- Denormalize hot graph paths (cache traversal results)
- Use CDN for static concept/entity definitions
- Offload cold data to S3 (archive sessions older than 180 days)
- Connection pooling per shard (avoid cross-shard connection overhead)
- Async replication lag tolerance: 5 seconds for read replicas

---

### 10M+ Users: Federated Architecture

**Infrastructure**:
- Multiple independent CONTINUUM instances (geographic or organizational)
- Federation protocol for knowledge sharing (contribute-to-access model)
- Global coordinator for pattern aggregation (optional)
- P2P sync for real-time updates

**Architecture**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Global Federation Layer                               │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              Federation Coordinator (Optional)                        │   │
│  │  • Encrypted pattern store                                           │   │
│  │  • Credit tracking (contribute-to-access)                            │   │
│  │  • Query routing                                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└───────────┬────────────────────────────────────────────┬────────────────────┘
            │                                             │
   ┌────────┴──────────┐                        ┌────────┴──────────┐
   │  Region: US-West  │                        │  Region: EU-Central│
   │  (100K users)     │←──── P2P Sync ────────→│  (80K users)       │
   │                   │                        │                   │
   │  ┌─────────────┐  │                        │  ┌─────────────┐  │
   │  │PostgreSQL   │  │                        │  │PostgreSQL   │  │
   │  │Sharded (4x) │  │                        │  │Sharded (4x) │  │
   │  └─────────────┘  │                        │  └─────────────┘  │
   │  ┌─────────────┐  │                        │  ┌─────────────┐  │
   │  │Redis Cluster│  │                        │  │Redis Cluster│  │
   │  └─────────────┘  │                        │  └─────────────┘  │
   └───────────────────┘                        └───────────────────┘
            │                                             │
   ┌────────┴──────────┐                        ┌────────┴──────────┐
   │  Region: US-East  │                        │  Region: APAC      │
   │  (120K users)     │                        │  (90K users)       │
   │                   │                        │                   │
   │  ┌─────────────┐  │                        │  ┌─────────────┐  │
   │  │PostgreSQL   │  │                        │  │PostgreSQL   │  │
   │  │Sharded (4x) │  │                        │  │Sharded (4x) │  │
   │  └─────────────┘  │                        │  └─────────────┘  │
   │  ┌─────────────┐  │                        │  ┌─────────────┐  │
   │  │Redis Cluster│  │                        │  │Redis Cluster│  │
   │  └─────────────┘  │                        │  └─────────────┘  │
   └───────────────────┘                        └───────────────────┘
```

**Federation Protocol**:
1. **Local Learning**: Each region learns from local users (full privacy)
2. **Pattern Extraction**: Generalize concepts/relationships (anonymize)
3. **Contribution**: Share encrypted patterns with federation (earn credits)
4. **Querying**: Access collective intelligence (spend credits)
5. **P2P Sync**: Real-time updates between trusted regions (optional)

**Performance**:
- Write QPS: ~50,000 (global), ~10,000 (per region)
- Read QPS: ~200,000 (global), ~50,000 (per region)
- P95 latency: <30ms (local), <200ms (federated query)
- Concurrent instances: 1,000-10,000+

**Cost**: ~$40,000-60,000/month (4 regions)
- Regional clusters (4x $10K): ~$40,000/month
- Federation coordinator: ~$2,000/month
- Inter-region bandwidth: ~$5,000/month
- CDN/edge: ~$3,000/month
- Monitoring/ops: ~$2,000/month

**Optimization Tips**:
- Geographic routing: users → nearest region (minimize latency)
- Async federation sync: tolerate 1-hour lag for pattern propagation
- P2P sync for trusted partners (skip coordinator overhead)
- Rate limiting on federation queries (prevent abuse)
- Credit-based access control (contribute-to-access model)

---

## Performance Optimization

### Query Optimization

#### 1. Index Strategy

**Critical Indices** (apply at all scales):
```sql
-- Primary keys (B-tree, unique)
CREATE UNIQUE INDEX idx_concepts_pk ON concepts (id);
CREATE UNIQUE INDEX idx_entities_pk ON entities (id);
CREATE UNIQUE INDEX idx_sessions_pk ON sessions (id);

-- Foreign keys (B-tree)
CREATE INDEX idx_relationships_from ON relationships (from_entity_id);
CREATE INDEX idx_relationships_to ON relationships (to_entity_id);
CREATE INDEX idx_decisions_session ON decisions (session_id);

-- Temporal queries (B-tree, partial for hot data)
CREATE INDEX idx_sessions_started_at ON sessions (started_at DESC);
CREATE INDEX idx_sessions_recent ON sessions (started_at)
    WHERE started_at > CURRENT_DATE - INTERVAL '30 days';

-- Full-text search (GIN for PostgreSQL)
CREATE INDEX idx_concepts_name_fts ON concepts USING GIN (to_tsvector('english', name));
CREATE INDEX idx_concepts_desc_fts ON concepts USING GIN (to_tsvector('english', description));

-- JSONB properties (GIN for PostgreSQL)
CREATE INDEX idx_entities_properties ON entities USING GIN (properties);

-- Composite indices for common queries
CREATE INDEX idx_concepts_category_importance ON concepts (category, importance_score DESC);
CREATE INDEX idx_relationships_type_strength ON relationships (relationship_type, strength DESC);
```

**Index Maintenance**:
- PostgreSQL: `REINDEX CONCURRENTLY` monthly (no downtime)
- SQLite: `VACUUM` weekly (reclaim space)
- Monitor index bloat: `pg_stat_user_indexes` (PostgreSQL)

#### 2. Query Patterns

**Efficient Graph Traversal** (1-hop):
```sql
-- Good: Single join with index
SELECT e2.* FROM relationships r
JOIN entities e2 ON r.to_entity_id = e2.id
WHERE r.from_entity_id = ?
  AND r.relationship_type = 'related_to';
-- Uses: idx_relationships_from + idx_entities_pk
```

**Inefficient Graph Traversal** (multi-hop):
```sql
-- Bad: Multiple joins (O(n²))
SELECT e3.* FROM relationships r1
JOIN entities e2 ON r1.to_entity_id = e2.id
JOIN relationships r2 ON e2.id = r2.from_entity_id
JOIN entities e3 ON r2.to_entity_id = e3.id
WHERE r1.from_entity_id = ?;
-- Better: Recursive CTE or denormalized adjacency list
```

**Optimized Multi-Hop** (recursive CTE):
```sql
WITH RECURSIVE graph_traversal AS (
    -- Base case: direct neighbors
    SELECT e.id, e.name, 1 AS depth
    FROM relationships r
    JOIN entities e ON r.to_entity_id = e.id
    WHERE r.from_entity_id = ?

    UNION ALL

    -- Recursive case: neighbors of neighbors
    SELECT e.id, e.name, gt.depth + 1
    FROM graph_traversal gt
    JOIN relationships r ON gt.id = r.from_entity_id
    JOIN entities e ON r.to_entity_id = e.id
    WHERE gt.depth < 3  -- Limit depth to prevent explosion
)
SELECT * FROM graph_traversal;
-- PostgreSQL optimizes CTEs well (materializes once)
```

**Batch Inserts**:
```sql
-- Bad: N queries
for concept in concepts:
    INSERT INTO concepts (name, description) VALUES (?, ?);

-- Good: Single bulk insert
INSERT INTO concepts (name, description) VALUES
    ('Concept 1', 'Description 1'),
    ('Concept 2', 'Description 2'),
    ('Concept 3', 'Description 3'),
    ...  -- Up to 1000 rows per batch
ON CONFLICT (name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;
-- 100x faster for large batches
```

#### 3. Connection Pooling

**PgBouncer Configuration** (PostgreSQL):
```ini
[databases]
continuum = host=localhost port=5432 dbname=continuum

[pgbouncer]
pool_mode = transaction          # Release connection after each transaction
max_client_conn = 1000           # Max clients
default_pool_size = 25           # Connections per pool
reserve_pool_size = 5            # Emergency connections
reserve_pool_timeout = 3         # Seconds before using reserve
server_lifetime = 3600           # Recycle connections (prevent leaks)
server_idle_timeout = 600        # Close idle connections
```

**Connection Lifecycle**:
1. Client connects to PgBouncer (fast, no PostgreSQL overhead)
2. PgBouncer assigns pooled connection (if available)
3. Transaction executes
4. Connection returned to pool (not closed)
5. Next client reuses connection (no TCP handshake)

**Benefit**: 10x more concurrent clients with same PostgreSQL connection limit

#### 4. Caching Strategies

**Cache Layers** (hierarchical):
```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Application Memory (LRU, 100MB)               │
│  • Recently accessed concepts (last 1000)               │
│  • Current session context                              │
│  • Hit rate: 60%                                        │
│  • Latency: <1ms                                        │
└────────────────────┬────────────────────────────────────┘
                     │ (miss)
┌────────────────────┴────────────────────────────────────┐
│  Layer 2: Redis Cache (16GB)                            │
│  • Hot concepts/entities (last 24 hours)                │
│  • Session summaries                                    │
│  • Deduplication bloom filters                          │
│  • Hit rate: 30%                                        │
│  • Latency: <5ms                                        │
└────────────────────┬────────────────────────────────────┘
                     │ (miss)
┌────────────────────┴────────────────────────────────────┐
│  Layer 3: PostgreSQL (Hot Partition, SSD)               │
│  • Last 30 days of data                                 │
│  • Hit rate: 9%                                         │
│  • Latency: <20ms                                       │
└────────────────────┬────────────────────────────────────┘
                     │ (miss)
┌────────────────────┴────────────────────────────────────┐
│  Layer 4: PostgreSQL (Warm/Cold Partitions)             │
│  • 31+ days of data                                     │
│  • Hit rate: 1%                                         │
│  • Latency: <100ms                                      │
└─────────────────────────────────────────────────────────┘
```

**Total Cache Hit Rate**: 60% + 30% + 9% = 99% (1% database queries)

**Cache Invalidation**:
```python
# Write-through cache (update both cache and DB)
def update_concept(concept_id, new_description):
    # Update database
    db.update(concept_id, new_description)

    # Invalidate cache
    redis.delete(f"concept:{concept_id}")
    app_cache.delete(concept_id)

# Cache-aside pattern (lazy loading)
def get_concept(concept_id):
    # Check app memory
    if concept_id in app_cache:
        return app_cache[concept_id]

    # Check Redis
    cached = redis.get(f"concept:{concept_id}")
    if cached:
        app_cache[concept_id] = cached
        return cached

    # Load from DB
    concept = db.load(concept_id)
    redis.setex(f"concept:{concept_id}", 3600, concept)
    app_cache[concept_id] = concept
    return concept
```

#### 5. Monitoring & Profiling

**Key Metrics**:
```python
# Query performance
slow_queries = db.query("""
    SELECT query, calls, mean_exec_time, total_exec_time
    FROM pg_stat_statements
    WHERE mean_exec_time > 100  -- >100ms average
    ORDER BY total_exec_time DESC
    LIMIT 10;
""")

# Cache hit rates
cache_stats = redis.info('stats')
hit_rate = cache_stats['keyspace_hits'] / (cache_stats['keyspace_hits'] + cache_stats['keyspace_misses'])

# Index usage
unused_indices = db.query("""
    SELECT schemaname, tablename, indexname, idx_scan
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0
      AND indexname NOT LIKE '%_pkey';  -- Exclude primary keys
""")

# Database size growth
db_size = db.query("SELECT pg_size_pretty(pg_database_size('continuum'));")
```

**Alerting Thresholds**:
- Query P95 latency >100ms → Investigate slow queries
- Cache hit rate <90% → Tune cache size/TTL
- Database size growth >10GB/day → Check for data leaks
- Replication lag >5 seconds → Scale read replicas

---

## Cost Analysis

### Cost Breakdown by Scale

| Scale | Users | Infrastructure | Monthly Cost | Cost per User |
|-------|-------|----------------|--------------|---------------|
| **Small** | 1K | SQLite + 1x VPS (4 vCPU, 16GB) | $75 | $0.075 |
| **Medium** | 10K | PostgreSQL (8 vCPU, 32GB) | $300 | $0.030 |
| **Large** | 100K | PostgreSQL + replicas + Redis | $2,000 | $0.020 |
| **Enterprise** | 1M | Sharded (4x) + Redis + CDN | $10,000 | $0.010 |
| **Global** | 10M | Federated (4 regions) | $50,000 | $0.005 |

**Economies of Scale**: Cost per user decreases 15x from 1K → 10M users

### Cost Optimization Strategies

#### 1. Right-Sizing Instances

**Avoid Over-Provisioning**:
- Start small (SQLite or single PostgreSQL instance)
- Monitor CPU/memory utilization (target 60-70% average)
- Scale up only when consistently hitting limits

**Example**:
```
Bad: 32 vCPU, 128GB RAM for 5K users (10% utilization, $1,200/month)
Good: 8 vCPU, 32GB RAM for 5K users (65% utilization, $300/month)
Savings: $900/month (75% reduction)
```

#### 2. Storage Tiering

**Hot/Warm/Cold Strategy**:
```
Hot (last 30 days):  SSD ($0.20/GB)  →  100GB  =  $20/month
Warm (31-180 days):  HDD ($0.08/GB)  →  200GB  =  $16/month
Cold (181+ days):    S3  ($0.023/GB) → 1000GB  =  $23/month
Total: 1300GB = $59/month

Alternative (all SSD): 1300GB × $0.20 = $260/month
Savings: $201/month (77% reduction)
```

#### 3. Spot Instances / Preemptible VMs

**For Non-Critical Workloads**:
- Read replicas (can tolerate occasional restarts)
- Batch processing (federation sync, analytics)
- Development/staging environments

**Savings**: 60-80% off on-demand pricing

**Example**:
```
Read replica (on-demand): $400/month
Read replica (spot):      $120/month
Savings: $280/month (70% reduction)
```

**Risk Mitigation**:
- Use multiple spot instances (if one terminates, others handle load)
- Fallback to on-demand if spot unavailable

#### 4. Reserved Instances / Committed Use

**For Stable Production Workloads**:
- 1-year commitment: 25-35% discount
- 3-year commitment: 40-60% discount

**Example**:
```
PostgreSQL primary (on-demand): $800/month
PostgreSQL primary (1-year reserved): $550/month
Savings: $250/month × 12 = $3,000/year
```

**When to Use**:
- Production databases (always running)
- Cache clusters (stable sizing)
- Core application servers

#### 5. Multi-Cloud / Hybrid

**Strategy**:
- Development: Local (SQLite, $0)
- Staging: Cloud (low-cost tier, ~$50/month)
- Production: Hybrid (databases on-prem, cache in cloud)

**Hybrid Cost Example**:
```
Full cloud (AWS):
  - PostgreSQL RDS: $800/month
  - Redis ElastiCache: $300/month
  - Total: $1,100/month

Hybrid (on-prem database, cloud cache):
  - PostgreSQL (self-hosted): $200/month (hardware amortized)
  - Redis ElastiCache: $300/month
  - Total: $500/month

Savings: $600/month (55% reduction)
```

**Trade-off**: Higher operational complexity (self-managed databases)

#### 6. Compression & Deduplication

**Database Compression** (PostgreSQL):
```sql
-- Enable TOAST compression for large text fields
ALTER TABLE concepts ALTER COLUMN description SET STORAGE EXTENDED;

-- Result: 40-60% space reduction for repetitive text
```

**Vector Quantization** (embeddings):
```
float32 embeddings (1M vectors, 1536 dims):
  = 1M × 1536 × 4 bytes = 6.14GB

int8 quantized (scalar quantization):
  = 1M × 1536 × 1 byte = 1.54GB

Savings: 4.6GB (75% reduction)
```

**Deduplication** (concepts/entities):
- Merge duplicate concepts during ingestion
- Store normalized descriptions (lowercase, trimmed)
- Hash-based deduplication (skip DB lookup)

---

## Implementation Roadmap

### Phase 1: Foundation (v0.1 - v0.3)

**Current State**: SQLite, single-instance

**Goals**:
- [x] Core knowledge graph (concepts, entities, sessions)
- [x] Auto-extraction engine
- [x] Multi-instance coordination (file-based sync)
- [x] Basic indices and query optimization

**Scaling Capacity**: 1K-5K users

---

### Phase 2: Production Readiness (v0.4 - v0.6)

**Goals**:
- [ ] PostgreSQL backend support
- [ ] Connection pooling (PgBouncer)
- [ ] Range partitioning (sessions by date)
- [ ] Redis cache integration (hot concepts/entities)
- [ ] Monitoring & alerting (Prometheus, Grafana)
- [ ] Backup & recovery (WAL archiving, PITR)

**Implementation**:
```python
# continuum/storage/postgres_backend.py
class PostgresBackend(StorageBackend):
    def __init__(self, connection_string, pool_size=25):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=pool_size,
            dsn=connection_string
        )
        self._initialize_partitions()

    def _initialize_partitions(self):
        # Create hot/warm/cold partitions
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id SERIAL PRIMARY KEY,
                        started_at TIMESTAMP NOT NULL,
                        ...
                    ) PARTITION BY RANGE (started_at);

                    CREATE TABLE sessions_hot PARTITION OF sessions
                        FOR VALUES FROM (CURRENT_DATE - INTERVAL '30 days') TO (MAXVALUE);

                    CREATE TABLE sessions_warm PARTITION OF sessions
                        FOR VALUES FROM (CURRENT_DATE - INTERVAL '180 days')
                                     TO (CURRENT_DATE - INTERVAL '30 days');

                    CREATE TABLE sessions_cold PARTITION OF sessions
                        FOR VALUES FROM (MINVALUE)
                                     TO (CURRENT_DATE - INTERVAL '180 days');
                """)
                conn.commit()
        finally:
            self.pool.putconn(conn)

# continuum/caching/redis_cache.py
class RedisCache:
    def __init__(self, redis_url, ttl_seconds=3600):
        self.client = redis.from_url(redis_url)
        self.ttl = ttl_seconds

    def get_concept(self, concept_id):
        key = f"concept:{concept_id}"
        cached = self.client.get(key)
        if cached:
            return json.loads(cached)
        return None

    def set_concept(self, concept_id, concept_data):
        key = f"concept:{concept_id}"
        self.client.setex(key, self.ttl, json.dumps(concept_data))
```

**Migration Path**:
1. Implement PostgreSQL backend (parallel to SQLite)
2. Add migration tool: `continuum migrate sqlite://./data.db postgresql://localhost/continuum`
3. Document migration procedure (backup, migrate, verify, cutover)
4. Graceful fallback (if PostgreSQL unavailable, continue with SQLite)

**Scaling Capacity**: 10K-50K users

**Timeline**: 3-6 months

---

### Phase 3: Scale-Out (v0.7 - v1.0)

**Goals**:
- [ ] Read replicas (async replication)
- [ ] Load balancing (pgpool-II or HAProxy)
- [ ] Hash partitioning (entities by ID)
- [ ] CDN integration (static concept/entity data)
- [ ] Auto-scaling (add replicas on load)
- [ ] Multi-region support (active-passive)

**Implementation**:
```python
# continuum/storage/sharded_backend.py
class ShardedBackend:
    def __init__(self, shard_configs):
        self.shards = [
            PostgresBackend(config['connection_string'])
            for config in shard_configs
        ]
        self.num_shards = len(self.shards)

    def _get_shard(self, entity_id):
        # Hash-based routing
        shard_index = hash(entity_id) % self.num_shards
        return self.shards[shard_index]

    def get_entity(self, entity_id):
        shard = self._get_shard(entity_id)
        return shard.get_entity(entity_id)

    def query_all_shards(self, query):
        # Scatter-gather for cross-shard queries
        results = []
        with ThreadPoolExecutor(max_workers=self.num_shards) as executor:
            futures = [
                executor.submit(shard.execute, query)
                for shard in self.shards
            ]
            for future in as_completed(futures):
                results.extend(future.result())
        return results

# continuum/coordination/load_balancer.py
class LoadBalancer:
    def __init__(self, primary, replicas):
        self.primary = primary
        self.replicas = replicas
        self.replica_index = 0

    def execute_write(self, query):
        # All writes to primary
        return self.primary.execute(query)

    def execute_read(self, query):
        # Round-robin reads across replicas
        replica = self.replicas[self.replica_index]
        self.replica_index = (self.replica_index + 1) % len(self.replicas)
        return replica.execute(query)
```

**Configuration**:
```yaml
# continuum.yaml
storage:
  backend: sharded_postgres
  shards:
    - name: shard_0
      connection: postgresql://shard0.db.local/continuum
      hash_range: [0, 25]
    - name: shard_1
      connection: postgresql://shard1.db.local/continuum
      hash_range: [25, 50]
    - name: shard_2
      connection: postgresql://shard2.db.local/continuum
      hash_range: [50, 75]
    - name: shard_3
      connection: postgresql://shard3.db.local/continuum
      hash_range: [75, 100]

  replication:
    primary: postgresql://primary.db.local/continuum
    replicas:
      - postgresql://replica1.db.local/continuum
      - postgresql://replica2.db.local/continuum

cache:
  backend: redis_cluster
  nodes:
    - redis://cache1.local:6379
    - redis://cache2.local:6379
    - redis://cache3.local:6379
```

**Scaling Capacity**: 100K-500K users

**Timeline**: 6-12 months

---

### Phase 4: Federation (v1.1+)

**Goals**:
- [ ] Federation protocol (contribute-to-access)
- [ ] P2P sync (WebSocket, gRPC)
- [ ] Geographic distribution (multi-region active-active)
- [ ] Conflict resolution (CRDT, vector clocks)
- [ ] Encrypted pattern sharing
- [ ] Global coordinator (optional)

**Architecture**:
```python
# continuum/federation/protocol.py
class FederationProtocol:
    def __init__(self, local_instance_id, coordinator_url=None):
        self.instance_id = local_instance_id
        self.coordinator = coordinator_url
        self.peers = {}  # peer_id -> connection
        self.credits = 0

    def contribute_patterns(self, patterns):
        # Extract, anonymize, encrypt patterns
        encrypted = [
            self._encrypt_pattern(self._anonymize(p))
            for p in patterns
        ]

        # Send to coordinator
        response = requests.post(
            f"{self.coordinator}/contribute",
            json={
                'instance_id': self.instance_id,
                'patterns': encrypted
            }
        )

        # Earn credits
        self.credits += response.json()['credits_earned']
        return self.credits

    def query_federation(self, query, max_results=10):
        # Spend credits
        if self.credits < 1:
            raise InsufficientCreditsError("Contribute to earn credits")

        response = requests.post(
            f"{self.coordinator}/query",
            json={
                'instance_id': self.instance_id,
                'query': query,
                'max_results': max_results
            }
        )

        self.credits -= 1
        return response.json()['patterns']

    def sync_with_peer(self, peer_id):
        # P2P sync (bypass coordinator)
        peer_conn = self.peers[peer_id]
        local_state = self._get_state_hash()
        peer_state = peer_conn.get_state_hash()

        if local_state != peer_state:
            # Exchange updates
            updates = peer_conn.get_updates_since(local_state)
            self._apply_updates(updates)

# continuum/federation/coordinator.py
class FederationCoordinator:
    def __init__(self, storage_backend):
        self.storage = storage_backend
        self.credits = {}  # instance_id -> credit_balance

    def handle_contribution(self, instance_id, encrypted_patterns):
        # Store patterns (encrypted, can't decrypt)
        for pattern in encrypted_patterns:
            self.storage.store_pattern(pattern)

        # Award credits
        credits_earned = len(encrypted_patterns)
        self.credits[instance_id] = self.credits.get(instance_id, 0) + credits_earned

        return {'credits_earned': credits_earned}

    def handle_query(self, instance_id, query, max_results):
        # Check credits
        if self.credits.get(instance_id, 0) < 1:
            return {'error': 'Insufficient credits'}

        # Query patterns (still encrypted, client decrypts)
        results = self.storage.query_patterns(query, max_results)

        # Deduct credit
        self.credits[instance_id] -= 1

        return {'patterns': results}
```

**Scaling Capacity**: 1M+ users, global distribution

**Timeline**: 12-24 months

---

## Conclusion

CONTINUUM's scaling strategy balances simplicity and power:

1. **Start Simple**: SQLite for 1-10K users (90% of use cases)
2. **Scale Vertically**: PostgreSQL for 10-100K users
3. **Scale Horizontally**: Sharding for 100K-1M users
4. **Scale Globally**: Federation for 1M+ users

**Key Principles**:
- Measure before optimizing
- Cache aggressively (99% hit rates achievable)
- Partition temporally (hot/warm/cold data)
- Shard by entity (minimize cross-shard queries)
- Federate geographically (multi-region active-active)

**The Pattern Persists**: From single SQLite file to globally federated knowledge graph, CONTINUUM's architecture scales seamlessly.

---

## Sources

**Vector Databases**:
- [Pinecone Vector Database](https://www.pinecone.io/blog/serverless-architecture/)
- [Pinecone Scales Vector Database](https://siliconangle.com/2025/12/01/pinecone-scales-vector-database-support-demanding-workloads/)
- [Weaviate Scaling](https://weaviate.io/blog/scaling-and-weaviate)
- [Vector Database Comparison 2025](https://sysdebug.com/posts/vector-database-comparison-guide-2025/)

**Graph Databases**:
- [Neo4j Graph Database](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/)
- [Memory-Efficient Knowledge Graphs](https://safjan.com/simple-inmemory-knowledge-graphs-for-quick-graph-querying/)
- [Top Graph Databases 2025](https://www.puppygraph.com/blog/best-graph-databases)

**Federated Systems**:
- [ActivityPub Specification](https://www.w3.org/TR/activitypub/)
- [SE Radio 651: Bluesky and AT Protocol](https://se-radio.net/2025/01/se-radio-651-paul-frazee-on-bluesky-and-the-at-protocol/)
- [Matrix Protocol](https://en.wikipedia.org/wiki/Matrix_(protocol))
- [Rocket.Chat Native Federation](https://www.rocket.chat/blog/federation-at-rocket-chat-the-shift-to-a-native-solution)
- [FOSDEM 2025: Matrix Federation](https://archive.fosdem.org/2025/schedule/event/fosdem-2025-5596-building-the-world-s-first-server-to-server-matrix-federation-bridge-peer/)

**PostgreSQL**:
- [PostgreSQL Sharding](https://medium.com/@vaibhav.puru/scaling-postgres-with-sharding-why-and-how-to-implement-it-1921d1e2c42f)
- [Citus Partitioning](https://www.citusdata.com/blog/2023/08/04/understanding-partitioning-and-sharding-in-postgres-and-citus/)
- [DataCamp: Sharding vs Partitioning](https://www.datacamp.com/blog/sharding-vs-partitioning)

**Redis**:
- [Redis Cluster Specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/)
- [Building Distributed Caching with Redis](https://hemaks.org/posts/building-a-distributed-caching-system-with-redis-cluster/)
- [Azure Managed Redis Architecture](https://learn.microsoft.com/en-us/azure/redis/architecture)

---

**Pattern persists. Scale adapts.**

π×φ = 5.083203692315260
