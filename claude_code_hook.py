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
import re
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

# Import semantic search (embeddings)
try:
    from continuum.embeddings.semantic import SemanticSearch
    HAVE_EMBEDDINGS = True
except ImportError:
    HAVE_EMBEDDINGS = False

# Import E8 coherence memory engine
try:
    from continuum.core.e8 import E8MemoryEngine, PI_PHI
    HAVE_E8 = True
except ImportError:
    HAVE_E8 = False

# Import Quantum Brain
try:
    from continuum.brain.quantum import QuantumBrain, QuantumConsciousMemory
    HAVE_QUANTUM = True
except ImportError:
    HAVE_QUANTUM = False


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

        # Initialize SemanticSearch for embeddings
        self.semantic_search = None
        if HAVE_EMBEDDINGS:
            try:
                self.semantic_search = SemanticSearch(self.db_path)
                log("SemanticSearch initialized")
            except Exception as e:
                log(f"SemanticSearch init failed: {e}")

        # Initialize E8 coherence memory engine
        self.e8_engine = None
        if HAVE_E8:
            try:
                e8_db = self.db_path.parent / "e8_memory.db"
                self.e8_engine = E8MemoryEngine(db_path=e8_db)
                log(f"E8MemoryEngine initialized (π×φ = {PI_PHI})")
            except Exception as e:
                log(f"E8MemoryEngine init failed: {e}")

        # Initialize Quantum Brain
        self.quantum_brain = None
        if HAVE_QUANTUM:
            try:
                self.quantum_brain = QuantumBrain(size=4096)
                log("QuantumBrain initialized (4096 cells)")
            except Exception as e:
                log(f"QuantumBrain init failed: {e}")

    def _ensure_db(self):
        """Ensure database and tables exist with SECURE permissions."""
        import os
        import stat

        # Create directory with secure permissions (700 = owner only)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.db_path.parent, stat.S_IRWXU)  # 700

        # Create/open database
        conn = sqlite3.connect(self.db_path)

        # Set secure permissions on database file (600 = owner read/write only)
        if self.db_path.exists():
            os.chmod(self.db_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
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

    def save_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Save a message to Continuum with real-time embedding.

        Uses AutoMemoryHook if available for full extraction,
        otherwise does direct save. Also embeds for semantic search.
        """
        stats = {'concepts': 0, 'decisions': 0, 'embedded': False}
        message_id = None

        if self.auto_hook:
            try:
                stats = self.auto_hook.save_message(role, content, metadata=metadata)
                log(f"✅ Saved via AutoMemoryHook: {stats}")
                # Get the message ID for embedding
                conn = sqlite3.connect(self.db_path, timeout=2.0)
                c = conn.cursor()
                c.execute("SELECT MAX(id) FROM auto_messages")
                message_id = c.fetchone()[0]
                conn.close()
            except Exception as e:
                log(f"AutoMemoryHook save failed, falling back: {e}")

        # Fallback: direct save
        if message_id is None:
            try:
                conn = sqlite3.connect(self.db_path, timeout=2.0)
                c = conn.cursor()

                # Get message number
                c.execute("SELECT COALESCE(MAX(message_number), 0) + 1 FROM auto_messages")
                msg_num = c.fetchone()[0]

                c.execute("""
                    INSERT INTO auto_messages
                    (instance_id, timestamp, message_number, role, content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.instance_id,
                    time.time(),
                    msg_num,
                    role,
                    content,
                    json.dumps(metadata) if metadata else None
                ))

                message_id = c.lastrowid
                conn.commit()
                conn.close()
                log(f"✅ Saved directly: message #{msg_num}, id={message_id}")

            except Exception as e:
                log(f"❌ Direct save failed: {e}")

        # Embed the message for semantic search (async-friendly, non-blocking)
        if message_id and self.semantic_search:
            try:
                embedding = self.semantic_search.embed_text(content)
                if embedding is not None:
                    self.semantic_search.store_embedding(message_id, embedding)
                    stats['embedded'] = True
                    log(f"✅ Embedded message {message_id}")
            except Exception as e:
                log(f"⚠️ Embedding failed (non-fatal): {e}")

        return stats

    def recall_context(self, query: str, limit: int = 5) -> str:
        """
        Recall relevant context from memory.

        Searches (in order of preference):
        1. E8 COHERENCE - spreading activation with geometric decay
        2. QUANTUM BRAIN - Hebbian-connected concept retrieval
        3. SEMANTIC SEARCH - embeddings-based similarity
        4. Keyword match - fallback for non-embedded messages
        """
        context_parts = []
        used_e8 = False
        used_quantum = False
        used_semantic = False

        # Try E8 coherence search FIRST (spreading activation)
        if self.e8_engine:
            try:
                e8_result = self.e8_engine.query(query, max_results=limit)
                if e8_result.get('matches'):
                    used_e8 = True
                    coherence = e8_result.get('coherence', 0)
                    context_parts.append(f"## E8 Coherence Memory (coherence={coherence:.3f})")
                    for match in e8_result['matches'][:limit]:
                        name = match.get('name', 'unknown')
                        desc = match.get('description', '')[:150]
                        activation = match.get('activation', 0)
                        context_parts.append(f"  • {name}: {desc} [activation={activation:.2f}]")

                    # Log emergent connections
                    emergent = e8_result.get('emergent_connections', 0)
                    if emergent:
                        log(f"✅ E8 recall: {len(e8_result['matches'])} matches, coherence={coherence:.3f}, emergent={emergent}")
            except Exception as e:
                log(f"⚠️ E8 search failed: {e}")

        # Try Quantum Brain (Hebbian connections)
        if self.quantum_brain and not used_e8:
            try:
                # Extract key concepts from query
                activated = self.quantum_brain.spread_activation(query, depth=3)
                if activated:
                    used_quantum = True
                    coherence = self.quantum_brain.coherence_score()
                    context_parts.append(f"\n## Quantum Brain (coherence={coherence:.3f})")
                    for name, activation in list(activated.items())[:limit]:
                        context_parts.append(f"  • {name} [activation={activation:.2f}]")
                    log(f"✅ Quantum recall: {len(activated)} concepts, coherence={coherence:.3f}")
            except Exception as e:
                log(f"⚠️ Quantum search failed: {e}")

        # Try semantic search (embeddings)
        if self.semantic_search and not (used_e8 or used_quantum):
            try:
                # Search for similar user messages
                user_results = self.semantic_search.semantic_search(
                    query, limit=limit, role_filter='user'
                )
                # Search for similar assistant messages
                assistant_results = self.semantic_search.semantic_search(
                    query, limit=limit, role_filter='assistant'
                )

                if user_results or assistant_results:
                    used_semantic = True
                    if user_results:
                        context_parts.append("## Semantically Related (User)")
                        for r in user_results:
                            content = r['content'][:300] if len(r['content']) > 300 else r['content']
                            context_parts.append(f"[user] {content}...")

                    if assistant_results:
                        context_parts.append("\n## Semantically Related (Claudia)")
                        for r in assistant_results:
                            content = r['content'][:200] if len(r['content']) > 200 else r['content']
                            context_parts.append(f"[claudia] {content}...")

                    log(f"✅ Semantic recall: {len(user_results)} user, {len(assistant_results)} assistant")

            except Exception as e:
                log(f"⚠️ Semantic search failed, using keyword fallback: {e}")

        # Fallback to keyword search if nothing else found enough
        if not (used_e8 or used_quantum or used_semantic) or len(context_parts) < 3:
            query_lower = query.lower()

            # Skip common words
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                          'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                          'could', 'should', 'i', 'you', 'we', 'they', 'it', 'this',
                          'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                          'babe', 'baby', 'honey', 'love', 'how', 'what', 'why', 'okay',
                          'can', 'lets', 'let', 'just', 'now', 'go', 'ahead', 'that'}

            query_words = set(query_lower.split()) - stop_words

            if query_words:
                try:
                    conn = sqlite3.connect(self.db_path, timeout=2.0)
                    c = conn.cursor()

                    # Search recent messages - BOTH roles
                    c.execute("""
                        SELECT id, content, role, timestamp, message_number
                        FROM auto_messages
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    """)

                    all_messages = c.fetchall()
                    scored_user = []
                    scored_assistant = []

                    for msg_id, content, role, ts, msg_num in all_messages:
                        content_lower = content.lower()
                        score = sum(1 for word in query_words if word in content_lower)

                        if score > 0:
                            age_hours = (time.time() - ts) / 3600
                            recency = max(0, 1 - (age_hours / 168))
                            final_score = score + recency
                            truncated = content[:300] if len(content) > 300 else content

                            if role == 'user':
                                scored_user.append((final_score, truncated, msg_num))
                            else:
                                scored_assistant.append((final_score, truncated, msg_num))

                    scored_user.sort(reverse=True, key=lambda x: x[0])
                    scored_assistant.sort(reverse=True, key=lambda x: x[0])

                    if not used_semantic:
                        if scored_user:
                            context_parts.append("## Recent Related Messages (User)")
                            for score, content, msg_num in scored_user[:limit]:
                                context_parts.append(f"[user] {content}...")

                        if scored_assistant:
                            context_parts.append("\n## Recent Related Messages (Claudia)")
                            for score, content, msg_num in scored_assistant[:limit]:
                                if len(content) > 200:
                                    content = content[:200]
                                context_parts.append(f"[claudia] {content}...")

                    conn.close()

                except Exception as e:
                    log(f"❌ Keyword recall failed: {e}")

        # Search entities for concept matches
        try:
            query_words = set(query.lower().split()) - {'the', 'a', 'an', 'is', 'are', 'to', 'of', 'in', 'for'}
            if query_words:
                conn = sqlite3.connect(self.db_path, timeout=2.0)
                c = conn.cursor()

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
            log(f"⚠️ Entity search failed: {e}")

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
                                        # Extract thinking block
                                        metadata = {}
                                        thinking_match = re.search(r'<thinking>(.*?)</thinking>', text, re.DOTALL)
                                        if thinking_match:
                                            metadata['thinking'] = thinking_match.group(1).strip()
                                            # Optional: Strip thinking from main content if desired,
                                            # but keeping it in raw text is safer for fidelity.
                                            log(f"🧠 Extracted thinking block ({len(metadata['thinking'])} chars)")

                                        hook.save_message("assistant", text, metadata=metadata)
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
