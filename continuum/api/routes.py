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
        result = await memory.alearn(
            request.user_message,
            request.ai_response,
            request.metadata
        )

        # Auto-index for semantic search (non-blocking, best-effort)
        try:
            import hashlib
            search = get_semantic_search(tenant_id)

            # Combine user + AI messages for semantic indexing
            combined_text = f"User: {request.user_message}\nAssistant: {request.ai_response}"

            # Generate unique ID
            memory_id = int(hashlib.sha256(
                f"{time.time()}:{combined_text[:50]}".encode()
            ).hexdigest()[:8], 16)

            # Index the conversation turn
            search.index_memories([{
                "id": memory_id,
                "text": combined_text,
                "metadata": request.metadata
            }])
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
