"""
Pydantic schemas for API request/response validation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# =============================================================================
# RECALL SCHEMAS
# =============================================================================

class RecallRequest(BaseModel):
    """Request to query memory for relevant context."""

    message: str = Field(
        ...,
        description="Message to find context for",
        min_length=1,
        example="Tell me about the quantum mechanics discussion"
    )
    max_concepts: int = Field(
        10,
        description="Maximum number of concepts to return",
        ge=1,
        le=100
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What did we discuss about machine learning?",
                "max_concepts": 10
            }
        }


class RecallResponse(BaseModel):
    """Response containing memory context."""

    context: str = Field(
        ...,
        description="Formatted context string for injection into prompts"
    )
    concepts_found: int = Field(
        ...,
        description="Number of relevant concepts found"
    )
    relationships_found: int = Field(
        ...,
        description="Number of concept relationships found"
    )
    query_time_ms: float = Field(
        ...,
        description="Query execution time in milliseconds"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )


# =============================================================================
# LEARN SCHEMAS
# =============================================================================

class LearnRequest(BaseModel):
    """Request to learn from a message exchange."""

    user_message: str = Field(
        ...,
        description="User's message",
        min_length=1
    )
    ai_response: str = Field(
        ...,
        description="AI's response",
        min_length=1
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata about the exchange"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_message": "What is quantum entanglement?",
                "ai_response": "Quantum entanglement is a phenomenon where particles become correlated...",
                "metadata": {
                    "session_id": "abc123",
                    "timestamp": "2025-12-06T10:00:00Z"
                }
            }
        }


class LearnResponse(BaseModel):
    """Response after learning from an exchange."""

    concepts_extracted: int = Field(
        ...,
        description="Number of concepts extracted"
    )
    decisions_detected: int = Field(
        ...,
        description="Number of decisions detected"
    )
    links_created: int = Field(
        ...,
        description="Number of graph links created"
    )
    compounds_found: int = Field(
        ...,
        description="Number of compound concepts found"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )


# =============================================================================
# TURN SCHEMAS
# =============================================================================

class TurnRequest(BaseModel):
    """Request to process a complete conversation turn (recall + learn)."""

    user_message: str = Field(
        ...,
        description="User's message",
        min_length=1
    )
    ai_response: str = Field(
        ...,
        description="AI's response",
        min_length=1
    )
    max_concepts: int = Field(
        10,
        description="Maximum concepts for recall",
        ge=1,
        le=100
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_message": "Explain neural networks",
                "ai_response": "Neural networks are computational models inspired by biological neurons...",
                "max_concepts": 10,
                "metadata": {"source": "chat"}
            }
        }


class TurnResponse(BaseModel):
    """Response containing both recall and learn results."""

    recall: RecallResponse = Field(
        ...,
        description="Memory recall results"
    )
    learn: LearnResponse = Field(
        ...,
        description="Learning results"
    )


# =============================================================================
# STATS & ENTITIES SCHEMAS
# =============================================================================

class StatsResponse(BaseModel):
    """Memory statistics for a tenant."""

    tenant_id: str = Field(..., description="Tenant identifier")
    instance_id: str = Field(..., description="Instance identifier")
    entities: int = Field(..., description="Total entities/concepts")
    messages: int = Field(..., description="Total messages processed")
    decisions: int = Field(..., description="Total decisions recorded")
    attention_links: int = Field(..., description="Total attention links")


class EntityItem(BaseModel):
    """Single entity/concept item."""

    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (concept/decision/etc)")
    description: Optional[str] = Field(None, description="Entity description")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class EntitiesResponse(BaseModel):
    """List of entities/concepts."""

    entities: List[EntityItem] = Field(
        ...,
        description="List of entities"
    )
    total: int = Field(
        ...,
        description="Total number of entities"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )


# =============================================================================
# HEALTH SCHEMA
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")


# =============================================================================
# API KEY SCHEMAS
# =============================================================================

class CreateKeyRequest(BaseModel):
    """Request to create a new API key."""

    tenant_id: str = Field(
        ...,
        description="Tenant identifier",
        min_length=1
    )
    name: Optional[str] = Field(
        None,
        description="Human-readable name for the key"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "my_app",
                "name": "Production API Key"
            }
        }


class CreateKeyResponse(BaseModel):
    """Response after creating an API key."""

    api_key: str = Field(
        ...,
        description="The generated API key (store securely)"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )
    message: str = Field(
        ...,
        description="Important instructions about key storage"
    )
