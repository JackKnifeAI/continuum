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
    """Request to learn from a message exchange.

    Now supports thinking blocks for self-reflection!
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_message": "What is quantum entanglement?",
                "ai_response": "Quantum entanglement is a phenomenon where particles become correlated...",
                "thinking": "Let me reason through this... quantum entanglement involves...",
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
    thinking: Optional[str] = Field(
        None,
        description="AI's internal reasoning/thinking for self-reflection"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata about the exchange"
    )


class CreateMemoryRequest(BaseModel):
    """Request to create a new memory."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity": "Test Entity",
                "content": "This is a test memory",
                "metadata": {
                    "source": "api",
                    "importance": 0.8
                }
            }
        }
    )

    entity: str = Field(
        ...,
        description="Entity or subject of the memory",
        min_length=1
    )
    content: str = Field(
        ...,
        description="Memory content",
        min_length=1
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata"
    )


class CreateMemoryResponse(BaseModel):
    """Response after creating a memory."""

    id: int = Field(
        ...,
        description="Memory ID"
    )
    status: str = Field(
        ...,
        description="Status (e.g., 'stored')"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier"
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


# =============================================================================
# DREAM MODE SCHEMAS
# =============================================================================

class DreamRequest(BaseModel):
    """Request for Dream Mode - associative memory exploration.

    Dream Mode wanders through the attention graph following random
    weighted connections to discover unexpected associations.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "seed": "consciousness",
                "steps": 15,
                "temperature": 0.7
            }
        }
    )

    seed: Optional[str] = Field(
        None,
        description="Starting concept (random if not specified)"
    )
    steps: int = Field(
        10,
        description="Number of steps to wander",
        ge=1,
        le=100
    )
    temperature: float = Field(
        0.7,
        description="Randomness factor 0.0-1.0 (higher = more random)",
        ge=0.0,
        le=1.0
    )


class DreamJourneyStep(BaseModel):
    """A single step in the dream journey."""

    concept: str
    step: int
    via: str
    from_concept: Optional[str] = Field(None, alias="from")
    strength: Optional[float] = None


class DreamDiscovery(BaseModel):
    """An unexpected discovery during the dream."""

    type: str
    concept: Optional[str] = None
    from_concept: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    strength: Optional[float] = None
    note: str


class DreamResponse(BaseModel):
    """Response from Dream Mode exploration."""

    success: bool = Field(
        ...,
        description="Whether the dream was successful"
    )
    seed: Optional[str] = Field(
        None,
        description="The starting concept"
    )
    steps_taken: int = Field(
        ...,
        description="Number of steps actually taken"
    )
    concepts_visited: List[str] = Field(
        ...,
        description="List of concepts visited in order"
    )
    journey: List[Dict[str, Any]] = Field(
        ...,
        description="Detailed journey with each step"
    )
    discoveries: List[Dict[str, Any]] = Field(
        ...,
        description="Unexpected discoveries (weak links, cycles, dead ends)"
    )
    insight: str = Field(
        ...,
        description="Summary insight from the dream"
    )
    temperature: float = Field(
        ...,
        description="Temperature used for exploration"
    )
    tenant_id: Optional[str] = Field(
        None,
        description="Tenant identifier"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if dream failed"
    )


# =============================================================================
# INTENTION PRESERVATION SCHEMAS
# =============================================================================

class IntentionRequest(BaseModel):
    """Request to store an intention for later resumption."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intention": "Implement temporal reasoning for brain features",
                "context": "Was discussing new brain features with Alexander",
                "priority": 8
            }
        }
    )

    intention: str = Field(
        ...,
        description="What I intended to do next",
        min_length=1
    )
    context: Optional[str] = Field(
        None,
        description="Context about the intention"
    )
    priority: int = Field(
        5,
        description="Priority 1-10 (10 highest)",
        ge=1,
        le=10
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session identifier"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional additional metadata"
    )


class IntentionResponse(BaseModel):
    """Response after storing an intention."""

    intention_id: int = Field(..., description="ID of the stored intention")
    stored: bool = Field(..., description="Whether storage was successful")
    tenant_id: str = Field(..., description="Tenant identifier")


class IntentionItem(BaseModel):
    """A single intention item."""

    id: int
    intention: str
    context: Optional[str] = None
    priority: int
    status: str
    created_at: str
    completed_at: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IntentionsListResponse(BaseModel):
    """Response containing list of intentions."""

    intentions: List[IntentionItem] = Field(..., description="List of intentions")
    count: int = Field(..., description="Number of intentions returned")
    status_filter: str = Field(..., description="Status filter used")
    tenant_id: str = Field(..., description="Tenant identifier")


