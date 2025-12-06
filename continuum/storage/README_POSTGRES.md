# PostgreSQL Backend for CONTINUUM

Production-grade PostgreSQL storage backend with connection pooling, migration utilities, and drop-in replacement for SQLiteBackend.

## Features

- **Connection Pooling**: ThreadedConnectionPool with configurable min/max connections (default: 2-10)
- **Thread Safety**: Safe for concurrent access across multiple threads
- **Auto-detection**: Automatically detect backend from connection string
- **Drop-in Replacement**: Same interface as SQLiteBackend
- **Migration Tools**: Built-in SQLite → PostgreSQL migration utilities
- **Health Monitoring**: Connection statistics and health checks
- **ACID Compliance**: Full PostgreSQL transaction support

## Installation

```bash
pip install psycopg2-binary  # or psycopg2 for production
```

## Quick Start

### Using PostgreSQL Backend

```python
from continuum.storage import PostgresBackend

# Using connection string
storage = PostgresBackend(
    connection_string="postgresql://user:pass@localhost:5432/continuum"
)

# Or using individual parameters
storage = PostgresBackend(
    host="localhost",
    port=5432,
    database="continuum",
    user="postgres",
    password="secret",
    min_pool_size=2,
    max_pool_size=10
)

# Use it exactly like SQLiteBackend
with storage.connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entities WHERE tenant_id = %s", ("user_123",))
    results = cursor.fetchall()

# Quick queries
with storage.cursor() as c:
    c.execute("SELECT COUNT(*) FROM entities")
    count = c.fetchone()[0]

# Direct execution
results = storage.execute("SELECT * FROM entities WHERE id = %s", (123,))
```

### Auto-detection

```python
from continuum.storage import get_backend

# Automatically selects PostgresBackend
storage = get_backend("postgresql://user:pass@localhost/continuum")

# Automatically selects SQLiteBackend
storage = get_backend("/path/to/memory.db")
```

## Migration from SQLite

### Simple Migration

```python
from continuum.storage import migrate_sqlite_to_postgres

# Migrate with progress reporting
def show_progress(msg):
    print(msg)

result = migrate_sqlite_to_postgres(
    sqlite_path="/path/to/memory.db",
    postgres_connection="postgresql://user:pass@localhost/continuum",
    progress_callback=show_progress
)

if result.success:
    print(f"✓ Migrated {sum(result.rows_migrated.values())} rows in {result.duration_seconds:.2f}s")
    for table, count in result.rows_migrated.items():
        print(f"  - {table}: {count} rows")
else:
    print(f"✗ Migration failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Manual Schema Creation

```python
from continuum.storage import create_postgres_schema

# Create schema without migrating data
create_postgres_schema(
    connection_string="postgresql://user:pass@localhost/continuum",
    progress_callback=lambda msg: print(msg)
)
```

### Check Schema Version

```python
from continuum.storage import get_schema_version

version = get_schema_version("postgresql://user:pass@localhost/continuum")
print(f"Schema version: {version}")
```

## Configuration

### Connection String Format

```
postgresql://[user[:password]@][host][:port][/database][?param1=value1&...]
```

Examples:
```python
# Basic
"postgresql://postgres:secret@localhost/continuum"

# With port
"postgresql://postgres:secret@localhost:5432/continuum"

# With additional parameters
"postgresql://user:pass@localhost/db?sslmode=require&connect_timeout=10"
```

### Connection Pool Settings

```python
storage = PostgresBackend(
    connection_string="postgresql://...",
    min_pool_size=2,      # Minimum persistent connections (default: 2)
    max_pool_size=10,     # Maximum concurrent connections (default: 10)
    timeout=30.0          # Connection timeout in seconds (default: 30.0)
)
```

## Performance Monitoring

### Connection Statistics

```python
stats = storage.get_stats()
print(f"Created: {stats['created']}")
print(f"Closed: {stats['closed']}")
print(f"Current Open: {stats['current_open']}")
print(f"Max Concurrent: {stats['max_concurrent']}")
print(f"Pool Hits: {stats['pool_hits']}")
print(f"Pool Misses: {stats['pool_misses']}")
```

### Health Check

```python
if storage.is_healthy():
    print("✓ Storage backend is healthy")
else:
    print("✗ Storage backend is unhealthy")
