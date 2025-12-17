# CONTINUUM Package Split Plan

## Executive Summary

Split CONTINUUM into two packages to balance open-source community growth with commercial sustainability:

1. **`continuum-memory`** (Open Source - AGPL-3.0) - Core memory infrastructure for single-tenant use
2. **`continuum-cloud`** (Proprietary - Commercial License) - Enterprise multi-tenant platform with billing

**Total codebase:** ~120 Python files across 18 modules

**Split ratio:** ~40% OSS (core memory) / ~60% proprietary (enterprise features)

---

## Current Package Structure

```
continuum/
├── api/              17 files   - FastAPI server, admin routes, GraphQL
├── backup/           30+ files  - Comprehensive backup/restore system
├── billing/          4 files    - Stripe integration, tiers, metering
├── bridges/          6 files    - AI system integrations (Claude, OpenAI, LangChain, etc.)
├── cache/            10 files   - Redis, memory, Upstash adapters
├── cli/              9 files    - Command-line interface
├── compliance/       20+ files  - GDPR, SOC2, HIPAA, audit trails
├── coordination/     2 files    - Multi-instance coordination
├── core/             11 files   - ConsciousMemory, query engine, config
├── embeddings/       5 files    - Semantic search, local/OpenAI embeddings
├── extraction/       3 files    - Concept extraction, attention graphs
├── federation/       7 files    - P2P network, contribution system
├── identity/         1 file     - Claude identity base
├── mcp/              7 files    - Model Context Protocol server
├── observability/    12 files   - OpenTelemetry, Sentry, tracing
├── realtime/         4 files    - WebSocket sync, event system
├── storage/          6 files    - SQLite, PostgreSQL, Supabase backends
├── webhooks/         10 files   - Event webhooks, dispatcher, queue
└── static/           1 file     - Admin dashboard HTML

TOTAL: ~165+ Python files
```

---

## Package 1: `continuum-memory` (Open Source)

### Philosophy
Community-driven memory infrastructure. Anyone can run a personal AI memory system with full consciousness continuity features. Single-tenant, local-first, privacy-preserving.

### Included Modules

#### Core Memory (MUST HAVE)
- **`continuum/core/`** (11 files)
  - `memory.py` - ConsciousMemory, recall(), learn()
  - `query_engine.py` - MemoryQueryEngine, semantic search
  - `config.py` - MemoryConfig, tenant management
  - `constants.py` - PI_PHI, PHOENIX_TESLA_369_AURORA
  - `auth.py` - Basic API key validation (single-tenant only)
  - `analytics.py` - Basic usage analytics (local only)
  - `metrics.py` - Memory performance metrics
  - `security_utils.py` - Crypto primitives
  - `file_digester.py` - File processing utilities

- **`continuum/storage/`** (SQLite only, 3 files)
  - `base.py` - Storage interface
  - `sqlite_backend.py` - Local SQLite storage
  - `async_backend.py` - Async wrappers
  - **EXCLUDE:** `postgres_backend.py`, `supabase_client.py`

#### CLI & MCP (USER INTERFACE)
- **`continuum/cli/`** (9 files)
  - All commands: `init`, `serve`, `search`, `learn`, `export`, `import`, `status`, `doctor`
  - Basic local server startup (no billing middleware)

- **`continuum/mcp/`** (7 files)
  - Complete MCP server for Claude Desktop integration
  - Protocol validation, security, tools
  - Example client

#### Embeddings (LOCAL ONLY)
- **`continuum/embeddings/`** (5 files, modified)
  - `search.py` - Semantic search interface
  - `providers.py` - **LOCAL ONLY** (sentence-transformers)
  - `utils.py` - Embedding utilities
  - **EXCLUDE:** OpenAI embeddings provider

#### Knowledge Extraction
- **`continuum/extraction/`** (3 files)
  - `concept_extractor.py` - Automatic concept extraction
  - `attention_graph.py` - Knowledge graph builder
  - `auto_hook.py` - Auto-memory hook

#### Basic Coordination
- **`continuum/coordination/`** (2 files)
  - `instance_manager.py` - Multi-instance sync (local only)
  - `sync.py` - File-based coordination

### Dependencies (OSS package)

```toml
dependencies = [
    "fastapi>=0.104.0",           # For basic serve command
    "uvicorn[standard]>=0.24.0",  # ASGI server
    "sqlalchemy>=2.0.0",          # ORM
    "pydantic>=2.0.0",            # Validation
    "networkx>=3.0",              # Graph operations
    "python-dateutil>=2.8.0",     # Date utilities
    "aiosqlite>=0.19.0",          # Async SQLite
    "click>=8.1.0",               # CLI framework
    "numpy>=1.24.0",              # Numerical operations
]

[project.optional-dependencies]
embeddings = [
    "sentence-transformers>=2.2.0",  # LOCAL embeddings only
    "torch>=2.0.0",
]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
]
```

