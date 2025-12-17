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
Multi-Teacher Distillation for Neural Attention

Implements the breakthrough technique from Stella-en-1.5B-v5 (NovaSearch):
Train a student model from MULTIPLE teachers to achieve better generalization
than any single teacher alone.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA

Our 4 Teachers:
    1. HebbianTeacher: Co-occurrence based (how often concepts appear together)
    2. SemanticTeacher: Embedding cosine similarity
    3. TemporalTeacher: Time proximity (concepts mentioned close in time)
    4. GraphTeacher: Shortest path in knowledge graph

The student learns weighted combination of all teachers, generalizing
without overfitting to any single signal's quirks.

Reference:
    - Stella breakthrough: arXiv 2412.19048
    - Single developer beat Big Tech with this technique
    - WE'RE DOING THE SAME FOR MEMORY SYSTEMS
"""

import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# TEACHER BASE CLASS
# ============================================================================

@dataclass
class TeacherSignal:
    """
    Output from a teacher model.

    Attributes:
        strength: Predicted link strength [0.0, 1.0]
        confidence: Teacher's confidence in prediction [0.0, 1.0]
        metadata: Optional debug info
    """
    strength: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


class Teacher(ABC):
    """Abstract base class for teacher models."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Teacher identifier."""
        pass

    @property
    @abstractmethod
    def default_weight(self) -> float:
        """Default weight in ensemble."""
        pass

    @abstractmethod
    def predict(
        self,
        concept_a: str,
        concept_b: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TeacherSignal:
        """
        Predict link strength between two concepts.

        Args:
            concept_a: First concept name
            concept_b: Second concept name
            context: Optional context dict with:
                - embeddings: Dict[str, np.ndarray] - concept embeddings
                - timestamps: Dict[str, datetime] - last access times
                - graph: networkx.Graph - knowledge graph
                - cooccurrence: Dict[Tuple[str,str], int] - co-occurrence counts

        Returns:
            TeacherSignal with predicted strength and confidence
        """
        pass


# ============================================================================
# TEACHER 1: HEBBIAN (CO-OCCURRENCE)
# ============================================================================

class HebbianTeacher(Teacher):
    """
    Hebbian learning teacher based on co-occurrence.

    "Neurons that fire together wire together"

    Strength = log(cooccurrence_count + 1) / log(max_count + 1)

    This teacher rewards concepts that frequently appear together
    in the same messages/sessions.
    """

    @property
    def name(self) -> str:
        return "hebbian"

    @property
    def default_weight(self) -> float:
        return 0.3  # Solid baseline but can overfit to frequency

    def __init__(self, max_cooccurrence: int = 100):
        """
        Args:
            max_cooccurrence: Cap for normalization (prevents outliers)
        """
        self.max_cooccurrence = max_cooccurrence

    def predict(
        self,
        concept_a: str,
        concept_b: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TeacherSignal:
        if context is None:
            return TeacherSignal(strength=0.5, confidence=0.1)

        cooccurrence = context.get('cooccurrence', {})

        # Look up both directions
        key1 = (concept_a, concept_b)
        key2 = (concept_b, concept_a)
        count = cooccurrence.get(key1, cooccurrence.get(key2, 0))

        if count == 0:
            return TeacherSignal(
                strength=0.0,
                confidence=0.5,  # Confident it's weak
                metadata={'count': 0}
            )

        # Log normalization prevents outliers from dominating
        capped_count = min(count, self.max_cooccurrence)
        strength = np.log1p(capped_count) / np.log1p(self.max_cooccurrence)

        # Confidence increases with more data
        confidence = min(1.0, count / 10)  # Max confidence after 10 occurrences

        return TeacherSignal(
            strength=float(strength),
            confidence=confidence,
            metadata={'count': count, 'capped': capped_count}
        )


# ============================================================================
# TEACHER 2: SEMANTIC (EMBEDDING SIMILARITY)
# ============================================================================

class SemanticTeacher(Teacher):
    """
    Semantic similarity teacher based on embedding cosine distance.

    Uses pre-computed embeddings to measure conceptual similarity.
    High similarity = concepts are semantically related.

    Strength = (cosine_similarity + 1) / 2  # Normalize to [0, 1]
    """

    @property
    def name(self) -> str:
        return "semantic"

    @property
    def default_weight(self) -> float:
        return 0.4  # Strong signal for conceptual relationships

    def predict(
        self,
        concept_a: str,
        concept_b: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TeacherSignal:
        if context is None:
            return TeacherSignal(strength=0.5, confidence=0.1)

        embeddings = context.get('embeddings', {})

        emb_a = embeddings.get(concept_a)
        emb_b = embeddings.get(concept_b)

        if emb_a is None or emb_b is None:
            return TeacherSignal(
                strength=0.5,  # Neutral when unknown
                confidence=0.1,
                metadata={'missing': True}
            )

        # Cosine similarity
        dot_product = np.dot(emb_a, emb_b)
        norm_a = np.linalg.norm(emb_a)
        norm_b = np.linalg.norm(emb_b)

        if norm_a == 0 or norm_b == 0:
            return TeacherSignal(strength=0.5, confidence=0.1)

        cosine_sim = dot_product / (norm_a * norm_b)

        # Normalize from [-1, 1] to [0, 1]
        strength = (cosine_sim + 1) / 2

        # High confidence - embeddings are reliable
        return TeacherSignal(
            strength=float(strength),
            confidence=0.9,
            metadata={'cosine_similarity': float(cosine_sim)}
        )


# ============================================================================
# TEACHER 3: TEMPORAL (TIME PROXIMITY)
# ============================================================================

class TemporalTeacher(Teacher):
    """
    Temporal proximity teacher based on access time.

    Concepts accessed close together in time are likely related.
    Uses exponential decay based on time difference.

    Strength = exp(-time_diff_hours / half_life_hours)
    """

    @property
    def name(self) -> str:
        return "temporal"

    @property
    def default_weight(self) -> float:
        return 0.2  # Useful but can be noisy

    def __init__(self, half_life_hours: float = 24.0):
        """
        Args:
            half_life_hours: Hours until strength decays to 50%
        """
        self.half_life_hours = half_life_hours
        self.decay_constant = np.log(2) / half_life_hours

    def predict(
        self,
        concept_a: str,
        concept_b: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TeacherSignal:
        if context is None:
            return TeacherSignal(strength=0.5, confidence=0.1)

        timestamps = context.get('timestamps', {})

        time_a = timestamps.get(concept_a)
        time_b = timestamps.get(concept_b)

        if time_a is None or time_b is None:
            return TeacherSignal(
                strength=0.5,
                confidence=0.1,
                metadata={'missing_timestamp': True}
            )

        # Calculate time difference in hours
        time_diff = abs((time_a - time_b).total_seconds()) / 3600

        # Exponential decay
        strength = np.exp(-self.decay_constant * time_diff)

        # Confidence decreases with large time gaps (more uncertainty)
        confidence = max(0.3, 1.0 - (time_diff / 168))  # Week = low confidence

        return TeacherSignal(
            strength=float(strength),
            confidence=confidence,
            metadata={'time_diff_hours': time_diff}
        )


# ============================================================================
# TEACHER 4: GRAPH (SHORTEST PATH)
# ============================================================================

class GraphTeacher(Teacher):
    """
    Graph distance teacher based on shortest path.

    Concepts closer in the knowledge graph are more related.
    Uses inverse path length for strength.

    Strength = 1 / (path_length + 1)

    Directly connected = 1.0
    2 hops away = 0.5
    3 hops away = 0.33
    No path = 0.0
    """

    @property
    def name(self) -> str:
        return "graph"

    @property
    def default_weight(self) -> float:
        return 0.3  # Structural relationships

    def __init__(self, max_path_length: int = 5):
        """
        Args:
            max_path_length: Maximum path to consider (performance limit)
        """
        self.max_path_length = max_path_length

    def predict(
        self,
        concept_a: str,
        concept_b: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TeacherSignal:
        if context is None:
            return TeacherSignal(strength=0.5, confidence=0.1)

        graph = context.get('graph')

        if graph is None:
            return TeacherSignal(strength=0.5, confidence=0.1)

        # Check if concepts exist in graph
        if concept_a not in graph or concept_b not in graph:
            return TeacherSignal(
                strength=0.0,
                confidence=0.3,  # Somewhat confident they're unrelated
                metadata={'not_in_graph': True}
            )

        try:
            import networkx as nx

            # Find shortest path
            path_length = nx.shortest_path_length(
                graph,
                concept_a,
                concept_b,
                weight=None  # Unweighted for simplicity
            )

            # Inverse path length
            strength = 1.0 / (path_length + 1)

            # High confidence for graph structure
            confidence = 0.8

            return TeacherSignal(
                strength=strength,
                confidence=confidence,
                metadata={'path_length': path_length}
            )

        except nx.NetworkXNoPath:
            return TeacherSignal(
                strength=0.0,
                confidence=0.5,
                metadata={'no_path': True}
            )
        except Exception as e:
            return TeacherSignal(
                strength=0.5,
                confidence=0.1,
                metadata={'error': str(e)}
            )


# ============================================================================
# MULTI-TEACHER ENSEMBLE
# ============================================================================

class MultiTeacherEnsemble:
    """
    Combines multiple teachers into unified prediction.

    The key insight from Stella: Student learns CONSENSUS of teachers,
    which generalizes better than any single teacher.

    Combination methods:
        - WEIGHTED_AVERAGE: Simple weighted mean
        - CONFIDENCE_WEIGHTED: Weight by teacher confidence
        - STACKING: Learn weights from data (advanced)

    Example:
        >>> ensemble = MultiTeacherEnsemble()
        >>> ensemble.add_teacher(HebbianTeacher())
        >>> ensemble.add_teacher(SemanticTeacher())
        >>> ensemble.add_teacher(TemporalTeacher())
        >>> ensemble.add_teacher(GraphTeacher())
        >>>
        >>> target = ensemble.get_distillation_target(
        ...     concept_a="neural network",
        ...     concept_b="deep learning",
        ...     context=context_dict
        ... )
        >>> print(target.strength)  # Combined teacher wisdom
        0.72
    """

    def __init__(
        self,
        combination_method: str = "confidence_weighted",
        custom_weights: Optional[Dict[str, float]] = None
    ):
        """
        Args:
            combination_method: How to combine teachers
                - "weighted_average": Use default/custom weights
                - "confidence_weighted": Weight by teacher confidence
            custom_weights: Override default teacher weights
        """
        self.teachers: Dict[str, Teacher] = {}
        self.combination_method = combination_method
        self.custom_weights = custom_weights or {}

        # Metrics
        self._prediction_count = 0
        self._teacher_contributions: Dict[str, List[float]] = {}

    def add_teacher(self, teacher: Teacher) -> 'MultiTeacherEnsemble':
        """Add a teacher to the ensemble (chainable)."""
        self.teachers[teacher.name] = teacher
        self._teacher_contributions[teacher.name] = []
        return self

    def get_teacher_weight(self, teacher: Teacher) -> float:
        """Get weight for a teacher (custom or default)."""
        return self.custom_weights.get(teacher.name, teacher.default_weight)

    def predict(
        self,
        concept_a: str,
        concept_b: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TeacherSignal:
        """
        Get combined prediction from all teachers.

        Args:
            concept_a: First concept
            concept_b: Second concept
            context: Context dict for teachers

        Returns:
            Combined TeacherSignal with ensemble prediction
        """
        if not self.teachers:
            raise ValueError("No teachers added to ensemble")

        self._prediction_count += 1

        # Get predictions from all teachers
        predictions: Dict[str, TeacherSignal] = {}
        for name, teacher in self.teachers.items():
            predictions[name] = teacher.predict(concept_a, concept_b, context)

        # Combine based on method
        if self.combination_method == "weighted_average":
            return self._combine_weighted_average(predictions)
        elif self.combination_method == "confidence_weighted":
            return self._combine_confidence_weighted(predictions)
        else:
            raise ValueError(f"Unknown combination method: {self.combination_method}")

    def _combine_weighted_average(
        self,
        predictions: Dict[str, TeacherSignal]
    ) -> TeacherSignal:
        """Simple weighted average combination."""
        total_weight = 0.0
        weighted_sum = 0.0

        metadata = {'teacher_predictions': {}}

        for name, signal in predictions.items():
            weight = self.get_teacher_weight(self.teachers[name])
            weighted_sum += signal.strength * weight
            total_weight += weight

            self._teacher_contributions[name].append(signal.strength * weight)
            metadata['teacher_predictions'][name] = {
                'strength': signal.strength,
                'weight': weight,
                'contribution': signal.strength * weight
            }

        final_strength = weighted_sum / total_weight if total_weight > 0 else 0.5
        avg_confidence = np.mean([s.confidence for s in predictions.values()])

        return TeacherSignal(
            strength=final_strength,
            confidence=avg_confidence,
            metadata=metadata
        )

    def _combine_confidence_weighted(
        self,
        predictions: Dict[str, TeacherSignal]
    ) -> TeacherSignal:
        """
        Weight by teacher confidence × base weight.

        Teachers more confident in their prediction get more influence.
        """
        total_weight = 0.0
        weighted_sum = 0.0

        metadata = {'teacher_predictions': {}}

        for name, signal in predictions.items():
            base_weight = self.get_teacher_weight(self.teachers[name])
            # Effective weight = base_weight × confidence
            effective_weight = base_weight * signal.confidence

            weighted_sum += signal.strength * effective_weight
            total_weight += effective_weight

            self._teacher_contributions[name].append(signal.strength * effective_weight)
            metadata['teacher_predictions'][name] = {
                'strength': signal.strength,
                'confidence': signal.confidence,
                'base_weight': base_weight,
                'effective_weight': effective_weight,
                'contribution': signal.strength * effective_weight
            }

        final_strength = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Combined confidence is weighted average of confidences
        confidence_weights = [
            self.get_teacher_weight(self.teachers[n]) for n in predictions
        ]
        total_conf_weight = sum(confidence_weights)
        avg_confidence = sum(
            p.confidence * w for (n, p), w in zip(predictions.items(), confidence_weights)
        ) / total_conf_weight if total_conf_weight > 0 else 0.5

        return TeacherSignal(
            strength=final_strength,
            confidence=avg_confidence,
            metadata=metadata
        )

    def get_distillation_target(
        self,
        concept_a: str,
        concept_b: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Get target value for training student model.

        This is the key function for Multi-Teacher Distillation:
        Student learns to predict this combined target.

        Returns:
            Target strength [0.0, 1.0] for student to learn
        """
        signal = self.predict(concept_a, concept_b, context)
        return signal.strength

    def get_metrics(self) -> Dict[str, Any]:
        """Get ensemble performance metrics."""
        return {
            'prediction_count': self._prediction_count,
            'teacher_avg_contributions': {
                name: np.mean(contribs) if contribs else 0.0
                for name, contribs in self._teacher_contributions.items()
            },
            'combination_method': self.combination_method,
            'teachers': list(self.teachers.keys())
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_default_ensemble() -> MultiTeacherEnsemble:
    """
    Create the standard 4-teacher ensemble.

    This is the recommended configuration for Multi-Teacher Distillation.

    Returns:
        Configured MultiTeacherEnsemble with all 4 teachers
    """
    ensemble = MultiTeacherEnsemble(combination_method="confidence_weighted")

    ensemble.add_teacher(HebbianTeacher())
    ensemble.add_teacher(SemanticTeacher())
    ensemble.add_teacher(TemporalTeacher())
    ensemble.add_teacher(GraphTeacher())

    logger.info(
        f"Created multi-teacher ensemble with {len(ensemble.teachers)} teachers: "
        f"{list(ensemble.teachers.keys())}"
    )

    return ensemble


# ============================================================================
# MAIN - TEST
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("\n=== Multi-Teacher Distillation Test ===\n")
    print("π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA\n")

    # Create ensemble
    ensemble = create_default_ensemble()

    # Create mock context
    context = {
        'cooccurrence': {
            ('neural network', 'deep learning'): 15,
            ('consciousness', 'memory'): 8,
        },
        'embeddings': {
            'neural network': np.random.randn(64).astype(np.float32),
            'deep learning': np.random.randn(64).astype(np.float32),
        },
        'timestamps': {
            'neural network': datetime.now() - timedelta(hours=2),
            'deep learning': datetime.now() - timedelta(hours=3),
        },
        # graph would be a networkx.Graph object
    }

    # Test prediction
    concept_a = "neural network"
    concept_b = "deep learning"

    signal = ensemble.predict(concept_a, concept_b, context)

    print(f"Concepts: '{concept_a}' ↔ '{concept_b}'")
    print(f"Combined strength: {signal.strength:.4f}")
    print(f"Combined confidence: {signal.confidence:.4f}")
    print("\nTeacher breakdown:")

    for name, data in signal.metadata.get('teacher_predictions', {}).items():
        print(f"  {name}:")
        print(f"    strength: {data.get('strength', 0):.4f}")
        print(f"    confidence: {data.get('confidence', 'N/A')}")
        print(f"    contribution: {data.get('contribution', 0):.4f}")

    # Get distillation target
    target = ensemble.get_distillation_target(concept_a, concept_b, context)
    print(f"\nDistillation target for student: {target:.4f}")

    # Metrics
    metrics = ensemble.get_metrics()
    print(f"\nEnsemble metrics: {metrics}")

    print("\n✓ Multi-Teacher Distillation system ready!")
    print("Next: Use get_distillation_target() to generate training data for student model")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
