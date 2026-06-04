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
from typing import Dict, List, Optional

from strawberry.types import Info


def _parse_iso(dt_str: str) -> Optional[datetime]:
    """Parse an ISO datetime string to an aware datetime, or return None."""
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _collect_peers_from_storage(storage_path: Path) -> Dict[str, dict]:
    """Read all node state files and return a deduplicated peer_id -> peer_data map."""
    seen: Dict[str, dict] = {}
    for state_file in storage_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            for peer_id, peer_data in state.get("peers", {}).items():
                if peer_id not in seen:
                    seen[peer_id] = peer_data
        except (json.JSONDecodeError, OSError):
            continue
    return seen


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from local node state files."""
    from ..types import FederationPeer, PeerStatus

    db_path_str = info.context.get("db_path")
    if not db_path_str:
        return []

    storage_path = Path(db_path_str).parent / "federation"
    if not storage_path.exists():
        return []

    now = datetime.now(timezone.utc)
    online_threshold = timedelta(minutes=5)
    peers = _collect_peers_from_storage(storage_path)

    result = []
    for peer_id, peer_data in peers.items():
        host = peer_data.get("host", "unknown")
        port = peer_data.get("port", 0)
        last_seen = _parse_iso(peer_data.get("last_seen", ""))

        if last_seen and (now - last_seen) < online_threshold:
            status = PeerStatus.ONLINE
        else:
            status = PeerStatus.OFFLINE

        ts = last_seen or now
        result.append(
            FederationPeer(
                id=peer_id,
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=0.0,
                metadata=None,
                created_at=ts,
                updated_at=ts,
            )
        )

    return result


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from local node state files."""
    from ..types import FederationStatus

    db_path_str = info.context.get("db_path")
    if not db_path_str:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    storage_path = Path(db_path_str).parent / "federation"
    if not storage_path.exists():
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(timezone.utc)
    online_threshold = timedelta(minutes=5)
    latest_sync: Optional[datetime] = None

    for state_file in storage_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            node_sync = _parse_iso(state.get("last_sync", ""))
            if node_sync and (latest_sync is None or node_sync > latest_sync):
                latest_sync = node_sync
        except (json.JSONDecodeError, OSError):
            continue

    peers = _collect_peers_from_storage(storage_path)

    online_count = sum(
        1
        for peer_data in peers.values()
        if (
            (ts := _parse_iso(peer_data.get("last_seen", ""))) is not None
            and (now - ts) < online_threshold
        )
    )

    return FederationStatus(
        enabled=storage_path.exists(),
        total_peers=len(peers),
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
