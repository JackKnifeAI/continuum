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
Federation Coordinator
======================

Central coordination for distributed federation nodes.
Manages node discovery, health checking, load balancing, and failover.

The coordinator maintains a view of all active nodes and routes
requests to healthy nodes based on load and capacity.
"""

import asyncio
import time
import ssl
import hashlib
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Node status states"""
    UNKNOWN = "unknown"
    JOINING = "joining"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    LEAVING = "leaving"
    DEAD = "dead"


@dataclass
class NodeHealth:
    """
    Health information for a federation node.

    Attributes:
        node_id: Unique node identifier
        address: Network address (host:port)
        status: Current health status
        last_heartbeat: Timestamp of last heartbeat
        latency_ms: Average latency in milliseconds
        load_score: Load score (0.0-1.0, lower is better)
        capacity: Total capacity (concepts, requests/sec, etc.)
        version: Node software version
        uptime_seconds: Node uptime in seconds
        consecutive_failures: Number of consecutive health check failures
    """
    node_id: str
    address: str
    status: NodeStatus = NodeStatus.UNKNOWN
    last_heartbeat: Optional[datetime] = None
    latency_ms: float = 0.0
    load_score: float = 0.0
    capacity: Dict[str, Any] = field(default_factory=dict)
    version: str = "0.1.0"
    uptime_seconds: float = 0.0
    consecutive_failures: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadBalance:
    """Load balancing strategy configuration"""
    algorithm: str = "least_loaded"  # least_loaded, round_robin, random, latency
    health_check_interval: float = 10.0  # seconds
    unhealthy_threshold: int = 3  # consecutive failures
    degraded_threshold: float = 0.7  # load score threshold
    rebalance_interval: float = 60.0  # seconds


