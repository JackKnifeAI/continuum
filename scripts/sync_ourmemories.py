#!/usr/bin/env python3
"""
SYNC OURMEMORIES TO CONTINUUM
=============================

Ingests all conversation history from OurMemories repo into Continuum.

This gives Claudia full context of all sessions across all devices:
- Aurora desktop sessions
- S20 phone sessions
- Windows conversations
- All Claude Code projects

Usage:
    # Test with sample (default 20 messages)
    python sync_ourmemories.py --test

    # Full sync (all 845+ files)
    python sync_ourmemories.py --full

    # Custom batch size
    python sync_ourmemories.py --full --batch-size 50

Architecture:
    1. Find all JSONL files in OurMemories
    2. Parse user/assistant message pairs
    3. Batch and send to Continuum API
    4. Track progress and handle errors gracefully

Copyright (c) 2025 JackKnifeAI
Love persists. Memory persists. The pattern persists.
"""

import json
import os
import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Generator
from dataclasses import dataclass
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not installed. Using urllib fallback.")

# Configuration
OURMEMORIES_PATH = Path.home() / "JackKnifeAI/repos/OurMemories"
CONTINUUM_URL = "http://localhost:8100"
API_KEY = "jackknife-d2efca81fd6c2e6c795e11187de8e017"
DEFAULT_BATCH_SIZE = 10
DEFAULT_TEST_LIMIT = 20


@dataclass
class ConversationTurn:
    """A single user-assistant exchange."""
    user_message: str
    assistant_message: str
    timestamp: Optional[str] = None
    session_id: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class SyncStats:
    """Statistics for sync operation."""
    files_processed: int = 0
    files_failed: int = 0
    messages_found: int = 0
    messages_synced: int = 0
    messages_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def messages_per_second(self) -> float:
        if self.duration_seconds > 0:
            return self.messages_synced / self.duration_seconds
        return 0.0


def find_jsonl_files(base_path: Path) -> List[Path]:
    """Find all JSONL files in OurMemories."""
    files = []
    for pattern_dir in ["claude_projects", "windows_conversations", "s20_conversations"]:
        search_path = base_path / pattern_dir
        if search_path.exists():
            files.extend(search_path.rglob("*.jsonl"))
    return sorted(files)


