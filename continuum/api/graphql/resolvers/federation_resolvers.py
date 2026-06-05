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

from typing import List

from strawberry.types import Info

# Peers unseen for longer than this are considered offline
_ONLINE_THRESHOLD_SECONDS = 300


def _load_federation_peers(db_path: str) -> dict:
    """
    Scan federation storage for peer data from persisted node state files.

    Returns a dict of peer_id -> peer_data, deduplicating across node files.
    """
    import json
    from pathlib import Path

    storage_path = Path(db_path).parent / "federation"
    if not storage_path.exists():
        return {}

    peers: dict = {}
    for state_file in storage_path.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            for peer_id, peer_data in state.get("peers", {}).items():
                if peer_id not in peers:
                    peers[peer_id] = peer_data
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return peers


def _load_local_node_state(db_path: str) -> dict:
    """
    Read the first node state file found in federation storage.

    Returns an empty dict if no state files exist yet.
    """
    import json
    from pathlib import Path

    storage_path = Path(db_path).parent / "federation"
    if not storage_path.exists():
        return {}

    for state_file in storage_path.glob("*.json"):
        try:
            return json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
    return {}


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from persisted node state files."""
    from datetime import datetime, timezone

    import strawberry

    from ..types import FederationPeer, PeerStatus

    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return []

    raw_peers = _load_federation_peers(db_path)
    if not raw_peers:
        return []

    now = datetime.now(timezone.utc)
    result: List[FederationPeer] = []

    for peer_id, peer_data in raw_peers.items():
        host = peer_data.get("host", "unknown")
        port = peer_data.get("port", 0)
        last_seen_str = peer_data.get("last_seen")

        last_seen: datetime | None = None
        if last_seen_str:
            try:
                last_seen = datetime.fromisoformat(last_seen_str)
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        if last_seen and (now - last_seen).total_seconds() < _ONLINE_THRESHOLD_SECONDS:
            status = PeerStatus.ONLINE
        elif last_seen:
            status = PeerStatus.OFFLINE
        else:
            status = PeerStatus.UNREACHABLE

        timestamp = last_seen or now
        result.append(
            FederationPeer(
                id=strawberry.ID(peer_id),
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=0.5,
                metadata=None,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )

    return result


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from persisted node state."""
    from datetime import datetime, timezone

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

    raw_peers = _load_federation_peers(db_path)
    node_state = _load_local_node_state(db_path)
    now = datetime.now(timezone.utc)

    online_count = 0
    for peer_data in raw_peers.values():
        last_seen_str = peer_data.get("last_seen")
        if last_seen_str:
            try:
                last_seen = datetime.fromisoformat(last_seen_str)
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                if (now - last_seen).total_seconds() < _ONLINE_THRESHOLD_SECONDS:
                    online_count += 1
            except ValueError:
                pass

    last_sync: datetime | None = None
    last_sync_str = node_state.get("last_sync")
    if last_sync_str:
        try:
            last_sync = datetime.fromisoformat(last_sync_str)
            if last_sync.tzinfo is None:
                last_sync = last_sync.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    enabled = node_state.get("registered", False) or bool(raw_peers)

    return FederationStatus(
        enabled=enabled,
        total_peers=len(raw_peers),
        online_peers=online_count,
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
