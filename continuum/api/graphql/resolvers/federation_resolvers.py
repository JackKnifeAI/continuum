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
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from strawberry.types import Info

logger = logging.getLogger(__name__)

# Peers last seen within this window are considered ONLINE
_ONLINE_THRESHOLD = timedelta(minutes=5)


def _get_federation_storage(info: Info) -> Optional[Path]:
    """Derive the federation state directory from the context db_path."""
    ctx = info.context
    db_path = getattr(ctx, "db_path", None) or (ctx.get("db_path") if isinstance(ctx, dict) else None)
    if not db_path:
        return None
    return Path(db_path).parent / "federation"


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the local node state files."""
    from ..types import FederationPeer, PeerStatus

    storage = _get_federation_storage(info)
    if not storage or not storage.exists():
        return []

    now = datetime.now(timezone.utc)
    peers_by_id: dict = {}

    for state_file in storage.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read federation state file: %s", state_file)
            continue

        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in peers_by_id:
                continue  # deduplicate

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen_str = peer_data.get("last_seen")
            last_seen = _parse_dt(last_seen_str)

            # Make last_seen timezone-aware for comparison
            if last_seen and last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)

            if last_seen and (now - last_seen) <= _ONLINE_THRESHOLD:
                status = PeerStatus.ONLINE
            elif last_seen:
                status = PeerStatus.OFFLINE
            else:
                status = PeerStatus.UNREACHABLE

            peers_by_id[peer_id] = FederationPeer(
                id=peer_id,
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=last_seen or now,
                updated_at=last_seen or now,
            )

    return list(peers_by_id.values())


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from local node state and shared knowledge pool."""
    from ..types import FederationStatus

    storage = _get_federation_storage(info)
    if not storage or not storage.exists():
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(timezone.utc)
    total_peers: set = set()
    online_peers: set = set()
    last_sync: Optional[datetime] = None

    for state_file in storage.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # Track peers seen by any local node state
        for peer_id, peer_data in state.get("peers", {}).items():
            total_peers.add(peer_id)
            last_seen_str = peer_data.get("last_seen")
            last_seen = _parse_dt(last_seen_str)
            if last_seen:
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                if (now - last_seen) <= _ONLINE_THRESHOLD:
                    online_peers.add(peer_id)

        # Track most recent sync across all local node states
        node_sync = _parse_dt(state.get("last_sync"))
        if node_sync:
            if node_sync.tzinfo is None:
                node_sync = node_sync.replace(tzinfo=timezone.utc)
            if last_sync is None or node_sync > last_sync:
                last_sync = node_sync

    # Count shared memories from the knowledge pool
    synced_memories = 0
    try:
        from continuum.federation.shared import SharedKnowledge
        shared = SharedKnowledge(storage_path=storage / "shared")
        synced_memories = len(shared.concepts)
    except Exception:
        pass

    enabled = len(total_peers) > 0 or last_sync is not None

    return FederationStatus(
        enabled=enabled,
        total_peers=len(total_peers),
        online_peers=len(online_peers),
        last_sync=last_sync,
        synced_memories=synced_memories,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
