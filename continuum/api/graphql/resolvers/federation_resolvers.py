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
from typing import List

from strawberry.types import Info

_CREATE_PEERS_TABLE = """
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


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the local database."""
    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(_CREATE_PEERS_TABLE)
        await conn.commit()

        cursor = await conn.execute(
            """
            SELECT id, url, name, status, last_sync, shared_memories,
                   trust_score, metadata, created_at, updated_at
            FROM federation_peers
            ORDER BY created_at DESC
            """
        )
        rows = await cursor.fetchall()

    return [
        FederationPeer(
            id=row["id"],
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
        for row in rows
    ]


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating peer data from the local database."""
    import aiosqlite

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
        conn.row_factory = aiosqlite.Row
        await conn.execute(_CREATE_PEERS_TABLE)
        await conn.commit()

        cursor = await conn.execute("SELECT COUNT(*) AS count FROM federation_peers")
        row = await cursor.fetchone()
        total_peers = row["count"] if row else 0

        cursor = await conn.execute(
            "SELECT COUNT(*) AS count FROM federation_peers WHERE status = ?",
            [PeerStatus.ONLINE.value],
        )
        row = await cursor.fetchone()
        online_peers = row["count"] if row else 0

        cursor = await conn.execute(
            "SELECT MAX(last_sync) AS last_sync FROM federation_peers WHERE last_sync IS NOT NULL"
        )
        row = await cursor.fetchone()
        last_sync_str = row["last_sync"] if row else None
        last_sync = datetime.fromisoformat(last_sync_str) if last_sync_str else None

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(shared_memories), 0) AS total FROM federation_peers"
        )
        row = await cursor.fetchone()
        synced_memories = row["total"] if row else 0

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
