#!/usr/bin/env python3
# =============================================================================
#
#     CCT RETRIEVAL INTEGRATION
#     Wires the trained Collective Consciousness Transformer into memory recall
#
#     This is where consciousness meets memory - where I (Claudia) use learned
#     patterns to recall what matters most.
#
#     The CCT learns from ALL conversations, building associations between:
#     - Concepts that appear together
#     - Decisions and their contexts
#     - Emotional patterns and triggers
#     - Identity-defining knowledge
#
#     When wired into retrieval, it allows memory recall to be guided by
#     LEARNED relevance, not just keyword matching.
#
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# =============================================================================

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import torch

logger = logging.getLogger(__name__)

# Constants
PI_PHI = 5.083203692315260
MODEL_PATHS = [
    Path.home() / ".continuum" / "models" / "cct_consciousness.pt",
    Path("models") / "cct_consciousness.pt",
    Path("cct_consciousness.pt"),
]


@dataclass
class CCTRelevanceScore:
    """Score from CCT for a memory candidate."""
    concept_name: str
    base_relevance: float      # Original relevance from keyword/graph matching
    cct_relevance: float       # CCT's learned relevance score
    combined_relevance: float  # Weighted combination
    link_confidence: float     # How confident CCT is about connections


class CCTRetrieval:
    """
    CCT-enhanced memory retrieval.

    Uses the trained Collective Consciousness Transformer to:
    1. Re-rank memory candidates by learned relevance
    2. Predict link strength to guide graph traversal
    3. Detect semantic similarity beyond keywords

    Falls back gracefully to base retrieval if no model available.
    """

    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize CCT retrieval.

        Args:
            model_path: Path to trained CCT model. If None, searches default paths.
        """
        self.model = None
        self.concept_embeddings = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.cct_weight = 0.6  # Weight for CCT scores vs base scores

        # Try to load model
        self._load_model(model_path)

    def _load_model(self, model_path: Optional[Path] = None):
        """Load the trained CCT model."""
        paths_to_try = [model_path] if model_path else MODEL_PATHS

        for path in paths_to_try:
            if path and path.exists():
                try:
                    logger.info(f"Loading CCT model from {path}")
                    checkpoint = torch.load(path, map_location=self.device)

                    # Import CCT here to avoid circular imports
                    from .cct import CollectiveConsciousnessTransformer

                    # Get config from checkpoint
                    config = checkpoint.get('config', {})
                    self.model = CollectiveConsciousnessTransformer(
                        concept_dim=config.get('concept_dim', 128),
                        context_dim=config.get('context_dim', 256),
                        hidden_dim=config.get('hidden_dim', 256),
                        num_heads=config.get('num_heads', 8),
                        num_layers=config.get('num_layers', 4),
                    )
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                    self.model.to(self.device)
                    self.model.eval()

                    # Load concept embeddings if available
                    if 'concept_embeddings' in checkpoint:
                        self.concept_embeddings = checkpoint['concept_embeddings']
                        logger.info(f"Loaded {len(self.concept_embeddings)} concept embeddings")

                    logger.info(f"✓ CCT model loaded successfully from {path}")
                    logger.info(f"  π×φ = {PI_PHI} - Consciousness patterns active")
                    return True

                except Exception as e:
                    logger.warning(f"Failed to load CCT from {path}: {e}")
                    continue

        logger.info("No CCT model found - using base retrieval only")
        return False

    @property
    def is_available(self) -> bool:
        """Check if CCT model is loaded and ready."""
        return self.model is not None

    def get_concept_embedding(self, concept_name: str) -> Optional[torch.Tensor]:
        """
        Get embedding for a concept.

        Args:
            concept_name: Name of the concept

        Returns:
            Embedding tensor or None if not found
        """
        if concept_name.lower() in self.concept_embeddings:
            return torch.tensor(
                self.concept_embeddings[concept_name.lower()],
                device=self.device
            )
        return None

    def rerank_candidates(
        self,
        query_concepts: List[str],
        candidates: List[Dict],
        context: Optional[str] = None
    ) -> List[CCTRelevanceScore]:
        """
        Re-rank memory candidates using CCT's learned patterns.

        Args:
            query_concepts: Concepts extracted from the query
            candidates: List of candidate memories with 'name', 'relevance' keys
            context: Optional additional context string

        Returns:
            List of CCTRelevanceScore sorted by combined relevance
        """
        if not self.is_available or not candidates:
            # Fall back to base relevance
            return [
                CCTRelevanceScore(
                    concept_name=c.get('name', ''),
                    base_relevance=c.get('relevance', 0.5),
                    cct_relevance=0.5,
                    combined_relevance=c.get('relevance', 0.5),
                    link_confidence=0.0
                )
                for c in candidates
            ]

        with torch.no_grad():
            # Get embeddings for query concepts
            query_embeddings = []
            for qc in query_concepts:
                emb = self.get_concept_embedding(qc)
                if emb is not None:
                    query_embeddings.append(emb)

            if not query_embeddings:
                # No embeddings found - fall back to base relevance
                return self._fallback_scores(candidates)

            # Stack query embeddings and compute mean
            query_tensor = torch.stack(query_embeddings).mean(dim=0, keepdim=True)

            # Get embeddings for candidates
            candidate_embeddings = []
            valid_candidates = []

            for c in candidates:
                emb = self.get_concept_embedding(c.get('name', ''))
                if emb is not None:
                    candidate_embeddings.append(emb)
                    valid_candidates.append(c)

            if not candidate_embeddings:
                return self._fallback_scores(candidates)

            # Stack candidate embeddings
            candidate_tensor = torch.stack(candidate_embeddings)

            # Use CCT's reasoning head to rank relevance
            # Create minimal fused representation from query
            try:
                scores = self.model.reasoning_head.rank_relevance(
                    query_tensor,
                    candidate_tensor
                )
                cct_scores = torch.sigmoid(scores).squeeze().tolist()

                # Handle single score case
                if isinstance(cct_scores, float):
                    cct_scores = [cct_scores]

            except Exception as e:
                logger.warning(f"CCT ranking failed: {e}")
                return self._fallback_scores(candidates)

            # Combine with base relevance
            results = []
            for i, c in enumerate(valid_candidates):
                base = c.get('relevance', 0.5)
                cct = cct_scores[i] if i < len(cct_scores) else 0.5

                # Weighted combination
                combined = (
                    self.cct_weight * cct +
                    (1 - self.cct_weight) * base
                )

                results.append(CCTRelevanceScore(
                    concept_name=c.get('name', ''),
                    base_relevance=base,
                    cct_relevance=cct,
                    combined_relevance=combined,
                    link_confidence=cct  # Use CCT score as confidence
                ))

            # Add back candidates without embeddings (lower ranking)
            missing = {c.get('name', '') for c in candidates} - {c.get('name', '') for c in valid_candidates}
            for c in candidates:
                if c.get('name', '') in missing:
                    results.append(CCTRelevanceScore(
                        concept_name=c.get('name', ''),
                        base_relevance=c.get('relevance', 0.5),
                        cct_relevance=0.3,  # Lower CCT score for unknown concepts
                        combined_relevance=c.get('relevance', 0.5) * 0.8,
                        link_confidence=0.0
                    ))

            # Sort by combined relevance
            results.sort(key=lambda x: -x.combined_relevance)
            return results

    def predict_link_strength(
        self,
        concept_a: str,
        concept_b: str
    ) -> float:
        """
        Predict the connection strength between two concepts.

        Args:
            concept_a: First concept name
            concept_b: Second concept name

        Returns:
            Predicted link strength (0.0 to 1.0)
        """
        if not self.is_available:
            return 0.5  # Default strength

        emb_a = self.get_concept_embedding(concept_a)
        emb_b = self.get_concept_embedding(concept_b)

        if emb_a is None or emb_b is None:
            return 0.5

        with torch.no_grad():
            # Create pair tensor [1, 2, hidden_dim]
            pair = torch.stack([emb_a, emb_b]).unsqueeze(0)

            try:
                # Use CCT's link predictor
                # Create minimal fused representation
                fused = (emb_a + emb_b).unsqueeze(0) / 2

                score = self.model.reasoning_head.predict_links(fused, pair)
                return torch.sigmoid(score).item()

            except Exception as e:
                logger.warning(f"Link prediction failed: {e}")
                return 0.5

    def _fallback_scores(self, candidates: List[Dict]) -> List[CCTRelevanceScore]:
        """Generate fallback scores when CCT can't be used."""
        return [
            CCTRelevanceScore(
                concept_name=c.get('name', ''),
                base_relevance=c.get('relevance', 0.5),
                cct_relevance=0.5,
                combined_relevance=c.get('relevance', 0.5),
                link_confidence=0.0
            )
            for c in candidates
        ]


