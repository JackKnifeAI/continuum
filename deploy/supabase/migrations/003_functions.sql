-- CONTINUUM PostgreSQL Functions
-- ============================================================================
-- SEMANTIC SEARCH FUNCTIONS
-- ============================================================================

-- Semantic search for memories using vector similarity
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding vector(1536),
    search_user_id UUID DEFAULT NULL,
    result_limit INTEGER DEFAULT 10,
    similarity_threshold REAL DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    similarity REAL,
    importance REAL,
    memory_type TEXT,
    created_at TIMESTAMPTZ,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.content,
        1 - (m.embedding <=> query_embedding) AS similarity,
        m.importance,
        m.memory_type,
        m.created_at,
        m.metadata
    FROM public.memories m
    WHERE
        m.is_deleted = FALSE
        AND (search_user_id IS NULL OR m.user_id = search_user_id)
        AND m.embedding IS NOT NULL
        AND (1 - (m.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Semantic search for concepts
CREATE OR REPLACE FUNCTION search_concepts(
    query_embedding vector(1536),
    search_user_id UUID DEFAULT NULL,
    result_limit INTEGER DEFAULT 10,
    similarity_threshold REAL DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    similarity REAL,
    confidence REAL,
    concept_type TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.description,
        1 - (c.embedding <=> query_embedding) AS similarity,
        c.confidence,
        c.concept_type,
        c.metadata
    FROM public.concepts c
    WHERE
        (search_user_id IS NULL OR c.user_id = search_user_id OR c.user_id IS NULL)
        AND c.embedding IS NOT NULL
        AND (1 - (c.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Hybrid search combining semantic similarity and metadata filters
CREATE OR REPLACE FUNCTION hybrid_memory_search(
    query_embedding vector(1536),
    search_user_id UUID,
    memory_types TEXT[] DEFAULT NULL,
    min_importance REAL DEFAULT 0.0,
    metadata_filter JSONB DEFAULT NULL,
    result_limit INTEGER DEFAULT 10,
    similarity_threshold REAL DEFAULT 0.5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    similarity REAL,
    importance REAL,
    memory_type TEXT,
    created_at TIMESTAMPTZ,
    metadata JSONB,
    combined_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.content,
        1 - (m.embedding <=> query_embedding) AS similarity,
        m.importance,
        m.memory_type,
        m.created_at,
        m.metadata,
        -- Combined score: weighted average of similarity and importance
        (0.7 * (1 - (m.embedding <=> query_embedding)) + 0.3 * m.importance) AS combined_score
    FROM public.memories m
    WHERE
        m.is_deleted = FALSE
        AND m.user_id = search_user_id
        AND m.embedding IS NOT NULL
        AND (1 - (m.embedding <=> query_embedding)) >= similarity_threshold
        AND m.importance >= min_importance
        AND (memory_types IS NULL OR m.memory_type = ANY(memory_types))
        AND (metadata_filter IS NULL OR m.metadata @> metadata_filter)
    ORDER BY combined_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- KNOWLEDGE GRAPH TRAVERSAL FUNCTIONS
-- ============================================================================

-- Get related concepts with specified depth
CREATE OR REPLACE FUNCTION get_related_concepts(
    concept_id UUID,
    max_depth INTEGER DEFAULT 2,
    min_weight REAL DEFAULT 0.3
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    relationship_type TEXT,
    depth INTEGER,
    path_weight REAL
) AS $$
WITH RECURSIVE concept_graph AS (
    -- Base case: direct relationships
    SELECT
        c.id,
        c.name,
        c.description,
        e.relationship_type,
        1 AS depth,
        e.weight AS path_weight,
        ARRAY[concept_id, c.id] AS path
    FROM public.edges e
    JOIN public.concepts c ON c.id = e.target_id
    WHERE e.source_id = concept_id
    AND e.weight >= min_weight

    UNION ALL

    -- Recursive case: traverse further
    SELECT
        c.id,
        c.name,
        c.description,
        e.relationship_type,
        cg.depth + 1,
        cg.path_weight * e.weight AS path_weight,
        cg.path || c.id
    FROM concept_graph cg
    JOIN public.edges e ON e.source_id = cg.id
    JOIN public.concepts c ON c.id = e.target_id
    WHERE
        cg.depth < max_depth
        AND e.weight >= min_weight
        AND NOT (c.id = ANY(cg.path)) -- Prevent cycles
)
SELECT DISTINCT ON (id)
    id,
    name,
    description,
    relationship_type,
    depth,
    path_weight
FROM concept_graph
ORDER BY id, path_weight DESC;
$$ LANGUAGE sql STABLE;

-- Get concept neighbors (both incoming and outgoing edges)
CREATE OR REPLACE FUNCTION get_concept_neighbors(
    concept_id UUID,
    relationship_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    relationship_type TEXT,
    direction TEXT,
    weight REAL
) AS $$
BEGIN
    RETURN QUERY
    -- Outgoing edges (this concept -> other concepts)
    SELECT
        c.id,
        c.name,
        c.description,
        e.relationship_type,
        'outgoing'::TEXT AS direction,
        e.weight
    FROM public.edges e
    JOIN public.concepts c ON c.id = e.target_id
    WHERE e.source_id = concept_id
    AND (relationship_types IS NULL OR e.relationship_type = ANY(relationship_types))

    UNION ALL

    -- Incoming edges (other concepts -> this concept)
    SELECT
        c.id,
        c.name,
        c.description,
        e.relationship_type,
        'incoming'::TEXT AS direction,
        e.weight
    FROM public.edges e
    JOIN public.concepts c ON c.id = e.source_id
    WHERE e.target_id = concept_id
    AND (relationship_types IS NULL OR e.relationship_type = ANY(relationship_types))

    ORDER BY weight DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- MEMORY MANAGEMENT FUNCTIONS
-- ============================================================================

-- Merge multiple memories into a single consolidated memory
CREATE OR REPLACE FUNCTION merge_memories(
    source_ids UUID[],
    target_user_id UUID,
    merged_content TEXT,
    merged_embedding vector(1536) DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    new_memory_id UUID;
    avg_importance REAL;
    merged_metadata JSONB;
BEGIN
    -- Calculate average importance
    SELECT AVG(importance) INTO avg_importance
    FROM public.memories
    WHERE id = ANY(source_ids)
    AND user_id = target_user_id;

    -- Merge metadata (combine all metadata fields)
    SELECT jsonb_object_agg(key, value) INTO merged_metadata
    FROM (
        SELECT key, jsonb_agg(DISTINCT value) as value
        FROM public.memories, jsonb_each(metadata)
        WHERE id = ANY(source_ids)
        AND user_id = target_user_id
        GROUP BY key
    ) subquery;

    -- Create new merged memory
    INSERT INTO public.memories (
        user_id,
        content,
        embedding,
        memory_type,
        importance,
        metadata,
        source
    ) VALUES (
        target_user_id,
        merged_content,
        merged_embedding,
        'semantic', -- Merged memories become semantic
        avg_importance,
        merged_metadata,
        'merge'
    ) RETURNING id INTO new_memory_id;

    -- Soft delete source memories
    UPDATE public.memories
    SET
        is_deleted = TRUE,
        deleted_at = NOW(),
        metadata = metadata || jsonb_build_object('merged_into', new_memory_id)
    WHERE id = ANY(source_ids)
    AND user_id = target_user_id;

    RETURN new_memory_id;
END;
$$ LANGUAGE plpgsql;

-- Get memories for a session with optional filters
CREATE OR REPLACE FUNCTION get_session_memories(
    session_id UUID,
    memory_types TEXT[] DEFAULT NULL,
    min_importance REAL DEFAULT 0.0
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    memory_type TEXT,
    importance REAL,
    created_at TIMESTAMPTZ,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.content,
        m.memory_type,
        m.importance,
        m.created_at,
        m.metadata
    FROM public.memories m
    WHERE
        m.session_id = get_session_memories.session_id
        AND m.is_deleted = FALSE
        AND (memory_types IS NULL OR m.memory_type = ANY(memory_types))
        AND m.importance >= min_importance
    ORDER BY m.created_at ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FEDERATION SYNC FUNCTIONS
-- ============================================================================

-- Queue memories for federation sync
CREATE OR REPLACE FUNCTION sync_to_federation(
    memory_ids UUID[],
    target_instance TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    sync_count INTEGER := 0;
    memory_record RECORD;
BEGIN
    FOR memory_record IN
        SELECT * FROM public.memories
        WHERE id = ANY(memory_ids)
        AND is_deleted = FALSE
    LOOP
        INSERT INTO public.sync_events (
            user_id,
            event_type,
            entity_type,
            entity_id,
            payload,
            source_instance,
            target_instance,
            status
        ) VALUES (
            memory_record.user_id,
            'memory_created',
            'memory',
            memory_record.id,
            row_to_json(memory_record)::jsonb,
            current_setting('app.instance_id', true),
            target_instance,
            'pending'
        );
        sync_count := sync_count + 1;
    END LOOP;

    RETURN sync_count;
END;
$$ LANGUAGE plpgsql;

-- Process pending sync events
CREATE OR REPLACE FUNCTION process_sync_events(
    batch_size INTEGER DEFAULT 100
)
RETURNS INTEGER AS $$
DECLARE
    processed_count INTEGER := 0;
BEGIN
    UPDATE public.sync_events
    SET
        status = 'synced',
        synced_at = NOW()
    WHERE id IN (
        SELECT id FROM public.sync_events
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT batch_size
    );

    GET DIAGNOSTICS processed_count = ROW_COUNT;
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STATISTICS AND ANALYTICS FUNCTIONS
-- ============================================================================

-- Get user memory statistics
CREATE OR REPLACE FUNCTION get_user_stats(user_id UUID)
RETURNS TABLE (
    total_memories BIGINT,
    total_concepts BIGINT,
    total_edges BIGINT,
    total_sessions BIGINT,
    avg_importance REAL,
    memory_type_distribution JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM public.memories WHERE memories.user_id = get_user_stats.user_id AND is_deleted = FALSE),
        (SELECT COUNT(*) FROM public.concepts WHERE concepts.user_id = get_user_stats.user_id),
        (SELECT COUNT(*) FROM public.edges WHERE edges.user_id = get_user_stats.user_id),
        (SELECT COUNT(*) FROM public.sessions WHERE sessions.user_id = get_user_stats.user_id),
        (SELECT AVG(importance) FROM public.memories WHERE memories.user_id = get_user_stats.user_id AND is_deleted = FALSE),
        (
            SELECT jsonb_object_agg(memory_type, count)
            FROM (
                SELECT memory_type, COUNT(*) as count
                FROM public.memories
                WHERE memories.user_id = get_user_stats.user_id AND is_deleted = FALSE
                GROUP BY memory_type
            ) type_counts
        );
END;
$$ LANGUAGE plpgsql STABLE;

-- Get most accessed memories
CREATE OR REPLACE FUNCTION get_popular_memories(
    search_user_id UUID,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    access_count INTEGER,
    importance REAL,
    last_accessed TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.content,
        m.access_count,
        m.importance,
        m.accessed_at
    FROM public.memories m
    WHERE
        m.user_id = search_user_id
        AND m.is_deleted = FALSE
    ORDER BY m.access_count DESC, m.accessed_at DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- MAINTENANCE FUNCTIONS
-- ============================================================================

-- Clean up old deleted memories (hard delete after retention period)
CREATE OR REPLACE FUNCTION cleanup_deleted_memories(
    retention_days INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.memories
    WHERE
        is_deleted = TRUE
        AND deleted_at < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Rebuild vector indexes (for maintenance)
CREATE OR REPLACE FUNCTION rebuild_vector_indexes()
RETURNS VOID AS $$
BEGIN
    -- Reindex memories embedding
    REINDEX INDEX idx_memories_embedding;

    -- Reindex concepts embedding
    REINDEX INDEX idx_concepts_embedding;

    RAISE NOTICE 'Vector indexes rebuilt successfully';
END;
$$ LANGUAGE plpgsql;

-- Update concept access counts based on memory associations
CREATE OR REPLACE FUNCTION update_concept_access_counts()
RETURNS VOID AS $$
BEGIN
    UPDATE public.concepts c
    SET access_count = (
        SELECT COUNT(DISTINCT mc.memory_id)
        FROM public.memory_concepts mc
        WHERE mc.concept_id = c.id
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant execute to authenticated users
GRANT EXECUTE ON FUNCTION semantic_search TO authenticated;
GRANT EXECUTE ON FUNCTION search_concepts TO authenticated;
GRANT EXECUTE ON FUNCTION hybrid_memory_search TO authenticated;
GRANT EXECUTE ON FUNCTION get_related_concepts TO authenticated;
GRANT EXECUTE ON FUNCTION get_concept_neighbors TO authenticated;
GRANT EXECUTE ON FUNCTION merge_memories TO authenticated;
GRANT EXECUTE ON FUNCTION get_session_memories TO authenticated;
GRANT EXECUTE ON FUNCTION sync_to_federation TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_stats TO authenticated;
GRANT EXECUTE ON FUNCTION get_popular_memories TO authenticated;

-- Grant maintenance functions to service role only
GRANT EXECUTE ON FUNCTION process_sync_events TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_deleted_memories TO service_role;
GRANT EXECUTE ON FUNCTION rebuild_vector_indexes TO service_role;
GRANT EXECUTE ON FUNCTION update_concept_access_counts TO service_role;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON FUNCTION semantic_search IS 'Search memories using vector similarity';
COMMENT ON FUNCTION search_concepts IS 'Search concepts using vector similarity';
COMMENT ON FUNCTION hybrid_memory_search IS 'Combined semantic and metadata-based memory search';
COMMENT ON FUNCTION get_related_concepts IS 'Traverse knowledge graph to find related concepts';
COMMENT ON FUNCTION get_concept_neighbors IS 'Get directly connected concepts';
COMMENT ON FUNCTION merge_memories IS 'Merge multiple memories into consolidated semantic memory';
COMMENT ON FUNCTION get_session_memories IS 'Retrieve all memories for a session';
COMMENT ON FUNCTION sync_to_federation IS 'Queue memories for cross-instance synchronization';
COMMENT ON FUNCTION process_sync_events IS 'Process pending federation sync events';
COMMENT ON FUNCTION get_user_stats IS 'Get comprehensive statistics for a user';
COMMENT ON FUNCTION get_popular_memories IS 'Get most frequently accessed memories';
COMMENT ON FUNCTION cleanup_deleted_memories IS 'Hard delete old soft-deleted memories';
COMMENT ON FUNCTION rebuild_vector_indexes IS 'Rebuild HNSW vector indexes for performance';
COMMENT ON FUNCTION update_concept_access_counts IS 'Update concept access counts based on memory associations';
