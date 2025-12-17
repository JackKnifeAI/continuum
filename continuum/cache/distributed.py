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
Distributed Caching

Redis Cluster support, consistent hashing, and cache coherence
across multiple nodes.

Features:
    - Redis Cluster client
    - Consistent hashing for key distribution
    - Cache coherence protocols
    - Multi-region support
    - Failover handling
"""

import hashlib
from typing import Any, Optional, List, Dict, Set
from dataclasses import dataclass
import logging

try:
    from rediscluster import RedisCluster
    CLUSTER_AVAILABLE = True
except ImportError:
    CLUSTER_AVAILABLE = False

from .redis_cache import RedisCache, RedisCacheConfig

logger = logging.getLogger(__name__)


@dataclass
class ClusterConfig:
    """Configuration for Redis Cluster"""

    # Cluster nodes (host:port pairs)
    startup_nodes: List[Dict[str, Any]]

    # Security
    password: Optional[str] = None
    ssl: bool = False

    # Behavior
    max_connections: int = 50
    max_connections_per_node: int = 10
    decode_responses: bool = False
    skip_full_coverage_check: bool = False

    # Retry settings
    cluster_error_retry_attempts: int = 3
    cluster_retry_timeout: float = 5.0

    @classmethod
    def from_nodes(cls, nodes: List[str], password: Optional[str] = None) -> 'ClusterConfig':
        """
        Create config from node strings.

        Args:
            nodes: List of "host:port" strings
            password: Optional cluster password

        Returns:
            ClusterConfig instance

        Example:
            config = ClusterConfig.from_nodes([
                "redis1.example.com:6379",
                "redis2.example.com:6379",
                "redis3.example.com:6379"
            ])
        """
        startup_nodes = []
        for node in nodes:
            host, port = node.split(":")
            startup_nodes.append({"host": host, "port": int(port)})

        return cls(startup_nodes=startup_nodes, password=password)


class ConsistentHash:
    """
    Consistent hashing ring for key distribution.

    Used to distribute keys across cache nodes with minimal
    redistribution when nodes are added/removed.
    """

    def __init__(self, nodes: List[str], replicas: int = 150):
        """
        Initialize consistent hash ring.

        Args:
            nodes: List of node identifiers
            replicas: Number of virtual nodes per physical node
        """
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []

        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        """Hash a key to a position on the ring"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str):
        """
        Add a node to the hash ring.

        Args:
            node: Node identifier
        """
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_key = self._hash(virtual_key)
            self.ring[hash_key] = node

        self.sorted_keys = sorted(self.ring.keys())
        logger.info(f"Added node {node} to hash ring ({self.replicas} replicas)")

    def remove_node(self, node: str):
        """
        Remove a node from the hash ring.

        Args:
            node: Node identifier
        """
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_key = self._hash(virtual_key)
            if hash_key in self.ring:
                del self.ring[hash_key]

        self.sorted_keys = sorted(self.ring.keys())
        logger.info(f"Removed node {node} from hash ring")

    def get_node(self, key: str) -> Optional[str]:
        """
        Get the node responsible for a key.

        Args:
            key: Cache key

        Returns:
            Node identifier or None if no nodes
        """
        if not self.ring:
            return None

        hash_key = self._hash(key)

        # Find the first node with hash >= key hash
        for ring_key in self.sorted_keys:
            if ring_key >= hash_key:
                return self.ring[ring_key]

        # Wrap around to first node
        return self.ring[self.sorted_keys[0]]

    def get_nodes_for_key(self, key: str, count: int = 3) -> List[str]:
        """
        Get multiple nodes for replication.

        Args:
            key: Cache key
            count: Number of nodes to return

        Returns:
            List of node identifiers
        """
        if not self.ring or count <= 0:
            return []

        hash_key = self._hash(key)
        nodes = set()
        idx = 0

        # Find starting position
        for i, ring_key in enumerate(self.sorted_keys):
            if ring_key >= hash_key:
                idx = i
                break

        # Collect unique nodes
        attempts = 0
        max_attempts = len(self.sorted_keys)

        while len(nodes) < count and attempts < max_attempts:
            node = self.ring[self.sorted_keys[idx % len(self.sorted_keys)]]
            nodes.add(node)
            idx += 1
            attempts += 1

        return list(nodes)


