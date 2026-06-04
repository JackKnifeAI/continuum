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

import hashlib
from datetime import datetime, timezone
from typing import List
from urllib.parse import urlparse

from strawberry.types import Info


async def resolve_federation_peers(info: Info) -> List:
    """Resolve federation peers from MCP configuration."""
    from ..types import FederationPeer, PeerStatus

    try:
        from continuum.mcp.config import get_mcp_config
        config = get_mcp_config()
        peer_urls = config.allowed_federation_nodes
    except Exception:
        return []

    peers = []
    now = datetime.now(timezone.utc)

    for url in peer_urls:
        parsed = urlparse(url)
        name = parsed.hostname or url

        # Deterministic ID from URL so the same peer always has the same ID
        peer_id = hashlib.sha256(url.encode()).hexdigest()[:32]

        peers.append(
            FederationPeer(
                id=peer_id,
                url=url,
                name=name,
                # Status is unknown without an outbound probe; callers
                # can trigger explicit sync to get a live status.
                status=PeerStatus.OFFLINE,
                last_sync=None,
                shared_memories=0,
                trust_score=1.0,
                metadata=None,
                created_at=now,
                updated_at=now,
            )
        )

    return peers


async def resolve_federation_status(info: Info) -> dict:
    """Resolve federation status from MCP configuration."""
    from ..types import FederationStatus

    try:
        from continuum.mcp.config import get_mcp_config
        config = get_mcp_config()
        enabled = config.enable_federation
        total_peers = len(config.allowed_federation_nodes)
    except Exception:
        enabled = False
        total_peers = 0

    return FederationStatus(
        enabled=enabled,
        total_peers=total_peers,
        # Online peer count requires live probes; reported as 0 until
        # an explicit sync populates per-peer status in the database.
        online_peers=0,
        last_sync=None,
        synced_memories=0,
        pending_sync=0,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
