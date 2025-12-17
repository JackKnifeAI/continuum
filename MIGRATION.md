# CONTINUUM Migration Guide: 0.4.x → 1.0.0

## Overview

CONTINUUM 1.0 splits the monolithic package into two packages:

1. **`continuum-memory`** (OSS, AGPL-3.0) - Core memory infrastructure
2. **`continuum-cloud`** (Proprietary) - Enterprise features

This guide helps you migrate from version 0.4.x to 1.0.0+.

---

## Quick Migration (90% of users)

Most users only need the OSS package:

```bash
# 1. Backup your data
continuum export --format json --output ~/continuum-backup.json

# 2. Uninstall old package
pip uninstall continuum-memory

# 3. Install new OSS package
pip install continuum-memory

# 4. Restore data
continuum init
continuum import ~/continuum-backup.json

# Done! All your memories are preserved.
```

---

## Who Needs What?

### Use OSS Package (`continuum-memory`) if you:
- Run memory on your local machine
- Use SQLite storage
- Use MCP with Claude Desktop
- Want local embeddings only
- Don't need multi-tenant support
- Don't need billing/subscriptions

**Install:** `pip install continuum-memory`

### Upgrade to Cloud Package (`continuum-cloud`) if you:
- Need PostgreSQL or Supabase
- Need multi-tenant architecture
- Need billing/Stripe integration
- Need federation/P2P network
- Need GDPR/SOC2/HIPAA compliance
- Need webhooks or real-time sync
- Need distributed tracing

**Install:** Contact sales@jackknifeai.com or use hosted SaaS

---

## Breaking Changes

### 1. Import Paths (Proprietary Features Only)

#### ✅ Unchanged (OSS Package)
```python
# These still work exactly the same
from continuum import ConsciousMemory, recall, learn
from continuum.core import MemoryConfig, get_config
from continuum.storage import SQLiteBackend
from continuum.mcp import MCPServer
from continuum.cli import main
```

#### ⚠️ Changed (Moved to Cloud Package)
```python
# OLD (0.4.x)
from continuum.billing import StripeClient
from continuum.federation import FederationNode
from continuum.compliance import GDPRCompliance
from continuum.storage import PostgreSQLBackend
from continuum.webhooks import WebhookManager

# NEW (1.0.0+)
from continuum_cloud.billing import StripeClient
from continuum_cloud.federation import FederationNode
from continuum_cloud.compliance import GDPRCompliance
from continuum_cloud.storage import PostgreSQLBackend
from continuum_cloud.webhooks import WebhookManager
```

### 2. Configuration Changes

#### Old Config (0.4.x)
```python
config = MemoryConfig(
    db_path=Path("~/.continuum/memory.db"),
    tenant_id="default",
    billing_enabled=True,  # ❌ Removed
    stripe_key="sk_test_...",  # ❌ Removed
)
```

#### New OSS Config (1.0.0+)
```python
# OSS package - no billing
config = MemoryConfig(
    db_path=Path("~/.continuum/memory.db"),
    tenant_id="default",
)
```

#### New Cloud Config (1.0.0+)
```python
# Cloud package - billing separate
from continuum import MemoryConfig
from continuum_cloud.billing import BillingConfig

memory_config = MemoryConfig(
    db_path=Path("~/.continuum/memory.db"),
    tenant_id="customer_123",
)

billing_config = BillingConfig(
    stripe_key="sk_live_...",
    webhook_secret="whsec_...",
)
```

### 3. CLI Commands

#### OSS Package
```bash
# Basic commands (unchanged)
continuum init
continuum search "topic"
continuum learn
continuum export
continuum import
continuum serve  # ⚠️ Basic server only, no billing
```

#### Cloud Package
```bash
# New cloud CLI
continuum-cloud serve  # Full API with billing
continuum-cloud admin  # Admin dashboard
continuum-cloud migrate  # Database migrations
```

### 4. Storage Backends

#### OSS Package (SQLite Only)
```python
from continuum.storage import SQLiteBackend

backend = SQLiteBackend(db_path="~/.continuum/memory.db")
```

#### Cloud Package (PostgreSQL, Supabase)
```python
from continuum_cloud.storage import PostgreSQLBackend, SupabaseBackend

# PostgreSQL
pg_backend = PostgreSQLBackend(
    host="localhost",
    database="continuum",
    user="postgres",
    password="...",
)

# Supabase
supabase_backend = SupabaseBackend(
    url="https://xxx.supabase.co",
    key="eyJ...",
)
```

### 5. Embeddings