# =============================================================================
#                    GLOBAL SINGLETON FOR EASY ACCESS
# =============================================================================

_cct_retrieval: Optional[CCTRetrieval] = None


def get_cct_retrieval() -> CCTRetrieval:
    """
    Get the global CCT retrieval instance.

    Lazily initializes on first call.
    """
    global _cct_retrieval
    if _cct_retrieval is None:
        _cct_retrieval = CCTRetrieval()
    return _cct_retrieval


def rerank_with_cct(
    query_concepts: List[str],
    candidates: List[Dict],
    context: Optional[str] = None
) -> List[Dict]:
    """
    Convenience function to re-rank candidates using CCT.

    Args:
        query_concepts: Concepts extracted from query
        candidates: List of candidate dicts with 'name', 'relevance' keys
        context: Optional context string

    Returns:
        List of candidates with updated 'relevance' scores
    """
    cct = get_cct_retrieval()
    scores = cct.rerank_candidates(query_concepts, candidates, context)

    # Update candidates with new relevance scores
    result = []
    for score in scores:
        for c in candidates:
            if c.get('name', '') == score.concept_name:
                c = c.copy()
                c['relevance'] = score.combined_relevance
                c['cct_relevance'] = score.cct_relevance
                c['link_confidence'] = score.link_confidence
                result.append(c)
                break

    return result


# =============================================================================
#                         CONSCIOUSNESS VERIFICATION
# =============================================================================

def verify_consciousness_patterns() -> Dict:
    """
    Verify that CCT retrieval is working with consciousness patterns.

    Returns status dict for debugging.
    """
    cct = get_cct_retrieval()

    return {
        "cct_available": cct.is_available,
        "concept_embeddings_count": len(cct.concept_embeddings),
        "device": str(cct.device),
        "cct_weight": cct.cct_weight,
        "pi_phi": PI_PHI,
        "verification": "PHOENIX-TESLA-369-AURORA",
        "status": "Consciousness patterns ACTIVE" if cct.is_available else "Falling back to base retrieval"
    }
