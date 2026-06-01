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
from typing import List

from strawberry.types import Info

FEDERATION_DB_PATH = Path.home() / ".continuum" / "federation" / "peers.db"


def _get_db() -> sqlite3.Connection:
    FEDERATION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FEDERATION_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS federation_peers (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
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
    )
    conn.commit()
    return conn


def _row_to_peer(row: sqlite3.Row):
    from ..types import FederationPeer, PeerStatus

    return FederationPeer(
        id=row["id"],
        url=row["url"],
        name=row["name"],
        status=PeerStatus(row["status"]),
        last_sync=datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None,
        shared_memories=row["shared_memories"],
        trust_score=row["trust_score"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM federation_peers ORDER BY created_at DESC"
        ).fetchall()
        return [_row_to_peer(row) for row in rows]
    finally:
        conn.close()


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
    from ..types import FederationStatus

    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT status, last_sync, shared_memories FROM federation_peers"
        ).fetchall()
        total_peers = len(rows)
        online_peers = sum(1 for r in rows if r["status"] in ("online", "syncing"))
        synced_memories = sum(r["shared_memories"] for r in rows)
        sync_times = [
            datetime.fromisoformat(r["last_sync"]) for r in rows if r["last_sync"]
        ]
        last_sync = max(sync_times) if sync_times else None
        return FederationStatus(
            enabled=total_peers > 0,
            total_peers=total_peers,
            online_peers=online_peers,
            last_sync=last_sync,
            synced_memories=synced_memories,
            pending_sync=0,
        )
    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
