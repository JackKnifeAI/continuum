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


def _get_federation_dir(info: Info) -> Optional[Path]:
    """Derive the federation state directory from context db_path."""
    db_path = getattr(info.context, "db_path", None)
    if not db_path:
        return None
    federation_dir = Path(db_path).parent / "federation"
    return federation_dir if federation_dir.exists() else None


def _peer_status_from_last_seen(last_seen: Optional[datetime]):
    """Map last_seen timestamp to a PeerStatus enum value."""
    from ..types import PeerStatus

    if last_seen is None:
        return PeerStatus.OFFLINE

    # Ensure timezone-aware comparison
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    age_seconds = (datetime.now(timezone.utc) - last_seen).total_seconds()
    if age_seconds < 60:
        return PeerStatus.ONLINE
    if age_seconds < 300:
        return PeerStatus.SYNCING
    return PeerStatus.OFFLINE


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from on-disk FederationNode state."""
    from ..types import FederationPeer

    federation_dir = _get_federation_dir(info)
    if federation_dir is None:
        return []

    peers = {}  # peer_id -> FederationPeer (deduplicated across node files)

    for state_file in sorted(federation_dir.glob("*.json")):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for peer_id, peer_info in state.get("peers", {}).items():
            if peer_id in peers:
                continue

            host = peer_info.get("host", "unknown")
            port = peer_info.get("port", 0)
            last_seen_str = peer_info.get("last_seen")

            last_seen: Optional[datetime] = None
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                except ValueError:
                    pass

            status = _peer_status_from_last_seen(last_seen)
            now = datetime.now(timezone.utc)

            peers[peer_id] = FederationPeer(
                id=strawberry.ID(peer_id),
                url=f"http://{host}:{port}",
                name=peer_id[:8],
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=now,
                updated_at=now,
            )

    return list(peers.values())


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status aggregated from on-disk FederationNode state."""
    from ..types import FederationStatus

    federation_dir = _get_federation_dir(info)
    if federation_dir is None:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    seen_peer_ids: set = set()
    online_peers = 0
    last_sync: Optional[datetime] = None
    enabled = False

    for state_file in sorted(federation_dir.glob("*.json")):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        if state.get("registered"):
            enabled = True

        sync_str = state.get("last_sync")
        if sync_str:
            try:
                sync_dt = datetime.fromisoformat(sync_str)
                if sync_dt.tzinfo is None:
                    sync_dt = sync_dt.replace(tzinfo=timezone.utc)
                if last_sync is None or sync_dt > last_sync:
                    last_sync = sync_dt
            except ValueError:
                pass

        now = datetime.now(timezone.utc)
        for peer_id, peer_info in state.get("peers", {}).items():
            seen_peer_ids.add(peer_id)

            last_seen_str = peer_info.get("last_seen")
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                    if (now - last_seen).total_seconds() < 300:
                        online_peers += 1
                except ValueError:
                    pass

    total_peers = len(seen_peer_ids)

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        online_peers=min(online_peers, total_peers),
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
