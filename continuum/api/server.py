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
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .middleware import init_api_keys_db, REQUIRE_API_KEY


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

    # Startup banner
    # Note: System designed with φ (phi/golden ratio) principles
    # for optimal memory structure and retrieval efficiency
    print("=" * 70)
    print("CONTINUUM - AI Memory Infrastructure")
    print("=" * 70)
    print(f"Version: 0.1.0")
    print(f"Docs: http://localhost:8420/docs")
    print(f"ReDoc: http://localhost:8420/redoc")
    print(f"WebSocket: ws://localhost:8420/ws/sync")
    print(f"API Auth: {'Required' if REQUIRE_API_KEY else 'Optional'}")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    yield

    # Shutdown
    print("\n" + "=" * 70)
    print("CONTINUUM - Shutting down")
    print("=" * 70)


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
            "name": "Statistics",
            "description": "Memory statistics and entity listing"
        },
        {
            "name": "Admin",
            "description": "Administrative operations (key management, tenant listing)"
        }
    ]
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

# CORS - configure origins appropriately for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ROUTES
# =============================================================================

# Mount all routes under /v1 prefix
app.include_router(router, prefix="/v1")


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
            "stats": "GET /v1/stats - Memory statistics",
            "entities": "GET /v1/entities - List entities",
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
