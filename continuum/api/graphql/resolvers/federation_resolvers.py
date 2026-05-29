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

from ..types import FederationPeer, FederationStatus, PeerStatus

_ONLINE_THRESHOLD = timedelta(minutes=5)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _peer_status(last_seen: Optional[datetime]) -> PeerStatus:
    if last_seen is None:
        return PeerStatus.OFFLINE
    now = datetime.now(timezone.utc)
    aware = last_seen if last_seen.tzinfo else last_seen.replace(tzinfo=timezone.utc)
    return PeerStatus.ONLINE if (now - aware) <= _ONLINE_THRESHOLD else PeerStatus.OFFLINE


def _load_federation_states(db_path: str) -> list:
    federation_dir = Path(db_path).parent / "federation"
    if not federation_dir.exists():
        return []
    states = []
    for path in federation_dir.glob("*.json"):
        try:
            states.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return states


async def resolve_federation_peers(info: Info) -> List[FederationPeer]:
    """Resolve federation peers from on-disk federation state files."""
    db_path = info.context.get("db_path")
    if not db_path:
        return []

    seen: dict = {}
    for state in _load_federation_states(db_path):
        for peer_id, peer_data in state.get("peers", {}).items():
            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen = _parse_dt(peer_data.get("last_seen"))
            ts = last_seen or datetime.now(timezone.utc)
            seen[peer_id] = FederationPeer(
                id=peer_id,
                url=f"http://{host}:{port}",
                name=None,
                status=_peer_status(last_seen),
                last_sync=last_seen,
                shared_memories=0,
                trust_score=0.0,
                metadata=None,
                created_at=ts,
                updated_at=ts,
            )

    return list(seen.values())


async def resolve_federation_status(info: Info) -> FederationStatus:
    """Resolve federation status by aggregating all on-disk federation state files."""
    db_path = info.context.get("db_path")
    if not db_path:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    states = _load_federation_states(db_path)
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

    for state in states:
        node_last_sync = _parse_dt(state.get("last_sync"))
        if node_last_sync is not None:
            aware = node_last_sync if node_last_sync.tzinfo else node_last_sync.replace(tzinfo=timezone.utc)
            if latest_sync is None or aware > latest_sync:
                latest_sync = aware

        for peer_id, peer_data in state.get("peers", {}).items():
            all_peers[peer_id] = _parse_dt(peer_data.get("last_seen"))

    total = len(all_peers)
    online = sum(1 for ls in all_peers.values() if _peer_status(ls) == PeerStatus.ONLINE)

    return FederationStatus(
        enabled=total > 0,
        total_peers=total,
        online_peers=online,
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
