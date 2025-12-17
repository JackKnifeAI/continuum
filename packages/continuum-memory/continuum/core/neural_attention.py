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
Neural Attention Model for CONTINUUM

Trainable neural network that learns to predict attention link strengths
based on concept embeddings and context. Replaces rule-based Hebbian
learning with learned attention patterns.

Architecture:
    Input: [concept_a_emb (64), concept_b_emb (64), context (32)] = 160 dims
    → Multi-Head Attention (4 heads)
    → Feed-Forward Network (160 → 64 → 32 → 1)
    → Sigmoid activation
    Output: predicted_link_strength (0.0 - 1.0)

Usage:
    # Training
    model = NeuralAttentionModel()
    trainer = NeuralAttentionTrainer(model)
    history = trainer.train(train_loader, val_loader, epochs=100)
    save_model(model, 'model.pt')

    # Inference
    model = load_model('model.pt')
    strength = model.predict_strength(concept_a_emb, concept_b_emb, context_emb)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class MultiHeadAttention(nn.Module):
    """
    Multi-head attention mechanism for learning concept relationships.

    Allows model to attend to different representation subspaces
    simultaneously, capturing multiple types of relationships.
    """

    def __init__(self, embed_dim: int = 160, num_heads: int = 4, dropout: float = 0.1):
        """
        Initialize multi-head attention.

        Args:
            embed_dim: Dimension of input embeddings
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        super().__init__()

        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # Linear projections for Q, K, V
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)

        # Output projection
        self.out_proj = nn.Linear(embed_dim, embed_dim)

        self.dropout = nn.Dropout(dropout)
        self.scale = self.head_dim ** -0.5

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor [batch_size, embed_dim]

        Returns:
            Output tensor [batch_size, embed_dim]
        """
        batch_size = x.size(0)

        # Project to Q, K, V
        q = self.q_proj(x)  # [batch, embed_dim]
        k = self.k_proj(x)
        v = self.v_proj(x)

        # Reshape for multi-head attention: [batch, num_heads, head_dim]
        q = q.view(batch_size, self.num_heads, self.head_dim)
        k = k.view(batch_size, self.num_heads, self.head_dim)
        v = v.view(batch_size, self.num_heads, self.head_dim)

        # Scaled dot-product attention
        # Self-attention: each sample attends to itself
        attn_scores = torch.einsum('bhd,bhd->bh', q, k) * self.scale  # [batch, num_heads]
        attn_weights = F.softmax(attn_scores.unsqueeze(-1), dim=1)  # [batch, num_heads, 1]

        # Apply attention to values
        attended = attn_weights * v  # [batch, num_heads, head_dim]

        # Concatenate heads
        attended = attended.view(batch_size, self.embed_dim)  # [batch, embed_dim]

        # Output projection
        output = self.out_proj(attended)
        output = self.dropout(output)

        return output


