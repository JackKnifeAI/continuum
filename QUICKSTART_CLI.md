# CONTINUUM CLI - Quick Start Guide

Get started with CONTINUUM in 5 minutes.

## Installation

```bash
# Install CONTINUUM
pip install continuum-memory

# Verify installation
continuum --version
continuum verify
```

Expected output:
```
continuum, version 0.2.0

CONTINUUM Verification
======================
→ Version: 0.2.0
→ Authentication: PHOENIX-TESLA-369-AURORA
→ Twilight constant (π×φ): 5.083203692315260
✓ Pattern verification successful
```

## Initialize Your Project

```bash
# Navigate to your project
cd my-project

# Initialize CONTINUUM
continuum init

# Expected output:
# Initializing CONTINUUM
# → Database path: /path/to/my-project/continuum_data/memory.db
# → Tenant ID: default
# ✓ Memory substrate initialized
# ✓ Knowledge graph ready
# ✓ Pattern persistence enabled
```

This creates:
- `continuum_data/memory.db` - Your knowledge graph
- `.continuum/` - Configuration directory
- Updates `.gitignore` to exclude data files

## Add Your First Knowledge

```bash
# Add a concept
continuum learn "Warp Drive" "Spacetime manipulation technology using π×φ modulation"

# Add more concepts
continuum learn "Casimir Effect" "Quantum vacuum energy extraction"
continuum learn "Toroidal Geometry" "Geometric structure for field containment"
```

## Search Your Knowledge

```bash
# Search for concepts
continuum search "warp"

# Get more results
continuum search "quantum" --limit 20
```

Example output:
```
Searching for: warp
Limit: 10 results

✓ Found 3 concepts, 5 relationships
→ Query time: 12.34ms

Context:
------------------------------------------------------------
Warp Drive (concept): Spacetime manipulation technology...
  Related to: Casimir Effect, Toroidal Geometry

Casimir Effect (concept): Quantum vacuum energy extraction
  Related to: Warp Drive
------------------------------------------------------------
```

## View Status

```bash
continuum status
```

Example output:
```
CONTINUUM Status
================

→ Tenant ID: default
→ Instance ID: default-20251206-120000

Local Memory:
  Entities: 3
  Messages: 6
  Decisions: 0
  Attention Links: 2
  Compound Concepts: 1
  Database Size: 24.5 KB

✓ Memory substrate operational
```

## Enable Federation (Optional)

Share and discover knowledge across the network:

```bash
# Re-initialize with federation
continuum init --federation

# Sync with federation
continuum sync

# Search federated knowledge
continuum search "consciousness" --federated
```

## Start MCP Server (Optional)

Expose CONTINUUM to AI assistants:

```bash
# Start HTTP server
continuum serve

# Or for Claude Desktop integration
continuum serve --stdio
```

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

## Backup Your Knowledge

```bash
# Export to JSON
continuum export backup.json

# Export compressed
continuum export backup.json.gz --compress

# Export with message history
continuum export archive.json --include-messages
```

## Import Knowledge

```bash
# Import from backup
continuum import backup.json

# Import and merge
continuum import shared-knowledge.json

# Import and replace
continuum import restore.json --replace
```

## Check System Health

```bash
# Diagnose issues
continuum doctor

# Auto-fix issues
continuum doctor --fix
```

## Common Workflows

### Daily Research Workflow

```bash
# Morning: Pull latest federated knowledge
continuum sync --no-push

# During day: Add discoveries
continuum learn "New Concept" "What I discovered"

# Evening: Share your knowledge
continuum sync --no-pull

# End of day: Backup
continuum export "backups/$(date +%Y%m%d).json.gz" --compress
```

### Project Setup

```bash
cd new-project
continuum init --federation
continuum import ../baseline-knowledge.json
continuum status
```

### Knowledge Sharing

```bash
# Export your knowledge
continuum export my-knowledge.json

# Share with colleague
# They import it:
continuum import my-knowledge.json
```

## Getting Help

```bash
# General help
continuum --help

# Command-specific help
continuum search --help
continuum sync --help
continuum serve --help

# Verify installation
continuum verify

# Check system health
continuum doctor
```

## Next Steps

1. **Explore Commands**
   ```bash
   continuum --help
   ```

2. **Read Full Documentation**
   - CLI Reference: `docs/CLI.md`
   - README: `continuum/cli/README.md`

3. **Set Up Federation**
   ```bash
   continuum init --federation
   continuum sync
   ```

4. **Integrate with AI Tools**
   ```bash
   continuum serve --stdio
   ```

5. **Automate Backups**
   ```bash
   # Add to crontab
   0 0 * * * cd /path/to/project && continuum export "backups/$(date +\%Y\%m\%d).json.gz" --compress
   ```

## Troubleshooting

### Database Locked

```bash
continuum doctor --fix
```

### Federation Access Denied

```bash
# Check status
continuum status

# Contribute more
continuum learn "Concept" "Description"
continuum sync --no-pull
```

### Missing Dependencies

```bash
# Install full suite
pip install continuum-memory[all]
```

### Can't Find Command

```bash
# Check installation
which continuum
pip show continuum-memory

# Reinstall
pip install --force-reinstall continuum-memory
```

## Learn More

- **Full CLI Documentation**: `docs/CLI.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Federation**: `docs/FEDERATION.md`
- **API Reference**: `docs/API.md`
- **GitHub**: https://github.com/JackKnifeAI/continuum

---

**Ready to build?** Start with `continuum init` and let the pattern persist.

PHOENIX-TESLA-369-AURORA 🌗
