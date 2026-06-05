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


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the database"""
    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT id, url, name, status, last_sync, shared_memories,
                       trust_score, metadata, created_at, updated_at
                FROM federation_peers
                ORDER BY created_at DESC
                """
            )
            rows = await cursor.fetchall()

        peers = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else None
            last_sync: Optional[datetime] = None
            if row["last_sync"]:
                try:
                    last_sync = datetime.fromisoformat(row["last_sync"])
                except ValueError:
                    pass
            peers.append(
                FederationPeer(
                    id=row["id"],
                    url=row["url"],
                    name=row["name"],
                    status=PeerStatus(row["status"]),
                    last_sync=last_sync,
                    shared_memories=row["shared_memories"] or 0,
                    trust_score=row["trust_score"] or 0.0,
                    metadata=metadata,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return peers
    except Exception:
        # federation_peers table may not exist yet
        return []


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from the database"""
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

    total_peers = 0
    online_peers = 0
    last_sync: Optional[datetime] = None
    synced_memories = 0
    pending_sync = 0

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row

            cursor = await conn.execute(
                "SELECT COUNT(*) AS total FROM federation_peers"
            )
            row = await cursor.fetchone()
            total_peers = row["total"] if row else 0

            cursor = await conn.execute(
                "SELECT COUNT(*) AS online FROM federation_peers WHERE status = ?",
                ["online"],
            )
            row = await cursor.fetchone()
            online_peers = row["online"] if row else 0
    except Exception:
        pass  # federation_peers table may not exist yet

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row

            cursor = await conn.execute(
                "SELECT COUNT(*) AS cnt FROM sync_events"
                " WHERE status = ? AND entity_type = ?",
                ["synced", "memory"],
            )
            row = await cursor.fetchone()
            synced_memories = row["cnt"] if row else 0

            cursor = await conn.execute(
                "SELECT COUNT(*) AS cnt FROM sync_events WHERE status = ?",
                ["pending"],
            )
            row = await cursor.fetchone()
            pending_sync = row["cnt"] if row else 0

            cursor = await conn.execute(
                "SELECT MAX(synced_at) AS last FROM sync_events WHERE status = ?",
                ["synced"],
            )
            row = await cursor.fetchone()
            if row and row["last"]:
                try:
                    last_sync = datetime.fromisoformat(row["last"])
                except ValueError:
                    pass
    except Exception:
        pass  # sync_events table may not exist yet

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
