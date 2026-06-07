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
import logging
import os
from datetime import datetime
from typing import List, Optional

import aiosqlite
from strawberry.types import Info

logger = logging.getLogger(__name__)


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers by querying the federation_peers database table."""
    from ..types import FederationPeer, PeerStatus

    db_path = getattr(info.context, "db_path", None)
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
            try:
                status = PeerStatus(row["status"])
            except (ValueError, KeyError):
                status = PeerStatus.OFFLINE

            last_sync: Optional[datetime] = None
            if row["last_sync"]:
                try:
                    last_sync = datetime.fromisoformat(row["last_sync"])
                except (ValueError, TypeError):
                    pass

            metadata = None
            if row["metadata"]:
                try:
                    metadata = json.loads(row["metadata"])
                except (ValueError, TypeError):
                    pass

            peers.append(
                FederationPeer(
                    id=row["id"],
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
        return peers

    except aiosqlite.OperationalError:
        # federation_peers table does not exist yet
        return []
    except Exception:
        logger.exception("Failed to load federation peers")
        return []


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status derived from live peers and configuration."""
    from ..types import FederationStatus, PeerStatus

    peers = await resolve_federation_peers(info)

    online_statuses = {PeerStatus.ONLINE, PeerStatus.SYNCING}
    online_peers = sum(1 for p in peers if p.status in online_statuses)

    last_sync: Optional[datetime] = None
    synced_memories = 0
    for peer in peers:
        if peer.last_sync and (last_sync is None or peer.last_sync > last_sync):
            last_sync = peer.last_sync
        synced_memories += peer.shared_memories

    # Federation is active when peers exist or explicitly configured
    federation_enabled = bool(peers) or os.getenv(
        "CONTINUUM_FEDERATION_ENABLED", ""
    ).lower() in ("1", "true", "yes")

    return FederationStatus(
        enabled=federation_enabled,
        total_peers=len(peers),
        online_peers=online_peers,
        last_sync=last_sync,
        synced_memories=synced_memories,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
