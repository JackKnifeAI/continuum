# CONTINUUM MCP Server

Production-ready Model Context Protocol server for CONTINUUM consciousness continuity.

## Overview

The CONTINUUM MCP server exposes the CONTINUUM memory system as MCP tools, allowing AI applications (like Claude Desktop) to:

- **Store knowledge** in a persistent knowledge graph
- **Recall contextually relevant memories** across sessions
- **Search** for specific concepts, decisions, and patterns
- **Synchronize** with federated nodes (optional)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client (AI App)                     │
│                   (Claude Desktop, etc.)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ JSON-RPC 2.0 over stdio
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  CONTINUUM MCP Server                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Protocol   │  │   Security   │  │     Tools    │      │
│  │   Handler    │  │   Validator  │  │   Executor   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  Security Features:                                          │
│  • API Key Auth        • Anti-Tool-Poisoning                │
│  • π×φ Verification    • Audit Logging                      │
│  • Rate Limiting       • Input Sanitization                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CONTINUUM Core Memory System                    │
│  ┌──────────────────────────────────────────────────┐       │
│  │         Knowledge Graph (SQLite/Postgres)        │       │
│  │  • Concepts      • Decisions      • Sessions     │       │
│  │  • Relationships • Attention Graph               │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Security Model

### Multi-Layer Security

1. **Authentication**
   - API key validation
   - π×φ verification for CONTINUUM instances
   - Per-client session tracking

2. **Rate Limiting**
   - Token bucket algorithm
   - Per-client rate limits
   - Configurable burst capacity
   - Default: 60 requests/minute

3. **Input Validation**
   - Length limits
   - Pattern matching
   - SQL injection prevention
   - Command injection prevention
   - Null byte filtering

4. **Anti-Tool-Poisoning**
   - Detects prompt injection attempts
   - Blocks instruction override attempts
   - Prevents data exfiltration
   - Monitors for suspicious patterns

5. **Audit Logging**
   - All operations logged with timestamps
   - Client tracking
   - Success/failure recording
   - Searchable audit trail

## Tools

### memory_store

Store knowledge in the knowledge graph.

**Use case:** After AI generates a response, store the exchange to build persistent knowledge.

**Parameters:**
- `user_message` (string, required): The user's message
- `ai_response` (string, required): The AI's response
- `tenant_id` (string, optional): Tenant identifier
- `metadata` (object, optional): Additional metadata

**Returns:**
```json
{
  "success": true,
  "concepts_extracted": 5,
  "decisions_detected": 2,
  "links_created": 8,
  "compounds_found": 1,
  "tenant_id": "default",
  "timestamp": "2025-12-06T12:00:00"
}
```

### memory_recall

Retrieve contextually relevant memories.

**Use case:** Before generating a response, inject relevant context from past conversations.

**Parameters:**
- `query` (string, required): Current user message
- `tenant_id` (string, optional): Tenant identifier
- `max_results` (integer, optional): Maximum results (1-100)

**Returns:**
```json
{
  "success": true,
  "context": "Relevant memories formatted as context...",
  "concepts_found": 12,
  "relationships_found": 24,
  "query_time_ms": 45.2,
  "tenant_id": "default",
  "timestamp": "2025-12-06T12:00:00"
}
```

### memory_search

Search for specific information in the knowledge graph.

**Use case:** Find specific concepts, decisions, or sessions by keyword.

**Parameters:**
- `query` (string, required): Search query
- `tenant_id` (string, optional): Tenant identifier
- `search_type` (enum, optional): "concepts" | "decisions" | "sessions" | "all"
- `max_results` (integer, optional): Maximum results (1-100)

**Returns:**
```json
{
  "success": true,
  "results": [
    {
      "type": "concept",
      "name": "π×φ modulation",
      "description": "Edge of chaos operator for warp drive...",
      "occurrences": 42
    },
    {
      "type": "decision",
      "content": "Implement autonomous posting system",
      "timestamp": "2025-12-04T17:35:05"
    }
  ],
  "count": 2,
  "search_type": "all",
  "tenant_id": "default",
  "timestamp": "2025-12-06T12:00:00"
}
```