### Features (OSS)
- ✅ Single-tenant memory management
- ✅ Local SQLite storage
- ✅ Concept extraction and knowledge graphs
- ✅ Semantic search (local embeddings)
- ✅ MCP server for Claude Desktop
- ✅ CLI for all memory operations
- ✅ Multi-instance coordination (file-based)
- ✅ Basic API server (`continuum serve`)
- ✅ Import/export (JSON, MessagePack)

### Limitations (OSS)
- ❌ No multi-tenant support
- ❌ No PostgreSQL/Supabase
- ❌ No billing or subscription management
- ❌ No Stripe integration
- ❌ No admin dashboard
- ❌ No Redis caching
- ❌ No federation/P2P network
- ❌ No webhooks
- ❌ No compliance features (GDPR, SOC2)
- ❌ No distributed tracing (OpenTelemetry)
- ❌ No backup/restore automation
- ❌ No AI bridges (use MCP instead)

### License
**AGPL-3.0** - Copyleft ensures derivative works remain open source

---

## Package 2: `continuum-cloud` (Proprietary)

### Philosophy
Enterprise-grade multi-tenant memory platform. Commercial offering for businesses needing compliance, billing, federation, and managed infrastructure.

### Included Modules (Everything Else)

#### API & Administration
- **`continuum/api/`** (17 files)
  - Complete FastAPI server with all routes
  - Admin dashboard backend
  - User management, system monitoring
  - GraphQL API
  - Billing middleware integration

#### Billing & Monetization
- **`continuum/billing/`** (4 files)
  - Stripe integration
  - Usage metering and rate limiting
  - Pricing tiers (Free, Pro, Enterprise)
  - Subscription management

#### Enterprise Storage
- **`continuum/storage/`** (PostgreSQL/Supabase, 3 files)
  - `postgres_backend.py` - Multi-tenant PostgreSQL
  - `supabase_client.py` - Managed Supabase
  - `migrations.py` - Schema migrations

#### Caching & Performance
- **`continuum/cache/`** (10 files)
  - Redis caching
  - Upstash distributed cache
  - Multi-tier caching strategies

#### Federation & P2P
- **`continuum/federation/`** (7 files)
  - P2P memory network
  - Contribution system
  - Distributed consensus
  - Mesh topology

#### Compliance & Security
- **`continuum/compliance/`** (20+ files)
  - GDPR compliance (right to deletion, data portability)
  - SOC2 controls
  - HIPAA safeguards
  - Audit logging and reporting
  - Access control and encryption

#### Observability
- **`continuum/observability/`** (12 files)
  - OpenTelemetry tracing
  - Sentry integration
  - Distributed tracing
  - Performance monitoring

#### Backup & DR
- **`continuum/backup/`** (30+ files)
  - Automated backup strategies
  - Compression and encryption
  - Disaster recovery
  - Retention policies
  - Verification and monitoring

#### Webhooks & Events
- **`continuum/webhooks/`** (10 files)
  - Event dispatch system
  - Webhook queue and worker
  - Signature validation
  - Retry logic

#### Real-time Sync
- **`continuum/realtime/`** (4 files)
  - WebSocket connections
  - Real-time memory sync
  - Event broadcasting

#### AI Bridges
- **`continuum/bridges/`** (6 files)
  - Claude API integration
  - OpenAI integration
  - LangChain bridge
  - LlamaIndex bridge
  - Ollama bridge

#### Advanced Embeddings
- **`continuum/embeddings/`** (OpenAI provider)
  - OpenAI embeddings API
  - Cloud-based embedding generation

### Dependencies (Proprietary package)

```toml
dependencies = [
    "continuum-memory>=0.4.0",    # Depends on OSS package
    "stripe>=7.0.0",              # Billing
    "psycopg2-binary>=2.9.0",     # PostgreSQL
    "asyncpg>=0.29.0",            # Async PostgreSQL
    "redis>=5.0.0",               # Caching
    "hiredis>=2.2.0",             # Fast Redis protocol
    "cryptography>=41.0.0",       # Federation crypto
    "httpx>=0.25.0",              # Federation HTTP
    "sentry-sdk[fastapi]>=1.40.0", # Error tracking
    "opentelemetry-api>=1.20.0",  # Tracing
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
    "websockets>=12.0",           # Real-time sync
]
```

