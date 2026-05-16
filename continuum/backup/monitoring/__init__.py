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

import asyncio
import json
import logging
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

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
        config: Optional backup configuration to query the metadata store

    Returns:
        Dictionary of metrics with counters and histogram sample lists
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_duration_seconds": [],   # histogram samples
        "backup_size_bytes": [],          # histogram samples
        "restore_duration_seconds": [],   # histogram samples (populated externally)
        "retention_deletions_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                metrics["backup_duration_seconds"].append(duration)

            size = backup.compressed_size_bytes or backup.original_size_bytes
            if size > 0:
                metrics["backup_size_bytes"].append(size)

        logger.debug(
            "Metrics collected: %d successful, %d failed, %d samples",
            metrics["backup_success_total"],
            metrics["backup_failure_total"],
            len(metrics["backup_duration_seconds"]),
        )

    except Exception as e:
        logger.error(f"Failed to collect backup metrics: {e}")

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

    channels: List[str] = config.notification_channels
    if not channels:
        logger.warning(f"No notification channels configured; alert dropped: {message}")
        return

    loop = asyncio.get_event_loop()
    sent = 0
    for channel in channels:
        try:
            if channel.startswith(("http://", "https://")):
                success = await loop.run_in_executor(
                    None, _sync_webhook, channel, alert_type, message
                )
            elif channel.startswith("slack:"):
                success = await loop.run_in_executor(
                    None, _sync_slack, channel[6:], alert_type, message
                )
            elif channel.startswith("pagerduty:"):
                success = await loop.run_in_executor(
                    None, _sync_pagerduty, channel[10:], alert_type, message
                )
            else:
                logger.warning(f"Unknown notification channel format: {channel!r}")
                success = False

            if success:
                sent += 1
        except Exception as e:
            logger.error(f"Failed to deliver alert to {channel!r}: {e}")

    logger.info(f"Alert dispatched to {sent}/{len(channels)} channels: {message}")

def _post_json(url: str, payload: Dict[str, Any], timeout: int = 10) -> bool:
    """POST a JSON payload to a URL; returns True on HTTP 2xx."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return resp.status < 300
    except Exception as e:
        logger.error(f"HTTP POST to {url} failed: {e}")
        return False


def _sync_webhook(url: str, alert_type: str, message: str) -> bool:
    """Generic HTTP webhook notification."""
    payload: Dict[str, Any] = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "continuum-backup",
    }
    return _post_json(url, payload)


def _sync_slack(webhook_url: str, alert_type: str, message: str) -> bool:
    """Slack incoming-webhook notification."""
    emoji = {"failure": ":x:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":bell:"
    )
    payload: Dict[str, Any] = {
        "text": f"{emoji} *Continuum Backup {alert_type.upper()}*\n{message}"
    }
    return _post_json(webhook_url, payload)


def _sync_pagerduty(routing_key: str, alert_type: str, message: str) -> bool:
    """PagerDuty Events API v2 notification."""
    severity = {"failure": "critical", "warning": "warning", "success": "info"}.get(
        alert_type, "info"
    )
    event_action = "trigger" if alert_type == "failure" else "resolve"
    payload: Dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": event_action,
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "continuum-backup",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    return _post_json("https://events.pagerduty.com/v2/enqueue", payload)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
