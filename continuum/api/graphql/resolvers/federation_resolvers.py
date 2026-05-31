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
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import strawberry
from strawberry.types import Info


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO datetime string into a timezone-aware datetime, or return None."""
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _peer_status_from_last_seen(last_seen: datetime | None):
    """Determine PeerStatus based on how recently a peer was seen."""
    from ..types import PeerStatus

    if last_seen is None:
        return PeerStatus.OFFLINE
    now = datetime.now(tz=timezone.utc)
    delta = (now - last_seen).total_seconds()
    if delta < 60:
        return PeerStatus.ONLINE
    if delta < 300:
        return PeerStatus.SYNCING
    return PeerStatus.OFFLINE


def _load_federation_nodes(db_path: str | None) -> list[dict]:
    """Load all federation node JSON files from the federation directory."""
    if not db_path:
        return []
    federation_dir = Path(db_path).parent / "federation"
    if not federation_dir.is_dir():
        return []
    nodes = []
    for json_file in federation_dir.glob("*.json"):
        try:
            with json_file.open() as fh:
                data = json.load(fh)
            nodes.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return nodes


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers by reading federation node JSON files."""
    from ..types import FederationPeer

    db_path: str | None = getattr(info.context, "db_path", None)
    nodes = _load_federation_nodes(db_path)

    peers = []
    for node in nodes:
        node_id = node.get("node_id", "")
        peer_map: dict = node.get("peers", {})
        last_sync_dt = _parse_dt(node.get("last_sync"))

        for peer_id, peer_info in peer_map.items():
            host = peer_info.get("host", "")
            port = peer_info.get("port", 0)
            last_seen_dt = _parse_dt(peer_info.get("last_seen"))
            status = _peer_status_from_last_seen(last_seen_dt)
            url = f"http://{host}:{port}" if host else ""
            now = datetime.now(tz=timezone.utc)
            peers.append(
                FederationPeer(
                    id=strawberry.ID(peer_id),
                    url=url,
                    name=None,
                    status=status,
                    last_sync=last_sync_dt,
                    shared_memories=0,
                    trust_score=node.get("contribution_score", 0.0),
                    metadata={"node_id": node_id, "access_level": node.get("access_level")},
                    created_at=now,
                    updated_at=last_seen_dt or now,
                )
            )

    return peers


async def resolve_federation_status(info: Info):
    """Resolve federation status from node files and the sync_events DB table."""
    from ..types import FederationStatus, PeerStatus

    db_path: str | None = getattr(info.context, "db_path", None)
    nodes = _load_federation_nodes(db_path)

    # Build peer list to count statuses and find latest sync
    total_peers = 0
    online_peers = 0
    latest_sync: datetime | None = None

    for node in nodes:
        peer_map: dict = node.get("peers", {})
        for peer_info in peer_map.values():
            total_peers += 1
            last_seen_dt = _parse_dt(peer_info.get("last_seen"))
            status = _peer_status_from_last_seen(last_seen_dt)
            if status == PeerStatus.ONLINE:
                online_peers += 1

        node_last_sync = _parse_dt(node.get("last_sync"))
        if node_last_sync is not None:
            if latest_sync is None or node_last_sync > latest_sync:
                latest_sync = node_last_sync

    enabled = total_peers > 0

    # Query sync_events table if it exists
    synced_memories = 0
    pending_sync = 0
    if db_path:
        try:
            import aiosqlite

            async with aiosqlite.connect(db_path) as db:
                # Check if table exists
                async with db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_events'"
                ) as cur:
                    row = await cur.fetchone()

                if row:
                    async with db.execute(
                        "SELECT COUNT(*) FROM sync_events WHERE status = 'synced'"
                    ) as cur:
                        result = await cur.fetchone()
                        synced_memories = result[0] if result else 0

                    async with db.execute(
                        "SELECT COUNT(*) FROM sync_events WHERE status = 'pending'"
                    ) as cur:
                        result = await cur.fetchone()
                        pending_sync = result[0] if result else 0
        except Exception:
            pass

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=latest_sync,
        synced_memories=synced_memories,
        pending_sync=pending_sync,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
