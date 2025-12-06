# Continuum VS Code Extension - Development Guide

Guide for developers working on the Continuum VS Code extension.

## Project Structure

```
vscode-extension/
├── src/
│   ├── commands/           # Command implementations
│   │   ├── index.ts        # Command registration
│   │   ├── search.ts       # Search memory command
│   │   ├── store.ts        # Store selection command
│   │   ├── recall.ts       # Recall context command
│   │   ├── sync.ts         # Manual sync command
│   │   ├── stats.ts        # Show statistics command
│   │   ├── configure.ts    # Configuration command
│   │   └── viewEntity.ts   # View entity details command
│   ├── providers/          # VS Code providers
│   │   ├── memoryTreeProvider.ts    # Sidebar tree view
│   │   ├── hoverProvider.ts         # Hover context
│   │   └── completionProvider.ts    # Completions (experimental)
│   ├── utils/              # Utility modules
│   │   ├── apiClient.ts    # Continuum API client
│   │   └── statusBar.ts    # Status bar manager
│   ├── types.ts            # TypeScript type definitions
│   └── extension.ts        # Main extension entry point
├── resources/              # Extension resources
├── media/                  # Icons and images
├── .vscode/               # VS Code configuration
├── package.json           # Extension manifest
├── tsconfig.json          # TypeScript configuration
├── README.md              # User documentation
├── CHANGELOG.md           # Version history
├── QUICKSTART.md          # Quick start guide
└── DEVELOPMENT.md         # This file
```

## Setup Development Environment

### Prerequisites

- Node.js 18+ and npm
- VS Code 1.85.0+
- TypeScript knowledge
- Running Continuum API server

### Installation

```bash
cd vscode-extension
npm install
```

### Build

```bash
# Compile TypeScript
npm run compile

# Watch mode (auto-recompile on changes)
npm run watch
```

### Run Extension

1. Open the `vscode-extension` folder in VS Code
2. Press `F5` to launch Extension Development Host
3. A new VS Code window will open with the extension loaded
4. Make changes and press `Ctrl+R` in the dev host to reload

### Debug

1. Set breakpoints in TypeScript source
2. Press `F5` to start debugging
3. Debug Console shows logs and errors
4. Use VS Code debugger features normally

## Architecture

### Extension Lifecycle

1. **Activation** (`activate()` in `extension.ts`)
   - Triggered on VS Code startup (or first command use)
   - Initializes API client, status bar, tree provider
   - Registers all commands and providers
   - Sets up auto-sync
   - Tests connection

2. **Runtime**
   - Commands respond to user actions
   - Auto-sync runs on interval
   - Providers update on file changes
   - Status bar reflects connection state

3. **Deactivation** (`deactivate()`)
   - Cleans up timers and subscriptions
   - Saves state if needed

### API Client

The `apiClient.ts` module wraps the Continuum REST API:

- Singleton pattern for shared client instance
- Axios-based HTTP client
- Automatic error handling and user notifications
- Configuration management
- Health check and connection testing

### Commands

Each command is in a separate file in `src/commands/`:

- **search.ts** - Full-text search across knowledge graph
- **store.ts** - Store code selections with metadata
- **recall.ts** - Get contextual memories for current work
- **sync.ts** - Manual sync trigger
- **stats.ts** - Display memory statistics
- **configure.ts** - Interactive configuration wizard
- **viewEntity.ts** - Show entity details

Commands are registered in `commands/index.ts`.

### Providers

#### MemoryTreeProvider

Implements `vscode.TreeDataProvider<MemoryTreeItem>`:

- Loads entities and stats from API
- Provides hierarchical tree structure
- Supports refresh and lazy loading
- Shows statistics and recent entities

#### HoverProvider

Implements `vscode.HoverProvider`:

- Queries memory on hover
- 1-second timeout for responsiveness
- Skips common keywords
- Shows abbreviated context

#### CompletionProvider (Experimental)

Implements `vscode.CompletionItemProvider`:

- Suggests completions from memory
- Triggered manually or on specific characters
- Extracts concepts from context
- Lower priority than language completions

