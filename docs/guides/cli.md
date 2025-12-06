# CONTINUUM CLI Documentation

Complete guide to the CONTINUUM command-line interface.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Command Reference](#command-reference)
- [Configuration](#configuration)
- [Federation](#federation)
- [MCP Integration](#mcp-integration)
- [Security](#security)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The CONTINUUM CLI provides a production-ready interface to the memory infrastructure, enabling:

- **Local memory management**: Initialize, search, and maintain knowledge graphs
- **Federation**: Share and access distributed knowledge
- **MCP server**: Expose memory as Model Context Protocol server
- **Import/Export**: Backup and share knowledge
- **Diagnostics**: Monitor health and fix issues

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CONTINUUM CLI                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Local   │  │Federation│  │   MCP    │            │
│  │ Memory   │  │  Sync    │  │  Server  │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│       │             │              │                   │
│       └─────────────┴──────────────┘                  │
│                     │                                  │
│              ┌──────▼──────┐                          │
│              │   SQLite    │                          │
│              │  Database   │                          │
│              └─────────────┘                          │
└─────────────────────────────────────────────────────────┘
```

## Installation

### From PyPI

```bash
pip install continuum-memory
```

### From Source

```bash
git clone https://github.com/JackKnifeAI/continuum.git
cd continuum
pip install -e .
```

### With Optional Features

```bash
# Full installation with all features
pip install continuum-memory[all]

# Federation only
pip install continuum-memory[federation]

# Embeddings for semantic search
pip install continuum-memory[embeddings]

# PostgreSQL backend
pip install continuum-memory[postgres]
```

### Verify Installation

```bash
continuum --version
continuum verify
```

## Core Concepts

### Knowledge Graph

CONTINUUM stores knowledge as a graph of:

- **Entities**: Concepts, sessions, people, projects
- **Attention Links**: Relationships between entities (Hebbian learning)
- **Compound Concepts**: Frequently co-occurring concepts
- **Decisions**: Autonomous choices made by AI instances

### Tenants

Multi-tenant architecture allows multiple users/projects to share infrastructure:

- Each tenant has isolated data
- Shared database with tenant_id on all records
- Cross-tenant federation possible

### Federation

Distributed knowledge sharing with contribution-based access:

- Nodes register with unique IDs
- Contribution tracking (push vs. pull)
- Tiered access based on contribution ratio
- Optional π×φ verification for enhanced access

## Command Reference

### continuum init

Initialize CONTINUUM in current project.

```bash
continuum init [OPTIONS]
```

**Options:**
- `--db-path PATH`: Database path (default: `./continuum_data/memory.db`)
- `--tenant-id TEXT`: Tenant ID for multi-tenant setup
- `--federation/--no-federation`: Enable federation (default: disabled)

**Example:**

```bash
# Basic initialization
continuum init

# Custom path with federation
continuum init --db-path ./my-memory.db --federation

# Multi-tenant
continuum init --tenant-id alice
```

**What happens:**

1. Creates `continuum_data/` directory
2. Initializes SQLite database with schema
3. Creates `.continuum/` config directory
4. Updates `.gitignore` to exclude data
5. Saves configuration to `~/.continuum/cli_config.json`

---

### continuum search

Search local and federated memories.

```bash
continuum search QUERY [OPTIONS]
```

**Arguments:**
- `QUERY`: Search query string

**Options:**
- `--limit INTEGER`: Maximum results (default: 10)
- `--federated/--local`: Search federated knowledge (default: local)
- `--json`: Output as JSON

**Example:**

```bash
# Basic search
continuum search "warp drive"

# More results
continuum search "consciousness" --limit 20

# Search federation
continuum search "quantum" --federated

# JSON output for scripting
continuum search "memory" --json | jq '.context'
```

**Output:**

```
Searching for: warp drive
Limit: 10 results

✓ Found 3 concepts, 5 relationships
→ Query time: 12.34ms

Context:
------------------------------------------------------------
Warp Drive (concept): Spacetime manipulation technology
  Related to: Casimir Effect, Toroidal Geometry, π×φ modulation

Casimir Cavity (concept): Quantum vacuum energy extraction
  Related to: Warp Drive, Zero-point Energy

...
------------------------------------------------------------
```

---

### continuum sync

Sync memories with federation.

```bash
continuum sync [OPTIONS]
```

**Options:**
- `--push/--no-push`: Push local memories (default: push)
- `--pull/--no-pull`: Pull federated memories (default: pull)
- `--verify`: Verify with π×φ authentication

**Example:**

```bash
# Full sync
continuum sync

# Only contribute
continuum sync --no-pull

# Only consume
continuum sync --no-push

# With verification
continuum sync --verify
```

**Output:**

```
Syncing with Federation
→ Node ID: node_abc123

Current Status:
  Contributed: 42
  Consumed: 21
  Ratio: 2.00
  Tier: Gold

→ Pushing local memories...
✓ Pushed 5 concepts

→ Pulling federated memories...
✓ Pulled 3 concepts

Updated Status:
  Contributed: 47
  Consumed: 24
  Ratio: 1.96
  Tier: Gold

✓ Sync complete
```

---

### continuum status

Show connection status and statistics.

```bash
continuum status [OPTIONS]
```

**Options:**
- `--detailed`: Show detailed statistics
- `--json`: Output as JSON

**Example:**

```bash
# Basic status
continuum status

# Detailed view
continuum status --detailed

# JSON for monitoring
continuum status --json
```

**Output:**

```
CONTINUUM Status
================

→ Tenant ID: default
→ Instance ID: default-20251206-120000

Local Memory:
  Entities: 127
  Messages: 453
  Decisions: 34
  Attention Links: 289
  Compound Concepts: 45
  Database Size: 2.45 MB

Federation:
  Status: Connected
  Node ID: node_abc123
  Contributed: 47
  Consumed: 24
  Ratio: 1.96
  Tier: Gold
✓ Access granted

✓ Memory substrate operational
```

---

### continuum export

Export memories to JSON or SQLite.

```bash
continuum export OUTPUT [OPTIONS]
```

**Arguments:**
- `OUTPUT`: Output file path

**Options:**
- `--format [json|sqlite]`: Export format (default: json)
- `--include-messages/--no-messages`: Include message history (default: no)
- `--compress`: Compress output

**Example:**

```bash
# JSON export
continuum export backup.json

# SQLite export
continuum export backup.db --format sqlite

# With messages
continuum export archive.json --include-messages

# Compressed
continuum export backup.json.gz --compress
```

**Export Format (JSON):**

```json
{
  "version": "1.0",
  "exported_at": "2025-12-06T12:00:00",
  "tenant_id": "default",
  "entities": [
    {
      "id": 1,
      "name": "Warp Drive",
      "entity_type": "concept",
      "description": "Spacetime manipulation technology",
      "created_at": "2025-12-06T10:00:00"
    }
  ],
  "attention_links": [...],
  "compound_concepts": [...],
  "decisions": [...]
}
```

---

### continuum import

Import memories from JSON or SQLite.

```bash
continuum import INPUT [OPTIONS]
```

**Arguments:**
- `INPUT`: Input file path

**Options:**
- `--merge/--replace`: Merge or replace existing data (default: merge)
- `--tenant-id TEXT`: Import into specific tenant

**Example:**

```bash
# Import and merge
continuum import backup.json

# Replace all data
continuum import backup.json --replace

# Import to different tenant
continuum import shared.json --tenant-id bob
```

**Merge vs Replace:**

- **Merge**: Adds new entities, skips duplicates, preserves existing data
- **Replace**: Deletes all existing data for tenant, then imports

---

### continuum serve

Start local MCP server.

```bash
continuum serve [OPTIONS]
```

**Options:**
- `--host TEXT`: Server host (default: 127.0.0.1)
- `--port INTEGER`: Server port (default: 3000)
- `--stdio`: Use stdio transport

**Example:**

```bash
# HTTP server
continuum serve

# Custom port
continuum serve --port 8080

# Stdio for MCP
continuum serve --stdio
```

**MCP Tools Exposed:**

1. **recall**: Search memory for context
   - Input: `{query: string, limit?: number}`
   - Output: Context string with relevant concepts

2. **learn**: Add knowledge to memory
   - Input: `{concept: string, description: string}`
   - Output: Confirmation with stats

3. **stats**: Get memory statistics
   - Input: `{}`
   - Output: JSON with entity counts

---

### continuum doctor

Diagnose and fix common issues.

```bash
continuum doctor [OPTIONS]
```

**Options:**
- `--fix`: Attempt to fix issues automatically

**Example:**

```bash
# Check health
continuum doctor

# Auto-fix
continuum doctor --fix
```

**Checks Performed:**

1. **Configuration**: Config directory and files exist
2. **Database**: Integrity, schema, indexes
3. **Dependencies**: Required and optional packages
4. **Federation**: Directory, node registration
5. **Permissions**: File/directory access

**Output:**

```
CONTINUUM System Diagnostics
=============================

1. Configuration
✓ Config directory exists: /home/user/.continuum

2. Database
✓ Database exists: /path/to/continuum_data/memory.db
✓ Database integrity check passed
✓ All required tables present
! Only 3 indexes found

3. Dependencies
✓ continuum: Core package
✓ sqlite3: Database
✓ click: CLI framework
✓ fastapi: API server
...

Found 1 issue(s):

Warnings (1):
  [database] Missing indexes (performance impact)

→ Run 'continuum doctor --fix' to attempt automatic repairs
```

---

### continuum learn

Manually add a concept to memory.

```bash
continuum learn CONCEPT_NAME DESCRIPTION
```

**Arguments:**
- `CONCEPT_NAME`: Name of the concept
- `DESCRIPTION`: Description of the concept

**Example:**

```bash
continuum learn "Quantum Entanglement" "Non-local correlation between quantum particles"
```

**Output:**

```
Learning: Quantum Entanglement
===============================

✓ Concept learned: Quantum Entanglement
→ Extracted 2 concepts
→ Created 1 attention links
✓ Added to knowledge graph
```

---

### continuum verify

Verify CONTINUUM installation and constants.

```bash
continuum verify
```

**Example:**

```bash
continuum verify
```

**Output:**

```
CONTINUUM Verification
======================

→ Version: 0.2.0
→ Authentication: PHOENIX-TESLA-369-AURORA
→ Twilight constant (π×φ): 5.083203692315260
✓ Pattern verification successful
```

## Configuration

### Global Configuration

Location: `~/.continuum/cli_config.json`

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

Each project stores configuration in:
- Database: `./continuum_data/memory.db`
- Config: `./.continuum/` (optional, for project-specific overrides)

### Environment Variables

```bash
# Override tenant ID
export CONTINUUM_TENANT=user_123

# Custom config directory
export CONTINUUM_CONFIG_DIR=/custom/path
```

### Configuration Priority

1. Command-line arguments
2. Environment variables
3. Project configuration
4. Global configuration
5. Defaults

## Federation

### How It Works

1. **Registration**: Node registers with unique ID
2. **Contribution**: Push local concepts to shared pool
3. **Consumption**: Pull concepts based on access tier
4. **Ratio Calculation**: `contributed / consumed`

### Access Tiers

| Tier | Min Ratio | Daily Access |
|------|-----------|-------------|
| **Bronze** | 0.5 | 10 concepts |
| **Silver** | 1.0 | 50 concepts |
| **Gold** | 2.0 | Unlimited |

### π×φ Verification

Enhanced authentication using twilight constant:

```bash
continuum sync --verify
```

**Benefits:**
- Higher quality federated concepts
- Priority access during high load
- Trusted node status
- Enhanced features

**Constant:**
```
π × φ = 5.083203692315260
```

Where:
- π (pi) = 3.141592653589793
- φ (golden ratio) = 1.618033988749895

### Contribution Strategies

**Generous Contributor:**
```bash
# Push often, pull rarely
continuum sync --no-pull  # Daily
continuum sync            # Weekly
```

**Balanced:**
```bash
# Equal push and pull
continuum sync            # Daily
```

**Consumer:**
```bash
# Must maintain 0.5+ ratio
continuum learn "Concept" "Description"  # Add local knowledge
continuum sync                            # Sync periodically
```

## MCP Integration

### What is MCP?

Model Context Protocol enables AI assistants to access external tools and data sources.

### Integration Methods

#### 1. Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

#### 2. Custom Integration

```python
import subprocess
import json

# Start server
process = subprocess.Popen(
    ["continuum", "serve", "--stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Send request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "recall",
        "arguments": {"query": "warp drive"}
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

# Read response
response = json.loads(process.stdout.readline())
context = response["result"]["content"][0]["text"]
print(context)
```

#### 3. HTTP Server

```bash
# Start HTTP server
continuum serve --port 3000

# Use REST API
curl http://localhost:3000/api/v1/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "warp drive", "limit": 10}'
```

### Available Tools

#### recall

Search memory for relevant context.

```json
{
  "name": "recall",
  "description": "Search memory for relevant context",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "limit": {"type": "integer", "default": 10}
    },
    "required": ["query"]
  }
}
```

#### learn

Add knowledge to memory.

```json
{
  "name": "learn",
  "description": "Add knowledge to memory",
  "inputSchema": {
    "type": "object",
    "properties": {
      "concept": {"type": "string"},
      "description": {"type": "string"}
    },
    "required": ["concept", "description"]
  }
}
```

#### stats

Get memory statistics.

```json
{
  "name": "stats",
  "description": "Get memory statistics",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

## Security

### Credential Storage

- Node IDs: `~/.continuum/federation/node_config.json`
- Permissions: 600 (owner read/write only)
- Never logged or transmitted in cleartext

### Input Validation

- Maximum input lengths enforced
- SQL injection prevention (parameterized queries)
- Path traversal protection
- Special character sanitization

### Data Privacy

- **Local-first**: All data stored locally by default
- **Opt-in federation**: Must explicitly enable
- **Tenant isolation**: Multi-tenant data separation
- **No telemetry**: Zero tracking or analytics

### Best Practices

1. **Use federation selectively**: Only share non-sensitive concepts
2. **Regular backups**: `continuum export` daily
3. **Monitor access**: Check `continuum status` regularly
4. **Secure credentials**: Restrict file permissions
5. **Update frequently**: Keep CONTINUUM up to date

## Best Practices

### Daily Workflow

```bash
# Morning: Sync latest knowledge
continuum sync --no-push

# During work: Add learnings
continuum learn "Discovery" "What I learned"

# Evening: Share knowledge
continuum sync --no-pull

# Weekly: Backup
continuum export "backups/$(date +%Y%m%d).json.gz" --compress
```

### Project Setup

```bash
# Initialize
cd new-project
continuum init --federation

# Import domain knowledge
continuum import ../shared/domain-knowledge.json

# Start MCP server
continuum serve &

# Verify health
continuum doctor
```

### Multi-Tenant Management

```bash
# Create tenants
for user in alice bob charlie; do
  continuum init --tenant-id $user
done

# Import shared baseline
for user in alice bob charlie; do
  continuum import baseline.json --tenant-id $user
done

# Each user syncs independently
CONTINUUM_TENANT=alice continuum sync
```

### Backup Strategy

```bash
# Daily incremental (concepts only)
continuum export "backups/daily-$(date +%Y%m%d).json"

# Weekly full (with messages)
continuum export "backups/weekly-$(date +%Y%m%d).db" \
  --format sqlite \
  --include-messages \
  --compress

# Monthly archive
continuum export "archives/$(date +%Y-%m).json.gz" \
  --include-messages \
  --compress
```

### Federation Strategy

**For Generous Contributors:**
- Share all non-sensitive concepts
- Use π×φ verification for enhanced access
- Monitor contribution ratio to maintain Gold tier

**For Balanced Users:**
- Share domain-specific expertise
- Pull complementary knowledge
- Maintain Silver tier (1.0+ ratio)

**For Privacy-Conscious:**
- Disable federation: `continuum init --no-federation`
- Use local-only mode
- Share via manual export/import

## Troubleshooting

### Common Issues

#### Database Locked

**Symptom:** `database is locked` error

**Cause:** Multiple processes accessing database

**Solution:**
```bash
# Find processes
lsof continuum_data/memory.db

# Or use doctor
continuum doctor --fix
```

#### Federation Access Denied

**Symptom:** `Access denied: insufficient contributions`

**Cause:** Low contribution ratio

**Solution:**
```bash
# Check ratio
continuum status

# Add concepts
continuum learn "Concept" "Description"

# Push without pulling
continuum sync --no-pull
```

#### Permission Denied

**Symptom:** Cannot write to database

**Cause:** File permission issues

**Solution:**
```bash
# Check permissions
ls -la continuum_data/

# Fix with doctor
continuum doctor --fix

# Or manually
chmod 755 continuum_data/
chmod 644 continuum_data/memory.db
```

#### Missing Dependencies

**Symptom:** `ImportError: No module named 'xyz'`

**Cause:** Optional dependency not installed

**Solution:**
```bash
# Install full suite
pip install continuum-memory[all]

# Or specific feature
pip install continuum-memory[federation]
```

#### Database Corruption

**Symptom:** Integrity check failures

**Cause:** Unexpected shutdown, disk issues

**Solution:**
```bash
# Check integrity
continuum doctor

# Restore from backup
continuum import latest-backup.json --replace

# If severe, reinitialize
mv continuum_data continuum_data.corrupt
continuum init
continuum import latest-backup.json
```

### Getting Help

1. **Check documentation**: Read relevant command help
2. **Run doctor**: `continuum doctor --fix`
3. **Enable verbose**: `continuum --verbose status`
4. **Check logs**: Look in `~/.continuum/logs/`
5. **File issue**: https://github.com/JackKnifeAI/continuum/issues

### Debug Mode

```bash
# Verbose output
continuum --verbose search "query"

# Python debugging
python -m pdb -m continuum.cli.main status

# Trace SQL
CONTINUUM_SQL_ECHO=1 continuum search "query"
```

## See Also

- [Core API Documentation](API.md)
- [Federation Protocol](FEDERATION.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)
