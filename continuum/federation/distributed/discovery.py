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
Node Discovery
==============

Multi-method node discovery for distributed federation.
Supports DNS, mDNS, and bootstrap nodes for finding peers.

Discovery Methods:
- DNS-based: Query DNS SRV records for node locations
- mDNS: Multicast DNS for local network discovery
- Bootstrap: Connect to known seed nodes
- Gossip: Learn about peers from peers
"""

import asyncio
import socket
import struct
import random
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class DiscoveryMethod(str, Enum):
    """Methods for discovering federation nodes"""
    DNS = "dns"
    MDNS = "mdns"
    BOOTSTRAP = "bootstrap"
    GOSSIP = "gossip"
    STATIC = "static"


@dataclass
class DiscoveredNode:
    """
    Information about a discovered node.

    Attributes:
        node_id: Unique node identifier
        address: Network address (host:port)
        discovery_method: How this node was discovered
        discovered_at: When node was discovered
        metadata: Additional metadata about the node
        priority: Priority for connection (higher = prefer)
        verified: Whether node identity has been verified
    """
    node_id: str
    address: str
    discovery_method: DiscoveryMethod
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    verified: bool = False


@dataclass
class DiscoveryConfig:
    """Configuration for node discovery"""
    enabled_methods: Set[DiscoveryMethod] = field(default_factory=lambda: {
        DiscoveryMethod.DNS,
        DiscoveryMethod.MDNS,
        DiscoveryMethod.BOOTSTRAP
    })
    dns_domain: Optional[str] = None  # e.g., "_continuum._tcp.example.com"
    mdns_service_type: str = "_continuum._tcp.local."
    mdns_interval_seconds: float = 30.0
    bootstrap_nodes: List[str] = field(default_factory=list)  # ["node1:7000", "node2:7000"]
    max_discovered_nodes: int = 100
    discovery_interval_seconds: float = 60.0


class NodeDiscovery:
    """
    Multi-method node discovery for federation.

    Continuously discovers and maintains a list of available federation nodes.
    """

    def __init__(
        self,
        node_id: str,
        config: Optional[DiscoveryConfig] = None,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize node discovery.

        Args:
            node_id: This node's unique identifier
            config: Discovery configuration
            storage_path: Path to persist discovered nodes
        """
        self.node_id = node_id
        self.config = config or DiscoveryConfig()
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "discovery"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Discovered nodes: node_id -> DiscoveredNode
        self.discovered_nodes: Dict[str, DiscoveredNode] = {}
        self.nodes_lock = asyncio.Lock()

        # Background tasks
        self.discovery_task: Optional[asyncio.Task] = None
        self.mdns_task: Optional[asyncio.Task] = None

        # mDNS socket
        self.mdns_socket: Optional[socket.socket] = None

        # Metrics
        self.discovery_attempts = 0
        self.nodes_discovered = 0

        # Running flag
        self._running = False

        # Load persisted nodes
        self._load_state()

    async def start(self):
        """Start node discovery"""
        if self._running:
            logger.warning("Discovery already running")
            return

        self._running = True
        logger.info(f"Starting node discovery with methods: {self.config.enabled_methods}")

        # Start discovery methods
        if DiscoveryMethod.MDNS in self.config.enabled_methods:
            self.mdns_task = asyncio.create_task(self._mdns_discovery_loop())

        # Start periodic discovery
        self.discovery_task = asyncio.create_task(self._discovery_loop())

        logger.info("Node discovery started")

    async def stop(self):
        """Stop node discovery"""
        if not self._running:
            return

        logger.info("Stopping node discovery")
        self._running = False

        # Cancel tasks
        if self.discovery_task:
            self.discovery_task.cancel()
            try:
                await self.discovery_task
            except asyncio.CancelledError:
                pass

        if self.mdns_task:
            self.mdns_task.cancel()
            try:
                await self.mdns_task
            except asyncio.CancelledError:
                pass

        # Close mDNS socket
        if self.mdns_socket:
            self.mdns_socket.close()

        # Save state
        self._save_state()

        logger.info("Node discovery stopped")

    async def discover_now(self) -> List[DiscoveredNode]:
        """
        Trigger immediate discovery across all enabled methods.

        Returns:
            List of newly discovered nodes
        """
        newly_discovered = []

        if DiscoveryMethod.DNS in self.config.enabled_methods:
            nodes = await self._discover_via_dns()
            newly_discovered.extend(nodes)

        if DiscoveryMethod.BOOTSTRAP in self.config.enabled_methods:
            nodes = await self._discover_via_bootstrap()
            newly_discovered.extend(nodes)

        if DiscoveryMethod.STATIC in self.config.enabled_methods:
            nodes = await self._discover_static()
            newly_discovered.extend(nodes)

        return newly_discovered

    async def register_node(self, node: DiscoveredNode):
        """
        Manually register a discovered node.

        Args:
            node: Node to register
        """
        async with self.nodes_lock:
            if node.node_id in self.discovered_nodes:
                # Update existing
                existing = self.discovered_nodes[node.node_id]
                existing.address = node.address
                existing.metadata.update(node.metadata)
                existing.priority = max(existing.priority, node.priority)
                logger.debug(f"Updated discovered node {node.node_id}")
            else:
                # Add new
                self.discovered_nodes[node.node_id] = node
                self.nodes_discovered += 1
                logger.info(f"Discovered new node {node.node_id} at {node.address} via {node.discovery_method.value}")

            # Enforce max nodes limit
            if len(self.discovered_nodes) > self.config.max_discovered_nodes:
                self._evict_lowest_priority_nodes()

    async def get_nodes(
        self,
        verified_only: bool = False,
        min_priority: int = 0
    ) -> List[DiscoveredNode]:
        """
        Get discovered nodes.

        Args:
            verified_only: Only return verified nodes
            min_priority: Minimum priority threshold

        Returns:
            List of discovered nodes
        """
        async with self.nodes_lock:
            nodes = list(self.discovered_nodes.values())

        # Filter
        if verified_only:
            nodes = [n for n in nodes if n.verified]

        if min_priority > 0:
            nodes = [n for n in nodes if n.priority >= min_priority]

        # Sort by priority (descending)
        nodes.sort(key=lambda n: n.priority, reverse=True)

        return nodes

    async def verify_node(self, node_id: str, verified: bool = True):
        """
        Mark a node as verified (or unverified).

        Args:
            node_id: Node to verify
            verified: Verification status
        """
        async with self.nodes_lock:
            if node_id in self.discovered_nodes:
                self.discovered_nodes[node_id].verified = verified
                logger.info(f"Node {node_id} marked as {'verified' if verified else 'unverified'}")

    async def remove_node(self, node_id: str):
        """
        Remove a node from discovered list.

        Args:
            node_id: Node to remove
        """
        async with self.nodes_lock:
            if node_id in self.discovered_nodes:
                del self.discovered_nodes[node_id]
                logger.info(f"Removed node {node_id} from discovery")

    async def _discovery_loop(self):
        """Periodic discovery across all enabled methods"""
        while self._running:
            try:
                self.discovery_attempts += 1
                await self.discover_now()
                await asyncio.sleep(self.config.discovery_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")

    async def _discover_via_dns(self) -> List[DiscoveredNode]:
        """
        Discover nodes via DNS SRV records.

        Returns:
            List of discovered nodes
        """
        if not self.config.dns_domain:
            return []

        discovered = []

        try:
            import dns.resolver

            # Query SRV records
            answers = dns.resolver.resolve(self.config.dns_domain, 'SRV')

            for rdata in answers:
                address = f"{rdata.target}:{rdata.port}"

                # Create discovered node (node_id will need to be resolved via connection)
                node = DiscoveredNode(
                    node_id=f"dns-{rdata.target}-{rdata.port}",  # Temporary ID
                    address=address,
                    discovery_method=DiscoveryMethod.DNS,
                    priority=rdata.priority,
                    metadata={"weight": rdata.weight}
                )

                await self.register_node(node)
                discovered.append(node)

            logger.info(f"DNS discovery found {len(discovered)} nodes")

        except ImportError:
            logger.warning("dnspython not installed, DNS discovery disabled")
        except Exception as e:
            logger.error(f"DNS discovery error: {e}")

        return discovered

    async def _discover_via_bootstrap(self) -> List[DiscoveredNode]:
        """
        Discover nodes via bootstrap node list.

        Returns:
            List of discovered nodes
        """
        discovered = []

        for address in self.config.bootstrap_nodes:
            # Create node entry
            node = DiscoveredNode(
                node_id=f"bootstrap-{address}",  # Temporary ID
                address=address,
                discovery_method=DiscoveryMethod.BOOTSTRAP,
                priority=10,  # Bootstrap nodes get high priority
                metadata={"bootstrap": True}
            )

            await self.register_node(node)
            discovered.append(node)

        if discovered:
            logger.info(f"Bootstrap discovery registered {len(discovered)} nodes")

        return discovered

    async def _discover_static(self) -> List[DiscoveredNode]:
        """
        Load statically configured nodes.

        Returns:
            List of discovered nodes
        """
        # This would load from configuration file
        # For now, just return empty list
        return []

    async def _mdns_discovery_loop(self):
        """
        Continuous mDNS discovery for local network nodes.

        Uses multicast DNS to discover nodes on local network.
        """
        while self._running:
            try:
                await self._mdns_query()
                await asyncio.sleep(self.config.mdns_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in mDNS discovery: {e}")

    async def _mdns_query(self):
        """
        Send mDNS query for CONTINUUM nodes.

        This is a simplified mDNS implementation.
        Production use should leverage libraries like zeroconf.
        """
        try:
            # Create multicast socket
            if not self.mdns_socket:
                self.mdns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.mdns_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.mdns_socket.settimeout(1.0)

                # Join multicast group
                mcast_group = '224.0.0.251'
                mreq = struct.pack("4sl", socket.inet_aton(mcast_group), socket.INADDR_ANY)
                self.mdns_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # In a real implementation, we would:
            # 1. Send mDNS query packet for _continuum._tcp.local.
            # 2. Listen for responses
            # 3. Parse responses and extract node info
            # 4. Register discovered nodes

            # For now, just log
            logger.debug("mDNS query sent (simplified implementation)")

        except Exception as e:
            logger.error(f"mDNS query error: {e}")

    def _evict_lowest_priority_nodes(self):
        """Remove lowest priority nodes to stay under max limit"""
        while len(self.discovered_nodes) > self.config.max_discovered_nodes:
            # Find lowest priority node
            lowest = min(self.discovered_nodes.values(), key=lambda n: (n.priority, n.discovered_at))
            del self.discovered_nodes[lowest.node_id]
            logger.debug(f"Evicted low-priority node {lowest.node_id}")

    def _save_state(self):
        """Persist discovered nodes to disk"""
        state_file = self.storage_path / f"discovery_{self.node_id}.json"

        state = {
            "node_id": self.node_id,
            "discovered_nodes": {
                node_id: {
                    **asdict(node),
                    "discovery_method": node.discovery_method.value,
                    "discovered_at": node.discovered_at.isoformat(),
                }
                for node_id, node in self.discovered_nodes.items()
            },
            "metrics": {
                "discovery_attempts": self.discovery_attempts,
                "nodes_discovered": self.nodes_discovered,
            }
        }

        state_file.write_text(json.dumps(state, indent=2))

    def _load_state(self):
        """Load discovered nodes from disk"""
        state_file = self.storage_path / f"discovery_{self.node_id}.json"

        if not state_file.exists():
            return

        try:
            state = json.loads(state_file.read_text())

            for node_id, node_data in state.get("discovered_nodes", {}).items():
                node_data["discovery_method"] = DiscoveryMethod(node_data["discovery_method"])
                node_data["discovered_at"] = datetime.fromisoformat(node_data["discovered_at"])

                self.discovered_nodes[node_id] = DiscoveredNode(**node_data)

            metrics = state.get("metrics", {})
            self.discovery_attempts = metrics.get("discovery_attempts", 0)
            self.nodes_discovered = metrics.get("nodes_discovered", 0)

            logger.info(f"Loaded discovery state: {len(self.discovered_nodes)} nodes")

        except Exception as e:
            logger.error(f"Error loading discovery state: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        return {
            "node_id": self.node_id,
            "enabled_methods": [m.value for m in self.config.enabled_methods],
            "discovered_nodes": len(self.discovered_nodes),
            "verified_nodes": sum(1 for n in self.discovered_nodes.values() if n.verified),
            "discovery_attempts": self.discovery_attempts,
            "nodes_discovered": self.nodes_discovered,
            "methods": {
                method.value: sum(
                    1 for n in self.discovered_nodes.values()
                    if n.discovery_method == method
                )
                for method in DiscoveryMethod
            }
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
