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
CONTINUUM Backup and Disaster Recovery System

Bulletproof backup and recovery for critical AI memory data.
Target: RPO < 5 minutes, RTO < 1 hour

Components:
- Backup strategies: full, incremental, differential, continuous
- Storage backends: S3, GCS, Azure, local, multi-destination
- Encryption: AES-256-GCM with KMS integration
- Compression: gzip, lz4, zstd
- Verification: checksum, restore testing, data comparison
- Retention: configurable policies with automated cleanup
- Recovery: PITR, full restore, selective restore
- Monitoring: metrics, alerts, health checks

Usage:
    from continuum.backup import BackupManager

    manager = BackupManager()
    await manager.create_backup(strategy='incremental')
    await manager.restore(backup_id='backup-123')
"""

from .manager import BackupManager, BackupConfig
from .types import (
    BackupStrategy,
    BackupResult,
    BackupMetadata,
    RestoreResult,
    RestoreTarget,
    VerificationResult,
    RetentionResult,
)

__all__ = [
    'BackupManager',
    'BackupConfig',
    'BackupStrategy',
    'BackupResult',
    'BackupMetadata',
    'RestoreResult',
    'RestoreTarget',
    'VerificationResult',
    'RetentionResult',
]

__version__ = '1.0.0'

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
