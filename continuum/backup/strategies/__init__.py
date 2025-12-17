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
Backup Strategies

Different backup strategies for different RPO/RTO requirements.
"""

from .base import BackupStrategyBase
from .full import FullBackupStrategy
from .incremental import IncrementalBackupStrategy
from .differential import DifferentialBackupStrategy
from .continuous import ContinuousBackupStrategy

from ..types import BackupStrategy


def get_backup_strategy(strategy: BackupStrategy) -> BackupStrategyBase:
    """
    Get backup strategy implementation.

    Args:
        strategy: Backup strategy type

    Returns:
        BackupStrategyBase implementation
    """
    strategies = {
        BackupStrategy.FULL: FullBackupStrategy(),
        BackupStrategy.INCREMENTAL: IncrementalBackupStrategy(),
        BackupStrategy.DIFFERENTIAL: DifferentialBackupStrategy(),
        BackupStrategy.CONTINUOUS: ContinuousBackupStrategy(),
    }

    impl = strategies.get(strategy)
    if not impl:
        raise ValueError(f"Unknown backup strategy: {strategy}")

    return impl


__all__ = [
    'BackupStrategyBase',
    'FullBackupStrategy',
    'IncrementalBackupStrategy',
    'DifferentialBackupStrategy',
    'ContinuousBackupStrategy',
    'get_backup_strategy',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
