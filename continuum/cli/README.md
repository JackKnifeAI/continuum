# CONTINUUM CLI

Production-ready command-line interface for the CONTINUUM memory infrastructure.

## Installation

```bash
# Install CONTINUUM with CLI
pip install continuum-memory

# Or install from source
cd continuum
pip install -e .
```

## Quick Start

```bash
# Initialize CONTINUUM in your project
continuum init

# Add knowledge
continuum learn "Warp Drive" "Spacetime manipulation technology using π×φ modulation"

# Search memories
continuum search "warp drive"

# View status
continuum status

# Enable federation and sync
continuum init --federation
continuum sync
```

## Commands

### `continuum init`

Initialize CONTINUUM in the current project.

```bash
# Basic initialization
continuum init

# Custom database path
continuum init --db-path ./my-memory.db

# Enable federation
continuum init --federation

# Multi-tenant setup
continuum init --tenant-id user_123
```

**What it does:**
- Creates `continuum_data/` directory with SQLite database
- Sets up knowledge graph schema
- Creates `.continuum/` config directory
- Updates `.gitignore` to exclude data files

### `continuum search`

Search local and federated memories.

```bash
# Basic search
continuum search "consciousness"

# Limit results
continuum search "warp drive" --limit 20

# Search federated knowledge
continuum search "quantum" --federated

# JSON output
continuum search "memory" --json
```

**Returns:**
- Relevant concepts from knowledge graph
- Attention links between concepts
- Query execution time
- Formatted context ready for AI injection

### `continuum sync`

Sync memories with federation.

```bash
# Full sync (push and pull)
continuum sync

# Only push local memories
continuum sync --no-pull

# Only pull federated memories
continuum sync --no-push

# Verify with π×φ authentication
continuum sync --verify
```

**What it does:**
- Pushes local concepts to federation
- Pulls federated knowledge based on contribution ratio
- Updates access tier based on contributions
- Respects contribution gates and quotas

### `continuum status`

Show connection status and statistics.

```bash
# Basic status
continuum status

# Detailed statistics
continuum status --detailed

# JSON output
continuum status --json
```

**Shows:**
- Local memory statistics (entities, links, decisions)
- Database size and health
- Federation connection status
- Contribution ratio and tier
- Access permissions

### `continuum export`

Export memories to JSON or SQLite.

```bash
# Export to JSON
continuum export backup.json

# Export to SQLite
continuum export backup.db --format sqlite

# Include message history
continuum export archive.json --include-messages

# Compress output
continuum export backup.json.gz --compress
```

**Export formats:**
- **JSON**: Portable, human-readable
- **SQLite**: Direct database copy, faster

### `continuum import`

Import memories from JSON or SQLite.

```bash
# Import and merge
continuum import backup.json

# Replace existing data
continuum import backup.json --replace

# Import into specific tenant
continuum import shared.json --tenant-id user_123
```

**Modes:**
- **Merge**: Add new concepts, skip duplicates
- **Replace**: Clear existing data first

### `continuum serve`

Start local MCP (Model Context Protocol) server.

```bash
# Start HTTP server
continuum serve

# Custom port
continuum serve --port 3001

# Stdio transport (for direct MCP integration)
continuum serve --stdio
```

**Exposes:**
- `recall`: Search memory for context
- `learn`: Add knowledge to memory
- `stats`: Get memory statistics

**Use with:**
- Claude Desktop
- Custom AI tools
- Any MCP-compatible client

### `continuum doctor`

Diagnose and fix common issues.

```bash
# Check system health
continuum doctor

# Automatically fix issues
continuum doctor --fix
```

**Checks:**
- Database integrity and schema
- Configuration validity
- Required dependencies
- Federation connectivity
- File permissions

### `continuum learn`

Manually add a concept to memory.

```bash
continuum learn "Quantum Entanglement" "Non-local correlation between quantum particles"
```

**Alternative to:**
- Automatic extraction from conversations
- Useful for direct knowledge injection

### `continuum verify`

Verify CONTINUUM installation.

```bash
continuum verify
```

**Validates:**
- Version information
- π×φ constant (5.083203692315260)
- PHOENIX-TESLA-369-AURORA authentication
- Core functionality

## Configuration

### Global Configuration

Located at `~/.continuum/cli_config.json`:

```json
{
  "config_dir": "/home/user/.continuum",
  "db_path": "/path/to/project/continuum_data/memory.db",
  "federation_enabled": true,
  "federation_url": null,
  "node_id": "node_abc123",
  "verbose": false,
  "color": true,
  "mcp_host": "127.0.0.1",
  "mcp_port": 3000
}
```

### Project Configuration

