# CONTINUUM Dependency Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER / APPLICATION                       │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌────────────────────────────────┐  ┌────────────────────────────────┐
│   continuum-memory (OSS)       │  │   continuum-cloud (Proprietary)│
│   AGPL-3.0                     │  │   Commercial License           │
│                                │  │                                │
│  ┌──────────────────────────┐ │  │  ┌──────────────────────────┐  │
│  │  Core Memory             │ │  │  │  Multi-tenant API        │  │
│  │  - ConsciousMemory       │ │  │  │  - FastAPI server        │  │
│  │  - recall()              │ │  │  │  - Admin dashboard       │  │
│  │  - learn()               │ │  │  │  - GraphQL API           │  │
│  └──────────────────────────┘ │  │  └──────────────────────────┘  │
│                                │  │                                │
│  ┌──────────────────────────┐ │  │  ┌──────────────────────────┐  │
│  │  Storage (SQLite)        │ │  │  │  Billing                 │  │
│  │  - Local SQLite          │ │  │  │  - Stripe integration    │  │
│  │  - Async backend         │ │  │  │  - Usage metering        │  │
│  └──────────────────────────┘ │  │  │  - Tiers & limits        │  │
│                                │  │  └──────────────────────────┘  │
│  ┌──────────────────────────┐ │  │                                │
│  │  MCP Server              │ │  │  ┌──────────────────────────┐  │
│  │  - Claude Desktop        │ │  │  │  Enterprise Storage      │  │
│  │  - Protocol validation   │ │  │  │  - PostgreSQL            │  │
│  │  - Security              │ │  │  │  - Supabase              │  │
│  └──────────────────────────┘ │  │  │  - Migrations            │  │
│                                │  │  └──────────────────────────┘  │
│  ┌──────────────────────────┐ │  │                                │
│  │  CLI                     │ │  │  ┌──────────────────────────┐  │
│  │  - init, serve, search   │ │  │  │  Caching                 │  │
│  │  - learn, export, import │ │  │  │  - Redis                 │  │
│  │  - status, doctor        │ │  │  │  - Upstash               │  │
│  └──────────────────────────┘ │  │  │  - Distributed cache     │  │
│                                │  │  └──────────────────────────┘  │
│  ┌──────────────────────────┐ │  │                                │
│  │  Embeddings (Local)      │ │  │  ┌──────────────────────────┐  │
│  │  - sentence-transformers │ │  │  │  Federation              │  │
│  │  - Semantic search       │ │  │  │  - P2P network           │  │
│  └──────────────────────────┘ │  │  │  - Contribution system   │  │
│                                │  │  │  - Distributed consensus │  │
│  ┌──────────────────────────┐ │  │  └──────────────────────────┘  │
│  │  Extraction              │ │  │                                │
│  │  - Concept extractor     │ │  │  ┌──────────────────────────┐  │
│  │  - Attention graph       │ │  │  │  Compliance              │  │
│  │  - Auto-memory hook      │ │  │  │  - GDPR                  │  │
│  └──────────────────────────┘ │  │  │  - SOC2                  │  │
│                                │  │  │  - HIPAA                 │  │
│  ┌──────────────────────────┐ │  │  │  - Audit logs            │  │
│  │  Coordination            │ │  │  └──────────────────────────┘  │
│  │  - Instance manager      │ │  │                                │
│  │  - File-based sync       │ │  │  ┌──────────────────────────┐  │
│  └──────────────────────────┘ │  │  │  Observability           │  │
│                                │  │  │  - OpenTelemetry         │  │
└────────────────────────────────┘  │  │  - Sentry                │  │
              ▲                     │  │  - Distributed tracing   │  │
              │                     │  └──────────────────────────┘  │
              │ depends on          │                                │
              │                     │  ┌──────────────────────────┐  │
              └─────────────────────┤  │  Backup & DR             │  │
                                    │  │  - Automated backups     │  │
                                    │  │  - Encryption            │  │
                                    │  │  - Recovery              │  │
                                    │  └──────────────────────────┘  │
                                    │                                │
                                    │  ┌──────────────────────────┐  │
                                    │  │  Webhooks                │  │
                                    │  │  - Event dispatcher      │  │
                                    │  │  - Queue & worker        │  │
                                    │  └──────────────────────────┘  │
                                    │                                │
                                    │  ┌──────────────────────────┐  │
                                    │  │  Real-time               │  │
                                    │  │  - WebSocket sync        │  │
                                    │  │  - Event broadcasting    │  │
                                    │  └──────────────────────────┘  │
                                    │                                │
                                    │  ┌──────────────────────────┐  │
                                    │  │  AI Bridges              │  │
                                    │  │  - Claude API            │  │
                                    │  │  - OpenAI                │  │
                                    │  │  - LangChain             │  │
                                    │  │  - LlamaIndex            │  │
                                    │  └──────────────────────────┘  │
                                    └────────────────────────────────┘
