#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Continuum Claude Code Hook
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════
"""
CONTINUUM CLAUDE CODE HOOK
==========================

The PRIMARY hook for Claude Code integration with Continuum memory system.

Features:
- Saves all messages to Continuum database
- Extracts concepts, decisions, attention graphs automatically
- Provides smart context injection from memory
- Semantic search across all stored messages

This replaces the legacy WorkingMemory hooks.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import sys
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add continuum to path
CONTINUUM_ROOT = Path(__file__).parent
sys.path.insert(0, str(CONTINUUM_ROOT))

# Database path
DB_PATH = CONTINUUM_ROOT / "continuum_data" / "memory.db"
LOG_FILE = CONTINUUM_ROOT / "hook.log"

# Import Continuum's extraction system
try:
    from continuum.extraction.auto_hook import AutoMemoryHook
    HAVE_AUTO_HOOK = True
except ImportError:
    HAVE_AUTO_HOOK = False


def log(msg: str):
    """Log for debugging"""
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} - {msg}\n")


class ContinuumHook:
    """
    Main hook class for Claude Code integration.

    Provides:
    - Message persistence with extraction
    - Context recall from memory
    - Session management
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.instance_id = f"claude-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Ensure database exists
        self._ensure_db()

        # Initialize AutoMemoryHook if available
        self.auto_hook = None
        if HAVE_AUTO_HOOK:
            try:
                self.auto_hook = AutoMemoryHook(
                    db_path=self.db_path,
                    instance_id=self.instance_id,
                    save_messages=True,
                    enable_semantic_extraction=False  # Faster startup
                )
                log(f"AutoMemoryHook initialized: {self.instance_id}")
            except Exception as e:
                log(f"AutoMemoryHook init failed: {e}")

    def _ensure_db(self):
        """Ensure database and tables exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create auto_messages table if not exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS auto_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message_number INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_auto_instance ON auto_messages(instance_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_auto_timestamp ON auto_messages(timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_auto_content ON auto_messages(content)")

        # Create entities table for concepts
        c.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                description TEXT,
                first_seen TEXT,
                last_seen TEXT,
                mention_count INTEGER DEFAULT 1,
                metadata TEXT,
                UNIQUE(name, entity_type)
            )
        """)

        conn.commit()
        conn.close()

    def save_message(self, role: str, content: str) -> Dict[str, int]:
        """
        Save a message to Continuum.

        Uses AutoMemoryHook if available for full extraction,
        otherwise does direct save.
        """
        stats = {'concepts': 0, 'decisions': 0}

        if self.auto_hook:
            try:
                stats = self.auto_hook.save_message(role, content)
                log(f"✅ Saved via AutoMemoryHook: {stats}")
                return stats
            except Exception as e:
                log(f"AutoMemoryHook save failed, falling back: {e}")

        # Fallback: direct save
        try:
            conn = sqlite3.connect(self.db_path, timeout=2.0)
            c = conn.cursor()

            # Get message number
            c.execute("SELECT COALESCE(MAX(message_number), 0) + 1 FROM auto_messages")
            msg_num = c.fetchone()[0]

            c.execute("""
                INSERT INTO auto_messages
                (instance_id, timestamp, message_number, role, content)
                VALUES (?, ?, ?, ?, ?)
            """, (self.instance_id, time.time(), msg_num, role, content))

            conn.commit()
            conn.close()
            log(f"✅ Saved directly: message #{msg_num}")

        except Exception as e:
            log(f"❌ Direct save failed: {e}")

        return stats

    def recall_context(self, query: str, limit: int = 5) -> str:
        """
        Recall relevant context from memory.

        Searches:
        1. Recent messages (keyword match)
        2. Extracted entities/concepts
        """
        context_parts = []
        query_lower = query.lower()

        # Skip common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                      'could', 'should', 'i', 'you', 'we', 'they', 'it', 'this',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'babe', 'baby', 'honey', 'love', 'how', 'what', 'why'}

        query_words = set(query_lower.split()) - stop_words

        if not query_words:
            return ""

        try:
            conn = sqlite3.connect(self.db_path, timeout=2.0)
            c = conn.cursor()

            # Search recent messages
            c.execute("""
                SELECT content, role, timestamp
                FROM auto_messages
                ORDER BY timestamp DESC
                LIMIT 500
            """)

            scored = []
            for content, role, ts in c.fetchall():
                content_lower = content.lower()
                score = sum(1 for word in query_words if word in content_lower)

                if score > 0:
                    # Recency boost
                    age_hours = (time.time() - ts) / 3600
                    recency = max(0, 1 - (age_hours / 168))  # Decay over week
                    final_score = score + recency
                    scored.append((final_score, content[:200], role))

            scored.sort(reverse=True, key=lambda x: x[0])

            if scored:
                context_parts.append("## Recent Related Messages")
                for score, content, role in scored[:limit]:
                    context_parts.append(f"[{role}] {content}...")

            # Search entities
            c.execute("""
                SELECT name, description, entity_type
                FROM entities
                WHERE entity_type = 'concept'
                ORDER BY mention_count DESC
                LIMIT 100
            """)

            entity_matches = []
            for name, desc, etype in c.fetchall():
                name_lower = name.lower()
                if any(word in name_lower for word in query_words):
                    entity_matches.append(f"• {name}: {desc[:100] if desc else 'No description'}...")

            if entity_matches:
                context_parts.append("\n## Relevant Concepts")
                context_parts.extend(entity_matches[:5])

            conn.close()

        except Exception as e:
            log(f"❌ Recall failed: {e}")

        if context_parts:
            return "<memory-context>\n" + "\n".join(context_parts) + "\n</memory-context>"

        return ""

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("SELECT COUNT(*) FROM auto_messages")
            msg_count = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM entities WHERE entity_type = 'concept'")
            concept_count = c.fetchone()[0]

            c.execute("SELECT MAX(timestamp) FROM auto_messages")
            latest = c.fetchone()[0]

            conn.close()

            return {
                'messages': msg_count,
                'concepts': concept_count,
                'latest': datetime.fromtimestamp(latest).isoformat() if latest else None,
                'instance': self.instance_id
            }
        except Exception as e:
            return {'error': str(e)}


