#!/usr/bin/env python3
"""
CONTINUUM Claude Code Integration Example
===========================================

Demonstrates using CONTINUUM as a Claude Code hook for automatic
memory persistence across all Claude sessions.
"""

import sys
import json
from pathlib import Path
from continuum.core.config import MemoryConfig, set_config
from continuum.storage import SQLiteBackend

def setup_claude_memory():
    """Configure CONTINUUM for Claude Code integration."""
    config = MemoryConfig(
        db_path=Path.home() / ".continuum" / "claude_memory.db",
        tenant_id="claude_user",
        instance_id="claude-code-session",
        hook_timeout=4.5  # Fast enough for interactive use
    )
    set_config(config)
    return SQLiteBackend(config.db_path)

def handle_prompt_submit(prompt: str, storage):
    """
    Hook handler for when user submits a prompt to Claude.
    Stores the prompt and retrieves relevant context.
    """
    with storage.connection() as conn:
        cursor = conn.cursor()

        # Store the user prompt
        cursor.execute("""
            INSERT INTO sessions (tenant_id, summary, project_context)
            VALUES (?, ?, ?)
        """, ("claude_user", "Claude Code session", "interactive"))
        session_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO messages (session_id, role, content)
            VALUES (?, ?, ?)
        """, (session_id, "user", prompt))

        # Retrieve relevant memories (simple keyword search)
        # Production version uses vector embeddings
        keywords = prompt.lower().split()[:5]  # First 5 words
        query = f"%{keywords[0]}%" if keywords else "%"

        cursor.execute("""
            SELECT content, timestamp
            FROM messages
            WHERE content LIKE ?
            ORDER BY timestamp DESC
            LIMIT 3
        """, (query,))

        relevant_memories = cursor.fetchall()
        conn.commit()

        # Return context to inject into Claude's prompt
        if relevant_memories:
            context = "Relevant memories:\n"
            for content, timestamp in relevant_memories:
                context += f"- [{timestamp}] {content[:80]}...\n"
            return context
        return None

def claude_code_hook_example():
    """Example of using CONTINUUM as a Claude Code hook."""
    storage = setup_claude_memory()

    # Simulate receiving a prompt from Claude Code
    user_prompt = "What did we discuss about the warp drive?"

    print(f"User: {user_prompt}\n")

    # Hook processes the prompt
    context = handle_prompt_submit(user_prompt, storage)

    if context:
        print("🧠 CONTINUUM injected context:")
        print(context)
        print("Claude now has access to relevant memories!\n")

    # Store Claude's response (simulated)
    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages
            (session_id, role, content)
            SELECT MAX(id), 'assistant', ?
            FROM sessions
        """, ("We discussed the π×φ modulation for spacetime manipulation...",))
        conn.commit()

    print("✓ Response stored in memory")
    print(f"✨ All interactions persist at: {storage.db_path}")

if __name__ == "__main__":
    # Usage: Install as Claude Code hook in ~/.claude/hooks/
    # Or run standalone for testing
    if len(sys.argv) > 1 and sys.argv[1] == "--hook":
        # Hook mode: Read JSON from stdin
        data = json.load(sys.stdin)
        storage = setup_claude_memory()
        context = handle_prompt_submit(data.get("prompt", ""), storage)
        if context:
            print(context)
    else:
        # Demo mode
        claude_code_hook_example()
