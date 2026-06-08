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
import strawberry
from strawberry.types import Info

_ENSURE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS federation_peers (
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        name TEXT,
        status TEXT NOT NULL DEFAULT 'offline',
        last_sync TEXT,
        shared_memories INTEGER NOT NULL DEFAULT 0,
        trust_score REAL NOT NULL DEFAULT 0.0,
        metadata TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
"""


async def _ensure_federation_table(conn: aiosqlite.Connection) -> None:
    await conn.execute(_ENSURE_TABLE_SQL)
    await conn.commit()


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the SQLite database."""
    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_federation_table(conn)

        cursor = await conn.execute(
            "SELECT id, url, name, status, last_sync, shared_memories, "
            "trust_score, metadata, created_at, updated_at "
            "FROM federation_peers ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()

    peers = []
    for row in rows:
        peers.append(
            FederationPeer(
                id=strawberry.ID(row["id"]),
                url=row["url"],
                name=row["name"],
                status=PeerStatus(row["status"]),
                last_sync=datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None,
                shared_memories=row["shared_memories"],
                trust_score=row["trust_score"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from the SQLite database."""
    from ..types import FederationStatus

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

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_federation_table(conn)

        agg_cursor = await conn.execute(
            "SELECT "
            "  COUNT(*) AS total, "
            "  SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) AS online_count, "
            "  MAX(last_sync) AS latest_sync, "
            "  SUM(shared_memories) AS total_synced, "
            "  SUM(CASE WHEN status IN ('offline', 'unreachable') AND shared_memories > 0 THEN 1 ELSE 0 END) AS pending "
            "FROM federation_peers"
        )
        row = await agg_cursor.fetchone()

    total_peers: int = row["total"] or 0
    online_peers: int = row["online_count"] or 0
    synced_memories: int = row["total_synced"] or 0
    pending_sync: int = row["pending"] or 0
    last_sync: Optional[datetime] = (
        datetime.fromisoformat(row["latest_sync"]) if row["latest_sync"] else None
    )

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
