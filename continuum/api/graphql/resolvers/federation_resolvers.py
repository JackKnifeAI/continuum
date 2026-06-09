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

import strawberry
from strawberry.types import Info

from ..types import FederationPeer, FederationStatus, PeerStatus


def _get_federation_dir(info: Info) -> Optional[Path]:
    """Derive federation storage directory from the context db_path."""
    db_path = info.context.get("db_path")
    if not db_path:
        return None
    federation_dir = Path(db_path).parent / "federation"
    return federation_dir if federation_dir.exists() else None


def _load_node_states(federation_dir: Path) -> List[dict]:
    """Read all node state JSON files from the federation directory."""
    states = []
    for state_file in federation_dir.glob("*.json"):
        try:
            states.append(json.loads(state_file.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return states


def _peer_status_from_last_seen(last_seen_iso: Optional[str]) -> PeerStatus:
    """Map last_seen timestamp to a PeerStatus enum value."""
    if not last_seen_iso:
        return PeerStatus.OFFLINE
    try:
        last_seen = datetime.fromisoformat(last_seen_iso)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - last_seen
        if age < timedelta(minutes=5):
            return PeerStatus.ONLINE
        if age < timedelta(hours=1):
            return PeerStatus.OFFLINE
        return PeerStatus.UNREACHABLE
    except (ValueError, TypeError):
        return PeerStatus.OFFLINE


async def resolve_federation_peers(info: Info) -> List[FederationPeer]:
    """Resolve federation peers by reading node state files from disk."""
    federation_dir = _get_federation_dir(info)
    if not federation_dir:
        return []

    seen_ids: set = set()
    peers: List[FederationPeer] = []

    for state in _load_node_states(federation_dir):
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen_ids:
                continue
            seen_ids.add(peer_id)

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen_iso: Optional[str] = peer_data.get("last_seen")

            last_sync_dt: Optional[datetime] = None
            if last_seen_iso:
                try:
                    last_sync_dt = datetime.fromisoformat(last_seen_iso)
                    if last_sync_dt.tzinfo is None:
                        last_sync_dt = last_sync_dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            ts = last_sync_dt or datetime.now(timezone.utc)
            peers.append(
                FederationPeer(
                    id=strawberry.ID(peer_id),
                    url=f"http://{host}:{port}",
                    name=None,
                    status=_peer_status_from_last_seen(last_seen_iso),
                    last_sync=last_sync_dt,
                    shared_memories=0,
                    trust_score=1.0,
                    metadata=None,
                    created_at=ts,
                    updated_at=ts,
                )
            )

    return peers


async def resolve_federation_status(info: Info) -> FederationStatus:
    """Resolve federation status by aggregating all node state files."""
    federation_dir = _get_federation_dir(info)

    _disabled = FederationStatus(
        enabled=False,
        total_peers=0,
        online_peers=0,
        last_sync=None,
        synced_memories=0,
        pending_sync=0,
    )

    if not federation_dir:
        return _disabled

    states = _load_node_states(federation_dir)
    if not states:
        return _disabled

    seen_peer_ids: set = set()
    online_count = 0
    latest_sync: Optional[datetime] = None
    total_contributions = 0.0

    for state in states:
        last_sync_iso: Optional[str] = state.get("last_sync")
        if last_sync_iso:
            try:
                dt = datetime.fromisoformat(last_sync_iso)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if latest_sync is None or dt > latest_sync:
                    latest_sync = dt
            except (ValueError, TypeError):
                pass

        total_contributions += state.get("contribution_score", 0.0)

        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen_peer_ids:
                continue
            seen_peer_ids.add(peer_id)
            if _peer_status_from_last_seen(peer_data.get("last_seen")) == PeerStatus.ONLINE:
                online_count += 1

    return FederationStatus(
        enabled=True,
        total_peers=len(seen_peer_ids),
        online_peers=online_count,
        last_sync=latest_sync,
        synced_memories=int(total_contributions),
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