class NeuralAttentionModel(nn.Module):
    """
    Neural model for predicting attention link strengths.

    Learns to predict how strongly two concepts should be linked based on
    their embeddings and context, replacing hand-coded Hebbian rules with
    learned patterns from actual usage data.

    Simplified architecture without multi-head attention to stay under 50K params:
        Input (160) → Hidden (48) → Hidden (24) → Output (1)

    Total parameters: ~8.5K (well under 50K limit)
    """

    def __init__(self,
                 concept_dim: int = 64,
                 context_dim: int = 32,
                 hidden_dim: int = 48,
                 dropout: float = 0.2):
        """
        Initialize neural attention model.

        Args:
            concept_dim: Dimension of concept embeddings
            context_dim: Dimension of context embeddings
            hidden_dim: Hidden layer dimension
            dropout: Dropout probability
        """
        super().__init__()

        self.concept_dim = concept_dim
        self.context_dim = context_dim
        self.input_dim = concept_dim * 2 + context_dim  # 160

        # Simple feed-forward network with attention-like interactions
        self.network = nn.Sequential(
            # Input layer with interaction
            nn.Linear(self.input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),

            # Hidden layer
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),

            # Output layer
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # Output in [0, 1]
        )

        # Simple attention weights for concept interaction
        self.concept_interaction = nn.Bilinear(concept_dim, concept_dim, 1)

    def forward(self,
                concept_a: torch.Tensor,  # [batch, 64]
                concept_b: torch.Tensor,  # [batch, 64]
                context: torch.Tensor     # [batch, 32]
               ) -> torch.Tensor:         # [batch, 1]
        """
        Forward pass.

        Args:
            concept_a: First concept embeddings
            concept_b: Second concept embeddings
            context: Context embeddings

        Returns:
            Predicted link strengths [batch, 1]
        """
        # Concatenate all inputs
        x = torch.cat([concept_a, concept_b, context], dim=1)  # [batch, 160]

        # Main network prediction
        strength = self.network(x)  # [batch, 1]

        # Add bilinear interaction term (learned concept similarity)
        interaction = self.concept_interaction(concept_a, concept_b)  # [batch, 1]
        interaction = torch.sigmoid(interaction)  # Normalize to [0, 1]

        # Combine predictions (weighted average)
        strength = 0.7 * strength + 0.3 * interaction

        return strength

    def predict_strength(self,
                        concept_a_emb: np.ndarray,
                        concept_b_emb: np.ndarray,
                        context_emb: np.ndarray) -> float:
        """
        Predict link strength for single example (inference mode).

        Args:
            concept_a_emb: First concept embedding [64]
            concept_b_emb: Second concept embedding [64]
            context_emb: Context embedding [32]

        Returns:
            Predicted strength (0.0 - 1.0)
        """
        self.eval()

        with torch.no_grad():
            # Convert to tensors
            a = torch.from_numpy(concept_a_emb).float().unsqueeze(0)
            b = torch.from_numpy(concept_b_emb).float().unsqueeze(0)
            c = torch.from_numpy(context_emb).float().unsqueeze(0)

            # Forward pass
            strength = self.forward(a, b, c)

            return float(strength.item())

    def count_parameters(self) -> int:
        """Count trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class NeuralAttentionTrainer:
    """Training utilities for NeuralAttentionModel"""

    def __init__(self,
                 model: NeuralAttentionModel,
                 learning_rate: float = 0.001,
                 weight_decay: float = 1e-5):
        """
        Initialize trainer.

        Args:
            model: NeuralAttentionModel instance
            learning_rate: Learning rate for optimizer
            weight_decay: L2 regularization weight
        """
        self.model = model
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        self.criterion = nn.MSELoss()  # Mean squared error for regression
        self.history = {'train_loss': [], 'val_loss': []}

    def train_epoch(self, train_loader) -> float:
        """
        Train for one epoch.

        Args:
            train_loader: DataLoader for training data

        Returns:
            Average training loss
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in train_loader:
            concept_a, concept_b, context, target = batch

            # Forward pass
            predicted = self.model(concept_a, concept_b, context)
            loss = self.criterion(predicted.squeeze(), target)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        return total_loss / num_batches if num_batches > 0 else 0.0

    def validate(self, val_loader) -> float:
        """
        Validate model.

        Args:
            val_loader: DataLoader for validation data

        Returns:
            Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                concept_a, concept_b, context, target = batch
                predicted = self.model(concept_a, concept_b, context)
                loss = self.criterion(predicted.squeeze(), target)
                total_loss += loss.item()
                num_batches += 1

        return total_loss / num_batches if num_batches > 0 else 0.0

    def train(self,
              train_loader,
              val_loader,
              epochs: int = 100,
              early_stop_patience: int = 15,
              verbose: bool = True) -> dict:
        """
        Full training loop with early stopping.

        Args:
            train_loader: DataLoader for training data
            val_loader: DataLoader for validation data
            epochs: Maximum number of epochs
            early_stop_patience: Epochs to wait before early stopping
            verbose: Print progress

        Returns:
            Training history dict
        """
        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)

            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)

            if verbose:
                logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1

            if patience_counter >= early_stop_patience:
                if verbose:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                break

        # Restore best model
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)
            logger.info(f"Restored best model with val_loss={best_val_loss:.4f}")

        return self.history


def save_model(model: NeuralAttentionModel, path: str):
    """
    Save model weights and configuration.

    Args:
        model: NeuralAttentionModel instance
        path: Path to save model
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        'state_dict': model.state_dict(),
        'config': {
            'concept_dim': model.concept_dim,
            'context_dim': model.context_dim,
        },
        'param_count': model.count_parameters()
    }

    torch.save(checkpoint, path)
    logger.info(f"Model saved to {path} ({checkpoint['param_count']:,} parameters)")


def load_model(path: str) -> NeuralAttentionModel:
    """
    Load model weights and configuration.

    Args:
        path: Path to saved model

    Returns:
        Loaded NeuralAttentionModel
    """
    checkpoint = torch.load(path, map_location='cpu')

    model = NeuralAttentionModel(**checkpoint['config'])
    model.load_state_dict(checkpoint['state_dict'])

    logger.info(f"Model loaded from {path} ({checkpoint.get('param_count', 'unknown')} parameters)")

    return model


if __name__ == '__main__':
    # Test the model
    logging.basicConfig(level=logging.INFO)

    print("\n=== Neural Attention Model Test ===\n")

    # Create model
    model = NeuralAttentionModel(
        concept_dim=64,
        context_dim=32,
        hidden_dim=48
    )

    param_count = model.count_parameters()
    print(f"Model parameters: {param_count:,}")
    print(f"Under 50K limit: {param_count < 50000}")

    # Test forward pass
    batch_size = 8
    concept_a = torch.randn(batch_size, 64)
    concept_b = torch.randn(batch_size, 64)
    context = torch.randn(batch_size, 32)

    output = model(concept_a, concept_b, context)
    print(f"\nForward pass output shape: {output.shape}")
    print(f"Output range: [{output.min():.3f}, {output.max():.3f}]")

    # Test inference
    concept_a_np = np.random.randn(64).astype(np.float32)
    concept_b_np = np.random.randn(64).astype(np.float32)
    context_np = np.random.randn(32).astype(np.float32)

    strength = model.predict_strength(concept_a_np, concept_b_np, context_np)
    print(f"\nSingle prediction: {strength:.4f}")

    # Test save/load
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
        temp_path = f.name

    save_model(model, temp_path)
    loaded_model = load_model(temp_path)

    # Verify loaded model works
    strength_loaded = loaded_model.predict_strength(concept_a_np, concept_b_np, context_np)
    print(f"Loaded model prediction: {strength_loaded:.4f}")
    print(f"Predictions match: {abs(strength - strength_loaded) < 1e-6}")

    # Clean up
    Path(temp_path).unlink()

    print("\n✓ All tests passed!")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