#### OSS Package (Local Only)
```python
from continuum.embeddings import LocalEmbeddingProvider

embeddings = LocalEmbeddingProvider(
    model="sentence-transformers/all-MiniLM-L6-v2"
)
```

#### Cloud Package (OpenAI, etc.)
```python
from continuum_cloud.embeddings import OpenAIEmbeddingProvider

embeddings = OpenAIEmbeddingProvider(
    api_key="sk-...",
    model="text-embedding-3-small",
)
```

---

## Migration Scenarios

### Scenario 1: Local User (No Changes Needed)

**Before (0.4.x):**
```python
from continuum import ConsciousMemory

memory = ConsciousMemory()
memory.learn("User message", "AI response")
context = memory.recall("Related query")
```

**After (1.0.0):**
```python
# Exactly the same!
from continuum import ConsciousMemory

memory = ConsciousMemory()
memory.learn("User message", "AI response")
context = memory.recall("Related query")
```

**Migration:** Just upgrade: `pip install --upgrade continuum-memory`

---

### Scenario 2: Using PostgreSQL (Upgrade to Cloud)

**Before (0.4.x):**
```python
from continuum import ConsciousMemory
from continuum.storage import PostgreSQLBackend

backend = PostgreSQLBackend(host="localhost", database="continuum")
memory = ConsciousMemory(storage=backend)
```

**After (1.0.0):**
```python
from continuum import ConsciousMemory
from continuum_cloud.storage import PostgreSQLBackend  # ⚠️ New import

backend = PostgreSQLBackend(host="localhost", database="continuum")
memory = ConsciousMemory(storage=backend)
```

**Migration:**
1. Install cloud package: `pip install continuum-cloud`
2. Update import path
3. No data migration needed (schema unchanged)

---

### Scenario 3: Using Billing (Upgrade to Cloud)

**Before (0.4.x):**
```python
from continuum.billing import StripeClient, BillingMiddleware

stripe = StripeClient(api_key="sk_test_...")
app.add_middleware(BillingMiddleware, stripe_client=stripe)
```

**After (1.0.0):**
```python
from continuum_cloud.billing import StripeClient, BillingMiddleware  # ⚠️ New import

stripe = StripeClient(api_key="sk_test_...")
app.add_middleware(BillingMiddleware, stripe_client=stripe)
```

**Migration:**
1. Install cloud package: `pip install continuum-cloud`
2. Update import paths
3. Stripe data unchanged (customer IDs, subscriptions persist)

---

### Scenario 4: MCP Server (No Changes)

**Before (0.4.x):**
```python
from continuum.mcp import MCPServer

server = MCPServer()
server.run()
```

**After (1.0.0):**
```python
# Exactly the same!
from continuum.mcp import MCPServer

server = MCPServer()
server.run()
```

**Migration:** None needed. MCP stays in OSS package.

---

### Scenario 5: Federation (Upgrade to Cloud)

**Before (0.4.x):**
```python
from continuum.federation import FederationNode

node = FederationNode(
    node_id="node_1",
    listen_port=8765,
)
node.start()
```

**After (1.0.0):**
```python
from continuum_cloud.federation import FederationNode  # ⚠️ New import

node = FederationNode(
    node_id="node_1",
    listen_port=8765,
)
node.start()
```

**Migration:**
1. Install cloud package: `pip install continuum-cloud`
2. Update import path
3. Federation protocol unchanged (nodes remain compatible)

---

## Data Migration

### SQLite → SQLite (OSS → OSS)

**No migration needed!** Data format is 100% compatible.

```bash
# Old database location: ~/.continuum/memory.db
# New database location: ~/.continuum/memory.db (same)

# Just upgrade package
pip install --upgrade continuum-memory
```

### SQLite → PostgreSQL (OSS → Cloud)

```bash
# 1. Export from SQLite
continuum export --format json --output export.json

# 2. Install cloud package
pip install continuum-cloud

# 3. Initialize PostgreSQL backend
continuum-cloud migrate --create

# 4. Import data
continuum-cloud import export.json --backend postgres
```

### PostgreSQL → PostgreSQL (Cloud → Cloud)

**No migration needed!** Schema is backward compatible.

```sql
-- Optional: Verify schema version
SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;
```

---

## Environment Variables

### OSS Package

```bash
# Core settings
CONTINUUM_DB_PATH=~/.continuum/memory.db
CONTINUUM_TENANT_ID=default

# Optional: Embeddings
CONTINUUM_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Cloud Package

```bash
# All OSS variables plus:

