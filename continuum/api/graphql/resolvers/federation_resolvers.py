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

from strawberry.types import Info


def _get_federation_storage(info: Info) -> Path:
    db_path = getattr(info.context, "db_path", None)
    if db_path:
        return Path(db_path).parent / "federation"
    return Path.home() / ".continuum" / "federation"


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from node state files on disk."""
    from ..types import FederationPeer, PeerStatus

    storage = _get_federation_storage(info)
    if not storage.exists():
        return []

    now = datetime.now(timezone.utc)
    seen: set = set()
    peers = []

    for state_file in storage.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for peer_id, peer_data in state.get("peers", {}).items():
            if peer_id in seen:
                continue
            seen.add(peer_id)

            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen: Optional[datetime] = None
            last_seen_str = peer_data.get("last_seen")
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            if last_seen:
                status = PeerStatus.ONLINE if (now - last_seen) < timedelta(minutes=5) else PeerStatus.OFFLINE
            else:
                status = PeerStatus.OFFLINE

            ts = last_seen or now
            peers.append(FederationPeer(
                id=peer_id,
                url=f"http://{host}:{port}",
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=ts,
                updated_at=ts,
            ))

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status aggregated from all local node state files."""
    from ..types import FederationStatus

    storage = _get_federation_storage(info)

    enabled = False
    total_peers = 0
    online_peers = 0
    last_sync: Optional[datetime] = None

    if storage.exists():
        now = datetime.now(timezone.utc)
        seen: set = set()

        for state_file in storage.glob("*.json"):
            try:
                state = json.loads(state_file.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if state.get("registered"):
                enabled = True

            sync_str = state.get("last_sync")
            if sync_str:
                try:
                    sync_time = datetime.fromisoformat(sync_str)
                    if sync_time.tzinfo is None:
                        sync_time = sync_time.replace(tzinfo=timezone.utc)
                    if last_sync is None or sync_time > last_sync:
                        last_sync = sync_time
                except ValueError:
                    pass

            for peer_id, peer_data in state.get("peers", {}).items():
                if peer_id in seen:
                    continue
                seen.add(peer_id)
                total_peers += 1

                last_seen_str = peer_data.get("last_seen")
                if last_seen_str:
                    try:
                        last_seen = datetime.fromisoformat(last_seen_str)
                        if last_seen.tzinfo is None:
                            last_seen = last_seen.replace(tzinfo=timezone.utc)
                        if (now - last_seen) < timedelta(minutes=5):
                            online_peers += 1
                    except ValueError:
                        pass

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
