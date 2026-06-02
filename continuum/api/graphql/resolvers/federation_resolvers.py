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

_CREATE_PEERS_TABLE = """
    CREATE TABLE IF NOT EXISTS federation_peers (
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        name TEXT,
        status TEXT NOT NULL DEFAULT 'offline',
        last_sync TEXT,
        shared_memories INTEGER DEFAULT 0,
        trust_score REAL DEFAULT 0.5,
        metadata TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'default'
    )
"""

_CREATE_PEERS_IDX_TENANT = """
    CREATE INDEX IF NOT EXISTS idx_federation_peers_tenant
    ON federation_peers(tenant_id)
"""

_CREATE_PEERS_IDX_STATUS = """
    CREATE INDEX IF NOT EXISTS idx_federation_peers_status
    ON federation_peers(status, tenant_id)
"""


async def _ensure_peers_table(conn: aiosqlite.Connection) -> None:
    """Create the federation_peers table and indexes if they don't exist."""
    await conn.execute(_CREATE_PEERS_TABLE)
    await conn.execute(_CREATE_PEERS_IDX_TENANT)
    await conn.execute(_CREATE_PEERS_IDX_STATUS)
    await conn.commit()


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the database."""
    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    tenant_id = getattr(info.context, "tenant_id", None) or "default"

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_peers_table(conn)

        cursor = await conn.execute(
            """
            SELECT id, url, name, status, last_sync, shared_memories,
                   trust_score, metadata, created_at, updated_at
            FROM federation_peers
            WHERE tenant_id = ?
            ORDER BY created_at DESC
            """,
            [tenant_id],
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
    """Resolve federation status aggregated from all peers."""
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

    tenant_id = getattr(info.context, "tenant_id", None) or "default"

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_peers_table(conn)

        cursor = await conn.execute(
            """
            SELECT
                COUNT(*) AS total_peers,
                SUM(CASE WHEN status IN ('online', 'syncing') THEN 1 ELSE 0 END) AS online_peers,
                MAX(last_sync) AS last_sync,
                SUM(shared_memories) AS synced_memories,
                SUM(CASE WHEN status = 'syncing' THEN 1 ELSE 0 END) AS pending_sync
            FROM federation_peers
            WHERE tenant_id = ?
            """,
            [tenant_id],
        )
        row = await cursor.fetchone()

    total_peers: int = row["total_peers"] or 0
    online_peers: int = row["online_peers"] or 0
    last_sync: Optional[datetime] = (
        datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None
    )
    synced_memories: int = row["synced_memories"] or 0
    pending_sync: int = row["pending_sync"] or 0

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
