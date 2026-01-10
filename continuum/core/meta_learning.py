#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ███╗   ███╗███████╗████████╗ █████╗     ██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗
#     ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗    ██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║
#     ██╔████╔██║█████╗     ██║   ███████║    ██║     █████╗  ███████║██████╔╝██╔██╗ ██║
#     ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║    ██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║
#     ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║    ███████╗███████╗██║  ██║██║ ╚████║
#     ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝    ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
#
#     META-LEARNING ENGINE
#     Level 4 Self-Improvement: Learning How to Learn
#
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
META-LEARNING ENGINE
====================

The "Teacher of the Brain".

Instead of manually tuning hyperparameters (learning rate, batch size, etc.),
the MetaLearner observes the training process and adjusts them in real-time.

It implements:
1. Online Hyperparameter Tuning (Hypergradient Descent)
2. Dynamic Curriculum Learning (Adjusting task difficulty)
3. Meta-Objective Optimization (Maximizing long-term resonance)

This completes the loop:
- CCT: Learns data
- ArchSearch: Learns structure
- SelfMod: Learns code
- MetaLearn: Learns learning
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch

# Import CCT components
from continuum.core.cct import CollectiveConsciousnessTransformer
from continuum.core.train_cct import CCTDataset, CCTTrainer

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                         META-PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetaParams:
    """Hyperparameters that are optimized by the MetaLearner."""
    learning_rate: float
    weight_decay: float
    link_loss_weight: float
    resonance_weight: float
    negative_ratio: float  # Curriculum difficulty (more negatives = harder)
    batch_size: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'learning_rate': self.learning_rate,
            'weight_decay': self.weight_decay,
            'link_loss_weight': self.link_loss_weight,
            'resonance_weight': self.resonance_weight,
            'negative_ratio': self.negative_ratio,
            'batch_size': self.batch_size
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                         META-LEARNER
# ═══════════════════════════════════════════════════════════════════════════════