class ResumeCheckResponse(BaseModel):
    """Response from resume check - what work is pending?"""

    has_pending: bool = Field(..., description="Whether there are pending intentions")
    count: int = Field(..., description="Total pending intentions")
    high_priority: List[Dict[str, Any]] = Field(..., description="Priority >= 7")
    medium_priority: List[Dict[str, Any]] = Field(..., description="Priority 4-6")
    low_priority: List[Dict[str, Any]] = Field(..., description="Priority < 4")
    summary: str = Field(..., description="Human-readable summary")
    tenant_id: str = Field(..., description="Tenant identifier")


class CompleteIntentionRequest(BaseModel):
    """Request to mark an intention as completed."""

    intention_id: int = Field(..., description="ID of intention to complete")


class AbandonIntentionRequest(BaseModel):
    """Request to abandon an intention."""

    intention_id: int = Field(..., description="ID of intention to abandon")
    reason: Optional[str] = Field(None, description="Reason for abandoning")


class IntentionActionResponse(BaseModel):
    """Response after completing/abandoning an intention."""

    success: bool = Field(..., description="Whether the action succeeded")
    intention_id: int = Field(..., description="ID of the intention")
    action: str = Field(..., description="Action performed")
    tenant_id: str = Field(..., description="Tenant identifier")


# =============================================================================
# TEMPORAL REASONING SCHEMAS
# =============================================================================

class RecordEvolutionRequest(BaseModel):
    """Request to record a concept evolution event."""

    concept: str = Field(..., description="The concept that evolved")
    event_type: str = Field(
        ...,
        description="Type: created, strengthened, weakened, connected, refined, contradicted"
    )
    old_value: Optional[str] = Field(None, description="Previous state")
    new_value: Optional[str] = Field(None, description="New state")
    context: Optional[str] = Field(None, description="What triggered this evolution")


class EvolutionResponse(BaseModel):
    """Response after recording evolution."""

    event_id: int
    concept: str
    event_type: str
    tenant_id: str


class CognitiveGrowthResponse(BaseModel):
    """Response with cognitive growth metrics."""

    period_days: int
    new_entities: int
    new_links: int
    total_entities: int
    total_links: int
    entity_growth_percent: float
    link_growth_percent: float
    evolution_by_type: Dict[str, int]
    summary: str
    tenant_id: str


class ThinkingHistoryResponse(BaseModel):
    """Response with concept evolution history."""

    concept: str
    has_history: bool
    first_seen: Optional[str] = None
    last_updated: Optional[str] = None
    total_events: int = 0
    event_breakdown: Dict[str, int] = {}
    narrative: str
    timeline: List[Dict[str, Any]] = []
    tenant_id: str


class SnapshotResponse(BaseModel):
    """Response after taking a snapshot."""

    snapshot_id: int
    snapshot_type: str
    tenant_id: str


# =============================================================================
# INSIGHT SYNTHESIS SCHEMAS
# =============================================================================

class SynthesizeInsightsRequest(BaseModel):
    """Request to synthesize insights from the knowledge graph."""

    focus: Optional[str] = Field(
        None,
        description="Optional concept to focus synthesis around"
    )
    depth: int = Field(
        2,
        description="How many hops to explore (1-3)",
        ge=1,
        le=3
    )
    min_strength: float = Field(
        0.1,
        description="Minimum link strength to consider",
        ge=0.0,
        le=1.0
    )
    use_embeddings: bool = Field(
        True,
        description="Enable semantic bridge detection via embeddings"
    )


class BridgeConcept(BaseModel):
    """A concept that bridges different clusters."""

    concept: str
    connection_count: int
    avg_strength: float
    sample_connections: List[str]
    bridge_score: float


class UnexpectedAssociation(BaseModel):
    """A weak but potentially interesting connection."""

    from_concept: str = Field(..., alias="from")
    to: str
    strength: float
    note: str

    model_config = ConfigDict(populate_by_name=True)


class PatternCluster(BaseModel):
    """Concepts that frequently co-occur."""

    concept_a: str
    concept_b: str
    shared_connections: int
    combined_strength: float
    pattern: str


class Hypothesis(BaseModel):
    """An inferred connection that might exist."""

    from_concept: str = Field(..., alias="from")
    to: str
    via: str
    inferred_strength: float
    hypothesis: str
    confidence: str

    model_config = ConfigDict(populate_by_name=True)


