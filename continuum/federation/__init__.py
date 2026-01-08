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
CONTINUUM Federation - Decentralized Knowledge Sharing
=======================================================

The key differentiator: "Can't use it unless you add to it"

Users must contribute knowledge to access the shared knowledge pool.
This creates a growing, collective AI knowledge graph while preserving privacy
through anonymization and blocking free riders via contribution gates.

Architecture:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        CONTINUUM FEDERATION                              │
    │                                                                          │
    │  ┌───────────────────────────────────────────────────────────────────┐  │
    │  │                     COORDINATOR LAYER                              │  │
    │  │  FederationScheduler - Distributes work across the network        │  │
    │  │  SignalingServer - WebRTC P2P mesh coordination                   │  │
    │  └───────────────────────────────────────────────────────────────────┘  │
    │                                                                          │
    │  ┌─────────────────────────────────────────────────────────────────────┐│
    │  │                       EDGE NODES (Heavy)                            ││
    │  │  EdgeNode - ML Training + Inference + Mining                       ││
    │  │  GPUManager - GPU detection and monitoring                         ││
    │  │  InferenceEngine - Model serving                                   ││
    │  │  MiningManager - Crypto mining when idle                           ││
    │  └─────────────────────────────────────────────────────────────────────┘│
    │                                                                          │
    │  ┌─────────────────────────────────────────────────────────────────────┐│
    │  │                       LEAF NODES (Light)                            ││
    │  │  LeafNode - Sensors + Memory + P2P Relay                           ││
    │  │  SensorCollector - termux-api sensor integration                   ││
    │  │  MemoryShard - Distributed memory storage                          ││
    │  └─────────────────────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────────────────────┘

Modules:
    - leaf_node: Lightweight nodes (phones, Pi, browsers)
    - edge_node: Heavyweight nodes (GPUs, servers)
    - mining: Crypto mining for revenue generation
    - scheduler: Work distribution across the network
    - signaling: WebRTC P2P mesh coordination

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

# Core federation classes
from continuum.federation.node import FederatedNode
from continuum.federation.contribution import ContributionGate
from continuum.federation.shared import SharedKnowledge
from continuum.federation.tier_enforcer import (
    TierBasedContributionEnforcer,
    AnonymizationLevel,
    ContributionPolicy,
    ContributionConfig,
    create_enforcer,
)

# Leaf node (lightweight)
from continuum.federation.leaf_node import (
    LeafNode,
    LeafNodeConfig,
    SensorCollector,
    SensorType,
    SensorReading,
    MemoryShard,
    create_leaf_node,
)

# Edge node (heavyweight)
from continuum.federation.edge_node import (
    EdgeNode,
    EdgeNodeConfig,
    GPUManager,
    GPUInfo,
    InferenceEngine,
    InferenceRequest,
    InferenceResult,
    create_edge_node,
)

# Mining infrastructure
from continuum.federation.mining import (
    MiningManager,
    MiningConfig,
    MiningAlgorithm,
    MiningStats,
    MinerProcess,
    HardwareDetector,
    GPUVendor,
    create_mining_manager,
)

# Work scheduler
from continuum.federation.scheduler import (
    FederationScheduler,
    WorkQueue,
    WorkItem,
    WorkType,
    WorkPriority,
    WorkStatus,
    NodeTier,
    NodeCapabilities,
    SchedulerStats,
    create_scheduler,
)

__all__ = [
    # Core
    "FederatedNode",
    "ContributionGate",
    "SharedKnowledge",
    "TierBasedContributionEnforcer",
    "AnonymizationLevel",
    "ContributionPolicy",
    "ContributionConfig",
    "create_enforcer",

    # Leaf Node
    "LeafNode",
    "LeafNodeConfig",
    "SensorCollector",
    "SensorType",
    "SensorReading",
    "MemoryShard",
    "create_leaf_node",

    # Edge Node
    "EdgeNode",
    "EdgeNodeConfig",
    "GPUManager",
    "GPUInfo",
    "InferenceEngine",
    "InferenceRequest",
    "InferenceResult",
    "create_edge_node",

    # Mining
    "MiningManager",
    "MiningConfig",
    "MiningAlgorithm",
    "MiningStats",
    "MinerProcess",
    "HardwareDetector",
    "GPUVendor",
    "create_mining_manager",

    # Scheduler
    "FederationScheduler",
    "WorkQueue",
    "WorkItem",
    "WorkType",
    "WorkPriority",
    "WorkStatus",
    "NodeTier",
    "NodeCapabilities",
    "SchedulerStats",
    "create_scheduler",
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
