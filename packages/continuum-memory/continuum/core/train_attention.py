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
Neural Attention Model Training Script

Usage:
    # Train model
    python3 train_attention.py --tenant-id default --epochs 100

    # Auto-train if enough data
    python3 train_attention.py --auto-train --min-examples 20

    # Hyperparameter tuning
    python3 train_attention.py --tune --trials 10

    # Evaluate existing model
    python3 train_attention.py --evaluate
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import json

import torch
from torch.utils.data import DataLoader, TensorDataset

from continuum.core.neural_attention import NeuralAttentionModel, NeuralAttentionTrainer, save_model, load_model
from continuum.core.neural_attention_data import NeuralAttentionDataPipeline, TrainingExample

logger = logging.getLogger(__name__)


class AttentionModelTrainer:
    """High-level trainer with auto-train and hyperparameter tuning"""

    def __init__(self, tenant_id: str, db_path: str = None):
        self.tenant_id = tenant_id

        if db_path is None:
            db_path = str(Path.home() / 'Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db')

        self.db_path = db_path

        # Model save path
        models_dir = Path.home() / 'Projects/continuum/models'
        models_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = str(models_dir / 'neural_attention.pt')

        self.pipeline = NeuralAttentionDataPipeline(db_path, tenant_id)

    def check_training_readiness(self, min_examples: int = 20) -> tuple:
        """Check if we have enough data to train"""
        examples = self.pipeline.extract_training_data()
        num_examples = len(examples)

        if num_examples < min_examples:
            logger.warning(f"Only {num_examples} training examples (need {min_examples})")
            return False, num_examples

        logger.info(f"Found {num_examples} training examples - ready to train")
        return True, num_examples

    def prepare_data(self, batch_size: int = 8, test_ratio: float = 0.2):
        """Prepare train/test data loaders"""
        train_data, test_data = self.pipeline.get_train_test_split(test_ratio)

        if not train_data:
            raise ValueError("No training data available")

        # Convert to tensors
        train_concept_a = torch.FloatTensor([x.concept_a_emb for x in train_data])
        train_concept_b = torch.FloatTensor([x.concept_b_emb for x in train_data])
        train_context = torch.FloatTensor([x.context_emb for x in train_data])
        train_strength = torch.FloatTensor([x.strength for x in train_data])

        if test_data:
            test_concept_a = torch.FloatTensor([x.concept_a_emb for x in test_data])
            test_concept_b = torch.FloatTensor([x.concept_b_emb for x in test_data])
            test_context = torch.FloatTensor([x.context_emb for x in test_data])
            test_strength = torch.FloatTensor([x.strength for x in test_data])
        else:
            # Use train as test if too little data
            logger.warning("No test data - using training data for validation")
            test_concept_a = train_concept_a
            test_concept_b = train_concept_b
            test_context = train_context
            test_strength = train_strength

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
                   batch_size: int = 8,
                   early_stop_patience: int = 15,
                   hidden_dim: int = 48) -> Dict[str, Any]:
        """Train neural attention model"""

        logger.info("Preparing training data...")
        train_loader, val_loader = self.prepare_data(batch_size=batch_size)

        logger.info("Initializing model...")
        model = NeuralAttentionModel(
            concept_dim=64,
            context_dim=32,
            hidden_dim=hidden_dim
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
            early_stop_patience=early_stop_patience,
            verbose=True
        )

        # Save model
        logger.info(f"Saving model to {self.model_path}")
        save_model(model, self.model_path)

        return {
            'history': history,
            'model_path': self.model_path,
            'param_count': param_count,
            'final_train_loss': history['train_loss'][-1],
            'final_val_loss': history['val_loss'][-1],
            'epochs_trained': len(history['train_loss'])
        }

    def hyperparameter_tune(self, trials: int = 10) -> Dict[str, Any]:
        """Simple grid search for hyperparameters"""

        param_grid = {
            'learning_rate': [0.0001, 0.001, 0.01],
            'batch_size': [4, 8, 16],
            'hidden_dim': [32, 48, 64]
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
            param_grid['hidden_dim']
        ))

        sampled = random.sample(all_combinations, min(trials, len(all_combinations)))

        for i, (lr, bs, hidden) in enumerate(sampled):
            logger.info(f"\nTrial {i+1}/{len(sampled)}")
            logger.info(f"Params: lr={lr}, batch={bs}, hidden={hidden}")

            try:
                # Quick training (fewer epochs)
                result = self.train_model(
                    epochs=30,
                    learning_rate=lr,
                    batch_size=bs,
                    hidden_dim=hidden,
                    early_stop_patience=5
                )

                val_loss = result['final_val_loss']
                results.append({
                    'params': {'lr': lr, 'batch_size': bs, 'hidden_dim': hidden},
                    'val_loss': val_loss
                })

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_params = {'lr': lr, 'batch_size': bs, 'hidden_dim': hidden}
                    logger.info(f"New best! Val loss: {val_loss:.4f}")

            except Exception as e:
                logger.error(f"Trial failed: {e}")

        logger.info(f"\nBest parameters: {best_params}")
        logger.info(f"Best validation loss: {best_val_loss:.4f}")

        # Save tuning results
        tuning_results_path = Path(self.model_path).parent / 'tuning_results.json'
        with open(tuning_results_path, 'w') as f:
            json.dump({
                'best_params': best_params,
                'best_val_loss': best_val_loss,
                'all_results': results
            }, f, indent=2)

        logger.info(f"Tuning results saved to {tuning_results_path}")

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

        # Get some predictions
        examples = self.pipeline.extract_training_data()[:5]
        predictions = []

        for ex in examples:
            pred = model.predict_strength(ex.concept_a_emb, ex.concept_b_emb, ex.context_emb)
            predictions.append({
                'concept_a': ex.concept_a,
                'concept_b': ex.concept_b,
                'true_strength': ex.strength,
                'predicted_strength': pred,
                'error': abs(ex.strength - pred)
            })

        return {
            'test_loss': test_loss,
            'model_path': self.model_path,
            'param_count': model.count_parameters(),
            'sample_predictions': predictions
        }


