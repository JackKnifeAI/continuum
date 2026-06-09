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
from typing import Dict, List, Optional

from strawberry.types import Info

# Storage path matches FederatedNode default in continuum/federation/node.py
_FEDERATION_STORAGE = Path.home() / ".continuum" / "federation"

# Peer is considered online if seen within this window
_ONLINE_THRESHOLD_SECONDS = 300


def _parse_utc(ts: Optional[str]) -> Optional[datetime]:
    """Parse an ISO datetime string, ensuring UTC tzinfo."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _load_node_states() -> List[Dict]:
    """Read all node state JSON files from the federation storage directory."""
    if not _FEDERATION_STORAGE.exists():
        return []
    states = []
    for state_file in _FEDERATION_STORAGE.glob("*.json"):
        try:
            states.append(json.loads(state_file.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return states


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from local node state files."""
    from ..types import FederationPeer, PeerStatus

    states = _load_node_states()
    if not states:
        return []

    seen: Dict[str, FederationPeer] = {}
    now = datetime.now(timezone.utc)

    for state in states:
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen:
                continue

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen = _parse_utc(peer_data.get("last_seen"))

            if last_seen is not None:
                age = (now - last_seen).total_seconds()
                status = PeerStatus.ONLINE if age < _ONLINE_THRESHOLD_SECONDS else PeerStatus.OFFLINE
            else:
                status = PeerStatus.OFFLINE

            ts = last_seen or now
            seen[peer_id] = FederationPeer(
                id=peer_id,
                url=f"http://{host}:{port}",
                name=peer_id,
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
    """Resolve federation status from local node state files."""
    from ..types import FederationStatus

    states = _load_node_states()
    if not states:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(timezone.utc)
    seen_online: Dict[str, bool] = {}
    last_sync: Optional[datetime] = None

    for state in states:
        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen_online:
                continue
            last_seen = _parse_utc(peer_data.get("last_seen"))
            if last_seen is not None:
                seen_online[peer_id] = (now - last_seen).total_seconds() < _ONLINE_THRESHOLD_SECONDS
            else:
                seen_online[peer_id] = False

        sync_dt = _parse_utc(state.get("last_sync"))
        if sync_dt is not None and (last_sync is None or sync_dt > last_sync):
            last_sync = sync_dt

    return FederationStatus(
        enabled=True,
        total_peers=len(seen_online),
        online_peers=sum(1 for online in seen_online.values() if online),
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
