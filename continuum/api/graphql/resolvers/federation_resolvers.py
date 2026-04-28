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
from typing import List, Optional

import strawberry
from strawberry.types import Info

_ONLINE_THRESHOLD = timedelta(minutes=5)


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from persisted node state."""
    from continuum.core.config import get_config

    from ..types import FederationPeer, PeerStatus

    config = get_config()
    federation_path = config.db_path.parent / "federation"

    if not federation_path.exists():
        return []

    peers = []
    now = datetime.now(timezone.utc)

    for state_file in federation_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for peer_id, peer_data in state.get("peers", {}).items():
            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen_str = peer_data.get("last_seen")

            peer_last_seen: Optional[datetime] = None
            status = PeerStatus.OFFLINE
            if last_seen_str:
                try:
                    peer_last_seen = datetime.fromisoformat(last_seen_str)
                    if (now - peer_last_seen) < _ONLINE_THRESHOLD:
                        status = PeerStatus.ONLINE
                except ValueError:
                    pass

            peers.append(FederationPeer(
                id=strawberry.ID(peer_id),
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=peer_last_seen,
                shared_memories=0,
                trust_score=0.5,
                metadata=None,
                created_at=peer_last_seen or now,
                updated_at=peer_last_seen or now,
            ))

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from node state and sync event counts."""
    import aiosqlite

    from continuum.core.config import get_config

    from ..types import FederationStatus

    config = get_config()
    federation_path = config.db_path.parent / "federation"

    enabled = False
    total_peers = 0
    online_peers = 0
    last_sync: Optional[datetime] = None
    now = datetime.now(timezone.utc)

    if federation_path.exists():
        for state_file in federation_path.glob("*.json"):
            try:
                state = json.loads(state_file.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            enabled = enabled or bool(state.get("registered", False))

            node_peers = state.get("peers", {})
            total_peers += len(node_peers)

            last_sync_str = state.get("last_sync")
            if last_sync_str:
                try:
                    candidate = datetime.fromisoformat(last_sync_str)
                    if last_sync is None or candidate > last_sync:
                        last_sync = candidate
                except ValueError:
                    pass

            for peer_data in node_peers.values():
                last_seen_str = peer_data.get("last_seen")
                if last_seen_str:
                    try:
                        peer_last_seen = datetime.fromisoformat(last_seen_str)
                        if (now - peer_last_seen) < _ONLINE_THRESHOLD:
                            online_peers += 1
                    except ValueError:
                        pass

    synced_memories = 0
    pending_sync = 0
    db_path = info.context.get("db_path") or str(config.db_path)
    try:
        async with aiosqlite.connect(db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM sync_events WHERE status = 'synced'"
            )
            row = await cursor.fetchone()
            if row:
                synced_memories = row[0]

            cursor = await conn.execute(
                "SELECT COUNT(*) FROM sync_events WHERE status = 'pending'"
            )
            row = await cursor.fetchone()
            if row:
                pending_sync = row[0]
    except Exception:
        pass

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=last_sync,
        synced_memories=synced_memories,
        pending_sync=pending_sync,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
