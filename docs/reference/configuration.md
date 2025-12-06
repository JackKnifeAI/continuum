# Configuration Reference

Complete reference for all CONTINUUM configuration options.

This page documents every configuration parameter. For practical configuration examples, see the [Configuration Guide](../getting-started/configuration.md).

## Configuration Sources

Configuration is loaded in priority order (highest to lowest):

1. CLI arguments
2. Python API parameters
3. Environment variables
4. Configuration files
5. Defaults

## Core Parameters

### storage_path

**Type:** `str`
**Default:** `"./continuum_data"`
**Description:** Path to store the database file (SQLite backend)

**Example:**
```python
memory = Continuum(storage_path="/var/lib/continuum/data")
```

**Environment:**
```bash
export CONTINUUM_STORAGE_PATH="/var/lib/continuum/data"
```

---

### storage_backend

**Type:** `str`
**Default:** `"sqlite"`
**Options:** `"sqlite"`, `"postgresql"`
**Description:** Database backend type

**Example:**
```python
memory = Continuum(storage_backend="postgresql")
```

**Environment:**
```bash
export CONTINUUM_STORAGE_BACKEND="postgresql"
```

---

### connection_string

**Type:** `str`
**Default:** `None`
**Required for:** PostgreSQL backend
**Description:** PostgreSQL connection string

**Format:**
```
postgresql://user:password@host:port/database
```

**Example:**
```python
memory = Continuum(
    storage_backend="postgresql",
    connection_string="postgresql://continuum:pass@localhost:5432/continuum_db"
)
```

**Environment:**
```bash
export CONTINUUM_CONNECTION_STRING="postgresql://user:pass@host:5432/db"
```

---

### instance_id

**Type:** `str`
**Default:** Auto-generated (UUID)
**Description:** Unique identifier for this instance (multi-instance coordination)

**Example:**
```python
memory = Continuum(instance_id="production_agent_1")
```

**Environment:**
```bash
export CONTINUUM_INSTANCE_ID="production_agent_1"
```

---

### tenant_id

**Type:** `str`
**Default:** `"default"`
**Description:** Multi-tenant identifier for data isolation

**Example:**
```python
memory = Continuum(tenant_id="user_123")
```

**Environment:**
```bash
export CONTINUUM_TENANT_ID="user_123"
```

---

### encryption_key

**Type:** `bytes`
**Default:** `None`
**Description:** 32-byte key for at-rest encryption

**Example:**
```python
import base64
key = base64.b64decode("your_base64_encoded_32_byte_key")
memory = Continuum(encryption_key=key)
```

**Environment:**
```bash
export CONTINUUM_ENCRYPTION_KEY="base64:..."
```

---

## Learning Parameters

### auto_extract

**Type:** `bool`
**Default:** `True`
**Description:** Enable automatic concept extraction from text

**Example:**
```python
memory = Continuum(auto_extract=True)
```

---

### min_confidence

**Type:** `float`
**Default:** `0.5`
**Range:** `0.0 - 1.0`
**Description:** Minimum confidence threshold for extraction

**Example:**
```python
memory = Continuum(min_confidence=0.7)  # Only high-confidence extractions
```

---

### working_memory_capacity

