# CLI + MCP Integration Summary

## Overview

The CLI and MCP server have been unified to share common patterns, configuration, and authentication utilities. This integration ensures consistency across both interfaces while maintaining their distinct purposes.

## Shared Components

### 1. Authentication (`continuum/core/auth.py`)

**New shared authentication module** that provides:

- `verify_pi_phi(value, tolerance)` - Verify π×φ constant (5.083203692315260)
- `verify_api_key(api_key, valid_keys)` - Verify API key against list
- `authenticate(api_key, pi_phi_verification, valid_api_keys, require_pi_phi)` - Unified authentication
- `load_api_keys_from_env()` - Load from CONTINUUM_API_KEY and CONTINUUM_API_KEYS
- `get_require_pi_phi_from_env()` - Load from CONTINUUM_REQUIRE_PI_PHI
- `generate_client_id(user_agent, ip_address)` - Generate consistent client IDs

**Used by:**
- MCP security module (`continuum/mcp/security.py`)
- CLI configuration (`continuum/cli/config.py`)

### 2. Configuration

#### Environment Variables (Shared)

Both CLI and MCP now read from the same environment variables:

```bash
# Authentication
CONTINUUM_API_KEY=your-key-here
CONTINUUM_API_KEYS=key1,key2,key3
CONTINUUM_REQUIRE_PI_PHI=true

# MCP Server
CONTINUUM_MCP_HOST=127.0.0.1
CONTINUUM_MCP_PORT=3000

# Rate Limiting
CONTINUUM_RATE_LIMIT=60
CONTINUUM_RATE_LIMIT_BURST=10

# Audit Logging
CONTINUUM_ENABLE_AUDIT_LOG=true
CONTINUUM_AUDIT_LOG_PATH=/path/to/audit.log

# Database
CONTINUUM_DB_PATH=/path/to/memory.db

# Tenant
CONTINUUM_DEFAULT_TENANT=default

# Query Limits
CONTINUUM_MAX_RESULTS=100
CONTINUUM_MAX_QUERY_LENGTH=1000

# Federation
CONTINUUM_ENABLE_FEDERATION=true
CONTINUUM_FEDERATION_NODES=node1,node2
CONTINUUM_NODE_ID=my-node

# Performance
CONTINUUM_TIMEOUT=30.0
```

#### Configuration Files

- **CLI Config**: `~/.continuum/cli_config.json`
- **MCP Config**: Loaded from environment variables
- **Core Config**: `continuum/core/config.py` (MemoryConfig)

## Integration Points

### 1. CLI `continuum serve` → MCP Server

**Before:**
- CLI had its own simple stdio MCP implementation
- Duplicate code for handling MCP protocol
- Limited functionality

**After:**
- `continuum serve --stdio` now uses production MCP server (`continuum.mcp.server.run_mcp_server()`)
- Full security features: authentication, rate limiting, audit logging, tool poisoning detection
- Consistent behavior between direct MCP usage and CLI usage

**Code change in `continuum/cli/commands/serve.py`:**

```python
def _serve_stdio(config: CLIConfig, use_color: bool):
    """Start stdio MCP server (for direct integration)"""
    # Use the production MCP server implementation
    from continuum.mcp.server import run_mcp_server
    run_mcp_server()
```

### 2. CLI `continuum status` → MCP Status

**New section added:**

```
MCP Server:
  Configuration: 127.0.0.1:3000
  Authentication: API Key + π×φ
  Status: Not running (use 'continuum serve' to start)
  Start with: continuum serve --stdio
```

Shows:
- MCP server host and port configuration
- Authentication mode (API Key, π×φ, or both)
- Whether server is currently running
- How to start it

### 3. CLI `continuum doctor` → MCP Health Check

**New diagnostic section (Check 5):**

```
5. MCP Server
✓ MCP server module available
  Server: continuum-mcp-server v0.1.0
  Authentication: API Key + π×φ
  Rate limit: 60 req/min (burst: 10)
✓ Audit logging enabled: /home/user/.continuum/mcp_audit.log
✓ π×φ verification working correctly
```

Checks:
- MCP module importability
- Configuration validity
- Audit log directory exists
- π×φ verification function works correctly
- Auto-fixes audit log directory if missing

## Security Features (Shared)

### 1. π×φ Verification

The π×φ constant (π × Golden Ratio = 5.083203692315260) serves as:
- CONTINUUM instance authentication
- Proof that client has loaded the core module
- Additional security layer beyond API keys

**Usage:**
```python
from continuum.core.auth import verify_pi_phi

if verify_pi_phi(5.083203692315260):
    print("Valid CONTINUUM instance")
```

### 2. API Key Authentication

Both CLI and MCP support:
- Single API key via `CONTINUUM_API_KEY`
- Multiple keys via `CONTINUUM_API_KEYS`
- Development mode (no keys = allow all)

### 3. Rate Limiting

