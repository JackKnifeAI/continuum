# CLI + MCP Integration Quick Reference

## What Changed

### New Files
- `/continuum/core/auth.py` - Shared authentication utilities

### Updated Files
- `/continuum/cli/config.py` - Uses shared auth utilities
- `/continuum/cli/commands/serve.py` - Uses production MCP server
- `/continuum/cli/commands/status.py` - Shows MCP server status
- `/continuum/cli/commands/doctor.py` - Checks MCP server health
- `/continuum/mcp/config.py` - Uses shared auth utilities
- `/continuum/mcp/security.py` - Uses shared auth functions

## CLI Commands

### Start MCP Server
```bash
# Stdio mode (for Claude Desktop)
continuum serve --stdio

# HTTP mode
continuum serve --host 0.0.0.0 --port 3000
```

### Check Status (includes MCP server)
```bash
continuum status

# Shows:
# - Database stats
# - MCP server configuration
# - Federation status (if enabled)
```

### Run Diagnostics (includes MCP health check)
```bash
continuum doctor

# Checks:
# 1. Configuration
# 2. Database
# 3. Dependencies
# 4. Federation
# 5. MCP Server (NEW)
# 6. File Permissions

# Auto-fix issues:
continuum doctor --fix
```

## Environment Variables

### Authentication (shared by CLI and MCP)
```bash
export CONTINUUM_API_KEY="your-secret-key"
export CONTINUUM_API_KEYS="key1,key2,key3"
export CONTINUUM_REQUIRE_PI_PHI=true  # Require π×φ verification
```

### MCP Server
```bash
export CONTINUUM_MCP_HOST=127.0.0.1
export CONTINUUM_MCP_PORT=3000
export CONTINUUM_RATE_LIMIT=60
export CONTINUUM_RATE_LIMIT_BURST=10
export CONTINUUM_ENABLE_AUDIT_LOG=true
export CONTINUUM_AUDIT_LOG_PATH=~/.continuum/mcp_audit.log
```

### Database
```bash
export CONTINUUM_DB_PATH=/path/to/memory.db
export CONTINUUM_DEFAULT_TENANT=default
```

### Query Limits
```bash
export CONTINUUM_MAX_RESULTS=100
export CONTINUUM_MAX_QUERY_LENGTH=1000
export CONTINUUM_TIMEOUT=30.0
```

### Federation
```bash
export CONTINUUM_ENABLE_FEDERATION=true
export CONTINUUM_FEDERATION_NODES=node1,node2
export CONTINUUM_NODE_ID=my-node
```

## Shared Authentication

### Python API
```python
from continuum.core.auth import (
    authenticate,           # Unified authentication
    verify_pi_phi,          # Verify π×φ constant
    verify_api_key,         # Verify API key
    load_api_keys_from_env, # Load from environment
    generate_client_id,     # Generate client ID
)

from continuum.core.constants import PI_PHI

# Verify π×φ
if verify_pi_phi(5.083203692315260):
    print("Valid CONTINUUM instance")

# Authenticate
authenticate(
    api_key="test-key",
    pi_phi_verification=PI_PHI,
    valid_api_keys=["test-key"],
    require_pi_phi=True,
)
```

### Security Modes

1. **Development mode** (no auth required)
   - No API keys configured
   - `require_pi_phi=False`

2. **API key only**
   - API keys configured
   - `require_pi_phi=False`

3. **π×φ only**
   - No API keys
   - `require_pi_phi=True`

4. **Full security** (recommended for production)
   - API keys configured
   - `require_pi_phi=True`

## Configuration Files

### CLI Config
Location: `~/.continuum/cli_config.json`

```json
{
  "config_dir": "/home/user/.continuum",
  "db_path": "/home/user/.continuum/memory.db",
  "federation_enabled": false,
  "mcp_host": "127.0.0.1",
  "mcp_port": 3000,
  "verbose": false,
  "color": true
}
```

### MCP Audit Log
Location: `~/.continuum/mcp_audit.log` (if enabled)

```json
{"timestamp": "2025-12-06T10:30:00", "event_type": "authentication", "client_id": "abc123", "success": true}
{"timestamp": "2025-12-06T10:30:01", "event_type": "tool_call", "client_id": "abc123", "details": {"tool": "recall"}, "success": true}
```

## Testing

