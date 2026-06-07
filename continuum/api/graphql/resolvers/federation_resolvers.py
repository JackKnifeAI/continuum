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
from typing import List

import strawberry
from strawberry.types import Info

# Peers unseen for longer than this are considered offline.
_ONLINE_THRESHOLD = timedelta(minutes=5)


def _load_federation_states(db_path: str) -> list:
    """Return parsed JSON state dicts from all federation node state files."""
    federation_dir = Path(db_path).parent / "federation"
    if not federation_dir.exists():
        return []

    states = []
    for state_file in federation_dir.glob("*.json"):
        try:
            states.append(json.loads(state_file.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return states


def _parse_dt(value: str) -> datetime | None:
    """Parse an ISO datetime string, attaching UTC timezone if naive."""
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
    """Resolve federation peers from on-disk FederationNode state files."""
    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    states = _load_federation_states(db_path)
    now = datetime.now(timezone.utc)
    peers = []

    seen_peer_ids: set = set()
    for state in states:
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_sync = _parse_dt(peer_data.get("last_seen"))

            if last_sync and now - last_sync < _ONLINE_THRESHOLD:
                status = PeerStatus.ONLINE
            else:
                status = PeerStatus.OFFLINE

            ts = last_sync or now
            peers.append(FederationPeer(
                id=strawberry.ID(peer_id),
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=last_sync,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=ts,
                updated_at=ts,
            ))

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from node state files and sync_events table."""
    from ..types import FederationStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return FederationStatus(
            enabled=False, total_peers=0, online_peers=0,
            last_sync=None, synced_memories=0, pending_sync=0,
        )

    states = _load_federation_states(db_path)
    now = datetime.now(timezone.utc)

    enabled = len(states) > 0
    total_peers = 0
    online_peers = 0
    last_sync: datetime | None = None

    for state in states:
        for peer_data in state.get("peers", {}).values():
            total_peers += 1
            last_seen = _parse_dt(peer_data.get("last_seen"))
            if last_seen:
                if now - last_seen < _ONLINE_THRESHOLD:
                    online_peers += 1
                if last_sync is None or last_seen > last_sync:
                    last_sync = last_seen

        node_last_sync = _parse_dt(state.get("last_sync"))
        if node_last_sync and (last_sync is None or node_last_sync > last_sync):
            last_sync = node_last_sync

    synced_memories = 0
    pending_sync = 0

    try:
        import aiosqlite

        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row

            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_events'"
            )
            if await cursor.fetchone():
                cursor = await conn.execute(
                    "SELECT COUNT(*) AS count FROM sync_events"
                    " WHERE status='synced' AND entity_type='memory'"
                )
                row = await cursor.fetchone()
                synced_memories = row["count"] if row else 0

                cursor = await conn.execute(
                    "SELECT COUNT(*) AS count FROM sync_events WHERE status='pending'"
                )
                row = await cursor.fetchone()
                pending_sync = row["count"] if row else 0
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
