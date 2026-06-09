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

Peers are persisted as JSON state files by FederationNode at
{db_dir}/federation/{node_id}.json. Sync counts come from the
sync_events table in the main SQLite DB when available.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import aiosqlite
import strawberry
from strawberry.types import Info


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse an ISO datetime string, attaching UTC if no tzinfo."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _peer_status(last_seen: Optional[datetime], now: datetime):
    """Derive PeerStatus from last-seen timestamp."""
    from ..types import PeerStatus

    if last_seen is None:
        return PeerStatus.UNREACHABLE
    age = now - last_seen
    if age < timedelta(minutes=5):
        return PeerStatus.ONLINE
    if age < timedelta(hours=1):
        return PeerStatus.OFFLINE
    return PeerStatus.UNREACHABLE


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from FederationNode JSON state files."""
    from ..types import FederationPeer

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    federation_dir = Path(db_path).parent / "federation"
    if not federation_dir.exists():
        return []

    now = datetime.now(timezone.utc)
    seen: dict = {}

    for state_file in federation_dir.glob("*.json"):
        try:
            data = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for peer_id, peer_data in data.get("peers", {}).items():
            if peer_id in seen:
                continue

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen = _parse_iso(peer_data.get("last_seen"))
            status = _peer_status(last_seen, now)
            ts = last_seen or now

            seen[peer_id] = FederationPeer(
                id=strawberry.ID(peer_id),
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=ts,
                updated_at=ts,
            )

    return list(seen.values())


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating JSON state files and sync_events."""
    from ..types import FederationStatus

    db_path = info.context.get("db_path")

    enabled = False
    total_peers = 0
    online_peers = 0
    last_sync: Optional[datetime] = None
    synced_memories = 0
    pending_sync = 0

    if db_path:
        federation_dir = Path(db_path).parent / "federation"
        if federation_dir.exists():
            enabled = True
            now = datetime.now(timezone.utc)
            seen_peers: set = set()

            for state_file in federation_dir.glob("*.json"):
                try:
                    data = json.loads(state_file.read_text())
                except (json.JSONDecodeError, OSError):
                    continue

                node_sync = _parse_iso(data.get("last_sync"))
                if node_sync and (last_sync is None or node_sync > last_sync):
                    last_sync = node_sync

                for peer_id, peer_data in data.get("peers", {}).items():
                    if peer_id in seen_peers:
                        continue
                    seen_peers.add(peer_id)
                    total_peers += 1

                    last_seen = _parse_iso(peer_data.get("last_seen"))
                    if last_seen and (now - last_seen) < timedelta(minutes=5):
                        online_peers += 1

        # Query sync_events counts if the table exists in this SQLite DB.
        try:
            async with aiosqlite.connect(db_path) as conn:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_events'"
                )
                if await cursor.fetchone():
                    cursor = await conn.execute(
                        "SELECT COUNT(*) FROM sync_events WHERE status='synced'"
                    )
                    row = await cursor.fetchone()
                    synced_memories = row[0] if row else 0

                    cursor = await conn.execute(
                        "SELECT COUNT(*) FROM sync_events WHERE status='pending'"
                    )
                    row = await cursor.fetchone()
                    pending_sync = row[0] if row else 0
        except Exception:
            pass

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=last_sync,
        synced_memories=synced_memories,
        pending_sync=pending_sync,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
