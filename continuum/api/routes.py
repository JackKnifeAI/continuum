"""
API route handlers for CONTINUUM memory operations.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from .schemas import (
    RecallRequest,
    RecallResponse,
    LearnRequest,
    LearnResponse,
    TurnRequest,
    TurnResponse,
    StatsResponse,
    EntitiesResponse,
    EntityItem,
    HealthResponse,
    CreateKeyRequest,
    CreateKeyResponse,
)
from .middleware import get_tenant_from_key, optional_tenant_from_key
from continuum.core.memory import TenantManager


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter()

# Global tenant manager instance
tenant_manager = TenantManager()


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns service status and version information.
    No authentication required.
    """
    return HealthResponse(
        status="healthy",
        service="continuum",
        version="0.1.0",
        timestamp=datetime.now().isoformat()
    )


# =============================================================================
# MEMORY ENDPOINTS
# =============================================================================

@router.post("/recall", response_model=RecallResponse, tags=["Memory"])
async def recall(
    request: RecallRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Query memory for relevant context.

    Call this BEFORE generating an AI response to retrieve relevant
    context from the knowledge graph.

    **Flow:**
    1. User sends message
    2. Call /recall with message
    3. Inject returned context into AI prompt
    4. Generate AI response
    5. Call /learn to save the exchange

    **Returns:**
    - Formatted context string for prompt injection
    - Statistics about retrieved concepts and relationships
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = memory.recall(request.message, request.max_concepts)

        return RecallResponse(
            context=result.context_string,
            concepts_found=result.concepts_found,
            relationships_found=result.relationships_found,
            query_time_ms=result.query_time_ms,
            tenant_id=result.tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recall failed: {str(e)}")


@router.post("/learn", response_model=LearnResponse, tags=["Memory"])
async def learn(
    request: LearnRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Learn from a message exchange.

    Call this AFTER generating an AI response to extract concepts,
    detect decisions, and build knowledge graph links.

    **Flow:**
    1. User message received
    2. AI response generated
    3. Call /learn with both messages
    4. System extracts and stores knowledge

    **Extracts:**
    - Concepts and entities mentioned
    - Decisions and commitments made
    - Relationships between concepts
    - Compound concepts (multi-word phrases)
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = memory.learn(
            request.user_message,
            request.ai_response,
            request.metadata
        )

        return LearnResponse(
            concepts_extracted=result.concepts_extracted,
            decisions_detected=result.decisions_detected,
            links_created=result.links_created,
            compounds_found=result.compounds_found,
            tenant_id=result.tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Learning failed: {str(e)}")


@router.post("/turn", response_model=TurnResponse, tags=["Memory"])
async def process_turn(
    request: TurnRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Process a complete conversation turn (recall + learn).

    Combines recall and learn in a single API call for simplified
    integration. Useful for batch processing or async workflows.

    **Use when:**
    - Processing conversation history in batch
    - Implementing async memory updates
    - Simplifying client integration

    **Not recommended when:**
    - Need to inject context before AI response (use /recall then /learn)
    - Need fine-grained control over memory operations
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)

        # Recall context
        recall_result = memory.recall(request.user_message, request.max_concepts)

        # Learn from exchange
        learn_result = memory.learn(
            request.user_message,
            request.ai_response,
            request.metadata
        )

        return TurnResponse(
            recall=RecallResponse(
                context=recall_result.context_string,
                concepts_found=recall_result.concepts_found,
                relationships_found=recall_result.relationships_found,
                query_time_ms=recall_result.query_time_ms,
                tenant_id=recall_result.tenant_id
            ),
            learn=LearnResponse(
                concepts_extracted=learn_result.concepts_extracted,
                decisions_detected=learn_result.decisions_detected,
                links_created=learn_result.links_created,
                compounds_found=learn_result.compounds_found,
                tenant_id=learn_result.tenant_id
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Turn processing failed: {str(e)}")


# =============================================================================
# STATISTICS & INFORMATION ENDPOINTS
# =============================================================================

@router.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats(tenant_id: str = Depends(get_tenant_from_key)):
    """
    Get memory statistics for the tenant.

    Returns counts of entities, messages, decisions, and graph links.
    Useful for monitoring memory growth and system health.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        stats = memory.get_stats()

        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/entities", response_model=EntitiesResponse, tags=["Statistics"])
async def get_entities(
    limit: int = 100,
    offset: int = 0,
    entity_type: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    List entities/concepts in the knowledge graph.

    **Parameters:**
    - limit: Maximum entities to return (default 100)
    - offset: Pagination offset (default 0)
    - entity_type: Filter by type (optional)

    **Returns:**
    List of entities with names, types, and descriptions.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)

        # Get entities from memory system
        # TODO: Implement get_entities method in ConsciousMemory
        # For now, return empty list
        entities = []
        total = 0

        return EntitiesResponse(
            entities=[
                EntityItem(
                    name=e.get("name", ""),
                    type=e.get("type", "concept"),
                    description=e.get("description"),
                    created_at=e.get("created_at")
                )
                for e in entities
            ],
            total=total,
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity listing failed: {str(e)}")


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.get("/tenants", tags=["Admin"])
async def list_tenants():
    """
    List all registered tenants.

    **Admin endpoint** - in production, should require admin authentication.
    Returns list of tenant IDs currently in the system.
    """
    return {"tenants": tenant_manager.list_tenants()}


@router.post("/keys", response_model=CreateKeyResponse, tags=["Admin"])
async def create_key(request: CreateKeyRequest):
    """
    Create a new API key for a tenant.

    **Admin endpoint** - in production, should require admin authentication.

    **Important:**
    - Store the returned API key securely
    - It will not be shown again
    - Keys are hashed in the database

    **Usage:**
    Include the key in all API requests via X-API-Key header.
    """
    from .middleware import init_api_keys_db, hash_key, get_api_keys_db_path
    import secrets
    import sqlite3

    try:
        init_api_keys_db()

        # Generate API key with continuum prefix
        api_key = f"cm_{secrets.token_urlsafe(32)}"
        key_hash = hash_key(api_key)

        # Store in database
        db_path = get_api_keys_db_path()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO api_keys (key_hash, tenant_id, created_at, name)
            VALUES (?, ?, ?, ?)
            """,
            (key_hash, request.tenant_id, datetime.now().isoformat(), request.name)
        )
        conn.commit()
        conn.close()

        return CreateKeyResponse(
            api_key=api_key,
            tenant_id=request.tenant_id,
            message="Store this key securely - it won't be shown again"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key creation failed: {str(e)}")