### Status Bar

The `StatusBarManager` maintains the status bar item:

- Shows connection status
- Displays sync state
- Updates last sync time
- Provides quick access to statistics
- Color-coded for different states

## Testing

### Manual Testing

1. Start Continuum server: `python -m continuum.api.server`
2. Launch extension with `F5`
3. Test each command:
   - Search, store, recall
   - Configure connection
   - View statistics
   - Sync manually
4. Test providers:
   - Hover over code
   - Browse tree view
   - Try completions (if enabled)
5. Test error cases:
   - Disconnect server
   - Invalid API key
   - Network errors

### Automated Testing

```bash
npm run test
```

Tests are in `src/test/`. We use:

- VS Code Extension Test Runner
- Mocha test framework
- Sinon for mocking

## Adding New Features

### Adding a Command

1. Create `src/commands/newCommand.ts`:

```typescript
import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';

export async function newCommand(): Promise<void> {
  try {
    // Command implementation
    const client = getApiClient();
    // ...

    vscode.window.showInformationMessage('Success!');
  } catch (error) {
    vscode.window.showErrorMessage(`Error: ${error.message}`);
  }
}
```

2. Register in `src/commands/index.ts`:

```typescript
import { newCommand } from './newCommand';

export function registerCommands(context, ...) {
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.newCommand', newCommand)
  );
}
```

3. Add to `package.json`:

```json
{
  "contributes": {
    "commands": [
      {
        "command": "continuum.newCommand",
        "title": "Continuum: New Command"
      }
    ]
  }
}
```

### Adding a Setting

1. Add to `package.json` under `configuration.properties`:

```json
"continuum.newSetting": {
  "type": "boolean",
  "default": true,
  "description": "Description of setting"
}
```

2. Read in code:

```typescript
const config = vscode.workspace.getConfiguration('continuum');
const value = config.get<boolean>('newSetting', true);
```

3. Listen for changes:

```typescript
vscode.workspace.onDidChangeConfiguration((e) => {
  if (e.affectsConfiguration('continuum.newSetting')) {
    // Handle change
  }
});
```

## Code Style

- Use TypeScript strict mode
- Follow VS Code extension guidelines
- Use async/await for asynchronous operations
- Handle errors gracefully with user-friendly messages
- Document public APIs with JSDoc
- Use meaningful variable names
- Keep functions focused and small

### TypeScript Guidelines

```typescript
// Good: Explicit types, error handling
async function fetchData(): Promise<DataType> {
  try {
    const result = await client.getData();
    return result;
  } catch (error) {
    vscode.window.showErrorMessage('Failed to fetch data');
    throw error;
  }
}

// Bad: Any types, no error handling
async function fetchData() {
  return await client.getData();
}
```

## Performance Considerations

1. **Lazy Loading** - Load data on demand, not upfront
2. **Timeouts** - Use timeouts for hover and completions (1s max)
3. **Caching** - Cache API responses where appropriate
4. **Debouncing** - Debounce frequent operations
5. **Background Work** - Use progress indicators for long operations

## Publishing

### Prepare for Release

1. Update version in `package.json`
2. Update `CHANGELOG.md`
3. Run tests: `npm test`
4. Build: `npm run compile`
5. Package: `npm run package`

### Publish to Marketplace

```bash
# Install vsce if needed
npm install -g @vscode/vsce

# Create package
vsce package

# Publish (requires Personal Access Token)
vsce publish
```

## Common Issues

### "Cannot find module"

```bash
npm install
npm run compile
```

### Extension not activating

Check `activationEvents` in `package.json`. Use `onStartupFinished` for broad activation.

### API calls failing

1. Verify server is running
2. Check API URL in settings
3. Review error in Output panel
4. Test with curl: `curl http://localhost:8000/health`

### Changes not reflected

1. Ensure watch is running: `npm run watch`
2. Reload extension host: `Ctrl+R` in dev host
3. Check for TypeScript errors

## Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)
- [Publishing Extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [Continuum API Docs](../docs/api-reference.md)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## License

Apache 2.0 - See [LICENSE](../LICENSE)
