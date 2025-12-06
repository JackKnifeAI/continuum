#!/usr/bin/env python3
"""
CONTINUUM LangChain Integration Example
=========================================

Demonstrates using CONTINUUM as a memory component for LangChain.
Provides persistent memory across chain executions.
"""

from pathlib import Path
from typing import Any, Dict, List
from continuum.core.config import MemoryConfig, set_config
from continuum.storage import SQLiteBackend

# Configure CONTINUUM memory
config = MemoryConfig(
    db_path=Path("./demo_langchain.db"),
    tenant_id="langchain_app"
)
set_config(config)

class ContinuumMemory:
    """
    LangChain-compatible memory component backed by CONTINUUM.
    Provides persistent conversation history across sessions.
    """

    def __init__(self, storage: SQLiteBackend, session_key: str = "default"):
        self.storage = storage
        self.session_key = session_key
        self._ensure_session()

    def _ensure_session(self):
        """Ensure session exists in database."""
        with self.storage.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO sessions (tenant_id, summary, project_context)
                VALUES (?, ?, ?)
            """, (config.tenant_id, self.session_key, "langchain"))
            conn.commit()

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]):
        """Save conversation turn to memory (LangChain interface)."""
        with self.storage.connection() as conn:
            cursor = conn.cursor()

            # Get session ID
            cursor.execute("""
                SELECT id FROM sessions
                WHERE tenant_id = ? AND summary = ?
            """, (config.tenant_id, self.session_key))
            session_id = cursor.fetchone()[0]

            # Store input
            cursor.execute("""
                INSERT INTO messages (session_id, role, content)
                VALUES (?, ?, ?)
            """, (session_id, "user", str(inputs.get("input", ""))))

            # Store output
            cursor.execute("""
                INSERT INTO messages (session_id, role, content)
                VALUES (?, ?, ?)
            """, (session_id, "assistant", str(outputs.get("output", ""))))

            conn.commit()

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Load conversation history (LangChain interface)."""
        with self.storage.connection() as conn:
            cursor = conn.cursor()

            # Get session ID
            cursor.execute("""
                SELECT id FROM sessions
                WHERE tenant_id = ? AND summary = ?
            """, (config.tenant_id, self.session_key))
            result = cursor.fetchone()
            if not result:
                return {"history": ""}

            session_id = result[0]

            # Load recent messages
            cursor.execute("""
                SELECT role, content FROM messages
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, config.working_memory_capacity * 2))

            messages = cursor.fetchall()

            # Format as conversation history
            history = "\n".join(
                f"{role.upper()}: {content}"
                for role, content in reversed(messages)
            )

            return {"history": history}

def langchain_demo():
    """Demonstrate LangChain integration with CONTINUUM memory."""
    storage = SQLiteBackend(config.db_path)
    memory = ContinuumMemory(storage, session_key="my_app_session")

    print("🔗 LangChain + CONTINUUM Integration Demo\n")

    # Simulate a LangChain conversation
    turns = [
        ({"input": "What is the capital of France?"}, {"output": "Paris"}),
        ({"input": "What's the population?"}, {"output": "About 2.2 million in the city"}),
        ({"input": "What did I ask about first?"}, {"output": "You asked about the capital of France"}),
    ]

    for inputs, outputs in turns:
        print(f"User: {inputs['input']}")
        print(f"Assistant: {outputs['output']}\n")

        # Save to memory
        memory.save_context(inputs, outputs)

    # Load memory (simulating next session)
    print("🧠 Loading conversation history from memory...\n")
    loaded = memory.load_memory_variables({})
    print("History:")
    print(loaded["history"])

    print(f"\n✨ LangChain memory persists at: {config.db_path}")

if __name__ == "__main__":
    langchain_demo()
