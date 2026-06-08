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
from typing import List, Optional

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
                """
                SELECT id, url, name, status, last_sync, shared_memories,
                       trust_score, metadata, created_at, updated_at
                FROM federation_peers
                ORDER BY trust_score DESC, created_at DESC
                """
            )
            rows = await cursor.fetchall()

        peers = []
        for row in rows:
            last_sync: Optional[datetime] = None
            if row["last_sync"]:
                last_sync = datetime.fromisoformat(row["last_sync"])

            peers.append(
                FederationPeer(
                    id=strawberry.ID(str(row["id"])),
                    url=row["url"],
                    name=row["name"],
                    status=PeerStatus(row["status"]),
                    last_sync=last_sync,
                    shared_memories=row["shared_memories"] or 0,
                    trust_score=float(row["trust_score"] or 0.0),
                    metadata=row["metadata"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return peers
    except Exception:
        return []


async def resolve_federation_status(info: Info) -> "FederationStatus":  # noqa: F821
    """Resolve federation status by aggregating peer state from the database."""
    import aiosqlite

    from ..types import FederationStatus, PeerStatus

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
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row

            cursor = await conn.execute("SELECT COUNT(*) AS count FROM federation_peers")
            row = await cursor.fetchone()
            total_peers: int = row["count"] if row else 0

            cursor = await conn.execute(
                "SELECT COUNT(*) AS count FROM federation_peers WHERE status = ?",
                [PeerStatus.ONLINE.value],
            )
            row = await cursor.fetchone()
            online_peers: int = row["count"] if row else 0

            cursor = await conn.execute(
                "SELECT MAX(last_sync) AS last_sync FROM federation_peers WHERE last_sync IS NOT NULL"
            )
            row = await cursor.fetchone()
            last_sync: Optional[datetime] = None
            if row and row["last_sync"]:
                last_sync = datetime.fromisoformat(row["last_sync"])

            cursor = await conn.execute(
                "SELECT COALESCE(SUM(shared_memories), 0) AS total FROM federation_peers"
            )
            row = await cursor.fetchone()
            synced_memories: int = row["total"] if row else 0

            cursor = await conn.execute(
                "SELECT COUNT(*) AS count FROM federation_peers WHERE status = ?",
                [PeerStatus.SYNCING.value],
            )
            row = await cursor.fetchone()
            pending_sync: int = row["count"] if row else 0

        return FederationStatus(
            enabled=total_peers > 0,
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
