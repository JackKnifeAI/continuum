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

CREATE_FEDERATION_PEERS_TABLE = """
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
        updated_at TEXT NOT NULL,
        tenant_id TEXT
    )
"""


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        await conn.execute(CREATE_FEDERATION_PEERS_TABLE)
        await conn.commit()

        tenant_id = info.context.get("tenant_id")
        is_admin = info.context.get("is_admin")

        if tenant_id and not is_admin:
            cursor = await conn.execute(
                "SELECT * FROM federation_peers WHERE tenant_id = ?",
                [tenant_id]
            )
        else:
            cursor = await conn.execute("SELECT * FROM federation_peers")

        rows = await cursor.fetchall()

        peers = []
        for row in rows:
            last_sync = (
                datetime.fromisoformat(row["last_sync"])
                if row["last_sync"]
                else None
            )
            metadata = (
                json.loads(row["metadata"])
                if row["metadata"]
                else None
            )
            peers.append(FederationPeer(
                id=row["id"],
                url=row["url"],
                name=row["name"],
                status=PeerStatus(row["status"]),
                last_sync=last_sync,
                shared_memories=row["shared_memories"],
                trust_score=row["trust_score"],
                metadata=metadata,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            ))

        return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
    import aiosqlite

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

        await conn.execute(CREATE_FEDERATION_PEERS_TABLE)
        await conn.commit()

        tenant_id = info.context.get("tenant_id")
        is_admin = info.context.get("is_admin")

        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='online' THEN 1 ELSE 0 END) as online,
                MAX(last_sync) as last_sync,
                SUM(shared_memories) as synced
            FROM federation_peers
        """

        if tenant_id and not is_admin:
            query += " WHERE tenant_id = ?"
            cursor = await conn.execute(query, [tenant_id])
        else:
            cursor = await conn.execute(query)

        row = await cursor.fetchone()

        total_peers = row["total"] or 0
        online_peers = row["online"] or 0
        last_sync = (
            datetime.fromisoformat(row["last_sync"])
            if row["last_sync"]
            else None
        )
        synced_memories = row["synced"] or 0
        enabled = total_peers > 0
        pending_sync = max(0, total_peers - online_peers)

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