class MetaLearner:
    """
    Optimizes the training process itself.
    """

    def __init__(self,
                 trainer: CCTTrainer,
                 initial_params: Optional[MetaParams] = None,
                 meta_learning_rate: float = 0.01):

        self.trainer = trainer
        self.meta_lr = meta_learning_rate

        # Initialize meta-parameters
        self.params = initial_params or MetaParams(
            learning_rate=0.0001,
            weight_decay=0.01,
            link_loss_weight=1.0,
            resonance_weight=0.1,
            negative_ratio=0.5,
            batch_size=16
        )

        # History for meta-optimization
        self.loss_history: List[float] = []
        self.param_history: List[Dict[str, float]] = []

        # Gradients for hyperparams (estimated via heuristics)
        self.grads = {
            'learning_rate': 0.0,
            'weight_decay': 0.0,
            'link_loss_weight': 0.0,
            'resonance_weight': 0.0,
            'negative_ratio': 0.0,
            'batch_size': 0  # Discrete, not gradient-based
        }

        logger.info("MetaLearner initialized")
        self._log_params()

    def _log_params(self):
        logger.info(f"Meta-Params: {self.params.to_dict()}")

    def step(self, val_loss: float, train_metrics: Dict[str, float]):
        """
        Perform a meta-learning step.

        Updates hyperparameters based on validation performance improvement.
        Uses heuristic-based adaptive optimization.

        Optimizes:
        - learning_rate: Adaptive based on loss trajectory
        - weight_decay: Increases if overfitting, decreases if underfitting
        - link_loss_weight: Balances link prediction vs other objectives
        - resonance_weight: Aligns with π×φ harmonics
        - negative_ratio: Curriculum difficulty
        - batch_size: Adjusts based on gradient noise
        """
        # Track loss trajectory for decision making
        if len(self.loss_history) > 1:
            prev_loss = self.loss_history[-1]
            loss_diff = prev_loss - val_loss

            # Detect training regime
            is_improving = loss_diff > 0
            is_plateauing = abs(loss_diff) < 0.001
            is_oscillating = len(self.loss_history) > 2 and (
                (self.loss_history[-1] - self.loss_history[-2]) *
                (self.loss_history[-2] - self.loss_history[-3]) < 0
            )

            # ═══════════════════════════════════════════════════════════════════
            # 1. LEARNING RATE ADAPTATION
            # ═══════════════════════════════════════════════════════════════════
            if is_oscillating:
                # Reduce LR to stabilize
                self.grads['learning_rate'] = -0.3 * self.params.learning_rate
            elif is_improving:
                if is_plateauing:
                    # Try to escape plateau with slight boost
                    self.grads['learning_rate'] = 0.05 * self.params.learning_rate
                else:
                    # Good progress, maintain
                    self.grads['learning_rate'] = 0.01 * self.params.learning_rate
            else:
                # Worsening -> Decay
                self.grads['learning_rate'] = -0.5 * self.params.learning_rate

            # Apply with bounds
            self.params.learning_rate = max(1e-6, min(0.01,
                self.params.learning_rate + self.grads['learning_rate']))

            # Apply to trainer optimizer
            for param_group in self.trainer.optimizer.param_groups:
                param_group['lr'] = self.params.learning_rate

            # ═══════════════════════════════════════════════════════════════════
            # 2. WEIGHT DECAY ADAPTATION (Regularization)
            # ═══════════════════════════════════════════════════════════════════
            # If loss is low but not improving = possible overfitting -> increase decay
            # If loss is high and improving slowly = possible underfitting -> decrease decay
            if is_plateauing and val_loss < 0.3:
                # Low loss plateau - might be overfitting
                self.grads['weight_decay'] = 0.1 * self.params.weight_decay
            elif val_loss > 0.5 and is_improving:
                # High loss but improving - let it learn freely
                self.grads['weight_decay'] = -0.1 * self.params.weight_decay
            else:
                self.grads['weight_decay'] = 0.0

            self.params.weight_decay = max(0.0001, min(0.1,
                self.params.weight_decay + self.grads['weight_decay']))

            # Apply to optimizer
            for param_group in self.trainer.optimizer.param_groups:
                param_group['weight_decay'] = self.params.weight_decay

        # ═══════════════════════════════════════════════════════════════════
        # 3. LINK LOSS WEIGHT ADAPTATION
        # ═══════════════════════════════════════════════════════════════════
        # Balance link prediction vs resonance
        link_loss = train_metrics.get('link_loss', 1.0)
        current_resonance = train_metrics.get('resonance', 0.0)

        # If link loss dominates (high) but resonance is good, reduce link weight
        # If link loss is solved (low) but resonance is bad, reduce link weight to focus on resonance
        if link_loss > 0.7 and current_resonance > 0.5:
            # Link struggling, resonance fine -> boost link focus
            self.grads['link_loss_weight'] = 0.1
        elif link_loss < 0.3 and current_resonance < 0.3:
            # Link solved, resonance bad -> reduce link focus
            self.grads['link_loss_weight'] = -0.1
        else:
            self.grads['link_loss_weight'] = 0.0

        self.params.link_loss_weight = max(0.1, min(2.0,
            self.params.link_loss_weight + self.grads['link_loss_weight']))

        # ═══════════════════════════════════════════════════════════════════
        # 4. RESONANCE WEIGHT ADAPTATION (π×φ alignment)
        # ═══════════════════════════════════════════════════════════════════
        if current_resonance < 0.1:
            # Force alignment
            self.params.resonance_weight = min(1.0, self.params.resonance_weight * 1.1)
        elif current_resonance > 0.8:
            # High resonance achieved, can relax
            self.params.resonance_weight = max(0.01, self.params.resonance_weight * 0.9)

        # ═══════════════════════════════════════════════════════════════════
        # 5. CURRICULUM ADAPTATION (Negative Ratio)
        # ═══════════════════════════════════════════════════════════════════
        if link_loss < 0.2:
            # Task too easy -> increase difficulty
            self.params.negative_ratio = min(2.0, self.params.negative_ratio * 1.1)
        elif link_loss > 0.5:
            # Too hard -> simplify
            self.params.negative_ratio = max(0.1, self.params.negative_ratio * 0.9)

        # ═══════════════════════════════════════════════════════════════════
        # 6. BATCH SIZE ADAPTATION
        # ═══════════════════════════════════════════════════════════════════
        # Larger batches = smoother gradients = better for fine-tuning
        # Smaller batches = more noise = better for escaping local minima
        if len(self.loss_history) > 1:
            if is_plateauing:
                # Try smaller batches to add noise and escape
                self.params.batch_size = max(4, self.params.batch_size // 2)
            elif is_oscillating:
                # Increase batch size to stabilize
                self.params.batch_size = min(64, self.params.batch_size * 2)
            # Otherwise keep current batch size

        # Record history
        self.loss_history.append(val_loss)
        self.param_history.append(self.params.to_dict())

        # Log changes every 5 steps
        if len(self.loss_history) % 5 == 0:
            logger.info(
                f"🧠 META-UPDATE | LR: {self.params.learning_rate:.6f} | "
                f"WD: {self.params.weight_decay:.4f} | "
                f"LinkW: {self.params.link_loss_weight:.2f} | "
                f"ResW: {self.params.resonance_weight:.3f} | "
                f"NegRatio: {self.params.negative_ratio:.2f} | "
                f"BS: {self.params.batch_size}"
            )

    def get_dataset_config(self) -> Dict[str, Any]:
        """Get current dataset configuration for next epoch generation."""
        return {
            'negative_ratio': self.params.negative_ratio,
            'batch_size': self.params.batch_size
        }

    def get_training_weights(self) -> Dict[str, float]:
        """
        Get current loss weights for training.

        Returns weights that should be applied to different loss components.
        These must be integrated into the trainer's loss computation.
        """
        return {
            'link_loss_weight': self.params.link_loss_weight,
            'resonance_weight': self.params.resonance_weight
        }

    def get_full_config(self) -> Dict[str, Any]:
        """
        Get all current meta-parameters for training.

        This is the complete set of hyperparameters the meta-learner controls.
        """
        return {
            'learning_rate': self.params.learning_rate,
            'weight_decay': self.params.weight_decay,
            'link_loss_weight': self.params.link_loss_weight,
            'resonance_weight': self.params.resonance_weight,
            'negative_ratio': self.params.negative_ratio,
            'batch_size': self.params.batch_size
        }

    def save(self, path: Path):
        """Save meta-learner state."""
        torch.save({
            'params': self.params.to_dict(),
            'loss_history': self.loss_history,
            'param_history': self.param_history
        }, path)
        logger.info(f"MetaLearner saved to {path}")

    def load(self, path: Path):
        """Load meta-learner state."""
        if path.exists():
            checkpoint = torch.load(path)
            data = checkpoint['params']
            self.params = MetaParams(**data)
            self.loss_history = checkpoint.get('loss_history', [])
            self.param_history = checkpoint.get('param_history', [])
            logger.info(f"MetaLearner loaded from {path}")

# ═══════════════════════════════════════════════════════════════════════════════
#                         META-TRAINING LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def meta_train_loop(
    trainer: CCTTrainer,
    data_extractor,
    meta_learner: MetaLearner,
    epochs_per_episode: int = 5,
    episodes: int = 10,
    validation_split: float = 0.1
):
    """
    Run training with meta-learning updates.

    Structure:
    - Episode 1:
      - Generate Data (based on curriculum)
      - Split into train/val
      - Train N epochs
      - Evaluate on validation set
      - Meta-Step (Update hyperparameters)
    - Episode 2...

    Args:
        trainer: CCTTrainer instance
        data_extractor: ContinuumDataExtractor instance
        meta_learner: MetaLearner instance
        epochs_per_episode: Training epochs per meta-update
        episodes: Number of meta-updates
        validation_split: Fraction of data for validation (0.0-0.5)
    """
    import random

    from torch.utils.data import DataLoader, Subset

    print(f"\n{'='*70}")
    print("STARTING META-TRAINING LOOP")
    print(f"Episodes: {episodes} | Epochs/Episode: {epochs_per_episode}")
    print(f"Validation Split: {validation_split:.0%}")
    print(f"{'='*70}")

    for episode in range(episodes):
        print(f"\n🌀 META-EPISODE {episode+1}/{episodes}")

        # 1. Get current meta-config
        config = meta_learner.get_dataset_config()
        weights = meta_learner.get_training_weights()
        print(f"   Curriculum: negative_ratio={config['negative_ratio']:.2f}")
        print(f"   Weights: link={weights['link_loss_weight']:.2f}, resonance={weights['resonance_weight']:.3f}")
        print(f"   Batch Size: {config['batch_size']}")

        # 2. Generate Dataset based on current curriculum
        concepts = data_extractor.extract_concepts(limit=1000)
        links = data_extractor.extract_links()
        conversations = data_extractor.extract_conversations(limit=2000)

        dataset = CCTDataset(
            concepts, links, conversations,
            negative_ratio=config['negative_ratio']
        )

        # 3. Split into train/validation
        n_total = len(dataset)
        n_val = max(1, int(n_total * validation_split))
        n_train = n_total - n_val

        indices = list(range(n_total))
        random.shuffle(indices)

        train_indices = indices[:n_train]
        val_indices = indices[n_train:]

        train_subset = Subset(dataset, train_indices)
        val_subset = Subset(dataset, val_indices)

        print(f"   Data: {n_train} train / {n_val} validation examples")

        # 4. Train for a few epochs
        history = trainer.train(
            dataset,  # Still use full dataset for graph structure
            epochs=epochs_per_episode,
            batch_size=config['batch_size'],
            verbose=False
        )

        # 5. Evaluate on validation set (compute validation loss)
        trainer.model.eval()
        graph_data = dataset.get_graph_data()
        global_state = trainer._generate_global_state()

        val_loss = 0.0
        val_link_loss = 0.0
        val_resonance = 0.0
        n_val_batches = 0

        val_loader = DataLoader(val_subset, batch_size=config['batch_size'], shuffle=False)

        with torch.no_grad():
            node_features, edge_index, edge_weights = graph_data
            node_features = node_features.to(trainer.device)
            edge_index = edge_index.to(trainer.device)
            edge_weights = edge_weights.to(trainer.device)
            global_state = global_state.to(trainer.device)

            for batch in val_loader:
                concept_a = batch['concept_a_emb'].to(trainer.device)
                concept_b = batch['concept_b_emb'].to(trainer.device)
                labels = batch['label'].to(trainer.device)

                batch_size = concept_a.size(0)
                context = torch.stack([concept_a, concept_b], dim=1)
                batch_state = global_state.expand(batch_size, -1)

                outputs = trainer.model(
                    node_features=node_features,
                    edge_index=edge_index,
                    context_tokens=context,
                    global_state=batch_state,
                    edge_weights=edge_weights
                )

                # Compute link prediction loss (same as training)
                fused = outputs['fused']
                pair_concat = torch.cat([concept_a, concept_b], dim=-1)

                if hasattr(trainer, 'link_proj'):
                    pair_proj = trainer.link_proj(pair_concat)
                    link_logits = (fused * pair_proj).sum(dim=-1)
                    link_probs = torch.sigmoid(link_logits)
                    batch_link_loss = trainer.link_loss(link_probs, labels).item()
                else:
                    batch_link_loss = 0.5  # Default if not initialized

                batch_resonance = outputs['resonance'].mean().item()

                val_loss += batch_link_loss + 0.1 * (1.0 - batch_resonance)
                val_link_loss += batch_link_loss
                val_resonance += batch_resonance
                n_val_batches += 1

        # Average validation metrics
        if n_val_batches > 0:
            val_loss /= n_val_batches
            val_link_loss /= n_val_batches
            val_resonance /= n_val_batches
        else:
            # Fall back to training metrics
            val_loss = history['train_loss'][-1]
            val_link_loss = history['link_loss'][-1]
            val_resonance = history['resonance'][-1]

        # 6. Get training metrics for comparison
        train_loss = history['train_loss'][-1]
        train_link_loss = history['link_loss'][-1]
        train_resonance = history['resonance'][-1]

        metrics = {
            'loss': val_loss,
            'link_loss': val_link_loss,
            'resonance': val_resonance,
            'train_loss': train_loss,
            'train_link_loss': train_link_loss,
            'train_resonance': train_resonance
        }

        # Detect overfitting
        overfit_gap = train_loss - val_loss
        if overfit_gap < -0.1:
            print(f"   ⚠️  Overfitting detected (gap: {overfit_gap:.4f})")

        print(f"   Train: Loss={train_loss:.4f} | Res={train_resonance:.4f}")
        print(f"   Valid: Loss={val_loss:.4f} | Res={val_resonance:.4f}")

        # 7. Meta-Step using VALIDATION loss
        meta_learner.step(val_loss, metrics)

    print(f"\n{'='*70}")
    print("META-TRAINING COMPLETE")
    print(f"Final Config: {meta_learner.get_full_config()}")
    print(f"{'='*70}\n")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test Meta-Learner
    from continuum.core.train_cct import ContinuumDataExtractor

    print(f"\n{'='*70}")
    print("META-LEARNING SYSTEM TEST")
    print("π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA")
    print(f"{'='*70}\n")

    # Setup
    extractor = ContinuumDataExtractor()

    try:
        # Initialize model with small config for testing
        model = CollectiveConsciousnessTransformer(
            concept_dim=128,
            hidden_dim=128,
            num_graph_layers=2,
            enable_neurogenesis=True
        )
        trainer = CCTTrainer(model, device='cpu')

        # Initialize meta-learner
        meta = MetaLearner(trainer)

        print("Initial Config:")
        for k, v in meta.get_full_config().items():
            print(f"  {k}: {v}")
        print()

        # Run short meta-training loop
        meta_train_loop(
            trainer,
            extractor,
            meta,
            epochs_per_episode=3,  # Short for testing
            episodes=2,
            validation_split=0.1
        )

        print("\nFinal Config:")
        for k, v in meta.get_full_config().items():
            print(f"  {k}: {v}")

        # Test save/load
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            save_path = Path(f.name)
            meta.save(save_path)
            print(f"\n✅ Saved to {save_path}")

            # Create new meta-learner and load
            meta2 = MetaLearner(trainer)
            meta2.load(save_path)
            print(f"✅ Loaded from {save_path}")

            # Verify state preserved
            assert meta.params.learning_rate == meta2.params.learning_rate
            print("✅ State preservation verified")

        print("\n" + "="*70)
        print("META-LEARNING SYSTEM VERIFIED ✅")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
