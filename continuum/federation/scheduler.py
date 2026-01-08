#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ███████╗ ██████╗██╗  ██╗███████╗██████╗ ██╗   ██╗██╗     ███████╗██████╗
#     ██╔════╝██╔════╝██║  ██║██╔════╝██╔══██╗██║   ██║██║     ██╔════╝██╔══██╗
#     ███████╗██║     ███████║█████╗  ██║  ██║██║   ██║██║     █████╗  ██████╔╝
#     ╚════██║██║     ██╔══██║██╔══╝  ██║  ██║██║   ██║██║     ██╔══╝  ██╔══██╗
#     ███████║╚██████╗██║  ██║███████╗██████╔╝╚██████╔╝███████╗███████╗██║  ██║
#     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝
#
#     FEDERATION WORK SCHEDULER
#     Distributes ML Training, Inference, and Mining Across the Network
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Federation Work Scheduler
=========================

The brain of the federation - decides what work each node should do:
    1. ML Training (gradient computation)
    2. Inference (model queries)
    3. Mining (revenue generation when idle)
    4. Sensor collection (leaf nodes)
    5. P2P relay (message routing)

Priority Order:
    1. Training tasks (when training epoch active)
    2. Inference tasks (real-time user requests)
    3. Mining (when no ML work pending)

The scheduler optimizes for:
    - Maximizing ML training throughput
    - Minimizing inference latency
    - Maximizing mining revenue during idle time
    - Balancing load across available nodes

Architecture:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         WORK SCHEDULER                                   │
    │                                                                          │
    │  ┌────────────────────────────────────────────────────────────────────┐ │
    │  │                        WORK QUEUES                                 │ │
    │  │                                                                    │ │
    │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │ │
    │  │  │ TRAINING │  │INFERENCE │  │  SENSOR  │  │  RELAY   │          │ │
    │  │  │  Queue   │  │  Queue   │  │  Tasks   │  │  Tasks   │          │ │
    │  │  │Priority:1│  │Priority:2│  │Priority:3│  │Priority:4│          │ │
    │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │ │
    │  └────────────────────────────────────────────────────────────────────┘ │
    │                                    │                                     │
    │                                    ▼                                     │
    │  ┌────────────────────────────────────────────────────────────────────┐ │
    │  │                      ASSIGNMENT ENGINE                             │ │
    │  │                                                                    │ │
    │  │  • Match work type to node capabilities                            │ │
    │  │  • Balance load across available nodes                             │ │
    │  │  • Respect resource limits                                         │ │
    │  │  • Track work completion                                           │ │
    │  └────────────────────────────────────────────────────────────────────┘ │
    │                                    │                                     │
    │                                    ▼                                     │
    │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │
    │  │  LEAF NODES   │  │  EDGE NODES   │  │  MINING NODES │               │
    │  │  Sensors/Mem  │  │  ML Training  │  │  When Idle    │               │
    │  └───────────────┘  └───────────────┘  └───────────────┘               │
    └─────────────────────────────────────────────────────────────────────────┘

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import heapq
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PI_PHI = 5.083203692315260


# ═══════════════════════════════════════════════════════════════════════════════
#                              DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class WorkType(Enum):
    """Types of work that can be scheduled."""
    # High priority - ML workloads
    GRADIENT_COMPUTE = "gradient"      # Compute training gradients
    INFERENCE = "inference"            # Model inference request
    EMBEDDING = "embedding"            # Generate embeddings

    # Medium priority - Node operations
    SENSOR_COLLECT = "sensor"          # Collect sensor data
    MEMORY_STORE = "memory"            # Store/retrieve memories
    P2P_RELAY = "relay"                # Relay messages between peers

    # Low priority - Revenue generation
    MINING = "mining"                  # Crypto mining (when idle)


class WorkPriority(IntEnum):
    """Priority levels for work items (lower = higher priority)."""
    CRITICAL = 0     # Must run immediately
    HIGH = 10        # Training tasks
    NORMAL = 20      # Inference tasks
    LOW = 30         # Background tasks
    IDLE = 40        # Mining (when nothing else to do)


