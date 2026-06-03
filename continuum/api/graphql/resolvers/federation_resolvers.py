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
from datetime import datetime
from typing import List, Optional

import aiosqlite
from strawberry.types import Info

_INIT_DDL = """
CREATE TABLE IF NOT EXISTS federation_peers (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    name TEXT,
    status TEXT NOT NULL DEFAULT 'offline',
    last_sync TEXT,
    shared_memories INTEGER NOT NULL DEFAULT 0,
    trust_score REAL NOT NULL DEFAULT 0.5,
    metadata TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_SYNC_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS federation_sync_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_id TEXT NOT NULL,
    memories_synced INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
)
"""


async def _ensure_tables(conn: aiosqlite.Connection) -> None:
    await conn.execute(_INIT_DDL)
    await conn.execute(_SYNC_EVENTS_DDL)
    await conn.commit()


def _row_to_peer(row: aiosqlite.Row):
    from ..types import FederationPeer, PeerStatus

    raw_meta = row["metadata"]
    metadata = json.loads(raw_meta) if raw_meta else None

    last_sync: Optional[datetime] = None
    if row["last_sync"]:
        try:
            last_sync = datetime.fromisoformat(row["last_sync"])
        except ValueError:
            pass

    status_val = row["status"] if row["status"] in {s.value for s in PeerStatus} else PeerStatus.OFFLINE.value
    status = PeerStatus(status_val)

    return FederationPeer(
        id=row["id"],
        url=row["url"],
        name=row["name"],
        status=status,
        last_sync=last_sync,
        shared_memories=row["shared_memories"],
        trust_score=row["trust_score"],
        metadata=metadata,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the local database."""
    from ..types import FederationPeer

    db_path: Optional[str] = getattr(info.context, "db_path", None)
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_tables(conn)

        cursor = await conn.execute(
            "SELECT * FROM federation_peers ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()

    peers: List[FederationPeer] = []
    for row in rows:
        try:
            peers.append(_row_to_peer(row))
        except Exception:
            continue

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating peer data from the local database."""
    from ..types import FederationStatus, PeerStatus

    db_path: Optional[str] = getattr(info.context, "db_path", None)
    if not db_path:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_tables(conn)

        total_row = await (await conn.execute("SELECT COUNT(*) AS cnt FROM federation_peers")).fetchone()
        total_peers: int = total_row["cnt"] if total_row else 0

        online_statuses = ", ".join(f"'{s}'" for s in (PeerStatus.ONLINE.value, PeerStatus.SYNCING.value))
        online_row = await (
            await conn.execute(
                f"SELECT COUNT(*) AS cnt FROM federation_peers WHERE status IN ({online_statuses})"
            )
        ).fetchone()
        online_peers: int = online_row["cnt"] if online_row else 0

        last_sync_row = await (
            await conn.execute(
                "SELECT MAX(last_sync) AS ls FROM federation_peers WHERE last_sync IS NOT NULL"
            )
        ).fetchone()
        last_sync: Optional[datetime] = None
        if last_sync_row and last_sync_row["ls"]:
            try:
                last_sync = datetime.fromisoformat(last_sync_row["ls"])
            except ValueError:
                pass

        synced_row = await (
            await conn.execute(
                "SELECT COALESCE(SUM(memories_synced), 0) AS total FROM federation_sync_events WHERE status = 'completed'"
            )
        ).fetchone()
        synced_memories: int = synced_row["total"] if synced_row else 0

        pending_row = await (
            await conn.execute(
                "SELECT COUNT(*) AS cnt FROM federation_sync_events WHERE status = 'pending'"
            )
        ).fetchone()
        pending_sync: int = pending_row["cnt"] if pending_row else 0

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
