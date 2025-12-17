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
Multi-Master Replication
========================

CRDT-based multi-master replication for CONTINUUM federation.
Enables multiple nodes to accept writes while maintaining eventual consistency.

Conflict-free Replicated Data Types (CRDTs):
- LWW-Register: Last-Write-Wins for simple values
- OR-Set: Observed-Remove Set for collections
- PN-Counter: Positive-Negative Counter for numeric values
- Version Vectors: For causal ordering

References:
- CRDT Paper: https://hal.inria.fr/hal-00932836/document
- Riak implementation: https://github.com/basho/riak_dt
"""

import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving write conflicts"""
    LAST_WRITE_WINS = "last_write_wins"  # LWW based on timestamp
    HIGHEST_NODE_WINS = "highest_node_wins"  # Deterministic node ID ordering
    MERGE_UNION = "merge_union"  # Merge sets via union
    CUSTOM = "custom"  # User-provided resolution


@dataclass
class VectorClock:
    """
    Vector clock for causal ordering.

    Tracks logical time for each node to determine causality and conflicts.
    """
    clocks: Dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str):
        """Increment clock for a node"""
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1

    def update(self, other: 'VectorClock'):
        """Merge with another vector clock (take max of each component)"""
        for node_id, clock in other.clocks.items():
            self.clocks[node_id] = max(self.clocks.get(node_id, 0), clock)

    def compare(self, other: 'VectorClock') -> str:
        """
        Compare two vector clocks.

        Returns:
            'before': self happened before other
            'after': self happened after other
            'concurrent': self and other are concurrent (conflict)
        """
        self_greater = False
        other_greater = False

        all_nodes = set(self.clocks.keys()) | set(other.clocks.keys())

        for node_id in all_nodes:
            self_val = self.clocks.get(node_id, 0)
            other_val = other.clocks.get(node_id, 0)

            if self_val > other_val:
                self_greater = True
            elif other_val > self_val:
                other_greater = True

        if self_greater and not other_greater:
            return 'after'
        elif other_greater and not self_greater:
            return 'before'
        else:
            return 'concurrent'

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary"""
        return dict(self.clocks)

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'VectorClock':
        """Create from dictionary"""
        return cls(clocks=data)


@dataclass
class ReplicatedValue:
    """
    A value with metadata for replication.

    Attributes:
        value: The actual value
        timestamp: When value was written
        node_id: Which node wrote it
        version: Vector clock for causal ordering
        checksum: SHA256 checksum of value
    """
    value: Any
    timestamp: float
    node_id: str
    version: VectorClock = field(default_factory=VectorClock)
    checksum: Optional[str] = None

    def __post_init__(self):
        if self.checksum is None:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """Compute SHA256 checksum of value"""
        value_str = json.dumps(self.value, sort_keys=True)
        return hashlib.sha256(value_str.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify checksum matches value"""
        return self.checksum == self._compute_checksum()


@dataclass
class ReplicationLog:
    """
    Log of replication operations.

    Tracks all write operations for a key to enable replay and conflict resolution.
    """
    key: str
    operations: List[ReplicatedValue] = field(default_factory=list)
    resolved_value: Optional[ReplicatedValue] = None
    conflicts: int = 0


class ConflictResolver:
    """
    Resolves conflicts between concurrent writes using CRDTs.
    """

    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS):
        """
        Initialize conflict resolver.

        Args:
            strategy: Conflict resolution strategy
        """
        self.strategy = strategy

    def resolve(self, values: List[ReplicatedValue]) -> ReplicatedValue:
        """
        Resolve conflicts between multiple concurrent writes.

        Args:
            values: List of conflicting values

        Returns:
            Resolved value
        """
        if not values:
            raise ValueError("Cannot resolve empty value list")

        if len(values) == 1:
            return values[0]

        if self.strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            return self._resolve_lww(values)
        elif self.strategy == ConflictResolutionStrategy.HIGHEST_NODE_WINS:
            return self._resolve_highest_node(values)
        elif self.strategy == ConflictResolutionStrategy.MERGE_UNION:
            return self._resolve_merge_union(values)
        else:
            # Default to LWW
            return self._resolve_lww(values)

    def _resolve_lww(self, values: List[ReplicatedValue]) -> ReplicatedValue:
        """Last-Write-Wins resolution based on timestamp"""
        return max(values, key=lambda v: (v.timestamp, v.node_id))

    def _resolve_highest_node(self, values: List[ReplicatedValue]) -> ReplicatedValue:
        """Deterministic resolution based on node ID"""
        return max(values, key=lambda v: v.node_id)

    def _resolve_merge_union(self, values: List[ReplicatedValue]) -> ReplicatedValue:
        """
        Merge values via union (for sets/lists).

        Takes the latest timestamp and merges all values.
        """
        latest = max(values, key=lambda v: v.timestamp)

        # Merge all values (assuming they're lists or sets)
        merged = set()
        for val in values:
            if isinstance(val.value, (list, set)):
                merged.update(val.value)
            else:
                merged.add(val.value)

        # Create merged value with latest metadata
        return ReplicatedValue(
            value=list(merged),
            timestamp=latest.timestamp,
            node_id=latest.node_id,
            version=latest.version
        )

    def detect_conflicts(self, values: List[ReplicatedValue]) -> bool:
        """
        Detect if values are concurrent (conflicting).

        Args:
            values: List of values to check

        Returns:
            True if any values are concurrent
        """
        for i, val1 in enumerate(values):
            for val2 in values[i+1:]:
                if val1.version.compare(val2.version) == 'concurrent':
                    return True
        return False


