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

Derives peer and status information from the sync_events table, which records
cross-instance synchronization activity (source_instance → target_instance).
"""

from datetime import datetime, timezone
from typing import List, Optional

import aiosqlite
import strawberry
from strawberry.types import Info


def _parse_ts(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp string into a UTC-aware datetime."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers derived from sync_events history."""
    from ..types import FederationPeer, PeerStatus

    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return []

    now = datetime.now(timezone.utc)
    peers: List[FederationPeer] = []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT
                target_instance                                                     AS instance_id,
                MIN(created_at)                                                     AS first_seen,
                MAX(COALESCE(synced_at, created_at))                                AS last_activity,
                MAX(synced_at)                                                      AS last_sync,
                COUNT(CASE WHEN entity_type = 'memory' AND status = 'synced'
                           THEN 1 END)                                              AS shared_memories,
                COUNT(CASE WHEN status = 'failed'  THEN 1 END)                     AS failed_syncs,
                COUNT(CASE WHEN status = 'pending' THEN 1 END)                     AS pending_syncs,
                COUNT(*)                                                            AS total_syncs
            FROM sync_events
            WHERE target_instance IS NOT NULL
            GROUP BY target_instance
            ORDER BY last_activity DESC
            """
        )
        rows = await cursor.fetchall()

    for row in rows:
        r = dict(row)
        instance_id: str = r["instance_id"]
        last_activity_dt = _parse_ts(r["last_activity"])
        last_sync_dt = _parse_ts(r["last_sync"])
        created_at_dt = _parse_ts(r["first_seen"]) or now
        pending_syncs: int = r["pending_syncs"] or 0
        failed_syncs: int = r["failed_syncs"] or 0
        total_syncs: int = r["total_syncs"] or 0
        shared_memories: int = r["shared_memories"] or 0

        # Determine peer status from recent activity.
        if pending_syncs > 0:
            status = PeerStatus.SYNCING
        elif last_activity_dt:
            age_s = (now - last_activity_dt).total_seconds()
            if age_s < 300:
                status = PeerStatus.ONLINE
            elif age_s < 3600:
                status = PeerStatus.OFFLINE
            else:
                status = PeerStatus.UNREACHABLE
        else:
            status = PeerStatus.OFFLINE

        # Trust score: fraction of successful syncs, floored at 0.1.
        trust_score = (
            round(max(0.1, (total_syncs - failed_syncs) / total_syncs), 4)
            if total_syncs > 0
            else 0.5
        )

        # Derive a human-readable name from the instance URL/identifier.
        name = (
            instance_id.split("://")[-1].split("/")[0]
            if "://" in instance_id
            else instance_id
        )

        peers.append(
            FederationPeer(
                id=strawberry.ID(instance_id),
                url=instance_id,
                name=name,
                status=status,
                last_sync=last_sync_dt,
                shared_memories=shared_memories,
                trust_score=trust_score,
                metadata={
                    "total_syncs": total_syncs,
                    "failed_syncs": failed_syncs,
                    "pending_syncs": pending_syncs,
                },
                created_at=created_at_dt,
                updated_at=last_activity_dt or created_at_dt,
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from sync_events aggregate statistics."""
    from ..types import FederationStatus

    db_path = getattr(info.context, "db_path", None)
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
                COUNT(DISTINCT target_instance)                                     AS total_peers,
                MAX(synced_at)                                                      AS last_sync,
                COUNT(CASE WHEN entity_type = 'memory' AND status = 'synced'
                           THEN 1 END)                                              AS synced_memories,
                COUNT(CASE WHEN status = 'pending' THEN 1 END)                     AS pending_sync
            FROM sync_events
            WHERE target_instance IS NOT NULL
            """
        )
        row = await cursor.fetchone()

        # Peers are considered "online" if they have a pending sync or were
        # active within the last 5 minutes.
        online_cursor = await conn.execute(
            """
            SELECT COUNT(DISTINCT target_instance) AS online_peers
            FROM sync_events
            WHERE target_instance IS NOT NULL
              AND (status = 'pending'
                   OR datetime(COALESCE(synced_at, created_at)) >
                      datetime('now', '-5 minutes'))
            """
        )
        online_row = await online_cursor.fetchone()

    if not row:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    r = dict(row)
    total_peers: int = r.get("total_peers") or 0

    return FederationStatus(
        enabled=total_peers > 0,
        total_peers=total_peers,
        online_peers=dict(online_row).get("online_peers") or 0 if online_row else 0,
        last_sync=_parse_ts(r.get("last_sync")),
        synced_memories=r.get("synced_memories") or 0,
        pending_sync=r.get("pending_sync") or 0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
