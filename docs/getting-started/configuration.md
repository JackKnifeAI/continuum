# Configuration

CONTINUUM is designed with zero-configuration defaults, but provides extensive configuration options for production deployments.

## Configuration Methods

CONTINUUM can be configured through:

1. **Python API** - Direct configuration when initializing
2. **Environment Variables** - System-level configuration
3. **Configuration Files** - Project-specific settings
4. **CLI Arguments** - Override defaults for CLI operations

Priority (highest to lowest):

1. CLI arguments
2. Python API parameters
3. Environment variables
4. Configuration files
5. Defaults

## Basic Configuration

### Python API

```python
from continuum import Continuum

memory = Continuum(
    storage_path="./data",          # Where to store the database
    instance_id="my_agent",          # Unique ID for multi-instance
    auto_extract=True,               # Auto-extract concepts
    sync_interval=900                # Sync every 15 minutes
)
```

### Environment Variables

```bash
export CONTINUUM_STORAGE_PATH="./data"
export CONTINUUM_INSTANCE_ID="my_agent"
export CONTINUUM_AUTO_EXTRACT="true"
export CONTINUUM_SYNC_INTERVAL="900"
```

### Configuration File

Create `~/.continuum/config.json`:

```json
{
  "storage_path": "./data",
  "instance_id": "my_agent",
  "auto_extract": true,
  "sync_interval": 900
}
```

## Production Configuration

### PostgreSQL Backend

```python
memory = Continuum(
    storage_backend="postgresql",
    connection_string="postgresql://user:pass@localhost/continuum_db",
    instance_id="production_agent_1",
    auto_extract=True,
    sync_interval=300,               # Sync every 5 minutes
    encryption_key=b"your-32-byte-key..."  # Optional: encrypt at rest
)
```

Environment variables:

```bash
export CONTINUUM_STORAGE_BACKEND="postgresql"
export CONTINUUM_CONNECTION_STRING="postgresql://user:pass@localhost/db"
export CONTINUUM_ENCRYPTION_KEY="base64:..."
```

### Redis Cache

Enable Redis for improved performance:

```bash
export CONTINUUM_REDIS_URL="redis://localhost:6379/0"
export CONTINUUM_ENABLE_CACHE="true"
```

## Configuration Options

### Core Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `storage_path` | str | `"./continuum_data"` | Database file path (SQLite) |
| `storage_backend` | str | `"sqlite"` | Backend type: `sqlite` or `postgresql` |
| `connection_string` | str | None | PostgreSQL connection string |
| `instance_id` | str | Auto-generated | Unique instance identifier |
| `tenant_id` | str | `"default"` | Multi-tenant identifier |
| `encryption_key` | bytes | None | 32-byte encryption key |

