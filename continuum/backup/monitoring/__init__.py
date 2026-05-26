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
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)

# Module-level metrics registry — updated by record_metric(); read by get_backup_metrics()
_metrics: Dict[str, Any] = {
    "backup_duration_seconds": [],     # histogram samples
    "backup_size_bytes": [],           # histogram samples
    "backup_success_total": 0,         # counter
    "backup_failure_total": 0,         # counter
    "restore_duration_seconds": [],    # histogram samples
    "retention_deletions_total": 0,    # counter
    "last_updated": None,
}

_METRIC_HISTOGRAMS = {"backup_duration_seconds", "backup_size_bytes", "restore_duration_seconds"}
_METRIC_COUNTERS = {"backup_success_total", "backup_failure_total", "retention_deletions_total"}


def record_metric(name: str, value: float) -> None:
    """Update a named metric counter or append a histogram sample."""
    if name in _METRIC_HISTOGRAMS:
        _metrics[name].append(value)
        if len(_metrics[name]) > 1000:  # keep a rolling window
            _metrics[name] = _metrics[name][-1000:]
    elif name in _METRIC_COUNTERS:
        _metrics[name] = _metrics.get(name, 0) + value
    else:
        logger.warning(f"Unknown metric: {name}")
        return
    _metrics["last_updated"] = datetime.utcnow().isoformat()


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


def get_backup_metrics() -> Dict[str, Any]:
    """
    Get backup system metrics for monitoring.

    Returns metrics suitable for Prometheus, CloudWatch, etc.

    Returns:
        Dictionary of metrics with counters and histogram summaries
    """

    def _histogram_summary(samples: List[float]) -> Dict[str, Any]:
        if not samples:
            return {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None}
        return {
            "count": len(samples),
            "sum": sum(samples),
            "min": min(samples),
            "max": max(samples),
            "avg": sum(samples) / len(samples),
        }

    return {
        "backup_duration_seconds": _histogram_summary(_metrics["backup_duration_seconds"]),
        "backup_size_bytes": _histogram_summary(_metrics["backup_size_bytes"]),
        "backup_success_total": _metrics["backup_success_total"],
        "backup_failure_total": _metrics["backup_failure_total"],
        "restore_duration_seconds": _histogram_summary(_metrics["restore_duration_seconds"]),
        "retention_deletions_total": _metrics["retention_deletions_total"],
        "last_updated": _metrics["last_updated"],
    }


def _dispatch_channel(channel: str, alert_type: str, message: str) -> None:
    """
    Deliver an alert to a single channel URL (blocking; run in executor).

    Channel URL schemes:
      https://hooks.slack.com/...  → Slack Incoming Webhook
      https://events.pagerduty.com/... → PagerDuty Events v2
      http:// or https://          → Generic JSON webhook POST
    """
    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    severity = severity_map.get(alert_type, "info")

    if "hooks.slack.com" in channel:
        color = {"failure": "danger", "warning": "warning", "success": "good"}.get(alert_type, "#439FE0")
        payload: Dict[str, Any] = {
            "attachments": [{
                "color": color,
                "title": f"Backup {alert_type.upper()}",
                "text": message,
                "ts": int(datetime.utcnow().timestamp()),
            }]
        }
    elif "pagerduty.com" in channel:
        payload = {
            "routing_key": channel.split("/")[-1],  # key embedded at end of URL
            "event_action": "trigger" if alert_type == "failure" else "resolve",
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "continuum-backup",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }
        # PagerDuty Events v2 endpoint is fixed
        channel = "https://events.pagerduty.com/v2/enqueue"
    else:
        payload = {
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "continuum-backup",
        }

    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        channel,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "continuum-backup/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"Alert delivered to {channel!r}: HTTP {resp.status}")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} from {channel!r}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error reaching {channel!r}: {exc.reason}") from exc


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
    results = await asyncio.gather(
        *[loop.run_in_executor(None, _dispatch_channel, channel, alert_type, message)
          for channel in channels],
        return_exceptions=True,
    )
    for channel, result in zip(channels, results):
        if isinstance(result, Exception):
            logger.error(f"Alert delivery failed for channel {channel!r}: {result}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
