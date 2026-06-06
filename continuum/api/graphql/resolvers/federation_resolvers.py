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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from strawberry.types import Info

# Peers unseen for longer than this are considered offline.
_ONLINE_THRESHOLD = timedelta(minutes=5)


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from local federation state files."""
    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    federation_dir = Path(db_path).parent / "federation"
    if not federation_dir.exists():
        return []

    now = datetime.now(timezone.utc)
    seen_ids: set = set()
    peers: List[FederationPeer] = []

    for state_file in federation_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen_ids:
                continue
            seen_ids.add(peer_id)

            last_seen: Optional[datetime] = None
            last_seen_str = peer_data.get("last_seen")
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                except ValueError:
                    pass

            if last_seen and (now - last_seen) < _ONLINE_THRESHOLD:
                status = PeerStatus.ONLINE
            else:
                status = PeerStatus.OFFLINE

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)

            peers.append(FederationPeer(
                id=peer_id,
                url=f"http://{host}:{port}",
                name=peer_id,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=last_seen or now,
                updated_at=last_seen or now,
            ))

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from env config and local state files."""
    from ..types import FederationStatus

    enabled = os.environ.get("CONTINUUM_ENABLE_FEDERATION", "").lower() == "true"

    db_path = info.context.get("db_path")
    federation_dir = Path(db_path).parent / "federation" if db_path else None

    total_peers = 0
    online_peers = 0
    last_sync: Optional[datetime] = None
    now = datetime.now(timezone.utc)
    seen_ids: set = set()

    if federation_dir and federation_dir.exists():
        for state_file in federation_dir.glob("*.json"):
            try:
                state = json.loads(state_file.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            node_last_sync_str = state.get("last_sync")
            if node_last_sync_str:
                try:
                    node_last_sync = datetime.fromisoformat(node_last_sync_str)
                    if last_sync is None or node_last_sync > last_sync:
                        last_sync = node_last_sync
                except ValueError:
                    pass

            for peer_id, peer_data in state.get("peers", {}).items():
                if peer_id in seen_ids:
                    continue
                seen_ids.add(peer_id)
                total_peers += 1

                last_seen_str = peer_data.get("last_seen")
                if last_seen_str:
                    try:
                        last_seen = datetime.fromisoformat(last_seen_str)
                        if (now - last_seen) < _ONLINE_THRESHOLD:
                            online_peers += 1
                    except ValueError:
                        pass

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
