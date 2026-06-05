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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import strawberry
from strawberry.types import Info

_ONLINE_THRESHOLD = timedelta(minutes=5)
_FEDERATION_PATH = Path.home() / ".continuum" / "federation"


def _load_node_states() -> List[Dict[str, Any]]:
    """Load all FederationNode JSON state files from the local storage path."""
    if not _FEDERATION_PATH.exists():
        return []
    states = []
    for state_file in _FEDERATION_PATH.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            if "node_id" in state and "peers" in state:
                states.append(state)
        except (json.JSONDecodeError, OSError):
            pass
    return states


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO datetime string, coercing naive datetimes to UTC."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _count_shared_memories() -> int:
    """Return the number of concepts in the shared federation knowledge pool."""
    knowledge_file = _FEDERATION_PATH / "shared" / "knowledge.json"
    if not knowledge_file.exists():
        return 0
    try:
        data = json.loads(knowledge_file.read_text())
        return len(data.get("concepts", {}))
    except (json.JSONDecodeError, OSError):
        return 0


async def resolve_federation_peers(info: Info) -> List:
    """
    Resolve federation peers by reading all local node state files.

    Each FederationNode persists its known peers to disk as
    ~/.continuum/federation/<node_id>.json.  We scan those files,
    deduplicate peers across nodes, and map each entry to a
    FederationPeer GraphQL type.  Online/offline status is derived
    from the last_seen timestamp.
    """
    from ..types import FederationPeer, PeerStatus

    now = datetime.now(timezone.utc)
    seen_peer_ids: Set[str] = set()
    peers: List[FederationPeer] = []

    for state in _load_node_states():
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen = _parse_dt(peer_data.get("last_seen"))

            if last_seen and (now - last_seen) < _ONLINE_THRESHOLD:
                status = PeerStatus.ONLINE
            elif last_seen:
                status = PeerStatus.OFFLINE
            else:
                status = PeerStatus.UNREACHABLE

            url = f"{host}:{port}" if port else host
            timestamp = last_seen or now

            peers.append(FederationPeer(
                id=strawberry.ID(peer_id),
                url=url,
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=timestamp,
                updated_at=timestamp,
            ))

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """
    Resolve federation status by aggregating all local node state files.

    Reports whether federation is enabled (any registered node), total and
    online peer counts, the most recent sync timestamp, and the number of
    concepts in the shared knowledge pool.
    """
    from ..types import FederationStatus

    now = datetime.now(timezone.utc)
    states = _load_node_states()

    enabled = any(s.get("registered", False) for s in states)

    seen_peer_ids: Set[str] = set()
    online_count = 0
    for state in states:
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)
            last_seen = _parse_dt(peer_data.get("last_seen"))
            if last_seen and (now - last_seen) < _ONLINE_THRESHOLD:
                online_count += 1

    last_sync: Optional[datetime] = None
    for state in states:
        dt = _parse_dt(state.get("last_sync"))
        if dt and (last_sync is None or dt > last_sync):
            last_sync = dt

    return FederationStatus(
        enabled=enabled,
        total_peers=len(seen_peer_ids),
        online_peers=online_count,
        last_sync=last_sync,
        synced_memories=_count_shared_memories(),
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