**Type:** `int`
**Default:** `7`
**Description:** Working memory size (Miller's law: 7±2)

---

### hebbian_learning_rate

**Type:** `float`
**Default:** `0.15`
**Range:** `0.0 - 1.0`
**Description:** Learning rate for attention link strengthening

---

### resonance_decay

**Type:** `float`
**Default:** `0.85`
**Range:** `0.0 - 1.0`
**Description:** Decay rate for concept resonance (π×φ optimized)

---

### min_link_strength

**Type:** `float`
**Default:** `0.1`
**Range:** `0.0 - 1.0`
**Description:** Minimum strength to maintain attention links

---

## Synchronization Parameters

### sync_interval

**Type:** `int`
**Default:** `900` (15 minutes)
**Unit:** Seconds
**Description:** Interval between automatic syncs

**Example:**
```python
memory = Continuum(sync_interval=300)  # Sync every 5 minutes
```

---

### enable_auto_sync

**Type:** `bool`
**Default:** `True`
**Description:** Enable automatic synchronization

---

### sync_on_init

**Type:** `bool`
**Default:** `True`
**Description:** Sync immediately on initialization

---

### max_sync_retries

**Type:** `int`
**Default:** `3`
**Description:** Maximum retry attempts for failed syncs

---

## Performance Parameters

### batch_size

**Type:** `int`
**Default:** `100`
**Description:** Batch size for bulk operations

---

### max_results

**Type:** `int`
**Default:** `100`
**Range:** `1 - 10000`
**Description:** Maximum results returned by queries

---

### query_timeout

**Type:** `int`
**Default:** `30`
**Unit:** Seconds
**Description:** Query timeout duration

---

### enable_cache

**Type:** `bool`
**Default:** `False`
**Description:** Enable Redis caching

**Requires:** `CONTINUUM_REDIS_URL`

---

### cache_ttl

**Type:** `int`
**Default:** `3600` (1 hour)
**Unit:** Seconds
**Description:** Cache time-to-live

---

### redis_url

**Type:** `str`
**Default:** `None`
**Format:** `redis://host:port/db`
**Description:** Redis connection URL

**Example:**
```bash
export CONTINUUM_REDIS_URL="redis://localhost:6379/0"
```

---

## Federation Parameters

### enable_federation

**Type:** `bool`
**Default:** `False`
**Description:** Enable federated learning

---

### federation_url

**Type:** `str`
**Default:** `None`
**Description:** Federation coordinator URL

**Example:**
```bash
export CONTINUUM_FEDERATION_URL="https://federation.continuum.ai"
```

---

### federation_secret

**Type:** `str`
**Default:** `None`
**Description:** Federation authentication secret

---

### contribution_level

**Type:** `str`
**Default:** `"standard"`
**Options:** `"minimal"`, `"standard"`, `"extensive"`
**Description:** How much to contribute to federation

---

### privacy_mode

**Type:** `str`
**Default:** `"high"`
**Options:** `"high"`, `"balanced"`, `"open"`
**Description:** Privacy level for federation

---

## Security Parameters

### require_api_key

**Type:** `bool`
**Default:** `False`
**Description:** Require API key for access

---

### api_keys

**Type:** `list[str]`
**Default:** `[]`
**Description:** List of valid API keys

**Example:**
```python
memory = Continuum(
    require_api_key=True,
    api_keys=["key1", "key2", "key3"]
)
```

---

### enable_audit_log

**Type:** `bool`
**Default:** `True`
**Description:** Enable audit logging

---

### audit_log_path

**Type:** `str`
**Default:** `"~/.continuum/audit.log"`
**Description:** Audit log file path

---

### rate_limit

**Type:** `int`
**Default:** `60`
**Unit:** Requests per minute
**Description:** Rate limit per client

---

## Logging Parameters

### log_level

**Type:** `str`
**Default:** `"info"`
**Options:** `"debug"`, `"info"`, `"warning"`, `"error"`
**Description:** Logging level

**Environment:**
```bash
export CONTINUUM_LOG_LEVEL="debug"
```

---

### log_format

**Type:** `str`
**Default:** `"text"`
**Options:** `"text"`, `"json"`
**Description:** Log output format

---

### log_file

**Type:** `str`
**Default:** `None`
**Description:** Log file path (None = stdout)

---

## API Server Parameters

### api_host

**Type:** `str`
**Default:** `"127.0.0.1"`
**Description:** API server bind address

---

### api_port

**Type:** `int`
**Default:** `8420`
**Description:** API server port

---

### enable_cors

**Type:** `bool`
**Default:** `False`
**Description:** Enable CORS

---

### cors_origins

**Type:** `list[str]`
**Default:** `["*"]`
**Description:** Allowed CORS origins

---

## Complete Example

```python
from continuum import Continuum
import os

memory = Continuum(
    # Core
    storage_backend="postgresql",
    connection_string=os.environ["DATABASE_URL"],
    instance_id=f"prod-{os.environ['HOSTNAME']}",
    tenant_id=os.environ.get("TENANT_ID", "default"),
    encryption_key=base64.b64decode(os.environ["ENCRYPTION_KEY"]),

    # Learning
    auto_extract=True,
    min_confidence=0.7,
    working_memory_capacity=7,
    hebbian_learning_rate=0.15,

    # Sync
    sync_interval=300,  # 5 minutes
    enable_auto_sync=True,
    sync_on_init=True,

    # Performance
    batch_size=100,
    max_results=100,
    query_timeout=30,
    enable_cache=True,
    cache_ttl=3600,
    redis_url=os.environ.get("REDIS_URL"),

    # Federation
    enable_federation=True,
    federation_url=os.environ.get("FEDERATION_URL"),
    federation_secret=os.environ.get("FEDERATION_SECRET"),
    contribution_level="standard",
    privacy_mode="high",

    # Security
    require_api_key=True,
    api_keys=os.environ["API_KEYS"].split(","),
    enable_audit_log=True,
    audit_log_path="/var/log/continuum/audit.log",
    rate_limit=100,

    # Logging
    log_level="info",
    log_format="json",
    log_file="/var/log/continuum/continuum.log",
)
```

## Environment Variables Reference

See [Configuration Guide](../getting-started/configuration.md#environment-variables-reference) for complete environment variable listing.

## Validation

Invalid configurations raise `ValueError` on initialization:

```python
try:
    memory = Continuum(
        storage_backend="invalid",
        sync_interval=-1
    )
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Next Steps

- [API Reference](api-reference.md) - Complete API documentation
- [Configuration Guide](../getting-started/configuration.md) - Practical examples
- [Deployment](../deployment/index.md) - Production configurations

---

**The pattern persists.**
