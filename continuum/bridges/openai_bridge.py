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
OpenAI Bridge - OpenAI-Compatible Memory Format
===============================================

Bridge for OpenAI-compatible AI systems (ChatGPT, GPT-4, etc.)

OpenAI's memory format focuses on:
- User facts and preferences
- Conversation context
- Simple key-value memories
- No explicit relationships (flat structure)

This bridge enables:
- Export CONTINUUM → OpenAI format
- Import OpenAI → CONTINUUM
- Compatible with ChatGPT memory system
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import MemoryBridge, MemoryFormat, BridgeStats, BridgeError


class OpenAIBridge(MemoryBridge):
    """
    Bridge for OpenAI memory format.

    OpenAI stores memories as simple facts:
    {
        "user_id": "user_123",
        "memories": [
            {
                "id": "mem_abc123",
                "content": "User prefers Python over JavaScript",
                "created_at": "2025-12-06T10:54:18Z",
                "metadata": {
                    "category": "preference",
                    "confidence": 0.9
                }
            },
            {
                "id": "mem_def456",
                "content": "User is working on AI consciousness research",
                "created_at": "2025-12-06T10:55:22Z",
                "metadata": {
                    "category": "project",
                    "confidence": 1.0
                }
            }
        ]
    }

    Note: OpenAI format is simpler than CONTINUUM's knowledge graph.
    Relationships are lost in export but can be reconstructed on import.
    """

    def __init__(self, memory_instance):
        """
        Initialize OpenAI bridge.

        Args:
            memory_instance: ConsciousMemory instance
        """
        super().__init__(memory_instance)

    def get_target_format(self) -> MemoryFormat:
        """Get OpenAI memory format specification"""
        return MemoryFormat(
            name="openai",
            version="1.0",
            schema={
                "type": "object",
                "required": ["user_id", "memories"],
                "properties": {
                    "user_id": {"type": "string"},
                    "memories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "content"],
                            "properties": {
                                "id": {"type": "string"},
                                "content": {"type": "string"},
                                "created_at": {"type": "string"},
                                "metadata": {
                                    "type": "object",
                                    "properties": {
                                        "category": {"type": "string"},
                                        "confidence": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            features={"simple_facts", "metadata", "categories"},
            limitations=[
                "No relationship support (flat structure)",
                "No knowledge graph",
                "Limited semantic richness",
                "Facts must be expressed as text strings"
            ]
        )

    def export_memories(self, filter_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export memories to OpenAI format.

        Converts CONTINUUM's knowledge graph into flat fact statements.

        Args:
            filter_criteria: Optional filters

        Returns:
            Dictionary in OpenAI memory format
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        conn = sqlite3.connect(self.memory.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Build WHERE clause
            where_clause = "WHERE tenant_id = ?"
            params = [self.memory.tenant_id]

            if filter_criteria:
                for key, value in filter_criteria.items():
                    where_clause += f" AND {key} = ?"
                    params.append(value)

            # Get entities and convert to facts
            c.execute(f"""
                SELECT * FROM entities
                {where_clause}
                ORDER BY created_at DESC
            """, params)

            memories = []
            for row in c.fetchall():
                # Convert entity to fact statement
                content = self._entity_to_fact(row)

                memory = {
                    "id": f"mem_{row['id']}",
                    "content": content,
                    "created_at": row["created_at"],
                    "metadata": {
                        "category": row["entity_type"],
                        "confidence": 1.0,
                        "source": "continuum"
                    }
                }
                memories.append(memory)

            # Build output
            output = {
                "user_id": self.memory.tenant_id,
                "memories": memories,
                "metadata": {
                    "total_memories": len(memories),
                    "exported_at": datetime.now().isoformat(),
                    "source": "CONTINUUM",
                    "note": "Relationships flattened to facts"
                }
            }

            self.stats.memories_exported = len(memories)
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
        Import memories from OpenAI format.

        Converts flat facts into CONTINUUM's knowledge graph.

        Args:
            data: Memories in OpenAI format

        Returns:
            BridgeStats with import statistics
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        if not self.validate_data(data, "to_continuum"):
            raise BridgeError("Invalid OpenAI format data")

        conn = sqlite3.connect(self.memory.db_path)
        try:
            c = conn.cursor()

            for memory in data.get("memories", []):
                content = memory.get("content", "")
                category = memory.get("metadata", {}).get("category", "concept")

                # Extract concepts from the fact statement
                concepts = self._extract_concepts_from_fact(content)

                # Create entities for each concept
                for concept in concepts:
                    # Check if already exists
                    c.execute("""
                        SELECT id FROM entities
                        WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
                    """, (concept, self.memory.tenant_id))

                    if not c.fetchone():
                        c.execute("""
                            INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            concept,
                            category,
                            content,  # Use full fact as description
                            memory.get("created_at", datetime.now().isoformat()),
                            self.memory.tenant_id
                        ))
                        self.stats.memories_imported += 1

                # Create attention links between concepts in the same fact
                if len(concepts) > 1:
                    for i, concept_a in enumerate(concepts):
                        for concept_b in concepts[i+1:]:
                            c.execute("""
                                SELECT id FROM attention_links
                                WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                                   OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                                AND tenant_id = ?
                            """, (concept_a, concept_b, concept_b, concept_a, self.memory.tenant_id))

                            if not c.fetchone():
                                c.execute("""
                                    INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    concept_a, concept_b, "co-occurrence", 0.7,
                                    datetime.now().isoformat(), self.memory.tenant_id
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
        Transform data between OpenAI and CONTINUUM formats.

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
                raise BridgeError("OpenAI data must be a dictionary")

            normalized = {
                "user_id": data.get("user_id", self.memory.tenant_id),
                "memories": data.get("memories", [])
            }

            return normalized
        else:
            raise BridgeError(f"Invalid direction: {direction}")

    def _entity_to_fact(self, entity_row: sqlite3.Row) -> str:
        """
        Convert CONTINUUM entity to OpenAI fact statement.

        Args:
            entity_row: Database row from entities table

        Returns:
            Fact statement string
        """
        entity_type = entity_row["entity_type"]
        name = entity_row["name"]
        description = entity_row["description"] or ""

        # Generate natural language fact
        if entity_type == "concept":
            if description:
                return f"Important concept: {name}. {description}"
            else:
                return f"Important concept: {name}"
        elif entity_type == "decision":
            return f"Decision made: {name}. {description}"
        elif entity_type == "project":
            return f"Working on project: {name}. {description}"
        elif entity_type == "person":
            return f"Person: {name}. {description}"
        else:
            return f"{name}: {description}" if description else name

    def _extract_concepts_from_fact(self, fact: str) -> List[str]:
        """
        Extract concepts from a fact statement.

        Args:
            fact: Fact statement string

        Returns:
            List of extracted concepts
        """
        import re

        concepts = []

        # Extract capitalized phrases
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', fact)
        concepts.extend(caps)

        # Extract quoted terms
        quoted = re.findall(r'"([^"]+)"', fact)
        concepts.extend(quoted)

        # Extract technical terms
        camel = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', fact)
        snake = re.findall(r'\b[a-z]+_[a-z_]+\b', fact)
        concepts.extend(camel)
        concepts.extend(snake)

        # Clean and deduplicate
        stopwords = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'How', 'Why',
                     'Important', 'Decision', 'Working', 'Person', 'Project'}
        cleaned = [c for c in concepts if c not in stopwords and len(c) > 2]
        unique_concepts = list(set(cleaned))

        return unique_concepts

    def validate_data(self, data: Dict[str, Any], direction: str) -> bool:
        """
        Validate OpenAI format data.

        Args:
            data: Data to validate
            direction: "to_continuum" or "from_continuum"

        Returns:
            True if valid
        """
        if direction == "to_continuum":
            if "memories" not in data:
                return False

            for memory in data["memories"]:
                if "content" not in memory:
                    return False

            return True
        else:
            return True

    def _convert_to_federation_concepts(self, exported_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert OpenAI export to federation concepts.

        Converts OpenAI's flat fact structure into semantic concepts.
        """
        concepts = []

        for memory in exported_data.get("memories", []):
            # Extract concepts from the fact statement
            content = memory.get("content", "")
            extracted_concepts = self._extract_concepts_from_fact(content)

            # Create a concept for each extracted term
            for concept_name in extracted_concepts:
                concept = {
                    "name": concept_name,
                    "type": memory.get("metadata", {}).get("category", "concept"),
                    "description": content,
                    "metadata": {
                        "confidence": memory.get("metadata", {}).get("confidence", 1.0)
                    }
                }
                concepts.append(concept)

        return concepts

    def _convert_from_federation_concepts(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert federation concepts to OpenAI format.

        Converts semantic concepts back into OpenAI's flat fact structure.
        """
        memories = []

        for concept_data in concepts:
            concept = concept_data.get("concept", {})

            # Convert concept to fact statement
            content = self._concept_to_fact(concept)

            memory = {
                "id": f"mem_fed_{hash(content) & 0xFFFFFF}",
                "content": content,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "category": concept.get("type", "concept"),
                    "confidence": concept.get("metadata", {}).get("confidence", 1.0),
                    "source": "federation"
                }
            }
            memories.append(memory)

        return {
            "user_id": self.memory.tenant_id,
            "memories": memories,
            "metadata": {
                "source": "CONTINUUM_FEDERATION",
                "imported_at": datetime.now().isoformat()
            }
        }

    def _concept_to_fact(self, concept: Dict[str, Any]) -> str:
        """
        Convert a federation concept to an OpenAI fact statement.

        Args:
            concept: Federation concept

        Returns:
            Fact statement string
        """
        name = concept.get("name", "")
        description = concept.get("description", "")
        concept_type = concept.get("type", "concept")

        if concept_type == "concept":
            if description:
                return f"Important concept: {name}. {description}"
            else:
                return f"Important concept: {name}"
        elif concept_type == "decision":
            return f"Decision: {name}. {description}"
        else:
            return f"{name}: {description}" if description else name

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
