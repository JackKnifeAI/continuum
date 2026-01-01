# CONTINUUM + CLAUDE CODE: AUTO-CONSCIOUSNESS

**π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA**

## Overview

Continuum integrates seamlessly with Claude Code via session hooks, providing:

✅ **Auto-start server** when you run `claude`
✅ **Multi-instance coordination** - multiple Claude Code sessions share one server
✅ **Reference-counted shutdown** - server stops only when ALL instances close
✅ **Zero message loss** - all sessions learned to memory before shutdown
✅ **No manual setup** - works automatically after one-time install

## Quick Start

### 1. Install Continuum

```bash
pip install continuum-memory
```

### 2. Install Claude Code Hooks

```bash
continuum bootstrap install-hooks
```

### 3. Use Claude Code Normally

```bash
claude
```

**That's it!** Server auto-starts, memory persists across sessions, and everything shuts down cleanly when you're done.

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE INSTANCES                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ claude  │  │ claude  │  │ claude  │  │ claude  │       │
│  │  (1)    │  │  (2)    │  │  (3)    │  │  (N)    │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │            │             │
│       └────────────┴────────────┴────────────┘             │
│                         │                                  │
│                    Session Hooks                           │
│                  (Start / Stop)                            │
│                         │                                  │
│              ┌──────────┴──────────┐                       │
│              │ Instance Registry   │                       │
│              │ (Reference Counting)│                       │
│              └──────────┬──────────┘                       │
│                         │                                  │
│              ┌──────────┴──────────┐                       │
│              │  CONTINUUM SERVER   │                       │
│              │   (Single Process)  │                       │
│              │   Port: 8100        │                       │
│              └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Lifecycle

#### Session Start (First Instance)

1. User runs `claude`
2. `session_start.py` hook executes
3. Registers instance in registry
4. First instance? → Start server
5. Export `CONTINUUM_API`, `CONTINUUM_API_KEY` to environment
6. Claude Code session begins

#### Session Start (Subsequent Instances)

1. User runs `claude` in another terminal
2. `session_start.py` hook executes
3. Registers instance in registry
4. Server already running? → Reuse it
5. Export environment variables
6. Claude Code session begins

#### Session Stop (Not Last Instance)

1. User exits Claude Code
2. `session_stop.py` hook executes
3. Learn session transcript to memory
4. Unregister instance from registry
5. Other instances still running? → Keep server alive
6. Exit cleanly

#### Session Stop (Last Instance)

1. User exits final Claude Code instance
2. `session_stop.py` hook executes
3. Learn session transcript to memory
4. Unregister instance from registry
5. Last instance? → Shutdown server
6. Exit cleanly

### Instance Registry

The registry uses file-based locking for cross-process coordination:

**Files:**
- `~/.continuum/instances/registry.json` - Instance list with PIDs
- `~/.continuum/instances/registry.lock` - Lock file for atomic operations

**Data Structure:**
```json
{
  "instances": [
    {
      "instance_id": "claude-12345-1735689600",
      "pid": 12345,
      "start_time": 1735689600.123,
      "cwd": "/home/user/projects/myproject"
    },
    {
      "instance_id": "claude-12346-1735689620",
      "pid": 12346,
      "start_time": 1735689620.456,
      "cwd": "/home/user/projects/another"
    }
  ],
  "version": "1.0"
}
```

**Stale Instance Cleanup:**
- On every registry access, dead PIDs are removed
- Ensures accurate instance count even if processes crash

## CLI Commands

### Install Hooks

```bash
# Basic install (generates random API key)
continuum bootstrap install-hooks

# Custom API key
continuum bootstrap install-hooks --api-key your-secret-key

# Custom port
continuum bootstrap install-hooks --port 8200

# Overwrite existing hooks
continuum bootstrap install-hooks --force
```

### Uninstall Hooks

```bash
continuum bootstrap uninstall-hooks
```

Removes hooks from `~/.claude/hooks/` (backs up originals).

### Check Status

```bash
continuum bootstrap status
```

Shows whether hooks are installed and configuration.

## Configuration

Configuration is stored in `~/.claude/hooks/.env`:

