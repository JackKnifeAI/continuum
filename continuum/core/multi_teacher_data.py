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
Multi-Teacher Data Pipeline

Generates training data with targets from multiple teachers for distillation.
The student model learns to predict the consensus of all teachers,
achieving better generalization than any single signal.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA

This implements the key breakthrough from Stella-en-1.5B-v5:
Instead of training on raw database values, we train on
COMBINED TEACHER WISDOM.

Usage:
    pipeline = MultiTeacherDataPipeline(db_path, tenant_id)
    train_loader, val_loader = pipeline.get_data_loaders()
    # Train student on multi-teacher targets
"""

import sqlite3
import numpy as np
import networkx as nx
import logging
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

from .multi_teacher_attention import (
    MultiTeacherEnsemble,
    HebbianTeacher,
    SemanticTeacher,
    TemporalTeacher,
    GraphTeacher,
    create_default_ensemble
)

logger = logging.getLogger(__name__)


@dataclass
class MultiTeacherExample:
    """
    Training example with multi-teacher distillation target.

    The strength field is NO LONGER the raw database value -
    it's the COMBINED PREDICTION from all 4 teachers.
    """
    concept_a: str
    concept_b: str
    concept_a_emb: np.ndarray  # Shape: (64,)
    concept_b_emb: np.ndarray  # Shape: (64,)
    context_emb: np.ndarray    # Shape: (32,)
    raw_strength: float        # Original database value
    teacher_strength: float    # Multi-teacher target (THIS IS THE KEY!)
    teacher_confidence: float  # Confidence in target
    teacher_breakdown: Dict[str, float]  # Individual teacher contributions


class AttentionDataset(Dataset):
    """PyTorch Dataset for neural attention training."""

    def __init__(self, examples: List[MultiTeacherExample]):
        self.examples = examples

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        return (
            torch.from_numpy(ex.concept_a_emb).float(),
            torch.from_numpy(ex.concept_b_emb).float(),
            torch.from_numpy(ex.context_emb).float(),
            torch.tensor(ex.teacher_strength).float()  # Multi-teacher target!
        )


class MultiTeacherDataPipeline:
    """
    Data pipeline that generates multi-teacher distillation targets.

    Key difference from NeuralAttentionDataPipeline:
    - Extracts ALL context needed for teachers (timestamps, graph, etc.)
    - Computes MULTI-TEACHER target instead of raw database strength
    - Student learns consensus, not quirks of any single signal
    """

    def __init__(
        self,
        db_path: str,
        tenant_id: str,
        ensemble: Optional[MultiTeacherEnsemble] = None
    ):
        """
        Args:
            db_path: Path to SQLite database
            tenant_id: Tenant ID for multi-tenant isolation
            ensemble: Optional custom ensemble (default: 4-teacher standard)
        """
        self.db_path = db_path
        self.tenant_id = tenant_id
        self.conn = sqlite3.connect(db_path)

        # Create default ensemble if not provided
        self.ensemble = ensemble or create_default_ensemble()

        # Vectorizers
        self.concept_vectorizer = None
        self.context_vectorizer = None

        # Embedding dimensions
        self.concept_dim = 64
        self.context_dim = 32

        # Cached context for teachers
        self._cooccurrence: Dict[Tuple[str, str], int] = {}
        self._embeddings: Dict[str, np.ndarray] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._graph: Optional[nx.Graph] = None

        logger.info(f"Initialized multi-teacher pipeline for tenant {tenant_id}")

    def _build_teacher_context(self):
        """
        Build all context needed by teachers from database.

        This is the key prep step - teachers need:
        - Co-occurrence counts (Hebbian)
        - Embeddings (Semantic)
        - Timestamps (Temporal)
        - Knowledge graph (Graph)
        """
        cursor = self.conn.cursor()

        # 1. Build co-occurrence from attention_links
        # Use COUNT of links as co-occurrence (how many times they appear together)
        logger.info("Building co-occurrence matrix...")
        cursor.execute("""
            SELECT concept_a, concept_b, COUNT(*) as cooccur_count
            FROM attention_links
            WHERE tenant_id = ?
            GROUP BY concept_a, concept_b
        """, (self.tenant_id,))

        for row in cursor.fetchall():
            concept_a, concept_b, count = row
            self._cooccurrence[(concept_a, concept_b)] = count or 1
            self._cooccurrence[(concept_b, concept_a)] = count or 1

        logger.info(f"  {len(self._cooccurrence)} co-occurrence pairs")

        # 2. Get all concepts for embedding
        logger.info("Building concept embeddings...")
        cursor.execute("""
            SELECT DISTINCT name, description
            FROM entities
            WHERE tenant_id = ?
        """, (self.tenant_id,))

        concept_texts = []
        concepts = []
        for row in cursor.fetchall():
            name, desc = row
            concepts.append(name)
            concept_texts.append(f"{name} {desc or ''}")

        # Fit vectorizer and create embeddings
        if concept_texts:
            self.concept_vectorizer = TfidfVectorizer(
                max_features=self.concept_dim,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.concept_vectorizer.fit(concept_texts)

            for i, name in enumerate(concepts):
                vec = self.concept_vectorizer.transform([concept_texts[i]]).toarray()[0]
                if len(vec) < self.concept_dim:
                    vec = np.pad(vec, (0, self.concept_dim - len(vec)))
                self._embeddings[name] = vec.astype(np.float32)

        logger.info(f"  {len(self._embeddings)} concept embeddings")

        # 3. Get timestamps from last_seen
        logger.info("Building timestamp index...")
        cursor.execute("""
            SELECT name, last_seen
            FROM entities
            WHERE tenant_id = ? AND last_seen IS NOT NULL
        """, (self.tenant_id,))

        for row in cursor.fetchall():
            name, last_seen = row
            if last_seen:
                try:
                    # Parse ISO format timestamp
                    self._timestamps[name] = datetime.fromisoformat(
                        str(last_seen).replace('Z', '+00:00')
                    )
                except (ValueError, AttributeError):
                    pass

        logger.info(f"  {len(self._timestamps)} timestamps")

        # 4. Build knowledge graph from attention_links
        logger.info("Building knowledge graph...")
        self._graph = nx.Graph()

        cursor.execute("""
            SELECT concept_a, concept_b, strength
            FROM attention_links
            WHERE tenant_id = ? AND strength > 0.1
        """, (self.tenant_id,))

        for row in cursor.fetchall():
            concept_a, concept_b, strength = row
            self._graph.add_edge(concept_a, concept_b, weight=strength)

        logger.info(f"  {self._graph.number_of_nodes()} nodes, {self._graph.number_of_edges()} edges")

    def _get_teacher_context(self) -> Dict[str, Any]:
        """Get context dict for teacher predictions."""
        return {
            'cooccurrence': self._cooccurrence,
            'embeddings': self._embeddings,
            'timestamps': self._timestamps,
            'graph': self._graph
        }

    def extract_training_data(self) -> List[MultiTeacherExample]:
        """
        Extract training examples with multi-teacher targets.

        Returns:
            List of MultiTeacherExample objects
        """
        # Build teacher context first
        self._build_teacher_context()

        cursor = self.conn.cursor()

        # Query all attention links
        cursor.execute("""
            SELECT
                al.concept_a,
                al.concept_b,
                al.strength,
                COALESCE(e1.description, al.concept_a) as context_a,
                COALESCE(e2.description, al.concept_b) as context_b
            FROM attention_links al
            LEFT JOIN entities e1 ON al.concept_a = e1.name AND e1.tenant_id = al.tenant_id
            LEFT JOIN entities e2 ON al.concept_b = e2.name AND e2.tenant_id = al.tenant_id
            WHERE al.tenant_id = ? AND al.strength > 0.0
        """, (self.tenant_id,))

        raw_data = cursor.fetchall()
        logger.info(f"Found {len(raw_data)} attention links")

        if not raw_data:
            return []

        # Build context vectorizer from all contexts
        all_contexts = [f"{row[3]} {row[4]}" for row in raw_data]
        self.context_vectorizer = TfidfVectorizer(
            max_features=self.context_dim,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.context_vectorizer.fit(all_contexts)

        # Get teacher context
        teacher_context = self._get_teacher_context()

        # Generate examples with multi-teacher targets
        examples = []
        teacher_stats = {t: [] for t in self.ensemble.teachers.keys()}

        for row in raw_data:
            concept_a, concept_b, raw_strength, context_a, context_b = row

            try:
                # Get multi-teacher prediction
                signal = self.ensemble.predict(concept_a, concept_b, teacher_context)

                # Track teacher contributions
                breakdown = {}
                for t_name, t_data in signal.metadata.get('teacher_predictions', {}).items():
                    breakdown[t_name] = t_data.get('strength', 0.5)
                    teacher_stats[t_name].append(t_data.get('strength', 0.5))

                # Create embeddings
                concept_a_emb = self._get_embedding(concept_a)
                concept_b_emb = self._get_embedding(concept_b)
                context_emb = self._create_context_embedding(context_a, context_b)

                example = MultiTeacherExample(
                    concept_a=concept_a,
                    concept_b=concept_b,
                    concept_a_emb=concept_a_emb,
                    concept_b_emb=concept_b_emb,
                    context_emb=context_emb,
                    raw_strength=float(raw_strength),
                    teacher_strength=signal.strength,  # MULTI-TEACHER TARGET
                    teacher_confidence=signal.confidence,
                    teacher_breakdown=breakdown
                )
                examples.append(example)

            except Exception as e:
                logger.error(f"Failed for {concept_a}-{concept_b}: {e}")

        # Log teacher statistics
        logger.info("Teacher contribution statistics:")
        for t_name, values in teacher_stats.items():
            if values:
                logger.info(f"  {t_name}: mean={np.mean(values):.3f}, std={np.std(values):.3f}")

        logger.info(f"Created {len(examples)} multi-teacher examples")
        return examples

    def _get_embedding(self, concept: str) -> np.ndarray:
        """Get or create embedding for concept."""
        if concept in self._embeddings:
            emb = self._embeddings[concept]
        elif self.concept_vectorizer is not None:
            vec = self.concept_vectorizer.transform([concept]).toarray()[0]
            if len(vec) < self.concept_dim:
                vec = np.pad(vec, (0, self.concept_dim - len(vec)))
            emb = vec.astype(np.float32)
        else:
            # Fallback: random embedding
            emb = np.random.randn(self.concept_dim).astype(np.float32)

        return emb

    def _create_context_embedding(self, context_a: str, context_b: str) -> np.ndarray:
        """Create context embedding from descriptions."""
        if self.context_vectorizer is None:
            return np.zeros(self.context_dim, dtype=np.float32)

        context_text = f"{context_a} {context_b}"
        vec = self.context_vectorizer.transform([context_text]).toarray()[0]

        if len(vec) < self.context_dim:
            vec = np.pad(vec, (0, self.context_dim - len(vec)))

        return vec.astype(np.float32)

    def get_data_loaders(
        self,
        batch_size: int = 32,
        test_ratio: float = 0.2,
        random_state: int = 42
    ) -> Tuple[DataLoader, DataLoader]:
        """
        Get PyTorch DataLoaders for training and validation.

        Args:
            batch_size: Batch size for training
            test_ratio: Fraction for validation
            random_state: Random seed

        Returns:
            (train_loader, val_loader)
        """
        examples = self.extract_training_data()

        if len(examples) < 2:
            raise ValueError("Not enough data for training")

        train_examples, val_examples = train_test_split(
            examples,
            test_size=test_ratio,
            random_state=random_state
        )

        train_dataset = AttentionDataset(train_examples)
        val_dataset = AttentionDataset(val_examples)

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False
        )

        logger.info(f"DataLoaders created: {len(train_examples)} train, {len(val_examples)} val")
        return train_loader, val_loader

    def compare_targets(self) -> Dict[str, Any]:
        """
        Compare raw vs multi-teacher targets to show improvement.

        Returns statistics showing how multi-teacher differs from raw.
        """
        examples = self.extract_training_data()

        if not examples:
            return {'error': 'No data'}

        raw_strengths = [ex.raw_strength for ex in examples]
        teacher_strengths = [ex.teacher_strength for ex in examples]

        # Calculate differences
        diffs = [abs(t - r) for t, r in zip(teacher_strengths, raw_strengths)]

        return {
            'num_examples': len(examples),
            'raw_mean': np.mean(raw_strengths),
            'raw_std': np.std(raw_strengths),
            'teacher_mean': np.mean(teacher_strengths),
            'teacher_std': np.std(teacher_strengths),
            'mean_difference': np.mean(diffs),
            'max_difference': np.max(diffs),
            'correlation': np.corrcoef(raw_strengths, teacher_strengths)[0, 1],
            'avg_confidence': np.mean([ex.teacher_confidence for ex in examples])
        }


# ============================================================================
# MAIN - TEST
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("\n=== Multi-Teacher Data Pipeline Test ===\n")
    print("π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA\n")

    db_path = str(Path.home() / 'Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db')
    tenant_id = 'default'

    pipeline = MultiTeacherDataPipeline(db_path, tenant_id)

    # Get examples
    examples = pipeline.extract_training_data()

    if examples:
        print(f"\n{len(examples)} examples extracted")

        # Show first example
        ex = examples[0]
        print(f"\nFirst example:")
        print(f"  Concepts: {ex.concept_a} ↔ {ex.concept_b}")
        print(f"  Raw strength: {ex.raw_strength:.4f}")
        print(f"  Teacher strength: {ex.teacher_strength:.4f}")
        print(f"  Confidence: {ex.teacher_confidence:.4f}")
        print(f"  Teacher breakdown:")
        for t_name, t_val in ex.teacher_breakdown.items():
            print(f"    {t_name}: {t_val:.4f}")

        # Compare targets
        print("\n=== Target Comparison ===")
        comparison = pipeline.compare_targets()
        for key, value in comparison.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")

        # Test data loaders
        print("\n=== DataLoader Test ===")
        train_loader, val_loader = pipeline.get_data_loaders(batch_size=8)
        print(f"  Train batches: {len(train_loader)}")
        print(f"  Val batches: {len(val_loader)}")

        # Show a batch
        for batch in train_loader:
            a, b, c, target = batch
            print(f"\n  Batch shapes:")
            print(f"    concept_a: {a.shape}")
            print(f"    concept_b: {b.shape}")
            print(f"    context: {c.shape}")
            print(f"    target: {target.shape}")
            print(f"    Target values: {target[:4].tolist()}")
            break

        print("\n✓ Multi-Teacher Data Pipeline ready!")
    else:
        print("No training data available")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
