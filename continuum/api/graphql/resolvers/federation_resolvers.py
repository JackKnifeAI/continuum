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

from typing import List

from strawberry.types import Info


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    import json
    from datetime import datetime

    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = getattr(info.context, "db_path", None)
    tenant_id = getattr(info.context, "tenant_id", None)

    if not db_path or not tenant_id:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS federation_peers (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
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
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_federation_peers_tenant_id
            ON federation_peers (tenant_id)
            """
        )
        await conn.commit()

        cursor = await conn.execute(
            """
            SELECT id, url, name, status, last_sync, shared_memories,
                   trust_score, metadata, created_at, updated_at
            FROM federation_peers
            WHERE tenant_id = ?
            ORDER BY created_at DESC
            """,
            (tenant_id,),
        )
        rows = await cursor.fetchall()

    peers = []
    for row in rows:
        last_sync = None
        if row["last_sync"]:
            try:
                last_sync = datetime.fromisoformat(row["last_sync"])
            except (ValueError, TypeError):
                last_sync = None

        created_at = datetime.fromisoformat(row["created_at"])
        updated_at = datetime.fromisoformat(row["updated_at"])

        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except (ValueError, TypeError):
                metadata = None

        try:
            status = PeerStatus(row["status"])
        except ValueError:
            status = PeerStatus.OFFLINE

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


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
    from datetime import datetime

    import aiosqlite

    from ..types import FederationStatus

    db_path = getattr(info.context, "db_path", None)
    tenant_id = getattr(info.context, "tenant_id", None)

    if not db_path or not tenant_id:
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

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS federation_peers (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
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
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS federation_preferences (
                tenant_id TEXT PRIMARY KEY,
                tier TEXT NOT NULL DEFAULT 'free',
                opted_out INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await conn.commit()

        pref_cursor = await conn.execute(
            """
            SELECT tier, opted_out
            FROM federation_preferences
            WHERE tenant_id = ?
            """,
            (tenant_id,),
        )
        pref_row = await pref_cursor.fetchone()

        enabled = False
        if pref_row is not None:
            tier = pref_row["tier"]
            opted_out = pref_row["opted_out"]
            enabled = tier in ("pro", "enterprise") and not opted_out

        total_cursor = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM federation_peers WHERE tenant_id = ?",
            (tenant_id,),
        )
        total_row = await total_cursor.fetchone()
        total_peers = total_row["cnt"] if total_row else 0

        online_cursor = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM federation_peers WHERE tenant_id = ? AND status = 'online'",
            (tenant_id,),
        )
        online_row = await online_cursor.fetchone()
        online_peers = online_row["cnt"] if online_row else 0

        agg_cursor = await conn.execute(
            "SELECT MAX(last_sync) AS max_sync, SUM(shared_memories) AS total_shared FROM federation_peers WHERE tenant_id = ?",
            (tenant_id,),
        )
        agg_row = await agg_cursor.fetchone()

        last_sync = None
        synced_memories = 0
        if agg_row is not None:
            if agg_row["max_sync"]:
                try:
                    last_sync = datetime.fromisoformat(agg_row["max_sync"])
                except (ValueError, TypeError):
                    last_sync = None
            if agg_row["total_shared"] is not None:
                synced_memories = agg_row["total_shared"]

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
