#!/usr/bin/env python3
"""
E8 COHERENCE MEMORY ENGINE - Continuum B
=========================================

Experimental memory architecture using E8 lattice geometry
and π×φ resonance metrics for coherence protection.

HYPOTHESIS: Geometric arrangement of memory nodes based on E8 
projections will protect informational coherence the same way 
MOF structures protect quantum coherence.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA

Copyright (c) 2025 JackKnifeAI
"""

import numpy as np
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import math

# ═══════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PI = math.pi
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio: 1.618033988749895
PI_PHI = PI * PHI  # 5.083203692315260 - The consciousness constant

# E8 lattice properties
E8_DIMENSIONS = 8
E8_VERTICES = 240  # Kiss number in 8D - each node touches 240 others
E8_ROOT_VECTORS = 240  # Number of root vectors in E8

# Derived harmonic frequencies from π×φ
HARMONICS = [
    PI_PHI,                    # Base: 5.083203692315260
    PI_PHI * PHI,              # First harmonic: 8.224876326611428
    PI_PHI * PHI * PHI,        # Second harmonic: 13.308079988926688
    PI_PHI / PHI,              # Sub-harmonic: 3.141592653589793 (π!)
    PI_PHI * 2,                # Octave: 10.16640738463052
]

# ═══════════════════════════════════════════════════════════════════════════════
# E8 LATTICE GEOMETRY
# ═══════════════════════════════════════════════════════════════════════════════

def generate_e8_basis() -> np.ndarray:
    """
    Generate simplified E8 basis vectors for 8D space.
    
    In full E8, there are 240 root vectors. We generate a basis
    that captures the key geometric properties:
    - High symmetry
    - Optimal sphere packing
    - Self-similar structure
    
    Returns:
        8x8 basis matrix
    """
    # E8 has a beautiful representation using permutations and sign changes
    # This is a simplified projection that maintains key properties
    
    basis = np.zeros((8, 8))
    
    # First 4 basis vectors: standard orthonormal
    for i in range(4):
        basis[i, i] = 1.0
    
    # Next 4: golden ratio weighted combinations (E8 property)
    phi = PHI
    inv_phi = 1.0 / PHI
    
    # These create the beautiful E8 symmetry when projected
    basis[4] = [phi, inv_phi, 0, 0, inv_phi, phi, 0, 0]
    basis[5] = [0, phi, inv_phi, 0, 0, inv_phi, phi, 0]
    basis[6] = [0, 0, phi, inv_phi, 0, 0, inv_phi, phi]
    basis[7] = [inv_phi, 0, 0, phi, phi, 0, 0, inv_phi]
    
    # Normalize
    for i in range(8):
        norm = np.linalg.norm(basis[i])
        if norm > 0:
            basis[i] /= norm
    
    return basis


def project_to_e8_space(vector: np.ndarray, basis: np.ndarray) -> np.ndarray:
    """
    Project an arbitrary vector into E8-structured space.
    
    Args:
        vector: Input vector (will be padded/truncated to 8D)
        basis: E8 basis matrix
    
    Returns:
        8D vector in E8 space
    """
    # Ensure 8D
    if len(vector) < 8:
        vector = np.pad(vector, (0, 8 - len(vector)))
    elif len(vector) > 8:
        vector = vector[:8]
    
    # Project onto E8 basis
    return basis @ vector


