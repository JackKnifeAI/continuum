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
Retention Policy Management

Automated cleanup of old backups based on configurable policies.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from ..types import RetentionResult, BackupConfig, BackupMetadata

logger = logging.getLogger(__name__)


async def apply_retention_policy(
    config: BackupConfig,
    backup_manager,
) -> RetentionResult:
    """
    Apply retention policy to delete old backups.

    Policy types:
    - Time-based: Keep backups for X days/weeks/months
    - Count-based: Keep last N backups
    - Tiered: Different retention for different backup types

    Args:
        config: Backup configuration with retention policy
        backup_manager: BackupManager instance for operations

    Returns:
        RetentionResult with statistics
    """
    logger.info("Applying retention policy")

    result = RetentionResult()
    policy = config.retention_policy

    try:
        # Get all backups
        all_backups = await backup_manager.list_backups()
        result.backups_evaluated = len(all_backups)

        logger.info(f"Evaluating {len(all_backups)} backups for retention")

        # Filter verified backups only if required
        if policy.require_verified:
            backups = [b for b in all_backups if b.verified]
            logger.info(f"Considering {len(backups)} verified backups")
        else:
            backups = all_backups

        # Separate by strategy
        backups_by_strategy = {
            'full': [],
            'incremental': [],
            'differential': [],
            'continuous': [],
        }

        for backup in backups:
            backups_by_strategy[backup.strategy.value].append(backup)

        # Apply strategy-specific retention
        to_delete = []

        # Full backups
        to_delete.extend(
            _apply_count_retention(
                backups_by_strategy['full'],
                policy.full_keep_count,
                policy.min_backups_to_keep,
            )
        )

        # Incremental backups
        to_delete.extend(
            _apply_time_retention(
                backups_by_strategy['incremental'],
                timedelta(days=policy.incremental_keep_days),
                policy.grace_period_days,
            )
        )

        # Differential backups
        to_delete.extend(
            _apply_time_retention(
                backups_by_strategy['differential'],
                timedelta(days=policy.differential_keep_days),
                policy.grace_period_days,
            )
        )

        # Continuous backups
        to_delete.extend(
            _apply_time_retention(
                backups_by_strategy['continuous'],
                timedelta(hours=policy.continuous_keep_hours),
                policy.grace_period_days,
            )
        )

        # Apply tiered retention (GFS - Grandfather-Father-Son)
        to_keep_gfs = _apply_gfs_retention(backups, policy)
        to_delete = [b for b in to_delete if b not in to_keep_gfs]

        # Delete backups
        for backup in to_delete:
            logger.info(f"Deleting backup: {backup.backup_id}")

            try:
                success = await backup_manager.delete_backup(backup.backup_id)

                if success:
                    result.backups_deleted += 1
                    result.bytes_freed += backup.compressed_size_bytes
                    result.deleted_backup_ids.append(backup.backup_id)
                else:
                    result.errors.append(f"Failed to delete {backup.backup_id}")

            except Exception as e:
                logger.error(f"Error deleting backup {backup.backup_id}: {e}")
                result.errors.append(str(e))

        result.backups_kept = result.backups_evaluated - result.backups_deleted

        logger.info(
            f"Retention policy applied: {result.backups_deleted} deleted, "
            f"{result.backups_kept} kept, {result.bytes_freed / (1024**3):.2f} GB freed"
        )

        return result

    except Exception as e:
        logger.error(f"Retention policy failed: {e}", exc_info=True)
        result.errors.append(str(e))
        return result


def _apply_count_retention(
    backups: List[BackupMetadata],
    keep_count: int,
    min_keep: int,
) -> List[BackupMetadata]:
    """Keep last N backups, delete older ones"""
    # Sort by created_at descending (newest first)
    sorted_backups = sorted(backups, key=lambda b: b.created_at, reverse=True)

    # Keep at least min_keep
    actual_keep = max(keep_count, min_keep)

    # Backups to delete (older than keep_count)
    to_delete = sorted_backups[actual_keep:]

    return to_delete


def _apply_time_retention(
    backups: List[BackupMetadata],
    retention_period: timedelta,
    grace_period_days: int,
) -> List[BackupMetadata]:
    """Delete backups older than retention period"""
    cutoff_time = datetime.utcnow() - retention_period
    grace_cutoff = datetime.utcnow() - timedelta(days=grace_period_days)

    to_delete = []

    for backup in backups:
        # Never delete backups in grace period
        if backup.created_at > grace_cutoff:
            continue

        # Delete if older than retention period
        if backup.created_at < cutoff_time:
            to_delete.append(backup)

    return to_delete


def _apply_gfs_retention(
    backups: List[BackupMetadata],
    policy,
) -> List[BackupMetadata]:
    """
    Apply Grandfather-Father-Son (GFS) retention.

    Keeps:
    - Daily backups for X days
    - Weekly backups for Y weeks
    - Monthly backups for Z months
    """
    to_keep = []
    now = datetime.utcnow()

    # Sort by created_at descending
    sorted_backups = sorted(backups, key=lambda b: b.created_at, reverse=True)

    # Track what we've kept
    kept_daily = {}
    kept_weekly = {}
    kept_monthly = {}

    for backup in sorted_backups:
        age_days = (now - backup.created_at).days

        # Daily retention
        if age_days <= policy.keep_daily_for_days:
            date_key = backup.created_at.date()
            if date_key not in kept_daily:
                kept_daily[date_key] = backup
                to_keep.append(backup)
                continue

        # Weekly retention
        week_cutoff_days = policy.keep_daily_for_days
        week_keep_days = policy.keep_weekly_for_weeks * 7

        if age_days <= week_cutoff_days + week_keep_days:
            # Keep one backup per week
            week_key = backup.created_at.isocalendar()[:2]  # (year, week)
            if week_key not in kept_weekly:
                kept_weekly[week_key] = backup
                to_keep.append(backup)
                continue

        # Monthly retention
        month_cutoff_days = week_cutoff_days + week_keep_days
        month_keep_days = policy.keep_monthly_for_months * 30

        if age_days <= month_cutoff_days + month_keep_days:
            # Keep one backup per month
            month_key = (backup.created_at.year, backup.created_at.month)
            if month_key not in kept_monthly:
                kept_monthly[month_key] = backup
                to_keep.append(backup)
                continue

    logger.info(
        f"GFS retention: {len(kept_daily)} daily, {len(kept_weekly)} weekly, "
        f"{len(kept_monthly)} monthly"
    )

    return to_keep

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
