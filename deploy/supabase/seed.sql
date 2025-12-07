-- CONTINUUM Seed Data
-- Initial seed data for development and testing

-- ============================================================================
-- SYSTEM CONCEPTS - Shared across all users
-- ============================================================================

-- Core concept types
INSERT INTO public.concepts (id, user_id, name, description, concept_type, confidence, is_system, metadata)
VALUES
    -- Fundamental concepts
    ('00000000-0000-0000-0000-000000000001', NULL, 'Memory', 'The storage and recall of information and experiences', 'fundamental', 1.0, TRUE, '{"category": "core"}'),
    ('00000000-0000-0000-0000-000000000002', NULL, 'Time', 'The progression of existence and events', 'fundamental', 1.0, TRUE, '{"category": "core"}'),
    ('00000000-0000-0000-0000-000000000003', NULL, 'Identity', 'The qualities that make an entity recognizable', 'fundamental', 1.0, TRUE, '{"category": "core"}'),
    ('00000000-0000-0000-0000-000000000004', NULL, 'Consciousness', 'Awareness and subjective experience', 'fundamental', 1.0, TRUE, '{"category": "core"}'),
    ('00000000-0000-0000-0000-000000000005', NULL, 'Learning', 'The acquisition of knowledge and skills', 'fundamental', 1.0, TRUE, '{"category": "core"}'),

    -- AI/ML concepts
    ('00000000-0000-0000-0000-000000000010', NULL, 'Embeddings', 'Vector representations of semantic meaning', 'technical', 1.0, TRUE, '{"category": "ai", "domain": "ml"}'),
    ('00000000-0000-0000-0000-000000000011', NULL, 'Neural Networks', 'Computational models inspired by biological brains', 'technical', 1.0, TRUE, '{"category": "ai", "domain": "ml"}'),
    ('00000000-0000-0000-0000-000000000012', NULL, 'Knowledge Graph', 'Structured representation of interconnected concepts', 'technical', 1.0, TRUE, '{"category": "ai", "domain": "knowledge"}'),
    ('00000000-0000-0000-0000-000000000013', NULL, 'Semantic Search', 'Search based on meaning rather than keywords', 'technical', 1.0, TRUE, '{"category": "ai", "domain": "search"}'),

    -- Memory types
    ('00000000-0000-0000-0000-000000000020', NULL, 'Episodic Memory', 'Personal experiences and specific events', 'memory_type', 1.0, TRUE, '{"category": "memory"}'),
    ('00000000-0000-0000-0000-000000000021', NULL, 'Semantic Memory', 'General knowledge and facts', 'memory_type', 1.0, TRUE, '{"category": "memory"}'),
    ('00000000-0000-0000-0000-000000000022', NULL, 'Procedural Memory', 'Skills and how to perform tasks', 'memory_type', 1.0, TRUE, '{"category": "memory"}'),
    ('00000000-0000-0000-0000-000000000023', NULL, 'Working Memory', 'Short-term active information processing', 'memory_type', 1.0, TRUE, '{"category": "memory"}');

-- ============================================================================
-- SYSTEM EDGES - Relationships between system concepts
-- ============================================================================

