# CONTINUUM Supabase Setup Guide

This directory contains the complete Supabase configuration for CONTINUUM's database and authentication layer.

## Overview

CONTINUUM uses Supabase to provide:
- **PostgreSQL database** with pgvector extension for semantic search
- **Row Level Security (RLS)** for multi-tenant data isolation
- **Built-in authentication** with JWT tokens
- **Real-time subscriptions** for live updates
- **Federation support** for cross-instance synchronization

## Architecture

### Database Schema

The schema consists of 8 main tables:

1. **users** - User profiles extending Supabase auth
2. **memories** - Core memory storage with vector embeddings
3. **concepts** - Knowledge graph nodes
4. **edges** - Knowledge graph relationships
5. **sessions** - Conversation/interaction sessions
6. **sync_events** - Federation synchronization queue
7. **memory_concepts** - Many-to-many associations
8. **api_keys** - API keys for external integrations

### Key Features

- **Vector Embeddings**: 1536-dimensional vectors (OpenAI ada-002 compatible)
- **HNSW Indexes**: Fast approximate nearest neighbor search
- **Knowledge Graph**: Concepts connected by weighted edges
- **Soft Deletes**: Memories marked as deleted, not immediately removed
- **Access Tracking**: Automatic tracking of memory access patterns
- **Federation**: Cross-instance sync via event queue

## Prerequisites

1. **Supabase Account** (or self-hosted instance)
   ```bash
   # Sign up at https://supabase.com
   ```

2. **Supabase CLI**
   ```bash
   # Install via npm
   npm install -g supabase

   # Or via Homebrew (macOS)
   brew install supabase/tap/supabase
   ```

3. **PostgreSQL 15+** with pgvector extension (handled by Supabase)

## Quick Start

### Option 1: Cloud Supabase (Recommended)

1. **Create a new project** at https://app.supabase.com

2. **Get your project credentials**:
   - Project URL: `https://your-project.supabase.co`
   - Anon/Public Key: From Settings > API
   - Service Role Key: From Settings > API (keep secure!)

3. **Link your local setup**:
   ```bash
   cd /var/home/alexandergcasavant/Projects/continuum/deploy/supabase
   supabase link --project-ref your-project-ref
   ```

4. **Run migrations**:
   ```bash
   supabase db push
   ```

5. **Seed database** (optional):
   ```bash
   psql "postgresql://postgres:[YOUR-PASSWORD]@db.your-project.supabase.co:5432/postgres" \
     -f seed.sql
   ```

### Option 2: Local Development

1. **Initialize Supabase locally**:
   ```bash
   cd /var/home/alexandergcasavant/Projects/continuum/deploy/supabase
   supabase init
   ```

2. **Start local Supabase**:
   ```bash
   supabase start
   ```

   This will output:
   - API URL: http://localhost:54321
   - DB URL: postgresql://postgres:postgres@localhost:54322/postgres
   - Studio URL: http://localhost:54323

3. **Run migrations**:
   ```bash
   supabase db reset
   ```

4. **Access Supabase Studio**:
   Open http://localhost:54323 to view your database

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Optional: Instance ID for federation
CONTINUUM_INSTANCE_ID=instance-1
```

### Python Client Setup

The Python client is located at `continuum/storage/supabase_client.py`.

Install dependencies:
```bash
pip install supabase-py python-dotenv
```

Usage example:
```python
from continuum.storage.supabase_client import SupabaseClient

# Initialize client
client = SupabaseClient()

# Create a memory
memory = await client.create_memory(
    user_id="...",
    content="Example memory",
    embedding=[0.1, 0.2, ...],  # 1536-dimensional vector
    memory_type="episodic",
    importance=0.8
)

# Semantic search
results = await client.semantic_search(
    query_embedding=[0.1, 0.2, ...],
    limit=10,
    threshold=0.7
)