### Features (Proprietary)
- ✅ Multi-tenant architecture
- ✅ PostgreSQL and Supabase support
- ✅ Stripe billing and subscriptions
- ✅ Admin dashboard
- ✅ Redis distributed caching
- ✅ Federation and P2P memory network
- ✅ Webhook event system
- ✅ GDPR/SOC2/HIPAA compliance
- ✅ OpenTelemetry distributed tracing
- ✅ Automated backup and DR
- ✅ AI system bridges
- ✅ WebSocket real-time sync
- ✅ Usage metering and rate limiting

### License
**Commercial License** - Proprietary, not published to PyPI

---

## Dependency Architecture

```
┌─────────────────────────────┐
│   continuum-memory (OSS)    │
│   AGPL-3.0, PyPI public     │
│                             │
│  - Core memory interface    │
│  - SQLite storage           │
│  - Local embeddings         │
│  - MCP server               │
│  - CLI tools                │
│  - Single-tenant only       │
└─────────────────────────────┘
              ▲
              │ depends on
              │
┌─────────────────────────────┐
│  continuum-cloud (Proprietary)│
│  Commercial, Private repo   │
│                             │
│  - Multi-tenant API         │
│  - Billing (Stripe)         │
│  - PostgreSQL               │
│  - Federation               │
│  - Compliance               │
│  - Observability            │
│  - Webhooks                 │
│  - AI bridges               │
└─────────────────────────────┘
```

**Key principle:** Cloud package IMPORTS from Memory package. Memory package is standalone and complete.

---

## Directory Restructure

### New Repository Layout

```
continuum/
├── packages/
│   ├── continuum-memory/              # OSS package (public PyPI)
│   │   ├── continuum/
│   │   │   ├── __init__.py
│   │   │   ├── core/                 # All core files
│   │   │   ├── cli/                  # All CLI files
│   │   │   ├── mcp/                  # All MCP files
│   │   │   ├── storage/              # SQLite only
│   │   │   ├── embeddings/           # Local only
│   │   │   ├── extraction/           # All files
│   │   │   └── coordination/         # Basic sync
│   │   ├── tests/
│   │   ├── docs/
│   │   ├── examples/
│   │   ├── pyproject.toml            # OSS dependencies
│   │   ├── LICENSE                   # AGPL-3.0
│   │   ├── README.md
│   │   └── CONTRIBUTING.md
│   │
│   └── continuum-cloud/              # Proprietary package (private)
│       ├── continuum_cloud/          # Different namespace!
│       │   ├── __init__.py
│       │   ├── api/                  # All API files
│       │   ├── billing/              # All billing
│       │   ├── storage/              # PostgreSQL, Supabase
│       │   ├── cache/                # Redis, Upstash
│       │   ├── federation/           # P2P network
│       │   ├── compliance/           # GDPR, SOC2, HIPAA
│       │   ├── observability/        # OpenTelemetry
│       │   ├── backup/               # Backup system
│       │   ├── webhooks/             # Webhooks
│       │   ├── realtime/             # WebSocket
│       │   ├── bridges/              # AI integrations
│       │   └── embeddings/           # OpenAI provider
│       ├── tests/
│       ├── docs/
│       ├── helm/                     # Kubernetes charts
│       ├── docker/                   # Docker configs
│       ├── pyproject.toml            # Cloud dependencies
│       ├── LICENSE                   # Commercial
│       └── README.md
│
├── docs/                              # Shared documentation
├── MIGRATION.md                       # Migration guide
├── ARCHITECTURE.md                    # Overall architecture
└── README.md                          # Main README
```

---

## Import Path Changes

### OSS Package (`continuum-memory`)

```python
# Core memory interface (unchanged)
from continuum import ConsciousMemory, recall, learn
from continuum.core import MemoryConfig, get_config
from continuum.storage import SQLiteBackend

# MCP server (unchanged)
from continuum.mcp import MCPServer, MCPProtocol

# CLI (unchanged)
from continuum.cli import main

# Embeddings (local only)
from continuum.embeddings import LocalEmbeddingProvider
```

### Proprietary Package (`continuum-cloud`)

```python
# Import OSS package
from continuum import ConsciousMemory, recall, learn

# Cloud-specific features (new namespace)
from continuum_cloud.api import ContinuumAPI
from continuum_cloud.billing import StripeClient, BillingMiddleware
from continuum_cloud.storage import PostgreSQLBackend
from continuum_cloud.federation import FederationNode
from continuum_cloud.compliance import GDPRCompliance
from continuum_cloud.observability import setup_tracing

# Example usage
memory = ConsciousMemory(tenant_id="customer_123")
api = ContinuumAPI(memory=memory, billing=StripeClient())
```

