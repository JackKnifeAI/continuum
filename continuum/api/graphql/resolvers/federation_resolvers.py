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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from strawberry.types import Info


def _parse_last_seen(last_seen_str: str) -> datetime:
    """Parse a last_seen ISO string into a timezone-aware datetime."""
    dt = datetime.fromisoformat(last_seen_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _collect_peers(federation_path: Path) -> dict:
    """
    Scan all *.json files in federation_path and return a dict of
    peer_id -> peer_data (latest entry wins on duplicate peer_id).
    """
    peers: dict = {}
    if not federation_path.exists():
        return peers

    for node_file in federation_path.glob("*.json"):
        try:
            with node_file.open() as fh:
                node_data = json.load(fh)
        except Exception:
            continue

        for peer_id, peer_info in node_data.get("peers", {}).items():
            peers[peer_id] = peer_info

    return peers


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    from ..types import FederationPeer, PeerStatus

    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return []

    federation_path = Path(db_path).parent / "federation"
    peers = _collect_peers(federation_path)

    now = datetime.now(timezone.utc)
    online_threshold = timedelta(minutes=5)

    result = []
    for peer_id, peer_info in peers.items():
        host = peer_info.get("host", "")
        port = peer_info.get("port", 0)
        last_seen_raw = peer_info.get("last_seen")

        last_sync_dt: datetime | None = None
        if last_seen_raw:
            try:
                last_sync_dt = _parse_last_seen(last_seen_raw)
            except Exception:
                last_sync_dt = None

        if last_sync_dt is not None and (now - last_sync_dt) <= online_threshold:
            status = PeerStatus.ONLINE
        else:
            status = PeerStatus.OFFLINE

        ts = last_sync_dt or now

        result.append(
            FederationPeer(
                id=str(peer_id),
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=last_sync_dt,
                shared_memories=0,
                trust_score=0.5,
                metadata=None,
                created_at=ts,
                updated_at=ts,
            )
        )

    return result


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
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

    federation_path = Path(db_path).parent / "federation"

    if not federation_path.exists():
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    enabled = False
    last_sync_dt: datetime | None = None
    all_peers: dict = {}
    now = datetime.now(timezone.utc)
    online_threshold = timedelta(minutes=5)

    for node_file in federation_path.glob("*.json"):
        try:
            with node_file.open() as fh:
                node_data = json.load(fh)
        except Exception:
            continue

        if node_data.get("registered"):
            enabled = True

        # Track most recent last_sync across all node files
        node_last_sync_raw = node_data.get("last_sync")
        if node_last_sync_raw:
            try:
                node_last_sync_dt = _parse_last_seen(node_last_sync_raw)
                if last_sync_dt is None or node_last_sync_dt > last_sync_dt:
                    last_sync_dt = node_last_sync_dt
            except Exception:
                pass

        for peer_id, peer_info in node_data.get("peers", {}).items():
            all_peers[peer_id] = peer_info

    online_count = 0
    for peer_info in all_peers.values():
        last_seen_raw = peer_info.get("last_seen")
        if last_seen_raw:
            try:
                last_seen_dt = _parse_last_seen(last_seen_raw)
                if (now - last_seen_dt) <= online_threshold:
                    online_count += 1
            except Exception:
                pass

    return FederationStatus(
        enabled=enabled,
        total_peers=len(all_peers),
        online_peers=online_count,
        last_sync=last_sync_dt,
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