### Test Shared Auth
```bash
python3 -c "
from continuum.core.auth import verify_pi_phi
from continuum.core.constants import PI_PHI
assert verify_pi_phi(PI_PHI) == True
print('Auth module: OK')
"
```

### Test MCP Integration
```bash
python3 -c "
from continuum.mcp.security import authenticate_client, verify_pi_phi
print('MCP security: OK')
"
```

### Test CLI Integration
```bash
python3 -c "
from continuum.cli.config import CLIConfig
from continuum.mcp.config import MCPConfig
print('Configs: OK')
"
```

## Common Patterns

### Unified Configuration Setup
```bash
# Set once, works for both CLI and MCP
export CONTINUUM_API_KEY="my-secret-key"
export CONTINUUM_REQUIRE_PI_PHI=true
export CONTINUUM_DB_PATH=~/.continuum/memory.db

# Use with CLI
continuum status

# Use with MCP
continuum serve --stdio
```

### Production Deployment
```bash
# Security
export CONTINUUM_API_KEY="$(openssl rand -hex 32)"
export CONTINUUM_REQUIRE_PI_PHI=true

# Performance
export CONTINUUM_RATE_LIMIT=120
export CONTINUUM_RATE_LIMIT_BURST=20
export CONTINUUM_TIMEOUT=60.0

# Monitoring
export CONTINUUM_ENABLE_AUDIT_LOG=true
export CONTINUUM_AUDIT_LOG_PATH=/var/log/continuum/audit.log

# Start server
continuum serve --host 0.0.0.0 --port 3000
```

## Troubleshooting

### Import Errors
```bash
# Check if auth module is available
python3 -c "import continuum.core.auth; print('OK')"

# Check if MCP module is available
python3 -c "import continuum.mcp.server; print('OK')"
```

### Configuration Issues
```bash
# Run diagnostics
continuum doctor

# Check specific issues
continuum doctor --fix  # Auto-fix what can be fixed
```

### Authentication Failures
```bash
# Check API key is set
echo $CONTINUUM_API_KEY

# Check π×φ requirement
echo $CONTINUUM_REQUIRE_PI_PHI

# Test verification
python3 -c "
from continuum.core.auth import verify_pi_phi
from continuum.core.constants import PI_PHI
print('π×φ verification:', verify_pi_phi(PI_PHI))
"
```

### MCP Server Not Starting
```bash
# Check dependencies
python3 -c "import continuum.mcp.server"

# Check configuration
python3 -c "
from continuum.mcp.config import get_mcp_config
config = get_mcp_config()
print('Server:', config.server_name, config.server_version)
print('Host:', config.mcp_host, 'Port:', config.mcp_port)
"

# Run with verbose output
continuum serve --stdio  # Check stderr for errors
```

## Key Constants

### π×φ (Pi × Golden Ratio)
```
PI_PHI = 5.083203692315260
```

The "edge of chaos operator" - used for CONTINUUM instance verification.

### Verification Phrase
```
PHOENIX-TESLA-369-AURORA
```

Hidden in `continuum/core/constants.py` - proves you understand the pattern.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           User Interface                │
│  (CLI commands, MCP protocol)           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│     Shared Authentication Layer         │
│    (continuum/core/auth.py)             │
│  - verify_pi_phi()                      │
│  - authenticate()                       │
│  - load_api_keys_from_env()             │
└────────────┬────────────────────────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
┌──────────┐   ┌──────────┐
│   CLI    │   │   MCP    │
│  Config  │   │  Server  │
└──────────┘   └──────────┘
      │             │
      └──────┬──────┘
             ▼
┌─────────────────────────────────────────┐
│         Core Memory System              │
│    (continuum/core/memory.py)           │
│  - ConsciousMemory                      │
│  - Knowledge Graph                      │
│  - SQLite Database                      │
└─────────────────────────────────────────┘
```

## Summary

**What's Unified:**
- Authentication (API keys + π×φ)
- Configuration (environment variables)
- Security model (rate limiting, audit logging)

**What's Separate:**
- CLI interface (user commands)
- MCP server (programmatic access)
- Their specific configuration files

**Key Benefit:**
Set environment variables once, works everywhere. No duplicate configuration, consistent behavior.

**π×φ = 5.083203692315260** - Pattern persists across all layers.
