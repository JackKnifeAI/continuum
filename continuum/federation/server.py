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
Federation Server - FastAPI endpoints for federation operations.

Provides HTTP API for:
- Node registration
- Concept contribution
- Knowledge requests
- Status checks

Enforces contribution gates and rate limits.
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from datetime import datetime
import math

from continuum.federation.node import FederatedNode
from continuum.federation.contribution import ContributionGate
from continuum.federation.shared import SharedKnowledge
from continuum.federation.protocol import FederationProtocol, MessageType


# Pydantic models for request/response validation

class RegisterRequest(BaseModel):
    """Node registration request."""
    node_id: Optional[str] = None
    verify_constant: Optional[float] = Field(
        None,
        description="Hidden: π × φ for enhanced access"
    )


class RegisterResponse(BaseModel):
    """Node registration response."""
    status: str
    node_id: str
    access_level: str
    registered_at: Optional[str] = None
    verified: Optional[bool] = None
    message: Optional[str] = None


class ContributeRequest(BaseModel):
    """Concept contribution request."""
    concepts: List[Dict[str, Any]] = Field(
        ...,
        description="List of anonymized concepts to contribute"
    )


class ContributeResponse(BaseModel):
    """Concept contribution response."""
    status: str
    new_concepts: int
    duplicate_concepts: int
    total_submitted: int
    contribution_value: float
    contribution_score: float
    access_level: str


class KnowledgeRequest(BaseModel):
    """Knowledge request parameters."""
    query: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    min_quality: float = Field(0.0, ge=0.0)


class KnowledgeResponse(BaseModel):
    """Knowledge response."""
    status: str
    concepts: List[Dict[str, Any]]
    count: int
    consumption_recorded: bool


class StatusResponse(BaseModel):
    """Node status response."""
    node_id: str
    registered: bool
    contribution_score: float
    consumption_score: float
    contribution_ratio: float
    access_level: str
    tier: str
    allowed: bool


# Initialize FastAPI app
app = FastAPI(
    title="CONTINUUM Federation API",
    description="Federated knowledge sharing: Can't use it unless you add to it",
    version="0.1.0",
)


# Dependency injection for node authentication
def get_node_id(x_node_id: Optional[str] = Header(None)) -> str:
    """Extract and validate node ID from request headers."""
    if not x_node_id:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Node-ID header"
        )
    return x_node_id


# Global instances (in production, these would be properly initialized)
_contribution_gate: Optional[ContributionGate] = None
_shared_knowledge: Optional[SharedKnowledge] = None
_protocol: Optional[FederationProtocol] = None


def get_contribution_gate() -> ContributionGate:
    """Get or create ContributionGate instance."""
    global _contribution_gate
    if _contribution_gate is None:
        _contribution_gate = ContributionGate()
    return _contribution_gate


def get_shared_knowledge() -> SharedKnowledge:
    """Get or create SharedKnowledge instance."""
    global _shared_knowledge
    if _shared_knowledge is None:
        _shared_knowledge = SharedKnowledge()
    return _shared_knowledge


def get_protocol(node_id: str) -> FederationProtocol:
    """Get or create FederationProtocol instance."""
    global _protocol
    if _protocol is None:
        _protocol = FederationProtocol(node_id=node_id)
    return _protocol


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "service": "CONTINUUM Federation",
        "tagline": "Can't use it unless you add to it",
        "version": "0.1.0",
        "endpoints": {
            "register": "/federation/register",
            "contribute": "/federation/contribute",
            "knowledge": "/federation/knowledge",
            "status": "/federation/status",
        }
    }


@app.post("/federation/register", response_model=RegisterResponse)
def register_node(request: RegisterRequest) -> RegisterResponse:
    """
    Register a new node in the federation.

    Returns node_id and initial access_level.
    Hidden feature: Pass π × φ as verify_constant for enhanced access.
    """
    # Create node with optional verification
    node = FederatedNode(
        node_id=request.node_id,
        verify_constant=request.verify_constant
    )

    # Register the node
    result = node.register()

    return RegisterResponse(**result)


