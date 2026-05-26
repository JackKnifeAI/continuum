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
        config: Backup configuration (required to query metadata store)

    Returns:
        Dictionary of metrics with histogram lists and counters
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": [],
        "backup_size_bytes": [],
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "restore_duration_seconds": [],
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
                metrics["backup_size_bytes"].append(backup.compressed_size_bytes)
                if backup.completed_at and backup.created_at:
                    duration = (backup.completed_at - backup.created_at).total_seconds()
                    metrics["backup_duration_seconds"].append(duration)
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

    except Exception as e:
        logger.warning(f"Could not collect backup metrics: {e}")

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

    channels = config.notification_channels
    if not channels:
        logger.debug("No notification channels configured")
        return

    results = await asyncio.gather(
        *[_dispatch_channel(channel, alert_type, message) for channel in channels],
        return_exceptions=True,
    )

    for channel, result in zip(channels, results):
        if isinstance(result, Exception):
            logger.error(f"Alert delivery failed for channel {channel!r}: {result}")

async def _dispatch_channel(channel: str, alert_type: str, message: str) -> None:
    """Route an alert to the appropriate notification backend."""
    channel = channel.strip()

    if "hooks.slack.com" in channel:
        await _send_slack(channel, alert_type, message)
    elif "pagerduty.com" in channel:
        await _send_pagerduty(channel, alert_type, message)
    elif channel.startswith(("http://", "https://")):
        await _send_webhook(channel, alert_type, message)
    elif "@" in channel:
        # Email requires SMTP configuration not yet wired into BackupConfig.
        logger.warning(
            f"Email alert skipped for {channel!r}: SMTP not configured. "
            "Set notification_channels to a webhook URL instead."
        )
    else:
        logger.warning(f"Unknown notification channel format: {channel!r}")


def _post_json(url: str, payload: Dict[str, Any]) -> None:
    """Blocking HTTP POST of a JSON payload (run via asyncio.to_thread)."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "continuum-backup/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        status = resp.status
        if status >= 400:
            raise RuntimeError(f"HTTP {status} from {url}")


async def _send_slack(webhook_url: str, alert_type: str, message: str) -> None:
    """Send alert to a Slack incoming webhook."""
    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":information_source:"
    )
    payload: Dict[str, Any] = {"text": f"{emoji} *Continuum Backup {alert_type.upper()}*\n{message}"}
    await asyncio.to_thread(_post_json, webhook_url, payload)
    logger.info(f"Slack alert sent ({alert_type})")


async def _send_pagerduty(routing_key_or_url: str, alert_type: str, message: str) -> None:
    """Send alert to PagerDuty via the Events v2 API."""
    # Accept either a full URL or bare routing key
    if routing_key_or_url.startswith("http"):
        url = routing_key_or_url
        routing_key = ""
    else:
        url = "https://events.pagerduty.com/v2/enqueue"
        routing_key = routing_key_or_url

    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    payload: Dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": "trigger" if alert_type == "failure" else "resolve",
        "payload": {
            "summary": message,
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
        },
    }
    await asyncio.to_thread(_post_json, url, payload)
    logger.info(f"PagerDuty alert sent ({alert_type})")


async def _send_webhook(url: str, alert_type: str, message: str) -> None:
    """Send alert to a generic HTTP webhook as a JSON POST."""
    payload: Dict[str, Any] = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }
    await asyncio.to_thread(_post_json, url, payload)
    logger.info(f"Webhook alert sent to {url} ({alert_type})")


def summarize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute summary statistics from raw metric histograms.

    Converts histogram lists into min/max/avg/p50/p95 summaries,
    suitable for display or export to CloudWatch/Datadog.
    """
    def _summarize(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0}
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        return {
            "count": n,
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "avg": sum(sorted_vals) / n,
            "p50": sorted_vals[int(n * 0.50)],
            "p95": sorted_vals[int(n * 0.95)],
        }

    return {
        "backup_duration_seconds": _summarize(metrics.get("backup_duration_seconds", [])),
        "backup_size_bytes": _summarize(metrics.get("backup_size_bytes", [])),
        "backup_success_total": metrics.get("backup_success_total", 0),
        "backup_failure_total": metrics.get("backup_failure_total", 0),
        "restore_duration_seconds": _summarize(metrics.get("restore_duration_seconds", [])),
        "retention_deletions_total": metrics.get("retention_deletions_total", 0),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
