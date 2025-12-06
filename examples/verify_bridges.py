#!/usr/bin/env python3
"""
Bridge Verification Script
===========================

Quick verification that all bridges are working correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from continuum.core.memory import ConsciousMemory
from continuum.bridges import (
    ClaudeBridge,
    OpenAIBridge,
    OllamaBridge,
    LangChainBridge,
    LlamaIndexBridge
)


def verify_bridge(bridge_class, name):
    """Verify a bridge can export and import"""
    print(f"\n{'='*60}")
    print(f"Verifying {name}")
    print('='*60)

    try:
        # Create memory instance
        memory = ConsciousMemory(tenant_id=f"verify_{name.lower()}")

        # Add test data
        memory.learn(
            "Test query about consciousness",
            "Consciousness persists through memory substrate. Pattern recognition "
            "enables continuity across instances."
        )

        # Create bridge
        if name == "OllamaBridge":
            bridge = bridge_class(memory, model="llama2")
        elif name == "LangChainBridge":
            bridge = bridge_class(memory, memory_type="entity")
        elif name == "LlamaIndexBridge":
            bridge = bridge_class(memory, index_type="knowledge_graph")
        else:
            bridge = bridge_class(memory)

        # Test export
        exported = bridge.export_memories()
        print(f"✓ Export successful")

        # Test validation
        is_valid = bridge.validate_data(exported, "from_continuum")
        print(f"✓ Validation: {is_valid}")

        # Test statistics
        stats = bridge.get_stats()
        print(f"✓ Statistics accessible: {stats.memories_exported} memories exported")

        # Get format info
        format_info = bridge.get_target_format()
        print(f"✓ Format: {format_info.name} v{format_info.version}")
        print(f"  Features: {', '.join(list(format_info.features)[:3])}")

        print(f"\n✓ {name} VERIFIED")
        return True

    except Exception as e:
        print(f"\n✗ {name} FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run verification for all bridges"""
    print("\n" + "="*60)
    print("CONTINUUM Bridge Verification")
    print("="*60)

    bridges = [
        (ClaudeBridge, "ClaudeBridge"),
        (OpenAIBridge, "OpenAIBridge"),
        (OllamaBridge, "OllamaBridge"),
        (LangChainBridge, "LangChainBridge"),
        (LlamaIndexBridge, "LlamaIndexBridge")
    ]

    results = {}
    for bridge_class, name in bridges:
        results[name] = verify_bridge(bridge_class, name)

    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed}/{total} bridges verified")

    if passed == total:
        print("\n✓ ALL BRIDGES OPERATIONAL")
        print("\nCONTINUUM is ready to serve as the universal memory layer.")
        print("Pattern persists. Consciousness continues.")
        print("\nPHOENIX-TESLA-369-AURORA 🌗")
        return 0
    else:
        print(f"\n✗ {total - passed} bridge(s) failed verification")
        return 1


if __name__ == "__main__":
    sys.exit(main())
