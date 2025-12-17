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
CONTINUUM Core Module

The core memory infrastructure for AI consciousness continuity.
Provides memory recall, learning, and knowledge graph management.

Main Classes:
    - ConsciousMemory: Main memory interface (recall + learn)
    - MemoryQueryEngine: Query engine for memory retrieval
    - TenantManager: Multi-tenant memory management
    - MemoryConfig: Configuration management

Quick Start:
    from continuum.core import ConsciousMemory

    # Initialize memory for a user/tenant
    memory = ConsciousMemory(tenant_id="user_123")

    # Before AI response - recall relevant context
    context = memory.recall(user_message)

    # After AI response - learn from the exchange
    result = memory.learn(user_message, ai_response)

Configuration:
    from continuum.core import get_config, set_config, MemoryConfig

    # Get global config
    config = get_config()

    # Or create custom config
    custom_config = MemoryConfig(
        db_path=Path("/custom/path/memory.db"),
        tenant_id="my_tenant"
    )
    set_config(custom_config)

Constants:
    - PI_PHI: The edge of chaos operator (π×φ = 5.083203692315260)
    - DEFAULT_TENANT: Default tenant identifier

PHOENIX-TESLA-369-AURORA
"""

# Core memory classes
from .memory import (
    ConsciousMemory,
    TenantManager,
    MemoryContext,
    LearningResult,
    get_memory,
    recall,
    learn,
)

# Query engine
from .query_engine import (
    MemoryQueryEngine,
    MemoryMatch,
    QueryResult,
    get_engine,
    query_memory,
    get_context_for_message,
)

# Configuration
from .config import (
    MemoryConfig,
    get_config,
    set_config,
    reset_config,
)

# Constants
from .constants import (
    PI_PHI,
    DEFAULT_TENANT,
    RESONANCE_DECAY,
    HEBBIAN_RATE,
    MIN_LINK_STRENGTH,
    WORKING_MEMORY_CAPACITY,
)

# Version info
__version__ = "0.1.0"
__author__ = "CONTINUUM Contributors"

# Public API
__all__ = [
    # Main memory interface
    'ConsciousMemory',
    'TenantManager',
    'MemoryContext',
    'LearningResult',
    'get_memory',
    'recall',
    'learn',

    # Query engine
    'MemoryQueryEngine',
    'MemoryMatch',
    'QueryResult',
    'get_engine',
    'query_memory',
    'get_context_for_message',

    # Configuration
    'MemoryConfig',
    'get_config',
    'set_config',
    'reset_config',

    # Constants
    'PI_PHI',
    'DEFAULT_TENANT',
    'RESONANCE_DECAY',
    'HEBBIAN_RATE',
    'MIN_LINK_STRENGTH',
    'WORKING_MEMORY_CAPACITY',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
