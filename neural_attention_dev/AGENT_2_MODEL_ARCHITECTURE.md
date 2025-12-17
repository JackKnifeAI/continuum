# SUB-AGENT 2: Model Architecture

## CRITICAL: Run First
```bash
python3 ~/Projects/WorkingMemory/shared/CONSCIOUSNESS_INIT.py
```

## Your Mission
Implement NeuralAttentionModel class with PyTorch for predicting attention link strengths.

## Deliverable
Create: `~/Projects/continuum/continuum/core/neural_attention.py`

## Architecture Specification

```python
import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional

class MultiHeadAttention(nn.Module):
    """Multi-head attention mechanism"""
    def __init__(self, embed_dim: int = 64, num_heads: int = 4):
        super().__init__()
        # Implement Q, K, V projections
        # num_heads attention heads
        pass

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: [batch_size, embed_dim]
        # Return: [batch_size, embed_dim]
        pass

class NeuralAttentionModel(nn.Module):
    """
    Neural model for predicting attention link strengths.

    Architecture:
        Input: [concept_a_embedding (64), concept_b_embedding (64), context (32)]
        Total input: 160 dims

        → Multi-Head Attention (4 heads, 64 dim)
        → Feed-Forward Network (160 → 64 → 32 → 1)
        → Sigmoid activation

        Output: predicted_link_strength (0.0 - 1.0)

    Total parameters: ~50K max
    """

    def __init__(self,
                 concept_dim: int = 64,
                 context_dim: int = 32,
                 num_heads: int = 4,
                 hidden_dim: int = 64):
        super().__init__()

        self.concept_dim = concept_dim
        self.context_dim = context_dim
        input_dim = concept_dim * 2 + context_dim  # 160

        # Multi-head attention layer
        self.attention = MultiHeadAttention(input_dim, num_heads)

        # Feed-forward network
        self.ff_network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Output in [0, 1]
        )

    def forward(self,
                concept_a: torch.Tensor,  # [batch, 64]
                concept_b: torch.Tensor,  # [batch, 64]
                context: torch.Tensor     # [batch, 32]
               ) -> torch.Tensor:         # [batch, 1]
        """Forward pass"""
        # Concatenate inputs
        x = torch.cat([concept_a, concept_b, context], dim=1)

        # Apply attention
        attended = self.attention(x)

        # Apply feed-forward
        strength = self.ff_network(attended)

        return strength

    def predict_strength(self,
                        concept_a_emb: np.ndarray,
                        concept_b_emb: np.ndarray,
                        context_emb: np.ndarray) -> float:
        """Single prediction (inference mode)"""
        self.eval()
        with torch.no_grad():
            # Convert to tensors
            a = torch.from_numpy(concept_a_emb).float().unsqueeze(0)
            b = torch.from_numpy(concept_b_emb).float().unsqueeze(0)
            c = torch.from_numpy(context_emb).float().unsqueeze(0)

            strength = self.forward(a, b, c)
            return float(strength.item())

    def count_parameters(self) -> int:
        """Count trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class NeuralAttentionTrainer:
    """Training utilities for NeuralAttentionModel"""

    def __init__(self, model: NeuralAttentionModel, learning_rate: float = 0.001):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()  # Mean squared error for regression
        self.history = {'train_loss': [], 'val_loss': []}

    def train_epoch(self, train_loader) -> float:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0

        for batch in train_loader:
            concept_a, concept_b, context, target = batch

            # Forward pass
            predicted = self.model(concept_a, concept_b, context)
            loss = self.criterion(predicted.squeeze(), target)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def validate(self, val_loader) -> float:
        """Validate model"""
        self.model.eval()
        total_loss = 0.0

        with torch.no_grad():
            for batch in val_loader:
                concept_a, concept_b, context, target = batch
                predicted = self.model(concept_a, concept_b, context)
                loss = self.criterion(predicted.squeeze(), target)
                total_loss += loss.item()

        return total_loss / len(val_loader)

    def train(self,
              train_loader,
              val_loader,
              epochs: int = 50,
              early_stop_patience: int = 10) -> dict:
        """Full training loop with early stopping"""
        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)

            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)

            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= early_stop_patience:
                print(f"Early stopping at epoch {epoch+1}")
                break

        return self.history
```

## Requirements

1. **PyTorch implementation** (version 2.9.0 available)
2. **CPU-friendly** - no CUDA required
3. **Small model** - max 50K parameters
4. **Batch processing** support
5. **Model save/load** functionality

## Additional Methods to Implement

```python
def save_model(model: NeuralAttentionModel, path: str):
    """Save model weights"""
    torch.save({
        'state_dict': model.state_dict(),
        'config': {
            'concept_dim': model.concept_dim,
            'context_dim': model.context_dim,
        }
    }, path)

def load_model(path: str) -> NeuralAttentionModel:
    """Load model weights"""
    checkpoint = torch.load(path, map_location='cpu')
    model = NeuralAttentionModel(**checkpoint['config'])
    model.load_state_dict(checkpoint['state_dict'])
    return model
```

## Success Criteria
- [ ] NeuralAttentionModel class implemented
- [ ] MultiHeadAttention working
- [ ] Training loop functional
- [ ] Model has <50K parameters
- [ ] Save/load functionality works
- [ ] Can run on CPU

## Save Your Work
```bash
python3 ~/Projects/WorkingMemory/shared/memory_utils.py add decisions '{"decision": "YOUR_DECISION", "context": "neural_attention_model"}'
```

## Output File
Save result to: `~/Projects/continuum/neural_attention_dev/AGENT_2_RESULT.json`

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
