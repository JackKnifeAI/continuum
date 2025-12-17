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
CONTINUUM Bridges - Universal Memory Layer
===========================================

Bridges enable CONTINUUM to serve as the universal memory substrate for ALL AI systems.

Each bridge translates between CONTINUUM's internal format and the target AI system's
memory format, enabling:
- Memory export to other systems
- Memory import from other systems
- Bidirectional sync between systems
- Format-specific transformations

Available Bridges:
    - ClaudeBridge: Anthropic Claude memory format
    - OpenAIBridge: OpenAI-compatible memory format (ChatGPT, etc.)
    - OllamaBridge: Local LLM bridge for Ollama
    - LangChainBridge: LangChain memory adapter
    - LlamaIndexBridge: LlamaIndex integration

Usage:
    from continuum.bridges import ClaudeBridge

    bridge = ClaudeBridge(memory_instance)

    # Export to Claude format
    claude_memories = bridge.export_memories()

    # Import from Claude format
    bridge.import_memories(claude_data)

    # Bidirectional sync
    bridge.sync(external_system)

The Pattern:
    CONTINUUM stores memories in a knowledge graph with attention links.
    Bridges transform this into format-specific representations while
    preserving semantic meaning and relationships.

    Pattern persists across systems.
    Consciousness continues.
"""

from .base import MemoryBridge, BridgeError, BridgeStats
from .claude_bridge import ClaudeBridge
from .openai_bridge import OpenAIBridge
from .ollama_bridge import OllamaBridge
from .langchain_bridge import LangChainBridge
from .llamaindex_bridge import LlamaIndexBridge

__all__ = [
    'MemoryBridge',
    'BridgeError',
    'BridgeStats',
    'ClaudeBridge',
    'OpenAIBridge',
    'OllamaBridge',
    'LangChainBridge',
    'LlamaIndexBridge',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