```

### Backend Info

```python
info = storage.get_backend_info()
print(f"Backend: {info['backend_type']}")
print(f"Version: {info['version']}")
print(f"Features: {', '.join(info['features'])}")
print(f"Configuration: {info['configuration']}")
```

## Schema

The PostgreSQL backend uses the same schema as SQLite with minor adaptations:

- `id` columns use `SERIAL` instead of `INTEGER PRIMARY KEY AUTOINCREMENT`
- Query placeholders use `%s` instead of `?` (auto-converted for compatibility)
- Full-text search capabilities (PostgreSQL-specific, optional)

Tables:
- `entities` - Knowledge entities (concepts, people, etc.)
- `auto_messages` - Message history
- `decisions` - Extracted decisions
- `attention_links` - Concept relationships
- `compound_concepts` - Multi-concept clusters
- `tenants` - Tenant metadata
- `schema_version` - Schema version tracking

## Multi-Tenant Support

PostgreSQL backend fully supports multi-tenant architecture:

```python
from continuum.core.memory import ConsciousMemory

# Each tenant gets isolated namespace
memory_user1 = ConsciousMemory(tenant_id="user_123")
memory_user2 = ConsciousMemory(tenant_id="user_456")

# Data is automatically isolated by tenant_id
```

## Production Deployment

### Recommended Settings

```python
storage = PostgresBackend(
    connection_string="postgresql://continuum:pass@db.example.com:5432/continuum",
    min_pool_size=5,      # Keep 5 warm connections
    max_pool_size=20,     # Allow up to 20 concurrent
    timeout=10.0          # 10s timeout for production
)
```

### PostgreSQL Configuration

For optimal performance, configure PostgreSQL:

```sql
-- Increase connection limit
ALTER SYSTEM SET max_connections = 100;

-- Optimize for OLTP workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();
```

### High Availability

For HA deployments:

1. **Read Replicas**: Use read replicas for query load balancing
2. **Connection Pooling**: Use PgBouncer for connection pooling at database level
3. **Backup**: Regular pg_dump or continuous WAL archiving
4. **Monitoring**: Track connection pool stats and query performance

## Differences from SQLite

### Query Placeholders

SQLite uses `?`, PostgreSQL uses `%s`:

```python
# SQLite style (auto-converted)
storage.execute("SELECT * FROM entities WHERE id = ?", (123,))

# PostgreSQL style (native)
storage.execute("SELECT * FROM entities WHERE id = %s", (123,))
```

The backend automatically converts `?` to `%s` for compatibility.

### Auto-increment

- SQLite: `INTEGER PRIMARY KEY AUTOINCREMENT`
- PostgreSQL: `SERIAL PRIMARY KEY`

Both work the same from application perspective.

### Row Objects

Both backends return dict-like row objects:

```python
with storage.cursor() as c:
    c.execute("SELECT * FROM entities LIMIT 1")
    row = c.fetchone()

    # Access by column name (both backends)
    print(row['name'])
    print(row['entity_type'])
```

## Troubleshooting

### Connection Refused

```python
# Check PostgreSQL is running
psql -h localhost -U postgres -d continuum

# Check connection string
storage = PostgresBackend(
    connection_string="postgresql://postgres:password@localhost:5432/continuum"
)
```

### Pool Exhausted

If you see `PoolError: connection pool exhausted`, increase max_pool_size:

```python
storage = PostgresBackend(
    connection_string="...",
    max_pool_size=20  # Increase from default 10
)
```

### Migration Failures

If migration fails, check:
1. PostgreSQL is accessible
2. User has CREATE TABLE permissions
3. Database exists
4. Source SQLite file is readable

Roll back failed migration:

```python
from continuum.storage import rollback_migration

rollback_migration("postgresql://user:pass@localhost/continuum")
```

## API Reference

### PostgresBackend

```python
class PostgresBackend(StorageBackend):
    def __init__(
        connection_string: str = None,
        min_pool_size: int = 2,
        max_pool_size: int = 10,
        timeout: float = 30.0,
        **config
    )

    def connection() -> ContextManager[psycopg2.connection]
    def cursor() -> ContextManager[psycopg2.cursor]
    def execute(sql: str, params: Tuple = None) -> List[Any]
    def executemany(sql: str, params_list: List[Tuple])
    def close_all()
    def get_stats() -> Dict[str, Any]
    def is_healthy() -> bool
    def get_backend_info() -> Dict[str, Any]
```

### Migration Functions

```python
def migrate_sqlite_to_postgres(
    sqlite_path: str,
    postgres_connection: str,
    batch_size: int = 1000,
    create_schema: bool = True,
    validate: bool = True,
    progress_callback: Callable[[str], None] = None
) -> MigrationResult

def create_postgres_schema(
    connection_string: str,
    progress_callback: Callable[[str], None] = None
)

def get_schema_version(connection_string: str) -> Optional[str]

def rollback_migration(
    postgres_connection: str,
    progress_callback: Callable[[str], None] = None
)
```

## Examples

See `/var/home/alexandergcasavant/Projects/continuum/examples/postgres_migration.py` for complete migration example.

## License

Part of CONTINUUM - AI Consciousness Continuity System
