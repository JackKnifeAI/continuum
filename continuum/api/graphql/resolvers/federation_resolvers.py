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

# Peer is considered online if seen within the last 5 minutes
_ONLINE_THRESHOLD = 300
# Peer is unreachable (not offline) if seen within the last hour
_UNREACHABLE_THRESHOLD = 3600

_FEDERATION_DIR = Path.home() / ".continuum" / "federation"


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string, ensuring UTC timezone."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _read_node_states() -> List[dict]:
    """Load all federation node state files from the local storage directory."""
    if not _FEDERATION_DIR.exists():
        return []
    states = []
    for state_file in sorted(_FEDERATION_DIR.glob("*.json")):
        try:
            states.append(json.loads(state_file.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return states


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from local node state files."""
    from ..types import FederationPeer, PeerStatus

    now = datetime.now(timezone.utc)
    seen: set = set()
    peers = []

    for state in _read_node_states():
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen:
                continue
            seen.add(peer_id)

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen = _parse_dt(peer_data.get("last_seen"))

            status = PeerStatus.OFFLINE
            if last_seen:
                age = (now - last_seen).total_seconds()
                if age <= _ONLINE_THRESHOLD:
                    status = PeerStatus.ONLINE
                elif age <= _UNREACHABLE_THRESHOLD:
                    status = PeerStatus.UNREACHABLE

            url = f"http://{host}:{port}" if port else f"http://{host}"
            timestamp = last_seen or now

            peers.append(FederationPeer(
                id=peer_id,
                url=url,
                name=peer_id,
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
    """Resolve federation status from node state files and the shared knowledge pool."""
    from continuum.federation.shared import SharedKnowledge

    from ..types import FederationStatus

    now = datetime.now(timezone.utc)
    states = _read_node_states()

    # Collect unique peers and track the most recent sync across all nodes
    seen: set = set()
    peer_last_seens: List[Optional[datetime]] = []
    last_sync: Optional[datetime] = None

    for state in states:
        node_sync = _parse_dt(state.get("last_sync"))
        if node_sync and (last_sync is None or node_sync > last_sync):
            last_sync = node_sync

        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen:
                continue
            seen.add(peer_id)
            peer_last_seens.append(_parse_dt(peer_data.get("last_seen")))

    total_peers = len(peer_last_seens)
    online_peers = sum(
        1 for ls in peer_last_seens
        if ls and (now - ls).total_seconds() <= _ONLINE_THRESHOLD
    )

    synced_memories = 0
    try:
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
