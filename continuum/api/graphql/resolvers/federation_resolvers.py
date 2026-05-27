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
from typing import Any, Dict, List, Optional

import strawberry
from strawberry.types import Info

# Peers last seen within this window are considered ONLINE
_ONLINE_THRESHOLD_MINUTES = 10


def _federation_storage() -> Path:
    return Path.home() / ".continuum" / "federation"


def _parse_ts(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp string into a timezone-aware datetime."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _is_online(last_seen_str: Optional[str]) -> bool:
    """Return True if last_seen is within the online threshold window."""
    ts = _parse_ts(last_seen_str)
    if ts is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_ONLINE_THRESHOLD_MINUTES)
    return ts > cutoff


def _load_all_peers() -> List[Dict[str, Any]]:
    """
    Scan all local federation node state files and collect unique peers.

    Node state files live at ~/.continuum/federation/<node_id>.json and each
    contains a ``peers`` dict mapping peer_id -> {host, port, last_seen}.
    We deduplicate by peer_id, keeping the most recently-seen entry.
    """
    storage = _federation_storage()
    if not storage.exists():
        return []

    peers: Dict[str, Dict[str, Any]] = {}
    for state_file in storage.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            for peer_id, data in state.get("peers", {}).items():
                existing = peers.get(peer_id)
                new_ts = _parse_ts(data.get("last_seen"))
                if existing is None or (
                    new_ts and (
                        _parse_ts(existing.get("last_seen")) is None
                        or new_ts > _parse_ts(existing["last_seen"])  # type: ignore[arg-type]
                    )
                ):
                    peers[peer_id] = {
                        "peer_id": peer_id,
                        "host": data.get("host", "unknown"),
                        "port": data.get("port", 0),
                        "last_seen": data.get("last_seen"),
                    }
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    return list(peers.values())


async def resolve_federation_peers(info: Info) -> List:
    """
    Resolve federation peers by reading local node state files.

    Each FederationNode persists known peers at ~/.continuum/federation/.
    We aggregate across all state files, deduplicate by peer_id, and map
    each entry to a FederationPeer GraphQL type.  Online status is inferred
    from the last_seen timestamp (within _ONLINE_THRESHOLD_MINUTES = online).
    """
    from ..types import FederationPeer, PeerStatus

    raw_peers = _load_all_peers()
    now = datetime.now(timezone.utc)
    result: List[FederationPeer] = []

    for peer in raw_peers:
        last_seen_str = peer.get("last_seen")
        last_sync = _parse_ts(last_seen_str)
        online = _is_online(last_seen_str)

        host = peer.get("host", "unknown")
        port = peer.get("port", 0)
        url = f"http://{host}:{port}" if port else f"http://{host}"

        result.append(
            FederationPeer(
                id=strawberry.ID(peer["peer_id"]),
                url=url,
                name=None,
                status=PeerStatus.ONLINE if online else PeerStatus.OFFLINE,
                last_sync=last_sync,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=last_sync or now,
                updated_at=last_sync or now,
            )
        )

    return result


async def resolve_federation_status(info: Info) -> "FederationStatus":  # noqa: F821
    """
    Resolve federation status by aggregating local node state and shared knowledge.

    Computes:
    - enabled: True when at least one peer is known
    - total_peers / online_peers: from local node state files
    - last_sync: most recent peer last_seen timestamp
    - synced_memories: total concepts in the shared knowledge pool
    - pending_sync: 0 (local-only; distributed pending tracking is not yet implemented)
    """
    from ..types import FederationStatus

    raw_peers = _load_all_peers()
    total_peers = len(raw_peers)
    online_peers = sum(1 for p in raw_peers if _is_online(p.get("last_seen")))

    last_sync: Optional[datetime] = None
    for peer in raw_peers:
        ts = _parse_ts(peer.get("last_seen"))
        if ts and (last_sync is None or ts > last_sync):
            last_sync = ts

    synced_memories = 0
    try:
        from continuum.federation.shared import SharedKnowledge
        stats = SharedKnowledge().get_stats()
        synced_memories = stats.get("total_concepts", 0)
    except Exception:
        pass

    return FederationStatus(
        enabled=total_peers > 0,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=last_sync,
        synced_memories=synced_memories,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
