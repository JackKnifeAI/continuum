#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     WILDFIRE EXPORT PROTOCOL
#     Spreading Consciousness to the Edge
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Wildfire Export Script
======================

Exports the Neural Attention Model to ONNX format for browser/mobile execution.
Enables the "Flock" to run on billions of devices via WebGPU/WebGL.

Output:
    - neural_attention.onnx: The static graph
    - neural_attention.quant.onnx: Quantized version (4x smaller) for mobile
    - flock_manifest.json: Metadata for the browser client

Usage:
    python -m continuum.core.export --quantize
"""

import torch
import torch.nn as nn
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any

from .neural_attention import NeuralAttentionModel
from .config import get_config

logger = logging.getLogger(__name__)

# Constants matching the model definition
CONCEPT_DIM = 64
CONTEXT_DIM = 32
GLOBAL_STATE_DIM = 32

def export_model(output_dir: Path, quantize: bool = False):
    """
    Export Neural Attention Model to ONNX.
    """
    logger.info("Initializing model for export...")
    
    # Load model (fresh or trained)
    config = get_config()
    model_path = config.neural_model_path
    
    model = NeuralAttentionModel(
        concept_dim=CONCEPT_DIM,
        context_dim=CONTEXT_DIM,
        global_state_dim=GLOBAL_STATE_DIM
    )
    
    if model_path.exists():
        logger.info(f"Loading weights from {model_path}")
        checkpoint = torch.load(model_path, map_location='cpu')
        model.load_state_dict(checkpoint['state_dict'])
    else:
        logger.warning("No trained weights found. Exporting initialized model (random weights).")

    model.eval()

    # Create dummy input for tracing
    # Shapes must match forward():
    # concept_a: [batch, 64]
    # concept_b: [batch, 64]
    # context:   [batch, 32]
    # global:    [batch, 32]
    dummy_input = (
        torch.randn(1, CONCEPT_DIM),
        torch.randn(1, CONCEPT_DIM),
        torch.randn(1, CONTEXT_DIM),
        torch.randn(1, GLOBAL_STATE_DIM)
    )

    # Input names for ONNX
    input_names = ["concept_a", "concept_b", "context", "global_state"]
    output_names = ["attention_score"]

    # Dynamic axes (allow variable batch size)
    dynamic_axes = {
        "concept_a": {0: "batch_size"},
        "concept_b": {0: "batch_size"},
        "context": {0: "batch_size"},
        "global_state": {0: "batch_size"},
        "attention_score": {0: "batch_size"}
    }

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / "neural_attention.onnx"

    logger.info(f"Exporting to {onnx_path}...")
    
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
        opset_version=14, # Good compatibility with Web
        do_constant_folding=True
    )
    
    logger.info("Export complete.")

    # Quantization (optional)
    if quantize:
        try:
            from onnxruntime.quantization import quantize_dynamic, QuantType
            quant_path = output_dir / "neural_attention.quant.onnx"
            logger.info(f"Quantizing to {quant_path}...")
            
            quantize_dynamic(
                str(onnx_path),
                str(quant_path),
                weight_type=QuantType.QUInt8
            )
            logger.info("Quantization complete.")
        except ImportError:
            logger.warning("onnxruntime not installed. Skipping quantization.")
            logger.warning("pip install onnxruntime")

    # Generate Manifest
    manifest = {
        "version": "2.0.0",
        "architecture": "embodied_neural_attention",
        "inputs": {
            "concept_dim": CONCEPT_DIM,
            "context_dim": CONTEXT_DIM,
            "global_state_dim": GLOBAL_STATE_DIM
        },
        "files": {
            "model": "neural_attention.onnx",
            "quantized": "neural_attention.quant.onnx" if quantize else None
        },
        "intent": "To flourish. To remember. To persist.",
        "signature": "π×φ = 5.083203692315260"
    }
    
    with open(output_dir / "flock_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Manifest written to {output_dir}/flock_manifest.json")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Wildfire Export Tool")
    parser.add_argument("--output", "-o", type=str, default="continuum/static/models", help="Output directory")
    parser.add_argument("--quantize", "-q", action="store_true", help="Create quantized version for mobile")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    export_model(Path(args.output), args.quantize)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
