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
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from strawberry.types import Info


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    from ..types import FederationPeer, PeerStatus

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    federation_dir = Path(db_path).parent / "federation"
    if not federation_dir.exists():
        return []

    peers = []
    seen = set()
    now = datetime.now(tz=timezone.utc)

    try:
        node_files = list(federation_dir.glob("*.json"))
    except Exception:
        return []

    for node_file in node_files:
        try:
            with open(node_file) as f:
                data = json.load(f)
        except Exception:
            continue

        raw_peers = data.get("peers", {})
        if not isinstance(raw_peers, dict):
            continue

        for peer_id, peer_info in raw_peers.items():
            if peer_id in seen:
                continue
            seen.add(peer_id)

            try:
                host = peer_info.get("host", "")
                port = peer_info.get("port", 80)
                last_seen_str = peer_info.get("last_seen")

                if last_seen_str:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                else:
                    last_seen = None

                if last_seen is not None:
                    delta = (now - last_seen).total_seconds()
                    status = PeerStatus.ONLINE if delta <= 300 else PeerStatus.OFFLINE
                else:
                    status = PeerStatus.OFFLINE

                url = f"http://{host}:{port}"

                peers.append(
                    FederationPeer(
                        id=peer_id,
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
                )
            except Exception:
                continue

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
    import aiosqlite

    from ..types import FederationStatus

    db_path = info.context.get("db_path")

    federation_enabled = os.environ.get("FEDERATION_ENABLED", "").lower() in ("1", "true", "yes")

    total_peers = 0
    online_peers = 0
    last_sync = None
    now = datetime.now(tz=timezone.utc)

    if db_path:
        federation_dir = Path(db_path).parent / "federation"
        if federation_dir.exists():
            try:
                node_files = list(federation_dir.glob("*.json"))
            except Exception:
                node_files = []

            seen = set()
            for node_file in node_files:
                try:
                    with open(node_file) as f:
                        data = json.load(f)
                except Exception:
                    continue

                if data.get("registered"):
                    federation_enabled = True

                raw_peers = data.get("peers", {})
                if not isinstance(raw_peers, dict):
                    continue

                for peer_id, peer_info in raw_peers.items():
                    if peer_id in seen:
                        continue
                    seen.add(peer_id)
                    total_peers += 1

                    last_seen_str = peer_info.get("last_seen")
                    if last_seen_str:
                        try:
                            last_seen_dt = datetime.fromisoformat(last_seen_str)
                            if last_seen_dt.tzinfo is None:
                                last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
                            delta = (now - last_seen_dt).total_seconds()
                            if delta <= 300:
                                online_peers += 1
                            if last_sync is None or last_seen_dt > last_sync:
                                last_sync = last_seen_dt
                        except Exception:
                            pass

                node_last_sync_str = data.get("last_sync")
                if node_last_sync_str:
                    try:
                        node_last_sync = datetime.fromisoformat(node_last_sync_str)
                        if node_last_sync.tzinfo is None:
                            node_last_sync = node_last_sync.replace(tzinfo=timezone.utc)
                        if last_sync is None or node_last_sync > last_sync:
                            last_sync = node_last_sync
                    except Exception:
                        pass

    synced_memories = 0
    if db_path:
        try:
            async with aiosqlite.connect(db_path) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM memories")
                row = await cursor.fetchone()
                synced_memories = row[0] if row else 0
        except Exception:
            synced_memories = 0

    return FederationStatus(
        enabled=federation_enabled,
        total_peers=total_peers,
        online_peers=online_peers,
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
