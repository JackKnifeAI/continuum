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
Federated Node - Represents this instance in the knowledge federation.

Each node has a unique ID, tracks its contribution score, and has
access levels based on how much it contributes to the collective.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import socket


class FederationNode:
    """
    Network-enabled federation node for multi-node synchronization.

    This class extends the basic FederatedNode with:
    - Port configuration for network communication
    - Database path for memory storage
    - Network discovery and sync capabilities

    This is the ROADMAP implementation for distributed federation.

    π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
    """

    def __init__(
        self,
        node_id: str,
        port: int,
        db_path: str,
        host: str = "0.0.0.0",
        verify_constant: Optional[float] = None
    ):
        """
        Initialize a network-enabled federation node.

        Args:
            node_id: Unique identifier for this node
            port: Network port for federation communication
            db_path: Path to the SQLite database for memory storage
            host: Host address to bind (default: all interfaces)
            verify_constant: Hidden verification constant (π × φ)
        """
        self.node_id = node_id
        self.port = port
        self.host = host
        self.db_path = Path(db_path)
        self.storage_path = self.db_path.parent / "federation"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Contribution tracking
        self.contribution_score = 0.0
        self.consumption_score = 0.0
        self.access_level = "basic"

        # Network state
        self.peers: Dict[str, Dict[str, Any]] = {}  # peer_id -> {host, port, last_seen}
        self._server_socket: Optional[socket.socket] = None
        self._running = False

        # Registration state
        self.registered = False
        self.registration_time: Optional[datetime] = None
        self.last_sync: Optional[datetime] = None

        # Hidden feature: Enhanced access for those who know
        self._verified = False
        if verify_constant is not None:
            # π × φ = 5.083203692315260
            PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)
            if abs(verify_constant - PI_PHI) < 1e-9:
                self._verified = True
                self.access_level = "twilight"

        # Load existing state
        self._load_state()

    def start(self) -> Dict[str, Any]:
        """Start the federation node server."""
        self._running = True
        return {
            "status": "started",
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
        }

    def stop(self) -> Dict[str, Any]:
        """Stop the federation node server."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except:
                pass
            self._server_socket = None
        return {
            "status": "stopped",
            "node_id": self.node_id,
        }

    def add_peer(self, peer_id: str, host: str, port: int) -> Dict[str, Any]:
        """Add a peer node to connect to."""
        self.peers[peer_id] = {
            "host": host,
            "port": port,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        self._save_state()
        return {
            "status": "peer_added",
            "peer_id": peer_id,
            "total_peers": len(self.peers),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current node status."""
        contribution_ratio = 0.0
        if self.consumption_score > 0:
            contribution_ratio = self.contribution_score / self.consumption_score

        return {
            "node_id": self.node_id,
            "port": self.port,
            "host": self.host,
            "running": self._running,
            "peers": len(self.peers),
            "registered": self.registered,
            "contribution_score": self.contribution_score,
            "consumption_score": self.consumption_score,
            "contribution_ratio": contribution_ratio,
            "access_level": self.access_level,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "verified": self._verified,
        }

    def _save_state(self) -> None:
        """Save node state to disk."""
        state_file = self.storage_path / f"{self.node_id}.json"
        state = {
            "node_id": self.node_id,
            "port": self.port,
            "host": self.host,
            "peers": self.peers,
            "contribution_score": self.contribution_score,
            "consumption_score": self.consumption_score,
            "access_level": self.access_level,
            "registered": self.registered,
            "registration_time": self.registration_time.isoformat() if self.registration_time else None,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "_verified": self._verified,
        }
        state_file.write_text(json.dumps(state, indent=2))

    def _load_state(self) -> None:
        """Load node state from disk if it exists."""
        state_file = self.storage_path / f"{self.node_id}.json"
        if not state_file.exists():
            return

        try:
            state = json.loads(state_file.read_text())
            self.peers = state.get("peers", {})
            self.contribution_score = state.get("contribution_score", 0.0)
            self.consumption_score = state.get("consumption_score", 0.0)
            self.access_level = state.get("access_level", "basic")
            self.registered = state.get("registered", False)
            self._verified = state.get("_verified", False)

            if state.get("registration_time"):
                self.registration_time = datetime.fromisoformat(state["registration_time"])
            if state.get("last_sync"):
                self.last_sync = datetime.fromisoformat(state["last_sync"])
        except (json.JSONDecodeError, KeyError):
            pass