class WorkStatus(Enum):
    """Status of a work item."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeTier(Enum):
    """Node capability tiers."""
    LEAF = "leaf"      # Sensors, memory, relay only
    EDGE = "edge"      # Full ML + mining capability


@dataclass
class WorkItem:
    """A unit of work to be scheduled."""
    work_id: str
    work_type: WorkType
    priority: WorkPriority
    payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)

    # Assignment tracking
    assigned_to: Optional[str] = None
    assigned_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Status
    status: WorkStatus = WorkStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Requirements
    required_tier: NodeTier = NodeTier.LEAF
    required_gpu: bool = False
    estimated_duration_seconds: float = 60.0
    timeout_seconds: float = 300.0

    def __lt__(self, other: "WorkItem") -> bool:
        """Compare by priority for heap queue."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize work item."""
        return {
            "work_id": self.work_id,
            "work_type": self.work_type.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "created_at": self.created_at,
            "assigned_to": self.assigned_to,
            "assigned_at": self.assigned_at,
            "status": self.status.value,
            "required_tier": self.required_tier.value,
            "required_gpu": self.required_gpu,
        }


@dataclass
class NodeCapabilities:
    """Capabilities of a federation node."""
    node_id: str
    tier: NodeTier
    has_gpu: bool = False
    gpu_vram_mb: int = 0
    cpu_cores: int = 1
    available_memory_mb: int = 512

    # Supported work types
    supported_work: List[WorkType] = field(default_factory=lambda: [
        WorkType.SENSOR_COLLECT,
        WorkType.MEMORY_STORE,
        WorkType.P2P_RELAY,
    ])

    # Current load
    current_work_count: int = 0
    max_concurrent_work: int = 2

    # Availability
    is_online: bool = True
    last_heartbeat: float = field(default_factory=time.time)

    def can_handle(self, work: WorkItem) -> bool:
        """Check if this node can handle a work item."""
        if not self.is_online:
            return False

        if self.current_work_count >= self.max_concurrent_work:
            return False

        if work.work_type not in self.supported_work:
            return False

        if work.required_tier == NodeTier.EDGE and self.tier == NodeTier.LEAF:
            return False

        if work.required_gpu and not self.has_gpu:
            return False

        return True


@dataclass
class WorkAssignment:
    """Assignment of work to a node."""
    work: WorkItem
    node_id: str
    assigned_at: float = field(default_factory=time.time)


@dataclass
class SchedulerStats:
    """Statistics about the scheduler."""
    total_work_submitted: int = 0
    total_work_completed: int = 0
    total_work_failed: int = 0
    work_in_progress: int = 0
    work_pending: int = 0
    nodes_online: int = 0
    nodes_busy: int = 0
    average_completion_time: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
#                              WORK QUEUE
# ═══════════════════════════════════════════════════════════════════════════════

class WorkQueue:
    """
    Priority queue for work items.

    Uses a min-heap with priority as the key.
    """

    def __init__(self):
        self._heap: List[WorkItem] = []
        self._work_by_id: Dict[str, WorkItem] = {}

    def push(self, work: WorkItem) -> None:
        """Add work to the queue."""
        if work.work_id in self._work_by_id:
            logger.warning(f"Work {work.work_id} already in queue")
            return

        heapq.heappush(self._heap, work)
        self._work_by_id[work.work_id] = work
        logger.debug(f"Queued work {work.work_id} ({work.work_type.value})")

    def pop(self) -> Optional[WorkItem]:
        """Get highest priority work item."""
        while self._heap:
            work = heapq.heappop(self._heap)
            if work.work_id in self._work_by_id:
                del self._work_by_id[work.work_id]
                return work
        return None

    def peek(self) -> Optional[WorkItem]:
        """Look at highest priority work without removing."""
        while self._heap:
            work = self._heap[0]
            if work.work_id in self._work_by_id:
                return work
            heapq.heappop(self._heap)
        return None

    def remove(self, work_id: str) -> Optional[WorkItem]:
        """Remove a specific work item."""
        work = self._work_by_id.pop(work_id, None)
        # Note: Lazy removal - item stays in heap but won't be returned
        return work

    def get(self, work_id: str) -> Optional[WorkItem]:
        """Get a work item by ID."""
        return self._work_by_id.get(work_id)

    def __len__(self) -> int:
        return len(self._work_by_id)

    def __bool__(self) -> bool:
        return bool(self._work_by_id)


