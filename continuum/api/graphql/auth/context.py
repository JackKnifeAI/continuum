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
    ConceptLoader,
    ConceptsByMemoryLoader,
    MemoriesByConceptLoader,
    MemoryLoader,
    SessionLoader,
    UserLoader,
)


class GraphQLContext(BaseContext):
    """Custom GraphQL context with authentication and DataLoaders"""

    def __init__(
        self,
        request: Request,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_admin: bool = False,
        db_path: str = None,
    ):
        super().__init__()
        self.request = request
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.is_admin = is_admin
        self.db_path = db_path

        # Initialize DataLoaders
        if db_path:
            self.loaders = {
                "memory": MemoryLoader(db_path),
                "concepts_by_memory": ConceptsByMemoryLoader(db_path),
                "concept": ConceptLoader(db_path),
                "memories_by_concept": MemoriesByConceptLoader(db_path),
                "user": UserLoader(db_path),
                "session": SessionLoader(db_path),
            }
        else:
             self.loaders = {}


async def get_context(request: Request) -> GraphQLContext:
    """
    Build GraphQL context from FastAPI request.

    Extracts authentication from X-API-Key header and builds context
    with user info and DataLoaders.
    """
    import os

    from continuum.api.middleware import validate_api_key
    from continuum.core.config import get_config

    config = get_config()

    # Extract API key from header
    api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    admin_token_header = request.headers.get("x-admin-token") or request.headers.get("X-Admin-Token")

    user_id = None
    tenant_id = None
    is_admin = False

    if api_key:
        try:
            # Verify API key and get tenant
            # validate_api_key returns tenant_id or None
            tenant_id = validate_api_key(api_key)
            if tenant_id:
                user_id = tenant_id
        except Exception:
            # Invalid API key - context will have no auth
            pass

    # Admin Check
    env_admin_token = os.getenv("CONTINUUM_ADMIN_TOKEN")
    if env_admin_token and admin_token_header == env_admin_token:
        is_admin = True

    # Get database path from config dataclass
    db_path = str(config.db_path)

    return GraphQLContext(
        request=request,
        user_id=user_id,
        tenant_id=tenant_id,
        is_admin=is_admin,
        db_path=db_path,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
