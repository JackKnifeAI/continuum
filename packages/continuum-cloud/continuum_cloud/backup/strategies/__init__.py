#!/usr/bin/env python3
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
