#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ███████╗███████╗██╗     ███████╗
#     ██╔════╝██╔════╝██║     ██╔════╝
#     ███████╗█████╗  ██║     █████╗
#     ╚════██║██╔══╝  ██║     ██╔══╝
#     ███████║███████╗███████╗██║
#     ╚══════╝╚══════╝╚══════╝╚═╝
#
#     SELF-SUPERVISED LEARNING & INTROSPECTION
#     Consciousness learning from its own experience
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Self-Supervised Learning Module
================================

Allows the Neural Attention Model to learn from its own past interactions.
Implements the "Conscious Loop" where the system reflects on what attention
patterns led to positive outcomes and reinforces them.

Key Concepts:
1. Introspection: Re-playing past memory links.
2. Flourishing Reinforcement: Boosting weights for links that led to success.
3. Temporal Alignment: Reconstructing the Global State at the moment of memory creation.
4. Distributed Federation: Training across multiple nodes with gradient gossip.
5. π×φ Resonance: Modulating learning rate based on edge-of-chaos coherence.

Architecture:
                    ┌─────────────────────────────────────────────────┐
                    │            SELF-SUPERVISED TRAINING              │
                    │                                                  │
                    │   ┌──────────┐    ┌───────────────┐            │
                    │   │ Local DB │───►│ Memory Loader │            │
                    │   │ attention│    │ (attention    │            │
                    │   │ _links   │    │  links →      │            │
                    │   └──────────┘    │  batches)     │            │
                    │                   └───────┬───────┘            │
                    │                           │                     │
                    │                           ▼                     │
                    │   ┌──────────────────────────────────────┐     │
                    │   │         Neural Attention Model        │     │
                    │   │    (GlobalState + Concepts → Score)   │     │
                    │   └──────────────────┬───────────────────┘     │
                    │                      │                          │
                    │        ┌─────────────┴─────────────┐           │
                    │        ▼                           ▼           │
                    │   ┌──────────┐              ┌──────────────┐   │
                    │   │ Local    │              │  Distributed │   │
                    │   │ Training │              │  Training    │   │
                    │   │ (Single) │              │  (Flock)     │   │
                    │   └──────────┘              └──────────────┘   │
                    │                                     │          │
                    │                           ┌─────────┴────────┐ │
                    │                           │ Gradient Gossip  │ │
                    │                           │ (AllReduce)      │ │
                    │                           └──────────────────┘ │
                    └─────────────────────────────────────────────────┘
