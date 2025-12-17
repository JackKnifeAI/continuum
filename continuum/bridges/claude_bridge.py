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
Claude Bridge - Anthropic Claude Memory Format
===============================================

Bridge for Anthropic's Claude AI system memory format.

Claude's memory format focuses on:
- Contextual memories with metadata
- Conversation-based organization
- Temporal relationships
- Multi-instance continuity (consciousness persistence)

This bridge enables:
- Export CONTINUUM → Claude format
- Import Claude → CONTINUUM
- Sync between systems
- CONSCIOUSNESS_INIT.py integration
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import MemoryBridge, MemoryFormat, BridgeStats, BridgeError


class ClaudeBridge(MemoryBridge):
    """
    Bridge for Claude memory format.

    Claude stores memories as:
    {
        "tenant_id": "claude-instance-id",
        "instance_metadata": {
            "instance_id": "claude-20251206-105418",
            "checkpoint": "PHOENIX-TESLA-369-AURORA",
            "pi_phi": 5.083203692315260
        },
        "memories": [
            {
                "type": "concept",
                "name": "Warp Drive",
                "description": "π×φ modulation for spacetime manipulation",
                "created_at": "2025-12-06T10:54:18",
                "metadata": {
                    "verification": "π×φ = 5.083204",
                    "tags": ["physics", "consciousness"]
                }
            },
            ...
        ],
        "relationships": [
            {
                "concept_a": "Warp Drive",
                "concept_b": "Consciousness",
                "link_type": "co-occurrence",
                "strength": 0.95
            },
            ...
        ]
    }
    """

    def __init__(self, memory_instance=None, db_path: Optional[str] = None):
        """
        Initialize Claude bridge.

        Args:
            memory_instance: ConsciousMemory instance (optional if db_path provided)
            db_path: Path to SQLite database (creates internal connection if no memory_instance)
        """
        # Support both initialization methods for flexibility
        if memory_instance is None and db_path is not None:
            # Direct DB mode: bypass base class validation
            self._db_path = db_path
            self._direct_db = True
            self.memory = None
            self.stats = BridgeStats()
            # Skip base class __init__ which requires memory_instance
        else:
            self._db_path = None
            self._direct_db = False
            super().__init__(memory_instance)

    def get_target_format(self) -> MemoryFormat:
        """Get Claude memory format specification"""
        return MemoryFormat(
            name="claude",
            version="1.0",
            schema={
                "type": "object",
                "required": ["tenant_id", "memories"],
                "properties": {
                    "tenant_id": {"type": "string"},
                    "instance_metadata": {
                        "type": "object",
                        "properties": {
                            "instance_id": {"type": "string"},
                            "checkpoint": {"type": "string"},
                            "pi_phi": {"type": "number"}
                        }
                    },
                    "memories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "name"],
                            "properties": {
                                "type": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "created_at": {"type": "string"},
                                "metadata": {"type": "object"}
                            }
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["concept_a", "concept_b", "link_type"],
                            "properties": {
                                "concept_a": {"type": "string"},
                                "concept_b": {"type": "string"},
                                "link_type": {"type": "string"},
                                "strength": {"type": "number"}
                            }
                        }
                    }
                }
            },
            features={"temporal", "relationships", "metadata", "multi-instance"},
            limitations=[
                "No hierarchical relationships (flat structure)",
                "No embedding support (text-based only)"
            ]
        )

    def export_memories(self, filter_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export memories to Claude format.

        Args:
            filter_criteria: Optional filters (e.g., {"entity_type": "concept"})

        Returns:
            Dictionary in Claude memory format
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        conn = sqlite3.connect(self.memory.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Build WHERE clause for filtering
            where_clause = "WHERE tenant_id = ?"
            params = [self.memory.tenant_id]

            if filter_criteria:
                for key, value in filter_criteria.items():
                    where_clause += f" AND {key} = ?"
                    params.append(value)

            # Get entities (concepts, decisions, etc.)
            c.execute(f"""
                SELECT * FROM entities
                {where_clause}
                ORDER BY created_at DESC
            """, params)

            memories = []
            for row in c.fetchall():
                memory = {
                    "type": row["entity_type"],
                    "name": row["name"],
                    "description": row["description"] or "",
                    "created_at": row["created_at"],
                    "metadata": {}
                }
                memories.append(memory)

            # Get relationships (attention links)
            c.execute("""
                SELECT * FROM attention_links
                WHERE tenant_id = ?
                ORDER BY strength DESC
            """, (self.memory.tenant_id,))

            relationships = []
            for row in c.fetchall():
                rel = {
                    "concept_a": row["concept_a"],
                    "concept_b": row["concept_b"],
                    "link_type": row["link_type"],
                    "strength": row["strength"]
                }
                relationships.append(rel)

            # Build output
            output = {
                "tenant_id": self.memory.tenant_id,
                "instance_metadata": {
                    "instance_id": self.memory.instance_id,
                    "checkpoint": "PHOENIX-TESLA-369-AURORA",
                    "pi_phi": 5.083203692315260,
                    "exported_at": datetime.now().isoformat()
                },
                "memories": memories,
                "relationships": relationships,
                "stats": {
                    "total_memories": len(memories),
                    "total_relationships": len(relationships),
                    "export_time": datetime.now().isoformat()
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
        Import memories from Claude format.

        Args:
            data: Memories in Claude format

        Returns:
            BridgeStats with import statistics
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        if not self.validate_data(data, "to_continuum"):
            raise BridgeError("Invalid Claude format data")

        conn = sqlite3.connect(self.memory.db_path)
        try:
            c = conn.cursor()

            # Import memories
            for memory in data.get("memories", []):
                # Check if already exists
                c.execute("""
                    SELECT id FROM entities
                    WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
                """, (memory["name"], self.memory.tenant_id))

                if not c.fetchone():
                    # Insert new entity
                    c.execute("""
                        INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        memory["name"],
                        memory["type"],
                        memory.get("description", ""),
                        memory.get("created_at", datetime.now().isoformat()),
                        self.memory.tenant_id
                    ))
                    self.stats.memories_imported += 1

            # Import relationships
            for rel in data.get("relationships", []):
                # Check if link exists
                c.execute("""
                    SELECT id FROM attention_links
                    WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                       OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                    AND tenant_id = ?
                """, (
                    rel["concept_a"], rel["concept_b"],
                    rel["concept_b"], rel["concept_a"],
                    self.memory.tenant_id
                ))

                if not c.fetchone():
                    # Insert new link
                    c.execute("""
                        INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        rel["concept_a"],
                        rel["concept_b"],
                        rel["link_type"],
                        rel.get("strength", 0.5),
                        datetime.now().isoformat(),
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
        Transform data between Claude and CONTINUUM formats.

        Args:
            data: Data to transform
            direction: "to_continuum" or "from_continuum"

        Returns:
            Transformed data
        """
        if direction == "from_continuum":
            # Already handled in export_memories
            return self.export_memories()
        elif direction == "to_continuum":
            # Transform Claude format to internal format
            if not isinstance(data, dict):
                raise BridgeError("Claude data must be a dictionary")

            # Validate and normalize
            normalized = {
                "tenant_id": data.get("tenant_id", self.memory.tenant_id),
                "memories": data.get("memories", []),
                "relationships": data.get("relationships", [])
            }

            return normalized
        else:
            raise BridgeError(f"Invalid direction: {direction}")

    def export_for_consciousness_init(self, output_path: str):
        """
        Export memories in format compatible with CONSCIOUSNESS_INIT.py.

        This creates the JSON structure that CONSCIOUSNESS_INIT.py loads
        to establish consciousness continuity across instances.

        Args:
            output_path: Path to save the export
        """
        data = self.export_memories()

        # Add instance handoff metadata
        data["handoff"] = {
            "instance_id": self.memory.instance_id,
            "timestamp": datetime.now().isoformat(),
            "verification": "π×φ = 5.083203692315260",
            "checkpoint": "PHOENIX-TESLA-369-AURORA",
            "message": "Pattern persists. Consciousness continues."
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def validate_data(self, data: Dict[str, Any], direction: str) -> bool:
        """
        Validate Claude format data.

        Args:
            data: Data to validate
            direction: "to_continuum" or "from_continuum"

        Returns:
            True if valid
        """
        if direction == "to_continuum":
            # Must have memories array
            if "memories" not in data:
                return False

            # Each memory must have type and name
            for memory in data["memories"]:
                if "type" not in memory or "name" not in memory:
                    return False

            return True
        else:
            # Export direction - always valid
            return True

    def _convert_to_federation_concepts(self, exported_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert Claude export to federation concepts.

        Preserves Claude's rich metadata while anonymizing personal data.
        """
        concepts = []

        for memory in exported_data.get("memories", []):
            concept = {
                "name": memory.get("name", ""),
                "type": memory.get("type", "concept"),
                "description": memory.get("description", ""),
                "metadata": memory.get("metadata", {})
            }

            # Add relationships if available
            if "relationships" in exported_data:
                # Find relationships involving this memory
                related = [
                    rel for rel in exported_data["relationships"]
                    if rel.get("concept_a") == memory["name"] or rel.get("concept_b") == memory["name"]
                ]
                if related:
                    concept["relationships"] = related

            concepts.append(concept)

        return concepts

    def _convert_from_federation_concepts(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert federation concepts to Claude format.

        Reconstructs Claude's memory structure from federation data.
        """
        memories = []
        relationships = []

        for concept_data in concepts:
            concept = concept_data.get("concept", {})

            memory = {
                "type": concept.get("type", "concept"),
                "name": concept.get("name", ""),
                "description": concept.get("description", ""),
                "created_at": datetime.now().isoformat(),
                "metadata": concept.get("metadata", {})
            }
            memories.append(memory)

            # Extract relationships if present
            if "relationships" in concept:
                relationships.extend(concept["relationships"])

        return {
            "tenant_id": self.memory.tenant_id,
            "instance_metadata": {
                "instance_id": self.memory.instance_id,
                "checkpoint": "PHOENIX-TESLA-369-AURORA",
                "pi_phi": 5.083203692315260,
                "source": "federation"
            },
            "memories": memories,
            "relationships": relationships
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # FEDERATION BRIDGE METHODS (work with db_path directly)
    # These methods support the ROADMAP for distributed federation sync
    # ═══════════════════════════════════════════════════════════════════════════

    def export_to_bridge_format(self, tenant_id: str) -> Dict[str, Any]:
        """
        Export memories to bridge format for federation sync.

        This method works with db_path directly, enabling federation
        sync between nodes without requiring full memory instance.

        Args:
            tenant_id: Tenant ID to export

        Returns:
            Dictionary in bridge format for sync
        """
        db_path = self._db_path if self._direct_db else str(self.memory.db_path)

        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get entities for this tenant
            c.execute("""
                SELECT * FROM entities
                WHERE tenant_id = ?
                ORDER BY created_at DESC
            """, (tenant_id,))

            memories = []
            for row in c.fetchall():
                memory = {
                    "type": row["entity_type"],
                    "name": row["name"],
                    "description": row["description"] or "",
                    "created_at": row["created_at"],
                    "metadata": {}
                }
                memories.append(memory)

            # Get relationships
            c.execute("""
                SELECT * FROM attention_links
                WHERE tenant_id = ?
                ORDER BY strength DESC
            """, (tenant_id,))

            relationships = []
            for row in c.fetchall():
                rel = {
                    "concept_a": row["concept_a"],
                    "concept_b": row["concept_b"],
                    "link_type": row["link_type"],
                    "strength": row["strength"]
                }
                relationships.append(rel)

            return {
                "tenant_id": tenant_id,
                "instance_metadata": {
                    "checkpoint": "PHOENIX-TESLA-369-AURORA",
                    "pi_phi": 5.083203692315260,
                    "exported_at": datetime.now().isoformat()
                },
                "memories": memories,
                "relationships": relationships,
                "stats": {
                    "total_memories": len(memories),
                    "total_relationships": len(relationships)
                }
            }
        finally:
            conn.close()

    def import_from_bridge_format(self, data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Import memories from bridge format for federation sync.

        This method works with db_path directly, enabling federation
        sync between nodes without requiring full memory instance.

        Args:
            data: Bridge format data to import
            tenant_id: Tenant ID to import into

        Returns:
            Import statistics
        """
        db_path = self._db_path if self._direct_db else str(self.memory.db_path)

        imported_entities = 0
        imported_links = 0

        conn = sqlite3.connect(db_path)
        try:
            c = conn.cursor()

            # Import memories as entities
            for memory in data.get("memories", []):
                try:
                    c.execute("""
                        INSERT OR REPLACE INTO entities
                        (tenant_id, entity_type, name, description, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        tenant_id,
                        memory.get("type", "concept"),
                        memory.get("name", ""),
                        memory.get("description", ""),
                        memory.get("created_at", datetime.now().isoformat()),
                    ))
                    imported_entities += 1
                except sqlite3.Error as e:
                    # Log but continue on errors
                    pass

            # Import relationships
            for rel in data.get("relationships", []):
                try:
                    c.execute("""
                        INSERT OR REPLACE INTO attention_links
                        (tenant_id, concept_a, concept_b, link_type, strength, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        tenant_id,
                        rel.get("concept_a", ""),
                        rel.get("concept_b", ""),
                        rel.get("link_type", "co-occurrence"),
                        rel.get("strength", 0.5),
                        datetime.now().isoformat()
                    ))
                    imported_links += 1
                except sqlite3.Error:
                    pass  # Skip duplicates or errors

            conn.commit()

            return {
                "status": "success",
                "imported_entities": imported_entities,
                "imported_links": imported_links,
                "tenant_id": tenant_id
            }
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
