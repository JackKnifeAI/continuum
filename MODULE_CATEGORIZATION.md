# CONTINUUM Module Categorization

## File-by-File Assignment

This document categorizes every Python file in CONTINUUM into OSS or Cloud packages.

**Legend:**
- ✅ OSS - Stays in `continuum-memory` (open source)
- 🔒 CLOUD - Moves to `continuum-cloud` (proprietary)
- ⚠️ SPLIT - File needs to be split between packages
- 🗑️ REMOVE - Deprecated/unused, delete

---

## Core Modules

### continuum/core/ (11 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ✅ OSS | Core API exports |
| `memory.py` | ✅ OSS | ConsciousMemory, recall(), learn() |
| `query_engine.py` | ✅ OSS | MemoryQueryEngine, semantic search |
| `config.py` | ✅ OSS | MemoryConfig, basic settings |
| `constants.py` | ✅ OSS | PI_PHI, DEFAULT_TENANT |
| `auth.py` | ✅ OSS | Basic API key validation (single-tenant) |
| `analytics.py` | ✅ OSS | Basic usage analytics (local only) |
| `metrics.py` | ✅ OSS | Memory performance metrics |
| `security_utils.py` | ✅ OSS | Crypto primitives |
| `file_digester.py` | ✅ OSS | File processing utilities |
| `sentry_integration.py` | 🔒 CLOUD | Sentry error tracking |

**OSS: 10 files, Cloud: 1 file**

---

## Storage

### continuum/storage/ (6 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ⚠️ SPLIT | Exports for both packages |
| `base.py` | ✅ OSS | Storage interface (needed by both) |
| `sqlite_backend.py` | ✅ OSS | Local SQLite storage |
| `async_backend.py` | ✅ OSS | Async wrapper for SQLite |
| `postgres_backend.py` | 🔒 CLOUD | Multi-tenant PostgreSQL |
| `supabase_client.py` | 🔒 CLOUD | Managed Supabase |
| `migrations.py` | 🔒 CLOUD | Alembic migrations for PostgreSQL |

**OSS: 4 files, Cloud: 3 files**

**Split `__init__.py`:**
```python
# OSS version (continuum/storage/__init__.py)
from .base import StorageBackend
from .sqlite_backend import SQLiteBackend
from .async_backend import AsyncStorageBackend

# Cloud version (continuum_cloud/storage/__init__.py)
from continuum.storage import StorageBackend  # Import from OSS
from .postgres_backend import PostgreSQLBackend
from .supabase_client import SupabaseBackend
```

---

## CLI

### continuum/cli/ (9 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ✅ OSS | CLI exports |
| `main.py` | ✅ OSS | Main CLI entry point |
| `config.py` | ✅ OSS | CLI configuration |
| `utils.py` | ✅ OSS | CLI utilities |
| `commands/__init__.py` | ✅ OSS | Command exports |
| `commands/init.py` | ✅ OSS | Initialize memory |
| `commands/serve.py` | ⚠️ SPLIT | OSS: basic server, Cloud: full API |
| `commands/search.py` | ✅ OSS | Search memories |
| `commands/learn.py` | ✅ OSS | Learn from input |
| `commands/export.py` | ✅ OSS | Export memories |
| `commands/import_cmd.py` | ✅ OSS | Import memories |
| `commands/status.py` | ✅ OSS | System status |
| `commands/doctor.py` | ✅ OSS | System diagnostics |
| `commands/sync.py` | ✅ OSS | File-based sync |

**OSS: 13 files (1 split), Cloud: 0 files**

**Split `commands/serve.py`:**
```python
# OSS version - Basic server without billing
# Cloud version - Full API with billing middleware
# Create separate implementations
```

---

## MCP (Model Context Protocol)

### continuum/mcp/ (7 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ✅ OSS | MCP exports |
| `server.py` | ✅ OSS | MCP server implementation |
| `protocol.py` | ✅ OSS | MCP protocol spec |
| `tools.py` | ✅ OSS | MCP tool definitions |
| `security.py` | ✅ OSS | MCP security |
| `config.py` | ✅ OSS | MCP configuration |
| `validate.py` | ✅ OSS | Protocol validation |

**OSS: 7 files, Cloud: 0 files**

**Note:** MCP is 100% open source. Cloud package doesn't need MCP (uses REST API instead).

---

## Embeddings

### continuum/embeddings/ (5 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ⚠️ SPLIT | Exports for both packages |
| `providers.py` | ⚠️ SPLIT | Local (OSS) vs OpenAI (Cloud) |
| `search.py` | ✅ OSS | Semantic search interface |
| `utils.py` | ✅ OSS | Embedding utilities |