class FederationCoordinator:
    """
    Coordinates a distributed federation of CONTINUUM nodes.

    Responsibilities:
    - Node registration and deregistration
    - Health monitoring and status tracking
    - Load balancing across nodes
    - Automatic failover on node failure
    - Federation-wide state synchronization
    """

    def __init__(
        self,
        node_id: str,
        bind_address: str = "0.0.0.0:7000",
        storage_path: Optional[Path] = None,
        tls_cert: Optional[str] = None,
        tls_key: Optional[str] = None,
        tls_ca: Optional[str] = None,
        load_balance: Optional[LoadBalance] = None,
    ):
        """
        Initialize federation coordinator.

        Args:
            node_id: This coordinator's node ID
            bind_address: Address to bind to (host:port)
            storage_path: Path to store federation state
            tls_cert: Path to TLS certificate for mutual auth
            tls_key: Path to TLS private key
            tls_ca: Path to CA certificate for peer verification
            load_balance: Load balancing configuration
        """
        self.node_id = node_id
        self.bind_address = bind_address
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "distributed"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # TLS configuration
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.tls_ca = tls_ca
        self.ssl_context = self._create_ssl_context() if tls_cert else None

        # Load balancing
        self.load_balance = load_balance or LoadBalance()

        # Node registry
        self.nodes: Dict[str, NodeHealth] = {}
        self.nodes_lock = asyncio.Lock()

        # Routing state
        self.round_robin_index = 0

        # Background tasks
        self.health_check_task: Optional[asyncio.Task] = None
        self.rebalance_task: Optional[asyncio.Task] = None

        # Metrics
        self.start_time = time.time()
        self.total_requests = 0
        self.total_failures = 0

        # Running state
        self._running = False

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for TLS mutual authentication"""
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        if self.tls_cert and self.tls_key:
            context.load_cert_chain(self.tls_cert, self.tls_key)

        if self.tls_ca:
            context.load_verify_locations(self.tls_ca)
            context.verify_mode = ssl.CERT_REQUIRED

        # Strong security settings
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.check_hostname = True

        return context

    async def start(self):
        """Start the federation coordinator"""
        if self._running:
            logger.warning("Coordinator already running")
            return

        self._running = True
        logger.info(f"Starting federation coordinator on {self.bind_address}")

        # Load persisted state
        await self._load_state()

        # Start background tasks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.rebalance_task = asyncio.create_task(self._rebalance_loop())

        logger.info("Federation coordinator started")

    async def stop(self):
        """Stop the federation coordinator"""
        if not self._running:
            return

        logger.info("Stopping federation coordinator")
        self._running = False

        # Cancel background tasks
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        if self.rebalance_task:
            self.rebalance_task.cancel()
            try:
                await self.rebalance_task
            except asyncio.CancelledError:
                pass

        # Save state
        await self._save_state()

        logger.info("Federation coordinator stopped")

    async def register_node(self, node_id: str, address: str, metadata: Optional[Dict] = None) -> NodeHealth:
        """
        Register a new node in the federation.

        Args:
            node_id: Unique node identifier
            address: Node address (host:port)
            metadata: Optional metadata about the node

        Returns:
            NodeHealth object for the registered node
        """
        async with self.nodes_lock:
            if node_id in self.nodes:
                logger.info(f"Node {node_id} re-registering")
                node = self.nodes[node_id]
                node.status = NodeStatus.JOINING
                node.address = address
                if metadata:
                    node.metadata.update(metadata)
            else:
                logger.info(f"Registering new node {node_id} at {address}")
                node = NodeHealth(
                    node_id=node_id,
                    address=address,
                    status=NodeStatus.JOINING,
                    last_heartbeat=datetime.now(timezone.utc),
                    metadata=metadata or {}
                )
                self.nodes[node_id] = node

            # Trigger immediate health check
            asyncio.create_task(self._check_node_health(node_id))

            return node

    async def deregister_node(self, node_id: str):
        """
        Deregister a node from the federation.

        Args:
            node_id: Node to deregister
        """
        async with self.nodes_lock:
            if node_id in self.nodes:
                logger.info(f"Deregistering node {node_id}")
                self.nodes[node_id].status = NodeStatus.LEAVING
                # Don't remove immediately - allow graceful shutdown
                await asyncio.sleep(5)  # Grace period
                del self.nodes[node_id]
            else:
                logger.warning(f"Attempted to deregister unknown node {node_id}")

    async def heartbeat(self, node_id: str, health_data: Optional[Dict] = None) -> bool:
        """
        Record a heartbeat from a node.

        Args:
            node_id: Node sending heartbeat
            health_data: Optional health metrics

        Returns:
            True if heartbeat accepted, False if node unknown
        """
        async with self.nodes_lock:
            if node_id not in self.nodes:
                logger.warning(f"Heartbeat from unknown node {node_id}")
                return False

            node = self.nodes[node_id]
            node.last_heartbeat = datetime.now(timezone.utc)
            node.consecutive_failures = 0

            if health_data:
                node.load_score = health_data.get("load_score", 0.0)
                node.latency_ms = health_data.get("latency_ms", 0.0)
                node.uptime_seconds = health_data.get("uptime_seconds", 0.0)
                if "capacity" in health_data:
                    node.capacity.update(health_data["capacity"])

            # Update status based on health data
            if node.status == NodeStatus.JOINING:
                node.status = NodeStatus.HEALTHY
            elif node.load_score > self.load_balance.degraded_threshold:
                node.status = NodeStatus.DEGRADED
            else:
                node.status = NodeStatus.HEALTHY

            return True

    async def select_node(self, criteria: Optional[Dict] = None) -> Optional[NodeHealth]:
        """
        Select a node for request routing based on load balancing algorithm.

        Args:
            criteria: Optional selection criteria (e.g., min_capacity)

        Returns:
            Selected NodeHealth or None if no healthy nodes
        """
        criteria = criteria or {}

        async with self.nodes_lock:
            # Filter to healthy/degraded nodes
            available = [
                node for node in self.nodes.values()
                if node.status in (NodeStatus.HEALTHY, NodeStatus.DEGRADED)
            ]

            if not available:
                logger.warning("No healthy nodes available")
                return None

            # Apply criteria filters
            if "min_capacity" in criteria:
                min_cap = criteria["min_capacity"]
                available = [n for n in available if n.capacity.get("total", 0) >= min_cap]

            if not available:
                return None

            # Select based on algorithm
            algorithm = self.load_balance.algorithm

            if algorithm == "least_loaded":
                return min(available, key=lambda n: n.load_score)

            elif algorithm == "latency":
                return min(available, key=lambda n: n.latency_ms)

            elif algorithm == "round_robin":
                selected = available[self.round_robin_index % len(available)]
                self.round_robin_index = (self.round_robin_index + 1) % len(available)
                return selected

            elif algorithm == "random":
                import random
                return random.choice(available)

            else:
                # Default: least loaded
                return min(available, key=lambda n: n.load_score)

    async def get_all_nodes(self, status_filter: Optional[Set[NodeStatus]] = None) -> List[NodeHealth]:
        """
        Get all nodes, optionally filtered by status.

        Args:
            status_filter: Set of statuses to include (None = all)

        Returns:
            List of NodeHealth objects
        """
        async with self.nodes_lock:
            if status_filter:
                return [node for node in self.nodes.values() if node.status in status_filter]
            return list(self.nodes.values())

    async def get_node(self, node_id: str) -> Optional[NodeHealth]:
        """
        Get health information for a specific node.

        Args:
            node_id: Node identifier

        Returns:
            NodeHealth or None if not found
        """
        async with self.nodes_lock:
            return self.nodes.get(node_id)

    async def _health_check_loop(self):
        """Background task for periodic health checks"""
        while self._running:
            try:
                await asyncio.sleep(self.load_balance.health_check_interval)
                await self._check_all_nodes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def _check_all_nodes(self):
        """Check health of all registered nodes"""
        async with self.nodes_lock:
            node_ids = list(self.nodes.keys())

        for node_id in node_ids:
            await self._check_node_health(node_id)

    async def _check_node_health(self, node_id: str):
        """
        Check health of a specific node.

        Args:
            node_id: Node to check
        """
        async with self.nodes_lock:
            if node_id not in self.nodes:
                return
            node = self.nodes[node_id]

        # Check if last heartbeat is too old
        if node.last_heartbeat:
            age = (datetime.now(timezone.utc) - node.last_heartbeat).total_seconds()
            timeout = self.load_balance.health_check_interval * 2

            if age > timeout:
                async with self.nodes_lock:
                    node.consecutive_failures += 1

                    if node.consecutive_failures >= self.load_balance.unhealthy_threshold:
                        if node.status != NodeStatus.DEAD:
                            logger.warning(f"Node {node_id} marked as DEAD (no heartbeat for {age:.1f}s)")
                            node.status = NodeStatus.DEAD
                    else:
                        node.status = NodeStatus.UNHEALTHY
                        logger.warning(f"Node {node_id} unhealthy (failure {node.consecutive_failures}/{self.load_balance.unhealthy_threshold})")

    async def _rebalance_loop(self):
        """Background task for periodic load rebalancing"""
        while self._running:
            try:
                await asyncio.sleep(self.load_balance.rebalance_interval)
                await self._rebalance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rebalance loop: {e}")

    async def _rebalance(self):
        """
        Rebalance load across federation nodes.

        This is a hook for future advanced rebalancing logic
        (e.g., migrating data, adjusting request routing weights, etc.)
        """
        async with self.nodes_lock:
            healthy_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.HEALTHY]
            degraded_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.DEGRADED]

        if degraded_nodes:
            logger.info(f"Rebalancing: {len(degraded_nodes)} degraded nodes detected")
            # Future: Implement data migration, request throttling, etc.

    async def _save_state(self):
        """Persist coordinator state to disk"""
        state_file = self.storage_path / f"coordinator_{self.node_id}.json"

        async with self.nodes_lock:
            state = {
                "node_id": self.node_id,
                "nodes": {
                    node_id: {
                        **asdict(node),
                        "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                        "status": node.status.value,
                    }
                    for node_id, node in self.nodes.items()
                },
                "metrics": {
                    "total_requests": self.total_requests,
                    "total_failures": self.total_failures,
                    "uptime_seconds": time.time() - self.start_time,
                }
            }

        state_file.write_text(json.dumps(state, indent=2))

    async def _load_state(self):
        """Load coordinator state from disk"""
        state_file = self.storage_path / f"coordinator_{self.node_id}.json"

        if not state_file.exists():
            return

        try:
            state = json.loads(state_file.read_text())

            async with self.nodes_lock:
                for node_id, node_data in state.get("nodes", {}).items():
                    # Convert status back to enum
                    node_data["status"] = NodeStatus(node_data["status"])

                    # Parse datetime
                    if node_data["last_heartbeat"]:
                        node_data["last_heartbeat"] = datetime.fromisoformat(node_data["last_heartbeat"])

                    self.nodes[node_id] = NodeHealth(**node_data)

            metrics = state.get("metrics", {})
            self.total_requests = metrics.get("total_requests", 0)
            self.total_failures = metrics.get("total_failures", 0)

            logger.info(f"Loaded state: {len(self.nodes)} nodes")

        except Exception as e:
            logger.error(f"Error loading coordinator state: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get coordinator statistics.

        Returns:
            Statistics dictionary
        """
        uptime = time.time() - self.start_time

        node_counts = {}
        for status in NodeStatus:
            node_counts[status.value] = sum(1 for n in self.nodes.values() if n.status == status)

        return {
            "coordinator_id": self.node_id,
            "uptime_seconds": uptime,
            "total_nodes": len(self.nodes),
            "nodes_by_status": node_counts,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "success_rate": 1.0 - (self.total_failures / max(self.total_requests, 1)),
            "load_balance_algorithm": self.load_balance.algorithm,
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
