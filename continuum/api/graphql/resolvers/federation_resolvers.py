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

from strawberry.types import Info


def _peer_status_from_last_seen(last_seen_str):
    """Determine PeerStatus based on how long ago the peer was last seen."""
    from ..types import PeerStatus

    if not last_seen_str:
        return PeerStatus.OFFLINE

    try:
        last_seen = datetime.fromisoformat(last_seen_str)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        age_seconds = (now - last_seen).total_seconds()
        if age_seconds < 300:
            return PeerStatus.ONLINE
        elif age_seconds < 3600:
            return PeerStatus.OFFLINE
        else:
            return PeerStatus.UNREACHABLE
    except (ValueError, TypeError):
        return PeerStatus.OFFLINE


def _load_federation_state_files(db_path: str):
    """Load all federation JSON state files for the given db_path.

    Returns a list of parsed state dicts.
    """
    fed_dir = Path(db_path).parent / "federation"
    if not fed_dir.is_dir():
        return []

    states = []
    for json_file in fed_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            states.append(state)
        except (OSError, json.JSONDecodeError):
            continue
    return states


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from FederationNode state files."""
    from ..types import FederationPeer

    db_path = (
        info.context.get("db_path")
        if hasattr(info.context, "get")
        else getattr(info.context, "db_path", None)
    )

    if not db_path:
        return []

    states = _load_federation_state_files(db_path)

    peers = []
    seen_peer_ids = set()

    for state in states:
        raw_peers = state.get("peers", {})
        for peer_id_str, peer_data in raw_peers.items():
            if peer_id_str in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id_str)

            host = peer_data.get("host", "")
            port = peer_data.get("port", 80)
            url = f"http://{host}:{port}"
            name = peer_data.get("name") or None
            last_seen_str = peer_data.get("last_seen")
            status = _peer_status_from_last_seen(last_seen_str)

            last_sync_dt = None
            if last_seen_str:
                try:
                    last_sync_dt = datetime.fromisoformat(last_seen_str)
                    if last_sync_dt.tzinfo is None:
                        last_sync_dt = last_sync_dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    last_sync_dt = None

            now = datetime.now(tz=timezone.utc)
            peer = FederationPeer(
                id=peer_id_str,
                url=url,
                name=name,
                status=status,
                last_sync=last_sync_dt,
                shared_memories=0,
                trust_score=0.0,
                metadata=None,
                created_at=now,
                updated_at=now,
            )
            peers.append(peer)

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status aggregated from FederationNode state files."""
    from ..types import FederationStatus

    db_path = (
        info.context.get("db_path")
        if hasattr(info.context, "get")
        else getattr(info.context, "db_path", None)
    )

    if not db_path:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    states = _load_federation_state_files(db_path)

    if not states:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    enabled = any(state.get("registered", False) for state in states)

    seen_peer_ids = set()
    online_count = 0
    latest_sync: datetime | None = None

    for state in states:
        raw_peers = state.get("peers", {})
        for peer_id_str, peer_data in raw_peers.items():
            if peer_id_str in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id_str)

            last_seen_str = peer_data.get("last_seen")
            status = _peer_status_from_last_seen(last_seen_str)
            from ..types import PeerStatus
            if status == PeerStatus.ONLINE:
                online_count += 1

        last_sync_str = state.get("last_sync")
        if last_sync_str:
            try:
                sync_dt = datetime.fromisoformat(last_sync_str)
                if sync_dt.tzinfo is None:
                    sync_dt = sync_dt.replace(tzinfo=timezone.utc)
                if latest_sync is None or sync_dt > latest_sync:
                    latest_sync = sync_dt
            except (ValueError, TypeError):
                pass

    total_peers = len(seen_peer_ids)

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
