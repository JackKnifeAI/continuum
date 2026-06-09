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


async def _ensure_federation_table(conn: aiosqlite.Connection) -> None:
    """Create the federation_peers table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS federation_peers (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            name TEXT,
            status TEXT NOT NULL DEFAULT 'offline',
            last_sync TEXT,
            shared_memories INTEGER NOT NULL DEFAULT 0,
            trust_score REAL NOT NULL DEFAULT 0.5,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    await conn.commit()


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers by querying the federation_peers table."""
    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        await _ensure_federation_table(conn)
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM federation_peers ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()

    peers = []
    for row in rows:
        try:
            status = PeerStatus(row["status"])
        except ValueError:
            status = PeerStatus.OFFLINE

        peers.append(FederationPeer(
            id=strawberry.ID(row["id"]),
            url=row["url"],
            name=row["name"],
            status=status,
            last_sync=datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None,
            shared_memories=row["shared_memories"] or 0,
            trust_score=row["trust_score"] or 0.0,
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        ))

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating the federation_peers table."""
    from ..types import FederationStatus, PeerStatus

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
        await _ensure_federation_table(conn)

        async with conn.execute("SELECT COUNT(*) FROM federation_peers") as cursor:
            total_peers: int = (await cursor.fetchone())[0]

        async with conn.execute(
            "SELECT COUNT(*) FROM federation_peers WHERE status = ?",
            (PeerStatus.ONLINE.value,),
        ) as cursor:
            online_peers: int = (await cursor.fetchone())[0]

        async with conn.execute(
            "SELECT MAX(last_sync) FROM federation_peers"
        ) as cursor:
            last_sync_row = await cursor.fetchone()
            last_sync: Optional[datetime] = (
                datetime.fromisoformat(last_sync_row[0])
                if last_sync_row and last_sync_row[0]
                else None
            )

        async with conn.execute(
            "SELECT COALESCE(SUM(shared_memories), 0) FROM federation_peers"
        ) as cursor:
            synced_memories: int = (await cursor.fetchone())[0]

    return FederationStatus(
        enabled=total_peers > 0,
        total_peers=total_peers,
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
