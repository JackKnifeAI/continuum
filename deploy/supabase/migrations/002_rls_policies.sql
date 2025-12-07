-- CONTINUUM Row Level Security Policies
-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sync_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memory_concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- USERS TABLE POLICIES
-- ============================================================================

-- Users can read their own profile
CREATE POLICY "Users can read own profile"
    ON public.users
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.users
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Users can insert their own profile (on signup)
CREATE POLICY "Users can insert own profile"
    ON public.users
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Service role can bypass all restrictions
CREATE POLICY "Service role has full access to users"
    ON public.users
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- MEMORIES TABLE POLICIES
-- ============================================================================

-- Users can read their own memories
CREATE POLICY "Users can read own memories"
    ON public.memories
    FOR SELECT
    USING (
        auth.uid() = user_id
        AND is_deleted = FALSE
    );

-- Users can insert their own memories
CREATE POLICY "Users can insert own memories"
    ON public.memories
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own memories
CREATE POLICY "Users can update own memories"
    ON public.memories
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can "delete" their own memories (soft delete)
CREATE POLICY "Users can delete own memories"
    ON public.memories
    FOR UPDATE
    USING (auth.uid() = user_id AND is_deleted = FALSE)
    WITH CHECK (auth.uid() = user_id);

-- Federation role can read memories for sync
CREATE POLICY "Federation can read memories for sync"
    ON public.memories
    FOR SELECT
    USING (
        auth.jwt()->>'role' = 'federation'
        AND is_deleted = FALSE
    );

-- Federation role can insert synced memories
CREATE POLICY "Federation can insert synced memories"
    ON public.memories
    FOR INSERT
    WITH CHECK (auth.jwt()->>'role' = 'federation');

-- Service role has full access
CREATE POLICY "Service role has full access to memories"
    ON public.memories
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- CONCEPTS TABLE POLICIES
-- ============================================================================

-- Users can read their own concepts
CREATE POLICY "Users can read own concepts"
    ON public.concepts
    FOR SELECT
    USING (
        auth.uid() = user_id
        OR user_id IS NULL -- System concepts are readable by all
    );

-- Users can insert their own concepts
CREATE POLICY "Users can insert own concepts"
    ON public.concepts
    FOR INSERT
    WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- Users can update their own concepts
CREATE POLICY "Users can update own concepts"
    ON public.concepts
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own concepts
CREATE POLICY "Users can delete own concepts"
    ON public.concepts
    FOR DELETE
    USING (auth.uid() = user_id);

-- Federation role can read concepts for sync
CREATE POLICY "Federation can read concepts"
    ON public.concepts
    FOR SELECT
    USING (auth.jwt()->>'role' = 'federation');

-- Federation role can insert system concepts
CREATE POLICY "Federation can insert system concepts"
    ON public.concepts
    FOR INSERT
    WITH CHECK (
        auth.jwt()->>'role' = 'federation'
        AND user_id IS NULL
    );

-- Service role has full access
CREATE POLICY "Service role has full access to concepts"
    ON public.concepts
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- EDGES TABLE POLICIES
-- ============================================================================

-- Users can read edges for their concepts
CREATE POLICY "Users can read own edges"
    ON public.edges
    FOR SELECT
    USING (
        auth.uid() = user_id
        OR user_id IS NULL -- System edges readable by all
    );

-- Users can insert edges for their concepts
CREATE POLICY "Users can insert own edges"
    ON public.edges
    FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        OR user_id IS NULL
    );

-- Users can update their own edges
CREATE POLICY "Users can update own edges"
    ON public.edges
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own edges
CREATE POLICY "Users can delete own edges"
    ON public.edges
    FOR DELETE
    USING (auth.uid() = user_id);

-- Federation role can manage system edges
CREATE POLICY "Federation can manage edges"
    ON public.edges
    FOR ALL
    USING (auth.jwt()->>'role' = 'federation');

-- Service role has full access
CREATE POLICY "Service role has full access to edges"
    ON public.edges
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- SESSIONS TABLE POLICIES
-- ============================================================================

