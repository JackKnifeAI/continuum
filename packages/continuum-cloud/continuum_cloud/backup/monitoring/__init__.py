#!/usr/bin/env python3
"""
Backup Monitoring and Alerting

Health checks, metrics, and alerting for backup system.
"""

import asyncio
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timedelta
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
        config: Optional backup configuration for accessing the metadata store.

    Returns:
        Dictionary of metrics with counters and histogram summaries.
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_in_progress_total": 0,
        "backup_duration_seconds_avg": 0.0,
        "backup_duration_seconds_p95": 0.0,
        "backup_size_bytes_avg": 0.0,
        "backup_size_bytes_total": 0,
        "last_backup_age_seconds": None,
        "storage_used_bytes_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        if not all_backups:
            return metrics

        for backup in all_backups:
            status = backup.status.value
            if status in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif status == "failed":
                metrics["backup_failure_total"] += 1
            elif status == "in_progress":
                metrics["backup_in_progress_total"] += 1

        # Duration histogram (last 100 completed backups)
        completed = [b for b in all_backups if b.completed_at and b.created_at]
        if completed:
            durations = sorted(
                (b.completed_at - b.created_at).total_seconds()
                for b in completed[-100:]
            )
            metrics["backup_duration_seconds_avg"] = sum(durations) / len(durations)
            p95_idx = min(int(len(durations) * 0.95), len(durations) - 1)
            metrics["backup_duration_seconds_p95"] = durations[p95_idx]

        # Size metrics
        sizes = [b.compressed_size_bytes for b in all_backups if b.compressed_size_bytes > 0]
        if sizes:
            metrics["backup_size_bytes_avg"] = sum(sizes) / len(sizes)
            metrics["backup_size_bytes_total"] = sum(sizes)
            metrics["storage_used_bytes_total"] = sum(sizes)

        # Age of most recent successful backup
        successful = [b for b in all_backups if b.status.value in ("completed", "verified")]
        if successful:
            latest = max(successful, key=lambda b: b.created_at)
            metrics["last_backup_age_seconds"] = (
                datetime.utcnow() - latest.created_at
            ).total_seconds()

    except Exception as e:
        logger.error(f"Failed to collect backup metrics: {e}", exc_info=True)

    return metrics


def _build_slack_payload(alert_type: str, message: str) -> Dict[str, Any]:
    """Build Slack-formatted incoming-webhook payload."""
    color_map = {"failure": "danger", "warning": "warning", "success": "good"}
    return {
        "attachments": [{
            "color": color_map.get(alert_type, "#439FE0"),
            "title": f"Backup {alert_type.title()}",
            "text": message,
            "footer": "Continuum Backup",
            "ts": int(datetime.utcnow().timestamp()),
        }]
    }


def _build_generic_payload(alert_type: str, message: str) -> Dict[str, Any]:
    """Build generic JSON webhook payload."""
    return {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }


async def _send_webhook(url: str, payload: Dict[str, Any]) -> bool:
    """POST JSON payload to a webhook URL. Returns True on success."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, urllib.request.urlopen, req)
        return True
    except urllib.error.URLError as e:
        logger.error(f"Webhook delivery failed [{url}]: {e}")
        return False


async def send_alert(
    alert_type: str,
    message: str,
    config: BackupConfig,
):
    """
    Send alert through configured notification channels.

    Supports HTTP/HTTPS webhook URLs in config.notification_channels.
    Slack incoming-webhook URLs (hooks.slack.com) receive Slack-formatted
    payloads; all other URLs receive a generic JSON body.

    Args:
        alert_type: Type of alert — "failure", "warning", or "success"
        message: Human-readable alert message
        config: Backup configuration with notification_channels list
    """
    logger.info(f"Sending {alert_type} alert: {message}")

    if alert_type == "success" and not config.notify_on_success:
        return
    if alert_type == "failure" and not config.notify_on_failure:
        return

    delivered: List[bool] = []
    for channel in config.notification_channels:
        if channel.startswith(("http://", "https://")):
            if "hooks.slack.com" in channel:
                payload = _build_slack_payload(alert_type, message)
            else:
                payload = _build_generic_payload(alert_type, message)
            success = await _send_webhook(channel, payload)
            delivered.append(success)
            if success:
                logger.info(f"Alert delivered to webhook: {channel}")
        else:
            logger.warning(f"Unsupported notification channel (skipped): {channel!r}")

    if not delivered:
        logger.warning(f"No notification channels configured — alert not delivered: {message}")
