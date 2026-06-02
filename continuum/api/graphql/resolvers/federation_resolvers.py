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
    """Resolve federation peers from the local SQLite database."""
    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    peers: List[FederationPeer] = []
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
            for row in rows:
                metadata = None
                if row["metadata"]:
                    try:
                        metadata = json.loads(row["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        metadata = None

                last_sync: Optional[datetime] = None
                if row["last_sync"]:
                    try:
                        last_sync = datetime.fromisoformat(row["last_sync"])
                    except (ValueError, TypeError):
                        last_sync = None

                try:
                    status = PeerStatus(row["status"])
                except ValueError:
                    status = PeerStatus.OFFLINE

                peers.append(
                    FederationPeer(
                        id=str(row["id"]),
                        url=row["url"],
                        name=row["name"],
                        status=status,
                        last_sync=last_sync,
                        shared_memories=row["shared_memories"] or 0,
                        trust_score=row["trust_score"] or 0.0,
                        metadata=metadata,
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
    except Exception:
        # Table may not exist yet or db unavailable — return empty list
        return []

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating peer data."""
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

    import aiosqlite

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT
                    COUNT(*) AS total_peers,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS online_peers,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pending_sync,
                    MAX(last_sync) AS last_sync,
                    SUM(shared_memories) AS synced_memories
                FROM federation_peers
                """,
                (PeerStatus.ONLINE.value, PeerStatus.SYNCING.value),
            )
            row = await cursor.fetchone()

            last_sync: Optional[datetime] = None
            if row["last_sync"]:
                try:
                    last_sync = datetime.fromisoformat(row["last_sync"])
                except (ValueError, TypeError):
                    last_sync = None

            return FederationStatus(
                enabled=True,
                total_peers=row["total_peers"] or 0,
                online_peers=row["online_peers"] or 0,
                last_sync=last_sync,
                synced_memories=row["synced_memories"] or 0,
                pending_sync=row["pending_sync"] or 0,
            )
    except Exception:
        # Table may not exist yet — report federation as disabled
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
