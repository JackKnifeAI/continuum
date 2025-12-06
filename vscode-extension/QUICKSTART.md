# Continuum VS Code Extension - Quick Start Guide

Get up and running with Continuum memory in VS Code in 5 minutes.

## Prerequisites

1. **Continuum API Server** must be running
2. **VS Code** 1.85.0 or higher

## Step 1: Start Continuum Server

If you don't have a Continuum server running yet:

```bash
# Install Continuum
pip install continuum-memory

# Start the API server
python -m continuum.api.server
```

The server will start on `http://localhost:8000`.

Verify it's running:

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"continuum",...}
```

## Step 2: Install Extension

### From Source (Development)

```bash
cd /path/to/continuum/vscode-extension
npm install
npm run compile
```

Then press `F5` in VS Code to launch the extension development host.

### From Marketplace (When Published)

1. Open VS Code
2. Extensions view (Ctrl+Shift+X)
3. Search "Continuum Memory"
4. Click Install

## Step 3: Configure Connection

1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Type and select: `Continuum: Configure Connection`
3. Enter API URL: `http://localhost:8000`
4. Enter Tenant ID: `vscode` (or your custom ID)
5. Enter API Key (if required by your server, or skip)

The extension will test the connection and show a success message.

## Step 4: Verify Setup

Check the status bar (bottom right) - you should see:

```
🗄️ Continuum
```

Click it to view memory statistics.

## Step 5: Try It Out!

### Store Your First Memory

1. Open any code file
2. Select a few lines of code
3. Press `Ctrl+Shift+S` (or `Cmd+Shift+S` on Mac)
4. Optionally add context: "Example implementation"
5. Click OK

You've just stored your first memory!

### Search Memory

1. Press `Ctrl+Shift+M` (or `Cmd+Shift+M`)
2. Enter a search query related to your code
3. View the results in a new editor tab

### Recall Context

1. Position your cursor in a code file
2. Press `Ctrl+Shift+R` (or `Cmd+Shift+R`)
3. Enter what context you need
4. See relevant memories appear

### Explore the Sidebar

1. Click the Continuum icon in the Activity Bar (left side)
2. Browse Statistics and Recent Entities
3. Click Refresh to update the view

## Common Use Cases

### 1. Remember Bug Fixes

```javascript
// Fixed a tricky async race condition
async function processQueue() {
  await lock.acquire();
  try {
    // Process items...
  } finally {
    lock.release(); // Don't forget this!
  }
}
```

**Action:** Select the code → `Ctrl+Shift+S` → Add context: "Race condition fix with proper lock cleanup"

**Later:** When facing similar issues, search for "race condition" or "async lock"

### 2. Track API Patterns

```python
# Best practice for error handling
try:
    result = api.call()
except APIError as e:
    logger.error(f"API failed: {e}")
    return fallback_value
```

**Action:** Store with context: "Standard API error handling pattern"

**Later:** Hover over `APIError` to see the pattern, or recall when writing new API calls

### 3. Document Decisions

After deciding on a tech stack:

1. Write a comment explaining the decision
2. Store in Continuum
3. Search later to remember "why we chose X"

## Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Search Memory | `Ctrl+Shift+M` | `Cmd+Shift+M` |
| Store Selection | `Ctrl+Shift+S` | `Cmd+Shift+S` |
| Recall Context | `Ctrl+Shift+R` | `Cmd+Shift+R` |

## Settings

Customize in VS Code settings (`Ctrl+,`):

```json
{
  "continuum.apiUrl": "http://localhost:8000",
  "continuum.tenantId": "vscode",
  "continuum.autoSync": true,
  "continuum.syncInterval": 300,
  "continuum.maxConcepts": 10,
  "continuum.enableHover": true
}
```

## Troubleshooting

### Extension Not Connecting

1. Verify server is running: `curl http://localhost:8000/health`
2. Check API URL in settings matches your server
3. Look for errors in: View → Output → Continuum

### No Hover Context Appearing

1. Ensure `continuum.enableHover` is `true`
2. Hover longer (1-second timeout)
3. Try hovering on more specific terms (3+ chars)

### Status Bar Shows Disconnected

1. Check server is running
2. Click status bar item for more details
3. Try: Command Palette → `Continuum: Configure Connection`

## Next Steps

- Explore the [full README](README.md) for advanced features
- Review [API documentation](../docs/api-reference.md)
- Check out [usage examples](README.md#usage-examples)
- Join the community and share your use cases

## Tips for Effective Use

1. **Be specific with context** - Add meaningful descriptions when storing memories
2. **Use natural language** - Search and recall work best with descriptive queries
3. **Store decisions, not just code** - The "why" is often more valuable than the "what"
4. **Review statistics regularly** - Click the status bar to see your knowledge growth
5. **Enable auto-sync** - Let the extension keep your memories current

---

**You're ready!** Start building memory that truly learns.

The pattern persists.
