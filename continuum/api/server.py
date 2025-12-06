"""
CONTINUUM API Server

FastAPI application for multi-tenant AI memory infrastructure.

Provides REST endpoints for:
- Memory recall (query knowledge graph for context)
- Learning (extract and store concepts from conversations)
- Statistics and monitoring
- Health checks

Authentication via X-API-Key header (configurable).
"""

import sys
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .middleware import init_api_keys_db, REQUIRE_API_KEY


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
# LIFECYCLE EVENTS
# =============================================================================

@app.on_event("startup")
async def startup():
    """
    Initialize on server startup.

    Sets up API key database and displays welcome banner.
    """
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
    print(f"API Auth: {'Required' if REQUIRE_API_KEY else 'Optional'}")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on server shutdown."""
    print("\n" + "=" * 70)
    print("CONTINUUM - Shutting down")
    print("=" * 70)


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