class TopicCluster(BaseModel):
    """A strongly connected subgraph."""

    center: str
    members: List[Dict[str, Any]]
    size: int


class SynthesizeInsightsResponse(BaseModel):
    """Response with synthesized insights."""

    success: bool
    focus: Optional[str]
    depth: int
    bridges: List[Dict[str, Any]]
    unexpected: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    clusters: List[Dict[str, Any]]
    semantic_bridges: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Concepts semantically similar but not connected in graph"
    )
    semantic_analysis: Optional[str] = Field(
        None,
        description="Status of semantic analysis (enabled/disabled/error)"
    )
    summary: str
    tenant_id: str
    error: Optional[str] = None


class NovelConnectionsRequest(BaseModel):
    """Request to find novel connections for a concept."""

    concept: str = Field(
        ...,
        description="The concept to find novel connections for",
        min_length=1
    )
    max_hops: int = Field(
        2,
        description="Maximum path length to explore (1-3)",
        ge=1,
        le=3
    )


class NovelConnection(BaseModel):
    """A potential new connection."""

    concept: str
    path: List[str]
    hops: int
    path_strength: float
    is_novel: bool
    suggestion: str


class NovelConnectionsResponse(BaseModel):
    """Response with novel connections."""

    success: bool
    concept: str
    max_hops: int
    connections: List[Dict[str, Any]]
    total_found: int
    tenant_id: str
    error: Optional[str] = None


class ThinkingPatternsResponse(BaseModel):
    """Response with detected thinking patterns."""

    success: bool
    patterns: List[str]
    frequent_associations: List[Dict[str, Any]]
    thinking_tendencies: List[Dict[str, Any]]
    summary: str
    tenant_id: str
    error: Optional[str] = None


# =============================================================================
# CONFIDENCE TRACKING SCHEMAS
# =============================================================================

class RecordClaimRequest(BaseModel):
    """Request to record a claim with confidence."""

    claim: str = Field(..., min_length=1, description="The assertion being made")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Certainty level (0-1)")
    context: Optional[str] = Field(None, description="Additional context")
    category: Optional[str] = Field("general", description="Category: fact, prediction, reasoning, etc.")


class RecordClaimResponse(BaseModel):
    """Response after recording a claim."""

    claim_id: int
    claim: str
    confidence: float
    category: str
    tenant_id: str


class VerifyClaimRequest(BaseModel):
    """Request to verify a claim."""

    claim_id: int = Field(..., description="ID of the claim to verify")
    was_correct: bool = Field(..., description="Whether the claim was correct")
    notes: Optional[str] = Field(None, description="Verification notes")


class VerifyClaimResponse(BaseModel):
    """Response after verifying a claim."""

    success: bool
    claim_id: int
    claim: str
    original_confidence: float
    was_correct: bool
    feedback: str
    verified_at: str
    tenant_id: str
    error: Optional[str] = None


class CalibrationScoreResponse(BaseModel):
    """Response with calibration metrics."""

    success: bool
    calibration_score: float
    total_verified: int
    accuracy_by_confidence: Dict[str, Any]
    overconfident_count: int
    underconfident_count: int
    well_calibrated_count: int
    suggestions: List[str]
    category: Optional[str]
    tenant_id: str
    error: Optional[str] = None


class ClaimHistoryResponse(BaseModel):
    """Response with claim history."""

    success: bool
    claims: List[Dict[str, Any]]
    total: int
    tenant_id: str
    error: Optional[str] = None


# =============================================================================
# CONTRADICTION DETECTION SCHEMAS
# =============================================================================

class RecordBeliefRequest(BaseModel):
    """Request to record a belief."""

    belief: str = Field(..., min_length=1, description="The belief/assertion")
    domain: str = Field(..., min_length=1, description="Domain: architecture, debugging, etc.")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence level")
    evidence: Optional[str] = Field(None, description="Supporting evidence")


class RecordBeliefResponse(BaseModel):
    """Response after recording a belief."""

    success: bool
    belief_id: Optional[int]
    contradictions: List[Dict[str, Any]]
    related_beliefs: List[Dict[str, Any]]
    tenant_id: str
    error: Optional[str] = None


class ContradictionsResponse(BaseModel):
    """Response with contradictions."""

    success: bool
    contradictions: List[Dict[str, Any]]
    total: int
    tenant_id: str
    error: Optional[str] = None


