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

from datetime import datetime, timezone
from typing import List, Optional

from strawberry.types import Info

# Synced events older than this many seconds mark a peer as OFFLINE
_ONLINE_THRESHOLD_SECONDS = 300


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers derived from sync_events source/target instances."""
    import hashlib

    import aiosqlite

    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        # Collect per-instance aggregate stats from sync_events.
        # We treat every distinct source_instance as a known peer.
        cursor = await conn.execute(
            """
            SELECT
                source_instance                         AS instance,
                MIN(created_at)                         AS first_seen,
                MAX(COALESCE(synced_at, created_at))    AS last_activity,
                MAX(synced_at)                          AS last_sync,
                COUNT(CASE WHEN status = 'synced' AND entity_type = 'memory' THEN 1 END)  AS shared_memories
            FROM sync_events
            WHERE source_instance IS NOT NULL
            GROUP BY source_instance
            ORDER BY last_activity DESC
            """
        )
        rows = await cursor.fetchall()

    now = datetime.now(timezone.utc)
    peers: List[FederationPeer] = []

    for row in rows:
        instance: str = row["instance"]
        last_sync_dt = _parse_dt(row["last_sync"])
        last_activity_dt = _parse_dt(row["last_activity"])
        first_seen_dt = _parse_dt(row["first_seen"]) or now
        shared: int = row["shared_memories"] or 0

        # Determine online/offline from recency of last activity.
        if last_activity_dt:
            age = (now - last_activity_dt.astimezone(timezone.utc)).total_seconds()
            status = PeerStatus.ONLINE if age < _ONLINE_THRESHOLD_SECONDS else PeerStatus.OFFLINE
        else:
            status = PeerStatus.OFFLINE

        # Stable synthetic ID derived from the instance identifier.
        peer_id = hashlib.sha256(instance.encode()).hexdigest()[:32]

        peers.append(
            FederationPeer(
                id=peer_id,
                url=instance,
                name=instance,
                status=status,
                last_sync=last_sync_dt,
                shared_memories=shared,
                trust_score=1.0,
                metadata=None,
                created_at=first_seen_dt,
                updated_at=last_activity_dt or first_seen_dt,
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status aggregated from sync_events."""
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

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        cursor = await conn.execute(
            """
            SELECT
                COUNT(DISTINCT source_instance)                                         AS total_peers,
                MAX(synced_at)                                                          AS last_sync,
                COUNT(CASE WHEN status = 'synced' AND entity_type = 'memory' THEN 1 END) AS synced_memories,
                COUNT(CASE WHEN status = 'pending' THEN 1 END)                          AS pending_sync
            FROM sync_events
            WHERE source_instance IS NOT NULL
            """
        )
        row = await cursor.fetchone()

    if not row or not row["total_peers"]:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    # Reuse peer resolver to count online peers without duplicating the logic.
    peers = await resolve_federation_peers(info)
    online_peers = sum(1 for p in peers if p.status == PeerStatus.ONLINE)

    return FederationStatus(
        enabled=True,
        total_peers=row["total_peers"],
        online_peers=online_peers,
        last_sync=_parse_dt(row["last_sync"]),
        synced_memories=row["synced_memories"] or 0,
        pending_sync=row["pending_sync"] or 0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
