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

from datetime import datetime, timedelta, timezone
from typing import List

from strawberry.types import Info


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers"""
    from continuum.federation.node import FederationNode

    from ..types import FederationPeer, PeerStatus

    try:
        tenant_id = getattr(info.context, "tenant_id", None)
        db_path = getattr(info.context, "db_path", None)
        if not tenant_id or not db_path:
            return []

        node = FederationNode(node_id=tenant_id, port=0, db_path=db_path)

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=5)
        peers = []

        for peer_id, peer_data in node.peers.items():
            host = peer_data.get("host", "unknown")
            port = peer_data.get("port", 0)
            last_seen_str = peer_data.get("last_seen")

            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                except ValueError:
                    last_seen = None
            else:
                last_seen = None

            status = PeerStatus.ONLINE if (last_seen and last_seen >= cutoff) else PeerStatus.OFFLINE
            url = f"http://{host}:{port}"
            timestamp = last_seen if last_seen else now

            peers.append(FederationPeer(
                id=peer_id,
                url=url,
                name=None,
                status=status,
                last_sync=last_seen,
                shared_memories=0,
                trust_score=0.0,
                metadata=None,
                created_at=timestamp,
                updated_at=timestamp,
            ))

        return peers
    except Exception:
        return []


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status"""
    from continuum.federation.node import FederationNode

    from ..types import FederationStatus

    def _disabled_status():
        return FederationStatus(
            enabled=False,
            total_peers=0,
            online_peers=0,
            last_sync=None,
            synced_memories=0,
            pending_sync=0,
        )

    try:
        tenant_id = getattr(info.context, "tenant_id", None)
        db_path = getattr(info.context, "db_path", None)
        if not tenant_id or not db_path:
            return _disabled_status()

        node = FederationNode(node_id=tenant_id, port=0, db_path=db_path)

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=5)
        online_peers = 0

        for peer_data in node.peers.values():
            last_seen_str = peer_data.get("last_seen")
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                    if last_seen >= cutoff:
                        online_peers += 1
                except ValueError:
                    pass

        return FederationStatus(
            enabled=node.registered,
            total_peers=len(node.peers),
            online_peers=online_peers,
            last_sync=node.last_sync,
            synced_memories=0,
            pending_sync=0,
        )
    except Exception:
        return _disabled_status()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