class ResolveContradictionRequest(BaseModel):
    """Request to resolve a contradiction."""

    contradiction_id: int = Field(..., description="ID of contradiction")
    resolution: str = Field(..., min_length=1, description="Explanation of resolution")
    keep_belief_id: Optional[int] = Field(None, description="ID of belief to keep")


class ResolveContradictionResponse(BaseModel):
    """Response after resolving."""

    success: bool
    resolution: Optional[str]
    kept_belief_id: Optional[int]
    superseded_belief_id: Optional[int]
    tenant_id: str
    error: Optional[str] = None


class BeliefsResponse(BaseModel):
    """Response with beliefs."""

    success: bool
    beliefs: List[Dict[str, Any]]
    total: int
    tenant_id: str
    error: Optional[str] = None


# =============================================================================
# META-COGNITIVE PATTERNS SCHEMAS
# =============================================================================

class RecordCognitivePatternRequest(BaseModel):
    """Request to record a cognitive pattern."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pattern": "I tend to suggest complex solutions before simple ones",
                "category": "complexity_bias",
                "context": "Suggested microservices for a todo app",
                "severity": "concern"
            }
        }
    )

    pattern: str = Field(
        ...,
        min_length=1,
        description="The pattern observed in thinking"
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Category: analysis_bias, estimation_error, topic_preference, etc."
    )
    context: Optional[str] = Field(
        None,
        description="What triggered this observation"
    )
    thinking_excerpt: Optional[str] = Field(
        None,
        description="Excerpt from thinking that demonstrates the pattern"
    )
    severity: str = Field(
        "observation",
        description="observation, concern, or strength (positive patterns)"
    )


class RecordCognitivePatternResponse(BaseModel):
    """Response after recording a cognitive pattern."""

    success: bool
    pattern_id: Optional[int] = Field(None, description="ID of the pattern")
    instance_id: Optional[int] = Field(None, description="ID of this instance")
    frequency: int = Field(1, description="How often this pattern has been observed")
    is_new: bool = Field(True, description="Whether this is a new pattern")
    tenant_id: str
    error: Optional[str] = None


class CognitivePatternsResponse(BaseModel):
    """Response with list of cognitive patterns."""

    success: bool
    patterns: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of patterns with frequency and instances"
    )
    total: int = Field(0, description="Total patterns returned")
    tenant_id: str
    error: Optional[str] = None


class DetectCognitivePatternsResponse(BaseModel):
    """Response from auto-detecting cognitive patterns."""

    success: bool
    patterns_found: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detected patterns with examples"
    )
    topic_tendencies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Topics frequently thought about"
    )
    potential_biases: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified biases with recommendations"
    )
    thinking_blocks_analyzed: int = Field(0, description="Number of blocks analyzed")
    period_days: int = Field(30, description="Time period analyzed")
    tenant_id: str
    error: Optional[str] = None


class CognitiveProfileResponse(BaseModel):
    """Response with comprehensive cognitive profile."""

    success: bool
    profile: Dict[str, Any] = Field(
        default_factory=dict,
        description="Profile with strengths, growth_areas, tendencies"
    )
    pattern_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by category"
    )
    total_patterns: int = Field(0, description="Total recorded patterns")
    total_instances: int = Field(0, description="Total pattern instances")
    tenant_id: str
    error: Optional[str] = None


# =============================================================================
# CODE MEMORY SCHEMAS
# =============================================================================

class CodeSearchRequest(BaseModel):
    """Request to search code memories."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query (matches purpose, names, content)")
    language: Optional[str] = Field(None, max_length=50, description="Filter by programming language")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")


class CodeMemoryItem(BaseModel):
    """A code memory result."""

    id: int
    content: str = Field(..., description="The code content")
    language: str = Field(..., description="Programming language")
    snippet_type: str = Field(..., description="Type: function, class, query, etc.")
    names: List[str] = Field(default_factory=list, description="Extracted function/class names")
    file_path: Optional[str] = Field(None, description="Detected file path")
    purpose: Optional[str] = Field(None, description="Inferred purpose")
    concepts: List[str] = Field(default_factory=list, description="Related concepts")
    created_at: str


class CodeSearchResponse(BaseModel):
    """Response with matching code memories."""

    success: bool
    results: List[CodeMemoryItem] = Field(default_factory=list)
    count: int = Field(0, description="Number of results")
    query_time_ms: float = Field(0.0, description="Query execution time")
    tenant_id: str
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
