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


def _federation_storage_path(info: Info) -> Optional[Path]:
    """Derive federation storage path from the GraphQL context's db_path."""
    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return None
    return Path(db_path).parent / "federation"


def _load_node_state(storage_path: Path, node_id: str) -> Optional[dict]:
    """Read persisted FederationNode JSON state from disk."""
    state_file = storage_path / f"{node_id}.json"
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _peer_status_from_last_seen(last_seen_iso: Optional[str]) -> PeerStatus:
    """Classify a peer as ONLINE if seen within 5 minutes, else OFFLINE."""
    if not last_seen_iso:
        return PeerStatus.OFFLINE
    try:
        last_seen = datetime.fromisoformat(last_seen_iso)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        return (
            PeerStatus.ONLINE
            if datetime.now(timezone.utc) - last_seen < timedelta(minutes=5)
            else PeerStatus.OFFLINE
        )
    except (ValueError, TypeError):
        return PeerStatus.OFFLINE


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 string to datetime, returning None on failure."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


async def resolve_federation_peers(info: Info) -> List[FederationPeer]:
    """Resolve federation peers from the persisted FederationNode state on disk."""
    storage_path = _federation_storage_path(info)
    if not storage_path or not storage_path.exists():
        return []

    try:
        from continuum.cli.config import CLIConfig
        cli_config = CLIConfig.load()
        node_id = cli_config.node_id
    except Exception:
        node_id = None

    if not node_id:
        return []

    state = _load_node_state(storage_path, node_id)
    if not state:
        return []

    now = datetime.now(timezone.utc)
    peers: dict = state.get("peers", {})
    result: List[FederationPeer] = []

    for peer_id, peer_data in peers.items():
        host = peer_data.get("host", "unknown")
        port = peer_data.get("port", 0)
        last_seen_iso = peer_data.get("last_seen")
        last_seen_dt = _parse_iso(last_seen_iso)
        status = _peer_status_from_last_seen(last_seen_iso)

        result.append(
            FederationPeer(
                id=strawberry.ID(peer_id),
                url=f"http://{host}:{port}",
                name=peer_id[:8],
                status=status,
                last_sync=last_seen_dt,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=last_seen_dt or now,
                updated_at=last_seen_dt or now,
            )
        )

    return result


async def resolve_federation_status(info: Info) -> FederationStatus:
    """Resolve federation status from persisted node state and CLI config."""
    try:
        from continuum.cli.config import CLIConfig
        cli_config = CLIConfig.load()
        federation_enabled = cli_config.federation_enabled
        node_id = cli_config.node_id
    except Exception:
        federation_enabled = False
        node_id = None

    if not federation_enabled or not node_id:
        return FederationStatus(
            enabled=federation_enabled,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    storage_path = _federation_storage_path(info)
    state = _load_node_state(storage_path, node_id) if storage_path else None

    if not state:
        return FederationStatus(
            enabled=True,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    peers: dict = state.get("peers", {})
    total_peers = len(peers)
    online_peers = sum(
        1
        for p in peers.values()
        if _peer_status_from_last_seen(p.get("last_seen")) == PeerStatus.ONLINE
    )

    return FederationStatus(
        enabled=True,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=_parse_iso(state.get("last_sync")),
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
