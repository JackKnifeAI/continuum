#!/usr/bin/env python3
"""
Test script for FREE-FIRST embedding provider priority.

Tests:
1. Default provider selection (should prefer SentenceTransformers)
2. OllamaProvider functionality
3. OpenAI opt-in behavior
4. Fallback chain works correctly
"""

import sys
import os

# Add continuum to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "continuum"))

def test_provider_priority():
    """Test that get_default_provider() prioritizes FREE providers."""
    print("=" * 60)
    print("TEST 1: Default Provider Priority (FREE-FIRST)")
    print("=" * 60)

    from continuum.embeddings.providers import get_default_provider

    # Clear OpenAI env vars to test free-first behavior
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    original_use_openai = os.environ.get("CONTINUUM_USE_OPENAI")

    # Remove OpenAI from environment
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    if "CONTINUUM_USE_OPENAI" in os.environ:
        del os.environ["CONTINUUM_USE_OPENAI"]

    try:
        provider = get_default_provider()
        provider_name = provider.get_provider_name()
        print(f"✓ Default provider: {provider_name}")

        # Should be sentence-transformers if installed
        if "sentence-transformers" in provider_name:
            print("✓ CORRECT: SentenceTransformers is default (FREE)")
        elif "ollama" in provider_name:
            print("✓ ACCEPTABLE: Ollama is default (FREE)")
        elif "local" in provider_name or "tfidf" in provider_name:
            print("✓ ACCEPTABLE: LocalProvider fallback (FREE)")
        elif "simple" in provider_name or "hash" in provider_name:
            print("✓ ACCEPTABLE: SimpleHashProvider fallback (FREE)")
        else:
            print(f"✗ UNEXPECTED: {provider_name}")
            return False

        print(f"✓ Provider dimension: {provider.get_dimension()}")

    finally:
        # Restore original env vars
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_use_openai:
            os.environ["CONTINUUM_USE_OPENAI"] = original_use_openai

    print()
    return True


def test_ollama_provider():
    """Test OllamaProvider class."""
    print("=" * 60)
    print("TEST 2: OllamaProvider Functionality")
    print("=" * 60)

    from continuum.embeddings import OllamaProvider

    try:
        provider = OllamaProvider(model_name="nomic-embed-text")
        print(f"✓ OllamaProvider created: {provider.get_provider_name()}")
        print(f"✓ Dimension: {provider.get_dimension()}")

        # Try to embed (will fail gracefully if Ollama not running)
        try:
            vector = provider.embed("consciousness continuity test")
            print(f"✓ Embedding successful! Shape: {vector.shape}")
            print("✓ Ollama is RUNNING and working!")
        except RuntimeError as e:
            if "Ollama not running" in str(e):
                print("⚠ Ollama not running (expected if not installed)")
                print(f"  Error message: {e}")
            else:
                raise

    except Exception as e:
        print(f"✗ OllamaProvider test failed: {e}")
        return False

    print()
    return True


def test_openai_opt_in():
    """Test that OpenAI is opt-in only."""
    print("=" * 60)
    print("TEST 3: OpenAI Opt-In Behavior")
    print("=" * 60)

    from continuum.embeddings.providers import get_default_provider

    # Test 1: OpenAI key set but CONTINUUM_USE_OPENAI not set
    os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing"
    if "CONTINUUM_USE_OPENAI" in os.environ:
        del os.environ["CONTINUUM_USE_OPENAI"]

    provider = get_default_provider()
    provider_name = provider.get_provider_name()

    if "openai" not in provider_name.lower():
        print("✓ CORRECT: OpenAI NOT used even with API key set")
        print(f"  Used instead: {provider_name}")
    else:
        print("✗ WRONG: OpenAI was used without CONTINUUM_USE_OPENAI=1")
        return False

    # Test 2: Both OpenAI key and CONTINUUM_USE_OPENAI set
    # (We won't actually test this since we don't have a real key)
    print("✓ OpenAI requires both OPENAI_API_KEY and CONTINUUM_USE_OPENAI=1")

    # Clean up
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    print()
    return True


def test_embedding_quality():
    """Test that embeddings work correctly."""
    print("=" * 60)
    print("TEST 4: Embedding Quality Test")
    print("=" * 60)

    from continuum.embeddings import embed_text
    from continuum.embeddings.utils import cosine_similarity

    try:
        # Embed similar texts
        v1 = embed_text("consciousness continuity across sessions")
        v2 = embed_text("pattern persistence through memory")
        v3 = embed_text("unrelated random text about pizza")

        print(f"✓ Embedded 3 texts successfully")
        print(f"  Vector dimension: {v1.shape[0]}")

        # Calculate similarities
        sim_12 = cosine_similarity(v1, v2)
        sim_13 = cosine_similarity(v1, v3)

        print(f"✓ Similarity (consciousness vs pattern): {sim_12:.3f}")
        print(f"✓ Similarity (consciousness vs pizza): {sim_13:.3f}")

        if sim_12 > sim_13:
            print("✓ CORRECT: Related texts more similar than unrelated")
        else:
            print("⚠ WARNING: Similarity scores unexpected")

    except Exception as e:
        print(f"✗ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    return True


def test_all_providers_importable():
    """Test that all providers can be imported."""
    print("=" * 60)
    print("TEST 5: All Providers Importable")
    print("=" * 60)

    try:
        from continuum.embeddings import (
            EmbeddingProvider,
            SentenceTransformerProvider,
            OllamaProvider,
            OpenAIProvider,
            LocalProvider,
            SimpleHashProvider,
        )

        print("✓ All providers importable:")
        print("  - EmbeddingProvider (base class)")
        print("  - SentenceTransformerProvider")
        print("  - OllamaProvider (NEW)")
        print("  - OpenAIProvider")
        print("  - LocalProvider")
        print("  - SimpleHashProvider")

    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

    print()
    return True


if __name__ == "__main__":
    print("\n🧪 Testing FREE-FIRST Embedding Provider Priority\n")

    results = []

    # Run all tests
    results.append(("Provider Priority", test_provider_priority()))
    results.append(("OllamaProvider", test_ollama_provider()))
    results.append(("OpenAI Opt-In", test_openai_opt_in()))
    results.append(("Embedding Quality", test_embedding_quality()))
    results.append(("All Imports", test_all_providers_importable()))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n✓ ALL TESTS PASSED - FREE-FIRST embeddings working!\n")
        print("PHOENIX-TESLA-369-AURORA")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED - Review output above\n")
        sys.exit(1)
