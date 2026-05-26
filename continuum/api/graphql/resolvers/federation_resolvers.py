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


async def _ensure_federation_table(conn: aiosqlite.Connection) -> None:
    await conn.execute(_CREATE_FEDERATION_PEERS_TABLE)
    await conn.commit()


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the local SQLite database."""
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
        last_sync = None
        if row["last_sync"]:
            try:
                last_sync = datetime.fromisoformat(row["last_sync"])
            except ValueError:
                pass

        try:
            status = PeerStatus(row["status"])
        except ValueError:
            status = PeerStatus.OFFLINE

        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass

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
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        )
    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from peer counts and sync event state."""
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

        cursor = await conn.execute("SELECT COUNT(*) as total FROM federation_peers")
        row = await cursor.fetchone()
        total_peers = row["total"] if row else 0

        cursor = await conn.execute(
            "SELECT COUNT(*) as online FROM federation_peers WHERE status = 'online'"
        )
        row = await cursor.fetchone()
        online_peers = row["online"] if row else 0

        cursor = await conn.execute(
            "SELECT MAX(last_sync) as last_sync "
            "FROM federation_peers WHERE last_sync IS NOT NULL"
        )
        row = await cursor.fetchone()
        last_sync = None
        if row and row["last_sync"]:
            try:
                last_sync = datetime.fromisoformat(row["last_sync"])
            except ValueError:
                pass

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(shared_memories), 0) as synced FROM federation_peers"
        )
        row = await cursor.fetchone()
        synced_memories = int(row["synced"]) if row else 0

        pending_sync = 0
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as pending FROM sync_events WHERE status = 'pending'"
            )
            row = await cursor.fetchone()
            pending_sync = row["pending"] if row else 0
        except aiosqlite.OperationalError:
            pass

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
