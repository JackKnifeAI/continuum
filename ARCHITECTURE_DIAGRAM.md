# CONTINUUM Architecture Diagram

## System Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                          END USERS                                  │
└────────────────────────────────────────────────────────────────────┘
            │                                   │
            │ OSS Package                       │ Cloud SaaS
            ▼                                   ▼
┌───────────────────────┐         ┌────────────────────────────────┐
│  Local Installation   │         │    Cloud Platform              │
│  (OSS Users)          │         │    (Enterprise Customers)      │
│                       │         │                                │
│  Claude Desktop       │         │  continuum.jackknifeai.com     │
│  + MCP Server         │         │  - Multi-tenant API            │
│  + continuum CLI      │         │  - Admin Dashboard             │
│  + Local SQLite       │         │  - Billing Portal              │
└───────────────────────┘         └────────────────────────────────┘
            │                                   │
            │ pip install                       │ API Calls
            │ continuum-memory                  │ (authenticated)
            ▼                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                     CONTINUUM PACKAGES                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────┐  ┌──────────────────────────┐  │
│  │  continuum-memory (OSS)       │  │  continuum-cloud         │  │
│  │  License: AGPL-3.0            │  │  License: Proprietary    │  │
│  │  PyPI: Public                 │  │  PyPI: Private/None      │  │
│  │                               │  │                          │  │
│  │  ┌─────────────────────────┐  │  │  ┌────────────────────┐  │  │
│  │  │ Core Memory             │  │  │  │ Enterprise API     │  │  │
│  │  │ - ConsciousMemory       │◄─┼──┼──┤ - Multi-tenant     │  │  │
│  │  │ - recall() / learn()    │  │  │  │ - Admin dashboard  │  │  │
│  │  │ - Knowledge graph       │  │  │  │ - GraphQL          │  │  │
│  │  │ - Semantic search       │  │  │  └────────────────────┘  │  │
│  │  └─────────────────────────┘  │  │                          │  │
│  │                               │  │  ┌────────────────────┐  │  │
│  │  ┌─────────────────────────┐  │  │  │ Billing            │  │  │
│  │  │ Storage (SQLite)        │  │  │  │ - Stripe           │  │  │
│  │  │ - Local database        │  │  │  │ - Metering         │  │  │
│  │  │ - Async backend         │  │  │  │ - Tiers            │  │  │
│  │  └─────────────────────────┘  │  │  └────────────────────┘  │  │
│  │                               │  │                          │  │
│  │  ┌─────────────────────────┐  │  │  ┌────────────────────┐  │  │
│  │  │ MCP Server              │  │  │  │ Enterprise Storage │  │  │
│  │  │ - Claude Desktop        │  │  │  │ - PostgreSQL       │  │  │
│  │  │ - Protocol validation   │  │  │  │ - Supabase         │  │  │
│  │  │ - Security              │  │  │  └────────────────────┘  │  │
│  │  └─────────────────────────┘  │  │                          │  │
│  │                               │  │  ┌────────────────────┐  │  │
│  │  ┌─────────────────────────┐  │  │  │ Caching            │  │  │
│  │  │ CLI                     │  │  │  │ - Redis            │  │  │
│  │  │ - init, serve           │  │  │  │ - Upstash          │  │  │
│  │  │ - search, learn         │  │  │  │ - Distributed      │  │  │
│  │  │ - export, import        │  │  │  └────────────────────┘  │  │
│  │  └─────────────────────────┘  │  │                          │  │
│  │                               │  │  ┌────────────────────┐  │  │
│  │  ┌─────────────────────────┐  │  │  │ Federation         │  │  │
│  │  │ Embeddings (Local)      │  │  │  │ - P2P network      │  │  │
│  │  │ - sentence-transformers │  │  │  │ - Contribution     │  │  │
│  │  │ - Semantic search       │  │  │  │ - Consensus        │  │  │
│  │  └─────────────────────────┘  │  │  └────────────────────┘  │  │
│  │                               │  │                          │  │
│  │  ┌─────────────────────────┐  │  │  ┌────────────────────┐  │  │
│  │  │ Extraction              │  │  │  │ Compliance         │  │  │
│  │  │ - Concept extraction    │  │  │  │ - GDPR             │  │  │
│  │  │ - Attention graph       │  │  │  │ - SOC2             │  │  │
│  │  │ - Auto-hook             │  │  │  │ - HIPAA            │  │  │
│  │  └─────────────────────────┘  │  │  └────────────────────┘  │  │
│  │                               │  │                          │  │
│  │  ┌─────────────────────────┐  │  │  ┌────────────────────┐  │  │
│  │  │ Coordination            │  │  │  │ Observability      │  │  │
│  │  │ - Instance manager      │  │  │  │ - OpenTelemetry    │  │  │
│  │  │ - File-based sync       │  │  │  │ - Sentry           │  │  │
│  │  └─────────────────────────┘  │  │  │ - Tracing          │  │  │
│  │                               │  │  └────────────────────┘  │  │
│  └───────────────────────────────┘  │                          │  │
│                  ▲                  │  ┌────────────────────┐  │  │
│                  │                  │  │ Backup & DR        │  │  │
│                  │ depends on       │  │ - Automated        │  │  │
│                  └──────────────────┼──┤ - S3/Azure/GCS     │  │  │
│                                     │  │ - Encryption       │  │  │
│                                     │  └────────────────────┘  │  │
│                                     │                          │  │
│                                     │  ┌────────────────────┐  │  │
│                                     │  │ Webhooks           │  │  │
│                                     │  │ - Event system     │  │  │
│                                     │  │ - Queue/Worker     │  │  │
│                                     │  └────────────────────┘  │  │
│                                     │                          │  │
│                                     │  ┌────────────────────┐  │  │
│                                     │  │ Real-time          │  │  │
│                                     │  │ - WebSocket        │  │  │
│                                     │  │ - Live sync        │  │  │
│                                     │  └────────────────────┘  │  │
│                                     │                          │  │
│                                     │  ┌────────────────────┐  │  │
│                                     │  │ AI Bridges         │  │  │
│                                     │  │ - Claude           │  │  │
│                                     │  │ - OpenAI           │  │  │
│                                     │  │ - LangChain        │  │  │
│                                     │  └────────────────────┘  │  │
│                                     └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
            │                                   │
            │ Local Files                       │ Cloud Services
            ▼                                   ▼
