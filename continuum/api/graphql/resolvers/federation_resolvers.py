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

from ..types import FederationPeer, FederationStatus, PeerStatus

CREATE_FEDERATION_PEERS_TABLE = """
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
    updated_at TEXT NOT NULL,
    tenant_id TEXT
)
"""


async def resolve_federation_peers(info: Info) -> List[FederationPeer]:
    """Resolve federation peers"""
    db_path = info.context.get("db_path")
    if db_path is None:
        return []

    tenant_id = info.context.get("tenant_id", "default")

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(CREATE_FEDERATION_PEERS_TABLE)
        await conn.commit()

        cursor = await conn.execute(
            "SELECT * FROM federation_peers WHERE tenant_id = ?",
            (tenant_id,),
        )
        rows = await cursor.fetchall()

    peers: List[FederationPeer] = []
    for row in rows:
        try:
            status = PeerStatus(row["status"])
        except ValueError:
            status = PeerStatus.OFFLINE

        last_sync: Optional[datetime] = None
        if row["last_sync"]:
            try:
                last_sync = datetime.fromisoformat(row["last_sync"])
            except ValueError:
                last_sync = None

        try:
            created_at = datetime.fromisoformat(row["created_at"])
        except (ValueError, TypeError):
            created_at = datetime.utcnow()

        try:
            updated_at = datetime.fromisoformat(row["updated_at"])
        except (ValueError, TypeError):
            updated_at = datetime.utcnow()

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
                last_sync=last_sync,
                shared_memories=row["shared_memories"],
                trust_score=row["trust_score"],
                metadata=metadata,
                created_at=created_at,
                updated_at=updated_at,
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> FederationStatus:
    """Resolve federation status"""
    db_path = info.context.get("db_path")
    if db_path is None:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    tenant_id = info.context.get("tenant_id", "default")

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(CREATE_FEDERATION_PEERS_TABLE)
        await conn.commit()

        cursor = await conn.execute(
            "SELECT COUNT(*) AS total FROM federation_peers WHERE tenant_id = ?",
            (tenant_id,),
        )
        total_row = await cursor.fetchone()
        total_peers: int = total_row["total"] if total_row else 0

        cursor = await conn.execute(
            "SELECT COUNT(*) AS online FROM federation_peers WHERE tenant_id = ? AND status = 'online'",
            (tenant_id,),
        )
        online_row = await cursor.fetchone()
        online_peers: int = online_row["online"] if online_row else 0

        cursor = await conn.execute(
            "SELECT MAX(last_sync) AS max_sync FROM federation_peers WHERE tenant_id = ?",
            (tenant_id,),
        )
        sync_row = await cursor.fetchone()
        last_sync: Optional[datetime] = None
        if sync_row and sync_row["max_sync"]:
            try:
                last_sync = datetime.fromisoformat(sync_row["max_sync"])
            except ValueError:
                last_sync = None

        cursor = await conn.execute(
            "SELECT SUM(shared_memories) AS total_synced FROM federation_peers WHERE tenant_id = ?",
            (tenant_id,),
        )
        synced_row = await cursor.fetchone()
        synced_memories: int = synced_row["total_synced"] if (synced_row and synced_row["total_synced"] is not None) else 0

    enabled = total_peers > 0

    return FederationStatus(
        enabled=enabled,
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
