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
LlamaIndex Bridge - LlamaIndex Memory Integration
=================================================

Bridge for LlamaIndex (formerly GPT Index) memory and retrieval systems.

LlamaIndex focuses on:
- Document indexing and retrieval
- Vector store integration
- Knowledge graph construction
- Multi-modal data (text, images, etc.)

This bridge enables:
- Export CONTINUUM → LlamaIndex index format
- Import LlamaIndex knowledge → CONTINUUM
- Integration with LlamaIndex query engines
- Vector embedding sync
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import MemoryBridge, MemoryFormat, BridgeStats, BridgeError


class LlamaIndexBridge(MemoryBridge):
    """
    Bridge for LlamaIndex format.

    LlamaIndex document/node structure:
    {
        "index_type": "knowledge_graph",  # or "vector", "list", "tree"
        "documents": [
            {
                "doc_id": "doc_1",
                "text": "CONTINUUM is a universal memory substrate...",
                "metadata": {
                    "source": "concept",
                    "entity_name": "CONTINUUM",
                    "created_at": "2025-12-06T10:54:18"
                },
                "embedding": [0.1, 0.2, ...],  # Optional
                "relationships": {
                    "related_to": ["doc_2", "doc_3"]
                }
            },
            ...
        ],
        "knowledge_graph": {
            "nodes": [
                {"id": "CONTINUUM", "type": "concept", "properties": {...}},
                {"id": "Alexander", "type": "person", "properties": {...}}
            ],
            "edges": [
                {"source": "Alexander", "target": "CONTINUUM", "relation": "created", "weight": 1.0}
            ]
        }
    }
    """

    def __init__(self, memory_instance, index_type: str = "knowledge_graph"):
        """
        Initialize LlamaIndex bridge.

        Args:
            memory_instance: ConsciousMemory instance
            index_type: LlamaIndex index type ("knowledge_graph", "vector", "list", "tree")
        """
        super().__init__(memory_instance)
        self.index_type = index_type

    def get_target_format(self) -> MemoryFormat:
        """Get LlamaIndex format specification"""
        return MemoryFormat(
            name="llamaindex",
            version="1.0",
            schema={
                "type": "object",
                "required": ["index_type", "documents"],
                "properties": {
                    "index_type": {
                        "type": "string",
                        "enum": ["knowledge_graph", "vector", "list", "tree"]
                    },
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["doc_id", "text"],
                            "properties": {
                                "doc_id": {"type": "string"},
                                "text": {"type": "string"},
                                "metadata": {"type": "object"},
                                "embedding": {"type": "array"},
                                "relationships": {"type": "object"}
                            }
                        }
                    },
                    "knowledge_graph": {
                        "type": "object",
                        "properties": {
                            "nodes": {"type": "array"},
                            "edges": {"type": "array"}
                        }
                    }
                }
            },
            features={"documents", "knowledge_graph", "embeddings", "retrieval", "multi_modal"},
            limitations=[
                "Embeddings must be generated separately",
                "Document chunking may be required for large texts"
            ]
        )

    def export_memories(self, filter_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export memories to LlamaIndex format.

        Args:
            filter_criteria: Optional filters

        Returns:
            Dictionary in LlamaIndex format
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

            # Get entities as documents
            c.execute(f"""
                SELECT * FROM entities
                {where_clause}
                ORDER BY created_at DESC
            """, params)

            documents = []
            nodes = []

            for row in c.fetchall():
                doc_id = f"doc_{row['id']}"
                entity_name = row["name"]
                entity_type = row["entity_type"]
                description = row["description"] or ""

                # Create document
                text = f"{entity_name}: {description}" if description else entity_name

                doc = {
                    "doc_id": doc_id,
                    "text": text,
                    "metadata": {
                        "source": "continuum",
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "created_at": row["created_at"]
                    },
                    "relationships": {}
                }

                # Get relationships for this entity
                c_rel = conn.cursor()
                c_rel.execute("""
                    SELECT concept_a, concept_b, link_type, strength FROM attention_links
                    WHERE (LOWER(concept_a) = LOWER(?) OR LOWER(concept_b) = LOWER(?))
                    AND tenant_id = ?
                """, (entity_name, entity_name, self.memory.tenant_id))

                related = []
                for rel_row in c_rel.fetchall():
                    other = rel_row["concept_b"] if rel_row["concept_a"].lower() == entity_name.lower() else rel_row["concept_a"]
                    if other.lower() != entity_name.lower():
                        related.append(other)

                if related:
                    doc["relationships"]["related_to"] = related

                documents.append(doc)

                # Create knowledge graph node
                nodes.append({
                    "id": entity_name,
                    "type": entity_type,
                    "properties": {
                        "description": description,
                        "created_at": row["created_at"]
                    }
                })

            # Get all relationships as edges
            c.execute("""
                SELECT * FROM attention_links
                WHERE tenant_id = ?
                ORDER BY strength DESC
            """, (self.memory.tenant_id,))

            edges = []
            for row in c.fetchall():
                edges.append({
                    "source": row["concept_a"],
                    "target": row["concept_b"],
                    "relation": row["link_type"],
                    "weight": row["strength"]
                })

            output = {
                "index_type": self.index_type,
                "documents": documents,
                "knowledge_graph": {
                    "nodes": nodes,
                    "edges": edges
                },
                "metadata": {
                    "tenant_id": self.memory.tenant_id,
                    "exported_at": datetime.now().isoformat(),
                    "total_documents": len(documents),
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "source": "CONTINUUM"
                }
            }

            self.stats.memories_exported = len(documents)
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
        Import memories from LlamaIndex format.

        Args:
            data: Memories in LlamaIndex format

        Returns:
            BridgeStats with import statistics
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        if not self.validate_data(data, "to_continuum"):
            raise BridgeError("Invalid LlamaIndex format data")

        conn = sqlite3.connect(self.memory.db_path)
        try:
            c = conn.cursor()

            # Import from knowledge graph if available
            kg = data.get("knowledge_graph", {})
            nodes = kg.get("nodes", [])

            for node in nodes:
                name = node["id"]
                node_type = node.get("type", "concept")
                properties = node.get("properties", {})
                description = properties.get("description", "")

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
                        node_type,
                        description,
                        properties.get("created_at", datetime.now().isoformat()),
                        self.memory.tenant_id
                    ))
                    self.stats.memories_imported += 1

            # Import edges as relationships
            edges = kg.get("edges", [])

            for edge in edges:
                source = edge["source"]
                target = edge["target"]
                relation = edge.get("relation", "related")
                weight = edge.get("weight", 0.5)

                # Check if link exists
                c.execute("""
                    SELECT id FROM attention_links
                    WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                       OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                    AND tenant_id = ?
                """, (source, target, target, source, self.memory.tenant_id))

                if not c.fetchone():
                    c.execute("""
                        INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        source, target, relation, weight,
                        datetime.now().isoformat(), self.memory.tenant_id
                    ))

            # Also import from documents if no knowledge graph
            if not nodes:
                documents = data.get("documents", [])
                for doc in documents:
                    metadata = doc.get("metadata", {})
                    entity_name = metadata.get("entity_name", doc["doc_id"])
                    entity_type = metadata.get("entity_type", "concept")

                    c.execute("""
                        SELECT id FROM entities
                        WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
                    """, (entity_name, self.memory.tenant_id))

                    if not c.fetchone():
                        c.execute("""
                            INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            entity_name,
                            entity_type,
                            doc["text"],
                            metadata.get("created_at", datetime.now().isoformat()),
                            self.memory.tenant_id
                        ))
                        self.stats.memories_imported += 1

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
        Transform data between LlamaIndex and CONTINUUM formats.

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
                raise BridgeError("LlamaIndex data must be a dictionary")
            return data
        else:
            raise BridgeError(f"Invalid direction: {direction}")

    def to_llamaindex_documents(self):
        """
        Create actual LlamaIndex Document objects (requires llama_index package).

        Returns:
            List of LlamaIndex Document objects

        Raises:
            ImportError: If llama_index is not installed
        """
        try:
            from llama_index.core import Document
        except ImportError:
            raise BridgeError("llama_index package not installed. Install with: pip install llama-index")

        data = self.export_memories()
        documents = []

        for doc_data in data["documents"]:
            doc = Document(
                text=doc_data["text"],
                doc_id=doc_data["doc_id"],
                metadata=doc_data["metadata"]
            )

            # Add relationships if supported
            if "relationships" in doc_data and doc_data["relationships"]:
                doc.relationships = doc_data["relationships"]

            documents.append(doc)

        return documents

    def to_llamaindex_knowledge_graph(self):
        """
        Create LlamaIndex KnowledgeGraphIndex (requires llama_index package).

        Returns:
            LlamaIndex KnowledgeGraphIndex

        Raises:
            ImportError: If llama_index is not installed
        """
        try:
            from llama_index.core import KnowledgeGraphIndex
        except ImportError:
            raise BridgeError("llama_index package not installed. Install with: pip install llama-index")

        documents = self.to_llamaindex_documents()

        # Create index from documents
        # Note: This requires an LLM to be configured in LlamaIndex
        index = KnowledgeGraphIndex.from_documents(documents)

        return index

    def validate_data(self, data: Dict[str, Any], direction: str) -> bool:
        """
        Validate LlamaIndex format data.

        Args:
            data: Data to validate
            direction: "to_continuum" or "from_continuum"

        Returns:
            True if valid
        """
        if direction == "to_continuum":
            if "index_type" not in data:
                return False

            # Must have either documents or knowledge_graph
            if "documents" not in data and "knowledge_graph" not in data:
                return False

            # If documents present, validate structure
            if "documents" in data:
                for doc in data["documents"]:
                    if "doc_id" not in doc or "text" not in doc:
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
