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
Resolvers for Federation type fields.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from strawberry.types import Info

# Age thresholds for deriving peer online/syncing/offline status from last_seen timestamp
_ONLINE_THRESHOLD_SECONDS = 60
_SYNCING_THRESHOLD_SECONDS = 300


def _parse_aware_datetime(value: str) -> datetime:
    """Parse an ISO datetime string and ensure it is timezone-aware (UTC)."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from persisted node state on disk.

    Reads ~/.continuum/federation/*.json files written by FederationNode._save_state().
    Each file contains a 'peers' dict mapping peer_id -> {host, port, last_seen}.
    Peer online status is inferred from how recently the node was last seen.
    """
    from ..types import FederationPeer, PeerStatus

    federation_dir = Path.home() / ".continuum" / "federation"
    if not federation_dir.exists():
        return []

    peers: List[FederationPeer] = []
    seen_peer_ids: set = set()
    now = datetime.now(timezone.utc)

    for state_file in sorted(federation_dir.glob("*.json")):
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            continue

        for peer_id, peer_info in state.get("peers", {}).items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)

            host = peer_info.get("host", "unknown")
            port = peer_info.get("port", 7000)
            last_seen_str = peer_info.get("last_seen")

            last_seen: datetime | None = None
            if last_seen_str:
                try:
                    last_seen = _parse_aware_datetime(last_seen_str)
                except (ValueError, TypeError):
                    pass

            if last_seen is not None:
                age = (now - last_seen).total_seconds()
                if age < _ONLINE_THRESHOLD_SECONDS:
                    status = PeerStatus.ONLINE
                elif age < _SYNCING_THRESHOLD_SECONDS:
                    status = PeerStatus.SYNCING
                else:
                    status = PeerStatus.OFFLINE
            else:
                status = PeerStatus.OFFLINE

            peers.append(
                FederationPeer(
                    id=peer_id,
                    url=f"http://{host}:{port}",
                    name=None,
                    status=status,
                    last_sync=last_seen,
                    shared_memories=0,
                    trust_score=1.0,
                    metadata=None,
                    created_at=last_seen or now,
                    updated_at=last_seen or now,
                )
            )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating persisted node state files.

    Reads ~/.continuum/federation/*.json files. A node is considered enabled
    when at least one registered node is found. Peer counts and last_sync are
    derived from the union of all node state files.
    """
    from ..types import FederationStatus

    federation_dir = Path.home() / ".continuum" / "federation"
    if not federation_dir.exists():
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(timezone.utc)
    enabled = False
    total_peers = 0
    online_peers = 0
    last_sync: datetime | None = None
    seen_peer_ids: set = set()

    for state_file in federation_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            continue

        if state.get("registered", False):
            enabled = True

        node_last_sync_str = state.get("last_sync")
        if node_last_sync_str:
            try:
                node_sync = _parse_aware_datetime(node_last_sync_str)
                if last_sync is None or node_sync > last_sync:
                    last_sync = node_sync
            except (ValueError, TypeError):
                pass

        for peer_id, peer_info in state.get("peers", {}).items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)
            total_peers += 1

            last_seen_str = peer_info.get("last_seen")
            if last_seen_str:
                try:
                    last_seen = _parse_aware_datetime(last_seen_str)
                    if (now - last_seen).total_seconds() < _ONLINE_THRESHOLD_SECONDS:
                        online_peers += 1
                except (ValueError, TypeError):
                    pass

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=last_sync,
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