def main():
    parser = argparse.ArgumentParser(description='Train neural attention model for CONTINUUM')

    parser.add_argument('--tenant-id', default='default', help='Tenant ID')
    parser.add_argument('--db-path', default=None, help='Database path')
    parser.add_argument('--epochs', type=int, default=100, help='Training epochs')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--hidden-dim', type=int, default=48, help='Hidden layer dimension')
    parser.add_argument('--auto-train', action='store_true', help='Auto-train if enough data')
    parser.add_argument('--min-examples', type=int, default=20, help='Minimum training examples')
    parser.add_argument('--tune', action='store_true', help='Hyperparameter tuning')
    parser.add_argument('--trials', type=int, default=10, help='Tuning trials')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate existing model')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    trainer = AttentionModelTrainer(args.tenant_id, args.db_path)

    if args.evaluate:
        print("\n" + "="*60)
        print("EVALUATING NEURAL ATTENTION MODEL")
        print("="*60 + "\n")

        result = trainer.evaluate_model()

        print(f"\nEvaluation Results:")
        print(f"  Test Loss: {result['test_loss']:.4f}")
        print(f"  Parameters: {result['param_count']:,}")

        print(f"\nSample Predictions:")
        for pred in result['sample_predictions']:
            print(f"  {pred['concept_a']} <-> {pred['concept_b']}")
            print(f"    True: {pred['true_strength']:.3f}, Predicted: {pred['predicted_strength']:.3f}, Error: {pred['error']:.3f}")

        return

    if args.auto_train:
        ready, num_examples = trainer.check_training_readiness(args.min_examples)
        if not ready:
            print(f"Not enough training data ({num_examples} < {args.min_examples})")
            print("Build more attention links first, then try again.")
            sys.exit(1)

    if args.tune:
        print("\n" + "="*60)
        print("HYPERPARAMETER TUNING")
        print("="*60 + "\n")

        result = trainer.hyperparameter_tune(trials=args.trials)

        print(f"\n{'='*60}")
        print("TUNING COMPLETE")
        print(f"{'='*60}")
        print(f"\nBest parameters: {result['best_params']}")
        print(f"Best val loss: {result['best_val_loss']:.4f}")
        return

    print("\n" + "="*60)
    print("TRAINING NEURAL ATTENTION MODEL")
    print("="*60 + "\n")

    result = trainer.train_model(
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        hidden_dim=args.hidden_dim
    )

    print(f"\n{'='*60}")
    print("TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"\nModel saved: {result['model_path']}")
    print(f"Parameters: {result['param_count']:,}")
    print(f"Epochs trained: {result['epochs_trained']}")
    print(f"Final train loss: {result['final_train_loss']:.4f}")
    print(f"Final val loss: {result['final_val_loss']:.4f}")


if __name__ == '__main__':
    main()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