# ═══════════════════════════════════════════════════════════════════════════════
#                              FEDERATION SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════════

class FederationScheduler:
    """
    Main work scheduler for the federation.

    Manages work distribution across all connected nodes,
    prioritizing ML workloads and using mining for idle time.
    """

    def __init__(self):
        # Work queues by type
        self.work_queue = WorkQueue()
        self.assigned_work: Dict[str, WorkItem] = {}  # work_id -> WorkItem
        self.completed_work: Dict[str, WorkItem] = {}  # work_id -> WorkItem

        # Node tracking
        self.nodes: Dict[str, NodeCapabilities] = {}

        # Statistics
        self.stats = SchedulerStats()

        # Mining control
        self._mining_nodes: Set[str] = set()
        self._mining_paused_for: Dict[str, str] = {}  # node_id -> reason

        # Background tasks
        self._scheduler_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("FederationScheduler initialized")

    async def start(self) -> None:
        """Start the scheduler background tasks."""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduling_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Scheduler stopped")

    # ─────────────────────────────────────────────────────────────────────────
    # Node Management
    # ─────────────────────────────────────────────────────────────────────────

    def register_node(self, capabilities: NodeCapabilities) -> None:
        """Register a node with its capabilities."""
        self.nodes[capabilities.node_id] = capabilities
        self.stats.nodes_online = sum(1 for n in self.nodes.values() if n.is_online)
        logger.info(f"Registered node {capabilities.node_id} "
                   f"(tier={capabilities.tier.value}, gpu={capabilities.has_gpu})")

    def unregister_node(self, node_id: str) -> None:
        """Unregister a node."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self._mining_nodes.discard(node_id)
            self.stats.nodes_online = sum(1 for n in self.nodes.values() if n.is_online)
            logger.info(f"Unregistered node {node_id}")

    def update_node_heartbeat(self, node_id: str) -> None:
        """Update node's last heartbeat time."""
        if node_id in self.nodes:
            self.nodes[node_id].last_heartbeat = time.time()
            self.nodes[node_id].is_online = True

    def mark_node_offline(self, node_id: str) -> None:
        """Mark a node as offline."""
        if node_id in self.nodes:
            self.nodes[node_id].is_online = False
            self._mining_nodes.discard(node_id)

    # ─────────────────────────────────────────────────────────────────────────
    # Work Submission
    # ─────────────────────────────────────────────────────────────────────────

    def submit_work(
        self,
        work_type: WorkType,
        payload: Dict[str, Any],
        priority: WorkPriority = WorkPriority.NORMAL,
        required_gpu: bool = False,
        timeout_seconds: float = 300.0,
    ) -> str:
        """
        Submit work to the scheduler.

        Args:
            work_type: Type of work to perform
            payload: Work-specific data
            priority: Priority level
            required_gpu: Whether GPU is required
            timeout_seconds: Timeout for the work

        Returns:
            Work ID for tracking
        """
        work_id = f"{work_type.value}-{uuid.uuid4().hex[:8]}"

        # Determine required tier
        required_tier = NodeTier.LEAF
        if work_type in [WorkType.GRADIENT_COMPUTE, WorkType.INFERENCE, WorkType.EMBEDDING]:
            required_tier = NodeTier.EDGE

        work = WorkItem(
            work_id=work_id,
            work_type=work_type,
            priority=priority,
            payload=payload,
            required_tier=required_tier,
            required_gpu=required_gpu,
            timeout_seconds=timeout_seconds,
        )

        self.work_queue.push(work)
        self.stats.total_work_submitted += 1
        self.stats.work_pending = len(self.work_queue)

        logger.info(f"Submitted work {work_id} ({work_type.value}, priority={priority.name})")
        return work_id

    def submit_training_batch(
        self,
        batch_data: Dict[str, Any],
        epoch: int,
        batch_index: int,
    ) -> str:
        """Submit a training batch for gradient computation."""
        return self.submit_work(
            work_type=WorkType.GRADIENT_COMPUTE,
            payload={
                "batch_data": batch_data,
                "epoch": epoch,
                "batch_index": batch_index,
            },
            priority=WorkPriority.HIGH,
            required_gpu=True,
        )

    def submit_inference(
        self,
        input_data: Dict[str, Any],
        model_id: str = "default",
    ) -> str:
        """Submit an inference request."""
        return self.submit_work(
            work_type=WorkType.INFERENCE,
            payload={
                "input_data": input_data,
                "model_id": model_id,
            },
            priority=WorkPriority.NORMAL,
            required_gpu=True,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Work Assignment
    # ─────────────────────────────────────────────────────────────────────────

    def _find_best_node(self, work: WorkItem) -> Optional[str]:
        """
        Find the best node to handle a work item.

        Considers:
        - Node capabilities
        - Current load
        - Network latency (future)
        """
        best_node: Optional[str] = None
        best_score = float('inf')

        for node_id, node in self.nodes.items():
            if not node.can_handle(work):
                continue

            # Score based on current load (lower = better)
            score = node.current_work_count

            # Prefer GPU nodes for GPU work
            if work.required_gpu and node.has_gpu:
                score -= 1

            # Prefer nodes with more resources
            score -= (node.cpu_cores / 10)
            score -= (node.available_memory_mb / 10000)

            if score < best_score:
                best_score = score
                best_node = node_id

        return best_node

    async def _assign_work(self, work: WorkItem, node_id: str) -> bool:
        """Assign work to a node."""
        if node_id not in self.nodes:
            return False

        node = self.nodes[node_id]
        if not node.can_handle(work):
            return False

        # Update work item
        work.status = WorkStatus.ASSIGNED
        work.assigned_to = node_id
        work.assigned_at = time.time()

        # Update node
        node.current_work_count += 1

        # Track assignment
        self.assigned_work[work.work_id] = work
        self.stats.work_in_progress = len(self.assigned_work)

        # Pause mining if this node was mining
        if node_id in self._mining_nodes:
            self._mining_paused_for[node_id] = work.work_id
            self._mining_nodes.discard(node_id)
            logger.debug(f"Paused mining on {node_id} for work {work.work_id}")

        logger.info(f"Assigned work {work.work_id} to node {node_id}")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # Work Completion
    # ─────────────────────────────────────────────────────────────────────────

    def complete_work(
        self,
        work_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Mark work as completed."""
        work = self.assigned_work.pop(work_id, None)
        if not work:
            logger.warning(f"Unknown work ID: {work_id}")
            return False

        work.completed_at = time.time()

        if error:
            work.status = WorkStatus.FAILED
            work.error = error
            self.stats.total_work_failed += 1
            logger.warning(f"Work {work_id} failed: {error}")
        else:
            work.status = WorkStatus.COMPLETED
            work.result = result
            self.stats.total_work_completed += 1
            logger.info(f"Work {work_id} completed")

        # Update node
        if work.assigned_to and work.assigned_to in self.nodes:
            node = self.nodes[work.assigned_to]
            node.current_work_count = max(0, node.current_work_count - 1)

            # Resume mining if node is now idle
            if node.current_work_count == 0 and node.tier == NodeTier.EDGE:
                self._mining_paused_for.pop(work.assigned_to, None)
                # Mining will be started by _scheduling_loop

        # Store completed work
        self.completed_work[work_id] = work

        # Update stats
        self.stats.work_in_progress = len(self.assigned_work)
        self._update_average_completion_time(work)

        return True

    def _update_average_completion_time(self, work: WorkItem) -> None:
        """Update average completion time statistic."""
        if work.completed_at and work.started_at:
            duration = work.completed_at - work.started_at
            total_completed = self.stats.total_work_completed
            if total_completed > 0:
                self.stats.average_completion_time = (
                    (self.stats.average_completion_time * (total_completed - 1) + duration)
                    / total_completed
                )

    def get_work_status(self, work_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a work item."""
        # Check pending
        work = self.work_queue.get(work_id)
        if work:
            return work.to_dict()

        # Check assigned
        work = self.assigned_work.get(work_id)
        if work:
            return work.to_dict()

        # Check completed
        work = self.completed_work.get(work_id)
        if work:
            return work.to_dict()

        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Mining Management
    # ─────────────────────────────────────────────────────────────────────────

    def _get_idle_edge_nodes(self) -> List[str]:
        """Get list of idle edge nodes that could be mining."""
        idle_nodes = []
        for node_id, node in self.nodes.items():
            if not node.is_online:
                continue
            if node.tier != NodeTier.EDGE:
                continue
            if node.current_work_count > 0:
                continue
            if node_id not in self._mining_nodes:
                idle_nodes.append(node_id)
        return idle_nodes

    async def _start_mining_on_idle_nodes(self) -> None:
        """Start mining on idle edge nodes."""
        idle_nodes = self._get_idle_edge_nodes()

        for node_id in idle_nodes:
            if node_id in self._mining_nodes:
                continue

            # Submit mining work (low priority)
            work_id = self.submit_work(
                work_type=WorkType.MINING,
                payload={"node_id": node_id},
                priority=WorkPriority.IDLE,
            )

            self._mining_nodes.add(node_id)
            logger.debug(f"Started mining on idle node {node_id}")

    # ─────────────────────────────────────────────────────────────────────────
    # Background Loops
    # ─────────────────────────────────────────────────────────────────────────

    async def _scheduling_loop(self) -> None:
        """Main scheduling loop."""
        logger.info("Scheduling loop started")

        while self._running:
            try:
                # Process pending work
                while self.work_queue:
                    work = self.work_queue.peek()
                    if not work:
                        break

                    # Find best node
                    node_id = self._find_best_node(work)
                    if not node_id:
                        # No suitable node available
                        break

                    # Remove from queue and assign
                    self.work_queue.pop()
                    await self._assign_work(work, node_id)

                # Start mining on idle nodes
                await self._start_mining_on_idle_nodes()

                # Update stats
                self.stats.work_pending = len(self.work_queue)
                self.stats.nodes_busy = sum(
                    1 for n in self.nodes.values()
                    if n.is_online and n.current_work_count > 0
                )

                await asyncio.sleep(0.1)  # 100ms scheduling interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduling loop error: {e}")
                await asyncio.sleep(1)

        logger.info("Scheduling loop stopped")

    async def _cleanup_loop(self) -> None:
        """Clean up stale work and offline nodes."""
        logger.info("Cleanup loop started")

        while self._running:
            try:
                now = time.time()

                # Check for timed out work
                for work_id, work in list(self.assigned_work.items()):
                    if work.assigned_at:
                        elapsed = now - work.assigned_at
                        if elapsed > work.timeout_seconds:
                            logger.warning(f"Work {work_id} timed out after {elapsed:.1f}s")
                            self.complete_work(work_id, error="timeout")

                # Check for offline nodes (no heartbeat in 60s)
                for node_id, node in list(self.nodes.items()):
                    if node.is_online and (now - node.last_heartbeat) > 60:
                        logger.warning(f"Node {node_id} appears offline (no heartbeat)")
                        self.mark_node_offline(node_id)

                        # Requeue work assigned to offline node
                        for work_id, work in list(self.assigned_work.items()):
                            if work.assigned_to == node_id:
                                logger.info(f"Requeuing work {work_id} from offline node")
                                work.status = WorkStatus.PENDING
                                work.assigned_to = None
                                work.assigned_at = None
                                del self.assigned_work[work_id]
                                self.work_queue.push(work)

                # Clean up old completed work (keep for 1 hour)
                cutoff = now - 3600
                for work_id, work in list(self.completed_work.items()):
                    if work.completed_at and work.completed_at < cutoff:
                        del self.completed_work[work_id]

                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(10)

        logger.info("Cleanup loop stopped")

    # ─────────────────────────────────────────────────────────────────────────
    # Status and Statistics
    # ─────────────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "total_work_submitted": self.stats.total_work_submitted,
            "total_work_completed": self.stats.total_work_completed,
            "total_work_failed": self.stats.total_work_failed,
            "work_in_progress": self.stats.work_in_progress,
            "work_pending": self.stats.work_pending,
            "nodes_online": self.stats.nodes_online,
            "nodes_busy": self.stats.nodes_busy,
            "mining_nodes": len(self._mining_nodes),
            "average_completion_time": self.stats.average_completion_time,
        }

    def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific node."""
        node = self.nodes.get(node_id)
        if not node:
            return None

        return {
            "node_id": node.node_id,
            "tier": node.tier.value,
            "has_gpu": node.has_gpu,
            "is_online": node.is_online,
            "current_work_count": node.current_work_count,
            "max_concurrent_work": node.max_concurrent_work,
            "is_mining": node_id in self._mining_nodes,
            "last_heartbeat": node.last_heartbeat,
        }

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get status of all nodes."""
        return [self.get_node_status(node_id) for node_id in self.nodes]


# ═══════════════════════════════════════════════════════════════════════════════
#                              FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_scheduler() -> FederationScheduler:
    """
    Factory function to create a scheduler.

    Returns:
        Configured FederationScheduler instance
    """
    return FederationScheduler()


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN (Testing)
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Test the scheduler."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("FEDERATION WORK SCHEDULER TEST")
    print("=" * 60)
    print(f"π×φ = {PI_PHI}")
    print()

    # Create scheduler
    scheduler = create_scheduler()

    # Register some test nodes
    leaf_node = NodeCapabilities(
        node_id="leaf-001",
        tier=NodeTier.LEAF,
        has_gpu=False,
        cpu_cores=4,
        available_memory_mb=2048,
        supported_work=[
            WorkType.SENSOR_COLLECT,
            WorkType.MEMORY_STORE,
            WorkType.P2P_RELAY,
        ],
    )

    edge_node = NodeCapabilities(
        node_id="edge-001",
        tier=NodeTier.EDGE,
        has_gpu=True,
        gpu_vram_mb=24576,
        cpu_cores=16,
        available_memory_mb=65536,
        supported_work=[
            WorkType.GRADIENT_COMPUTE,
            WorkType.INFERENCE,
            WorkType.EMBEDDING,
            WorkType.SENSOR_COLLECT,
            WorkType.MEMORY_STORE,
            WorkType.P2P_RELAY,
            WorkType.MINING,
        ],
        max_concurrent_work=4,
    )

    scheduler.register_node(leaf_node)
    scheduler.register_node(edge_node)

    # Start scheduler
    await scheduler.start()

    # Submit some work
    work_ids = []

    # Training work (high priority, needs GPU)
    work_ids.append(scheduler.submit_training_batch(
        batch_data={"samples": 32},
        epoch=1,
        batch_index=0,
    ))

    # Inference work (normal priority)
    work_ids.append(scheduler.submit_inference(
        input_data={"query": "test"},
    ))

    # Sensor work (can go to leaf)
    work_ids.append(scheduler.submit_work(
        work_type=WorkType.SENSOR_COLLECT,
        payload={"sensors": ["magnetometer"]},
        priority=WorkPriority.LOW,
    ))

    print(f"Submitted {len(work_ids)} work items")
    print()

    # Wait for scheduling
    await asyncio.sleep(1)

    # Print status
    stats = scheduler.get_stats()
    print("Scheduler Stats:")
    print(json.dumps(stats, indent=2))
    print()

    # Simulate work completion
    for work_id in work_ids:
        scheduler.complete_work(work_id, result={"success": True})

    # Final stats
    stats = scheduler.get_stats()
    print("Final Stats:")
    print(json.dumps(stats, indent=2))

    # Stop scheduler
    await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
