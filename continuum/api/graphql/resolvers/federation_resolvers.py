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
from typing import List, Optional

from strawberry.types import Info

# Thresholds for determining peer online/syncing status from last_seen age
_ONLINE_THRESHOLD_SECONDS = 300     # 5 minutes → ONLINE
_SYNCING_THRESHOLD_SECONDS = 1800   # 30 minutes → SYNCING, beyond → OFFLINE


def _federation_storage_path() -> Path:
    return Path.home() / ".continuum" / "federation"


def _load_federation_states() -> List[dict]:
    """Load all FederationNode state files from ~/.continuum/federation/."""
    storage = _federation_storage_path()
    if not storage.exists():
        return []
    states = []
    for f in storage.glob("*.json"):
        try:
            states.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    return states


def _peer_status_from_last_seen(last_seen: Optional[str]):
    """Map a last_seen ISO timestamp to a PeerStatus enum value."""
    from ..types import PeerStatus

    if not last_seen:
        return PeerStatus.UNREACHABLE
    try:
        ts = datetime.fromisoformat(last_seen)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age <= _ONLINE_THRESHOLD_SECONDS:
            return PeerStatus.ONLINE
        if age <= _SYNCING_THRESHOLD_SECONDS:
            return PeerStatus.SYNCING
        return PeerStatus.OFFLINE
    except (ValueError, TypeError):
        return PeerStatus.UNREACHABLE


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from local node state files.

    Reads FederationNode JSON state files from ~/.continuum/federation/ and
    returns the union of all known peers, deduplicating by peer ID.
    """
    from ..types import FederationPeer

    states = _load_federation_states()
    seen: set = set()
    peers = []
    now = datetime.now(timezone.utc)

    for state in states:
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen:
                continue
            seen.add(peer_id)

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen_str: Optional[str] = peer_data.get("last_seen")

            last_seen_dt: Optional[datetime] = None
            if last_seen_str:
                try:
                    last_seen_dt = datetime.fromisoformat(last_seen_str)
                except ValueError:
                    pass

            timestamp = last_seen_dt or now
            peers.append(FederationPeer(
                id=peer_id,
                url=f"http://{host}:{port}",
                name=None,
                status=_peer_status_from_last_seen(last_seen_str),
                last_sync=last_seen_dt,
                shared_memories=0,
                trust_score=0.0,
                metadata=None,
                created_at=timestamp,
                updated_at=timestamp,
            ))

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from local node state files.

    Aggregates peer counts and sync timestamps across all FederationNode
    state files in ~/.continuum/federation/.
    """
    from ..types import FederationStatus, PeerStatus

    states = _load_federation_states()

    if not states:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    all_peers: dict = {}
    latest_sync: Optional[datetime] = None
    any_registered = False

    for state in states:
        if state.get("registered"):
            any_registered = True

        last_sync_str: Optional[str] = state.get("last_sync")
        if last_sync_str:
            try:
                ts = datetime.fromisoformat(last_sync_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if latest_sync is None or ts > latest_sync:
                    latest_sync = ts
            except ValueError:
                pass

        for peer_id, peer_data in state.get("peers", {}).items():
            all_peers[peer_id] = peer_data

    online_peers = sum(
        1 for p in all_peers.values()
        if _peer_status_from_last_seen(p.get("last_seen")) == PeerStatus.ONLINE
    )

    return FederationStatus(
        enabled=any_registered,
        total_peers=len(all_peers),
        online_peers=online_peers,
        last_sync=latest_sync,
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
