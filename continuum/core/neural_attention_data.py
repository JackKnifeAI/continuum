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
Neural Attention Data Pipeline

Extracts training data from attention_links and entities tables,
creates embeddings, and prepares data for neural model training.

Usage:
    from neural_attention_data import NeuralAttentionDataPipeline

    pipeline = NeuralAttentionDataPipeline(db_path, tenant_id)
    training_data = pipeline.extract_training_data()
    train, test = pipeline.get_train_test_split(test_ratio=0.2)
"""

import sqlite3
import numpy as np
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Single training example for neural attention model"""
    concept_a: str
    concept_b: str
    concept_a_emb: np.ndarray  # Shape: (64,)
    concept_b_emb: np.ndarray  # Shape: (64,)
    context_emb: np.ndarray    # Shape: (32,)
    strength: float
    link_type: str


class NeuralAttentionDataPipeline:
    """
    Data pipeline for neural attention model training.

    Extracts attention_links from database, creates embeddings using TF-IDF,
    and prepares training/test splits.
    """

    def __init__(self, db_path: str, tenant_id: str):
        """
        Initialize data pipeline.

        Args:
            db_path: Path to SQLite database
            tenant_id: Tenant ID for multi-tenant isolation
        """
        self.db_path = db_path
        self.tenant_id = tenant_id
        self.conn = sqlite3.connect(db_path)

        # TF-IDF vectorizers
        self.concept_vectorizer = None
        self.context_vectorizer = None

        # Embedding dimensions
        self.concept_dim = 64
        self.context_dim = 32

        logger.info(f"Initialized data pipeline for tenant {tenant_id}")

    def extract_training_data(self) -> List[TrainingExample]:
        """
        Extract all training examples from database.

        Returns:
            List of TrainingExample objects
        """
        cursor = self.conn.cursor()

        # Query attention links with entity descriptions
        cursor.execute("""
            SELECT
                al.concept_a,
                al.concept_b,
                al.strength,
                al.link_type,
                COALESCE(e1.description, al.concept_a) as context_a,
                COALESCE(e2.description, al.concept_b) as context_b
            FROM attention_links al
            LEFT JOIN entities e1 ON al.concept_a = e1.name AND e1.tenant_id = al.tenant_id
            LEFT JOIN entities e2 ON al.concept_b = e2.name AND e2.tenant_id = al.tenant_id
            WHERE al.tenant_id = ? AND al.strength > 0.0
        """, (self.tenant_id,))

        raw_data = cursor.fetchall()
        logger.info(f"Found {len(raw_data)} attention links")

        if len(raw_data) == 0:
            logger.warning("No training data found!")
            return []

        # Extract all concept texts for vocabulary building
        all_concept_texts = []
        all_context_texts = []

        for row in raw_data:
            concept_a, concept_b, _, _, context_a, context_b = row
            all_concept_texts.extend([concept_a, concept_b])
            all_context_texts.append(f"{context_a} {context_b}")

        # Fit vectorizers on all data
        logger.info("Building TF-IDF vocabulary...")
        self._fit_vectorizers(all_concept_texts, all_context_texts)

        # Create training examples
        examples = []
        for row in raw_data:
            concept_a, concept_b, strength, link_type, context_a, context_b = row

            try:
                # Create embeddings
                concept_a_emb = self.create_embeddings(concept_a)
                concept_b_emb = self.create_embeddings(concept_b)
                context_emb = self.create_context_embedding(concept_a, concept_b, context_a, context_b)

                example = TrainingExample(
                    concept_a=concept_a,
                    concept_b=concept_b,
                    concept_a_emb=concept_a_emb,
                    concept_b_emb=concept_b_emb,
                    context_emb=context_emb,
                    strength=float(strength),
                    link_type=link_type
                )
                examples.append(example)

            except Exception as e:
                logger.error(f"Failed to create example for {concept_a}-{concept_b}: {e}")

        logger.info(f"Created {len(examples)} training examples")
        return examples

    def _fit_vectorizers(self, concept_texts: List[str], context_texts: List[str]):
        """Fit TF-IDF vectorizers on all data"""

        # Concept vectorizer (64 dimensions)
        self.concept_vectorizer = TfidfVectorizer(
            max_features=self.concept_dim,
            stop_words='english',
            ngram_range=(1, 2),  # Unigrams and bigrams
            lowercase=True
        )
        self.concept_vectorizer.fit(concept_texts)

        # Context vectorizer (32 dimensions)
        self.context_vectorizer = TfidfVectorizer(
            max_features=self.context_dim,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.context_vectorizer.fit(context_texts)

        logger.info(f"Vocabulary built: {len(self.concept_vectorizer.vocabulary_)} concept terms, "
                   f"{len(self.context_vectorizer.vocabulary_)} context terms")

    def create_embeddings(self, text: str) -> np.ndarray:
        """
        Convert text to concept embedding using TF-IDF.

        Args:
            text: Input text (concept name)

        Returns:
            Embedding vector of shape (concept_dim,)
        """
        if self.concept_vectorizer is None:
            raise RuntimeError("Vectorizer not fitted. Call extract_training_data() first.")

        # Transform to TF-IDF vector
        vec = self.concept_vectorizer.transform([text]).toarray()[0]

        # Ensure correct dimension
        if len(vec) < self.concept_dim:
            vec = np.pad(vec, (0, self.concept_dim - len(vec)))
        elif len(vec) > self.concept_dim:
            vec = vec[:self.concept_dim]

        return vec.astype(np.float32)

    def create_context_embedding(self,
                                 concept_a: str,
                                 concept_b: str,
                                 context_a: str = "",
                                 context_b: str = "") -> np.ndarray:
        """
        Create context embedding combining both concepts' contexts.

        Args:
            concept_a: First concept name
            concept_b: Second concept name
            context_a: Description of first concept
            context_b: Description of second concept

        Returns:
            Context vector of shape (context_dim,)
        """
        if self.context_vectorizer is None:
            raise RuntimeError("Vectorizer not fitted. Call extract_training_data() first.")

        # Combine all context information
        context_text = f"{context_a} {context_b} {concept_a} {concept_b}"

        # Transform to TF-IDF vector
        vec = self.context_vectorizer.transform([context_text]).toarray()[0]

        # Ensure correct dimension
        if len(vec) < self.context_dim:
            vec = np.pad(vec, (0, self.context_dim - len(vec)))
        elif len(vec) > self.context_dim:
            vec = vec[:self.context_dim]

        return vec.astype(np.float32)

    def get_train_test_split(self,
                            test_ratio: float = 0.2,
                            random_state: int = 42) -> Tuple[List[TrainingExample], List[TrainingExample]]:
        """
        Split data into train and test sets.

        Args:
            test_ratio: Fraction of data for testing (default: 0.2)
            random_state: Random seed for reproducibility

        Returns:
            (train_examples, test_examples)
        """
        examples = self.extract_training_data()

        if len(examples) < 2:
            logger.warning("Not enough examples for train/test split")
            return examples, []

        train, test = train_test_split(
            examples,
            test_size=test_ratio,
            random_state=random_state
        )

        logger.info(f"Split: {len(train)} train, {len(test)} test examples")
        return train, test

    def get_stats(self) -> dict:
        """Get statistics about training data"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_links,
                AVG(strength) as avg_strength,
                MIN(strength) as min_strength,
                MAX(strength) as max_strength,
                COUNT(DISTINCT link_type) as num_link_types
            FROM attention_links
            WHERE tenant_id = ?
        """, (self.tenant_id,))

        row = cursor.fetchone()

        return {
            'total_links': row[0],
            'avg_strength': row[1],
            'min_strength': row[2],
            'max_strength': row[3],
            'num_link_types': row[4],
            'concept_dim': self.concept_dim,
            'context_dim': self.context_dim
        }


if __name__ == '__main__':
    # Test the pipeline
    import sys

    logging.basicConfig(level=logging.INFO)

    db_path = str(Path.home() / 'Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db')
    tenant_id = 'default'

    pipeline = NeuralAttentionDataPipeline(db_path, tenant_id)

    print("\nData Pipeline Statistics:")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nExtracting training data...")
    examples = pipeline.extract_training_data()

    if examples:
        print(f"\nFirst example:")
        ex = examples[0]
        print(f"  {ex.concept_a} <-> {ex.concept_b}")
        print(f"  Strength: {ex.strength}")
        print(f"  Link type: {ex.link_type}")
        print(f"  Embedding shapes: {ex.concept_a_emb.shape}, {ex.concept_b_emb.shape}, {ex.context_emb.shape}")

        print("\nTrain/Test split:")
        train, test = pipeline.get_train_test_split()
        print(f"  Train: {len(train)} examples")
        print(f"  Test: {len(test)} examples")
    else:
        print("\nNo training data available")
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
