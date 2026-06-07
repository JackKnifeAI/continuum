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

_CREATE_FEDERATION_PEERS_TABLE = """
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


async def _ensure_table(conn: aiosqlite.Connection) -> None:
    await conn.execute(_CREATE_FEDERATION_PEERS_TABLE)


def _parse_peer_row(row: aiosqlite.Row):
    from ..types import FederationPeer, PeerStatus

    raw_meta = row["metadata"]
    metadata: Optional[dict] = None
    if raw_meta:
        try:
            metadata = json.loads(raw_meta)
        except (json.JSONDecodeError, TypeError):
            pass

    return FederationPeer(
        id=str(row["id"]),
        url=row["url"],
        name=row["name"],
        status=PeerStatus(row["status"]),
        last_sync=datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None,
        shared_memories=row["shared_memories"],
        trust_score=row["trust_score"],
        metadata=metadata,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the database."""
    db_path = info.context["db_path"]
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_table(conn)

        cursor = await conn.execute(
            "SELECT id, url, name, status, last_sync, shared_memories,"
            " trust_score, metadata, created_at, updated_at"
            " FROM federation_peers ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()

    return [_parse_peer_row(row) for row in rows]


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating peer data from the database."""
    from ..types import FederationStatus

    db_path = info.context["db_path"]
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
        await _ensure_table(conn)

        row = await (await conn.execute("SELECT COUNT(*) FROM federation_peers")).fetchone()
        total_peers: int = row[0]

        row = await (
            await conn.execute(
                "SELECT COUNT(*) FROM federation_peers WHERE status = 'online'"
            )
        ).fetchone()
        online_peers: int = row[0]

        row = await (
            await conn.execute(
                "SELECT MAX(last_sync) FROM federation_peers WHERE last_sync IS NOT NULL"
            )
        ).fetchone()
        last_sync: Optional[datetime] = (
            datetime.fromisoformat(row[0]) if row[0] else None
        )

        row = await (
            await conn.execute(
                "SELECT COALESCE(SUM(shared_memories), 0) FROM federation_peers"
            )
        ).fetchone()
        synced_memories: int = row[0]

        row = await (
            await conn.execute(
                "SELECT COUNT(*) FROM federation_peers"
                " WHERE status IN ('offline', 'unreachable') AND last_sync IS NOT NULL"
            )
        ).fetchone()
        pending_sync: int = row[0]

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