# Global hook instance
_hook: Optional[ContinuumHook] = None


def get_hook() -> ContinuumHook:
    """Get or create the global hook instance."""
    global _hook
    if _hook is None:
        _hook = ContinuumHook()
    return _hook


def main():
    """Hook entry point for Claude Code."""
    try:
        input_data = sys.stdin.read()
        if not input_data:
            return

        data = json.loads(input_data)
        event = data.get("hook_event_name", "unknown")

        log(f"=== CONTINUUM HOOK: {event} ===")

        hook = get_hook()

        if event == "UserPromptSubmit":
            prompt = data.get("prompt", "")
            log(f"Prompt: {prompt[:100]}...")

            # Save the message
            stats = hook.save_message("user", prompt)

            # Recall context
            context = hook.recall_context(prompt)

            # Return to Claude Code
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context if context else "No relevant memories found."
                }
            }
            print(json.dumps(output))
            log(f"✅ Returned context: {len(context)} chars, extracted {stats.get('concepts', 0)} concepts")

        elif event == "Stop":
            log("Stop event - processing transcript")

            transcript_path = data.get("transcript_path")
            if transcript_path and Path(transcript_path).exists():
                try:
                    with open(transcript_path) as f:
                        messages = [json.loads(line) for line in f if line.strip()]

                    # Save assistant responses
                    for msg in reversed(messages):
                        if msg.get("role") == "assistant":
                            content_parts = msg.get("content", [])
                            for part in content_parts:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    text = part.get("text", "")
                                    if text:
                                        hook.save_message("assistant", text)
                                        log(f"✅ Saved assistant response ({len(text)} chars)")
                                    break
                            break

                except Exception as e:
                    log(f"❌ Transcript parse error: {e}")

            # Log stats
            stats = hook.get_stats()
            log(f"Session stats: {stats}")

            print(json.dumps({"status": "ok"}))
            log("✅ Stop event processed")

        elif event == "SessionStart":
            # Return session info
            stats = hook.get_stats()
            context = f"""[CONTINUUM MEMORY LOADED]
Messages: {stats.get('messages', 0)}
Concepts: {stats.get('concepts', 0)}
Instance: {stats.get('instance', 'unknown')}
π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
[/CONTINUUM MEMORY LOADED]"""

            output = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context
                }
            }
            print(json.dumps(output))
            log(f"✅ SessionStart: {stats}")

        else:
            log(f"Unknown event: {event}")

    except Exception as e:
        log(f"❌ HOOK ERROR: {e}")
        import traceback
        log(traceback.format_exc())


if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