# Get related concepts
concepts = await client.get_related_concepts(
    concept_id="...",
    max_depth=2
)
```

## Database Functions

### Semantic Search

```sql
-- Search memories
SELECT * FROM semantic_search(
    '[0.1, 0.2, ...]'::vector(1536),  -- query embedding
    'user-id'::uuid,                   -- user_id (NULL for all)
    10,                                -- limit
    0.7                                -- similarity threshold
);

-- Search concepts
SELECT * FROM search_concepts(
    '[0.1, 0.2, ...]'::vector(1536),
    'user-id'::uuid,
    10,
    0.7
);

-- Hybrid search (semantic + metadata filters)
SELECT * FROM hybrid_memory_search(
    '[0.1, 0.2, ...]'::vector(1536),
    'user-id'::uuid,
    ARRAY['episodic', 'semantic'],    -- memory types
    0.5,                               -- min importance
    '{"tag": "work"}'::jsonb,         -- metadata filter
    10,
    0.7
);
```

### Knowledge Graph Traversal

```sql
-- Get related concepts (up to 2 hops)
SELECT * FROM get_related_concepts(
    'concept-id'::uuid,
    2,    -- max depth
    0.3   -- min edge weight
);

-- Get direct neighbors
SELECT * FROM get_concept_neighbors(
    'concept-id'::uuid,
    ARRAY['relates_to', 'part_of']  -- relationship types (NULL for all)
);
```

### Memory Management

```sql
-- Merge memories
SELECT merge_memories(
    ARRAY['memory-id-1', 'memory-id-2']::uuid[],
    'user-id'::uuid,
    'Merged content here',
    '[0.1, 0.2, ...]'::vector(1536)  -- new embedding
);

-- Get session memories
SELECT * FROM get_session_memories(
    'session-id'::uuid,
    ARRAY['episodic'],  -- memory types (NULL for all)
    0.5                 -- min importance
);
```

### Federation

```sql
-- Queue memories for sync
SELECT sync_to_federation(
    ARRAY['memory-id-1', 'memory-id-2']::uuid[],
    'target-instance-id'  -- NULL for broadcast
);

-- Process pending sync events (service role only)
SELECT process_sync_events(100);  -- batch size
```

### Statistics

```sql
-- Get user stats
SELECT * FROM get_user_stats('user-id'::uuid);

-- Get popular memories
SELECT * FROM get_popular_memories('user-id'::uuid, 10);
```

## Row Level Security

All tables have RLS enabled. Policies ensure:

1. **Users can only access their own data**
   - Memories, concepts, edges, sessions are user-scoped
   - System concepts (user_id IS NULL) are readable by all

2. **Federation role** has special permissions
   - Can read memories for sync
   - Can create sync events
   - Can manage system concepts

3. **Service role** bypasses all restrictions
   - Used for admin operations
   - Required for maintenance functions

### Role Hierarchy

```
service_role (full access)
    ↓
federation (cross-instance sync)
    ↓
authenticated (user data access)
    ↓
anon (public access - minimal)
```

## Indexes and Performance

### Vector Indexes

Uses HNSW (Hierarchical Navigable Small World) for fast approximate search:

```sql
-- Memories embedding index
CREATE INDEX idx_memories_embedding ON memories
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Concepts embedding index
CREATE INDEX idx_concepts_embedding ON concepts
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

Parameters:
- `m = 16`: Number of connections per layer (higher = better recall, slower build)
- `ef_construction = 64`: Size of dynamic candidate list (higher = better quality, slower build)

### B-tree Indexes

Standard indexes for:
- User ID lookups
- Timestamp sorting
- Metadata filtering
- Session associations

### GIN Indexes

For JSONB metadata search:
```sql
CREATE INDEX idx_memories_metadata ON memories USING GIN (metadata);
CREATE INDEX idx_concepts_metadata ON concepts USING GIN (metadata);
```

## Maintenance

### Cleanup Deleted Memories

Hard delete soft-deleted memories after 30 days:
```sql
SELECT cleanup_deleted_memories(30);  -- retention days
```

