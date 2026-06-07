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

from datetime import datetime
from typing import List

import strawberry
from strawberry.types import Info


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the database."""
    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row

            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='federation_peers'"
            )
            if not await cursor.fetchone():
                return []

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
                    id=strawberry.ID(row["id"]),
                    url=row["url"],
                    name=row["name"],
                    status=PeerStatus(row["status"]),
                    last_sync=datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None,
                    shared_memories=row["shared_memories"] or 0,
                    trust_score=row["trust_score"] or 0.0,
                    metadata=row["metadata"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]
    except Exception:
        return []


async def resolve_federation_status(info: Info):
    """Resolve federation status from peer and sync_events tables."""
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

    try:
        import aiosqlite

        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row

            total_peers = 0
            online_peers = 0

            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='federation_peers'"
            )
            if await cursor.fetchone():
                cursor = await conn.execute("SELECT COUNT(*) as count FROM federation_peers")
                row = await cursor.fetchone()
                total_peers = row["count"] if row else 0

                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM federation_peers WHERE status = 'online'"
                )
                row = await cursor.fetchone()
                online_peers = row["count"] if row else 0

            last_sync = None
            synced_memories = 0
            pending_sync = 0

            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_events'"
            )
            if await cursor.fetchone():
                cursor = await conn.execute(
                    "SELECT MAX(synced_at) as last_sync FROM sync_events WHERE status = 'synced'"
                )
                row = await cursor.fetchone()
                if row and row["last_sync"]:
                    last_sync = datetime.fromisoformat(row["last_sync"])

                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM sync_events"
                    " WHERE status = 'synced' AND entity_type = 'memory'"
                )
                row = await cursor.fetchone()
                synced_memories = row["count"] if row else 0

                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM sync_events"
                    " WHERE status = 'pending' AND entity_type = 'memory'"
                )
                row = await cursor.fetchone()
                pending_sync = row["count"] if row else 0

            return FederationStatus(
                enabled=total_peers > 0 or synced_memories > 0,
                total_peers=total_peers,
                online_peers=online_peers,
                last_sync=last_sync,
                synced_memories=synced_memories,
                pending_sync=pending_sync,
            )
    except Exception:
        return FederationStatus(
            enabled=False,
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