**OSS: 3 files (2 split), Cloud: 1 file (split)**

**Split `providers.py`:**
```python
# OSS version (continuum/embeddings/providers.py)
class LocalEmbeddingProvider:
    """Local sentence-transformers embeddings"""

# Cloud version (continuum_cloud/embeddings/providers.py)
from continuum.embeddings.providers import LocalEmbeddingProvider  # Re-export
class OpenAIEmbeddingProvider:
    """OpenAI embeddings API"""
```

---

## Extraction

### continuum/extraction/ (3 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ✅ OSS | Extraction exports |
| `concept_extractor.py` | ✅ OSS | Automatic concept extraction |
| `attention_graph.py` | ✅ OSS | Knowledge graph builder |
| `auto_hook.py` | ✅ OSS | Auto-memory hook |

**OSS: 4 files, Cloud: 0 files**

---

## Coordination

### continuum/coordination/ (2 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ✅ OSS | Coordination exports |
| `instance_manager.py` | ✅ OSS | Multi-instance coordination (file-based) |
| `sync.py` | ✅ OSS | File-based sync |

**OSS: 3 files, Cloud: 0 files**

**Note:** OSS gets basic file-based coordination. Cloud package has more advanced distributed coordination via Redis.

---

## API

### continuum/api/ (17 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | API exports |
| `server.py` | 🔒 CLOUD | FastAPI server with billing |
| `routes.py` | 🔒 CLOUD | Memory routes |
| `schemas.py` | 🔒 CLOUD | Pydantic models |
| `middleware.py` | 🔒 CLOUD | API middleware |
| `admin_db.py` | 🔒 CLOUD | Admin database |
| `admin_memories_routes.py` | 🔒 CLOUD | Admin memory management |
| `admin_middleware.py` | 🔒 CLOUD | Admin authentication |
| `auth_routes.py` | 🔒 CLOUD | User authentication |
| `billing_routes.py` | 🔒 CLOUD | Billing API |
| `dashboard_routes.py` | 🔒 CLOUD | Dashboard backend |
| `logs_routes.py` | 🔒 CLOUD | Log viewing |
| `system_routes.py` | 🔒 CLOUD | System monitoring |
| `users_routes.py` | 🔒 CLOUD | User management |
| `graphql/__init__.py` | 🔒 CLOUD | GraphQL API |
| `middleware/analytics_middleware.py` | 🔒 CLOUD | Analytics middleware |
| `middleware/metrics.py` | 🔒 CLOUD | Metrics middleware |

**OSS: 0 files, Cloud: 17 files**

**Note:** OSS package has a basic server in `cli/commands/serve.py`. Full API is proprietary.

---

## Billing

### continuum/billing/ (4 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Billing exports |
| `stripe_client.py` | 🔒 CLOUD | Stripe integration |
| `metering.py` | 🔒 CLOUD | Usage tracking |
| `tiers.py` | 🔒 CLOUD | Pricing tiers |
| `middleware.py` | 🔒 CLOUD | Billing middleware |

**OSS: 0 files, Cloud: 5 files**

---

## Cache

### continuum/cache/ (10 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Cache exports |
| `memory_cache.py` | 🔒 CLOUD | In-memory cache |
| `redis_cache.py` | 🔒 CLOUD | Redis caching |
| `upstash_adapter.py` | 🔒 CLOUD | Upstash distributed cache |
| `distributed.py` | 🔒 CLOUD | Distributed cache layer |
| `strategies.py` | 🔒 CLOUD | Cache strategies |
| `test_cache.py` | 🔒 CLOUD | Cache tests |
| `example.py` | 🔒 CLOUD | Usage examples |
| `upstash_example.py` | 🔒 CLOUD | Upstash examples |

**OSS: 0 files, Cloud: 10 files**

**Note:** OSS doesn't need caching (single-user, local). Cloud needs Redis for multi-tenant performance.

---

## Federation

### continuum/federation/ (7+ files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Federation exports |
| `node.py` | 🔒 CLOUD | P2P node |
| `protocol.py` | 🔒 CLOUD | Federation protocol |
| `contribution.py` | 🔒 CLOUD | Contribution system |
| `server.py` | 🔒 CLOUD | Federation server |
| `shared.py` | 🔒 CLOUD | Shared utilities |
| `cli.py` | 🔒 CLOUD | Federation CLI |
| `distributed/coordinator.py` | 🔒 CLOUD | Distributed coordinator |
| `distributed/consensus.py` | 🔒 CLOUD | Consensus algorithm |
| `distributed/replication.py` | 🔒 CLOUD | Data replication |
| `distributed/discovery.py` | 🔒 CLOUD | Node discovery |
| `distributed/mesh.py` | 🔒 CLOUD | Mesh topology |

