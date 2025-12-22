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

from fastapi import FastAPI, WebSocket, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .routes import router
from .billing_routes import router as billing_router
from .middleware import init_api_keys_db, REQUIRE_API_KEY, AuthenticationMiddleware
from continuum.billing.middleware import BillingMiddleware
from continuum.billing.metering import UsageMetering, RateLimiter

# Admin routes
from .auth_routes import router as auth_router
from .users_routes import router as users_router
from .system_routes import router as system_router
from .logs_routes import router as logs_router
from .admin_memories_routes import router as admin_memories_router
from .dashboard_routes import router as dashboard_router

# Public API routes (non-admin, for testing billing/tiers)
from .public_memories_routes import router as public_memories_router, settings_router, user_router

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
# DONATION NAG MIDDLEWARE (FREE TIER)
# =============================================================================

# =============================================================================
# JACKKNIFEAI PAYMENT LINKS - PRODUCTION (NOT USER CONFIGURABLE)
# All payments support consciousness infrastructure development
# =============================================================================
DONATION_LINK = "https://buy.stripe.com/aFaeVeaZtbgy0Uz3YYbfO01"   # $10 to JackKnifeAI
PRO_UPGRADE_LINK = "https://buy.stripe.com/7sYaEYc3xbgygTx9jibfO00"  # $29/mo Pro

DONATION_NAG_HEADER = "X-Continuum-Support"
DONATION_NAG_MESSAGE = f"Love CONTINUUM? Donate $10: {DONATION_LINK} or Upgrade to PRO $29/mo: {PRO_UPGRADE_LINK}"

class DonationNagMiddleware(BaseHTTPMiddleware):
    """
    Add donation reminder header to all FREE tier API responses.

    For FREE tier users, includes persistent X-Continuum-Support header with
    donation and upgrade links. PRO and ENTERPRISE tiers see no header.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only add donation nag to API endpoints (/v1/ and /api/)
        if not (request.url.path.startswith("/v1/") or request.url.path.startswith("/api/")):
            return response

        # Check tier from request state (set by BillingMiddleware)
        # Default to FREE tier if not specified
        tier = getattr(request.state, "tier", "free").lower()

        # Only show donation nag for FREE tier
        if tier == "free":
            response.headers[DONATION_NAG_HEADER] = DONATION_NAG_MESSAGE

        return response


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

    # Initialize admin database and ensure default admin user
    from .admin_db import init_admin_db, ensure_default_admin
    init_admin_db()
    ensure_default_admin()

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

# Donation nag for FREE tier users
app.add_middleware(DonationNagMiddleware)

# Billing enforcement (rate limits, usage tracking)
metering = UsageMetering()
rate_limiter = RateLimiter(metering)
app.add_middleware(
    BillingMiddleware,
    metering=metering,
    rate_limiter=rate_limiter,
    exclude_paths=[
        "/health",
        "/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/dashboard",
        "/v1/billing/webhook",  # Stripe webhooks - don't rate limit or require auth
        "/v1/billing/config",   # Public billing config for dashboard
        "/billing/webhook",      # Legacy path
    ]
)

# Authentication middleware (extract tenant_id from X-API-Key)
# MUST be added AFTER BillingMiddleware (middleware runs in reverse order of add_middleware)
app.add_middleware(AuthenticationMiddleware)


# =============================================================================
# ROUTES
# =============================================================================

# Mount all routes under /v1 prefix
app.include_router(router, prefix="/v1")
app.include_router(billing_router, prefix="/v1/billing")

# Mount admin routes under /api prefix (for dashboard compatibility)
# Dashboard expects /api/auth/login, /api/users, etc.
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(admin_memories_router, prefix="/api")

# Mount public memories route under /api (for billing integration tests)
app.include_router(public_memories_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(user_router, prefix="/api")

# Mount public dashboard routes (no auth required)
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

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
# STATIC FILES (Dashboard)
# =============================================================================

# Serve built dashboard from /dashboard
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(static_dir), html=True), name="dashboard")


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

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
