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
Redis Client Wrapper

Provides connection pooling, automatic serialization, TTL management,
and cache invalidation patterns.

Features:
    - Connection pooling (reduces overhead)
    - Automatic JSON/MessagePack serialization
    - TTL management with automatic expiration
    - Cache invalidation patterns (tags, wildcards)
    - Redis AUTH and TLS support
    - Health checks and failover
"""

import redis
import json
import hashlib
from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

# Try to use faster MessagePack if available
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False


@dataclass
class RedisCacheConfig:
    """Configuration for Redis cache"""

    # Connection
    host: str = "localhost"
    port: int = 6379
    db: int = 0

    # Security
    password: Optional[str] = None
    username: Optional[str] = None
    ssl: bool = False
    ssl_cert_reqs: str = "required"
    ssl_ca_certs: Optional[str] = None

    # Pool settings
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True

    # Behavior
    decode_responses: bool = False  # We handle encoding
    health_check_interval: int = 30

    # Default TTL (seconds)
    default_ttl: int = 300  # 5 minutes

    # Serialization
    use_msgpack: bool = MSGPACK_AVAILABLE

    @classmethod
    def from_env(cls) -> 'RedisCacheConfig':
        """
        Load configuration from environment variables.

        Environment variables:
            REDIS_HOST: Redis server host
            REDIS_PORT: Redis server port
            REDIS_PASSWORD: Redis password
            REDIS_DB: Redis database number
            REDIS_SSL: Enable SSL (true/false)
            REDIS_MAX_CONNECTIONS: Max pool connections

        Returns:
            RedisCacheConfig instance
        """
        return cls(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            db=int(os.environ.get("REDIS_DB", "0")),
            password=os.environ.get("REDIS_PASSWORD"),
            username=os.environ.get("REDIS_USERNAME"),
            ssl=os.environ.get("REDIS_SSL", "").lower() == "true",
            max_connections=int(os.environ.get("REDIS_MAX_CONNECTIONS", "50")),
        )

    def to_redis_kwargs(self) -> Dict[str, Any]:
        """Convert to redis-py connection kwargs"""
        kwargs = {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'socket_keepalive': self.socket_keepalive,
            'health_check_interval': self.health_check_interval,
            'decode_responses': self.decode_responses,
        }

        if self.password:
            kwargs['password'] = self.password
        if self.username:
            kwargs['username'] = self.username
        if self.ssl:
            kwargs['ssl'] = True
            kwargs['ssl_cert_reqs'] = self.ssl_cert_reqs
            if self.ssl_ca_certs:
                kwargs['ssl_ca_certs'] = self.ssl_ca_certs

        return kwargs


class RedisCache:
    """
    Redis client wrapper with connection pooling and serialization.

    Handles connection management, serialization/deserialization,
    and provides high-level caching primitives.
    """

    def __init__(self, config: Optional[RedisCacheConfig] = None):
        """
        Initialize Redis cache.

        Args:
            config: Optional configuration (uses environment if not provided)
        """
        self.config = config or RedisCacheConfig.from_env()

        # Create connection pool
        self.pool = redis.ConnectionPool(
            max_connections=self.config.max_connections,
            **self.config.to_redis_kwargs()
        )

        # Create client
        self.client = redis.Redis(connection_pool=self.pool)

        # Test connection
        try:
            self.client.ping()
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value for storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes
        """
        if self.config.use_msgpack and MSGPACK_AVAILABLE:
            return msgpack.packb(value, use_bin_type=True)
        else:
            return json.dumps(value).encode('utf-8')

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize value from storage.

        Args:
            data: Serialized bytes

        Returns:
            Deserialized value
        """
        if self.config.use_msgpack and MSGPACK_AVAILABLE:
            return msgpack.unpackb(data, raw=False)
        else:
            return json.loads(data.decode('utf-8'))

    def _make_key(self, *parts: str) -> str:
        """
        Create a cache key from parts.

        Args:
            *parts: Key components

        Returns:
            Formatted cache key
        """
        return ":".join(str(p) for p in parts)

    def _hash_key(self, key: str) -> str:
        """
        Hash a key for security (e.g., tenant IDs).

        Args:
            key: Key to hash

        Returns:
            Hashed key
        """
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            data = self.client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not specified)

        Returns:
            True if successful, False otherwise
        """
        try:
            data = self._serialize(value)
            ttl = ttl or self.config.default_ttl

            if ttl:
                return bool(self.client.setex(key, ttl, data))
            else:
                return bool(self.client.set(key, data))
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis glob pattern (e.g., "user:*:sessions")

        Returns:
            Number of keys deleted
        """
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += self.client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as e:
            logger.error(f"Cache DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """
        Set TTL on existing key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache EXPIRE error for key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None on error
        """
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache INCREMENT error for key {key}: {e}")
            return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrement a counter.

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value or None on error
        """
        try:
            return self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Cache DECREMENT error for key {key}: {e}")
            return None

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values at once.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key -> value (only includes found keys)
        """
        try:
            if not keys:
                return {}

            values = self.client.mget(keys)
            result = {}
            for key, data in zip(keys, values):
                if data is not None:
                    try:
                        result[key] = self._deserialize(data)
                    except Exception:
                        pass
            return result
        except Exception as e:
            logger.error(f"Cache GET_MANY error: {e}")
            return {}

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values at once.

        Args:
            mapping: Dictionary of key -> value
            ttl: Optional TTL for all keys

        Returns:
            True if successful, False otherwise
        """
        try:
            if not mapping:
                return True

            # Serialize all values
            serialized = {k: self._serialize(v) for k, v in mapping.items()}

            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            pipe.mset(serialized)

            # Set TTL if specified
            if ttl:
                for key in serialized.keys():
                    pipe.expire(key, ttl)

            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Cache SET_MANY error: {e}")
            return False

    def flush(self) -> bool:
        """
        Flush entire database (use with caution!).

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.flushdb()
            logger.warning("Redis database flushed")
            return True
        except Exception as e:
            logger.error(f"Cache FLUSH error: {e}")
            return False

    def ping(self) -> bool:
        """
        Check if Redis is reachable.

        Returns:
            True if reachable, False otherwise
        """
        try:
            return self.client.ping()
        except Exception:
            return False

    def info(self) -> Dict[str, Any]:
        """
        Get Redis server info.

        Returns:
            Dictionary of server statistics
        """
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Cache INFO error: {e}")
            return {}

    def close(self):
        """Close connection pool"""
        self.pool.disconnect()
        logger.info("Redis connection pool closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