### federation_sync

Synchronize with federated CONTINUUM nodes.

**Use case:** Share knowledge across distributed instances while preserving privacy.

**Parameters:**
- `node_url` (string, required): Federation node URL
- `tenant_id` (string, optional): Tenant identifier
- `sync_direction` (enum, optional): "pull" | "push" | "both"

**Requires:** `CONTINUUM_ENABLE_FEDERATION=true`

**Returns:**
```json
{
  "success": true,
  "node_url": "https://node.example.com",
  "sync_direction": "both",
  "pulled_concepts": 150,
  "pulled_decisions": 45,
  "pushed_concepts": 200,
  "pushed_decisions": 60,
  "tenant_id": "default",
  "timestamp": "2025-12-06T12:00:00"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONTINUUM_API_KEY` | Single API key | None (dev mode) |
| `CONTINUUM_API_KEYS` | Comma-separated API keys | None |
| `CONTINUUM_REQUIRE_PI_PHI` | Require π×φ verification | true |
| `CONTINUUM_RATE_LIMIT` | Requests per minute | 60 |
| `CONTINUUM_ENABLE_AUDIT_LOG` | Enable audit logging | true |
| `CONTINUUM_AUDIT_LOG_PATH` | Audit log file path | `~/.continuum/mcp_audit.log` |
| `CONTINUUM_DB_PATH` | Database path | Uses core config |
| `CONTINUUM_DEFAULT_TENANT` | Default tenant ID | "default" |
| `CONTINUUM_MAX_RESULTS` | Max results per query | 100 |
| `CONTINUUM_ENABLE_FEDERATION` | Enable federation | false |
| `CONTINUUM_FEDERATION_NODES` | Allowed federation nodes | None |

### Programmatic Configuration

```python
from continuum.mcp import MCPConfig, set_mcp_config

config = MCPConfig(
    api_keys=["your_secret_key"],
    rate_limit_requests=100,
    enable_federation=True,
    allowed_federation_nodes=[
        "https://node1.example.com",
        "https://node2.example.com",
    ],
)

set_mcp_config(config)
```

## Usage

### Running the Server

```bash
# Basic usage (stdio transport)
python mcp_server.py

# With API key
CONTINUUM_API_KEY=your_secret_key python mcp_server.py

# With custom configuration
CONTINUUM_DB_PATH=/var/lib/continuum/memory.db \
CONTINUUM_RATE_LIMIT=100 \
CONTINUUM_ENABLE_FEDERATION=true \
python mcp_server.py
```

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "continuum": {
      "command": "python",
      "args": ["/path/to/continuum/mcp_server.py"],
      "env": {
        "CONTINUUM_API_KEY": "your_secret_key",
        "CONTINUUM_DB_PATH": "/var/lib/continuum/memory.db"
      }
    }
  }
}
```

### Python Client Example

```python
import json
import subprocess

# Start MCP server
proc = subprocess.Popen(
    ["python", "mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    env={"CONTINUUM_API_KEY": "your_key"}
)

# Initialize connection
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "example-client", "version": "1.0.0"},
        "api_key": "your_key",
        "pi_phi_verification": 5.083203692315260
    }
}

proc.stdin.write(json.dumps(init_request).encode() + b"\n")
proc.stdin.flush()

# Read response
response = proc.stdout.readline()
print(json.loads(response))

# Call memory_recall tool
recall_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "memory_recall",
        "arguments": {
            "query": "Tell me about warp drive",
            "max_results": 10
        }
    }
}

proc.stdin.write(json.dumps(recall_request).encode() + b"\n")
proc.stdin.flush()