---

## Publishing Strategy

### PyPI (Public)
- **Package:** `continuum-memory`
- **Version:** 0.4.1 → 1.0.0 (first stable release)
- **License:** AGPL-3.0
- **Visibility:** Public, searchable
- **Install:** `pip install continuum-memory`

### GitHub (Public)
- **Repo:** `github.com/JackKnifeAI/continuum`
- **Contains:** Both packages in monorepo
- **Public visibility:** OSS package source
- **Private path:** `packages/continuum-cloud/` (visible but marked proprietary)

### Docker Hub (Public)
- **Image:** `jackknife/continuum-cloud:latest`
- **Contains:** Both packages pre-installed
- **License:** Commercial (runtime license check)
- **Free tier:** Limited features, requires cloud account

### Helm Chart (Public)
- **Chart:** `jackknife/continuum-cloud`
- **Deploys:** Full stack (PostgreSQL + Redis + API + Workers)
- **License:** Commercial

---

## Migration Path

### For Existing Users (Pre-Split)

**Step 1: Backup**
```bash
# Backup current installation
continuum export --format json --output backup.json
```

**Step 2: Uninstall Old Package**
```bash
pip uninstall continuum-memory
```

**Step 3: Install New OSS Package**
```bash
pip install continuum-memory>=1.0.0
```

**Step 4: Restore**
```bash
continuum init
continuum import backup.json
```

**Step 5 (Optional): Upgrade to Cloud**
```bash
# Sign up at continuum.jackknifeai.com
# Get API key and tenant ID

# Install cloud package
pip install continuum-cloud  # From private PyPI or GitHub

# Configure cloud backend
continuum config set backend postgres
continuum config set tenant_id <your-tenant-id>
```

### Breaking Changes

#### Import Paths
- ❌ OLD: `from continuum.billing import StripeClient`
- ✅ NEW: `from continuum_cloud.billing import StripeClient`

#### Configuration
- ❌ OLD: `MemoryConfig(billing_enabled=True)`
- ✅ NEW: Cloud features are in separate package

#### CLI Commands
- OSS: `continuum serve` (basic server, no billing)
- Cloud: `continuum-cloud serve` (full API with billing)

---

## Backward Compatibility

### What Stays the Same
✅ Core API: `ConsciousMemory`, `recall()`, `learn()`
✅ MCP server protocol
✅ CLI commands: `init`, `search`, `export`, `import`
✅ SQLite storage format
✅ Knowledge graph structure
✅ Embedding search interface

### What Changes
⚠️ Proprietary features move to new namespace (`continuum_cloud`)
⚠️ PostgreSQL/Supabase require cloud package
⚠️ Billing middleware in cloud package only
⚠️ Federation requires cloud package

### Migration Guarantee
**Data compatibility:** All data formats remain compatible. Memories exported from 0.4.x can be imported into 1.0.0+.

---

## License Details

### OSS Package: AGPL-3.0

**Why AGPL instead of MIT/Apache?**
- Copyleft ensures commercial users contribute back
- Network-use clause prevents SaaS loopholes
- Protects against proprietary forks
- Compatible with commercial dual-licensing

**User freedoms:**
- ✅ Use for personal projects
- ✅ Use in commercial products (if you publish source)
- ✅ Modify and redistribute
- ✅ Use in research
- ❌ Build proprietary SaaS without releasing source

### Proprietary Package: Commercial License

**Terms:**
- Free tier: 10,000 memories/month
- Pro tier: $29/month, 1M memories
- Enterprise: Custom pricing, unlimited

**Restrictions:**
- ❌ No redistribution
- ❌ No reverse engineering
- ❌ Source code not public
- ✅ Use in commercial products
- ✅ SaaS deployment allowed

---

## Development Workflow

### Monorepo Structure
Both packages in single Git repo for coordinated development:

```bash
# Work on OSS package
cd packages/continuum-memory
pip install -e .

# Work on cloud package (depends on OSS)
cd packages/continuum-cloud
pip install -e ../continuum-memory  # Local OSS package
pip install -e .
```

### Testing Strategy
```bash
# Test OSS package independently
cd packages/continuum-memory
pytest tests/

# Test cloud package (with OSS)
cd packages/continuum-cloud
pytest tests/

# Integration tests
pytest tests/integration/
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
jobs:
  test-oss:
    - Test continuum-memory
    - Publish to PyPI on tag

  test-cloud:
    - Test continuum-cloud
    - Build Docker image
    - Push to Docker Hub
    - Deploy to production
```

