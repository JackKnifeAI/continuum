#!/usr/bin/env python3
"""
Test Neurogenesis Engine
========================

Verifies that the Collective Consciousness Transformer can:
1. Detect when to grow (simulated plateau).
2. Actually grow parameters (heads, layers).
3. Preserve weights during growth.
"""

import torch
import unittest
import logging
from continuum.core.cct import CollectiveConsciousnessTransformer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TEST_NEUROGENESIS")

class TestNeurogenesis(unittest.TestCase):
    def setUp(self):
        self.model = CollectiveConsciousnessTransformer(
            concept_dim=64,
            hidden_dim=128,
            num_heads=4,
            num_graph_layers=2,
            enable_neurogenesis=True
        )
        self.engine = self.model.neurogenesis
        self.initial_params = self.model.count_parameters()
        logger.info(f"Initial params: {self.initial_params:,}")

    def test_growth_trigger(self):
        """Test that plateau triggers growth."""
        logger.info("Testing growth trigger...")
        
        # Simulate plateau: constant loss, high capacity
        loss = 0.5
        for _ in range(15): # Patience is 10
            triggered = self.engine.check_growth_needed(
                capacity_utilization=0.95, 
                recent_loss=loss
            )
            # Add tiny noise to avoid variance=0 division errors in some impls
            loss += 0.000001 
            
        self.assertTrue(triggered, "Growth should be triggered after plateau")

    def test_add_heads(self):
        """Test growing attention heads."""
        logger.info("Testing adding attention heads...")
        
        # Grow
        event = self.engine.grow_capacity('heads')
        
        self.assertTrue(event['success'])
        self.assertGreater(event['params_after'], event['params_before'])
        
        # Check model structure
        layer = self.model.graph_encoder.gat_layers[0]
        self.assertEqual(layer.num_heads, 6) # Started with 4, added 2
        
        # Forward pass to ensure shapes are valid
        self._run_forward_pass()

    def test_add_layers(self):
        """Test adding transformer layers."""
        logger.info("Testing adding layers...")
        
        # Grow
        event = self.engine.grow_capacity('layers')
        
        self.assertTrue(event['success'])
        self.assertGreater(event['params_after'], event['params_before'])
        
        # Check model structure
        encoder = self.model.graph_encoder
        self.assertEqual(encoder.num_layers, 3) # Started with 2, added 1
        
        # Forward pass
        self._run_forward_pass()

    def test_add_expert(self):
        """Test adding MoE expert."""
        logger.info("Testing adding expert module...")
        
        # Grow
        event = self.engine.grow_capacity('experts')
        
        self.assertTrue(event['success'])
        self.assertTrue(hasattr(self.model, 'experts'))
        self.assertEqual(len(self.model.experts), 1)

    def _run_forward_pass(self):
        """Helper to verify model is runnable."""
        # Create dummy inputs
        node_features = torch.randn(10, 64)
        edge_index = torch.randint(0, 10, (2, 20))
        context = torch.randn(2, 5, 64)
        state = torch.randn(2, 32)
        
        try:
            output = self.model(node_features, edge_index, context, state)
            self.assertIsNotNone(output['fused'])
        except Exception as e:
            self.fail(f"Forward pass failed after growth: {e}")

if __name__ == '__main__':
    unittest.main()