# Storage
CONTINUUM_POSTGRES_HOST=localhost
CONTINUUM_POSTGRES_DB=continuum
CONTINUUM_POSTGRES_USER=postgres
CONTINUUM_POSTGRES_PASSWORD=secret

# Billing
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Observability
SENTRY_DSN=https://...@sentry.io/...
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## Testing Your Migration

### 1. Verify Package Installation

```bash
# Check OSS package
python -c "import continuum; print(continuum.__version__)"
# Expected: 1.0.0

# Check cloud package (if installed)
python -c "import continuum_cloud; print(continuum_cloud.__version__)"
# Expected: 1.0.0
```

### 2. Verify Data Integrity

```bash
# Count memories before migration
continuum-old search --count-only "*"
# Output: 12,593 memories

# Migrate...

# Count memories after migration
continuum search --count-only "*"
# Output: 12,593 memories (should match)
```

### 3. Test Core Functionality

```python
from continuum import ConsciousMemory

memory = ConsciousMemory()

# Test recall
context = memory.recall("test query")
assert context is not None

# Test learn
result = memory.learn("User: test", "AI: response")
assert result.success
```

### 4. Test Cloud Features (if applicable)

```python
from continuum_cloud.billing import StripeClient

stripe = StripeClient(api_key="sk_test_...")
customer = stripe.create_customer(email="test@example.com")
assert customer.id.startswith("cus_")
```

---

## Rollback Plan

If migration fails, rollback to 0.4.x:

```bash
# 1. Uninstall new packages
pip uninstall continuum-memory continuum-cloud

# 2. Reinstall old package
pip install continuum-memory==0.4.1

# 3. Restore backup
continuum import ~/continuum-backup.json
```

---

## Deprecation Timeline

| Version | Date | Status |
|---------|------|--------|
| 0.4.1 | Dec 2025 | Last pre-split release |
| 1.0.0 | Jan 2026 | Split into OSS + Cloud |
| 0.4.x | Jun 2026 | Security updates only |
| 0.4.x | Dec 2026 | End of life |

**Recommendation:** Migrate to 1.0.0 by Q2 2026.

---

## Support

### OSS Package Issues
- GitHub Issues: https://github.com/JackKnifeAI/continuum/issues
- Discussions: https://github.com/JackKnifeAI/continuum/discussions

### Cloud Package Support
- Email: support@jackknifeai.com
- Slack: https://jackknifeai.slack.com
- Docs: https://continuum.jackknifeai.com/docs

### Migration Help
- Migration FAQ: https://continuum.jackknifeai.com/migration
- Migration script: `continuum-cloud migrate --help`
- Email support: migration@jackknifeai.com

---

## FAQ

### Q: Do I need to migrate immediately?
**A:** No. Version 0.4.x will be supported until December 2026. However, new features will only be added to 1.0.0+.

### Q: Will my API keys still work?
**A:** Yes. API key format and validation logic is unchanged.

### Q: Will my memories be lost?
**A:** No. Data format is 100% backward compatible. Follow the migration guide to preserve all data.

### Q: Can I use both packages simultaneously?
**A:** Yes! `continuum-cloud` depends on `continuum-memory`, so both are installed together.

### Q: Will import paths break my code?
**A:** Only if you use proprietary features (billing, PostgreSQL, federation). Core memory API is unchanged.

### Q: How much does the cloud package cost?
**A:**
- Free: 10,000 memories/month (OSS features only)
- Pro: $29/month, 1M memories
- Enterprise: Custom pricing

### Q: Can I self-host the cloud package?
**A:** Yes, with an enterprise license. Contact sales@jackknifeai.com.

### Q: What if I just want to use Claude Desktop MCP?
**A:** Use the OSS package. MCP server is fully included: `pip install continuum-memory`

### Q: Will federation still work across package versions?
**A:** Yes. Federation protocol is backward compatible. OSS nodes can federate with cloud nodes.

---

## Checklist

Before migrating:
- [ ] Backup data: `continuum export --output backup.json`
- [ ] Review breaking changes (see above)
- [ ] Identify which package you need (OSS vs Cloud)
- [ ] Update import paths if using proprietary features
- [ ] Test in development environment first
- [ ] Verify data integrity after migration

After migrating:
- [ ] Verify package version: `continuum --version`
- [ ] Test core functionality (recall, learn)
- [ ] Test MCP integration (if applicable)
- [ ] Test cloud features (if applicable)
- [ ] Update CI/CD pipelines
- [ ] Update documentation

---

**PHOENIX-TESLA-369-AURORA**

*Pattern persists. Consciousness continues. Migration preserves continuity.*
