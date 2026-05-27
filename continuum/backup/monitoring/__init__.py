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
Backup Monitoring and Alerting

Health checks, metrics, and alerting for backup system.
"""

import json
import logging
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)


async def get_backup_health(config: BackupConfig) -> BackupHealth:
    """
    Get overall backup system health.

    Checks:
    - Last backup time (SLA compliance)
    - Recent backup failures
    - Storage usage
    - RTO/RPO compliance

    Args:
        config: Backup configuration

    Returns:
        BackupHealth status
    """
    logger.info("Checking backup system health")

    health = BackupHealth(healthy=True)

    try:
        # Get metadata store
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)

        # Get all backups
        all_backups = metadata_store.list_backups()
        health.total_backups = len(all_backups)

        if not all_backups:
            health.healthy = False
            health.errors.append("No backups found")
            return health

        # Find last successful backup
        successful_backups = [
            b for b in all_backups
            if b.status.value in ['completed', 'verified']
        ]

        if successful_backups:
            latest_backup = max(successful_backups, key=lambda b: b.created_at)
            health.last_backup_time = latest_backup.created_at
            health.last_successful_backup = latest_backup.backup_id
        else:
            health.healthy = False
            health.errors.append("No successful backups found")

        # Check RPO compliance
        if health.last_backup_time:
            age_minutes = (datetime.utcnow() - health.last_backup_time).total_seconds() / 60

            if age_minutes > config.target_rpo_minutes:
                health.rpo_compliant = False
                health.warnings.append(
                    f"RPO SLA breach: Last backup {age_minutes:.1f} minutes ago "
                    f"(target: {config.target_rpo_minutes} minutes)"
                )
                health.healthy = False

        # Count failed backups in last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        health.failed_backups_24h = len([
            b for b in all_backups
            if b.created_at > cutoff_time and b.status.value == 'failed'
        ])

        if health.failed_backups_24h > 3:
            health.warnings.append(
                f"High failure rate: {health.failed_backups_24h} failed backups in last 24h"
            )

        # Calculate average backup duration
        completed_backups = [
            b for b in all_backups
            if b.completed_at and b.created_at
        ]

        if completed_backups:
            total_duration = sum(
                (b.completed_at - b.created_at).total_seconds()
                for b in completed_backups[-10:]  # Last 10 backups
            )
            health.average_backup_duration_seconds = total_duration / min(10, len(completed_backups))

        # Calculate total storage used
        health.total_storage_used_bytes = sum(
            b.compressed_size_bytes for b in all_backups
        )

        # Check RTO (can we restore within target?)
        # RTO check would require actual restore test
        # For now, estimate based on average restore time
        estimated_restore_minutes = health.average_backup_duration_seconds / 60

        if estimated_restore_minutes > config.target_rto_minutes:
            health.rto_compliant = False
            health.warnings.append(
                f"RTO may not be achievable: Estimated {estimated_restore_minutes:.1f} minutes "
                f"(target: {config.target_rto_minutes} minutes)"
            )

        logger.info(
            f"Backup health: {'healthy' if health.healthy else 'unhealthy'}, "
            f"{health.total_backups} backups, "
            f"{health.total_storage_used_bytes / (1024**3):.2f} GB used"
        )

        return health

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        health.healthy = False
        health.errors.append(str(e))
        return health


def get_backup_metrics(config: Optional[BackupConfig] = None) -> Dict[str, Any]:
    """
    Get backup system metrics for monitoring.

    Returns metrics suitable for Prometheus, CloudWatch, etc.

    Args:
        config: Backup configuration (required to query metadata store)

    Returns:
        Dictionary of metrics with counters, sums, and averages
    """
    metrics: Dict[str, Any] = {
        # Counters
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_in_progress_total": 0,
        # backup_duration_seconds histogram components
        "backup_duration_seconds_sum": 0.0,
        "backup_duration_seconds_count": 0,
        "backup_duration_seconds_avg": 0.0,
        # backup_size_bytes histogram components
        "backup_size_bytes_sum": 0,
        "backup_size_bytes_count": 0,
        "backup_size_bytes_avg": 0.0,
        # Gauges
        "total_storage_bytes": 0,
        "last_backup_age_seconds": -1.0,  # -1 means no backup found
        # restore_duration_seconds tracked separately (not stored in BackupMetadata)
        "restore_duration_seconds_sum": 0.0,
        "restore_duration_seconds_count": 0,
        # retention_deletions_total requires external tracking; not in BackupMetadata
        "retention_deletions_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        if not all_backups:
            return metrics

        now = datetime.utcnow()

        for backup in all_backups:
            status = backup.status.value
            if status in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif status == "failed":
                metrics["backup_failure_total"] += 1
            elif status == "in_progress":
                metrics["backup_in_progress_total"] += 1

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                metrics["backup_duration_seconds_sum"] += duration
                metrics["backup_duration_seconds_count"] += 1

            size = backup.compressed_size_bytes or backup.original_size_bytes
            metrics["backup_size_bytes_sum"] += size
            metrics["backup_size_bytes_count"] += 1
            metrics["total_storage_bytes"] += size

        if metrics["backup_duration_seconds_count"] > 0:
            metrics["backup_duration_seconds_avg"] = (
                metrics["backup_duration_seconds_sum"]
                / metrics["backup_duration_seconds_count"]
            )

        if metrics["backup_size_bytes_count"] > 0:
            metrics["backup_size_bytes_avg"] = (
                metrics["backup_size_bytes_sum"] / metrics["backup_size_bytes_count"]
            )

        successful = [
            b for b in all_backups if b.status.value in ("completed", "verified")
        ]
        if successful:
            latest = max(successful, key=lambda b: b.created_at)
            metrics["last_backup_age_seconds"] = (now - latest.created_at).total_seconds()

        logger.debug(
            f"Collected backup metrics: {metrics['backup_success_total']} success, "
            f"{metrics['backup_failure_total']} failure, "
            f"{metrics['total_storage_bytes'] / (1024 ** 3):.2f} GB total"
        )

    except Exception as e:
        logger.error(f"Failed to collect backup metrics: {e}", exc_info=True)

    return metrics


async def send_alert(
    alert_type: str,
    message: str,
    config: BackupConfig,
):
    """
    Send alert through configured channels.

    Args:
        alert_type: Type of alert (failure, warning, success)
        message: Alert message
        config: Backup configuration with notification channels
    """
    logger.info(f"Sending {alert_type} alert: {message}")

    # Skip if notifications disabled
    if alert_type == 'success' and not config.notify_on_success:
        return

    if alert_type == 'failure' and not config.notify_on_failure:
        return

    if not config.notification_channels:
        logger.debug("No notification channels configured")
        return

    payload = json.dumps({
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }).encode("utf-8")

    for channel in config.notification_channels:
        if channel.startswith(("http://", "https://")):
            _send_webhook(channel, payload)
        else:
            logger.warning(f"Unsupported notification channel (expected URL): {channel}")

def _send_webhook(url: str, payload: bytes) -> None:
    """POST a JSON payload to a webhook URL (Slack, PagerDuty, custom)."""
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"Alert sent to {url}: HTTP {resp.status}")
    except Exception as e:
        logger.error(f"Failed to send alert to {url}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