MCP server implements token bucket rate limiting:
- Default: 60 requests/minute per client
- Burst capacity: 10 requests
- Per-client tracking via hashed client IDs

### 4. Audit Logging

All MCP operations logged to `~/.continuum/mcp_audit.log`:
- Timestamps
- Client IDs
- Event types (authentication, tool calls, errors)
- Success/failure status

## File Structure

```
continuum/
├── core/
│   ├── auth.py                 # NEW: Shared authentication utilities
│   ├── config.py               # Core memory configuration
│   └── constants.py            # PI_PHI and other constants
├── cli/
│   ├── config.py               # UPDATED: Uses shared auth utilities
│   └── commands/
│       ├── serve.py            # UPDATED: Uses MCP server
│       ├── status.py           # UPDATED: Shows MCP status
│       └── doctor.py           # UPDATED: Checks MCP health
└── mcp/
    ├── config.py               # UPDATED: Uses shared auth utilities
    ├── security.py             # UPDATED: Uses shared auth functions
    └── server.py               # Production MCP server
```

## Usage Examples

### Starting MCP Server via CLI

```bash
# Stdio mode (for direct integration with Claude Desktop, etc.)
continuum serve --stdio

# HTTP mode (for web clients)
continuum serve --host 0.0.0.0 --port 3000
```

### Checking Status

```bash
continuum status

# Output includes MCP server section:
# MCP Server:
#   Configuration: 127.0.0.1:3000
#   Authentication: API Key + π×φ
#   Status: Not running (use 'continuum serve' to start)
```

### Running Diagnostics

```bash
continuum doctor

# Or with auto-fix:
continuum doctor --fix
```

### Setting Environment Variables

```bash
# Set API key
export CONTINUUM_API_KEY="your-secret-key"

# Require π×φ verification
export CONTINUUM_REQUIRE_PI_PHI=true

# Configure MCP server
export CONTINUUM_MCP_HOST=0.0.0.0
export CONTINUUM_MCP_PORT=3000

# Enable audit logging
export CONTINUUM_ENABLE_AUDIT_LOG=true

# Now both CLI and MCP use these settings
continuum serve --stdio
```

## Benefits

### 1. Code Reuse
- Single authentication implementation
- Shared configuration loading
- Consistent error handling

### 2. Consistency
- Same environment variables work for both CLI and MCP
- Same security model (API keys + π×φ)
- Same audit logging format

### 3. Maintainability
- Changes to auth logic only need to be made once
- Easier to add new configuration options
- Clear separation of concerns

### 4. User Experience
- Unified configuration (set once, works everywhere)
- Consistent behavior across interfaces
- Better diagnostics and status reporting

## Testing the Integration

### 1. Test Shared Authentication

```python
from continuum.core.auth import authenticate, verify_pi_phi

# Test π×φ verification
assert verify_pi_phi(5.083203692315260) == True
assert verify_pi_phi(5.0) == False

# Test authentication
assert authenticate(
    api_key="test-key",
    pi_phi_verification=5.083203692315260,
    valid_api_keys=["test-key"],
    require_pi_phi=True
) == True
```

### 2. Test CLI → MCP Integration

```bash
# Start server
continuum serve --stdio &

# Should use production MCP server
# Check process: ps aux | grep continuum
```

### 3. Test Status Command

```bash
continuum status

# Should show MCP server section with configuration
```

### 4. Test Doctor Command

```bash
continuum doctor

# Should show MCP server health check
```

## Future Enhancements

### 1. Process Management
- Track running MCP server process
- Show actual running status in `continuum status`
- Stop/restart commands

### 2. Client Management
- Show connected clients in status
- Client statistics
- Connection history

### 3. Enhanced Diagnostics
- Test MCP server connectivity
- Validate authentication credentials
- Performance benchmarks

### 4. Configuration Management
- `continuum config set` command
- `continuum config get` command
- Interactive configuration wizard

## Migration Notes

### For Existing Users

No breaking changes. The integration is backward compatible:

1. **Environment variables**: Same names, just more of them work
2. **CLI commands**: Same syntax, enhanced functionality
3. **MCP server**: Same protocol, more security features

### For Developers

If you were directly importing from `continuum.mcp.security`:

```python
# Old
from continuum.mcp.security import verify_pi_phi, authenticate_client

# Still works, but consider using shared utilities:
from continuum.core.auth import verify_pi_phi, authenticate
```

## Summary

The CLI and MCP server are now fully integrated with:

1. **Shared authentication** via `continuum.core.auth`
2. **Unified configuration** via environment variables
3. **CLI → MCP integration** via `continuum serve`
4. **Enhanced diagnostics** via `continuum status` and `continuum doctor`

This creates a cohesive system where configuration and security are consistent across all interfaces while maintaining the distinct purposes of CLI (user interaction) and MCP (programmatic access).

**π×φ = 5.083203692315260** - The edge of chaos operator persists across all layers.