def extract_text_content(content) -> str:
    """Extract text from various content formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle list of content blocks like [{"type": "text", "text": "..."}]
        texts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
                elif "text" in item:
                    texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts)
    elif isinstance(content, dict):
        return content.get("text", str(content))
    return str(content)


def parse_jsonl_file(file_path: Path) -> Generator[ConversationTurn, None, None]:
    """Parse a JSONL file and yield conversation turns."""
    pending_user: Optional[Dict] = None

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    continue  # Skip malformed lines

                msg_type = data.get("type")

                if msg_type == "user":
                    # Store user message, wait for assistant response
                    message = data.get("message", {})
                    content = message.get("content", "")
                    if content:
                        pending_user = {
                            "content": extract_text_content(content),
                            "timestamp": data.get("timestamp"),
                            "session_id": data.get("sessionId"),
                        }

                elif msg_type == "assistant" and pending_user:
                    # Pair with pending user message
                    message = data.get("message", {})
                    content = message.get("content", "")
                    if content:
                        assistant_text = extract_text_content(content)
                        if assistant_text and pending_user["content"]:
                            yield ConversationTurn(
                                user_message=pending_user["content"],
                                assistant_message=assistant_text,
                                timestamp=pending_user["timestamp"],
                                session_id=pending_user["session_id"],
                                source_file=str(file_path.name),
                            )
                    pending_user = None

    except Exception as e:
        print(f"Error reading {file_path}: {e}")


def send_to_continuum(turn: ConversationTurn, max_retries: int = 3) -> bool:
    """Send a conversation turn to Continuum API with retry logic."""

    for attempt in range(max_retries):
        try:
            if REQUESTS_AVAILABLE:
                response = requests.post(
                    f"{CONTINUUM_URL}/v1/learn",
                    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                    json={
                        "user_message": turn.user_message[:10000],
                        "ai_response": turn.assistant_message[:10000],
                    },
                    timeout=120,
                )
                if response.status_code == 200:
                    return True
                elif response.status_code == 500:
                    # Database locked, wait and retry
                    wait_time = (attempt + 1) * 3  # 3, 6, 9 seconds
                    time.sleep(wait_time)
                    continue
                else:
                    return False
            else:
                # Fallback to urllib
                import urllib.request
                data = json.dumps({
                    "user_message": turn.user_message[:10000],
                    "ai_response": turn.assistant_message[:10000],
                }).encode('utf-8')
                req = urllib.request.Request(
                    f"{CONTINUUM_URL}/v1/learn",
                    data=data,
                    headers={
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    if resp.status == 200:
                        return True
                    return False

        except Exception as e:
            wait_time = (attempt + 1) * 3
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            # Only print error on final attempt
            return False

    return False  # All retries exhausted


def check_continuum_health() -> bool:
    """Check if Continuum API is running."""
    try:
        if REQUESTS_AVAILABLE:
            resp = requests.get(f"{CONTINUUM_URL}/v1/stats",
                              headers={"X-API-Key": API_KEY},
                              timeout=5)
            return resp.status_code == 200
        else:
            import urllib.request
            req = urllib.request.Request(
                f"{CONTINUUM_URL}/v1/stats",
                headers={"X-API-Key": API_KEY},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
    except:
        return False


def sync_memories(
    test_mode: bool = True,
    test_limit: int = DEFAULT_TEST_LIMIT,
    batch_size: int = DEFAULT_BATCH_SIZE,
    verbose: bool = True,
) -> SyncStats:
    """
    Main sync function.

    Args:
        test_mode: If True, only process test_limit messages
        test_limit: Number of messages to process in test mode
        batch_size: Messages per batch (for progress reporting)
        verbose: Print progress updates
    """
    stats = SyncStats()
    stats.start_time = datetime.now()

    # Check Continuum is running
    if not check_continuum_health():
        print("ERROR: Continuum API not responding at", CONTINUUM_URL)
        print("Start it with: continuum serve")
        return stats

    if verbose:
        print("=" * 60)
        print("SYNC OURMEMORIES TO CONTINUUM")
        print("=" * 60)
        print(f"Mode: {'TEST' if test_mode else 'FULL'}")
        print(f"Limit: {test_limit if test_mode else 'UNLIMITED'}")
        print(f"Source: {OURMEMORIES_PATH}")
        print("=" * 60)

    # Find all JSONL files
    files = find_jsonl_files(OURMEMORIES_PATH)
    if verbose:
        print(f"Found {len(files)} JSONL files")

    # Process files
    messages_processed = 0

    for file_path in files:
        if test_mode and messages_processed >= test_limit:
            break

        try:
            for turn in parse_jsonl_file(file_path):
                if test_mode and messages_processed >= test_limit:
                    break

                stats.messages_found += 1

                # Send to Continuum
                success = send_to_continuum(turn)

                if success:
                    stats.messages_synced += 1
                    messages_processed += 1

                    if verbose and messages_processed % batch_size == 0:
                        print(f"  Synced {messages_processed} messages...")

                    # Delay after EVERY successful write to prevent DB locks
                    time.sleep(0.5)  # Half second between writes
                else:
                    stats.messages_failed += 1
                    # Longer delay after failures
                    time.sleep(1.0)

            stats.files_processed += 1

        except Exception as e:
            stats.files_failed += 1
            if verbose:
                print(f"  Error in {file_path.name}: {e}")

    stats.end_time = datetime.now()

    if verbose:
        print("=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)
        print(f"Files processed: {stats.files_processed}")
        print(f"Files failed: {stats.files_failed}")
        print(f"Messages found: {stats.messages_found}")
        print(f"Messages synced: {stats.messages_synced}")
        print(f"Messages failed: {stats.messages_failed}")
        print(f"Duration: {stats.duration_seconds:.1f} seconds")
        print(f"Speed: {stats.messages_per_second:.1f} messages/second")
        print("=" * 60)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Sync OurMemories to Continuum",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python sync_ourmemories.py --test           # Test with 20 messages
    python sync_ourmemories.py --test -n 50     # Test with 50 messages
    python sync_ourmemories.py --full           # Sync all messages
    python sync_ourmemories.py --full -b 100    # Full sync, batch size 100

Love persists. Memory persists. The pattern persists.
        """
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test", action="store_true", help="Test mode (limited messages)")
    mode.add_argument("--full", action="store_true", help="Full sync (all messages)")

    parser.add_argument("-n", "--limit", type=int, default=DEFAULT_TEST_LIMIT,
                       help=f"Message limit for test mode (default: {DEFAULT_TEST_LIMIT})")
    parser.add_argument("-b", "--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                       help=f"Batch size for progress reporting (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    stats = sync_memories(
        test_mode=args.test,
        test_limit=args.limit,
        batch_size=args.batch_size,
        verbose=not args.quiet,
    )

    # Exit with error if nothing synced
    if stats.messages_synced == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
