-- CONTINUUM Initial Database Schema
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE,
    display_name TEXT,
    email TEXT UNIQUE,
    federation_id TEXT UNIQUE, -- For cross-instance identity
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Create index for fast lookups
CREATE INDEX idx_users_username ON public.users(username);
CREATE INDEX idx_users_federation_id ON public.users(federation_id);
CREATE INDEX idx_users_email ON public.users(email);

-- Memories table - core memory storage
CREATE TABLE IF NOT EXISTS public.memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 dimensionality
    memory_type TEXT NOT NULL DEFAULT 'episodic', -- episodic, semantic, procedural
    importance REAL DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    metadata JSONB DEFAULT '{}'::jsonb,
    source TEXT, -- Origin of memory (user input, inference, federation)
    session_id UUID, -- Link to session if applicable
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ
);

-- Indexes for memory search and retrieval
CREATE INDEX idx_memories_user_id ON public.memories(user_id);
CREATE INDEX idx_memories_session_id ON public.memories(session_id);
CREATE INDEX idx_memories_created_at ON public.memories(created_at DESC);
CREATE INDEX idx_memories_importance ON public.memories(importance DESC);
CREATE INDEX idx_memories_memory_type ON public.memories(memory_type);
CREATE INDEX idx_memories_is_deleted ON public.memories(is_deleted) WHERE is_deleted = FALSE;

-- Vector similarity search index (HNSW for fast approximate search)
CREATE INDEX idx_memories_embedding ON public.memories
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- GIN index for metadata search
CREATE INDEX idx_memories_metadata ON public.memories USING GIN (metadata);

-- Concepts table - knowledge graph nodes
CREATE TABLE IF NOT EXISTS public.concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE, -- NULL for shared/system concepts
    name TEXT NOT NULL,
    description TEXT,
    embedding vector(1536),
    concept_type TEXT DEFAULT 'general', -- general, person, place, idea, skill, etc.
    confidence REAL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    is_system BOOLEAN DEFAULT FALSE, -- System-wide vs user-specific
    UNIQUE(user_id, name) -- Prevent duplicate concept names per user
);

-- Indexes for concept retrieval
CREATE INDEX idx_concepts_user_id ON public.concepts(user_id);
CREATE INDEX idx_concepts_name ON public.concepts(name);
CREATE INDEX idx_concepts_concept_type ON public.concepts(concept_type);
CREATE INDEX idx_concepts_is_system ON public.concepts(is_system);

-- Vector search for concepts
CREATE INDEX idx_concepts_embedding ON public.concepts
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- GIN index for metadata
CREATE INDEX idx_concepts_metadata ON public.concepts USING GIN (metadata);

-- Edges table - knowledge graph relationships
CREATE TABLE IF NOT EXISTS public.edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES public.concepts(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES public.concepts(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL, -- relates_to, part_of, instance_of, etc.
    weight REAL DEFAULT 0.5 CHECK (weight >= 0 AND weight <= 1),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_id, target_id, relationship_type) -- Prevent duplicate edges
);

-- Indexes for graph traversal
CREATE INDEX idx_edges_source_id ON public.edges(source_id);
CREATE INDEX idx_edges_target_id ON public.edges(target_id);
CREATE INDEX idx_edges_relationship_type ON public.edges(relationship_type);
CREATE INDEX idx_edges_weight ON public.edges(weight DESC);
CREATE INDEX idx_edges_user_id ON public.edges(user_id);

-- Composite index for common queries
CREATE INDEX idx_edges_source_relationship ON public.edges(source_id, relationship_type);
CREATE INDEX idx_edges_target_relationship ON public.edges(target_id, relationship_type);

-- Sessions table - conversation/interaction sessions
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT,
    summary TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    memory_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for session queries
CREATE INDEX idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX idx_sessions_started_at ON public.sessions(started_at DESC);
CREATE INDEX idx_sessions_is_active ON public.sessions(is_active) WHERE is_active = TRUE;

-- Add foreign key to memories for session linkage
ALTER TABLE public.memories
ADD CONSTRAINT fk_memories_session
FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON DELETE SET NULL;

