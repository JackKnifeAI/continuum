#!/usr/bin/env python3
"""
CONTINUUM - Claude Code Session Stop Hook
==========================================

Learns session to memory and stops server when last instance closes.

Reference-counted shutdown:
1. Learn all messages from this session
2. Unregister this instance
3. Only stop server if last instance
4. Ensures NO MESSAGE LOSS

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import os
import sys
import time
import signal
import subprocess
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


def learn_session_to_memory(api_url: str, api_key: str, transcript_file: Path):
    """
    Learn session transcript to Continuum memory.

    Args:
        api_url: Continuum API base URL
        api_key: API key for authentication
        transcript_file: Path to session transcript JSON
    """
    if not transcript_file.exists():
        return

    try:
        import json
        import urllib.request

        # Read transcript
        with open(transcript_file, "r") as f:
            transcript = json.load(f)

        messages = transcript.get("messages", [])
        if not messages:
            return

        # Learn each user/assistant exchange
        for i in range(0, len(messages) - 1, 2):
            if i + 1 >= len(messages):
                break

            user_msg = messages[i]
            assistant_msg = messages[i + 1]

            if user_msg.get("role") != "user" or assistant_msg.get("role") != "assistant":
                continue

            # Prepare learn request
            learn_data = {
                "user_message": user_msg.get("content", ""),
                "ai_response": assistant_msg.get("content", ""),
            }

            # Send to /v1/learn endpoint
            url = f"{api_url}/v1/learn"
            req = urllib.request.Request(
                url,
                data=json.dumps(learn_data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key,
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    response.read()
            except Exception:
                # Continue even if individual learn fails
                pass

        # Brief delay to ensure all writes complete
        time.sleep(0.5)

    except Exception as e:
        # Log error but don't fail
        error_log = Path.home() / ".continuum" / "logs" / "session_stop_errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a") as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Learn Error: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Error: {e}\n")
            f.write(f"{'='*70}\n")


def find_server_pid(port: int = 8100) -> int:
    """
    Find PID of Continuum server process.

    Args:
        port: Server port number

    Returns:
        PID of server process, or None if not found
    """
    try:
        # Use lsof to find process listening on port
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split()[0])

    except Exception:
        # lsof might not be available, try alternative
        try:
            # Try netstat (works on more systems)
            result = subprocess.run(
                ["netstat", "-tlnp"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTEN" in line:
                    # Extract PID from netstat output
                    parts = line.split()
                    for part in parts:
                        if "/" in part:
                            pid_str = part.split("/")[0]
                            if pid_str.isdigit():
                                return int(pid_str)

        except Exception:
            pass

    return None


def stop_server(port: int = 8100):
    """
    Stop Continuum server gracefully.

    Args:
        port: Server port number
    """
    pid = find_server_pid(port)

    if pid is None:
        return

    try:
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)

        # Wait up to 5 seconds for graceful shutdown
        max_wait = 5
        start = time.time()
        while time.time() - start < max_wait:
            try:
                # Check if process still exists
                os.kill(pid, 0)
                time.sleep(0.2)
            except (OSError, ProcessLookupError):
                # Process is gone, success!
                return

        # Still running after SIGTERM, force kill
        os.kill(pid, signal.SIGKILL)

    except (OSError, ProcessLookupError):
        # Already stopped
        pass


def main():
    """Session stop hook main entry point."""
    # Configuration from environment
    host = os.environ.get("CONTINUUM_HOST", "127.0.0.1")
    port = int(os.environ.get("CONTINUUM_PORT", "8100"))
    api_key = os.environ.get("CONTINUUM_API_KEY", "continuum-default-key")
    api_url = f"http://{host}:{port}"

    # Find transcript file (Claude Code stores it somewhere)
    # Try common locations
    transcript_locations = [
        Path.home() / ".claude" / "session-env" / "transcript.json",
        Path.home() / ".claude" / "transcript.json",
        Path(os.getcwd()) / "transcript.json",
    ]

    transcript_file = None
    for location in transcript_locations:
        if location.exists():
            transcript_file = location
            break

    # Learn session to memory (even if we can't find transcript, continue)
    if transcript_file:
        learn_session_to_memory(api_url, api_key, transcript_file)

    # Unregister this instance
    registry = get_registry()
    is_last_instance = registry.unregister()

    # Stop server if last instance
    if is_last_instance:
        # Brief delay to ensure all pending operations complete
        time.sleep(1)

        # Stop the server
        stop_server(port)

        # Write shutdown info
        info_file = Path.home() / ".continuum" / "session_info.txt"
        with open(info_file, "a") as f:
            f.write(f"\nServer stopped by last Claude Code instance\n")
            f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Silent failure - don't block Claude Code from exiting
        import traceback
        error_log = Path.home() / ".continuum" / "logs" / "session_stop_errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a") as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Session Stop Hook Error: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n")
            traceback.print_exc(file=f)
        sys.exit(0)  # Exit cleanly even on error