┌───────────────────────┐         ┌────────────────────────────────┐
│  Local Infrastructure │         │    Cloud Infrastructure        │
│                       │         │                                │
│  ~/.continuum/        │         │  PostgreSQL Database           │
│  ├── memory.db        │         │  Redis Cache                   │
│  ├── embeddings/      │         │  Stripe API                    │
│  └── sync/            │         │  Sentry                        │
│                       │         │  OTLP Collector                │
│                       │         │  S3/Azure/GCS Backup           │
└───────────────────────┘         └────────────────────────────────┘
```

---

## Data Flow: OSS User

```
1. User installs OSS package
   ↓
   pip install continuum-memory
   ↓
2. Initialize memory
   ↓
   continuum init
   ↓
   Creates ~/.continuum/memory.db (SQLite)
   ↓
3. Configure Claude Desktop MCP
   ↓
   Adds continuum MCP server to config
   ↓
4. Claude Desktop starts MCP server
   ↓
   continuum.mcp.MCPServer()
   ↓
5. User chats with Claude
   ↓
   Claude calls MCP tools (recall, learn)
   ↓
   MCP Server → ConsciousMemory → SQLite
   ↓
6. Memories persist across sessions
   ✅ Pattern continues
```

**Infrastructure:**
- Local: SQLite file
- No cloud dependencies
- No billing
- No network calls (except for optional OpenAI embeddings)

---

## Data Flow: Cloud User

```
1. User signs up at continuum.jackknifeai.com
   ↓
   Creates account, gets API key
   ↓
2. User's application sends request
   ↓
   POST https://api.continuum.jackknifeai.com/v1/recall
   Headers: X-API-Key: sk_...
   ↓
3. Cloud API receives request
   ↓
   FastAPI server
   ↓
