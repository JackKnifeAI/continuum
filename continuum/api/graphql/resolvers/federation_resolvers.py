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

# Peers not heard from within this window are considered offline
_OFFLINE_THRESHOLD_SECONDS = 300


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from FederationNode state persisted on disk."""
    from ..types import FederationPeer, PeerStatus

    db_path = Path(info.context.db_path)
    storage_path = db_path.parent / "federation"

    if not storage_path.exists():
        return []

    peers: List[FederationPeer] = []
    now = datetime.now(timezone.utc)

    for state_file in storage_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for peer_id, peer_data in state.get("peers", {}).items():
            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen_str = peer_data.get("last_seen")

            last_seen: Optional[datetime] = None
            peer_status = PeerStatus.OFFLINE
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if (now - last_seen).total_seconds() < _OFFLINE_THRESHOLD_SECONDS:
                        peer_status = PeerStatus.ONLINE
                except ValueError:
                    pass

            ts = last_seen or now
            peers.append(
                FederationPeer(
                    id=peer_id,
                    url=f"http://{host}:{port}",
                    name=None,
                    status=peer_status,
                    last_sync=last_seen,
                    shared_memories=0,
                    trust_score=1.0,
                    metadata=None,
                    created_at=ts,
                    updated_at=ts,
                )
            )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from FederationNode state persisted on disk."""
    from ..types import FederationStatus

    db_path = Path(info.context.db_path)
    storage_path = db_path.parent / "federation"

    if not storage_path.exists():
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    total_peers = 0
    online_peers = 0
    last_sync: Optional[datetime] = None
    now = datetime.now(timezone.utc)
    state_files = list(storage_path.glob("*.json"))

    for state_file in state_files:
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        raw_peers = state.get("peers", {})
        total_peers += len(raw_peers)

        for peer_data in raw_peers.values():
            last_seen_str = peer_data.get("last_seen")
            if last_seen_str:
                try:
                    last_seen_dt = datetime.fromisoformat(last_seen_str)
                    if (now - last_seen_dt).total_seconds() < _OFFLINE_THRESHOLD_SECONDS:
                        online_peers += 1
                except ValueError:
                    pass

        node_sync_str = state.get("last_sync")
        if node_sync_str:
            try:
                node_sync = datetime.fromisoformat(node_sync_str)
                if last_sync is None or node_sync > last_sync:
                    last_sync = node_sync
            except ValueError:
                pass

    enabled = len(state_files) > 0

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
