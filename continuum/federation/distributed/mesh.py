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
Gossip Mesh Networking
======================

Epidemic-style gossip protocol for distributed state propagation.
Enables peer-to-peer memory sharing across federation nodes.

Gossip Protocol:
- Peer selection: Random peer sampling for message propagation
- Anti-entropy: Periodic full state synchronization
- Message buffering: Temporary storage for unreliable networks
- Exponential propagation: Messages spread exponentially

Based on:
- SWIM: Scalable Weakly-consistent Infection-style Process Group Membership Protocol
- HyParView: Hybrid Partial View membership protocol
"""

import asyncio
import time
import random
import hashlib
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from collections import deque
import json
import logging

logger = logging.getLogger(__name__)


class GossipMessageType(str, Enum):
    """Types of gossip messages"""
    SYNC = "sync"  # Request full state sync
    PUSH = "push"  # Push state updates to peer
    PULL = "pull"  # Pull state from peer
    PUSH_PULL = "push_pull"  # Bidirectional exchange
    ACK = "ack"  # Acknowledgment
    PING = "ping"  # Liveness check
    PONG = "pong"  # Ping response


@dataclass
class GossipMessage:
    """
    A message in the gossip protocol.

    Attributes:
        message_id: Unique message identifier
        message_type: Type of gossip message
        sender_id: Node that sent this message
        payload: Message payload
        timestamp: When message was created
        ttl: Time-to-live (hops remaining)
        digest: SHA256 digest of payload
    """
    message_id: str
    message_type: GossipMessageType
    sender_id: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3
    digest: Optional[str] = None

    def __post_init__(self):
        if self.digest is None:
            self.digest = self._compute_digest()

    def _compute_digest(self) -> str:
        """Compute SHA256 digest of payload"""
        payload_str = json.dumps(self.payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify digest matches payload"""
        return self.digest == self._compute_digest()


@dataclass
class PeerState:
    """
    State information about a peer in the mesh.

    Attributes:
        peer_id: Peer node identifier
        address: Peer network address
        last_seen: Last time we received message from peer
        last_sync: Last time we synced state with peer
        message_count: Number of messages received from peer
        latency_ms: Average round-trip latency
        active: Whether peer is currently active
    """
    peer_id: str
    address: str
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_sync: Optional[datetime] = None
    message_count: int = 0
    latency_ms: float = 0.0
    active: bool = True


@dataclass
class MeshConfig:
    """Configuration for gossip mesh"""
    fanout: int = 3  # Number of peers to gossip to per round
    gossip_interval_ms: int = 100  # Milliseconds between gossip rounds
    sync_interval_seconds: float = 30.0  # Full state sync interval
    message_buffer_size: int = 1000  # Max messages to buffer
    peer_timeout_seconds: float = 60.0  # Mark peer inactive after this timeout
    max_ttl: int = 5  # Maximum message TTL
    enable_anti_entropy: bool = True  # Enable periodic full sync


