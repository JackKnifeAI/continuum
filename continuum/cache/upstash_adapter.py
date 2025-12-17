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
Upstash Redis Adapter

Serverless Redis adapter using Upstash's REST API or traditional Redis protocol.
Supports both REST mode (for Cloudflare Workers, AWS Lambda) and connection
pooling mode (for containerized applications).

Features:
    - REST API mode for serverless environments
    - Traditional Redis mode with connection pooling
    - Automatic failover to local in-memory cache
    - Rate limiting with sliding window
    - Pub/sub for WebSocket coordination
    - Regional and global database support
    - Cost-optimized with batching and compression

Usage:
    # REST mode (serverless)
    cache = UpstashCache(mode="rest")

    # Redis mode (traditional)
    cache = UpstashCache(mode="redis", pool_size=10)

    # With automatic fallback
    cache = UpstashCache(fallback=True)
"""

import os
import time
import json
import hashlib
import logging
from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import upstash-redis for REST mode
try:
    from upstash_redis import Redis as UpstashRedis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    logger.warning("upstash-redis not available. Install with: pip install upstash-redis")

# Try to import redis-py for traditional mode
try:
    import redis
    REDIS_PY_AVAILABLE = True
except ImportError:
    REDIS_PY_AVAILABLE = False
    logger.warning("redis not available. Install with: pip install redis")

# Try to import MessagePack for compression
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False


class ConnectionMode(Enum):
    """Redis connection mode"""
    REST = "rest"  # HTTP REST API (serverless-friendly)
    REDIS = "redis"  # Traditional Redis protocol (connection pooling)
    AUTO = "auto"  # Auto-detect based on environment


class CacheBackend(Enum):
    """Current cache backend"""
    UPSTASH = "upstash"
    LOCAL = "local"
    NONE = "none"


@dataclass
class UpstashConfig:
    """Configuration for Upstash Redis"""

    # Connection mode
    mode: ConnectionMode = ConnectionMode.AUTO

    # REST mode configuration
    rest_url: Optional[str] = None
    rest_token: Optional[str] = None

    # Redis mode configuration
    redis_url: Optional[str] = None
    pool_size: int = 10

    # Common configuration
    timeout_ms: int = 5000
    retry_max_attempts: int = 3
    retry_backoff_ms: int = 100
    retry_backoff_multiplier: float = 2.0

    # Serialization
    use_msgpack: bool = MSGPACK_AVAILABLE

    # Default TTL
    default_ttl: int = 300  # 5 minutes

    # Fallback configuration
    fallback_enabled: bool = True
    health_check_interval: int = 30

    # Regional configuration
    region: Optional[str] = None
    enable_telemetry: bool = False

    @classmethod
    def from_env(cls) -> 'UpstashConfig':
        """
        Load configuration from environment variables.

        Environment variables:
            UPSTASH_REDIS_REST_URL: REST API endpoint
            UPSTASH_REDIS_REST_TOKEN: REST API token
            UPSTASH_REDIS_URL: Traditional Redis URL
            CONTINUUM_CACHE_MODE: Connection mode (rest/redis/auto)
            CONTINUUM_CACHE_FALLBACK: Enable fallback (true/false)
            UPSTASH_ENABLE_TELEMETRY: Enable telemetry (true/false)

        Returns:
            UpstashConfig instance
        """
        mode_str = os.environ.get("CONTINUUM_CACHE_MODE", "auto")
        mode = ConnectionMode(mode_str) if mode_str in ["rest", "redis", "auto"] else ConnectionMode.AUTO

        return cls(
            mode=mode,
            rest_url=os.environ.get("UPSTASH_REDIS_REST_URL"),
            rest_token=os.environ.get("UPSTASH_REDIS_REST_TOKEN"),
            redis_url=os.environ.get("UPSTASH_REDIS_URL"),
            pool_size=int(os.environ.get("UPSTASH_POOL_SIZE", "10")),
            fallback_enabled=os.environ.get("CONTINUUM_CACHE_FALLBACK", "true").lower() == "true",
            enable_telemetry=os.environ.get("UPSTASH_ENABLE_TELEMETRY", "false").lower() == "true",
        )


class LocalCache:
    """Simple in-memory cache for fallback"""

    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}  # key -> (value, expiry)

    def get(self, key: str) -> Optional[Any]:
        """Get value from local cache"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry == 0 or time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in local cache"""
        expiry = time.time() + ttl if ttl else 0
        self._cache[key] = (value, expiry)
        return True

    def delete(self, key: str) -> bool:
        """Delete key from local cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self.get(key) is not None

    def clear(self):
        """Clear all cached data"""
        self._cache.clear()


class UpstashCache:
    """
    Upstash Redis adapter with automatic failover.

    Supports both REST mode (serverless) and traditional Redis mode
    (connection pooling) with automatic fallback to local cache.
    """

    def __init__(
        self,
        config: Optional[UpstashConfig] = None,
        mode: Optional[str] = None,
        fallback: Optional[bool] = None,
        **kwargs
    ):
        """
        Initialize Upstash cache.

        Args:
            config: Optional configuration (uses environment if not provided)
            mode: Override connection mode ("rest", "redis", "auto")
            fallback: Override fallback setting
            **kwargs: Additional configuration options
        """
        self.config = config or UpstashConfig.from_env()

        # Override mode if specified
        if mode:
            self.config.mode = ConnectionMode(mode)

        # Override fallback if specified
        if fallback is not None:
            self.config.fallback_enabled = fallback

        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Initialize clients
        self.client: Optional[Any] = None
        self.local_cache = LocalCache()
        self.current_backend = CacheBackend.NONE
        self.last_health_check = 0

        # Connect to Upstash
        self._connect()

    def _connect(self):
        """Connect to Upstash Redis"""
        # Determine connection mode
        mode = self.config.mode
        if mode == ConnectionMode.AUTO:
            # Auto-detect based on available credentials
            if self.config.rest_url and self.config.rest_token:
                mode = ConnectionMode.REST
            elif self.config.redis_url:
                mode = ConnectionMode.REDIS
            else:
                logger.warning("No Upstash credentials found. Using local cache only.")
                self.current_backend = CacheBackend.LOCAL
                return

        # Connect in REST mode
        if mode == ConnectionMode.REST:
            if not UPSTASH_AVAILABLE:
                logger.error("upstash-redis package not installed")
                if self.config.fallback_enabled:
                    self.current_backend = CacheBackend.LOCAL
                    logger.info("Using local cache fallback")
                return

            if not self.config.rest_url or not self.config.rest_token:
                logger.error("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN required for REST mode")
                if self.config.fallback_enabled:
                    self.current_backend = CacheBackend.LOCAL
                    logger.info("Using local cache fallback")
                return

            try:
                self.client = UpstashRedis(
                    url=self.config.rest_url,
                    token=self.config.rest_token,
                )
                # Test connection
                self.client.ping()
                self.current_backend = CacheBackend.UPSTASH
                logger.info(f"Connected to Upstash Redis (REST mode): {self.config.rest_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Upstash (REST): {e}")
                if self.config.fallback_enabled:
                    self.current_backend = CacheBackend.LOCAL
                    logger.info("Using local cache fallback")

        # Connect in Redis mode
        elif mode == ConnectionMode.REDIS:
            if not REDIS_PY_AVAILABLE:
                logger.error("redis package not installed")
                if self.config.fallback_enabled:
                    self.current_backend = CacheBackend.LOCAL
                    logger.info("Using local cache fallback")
                return

            if not self.config.redis_url:
                logger.error("UPSTASH_REDIS_URL required for Redis mode")
                if self.config.fallback_enabled:
                    self.current_backend = CacheBackend.LOCAL
                    logger.info("Using local cache fallback")
                return

            try:
                pool = redis.ConnectionPool.from_url(
                    self.config.redis_url,
                    max_connections=self.config.pool_size,
                    socket_timeout=self.config.timeout_ms / 1000,
                    socket_connect_timeout=self.config.timeout_ms / 1000,
                    socket_keepalive=True,
                    health_check_interval=self.config.health_check_interval,
                )
                self.client = redis.Redis(connection_pool=pool, decode_responses=False)
                # Test connection
                self.client.ping()
                self.current_backend = CacheBackend.UPSTASH
                logger.info(f"Connected to Upstash Redis (Redis mode): {self.config.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Upstash (Redis): {e}")
                if self.config.fallback_enabled:
                    self.current_backend = CacheBackend.LOCAL
                    logger.info("Using local cache fallback")

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if self.config.use_msgpack and MSGPACK_AVAILABLE:
            return msgpack.packb(value, use_bin_type=True)
        else:
            return json.dumps(value).encode('utf-8')

    def _deserialize(self, data: Union[bytes, str]) -> Any:
        """Deserialize value from storage"""
        if isinstance(data, str):
            data = data.encode('utf-8')

        if self.config.use_msgpack and MSGPACK_AVAILABLE:
            try:
                return msgpack.unpackb(data, raw=False)
            except Exception:
                # Fallback to JSON if msgpack fails
                return json.loads(data.decode('utf-8'))
        else:
            return json.loads(data.decode('utf-8'))

    def _health_check(self):
        """Periodic health check for Upstash"""
        now = time.time()
        if now - self.last_health_check < self.config.health_check_interval:
            return

        self.last_health_check = now

        # If using local cache, try to reconnect to Upstash
        if self.current_backend == CacheBackend.LOCAL and self.config.fallback_enabled:
            try:
                if self.client is None:
                    self._connect()
                elif hasattr(self.client, 'ping') and self.client.ping():
                    self.current_backend = CacheBackend.UPSTASH
                    logger.info("Reconnected to Upstash")
            except Exception:
                pass  # Still unavailable

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                data = self.client.get(key)
                if data is None:
                    return None
                return self._deserialize(data)
            except Exception as e:
                logger.error(f"Upstash GET error for key {key}: {e}")
                if self.config.fallback_enabled:
                    logger.info("Falling back to local cache")
                    self.current_backend = CacheBackend.LOCAL
                return None

        elif self.current_backend == CacheBackend.LOCAL:
            return self.local_cache.get(key)

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
        self._health_check()

        ttl = ttl or self.config.default_ttl

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                data = self._serialize(value)
                if ttl:
                    result = self.client.setex(key, ttl, data)
                else:
                    result = self.client.set(key, data)
                return bool(result)
            except Exception as e:
                logger.error(f"Upstash SET error for key {key}: {e}")
                if self.config.fallback_enabled:
                    logger.info("Falling back to local cache")
                    self.current_backend = CacheBackend.LOCAL
                    return self.local_cache.set(key, value, ttl)
                return False

        elif self.current_backend == CacheBackend.LOCAL:
            return self.local_cache.set(key, value, ttl)

        return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                return bool(self.client.delete(key))
            except Exception as e:
                logger.error(f"Upstash DELETE error for key {key}: {e}")
                return False

        elif self.current_backend == CacheBackend.LOCAL:
            return self.local_cache.delete(key)

        return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis glob pattern (e.g., "user:*:sessions")

        Returns:
            Number of keys deleted
        """
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                # Scan for keys matching pattern
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
                logger.error(f"Upstash DELETE_PATTERN error for pattern {pattern}: {e}")
                return 0

        elif self.current_backend == CacheBackend.LOCAL:
            # Simple pattern matching for local cache
            import fnmatch
            deleted = 0
            keys_to_delete = [k for k in self.local_cache._cache.keys() if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_delete:
                if self.local_cache.delete(key):
                    deleted += 1
            return deleted

        return 0

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                return bool(self.client.exists(key))
            except Exception as e:
                logger.error(f"Upstash EXISTS error for key {key}: {e}")
                return False

        elif self.current_backend == CacheBackend.LOCAL:
            return self.local_cache.exists(key)

        return False

    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key"""
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                return bool(self.client.expire(key, ttl))
            except Exception as e:
                logger.error(f"Upstash EXPIRE error for key {key}: {e}")
                return False

        elif self.current_backend == CacheBackend.LOCAL:
            # For local cache, re-set with new TTL
            value = self.local_cache.get(key)
            if value is not None:
                return self.local_cache.set(key, value, ttl)
            return False

        return False

    def ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                return self.client.ttl(key)
            except Exception as e:
                logger.error(f"Upstash TTL error for key {key}: {e}")
                return -2

        elif self.current_backend == CacheBackend.LOCAL:
            if key in self.local_cache._cache:
                _, expiry = self.local_cache._cache[key]
                if expiry == 0:
                    return -1
                remaining = int(expiry - time.time())
                return max(remaining, 0)
            return -2

        return -2

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                return self.client.incrby(key, amount)
            except Exception as e:
                logger.error(f"Upstash INCREMENT error for key {key}: {e}")
                return None

        elif self.current_backend == CacheBackend.LOCAL:
            current = self.local_cache.get(key) or 0
            new_value = current + amount
            self.local_cache.set(key, new_value)
            return new_value

        return None

    def pipeline(self):
        """Create a pipeline for batch operations"""
        if self.current_backend == CacheBackend.UPSTASH and hasattr(self.client, 'pipeline'):
            return self.client.pipeline()
        else:
            # Return a mock pipeline for local cache
            return MockPipeline(self)

    def publish(self, channel: str, message: Any):
        """Publish message to pub/sub channel"""
        self._health_check()

        if self.current_backend == CacheBackend.UPSTASH:
            try:
                serialized = self._serialize(message)
                return self.client.publish(channel, serialized)
            except Exception as e:
                logger.error(f"Upstash PUBLISH error for channel {channel}: {e}")
                return 0

        # Local cache doesn't support pub/sub
        return 0

    def pubsub(self):
        """Create pub/sub client"""
        if self.current_backend == CacheBackend.UPSTASH and hasattr(self.client, 'pubsub'):
            return self.client.pubsub()
        return None

    def ping(self) -> bool:
        """Check if cache is reachable"""
        if self.current_backend == CacheBackend.UPSTASH:
            try:
                return bool(self.client.ping())
            except Exception:
                return False
        elif self.current_backend == CacheBackend.LOCAL:
            return True
        return False

    def info(self) -> Dict[str, Any]:
        """Get cache information"""
        if self.current_backend == CacheBackend.UPSTASH and hasattr(self.client, 'info'):
            try:
                return self.client.info()
            except Exception:
                return {}
        elif self.current_backend == CacheBackend.LOCAL:
            return {
                'backend': 'local',
                'keys': len(self.local_cache._cache),
            }
        return {}

    def flush(self) -> bool:
        """Flush all keys (use with caution!)"""
        if self.current_backend == CacheBackend.UPSTASH:
            try:
                self.client.flushdb()
                return True
            except Exception as e:
                logger.error(f"Upstash FLUSH error: {e}")
                return False
        elif self.current_backend == CacheBackend.LOCAL:
            self.local_cache.clear()
            return True
        return False

    def close(self):
        """Close connection"""
        if self.client and hasattr(self.client, 'close'):
            self.client.close()


class MockPipeline:
    """Mock pipeline for local cache (batch operations not atomic)"""

    def __init__(self, cache: UpstashCache):
        self.cache = cache
        self.commands = []

    def set(self, key: str, value: Any, ex: Optional[int] = None):
        self.commands.append(('set', key, value, ex))
        return self

    def setex(self, key: str, ttl: int, value: Any):
        self.commands.append(('set', key, value, ttl))
        return self

    def delete(self, *keys: str):
        for key in keys:
            self.commands.append(('delete', key))
        return self

    def expire(self, key: str, ttl: int):
        self.commands.append(('expire', key, ttl))
        return self

    def execute(self):
        results = []
        for cmd in self.commands:
            if cmd[0] == 'set':
                _, key, value, ttl = cmd
                results.append(self.cache.set(key, value, ttl))
            elif cmd[0] == 'delete':
                _, key = cmd
                results.append(self.cache.delete(key))
            elif cmd[0] == 'expire':
                _, key, ttl = cmd
                results.append(self.cache.expire(key, ttl))
        self.commands.clear()
        return results


class RateLimiter:
    """
    Rate limiter using sliding window algorithm.

    Uses Redis sorted sets to track requests within time windows.
    """

    def __init__(self, cache: UpstashCache):
        self.cache = cache

    def check_rate_limit(
        self,
        identifier: str,
        window_seconds: int = 60,
        max_requests: int = 100
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            window_seconds: Time window in seconds
            max_requests: Max requests allowed in window

        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        window_start = now - window_seconds
        key = f"ratelimit:{identifier}:{window_seconds}"

        # Clean up old entries and count current
        try:
            # Remove old entries
            self.cache.client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            current_count = self.cache.client.zcard(key)

            if current_count >= max_requests:
                return False

            # Add current request
            self.cache.client.zadd(key, {str(now): now})

            # Set expiry
            self.cache.expire(key, window_seconds + 1)

            return True

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open (allow request) on error
            return True

    def get_usage(self, identifier: str, window_seconds: int = 60) -> Dict[str, int]:
        """
        Get current rate limit usage.

        Args:
            identifier: Unique identifier
            window_seconds: Time window in seconds

        Returns:
            Dictionary with 'current' count
        """
        now = time.time()
        window_start = now - window_seconds
        key = f"ratelimit:{identifier}:{window_seconds}"

        try:
            # Remove old entries
            self.cache.client.zremrangebyscore(key, 0, window_start)
            # Count current
            current = self.cache.client.zcard(key)
            return {'current': current}
        except Exception:
            return {'current': 0}

    def reset(self, identifier: str, window_seconds: int = 60):
        """Reset rate limit for identifier"""
        key = f"ratelimit:{identifier}:{window_seconds}"
        self.cache.delete(key)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
