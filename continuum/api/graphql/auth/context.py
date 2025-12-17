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
GraphQL context builder for request handling.
"""

from typing import Optional
from fastapi import Request
from strawberry.fastapi import BaseContext

from ..dataloaders import (
    MemoryLoader,
    ConceptsByMemoryLoader,
    ConceptLoader,
    MemoriesByConceptLoader,
    UserLoader,
    SessionLoader,
)


class GraphQLContext(BaseContext):
    """Custom GraphQL context with authentication and DataLoaders"""

    def __init__(
        self,
        request: Request,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        db_path: str = None,
    ):
        super().__init__()
        self.request = request
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.db_path = db_path

        # Initialize DataLoaders
        self.loaders = {
            "memory": MemoryLoader(db_path),
            "concepts_by_memory": ConceptsByMemoryLoader(db_path),
            "concept": ConceptLoader(db_path),
            "memories_by_concept": MemoriesByConceptLoader(db_path),
            "user": UserLoader(db_path),
            "session": SessionLoader(db_path),
        }


async def get_context(request: Request) -> GraphQLContext:
    """
    Build GraphQL context from FastAPI request.

    Extracts authentication from X-API-Key header and builds context
    with user info and DataLoaders.
    """
    from continuum.api.middleware import verify_api_key
    from continuum.core.config import get_config

    config = get_config()

    # Extract API key from header
    api_key = request.headers.get("x-api-key")

    user_id = None
    tenant_id = None

    if api_key:
        try:
            # Verify API key and get tenant
            tenant_id = verify_api_key(api_key)

            # For now, use tenant_id as user_id
            # In production, would have proper user management
            user_id = tenant_id
        except Exception:
            # Invalid API key - context will have no auth
            pass

    # Get database path from config dataclass
    db_path = str(config.db_path)

    return GraphQLContext(
        request=request,
        user_id=user_id,
        tenant_id=tenant_id,
        db_path=db_path,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
