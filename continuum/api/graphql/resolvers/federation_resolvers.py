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


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO datetime string from the database, returning None if absent."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the database for the current tenant."""
    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    tenant_id = info.context.get("tenant_id")

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        if tenant_id:
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
        else:
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
        try:
            status = PeerStatus(row["status"])
        except ValueError:
            status = PeerStatus.OFFLINE

        raw_metadata = row["metadata"]
        metadata = json.loads(raw_metadata) if raw_metadata else None

        peers.append(
            FederationPeer(
                id=row["id"],
                url=row["url"],
                name=row["name"],
                status=status,
                last_sync=_parse_dt(row["last_sync"]),
                shared_memories=row["shared_memories"] or 0,
                trust_score=row["trust_score"] or 0.0,
                metadata=metadata,
                created_at=_parse_dt(row["created_at"]) or datetime.min,
                updated_at=_parse_dt(row["updated_at"]) or datetime.min,
            )
        )

    return peers


async def resolve_federation_status(info: Info):
    """Resolve aggregate federation status for the current tenant."""
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

    tenant_id = info.context.get("tenant_id")
    params: list = [tenant_id] if tenant_id else []
    tenant_filter = "WHERE tenant_id = ?" if tenant_id else ""

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        # Aggregate peer counts and sync totals in a single pass
        cursor = await conn.execute(
            f"""
            SELECT
                COUNT(*) AS total_peers,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS online_peers,
                MAX(last_sync) AS last_sync,
                SUM(shared_memories) AS synced_memories
            FROM federation_peers
            {tenant_filter}
            """,
            [PeerStatus.ONLINE.value, *params],
        )
        row = await cursor.fetchone()

        # Pending sync: memories not yet propagated to any peer
        pending_cursor = await conn.execute(
            f"""
            SELECT COUNT(*) AS pending_sync
            FROM memories
            {"WHERE tenant_id = ?" if tenant_id else ""}
            AND id NOT IN (
                SELECT DISTINCT memory_id
                FROM federation_sync_log
                WHERE status = 'synced'
            )
            """,
            params,
        )
        pending_row = await pending_cursor.fetchone()

    total_peers = row["total_peers"] or 0
    online_peers = row["online_peers"] or 0
    synced_memories = row["synced_memories"] or 0
    pending_sync = pending_row["pending_sync"] or 0 if pending_row else 0

    return FederationStatus(
        enabled=total_peers > 0,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=_parse_dt(row["last_sync"]),
        synced_memories=synced_memories,
        pending_sync=pending_sync,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
