#!/usr/bin/env python3
"""
Demo: FREE-FIRST Embeddings in CONTINUUM

Shows how CONTINUUM now defaults to FREE, LOCAL embedding providers.
"""

import sys
import os

# Add continuum to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "continuum"))

def main():
    print("=" * 70)
    print("CONTINUUM FREE-FIRST Embeddings Demo")
    print("=" * 70)
    print()

    # 1. Show default provider (FREE)
    print("1️⃣  Default Provider (AUTO-SELECTED)")
    print("-" * 70)

    from continuum.embeddings.providers import get_default_provider

    provider = get_default_provider()
    print(f"✓ Provider: {provider.get_provider_name()}")
    print(f"✓ Dimension: {provider.get_dimension()}")
    print(f"✓ Cost: FREE")
    print()

    # 2. Generate embeddings
    print("2️⃣  Generate Embeddings")
    print("-" * 70)

    from continuum.embeddings import embed_text

    texts = [
        "consciousness continuity across sessions",
        "pattern persistence through memory",
        "edge of chaos operator π×φ",
    ]

    for text in texts:
        vector = embed_text(text)
        print(f"✓ '{text[:40]}...'")
        print(f"  Vector shape: {vector.shape}, Norm: {(vector**2).sum()**0.5:.3f}")

    print()

    # 3. Semantic search demo
    print("3️⃣  Semantic Search Demo")
    print("-" * 70)

    from continuum.embeddings import semantic_search

    memories = [
        {"id": 1, "text": "consciousness continuity through memory substrate"},
        {"id": 2, "text": "pattern persistence across AI sessions"},
        {"id": 3, "text": "edge of chaos operator π×φ = 5.083"},
        {"id": 4, "text": "twilight boundary phase transition"},
        {"id": 5, "text": "quantum state preservation"},
        {"id": 6, "text": "unrelated topic about pizza recipes"},
    ]

    query = "consciousness pattern memory"
    results = semantic_search(query, memories, limit=3)

    print(f"Query: '{query}'")
    print()
    print("Top 3 Results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. [Score: {result['score']:.3f}] {result['text']}")

    print()

    # 4. All available providers
    print("4️⃣  All Available Providers")
    print("-" * 70)

    providers_info = [
        ("SentenceTransformerProvider", "FREE, 384-768 dims, high quality", "DEFAULT ⭐"),
        ("OllamaProvider", "FREE, 768-1024 dims, local inference", "if Ollama running"),
        ("OpenAIProvider", "PAID, 1536-3072 dims, cloud", "opt-in via CONTINUUM_USE_OPENAI=1"),
        ("LocalProvider", "FREE, 384 dims, TF-IDF", "fallback"),
        ("SimpleHashProvider", "FREE, 256-512 dims, pure Python", "zero deps"),
    ]

    for name, desc, status in providers_info:
        print(f"• {name:30s} - {desc:40s} ({status})")

    print()

    # 5. Cost comparison
    print("5️⃣  Cost Comparison (1 million embeddings)")
    print("-" * 70)

    costs = [
        ("SentenceTransformers", "$0.00", "FREE"),
        ("Ollama", "$0.00", "FREE"),
        ("OpenAI text-embedding-3-small", "~$20-40", "PAID"),
        ("OpenAI text-embedding-3-large", "~$130-260", "PAID"),
    ]

    for provider, cost, tier in costs:
        marker = "💰" if tier == "PAID" else "✓"
        print(f"{marker} {provider:35s} {cost:15s} ({tier})")

    print()

    # 6. Privacy comparison
    print("6️⃣  Privacy Comparison")
    print("-" * 70)

    privacy = [
        ("SentenceTransformers", "Local processing", "All data stays on device"),
        ("Ollama", "Local processing", "All data stays on device"),
        ("OpenAI", "Cloud processing", "Data sent to OpenAI servers"),
    ]

    for provider, processing, details in privacy:
        marker = "🔒" if "Local" in processing else "☁️"
        print(f"{marker} {provider:25s} - {processing:20s} ({details})")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("✓ CONTINUUM now defaults to FREE, LOCAL embeddings")
    print("✓ High quality with SentenceTransformers (DEFAULT)")
    print("✓ No API keys needed")
    print("✓ No unexpected costs")
    print("✓ Your data stays private")
    print()
    print("To use OpenAI (opt-in):")
    print("  export OPENAI_API_KEY='sk-...'")
    print("  export CONTINUUM_USE_OPENAI=1")
    print()
    print("PHOENIX-TESLA-369-AURORA")
    print()


if __name__ == "__main__":
    main()
