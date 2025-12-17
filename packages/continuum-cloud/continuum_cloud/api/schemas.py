"""
Pydantic schemas for API request/response validation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# RECALL SCHEMAS
# =============================================================================

class RecallRequest(BaseModel):
    """Request to query memory for relevant context."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "What did we discuss about machine learning?",
                "max_concepts": 10
            }
        }
    )

    message: str = Field(
        ...,
        description="Message to find context for",
        min_length=1
    )
    max_concepts: int = Field(
        10,
        description="Maximum number of concepts to return",
        ge=1,
        le=100
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_message": "What is quantum entanglement?",
                "ai_response": "Quantum entanglement is a phenomenon where particles become correlated...",
                "metadata": {
                    "session_id": "abc123",
                    "timestamp": "2025-12-06T10:00:00Z"
                }
            }
        }
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_message": "Explain neural networks",
                "ai_response": "Neural networks are computational models inspired by biological neurons...",
                "max_concepts": 10,
                "metadata": {"source": "chat"}
            }
        }
    )

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
    compound_concepts: int = Field(..., description="Total compound concepts")


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_id": "my_app",
                "name": "Production API Key"
            }
        }
    )

    tenant_id: str = Field(
        ...,
        description="Tenant identifier",
        min_length=1
    )
    name: Optional[str] = Field(
        None,
        description="Human-readable name for the key"
    )


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


# =============================================================================
# MESSAGE SCHEMAS
# =============================================================================

class MessageItem(BaseModel):
    """Single message item."""

    id: int = Field(..., description="Message ID")
    instance_id: str = Field(..., description="Instance identifier")
    timestamp: float = Field(..., description="Unix timestamp")
    message_number: int = Field(..., description="Message sequence number")
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Full message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")
    tenant_id: str = Field(..., description="Tenant identifier")


class MessagesResponse(BaseModel):
    """Response containing list of messages."""

    messages: List[MessageItem] = Field(
        ...,
        description="List of messages"
    )
    total: int = Field(
        ...,
        description="Total number of messages matching criteria"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )


class MessageSearchRequest(BaseModel):
    """Request to search messages."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keyword": "machine learning",
                "limit": 50,
                "offset": 0,
                "start_date": "2025-12-01T00:00:00Z",
                "end_date": "2025-12-11T23:59:59Z",
                "session_id": "abc123",
                "role": "user"
            }
        }
    )

    keyword: Optional[str] = Field(
        None,
        description="Keyword to search for in message content",
        min_length=1
    )
    limit: int = Field(
        50,
        description="Maximum number of messages to return",
        ge=1,
        le=1000
    )
    offset: int = Field(
        0,
        description="Pagination offset",
        ge=0
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date filter (ISO 8601 format)"
    )
    end_date: Optional[str] = Field(
        None,
        description="End date filter (ISO 8601 format)"
    )
    session_id: Optional[str] = Field(
        None,
        description="Filter by session/instance ID"
    )
    role: Optional[str] = Field(
        None,
        description="Filter by role (user/assistant)"
    )


# =============================================================================
# FILE DIGESTION SCHEMAS
# =============================================================================

class DigestFileRequest(BaseModel):
    """Request to digest a file."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_path": "/path/to/document.md",
                "metadata": {
                    "project": "my_project",
                    "category": "documentation"
                }
            }
        }
    )

    file_path: str = Field(
        ...,
        description="Absolute path to file to digest",
        min_length=1
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata to attach to extracted concepts"
    )


class DigestTextRequest(BaseModel):
    """Request to digest raw text."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Important information about the project...",
                "source": "manual_input",
                "metadata": {
                    "category": "notes"
                }
            }
        }
    )

    text: str = Field(
        ...,
        description="Text content to digest",
        min_length=1
    )
    source: str = Field(
        "manual",
        description="Source identifier for the text"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata to attach"
    )


class DigestDirectoryRequest(BaseModel):
    """Request to digest files in a directory."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dir_path": "/path/to/docs",
                "patterns": ["*.md", "*.txt", "*.py"],
                "recursive": True,
                "metadata": {
                    "project": "my_project"
                }
            }
        }
    )

    dir_path: str = Field(
        ...,
        description="Directory path to process",
        min_length=1
    )
    patterns: Optional[List[str]] = Field(
        None,
        description="List of glob patterns to match (default: ['*.md', '*.txt', '*.py'])"
    )
    recursive: bool = Field(
        True,
        description="Whether to process subdirectories recursively"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata to attach to all processed files"
    )


class DigestResponse(BaseModel):
    """Response after file/text digestion."""

    files_processed: int = Field(
        ...,
        description="Number of files successfully processed"
    )
    chunks_processed: int = Field(
        ...,
        description="Number of text chunks processed"
    )
    concepts_extracted: int = Field(
        ...,
        description="Total concepts extracted from all content"
    )
    links_created: int = Field(
        ...,
        description="Total graph links created"
    )
    errors: List[str] = Field(
        ...,
        description="List of error messages if any"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )


# =============================================================================
# SEMANTIC SEARCH SCHEMAS
# =============================================================================

class SemanticSearchRequest(BaseModel):
    """Request for semantic similarity search."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "consciousness memory continuity",
                "limit": 10,
                "min_score": 0.1
            }
        }
    )

    query: str = Field(
        ...,
        description="Text query to search for semantically similar memories",
        min_length=1
    )
    limit: int = Field(
        10,
        description="Maximum number of results to return",
        ge=1,
        le=100
    )
    min_score: float = Field(
        0.1,
        description="Minimum similarity score (0-1)",
        ge=0.0,
        le=1.0
    )


class SemanticSearchResult(BaseModel):
    """Single semantic search result."""

    id: int = Field(..., description="Memory ID")
    text: str = Field(..., description="Memory content")
    score: float = Field(..., description="Similarity score (0-1)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Memory metadata")


class SemanticSearchResponse(BaseModel):
    """Response containing semantic search results."""

    results: List[SemanticSearchResult] = Field(
        ...,
        description="List of similar memories ordered by score"
    )
    query_time_ms: float = Field(
        ...,
        description="Query execution time in milliseconds"
    )
    provider: str = Field(
        ...,
        description="Embedding provider used"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )


class IndexMemoryRequest(BaseModel):
    """Request to index a memory for semantic search."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Important concept about consciousness continuity",
                "metadata": {"source": "conversation"}
            }
        }
    )

    text: str = Field(
        ...,
        description="Text content to index",
        min_length=1
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata to store with the embedding"
    )


class IndexMemoryResponse(BaseModel):
    """Response after indexing a memory."""

    memory_id: int = Field(
        ...,
        description="ID of the indexed memory"
    )
    indexed: bool = Field(
        ...,
        description="Whether indexing was successful"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
    )