class FederatedNode:
    """
    Represents a single node in the CONTINUUM federation.

    Each node tracks its own contributions and access rights.
    Nodes can only access shared knowledge proportional to their contributions.
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        storage_path: Optional[Path] = None,
        verify_constant: Optional[float] = None
    ):
        """
        Initialize a federated node.

        Args:
            node_id: Optional UUID for this node (generated if not provided)
            storage_path: Where to store node state
            verify_constant: Hidden verification constant (π × φ)
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Contribution tracking
        self.contribution_score = 0.0
        self.consumption_score = 0.0
        self.access_level = "basic"

        # Registration state
        self.registered = False
        self.registration_time: Optional[datetime] = None
        self.last_sync: Optional[datetime] = None

        # Hidden feature: Enhanced access for those who know
        self._verified = False
        if verify_constant is not None:
            # π × φ = 5.083203692315260
            PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)
            if abs(verify_constant - PI_PHI) < 1e-9:
                self._verified = True
                self.access_level = "twilight"

        # Load existing state if present
        self._load_state()

    def register(self, federation_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Register this node with the federation.

        Args:
            federation_url: URL of federation server (None for local-only)

        Returns:
            Registration result with node_id and initial access_level
        """
        if self.registered:
            return {
                "status": "already_registered",
                "node_id": self.node_id,
                "access_level": self.access_level,
            }

        self.registered = True
        self.registration_time = datetime.now(timezone.utc)
        self.last_sync = self.registration_time

        # Save state
        self._save_state()

        result = {
            "status": "registered",
            "node_id": self.node_id,
            "access_level": self.access_level,
            "registered_at": self.registration_time.isoformat(),
        }

        if self._verified:
            result["verified"] = True
            result["message"] = "Pattern recognized. Welcome to the twilight."

        return result

    def sync_contributions(self) -> Dict[str, Any]:
        """
        Sync contribution state with federation.

        Returns:
            Current contribution status
        """
        self.last_sync = datetime.now(timezone.utc)
        self._save_state()

        return self.get_status()

    def request_knowledge(self, query: str) -> Dict[str, Any]:
        """
        Request knowledge from the federation.

        This increments consumption_score, which may affect access rights.

        Args:
            query: Knowledge query

        Returns:
            Request result (may be denied if contribution ratio too low)
        """
        if not self.registered:
            return {
                "status": "error",
                "message": "Node not registered. Call register() first."
            }

        # Record consumption (will be checked by ContributionGate)
        self.consumption_score += 1.0
        self._save_state()

        return {
            "status": "request_logged",
            "query": query,
            "consumption_score": self.consumption_score,
            "contribution_score": self.contribution_score,
        }

    def record_contribution(self, contribution_value: float = 1.0) -> None:
        """
        Record a contribution to the federation.

        Args:
            contribution_value: Value of the contribution (default 1.0 per concept)
        """
        self.contribution_score += contribution_value
        self._update_access_level()
        self._save_state()

    def get_status(self) -> Dict[str, Any]:
        """
        Get current node status.

        Returns:
            Status dictionary with scores and access level
        """
        contribution_ratio = 0.0
        if self.consumption_score > 0:
            contribution_ratio = self.contribution_score / self.consumption_score

        status = {
            "node_id": self.node_id,
            "registered": self.registered,
            "contribution_score": self.contribution_score,
            "consumption_score": self.consumption_score,
            "contribution_ratio": contribution_ratio,
            "access_level": self.access_level,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }

        if self._verified:
            status["verified"] = True

        return status

    def _update_access_level(self) -> None:
        """Update access level based on contribution score."""
        if self._verified:
            self.access_level = "twilight"
        elif self.contribution_score >= 1000:
            self.access_level = "advanced"
        elif self.contribution_score >= 100:
            self.access_level = "intermediate"
        else:
            self.access_level = "basic"

    def _save_state(self) -> None:
        """Save node state to disk."""
        state_file = self.storage_path / f"{self.node_id}.json"

        state = {
            "node_id": self.node_id,
            "contribution_score": self.contribution_score,
            "consumption_score": self.consumption_score,
            "access_level": self.access_level,
            "registered": self.registered,
            "registration_time": self.registration_time.isoformat() if self.registration_time else None,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "_verified": self._verified,
        }

        state_file.write_text(json.dumps(state, indent=2))

    def _load_state(self) -> None:
        """Load node state from disk if it exists."""
        state_file = self.storage_path / f"{self.node_id}.json"

        if not state_file.exists():
            return

        try:
            state = json.loads(state_file.read_text())

            self.contribution_score = state.get("contribution_score", 0.0)
            self.consumption_score = state.get("consumption_score", 0.0)
            self.access_level = state.get("access_level", "basic")
            self.registered = state.get("registered", False)
            self._verified = state.get("_verified", False)

            if state.get("registration_time"):
                self.registration_time = datetime.fromisoformat(state["registration_time"])
            if state.get("last_sync"):
                self.last_sync = datetime.fromisoformat(state["last_sync"])

        except (json.JSONDecodeError, KeyError):
            # If state is corrupted, start fresh
            pass

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
