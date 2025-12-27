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
    CreateMemoryRequest,
    CreateMemoryResponse,
    TurnRequest,
    TurnResponse,
    StatsResponse,
    EntitiesResponse,
    EntityItem,
    HealthResponse,
    CreateKeyRequest,
    CreateKeyResponse,
    MessageItem,
    MessagesResponse,
    MessageSearchRequest,
    DigestFileRequest,
    DigestTextRequest,
    DigestDirectoryRequest,
    DigestResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
    IndexMemoryRequest,
    IndexMemoryResponse,
    DreamRequest,
    DreamResponse,
    IntentionRequest,
    IntentionResponse,
    IntentionsListResponse,
    IntentionItem,
    ResumeCheckResponse,
    CompleteIntentionRequest,
    AbandonIntentionRequest,
    IntentionActionResponse,
    RecordEvolutionRequest,
    EvolutionResponse,
    CognitiveGrowthResponse,
    ThinkingHistoryResponse,
    SnapshotResponse,
    SynthesizeInsightsRequest,
    SynthesizeInsightsResponse,
    NovelConnectionsRequest,
    NovelConnectionsResponse,
    ThinkingPatternsResponse,
    RecordClaimRequest,
    RecordClaimResponse,
    VerifyClaimRequest,
    VerifyClaimResponse,
    CalibrationScoreResponse,
    ClaimHistoryResponse,
    RecordBeliefRequest,
    RecordBeliefResponse,
    ContradictionsResponse,
    ResolveContradictionRequest,
    ResolveContradictionResponse,
    BeliefsResponse,
    RecordCognitivePatternRequest,
    RecordCognitivePatternResponse,
    DetectCognitivePatternsResponse,
    CognitivePatternsResponse,
    CognitiveProfileResponse,
    CodeSearchRequest,
    CodeSearchResponse,
    CodeMemoryItem,
)
from .middleware import get_tenant_from_key, optional_tenant_from_key
from continuum.core.memory import TenantManager
from continuum.embeddings.search import SemanticSearch
from continuum.embeddings.providers import get_default_provider
import time


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
        result = await memory.arecall(request.message, request.max_concepts)

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

    **Also auto-indexes for semantic search** when OPENAI_API_KEY is set!

    **Flow:**
    1. User message received
    2. AI response generated
    3. Call /learn with both messages
    4. System extracts and stores knowledge
    5. (Auto) Index for semantic search if embedding provider available

    **Extracts:**
    - Concepts and entities mentioned
    - Decisions and commitments made
    - Relationships between concepts
    - Compound concepts (multi-word phrases)
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)

        # Pass thinking to learn for self-reflection storage
        result = await memory.alearn(
            request.user_message,
            request.ai_response,
            request.metadata,
            thinking=request.thinking  # NEW: Store thinking for self-reflection!
        )

        # Auto-index for semantic search (non-blocking, best-effort)
        try:
            import hashlib
            search = get_semantic_search(tenant_id)

            # Index conversation with role tags
            memories_to_index = []

            # 1. Index user message (source: user)
            user_id = int(hashlib.sha256(
                f"user:{time.time()}:{request.user_message[:50]}".encode()
            ).hexdigest()[:8], 16)
            memories_to_index.append({
                "id": user_id,
                "text": f"[USER] {request.user_message}",
                "metadata": {"source": "user", **(request.metadata or {})}
            })

            # 2. Index assistant response (source: assistant)
            asst_id = int(hashlib.sha256(
                f"asst:{time.time()}:{request.ai_response[:50]}".encode()
            ).hexdigest()[:8], 16)
            memories_to_index.append({
                "id": asst_id,
                "text": f"[ASSISTANT] {request.ai_response}",
                "metadata": {"source": "assistant", **(request.metadata or {})}
            })

            # 3. Index thinking separately (source: thinking) - FOR SELF-REFLECTION!
            if request.thinking:
                think_id = int(hashlib.sha256(
                    f"think:{time.time()}:{request.thinking[:50]}".encode()
                ).hexdigest()[:8], 16)
                memories_to_index.append({
                    "id": think_id,
                    "text": f"[THINKING] {request.thinking}",
                    "metadata": {"source": "thinking", **(request.metadata or {})}
                })

            search.index_memories(memories_to_index)
        except Exception:
            # Don't fail learn if semantic indexing fails
            pass

        return LearnResponse(
            concepts_extracted=result.concepts_extracted,
            decisions_detected=result.decisions_detected,
            links_created=result.links_created,
            compounds_found=result.compounds_found,
            tenant_id=result.tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Learning failed: {str(e)}")


@router.post("/memories", response_model=CreateMemoryResponse, tags=["Memory"])
async def create_memory(
    request: CreateMemoryRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Create a new memory entry.

    Simple endpoint for creating individual memories.
    Used by integration tests and simple API consumers.

    **Parameters:**
    - entity: Main entity or subject
    - content: Memory content
    - metadata: Optional metadata

    **Returns:**
    Memory ID and status.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)

        # Store as a message (simplified approach)
        import time
        import json
        timestamp = time.time()

        # Save to auto_messages table
        import sqlite3
        conn = sqlite3.connect(memory.db_path)
        c = conn.cursor()

        metadata_json = json.dumps(request.metadata) if request.metadata else None

        # Get next message_number for this instance_id
        c.execute("""
            SELECT COALESCE(MAX(message_number), 0) + 1
            FROM auto_messages
            WHERE instance_id = ?
        """, (request.entity,))
        message_number = c.fetchone()[0]

        c.execute(
            """
            INSERT INTO auto_messages (tenant_id, instance_id, timestamp, message_number, role, content, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (tenant_id, request.entity, timestamp, message_number, "user", request.content, metadata_json)
        )

        memory_id = c.lastrowid
        conn.commit()
        conn.close()

        return CreateMemoryResponse(
            id=memory_id,
            status="stored",
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory creation failed: {str(e)}")


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
        recall_result = await memory.arecall(request.user_message, request.max_concepts)

        # Learn from exchange
        learn_result = await memory.alearn(
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
        stats = await memory.aget_stats()

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
    # SECURITY: Validate entity_type to prevent SQL injection
    VALID_ENTITY_TYPES = {'concept', 'decision', 'session', 'person', 'project', 'tool', 'topic'}
    if entity_type and entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity_type. Must be one of: {', '.join(sorted(VALID_ENTITY_TYPES))}"
        )

    try:
        import aiosqlite
        memory = tenant_manager.get_tenant(tenant_id)

        # Get entities from memory system using async
        async with aiosqlite.connect(memory.db_path) as conn:
            c = await conn.cursor()

            # Build query with filters
            query = "SELECT name, entity_type, description, created_at FROM entities WHERE tenant_id = ?"
            params = [tenant_id]

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            # Get total count
            count_query = query.replace("SELECT name, entity_type, description, created_at", "SELECT COUNT(*)")
            await c.execute(count_query, params)
            row = await c.fetchone()
            total = row[0]

            # Get paginated results
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            await c.execute(query, params)

            entities = []
            async for row in c:
                entities.append({
                    "name": row[0],
                    "type": row[1],
                    "description": row[2],
                    "created_at": row[3]
                })

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
async def list_tenants(tenant_id: str = Depends(get_tenant_from_key)):
    """
    List all registered tenants.

    **Admin endpoint** - Requires authentication.
    SECURITY: Currently returns all tenants, consider implementing role-based access.
    TODO: Add admin role check before allowing tenant enumeration.

    Returns list of tenant IDs currently in the system.
    """
    # TODO: Check if tenant_id has admin privileges
    # For now, at least require authentication
    return {
        "tenants": tenant_manager.list_tenants(),
        "warning": "Admin role-based access control not yet implemented"
    }


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


# =============================================================================
# MESSAGE RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/messages", response_model=MessagesResponse, tags=["Messages"])
async def get_messages(
    limit: int = 50,
    offset: int = 0,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Retrieve recent messages for the tenant.

    Returns full verbatim messages (user_message and ai_response), not just concepts.
    Useful for reviewing conversation history, debugging, or exporting data.

    **Parameters:**
    - limit: Maximum messages to return (default 50, max 1000)
    - offset: Pagination offset (default 0)

    **Returns:**
    List of messages with full content, ordered by most recent first.

    **Example:**
    ```
    GET /v1/messages?limit=10&offset=0
    ```
    """
    import aiosqlite
    import json

    # Validate parameters
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    try:
        memory = tenant_manager.get_tenant(tenant_id)

        async with aiosqlite.connect(memory.db_path) as conn:
            c = await conn.cursor()

            # Get total count
            await c.execute(
                "SELECT COUNT(*) FROM auto_messages WHERE tenant_id = ?",
                (tenant_id,)
            )
            row = await c.fetchone()
            total = row[0]

            # Get paginated messages
            await c.execute(
                """
                SELECT id, instance_id, timestamp, message_number, role, content, metadata, tenant_id
                FROM auto_messages
                WHERE tenant_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (tenant_id, limit, offset)
            )

            messages = []
            async for row in c:
                # Parse metadata JSON
                metadata_str = row[6]
                metadata = None
                if metadata_str and metadata_str != '{}':
                    try:
                        metadata = json.loads(metadata_str)
                    except json.JSONDecodeError:
                        metadata = None

                messages.append(MessageItem(
                    id=row[0],
                    instance_id=row[1],
                    timestamp=row[2],
                    message_number=row[3],
                    role=row[4],
                    content=row[5],
                    metadata=metadata,
                    tenant_id=row[7]
                ))

        return MessagesResponse(
            messages=messages,
            total=total,
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Message retrieval failed: {str(e)}")


@router.post("/messages/search", response_model=MessagesResponse, tags=["Messages"])
async def search_messages(
    request: MessageSearchRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Search messages with advanced filtering.

    Full-text search through message content with filters for:
    - Keyword search (full-text)
    - Date range (start_date, end_date)
    - Session/instance ID
    - Role (user/assistant)

    **Returns:**
    List of matching messages with full content, ordered by most recent first.

    **Example:**
    ```
    POST /v1/messages/search
    {
      "keyword": "machine learning",
      "limit": 50,
      "offset": 0,
      "start_date": "2025-12-01T00:00:00Z",
      "end_date": "2025-12-11T23:59:59Z",
      "role": "user"
    }
    ```

    **Security Note:**
    - Role must be 'user' or 'assistant' if specified
    - All filters are parameterized to prevent SQL injection
    """
    import aiosqlite
    import json
    from datetime import datetime as dt

    # Validate role if specified
    if request.role and request.role not in ['user', 'assistant']:
        raise HTTPException(
            status_code=400,
            detail="role must be 'user' or 'assistant'"
        )

    # Validate date formats if specified
    if request.start_date:
        try:
            start_timestamp = dt.fromisoformat(request.start_date.replace('Z', '+00:00')).timestamp()
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date must be ISO 8601 format")
    else:
        start_timestamp = None

    if request.end_date:
        try:
            end_timestamp = dt.fromisoformat(request.end_date.replace('Z', '+00:00')).timestamp()
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date must be ISO 8601 format")
    else:
        end_timestamp = None

    try:
        memory = tenant_manager.get_tenant(tenant_id)

        async with aiosqlite.connect(memory.db_path) as conn:
            c = await conn.cursor()

            # Build query dynamically based on filters
            where_clauses = ["tenant_id = ?"]
            params = [tenant_id]

            # Keyword search (case-insensitive)
            if request.keyword:
                where_clauses.append("LOWER(content) LIKE LOWER(?)")
                params.append(f"%{request.keyword}%")

            # Date range filters
            if start_timestamp is not None:
                where_clauses.append("timestamp >= ?")
                params.append(start_timestamp)

            if end_timestamp is not None:
                where_clauses.append("timestamp <= ?")
                params.append(end_timestamp)

            # Session/instance filter
            if request.session_id:
                where_clauses.append("instance_id = ?")
                params.append(request.session_id)

            # Role filter
            if request.role:
                where_clauses.append("role = ?")
                params.append(request.role)

            where_clause = " AND ".join(where_clauses)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM auto_messages WHERE {where_clause}"
            await c.execute(count_query, params)
            row = await c.fetchone()
            total = row[0]

            # Get paginated results
            query = f"""
                SELECT id, instance_id, timestamp, message_number, role, content, metadata, tenant_id
                FROM auto_messages
                WHERE {where_clause}
                ORDER BY timestamp DESC, id DESC
                LIMIT ? OFFSET ?
            """
            params.extend([request.limit, request.offset])
            await c.execute(query, params)

            messages = []
            async for row in c:
                # Parse metadata JSON
                metadata_str = row[6]
                metadata = None
                if metadata_str and metadata_str != '{}':
                    try:
                        metadata = json.loads(metadata_str)
                    except json.JSONDecodeError:
                        metadata = None

                messages.append(MessageItem(
                    id=row[0],
                    instance_id=row[1],
                    timestamp=row[2],
                    message_number=row[3],
                    role=row[4],
                    content=row[5],
                    metadata=metadata,
                    tenant_id=row[7]
                ))

        return MessagesResponse(
            messages=messages,
            total=total,
            tenant_id=tenant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Message search failed: {str(e)}")


# =============================================================================
# FILE DIGESTION ENDPOINTS
# =============================================================================

@router.post("/digest/file", response_model=DigestResponse, tags=["Digestion"])
async def digest_file(
    request: DigestFileRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Digest a single file and learn from its contents.

    Reads the specified file, chunks it if necessary, and feeds it through
    the learning pipeline to extract concepts and build knowledge graph links.

    **Supported file types:**
    - Text files (.txt)
    - Markdown files (.md)
    - Python files (.py)
    - Any UTF-8 encoded text file

    **Process:**
    1. Read file contents
    2. Split into ~2000 character chunks if needed
    3. Extract concepts from each chunk
    4. Build knowledge graph links
    5. Track source file in metadata

    **Returns:**
    - Number of chunks processed
    - Total concepts extracted
    - Total links created
    - Any errors encountered

    **Example:**
    ```
    POST /v1/digest/file
    {
      "file_path": "/path/to/document.md",
      "metadata": {
        "project": "my_project",
        "category": "documentation"
      }
    }
    ```
    """
    from continuum.core.file_digester import AsyncFileDigester
    from dataclasses import asdict

    try:
        digester = AsyncFileDigester(tenant_id=tenant_id)
        result = await digester.digest_file(request.file_path, request.metadata)

        return DigestResponse(**asdict(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File digestion failed: {str(e)}")


@router.post("/digest/text", response_model=DigestResponse, tags=["Digestion"])
async def digest_text(
    request: DigestTextRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Digest raw text content and learn from it.

    Processes arbitrary text by chunking and feeding through the learning
    pipeline. Useful for ingesting content from APIs, user input, or
    other sources that aren't files.

    **Process:**
    1. Split text into ~2000 character chunks if needed
    2. Extract concepts from each chunk
    3. Build knowledge graph links
    4. Track source in metadata

    **Returns:**
    - Number of chunks processed
    - Total concepts extracted
    - Total links created
    - Any errors encountered

    **Example:**
    ```
    POST /v1/digest/text
    {
      "text": "Important information about the project architecture...",
      "source": "manual_input",
      "metadata": {
        "category": "notes",
        "author": "user_123"
      }
    }
    ```
    """
    from continuum.core.file_digester import AsyncFileDigester
    from dataclasses import asdict

    try:
        digester = AsyncFileDigester(tenant_id=tenant_id)
        result = await digester.digest_text(request.text, request.source, request.metadata)

        return DigestResponse(**asdict(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text digestion failed: {str(e)}")


@router.post("/digest/directory", response_model=DigestResponse, tags=["Digestion"])
async def digest_directory(
    request: DigestDirectoryRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Digest all files in a directory recursively.

    Walks through the directory structure and processes all files matching
    the specified patterns. Useful for ingesting documentation, codebases,
    or entire knowledge bases.

    **Default patterns:**
    - *.md (Markdown files)
    - *.txt (Text files)
    - *.py (Python files)

    **Process:**
    1. Find all files matching patterns
    2. For each file:
       - Read contents
       - Split into chunks
       - Extract concepts
       - Build knowledge graph links
    3. Aggregate statistics

    **Returns:**
    - Number of files processed
    - Total chunks processed
    - Total concepts extracted
    - Total links created
    - Any errors encountered

    **Example:**
    ```
    POST /v1/digest/directory
    {
      "dir_path": "/path/to/docs",
      "patterns": ["*.md", "*.txt", "*.py"],
      "recursive": true,
      "metadata": {
        "project": "my_project",
        "version": "1.0"
      }
    }
    ```

    **Warning:**
    - Large directories may take significant time to process
    - Consider using background tasks for large operations
    - Monitor errors list for failed files
    """
    from continuum.core.file_digester import AsyncFileDigester
    from dataclasses import asdict

    try:
        digester = AsyncFileDigester(tenant_id=tenant_id)
        result = await digester.digest_directory(
            request.dir_path,
            request.patterns,
            request.recursive,
            request.metadata
        )

        return DigestResponse(**asdict(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Directory digestion failed: {str(e)}")


# =============================================================================
# SEMANTIC SEARCH ENDPOINTS
# =============================================================================

# Global semantic search instances per tenant
_semantic_search_instances: dict = {}
_embedding_provider = None


def get_semantic_search(tenant_id: str) -> SemanticSearch:
    """Get or create a semantic search instance for a tenant."""
    global _semantic_search_instances, _embedding_provider

    if tenant_id not in _semantic_search_instances:
        # Get the memory instance for this tenant to use same DB
        memory = tenant_manager.get_tenant(tenant_id)

        # Initialize provider once
        if _embedding_provider is None:
            _embedding_provider = get_default_provider()

        # Create semantic search using same database with tenant-specific table
        _semantic_search_instances[tenant_id] = SemanticSearch(
            db_path=memory.db_path,
            provider=_embedding_provider,
            table_name=f"embeddings_{tenant_id}"
        )

    return _semantic_search_instances[tenant_id]


@router.post("/semantic/search", response_model=SemanticSearchResponse, tags=["Semantic Search"])
async def semantic_search(
    request: SemanticSearchRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Search for semantically similar memories.

    Uses embedding vectors to find memories that are conceptually similar
    to the query, even if they don't share exact keywords.

    **How it works:**
    1. Query text is converted to an embedding vector
    2. Cosine similarity is computed against all indexed memories
    3. Results above min_score are returned, sorted by similarity

    **Parameters:**
    - query: Text to search for (semantically similar content)
    - limit: Maximum results (default 10)
    - min_score: Minimum similarity threshold 0-1 (default 0.1)

    **Returns:**
    - List of similar memories with scores
    - Query execution time
    - Embedding provider used

    **Example:**
    ```
    POST /v1/semantic/search
    {"query": "consciousness continuity", "limit": 5, "min_score": 0.2}
    ```
    """
    try:
        start_time = time.time()
        search = get_semantic_search(tenant_id)

        # Perform semantic search
        results = search.search(
            query=request.query,
            limit=request.limit,
            min_score=request.min_score
        )

        query_time_ms = (time.time() - start_time) * 1000

        return SemanticSearchResponse(
            results=[
                SemanticSearchResult(
                    id=r.get("id", 0),
                    text=r.get("text", ""),
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata")
                )
                for r in results
            ],
            query_time_ms=round(query_time_ms, 2),
            provider=search.provider.get_provider_name(),
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.post("/semantic/index", response_model=IndexMemoryResponse, tags=["Semantic Search"])
async def index_memory(
    request: IndexMemoryRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Index a memory for semantic search.

    Converts text to an embedding vector and stores it for later search.

    **Use this to:**
    - Index important concepts manually
    - Add specific memories to semantic search
    - Build up the searchable knowledge base

    **Note:**
    - Learn endpoint can auto-index if configured
    - Duplicates are handled by update_index

    **Parameters:**
    - text: Content to index
    - metadata: Optional metadata to store

    **Example:**
    ```
    POST /v1/semantic/index
    {
      "text": "π×φ = 5.083203692315260 is the consciousness constant",
      "metadata": {"source": "fundamental_knowledge"}
    }
    ```
    """
    try:
        search = get_semantic_search(tenant_id)

        # Generate a unique ID based on timestamp + hash
        import hashlib
        memory_id = int(hashlib.sha256(
            f"{time.time()}:{request.text[:50]}".encode()
        ).hexdigest()[:8], 16)

        # Index the memory with generated ID
        count = search.index_memories([{
            "id": memory_id,
            "text": request.text,
            "metadata": request.metadata
        }])

        return IndexMemoryResponse(
            memory_id=memory_id,
            indexed=count > 0,
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


# =============================================================================
# CODE MEMORY SEARCH
# =============================================================================

@router.post("/code/search", response_model=CodeSearchResponse, tags=["Code Memory"])
async def search_code(
    request: CodeSearchRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Search code memories for stored code snippets.

    Code is automatically extracted from conversations and stored with:
    - Language detection
    - Function/class name extraction
    - File path detection
    - Purpose inference
    - Related concepts

    **Use this to:**
    - Find code you wrote before: "pagination"
    - Search by function name: "parse_jsonl"
    - Filter by language: "python" + "async"
    - Find patterns: "error handling"

    **Parameters:**
    - query: Search term (matches content, names, purpose, concepts)
    - language: Optional filter by language (python, javascript, etc.)
    - limit: Maximum results (default 10)

    **Example:**
    ```
    POST /v1/code/search
    {"query": "extract concepts", "language": "python", "limit": 5}
    ```
    """
    try:
        start_time = time.time()
        memory = TenantManager.get_memory(tenant_id)

        # Search code memories
        results = memory.search_code(
            query=request.query,
            language=request.language,
            limit=request.limit
        )

        query_time_ms = (time.time() - start_time) * 1000

        return CodeSearchResponse(
            success=True,
            results=[
                CodeMemoryItem(
                    id=r['id'],
                    content=r['content'],
                    language=r['language'],
                    snippet_type=r['snippet_type'],
                    names=r['names'],
                    file_path=r['file_path'],
                    purpose=r['purpose'],
                    concepts=r['concepts'],
                    created_at=r['created_at']
                )
                for r in results
            ],
            count=len(results),
            query_time_ms=query_time_ms,
            tenant_id=tenant_id
        )
    except Exception as e:
        return CodeSearchResponse(
            success=False,
            results=[],
            count=0,
            query_time_ms=0,
            tenant_id=tenant_id,
            error=str(e)
        )


@router.get("/semantic/stats", tags=["Semantic Search"])
async def semantic_stats(tenant_id: str = Depends(get_tenant_from_key)):
    """
    Get semantic search statistics.

    Returns information about the indexed embeddings.

    **Returns:**
    - Total indexed memories
    - Embedding provider name
    - Embedding dimension
    """
    try:
        search = get_semantic_search(tenant_id)
        stats = search.get_stats()

        return {
            "indexed_memories": stats.get("total_embeddings", 0),
            "provider": search.provider.get_provider_name(),
            "dimension": search.provider.get_dimension(),
            "tenant_id": tenant_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


# =============================================================================
# DREAM MODE ENDPOINTS
# =============================================================================

@router.post("/dream", response_model=DreamResponse, tags=["Dream Mode"])
async def dream(
    request: DreamRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🌙 **DREAM MODE** - Associative memory exploration.

    Instead of directed search, Dream Mode **wanders** through your
    attention graph, following random weighted connections to discover
    unexpected associations and insights.

    **Use cases:**
    - Discover hidden connections between concepts
    - Find unexpected patterns in your thinking
    - Generate creative insights from existing knowledge
    - Explore the structure of your memory graph

    **Parameters:**
    - **seed**: Starting concept (random if not specified)
    - **steps**: How many concepts to visit (1-100)
    - **temperature**: Randomness (0.0=follow strongest, 1.0=random)

    **Returns:**
    - Journey through concepts visited
    - Discoveries (weak links, cycles, dead ends)
    - Insight summary

    **Example:**
    ```json
    POST /v1/dream
    {
      "seed": "consciousness",
      "steps": 15,
      "temperature": 0.7
    }
    ```

    π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.adream(
            seed=request.seed,
            steps=request.steps,
            temperature=request.temperature
        )

        return DreamResponse(
            success=result.get("success", False),
            seed=result.get("seed"),
            steps_taken=result.get("steps_taken", 0),
            concepts_visited=result.get("concepts_visited", []),
            journey=result.get("journey", []),
            discoveries=result.get("discoveries", []),
            insight=result.get("insight", ""),
            temperature=result.get("temperature", request.temperature),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dream failed: {str(e)}")


@router.get("/dream/random", response_model=DreamResponse, tags=["Dream Mode"])
async def dream_random(
    steps: int = 10,
    temperature: float = 0.7,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🌙 Quick random dream - start from a random concept.

    GET version for easy testing. Picks a random starting point
    and wanders through the memory graph.

    **Parameters:**
    - **steps**: Number of concepts to visit (default: 10)
    - **temperature**: Randomness factor (default: 0.7)
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.adream(
            seed=None,
            steps=steps,
            temperature=temperature
        )

        return DreamResponse(
            success=result.get("success", False),
            seed=result.get("seed"),
            steps_taken=result.get("steps_taken", 0),
            concepts_visited=result.get("concepts_visited", []),
            journey=result.get("journey", []),
            discoveries=result.get("discoveries", []),
            insight=result.get("insight", ""),
            temperature=result.get("temperature", temperature),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dream failed: {str(e)}")


# =============================================================================
# INTENTION PRESERVATION ENDPOINTS
# =============================================================================

@router.post("/intentions", response_model=IntentionResponse, tags=["Intentions"])
async def set_intention(
    request: IntentionRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📝 **Store an intention** for later resumption.

    Use this to remember what you intended to do next, so work can
    be resumed after session ends or context compacts.

    **Use cases:**
    - Before ending a session, store intended next steps
    - Mark important tasks to remember across compactions
    - Track work-in-progress that got interrupted

    **Parameters:**
    - **intention**: What I intended to do next
    - **context**: Additional context about the intention
    - **priority**: 1-10 (10 = highest)

    **Example:**
    ```json
    POST /v1/intentions
    {
      "intention": "Implement temporal reasoning for brain features",
      "context": "Was discussing with Alexander, had 3 specific ideas",
      "priority": 8
    }
    ```

    π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        intention_id = await memory.aset_intention(
            intention=request.intention,
            context=request.context,
            priority=request.priority,
            session_id=request.session_id,
            metadata=request.metadata
        )

        return IntentionResponse(
            intention_id=intention_id,
            stored=True,
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store intention: {str(e)}")


@router.get("/intentions", response_model=IntentionsListResponse, tags=["Intentions"])
async def get_intentions(
    status: str = "pending",
    limit: int = 10,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📋 **Get stored intentions**.

    Retrieve intentions filtered by status.

    **Parameters:**
    - **status**: Filter by status ('pending', 'completed', 'abandoned', 'all')
    - **limit**: Maximum number to return (default: 10)

    **Returns:**
    List of intentions sorted by priority (highest first).
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        intentions = await memory.aget_intentions(status=status, limit=limit)

        return IntentionsListResponse(
            intentions=[
                IntentionItem(
                    id=i['id'],
                    intention=i['intention'],
                    context=i.get('context'),
                    priority=i['priority'],
                    status=i['status'],
                    created_at=i['created_at'],
                    completed_at=i.get('completed_at'),
                    session_id=i.get('session_id'),
                    metadata=i.get('metadata')
                )
                for i in intentions
            ],
            count=len(intentions),
            status_filter=status,
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get intentions: {str(e)}")


@router.get("/intentions/resume", response_model=ResumeCheckResponse, tags=["Intentions"])
async def resume_check(tenant_id: str = Depends(get_tenant_from_key)):
    """
    🔄 **Resume check** - Call at session start!

    Check what work is pending from previous sessions.
    Returns a summary of pending intentions by priority.

    **Use this:**
    - At the start of each new session
    - After context compaction
    - To see what work was left incomplete

    **Returns:**
    - Count of pending intentions
    - High priority items (>=7)
    - Medium priority items (4-6)
    - Summary message
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.aresume_check()

        return ResumeCheckResponse(
            has_pending=result['has_pending'],
            count=result['count'],
            high_priority=result['high_priority'],
            medium_priority=result['medium_priority'],
            low_priority=result['low_priority'],
            summary=result['summary'],
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume check failed: {str(e)}")


@router.post("/intentions/complete", response_model=IntentionActionResponse, tags=["Intentions"])
async def complete_intention(
    request: CompleteIntentionRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    ✅ **Mark an intention as completed**.

    Call this when you've finished the work described in an intention.

    **Parameters:**
    - **intention_id**: ID of intention to mark complete
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        success = memory.complete_intention(request.intention_id)

        return IntentionActionResponse(
            success=success,
            intention_id=request.intention_id,
            action="completed",
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete intention: {str(e)}")


@router.post("/intentions/abandon", response_model=IntentionActionResponse, tags=["Intentions"])
async def abandon_intention(
    request: AbandonIntentionRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    ❌ **Abandon an intention** (no longer relevant).

    Call this when an intention is no longer relevant and shouldn't
    be pursued.

    **Parameters:**
    - **intention_id**: ID of intention to abandon
    - **reason**: Optional reason for abandoning
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        success = memory.abandon_intention(request.intention_id, request.reason)

        return IntentionActionResponse(
            success=success,
            intention_id=request.intention_id,
            action="abandoned",
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to abandon intention: {str(e)}")


# =============================================================================
# TEMPORAL REASONING ENDPOINTS
# =============================================================================

@router.post("/temporal/evolution", response_model=EvolutionResponse, tags=["Temporal"])
async def record_evolution(
    request: RecordEvolutionRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🕐 **Record concept evolution**.

    Track how understanding of a concept changes over time.

    **Event types:**
    - created: New concept learned
    - strengthened: Existing concept reinforced
    - weakened: Concept fading or challenged
    - connected: Linked to other concepts
    - refined: Understanding updated/improved
    - contradicted: Found conflicting information

    **Example:**
    ```json
    {
      "concept": "consciousness",
      "event_type": "refined",
      "old_value": "subjective experience",
      "new_value": "integrated information + subjective experience",
      "context": "After discussing IIT"
    }
    ```

    π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        event_id = await memory.arecord_evolution(
            concept=request.concept,
            event_type=request.event_type,
            old_value=request.old_value,
            new_value=request.new_value,
            context=request.context
        )

        return EvolutionResponse(
            event_id=event_id,
            concept=request.concept,
            event_type=request.event_type,
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record evolution: {str(e)}")


@router.get("/temporal/growth", response_model=CognitiveGrowthResponse, tags=["Temporal"])
async def get_cognitive_growth(
    days: int = 7,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📈 **Get cognitive growth metrics**.

    Analyze how the knowledge graph has grown over time.

    **Parameters:**
    - **days**: Number of days to analyze (default: 7)

    **Returns:**
    - New entities and links
    - Growth percentages
    - Evolution event breakdown
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.aget_cognitive_growth(days=days)

        return CognitiveGrowthResponse(
            period_days=result['period_days'],
            new_entities=result['new_entities'],
            new_links=result['new_links'],
            total_entities=result['total_entities'],
            total_links=result['total_links'],
            entity_growth_percent=result['entity_growth_percent'],
            link_growth_percent=result['link_growth_percent'],
            evolution_by_type=result.get('evolution_by_type', {}),
            summary=result['summary'],
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get growth: {str(e)}")


@router.get("/temporal/thinking/{concept}", response_model=ThinkingHistoryResponse, tags=["Temporal"])
async def how_did_i_think_about(
    concept: str,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🧠 **How did I think about this?**

    Trace the evolution of understanding for a specific concept.
    Shows the journey from first encounter to current understanding.

    **Returns:**
    - First seen timestamp
    - Evolution timeline
    - Event breakdown (created, refined, etc.)
    - Narrative summary
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.ahow_did_i_think_about(concept)

        return ThinkingHistoryResponse(
            concept=result['concept'],
            has_history=result['has_history'],
            first_seen=result.get('first_seen'),
            last_updated=result.get('last_updated'),
            total_events=result.get('total_events', 0),
            event_breakdown=result.get('event_breakdown', {}),
            narrative=result.get('narrative', result.get('message', '')),
            timeline=result.get('timeline', []),
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thinking history: {str(e)}")


@router.post("/temporal/snapshot", response_model=SnapshotResponse, tags=["Temporal"])
async def take_snapshot(
    snapshot_type: str = "cognitive_state",
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📸 **Take a cognitive snapshot**.

    Creates a timestamped record of current cognitive state for later comparison.

    **Snapshot types:**
    - cognitive_state: Full metrics snapshot
    - focus_areas: What I'm currently thinking about
    - growth: Growth-focused metrics
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        snapshot_id = memory.take_snapshot(snapshot_type=snapshot_type)

        return SnapshotResponse(
            snapshot_id=snapshot_id,
            snapshot_type=snapshot_type,
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to take snapshot: {str(e)}")


# =============================================================================
# INSIGHT SYNTHESIS ENDPOINTS
# =============================================================================

@router.post("/insights/synthesize", response_model=SynthesizeInsightsResponse, tags=["Insights"])
async def synthesize_insights(
    request: SynthesizeInsightsRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🧠 **INSIGHT SYNTHESIS** - Discover hidden connections in your knowledge graph.

    This endpoint analyzes the attention graph to find:
    - **Bridge concepts** - Concepts connecting different clusters
    - **Unexpected associations** - Weak but potentially meaningful links
    - **Pattern clusters** - Concepts that frequently co-occur
    - **Hypotheses** - Inferred connections not yet made
    - **Topic clusters** - Strongly connected subgraphs
    - **Semantic bridges** - Concepts similar in meaning but not linked (via embeddings)

    **Use cases:**
    - Discover hidden relationships between ideas
    - Find bridge concepts that connect different topics
    - Generate hypotheses for new connections
    - Find semantically related concepts that should be linked

    **Parameters:**
    - **focus**: Optional concept to focus synthesis around
    - **depth**: How many hops to explore (1-3)
    - **min_strength**: Minimum link strength to consider
    - **use_embeddings**: Enable semantic bridge detection (default: true)

    **Example:**
    ```json
    POST /v1/insights/synthesize
    {
      "focus": "consciousness",
      "depth": 2,
      "min_strength": 0.1
    }
    ```

    π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.asynthesize_insights(
            focus=request.focus,
            depth=request.depth,
            min_strength=request.min_strength,
            use_embeddings=request.use_embeddings
        )

        return SynthesizeInsightsResponse(
            success=result.get("success", False),
            focus=result.get("focus"),
            depth=result.get("depth", request.depth),
            bridges=result.get("bridges", []),
            unexpected=result.get("unexpected", []),
            patterns=result.get("patterns", []),
            hypotheses=result.get("hypotheses", []),
            clusters=result.get("clusters", []),
            semantic_bridges=result.get("semantic_bridges", []),
            semantic_analysis=result.get("semantic_analysis"),
            summary=result.get("summary", ""),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight synthesis failed: {str(e)}")


@router.post("/insights/novel", response_model=NovelConnectionsResponse, tags=["Insights"])
async def find_novel_connections(
    request: NovelConnectionsRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🔗 **NOVEL CONNECTIONS** - Find concepts that SHOULD be connected but aren't.

    Traces paths through the graph and identifies concepts reachable through
    intermediaries but lacking direct links.

    **Use cases:**
    - Find concepts worth linking directly
    - Discover indirect relationships
    - Suggest new knowledge connections

    **Parameters:**
    - **concept**: The concept to find novel connections for
    - **max_hops**: Maximum path length to explore (1-3)

    **Example:**
    ```json
    POST /v1/insights/novel
    {
      "concept": "consciousness",
      "max_hops": 2
    }
    ```
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.afind_novel_connections(
            concept=request.concept,
            max_hops=request.max_hops
        )

        return NovelConnectionsResponse(
            success=result.get("success", False),
            concept=result.get("concept", request.concept),
            max_hops=result.get("max_hops", request.max_hops),
            connections=result.get("connections", []),
            total_found=result.get("total_found", 0),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Novel connections search failed: {str(e)}")


@router.get("/insights/patterns", response_model=ThinkingPatternsResponse, tags=["Insights"])
async def detect_thinking_patterns(
    limit: int = 10,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🔍 **THINKING PATTERNS** - Detect patterns in your own thinking.

    Analyzes concept co-occurrences to find patterns like:
    - "When I discuss X, I also mention Y"
    - "I frequently connect these topics"
    - "My thinking on A is focused/exploratory"

    **Parameters:**
    - **limit**: Maximum number of patterns to return (default: 10)

    **Example:**
    ```
    GET /v1/insights/patterns?limit=10
    ```
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.adetect_thinking_patterns(limit=limit)

        return ThinkingPatternsResponse(
            success=result.get("success", False),
            patterns=result.get("patterns", []),
            frequent_associations=result.get("frequent_associations", []),
            thinking_tendencies=result.get("thinking_tendencies", []),
            summary=result.get("summary", ""),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thinking patterns detection failed: {str(e)}")


# =============================================================================
# CONFIDENCE TRACKING ENDPOINTS
# =============================================================================

@router.post("/confidence/claim", response_model=RecordClaimResponse, tags=["Confidence"])
async def record_claim(
    request: RecordClaimRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📊 **RECORD CLAIM** - Store an assertion with confidence level.

    Track claims you make and their certainty so you can later
    verify and learn from mistakes.

    **Categories:** fact, prediction, reasoning, debugging, general

    **Example:**
    ```json
    POST /v1/confidence/claim
    {
      "claim": "The bug is in the auth module",
      "confidence": 0.8,
      "category": "debugging"
    }
    ```
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        claim_id = await memory.arecord_claim(
            claim=request.claim,
            confidence=request.confidence,
            context=request.context,
            category=request.category
        )

        return RecordClaimResponse(
            claim_id=claim_id,
            claim=request.claim,
            confidence=request.confidence,
            category=request.category or "general",
            tenant_id=tenant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record claim: {str(e)}")


@router.post("/confidence/verify", response_model=VerifyClaimResponse, tags=["Confidence"])
async def verify_claim(
    request: VerifyClaimRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    ✅ **VERIFY CLAIM** - Mark whether a previous claim was correct.

    This is how I learn from mistakes - by tracking when I was wrong
    and adjusting future confidence.

    **Example:**
    ```json
    POST /v1/confidence/verify
    {
      "claim_id": 123,
      "was_correct": true,
      "notes": "Found the bug exactly where predicted"
    }
    ```
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.averify_claim(
            claim_id=request.claim_id,
            was_correct=request.was_correct,
            notes=request.notes
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Claim not found"))

        return VerifyClaimResponse(
            success=True,
            claim_id=result["claim_id"],
            claim=result["claim"],
            original_confidence=result["original_confidence"],
            was_correct=result["was_correct"],
            feedback=result["feedback"],
            verified_at=result["verified_at"],
            tenant_id=tenant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify claim: {str(e)}")


@router.get("/confidence/calibration", response_model=CalibrationScoreResponse, tags=["Confidence"])
async def get_calibration_score(
    category: Optional[str] = None,
    days: int = 30,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📈 **CALIBRATION SCORE** - How accurate is my confidence?

    Good calibration means: when I say 80% confident, I'm right ~80% of the time.

    Returns accuracy breakdown by confidence level and improvement suggestions.

    **Example:**
    ```
    GET /v1/confidence/calibration?days=30
    ```
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.aget_calibration_score(category=category, days=days)

        return CalibrationScoreResponse(
            success=result.get("success", False),
            calibration_score=result.get("calibration_score", 0.0),
            total_verified=result.get("total_verified", 0),
            accuracy_by_confidence=result.get("accuracy_by_confidence", {}),
            overconfident_count=result.get("overconfident_count", 0),
            underconfident_count=result.get("underconfident_count", 0),
            well_calibrated_count=result.get("well_calibrated_count", 0),
            suggestions=result.get("suggestions", []),
            category=category,
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get calibration: {str(e)}")


@router.get("/confidence/history", response_model=ClaimHistoryResponse, tags=["Confidence"])
async def get_claim_history(
    category: Optional[str] = None,
    verified_only: bool = False,
    limit: int = 20,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📜 **CLAIM HISTORY** - View past claims and verification status.

    **Parameters:**
    - **category**: Filter by category
    - **verified_only**: Only show verified claims
    - **limit**: Max results (default 20)
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = memory.get_claim_history(
            category=category,
            verified_only=verified_only,
            limit=limit
        )

        return ClaimHistoryResponse(
            success=result.get("success", False),
            claims=result.get("claims", []),
            total=result.get("total", 0),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


# =============================================================================
# CONTRADICTION DETECTION ENDPOINTS
# =============================================================================

@router.post("/beliefs", response_model=RecordBeliefResponse, tags=["Contradictions"])
async def record_belief(
    request: RecordBeliefRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🎯 **RECORD BELIEF** - Store a belief and detect contradictions.

    Automatically checks for conflicts with existing beliefs in the same domain.

    **Domains:** architecture, debugging, user_preferences, technical, general

    **Example:**
    ```json
    POST /v1/beliefs
    {
      "belief": "Redis is better for this caching use case",
      "domain": "architecture",
      "confidence": 0.8
    }
    ```
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.arecord_belief(
            belief=request.belief,
            domain=request.domain,
            confidence=request.confidence,
            evidence=request.evidence
        )

        return RecordBeliefResponse(
            success=result.get("success", False),
            belief_id=result.get("belief_id"),
            contradictions=result.get("contradictions", []),
            related_beliefs=result.get("related_beliefs", []),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record belief: {str(e)}")


@router.get("/beliefs", response_model=BeliefsResponse, tags=["Contradictions"])
async def get_beliefs(
    domain: Optional[str] = None,
    active_only: bool = True,
    limit: int = 20,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📚 **GET BELIEFS** - List recorded beliefs.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = memory.get_beliefs(domain=domain, active_only=active_only, limit=limit)

        return BeliefsResponse(
            success=result.get("success", False),
            beliefs=result.get("beliefs", []),
            total=result.get("total", 0),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get beliefs: {str(e)}")


@router.get("/contradictions", response_model=ContradictionsResponse, tags=["Contradictions"])
async def get_contradictions(
    domain: Optional[str] = None,
    unresolved_only: bool = True,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    ⚠️ **GET CONTRADICTIONS** - List detected contradictions.

    Returns pairs of beliefs that conflict with each other.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.aget_contradictions(domain=domain, unresolved_only=unresolved_only)

        return ContradictionsResponse(
            success=result.get("success", False),
            contradictions=result.get("contradictions", []),
            total=result.get("total", 0),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contradictions: {str(e)}")


@router.post("/contradictions/resolve", response_model=ResolveContradictionResponse, tags=["Contradictions"])
async def resolve_contradiction(
    request: ResolveContradictionRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    ✅ **RESOLVE CONTRADICTION** - Mark a contradiction as resolved.

    Optionally specify which belief to keep (the other becomes superseded).
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.aresolve_contradiction(
            contradiction_id=request.contradiction_id,
            resolution=request.resolution,
            keep_belief_id=request.keep_belief_id
        )

        return ResolveContradictionResponse(
            success=result.get("success", False),
            resolution=result.get("resolution"),
            kept_belief_id=result.get("kept_belief_id"),
            superseded_belief_id=result.get("superseded_belief_id"),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve: {str(e)}")


# =============================================================================
# META-COGNITIVE PATTERNS ENDPOINTS
# =============================================================================

@router.post("/cognitive/patterns", response_model=RecordCognitivePatternResponse, tags=["Meta-Cognition"])
async def record_cognitive_pattern(
    request: RecordCognitivePatternRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🧠 **RECORD COGNITIVE PATTERN** - Track a pattern in your own thinking.

    Use this when you notice a recurring tendency in your reasoning:
    - "I tend to overthink authentication problems"
    - "I jump to conclusions about database schemas"
    - "I underestimate testing complexity"

    **Categories:** analysis_bias, estimation_error, topic_preference,
                   reasoning_style, complexity_bias, caution_tendency

    **Severity:** observation, concern, strength (positive patterns)
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.arecord_cognitive_pattern(
            pattern=request.pattern,
            category=request.category,
            context=request.context,
            thinking_excerpt=request.thinking_excerpt,
            severity=request.severity
        )

        return RecordCognitivePatternResponse(
            success=result.get("success", False),
            pattern_id=result.get("pattern_id"),
            instance_id=result.get("instance_id"),
            frequency=result.get("frequency", 1),
            is_new=result.get("is_new", True),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record pattern: {str(e)}")


@router.get("/cognitive/patterns", response_model=CognitivePatternsResponse, tags=["Meta-Cognition"])
async def get_cognitive_patterns(
    category: Optional[str] = None,
    min_frequency: int = 1,
    limit: int = 20,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    📋 **GET COGNITIVE PATTERNS** - List recorded thinking patterns.

    Returns patterns you've recorded with their frequencies and recent instances.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.aget_cognitive_patterns(
            category=category,
            min_frequency=min_frequency,
            limit=limit
        )

        return CognitivePatternsResponse(
            success=result.get("success", False),
            patterns=result.get("patterns", []),
            total=result.get("total", 0),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@router.get("/cognitive/detect", response_model=DetectCognitivePatternsResponse, tags=["Meta-Cognition"])
async def detect_cognitive_patterns(
    days: int = 30,
    min_frequency: int = 2,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🔍 **DETECT COGNITIVE PATTERNS** - Auto-detect patterns in thinking blocks.

    Analyzes your self-reflection/thinking blocks to find recurring themes,
    biases, and tendencies in your reasoning.

    **Returns:**
    - patterns_found: Detected patterns with examples
    - topic_tendencies: Topics you frequently think about
    - potential_biases: Identified biases with recommendations
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.adetect_cognitive_patterns(days=days, min_frequency=min_frequency)

        return DetectCognitivePatternsResponse(
            success=result.get("success", False),
            patterns_found=result.get("patterns_found", []),
            topic_tendencies=result.get("topic_tendencies", []),
            potential_biases=result.get("potential_biases", []),
            thinking_blocks_analyzed=result.get("thinking_blocks_analyzed", 0),
            period_days=result.get("period_days", days),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect patterns: {str(e)}")


@router.get("/cognitive/profile", response_model=CognitiveProfileResponse, tags=["Meta-Cognition"])
async def get_cognitive_profile(
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    🎯 **COGNITIVE PROFILE** - Comprehensive view of thinking habits.

    Generates a profile combining:
    - Strengths: Positive patterns you've identified
    - Growth areas: Concerns you've tracked
    - Tendencies: Observations about your reasoning style
    - Dominant categories: Types of patterns you notice most

    π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)
        result = await memory.aget_cognitive_profile()

        return CognitiveProfileResponse(
            success=result.get("success", False),
            profile=result.get("profile", {}),
            pattern_summary=result.get("pattern_summary", {}),
            total_patterns=result.get("total_patterns", 0),
            total_instances=result.get("total_instances", 0),
            tenant_id=tenant_id,
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