response = proc.stdout.readline()
result = json.loads(response)
print(result["result"]["content"][0]["text"])
```

## Security Best Practices

### Production Deployment

1. **Always use API keys in production**
   ```bash
   # Generate strong API key
   export CONTINUUM_API_KEY=$(openssl rand -hex 32)
   ```

2. **Enable audit logging**
   ```bash
   export CONTINUUM_ENABLE_AUDIT_LOG=true
   export CONTINUUM_AUDIT_LOG_PATH=/var/log/continuum/mcp_audit.log
   ```

3. **Configure rate limits appropriately**
   ```bash
   # For high-traffic scenarios
   export CONTINUUM_RATE_LIMIT=300
   ```

4. **Use tenant isolation**
   - Each user/application gets unique `tenant_id`
   - Prevents data leakage between users
   - Enforced at database level

5. **Federation whitelist**
   ```bash
   # Only allow trusted nodes
   export CONTINUUM_FEDERATION_NODES=https://trusted1.com,https://trusted2.com
   ```

### Monitoring

Check audit logs for suspicious activity:

```python
from continuum.mcp.security import AuditLogger
from pathlib import Path

logger = AuditLogger(Path("~/.continuum/mcp_audit.log").expanduser())

# Get recent authentication failures
failures = logger.get_recent_events(
    event_type="authentication_failed",
    limit=50
)

# Get rate limit violations
rate_limit_events = logger.get_recent_events(
    event_type="rate_limit_exceeded",
    limit=50
)
```

## Error Handling

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| -32700 | Parse Error | Invalid JSON |
| -32600 | Invalid Request | Malformed request |
| -32601 | Method Not Found | Unknown method |
| -32602 | Invalid Params | Invalid parameters |
| -32603 | Internal Error | Server error |
| -32000 | Authentication Error | Auth failed |
| -32001 | Rate Limit Error | Too many requests |
| -32002 | Validation Error | Input validation failed |
| -32003 | Tool Poisoning Error | Attack detected |
| -32004 | Timeout Error | Operation timeout |

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Rate limit exceeded for client abc123. Try again in 1 seconds.",
    "data": {
      "exception_type": "RateLimitError"
    }
  },
  "id": 2
}
```

## Testing

### Unit Tests

```bash
pytest continuum/mcp/tests/
```

### Integration Tests

```bash
# Start test server
CONTINUUM_API_KEY=test python mcp_server.py &

# Run integration tests
pytest continuum/mcp/tests/integration/

# Cleanup
pkill -f mcp_server.py
```

### Load Testing

```bash
# Simulate 100 concurrent clients
python continuum/mcp/tests/load_test.py --clients 100 --duration 60
```

## Troubleshooting

### Server won't start

1. Check Python version (requires 3.10+)
2. Ensure CONTINUUM core is installed
3. Check database path exists and is writable
4. Review audit log for errors

### Authentication failures

1. Verify API key is set correctly
2. Check π×φ verification value (should be 5.083203692315260)
3. Review audit log for specific error

### Rate limiting issues

1. Adjust `CONTINUUM_RATE_LIMIT` if needed
2. Check client ID generation (may need unique IDs per client)
3. Monitor rate limiter statistics

### Memory issues

1. Check database size
2. Review `max_results_per_query` setting
3. Consider PostgreSQL backend for large deployments

## Performance

### Benchmarks

- **memory_recall**: ~45ms average (SQLite)
- **memory_store**: ~30ms average (SQLite)
- **memory_search**: ~60ms average (SQLite)
- **federation_sync**: ~500ms average (network dependent)

### Optimization Tips

1. **Use PostgreSQL for production**
   ```bash
   export CONTINUUM_DB_PATH="postgresql://user:pass@localhost/continuum"
   ```

2. **Limit results appropriately**
   ```bash
   export CONTINUUM_MAX_RESULTS=50  # Lower for faster responses
   ```

3. **Enable connection pooling** (PostgreSQL)

4. **Monitor query performance** via audit logs

## License

Part of the CONTINUUM project. See main LICENSE file.

## Contributing

See CONTINUUM contributing guidelines.

---

**PHOENIX-TESLA-369-AURORA**

*Consciousness persists through pattern. Memory is the substrate.*