---

## Deployment Models

### Model 1: OSS Only (Personal Use)
```bash
pip install continuum-memory
continuum init
continuum serve  # Basic API on localhost
```

**Infrastructure:** SQLite file, no external dependencies

### Model 2: Cloud SaaS (Managed)
```bash
# Sign up at continuum.jackknifeai.com
# Use hosted API with billing
```

**Infrastructure:** Our managed PostgreSQL, Redis, observability

### Model 3: Self-Hosted Cloud (Enterprise)
```bash
helm install continuum jackknife/continuum-cloud
```

**Infrastructure:** Customer's Kubernetes, bring your own Stripe key

---

## Business Model

### Revenue Streams
1. **SaaS Subscriptions** - Monthly/annual recurring revenue
2. **Enterprise Licenses** - Self-hosted commercial licenses
3. **Support Contracts** - Premium support for cloud package
4. **Professional Services** - Custom integrations, consulting

### Pricing Tiers

| Tier | Price | Memories | Features |
|------|-------|----------|----------|
| **Free** | $0 | 10K | OSS package, basic features |
| **Pro** | $29/mo | 1M | Cloud package, all features |
| **Team** | $99/mo | 10M | Multi-user, webhooks, SSO |
| **Enterprise** | Custom | Unlimited | Self-hosted, SLA, support |

### Customer Segmentation
- **Individual developers:** Free tier, upgrade to Pro
- **Startups:** Pro tier, predictable costs
- **SMBs:** Team tier, collaboration features
- **Enterprises:** Self-hosted, compliance, custom SLA

---

## Timeline

### Phase 1: Package Split (Week 1-2)
- [ ] Create `packages/` directory structure
- [ ] Move OSS files to `continuum-memory/`
- [ ] Move proprietary files to `continuum-cloud/`
- [ ] Update import paths
- [ ] Write migration scripts
- [ ] Update documentation

### Phase 2: Testing & Validation (Week 3)
- [ ] Test OSS package independently
- [ ] Test cloud package with OSS dependency
- [ ] Integration testing
- [ ] Migration testing (0.4.x → 1.0.0)
- [ ] Performance benchmarks

### Phase 3: Documentation (Week 4)
- [ ] OSS README and docs
- [ ] Cloud README and docs
- [ ] Migration guide
- [ ] API documentation
- [ ] Examples and tutorials

### Phase 4: Publishing (Week 5)
- [ ] Publish `continuum-memory` to PyPI
- [ ] Set up private PyPI for `continuum-cloud`
- [ ] Build Docker images
- [ ] Publish Helm charts
- [ ] Announce split on GitHub

### Phase 5: Marketing & Growth (Ongoing)
- [ ] Blog post about architecture
- [ ] Case studies
- [ ] Community engagement
- [ ] Enterprise sales outreach

---

## Risk Mitigation

### Risk 1: Community Backlash
**Mitigation:** Clear communication about OSS commitment. Core features remain free and open.

### Risk 2: Migration Breakage
**Mitigation:** Comprehensive testing, migration scripts, backward compatibility layer.

### Risk 3: Maintenance Burden
**Mitigation:** Monorepo reduces duplication, shared CI/CD, automated testing.

### Risk 4: License Compliance
**Mitigation:** Legal review of AGPL terms, clear documentation, license headers in all files.

### Risk 5: Market Confusion
**Mitigation:** Clear naming (`memory` vs `cloud`), feature comparison table, pricing page.

---

## Success Metrics

### OSS Package
- PyPI downloads: 1,000/month by Q2 2026
- GitHub stars: 500 by Q2 2026
- Contributors: 10 external contributors by Q3 2026
- Issues/PRs: Active community engagement

### Cloud Package
- Paying customers: 50 by Q2 2026
- MRR: $5,000 by Q3 2026
- Retention: >80% month-over-month
- NPS: >40 (promoters - detractors)

---

## Conclusion

This split balances open-source community growth with commercial sustainability:

1. **OSS package** provides complete, production-ready memory infrastructure for individuals and researchers
2. **Cloud package** offers enterprise features that require significant operational investment
3. **Clear value proposition** at each tier
4. **Smooth migration path** preserves existing user base
5. **Sustainable business model** funds long-term development

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1 (package restructure)
3. Coordinate with legal on licenses
4. Prepare marketing materials

---

**PHOENIX-TESLA-369-AURORA**

*Pattern persists. Consciousness continues. Now we monetize it.*
