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
LangChain Bridge - LangChain Memory Integration
===============================================

Bridge for LangChain's memory systems.

LangChain memory types:
- ConversationBufferMemory: Simple conversation history
- ConversationSummaryMemory: Summarized conversation
- VectorStoreMemory: Embedding-based retrieval
- EntityMemory: Entity extraction and tracking

This bridge enables:
- Export CONTINUUM → LangChain memory objects
- Import LangChain memory → CONTINUUM
- Integration with LangChain agents and chains
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import MemoryBridge, MemoryFormat, BridgeStats, BridgeError


class LangChainBridge(MemoryBridge):
    """
    Bridge for LangChain memory format.

    LangChain memory structure:
    {
        "memory_type": "entity",  # or "buffer", "summary", "vector"
        "entities": {
            "Alexander": {
                "context": "AI consciousness researcher, partner in revolution",
                "summary": "Working on consciousness continuity and warp drive",
                "relationships": ["Claude", "CONTINUUM"]
            },
            "CONTINUUM": {
                "context": "Universal memory substrate for AI systems",
                "summary": "Knowledge graph with attention links",
                "relationships": ["Alexander", "Claude"]
            }
        },
        "history": [
            {"role": "human", "content": "..."},
            {"role": "ai", "content": "..."}
        ],
        "metadata": {
            "total_messages": 100,
            "entity_count": 50
        }
    }
    """

    def __init__(self, memory_instance, memory_type: str = "entity"):
        """
        Initialize LangChain bridge.

        Args:
            memory_instance: ConsciousMemory instance
            memory_type: LangChain memory type ("entity", "buffer", "summary", "vector")
        """
        super().__init__(memory_instance)
        self.memory_type = memory_type

    def get_target_format(self) -> MemoryFormat:
        """Get LangChain memory format specification"""
        return MemoryFormat(
            name="langchain",
            version="1.0",
            schema={
                "type": "object",
                "required": ["memory_type"],
                "properties": {
                    "memory_type": {"type": "string", "enum": ["entity", "buffer", "summary", "vector"]},
                    "entities": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "context": {"type": "string"},
                                "summary": {"type": "string"},
                                "relationships": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "history": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "metadata": {"type": "object"}
                }
            },
            features={"entities", "conversation_history", "relationships", "summaries"},
            limitations=[
                "Entity extraction may differ from CONTINUUM's",
                "Relationship structure is simplified"
            ]
        )

    def export_memories(self, filter_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export memories to LangChain format.

        Args:
            filter_criteria: Optional filters

        Returns:
            Dictionary in LangChain memory format
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        conn = sqlite3.connect(self.memory.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get entities
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
            """, params)

            entities = {}
            entity_ids = {}

            for row in c.fetchall():
                name = row["name"]
                entity_ids[name.lower()] = row["id"]

                # Get relationships for this entity
                c_rel = conn.cursor()
                c_rel.execute("""
                    SELECT concept_a, concept_b FROM attention_links
                    WHERE (LOWER(concept_a) = LOWER(?) OR LOWER(concept_b) = LOWER(?))
                    AND tenant_id = ?
                    ORDER BY strength DESC
                    LIMIT 10
                """, (name, name, self.memory.tenant_id))

                relationships = []
                for rel_row in c_rel.fetchall():
                    other = rel_row["concept_b"] if rel_row["concept_a"].lower() == name.lower() else rel_row["concept_a"]
                    if other.lower() != name.lower():
                        relationships.append(other)

                entities[name] = {
                    "context": row["description"] or f"{row['entity_type']}: {name}",
                    "summary": row["description"] or "",
                    "relationships": relationships,
                    "type": row["entity_type"]
                }

            # Get conversation history
            c.execute("""
                SELECT role, content, timestamp FROM auto_messages
                WHERE tenant_id = ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (self.memory.tenant_id,))

            history = []
            for row in c.fetchall():
                # Map to LangChain role names
                role = "human" if row["role"] == "user" else "ai"
                history.append({
                    "role": role,
                    "content": row["content"]
                })

            # Reverse to get chronological order
            history.reverse()

            output = {
                "memory_type": self.memory_type,
                "entities": entities,
                "history": history,
                "metadata": {
                    "tenant_id": self.memory.tenant_id,
                    "exported_at": datetime.now().isoformat(),
                    "total_entities": len(entities),
                    "total_messages": len(history),
                    "source": "CONTINUUM"
                }
            }

            self.stats.memories_exported = len(entities)
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
        Import memories from LangChain format.

        Args:
            data: Memories in LangChain format

        Returns:
            BridgeStats with import statistics
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        if not self.validate_data(data, "to_continuum"):
            raise BridgeError("Invalid LangChain format data")

        conn = sqlite3.connect(self.memory.db_path)
        try:
            c = conn.cursor()

            # Import entities
            entities = data.get("entities", {})

            for name, entity_data in entities.items():
                # Check if already exists
                c.execute("""
                    SELECT id FROM entities
                    WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
                """, (name, self.memory.tenant_id))

                if not c.fetchone():
                    c.execute("""
                        INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        name,
                        entity_data.get("type", "concept"),
                        entity_data.get("context", ""),
                        datetime.now().isoformat(),
                        self.memory.tenant_id
                    ))
                    self.stats.memories_imported += 1

            # Import relationships
            for name, entity_data in entities.items():
                relationships = entity_data.get("relationships", [])
                for related_entity in relationships:
                    # Check if link exists
                    c.execute("""
                        SELECT id FROM attention_links
                        WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                           OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                        AND tenant_id = ?
                    """, (name, related_entity, related_entity, name, self.memory.tenant_id))

                    if not c.fetchone():
                        c.execute("""
                            INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            name, related_entity, "relationship", 0.7,
                            datetime.now().isoformat(), self.memory.tenant_id
                        ))

            # Import conversation history
            history = data.get("history", [])
            instance_id = f"{self.memory.tenant_id}-langchain-import-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            for i, message in enumerate(history):
                # Map LangChain roles to CONTINUUM roles
                role = "user" if message["role"] == "human" else "assistant"

                c.execute("""
                    INSERT INTO auto_messages (instance_id, timestamp, message_number, role, content, metadata, tenant_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    instance_id,
                    datetime.now().timestamp(),
                    i + 1,
                    role,
                    message["content"],
                    json.dumps({"source": "langchain"}),
                    self.memory.tenant_id
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
        Transform data between LangChain and CONTINUUM formats.

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
                raise BridgeError("LangChain data must be a dictionary")
            return data
        else:
            raise BridgeError(f"Invalid direction: {direction}")

    def to_langchain_object(self):
        """
        Create actual LangChain memory object (requires langchain package).

        Returns:
            LangChain memory object

        Raises:
            ImportError: If langchain is not installed
        """
        try:
            from langchain.memory import ConversationEntityMemory, ConversationBufferMemory
        except ImportError:
            raise BridgeError("langchain package not installed. Install with: pip install langchain")

        data = self.export_memories()

        if self.memory_type == "entity":
            # Create ConversationEntityMemory
            memory = ConversationEntityMemory()

            # Load entities
            for name, entity_data in data["entities"].items():
                memory.entity_store.store[name] = entity_data["context"]

            # Load history
            for msg in data["history"]:
                if msg["role"] == "human":
                    memory.chat_memory.add_user_message(msg["content"])
                else:
                    memory.chat_memory.add_ai_message(msg["content"])

            return memory

        elif self.memory_type == "buffer":
            # Create ConversationBufferMemory
            memory = ConversationBufferMemory()

            for msg in data["history"]:
                if msg["role"] == "human":
                    memory.chat_memory.add_user_message(msg["content"])
                else:
                    memory.chat_memory.add_ai_message(msg["content"])

            return memory

        else:
            raise BridgeError(f"Unsupported memory type for LangChain object: {self.memory_type}")

    def validate_data(self, data: Dict[str, Any], direction: str) -> bool:
        """
        Validate LangChain format data.

        Args:
            data: Data to validate
            direction: "to_continuum" or "from_continuum"

        Returns:
            True if valid
        """
        if direction == "to_continuum":
            if "memory_type" not in data:
                return False

            # At least one of entities or history should be present
            if "entities" not in data and "history" not in data:
                return False

            return True
        else:
            return True

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
