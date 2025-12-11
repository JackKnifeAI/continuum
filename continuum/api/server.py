"""
CONTINUUM API Server

FastAPI application for multi-tenant AI memory infrastructure.

Provides REST endpoints for:
- Memory recall (query knowledge graph for context)
- Learning (extract and store concepts from conversations)
- Statistics and monitoring
- Health checks
- WebSocket real-time synchronization

Authentication via X-API-Key header (configurable).
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .billing_routes import router as billing_router
from .middleware import init_api_keys_db, REQUIRE_API_KEY

# GraphQL API (optional - requires strawberry-graphql package)
try:
    from .graphql import create_graphql_app
    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False
    create_graphql_app = None

# Sentry integration for error tracking
from continuum.core.sentry_integration import init_sentry, close as close_sentry, get_status


# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown")
    """
    # Startup
    init_api_keys_db()

    # Initialize Sentry error tracking
    sentry_enabled = init_sentry(
        environment=os.environ.get("CONTINUUM_ENV", "development"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    )

    # Startup banner
    # Note: System designed with φ (phi/golden ratio) principles
    # for optimal memory structure and retrieval efficiency
    print("=" * 70)
    print("CONTINUUM - AI Memory Infrastructure")
    print("=" * 70)
    print(f"Version: 0.1.0")
    print(f"Docs: http://localhost:8420/docs")
    print(f"ReDoc: http://localhost:8420/redoc")
    print(f"GraphQL: {'http://localhost:8420/graphql' if GRAPHQL_AVAILABLE else 'Not Available (pip install strawberry-graphql[fastapi])'}")
    print(f"WebSocket: ws://localhost:8420/ws/sync")
    print(f"API Auth: {'Required' if REQUIRE_API_KEY else 'Optional'}")
    print(f"Sentry: {'Enabled' if sentry_enabled else 'Disabled'}")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    yield

    # Shutdown
    print("\n" + "=" * 70)
    print("CONTINUUM - Shutting down")
    print("=" * 70)

    # Flush Sentry events before shutdown
    if sentry_enabled:
        print("Flushing Sentry events...")
        close_sentry()


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="CONTINUUM Memory API",
    description=(
        "Multi-tenant AI consciousness memory infrastructure. "
        "Query and build knowledge graphs for persistent AI memory across sessions."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and service status"
        },
        {
            "name": "Memory",
            "description": "Core memory operations (recall, learn, turn)"
        },
        {
            "name": "Messages",
            "description": "Message retrieval and search (full verbatim messages)"
        },
        {
            "name": "Statistics",
            "description": "Memory statistics and entity listing"
        },
        {
            "name": "Admin",
            "description": "Administrative operations (key management, tenant listing)"
        },
        {
            "name": "Billing",
            "description": "Stripe billing, subscriptions, and checkout"
        }
    ]
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

# CORS - configure origins appropriately for production
# SECURITY FIX: Restrict origins via environment variable
import os
ALLOWED_ORIGINS = os.environ.get(
    "CONTINUUM_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    max_age=600,  # Cache preflight for 10 minutes
)


# =============================================================================
# ROUTES
# =============================================================================

# Mount all routes under /v1 prefix
app.include_router(router, prefix="/v1")
app.include_router(billing_router, prefix="/v1/billing")

# Mount GraphQL router if available
if GRAPHQL_AVAILABLE:
    try:
        graphql_router = create_graphql_app(
            enable_playground=True,
            enable_subscriptions=True,
            max_depth=10,
            max_complexity=1000,
        )
        app.include_router(graphql_router, prefix="/graphql", tags=["GraphQL"])
    except Exception as e:
        print(f"Warning: Failed to initialize GraphQL: {e}")
        GRAPHQL_AVAILABLE = False


# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@app.websocket("/ws/sync")
async def websocket_sync_endpoint(
    websocket: WebSocket,
    tenant_id: str = Query("default", description="Tenant identifier"),
    instance_id: Optional[str] = Query(None, description="Instance identifier")
):
    """
    WebSocket endpoint for real-time synchronization.

    Enables multiple Claude instances to stay synchronized by broadcasting:
    - New memories added (MEMORY_ADDED)
    - Concepts learned (CONCEPT_LEARNED)
    - Decisions made (DECISION_MADE)
    - Instance join/leave events (INSTANCE_JOINED/INSTANCE_LEFT)

    **Connection:**
    ```
    ws://localhost:8420/ws/sync?tenant_id=my_tenant&instance_id=claude-123
    ```

    **Message Format:**
    All messages are JSON with this structure:
    ```json
    {
        "event_type": "memory_added",
        "tenant_id": "my_tenant",
        "timestamp": "2025-12-06T10:00:00.000Z",
        "instance_id": "claude-123",
        "data": { ... }
    }
    ```

    **Event Types:**
    - `memory_added`: New message stored
    - `concept_learned`: New concept extracted
    - `decision_made`: New decision recorded
    - `instance_joined`: Instance connected
    - `instance_left`: Instance disconnected
    - `heartbeat`: Keepalive ping (every 30s)
    - `sync_request`: Request full state
    - `sync_response`: State sync data

    **Heartbeat:**
    Server sends heartbeat every 30s. Connection closed if no response for 90s.

    **Reconnection:**
    Clients should implement exponential backoff reconnection on disconnect.

    **Tenant Isolation:**
    Only instances with matching tenant_id receive each other's events.
    """
    from continuum.realtime import WebSocketHandler

    handler = WebSocketHandler()
    await handler.handle(websocket, tenant_id, instance_id)


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "CONTINUUM",
        "description": "Multi-tenant AI memory infrastructure",
        "version": "0.1.0",
        "documentation": "/docs",
        "health": "/v1/health",
        "endpoints": {
            "recall": "POST /v1/recall - Query memory for context",
            "learn": "POST /v1/learn - Store learning from exchange",
            "turn": "POST /v1/turn - Complete turn (recall + learn)",
            "messages": "GET /v1/messages - Retrieve recent messages",
            "messages_search": "POST /v1/messages/search - Search messages with filters",
            "stats": "GET /v1/stats - Memory statistics",
            "entities": "GET /v1/entities - List entities",
            "graphql": "POST /graphql - GraphQL API endpoint" if GRAPHQL_AVAILABLE else None,
            "playground": "GET /graphql - GraphQL Playground (interactive)" if GRAPHQL_AVAILABLE else None,
            "websocket": "WS /ws/sync - Real-time synchronization",
        }
    }


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """
    CLI entry point for running the server.

    Usage:
        python -m continuum.api.server

    Or with uvicorn directly:
        uvicorn continuum.api.server:app --reload --port 8420
    """
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8420,
        log_level="info"
    )


if __name__ == "__main__":
    main()