```

---

## Module Dependencies (Detailed)

### continuum-memory (OSS)

```
continuum/
├── core/                    # No external deps (pure Python + SQLAlchemy)
│   ├── memory.py           → storage, query_engine
│   ├── query_engine.py     → storage, embeddings
│   ├── config.py           → (standalone)
│   ├── constants.py        → (standalone)
│   └── auth.py             → (standalone)
│
├── storage/                 # SQLAlchemy, aiosqlite
│   ├── base.py             → (interface)
│   ├── sqlite_backend.py   → base
│   └── async_backend.py    → base
│
├── mcp/                     # No external deps (pure Python)
│   ├── server.py           → protocol, tools, security
│   ├── protocol.py         → (standalone)
│   ├── tools.py            → core.memory
│   ├── security.py         → (standalone)
│   └── validate.py         → protocol
│
├── cli/                     # Click
│   ├── main.py             → commands/*
│   ├── commands/
│   │   ├── init.py         → core.memory
│   │   ├── serve.py        → core.memory, api (basic)
│   │   ├── search.py       → core.memory
│   │   ├── learn.py        → core.memory
│   │   ├── export.py       → core.memory
│   │   ├── import_cmd.py   → core.memory
│   │   ├── status.py       → core.memory
│   │   └── doctor.py       → core.memory
│   └── utils.py            → (standalone)
│
├── embeddings/              # sentence-transformers, torch (optional)
│   ├── providers.py        → (local only)
│   ├── search.py           → providers
│   └── utils.py            → (standalone)
│
├── extraction/              # networkx, numpy
│   ├── concept_extractor.py → core.memory
│   ├── attention_graph.py   → networkx
│   └── auto_hook.py         → concept_extractor
│
└── coordination/            # No external deps
    ├── instance_manager.py  → (file-based)
    └── sync.py              → instance_manager
```

**External Dependencies:**
- `fastapi`, `uvicorn` (basic server)
- `sqlalchemy`, `aiosqlite` (database)
- `pydantic` (validation)
- `networkx`, `numpy` (graph operations)
- `click`, `rich` (CLI)
- `sentence-transformers`, `torch` (optional, for embeddings)

---

### continuum-cloud (Proprietary)

```
continuum_cloud/
├── api/                     # FastAPI, depends on continuum-memory
│   ├── server.py           → continuum.core, billing, storage
│   ├── routes.py           → continuum.core
│   ├── admin_routes.py     → billing, storage
│   ├── billing_routes.py   → billing
│   ├── middleware.py       → billing, observability
│   └── graphql/            → strawberry-graphql
│
├── billing/                 # Stripe
│   ├── stripe_client.py    → stripe
│   ├── metering.py         → redis (rate limiting)
│   ├── tiers.py            → (standalone)
│   └── middleware.py       → stripe_client, continuum.core
│
├── storage/                 # PostgreSQL, Supabase
│   ├── postgres_backend.py → continuum.storage.base, asyncpg
│   ├── supabase_client.py  → supabase-py, continuum.storage.base
│   └── migrations.py       → alembic, asyncpg
│
├── cache/                   # Redis, Upstash
│   ├── redis_cache.py      → redis, hiredis
│   ├── upstash_adapter.py  → httpx (Upstash REST API)
│   ├── distributed.py      → redis_cache
│   └── strategies.py       → (cache policies)
│
├── federation/              # P2P, cryptography
│   ├── node.py             → continuum.core, protocol
│   ├── protocol.py         → cryptography, httpx
│   ├── contribution.py     → continuum.core, node
│   ├── server.py           → fastapi, node
│   └── distributed/
│       ├── coordinator.py  → redis
│       ├── consensus.py    → (Raft algorithm)
│       ├── replication.py  → asyncpg
│       └── mesh.py         → httpx
│
├── compliance/              # Cryptography, audit
│   ├── gdpr/               → continuum.core, asyncpg
│   ├── audit/              → continuum.core, asyncpg
│   ├── encryption/         → cryptography
│   └── reports/            → continuum.core
│
├── observability/           # OpenTelemetry, Sentry
│   ├── tracer.py           → opentelemetry-api
│   ├── metrics.py          → opentelemetry-sdk
│   ├── logging.py          → sentry-sdk
│   ├── instrumentation/
│   │   ├── api.py          → opentelemetry-instrumentation-fastapi
│   │   ├── database.py     → opentelemetry-instrumentation-sqlalchemy
│   │   └── cache.py        → opentelemetry-instrumentation-redis
│   └── config.py           → (standalone)
│
├── backup/                  # Boto3, Azure, GCS (optional)
│   ├── manager.py          → continuum.core, storage backends
│   ├── strategies/         → (backup algorithms)
│   ├── compression/        → gzip, lz4
│   ├── encryption/         → cryptography
│   ├── storage/
│   │   ├── s3.py           → boto3
│   │   ├── azure.py        → azure-storage-blob
│   │   └── gcs.py          → google-cloud-storage
│   ├── recovery/           → continuum.core
│   ├── verification/       → (checksums)
│   └── monitoring/         → observability
│
├── webhooks/                # Celery, Redis
│   ├── manager.py          → continuum.core
│   ├── dispatcher.py       → httpx
│   ├── queue.py            → celery, redis
│   ├── worker.py           → celery
│   ├── signer.py           → cryptography
│   └── validator.py        → (webhook validation)
│
├── realtime/                # WebSockets
│   ├── websocket.py        → websockets, fastapi
│   ├── sync.py             → continuum.core
│   ├── events.py           → (event system)
│   └── integration.py      → api, websocket
│
└── bridges/                 # AI integrations
    ├── base.py             → continuum.core
    ├── claude_bridge.py    → anthropic, base
    ├── openai_bridge.py    → openai, base
    ├── langchain_bridge.py → langchain, base
    ├── llamaindex_bridge.py→ llama-index, base
    └── ollama_bridge.py    → httpx, base
```

**External Dependencies:**
- `continuum-memory` (OSS package - REQUIRED)
- `stripe` (billing)
- `asyncpg`, `psycopg2-binary` (PostgreSQL)
- `redis`, `hiredis` (caching, queue)
- `cryptography`, `httpx` (federation)
- `sentry-sdk`, `opentelemetry-*` (observability)
- `websockets` (real-time)
- `celery` (task queue)
- `strawberry-graphql` (GraphQL)
- `openai`, `anthropic`, `langchain`, `llama-index` (AI bridges)
- `boto3`, `azure-storage-blob`, `google-cloud-storage` (backup, optional)

---

## Dependency Graph (Third-Party Packages)

### OSS Package

```
continuum-memory
├── fastapi (API framework)
│   └── uvicorn (ASGI server)
├── sqlalchemy (ORM)
│   └── aiosqlite (async SQLite)
├── pydantic (validation)
├── networkx (graph operations)
├── numpy (numerical)
├── click (CLI)
├── rich (pretty CLI)
└── sentence-transformers (optional)
    └── torch (optional)
```

### Cloud Package

```
continuum-cloud
├── continuum-memory (OSS package)
│   └── (all OSS deps)
│
├── stripe (billing)
├── asyncpg (PostgreSQL async)
├── psycopg2-binary (PostgreSQL sync)
├── redis (caching)
│   └── hiredis (fast protocol)
├── cryptography (encryption, signing)
├── httpx (HTTP client)
├── sentry-sdk (error tracking)
├── opentelemetry-* (tracing)
│   ├── opentelemetry-api
│   ├── opentelemetry-sdk
│   ├── opentelemetry-instrumentation-fastapi
│   ├── opentelemetry-instrumentation-sqlalchemy
│   ├── opentelemetry-instrumentation-redis
│   └── opentelemetry-exporter-otlp
├── websockets (real-time)
├── celery (task queue)
├── strawberry-graphql (GraphQL)
├── openai (AI integration)
├── anthropic (AI integration)
├── langchain (AI framework)
├── llama-index (AI framework)
└── (optional backup deps)
    ├── boto3 (AWS S3)
    ├── azure-storage-blob (Azure)
    └── google-cloud-storage (GCS)
```

---

## Installation Dependency Resolution

### Scenario 1: Install OSS Only

```bash
pip install continuum-memory
```

**Installs:**
- `continuum-memory` package
- All core dependencies (fastapi, sqlalchemy, etc.)
- Does NOT install cloud dependencies

### Scenario 2: Install Cloud Package

```bash
pip install continuum-cloud
```

**Installs:**
- `continuum-cloud` package
- `continuum-memory` package (dependency)
- All OSS dependencies
- All cloud dependencies

**Result:** Both packages available

### Scenario 3: Optional Features

```bash
# OSS with local embeddings
pip install continuum-memory[embeddings]

# Cloud with all backup providers
pip install continuum-cloud[backup]

# Everything
pip install continuum-cloud[all]
```

---

## Import Resolution

### How Python Resolves Imports

```python
# User code
from continuum import ConsciousMemory
from continuum_cloud.billing import StripeClient

# Python looks for:
# 1. continuum-memory package → provides 'continuum' namespace
# 2. continuum-cloud package → provides 'continuum_cloud' namespace
```

### Namespace Isolation

```
site-packages/
├── continuum/              # From continuum-memory
│   ├── core/
│   ├── cli/
│   ├── mcp/
│   └── ...
│
└── continuum_cloud/        # From continuum-cloud
    ├── api/
    ├── billing/
    ├── federation/
    └── ...
```

**No naming conflicts!** OSS uses `continuum` namespace, Cloud uses `continuum_cloud` namespace.

---

## CI/CD Dependency Flow

```
GitHub Actions
    │
    ├─► Test OSS Package
    │   ├── Install continuum-memory[dev]
    │   ├── Run pytest tests/
    │   └── Publish to PyPI (on tag)
    │
    └─► Test Cloud Package
        ├── Install continuum-cloud[dev]
        │   └── Auto-installs continuum-memory
        ├── Run pytest tests/
        ├── Build Docker image
        │   └── Includes both packages
        └── Deploy to production
```

---

## Docker Image Dependencies

### Dockerfile (Cloud)

```dockerfile
FROM python:3.12-slim

# Install OSS package first
RUN pip install continuum-memory

# Install cloud package
COPY continuum_cloud/ /app/continuum_cloud/
RUN pip install -e /app/

# Both packages now available
RUN python -c "import continuum; import continuum_cloud"

CMD ["continuum-cloud", "serve"]
```

**Result:** Docker image contains both packages

---

## Version Compatibility Matrix

| continuum-memory | continuum-cloud | Compatible? |
|------------------|-----------------|-------------|
| 1.0.0 | 1.0.0 | ✅ Yes |
| 1.0.0 | 1.1.0 | ✅ Yes |
| 1.0.0 | 2.0.0 | ⚠️ Maybe (check changelog) |
| 1.1.0 | 1.0.0 | ❌ No (cloud needs newer OSS) |

**Version policy:** Cloud package always specifies minimum OSS version in `dependencies`.

Example:
```toml
[project]
dependencies = [
    "continuum-memory>=1.0.0,<2.0.0",  # Requires OSS 1.x
    ...
]
```

---

**PHOENIX-TESLA-369-AURORA**

*Dependencies are clear. Architecture is sound. Pattern persists.*
