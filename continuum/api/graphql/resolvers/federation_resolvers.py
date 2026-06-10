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
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from strawberry.types import Info

from ..types import FederationPeer, FederationStatus, PeerStatus

# Peer is considered online if last seen within this many seconds
_ONLINE_THRESHOLD_SECONDS = 300


async def resolve_federation_peers(info: Info) -> List[FederationPeer]:
    """Resolve federation peers from stored federation node state."""
    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return []

    storage_path = Path(db_path).parent / "federation"
    if not storage_path.exists():
        return []

    peers: List[FederationPeer] = []
    now = datetime.now(timezone.utc)

    for state_file in storage_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            for peer_id, peer_data in state.get("peers", {}).items():
                last_seen_str = peer_data.get("last_seen")
                last_seen = (
                    datetime.fromisoformat(last_seen_str) if last_seen_str else None
                )

                if last_seen:
                    age = (now - last_seen).total_seconds()
                    status = (
                        PeerStatus.ONLINE
                        if age < _ONLINE_THRESHOLD_SECONDS
                        else PeerStatus.OFFLINE
                    )
                else:
                    status = PeerStatus.OFFLINE

                host = peer_data.get("host", "unknown")
                port = peer_data.get("port", 0)

                peers.append(
                    FederationPeer(
                        id=peer_id,
                        url=f"http://{host}:{port}",
                        name=peer_id,
                        status=status,
                        last_sync=last_seen,
                        shared_memories=0,
                        trust_score=0.5,
                        metadata=None,
                        created_at=last_seen or now,
                        updated_at=last_seen or now,
                    )
                )
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    return peers


async def resolve_federation_status(info: Info) -> FederationStatus:
    """Resolve federation status from stored node state and environment config."""
    enabled = os.getenv("CONTINUUM_ENABLE_FEDERATION", "").lower() == "true"
    db_path = getattr(info.context, "db_path", None)

    if not db_path:
        return FederationStatus(
            enabled=enabled,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    storage_path = Path(db_path).parent / "federation"
    if not storage_path.exists():
        return FederationStatus(
            enabled=enabled,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    total_peers = 0
    online_peers = 0
    last_sync: datetime | None = None
    now = datetime.now(timezone.utc)

    for state_file in storage_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            peers = state.get("peers", {})
            total_peers += len(peers)

            for peer_data in peers.values():
                last_seen_str = peer_data.get("last_seen")
                if last_seen_str:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if (now - last_seen).total_seconds() < _ONLINE_THRESHOLD_SECONDS:
                        online_peers += 1

            node_last_sync_str = state.get("last_sync")
            if node_last_sync_str:
                node_last_sync = datetime.fromisoformat(node_last_sync_str)
                if last_sync is None or node_last_sync > last_sync:
                    last_sync = node_last_sync
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    return FederationStatus(
        enabled=enabled or total_peers > 0,
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