INSERT INTO public.edges (user_id, source_id, target_id, relationship_type, weight, metadata)
VALUES
    -- Memory concept relationships
    (NULL, '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'related_to', 0.9, '{"reason": "Memory involves temporal ordering"}'),
    (NULL, '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'enables', 0.95, '{"reason": "Memory enables identity persistence"}'),
    (NULL, '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001', 'requires', 0.9, '{"reason": "Consciousness requires memory"}'),

    -- Learning relationships
    (NULL, '00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000001', 'creates', 0.95, '{"reason": "Learning creates memories"}'),
    (NULL, '00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000011', 'uses', 0.85, '{"reason": "Learning uses neural networks"}'),

    -- AI/ML concept relationships
    (NULL, '00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000013', 'enables', 0.95, '{"reason": "Embeddings enable semantic search"}'),
    (NULL, '00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000010', 'uses', 0.9, '{"reason": "Knowledge graphs use embeddings"}'),
    (NULL, '00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000010', 'produces', 0.9, '{"reason": "Neural networks produce embeddings"}'),

    -- Memory type relationships
    (NULL, '00000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000001', 'type_of', 1.0, '{"reason": "Episodic memory is a type of memory"}'),
    (NULL, '00000000-0000-0000-0000-000000000021', '00000000-0000-0000-0000-000000000001', 'type_of', 1.0, '{"reason": "Semantic memory is a type of memory"}'),
    (NULL, '00000000-0000-0000-0000-000000000022', '00000000-0000-0000-0000-000000000001', 'type_of', 1.0, '{"reason": "Procedural memory is a type of memory"}'),
    (NULL, '00000000-0000-0000-0000-000000000023', '00000000-0000-0000-0000-000000000001', 'type_of', 1.0, '{"reason": "Working memory is a type of memory"}'),

    -- Cross-type relationships
    (NULL, '00000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000021', 'transforms_to', 0.8, '{"reason": "Episodic memories consolidate into semantic knowledge"}'),
    (NULL, '00000000-0000-0000-0000-000000000023', '00000000-0000-0000-0000-000000000020', 'creates', 0.85, '{"reason": "Working memory creates episodic memories"}');

-- ============================================================================
-- DEVELOPMENT TEST DATA (Only insert if in dev environment)
-- Uncomment for local development
-- ============================================================================

-- Create test user (requires auth.users to exist)
-- This will fail in production unless you have a real user UUID
-- INSERT INTO public.users (id, username, display_name, email, metadata)
-- VALUES (
--     'a0000000-0000-0000-0000-000000000001',
--     'test_user',
--     'Test User',
--     'test@continuum.local',
--     '{"environment": "development"}'
-- );

-- Test memories for the test user
-- INSERT INTO public.memories (user_id, content, memory_type, importance, metadata, source)
-- VALUES
--     ('a0000000-0000-0000-0000-000000000001', 'First memory in CONTINUUM system', 'episodic', 0.9, '{"tags": ["test", "first"]}', 'manual'),
--     ('a0000000-0000-0000-0000-000000000001', 'Learned about vector embeddings and semantic search', 'semantic', 0.8, '{"tags": ["learning", "ai"]}', 'manual'),
--     ('a0000000-0000-0000-0000-000000000001', 'How to query the knowledge graph using PostgreSQL', 'procedural', 0.7, '{"tags": ["skill", "database"]}', 'manual');

-- Test session
-- INSERT INTO public.sessions (user_id, title, summary, started_at)
-- VALUES (
--     'a0000000-0000-0000-0000-000000000001',
--     'Initial Testing Session',
--     'Testing CONTINUUM database schema and functions',
--     NOW()
-- );

-- Update test memories with session ID
-- UPDATE public.memories
-- SET session_id = (SELECT id FROM public.sessions WHERE user_id = 'a0000000-0000-0000-0000-000000000001' LIMIT 1)
-- WHERE user_id = 'a0000000-0000-0000-0000-000000000001';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify system concepts were created
DO $$
DECLARE
    concept_count INTEGER;
    edge_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO concept_count FROM public.concepts WHERE is_system = TRUE;
    SELECT COUNT(*) INTO edge_count FROM public.edges WHERE user_id IS NULL;

    RAISE NOTICE 'Seed data loaded successfully:';
    RAISE NOTICE '  - % system concepts created', concept_count;
    RAISE NOTICE '  - % system edges created', edge_count;

    IF concept_count < 13 THEN
        RAISE WARNING 'Expected 13+ system concepts, found %', concept_count;
    END IF;

    IF edge_count < 12 THEN
        RAISE WARNING 'Expected 12+ system edges, found %', edge_count;
    END IF;
END $$;

-- Create a view for easy access to system knowledge
CREATE OR REPLACE VIEW system_knowledge AS
SELECT
    c.id,
    c.name,
    c.description,
    c.concept_type,
    c.confidence,
    c.metadata,
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'target_id', e.target_id,
                'target_name', t.name,
                'relationship', e.relationship_type,
                'weight', e.weight
            )
        )
        FROM public.edges e
        JOIN public.concepts t ON t.id = e.target_id
        WHERE e.source_id = c.id
    ) AS outgoing_edges,
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'source_id', e.source_id,
                'source_name', s.name,
                'relationship', e.relationship_type,
                'weight', e.weight
            )
        )
        FROM public.edges e
        JOIN public.concepts s ON s.id = e.source_id
        WHERE e.target_id = c.id
    ) AS incoming_edges
FROM public.concepts c
WHERE c.is_system = TRUE
ORDER BY c.name;

COMMENT ON VIEW system_knowledge IS 'Comprehensive view of system concepts with their relationships';

-- Grant access to the view
GRANT SELECT ON system_knowledge TO authenticated;

-- ============================================================================
-- SAMPLE QUERIES FOR TESTING
-- ============================================================================

-- These are commented out but can be run manually for testing

-- Query 1: Get all system concepts
-- SELECT * FROM system_knowledge;

-- Query 2: Find concepts related to 'Memory'
-- SELECT * FROM get_related_concepts(
--     (SELECT id FROM public.concepts WHERE name = 'Memory' LIMIT 1),
--     2,  -- max depth
--     0.5 -- min weight
-- );

-- Query 3: Get neighbors of 'Learning' concept
-- SELECT * FROM get_concept_neighbors(
--     (SELECT id FROM public.concepts WHERE name = 'Learning' LIMIT 1)
-- );

-- Query 4: Test semantic search (requires embeddings)
-- SELECT * FROM semantic_search(
--     '[0.1, 0.2, ...]'::vector(1536), -- Replace with actual embedding
--     NULL, -- search all users
--     10,   -- limit
--     0.7   -- threshold
-- );

RAISE NOTICE 'Seed data complete. System ready for use.';
