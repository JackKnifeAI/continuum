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

import aiosqlite
from strawberry.types import Info

_ONLINE_THRESHOLD = timedelta(minutes=5)

_SYNC_EVENTS_DDL = """
    CREATE TABLE IF NOT EXISTS sync_events (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        source_instance TEXT,
        target_instance TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        synced_at TEXT,
        error_message TEXT
    )
"""


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from local node state files."""
    from ..types import FederationPeer, PeerStatus

    context = info.context
    db_path = getattr(context, "db_path", None)
    if not db_path:
        return []

    federation_dir = Path(db_path).parent / "federation"
    if not federation_dir.exists():
        return []

    now = datetime.now(timezone.utc)
    seen_ids: set = set()
    peers = []

    for state_file in federation_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            continue

        for peer_id, peer_info in state.get("peers", {}).items():
            if peer_id in seen_ids:
                continue
            seen_ids.add(peer_id)

            last_seen: Optional[datetime] = None
            last_seen_str = peer_info.get("last_seen")
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            if last_seen and (now - last_seen) < _ONLINE_THRESHOLD:
                status = PeerStatus.ONLINE
            elif last_seen:
                status = PeerStatus.OFFLINE
            else:
                status = PeerStatus.UNREACHABLE

            host = peer_info.get("host", "unknown")
            port = peer_info.get("port", 0)
            ts = last_seen or now

            peers.append(
                FederationPeer(
                    id=str(peer_id),
                    url=f"http://{host}:{port}",
                    name=peer_id,
                    status=status,
                    last_sync=last_seen,
                    shared_memories=0,
                    trust_score=0.5,
                    metadata=None,
                    created_at=ts,
                    updated_at=ts,
                )
            )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from peer state and local sync history."""
    from ..types import FederationStatus, PeerStatus

    peers = await resolve_federation_peers(info)
    total_peers = len(peers)
    online_peers = sum(1 for p in peers if p.status == PeerStatus.ONLINE)
    last_sync: Optional[datetime] = max(
        (p.last_sync for p in peers if p.last_sync), default=None
    )

    synced_memories = 0
    pending_sync = 0
    context = info.context
    db_path = getattr(context, "db_path", None)
    if db_path:
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute(_SYNC_EVENTS_DDL)
                cursor = await conn.execute(
                    "SELECT status, COUNT(*) FROM sync_events GROUP BY status"
                )
                for row in await cursor.fetchall():
                    if row[0] == "synced":
                        synced_memories = row[1]
                    elif row[0] == "pending":
                        pending_sync = row[1]
        except Exception:
            pass

    return FederationStatus(
        enabled=total_peers > 0,
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