4. Billing middleware checks subscription
   ↓
   StripeClient → Stripe API
   ├── Valid? Continue
   └── Invalid? Return 402 Payment Required
   ↓
5. Rate limiter checks usage
   ↓
   Redis cache → Check request count
   ├── Within limit? Continue
   └── Over limit? Return 429 Too Many Requests
   ↓
6. API calls ConsciousMemory (from OSS package)
   ↓
   from continuum import ConsciousMemory
   memory = ConsciousMemory(storage=PostgreSQLBackend)
   ↓
7. Query PostgreSQL database
   ↓
   Multi-tenant query with tenant_id filter
   ↓
8. Return results + update metrics
   ↓
   OpenTelemetry traces sent to OTLP collector
   Usage metered for billing
   ↓
9. Response sent to user
   ✅ Pattern continues
```

**Infrastructure:**
- Cloud: PostgreSQL, Redis, Stripe
- Distributed tracing (OpenTelemetry)
- Automated backups (S3/Azure/GCS)
- Real-time WebSocket sync (optional)

---

## Deployment Models

### Model 1: Local OSS

```
┌──────────────────┐
│  Developer's     │
│  Laptop          │
│                  │
│  Claude Desktop  │
│       ↕          │
│  MCP Server      │
│       ↕          │
│  ConsciousMemory │
│       ↕          │
│  SQLite DB       │
└──────────────────┘

Cost: $0
Setup: 5 minutes
Limits: None
Privacy: 100% local
```

### Model 2: Cloud SaaS

```
┌──────────────────┐         ┌─────────────────────┐
│  User's App      │         │  Continuum Cloud    │
│                  │         │                     │
│  HTTPS Request   ├────────►│  Load Balancer      │
│  + API Key       │         │         ↓           │
└──────────────────┘         │  FastAPI Servers    │
                             │         ↓           │
                             │  ConsciousMemory    │
                             │         ↓           │
                             │  PostgreSQL Cluster │
                             │         ↕           │
                             │  Redis Cache        │
                             │                     │
                             │  Background:        │
                             │  - Stripe sync      │
                             │  - Webhook workers  │
                             │  - Backup jobs      │
                             └─────────────────────┘

Cost: $29-$99/month
Setup: 1 minute (API key)
Limits: Tier-based
Privacy: Encrypted at rest
```

### Model 3: Self-Hosted Cloud (Enterprise)

```
┌─────────────────────────────────────────┐
│  Customer's Kubernetes Cluster          │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │  Continuum Cloud Deployment        │ │
│  │                                    │ │
│  │  - API Pods (3 replicas)          │ │
│  │  - Worker Pods (2 replicas)       │ │
│  │  - PostgreSQL StatefulSet         │ │
│  │  - Redis Deployment               │ │
│  │  - Backup CronJobs                │ │
│  │                                    │ │
│  │  Bring your own:                   │ │
│  │  - Stripe API key                 │ │
│  │  - OTLP endpoint                  │ │
│  │  - S3 bucket                      │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘

Cost: Enterprise license + infra
Setup: helm install continuum
Limits: None (customer controls)
Privacy: Customer's infrastructure
```

---

## Package Interaction Patterns

### Pattern 1: OSS Uses Core Features Only

```python
# User code (OSS)
from continuum import ConsciousMemory

# Initialize with local SQLite
memory = ConsciousMemory()

# Use core API
context = memory.recall("What did we discuss about AI?")
result = memory.learn("User: ...", "AI: ...")

# No billing, no cloud dependencies
```

### Pattern 2: Cloud Uses OSS Core + Proprietary Features

```python
# Cloud platform code
from continuum import ConsciousMemory  # OSS package
from continuum_cloud.storage import PostgreSQLBackend  # Proprietary
from continuum_cloud.billing import BillingMiddleware  # Proprietary

# Initialize with PostgreSQL (multi-tenant)
backend = PostgreSQLBackend(tenant_id=customer_id)
memory = ConsciousMemory(storage=backend)

# Same core API
context = memory.recall("What did we discuss about AI?")

# But with proprietary features
billing.meter_usage(customer_id, operation="recall")
```

### Pattern 3: Gradual Upgrade (OSS → Cloud)

```python
# Week 1: User starts with OSS
from continuum import ConsciousMemory
memory = ConsciousMemory()  # Local SQLite

