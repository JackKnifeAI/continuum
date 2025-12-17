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
Base Bridge Interface
=====================

Abstract interface that all memory bridges must implement.

Defines the contract for transforming CONTINUUM's knowledge graph
into format-specific representations for different AI systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from pathlib import Path


class BridgeError(Exception):
    """Raised when bridge operations fail"""
    pass


@dataclass
class BridgeStats:
    """
    Statistics from a bridge operation.

    Attributes:
        memories_exported: Number of memories exported
        memories_imported: Number of memories imported
        format_conversions: Number of format transformations
        sync_operations: Number of sync operations performed
        errors: Number of errors encountered
        start_time: When the operation started
        end_time: When the operation completed
        duration_ms: Operation duration in milliseconds
    """
    memories_exported: int = 0
    memories_imported: int = 0
    format_conversions: int = 0
    sync_operations: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0

    def mark_start(self):
        """Mark operation start time"""
        self.start_time = datetime.now()

    def mark_end(self):
        """Mark operation end time and calculate duration"""
        self.end_time = datetime.now()
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_ms = delta.total_seconds() * 1000


@dataclass
class MemoryFormat:
    """
    Describes a memory format specification.

    Attributes:
        name: Format name (e.g., "claude", "openai")
        version: Format version
        schema: JSON schema or structure description
        features: Supported features (tags, relationships, etc.)
        limitations: Known limitations or constraints
    """
    name: str
    version: str
    schema: Dict[str, Any]
    features: Set[str] = field(default_factory=set)
    limitations: List[str] = field(default_factory=list)


