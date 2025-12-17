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
Resolvers for Concept type fields.
"""

from typing import List, Optional
from strawberry.types import Info
import aiosqlite


async def resolve_concept_memories(concept, info: Info, pagination) -> dict:
    """Resolve memories for a concept with pagination"""
    from ..types import MemoryConnection, MemoryEdge, PageInfo

    loader = info.context["loaders"]["memories_by_concept"]
    all_memories = await loader.load(concept.id)

    # Simple pagination
    first = pagination.first if pagination else 20
    memories = all_memories[:first]

    edges = [
        MemoryEdge(
            cursor=str(i),
            node=memory,
            score=None
        )
        for i, memory in enumerate(memories)
    ]

    return MemoryConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(all_memories) > first,
            has_previous_page=False,
            start_cursor="0" if edges else None,
            end_cursor=str(len(edges) - 1) if edges else None,
        ),
        total_count=len(all_memories),
    )


async def resolve_related_concepts(
    concept, info: Info, depth: int, relationship
) -> List:
    """Resolve related concepts by traversing graph"""
    from ..types import ConceptEdge, ConceptRelationship
    from datetime import datetime

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        # Query concept relationships
        query = """
            SELECT
                source_id, target_id, relationship, label, strength, metadata, created_at
            FROM concept_relationships
            WHERE source_id = ?
        """
        params = [concept.id]

        if relationship:
            query += " AND relationship = ?"
            params.append(relationship.value)

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        # Load related concepts using DataLoader
        concept_loader = info.context["loaders"]["concept"]
        target_ids = [row["target_id"] for row in rows]
        target_concepts = await concept_loader.load_many(target_ids)

        # Build edges
        edges = []
        for row, target_concept in zip(rows, target_concepts):
            if target_concept:
                edges.append(
                    ConceptEdge(
                        from_concept=concept,
                        to_concept=target_concept,
                        relationship=ConceptRelationship(row["relationship"]),
                        label=row["label"],
                        strength=row["strength"],
                        metadata=row["metadata"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )

        return edges

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
