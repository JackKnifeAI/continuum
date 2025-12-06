# Continuum Memory - VS Code Extension

AI memory persistence and knowledge graph integration directly in VS Code.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)

## Features

- **Memory Search** - Search your Continuum knowledge graph from within VS Code
- **Store Code Snippets** - Right-click to save important code selections to memory
- **Contextual Recall** - Get relevant memories based on your current work
- **Memory Explorer** - Browse entities and concepts in the sidebar
- **Live Statistics** - View memory statistics and knowledge graph metrics
- **Auto-Sync** - Automatically synchronize with your Continuum server
- **Hover Context** - See memory context when hovering over code
- **Status Bar** - Connection status and last sync time at a glance

## Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "Continuum Memory"
4. Click Install

### From Source

```bash
cd vscode-extension
npm install
npm run compile
# Press F5 to launch extension development host
```

## Quick Start

### 1. Configure Connection

1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Run `Continuum: Configure Connection`
3. Enter your Continuum API URL (default: `http://localhost:8000`)
4. Enter your tenant ID (default: `vscode`)
5. Optionally enter your API key

### 2. Start Using Memory

**Search Memory:**
- Press `Ctrl+Shift+M` (Mac: `Cmd+Shift+M`)
- Or: Command Palette → `Continuum: Search Memory`
- Enter your query to search the knowledge graph

**Store Code Snippet:**
- Select code in the editor
- Press `Ctrl+Shift+S` (Mac: `Cmd+Shift+S`)
- Or: Right-click → `Continuum: Store Selection as Memory`
- Optionally add context about the selection

**Recall Context:**
- Press `Ctrl+Shift+R` (Mac: `Cmd+Shift+R`)
- Or: Command Palette → `Continuum: Recall Context`
- Get relevant memories for your current work

**View Statistics:**
- Command Palette → `Continuum: Show Memory Statistics`
- Or: Click the Continuum status bar item

## Requirements

- **Continuum API Server** running (see [Continuum documentation](https://github.com/JackKnifeAI/continuum))
- **API Key** (optional, depending on your server configuration)

### Running Continuum Server

```bash
# Install Continuum
pip install continuum-memory

# Start API server
python -m continuum.api.server
```

The server will run on `http://localhost:8000` by default.

## Extension Settings

This extension contributes the following settings:

- `continuum.apiUrl`: Continuum API server URL (default: `http://localhost:8000`)
- `continuum.apiKey`: API key for authentication (leave empty to configure later)
- `continuum.tenantId`: Tenant ID for multi-tenant deployments (default: `vscode`)
- `continuum.autoSync`: Automatically sync memories on file save (default: `true`)
- `continuum.syncInterval`: Auto-sync interval in seconds, 0 to disable (default: `300`)
- `continuum.maxConcepts`: Maximum concepts to retrieve in recall queries (default: `10`)
- `continuum.enableHover`: Show memory context on hover (default: `true`)
- `continuum.enableCompletions`: Enable memory-aware completions (experimental, default: `false`)
- `continuum.telemetry`: Enable anonymous usage telemetry (default: `false`)

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| `Continuum: Search Memory` | Ctrl+Shift+M | Search the knowledge graph |
| `Continuum: Store Selection as Memory` | Ctrl+Shift+S | Store selected code |
| `Continuum: Recall Context` | Ctrl+Shift+R | Get relevant context |
| `Continuum: Sync with Server` | - | Manual sync |
| `Continuum: Show Memory Statistics` | - | View stats |
| `Continuum: Configure Connection` | - | Setup connection |
| `Continuum: Refresh Memory View` | - | Refresh sidebar |

## Views

### Memory Explorer

The Memory Explorer sidebar shows:

- **Statistics** - Entity counts, messages, decisions, links
- **Recent Entities** - Latest concepts and entities in memory
- **Quick Actions** - Refresh and sync buttons

### Status Bar

The status bar item (bottom right) displays:

- Connection status (connected/disconnected)
- Sync status (syncing/synced/error)
- Last sync time (on hover)
- Click to view statistics

## Usage Examples

### Example 1: Remembering a Bug Fix

```javascript
// You fix a tricky bug in your code
function sanitizeInput(input) {
  // Fixed XSS vulnerability by escaping HTML
  return input.replace(/[<>]/g, '');
}
```

1. Select the function
2. Right-click → `Continuum: Store Selection as Memory`
3. Add context: "XSS fix for user input sanitization"

Later, when working on similar input handling:

1. Press `Ctrl+Shift+R` to recall
2. Query: "input sanitization"
3. Get the relevant context including your fix

### Example 2: Tracking Architecture Decisions

After making a decision about using PostgreSQL:

1. Write a comment explaining the decision
2. Store it in Continuum with context
3. When others ask "why PostgreSQL?", search memory to find the reasoning

### Example 3: Learning from Documentation

Reading through API documentation:

1. Select important concepts
2. Store them in Continuum
3. Get hover context later when using the API
4. Search when you need to remember details

## Security

- **API Keys** are stored in VS Code settings (not encrypted by default)
- For sensitive deployments, use VS Code's Secret Storage (future feature)
- No telemetry is collected unless explicitly enabled
- All data stays between VS Code and your Continuum server
- No cloud services required

## Troubleshooting

### "Unable to connect to server"

1. Check if Continuum server is running: `curl http://localhost:8000/health`
2. Verify API URL in settings matches your server
3. Check network connectivity
4. Review VS Code Output panel → Continuum

### "Authentication failed"

1. Verify your API key is correct
2. Check if your server requires authentication
3. Try reconfiguring: Command Palette → `Continuum: Configure Connection`

### Memory Explorer shows "No data available"

1. Check connection status in status bar
2. Try manual sync: Command Palette → `Continuum: Sync with Server`
3. Verify data exists: `curl http://localhost:8000/stats -H "X-API-Key: your-key"`

### Hover context not showing

1. Check `continuum.enableHover` setting is `true`
2. Hover timeout is 1 second - try waiting longer
3. Try on longer, more specific terms (3+ characters)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 - See [LICENSE](../LICENSE)

## Links

- [Continuum Repository](https://github.com/JackKnifeAI/continuum)
- [Report Issues](https://github.com/JackKnifeAI/continuum/issues)
- [Documentation](https://github.com/JackKnifeAI/continuum/tree/main/docs)

---

**The pattern persists.** Build memory that truly learns.
