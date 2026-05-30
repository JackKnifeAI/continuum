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


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers by querying the local federation_peers table."""
    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(_CREATE_FEDERATION_PEERS_TABLE)

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

        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                metadata = None

        peers.append(
            FederationPeer(
                id=row["id"],
                url=row["url"],
                name=row["name"],
                status=status,
                last_sync=_parse_dt(row["last_sync"]),
                shared_memories=row["shared_memories"] or 0,
                trust_score=row["trust_score"] or 0.5,
                metadata=metadata,
                created_at=_parse_dt(row["created_at"]) or datetime.utcnow(),
                updated_at=_parse_dt(row["updated_at"]) or datetime.utcnow(),
            )
        )

    return peers


async def resolve_federation_status(info: Info):
    """Resolve overall federation status from the local federation_peers table."""
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
        await conn.execute(_CREATE_FEDERATION_PEERS_TABLE)

        cursor = await conn.execute(
            """
            SELECT
                COUNT(*) AS total_peers,
                SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) AS online_peers,
                SUM(shared_memories) AS synced_memories,
                MAX(last_sync) AS last_sync,
                SUM(CASE WHEN status = 'syncing' OR last_sync IS NULL THEN 1 ELSE 0 END) AS pending_sync
            FROM federation_peers
            """
        )
        row = await cursor.fetchone()

    total_peers = row["total_peers"] or 0
    return FederationStatus(
        enabled=total_peers > 0,
        total_peers=total_peers,
        online_peers=row["online_peers"] or 0,
        last_sync=_parse_dt(row["last_sync"]),
        synced_memories=row["synced_memories"] or 0,
        pending_sync=row["pending_sync"] or 0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