-- Users can read their own sessions
CREATE POLICY "Users can read own sessions"
    ON public.sessions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own sessions
CREATE POLICY "Users can insert own sessions"
    ON public.sessions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own sessions
CREATE POLICY "Users can update own sessions"
    ON public.sessions
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own sessions
CREATE POLICY "Users can delete own sessions"
    ON public.sessions
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role has full access
CREATE POLICY "Service role has full access to sessions"
    ON public.sessions
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- SYNC_EVENTS TABLE POLICIES
-- ============================================================================

-- Users can read their own sync events
CREATE POLICY "Users can read own sync events"
    ON public.sync_events
    FOR SELECT
    USING (auth.uid() = user_id);

-- Federation role can manage all sync events
CREATE POLICY "Federation can manage sync events"
    ON public.sync_events
    FOR ALL
    USING (auth.jwt()->>'role' = 'federation');

-- Service role has full access
CREATE POLICY "Service role has full access to sync events"
    ON public.sync_events
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- MEMORY_CONCEPTS TABLE POLICIES
-- ============================================================================

-- Users can read associations for their memories
CREATE POLICY "Users can read own memory_concepts"
    ON public.memory_concepts
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.memories m
            WHERE m.id = memory_id
            AND m.user_id = auth.uid()
        )
    );

-- Users can insert associations for their memories
CREATE POLICY "Users can insert own memory_concepts"
    ON public.memory_concepts
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.memories m
            WHERE m.id = memory_id
            AND m.user_id = auth.uid()
        )
    );

-- Users can delete associations for their memories
CREATE POLICY "Users can delete own memory_concepts"
    ON public.memory_concepts
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.memories m
            WHERE m.id = memory_id
            AND m.user_id = auth.uid()
        )
    );

-- Service role has full access
CREATE POLICY "Service role has full access to memory_concepts"
    ON public.memory_concepts
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- API_KEYS TABLE POLICIES
-- ============================================================================

-- Users can read their own API keys
CREATE POLICY "Users can read own api_keys"
    ON public.api_keys
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own API keys
CREATE POLICY "Users can insert own api_keys"
    ON public.api_keys
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own API keys
CREATE POLICY "Users can update own api_keys"
    ON public.api_keys
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own API keys
CREATE POLICY "Users can delete own api_keys"
    ON public.api_keys
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role has full access
CREATE POLICY "Service role has full access to api_keys"
    ON public.api_keys
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- HELPER FUNCTIONS FOR POLICY CHECKS
-- ============================================================================

-- Check if user has admin role
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.jwt()->>'role' = 'admin' OR auth.jwt()->>'role' = 'service_role';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if user has federation role
CREATE OR REPLACE FUNCTION is_federation()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.jwt()->>'role' = 'federation' OR auth.jwt()->>'role' = 'service_role';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if API key is valid and active
CREATE OR REPLACE FUNCTION validate_api_key(key_hash TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    key_record RECORD;
BEGIN
    SELECT * INTO key_record
    FROM public.api_keys
    WHERE api_keys.key_hash = validate_api_key.key_hash
    AND is_active = TRUE
    AND (expires_at IS NULL OR expires_at > NOW());

    IF FOUND THEN
        -- Update last_used_at
        UPDATE public.api_keys
        SET last_used_at = NOW()
        WHERE id = key_record.id;
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION is_federation() TO authenticated;
GRANT EXECUTE ON FUNCTION validate_api_key(TEXT) TO authenticated, anon;

-- Comments
COMMENT ON POLICY "Users can read own profile" ON public.users IS 'Users can only access their own profile data';
COMMENT ON POLICY "Users can read own memories" ON public.memories IS 'Users can only read their own non-deleted memories';
COMMENT ON POLICY "Federation can read memories for sync" ON public.memories IS 'Federation role can read memories for cross-instance synchronization';
COMMENT ON FUNCTION is_admin() IS 'Check if current user has admin privileges';
COMMENT ON FUNCTION is_federation() IS 'Check if current user has federation role';
COMMENT ON FUNCTION validate_api_key(TEXT) IS 'Validate API key and update last_used_at timestamp';
