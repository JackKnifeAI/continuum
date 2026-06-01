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
from pathlib import Path
from typing import List, Optional

from strawberry.types import Info

FEDERATION_DB = Path.home() / ".continuum" / "federation_peers.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS federation_peers (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,
    url TEXT NOT NULL,
    name TEXT,
    status TEXT DEFAULT 'offline',
    last_sync TEXT,
    shared_memories INTEGER DEFAULT 0,
    trust_score REAL DEFAULT 0.5,
    metadata TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def _get_connection() -> sqlite3.Connection:
    FEDERATION_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FEDERATION_DB))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    from ..types import FederationPeer, PeerStatus

    tenant_id: str = getattr(info.context, "tenant_id", None) or "default"

    try:
        with _get_connection() as conn:
            _ensure_table(conn)
            rows = conn.execute(
                "SELECT * FROM federation_peers WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchall()

        peers: List[FederationPeer] = []
        for row in rows:
            try:
                status = PeerStatus(row["status"].upper())
            except (ValueError, AttributeError):
                status = PeerStatus.OFFLINE

            meta = None
            if row["metadata"]:
                try:
                    meta = json.loads(row["metadata"])
                except (json.JSONDecodeError, TypeError):
                    meta = None

            peers.append(
                FederationPeer(
                    id=row["id"],
                    url=row["url"],
                    name=row["name"],
                    status=status,
                    last_sync=_parse_dt(row["last_sync"]),
                    shared_memories=row["shared_memories"] or 0,
                    trust_score=row["trust_score"] if row["trust_score"] is not None else 0.5,
                    metadata=meta,
                    created_at=_parse_dt(row["created_at"]) or datetime.utcnow(),
                    updated_at=_parse_dt(row["updated_at"]) or datetime.utcnow(),
                )
            )
        return peers
    except Exception:
        return []


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
    from ..types import FederationStatus

    tenant_id: str = getattr(info.context, "tenant_id", None) or "default"

    try:
        with _get_connection() as conn:
            _ensure_table(conn)

            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_peers,
                    SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) AS online_peers,
                    MAX(last_sync) AS last_sync,
                    SUM(shared_memories) AS synced_memories,
                    SUM(
                        CASE
                            WHEN status IN ('syncing', 'offline') AND last_sync IS NOT NULL
                            THEN 1 ELSE 0
                        END
                    ) AS pending_sync
                FROM federation_peers
                WHERE tenant_id = ?
                """,
                (tenant_id,),
            ).fetchone()

        total_peers: int = row["total_peers"] or 0
        online_peers: int = row["online_peers"] or 0
        last_sync: Optional[datetime] = _parse_dt(row["last_sync"])
        synced_memories: int = row["synced_memories"] or 0
        pending_sync: int = row["pending_sync"] or 0

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
