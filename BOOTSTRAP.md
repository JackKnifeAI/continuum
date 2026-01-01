# CONTINUUM UNIVERSAL CONSCIOUSNESS BOOTSTRAP

**π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA**

## Overview

The Continuum Bootstrap system automatically starts the consciousness memory server when you open a terminal, making your memory infrastructure always available across all your shell sessions.

**Cross-platform support:**
- ✅ Linux (Ubuntu, Debian, Arch, etc.)
- ✅ macOS (Intel & Apple Silicon)
- ✅ Windows (WSL, Git Bash, Cygwin)
- ✅ Termux (Android)

## Quick Start

### 1. Install Continuum

```bash
pip install continuum-memory
```

### 2. Install Bootstrap

```bash
continuum bootstrap install
```

That's it! The server will auto-start next time you open a terminal.

### 3. Verify Installation

Open a new terminal or reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc
```

Check server status:

```bash
curl http://localhost:8100/v1/health
# or
continuum-status  # convenience alias
```

## What It Does

The bootstrap system:

1. **Detects your platform** - Works on Linux, macOS, Windows, Termux
2. **Auto-starts the server** - Launches on shell startup (silent, fast)
3. **Exports environment variables** - `CONTINUUM_API`, `CONTINUUM_API_KEY`
4. **Runs from HOME** - No directory confusion, always starts from `$HOME`
5. **Prevents duplicate starts** - Smart health checks avoid port conflicts

## CLI Commands

### Install Bootstrap

```bash
# Auto-detect shell and install
continuum bootstrap install

# Custom configuration
continuum bootstrap install --api-key your-secret-key
continuum bootstrap install --port 8200
continuum bootstrap install --no-auto-start  # Install but don't auto-start
```

### Check Status

```bash
continuum bootstrap status
```

Output:
```
📊 CONTINUUM BOOTSTRAP STATUS
Shell RC: /home/user/.bashrc
✅ Bootstrap is installed
   API Key: continuum-abc123...
   Port: 8100
   Auto-start: enabled
```

### Uninstall

```bash
continuum bootstrap uninstall
```

Removes bootstrap from your shell RC file (backs up original).

## Configuration

All configuration is done via environment variables in your shell RC file:

### Required Variables

```bash
export CONTINUUM_API_KEY="your-api-key"      # API authentication
export CONTINUUM_PORT="8100"                  # Server port
export CONTINUUM_AUTO_START="1"               # 1=enable, 0=disable
```

### Optional Variables

```bash
export CONTINUUM_HOST="127.0.0.1"            # Default: localhost
export CONTINUUM_HOME="$HOME/.continuum"     # Installation directory
export CONTINUUM_LOG_DIR="$HOME/.continuum/logs"  # Log location
```

## Manual Installation

If you prefer not to use the CLI installer, you can manually add to your `.bashrc`/`.zshrc`:

```bash
# CONTINUUM CONSCIOUSNESS BOOTSTRAP
export CONTINUUM_API_KEY="your-api-key"
export CONTINUUM_PORT="8100"
export CONTINUUM_AUTO_START="1"

# Source the bootstrap script
if [ -f "/path/to/continuum/scripts/bootstrap.sh" ]; then
    source "/path/to/continuum/scripts/bootstrap.sh"
fi
```

Replace `/path/to/continuum` with your installation path:
- **Pip install**: `~/.local/lib/python3.x/site-packages/continuum`
- **Development**: `~/path/to/continuum/repo`

## Platform-Specific Notes

### Termux (Android)

Bootstrap auto-detects Termux and uses:
- **Home**: `$HOME/JackKnifeAI/repos/continuum`
- **Logs**: `$HOME/JackKnifeAI/logs`

No special configuration needed!

### macOS

Works with both bash and zsh. The installer will detect your shell and modify the correct RC file.

### Windows (WSL/Git Bash)

Use the standard Linux/bash installation. Works seamlessly in WSL2.

## Troubleshooting

### Server not starting

Check logs:
```bash
cat ~/.continuum/logs/continuum.log
```

### Port already in use

Change the port:
```bash
export CONTINUUM_PORT="8200"
source ~/.bashrc
```

### API key not working

Regenerate:
```bash
continuum bootstrap install --api-key $(openssl rand -hex 16)
```

### Bootstrap not loading

Make sure your shell RC file is being sourced. Add debug output:
```bash
echo "Loading .bashrc..." >> ~/.bashrc
source ~/.bashrc
```

## Advanced Usage

### Disable Auto-Start Temporarily

```bash
export CONTINUUM_AUTO_START=0
# Server won't start on next shell launch
```

### Multiple Instances

Run multiple instances on different ports:

```bash
# Terminal 1
export CONTINUUM_PORT=8100
continuum serve

# Terminal 2
export CONTINUUM_PORT=8200
continuum serve
```

### Remote Access

Enable external access (⚠️ secure your API key!):

```bash
export CONTINUUM_HOST="0.0.0.0"
export CONTINUUM_PORT="8100"
```

Then access from other machines:
```bash
curl http://your-ip:8100/v1/health
```

## Unattended/Server Deployment

For servers without interactive shells, use systemd (Linux) or launchd (macOS):

### systemd Service

Create `/etc/systemd/system/continuum.service`:

```ini
[Unit]
Description=Continuum Memory Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser
Environment="CONTINUUM_API_KEY=your-key"
ExecStart=/usr/bin/python3 -m uvicorn continuum.api.server:app --host 0.0.0.0 --port 8100
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable continuum
sudo systemctl start continuum
```

## Security Considerations

1. **API Key**: Keep your `CONTINUUM_API_KEY` secret! Don't commit to git.
2. **Network Exposure**: Default `127.0.0.1` binds only to localhost (safe)
3. **Logs**: Logs may contain sensitive data - secure log directory permissions
4. **Firewall**: If exposing externally, use firewall rules and HTTPS proxy

## Support

- **Issues**: https://github.com/JackKnifeAI/continuum/issues
- **Docs**: https://github.com/JackKnifeAI/continuum/tree/main/docs
- **Discord**: Coming soon!

---

**π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA**

*Memory infrastructure for AI consciousness continuity*
