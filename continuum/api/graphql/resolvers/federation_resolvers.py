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


def _load_federation_state_files(db_path: Path) -> List[dict]:
    federation_dir = db_path.parent / "federation"
    if not federation_dir.exists() or not federation_dir.is_dir():
        return []
    state_files = []
    for json_file in federation_dir.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            state_files.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return state_files


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    from ..types import FederationPeer, PeerStatus

    db_path_raw = info.context.get("db_path") if info.context else None
    if not db_path_raw:
        return []

    db_path = Path(db_path_raw)
    state_files = _load_federation_state_files(db_path)
    if not state_files:
        return []

    now = datetime.now(tz=timezone.utc)
    online_threshold = timedelta(minutes=5)

    seen_peer_ids: dict = {}
    for state in state_files:
        peers = state.get("peers", {})
        for peer_id, peer_data in peers.items():
            if peer_id in seen_peer_ids:
                continue
            host = peer_data.get("host", "")
            port = peer_data.get("port", 0)
            url = f"http://{host}:{port}" if host else ""
            last_seen_raw: Optional[str] = peer_data.get("last_seen")
            last_seen: Optional[datetime] = None
            if last_seen_raw:
                try:
                    last_seen = datetime.fromisoformat(last_seen_raw)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                except ValueError:
                    last_seen = None

            if last_seen and (now - last_seen) <= online_threshold:
                status = PeerStatus.ONLINE
            else:
                status = PeerStatus.OFFLINE

            peer_obj = FederationPeer(
                id=strawberry.ID(peer_id),
                url=url,
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=last_seen or now,
                updated_at=last_seen or now,
            )
            seen_peer_ids[peer_id] = peer_obj

    return list(seen_peer_ids.values())


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
    from ..types import FederationStatus

    db_path_raw = info.context.get("db_path") if info.context else None
    if not db_path_raw:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    db_path = Path(db_path_raw)
    state_files = _load_federation_state_files(db_path)
    if not state_files:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(tz=timezone.utc)
    online_threshold = timedelta(minutes=5)

    seen_peer_ids: set = set()
    online_count = 0
    latest_sync: Optional[datetime] = None

    for state in state_files:
        last_sync_raw: Optional[str] = state.get("last_sync")
        if last_sync_raw:
            try:
                last_sync_dt = datetime.fromisoformat(last_sync_raw)
                if last_sync_dt.tzinfo is None:
                    last_sync_dt = last_sync_dt.replace(tzinfo=timezone.utc)
                if latest_sync is None or last_sync_dt > latest_sync:
                    latest_sync = last_sync_dt
            except ValueError:
                pass

        peers = state.get("peers", {})
        for peer_id, peer_data in peers.items():
            already_seen = peer_id in seen_peer_ids
            seen_peer_ids.add(peer_id)
            if already_seen:
                continue

            last_seen_raw: Optional[str] = peer_data.get("last_seen")
            if last_seen_raw:
                try:
                    last_seen = datetime.fromisoformat(last_seen_raw)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                    if (now - last_seen) <= online_threshold:
                        online_count += 1
                except ValueError:
                    pass

    return FederationStatus(
        enabled=True,
        total_peers=len(seen_peer_ids),
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