class GossipMesh:
    """
    Gossip-based mesh networking for distributed memory sharing.

    Implements epidemic-style message propagation with anti-entropy
    for eventual consistency across all nodes.
    """

    def __init__(
        self,
        node_id: str,
        config: Optional[MeshConfig] = None,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize gossip mesh.

        Args:
            node_id: This node's unique identifier
            config: Mesh configuration
            storage_path: Path to persist mesh state
        """
        self.node_id = node_id
        self.config = config or MeshConfig()
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "mesh"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Peer registry: peer_id -> PeerState
        self.peers: Dict[str, PeerState] = {}
        self.peers_lock = asyncio.Lock()

        # Message tracking
        self.seen_messages: Set[str] = set()  # Message IDs we've seen
        self.message_buffer: deque = deque(maxlen=self.config.message_buffer_size)

        # State to gossip
        self.local_state: Dict[str, Any] = {}
        self.state_version: int = 0
        self.state_lock = asyncio.Lock()

        # Background tasks
        self.gossip_task: Optional[asyncio.Task] = None
        self.sync_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_dropped = 0
        self.sync_count = 0

        # Callbacks for state updates
        self.state_update_callbacks: List[callable] = []

        # Running flag
        self._running = False

    async def start(self):
        """Start the gossip mesh"""
        if self._running:
            logger.warning("Gossip mesh already running")
            return

        self._running = True
        logger.info(f"Starting gossip mesh for node {self.node_id}")

        # Start gossip round task
        self.gossip_task = asyncio.create_task(self._gossip_loop())

        # Start anti-entropy sync task
        if self.config.enable_anti_entropy:
            self.sync_task = asyncio.create_task(self._sync_loop())

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Gossip mesh started")

    async def stop(self):
        """Stop the gossip mesh"""
        if not self._running:
            return

        logger.info("Stopping gossip mesh")
        self._running = False

        # Cancel tasks
        for task in [self.gossip_task, self.sync_task, self.cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("Gossip mesh stopped")

    async def add_peer(self, peer_id: str, address: str):
        """
        Add a peer to the mesh.

        Args:
            peer_id: Peer node identifier
            address: Peer network address
        """
        async with self.peers_lock:
            if peer_id in self.peers:
                # Update existing peer
                self.peers[peer_id].address = address
                self.peers[peer_id].active = True
                self.peers[peer_id].last_seen = datetime.now(timezone.utc)
            else:
                # Add new peer
                self.peers[peer_id] = PeerState(peer_id=peer_id, address=address)
                logger.info(f"Added peer {peer_id} at {address}")

    async def remove_peer(self, peer_id: str):
        """
        Remove a peer from the mesh.

        Args:
            peer_id: Peer to remove
        """
        async with self.peers_lock:
            if peer_id in self.peers:
                del self.peers[peer_id]
                logger.info(f"Removed peer {peer_id}")

    async def update_state(self, key: str, value: Any):
        """
        Update local state and gossip to peers.

        Args:
            key: State key
            value: State value
        """
        async with self.state_lock:
            self.local_state[key] = value
            self.state_version += 1

        # Create and broadcast update message
        message = GossipMessage(
            message_id=f"{self.node_id}-{self.state_version}-{key}",
            message_type=GossipMessageType.PUSH,
            sender_id=self.node_id,
            payload={
                "type": "state_update",
                "key": key,
                "value": value,
                "version": self.state_version,
            },
            ttl=self.config.max_ttl
        )

        await self._gossip_message(message)

        logger.debug(f"Updated state: {key}={value}")

    async def receive_message(self, message: GossipMessage):
        """
        Receive and process a gossip message.

        Args:
            message: Incoming gossip message
        """
        # Verify message
        if not message.verify():
            logger.warning(f"Invalid message digest from {message.sender_id}")
            self.messages_dropped += 1
            return

        # Check if already seen
        if message.message_id in self.seen_messages:
            logger.debug(f"Already seen message {message.message_id}")
            return

        # Mark as seen
        self.seen_messages.add(message.message_id)
        self.messages_received += 1

        # Update peer state
        async with self.peers_lock:
            if message.sender_id in self.peers:
                peer = self.peers[message.sender_id]
                peer.last_seen = datetime.now(timezone.utc)
                peer.message_count += 1

        # Process message based on type
        if message.message_type == GossipMessageType.PUSH:
            await self._handle_push(message)
        elif message.message_type == GossipMessageType.PULL:
            await self._handle_pull(message)
        elif message.message_type == GossipMessageType.PUSH_PULL:
            await self._handle_push_pull(message)
        elif message.message_type == GossipMessageType.SYNC:
            await self._handle_sync(message)
        elif message.message_type == GossipMessageType.PING:
            await self._handle_ping(message)
        elif message.message_type == GossipMessageType.PONG:
            await self._handle_pong(message)

        # Forward message if TTL > 0
        if message.ttl > 0:
            message.ttl -= 1
            await self._gossip_message(message, exclude={message.sender_id})

    async def get_state(self) -> Dict[str, Any]:
        """
        Get current local state.

        Returns:
            Local state dictionary
        """
        async with self.state_lock:
            return dict(self.local_state)

    async def _gossip_loop(self):
        """Periodic gossip rounds"""
        while self._running:
            try:
                await asyncio.sleep(self.config.gossip_interval_ms / 1000.0)

                # Select random messages from buffer to gossip
                if self.message_buffer:
                    messages_to_gossip = random.sample(
                        list(self.message_buffer),
                        min(3, len(self.message_buffer))
                    )

                    for message in messages_to_gossip:
                        await self._gossip_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in gossip loop: {e}")

    async def _sync_loop(self):
        """Periodic full state synchronization"""
        while self._running:
            try:
                await asyncio.sleep(self.config.sync_interval_seconds)
                await self._perform_anti_entropy_sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")

    async def _cleanup_loop(self):
        """Periodic cleanup of old messages and inactive peers"""
        while self._running:
            try:
                await asyncio.sleep(60.0)  # Cleanup every minute

                # Clean up old seen messages (keep only recent ones)
                if len(self.seen_messages) > 10000:
                    # Keep 50% newest
                    to_keep = list(self.seen_messages)[-5000:]
                    self.seen_messages = set(to_keep)

                # Mark inactive peers
                async with self.peers_lock:
                    cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.config.peer_timeout_seconds)
                    for peer in self.peers.values():
                        if peer.last_seen < cutoff:
                            peer.active = False
                            logger.debug(f"Peer {peer.peer_id} marked inactive")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _gossip_message(self, message: GossipMessage, exclude: Optional[Set[str]] = None):
        """
        Gossip a message to random peers.

        Args:
            message: Message to gossip
            exclude: Set of peer IDs to exclude
        """
        exclude = exclude or set()

        async with self.peers_lock:
            # Get active peers
            active_peers = [
                p for p in self.peers.values()
                if p.active and p.peer_id not in exclude and p.peer_id != self.node_id
            ]

        if not active_peers:
            return

        # Select random fanout peers
        num_peers = min(self.config.fanout, len(active_peers))
        selected_peers = random.sample(active_peers, num_peers)

        # Send to selected peers
        for peer in selected_peers:
            # In a real implementation, send message via network
            # For now, just log
            logger.debug(f"Gossiping message {message.message_id} to {peer.peer_id}")
            self.messages_sent += 1

        # Buffer message
        self.message_buffer.append(message)

    async def _handle_push(self, message: GossipMessage):
        """
        Handle PUSH message (incoming state update).

        Args:
            message: Push message
        """
        payload = message.payload

        if payload.get("type") == "state_update":
            key = payload.get("key")
            value = payload.get("value")
            version = payload.get("version", 0)

            async with self.state_lock:
                # Simple last-write-wins based on version
                current_version = self.local_state.get(f"_version_{key}", -1)

                if version > current_version:
                    self.local_state[key] = value
                    self.local_state[f"_version_{key}"] = version
                    logger.debug(f"Applied state update: {key}={value} (v{version})")

                    # Notify callbacks
                    for callback in self.state_update_callbacks:
                        try:
                            await callback(key, value)
                        except Exception as e:
                            logger.error(f"Error in state update callback: {e}")

    async def _handle_pull(self, message: GossipMessage):
        """
        Handle PULL message (request for state).

        Args:
            message: Pull message
        """
        # Send our state back to requester
        response = GossipMessage(
            message_id=f"{self.node_id}-pull-response-{time.time()}",
            message_type=GossipMessageType.PUSH,
            sender_id=self.node_id,
            payload={
                "type": "state_sync",
                "state": await self.get_state(),
            },
            ttl=1  # Direct response, no forwarding
        )

        # In real implementation, send directly to requester
        logger.debug(f"Sending pull response to {message.sender_id}")

    async def _handle_push_pull(self, message: GossipMessage):
        """
        Handle PUSH_PULL message (bidirectional exchange).

        Args:
            message: Push-pull message
        """
        # Apply their updates
        await self._handle_push(message)

        # Send our updates back
        await self._handle_pull(message)

    async def _handle_sync(self, message: GossipMessage):
        """
        Handle SYNC message (full state synchronization).

        Args:
            message: Sync message
        """
        payload = message.payload

        if "state" in payload:
            remote_state = payload["state"]

            async with self.state_lock:
                # Merge remote state with local state
                for key, value in remote_state.items():
                    if key not in self.local_state or key.startswith("_version_"):
                        continue  # Skip version keys in merge

                    # Simple last-write-wins
                    # In production, use vector clocks or CRDTs
                    self.local_state[key] = value

            logger.info(f"Synced state with {message.sender_id}")
            self.sync_count += 1

    async def _handle_ping(self, message: GossipMessage):
        """
        Handle PING message (liveness check).

        Args:
            message: Ping message
        """
        # Send pong response
        pong = GossipMessage(
            message_id=f"{self.node_id}-pong-{time.time()}",
            message_type=GossipMessageType.PONG,
            sender_id=self.node_id,
            payload={"ping_id": message.message_id},
            ttl=1
        )

        # In real implementation, send directly back
        logger.debug(f"Sending pong to {message.sender_id}")

    async def _handle_pong(self, message: GossipMessage):
        """
        Handle PONG message (ping response).

        Args:
            message: Pong message
        """
        # Update peer latency
        async with self.peers_lock:
            if message.sender_id in self.peers:
                peer = self.peers[message.sender_id]
                # Calculate latency from timestamp
                latency = (time.time() - message.timestamp) * 1000  # ms
                peer.latency_ms = latency
                logger.debug(f"Peer {message.sender_id} latency: {latency:.2f}ms")

    async def _perform_anti_entropy_sync(self):
        """
        Perform full anti-entropy state synchronization with random peer.

        Anti-entropy ensures eventual consistency by periodically exchanging
        complete state with random peers.
        """
        async with self.peers_lock:
            active_peers = [p for p in self.peers.values() if p.active]

        if not active_peers:
            return

        # Select random peer
        peer = random.choice(active_peers)

        # Create sync message
        sync_message = GossipMessage(
            message_id=f"{self.node_id}-sync-{time.time()}",
            message_type=GossipMessageType.SYNC,
            sender_id=self.node_id,
            payload={
                "state": await self.get_state(),
                "version": self.state_version,
            },
            ttl=1  # Direct sync, no forwarding
        )

        # In real implementation, send to peer
        logger.info(f"Performing anti-entropy sync with {peer.peer_id}")

        async with self.peers_lock:
            peer.last_sync = datetime.now(timezone.utc)

    def register_state_update_callback(self, callback: callable):
        """
        Register callback for state updates.

        Args:
            callback: Async function(key, value) called on state changes
        """
        self.state_update_callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Get gossip mesh statistics"""
        active_peers = sum(1 for p in self.peers.values() if p.active)

        return {
            "node_id": self.node_id,
            "total_peers": len(self.peers),
            "active_peers": active_peers,
            "state_version": self.state_version,
            "state_keys": len(self.local_state),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "messages_dropped": self.messages_dropped,
            "messages_buffered": len(self.message_buffer),
            "seen_messages": len(self.seen_messages),
            "sync_count": self.sync_count,
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