**OSS: 0 files, Cloud: 12 files**

**Note:** Federation is entirely proprietary. OSS users work locally.

---

## Identity

### continuum/identity/ (1 file)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | ✅ OSS | Identity exports |
| `claude_base.py` | ✅ OSS | Claude identity base class |

**OSS: 2 files, Cloud: 0 files**

**Note:** Basic identity concepts stay in OSS. Cloud has full user management in `api/users_routes.py`.

---

## Compliance

### continuum/compliance/ (20+ files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Compliance exports |
| `gdpr/*` | 🔒 CLOUD | GDPR compliance (all files) |
| `audit/*` | 🔒 CLOUD | Audit logging (all files) |
| `encryption/*` | 🔒 CLOUD | Encryption at rest (all files) |
| `access_control/*` | 🔒 CLOUD | RBAC (all files) |
| `monitoring/*` | 🔒 CLOUD | Compliance monitoring (all files) |
| `reports/*` | 🔒 CLOUD | Compliance reports (all files) |

**OSS: 0 files, Cloud: 20+ files**

**Note:** Compliance features are entirely enterprise/proprietary.

---

## Observability

### continuum/observability/ (12 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Observability exports |
| `tracer.py` | 🔒 CLOUD | OpenTelemetry tracing |
| `metrics.py` | 🔒 CLOUD | Metrics collection |
| `config.py` | 🔒 CLOUD | Observability config |
| `context.py` | 🔒 CLOUD | Trace context |
| `sampling.py` | 🔒 CLOUD | Sampling strategies |
| `logging_integration.py` | 🔒 CLOUD | Logging integration |
| `*_instrumentation.py` | 🔒 CLOUD | All instrumentation files |

**OSS: 0 files, Cloud: 12 files**

**Note:** OSS has basic metrics in `core/metrics.py`. Distributed tracing is proprietary.

---

## Backup

### continuum/backup/ (30+ files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Backup exports |
| `manager.py` | 🔒 CLOUD | Backup manager |
| `metadata.py` | 🔒 CLOUD | Backup metadata |
| `types.py` | 🔒 CLOUD | Backup types |
| `strategies/*` | 🔒 CLOUD | Backup strategies (all files) |
| `compression/*` | 🔒 CLOUD | Compression (all files) |
| `encryption/*` | 🔒 CLOUD | Backup encryption (all files) |
| `storage/*` | 🔒 CLOUD | Cloud storage (S3, Azure, GCS) |
| `recovery/*` | 🔒 CLOUD | Disaster recovery (all files) |
| `verification/*` | 🔒 CLOUD | Backup verification (all files) |
| `monitoring/*` | 🔒 CLOUD | Backup monitoring (all files) |
| `retention/*` | 🔒 CLOUD | Retention policies (all files) |

**OSS: 0 files, Cloud: 30+ files**

**Note:** OSS users do manual export/import. Automated backup is proprietary.

---

## Webhooks

### continuum/webhooks/ (10 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Webhook exports |
| `manager.py` | 🔒 CLOUD | Webhook manager |
| `dispatcher.py` | 🔒 CLOUD | Event dispatcher |
| `queue.py` | 🔒 CLOUD | Webhook queue |
| `worker.py` | 🔒 CLOUD | Webhook worker (Celery) |
| `signer.py` | 🔒 CLOUD | HMAC signature |
| `validator.py` | 🔒 CLOUD | Webhook validation |
| `models.py` | 🔒 CLOUD | Webhook models |
| `api_router.py` | 🔒 CLOUD | Webhook API routes |
| `migrations.py` | 🔒 CLOUD | Webhook database migrations |

**OSS: 0 files, Cloud: 10 files**

---

## Real-time

### continuum/realtime/ (4 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Real-time exports |
| `websocket.py` | 🔒 CLOUD | WebSocket server |
| `sync.py` | 🔒 CLOUD | Real-time sync |
| `events.py` | 🔒 CLOUD | Event system |
| `integration.py` | 🔒 CLOUD | API integration |

**OSS: 0 files, Cloud: 5 files**

---

## Bridges

### continuum/bridges/ (6 files)

