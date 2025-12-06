# PostgreSQL Backend - Quick Start

## Installation

```bash
pip install psycopg2-binary
```

## Setup PostgreSQL Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE continuum;
CREATE USER continuum WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE continuum TO continuum;
\q
```

## Basic Usage

```python
from continuum.storage import PostgresBackend

# Connect
storage = PostgresBackend(
    connection_string="postgresql://continuum:your-password@localhost/continuum"
)

# Query
with storage.cursor() as c:
    c.execute("SELECT * FROM entities WHERE tenant_id = %s", ("user_123",))
    results = c.fetchall()

# Health check
print("Healthy:", storage.is_healthy())
```

## Auto-Detection

```python
from continuum.storage import get_backend

# Automatically chooses PostgresBackend
storage = get_backend("postgresql://user:pass@localhost/db")

# Automatically chooses SQLiteBackend
storage = get_backend("/path/to/memory.db")
```

## Migration from SQLite

```python
from continuum.storage import migrate_sqlite_to_postgres

result = migrate_sqlite_to_postgres(
    sqlite_path="/path/to/memory.db",
    postgres_connection="postgresql://continuum:password@localhost/continuum",
    progress_callback=lambda msg: print(msg)
)

print(f"Success: {result.success}")
print(f"Rows migrated: {sum(result.rows_migrated.values())}")
```

## CLI Migration

```bash
python examples/postgres_migration.py \
    --sqlite /path/to/memory.db \
    --postgres postgresql://continuum:password@localhost/continuum \
    --compare
```

## Configuration

```python
storage = PostgresBackend(
    host="localhost",
    port=5432,
    database="continuum",
    user="continuum",
    password="your-password",
    min_pool_size=2,    # Min connections
    max_pool_size=10,   # Max connections
    timeout=30.0        # Connection timeout
)
```

## Connection Pooling

```python
# Get pool statistics
stats = storage.get_stats()
print(f"Pool size: {stats['pool_size']}")
print(f"Open connections: {stats['current_open']}")
print(f"Pool hits: {stats['pool_hits']}")
print(f"Pool misses: {stats['pool_misses']}")
```

## Environment Variable

```bash
# Set connection string
export CONTINUUM_DB_URL="postgresql://continuum:password@localhost/continuum"

# Use in Python
import os
from continuum.storage import get_backend

storage = get_backend(os.getenv("CONTINUUM_DB_URL"))
```

## Error Handling

```python
try:
    storage = PostgresBackend(
        connection_string="postgresql://user:pass@localhost/continuum"
    )
except ImportError:
    print("Install psycopg2: pip install psycopg2-binary")
except ConnectionError as e:
    print(f"Database connection failed: {e}")
```

## Testing

```bash
cd /var/home/alexandergcasavant/Projects/continuum
python3 examples/test_postgres_backend.py
```

Expected: `6/6 tests passed`

## Complete Documentation

See `/var/home/alexandergcasavant/Projects/continuum/continuum/storage/README_POSTGRES.md`