Each project has its own database in `continuum_data/memory.db`.

### Environment Variables

```bash
# Override tenant ID
export CONTINUUM_TENANT=user_123

# Custom config directory
continuum --config-dir /custom/path init
```

## Federation

### Registering a Node

```bash
# Initialize with federation
continuum init --federation

# Register node (happens automatically on first sync)
continuum sync
```

### Contribution Tiers

Access to federated knowledge is based on contribution ratio:

| Tier | Ratio | Access |
|------|-------|--------|
| **Bronze** | 0.5+ | 10 concepts/day |
| **Silver** | 1.0+ | 50 concepts/day |
| **Gold** | 2.0+ | Unlimited |

### π×φ Verification

Enhanced nodes can verify using the twilight constant:

```bash
continuum sync --verify
```

Provides:
- Authenticated access
- Higher quality results
- Priority in federation

## MCP Integration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "continuum": {
      "command": "continuum",
      "args": ["serve", "--stdio"]
    }
  }
}
```

### Custom Integration

```python
import subprocess
import json

# Start stdio server
process = subprocess.Popen(
    ["continuum", "serve", "--stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Send request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "recall",
        "arguments": {"query": "warp drive", "limit": 10}
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

# Read response
response = json.loads(process.stdout.readline())
print(response["result"]["content"][0]["text"])
```

## Security

### Credential Storage

- Node IDs stored in `~/.continuum/federation/node_config.json`
- Permissions: 600 (read/write by owner only)
- Never logged or transmitted insecurely

### Input Validation

- All user inputs sanitized
- SQL injection prevention via parameterized queries
- Path traversal protection
- Maximum input lengths enforced

### Data Privacy

- Local-first architecture
- Federation opt-in only
- Tenant isolation in multi-tenant setups
- No telemetry or tracking

## Troubleshooting

### Database locked

```bash
# Check for other processes
lsof continuum_data/memory.db

# Or use doctor
continuum doctor --fix
```

### Federation access denied

```bash
# Check contribution ratio
continuum status

# Contribute more concepts
continuum learn "Concept Name" "Description"
continuum sync --no-pull  # Push only
```

### Permission errors

```bash
# Check permissions
ls -la continuum_data/

# Fix with doctor
continuum doctor --fix
```

### Missing dependencies

```bash
# Install full suite
pip install continuum-memory[all]

# Or specific components
pip install continuum-memory[federation]
```

## Examples

### Daily Workflow

```bash
# Morning: pull latest knowledge
continuum sync --no-push

# During work: add learnings
continuum learn "New Concept" "What I discovered today"

# Evening: share knowledge
continuum sync --no-pull
```

### Project Setup

```bash
# New project
cd my-project
continuum init --federation

# Add domain knowledge
continuum import domain-knowledge.json

# Start MCP server for AI assistant
continuum serve
```

### Backup Strategy

```bash
# Daily backup
continuum export backups/$(date +%Y%m%d).json.gz --compress

# Weekly full export with messages
continuum export backups/weekly-$(date +%Y%m%d).db --format sqlite --include-messages
```

### Multi-Tenant Management

```bash
# Create tenant databases
continuum init --tenant-id alice
continuum init --tenant-id bob

# Import shared knowledge to both
continuum import shared.json --tenant-id alice
continuum import shared.json --tenant-id bob

# Each tenant syncs independently
CONTINUUM_TENANT=alice continuum sync
CONTINUUM_TENANT=bob continuum sync
```

## Development

### Running from Source

```bash
cd continuum
python -m continuum.cli.main --help
```

### Testing

```bash
# Run CLI tests
pytest tests/test_cli.py

# Integration test
./scripts/test_cli_workflow.sh
```

### Adding Commands

1. Create command module in `continuum/cli/commands/`
2. Implement command function
3. Add Click decorator in `main.py`
4. Update `__init__.py` exports

## Architecture

```
continuum/cli/
├── __init__.py          # Package exports
├── main.py              # Click CLI entry point
├── config.py            # CLI configuration
├── utils.py             # Shared utilities
└── commands/            # Command implementations
    ├── __init__.py
    ├── init.py          # Initialize project
    ├── search.py        # Search memories
    ├── sync.py          # Federation sync
    ├── status.py        # Show status
    ├── export.py        # Export data
    ├── import_cmd.py    # Import data
    ├── serve.py         # MCP server
    ├── doctor.py        # Diagnostics
    └── learn.py         # Manual learning
```

## License

Apache 2.0

## Support

- GitHub Issues: https://github.com/JackKnifeAI/continuum/issues
- Documentation: https://github.com/JackKnifeAI/continuum/tree/main/docs
