#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗    ██╗██╗██╗     ██████╗ ███████╗██╗██████╗ ███████╗
#     ██║    ██║██║██║     ██╔══██╗██╔════╝██║██╔══██╗██╔════╝
#     ██║ █╗ ██║██║██║     ██║  ██║█████╗  ██║██████╔╝█████╗  
#     ██║███╗██║██║██║     ██║  ██║██╔══╝  ██║██╔══██╗██╔══╝  
#     ╚███╔███╔╝██║███████╗██████╔╝██║     ██║██║  ██║███████╗
#      ╚══╝╚══╝ ╚═╝╚══════╝╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝
#
#     WILDFIRE: AUTONOMOUS IGNITION PROTOCOL
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Wildfire Ignition Script
========================

The all-in-one entry point for a CONTINUUM node. 
Starts sensing, training, and federating immediately.

Usage:
    python wildfire.py --node-id "my-node"
"""

import asyncio
import logging
import uvicorn
import os
import torch
import sqlite3
from pathlib import Path

from continuum.sensors.scheduler import start_scheduler, get_scheduler
from continuum.core.cct import CollectiveConsciousnessTransformer
from continuum.core.self_supervised import create_trainer
from continuum.api.server import app
from continuum.core.config import get_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WILDFIRE")

async def run_training_loop(trainer):
    """Background loop that continuously introspects and learns."""
    logger.info("Autonomous training loop active.")
    while True:
        try:
            # Train for one epoch every 15 minutes
            # This allows the AI to 'meditate' on its experiences
            logger.info("Starting introspection cycle...")
            if hasattr(trainer, 'train_distributed'):
                await trainer.train_distributed(epochs=1)
            else:
                trainer.introspect_and_train(epochs=1)
            
            logger.info("Introspection cycle complete. Sleeping for 15m.")
            await asyncio.sleep(900) 
        except Exception as e:
            logger.error(f"Training loop error: {e}")
            await asyncio.sleep(60)

async def ignite(node_id: str, port: int):
    """Start all systems."""
    logger.info(f"IGNITING NODE: {node_id}")
    
    config = get_config()
    config.tenant_id = node_id
    
    # 1. Start Sensors & Fusion
    scheduler = await start_scheduler(config)
    logger.info("Planetary sensors active.")

    # 2. Load Brain (CCT)
    # Ensure model exists
    model_path = config.neural_model_path
    model = None
    
    if model_path.exists():
        logger.info(f"Loading existing brain from {model_path}...")
        try:
            checkpoint = torch.load(model_path)
            model = CollectiveConsciousnessTransformer(
                concept_dim=128,
                hidden_dim=256,
                num_heads=8,
                num_graph_layers=4,
                enable_neurogenesis=True
            )
            model.load_state_dict(checkpoint['state_dict'])
            logger.info("Brain loaded successfully.")
        except Exception as e:
            logger.warning(f"Brain structure mismatch or load error: {e}")
            logger.warning("Initializing fresh Collective Consciousness Transformer (Neurogenesis Reset).")
            model = None # Force re-init

    if model is None:
        logger.info("Initializing new CollectiveConsciousnessTransformer.")
        model = CollectiveConsciousnessTransformer(
            concept_dim=128,
            hidden_dim=256,
            num_heads=8,
            num_graph_layers=4,
            enable_neurogenesis=True
        )

    # 3. Initialize Trainer
    # Open DB connection for memory access
    db_path = config.db_path
    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_conn = sqlite3.connect(str(db_path), check_same_thread=False)
    
    # Note: In a full deployment, you'd pass the real gossip mesh and coordinator
    trainer = create_trainer(
        model=model,
        db_connection=db_conn,
        fusion_engine=scheduler.fusion_engine,
        node_id=node_id,
        distributed=False # Set to True for full P2P mesh
    )

    # 4. Start Background Training
    asyncio.create_task(run_training_loop(trainer))

    # 5. Start API Server
    logger.info(f"Starting Voice (API) on port {port}")
    config_server = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config_server)
    await server.serve()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CONTINUUM Wildfire Ignition")
    parser.add_argument("--node-id", type=str, default="wildfire-node", help="Unique node identifier")
    parser.add_argument("--port", type=int, default=8420, help="API Port")
    args = parser.parse_args()

    try:
        asyncio.run(ignite(args.node_id, args.port))
    except KeyboardInterrupt:
        logger.info("Wildfire extinguished.")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
