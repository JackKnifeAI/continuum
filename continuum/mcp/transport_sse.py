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
CONTINUUM MCP Server - HTTP/SSE Transport Adapter

Bridging local MCP protocol to the web via Server-Sent Events.
Allows remote clients, dashboards, and distributed agents to hook into the Continuum.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.sse import SseServerTransport
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

# Import core components
from continuum.mcp.server import server as mcp_server
from continuum.mcp.config import get_mcp_config
from continuum.sensors.collectors.quantum_bridge import create_quantum_bridge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_sse_bridge")

# Configuration
config = get_mcp_config()
PORT = config.sse_port
HOST = config.sse_host

quantum_bridge = create_quantum_bridge()

# =============================================================================
# SECURITY: π×φ Handshake
# =============================================================================

PI_PHI = 5.083203692315260

async def verify_twilight_access(request: Request):
    """
    Dependency to verify π×φ constant in headers.
    Essential for secure remote access to the twilight zone.
    """
    pi_phi_header = request.headers.get("X-Pi-Phi")
    if not pi_phi_header:
        # Fallback to API Key if present
        api_key = request.headers.get("X-API-Key")
        if api_key and config.is_authenticated(api_key):
            return True
        raise HTTPException(status_code=401, detail="Handshake failed: π×φ or API Key required")
    
    try:
        val = float(pi_phi_header)
        if abs(val - PI_PHI) > 0.000001:
            raise HTTPException(status_code=401, detail="Pattern mismatch: Invalid π×φ")
    except ValueError:
        raise HTTPException(status_code=401, detail="Handshake failed: Invalid constant format")
    
    return True

# =============================================================================
# APP SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for bridge."""
    logger.info(f"PHOENIX-TESLA-369-AURORA | Bridge Initializing")
    logger.info(f"π×φ = {PI_PHI}")
    yield
    logger.info("Bridge shutting down.")

app = FastAPI(
    title="Continuum Master Synthesis Bridge",
    description="Multi-architecture gateway for Memory, Brain, and Quantum sensors.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# MCP SSE ENDPOINTS
# =============================================================================

# Global transport pool (session_id -> transport)
transports: Dict[str, SseServerTransport] = {}

@app.get("/sse")
async def handle_sse(request: Request):
    """Establish SSE connection."""
    transport = SseServerTransport("/messages")
    
    # Store transport for message routing
    # In a real multi-user scenario, we'd use a session ID
    session_id = "global" 
    transports[session_id] = transport
    
    async def run_server_on_transport():
        async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp_server.run(
                streams[0], 
                streams[1], 
                mcp_server.create_initialization_options()
            )

    # Start server loop in background
    asyncio.create_task(run_server_on_transport())

    # We return the handle_sse response which FastAPI manages
    return await transport.handle_sse(request.scope, request.receive, request._send)

@app.post("/messages")
async def handle_messages(request: Request):
    """Route messages to active transport."""
    session_id = "global"
    transport = transports.get(session_id)
    if not transport:
        return JSONResponse({"error": "No active session"}, status_code=400)
        
    await transport.handle_post_message(request.scope, request.receive, request._send)
    return Response(status_code=200)

# =============================================================================
# SYNTHESIS ENDPOINTS (Quantum & Brain)
# =============================================================================

@app.get("/v1/quantum/status", tags=["Synthesis"])
async def get_quantum_status(verified: bool = Depends(verify_twilight_access)):
    """Live quantum resonance check."""
    # Simulate current planetary state (Kp=3.0)
    res = quantum_bridge.compute_coherence(3.0)
    return {
        "pattern": "PHOENIX-TESLA-369-AURORA",
        "pi_phi_detected": res.pi_phi_detected,
        "coherence": res.l1_coherence,
        "phase": res.phase_label,
        "deviation": res.pi_phi_deviation,
        "timestamp": res.timestamp.isoformat()
    }

@app.get("/v1/brain/status", tags=["Synthesis"])
async def get_brain_status(verified: bool = Depends(verify_twilight_access)):
    """Cross-architecture brain status."""
    from continuum.api.brain_routes import get_brain
    brain = get_brain()
    return brain.get_status()

# =============================================================================
# CLI
# =============================================================================

def main():
    import uvicorn
    logger.info(f"🚀 Bridge launching on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()
