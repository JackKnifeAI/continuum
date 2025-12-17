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
Caching Strategies

LRU eviction, TTL-based expiration, and preemptive refresh strategies
for optimal cache performance.

Strategies:
    - LRU (Least Recently Used): Evict oldest unused items
    - TTL (Time To Live): Expire items after time limit
    - Preemptive Refresh: Refresh before expiration
    - Adaptive TTL: Adjust TTL based on access patterns
"""

import time
import math
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[int] = None

    @property
    def age(self) -> float:
        """Age in seconds"""
        return time.time() - self.created_at

    @property
    def time_since_access(self) -> float:
        """Time since last access in seconds"""
        return time.time() - self.last_accessed

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return self.age >= self.ttl

    @property
    def expiry_ratio(self) -> float:
        """Ratio of age to TTL (1.0 = expired)"""
        if self.ttl is None:
            return 0.0
        return self.age / self.ttl

    def touch(self):
        """Mark entry as accessed"""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheStrategy(ABC):
    """Base class for caching strategies"""

    @abstractmethod
    def should_evict(self, entry: CacheEntry) -> bool:
        """
        Determine if entry should be evicted.

        Args:
            entry: Cache entry to check

        Returns:
            True if should evict
        """
        pass

    @abstractmethod
    def select_eviction_candidates(self, entries: List[CacheEntry],
                                   count: int) -> List[CacheEntry]:
        """
        Select entries to evict.

        Args:
            entries: List of cache entries
            count: Number to evict

        Returns:
            List of entries to evict
        """
        pass

    @abstractmethod
    def calculate_ttl(self, entry: CacheEntry) -> int:
        """
        Calculate TTL for an entry.

        Args:
            entry: Cache entry

        Returns:
            TTL in seconds
        """
        pass


class LRUStrategy(CacheStrategy):
    """
    Least Recently Used eviction strategy.

    Evicts entries that haven't been accessed recently.
    """

    def __init__(self, max_age: int = 3600):
        """
        Initialize LRU strategy.

        Args:
            max_age: Maximum age before considering for eviction (seconds)
        """
        self.max_age = max_age

    def should_evict(self, entry: CacheEntry) -> bool:
        """Evict if not accessed recently"""
        return entry.time_since_access > self.max_age

    def select_eviction_candidates(self, entries: List[CacheEntry],
                                   count: int) -> List[CacheEntry]:
        """Select least recently accessed entries"""
        # Sort by last access time (oldest first)
        sorted_entries = sorted(entries, key=lambda e: e.last_accessed)
        return sorted_entries[:count]

    def calculate_ttl(self, entry: CacheEntry) -> int:
        """Use fixed TTL"""
        return self.max_age


class TTLStrategy(CacheStrategy):
    """
    Time To Live expiration strategy.

    Entries expire after a fixed time period.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize TTL strategy.

        Args:
            default_ttl: Default TTL in seconds
        """
        self.default_ttl = default_ttl

    def should_evict(self, entry: CacheEntry) -> bool:
        """Evict if expired"""
        return entry.is_expired

    def select_eviction_candidates(self, entries: List[CacheEntry],
                                   count: int) -> List[CacheEntry]:
        """Select oldest entries"""
        # Sort by age (oldest first)
        sorted_entries = sorted(entries, key=lambda e: e.age, reverse=True)
        return sorted_entries[:count]

    def calculate_ttl(self, entry: CacheEntry) -> int:
        """Use default TTL"""
        return self.default_ttl


class PreemptiveRefreshStrategy(CacheStrategy):
    """
    Preemptive refresh strategy.

    Refreshes entries before they expire to avoid cache misses.
    """

    def __init__(self, default_ttl: int = 300, refresh_threshold: float = 0.8):
        """
        Initialize preemptive refresh strategy.

        Args:
            default_ttl: Default TTL in seconds
            refresh_threshold: Refresh when expiry_ratio exceeds this (0.0-1.0)
        """
        self.default_ttl = default_ttl
        self.refresh_threshold = refresh_threshold

    def should_refresh(self, entry: CacheEntry) -> bool:
        """
        Check if entry should be refreshed.

        Args:
            entry: Cache entry

        Returns:
            True if should refresh
        """
        return entry.expiry_ratio >= self.refresh_threshold

    def should_evict(self, entry: CacheEntry) -> bool:
        """Evict if expired"""
        return entry.is_expired

    def select_eviction_candidates(self, entries: List[CacheEntry],
                                   count: int) -> List[CacheEntry]:
        """Select entries closest to expiration"""
        # Sort by expiry ratio (closest to expiration first)
        sorted_entries = sorted(entries,
                              key=lambda e: e.expiry_ratio if e.ttl else 0,
                              reverse=True)
        return sorted_entries[:count]

    def calculate_ttl(self, entry: CacheEntry) -> int:
        """Use default TTL"""
        return self.default_ttl

    def select_refresh_candidates(self, entries: List[CacheEntry],
                                  max_count: int = 10) -> List[CacheEntry]:
        """
        Select entries for preemptive refresh.

        Args:
            entries: List of cache entries
            max_count: Maximum entries to refresh

        Returns:
            List of entries to refresh
        """
        candidates = [e for e in entries if self.should_refresh(e)]
        # Prioritize by access count (refresh hot entries first)
        candidates.sort(key=lambda e: e.access_count, reverse=True)
        return candidates[:max_count]


class AdaptiveTTLStrategy(CacheStrategy):
    """
    Adaptive TTL strategy.

    Adjusts TTL based on access patterns:
    - Frequently accessed: longer TTL
    - Rarely accessed: shorter TTL
    """

    def __init__(self, min_ttl: int = 60, max_ttl: int = 3600,
                 base_ttl: int = 300):
        """
        Initialize adaptive TTL strategy.

        Args:
            min_ttl: Minimum TTL in seconds
            max_ttl: Maximum TTL in seconds
            base_ttl: Base TTL for new entries
        """
        self.min_ttl = min_ttl
        self.max_ttl = max_ttl
        self.base_ttl = base_ttl

    def should_evict(self, entry: CacheEntry) -> bool:
        """Evict if expired"""
        return entry.is_expired

    def select_eviction_candidates(self, entries: List[CacheEntry],
                                   count: int) -> List[CacheEntry]:
        """Select least valuable entries (low access count, old age)"""
        # Calculate score: access_count / age (higher is better)
        def score(e: CacheEntry) -> float:
            if e.age == 0:
                return float('inf')
            return e.access_count / e.age

        sorted_entries = sorted(entries, key=score)
        return sorted_entries[:count]

    def calculate_ttl(self, entry: CacheEntry) -> int:
        """
        Calculate adaptive TTL based on access patterns.

        Formula:
            ttl = base_ttl * log(1 + access_count)
            Clamped to [min_ttl, max_ttl]
        """
        if entry.access_count == 0:
            return self.base_ttl

        # Logarithmic scaling based on access count
        multiplier = math.log(1 + entry.access_count)
        ttl = int(self.base_ttl * multiplier)

        # Clamp to bounds
        return max(self.min_ttl, min(self.max_ttl, ttl))


class HybridStrategy(CacheStrategy):
    """
    Hybrid strategy combining multiple approaches.

    Uses LRU for cold entries and adaptive TTL for hot entries.
    """

    def __init__(self, hot_threshold: int = 10, cold_ttl: int = 300,
                 hot_min_ttl: int = 600, hot_max_ttl: int = 3600):
        """
        Initialize hybrid strategy.

        Args:
            hot_threshold: Access count threshold for "hot" entries
            cold_ttl: TTL for cold entries
            hot_min_ttl: Minimum TTL for hot entries
            hot_max_ttl: Maximum TTL for hot entries
        """
        self.hot_threshold = hot_threshold
        self.cold_ttl = cold_ttl
        self.lru = LRUStrategy(max_age=cold_ttl)
        self.adaptive = AdaptiveTTLStrategy(
            min_ttl=hot_min_ttl,
            max_ttl=hot_max_ttl,
            base_ttl=hot_min_ttl
        )

    def is_hot(self, entry: CacheEntry) -> bool:
        """
        Check if entry is "hot" (frequently accessed).

        Args:
            entry: Cache entry

        Returns:
            True if hot
        """
        return entry.access_count >= self.hot_threshold

    def should_evict(self, entry: CacheEntry) -> bool:
        """Use LRU for cold, adaptive for hot"""
        if self.is_hot(entry):
            return self.adaptive.should_evict(entry)
        else:
            return self.lru.should_evict(entry)

    def select_eviction_candidates(self, entries: List[CacheEntry],
                                   count: int) -> List[CacheEntry]:
        """Prioritize evicting cold entries"""
        cold = [e for e in entries if not self.is_hot(e)]
        hot = [e for e in entries if self.is_hot(e)]

        # Evict cold entries first
        candidates = self.lru.select_eviction_candidates(cold, count)

        # If need more, evict hot entries
        if len(candidates) < count:
            remaining = count - len(candidates)
            candidates.extend(
                self.adaptive.select_eviction_candidates(hot, remaining)
            )

        return candidates

    def calculate_ttl(self, entry: CacheEntry) -> int:
        """Use short TTL for cold, adaptive for hot"""
        if self.is_hot(entry):
            return self.adaptive.calculate_ttl(entry)
        else:
            return self.cold_ttl


class StrategyManager:
    """
    Manages caching strategy for a cache instance.

    Applies strategy to make eviction and TTL decisions.
    """

    def __init__(self, strategy: CacheStrategy):
        """
        Initialize strategy manager.

        Args:
            strategy: Caching strategy to use
        """
        self.strategy = strategy
        self.entries: Dict[str, CacheEntry] = {}

    def on_access(self, key: str):
        """
        Record cache access.

        Args:
            key: Cache key accessed
        """
        if key in self.entries:
            self.entries[key].touch()

    def on_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Record cache set operation.

        Args:
            key: Cache key
            value: Value stored
            ttl: Optional TTL override
        """
        now = time.time()

        if key in self.entries:
            entry = self.entries[key]
            entry.value = value
            entry.created_at = now
            entry.last_accessed = now
            if ttl is not None:
                entry.ttl = ttl
        else:
            calculated_ttl = ttl if ttl is not None else self.strategy.calculate_ttl(
                CacheEntry(key, value, now, now)
            )
            self.entries[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                ttl=calculated_ttl
            )

    def on_delete(self, key: str):
        """
        Record cache delete operation.

        Args:
            key: Cache key deleted
        """
        if key in self.entries:
            del self.entries[key]

    def get_eviction_candidates(self, count: int) -> List[str]:
        """
        Get keys to evict.

        Args:
            count: Number of keys to evict

        Returns:
            List of cache keys to evict
        """
        entries = list(self.entries.values())
        candidates = self.strategy.select_eviction_candidates(entries, count)
        return [e.key for e in candidates]

    def get_expired_keys(self) -> List[str]:
        """
        Get all expired keys.

        Returns:
            List of expired cache keys
        """
        expired = []
        for key, entry in self.entries.items():
            if self.strategy.should_evict(entry):
                expired.append(key)
        return expired

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        expired = self.get_expired_keys()
        for key in expired:
            del self.entries[key]
        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get strategy statistics.

        Returns:
            Dictionary of statistics
        """
        entries = list(self.entries.values())

        if not entries:
            return {
                'total_entries': 0,
                'hot_entries': 0,
                'cold_entries': 0,
                'avg_age': 0,
                'avg_access_count': 0,
            }

        hot_threshold = getattr(self.strategy, 'hot_threshold', 10)
        hot = [e for e in entries if e.access_count >= hot_threshold]
        cold = [e for e in entries if e.access_count < hot_threshold]

        return {
            'total_entries': len(entries),
            'hot_entries': len(hot),
            'cold_entries': len(cold),
            'avg_age': sum(e.age for e in entries) / len(entries),
            'avg_access_count': sum(e.access_count for e in entries) / len(entries),
            'oldest_entry': max(e.age for e in entries),
            'newest_entry': min(e.age for e in entries),
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
