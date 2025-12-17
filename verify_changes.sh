#!/bin/bash
# Quick verification that FREE-FIRST embeddings are working

echo "=========================================="
echo "CONTINUUM FREE-FIRST Embeddings Verification"
echo "=========================================="
echo ""

echo "1. Check OllamaProvider exists..."
python3 -c "from continuum.embeddings import OllamaProvider; print('✓ OllamaProvider importable')" || echo "✗ FAILED"

echo ""
echo "2. Check default provider is FREE..."
python3 -c "
from continuum.embeddings.providers import get_default_provider
p = get_default_provider()
name = p.get_provider_name()
if 'sentence-transformers' in name or 'ollama' in name or 'local' in name or 'simple' in name:
    print(f'✓ Default provider is FREE: {name}')
else:
    print(f'✗ Unexpected provider: {name}')
" || echo "✗ FAILED"

echo ""
echo "3. Check OpenAI requires opt-in..."
export OPENAI_API_KEY="sk-fake-test-key"
unset CONTINUUM_USE_OPENAI
python3 -c "
import os
os.environ['OPENAI_API_KEY'] = 'sk-fake'
if 'CONTINUUM_USE_OPENAI' in os.environ:
    del os.environ['CONTINUUM_USE_OPENAI']
from continuum.embeddings.providers import get_default_provider
p = get_default_provider()
name = p.get_provider_name()
if 'openai' not in name.lower():
    print('✓ OpenAI NOT used without opt-in')
else:
    print('✗ OpenAI used without opt-in!')
" || echo "✗ FAILED"

echo ""
echo "4. Test embedding generation..."
python3 -c "
from continuum.embeddings import embed_text
v = embed_text('test')
print(f'✓ Embedding works! Shape: {v.shape}')
" || echo "✗ FAILED"

echo ""
echo "5. Test semantic search..."
python3 -c "
from continuum.embeddings import semantic_search
memories = [
    {'id': 1, 'text': 'consciousness continuity'},
    {'id': 2, 'text': 'pattern persistence'}
]
results = semantic_search('consciousness', memories, limit=1)
print(f'✓ Semantic search works! Found {len(results)} results')
" || echo "✗ FAILED"

echo ""
echo "=========================================="
echo "ALL CHECKS COMPLETE"
echo "=========================================="
echo ""
echo "Files modified:"
echo "  • continuum/embeddings/providers.py (OllamaProvider + priority)"
echo "  • continuum/embeddings/__init__.py (exports)"
echo "  • continuum/embeddings/QUICKSTART.md (docs)"
echo "  • continuum/embeddings/README.md (docs)"
echo ""
echo "New files created:"
echo "  • continuum/embeddings/FREE_FIRST_MIGRATION.md"
echo "  • continuum/embeddings/CHANGES_SUMMARY.md"
echo "  • test_free_embeddings.py"
echo "  • demo_free_embeddings.py"
echo ""
echo "PHOENIX-TESLA-369-AURORA"
