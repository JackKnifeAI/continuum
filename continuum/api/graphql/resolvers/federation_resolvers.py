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

_NODE_STATUS_TO_PEER_STATUS = {
    "healthy": "online",
    "degraded": "syncing",
    "unhealthy": "unreachable",
    "dead": "offline",
    "unknown": "offline",
    "joining": "offline",
    "leaving": "offline",
}

_STALE_HEARTBEAT_SECONDS = 120


def _map_node_status(node_status: str, last_sync: Optional[datetime], now: datetime) -> str:
    """Map coordinator NodeStatus string to PeerStatus value, accounting for stale heartbeats."""
    if last_sync and (now - last_sync).total_seconds() > _STALE_HEARTBEAT_SECONDS:
        return "offline"
    return _NODE_STATUS_TO_PEER_STATUS.get(node_status.lower(), "offline")


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from coordinator state files on disk."""
    from ..types import FederationPeer, PeerStatus

    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return []

    storage_path = Path(db_path).parent / "federation"
    if not storage_path.exists():
        return []

    peers: List[FederationPeer] = []
    now = datetime.now(timezone.utc)

    for state_file in storage_path.glob("coordinator_*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for node_id, node_data in state.get("nodes", {}).items():
            try:
                last_hb_str = node_data.get("last_heartbeat")
                last_sync = datetime.fromisoformat(last_hb_str) if last_hb_str else None

                raw_status = node_data.get("status", "unknown")
                mapped = _map_node_status(raw_status, last_sync, now)
                status = PeerStatus(mapped)

                address = node_data.get("address", "")
                url = f"http://{address}" if address and "://" not in address else address

                capacity = node_data.get("capacity") or {}
                load_score = node_data.get("load_score", 0.0)

                peers.append(FederationPeer(
                    id=node_id,
                    url=url,
                    name=node_id,
                    status=status,
                    last_sync=last_sync,
                    shared_memories=int(capacity.get("memories", 0)),
                    trust_score=max(0.0, min(1.0, 1.0 - load_score)),
                    metadata=node_data.get("metadata") or None,
                    created_at=last_sync or now,
                    updated_at=last_sync or now,
                ))
            except (KeyError, ValueError):
                continue

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status aggregated from known peers."""
    from ..types import FederationStatus, PeerStatus

    peers = await resolve_federation_peers(info)

    online_peers = sum(1 for p in peers if p.status == PeerStatus.ONLINE)
    last_syncs = [p.last_sync for p in peers if p.last_sync is not None]
    last_sync = max(last_syncs) if last_syncs else None
    synced_memories = sum(p.shared_memories for p in peers)

    return FederationStatus(
        enabled=len(peers) > 0,
        total_peers=len(peers),
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
