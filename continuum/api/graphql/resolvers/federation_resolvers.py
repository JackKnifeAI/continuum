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

from strawberry.types import Info

# Peers last seen within this window are considered ONLINE
_ONLINE_THRESHOLD_SECONDS = 300


def _get_federation_dir(db_path: Optional[str]) -> Optional[Path]:
    """Return the federation state directory for this db, or None if unavailable."""
    if not db_path:
        return None
    fed_dir = Path(db_path).parent / "federation"
    return fed_dir if fed_dir.exists() else None


def _load_all_peers(federation_dir: Path) -> dict:
    """Scan all node state files and collect unique peers by peer_id."""
    peers: dict = {}
    for state_file in federation_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            for peer_id, peer_data in state.get("peers", {}).items():
                if peer_id not in peers:
                    peers[peer_id] = peer_data
        except (json.JSONDecodeError, OSError):
            continue
    return peers


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from persisted node state files."""
    from ..types import FederationPeer, PeerStatus

    federation_dir = _get_federation_dir(getattr(info.context, "db_path", None))
    if federation_dir is None:
        return []

    peers = _load_all_peers(federation_dir)
    now = datetime.now(timezone.utc)
    result = []

    for peer_id, peer_data in peers.items():
        host = peer_data.get("host", "unknown")
        port = peer_data.get("port", 0)
        url = f"http://{host}:{port}"

        last_sync: Optional[datetime] = None
        status = PeerStatus.OFFLINE
        last_seen_str = peer_data.get("last_seen")
        if last_seen_str:
            try:
                last_sync = datetime.fromisoformat(last_seen_str)
                age = (now - last_sync).total_seconds()
                status = PeerStatus.ONLINE if age < _ONLINE_THRESHOLD_SECONDS else PeerStatus.OFFLINE
            except ValueError:
                pass

        timestamp = last_sync or now
        result.append(FederationPeer(
            id=peer_id,
            url=url,
            name=None,
            status=status,
            last_sync=last_sync,
            shared_memories=0,
            trust_score=0.5,
            metadata=None,
            created_at=timestamp,
            updated_at=timestamp,
        ))

    return result


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status by aggregating persisted node state files."""
    from ..types import FederationStatus

    federation_dir = _get_federation_dir(getattr(info.context, "db_path", None))
    if federation_dir is None:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    enabled = False
    last_sync: Optional[datetime] = None
    now = datetime.now(timezone.utc)

    for state_file in federation_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            enabled = enabled or state.get("registered", False)
            sync_str = state.get("last_sync")
            if sync_str:
                try:
                    sync_dt = datetime.fromisoformat(sync_str)
                    if last_sync is None or sync_dt > last_sync:
                        last_sync = sync_dt
                except ValueError:
                    pass
        except (json.JSONDecodeError, OSError):
            continue

    peers = _load_all_peers(federation_dir)
    online_peers = sum(
        1 for p in peers.values()
        if p.get("last_seen") and _is_online(p["last_seen"], now)
    )

    return FederationStatus(
        enabled=enabled,
        total_peers=len(peers),
        online_peers=online_peers,
        last_sync=last_sync,
        synced_memories=0,
        pending_sync=0,
    )


def _is_online(last_seen_str: str, now: datetime) -> bool:
    """Return True if last_seen is within the online threshold."""
    try:
        last_seen = datetime.fromisoformat(last_seen_str)
        return (now - last_seen).total_seconds() < _ONLINE_THRESHOLD_SECONDS
    except ValueError:
        return False

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
