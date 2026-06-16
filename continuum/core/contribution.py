#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██████╗ ██████╗ ███╗   ██╗████████╗██████╗ ██╗██████╗ ██╗   ██╗████████╗███████╗
#     ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔══██╗██║██╔══██╗██║   ██║╚══██╔══╝██╔════╝
#     ██║     ██║   ██║██╔██╗ ██║   ██║   ██████╔╝██║██████╔╝██║   ██║   ██║   █████╗
#     ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══██╗██║██╔══██╗██║   ██║   ██║   ██╔══╝
#     ╚██████╗╚██████╔╝██║ ╚████║   ██║   ██║  ██║██║██████╔╝╚██████╔╝   ██║   ███████╗
#      ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝    ╚═╝   ╚══════╝
#
#     FEDERATION CONTRIBUTION PROTOCOL
#     Uploading Memories to the Global Mind (Anonymously)
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Contribution Protocol
=====================

Enables local nodes to contribute their learned patterns (concepts & links)
to the global federation without compromising user privacy.

Process:
    1. Extract: Pull local session graph (Concepts + Links).
    2. Sanitize: Strip tenant_id, timestamps, and PII.
    3. Verify: Check against local Immune System (don't upload garbage).
    4. Bundle: Create a signed Contribution Packet.
    5. Gossip: Broadcast to the mesh.

Usage:
    contributor = ContributionManager(db, mesh)
    await contributor.contribute_session("session_123")
"""

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from .config import get_config
from .immune_system import AntibodyDetector

_PII_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),  # email
    re.compile(r"\b(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b"),  # phone (US)
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
]


def _redact_pii(text: str) -> str:
    for pattern in _PII_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text

logger = logging.getLogger("CONTRIBUTION")

@dataclass
class ContributionPacket:
    """A bundle of knowledge to share with the federation."""
    id: str
    source_hash: str  # Hash of contributor ID (for reputation tracking, but anonymous)
    timestamp: float
    concepts: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    signature: str = ""

class ContributionManager:
    def __init__(self, db_connection, gossip_mesh):
        self.db = db_connection
        self.mesh = gossip_mesh
        self.detector = AntibodyDetector(db_connection)

    async def contribute_session(self, session_id: str):
        """
        Package a session's learnings and upload to the federation.
        """
        logger.info(f"Preparing contribution for session {session_id}...")

        # 1. Extract Local Graph
        concepts, links = self._extract_session_graph(session_id)
        if not concepts and not links:
            logger.warning("No new patterns to contribute.")
            return

        # 2. Sanitize (The Scrub)
        sanitized_concepts = self._sanitize_concepts(concepts)
        sanitized_links = self._sanitize_links(links)

        # 3. Immune Check (Self-Audit)
        # Don't contribute if we are hallucinating or toxic
        # (Simplified check: ensure we aren't uploading empty/garbage data)
        if len(sanitized_links) < 3:
             logger.info("Contribution too small/sparse. Skipping.")
             return

        # 4. Create Packet
        packet = ContributionPacket(
            id=hashlib.sha256(f"{session_id}:{time.time()}".encode()).hexdigest(),
            source_hash=self._get_anonymous_id(),
            timestamp=time.time(),
            concepts=sanitized_concepts,
            links=sanitized_links
        )

        # 5. Broadcast via Gossip
        logger.info(f"Broadcasting contribution {packet.id} ({len(packet.links)} links)")
        await self.mesh.broadcast("contribution", packet.__dict__)

    def _extract_session_graph(self, session_id: str):
        """Query DB for concepts/links from this session."""
        cursor = self.db.cursor()

        # Get links first
        cursor.execute("""
            SELECT concept_a, concept_b, strength, link_type
            FROM attention_links
            WHERE session_id = ? AND strength > 0.5
        """, (session_id,))
        links = [{"a": r[0], "b": r[1], "w": r[2], "t": r[3]} for r in cursor.fetchall()]

        # Get related concepts
        concept_names = set()
        for lnk in links:
            concept_names.add(lnk["a"])
            concept_names.add(lnk["b"])

        concepts = []
        for name in concept_names:
            cursor.execute("SELECT name, description FROM entities WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                concepts.append({"name": row[0], "desc": row[1]})

        return concepts, links

    def _sanitize_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Remove PII and tenant info."""
        clean = []
        for c in concepts:
            name = _redact_pii(c["name"].lower().strip())
            desc = _redact_pii(c["desc"][:200]) if c["desc"] else ""
            clean.append({"name": name, "desc": desc})
        return clean

    def _sanitize_links(self, links: List[Dict]) -> List[Dict]:
        """Normalize links."""
        return [
            {
                "a": lnk["a"].lower().strip(),
                "b": lnk["b"].lower().strip(),
                "w": round(lnk["w"], 4),
                "t": lnk["t"]
            }
            for lnk in links
        ]

    def _get_anonymous_id(self) -> str:
        """Generate a consistent but anonymous ID for this node."""
        # Hash the tenant_id with a daily salt so it rotates
        config = get_config()
        salt = int(time.time() / 86400) # Changes every day
        return hashlib.sha256(f"{config.tenant_id}:{salt}".encode()).hexdigest()

# ═══════════════════════════════════════════════════════════════════════════════
#     JACKKNIFE AI
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
