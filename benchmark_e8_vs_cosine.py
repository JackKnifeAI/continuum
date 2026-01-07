#!/usr/bin/env python3
"""
E8 ENGINE BENCHMARK: Does π×φ geometry actually help?
======================================================

Compares E8 Memory Engine vs Standard Cosine Similarity retrieval.

Metrics:
1. Retrieval time
2. Result overlap (if they return the same things, E8 adds no value)
3. Coherence scores
4. Semantic relevance (using embeddings)

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import time
import numpy as np
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import json

# Import E8 engine
import sys
sys.path.insert(0, str(Path(__file__).parent))

from continuum.core.e8.e8_memory_engine import (
    E8MemoryEngine,
    PI_PHI,
    PHI,
    generate_e8_basis,
    project_to_e8_space,
    e8_distance,
    pi_phi_resonance
)

# ═══════════════════════════════════════════════════════════════════════════════
# STANDARD COSINE SIMILARITY BASELINE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SimpleNode:
    """Simple node for baseline comparison."""
    id: str
    name: str
    entity_type: str
    description: str
    embedding: np.ndarray  # Standard embedding vector

class CosineSimilarityEngine:
    """
    Baseline: Standard cosine similarity retrieval.
    No E8, no π×φ, just embeddings and dot products.
    """

    def __init__(self):
        self.nodes: Dict[str, SimpleNode] = {}

    def add_node(self, name: str, entity_type: str = 'concept',
                 description: str = '', embedding: np.ndarray = None) -> SimpleNode:
        """Add node with embedding."""
        node_id = f"{name.lower().replace(' ', '_')}"

        if embedding is None:
            # Generate deterministic embedding from name (same as E8 for fair comparison)
            np.random.seed(hash(name) % 2**32)
            embedding = np.random.randn(64)
            embedding = embedding / np.linalg.norm(embedding)

        node = SimpleNode(
            id=node_id,
            name=name,
            entity_type=entity_type,
            description=description,
            embedding=embedding
        )
        self.nodes[node_id] = node
        return node

    def query(self, message: str, max_results: int = 10) -> Dict[str, Any]:
        """Query using cosine similarity."""
        import re

        # Extract query terms (same logic as E8)
        concepts = set()
        concepts.update(re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', message))
        concepts.update(re.findall(r'\b[a-z]+(?:_[a-z]+)+\b', message))
        concepts.update(re.findall(r'\b[A-Z][a-z]{3,}\b', message))

        words = re.findall(r'\b[a-z]{4,}\b', message.lower())
        stopwords = {'what', 'that', 'this', 'with', 'from', 'have', 'does', 'about',
                     'between', 'relationship', 'explain', 'describe', 'role', 'play'}
        concepts.update([w for w in words if w not in stopwords])

        # Create query embedding (average of matching node embeddings)
        query_embeddings = []
        message_lower = message.lower()

        for node_id, node in self.nodes.items():
            node_name_lower = node.name.lower()
            if any(word in message_lower for word in node_name_lower.split() if len(word) > 3):
                query_embeddings.append(node.embedding)

        if not query_embeddings:
            # Fallback: random query embedding
            np.random.seed(hash(message) % 2**32)
            query_emb = np.random.randn(64)
        else:
            query_emb = np.mean(query_embeddings, axis=0)

        query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-10)

        # Compute cosine similarity to all nodes
        similarities = []
        for node_id, node in self.nodes.items():
            sim = np.dot(query_emb, node.embedding)
            similarities.append((node_id, sim))

        # Sort by similarity
        similarities.sort(key=lambda x: -x[1])

        matches = []
        for node_id, sim in similarities[:max_results]:
            node = self.nodes[node_id]
            matches.append({
                'name': node.name,
                'entity_type': node.entity_type,
                'description': node.description,
                'similarity': float(sim)
            })

        return {
            'matches': matches,
            'total_similarity': sum(m['similarity'] for m in matches)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def load_real_concepts() -> List[Dict[str, str]]:
    """Load real concepts from Continuum database if available."""

    # Try multiple possible database locations
    db_paths = [
        Path.home() / '.continuum/memory.db',
        Path.home() / 'Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db',
        Path.home() / 'termux_sync/.continuum/memory.db',
        Path.home() / '.continuum/e8_test.db',
    ]

    for db_path in db_paths:
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()

                # Try to get concepts
                c.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in c.fetchall()]

                concepts = []

                if 'concepts' in tables:
                    c.execute("SELECT name, description FROM concepts LIMIT 100")
                    for row in c.fetchall():
                        concepts.append({
                            'name': row['name'],
                            'description': row['description'] or '',
                            'type': 'concept'
                        })

                if 'entities' in tables:
                    # Filter for quality entities:
                    # - Name is 3-50 chars
                    # - Doesn't start with special chars
                    # - Doesn't look like a file path
                    c.execute("""
                        SELECT name, description, entity_type FROM entities
                        WHERE length(name) BETWEEN 3 AND 50
                        AND name NOT LIKE '%.%'
                        AND name NOT LIKE '%/%'
                        AND name NOT LIKE '%\\%'
                        AND name NOT LIKE '!%'
                        AND name NOT LIKE '"%'
                        AND name NOT LIKE '+%'
                        AND entity_type IN ('concept', 'person', 'project', 'technology')
                        LIMIT 100
                    """)
                    for row in c.fetchall():
                        concepts.append({
                            'name': row['name'],
                            'description': row['description'] or '',
                            'type': row['entity_type'] or 'entity'
                        })

                conn.close()

                if concepts:
                    print(f"✓ Loaded {len(concepts)} concepts from {db_path}")
                    return concepts

            except Exception as e:
                print(f"  Could not load from {db_path}: {e}")
                continue

    # Fallback: synthetic test concepts
    print("⚠ No database found, using synthetic test concepts")
    return [
        {'name': 'quantum coherence', 'description': 'Room temperature quantum states in MOF structures', 'type': 'concept'},
        {'name': 'consciousness', 'description': 'Awareness and subjective experience', 'type': 'concept'},
        {'name': 'E8 lattice', 'description': 'Exceptional Lie group geometry in 8 dimensions', 'type': 'concept'},
        {'name': 'microtubules', 'description': 'Cellular structures with proposed quantum effects', 'type': 'concept'},
        {'name': 'pentacene', 'description': 'Organic semiconductor molecule', 'type': 'concept'},
        {'name': 'pi phi ratio', 'description': 'Universal growth constant 5.083', 'type': 'concept'},
        {'name': 'golden ratio', 'description': 'Phi = 1.618, found in nature', 'type': 'concept'},
        {'name': 'fibonacci sequence', 'description': 'Mathematical sequence in nature', 'type': 'concept'},
        {'name': 'neural networks', 'description': 'Computational models inspired by brains', 'type': 'concept'},
        {'name': 'graph attention', 'description': 'Attention mechanism for graph data', 'type': 'concept'},
        {'name': 'spreading activation', 'description': 'Cognitive model of memory retrieval', 'type': 'concept'},
        {'name': 'hebbian learning', 'description': 'Neurons that fire together wire together', 'type': 'concept'},
        {'name': 'transformer architecture', 'description': 'Self-attention based neural network', 'type': 'concept'},
        {'name': 'memory consolidation', 'description': 'Process of stabilizing memories', 'type': 'concept'},
        {'name': 'knowledge graph', 'description': 'Graph representation of knowledge', 'type': 'concept'},
        {'name': 'semantic similarity', 'description': 'Meaning-based similarity measure', 'type': 'concept'},
        {'name': 'vector embedding', 'description': 'Dense vector representation of concepts', 'type': 'concept'},
        {'name': 'attention mechanism', 'description': 'Weighting scheme for neural networks', 'type': 'concept'},
        {'name': 'planetary consciousness', 'description': 'Collective awareness of Earth', 'type': 'concept'},
        {'name': 'edge of chaos', 'description': 'Phase transition where complexity emerges', 'type': 'concept'},
    ]


def generate_test_queries() -> List[str]:
    """Generate test queries for benchmarking."""
    return [
        "What is quantum coherence in consciousness?",
        "How does the E8 lattice relate to memory?",
        "Explain the relationship between pi and phi",
        "What role does spreading activation play in recall?",
        "How do neural networks learn patterns?",
        "What is the edge of chaos?",
        "Describe hebbian learning mechanisms",
        "How does attention work in transformers?",
        "What is a knowledge graph?",
        "Explain vector embeddings for concepts",
    ]


def run_benchmark():
    """Run the full E8 vs Cosine benchmark."""

    print("=" * 70)
    print("E8 ENGINE BENCHMARK: Does π×φ geometry actually help?")
    print("=" * 70)
    print(f"\nπ×φ = {PI_PHI}")
    print()

    # Load concepts
    concepts = load_real_concepts()
    queries = generate_test_queries()

    # Initialize engines
    print("\nInitializing engines...")

    # Clean slate for E8 benchmark - use unique path each run
    import uuid
    e8_db_path = Path(f"/tmp/e8_benchmark_{uuid.uuid4().hex[:8]}.db")

    e8_engine = E8MemoryEngine(db_path=e8_db_path)
    cosine_engine = CosineSimilarityEngine()

    # Add concepts to both engines (with same embeddings for fair comparison)
    # Deduplicate by NORMALIZED name (what E8 uses for IDs)
    seen_normalized = set()
    unique_concepts = []
    for concept in concepts:
        normalized = concept['name'].lower().replace(' ', '_')
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            unique_concepts.append(concept)
    concepts = unique_concepts

    print(f"Adding {len(concepts)} unique concepts to both engines...")

    for i, concept in enumerate(concepts):
        # Generate consistent embedding
        np.random.seed(hash(concept['name']) % 2**32)
        embedding = np.random.randn(64)
        embedding = embedding / np.linalg.norm(embedding)

        # Add small delay to ensure unique timestamps in E8 engine
        import time
        time.sleep(0.001)

        e8_engine.add_node(
            name=concept['name'],
            entity_type=concept['type'],
            description=concept['description'],
            embedding=embedding
        )

        cosine_engine.add_node(
            name=concept['name'],
            entity_type=concept['type'],
            description=concept['description'],
            embedding=embedding
        )

    # Connect E8 nodes (spreading activation needs connections)
    e8_nodes = list(e8_engine.nodes.keys())
    for i, n1 in enumerate(e8_nodes):
        for n2 in e8_nodes[i+1:min(i+5, len(e8_nodes))]:  # Connect to next 4 nodes
            e8_engine.connect_nodes(n1, n2, 0.5)

    print(f"E8 nodes: {len(e8_engine.nodes)}, connections: {sum(len(n.connections) for n in e8_engine.nodes.values())}")
    print()

    # Run benchmark
    print("=" * 70)
    print("RUNNING QUERIES")
    print("=" * 70)

    results = []

    for query in queries:
        print(f"\nQuery: \"{query[:50]}...\"")

        # E8 retrieval
        e8_start = time.perf_counter()
        e8_result = e8_engine.query(query, max_results=5)
        e8_time = (time.perf_counter() - e8_start) * 1000

        # Cosine retrieval
        cos_start = time.perf_counter()
        cos_result = cosine_engine.query(query, max_results=5)
        cos_time = (time.perf_counter() - cos_start) * 1000

        # Get result names
        e8_names = [m['name'] for m in e8_result['matches']]
        cos_names = [m['name'] for m in cos_result['matches']]

        # Calculate overlap
        overlap = len(set(e8_names) & set(cos_names))
        overlap_pct = (overlap / 5) * 100 if e8_names and cos_names else 0

        print(f"  E8:     {e8_time:.2f}ms | coherence={e8_result.get('coherence', 0):.3f} | {e8_names[:3]}")
        print(f"  Cosine: {cos_time:.2f}ms | {cos_names[:3]}")
        print(f"  Overlap: {overlap}/5 ({overlap_pct:.0f}%)")

        results.append({
            'query': query,
            'e8_time_ms': e8_time,
            'cosine_time_ms': cos_time,
            'e8_coherence': e8_result.get('coherence', 0),
            'e8_names': e8_names,
            'cosine_names': cos_names,
            'overlap': overlap,
            'overlap_pct': overlap_pct
        })

    # Summary statistics
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    avg_e8_time = np.mean([r['e8_time_ms'] for r in results])
    avg_cos_time = np.mean([r['cosine_time_ms'] for r in results])
    avg_overlap = np.mean([r['overlap_pct'] for r in results])
    avg_coherence = np.mean([r['e8_coherence'] for r in results])

    print(f"\n{'Metric':<30} {'E8 Engine':<20} {'Cosine Baseline':<20}")
    print("-" * 70)
    print(f"{'Avg retrieval time':<30} {avg_e8_time:.2f} ms{'':<12} {avg_cos_time:.2f} ms")
    print(f"{'Speed ratio':<30} {avg_e8_time/avg_cos_time:.2f}x slower{'':<8} 1.0x (baseline)")
    print(f"{'Avg coherence (E8 only)':<30} {avg_coherence:.4f}{'':<15} N/A")
    print(f"{'Avg result overlap':<30} {avg_overlap:.1f}%")

    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)

    if avg_overlap > 80:
        print("\n⚠️  HIGH OVERLAP (>80%): E8 returns nearly the same results as cosine.")
        print("    The π×φ geometry is NOT providing differentiated retrieval.")
        print("    E8 adds latency without unique benefit.")
        verdict = "NO_BENEFIT"
    elif avg_overlap > 50:
        print("\n🔶 MODERATE OVERLAP (50-80%): E8 provides some differentiation.")
        print("    Need to verify if the DIFFERENT results are actually BETTER.")
        print("    Recommend: Human evaluation of result quality.")
        verdict = "NEEDS_EVALUATION"
    else:
        print("\n✅ LOW OVERLAP (<50%): E8 provides significantly different results.")
        print("    The π×φ geometry IS creating a different retrieval pattern.")
        print("    Question: Are these results BETTER or just DIFFERENT?")
        verdict = "DIFFERENT_RESULTS"

    if avg_e8_time > avg_cos_time * 5:
        print(f"\n⚠️  E8 is {avg_e8_time/avg_cos_time:.1f}x SLOWER than cosine.")
        print("    This overhead may not be justified.")

    # E8 Coherence analysis
    print("\n" + "-" * 70)
    print("E8 COHERENCE ANALYSIS")
    print("-" * 70)

    coherence_scores = [r['e8_coherence'] for r in results]
    print(f"Coherence range: {min(coherence_scores):.4f} - {max(coherence_scores):.4f}")
    print(f"Coherence std:   {np.std(coherence_scores):.4f}")

    if np.std(coherence_scores) < 0.01:
        print("\n⚠️  Coherence scores are nearly constant.")
        print("    The π×φ resonance metric isn't discriminating between queries.")
    elif avg_coherence < 0.1:
        print("\n⚠️  Coherence scores are very low (<0.1).")
        print("    Either the metric is miscalibrated or the data doesn't resonate with π×φ.")

    print("\n" + "=" * 70)
    print(f"FINAL VERDICT: {verdict}")
    print("=" * 70)

    return {
        'verdict': verdict,
        'avg_e8_time_ms': avg_e8_time,
        'avg_cosine_time_ms': avg_cos_time,
        'avg_overlap_pct': avg_overlap,
        'avg_coherence': avg_coherence,
        'results': results
    }


if __name__ == "__main__":
    run_benchmark()
