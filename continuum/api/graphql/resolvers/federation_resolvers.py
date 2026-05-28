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
from typing import List, Optional

from strawberry.types import Info

from ..types import FederationPeer, FederationStatus, PeerStatus


def _get_federation_storage(info: Info) -> Path:
    db_path: Optional[str] = info.context.get("db_path")
    if db_path:
        return Path(db_path).parent / "federation"
    return Path.home() / ".continuum" / "federation"


def _parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def resolve_federation_peers(info: Info) -> List[FederationPeer]:
    storage_dir = _get_federation_storage(info)
    if not storage_dir.exists():
        return []

    now = datetime.now(tz=timezone.utc)
    five_minutes = timedelta(minutes=5)
    seen_peer_ids: set = set()
    peers: List[FederationPeer] = []

    for json_file in storage_dir.glob("*.json"):
        try:
            state = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        raw_peers: dict = state.get("peers", {})
        for peer_id, peer_data in raw_peers.items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)

            host: str = peer_data.get("host", "")
            port: int = peer_data.get("port", 0)
            url = f"http://{host}:{port}" if port else f"http://{host}"

            last_seen_str: Optional[str] = peer_data.get("last_seen")
            if last_seen_str:
                try:
                    last_seen_dt: Optional[datetime] = _parse_datetime(last_seen_str)
                except ValueError:
                    last_seen_dt = None
            else:
                last_seen_dt = None

            if last_seen_dt is not None and (now - last_seen_dt) <= five_minutes:
                status = PeerStatus.ONLINE
            else:
                status = PeerStatus.OFFLINE

            created_at = last_seen_dt if last_seen_dt is not None else now
            updated_at = last_seen_dt if last_seen_dt is not None else now

            peers.append(
                FederationPeer(
                    id=peer_id,
                    url=url,
                    name=None,
                    status=status,
                    last_sync=last_seen_dt,
                    shared_memories=0,
                    trust_score=1.0,
                    metadata=None,
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )

    return peers


async def resolve_federation_status(info: Info) -> FederationStatus:
    storage_dir = _get_federation_storage(info)
    if not storage_dir.exists():
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(tz=timezone.utc)
    five_minutes = timedelta(minutes=5)
    any_node_running: bool = False
    latest_sync: Optional[datetime] = None
    seen_peer_ids: set = set()
    online_count: int = 0

    for json_file in storage_dir.glob("*.json"):
        try:
            state = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        if state.get("running") is True:
            any_node_running = True

        last_sync_str: Optional[str] = state.get("last_sync")
        if last_sync_str:
            try:
                last_sync_dt = _parse_datetime(last_sync_str)
                if latest_sync is None or last_sync_dt > latest_sync:
                    latest_sync = last_sync_dt
            except ValueError:
                pass

        raw_peers: dict = state.get("peers", {})
        for peer_id, peer_data in raw_peers.items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)

            last_seen_str: Optional[str] = peer_data.get("last_seen")
            if last_seen_str:
                try:
                    last_seen_dt = _parse_datetime(last_seen_str)
                    if (now - last_seen_dt) <= five_minutes:
                        online_count += 1
                except ValueError:
                    pass

    total_peers = len(seen_peer_ids)
    enabled = any_node_running or total_peers > 0

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        online_peers=online_count,
        last_sync=latest_sync,
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