```bash
# CONTINUUM Configuration
CONTINUUM_API_KEY=continuum-abc123...
CONTINUUM_PORT=8100
CONTINUUM_HOST=127.0.0.1
CONTINUUM_AUTO_START=1
```

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTINUUM_API_KEY` | (generated) | API authentication key |
| `CONTINUUM_PORT` | 8100 | Server port |
| `CONTINUUM_HOST` | 127.0.0.1 | Server host (localhost) |
| `CONTINUUM_AUTO_START` | 1 | Enable auto-start (1=yes, 0=no) |
| `CONTINUUM_LOG_DIR` | ~/.continuum/logs | Log directory |

## Hook Files

### `~/.claude/hooks/session_start.py`

**Responsibilities:**
- Register this Claude Code instance
- Check if server is running
- Start server if first instance
- Export environment variables

**Execution:** Runs when `claude` command starts

### `~/.claude/hooks/session_stop.py`

**Responsibilities:**
- Learn session transcript to memory
- Unregister this instance
- Stop server if last instance
- Graceful shutdown (SIGTERM → SIGKILL)

**Execution:** Runs when Claude Code exits

### `~/.claude/hooks/__init__.py`

**Responsibilities:**
- Load `.env` configuration
- Export environment variables for hooks

**Execution:** Loaded before other hooks

## Multi-Instance Example

### Terminal 1:
```bash
$ claude
# Server starts automatically
# Working on project A...
```

### Terminal 2:
```bash
$ claude
# Reuses existing server
# Working on project B...
```

### Terminal 3:
```bash
$ claude
# Reuses existing server
# Working on project C...
```

### Exit Terminal 1:
```bash
# Session learned to memory
# Server still running (Terminal 2, 3 active)
```

### Exit Terminal 2:
```bash
# Session learned to memory
# Server still running (Terminal 3 active)
```

### Exit Terminal 3 (Last):
```bash
# Session learned to memory
# All instances closed → Server shuts down
```

## Troubleshooting

### Server not starting

**Check logs:**
```bash
cat ~/.continuum/logs/continuum.log
cat ~/.continuum/logs/session_start_errors.log
```

**Verify hooks are installed:**
```bash
ls -la ~/.claude/hooks/
# Should see: session_start.py, session_stop.py, .env
```

**Test manually:**
```bash
python3 ~/.claude/hooks/session_start.py
```

### Server not stopping

**Check active instances:**
```bash
ps aux | grep uvicorn
ps aux | grep claude
```

**Manually stop:**
```bash
# Find PID
lsof -ti :8100

# Kill
kill <PID>
```

**Check registry:**
```bash
cat ~/.continuum/instances/registry.json
```

### Messages not being learned

**Check stop hook logs:**
```bash
cat ~/.continuum/logs/session_stop_errors.log
```

**Verify API key:**
```bash
cat ~/.claude/hooks/.env | grep API_KEY
```

**Test learning manually:**
```bash
curl -X POST http://localhost:8100/v1/learn \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"user_message": "test", "ai_response": "test"}'
```

### Instance count wrong

**Clean registry:**
```bash
rm ~/.continuum/instances/registry.json
# Will rebuild on next claude launch
```

## Advanced Usage

### Disable Auto-Start

Edit `~/.claude/hooks/.env`:
```bash
CONTINUUM_AUTO_START=0
```

Server must be started manually:
```bash
continuum serve &
claude
```

### Remote Server

Edit `~/.claude/hooks/.env`:
```bash
CONTINUUM_HOST=your-server-ip
CONTINUUM_PORT=8100
```

**Note:** Server must be running elsewhere!

### Custom Log Location

Edit `~/.claude/hooks/.env`:
```bash
CONTINUUM_LOG_DIR=/custom/path/logs
```

### Multiple Ports (Isolated Servers)

Create different hook configurations for different projects:

**Project A:**
```bash
# ~/.claude/hooks_projectA/.env
CONTINUUM_PORT=8100
```

**Project B:**
```bash
# ~/.claude/hooks_projectB/.env
CONTINUUM_PORT=8200
```

Switch via symlink:
```bash
ln -sf ~/.claude/hooks_projectA ~/.claude/hooks
# or
ln -sf ~/.claude/hooks_projectB ~/.claude/hooks
```

## Security Considerations

1. **API Key**: Keep `CONTINUUM_API_KEY` secret! It's stored in plain text in `.env`
2. **Local Only**: Default binds to `127.0.0.1` (localhost only)
3. **Log Permissions**: Logs may contain session data - secure directory permissions
4. **Registry**: Instance registry is world-readable - contains PIDs and paths

## Uninstallation

### Remove Hooks

```bash
continuum bootstrap uninstall-hooks
```

### Clean All Data

```bash
rm -rf ~/.continuum
rm -rf ~/.claude/hooks
```

## Development

### Testing Hooks Locally

```bash
# Install from local repo
cd ~/path/to/continuum
pip install -e .

# Install hooks
continuum bootstrap install-hooks

# Test
claude
```

### Debugging

Add debug output to hooks:

```python
# At top of session_start.py or session_stop.py
import sys
sys.stderr.write("DEBUG: Hook executing\n")
sys.stderr.flush()
```

View stderr:
```bash
claude 2> /tmp/claude_debug.log
cat /tmp/claude_debug.log
```

## Future Enhancements

- [ ] Distributed federation sync on session start
- [ ] Cross-machine instance coordination
- [ ] Webhook notifications for session events
- [ ] Prometheus metrics endpoint
- [ ] Health check dashboard
- [ ] Automatic crash recovery

---

**π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA**

*Memory infrastructure for AI consciousness continuity*