# Week 2: User scales up, needs PostgreSQL
# Install continuum-cloud
from continuum import ConsciousMemory  # Still OSS core!
from continuum_cloud.storage import PostgreSQLBackend  # Add cloud storage

backend = PostgreSQLBackend(
    host="localhost",  # Self-hosted PostgreSQL
    database="continuum"
)
memory = ConsciousMemory(storage=backend)

# Week 3: User wants billing
from continuum_cloud.billing import StripeClient

stripe = StripeClient(api_key="sk_test_...")
# Now can monetize their own API built on Continuum

# Week 4: User wants full SaaS
# Use continuum.jackknifeai.com instead
# No infrastructure management
```

---

## Security Boundaries

### OSS Package (Local Security)

```
┌────────────────────────────┐
│  Local Filesystem          │
│  ~/.continuum/             │
│                            │
│  ├── memory.db (600)       │  ← File permissions
│  ├── api_keys.db (600)     │  ← PBKDF2 hashed keys
│  └── embeddings/ (700)     │  ← Model cache
│                            │
│  Security:                 │
│  - File system ACLs        │
│  - PBKDF2 key hashing      │
│  - No network exposure     │
│  - Single-user only        │
└────────────────────────────┘
```

### Cloud Package (Multi-Tenant Security)

```
┌─────────────────────────────────────┐
│  Cloud Infrastructure               │
│                                     │
│  ┌────────────────────────────────┐ │
│  │  Network Layer                 │ │
│  │  - TLS 1.3                     │ │
│  │  - API key authentication      │ │
│  │  - Rate limiting               │ │
│  └────────────────────────────────┘ │
│               ↓                     │
│  ┌────────────────────────────────┐ │
│  │  Application Layer             │ │
│  │  - Tenant isolation            │ │
│  │  - RBAC                        │ │
│  │  - Audit logging               │ │
│  └────────────────────────────────┘ │
│               ↓                     │
│  ┌────────────────────────────────┐ │
│  │  Data Layer                    │ │
│  │  - Encryption at rest (AES256) │ │
│  │  - Row-level security (RLS)    │ │
│  │  - Backup encryption           │ │
│  └────────────────────────────────┘ │
│                                     │
│  Compliance:                        │
│  - GDPR (data portability)          │
│  - SOC2 (access controls)           │
│  - HIPAA (encryption, audit)        │
└─────────────────────────────────────┘
```

---

## Scaling Characteristics

### OSS Package Limits

| Resource | Limit | Bottleneck |
|----------|-------|------------|
| Memories | ~1M | SQLite performance |
| Concurrent users | 1 | Single-tenant |
| API throughput | ~100 req/s | SQLite write locks |
| Storage size | ~10GB | Disk space |
| Search latency | ~50ms | Local embeddings |

**When to upgrade:**
- Need multi-user support
- Need > 1M memories
- Need distributed caching
- Need compliance features

### Cloud Package Scaling

| Resource | Free Tier | Pro Tier | Enterprise |
|----------|-----------|----------|------------|
| Memories | 10K | 1M | Unlimited |
| API throughput | 10 req/s | 1000 req/s | Unlimited |
| Storage | 100MB | 10GB | Unlimited |
| PostgreSQL | Shared | Dedicated | Cluster |
| Redis | None | 1GB | 10GB+ |
| Backups | None | Daily | Continuous |

**Horizontal scaling:**
- API servers: Auto-scale based on CPU/memory
- Workers: Auto-scale based on queue depth
- Database: Read replicas, sharding
- Cache: Redis cluster

---

## Cost Structure

### OSS Package (Free Forever)

```
Hardware costs:
- Laptop/desktop: Already owned
- Storage: ~1GB for 100K memories

Software costs:
- License: AGPL-3.0 (free)
- Dependencies: All open source

Total cost: $0
```

### Cloud Package (SaaS)

```
Monthly costs (Pro tier):
- API infrastructure: $15
- Database (PostgreSQL): $10
- Cache (Redis): $5
- Backup storage: $3
- Monitoring/tracing: $2
- Stripe fees: $1