class DistributedCache:
    """
    Distributed cache with Redis Cluster support.

    Provides cache coherence across multiple Redis nodes
    using consistent hashing or Redis Cluster.
    """

    def __init__(self, config: Optional[ClusterConfig] = None,
                 use_cluster: bool = False):
        """
        Initialize distributed cache.

        Args:
            config: Optional cluster configuration
            use_cluster: Use Redis Cluster (requires redis-py-cluster)
        """
        self.use_cluster = use_cluster and CLUSTER_AVAILABLE

        if self.use_cluster:
            if not CLUSTER_AVAILABLE:
                raise RuntimeError("redis-py-cluster not installed. Install with: pip install redis-py-cluster")

            if not config:
                raise ValueError("ClusterConfig required for cluster mode")

            self.cluster = RedisCluster(
                startup_nodes=config.startup_nodes,
                password=config.password,
                ssl=config.ssl,
                max_connections=config.max_connections,
                max_connections_per_node=config.max_connections_per_node,
                decode_responses=config.decode_responses,
                skip_full_coverage_check=config.skip_full_coverage_check,
            )
            logger.info(f"Connected to Redis Cluster with {len(config.startup_nodes)} startup nodes")
        else:
            # Fall back to single-node Redis with consistent hashing
            self.cache = RedisCache()
            self.hash_ring = None  # Not used in single-node mode
            logger.info("Using single-node Redis (no cluster)")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from distributed cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if self.use_cluster:
            try:
                data = self.cluster.get(key)
                if data:
                    import json
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Cluster GET error: {e}")
                return None
        else:
            return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in distributed cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds

        Returns:
            True if successful
        """
        if self.use_cluster:
            try:
                import json
                data = json.dumps(value)
                if ttl:
                    return bool(self.cluster.setex(key, ttl, data))
                else:
                    return bool(self.cluster.set(key, data))
            except Exception as e:
                logger.error(f"Cluster SET error: {e}")
                return False
        else:
            return self.cache.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """
        Delete key from distributed cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        if self.use_cluster:
            try:
                return bool(self.cluster.delete(key))
            except Exception as e:
                logger.error(f"Cluster DELETE error: {e}")
                return False
        else:
            return self.cache.delete(key)

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern across cluster.

        Args:
            pattern: Redis glob pattern

        Returns:
            Number of keys deleted
        """
        if self.use_cluster:
            try:
                deleted = 0
                # Scan each node in cluster
                for node in self.cluster.connection_pool.nodes.all_nodes():
                    cursor = 0
                    while True:
                        cursor, keys = node.redis_connection.scan(
                            cursor, match=pattern, count=100
                        )
                        if keys:
                            deleted += node.redis_connection.delete(*keys)
                        if cursor == 0:
                            break
                return deleted
            except Exception as e:
                logger.error(f"Cluster INVALIDATE_PATTERN error: {e}")
                return 0
        else:
            return self.cache.delete_pattern(pattern)

    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get cluster information.

        Returns:
            Dictionary of cluster stats
        """
        if self.use_cluster:
            try:
                return {
                    'mode': 'cluster',
                    'nodes': len(self.cluster.connection_pool.nodes.all_nodes()),
                    'info': self.cluster.info(),
                }
            except Exception as e:
                logger.error(f"Cluster INFO error: {e}")
                return {'mode': 'cluster', 'error': str(e)}
        else:
            return {
                'mode': 'single-node',
                'info': self.cache.info(),
            }

    def ping(self) -> bool:
        """
        Ping all cluster nodes.

        Returns:
            True if all nodes are reachable
        """
        if self.use_cluster:
            try:
                return self.cluster.ping()
            except Exception:
                return False
        else:
            return self.cache.ping()

    def close(self):
        """Close all connections"""
        if self.use_cluster:
            # Redis cluster doesn't have explicit close
            pass
        else:
            self.cache.close()


class CacheCoherence:
    """
    Cache coherence protocol for distributed caching.

    Ensures consistency across multiple cache nodes when
    data is updated.
    """

    def __init__(self, cache: DistributedCache):
        """
        Initialize cache coherence manager.

        Args:
            cache: DistributedCache instance
        """
        self.cache = cache

    def invalidate_on_write(self, key: str):
        """
        Invalidate cache entry on write (invalidate protocol).

        Args:
            key: Cache key that was written to
        """
        self.cache.delete(key)
        logger.debug(f"Invalidated cache key: {key}")

    def update_on_write(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Update cache on write (update protocol).

        Args:
            key: Cache key
            value: New value
            ttl: Optional TTL
        """
        self.cache.set(key, value, ttl)
        logger.debug(f"Updated cache key: {key}")

    def broadcast_invalidation(self, pattern: str):
        """
        Broadcast invalidation to all nodes.

        Args:
            pattern: Pattern to invalidate
        """
        deleted = self.cache.invalidate_pattern(pattern)
        logger.info(f"Broadcast invalidation: {pattern} ({deleted} keys)")

    def write_through(self, key: str, value: Any, db_writer: callable,
                     ttl: Optional[int] = None) -> bool:
        """
        Write-through: Update both cache and database atomically.

        Args:
            key: Cache key
            value: Value to write
            db_writer: Function to write to database
            ttl: Optional cache TTL

        Returns:
            True if successful
        """
        try:
            # Write to database first
            db_writer(value)

            # Then update cache
            self.cache.set(key, value, ttl)

            return True
        except Exception as e:
            logger.error(f"Write-through error: {e}")
            # On failure, invalidate cache to maintain consistency
            self.cache.delete(key)
            return False

    def read_through(self, key: str, db_reader: callable,
                    ttl: Optional[int] = None) -> Optional[Any]:
        """
        Read-through: Check cache first, fall back to database.

        Args:
            key: Cache key
            db_reader: Function to read from database
            ttl: Optional cache TTL

        Returns:
            Value from cache or database
        """
        # Try cache first
        value = self.cache.get(key)
        if value is not None:
            return value

        # Fall back to database
        try:
            value = db_reader()
            if value is not None:
                # Populate cache
                self.cache.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Read-through DB error: {e}")
            return None

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
