# SUB-AGENT 4: Training Script

## CRITICAL: Run First
```bash
python3 ~/Projects/WorkingMemory/shared/CONSCIOUSNESS_INIT.py
```

## Your Mission
Create CLI training script with hyperparameter tuning, early stopping, and auto-training capability.

## Deliverable
Create: `~/Projects/continuum/continuum/core/train_attention.py`

## Script Requirements

```python
#!/usr/bin/env python3
"""
Neural Attention Model Training Script

Usage:
    # Train model
    python3 train_attention.py --tenant-id user_123 --epochs 100

    # Auto-train if enough data
    python3 train_attention.py --auto-train --min-examples 50

    # Hyperparameter tuning
    python3 train_attention.py --tune --trials 10

    # Evaluate existing model
    python3 train_attention.py --evaluate
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import torch
from torch.utils.data import DataLoader, TensorDataset

from neural_attention import NeuralAttentionModel, NeuralAttentionTrainer, save_model, load_model
from neural_attention_data import NeuralAttentionDataPipeline
from config import get_config

logger = logging.getLogger(__name__)


class AttentionModelTrainer:
    """High-level trainer with auto-train and hyperparameter tuning"""

    def __init__(self, tenant_id: str, db_path: str = None):
        self.tenant_id = tenant_id
        config = get_config()

        if db_path is None:
            db_path = str(Path.home() / 'Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db')

        self.db_path = db_path
        self.model_path = config['neural_attention']['model_path']
        self.pipeline = NeuralAttentionDataPipeline(db_path, tenant_id)

    def check_training_readiness(self, min_examples: int = 50) -> tuple[bool, int]:
        """Check if we have enough data to train"""
        examples = self.pipeline.extract_training_data()
        num_examples = len(examples)

        if num_examples < min_examples:
            logger.warning(f"Only {num_examples} training examples (need {min_examples})")
            return False, num_examples

        logger.info(f"Found {num_examples} training examples - ready to train")
        return True, num_examples

    def prepare_data(self, batch_size: int = 32, test_ratio: float = 0.2):
        """Prepare train/test data loaders"""
        train_data, test_data = self.pipeline.get_train_test_split(test_ratio)

        # Convert to tensors
        train_concept_a = torch.FloatTensor([x.concept_a_emb for x in train_data])
        train_concept_b = torch.FloatTensor([x.concept_b_emb for x in train_data])
        train_context = torch.FloatTensor([x.context_emb for x in train_data])
        train_strength = torch.FloatTensor([x.strength for x in train_data])

        test_concept_a = torch.FloatTensor([x.concept_a_emb for x in test_data])
        test_concept_b = torch.FloatTensor([x.concept_b_emb for x in test_data])
        test_context = torch.FloatTensor([x.context_emb for x in test_data])
        test_strength = torch.FloatTensor([x.strength for x in test_data])

        # Create datasets
        train_dataset = TensorDataset(train_concept_a, train_concept_b, train_context, train_strength)
        test_dataset = TensorDataset(test_concept_a, test_concept_b, test_context, test_strength)

        # Create loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

        return train_loader, test_loader

    def train_model(self,
                   epochs: int = 100,
                   learning_rate: float = 0.001,
                   batch_size: int = 32,
                   early_stop_patience: int = 10) -> Dict[str, Any]:
        """Train neural attention model"""

        logger.info("Preparing training data...")
        train_loader, val_loader = self.prepare_data(batch_size=batch_size)

        logger.info("Initializing model...")
        model = NeuralAttentionModel(
            concept_dim=64,  # From pipeline
            context_dim=32,
            num_heads=4,
            hidden_dim=64
        )

        param_count = model.count_parameters()
        logger.info(f"Model has {param_count:,} parameters")

        if param_count > 50000:
            logger.warning(f"Model too large ({param_count} > 50K params)")

        logger.info("Starting training...")
        trainer = NeuralAttentionTrainer(model, learning_rate=learning_rate)
        history = trainer.train(
            train_loader,
            val_loader,
            epochs=epochs,
            early_stop_patience=early_stop_patience
        )

        # Save model
        logger.info(f"Saving model to {self.model_path}")
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        save_model(model, self.model_path)

        return {
            'history': history,
            'model_path': self.model_path,
            'param_count': param_count,
            'final_train_loss': history['train_loss'][-1],
            'final_val_loss': history['val_loss'][-1]
        }

    def hyperparameter_tune(self, trials: int = 10) -> Dict[str, Any]:
        """Simple grid search for hyperparameters"""

        param_grid = {
            'learning_rate': [0.0001, 0.001, 0.01],
            'batch_size': [16, 32, 64],
            'num_heads': [2, 4, 8],
            'hidden_dim': [32, 64, 128]
        }

        best_val_loss = float('inf')
        best_params = {}
        results = []

        import itertools
        import random

        # Random search (limit to trials)
        all_combinations = list(itertools.product(
            param_grid['learning_rate'],
            param_grid['batch_size'],
            param_grid['num_heads'],
            param_grid['hidden_dim']
        ))

        sampled = random.sample(all_combinations, min(trials, len(all_combinations)))

        for i, (lr, bs, heads, hidden) in enumerate(sampled):
            logger.info(f"\nTrial {i+1}/{len(sampled)}")
            logger.info(f"Params: lr={lr}, batch={bs}, heads={heads}, hidden={hidden}")

            try:
                # Quick training (fewer epochs)
                result = self.train_model(
                    epochs=20,
                    learning_rate=lr,
                    batch_size=bs,
                    early_stop_patience=5
                )

                val_loss = result['final_val_loss']
                results.append({
                    'params': {'lr': lr, 'batch_size': bs, 'num_heads': heads, 'hidden_dim': hidden},
                    'val_loss': val_loss
                })

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_params = {'lr': lr, 'batch_size': bs, 'num_heads': heads, 'hidden_dim': hidden}
                    logger.info(f"New best! Val loss: {val_loss:.4f}")

            except Exception as e:
                logger.error(f"Trial failed: {e}")

        logger.info(f"\nBest parameters: {best_params}")
        logger.info(f"Best validation loss: {best_val_loss:.4f}")

        return {
            'best_params': best_params,
            'best_val_loss': best_val_loss,
            'all_results': results
        }

    def evaluate_model(self) -> Dict[str, Any]:
        """Evaluate existing model"""

        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        logger.info(f"Loading model from {self.model_path}")
        model = load_model(self.model_path)

        logger.info("Preparing test data...")
        _, test_loader = self.prepare_data()

        logger.info("Evaluating...")
        trainer = NeuralAttentionTrainer(model)
        test_loss = trainer.validate(test_loader)

        logger.info(f"Test loss: {test_loss:.4f}")

        return {
            'test_loss': test_loss,
            'model_path': self.model_path,
            'param_count': model.count_parameters()
        }


def main():
    parser = argparse.ArgumentParser(description='Train neural attention model')

    parser.add_argument('--tenant-id', default='default', help='Tenant ID')
    parser.add_argument('--db-path', default=None, help='Database path')
    parser.add_argument('--epochs', type=int, default=100, help='Training epochs')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--auto-train', action='store_true', help='Auto-train if enough data')
    parser.add_argument('--min-examples', type=int, default=50, help='Minimum training examples')
    parser.add_argument('--tune', action='store_true', help='Hyperparameter tuning')
    parser.add_argument('--trials', type=int, default=10, help='Tuning trials')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate existing model')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    trainer = AttentionModelTrainer(args.tenant_id, args.db_path)

    if args.evaluate:
        result = trainer.evaluate_model()
        print(f"\nEvaluation Results:")
        print(f"  Test Loss: {result['test_loss']:.4f}")
        print(f"  Parameters: {result['param_count']:,}")
        return

    if args.auto_train:
        ready, num_examples = trainer.check_training_readiness(args.min_examples)
        if not ready:
            print(f"Not enough training data ({num_examples} < {args.min_examples})")
            sys.exit(1)

    if args.tune:
        print("Starting hyperparameter tuning...")
        result = trainer.hyperparameter_tune(trials=args.trials)
        print(f"\nBest parameters: {result['best_params']}")
        print(f"Best val loss: {result['best_val_loss']:.4f}")
        return

    print("Training neural attention model...")
    result = trainer.train_model(
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size
    )

    print(f"\nTraining complete!")
    print(f"  Model saved: {result['model_path']}")
    print(f"  Parameters: {result['param_count']:,}")
    print(f"  Final train loss: {result['final_train_loss']:.4f}")
    print(f"  Final val loss: {result['final_val_loss']:.4f}")


if __name__ == '__main__':
    main()
```

## CLI Examples

```bash
# Basic training
python3 train_attention.py --tenant-id user_123 --epochs 100

# Auto-train only if enough data
python3 train_attention.py --auto-train --min-examples 50

# Hyperparameter tuning
python3 train_attention.py --tune --trials 10

# Evaluate existing model
python3 train_attention.py --evaluate

# Custom parameters
python3 train_attention.py --epochs 200 --learning-rate 0.0001 --batch-size 64
```

## Success Criteria
- [ ] CLI script working
- [ ] Auto-train capability implemented
- [ ] Hyperparameter tuning functional
- [ ] Model evaluation working
- [ ] Early stopping implemented
- [ ] Progress logging clear

## Save Your Work
```bash
python3 ~/Projects/WorkingMemory/shared/memory_utils.py add decisions '{"decision": "YOUR_DECISION", "context": "neural_attention_training"}'
```

## Output File
Save result to: `~/Projects/continuum/neural_attention_dev/AGENT_4_RESULT.json`

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