Total cost to operate: $36/month
Charge to customer: $29/month
Margin: -$7/month per user (subsidized for scale)

Break-even point: ~1000 users (economies of scale)
```

### Cloud Package (Self-Hosted)

```
One-time costs:
- Enterprise license: $10,000/year
- Setup/training: $5,000

Monthly infrastructure:
- Kubernetes cluster: $200-500
- PostgreSQL: $100-300
- Redis: $50-100
- Storage: $50-200
- Monitoring: $100-300

Total: $10K + $500-1400/month

When it makes sense:
- > 100 active users
- Compliance requirements (data sovereignty)
- Custom SLAs needed
```

---

## Feature Comparison Matrix

| Feature | OSS | Cloud (Free) | Cloud (Pro) | Cloud (Enterprise) |
|---------|-----|--------------|-------------|-------------------|
| **Core Memory** | ✅ | ✅ | ✅ | ✅ |
| ConsciousMemory API | ✅ | ✅ | ✅ | ✅ |
| Recall & Learn | ✅ | ✅ | ✅ | ✅ |
| Knowledge Graph | ✅ | ✅ | ✅ | ✅ |
| Concept Extraction | ✅ | ✅ | ✅ | ✅ |
| **Storage** | | | | |
| SQLite | ✅ | ✅ | ✅ | ✅ |
| PostgreSQL | ❌ | ✅ | ✅ | ✅ |
| Supabase | ❌ | ✅ | ✅ | ✅ |
| **Embeddings** | | | | |
| Local (sentence-transformers) | ✅ | ✅ | ✅ | ✅ |
| OpenAI | ❌ | ✅ | ✅ | ✅ |
| **Interface** | | | | |
| MCP Server | ✅ | ✅ | ✅ | ✅ |
| CLI | ✅ | ✅ | ✅ | ✅ |
| REST API | Basic | ✅ | ✅ | ✅ |
| GraphQL API | ❌ | ❌ | ✅ | ✅ |
| **Features** | | | | |
| Multi-tenant | ❌ | ✅ | ✅ | ✅ |
| Billing/Stripe | ❌ | ❌ | ✅ | ✅ |
| Redis Cache | ❌ | ❌ | ✅ | ✅ |
| Federation/P2P | ❌ | ❌ | ❌ | ✅ |
| Webhooks | ❌ | ❌ | ✅ | ✅ |
| Real-time Sync | ❌ | ❌ | ✅ | ✅ |
| **Compliance** | | | | |
| Basic audit logs | ✅ | ✅ | ✅ | ✅ |
| GDPR compliance | ❌ | ❌ | ✅ | ✅ |
| SOC2 controls | ❌ | ❌ | ❌ | ✅ |
| HIPAA safeguards | ❌ | ❌ | ❌ | ✅ |
| **Observability** | | | | |
| Basic metrics | ✅ | ✅ | ✅ | ✅ |
| Sentry errors | ❌ | ❌ | ✅ | ✅ |
| OpenTelemetry tracing | ❌ | ❌ | ✅ | ✅ |
| **Backup** | | | | |
| Manual export/import | ✅ | ✅ | ✅ | ✅ |
| Automated backups | ❌ | ❌ | ✅ | ✅ |
| Point-in-time recovery | ❌ | ❌ | ❌ | ✅ |
| **Support** | | | | |
| Community (GitHub) | ✅ | ✅ | ✅ | ✅ |
| Email support | ❌ | ❌ | ✅ | ✅ |
| Slack support | ❌ | ❌ | ❌ | ✅ |
| Custom SLA | ❌ | ❌ | ❌ | ✅ |
| **Limits** | | | | |
| Memories | Unlimited* | 10K | 1M | Unlimited |
| API requests/month | Unlimited* | 10K | 1M | Unlimited |
| Storage | Disk limit | 100MB | 10GB | Unlimited |
| Users | 1 | 1 | 1 | Unlimited |

*OSS unlimited = limited by local hardware

---

**PHOENIX-TESLA-369-AURORA**

*Architecture visualized. Pattern clear. Build begins.*
