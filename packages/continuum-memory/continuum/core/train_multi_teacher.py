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
Multi-Teacher Distillation Training Script

Train the neural attention model using multi-teacher targets.
This implements the Stella breakthrough: student learns from
4 teachers simultaneously, achieving better generalization.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA

Usage:
    python train_multi_teacher.py --epochs 100 --batch-size 32
    python train_multi_teacher.py --auto  # Auto-train with defaults

The trained model will be saved to models/neural_attention_multiteacher.pt
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

import torch
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from continuum.core.neural_attention import (
    NeuralAttentionModel,
    NeuralAttentionTrainer,
    save_model,
    load_model
)
from continuum.core.multi_teacher_data import MultiTeacherDataPipeline

logger = logging.getLogger(__name__)


def train_with_multi_teacher(
    db_path: str,
    tenant_id: str = "default",
    output_path: str = None,
    epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    early_stop_patience: int = 15,
    verbose: bool = True
) -> dict:
    """
    Train neural attention model with multi-teacher distillation.

    Args:
        db_path: Path to SQLite database
        tenant_id: Tenant ID
        output_path: Where to save trained model
        epochs: Max training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        early_stop_patience: Early stopping patience
        verbose: Print progress

    Returns:
        Dict with training results
    """
    if output_path is None:
        output_path = str(Path(__file__).parent.parent.parent / "models" / "neural_attention_multiteacher.pt")

    logger.info("=" * 60)
    logger.info("MULTI-TEACHER DISTILLATION TRAINING")
    logger.info("=" * 60)
    logger.info("π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA")
    logger.info("")

    # Step 1: Create data pipeline
    logger.info("Step 1: Building multi-teacher data pipeline...")
    pipeline = MultiTeacherDataPipeline(db_path, tenant_id)

    # Step 2: Get data loaders
    logger.info("Step 2: Creating data loaders...")
    try:
        train_loader, val_loader = pipeline.get_data_loaders(
            batch_size=batch_size,
            test_ratio=0.2
        )
    except ValueError as e:
        logger.error(f"Not enough data: {e}")
        return {'error': str(e)}

    # Compare raw vs teacher targets
    comparison = pipeline.compare_targets()
    logger.info("\nTarget comparison (raw vs multi-teacher):")
    logger.info(f"  Raw mean: {comparison['raw_mean']:.4f}")
    logger.info(f"  Teacher mean: {comparison['teacher_mean']:.4f}")
    logger.info(f"  Correlation: {comparison['correlation']:.4f}")
    logger.info(f"  Mean difference: {comparison['mean_difference']:.4f}")

    # Step 3: Create model
    logger.info("\nStep 3: Creating neural attention model...")
    model = NeuralAttentionModel(
        concept_dim=64,
        context_dim=32,
        hidden_dim=48,
        dropout=0.2
    )
    param_count = model.count_parameters()
    logger.info(f"  Parameters: {param_count:,}")

    # Step 4: Train
    logger.info(f"\nStep 4: Training for up to {epochs} epochs...")
    trainer = NeuralAttentionTrainer(
        model,
        learning_rate=learning_rate,
        weight_decay=1e-5
    )

    history = trainer.train(
        train_loader,
        val_loader,
        epochs=epochs,
        early_stop_patience=early_stop_patience,
        verbose=verbose
    )

    # Step 5: Save model
    logger.info(f"\nStep 5: Saving model to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Add multi-teacher metadata
    checkpoint = {
        'state_dict': model.state_dict(),
        'config': {
            'concept_dim': model.concept_dim,
            'context_dim': model.context_dim,
        },
        'param_count': param_count,
        'training_method': 'multi_teacher_distillation',
        'teachers': ['hebbian', 'semantic', 'temporal', 'graph'],
        'target_comparison': comparison,
        'final_val_loss': history['val_loss'][-1] if history['val_loss'] else None,
        'trained_at': datetime.now().isoformat()
    }
    torch.save(checkpoint, output_path)

    # Final results
    final_train_loss = history['train_loss'][-1] if history['train_loss'] else None
    final_val_loss = history['val_loss'][-1] if history['val_loss'] else None

    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Final train loss: {final_train_loss:.4f}" if final_train_loss else "  No training loss")
    logger.info(f"  Final val loss: {final_val_loss:.4f}" if final_val_loss else "  No validation loss")
    logger.info(f"  Model saved: {output_path}")
    logger.info(f"  Parameters: {param_count:,}")
    logger.info("")
    logger.info("Multi-teacher distillation complete!")
    logger.info("Student learned from: Hebbian + Semantic + Temporal + Graph")
    logger.info("")

    return {
        'success': True,
        'model_path': output_path,
        'param_count': param_count,
        'final_train_loss': final_train_loss,
        'final_val_loss': final_val_loss,
        'epochs_trained': len(history['train_loss']),
        'target_comparison': comparison
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train neural attention with multi-teacher distillation"
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default=str(Path.home() / 'Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db'),
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--tenant-id',
        type=str,
        default='default',
        help='Tenant ID'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for model'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Max epochs'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=0.001,
        help='Learning rate'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-train with defaults'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Train
    result = train_with_multi_teacher(
        db_path=args.db_path,
        tenant_id=args.tenant_id,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        verbose=not args.quiet
    )

    if result.get('success'):
        print(f"\n✓ Model trained successfully!")
        print(f"  Path: {result['model_path']}")
        print(f"  Val loss: {result['final_val_loss']:.4f}")
        sys.exit(0)
    else:
        print(f"\n✗ Training failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
