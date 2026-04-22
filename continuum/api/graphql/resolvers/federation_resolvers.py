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


async def _ensure_federation_peers_table(conn: aiosqlite.Connection) -> None:
    """Create federation_peers table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS federation_peers (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            name TEXT,
            status TEXT NOT NULL DEFAULT 'offline',
            last_sync TEXT,
            shared_memories INTEGER NOT NULL DEFAULT 0,
            trust_score REAL NOT NULL DEFAULT 1.0,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    await conn.commit()


def _parse_peer_row(row: aiosqlite.Row):
    """Convert a database row into a FederationPeer object."""
    from ..types import FederationPeer, PeerStatus

    status_map = {
        "online": PeerStatus.ONLINE,
        "offline": PeerStatus.OFFLINE,
        "syncing": PeerStatus.SYNCING,
        "unreachable": PeerStatus.UNREACHABLE,
        "blocked": PeerStatus.BLOCKED,
    }

    last_sync: Optional[datetime] = None
    if row["last_sync"]:
        try:
            last_sync = datetime.fromisoformat(row["last_sync"])
        except ValueError:
            pass

    metadata = None
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass

    return FederationPeer(
        id=row["id"],
        url=row["url"],
        name=row["name"],
        status=status_map.get(row["status"], PeerStatus.OFFLINE),
        last_sync=last_sync,
        shared_memories=row["shared_memories"],
        trust_score=row["trust_score"],
        metadata=metadata,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers by querying the local federation_peers table."""
    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return []

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await _ensure_federation_peers_table(conn)

            cursor = await conn.execute("""
                SELECT id, url, name, status, last_sync, shared_memories,
                       trust_score, metadata, created_at, updated_at
                FROM federation_peers
                ORDER BY trust_score DESC, created_at ASC
            """)
            rows = await cursor.fetchall()
            return [_parse_peer_row(row) for row in rows]
    except Exception:
        return []


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating peer data and config settings."""
    from continuum.core.config import get_config

    from ..types import FederationStatus

    config = get_config()
    db_path = getattr(info.context, "db_path", None)

    # Determine if federation is enabled from environment/config
    federation_enabled = bool(
        getattr(config, "federation_enabled", False)
        or getattr(config, "federation_url", None)
    )

    if not db_path:
        return FederationStatus(
            enabled=federation_enabled,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await _ensure_federation_peers_table(conn)

            # Aggregate peer counts
            cursor = await conn.execute("""
                SELECT
                    COUNT(*) AS total_peers,
                    SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) AS online_peers,
                    MAX(last_sync) AS last_sync,
                    SUM(shared_memories) AS synced_memories,
                    SUM(CASE WHEN status NOT IN ('online', 'syncing') THEN 1 ELSE 0 END) AS pending_sync
                FROM federation_peers
            """)
            row = await cursor.fetchone()

        total_peers = row["total_peers"] or 0
        online_peers = row["online_peers"] or 0
        synced_memories = row["synced_memories"] or 0
        pending_sync = row["pending_sync"] or 0

        last_sync: Optional[datetime] = None
        if row["last_sync"]:
            try:
                last_sync = datetime.fromisoformat(row["last_sync"])
            except ValueError:
                pass

        return FederationStatus(
            enabled=federation_enabled,
            total_peers=total_peers,
            online_peers=online_peers,
            last_sync=last_sync,
            synced_memories=synced_memories,
            pending_sync=pending_sync,
        )
    except Exception:
        return FederationStatus(
            enabled=federation_enabled,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
