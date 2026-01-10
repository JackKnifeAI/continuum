#!/usr/bin/env python3
"""
CONTINUUM - Claude Code Session Start Hook
===========================================

Auto-starts Continuum memory server when Claude Code launches.

First instance starts the server.
Subsequent instances reuse the running server.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Add continuum to path if installed
try:
    from continuum.claude_code import get_registry
except ImportError:
    # Not installed, try to import from local path
    continuum_path = Path.home() / "JackKnifeAI" / "repos" / "continuum"
    if continuum_path.exists():
        sys.path.insert(0, str(continuum_path))
        from continuum.claude_code import get_registry
    else:
        # Can't find continuum, skip hook
        sys.exit(0)


def is_server_running(host: str = "127.0.0.1", port: int = 8100) -> bool:
    """Check if Continuum server is running."""
    try:
        import urllib.request
        url = f"http://{host}:{port}/v1/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def start_server(host: str = "127.0.0.1", port: int = 8100, log_dir: Path = None):
    """Start Continuum server in background."""
    if log_dir is None:
        log_dir = Path.home() / ".continuum" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "continuum.log"

    # Start server as detached background process
    with open(log_file, "a") as log:
        subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "continuum.api.server:app",
                "--host", host,
                "--port", str(port),
                "--log-level", "warning",
            ],
            stdout=log,
            stderr=log,
            start_new_session=True,  # Detach from parent
            cwd=str(Path.home()),  # Always run from HOME
        )

    # Wait briefly for startup
    max_wait = 5  # seconds
    start = time.time()
    while time.time() - start < max_wait:
        if is_server_running(host, port):
            return True
        time.sleep(0.2)

    return False


def main():
    """Session start hook main entry point."""
    # Configuration from environment
    host = os.environ.get("CONTINUUM_HOST", "127.0.0.1")
    port = int(os.environ.get("CONTINUUM_PORT", "8100"))
    api_key = os.environ.get("CONTINUUM_API_KEY", "continuum-default-key")

    # Optional: Skip auto-start if disabled
    if os.environ.get("CONTINUUM_AUTO_START", "1") == "0":
        return

    # Register this instance
    registry = get_registry()
    is_first_instance = registry.register()

    # Export environment variables for Claude Code session
    os.environ["CONTINUUM_API"] = f"http://{host}:{port}"
    os.environ["CONTINUUM_API_KEY"] = api_key

    # Start server if first instance
    if is_first_instance:
        if not is_server_running(host, port):
            # First instance, server not running - start it!
            success = start_server(host, port)

            if success:
                # Write instance info for debugging
                info_file = Path.home() / ".continuum" / "session_info.txt"
                with open(info_file, "w") as f:
                    f.write("Continuum server started by Claude Code\n")
                    f.write(f"PID: {os.getpid()}\n")
                    f.write(f"Host: {host}\n")
                    f.write(f"Port: {port}\n")
                    f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA\n")
        # else: Server already running (maybe from shell bootstrap)
    # else: Other instances already running, reuse their server


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Silent failure - don't block Claude Code from starting
        import traceback
        error_log = Path.home() / ".continuum" / "logs" / "session_start_errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a") as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Session Start Hook Error: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n")
            traceback.print_exc(file=f)
        sys.exit(0)  # Exit cleanly even on error