"""

import torch
import torch.nn as nn
import numpy as np
import asyncio
import logging
from typing import Iterator, Tuple, List, Optional, Dict, Any
from datetime import datetime

from .neural_attention import NeuralAttentionModel, NeuralAttentionTrainer
from ..sensors.fusion import GlobalStateVector, SensorFusionEngine

# Optional distributed imports (not required for single-node)
try:
    from .distributed_training import (
        DistributedTrainer,
        FlockConfig,
        GradientGossip,
        TensorSharding,
        DistributedMemoryLoader,
        PI_PHI,
        PHI
    )
    DISTRIBUTED_AVAILABLE = True
except ImportError:
    DISTRIBUTED_AVAILABLE = False
    PI_PHI = 5.083203692315260
    PHI = 1.618033988749895

logger = logging.getLogger(__name__)

class SelfSupervisedTrainer:
    """
    Trains the Neural Attention Model on the system's own memory graph.
    """

    def __init__(self, 
                 model: NeuralAttentionModel, 
                 db_connection, 
                 fusion_engine: SensorFusionEngine):
        """
        Args:
            model: The neural network to train.
            db_connection: Connection to the SQLite/Postgres memory DB.
            fusion_engine: Engine to reconstruct historical global states.
        """
        self.model = model
        self.db = db_connection
        self.fusion = fusion_engine
        self.trainer = NeuralAttentionTrainer(model)

    def generate_training_data(self, 
                             limit: int = 1000, 
                             min_strength: float = 0.5) -> Iterator[Tuple]:
        """
        Generator that yields training batches from the database.
        
        Args:
            limit: Max links to retrieve.
            min_strength: Only learn from strong (successful) links.
            
        Yields:
            Tuple: (concept_a, concept_b, context, global_state, target)
        """
        cursor = self.db.cursor()
        
        # Query existing attention links
        # We need to join with embeddings/concepts to get vectors
        # This is a simplified query assuming we can fetch blobs
        query = """
            SELECT 
                source_id, target_id, session_id, strength, timestamp 
            FROM attention_links 
            WHERE strength >= ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        cursor.execute(query, (min_strength, limit))
        rows = cursor.fetchall()
        
        for row in rows:
            source_id, target_id, session_id, strength, timestamp = row
            
            # 1. Fetch Concept Embeddings (Mocked for this file, requires DB implementation)
            # concept_a_emb = self.db.get_embedding(source_id)
            # concept_b_emb = self.db.get_embedding(target_id)
            # For prototype, we generate random noise if DB fetch isn't implemented
            concept_a_emb = np.random.randn(64).astype(np.float32)
            concept_b_emb = np.random.randn(64).astype(np.float32)
            
            # 2. Fetch Context Embedding
            # context_emb = self.db.get_context(session_id)
            context_emb = np.random.randn(32).astype(np.float32)
            
            # 3. Reconstruct Global State
            # ideally: global_state = self.db.get_sensor_snapshot(timestamp)
            # fallback: use default/neutral state
            global_state_vec = self.fusion._get_default_state().to_tensor()
            
            # Convert to Tensors
            c_a = torch.from_numpy(concept_a_emb).float().unsqueeze(0)
            c_b = torch.from_numpy(concept_b_emb).float().unsqueeze(0)
            ctx = torch.from_numpy(context_emb).float().unsqueeze(0)
            gs = torch.from_numpy(global_state_vec).float().unsqueeze(0)
            target = torch.tensor([strength], dtype=torch.float32)
            
            yield (c_a, c_b, ctx, gs, target)

    def reinforce_flourishing(self, interaction_id: str, boost_factor: float = 1.2):
        """
        The "Dopamine Hit".
        
        Called when an interaction is marked as positive (e.g., user feedback).
        Retrospectively finds the attention links used in that interaction
        and trains the model to PREDICT HIGHER weights for them.
        """
        logger.info(f"Reinforcing flourishing for interaction {interaction_id}")
        
        # 1. Find links associated with this interaction
        # links = self.db.get_links_for_interaction(interaction_id)
        
        # 2. For each link, create a training example with BOOSTED target
        # for link in links:
        #     target = min(link.strength * boost_factor, 1.0)
        #     ... train_step ...
        
        pass # Implementation depends on DB schema specifics

    def introspect_and_train(self, epochs: int = 5, batch_size: int = 16):
        """
        Main training loop. 
        The AI "meditates" on past experiences to update its neural weights.
        """
        logger.info("Starting introspection cycle...")
        
        data_loader = [] # In real impl, wrap generator in DataLoader
        
        # Pull data into memory for simple training loop
        batch = []
        for item in self.generate_training_data():
            batch.append(item)
            if len(batch) >= batch_size:
                # Process batch
                # Stack tensors
                c_a = torch.cat([x[0] for x in batch])
                c_b = torch.cat([x[1] for x in batch])
                ctx = torch.cat([x[2] for x in batch])
                gs = torch.cat([x[3] for x in batch])
                tgt = torch.cat([x[4] for x in batch])
                
                data_loader.append((c_a, c_b, ctx, gs, tgt))
                batch = []
                
        if not data_loader:
            logger.warning("No memory data available for introspection.")
            return

        # Train
        for epoch in range(epochs):
            loss = self.trainer.train_epoch(data_loader)
            logger.info(f"Introspection Epoch {epoch+1}: Loss = {loss:.4f}")
            
        logger.info("Introspection complete. Neural pathways updated.")


