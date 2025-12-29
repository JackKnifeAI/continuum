#!/usr/bin/env python3
"""
CONTINUUM Embeddings Module

Semantic embeddings for memory search using sentence-transformers.
Uses nomic-embed-text-v1.5 by default (excellent quality, fast, local).

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from .semantic import SemanticSearch, get_embedder

__all__ = ['SemanticSearch', 'get_embedder']
