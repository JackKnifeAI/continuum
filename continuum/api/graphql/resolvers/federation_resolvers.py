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
from typing import List, Optional

from strawberry.types import Info

# Peers unseen for longer than this are considered offline
_ONLINE_THRESHOLD = timedelta(minutes=5)


def _parse_iso(s: str) -> Optional[datetime]:
    """Parse an ISO datetime string, returning a UTC-aware datetime or None."""
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _federation_dir(db_path: str) -> Optional[Path]:
    """Return the federation state directory, or None if db_path is missing."""
    if not db_path:
        return None
    d = Path(db_path).parent / "federation"
    return d if d.exists() else None


def _load_all_peers(federation_dir: Path) -> dict:
    """
    Scan all node state files and merge their peer lists.

    Returns a flat mapping of peer_id -> peer_data dict.
    """
    peers: dict = {}
    for state_file in federation_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            for peer_id, peer_data in state.get("peers", {}).items():
                if peer_id not in peers:
                    peers[peer_id] = peer_data
        except (json.JSONDecodeError, OSError):
            continue
    return peers


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from on-disk node state files."""
    from ..types import FederationPeer, PeerStatus

    fed_dir = _federation_dir(info.context.db_path)
    if fed_dir is None:
        return []

    now = datetime.now(timezone.utc)
    result = []

    for peer_id, peer_data in _load_all_peers(fed_dir).items():
        host = peer_data.get("host", "unknown")
        port = peer_data.get("port", 0)
        url = f"http://{host}:{port}"

        last_seen = _parse_iso(peer_data.get("last_seen", ""))

        if last_seen is None:
            status = PeerStatus.UNREACHABLE
        elif (now - last_seen) <= _ONLINE_THRESHOLD:
            status = PeerStatus.ONLINE
        else:
            status = PeerStatus.OFFLINE

        timestamp = last_seen or now
        result.append(FederationPeer(
            id=peer_id,
            url=url,
            name=peer_data.get("name"),
            status=status,
            last_sync=last_seen,
            shared_memories=0,
            trust_score=1.0,
            metadata=None,
            created_at=timestamp,
            updated_at=timestamp,
        ))

    return result


async def resolve_federation_status(info: Info):
    """Resolve federation status from on-disk node state files."""
    from ..types import FederationStatus

    _disabled = FederationStatus(
        enabled=False,
        total_peers=0,
        online_peers=0,
        last_sync=None,
        synced_memories=0,
        pending_sync=0,
    )

    fed_dir = _federation_dir(info.context.db_path)
    if fed_dir is None:
        return _disabled

    now = datetime.now(timezone.utc)
    last_sync: Optional[datetime] = None

    # Collect most-recent sync timestamp across all node state files
    for state_file in fed_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            node_sync = _parse_iso(state.get("last_sync", ""))
            if node_sync and (last_sync is None or node_sync > last_sync):
                last_sync = node_sync
        except (json.JSONDecodeError, OSError):
            continue

    all_peers = _load_all_peers(fed_dir)
    online_peers = sum(
        1 for p in all_peers.values()
        if (ts := _parse_iso(p.get("last_seen", ""))) and (now - ts) <= _ONLINE_THRESHOLD
    )

    return FederationStatus(
        enabled=True,
        total_peers=len(all_peers),
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
