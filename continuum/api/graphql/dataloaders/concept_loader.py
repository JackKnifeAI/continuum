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
DataLoaders for Concept entities.
"""

from typing import List, Optional
from strawberry.dataloader import DataLoader
import aiosqlite


class ConceptLoader(DataLoader):
    """Batch load concepts by ID"""

    def __init__(self, db_path: str):
        super().__init__(load_fn=self.batch_load_fn)
        self.db_path = db_path

    async def batch_load_fn(self, keys: List[str]) -> List[Optional[dict]]:
        """Batch load concepts by IDs"""
        from ..types import Concept
        from datetime import datetime

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            placeholders = ",".join("?" * len(keys))
            query = f"""
                SELECT
                    id, name, description, confidence, concept_type,
                    created_at, updated_at, tenant_id, metadata
                FROM concepts
                WHERE id IN ({placeholders})
            """

            cursor = await conn.execute(query, keys)
            rows = await cursor.fetchall()

            concept_dict = {}
            for row in rows:
                concept_dict[row["id"]] = Concept(
                    id=str(row["id"]),
                    name=row["name"],
                    description=row["description"],
                    confidence=row["confidence"],
                    concept_type=row["concept_type"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    tenant_id=row["tenant_id"],
                    metadata=row["metadata"],
                )

            return [concept_dict.get(key) for key in keys]


class MemoriesByConceptLoader(DataLoader):
    """Batch load memories for concepts"""

    def __init__(self, db_path: str):
        super().__init__(load_fn=self.batch_load_fn)
        self.db_path = db_path

    async def batch_load_fn(self, concept_ids: List[str]) -> List[List[dict]]:
        """Batch load memories for multiple concepts"""
        from ..types import Memory, MemoryType
        from datetime import datetime

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            placeholders = ",".join("?" * len(concept_ids))
            query = f"""
                SELECT
                    mc.concept_id,
                    m.id, m.content, m.memory_type, m.importance, m.embedding,
                    m.access_count, m.created_at, m.updated_at, m.last_accessed_at,
                    m.tenant_id, m.metadata
                FROM memory_concepts mc
                JOIN memories m ON mc.memory_id = m.id
                WHERE mc.concept_id IN ({placeholders})
                ORDER BY mc.concept_id, m.created_at DESC
            """

            cursor = await conn.execute(query, concept_ids)
            rows = await cursor.fetchall()

            memories_by_concept = {cid: [] for cid in concept_ids}
            for row in rows:
                memory = Memory(
                    id=str(row["id"]),
                    content=row["content"],
                    memory_type=MemoryType(row["memory_type"]),
                    importance=row["importance"],
                    embedding=row["embedding"],
                    access_count=row["access_count"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    last_accessed_at=(
                        datetime.fromisoformat(row["last_accessed_at"])
                        if row["last_accessed_at"]
                        else None
                    ),
                    tenant_id=row["tenant_id"],
                    metadata=row["metadata"],
                )
                memories_by_concept[row["concept_id"]].append(memory)

            return [memories_by_concept.get(cid, []) for cid in concept_ids]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
