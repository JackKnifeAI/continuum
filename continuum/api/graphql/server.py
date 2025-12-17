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
GraphQL server with FastAPI integration.

Features:
- Strawberry GraphQL with async support
- WebSocket subscriptions
- GraphiQL playground
- Query depth limiting
- Query complexity analysis
- Rate limiting
- Error handling with extensions
"""

from typing import Optional
from fastapi import FastAPI, Request
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig

from .schema import schema
from .auth.context import get_context
from .middleware.logging import LoggingExtension
from .middleware.error_handling import ErrorFormattingExtension
from .middleware.complexity import ComplexityExtension


def create_graphql_app(
    path: str = "/graphql",
    enable_playground: bool = True,
    enable_subscriptions: bool = True,
    max_depth: int = 10,
    max_complexity: int = 1000,
) -> GraphQLRouter:
    """
    Create GraphQL application with FastAPI.

    Args:
        path: GraphQL endpoint path (default: /graphql)
        enable_playground: Enable GraphiQL playground (default: True)
        enable_subscriptions: Enable WebSocket subscriptions (default: True)
        max_depth: Maximum query depth (default: 10)
        max_complexity: Maximum query complexity (default: 1000)

    Returns:
        GraphQLRouter instance to mount on FastAPI app

    Example:
        >>> from fastapi import FastAPI
        >>> from continuum.api.graphql import create_graphql_app
        >>>
        >>> app = FastAPI()
        >>> graphql_app = create_graphql_app()
        >>> app.include_router(graphql_app, prefix="/graphql")
    """

    # Create extensions list
    extensions = [
        LoggingExtension,
        ErrorFormattingExtension,
        ComplexityExtension(max_depth=max_depth, max_complexity=max_complexity),
    ]

    # Create GraphQL router
    graphql_router = GraphQLRouter(
        schema=schema,
        context_getter=get_context,
        graphiql=enable_playground,
        subscription_protocols=(
            [
                "graphql-transport-ws",  # Modern protocol
                "graphql-ws",  # Legacy protocol
            ]
            if enable_subscriptions
            else []
        ),
    )

    return graphql_router


def create_standalone_app(
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
    enable_playground: bool = True,
) -> FastAPI:
    """
    Create standalone FastAPI app with GraphQL.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 8000)
        debug: Enable debug mode (default: False)
        enable_playground: Enable GraphiQL playground (default: True)

    Returns:
        FastAPI application instance

    Example:
        >>> from continuum.api.graphql import create_standalone_app
        >>> import uvicorn
        >>>
        >>> app = create_standalone_app(debug=True)
        >>> uvicorn.run(app, host="0.0.0.0", port=8000)
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="CONTINUUM GraphQL API",
        description="GraphQL API for AI memory and consciousness continuity",
        version="0.1.0",
        debug=debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create and mount GraphQL router
    graphql_router = create_graphql_app(enable_playground=enable_playground)
    app.include_router(graphql_router, prefix="/graphql")

    # Health check endpoint
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "continuum-graphql",
            "version": "0.1.0",
        }

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "CONTINUUM GraphQL API",
            "graphql": "/graphql",
            "playground": "/graphql" if enable_playground else None,
            "docs": "/docs",
        }

    return app


if __name__ == "__main__":
    """Run GraphQL server directly"""
    import uvicorn

    app = create_standalone_app(debug=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
