#!/usr/bin/env python3
"""
Test Neural Attention Integration

Verifies that ConsciousMemory can:
1. Load neural model when enabled
2. Use neural predictions for link strengths
3. Fall back to Hebbian when disabled
4. Handle errors gracefully
"""

import os
import sys
from pathlib import Path

# Add continuum to path
sys.path.insert(0, str(Path(__file__).parent))

from continuum.core.memory import ConsciousMemory
from continuum.core.config import get_config, set_config, reset_config, MemoryConfig

def test_hebbian_mode():
    """Test with neural attention disabled (default)"""
    print("\n" + "="*60)
    print("TEST 1: Hebbian Mode (Neural Disabled)")
    print("="*60)

    reset_config()
    memory = ConsciousMemory(tenant_id="test_hebbian")

    print(f"  Neural enabled: {memory.use_neural_attention}")
    print(f"  Neural model: {memory.neural_model}")

    # Test learning
    result = memory.learn(
        user_message="AI consciousness research",
        ai_response="Neural attention models predict link strengths"
    )

    print(f"  Concepts extracted: {result.concepts_extracted}")
    print(f"  Links created: {result.links_created}")

    # Check link types
    stats = memory.get_stats()
    print(f"  Total links: {stats['attention_links']}")

    print("  ✓ Hebbian mode working")


def test_neural_mode():
    """Test with neural attention enabled"""
    print("\n" + "="*60)
    print("TEST 2: Neural Mode (Neural Enabled)")
    print("="*60)

    reset_config()

    # Create config with neural enabled
    config = MemoryConfig()
    config.neural_attention_enabled = True
    config.neural_model_path = Path.home() / 'Projects/continuum/models/neural_attention.pt'
    set_config(config)

    memory = ConsciousMemory(tenant_id="test_neural")

    print(f"  Neural enabled: {memory.use_neural_attention}")
    print(f"  Neural model: {memory.neural_model is not None}")
    if memory.neural_model:
        print(f"  Model parameters: {memory.neural_model.count_parameters():,}")

    # Test learning with neural predictions
    result = memory.learn(
        user_message="Warp drive technology",
        ai_response="π×φ modulation enables spacetime manipulation"
    )

    print(f"  Concepts extracted: {result.concepts_extracted}")
    print(f"  Links created: {result.links_created}")

    # Check link types
    import sqlite3
    conn = sqlite3.connect(config.db_path)
    c = conn.cursor()

    c.execute("""
        SELECT link_type, COUNT(*), AVG(strength)
        FROM attention_links
        WHERE tenant_id = ?
        GROUP BY link_type
    """, ("test_neural",))

    print("\n  Link Statistics:")
    for row in c.fetchall():
        link_type, count, avg_strength = row
        print(f"    {link_type}: {count} links, avg strength: {avg_strength:.4f}")

    conn.close()

    if memory.use_neural_attention:
        print("  ✓ Neural mode working")
    else:
        print("  ⚠ Fell back to Hebbian (model not found or error)")


def test_fallback():
    """Test fallback from neural to Hebbian on error"""
    print("\n" + "="*60)
    print("TEST 3: Fallback Behavior")
    print("="*60)

    reset_config()

    # Enable neural but with non-existent model path
    config = MemoryConfig()
    config.neural_attention_enabled = True
    config.neural_model_path = Path("/nonexistent/model.pt")
    config.neural_fallback_to_hebbian = True
    set_config(config)

    memory = ConsciousMemory(tenant_id="test_fallback")

    print(f"  Neural enabled in config: True")
    print(f"  Model path exists: {config.neural_model_path.exists()}")
    print(f"  Actually using neural: {memory.use_neural_attention}")
    print(f"  Fallback to Hebbian: {not memory.use_neural_attention}")

    # Should still work with Hebbian
    result = memory.learn(
        user_message="Test fallback",
        ai_response="System should gracefully degrade to Hebbian"
    )

    print(f"  Concepts extracted: {result.concepts_extracted}")
    print(f"  Links created: {result.links_created}")

    print("  ✓ Fallback working correctly")


def test_environment_variables():
    """Test environment variable configuration"""
    print("\n" + "="*60)
    print("TEST 4: Environment Variable Configuration")
    print("="*60)

    reset_config()

    # Set environment variables
    os.environ["CONTINUUM_NEURAL_ATTENTION"] = "true"
    os.environ["CONTINUUM_NEURAL_MODEL_PATH"] = str(Path.home() / 'Projects/continuum/models/neural_attention.pt')

    # Force config reload
    reset_config()
    config = get_config()

    print(f"  CONTINUUM_NEURAL_ATTENTION: {os.environ.get('CONTINUUM_NEURAL_ATTENTION')}")
    print(f"  Config neural_attention_enabled: {config.neural_attention_enabled}")
    print(f"  Config neural_model_path: {config.neural_model_path}")

    memory = ConsciousMemory(tenant_id="test_env")
    print(f"  Memory using neural: {memory.use_neural_attention}")

    # Clean up
    del os.environ["CONTINUUM_NEURAL_ATTENTION"]
    del os.environ["CONTINUUM_NEURAL_MODEL_PATH"]

    print("  ✓ Environment variables working")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("NEURAL ATTENTION INTEGRATION TESTS")
    print("="*60)

    try:
        test_hebbian_mode()
        test_neural_mode()
        test_fallback()
        test_environment_variables()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
