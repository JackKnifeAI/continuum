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
from typing import List, Optional

import strawberry
from strawberry.types import Info

# Peers unseen for longer than this are considered OFFLINE
_ONLINE_THRESHOLD_SECONDS = 300


def _get_federation_storage_path(info: Info) -> Path:
    """Derive federation state directory from GraphQL context db_path."""
    db_path_str = getattr(info.context, "db_path", None)
    if db_path_str:
        return Path(db_path_str).parent / "federation"
    return Path.home() / ".continuum" / "federation"


def _peer_status_from_last_seen(last_seen_iso: Optional[str]):
    """Return PeerStatus based on how recently the peer was seen."""
    from ..types import PeerStatus

    if not last_seen_iso:
        return PeerStatus.OFFLINE

    try:
        last_seen = datetime.fromisoformat(last_seen_iso)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - last_seen).total_seconds()
        return PeerStatus.ONLINE if age <= _ONLINE_THRESHOLD_SECONDS else PeerStatus.OFFLINE
    except (ValueError, OverflowError):
        return PeerStatus.OFFLINE


def _load_all_peers(storage_path: Path) -> List[dict]:
    """Read all JSON node state files and collect peer records."""
    peers: dict = {}  # peer_id -> merged peer dict

    if not storage_path.exists():
        return []

    for state_file in storage_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        node_last_sync = state.get("last_sync")

        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in peers:
                # Keep the entry with the most recent last_seen
                existing = peers[peer_id].get("last_seen")
                incoming = peer_data.get("last_seen")
                if existing and incoming and incoming > existing:
                    peers[peer_id] = {**peer_data, "peer_id": peer_id, "node_last_sync": node_last_sync}
            else:
                peers[peer_id] = {**peer_data, "peer_id": peer_id, "node_last_sync": node_last_sync}

    return list(peers.values())


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from on-disk node state files."""
    from ..types import FederationPeer

    storage_path = _get_federation_storage_path(info)
    raw_peers = _load_all_peers(storage_path)

    result = []
    for peer in raw_peers:
        peer_id = peer.get("peer_id", "unknown")
        host = peer.get("host", "unknown")
        port = peer.get("port", 0)
        last_seen_iso = peer.get("last_seen")
        url = f"http://{host}:{port}" if port else f"http://{host}"

        last_sync: Optional[datetime] = None
        if last_seen_iso:
            try:
                last_sync = datetime.fromisoformat(last_seen_iso)
                if last_sync.tzinfo is None:
                    last_sync = last_sync.replace(tzinfo=timezone.utc)
            except (ValueError, OverflowError):
                last_sync = None

        now = datetime.now(timezone.utc)
        status = _peer_status_from_last_seen(last_seen_iso)

        result.append(
            FederationPeer(
                id=strawberry.ID(peer_id),
                url=url,
                name=None,
                status=status,
                last_sync=last_sync,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=last_sync or now,
                updated_at=last_sync or now,
            )
        )

    return result


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status aggregated from on-disk node state files."""
    from ..types import FederationStatus, PeerStatus

    storage_path = _get_federation_storage_path(info)
    raw_peers = _load_all_peers(storage_path)

    enabled = storage_path.exists()
    total_peers = len(raw_peers)
    online_peers = sum(
        1 for p in raw_peers
        if _peer_status_from_last_seen(p.get("last_seen")) == PeerStatus.ONLINE
    )

    last_sync: Optional[datetime] = None
    for peer in raw_peers:
        ts_str = peer.get("last_seen") or peer.get("node_last_sync")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if last_sync is None or ts > last_sync:
                last_sync = ts
        except (ValueError, OverflowError):
            continue

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=last_sync,
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