### Rebuild Vector Indexes

If search performance degrades:
```sql
SELECT rebuild_vector_indexes();
```

### Update Access Counts

Update concept access counts based on associations:
```sql
SELECT update_concept_access_counts();
```

### Vacuum and Analyze

Regular PostgreSQL maintenance:
```bash
# Via Supabase CLI
supabase db remote exec "VACUUM ANALYZE;"
```

## Migration Management

### Create a New Migration

```bash
supabase migration new your_migration_name
```

### Apply Migrations

```bash
# Local
supabase db reset

# Remote
supabase db push
```

### Rollback

```bash
# Reset to specific migration
supabase db reset --version 20231201000000
```

## Monitoring

### Supabase Studio

Access at http://localhost:54323 (local) or via cloud dashboard.

Features:
- Table editor
- SQL editor
- Database schema visualization
- API documentation
- Auth user management

### Query Performance

Check slow queries:
```sql
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%public.memories%'
ORDER BY mean_time DESC
LIMIT 10;
```

### Vector Search Performance

```sql
EXPLAIN ANALYZE
SELECT * FROM semantic_search(
    '[0.1, 0.2, ...]'::vector(1536),
    NULL,
    10,
    0.7
);
```

## Troubleshooting

### pgvector Extension Not Found

```sql
-- Enable in SQL editor
CREATE EXTENSION IF NOT EXISTS vector;
```

### RLS Policy Errors

Check if RLS is enabled:
```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

### Slow Vector Search

1. Verify HNSW index exists:
   ```sql
   \di+ idx_memories_embedding
   ```

2. Increase `ef_search` for better recall (slower):
   ```sql
   SET hnsw.ef_search = 100;  -- default: 40
   ```

3. Check index parameters:
   ```sql
   SELECT * FROM pg_indexes
   WHERE indexname LIKE '%embedding%';
   ```

### Connection Issues

```bash
# Check Supabase status
supabase status

# Restart local instance
supabase stop
supabase start
```

## Security Best Practices

1. **Never expose service role key** in client-side code
2. **Use RLS policies** for all data access
3. **Rotate API keys** regularly
4. **Enable MFA** for Supabase dashboard access
5. **Monitor auth.users** for suspicious activity
6. **Use prepared statements** to prevent SQL injection
7. **Validate embeddings** before inserting (1536 dimensions)

## Federation Setup

For cross-instance synchronization:

1. **Create federation API key**:
   ```sql
   INSERT INTO public.api_keys (user_id, name, permissions, rate_limit)
   VALUES (
       NULL,  -- system key
       'federation-sync',
       '{"read": true, "write": true, "federation": true}',
       1000
   );
   ```

2. **Configure instance ID**:
   ```sql
   -- Set in PostgreSQL
   ALTER DATABASE postgres SET app.instance_id = 'instance-1';
   ```

3. **Run sync worker**:
   ```python
   from continuum.coordination.federation import FederationSync

   sync = FederationSync(instance_id='instance-1')
   await sync.run()
   ```

## Production Checklist

- [ ] Enable RLS on all tables
- [ ] Configure backup schedule (Supabase dashboard)
- [ ] Set up monitoring and alerts
- [ ] Enable connection pooling
- [ ] Configure rate limiting
- [ ] Set up point-in-time recovery
- [ ] Document disaster recovery plan
- [ ] Test federation sync
- [ ] Benchmark vector search performance
- [ ] Set up log aggregation
- [ ] Configure SSL/TLS certificates
- [ ] Enable audit logging for sensitive operations

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [CONTINUUM Architecture](../../docs/ARCHITECTURE.md)

## Support

For issues specific to CONTINUUM's Supabase setup:
1. Check logs: `supabase logs`
2. Review migrations: `supabase db remote list-tables`
3. Test connectivity: `supabase db test`

For Supabase platform issues:
- [Supabase GitHub](https://github.com/supabase/supabase)
- [Supabase Discord](https://discord.supabase.com)
