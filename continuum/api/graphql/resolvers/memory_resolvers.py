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
Resolvers for Memory type fields.
"""

from typing import List, Optional
from strawberry.types import Info


async def resolve_memory_concepts(memory, info: Info, limit: int) -> List:
    """Resolve concepts for a memory using DataLoader"""
    loader = info.context["loaders"]["concepts_by_memory"]
    all_concepts = await loader.load(memory.id)
    return all_concepts[:limit]


async def resolve_related_memories(
    memory, info: Info, limit: int, threshold: float
) -> List:
    """Resolve semantically related memories"""
    from continuum.core.memory import ConsciousMemory

    # Get memory instance from context
    memory_instance = info.context.get("memory")
    if not memory_instance:
        return []

    # Use similarity search (this would need embedding comparison)
    # For now, return empty - full implementation would use vector search
    return []


async def resolve_memory_session(memory, info: Info) -> Optional:
    """Resolve session for a memory"""
    # Check if memory has session_id in metadata
    if not memory.metadata or "session_id" not in memory.metadata:
        return None

    session_id = memory.metadata["session_id"]
    loader = info.context["loaders"]["session"]
    return await loader.load(session_id)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