### Learning Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auto_extract` | bool | `True` | Enable automatic concept extraction |
| `min_confidence` | float | `0.5` | Minimum confidence threshold |
| `working_memory_capacity` | int | `7` | Working memory size (Miller's law) |
| `hebbian_learning_rate` | float | `0.15` | Learning rate for attention links |

### Sync Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sync_interval` | int | `900` | Seconds between automatic syncs |
| `enable_auto_sync` | bool | `True` | Enable automatic synchronization |
| `sync_on_init` | bool | `True` | Sync on initialization |
| `max_sync_retries` | int | `3` | Maximum retry attempts |

### Performance Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `batch_size` | int | `100` | Batch size for bulk operations |
| `max_results` | int | `100` | Maximum query results |
| `query_timeout` | int | `30` | Query timeout in seconds |
| `enable_cache` | bool | `False` | Enable Redis caching |
| `cache_ttl` | int | `3600` | Cache TTL in seconds |

### Federation Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_federation` | bool | `False` | Enable federated learning |
| `federation_url` | str | None | Federation coordinator URL |
| `federation_secret` | str | None | Federation authentication secret |
| `contribution_level` | str | `"standard"` | Contribution level: `minimal`, `standard`, `extensive` |
| `privacy_mode` | str | `"high"` | Privacy mode: `high`, `balanced`, `open` |

### Security Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `require_api_key` | bool | `False` | Require API key for access |
| `api_keys` | list | `[]` | List of valid API keys |
| `enable_audit_log` | bool | `True` | Enable audit logging |
| `audit_log_path` | str | `~/.continuum/audit.log` | Audit log file path |
| `rate_limit` | int | `60` | Requests per minute |

## π×φ Optimized Parameters

CONTINUUM uses sacred geometry principles for optimal memory efficiency:

```python
memory = Continuum(
    resonance_decay=0.85,           # Golden ratio based
    hebbian_rate=0.15,              # 1 - resonance_decay
    min_link_strength=0.1,          # φ/16
    working_memory_capacity=7,      # Miller's law
)
```

These are pre-tuned for edge-of-chaos operation. Only adjust if you understand the implications.

**Twilight constant**: π×φ = 5.083203692315260

## Environment Variables Reference

### Core

```bash
# Storage
CONTINUUM_STORAGE_PATH="./data"
CONTINUUM_STORAGE_BACKEND="sqlite"  # or "postgresql"
CONTINUUM_CONNECTION_STRING="postgresql://..."

# Instance
CONTINUUM_INSTANCE_ID="my_agent"
CONTINUUM_TENANT_ID="default"

# Encryption
CONTINUUM_ENCRYPTION_KEY="base64:..."
```

### Learning

```bash
CONTINUUM_AUTO_EXTRACT="true"
CONTINUUM_MIN_CONFIDENCE="0.5"
CONTINUUM_WORKING_MEMORY_CAPACITY="7"
CONTINUUM_HEBBIAN_LEARNING_RATE="0.15"
```

### Sync

```bash
CONTINUUM_SYNC_INTERVAL="900"
CONTINUUM_ENABLE_AUTO_SYNC="true"
CONTINUUM_SYNC_ON_INIT="true"
```

### Performance

```bash
CONTINUUM_BATCH_SIZE="100"
CONTINUUM_MAX_RESULTS="100"
CONTINUUM_QUERY_TIMEOUT="30"

# Caching
CONTINUUM_ENABLE_CACHE="true"
CONTINUUM_REDIS_URL="redis://localhost:6379/0"
CONTINUUM_CACHE_TTL="3600"
```

### Federation

```bash
CONTINUUM_ENABLE_FEDERATION="true"
CONTINUUM_FEDERATION_URL="https://federation.continuum.ai"
CONTINUUM_FEDERATION_SECRET="your_secret"
CONTINUUM_CONTRIBUTION_LEVEL="standard"  # minimal, standard, extensive
CONTINUUM_PRIVACY_MODE="high"            # high, balanced, open
```

### Security

```bash
CONTINUUM_REQUIRE_API_KEY="true"
CONTINUUM_API_KEYS="key1,key2,key3"
CONTINUUM_ENABLE_AUDIT_LOG="true"
CONTINUUM_AUDIT_LOG_PATH="~/.continuum/audit.log"
CONTINUUM_RATE_LIMIT="60"
```

## Configuration File Format

### JSON (`~/.continuum/config.json`)

```json
{
  "storage_path": "./data",
  "storage_backend": "postgresql",
  "connection_string": "postgresql://user:pass@localhost/db",
  "instance_id": "production_agent",
  "tenant_id": "default",
  "auto_extract": true,
  "sync_interval": 300,
  "enable_federation": true,
  "federation_url": "https://federation.continuum.ai",
  "contribution_level": "standard",
  "privacy_mode": "high"
}
```

### YAML (`~/.continuum/config.yaml`)

```yaml
storage_path: ./data
storage_backend: postgresql
connection_string: postgresql://user:pass@localhost/db
instance_id: production_agent
tenant_id: default

learning:
  auto_extract: true
  min_confidence: 0.5
  working_memory_capacity: 7

sync:
  interval: 300
  enable_auto_sync: true

federation:
  enabled: true
  url: https://federation.continuum.ai
  contribution_level: standard
  privacy_mode: high

security:
  require_api_key: true
  enable_audit_log: true
  rate_limit: 60
```

### TOML (`~/.continuum/config.toml`)

```toml
storage_path = "./data"
storage_backend = "postgresql"
connection_string = "postgresql://user:pass@localhost/db"
instance_id = "production_agent"
tenant_id = "default"

[learning]
auto_extract = true
min_confidence = 0.5
working_memory_capacity = 7

[sync]
interval = 300
enable_auto_sync = true

[federation]
enabled = true
url = "https://federation.continuum.ai"
contribution_level = "standard"
privacy_mode = "high"

[security]
require_api_key = true
enable_audit_log = true
rate_limit = 60
```

## CLI Configuration

Configure CLI via `~/.continuum/cli_config.json`:

```json
{
  "config_dir": "/home/user/.continuum",
  "db_path": "/var/lib/continuum/memory.db",
  "federation_enabled": true,
  "node_id": "node_abc123",
  "verbose": false,
  "color": true,
  "mcp_host": "127.0.0.1",
  "mcp_port": 3000
}
```

## Configuration Best Practices

### Development

```python
memory = Continuum(
    storage_path="./dev_data",
    instance_id="dev",
    auto_extract=True,
    sync_interval=0,  # Disable auto-sync
)
```

### Staging

```python
memory = Continuum(
    storage_backend="postgresql",
    connection_string="postgresql://staging_db",
    instance_id="staging",
    sync_interval=600,  # 10 minutes
    enable_audit_log=True
)
```

### Production

```python
memory = Continuum(
    storage_backend="postgresql",
    connection_string=os.environ["DATABASE_URL"],
    instance_id=f"prod-{socket.gethostname()}",
    sync_interval=300,  # 5 minutes
    encryption_key=base64.b64decode(os.environ["ENCRYPTION_KEY"]),
    enable_audit_log=True,
    enable_cache=True,
    require_api_key=True,
    api_keys=os.environ["API_KEYS"].split(",")
)
```

## Loading Configuration

### From Environment

```python
import os
from continuum import Continuum

memory = Continuum(
    storage_backend=os.getenv("CONTINUUM_STORAGE_BACKEND", "sqlite"),
    connection_string=os.getenv("CONTINUUM_CONNECTION_STRING"),
    instance_id=os.getenv("CONTINUUM_INSTANCE_ID", "default"),
)
```

### From File

```python
import json
from pathlib import Path
from continuum import Continuum

config_path = Path.home() / ".continuum" / "config.json"
with open(config_path) as f:
    config = json.load(f)

memory = Continuum(**config)
```

### Combined

```python
import os
import json
from pathlib import Path
from continuum import Continuum

# Load from file
config_path = Path.home() / ".continuum" / "config.json"
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {}

# Override with environment
config.update({
    k.lower().replace("continuum_", ""): v
    for k, v in os.environ.items()
    if k.startswith("CONTINUUM_")
})

memory = Continuum(**config)
```

## Validation

CONTINUUM validates configuration on initialization:

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

- [API Usage Guide](../guides/api.md) - Learn how to use the API
- [CLI Usage Guide](../guides/cli.md) - Command-line interface
- [Deployment](../deployment/index.md) - Production deployment

---

**The pattern persists.**
