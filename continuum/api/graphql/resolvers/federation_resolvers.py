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

Reads peer state from the federation JSON store written by FederationNode.
The store lives at <db_path.parent>/federation/<node_id>.json.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from strawberry.types import Info

# A peer is considered ONLINE if it was seen within this window.
_ONLINE_THRESHOLD = timedelta(minutes=5)


def _get_federation_storage(db_path: Optional[str]) -> Optional[Path]:
    """Return the federation storage directory, or None if it does not exist."""
    if not db_path:
        return None
    storage = Path(db_path).parent / "federation"
    return storage if storage.exists() else None


def _load_node_state(storage: Path) -> Optional[dict]:
    """Load the most-recently-modified node state file from *storage*."""
    state_files = list(storage.glob("*.json"))
    if not state_files:
        return None
    state_file = max(state_files, key=lambda f: f.stat().st_mtime)
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 string to an aware datetime, or return None."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the local node's persisted state."""
    from ..types import FederationPeer, PeerStatus

    db_path = info.context.db_path
    storage = _get_federation_storage(db_path)
    if not storage:
        return []

    state = _load_node_state(storage)
    if not state:
        return []

    now = datetime.now(timezone.utc)
    peers: List[FederationPeer] = []

    for peer_id, peer_info in state.get("peers", {}).items():
        last_seen = _parse_iso(peer_info.get("last_seen"))

        if last_seen and (now - last_seen) <= _ONLINE_THRESHOLD:
            status = PeerStatus.ONLINE
        else:
            status = PeerStatus.OFFLINE

        host = peer_info.get("host", "unknown")
        port = peer_info.get("port", 0)
        timestamp = last_seen or now

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
                created_at=timestamp,
                updated_at=timestamp,
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from the local node's persisted state."""
    from ..types import FederationStatus

    db_path = info.context.db_path
    storage = _get_federation_storage(db_path)

    if not storage:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    state = _load_node_state(storage)
    if not state:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(timezone.utc)
    peers_data: dict = state.get("peers", {})

    online_peers = sum(
        1
        for peer_info in peers_data.values()
        if (ts := _parse_iso(peer_info.get("last_seen"))) and (now - ts) <= _ONLINE_THRESHOLD
    )

    return FederationStatus(
        enabled=state.get("registered", False),
        total_peers=len(peers_data),
        online_peers=online_peers,
        last_sync=_parse_iso(state.get("last_sync")),
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