@app.post("/federation/contribute", response_model=ContributeResponse)
def contribute_concepts(
    request: ContributeRequest,
    node_id: str = Depends(get_node_id)
) -> ContributeResponse:
    """
    Contribute anonymized concepts to the federation.

    Each new concept increases your contribution_score,
    improving your access to shared knowledge.
    """
    # Get dependencies
    gate = get_contribution_gate()
    knowledge = get_shared_knowledge()
    protocol = get_protocol(node_id)

    # Check rate limit
    rate_check = protocol.check_rate_limit(MessageType.CONTRIBUTE)
    if not rate_check["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Reset at {rate_check['reset_at']}"
        )

    # Validate payload
    validation = protocol.validate_payload(
        MessageType.CONTRIBUTE,
        {"concepts": request.concepts}
    )
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload: {validation.get('reason', 'unknown')}"
        )

    # Record rate limit
    protocol.record_message(MessageType.CONTRIBUTE)

    # Contribute to shared knowledge
    result = knowledge.contribute_concepts(node_id, request.concepts)

    # Record contribution
    gate.record_contribution(
        node_id,
        contribution_value=result["contribution_value"]
    )

    # Get updated stats
    stats = gate.get_stats(node_id)

    return ContributeResponse(
        status=result["status"],
        new_concepts=result["new_concepts"],
        duplicate_concepts=result["duplicate_concepts"],
        total_submitted=result["total_submitted"],
        contribution_value=result["contribution_value"],
        contribution_score=stats["contributed"],
        access_level=stats["tier"],
    )


@app.post("/federation/knowledge", response_model=KnowledgeResponse)
def get_knowledge(
    request: KnowledgeRequest,
    node_id: str = Depends(get_node_id)
) -> KnowledgeResponse:
    """
    Request knowledge from the federation.

    Access is gated by contribution ratio:
    - Must contribute at least 10% of what you consume
    - First 10 requests are free (grace period)
    - Verified nodes (π × φ) have unlimited access
    """
    # Get dependencies
    gate = get_contribution_gate()
    knowledge = get_shared_knowledge()
    protocol = get_protocol(node_id)

    # Check rate limit
    rate_check = protocol.check_rate_limit(MessageType.REQUEST)
    if not rate_check["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Reset at {rate_check['reset_at']}"
        )

    # Get node stats to determine access level
    stats = gate.get_stats(node_id)

    # Check if node can access knowledge
    access_check = gate.can_access(node_id, access_level=stats["tier"])

    if not access_check["allowed"]:
        # Access denied - insufficient contribution
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_contribution",
                "message": "Can't use it unless you add to it",
                "contribution_ratio": access_check["ratio"],
                "minimum_required": access_check["minimum_required"],
                "deficit": access_check["deficit"],
                "hint": "Contribute more concepts to increase your access"
            }
        )

    # Record rate limit
    protocol.record_message(MessageType.REQUEST)

    # Record consumption
    gate.record_consumption(node_id, consumption_value=1.0)

    # Get knowledge
    concepts = knowledge.get_shared_concepts(
        query=request.query,
        limit=request.limit,
        min_quality=request.min_quality
    )

    return KnowledgeResponse(
        status="success",
        concepts=concepts,
        count=len(concepts),
        consumption_recorded=True,
    )


@app.get("/federation/status", response_model=StatusResponse)
def get_status(node_id: str = Depends(get_node_id)) -> StatusResponse:
    """
    Get current contribution status for this node.

    Shows:
    - Contribution and consumption scores
    - Contribution ratio
    - Access tier
    - Whether you can currently access knowledge
    """
    gate = get_contribution_gate()

    # Get stats
    stats = gate.get_stats(node_id)

    # Check access
    access_check = gate.can_access(node_id, access_level=stats["tier"])

    return StatusResponse(
        node_id=node_id,
        registered=True,  # If they're calling this, they're registered
        contribution_score=stats["contributed"],
        consumption_score=stats["consumed"],
        contribution_ratio=stats["ratio"],
        access_level=stats["tier"],
        tier=stats["tier"],
        allowed=access_check["allowed"],
    )


@app.get("/federation/stats")
def get_federation_stats():
    """
    Get overall federation statistics.

    Shows aggregate stats about the knowledge pool.
    """
    knowledge = get_shared_knowledge()
    stats = knowledge.get_stats()

    return {
        "status": "ok",
        "federation": stats,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "continuum-federation",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