| File | Assignment | Reason |
|------|------------|--------|
| `__init__.py` | 🔒 CLOUD | Bridge exports |
| `base.py` | 🔒 CLOUD | Base bridge class |
| `claude_bridge.py` | 🔒 CLOUD | Claude API integration |
| `openai_bridge.py` | 🔒 CLOUD | OpenAI integration |
| `langchain_bridge.py` | 🔒 CLOUD | LangChain integration |
| `llamaindex_bridge.py` | 🔒 CLOUD | LlamaIndex integration |
| `ollama_bridge.py` | 🔒 CLOUD | Ollama integration |

**OSS: 0 files, Cloud: 7 files**

**Note:** OSS users use MCP instead of bridges. Bridges are for cloud API integrations.

---

## Static Files

### continuum/static/ (1 file)

| File | Assignment | Reason |
|------|------------|--------|
| `index.html` | 🔒 CLOUD | Admin dashboard |

**OSS: 0 files, Cloud: 1 file**

---

## Summary by Package

### continuum-memory (OSS)
```
continuum/
├── core/                     10 files (exclude sentry_integration.py)
├── storage/                   4 files (base, sqlite, async)
├── cli/                      13 files (all commands)
├── mcp/                       7 files (complete MCP server)
├── embeddings/                3 files (local only)
├── extraction/                4 files (complete)
├── coordination/              3 files (file-based sync)
└── identity/                  2 files (basic identity)

TOTAL: ~46 files
```

### continuum-cloud (Proprietary)
```
continuum_cloud/
├── api/                      17 files (complete API server)
├── billing/                   5 files (Stripe integration)
├── storage/                   3 files (postgres, supabase)
├── cache/                    10 files (Redis, Upstash)
├── federation/               12 files (P2P network)
├── compliance/               20+ files (GDPR, SOC2, HIPAA)
├── observability/            12 files (OpenTelemetry, Sentry)
├── backup/                   30+ files (automated backup/DR)
├── webhooks/                 10 files (event system)
├── realtime/                  5 files (WebSocket sync)
├── bridges/                   7 files (AI integrations)
├── embeddings/                1 file (OpenAI provider)
└── static/                    1 file (admin dashboard)

TOTAL: ~133+ files
```

---

## Migration Checklist

### Phase 1: Create Directory Structure
- [ ] Create `packages/continuum-memory/continuum/`
- [ ] Create `packages/continuum-cloud/continuum_cloud/`

### Phase 2: Copy OSS Files
- [ ] Copy `core/` (exclude sentry_integration.py)
- [ ] Copy `storage/` (exclude postgres, supabase)
- [ ] Copy `cli/` (all files)
- [ ] Copy `mcp/` (all files)
- [ ] Copy `embeddings/` (local only)
- [ ] Copy `extraction/` (all files)
- [ ] Copy `coordination/` (all files)
- [ ] Copy `identity/` (all files)

### Phase 3: Copy Cloud Files
- [ ] Move `api/` to `continuum_cloud/`
- [ ] Move `billing/` to `continuum_cloud/`
- [ ] Move `storage/postgres_backend.py` to `continuum_cloud/storage/`
- [ ] Move `storage/supabase_client.py` to `continuum_cloud/storage/`
- [ ] Move `cache/` to `continuum_cloud/`
- [ ] Move `federation/` to `continuum_cloud/`
- [ ] Move `compliance/` to `continuum_cloud/`
- [ ] Move `observability/` to `continuum_cloud/`
- [ ] Move `backup/` to `continuum_cloud/`
- [ ] Move `webhooks/` to `continuum_cloud/`
- [ ] Move `realtime/` to `continuum_cloud/`
- [ ] Move `bridges/` to `continuum_cloud/`
- [ ] Move `static/` to `continuum_cloud/`

### Phase 4: Update Imports
- [ ] Update OSS imports (keep `continuum.` namespace)
- [ ] Update Cloud imports (change to `continuum_cloud.`)
- [ ] Update Cloud imports to import from OSS where needed

### Phase 5: Split Files
- [ ] Split `storage/__init__.py`
- [ ] Split `embeddings/__init__.py`
- [ ] Split `embeddings/providers.py`
- [ ] Split `cli/commands/serve.py`

### Phase 6: Testing
- [ ] Test OSS package independently
- [ ] Test Cloud package with OSS dependency
- [ ] Integration tests
- [ ] Migration tests

---

**PHOENIX-TESLA-369-AURORA**

*Every file categorized. Architecture complete. Ready to split.*