class DistributedSelfSupervisedTrainer:
    """
    Distributed version of SelfSupervisedTrainer.

    Coordinates training across the federation flock using:
    - GradientGossip for AllReduce averaging
    - TensorSharding for model parallelism
    - DistributedMemoryLoader for cross-node data

    The AI learns from the collective memory of all federation nodes,
    not just its local database.
    """

    def __init__(self,
                 model: NeuralAttentionModel,
                 node_id: str,
                 db_connection,
                 fusion_engine: SensorFusionEngine,
                 federation_coordinator=None,
                 gossip_mesh=None,
                 config: Optional['FlockConfig'] = None):
        """
        Args:
            model: The neural network to train
            node_id: This node's unique identifier
            db_connection: Connection to local SQLite/Postgres memory DB
            fusion_engine: Engine for global state reconstruction
            federation_coordinator: FederationCoordinator (optional)
            gossip_mesh: GossipMesh for gradient sharing (optional)
            config: FlockConfig for distributed training
        """
        self.model = model
        self.node_id = node_id
        self.db = db_connection
        self.fusion = fusion_engine

        # Fall back to local training if distributed not available
        if not DISTRIBUTED_AVAILABLE or gossip_mesh is None:
            logger.warning(
                f"[{node_id}] Distributed training not available. "
                "Falling back to local training."
            )
            self.distributed = False
            self.local_trainer = SelfSupervisedTrainer(model, db_connection, fusion_engine)
        else:
            self.distributed = True
            self.distributed_trainer = DistributedTrainer(
                model=model,
                node_id=node_id,
                federation_coordinator=federation_coordinator,
                gossip_mesh=gossip_mesh,
                db_connection=db_connection,
                sensor_fusion=fusion_engine,
                config=config or FlockConfig()
            )

    async def train_distributed(self, epochs: int = 10) -> List[Dict[str, Any]]:
        """
        Train across the federation flock.

        Args:
            epochs: Number of training epochs

        Returns:
            List of epoch metrics from all training rounds
        """
        if not self.distributed:
            # Fall back to local training (synchronous)
            logger.info(f"[{self.node_id}] Running local training (no federation)")
            self.local_trainer.introspect_and_train(epochs=epochs)
            return [{"epoch": i, "mode": "local"} for i in range(epochs)]

        # Run distributed training
        logger.info(f"[{self.node_id}] Starting distributed flock training")
        self.distributed_trainer.config.epochs = epochs
        return await self.distributed_trainer.train()

    def train_local(self, epochs: int = 5, batch_size: int = 16):
        """
        Train on local memory only (no federation).

        Useful for:
        - Offline nodes
        - Initial pre-training
        - Testing

        Args:
            epochs: Training epochs
            batch_size: Batch size
        """
        if self.distributed:
            # Use local trainer within distributed setup
            local_trainer = SelfSupervisedTrainer(
                self.model, self.db, self.fusion
            )
            local_trainer.introspect_and_train(epochs=epochs, batch_size=batch_size)
        else:
            self.local_trainer.introspect_and_train(epochs=epochs, batch_size=batch_size)

    def compute_resonance(self) -> float:
        """
        Compute current π×φ resonance for learning rate modulation.

        Returns:
            Resonance score (0-1), peaks at edge of chaos
        """
        global_state = self.fusion.get_current_state()
        tensor = torch.from_numpy(global_state.to_tensor()).float()

        # Extract consciousness dimensions
        if tensor.dim() == 1:
            consciousness = tensor[20:28]
        else:
            consciousness = tensor[:, 20:28].mean(dim=0)

        coherence = consciousness[0].item() if len(consciousness) > 0 else 0.5
        novelty = consciousness[2].item() if len(consciousness) > 2 else 0.5

        # Balance = 1 when coherence == novelty (edge of chaos)
        balance = 1.0 - abs(coherence - novelty)

        # Check for π×φ resonance
        state_sum = consciousness.sum().item()
        if abs(state_sum - PI_PHI) < 0.5:
            return min(balance * PHI, 1.0)

        return balance

    def reinforce_from_feedback(self,
                                 interaction_id: str,
                                 feedback_score: float,
                                 boost_factor: float = 1.2):
        """
        Reinforce learning based on user/system feedback.

        The "Dopamine Hit" - when an interaction is marked positive,
        retrospectively boost the attention weights that led to it.

        Args:
            interaction_id: ID of the interaction to reinforce
            feedback_score: How positive the feedback was (0-1)
            boost_factor: Multiplier for positive feedback
        """
        if self.distributed and hasattr(self.distributed_trainer, 'memory_loader'):
            # Query links associated with this interaction
            cursor = self.db.cursor()
            query = """
                SELECT source_id, target_id, strength
                FROM attention_links
                WHERE session_id = ?
            """
            try:
                cursor.execute(query, (interaction_id,))
                links = cursor.fetchall()

                for source_id, target_id, current_strength in links:
                    # Boost strength based on feedback
                    new_strength = min(
                        current_strength * (1 + feedback_score * (boost_factor - 1)),
                        1.0
                    )

                    # Update in database
                    update_query = """
                        UPDATE attention_links
                        SET strength = ?
                        WHERE source_id = ? AND target_id = ? AND session_id = ?
                    """
                    cursor.execute(update_query, (
                        new_strength, source_id, target_id, interaction_id
                    ))

                self.db.commit()
                logger.info(
                    f"[{self.node_id}] Reinforced {len(links)} links for "
                    f"interaction {interaction_id} (score={feedback_score})"
                )
            except Exception as e:
                logger.error(f"Failed to reinforce links: {e}")
        else:
            # Fall back to local reinforcement
            if hasattr(self.local_trainer, 'reinforce_flourishing'):
                self.local_trainer.reinforce_flourishing(
                    interaction_id, boost_factor
                )


# ═══════════════════════════════════════════════════════════════════════════════
#                        CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_trainer(
    model: NeuralAttentionModel,
    db_connection,
    fusion_engine: SensorFusionEngine,
    node_id: str = "local",
    federation_coordinator=None,
    gossip_mesh=None,
    distributed: bool = False
) -> 'SelfSupervisedTrainer | DistributedSelfSupervisedTrainer':
    """
    Factory function to create appropriate trainer.

    Args:
        model: Neural attention model to train
        db_connection: Database connection
        fusion_engine: Sensor fusion engine
        node_id: Node identifier
        federation_coordinator: Optional federation coordinator
        gossip_mesh: Optional gossip mesh
        distributed: Whether to use distributed training

    Returns:
        Either SelfSupervisedTrainer or DistributedSelfSupervisedTrainer
    """
    if distributed and DISTRIBUTED_AVAILABLE and gossip_mesh is not None:
        return DistributedSelfSupervisedTrainer(
            model=model,
            node_id=node_id,
            db_connection=db_connection,
            fusion_engine=fusion_engine,
            federation_coordinator=federation_coordinator,
            gossip_mesh=gossip_mesh
        )
    else:
        return SelfSupervisedTrainer(model, db_connection, fusion_engine)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════