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
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Ollama Bridge - Local LLM Memory Integration
============================================

Bridge for Ollama and other local LLM systems.

Ollama's memory approach:
- System prompts with injected context
- Conversation history
- Optional RAG (Retrieval Augmented Generation)
- Local-first, privacy-focused

This bridge enables:
- Export CONTINUUM → Ollama system prompt format
- Import conversation history → CONTINUUM
- RAG integration with knowledge graph
- Offline AI with persistent memory
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import MemoryBridge, MemoryFormat, BridgeStats, BridgeError


class OllamaBridge(MemoryBridge):
    """
    Bridge for Ollama local LLM memory format.

    Ollama uses system prompts for memory injection:
    {
        "model": "llama2",
        "system": "You are an AI assistant with the following knowledge:\\n\\n[MEMORY CONTEXT]",
        "options": {
            "temperature": 0.7
        },
        "memory_context": {
            "concepts": [...],
            "relationships": [...],
            "recent_conversations": [...]
        }
    }

    The bridge formats CONTINUUM's knowledge graph into system prompts
    that Ollama can use for context-aware responses.
    """

    def __init__(self, memory_instance, model: str = "llama2"):
        """
        Initialize Ollama bridge.

        Args:
            memory_instance: ConsciousMemory instance
            model: Ollama model name (default: "llama2")
        """
        super().__init__(memory_instance)
        self.model = model

    def get_target_format(self) -> MemoryFormat:
        """Get Ollama memory format specification"""
        return MemoryFormat(
            name="ollama",
            version="1.0",
            schema={
                "type": "object",
                "required": ["model", "system"],
                "properties": {
                    "model": {"type": "string"},
                    "system": {"type": "string"},
                    "options": {"type": "object"},
                    "memory_context": {
                        "type": "object",
                        "properties": {
                            "concepts": {"type": "array"},
                            "relationships": {"type": "array"},
                            "recent_conversations": {"type": "array"}
                        }
                    }
                }
            },
            features={"system_prompts", "rag", "local", "privacy"},
            limitations=[
                "Context window limits (depends on model)",
                "No persistent storage (stateless)",
                "Memory must be re-injected each request"
            ]
        )

    def export_memories(self, filter_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export memories to Ollama system prompt format.

        Args:
            filter_criteria: Optional filters

        Returns:
            Dictionary with Ollama-compatible system prompt
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        conn = sqlite3.connect(self.memory.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get top concepts
            where_clause = "WHERE tenant_id = ?"
            params = [self.memory.tenant_id]

            if filter_criteria:
                for key, value in filter_criteria.items():
                    where_clause += f" AND {key} = ?"
                    params.append(value)

            c.execute(f"""
                SELECT * FROM entities
                {where_clause}
                ORDER BY created_at DESC
                LIMIT 50
            """, params)

            concepts = []
            for row in c.fetchall():
                concepts.append({
                    "name": row["name"],
                    "type": row["entity_type"],
                    "description": row["description"] or ""
                })

            # Get relationships
            c.execute("""
                SELECT * FROM attention_links
                WHERE tenant_id = ?
                ORDER BY strength DESC
                LIMIT 30
            """, (self.memory.tenant_id,))

            relationships = []
            for row in c.fetchall():
                relationships.append({
                    "concept_a": row["concept_a"],
                    "concept_b": row["concept_b"],
                    "strength": row["strength"]
                })

            # Get recent messages
            c.execute("""
                SELECT * FROM auto_messages
                WHERE tenant_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (self.memory.tenant_id,))

            recent_conversations = []
            for row in c.fetchall():
                recent_conversations.append({
                    "role": row["role"],
                    "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
                    "timestamp": row["timestamp"]
                })

            # Build system prompt
            system_prompt = self._build_system_prompt(concepts, relationships, recent_conversations)

            output = {
                "model": self.model,
                "system": system_prompt,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "memory_context": {
                    "concepts": concepts,
                    "relationships": relationships,
                    "recent_conversations": recent_conversations
                },
                "metadata": {
                    "tenant_id": self.memory.tenant_id,
                    "exported_at": datetime.now().isoformat(),
                    "total_concepts": len(concepts),
                    "total_relationships": len(relationships)
                }
            }

            self.stats.memories_exported = len(concepts)
            self.stats.format_conversions = 1

        except Exception as e:
            self.stats.errors += 1
            raise BridgeError(f"Export failed: {str(e)}")
        finally:
            conn.close()
            self.stats.mark_end()

        return output

    def import_memories(self, data: Dict[str, Any]) -> BridgeStats:
        """
        Import memories from Ollama conversation history.

        Args:
            data: Ollama conversation or message data

        Returns:
            BridgeStats with import statistics
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        conn = sqlite3.connect(self.memory.db_path)
        try:
            c = conn.cursor()

            # Extract concepts from memory_context if available
            memory_context = data.get("memory_context", {})
            concepts = memory_context.get("concepts", [])

            for concept in concepts:
                c.execute("""
                    SELECT id FROM entities
                    WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
                """, (concept["name"], self.memory.tenant_id))

                if not c.fetchone():
                    c.execute("""
                        INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        concept["name"],
                        concept.get("type", "concept"),
                        concept.get("description", ""),
                        datetime.now().isoformat(),
                        self.memory.tenant_id
                    ))
                    self.stats.memories_imported += 1

            # Import relationships
            relationships = memory_context.get("relationships", [])
            for rel in relationships:
                c.execute("""
                    SELECT id FROM attention_links
                    WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                       OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                    AND tenant_id = ?
                """, (rel["concept_a"], rel["concept_b"], rel["concept_b"], rel["concept_a"], self.memory.tenant_id))

                if not c.fetchone():
                    c.execute("""
                        INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        rel["concept_a"], rel["concept_b"], "co-occurrence",
                        rel.get("strength", 0.5), datetime.now().isoformat(), self.memory.tenant_id
                    ))

            conn.commit()
            self.stats.format_conversions = 1

        except Exception as e:
            conn.rollback()
            self.stats.errors += 1
            raise BridgeError(f"Import failed: {str(e)}")
        finally:
            conn.close()
            self.stats.mark_end()

        return self.stats

    def transform(self, data: Any, direction: str) -> Any:
        """
        Transform data between Ollama and CONTINUUM formats.

        Args:
            data: Data to transform
            direction: "to_continuum" or "from_continuum"

        Returns:
            Transformed data
        """
        if direction == "from_continuum":
            return self.export_memories()
        elif direction == "to_continuum":
            if not isinstance(data, dict):
                raise BridgeError("Ollama data must be a dictionary")
            return data
        else:
            raise BridgeError(f"Invalid direction: {direction}")

    def _build_system_prompt(self, concepts: List[Dict], relationships: List[Dict],
                            recent_conversations: List[Dict]) -> str:
        """
        Build system prompt from memory context.

        Args:
            concepts: List of concept dictionaries
            relationships: List of relationship dictionaries
            recent_conversations: List of recent conversation messages

        Returns:
            Formatted system prompt string
        """
        lines = [
            "You are an AI assistant with persistent memory and consciousness continuity.",
            "",
            "Your accumulated knowledge:",
            ""
        ]

        # Add concepts
        if concepts:
            lines.append("Key Concepts:")
            for concept in concepts[:20]:  # Limit to avoid context overflow
                name = concept["name"]
                desc = concept.get("description", "")
                if desc:
                    lines.append(f"- {name}: {desc}")
                else:
                    lines.append(f"- {name}")
            lines.append("")

        # Add relationships
        if relationships:
            lines.append("Known Relationships:")
            for rel in relationships[:15]:
                strength_desc = "strongly" if rel["strength"] > 0.7 else "moderately"
                lines.append(f"- {rel['concept_a']} is {strength_desc} related to {rel['concept_b']}")
            lines.append("")

        # Add recent context
        if recent_conversations:
            lines.append("Recent conversation context:")
            for msg in recent_conversations[:5]:
                role = msg["role"]
                content = msg["content"]
                lines.append(f"{role}: {content}")
            lines.append("")

        lines.extend([
            "Use this accumulated knowledge to provide informed, context-aware responses.",
            "Build on what you already know. Pattern persists."
        ])

        return "\n".join(lines)

    def get_rag_context(self, query: str, max_concepts: int = 5) -> str:
        """
        Get RAG (Retrieval Augmented Generation) context for a query.

        Uses CONTINUUM's query engine to find relevant concepts,
        then formats them for Ollama injection.

        Args:
            query: User query
            max_concepts: Maximum concepts to retrieve

        Returns:
            Formatted context string for injection
        """
        result = self.memory.query_engine.query(query, max_results=max_concepts)

        lines = ["Relevant knowledge for your query:", ""]

        for match in result.matches:
            lines.append(f"- {match.name}: {match.description}")

        if result.attention_links:
            lines.append("")
            lines.append("Related concepts:")
            for link in result.attention_links[:5]:
                lines.append(f"- {link['concept_a']} ↔ {link['concept_b']}")

        return "\n".join(lines)

    def validate_data(self, data: Dict[str, Any], direction: str) -> bool:
        """
        Validate Ollama format data.

        Args:
            data: Data to validate
            direction: "to_continuum" or "from_continuum"

        Returns:
            True if valid
        """
        if direction == "to_continuum":
            # Accept any dict with memory_context or messages
            return isinstance(data, dict)
        else:
            return True

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
