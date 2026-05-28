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
import sqlite3
from datetime import datetime
from typing import List, Optional

from strawberry.types import Info


def _get_db_path(info: Info) -> Optional[str]:
    """Extract db_path from GraphQL context."""
    ctx = info.context
    if hasattr(ctx, "db_path"):
        return ctx.db_path
    return None


def _get_tenant_id(info: Info) -> Optional[str]:
    """Extract tenant_id from GraphQL context."""
    ctx = info.context
    if hasattr(ctx, "tenant_id"):
        return ctx.tenant_id
    return None


def _ensure_federation_peers_table(conn: sqlite3.Connection) -> None:
    """Create federation_peers table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS federation_peers (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            url TEXT NOT NULL,
            name TEXT,
            status TEXT NOT NULL DEFAULT 'offline',
            last_sync TEXT,
            shared_memories INTEGER NOT NULL DEFAULT 0,
            trust_score REAL NOT NULL DEFAULT 0.5,
            metadata TEXT,
            synced_memories INTEGER NOT NULL DEFAULT 0,
            pending_sync INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


def _row_to_peer(row: sqlite3.Row):
    """Convert a sqlite3.Row to a FederationPeer GraphQL type."""
    from ..types import FederationPeer, PeerStatus

    last_sync = None
    if row["last_sync"]:
        try:
            last_sync = datetime.fromisoformat(row["last_sync"])
        except (ValueError, TypeError):
            pass

    metadata = None
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass

    try:
        status = PeerStatus(row["status"])
    except ValueError:
        status = PeerStatus.OFFLINE

    return FederationPeer(
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


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the database."""
    db_path = _get_db_path(info)
    if not db_path:
        return []

    tenant_id = _get_tenant_id(info)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_federation_peers_table(conn)
        if tenant_id:
            rows = conn.execute(
                "SELECT * FROM federation_peers WHERE tenant_id = ? ORDER BY created_at ASC",
                (tenant_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM federation_peers ORDER BY created_at ASC"
            ).fetchall()
        return [_row_to_peer(row) for row in rows]
    finally:
        conn.close()


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating peer data from the database."""
    from ..types import FederationStatus

    db_path = _get_db_path(info)
    if not db_path:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    tenant_id = _get_tenant_id(info)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_federation_peers_table(conn)

        if tenant_id:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_peers,
                    SUM(CASE WHEN status IN ('online', 'syncing') THEN 1 ELSE 0 END) AS online_peers,
                    MAX(last_sync) AS last_sync,
                    SUM(synced_memories) AS synced_memories,
                    SUM(pending_sync) AS pending_sync
                FROM federation_peers
                WHERE tenant_id = ?
                """,
                (tenant_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_peers,
                    SUM(CASE WHEN status IN ('online', 'syncing') THEN 1 ELSE 0 END) AS online_peers,
                    MAX(last_sync) AS last_sync,
                    SUM(synced_memories) AS synced_memories,
                    SUM(pending_sync) AS pending_sync
                FROM federation_peers
                """
            ).fetchone()

        total_peers = row["total_peers"] or 0
        online_peers = row["online_peers"] or 0
        synced_memories = row["synced_memories"] or 0
        pending_sync = row["pending_sync"] or 0

        last_sync = None
        if row["last_sync"]:
            try:
                last_sync = datetime.fromisoformat(row["last_sync"])
            except (ValueError, TypeError):
                pass

        return FederationStatus(
            enabled=total_peers > 0,
            total_peers=total_peers,
            online_peers=online_peers,
            last_sync=last_sync,
            synced_memories=synced_memories,
            pending_sync=pending_sync,
        )
    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
