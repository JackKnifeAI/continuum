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

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from strawberry.types import Info

if TYPE_CHECKING:
    from ..types import FederationStatus


def _parse_timestamp(raw: object, fallback: Optional[datetime] = None) -> Optional[datetime]:
    """Parse an epoch float, ISO string, or datetime into a UTC-aware datetime."""
    if raw is None:
        return fallback
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(raw))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return fallback


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from the FederationNode stored in context."""
    from ..types import FederationPeer, PeerStatus

    federation = info.context.get("federation")
    if not federation:
        return []

    now = datetime.now(tz=timezone.utc)
    peers = []

    for peer_id, peer_data in federation.peers.items():
        host = peer_data.get("host", "")
        port = peer_data.get("port")
        url = f"http://{host}:{port}" if port else host

        last_seen = _parse_timestamp(peer_data.get("last_seen"))

        if last_seen is None:
            status = PeerStatus.UNREACHABLE
        elif (now - last_seen).total_seconds() < 300:
            status = PeerStatus.ONLINE
        else:
            status = PeerStatus.OFFLINE

        peers.append(
            FederationPeer(
                id=peer_id,
                url=url,
                name=peer_data.get("name"),
                status=status,
                last_sync=last_seen,
                shared_memories=int(peer_data.get("shared_memories", 0)),
                trust_score=float(peer_data.get("trust_score", 0.0)),
                metadata=peer_data.get("metadata"),
                created_at=_parse_timestamp(peer_data.get("created_at"), now),
                updated_at=_parse_timestamp(peer_data.get("updated_at"), now),
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> "FederationStatus":
    """Resolve federation status"""
    from ..types import FederationStatus

    federation = info.context.get("federation")
    if not federation:
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    now = datetime.now(tz=timezone.utc)
    total_peers = len(federation.peers)
    online_peers = 0
    latest_sync: Optional[datetime] = None

    for peer_data in federation.peers.values():
        last_seen = _parse_timestamp(peer_data.get("last_seen"))

        if last_seen is not None:
            if (now - last_seen).total_seconds() < 300:
                online_peers += 1
            if latest_sync is None or last_seen > latest_sync:
                latest_sync = last_seen

    synced_memories = int(getattr(federation, "contribution_score", 0) or 0)

    return FederationStatus(
        enabled=True,
        total_peers=total_peers,
        online_peers=online_peers,
        last_sync=latest_sync,
        synced_memories=synced_memories,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
