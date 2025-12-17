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
Shared Knowledge - Anonymized concept sharing across the federation.

Concepts are stripped of personal data (tenant IDs, user context) before
sharing. Content hashing ensures deduplication across the federation.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib


class SharedKnowledge:
    """
    Manages the shared knowledge pool across the federation.

    Key principles:
    - Privacy through anonymization (no tenant IDs, no personal context)
    - Deduplication via content hashing
    - Attribution tracking (which nodes contributed what)
    - Quality scoring (based on usage and feedback)
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize shared knowledge pool.

        Args:
            storage_path: Where to store shared knowledge
        """
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "shared"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Shared concepts indexed by content hash
        self.concepts: Dict[str, Dict[str, Any]] = {}

        # Track which nodes contributed what (for attribution)
        self.attributions: Dict[str, Set[str]] = {}  # concept_hash -> set of node_ids

        self._load_knowledge()

    def contribute_concepts(
        self,
        node_id: str,
        concepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Contribute anonymized concepts to the shared pool.

        Args:
            node_id: The contributing node
            concepts: List of concepts to share (will be anonymized)

        Returns:
            Contribution result with count of new vs duplicate concepts
        """
        new_concepts = 0
        duplicate_concepts = 0
        anonymized_concepts = []

        for concept in concepts:
            # Anonymize the concept (remove personal data)
            anon_concept = self._anonymize_concept(concept)

            # Generate content hash for deduplication
            content_hash = self._hash_concept(anon_concept)

            # Check if this concept already exists
            if content_hash in self.concepts:
                duplicate_concepts += 1
                # Still record attribution
                if content_hash not in self.attributions:
                    self.attributions[content_hash] = set()
                self.attributions[content_hash].add(node_id)
            else:
                new_concepts += 1
                # Add to shared pool
                self.concepts[content_hash] = {
                    "concept": anon_concept,
                    "hash": content_hash,
                    "first_contributed": datetime.now(timezone.utc).isoformat(),
                    "usage_count": 0,
                    "quality_score": 0.0,
                }
                # Record attribution
                self.attributions[content_hash] = {node_id}
                anonymized_concepts.append(anon_concept)

        # Save updated knowledge pool
        self._save_knowledge()

        return {
            "status": "contributed",
            "new_concepts": new_concepts,
            "duplicate_concepts": duplicate_concepts,
            "total_submitted": len(concepts),
            "contribution_value": new_concepts * 1.0,  # Each new concept worth 1.0
        }

    def get_shared_concepts(
        self,
        query: Optional[str] = None,
        limit: int = 100,
        min_quality: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve concepts from the shared pool.

        Args:
            query: Optional search query (searches in concept content)
            limit: Maximum number of concepts to return
            min_quality: Minimum quality score threshold

        Returns:
            List of matching concepts
        """
        # Filter by quality
        filtered_concepts = [
            c for c in self.concepts.values()
            if c["quality_score"] >= min_quality
        ]

        # If query provided, filter by content
        if query:
            query_lower = query.lower()
            filtered_concepts = [
                c for c in filtered_concepts
                if self._matches_query(c["concept"], query_lower)
            ]

        # Sort by quality score (descending)
        filtered_concepts.sort(key=lambda c: c["quality_score"], reverse=True)

        # Limit results
        results = filtered_concepts[:limit]

        # Increment usage count for returned concepts
        for concept in results:
            concept["usage_count"] += 1
            # Simple quality score: usage_count / days_since_contribution
            days_since = self._days_since_contribution(concept["first_contributed"])
            if days_since > 0:
                concept["quality_score"] = concept["usage_count"] / days_since

        self._save_knowledge()

        # Return just the concept data (strip internal metadata)
        return [
            {
                "concept": c["concept"],
                "quality_score": c["quality_score"],
                "usage_count": c["usage_count"],
            }
            for c in results
        ]

    def merge_knowledge(
        self,
        external_concepts: List[Dict[str, Any]],
        source: str = "federation"
    ) -> Dict[str, Any]:
        """
        Merge knowledge from another federation node or server.

        Args:
            external_concepts: Concepts from external source
            source: Source identifier

        Returns:
            Merge result statistics
        """
        merged = 0
        duplicates = 0

        for ext_concept in external_concepts:
            content_hash = self._hash_concept(ext_concept)

            if content_hash not in self.concepts:
                merged += 1
                self.concepts[content_hash] = {
                    "concept": ext_concept,
                    "hash": content_hash,
                    "first_contributed": datetime.now(timezone.utc).isoformat(),
                    "usage_count": 0,
                    "quality_score": 0.0,
                    "source": source,
                }
                # External sources get generic attribution
                self.attributions[content_hash] = {f"external:{source}"}
            else:
                duplicates += 1

        self._save_knowledge()

        return {
            "status": "merged",
            "merged": merged,
            "duplicates": duplicates,
            "source": source,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the shared knowledge pool.

        Returns:
            Statistics dictionary
        """
        total_concepts = len(self.concepts)
        total_contributors = len(set(
            node_id
            for node_set in self.attributions.values()
            for node_id in node_set
        ))

        avg_quality = 0.0
        if total_concepts > 0:
            avg_quality = sum(c["quality_score"] for c in self.concepts.values()) / total_concepts

        return {
            "total_concepts": total_concepts,
            "total_contributors": total_contributors,
            "average_quality": avg_quality,
            "storage_path": str(self.storage_path),
        }

    def _anonymize_concept(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize a concept by removing personal data.

        Removes:
        - tenant_id
        - user_id
        - session_id
        - Any field starting with 'user_' or 'tenant_'
        - timestamps (replaced with generic timestamp)
        """
        anon = {}

        # Fields to always exclude
        exclude_fields = {"tenant_id", "user_id", "session_id", "id"}

        for key, value in concept.items():
            # Skip excluded fields
            if key in exclude_fields:
                continue

            # Skip fields starting with user_ or tenant_
            if key.startswith("user_") or key.startswith("tenant_"):
                continue

            # Anonymize timestamps
            if key.endswith("_at") or key.endswith("_time"):
                continue

            # Keep the rest
            anon[key] = value

        return anon

    def _hash_concept(self, concept: Dict[str, Any]) -> str:
        """
        Generate a content hash for deduplication.

        Uses sorted JSON representation for consistent hashing.
        """
        # Sort keys for consistent hashing
        sorted_json = json.dumps(concept, sort_keys=True)
        return hashlib.sha256(sorted_json.encode()).hexdigest()

    def _matches_query(self, concept: Dict[str, Any], query: str) -> bool:
        """Check if a concept matches a search query."""
        # Simple string matching in concept values
        concept_str = json.dumps(concept).lower()
        return query in concept_str

    def _days_since_contribution(self, timestamp_str: str) -> float:
        """Calculate days since a timestamp."""
        try:
            contributed_at = datetime.fromisoformat(timestamp_str)
            delta = datetime.now(timezone.utc) - contributed_at
            return max(1.0, delta.total_seconds() / 86400)  # At least 1 day
        except (ValueError, TypeError):
            return 1.0

    def _save_knowledge(self) -> None:
        """Save shared knowledge to disk."""
        knowledge_file = self.storage_path / "knowledge.json"

        # Convert attributions sets to lists for JSON serialization
        attributions_serializable = {
            k: list(v) for k, v in self.attributions.items()
        }

        data = {
            "concepts": self.concepts,
            "attributions": attributions_serializable,
        }

        knowledge_file.write_text(json.dumps(data, indent=2))

    def _load_knowledge(self) -> None:
        """Load shared knowledge from disk if it exists."""
        knowledge_file = self.storage_path / "knowledge.json"

        if not knowledge_file.exists():
            return

        try:
            data = json.loads(knowledge_file.read_text())
            self.concepts = data.get("concepts", {})

            # Convert attribution lists back to sets
            attributions_data = data.get("attributions", {})
            self.attributions = {
                k: set(v) for k, v in attributions_data.items()
            }
        except (json.JSONDecodeError, KeyError):
            # If data is corrupted, start fresh
            self.concepts = {}
            self.attributions = {}

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