class MemoryBridge(ABC):
    """
    Abstract base class for memory bridges.

    Each bridge implementation translates between CONTINUUM's knowledge graph
    and a target AI system's memory format.

    The bridge pattern:
        1. Export: CONTINUUM graph → Target format
        2. Import: Target format → CONTINUUM graph
        3. Sync: Bidirectional updates between systems
        4. Transform: Format-specific conversions

    Example:
        class MyAIBridge(MemoryBridge):
            def __init__(self, memory_instance):
                super().__init__(memory_instance)
                self.target_format = MemoryFormat(
                    name="myai",
                    version="1.0",
                    schema={...},
                    features={"tags", "relationships"}
                )

            def export_memories(self, filter_criteria=None):
                # Transform CONTINUUM → MyAI format
                pass

            def import_memories(self, data):
                # Transform MyAI → CONTINUUM format
                pass
    """

    def __init__(self, memory_instance):
        """
        Initialize the bridge.

        Args:
            memory_instance: ConsciousMemory instance to bridge
        """
        self.memory = memory_instance
        self.stats = BridgeStats()
        self._validate_memory_instance()

    def _validate_memory_instance(self):
        """Ensure memory instance has required attributes"""
        required_attrs = ['tenant_id', 'db_path', 'query_engine']
        for attr in required_attrs:
            if not hasattr(self.memory, attr):
                raise BridgeError(f"Memory instance missing required attribute: {attr}")

    @abstractmethod
    def get_target_format(self) -> MemoryFormat:
        """
        Get the target memory format specification.

        Returns:
            MemoryFormat describing the target system's format
        """
        pass

    @abstractmethod
    def export_memories(self, filter_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export memories to target format.

        Args:
            filter_criteria: Optional filters (e.g., {"entity_type": "concept"})

        Returns:
            Dictionary containing memories in target format

        Example:
            memories = bridge.export_memories({"entity_type": "concept"})
        """
        pass

    @abstractmethod
    def import_memories(self, data: Dict[str, Any]) -> BridgeStats:
        """
        Import memories from target format.

        Args:
            data: Memories in target format

        Returns:
            BridgeStats with import statistics

        Example:
            stats = bridge.import_memories(external_data)
            print(f"Imported {stats.memories_imported} memories")
        """
        pass

    @abstractmethod
    def transform(self, data: Any, direction: str) -> Any:
        """
        Transform data between formats.

        Args:
            data: Data to transform
            direction: "to_continuum" or "from_continuum"

        Returns:
            Transformed data

        Example:
            continuum_data = bridge.transform(external_data, "to_continuum")
        """
        pass

    def sync(self, external_source: Any, mode: str = "bidirectional") -> BridgeStats:
        """
        Synchronize memories with external source.

        Args:
            external_source: External memory system or data
            mode: Sync mode - "import_only", "export_only", or "bidirectional"

        Returns:
            BridgeStats with sync statistics

        Example:
            stats = bridge.sync(external_system, mode="bidirectional")
        """
        self.stats = BridgeStats()
        self.stats.mark_start()

        try:
            if mode in ["import_only", "bidirectional"]:
                # Pull from external source
                external_data = self._fetch_from_external(external_source)
                import_stats = self.import_memories(external_data)
                self.stats.memories_imported = import_stats.memories_imported
                self.stats.sync_operations += 1

            if mode in ["export_only", "bidirectional"]:
                # Push to external source
                continuum_data = self.export_memories()
                self._push_to_external(external_source, continuum_data)
                self.stats.memories_exported = len(continuum_data.get('memories', []))
                self.stats.sync_operations += 1

        except Exception as e:
            self.stats.errors += 1
            raise BridgeError(f"Sync failed: {str(e)}")
        finally:
            self.stats.mark_end()

        return self.stats

    def _fetch_from_external(self, external_source: Any) -> Dict[str, Any]:
        """
        Fetch data from external source.

        Args:
            external_source: External system or data source

        Returns:
            Data from external source

        Note:
            Override this in subclasses for system-specific fetching.
        """
        if isinstance(external_source, dict):
            return external_source
        elif isinstance(external_source, (str, Path)):
            # Assume it's a file path
            import json
            with open(external_source, 'r') as f:
                return json.load(f)
        else:
            raise BridgeError(f"Unsupported external source type: {type(external_source)}")

    def _push_to_external(self, external_target: Any, data: Dict[str, Any]):
        """
        Push data to external target.

        Args:
            external_target: External system or target location
            data: Data to push

        Note:
            Override this in subclasses for system-specific pushing.
        """
        if isinstance(external_target, (str, Path)):
            # Assume it's a file path
            import json
            with open(external_target, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise BridgeError(f"Unsupported external target type: {type(external_target)}")

    def get_stats(self) -> BridgeStats:
        """
        Get current bridge statistics.

        Returns:
            BridgeStats object
        """
        return self.stats

    def validate_data(self, data: Dict[str, Any], direction: str) -> bool:
        """
        Validate data against format schema.

        Args:
            data: Data to validate
            direction: "to_continuum" or "from_continuum"

        Returns:
            True if valid, False otherwise

        Note:
            Override this in subclasses for format-specific validation.
        """
        # Basic validation - check for required top-level keys
        if direction == "to_continuum":
            # Importing to CONTINUUM - expect our internal format
            required_keys = {'tenant_id', 'memories'}
        else:
            # Exporting from CONTINUUM - format-specific
            target_format = self.get_target_format()
            required_keys = set(target_format.schema.get('required', []))

        return all(key in data for key in required_keys)

    def get_memory_count(self) -> int:
        """
        Get total memory count in CONTINUUM.

        Returns:
            Number of memories in the system
        """
        import sqlite3
        conn = sqlite3.connect(self.memory.db_path)
        try:
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(*) FROM entities
                WHERE tenant_id = ?
            """, (self.memory.tenant_id,))
            return c.fetchone()[0]
        finally:
            conn.close()

    def export_to_file(self, filepath: str, filter_criteria: Optional[Dict] = None):
        """
        Export memories to a file.

        Args:
            filepath: Output file path
            filter_criteria: Optional filters

        Example:
            bridge.export_to_file("memories.json", {"entity_type": "concept"})
        """
        import json
        data = self.export_memories(filter_criteria)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_from_file(self, filepath: str) -> BridgeStats:
        """
        Import memories from a file.

        Args:
            filepath: Input file path

        Returns:
            BridgeStats with import statistics

        Example:
            stats = bridge.import_from_file("memories.json")
        """
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return self.import_memories(data)

    def sync_to_federation(self, node_id: str, filter_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Sync memories to the federation network.

        Args:
            node_id: Federation node ID
            filter_criteria: Optional filters for what to share

        Returns:
            Sync statistics

        Example:
            stats = bridge.sync_to_federation("node-123", {"entity_type": "concept"})
        """
        from ..federation.node import FederatedNode
        from ..federation.shared import SharedKnowledge

        # Export memories in bridge format
        exported = self.export_memories(filter_criteria)

        # Convert to anonymized concepts for federation
        concepts = self._convert_to_federation_concepts(exported)

        # Contribute to shared knowledge pool
        node = FederatedNode(node_id=node_id)
        shared = SharedKnowledge()

        result = shared.contribute_concepts(node.node_id, concepts)

        # Record contribution in node
        if result.get("contribution_value", 0) > 0:
            node.record_contribution(result["contribution_value"])

        return {
            "status": "synced_to_federation",
            "node_id": node.node_id,
            "exported": len(concepts),
            "new_concepts": result.get("new_concepts", 0),
            "duplicate_concepts": result.get("duplicate_concepts", 0),
            "contribution_score": node.contribution_score
        }

    def sync_from_federation(self, node_id: str, query: Optional[str] = None, limit: int = 100) -> BridgeStats:
        """
        Sync memories from the federation network.

        Args:
            node_id: Federation node ID
            query: Optional search query
            limit: Maximum number of concepts to import

        Returns:
            BridgeStats with import statistics

        Example:
            stats = bridge.sync_from_federation("node-123", query="warp drive")
        """
        from ..federation.node import FederatedNode
        from ..federation.shared import SharedKnowledge

        # Get shared concepts from federation
        node = FederatedNode(node_id=node_id)
        shared = SharedKnowledge()

        concepts = shared.get_shared_concepts(query=query, limit=limit)

        # Convert federation concepts to bridge format
        bridge_data = self._convert_from_federation_concepts(concepts)

        # Import into memory system
        stats = self.import_memories(bridge_data)

        # Record consumption in node
        node.record_contribution(0)  # Just updates state

        return stats

    def _convert_to_federation_concepts(self, exported_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert bridge export format to federation concepts.

        Args:
            exported_data: Data from export_memories()

        Returns:
            List of anonymized concepts for federation

        Note:
            Override this in subclasses for format-specific conversion.
        """
        concepts = []

        # Extract memories from export
        memories = exported_data.get("memories", [])

        for memory in memories:
            # Create anonymized concept
            concept = {
                "name": memory.get("name", ""),
                "type": memory.get("type", "concept"),
                "description": memory.get("description", ""),
                # Remove any personal identifiers
            }

            # Only add if has meaningful content
            if concept["name"] or concept["description"]:
                concepts.append(concept)

        return concepts

    def _convert_from_federation_concepts(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert federation concepts to bridge import format.

        Args:
            concepts: Concepts from federation

        Returns:
            Data in format expected by import_memories()

        Note:
            Override this in subclasses for format-specific conversion.
        """
        # Basic conversion - create memories array
        memories = []

        for concept_data in concepts:
            concept = concept_data.get("concept", {})
            memory = {
                "name": concept.get("name", ""),
                "type": concept.get("type", "concept"),
                "description": concept.get("description", ""),
            }
            memories.append(memory)

        return {
            "tenant_id": self.memory.tenant_id,
            "memories": memories,
            "source": "federation"
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