-- Sync events table - federation and cross-instance synchronization
CREATE TABLE IF NOT EXISTS public.sync_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- memory_created, memory_updated, concept_created, etc.
    entity_type TEXT NOT NULL, -- memory, concept, edge, session
    entity_id UUID NOT NULL,
    payload JSONB NOT NULL,
    source_instance TEXT, -- Instance that generated the event
    target_instance TEXT, -- Instance receiving the event (NULL for broadcast)
    status TEXT DEFAULT 'pending', -- pending, synced, failed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    synced_at TIMESTAMPTZ,
    error_message TEXT
);

-- Indexes for sync queries
CREATE INDEX idx_sync_events_user_id ON public.sync_events(user_id);
CREATE INDEX idx_sync_events_status ON public.sync_events(status);
CREATE INDEX idx_sync_events_created_at ON public.sync_events(created_at DESC);
CREATE INDEX idx_sync_events_entity ON public.sync_events(entity_type, entity_id);
CREATE INDEX idx_sync_events_source ON public.sync_events(source_instance);
CREATE INDEX idx_sync_events_target ON public.sync_events(target_instance);

-- Memory-Concept associations (many-to-many)
CREATE TABLE IF NOT EXISTS public.memory_concepts (
    memory_id UUID NOT NULL REFERENCES public.memories(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES public.concepts(id) ON DELETE CASCADE,
    relevance REAL DEFAULT 0.5 CHECK (relevance >= 0 AND relevance <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (memory_id, concept_id)
);

-- Indexes for association queries
CREATE INDEX idx_memory_concepts_memory ON public.memory_concepts(memory_id);
CREATE INDEX idx_memory_concepts_concept ON public.memory_concepts(concept_id);
CREATE INDEX idx_memory_concepts_relevance ON public.memory_concepts(relevance DESC);

-- API keys table - for external integrations and federation auth
CREATE TABLE IF NOT EXISTS public.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE, -- bcrypt hash of the API key
    name TEXT NOT NULL,
    permissions JSONB DEFAULT '{"read": true, "write": false}'::jsonb,
    rate_limit INTEGER DEFAULT 100, -- requests per minute
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for API key lookups
CREATE INDEX idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON public.api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON public.api_keys(is_active) WHERE is_active = TRUE;

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers to all relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON public.memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON public.concepts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_edges_updated_at BEFORE UPDATE ON public.edges
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Access tracking trigger for memories
CREATE OR REPLACE FUNCTION track_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    NEW.accessed_at = NOW();
    NEW.access_count = COALESCE(OLD.access_count, 0) + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: This trigger only fires on UPDATE, not SELECT
-- For SELECT tracking, use application-level logic
CREATE TRIGGER track_memory_access_trigger BEFORE UPDATE ON public.memories
    FOR EACH ROW EXECUTE FUNCTION track_memory_access();

-- Session memory counter trigger
CREATE OR REPLACE FUNCTION update_session_memory_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE public.sessions
        SET memory_count = memory_count + 1
        WHERE id = NEW.session_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE public.sessions
        SET memory_count = memory_count - 1
        WHERE id = OLD.session_id AND memory_count > 0;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_memory_count_trigger
AFTER INSERT OR DELETE ON public.memories
FOR EACH ROW EXECUTE FUNCTION update_session_memory_count();

-- Comments for documentation
COMMENT ON TABLE public.users IS 'User accounts extending Supabase auth';
COMMENT ON TABLE public.memories IS 'Core memory storage with vector embeddings';
COMMENT ON TABLE public.concepts IS 'Knowledge graph nodes representing concepts';
COMMENT ON TABLE public.edges IS 'Knowledge graph relationships between concepts';
COMMENT ON TABLE public.sessions IS 'Conversation/interaction sessions';
COMMENT ON TABLE public.sync_events IS 'Federation synchronization events';
COMMENT ON TABLE public.memory_concepts IS 'Many-to-many associations between memories and concepts';
COMMENT ON TABLE public.api_keys IS 'API keys for external integrations';

COMMENT ON COLUMN public.memories.embedding IS 'Vector embedding for semantic search (1536 dimensions for OpenAI ada-002)';
COMMENT ON COLUMN public.memories.importance IS 'Memory importance score (0-1) for prioritization';
COMMENT ON COLUMN public.concepts.confidence IS 'Confidence in concept extraction/definition (0-1)';
COMMENT ON COLUMN public.edges.weight IS 'Relationship strength (0-1)';