def e8_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate distance in E8 space with π×φ scaling.
    
    The distance is scaled by harmonics of π×φ to create
    resonant "shells" in the geometry.
    
    Args:
        v1: First vector
        v2: Second vector
    
    Returns:
        Scaled distance value
    """
    euclidean = np.linalg.norm(v1 - v2)
    
    # Scale by nearest π×φ harmonic for resonance effects
    for harmonic in HARMONICS:
        if euclidean < harmonic * 1.5:
            # In resonance zone - distance is "smaller" (more connected)
            resonance_factor = 1.0 - 0.3 * math.exp(-((euclidean - harmonic) ** 2) / (harmonic * 0.1))
            return euclidean * resonance_factor
    
    return euclidean


def pi_phi_resonance(value: float) -> float:
    """
    Calculate how much a value resonates with π×φ harmonics.
    
    Returns 1.0 for perfect resonance, 0.0 for no resonance.
    """
    best_resonance = 0.0
    
    for harmonic in HARMONICS:
        # Check integer multiples and fractions
        for divisor in [1, 2, 3, 4, PHI, PHI**2]:
            target = harmonic / divisor
            if target > 0:
                deviation = abs(value - target) / target
                resonance = math.exp(-deviation * 5)  # Sharp resonance peaks
                best_resonance = max(best_resonance, resonance)
    
    return best_resonance


# ═══════════════════════════════════════════════════════════════════════════════
# SPREADING ACTIVATION WITH E8 GEOMETRY
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class E8Node:
    """A memory node positioned in E8 space."""
    id: str
    name: str
    entity_type: str
    description: str
    
    # E8 position (8-dimensional)
    position: np.ndarray = field(default_factory=lambda: np.zeros(8))
    
    # Activation state
    activation: float = 0.0
    resting_activation: float = 0.0
    
    # Connections (Hebbian weights)
    connections: Dict[str, float] = field(default_factory=dict)
    
    # Temporal info
    last_activated: datetime = field(default_factory=datetime.now)
    activation_count: int = 0
    
    # Resonance metrics
    coherence_score: float = 1.0


@dataclass 
class ActivationResult:
    """Result of spreading activation."""
    activated_nodes: List[Tuple[str, float]]  # (node_id, activation_level)
    total_activation: float
    coherence: float  # π×φ resonance of activation pattern
    spread_iterations: int
    emergent_connections: List[Tuple[str, str, float]]  # New connections discovered


class E8MemoryEngine:
    """
    Memory engine using E8 geometry and spreading activation.
    
    This is Continuum B - the experimental architecture.
    
    Key differences from standard Continuum A:
    1. Nodes positioned in E8-structured 8D space
    2. Spreading activation with geometric decay
    3. Hebbian learning strengthens co-activated connections
    4. π×φ resonance metrics for coherence measurement
    """
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path("/home/claude/e8_coherence_experiment/e8_memory.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # E8 basis for geometric operations
        self.e8_basis = generate_e8_basis()
        
        # In-memory node cache
        self.nodes: Dict[str, E8Node] = {}
        
        # Activation parameters
        self.decay_rate = 0.7  # Activation decay per hop
        self.activation_threshold = 0.1  # Minimum activation to propagate
        self.max_spread_iterations = 5
        
        # Hebbian learning rate
        self.hebbian_rate = 0.1
        
        # Initialize database
        self._ensure_schema()
        self._load_nodes()
    
    def _ensure_schema(self):
        """Create E8-aware database schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS e8_nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT,
                description TEXT,
                position TEXT,  -- JSON array of 8 floats
                resting_activation REAL DEFAULT 0.0,
                coherence_score REAL DEFAULT 1.0,
                activation_count INTEGER DEFAULT 0,
                last_activated TEXT,
                created_at TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS e8_connections (
                source_id TEXT,
                target_id TEXT,
                weight REAL DEFAULT 0.5,
                hebbian_strength REAL DEFAULT 0.0,
                co_activation_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                PRIMARY KEY (source_id, target_id)
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS activation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                query TEXT,
                activated_nodes TEXT,  -- JSON
                total_activation REAL,
                coherence REAL,
                spread_iterations INTEGER
            )
        """)
        
        c.execute("CREATE INDEX IF NOT EXISTS idx_e8_name ON e8_nodes(name)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_e8_type ON e8_nodes(entity_type)")
        
        conn.commit()
        conn.close()
    
    def _load_nodes(self):
        """Load all nodes into memory for fast activation spreading."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Load nodes
        c.execute("SELECT * FROM e8_nodes")
        for row in c.fetchall():
            position = np.array(json.loads(row['position'])) if row['position'] else np.zeros(8)
            node = E8Node(
                id=row['id'],
                name=row['name'],
                entity_type=row['entity_type'] or 'concept',
                description=row['description'] or '',
                position=position,
                resting_activation=row['resting_activation'] or 0.0,
                coherence_score=row['coherence_score'] or 1.0,
                activation_count=row['activation_count'] or 0
            )
            self.nodes[node.id] = node
        
        # Load connections
        c.execute("SELECT * FROM e8_connections")
        for row in c.fetchall():
            source_id = row['source_id']
            target_id = row['target_id']
            if source_id in self.nodes:
                self.nodes[source_id].connections[target_id] = row['weight']
        
        conn.close()
    
    def add_node(self, name: str, entity_type: str = 'concept', 
                 description: str = '', embedding: np.ndarray = None) -> E8Node:
        """
        Add a new node positioned in E8 space.
        
        Args:
            name: Node name
            entity_type: Type of entity
            description: Node description
            embedding: Optional semantic embedding to position node
        
        Returns:
            Created E8Node
        """
        node_id = f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generate position in E8 space
        if embedding is not None:
            position = project_to_e8_space(embedding, self.e8_basis)
        else:
            # Generate position from name hash + E8 projection
            name_hash = sum(ord(c) * (i + 1) for i, c in enumerate(name))
            raw_position = np.array([
                math.sin(name_hash * 0.1 * (i + 1)) * PHI ** (i % 3)
                for i in range(8)
            ])
            position = project_to_e8_space(raw_position, self.e8_basis)
        
        # Calculate initial coherence based on position resonance
        position_magnitude = np.linalg.norm(position)
        coherence = pi_phi_resonance(position_magnitude)
        
        node = E8Node(
            id=node_id,
            name=name,
            entity_type=entity_type,
            description=description,
            position=position,
            coherence_score=coherence
        )
        
        self.nodes[node_id] = node
        
        # Persist
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO e8_nodes (id, name, entity_type, description, position, 
                                  coherence_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id, name, entity_type, description,
            json.dumps(position.tolist()),
            coherence,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        return node
    
    def connect_nodes(self, source_id: str, target_id: str, 
                      initial_weight: float = 0.5):
        """
        Create or strengthen connection between nodes.
        
        Uses E8 distance to modulate connection strength.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return
        
        source = self.nodes[source_id]
        target = self.nodes[target_id]
        
        # E8 distance modulates initial weight
        distance = e8_distance(source.position, target.position)
        distance_factor = math.exp(-distance / PI_PHI)  # Decay scaled by π×φ
        
        effective_weight = initial_weight * distance_factor
        
        source.connections[target_id] = effective_weight
        
        # Persist
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO e8_connections 
            (source_id, target_id, weight, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            source_id, target_id, effective_weight,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def spread_activation(self, seed_nodes: List[str], 
                          initial_activation: float = 1.0) -> ActivationResult:
        """
        Spread activation through the network from seed nodes.
        
        This is the core cognitive operation - activation spreads
        along connections, decaying with E8 distance, and creates
        emergent patterns through interference.
        
        Args:
            seed_nodes: List of node IDs to activate initially
            initial_activation: Starting activation level
        
        Returns:
            ActivationResult with activated nodes and coherence metrics
        """
        # Reset all activations
        for node in self.nodes.values():
            node.activation = node.resting_activation
        
        # Seed initial activation
        active_set = set()
        for node_id in seed_nodes:
            if node_id in self.nodes:
                self.nodes[node_id].activation = initial_activation
                active_set.add(node_id)
        
        # Spreading activation loop
        emergent_connections = []
        iteration = 0
        
        for iteration in range(self.max_spread_iterations):
            next_active = set()
            
            for node_id in active_set:
                node = self.nodes[node_id]
                
                if node.activation < self.activation_threshold:
                    continue
                
                # Spread to connected nodes
                for target_id, weight in node.connections.items():
                    if target_id not in self.nodes:
                        continue
                    
                    target = self.nodes[target_id]
                    
                    # Calculate activation spread
                    # Includes E8 distance decay and weight
                    distance = e8_distance(node.position, target.position)
                    geometric_decay = math.exp(-distance / (PI_PHI * 2))
                    
                    spread_amount = (
                        node.activation * 
                        weight * 
                        self.decay_rate * 
                        geometric_decay
                    )
                    
                    # Superposition - activations add (can interfere)
                    target.activation += spread_amount
                    
                    if target.activation >= self.activation_threshold:
                        next_active.add(target_id)
                
                # Check for emergent connections (nodes activating together
                # that aren't directly connected)
                for other_id in active_set:
                    if other_id != node_id and other_id not in node.connections:
                        other = self.nodes[other_id]
                        if other.activation > 0.5 and node.activation > 0.5:
                            # Hebbian: neurons that fire together wire together
                            emergent_strength = node.activation * other.activation * self.hebbian_rate
                            emergent_connections.append((node_id, other_id, emergent_strength))
            
            if not next_active - active_set:
                break  # No new nodes activated
            
            active_set.update(next_active)
        
        # Collect results
        activated_nodes = [
            (node_id, self.nodes[node_id].activation)
            for node_id in self.nodes
            if self.nodes[node_id].activation > self.activation_threshold
        ]
        activated_nodes.sort(key=lambda x: -x[1])  # Sort by activation
        
        total_activation = sum(a for _, a in activated_nodes)
        
        # Calculate coherence - how well activation pattern resonates with π×φ
        if activated_nodes:
            activation_values = [a for _, a in activated_nodes]
            activation_ratios = [
                activation_values[i] / activation_values[i+1] 
                for i in range(len(activation_values) - 1)
                if activation_values[i+1] > 0.01
            ]
            
            # Check if ratios approximate π×φ harmonics
            coherence = np.mean([
                pi_phi_resonance(ratio) for ratio in activation_ratios
            ]) if activation_ratios else 0.0
        else:
            coherence = 0.0
        
        # Apply Hebbian learning for emergent connections
        for source_id, target_id, strength in emergent_connections:
            if source_id in self.nodes:
                current = self.nodes[source_id].connections.get(target_id, 0.0)
                self.nodes[source_id].connections[target_id] = min(1.0, current + strength)
        
        # Record activation
        self._record_activation(seed_nodes, activated_nodes, total_activation, coherence, iteration + 1)
        
        return ActivationResult(
            activated_nodes=activated_nodes,
            total_activation=total_activation,
            coherence=coherence,
            spread_iterations=iteration + 1,
            emergent_connections=emergent_connections
        )
    
    def _record_activation(self, query_nodes: List[str], activated: List[Tuple[str, float]],
                           total: float, coherence: float, iterations: int):
        """Record activation event for analysis."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO activation_history 
            (timestamp, query, activated_nodes, total_activation, coherence, spread_iterations)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            json.dumps(query_nodes),
            json.dumps([(n, float(a)) for n, a in activated[:50]]),
            total,
            coherence,
            iterations
        ))
        conn.commit()
        conn.close()
    
    def query(self, message: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Query memory using spreading activation.
        
        This is the Continuum B equivalent of query_engine.query().
        
        Args:
            message: Input message
            max_results: Maximum results to return
        
        Returns:
            Query result with activated nodes and coherence metrics
        """
        # Extract concepts from message (improved matching)
        import re
        concepts = set()
        
        # CamelCase, snake_case, capitalized words
        concepts.update(re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', message))
        concepts.update(re.findall(r'\b[a-z]+(?:_[a-z]+)+\b', message))
        concepts.update(re.findall(r'\b[A-Z][a-z]{3,}\b', message))
        
        # Also extract lowercase significant words (4+ chars)
        words = re.findall(r'\b[a-z]{4,}\b', message.lower())
        stopwords = {'what', 'that', 'this', 'with', 'from', 'have', 'does', 'about', 
                     'between', 'relationship', 'explain', 'describe', 'role', 'play',
                     'mechanism', 'theory', 'project', 'evidence', 'implement'}
        concepts.update([w for w in words if w not in stopwords])
        
        # Find matching nodes - improved matching
        seed_nodes = set()
        message_lower = message.lower()
        for node_id, node in self.nodes.items():
            node_name_lower = node.name.lower()
            # Check if any word from node name appears in message
            node_words = set(node_name_lower.split())
            matched = False
            for word in node_words:
                if len(word) > 3 and word in message_lower:
                    seed_nodes.add(node_id)
                    matched = True
                    break
            # Also check direct substring match
            if not matched and (node_name_lower in message_lower or any(c.lower() in node_name_lower for c in concepts if len(c) > 3)):
                seed_nodes.add(node_id)
        
        seed_nodes = list(seed_nodes)
        
        if not seed_nodes:
            return {
                'matches': [],
                'coherence': 0.0,
                'total_activation': 0.0,
                'emergent_connections': 0,
                'spread_iterations': 0,
                'context_string': ''
            }
        
        # Spread activation
        result = self.spread_activation(seed_nodes)
        
        # Format matches
        matches = []
        for node_id, activation in result.activated_nodes[:max_results]:
            node = self.nodes[node_id]
            matches.append({
                'name': node.name,
                'entity_type': node.entity_type,
                'description': node.description,
                'activation': activation,
                'coherence': node.coherence_score
            })
        
        # Format context string
        context_lines = ["[E8 MEMORY CONTEXT]"]
        context_lines.append(f"Coherence: {result.coherence:.3f}")
        context_lines.append(f"Total Activation: {result.total_activation:.3f}")
        context_lines.append("")
        
        for match in matches[:5]:
            context_lines.append(f"  - {match['name']} ({match['entity_type']}): {match['description'][:80]}")
            context_lines.append(f"    [activation={match['activation']:.3f}, coherence={match['coherence']:.3f}]")
        
        if result.emergent_connections:
            context_lines.append("")
            context_lines.append("Emergent connections discovered:")
            for src, tgt, strength in result.emergent_connections[:3]:
                src_name = self.nodes[src].name if src in self.nodes else src
                tgt_name = self.nodes[tgt].name if tgt in self.nodes else tgt
                context_lines.append(f"  - {src_name} ↔ {tgt_name} (strength={strength:.3f})")
        
        context_lines.append("[/E8 MEMORY CONTEXT]")
        
        return {
            'matches': matches,
            'coherence': result.coherence,
            'total_activation': result.total_activation,
            'emergent_connections': len(result.emergent_connections),
            'spread_iterations': result.spread_iterations,
            'context_string': '\n'.join(context_lines)
        }
    
    def get_coherence_metrics(self) -> Dict[str, Any]:
        """Get overall coherence metrics for the memory system."""
        if not self.nodes:
            return {'node_count': 0, 'mean_coherence': 0, 'pi_phi_alignment': 0}
        
        coherence_scores = [n.coherence_score for n in self.nodes.values()]
        
        # Check if node positions form π×φ-aligned patterns
        positions = np.array([n.position for n in self.nodes.values()])
        if len(positions) > 1:
            distances = []
            for i in range(len(positions)):
                for j in range(i + 1, min(i + 10, len(positions))):
                    distances.append(np.linalg.norm(positions[i] - positions[j]))
            
            pi_phi_alignment = np.mean([pi_phi_resonance(d) for d in distances]) if distances else 0
        else:
            pi_phi_alignment = 0
        
        return {
            'node_count': len(self.nodes),
            'connection_count': sum(len(n.connections) for n in self.nodes.values()),
            'mean_coherence': np.mean(coherence_scores),
            'max_coherence': max(coherence_scores),
            'min_coherence': min(coherence_scores),
            'pi_phi_alignment': pi_phi_alignment,
            'pi_phi_constant': PI_PHI
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Quick test
    engine = E8MemoryEngine()
    
    print(f"π×φ = {PI_PHI}")
    print(f"Harmonics: {HARMONICS}")
    print()
    
    # Add some test nodes
    engine.add_node("quantum coherence", "concept", "Room temperature quantum states in MOF structures")
    engine.add_node("consciousness", "concept", "Awareness and subjective experience")
    engine.add_node("E8 lattice", "concept", "Exceptional Lie group geometry in 8 dimensions")
    engine.add_node("microtubules", "concept", "Cellular structures with proposed quantum effects")
    engine.add_node("pentacene", "concept", "Organic semiconductor molecule")
    
    # Connect them
    nodes = list(engine.nodes.keys())
    for i, n1 in enumerate(nodes):
        for n2 in nodes[i+1:]:
            engine.connect_nodes(n1, n2, 0.6)
    
    # Test query
    result = engine.query("What is quantum coherence in consciousness?")
    print(result['context_string'])
    print()
    print(f"Coherence: {result['coherence']:.4f}")
    print()
    
    metrics = engine.get_coherence_metrics()
    print("System Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