class MultiMasterReplicator:
    """
    Multi-master replication system with CRDT-based conflict resolution.

    Enables multiple nodes to accept writes while maintaining eventual consistency.
    """

    def __init__(
        self,
        node_id: str,
        storage_path: Optional[Path] = None,
        resolver: Optional[ConflictResolver] = None,
    ):
        """
        Initialize multi-master replicator.

        Args:
            node_id: This node's unique identifier
            storage_path: Path to persist replication state
            resolver: Conflict resolver (uses LWW if not provided)
        """
        self.node_id = node_id
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "replication"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.resolver = resolver or ConflictResolver()

        # Local store: key -> ReplicatedValue
        self.store: Dict[str, ReplicatedValue] = {}
        self.store_lock = asyncio.Lock()

        # Replication logs: key -> ReplicationLog
        self.replication_logs: Dict[str, ReplicationLog] = {}

        # Vector clock for this node
        self.vector_clock = VectorClock()

        # Metrics
        self.writes_local = 0
        self.writes_replicated = 0
        self.conflicts_resolved = 0

        # Load persisted state
        self._load_state()

    async def write(self, key: str, value: Any) -> ReplicatedValue:
        """
        Write a value locally.

        Args:
            key: Key to write
            value: Value to write

        Returns:
            ReplicatedValue with metadata
        """
        async with self.store_lock:
            # Increment vector clock
            self.vector_clock.increment(self.node_id)

            # Create replicated value
            replicated_value = ReplicatedValue(
                value=value,
                timestamp=time.time(),
                node_id=self.node_id,
                version=VectorClock(clocks=dict(self.vector_clock.clocks))
            )

            # Store locally
            self.store[key] = replicated_value

            # Add to replication log
            if key not in self.replication_logs:
                self.replication_logs[key] = ReplicationLog(key=key)

            self.replication_logs[key].operations.append(replicated_value)
            self.replication_logs[key].resolved_value = replicated_value

            self.writes_local += 1

            # Persist state
            self._save_state()

            logger.debug(f"Wrote {key}={value} at clock {self.vector_clock.to_dict()}")

            return replicated_value

    async def read(self, key: str) -> Optional[Any]:
        """
        Read a value.

        Args:
            key: Key to read

        Returns:
            Value or None if not found
        """
        async with self.store_lock:
            if key in self.store:
                return self.store[key].value
            return None

    async def replicate_from(self, node_id: str, key: str, replicated_value: ReplicatedValue):
        """
        Receive a replicated value from another node.

        Args:
            node_id: Source node ID
            key: Key being replicated
            replicated_value: The replicated value
        """
        async with self.store_lock:
            # Verify checksum
            if not replicated_value.verify():
                logger.error(f"Checksum mismatch for replicated {key} from {node_id}")
                return

            # Update our vector clock
            self.vector_clock.update(replicated_value.version)

            # Add to replication log
            if key not in self.replication_logs:
                self.replication_logs[key] = ReplicationLog(key=key)

            log = self.replication_logs[key]
            log.operations.append(replicated_value)

            # Check if current value exists
            if key in self.store:
                current = self.store[key]

                # Compare vector clocks
                comparison = replicated_value.version.compare(current.version)

                if comparison == 'after':
                    # Incoming value is newer - replace
                    self.store[key] = replicated_value
                    log.resolved_value = replicated_value
                    logger.debug(f"Replicated {key}: incoming is newer")

                elif comparison == 'before':
                    # Incoming value is older - ignore
                    logger.debug(f"Replicated {key}: incoming is older, ignoring")

                elif comparison == 'concurrent':
                    # Conflict - resolve
                    logger.warning(f"Conflict detected for {key} from {node_id}")
                    resolved = self.resolver.resolve([current, replicated_value])
                    self.store[key] = resolved
                    log.resolved_value = resolved
                    log.conflicts += 1
                    self.conflicts_resolved += 1

            else:
                # No current value - accept incoming
                self.store[key] = replicated_value
                log.resolved_value = replicated_value
                logger.debug(f"Replicated {key}: no current value, accepting")

            self.writes_replicated += 1

            # Persist state
            self._save_state()

    async def get_replication_state(self, keys: Optional[List[str]] = None) -> Dict[str, ReplicatedValue]:
        """
        Get current replication state for specified keys.

        Args:
            keys: Optional list of keys (None = all keys)

        Returns:
            Dictionary of key -> ReplicatedValue
        """
        async with self.store_lock:
            if keys is None:
                return dict(self.store)
            else:
                return {k: v for k, v in self.store.items() if k in keys}

    async def get_updates_since(self, vector_clock: VectorClock) -> List[Tuple[str, ReplicatedValue]]:
        """
        Get all updates that happened after a given vector clock.

        Args:
            vector_clock: Vector clock to compare against

        Returns:
            List of (key, value) tuples for updates
        """
        updates = []

        async with self.store_lock:
            for key, value in self.store.items():
                # Check if this value happened after the given clock
                if value.version.compare(vector_clock) == 'after':
                    updates.append((key, value))

        return updates

    async def merge_state(self, remote_state: Dict[str, ReplicatedValue]):
        """
        Merge state from a remote node.

        Args:
            remote_state: State from remote node
        """
        for key, value in remote_state.items():
            await self.replicate_from("remote", key, value)

    def _save_state(self):
        """Persist replication state to disk"""
        state_file = self.storage_path / f"replication_{self.node_id}.json"

        state = {
            "node_id": self.node_id,
            "vector_clock": self.vector_clock.to_dict(),
            "store": {
                key: {
                    "value": val.value,
                    "timestamp": val.timestamp,
                    "node_id": val.node_id,
                    "version": val.version.to_dict(),
                    "checksum": val.checksum,
                }
                for key, val in self.store.items()
            },
            "metrics": {
                "writes_local": self.writes_local,
                "writes_replicated": self.writes_replicated,
                "conflicts_resolved": self.conflicts_resolved,
            }
        }

        state_file.write_text(json.dumps(state, indent=2))

    def _load_state(self):
        """Load replication state from disk"""
        state_file = self.storage_path / f"replication_{self.node_id}.json"

        if not state_file.exists():
            return

        try:
            state = json.loads(state_file.read_text())

            self.vector_clock = VectorClock.from_dict(state.get("vector_clock", {}))

            for key, val_data in state.get("store", {}).items():
                self.store[key] = ReplicatedValue(
                    value=val_data["value"],
                    timestamp=val_data["timestamp"],
                    node_id=val_data["node_id"],
                    version=VectorClock.from_dict(val_data["version"]),
                    checksum=val_data.get("checksum")
                )

                # Rebuild replication log
                self.replication_logs[key] = ReplicationLog(
                    key=key,
                    operations=[self.store[key]],
                    resolved_value=self.store[key]
                )

            metrics = state.get("metrics", {})
            self.writes_local = metrics.get("writes_local", 0)
            self.writes_replicated = metrics.get("writes_replicated", 0)
            self.conflicts_resolved = metrics.get("conflicts_resolved", 0)

            logger.info(f"Loaded replication state: {len(self.store)} keys, clock={self.vector_clock.to_dict()}")

        except Exception as e:
            logger.error(f"Error loading replication state: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get replication statistics"""
        total_conflicts = sum(log.conflicts for log in self.replication_logs.values())

        return {
            "node_id": self.node_id,
            "vector_clock": self.vector_clock.to_dict(),
            "keys_stored": len(self.store),
            "writes_local": self.writes_local,
            "writes_replicated": self.writes_replicated,
            "conflicts_resolved": self.conflicts_resolved,
            "total_conflicts": total_conflicts,
            "resolution_strategy": self.resolver.strategy.value,
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
