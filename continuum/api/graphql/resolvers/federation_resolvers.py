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

import strawberry
from strawberry.types import Info

_CREATE_PEERS_TABLE = """
    CREATE TABLE IF NOT EXISTS federation_peers (
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        name TEXT,
        status TEXT DEFAULT 'offline',
        last_sync TEXT,
        shared_memories INTEGER DEFAULT 0,
        trust_score REAL DEFAULT 0.5,
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

        cursor = await conn.execute(
            "SELECT * FROM federation_peers ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()

    peers = []
    for row in rows:
        try:
            status = PeerStatus(row["status"])
        except ValueError:
            status = PeerStatus.OFFLINE

        peers.append(
            FederationPeer(
                id=strawberry.ID(row["id"]),
                url=row["url"],
                name=row["name"],
                status=status,
                last_sync=(
                    datetime.fromisoformat(row["last_sync"])
                    if row["last_sync"]
                    else None
                ),
                shared_memories=row["shared_memories"] or 0,
                trust_score=row["trust_score"] or 0.5,
                metadata=(
                    json.loads(row["metadata"]) if row["metadata"] else None
                ),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        )

    return peers


async def resolve_federation_status(info: Info):
    """Resolve federation status by aggregating peer and sync data."""
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
        await conn.execute(_CREATE_PEERS_TABLE)

        cursor = await conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) AS online,
                MAX(last_sync) AS last_sync,
                SUM(shared_memories) AS synced_memories
            FROM federation_peers
            """
        )
        row = await cursor.fetchone()

        total_peers = row["total"] or 0
        online_peers = row["online"] or 0
        last_sync_raw = row["last_sync"]
        synced_memories = row["synced_memories"] or 0

        # Count pending sync events if that table exists
        pending_sync = 0
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) AS pending FROM sync_events WHERE status = 'pending'"
            )
            pending_row = await cursor.fetchone()
            pending_sync = pending_row["pending"] or 0
        except Exception:
            pass

    last_sync = (
        datetime.fromisoformat(last_sync_raw) if last_sync_raw else None
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
