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

# Peers unseen for longer than this are considered offline.
_ONLINE_THRESHOLD = timedelta(minutes=5)


def _get_federation_storage(db_path: Optional[str]) -> Optional[Path]:
    """Return the federation storage directory for this instance, or None."""
    if not db_path:
        return None
    storage = Path(db_path).parent / "federation"
    return storage if storage.exists() else None


def _parse_ts(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp string into a timezone-aware datetime."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _peer_status(last_seen: Optional[datetime], now: datetime):
    """Return PeerStatus based on how recently the peer was seen."""
    from ..types import PeerStatus

    if last_seen is None:
        return PeerStatus.OFFLINE
    return PeerStatus.ONLINE if (now - last_seen) < _ONLINE_THRESHOLD else PeerStatus.OFFLINE


def _load_all_peers(storage: Path) -> dict:
    """
    Aggregate peer dicts from all node state files in the federation directory.
    Returns {peer_id: peer_data} with later-seen data winning on conflict.
    """
    all_peers: dict = {}
    for state_file in storage.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            for peer_id, peer_data in state.get("peers", {}).items():
                existing = all_peers.get(peer_id)
                if existing is None:
                    all_peers[peer_id] = peer_data
                else:
                    # Keep whichever record has the more recent last_seen.
                    existing_ts = _parse_ts(existing.get("last_seen"))
                    incoming_ts = _parse_ts(peer_data.get("last_seen"))
                    if incoming_ts and (existing_ts is None or incoming_ts > existing_ts):
                        all_peers[peer_id] = peer_data
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return all_peers


def _load_latest_sync(storage: Path) -> Optional[datetime]:
    """Return the most recent last_sync timestamp across all node state files."""
    latest: Optional[datetime] = None
    for state_file in storage.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            dt = _parse_ts(state.get("last_sync"))
            if dt and (latest is None or dt > latest):
                latest = dt
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return latest


async def resolve_federation_peers(info: Info) -> List:
    """
    Resolve federation peers by reading node state files from the federation
    storage directory ({db_path_parent}/federation/*.json).
    """
    from ..types import FederationPeer

    db_path = getattr(info.context, "db_path", None)
    storage = _get_federation_storage(db_path)
    if storage is None:
        return []

    now = datetime.now(timezone.utc)
    peers = []

    for peer_id, peer_data in _load_all_peers(storage).items():
        host = peer_data.get("host", "unknown")
        port = peer_data.get("port", 0)
        last_seen = _parse_ts(peer_data.get("last_seen"))

        peers.append(
            FederationPeer(
                id=strawberry.ID(peer_id),
                url=f"http://{host}:{port}",
                name=peer_id,
                status=_peer_status(last_seen, now),
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata={"host": host, "port": port},
                created_at=last_seen or now,
                updated_at=last_seen or now,
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """
    Resolve federation status by aggregating across all node state files in
    the federation storage directory ({db_path_parent}/federation/*.json).
    """
    from ..types import FederationStatus

    db_path = getattr(info.context, "db_path", None)
    storage = _get_federation_storage(db_path)

    if storage is None:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(timezone.utc)
    all_peers = _load_all_peers(storage)
    online_peers = sum(
        1
        for peer_data in all_peers.values()
        if _peer_status(_parse_ts(peer_data.get("last_seen")), now).value == "online"
    )

    return FederationStatus(
        enabled=True,
        total_peers=len(all_peers),
        online_peers=online_peers,
        last_sync=_load_latest_sync(storage),
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
