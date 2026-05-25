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
from typing import Any, Dict, List

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)

# Module-level in-memory metrics registry (counters + histogram samples).
# Thread-safe for CPython due to the GIL; list appends and int increments are atomic.
_metrics: Dict[str, Any] = {
    "backup_success_total": 0,
    "backup_failure_total": 0,
    "retention_deletions_total": 0,
    "backup_duration_seconds": [],
    "backup_size_bytes": [],
    "restore_duration_seconds": [],
}

_MAX_HISTOGRAM_SAMPLES = 1000  # prevent unbounded memory growth


def record_backup_success(duration_seconds: float, size_bytes: int = 0) -> None:
    """Record a successful backup with its duration and compressed size."""
    _metrics["backup_success_total"] += 1
    samples: List[float] = _metrics["backup_duration_seconds"]
    samples.append(duration_seconds)
    if len(samples) > _MAX_HISTOGRAM_SAMPLES:
        del samples[: len(samples) - _MAX_HISTOGRAM_SAMPLES]
    if size_bytes > 0:
        size_samples: List[float] = _metrics["backup_size_bytes"]
        size_samples.append(float(size_bytes))
        if len(size_samples) > _MAX_HISTOGRAM_SAMPLES:
            del size_samples[: len(size_samples) - _MAX_HISTOGRAM_SAMPLES]


def record_backup_failure() -> None:
    """Increment the backup failure counter."""
    _metrics["backup_failure_total"] += 1


def record_restore_duration(seconds: float) -> None:
    """Record a restore operation duration."""
    samples: List[float] = _metrics["restore_duration_seconds"]
    samples.append(seconds)
    if len(samples) > _MAX_HISTOGRAM_SAMPLES:
        del samples[: len(samples) - _MAX_HISTOGRAM_SAMPLES]


def record_retention_deletion(count: int = 1) -> None:
    """Increment the retention-deletion counter."""
    _metrics["retention_deletions_total"] += count


def _histogram_summary(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None,
                "p50": None, "p95": None, "p99": None}
    sv = sorted(values)
    n = len(sv)
    return {
        "count": n,
        "sum": sum(sv),
        "min": sv[0],
        "max": sv[-1],
        "avg": sum(sv) / n,
        "p50": sv[min(int(n * 0.50), n - 1)],
        "p95": sv[min(int(n * 0.95), n - 1)],
        "p99": sv[min(int(n * 0.99), n - 1)],
    }


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
    Counters persist for the process lifetime; histogram samples are capped
    at the last 1000 observations to bound memory use.

    Returns:
        Dictionary of metrics with counters and histogram summaries.
    """
    return {
        "backup_success_total": _metrics["backup_success_total"],
        "backup_failure_total": _metrics["backup_failure_total"],
        "retention_deletions_total": _metrics["retention_deletions_total"],
        "backup_duration_seconds": _histogram_summary(_metrics["backup_duration_seconds"]),
        "backup_size_bytes": _histogram_summary(_metrics["backup_size_bytes"]),
        "restore_duration_seconds": _histogram_summary(_metrics["restore_duration_seconds"]),
    }


async def send_alert(
    alert_type: str,
    message: str,
    config: BackupConfig,
) -> None:
    """
    Send alert through configured notification channels.

    Channel strings in ``config.notification_channels`` are parsed by prefix:

    * ``slack:<webhook_url>``     — Slack incoming webhook
    * ``pagerduty:<routing_key>`` — PagerDuty Events API v2
    * ``webhook:<url>``           — Generic HTTP POST (JSON body)
    * ``http://<url>`` / ``https://<url>`` — Same as ``webhook:``

    Args:
        alert_type: ``"failure"``, ``"warning"``, or ``"success"``
        message: Human-readable alert message
        config: Backup configuration with notification channel list
    """
    logger.info(f"Sending {alert_type} alert: {message}")

    if alert_type == "success" and not config.notify_on_success:
        return
    if alert_type == "failure" and not config.notify_on_failure:
        return

    if not config.notification_channels:
        logger.debug("No notification channels configured; skipping alert dispatch")
        return

    timestamp = datetime.utcnow().isoformat() + "Z"

    for channel in config.notification_channels:
        try:
            if channel.startswith("slack:"):
                await _send_slack_alert(channel[6:], alert_type, message)
            elif channel.startswith("pagerduty:"):
                await _send_pagerduty_alert(channel[10:], alert_type, message, timestamp)
            elif channel.startswith("webhook:"):
                await _send_webhook_alert(channel[8:], alert_type, message, timestamp)
            elif channel.startswith("http://") or channel.startswith("https://"):
                await _send_webhook_alert(channel, alert_type, message, timestamp)
            else:
                logger.warning(f"Unknown notification channel format: {channel!r}")
        except Exception as e:
            logger.error(f"Failed to send alert to channel {channel!r}: {e}")


def _post_json(url: str, payload: Dict[str, Any]) -> None:
    """Blocking HTTP POST of a JSON payload (run via asyncio.to_thread)."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.debug(f"Alert POST {url} → HTTP {resp.status}")


async def _send_slack_alert(webhook_url: str, alert_type: str, message: str) -> None:
    color_map = {"failure": "danger", "warning": "warning", "success": "good"}
    payload: Dict[str, Any] = {
        "text": f"Backup {alert_type.upper()}: {message}",
        "attachments": [{
            "color": color_map.get(alert_type, "#439FE0"),
            "text": message,
            "footer": "Continuum Backup Monitor",
        }],
    }
    await asyncio.to_thread(_post_json, webhook_url, payload)
    logger.info("Slack alert sent")


async def _send_pagerduty_alert(
    routing_key: str, alert_type: str, message: str, timestamp: str
) -> None:
    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    payload: Dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": f"Backup {alert_type}: {message}",
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
            "timestamp": timestamp,
        },
    }
    await asyncio.to_thread(
        _post_json, "https://events.pagerduty.com/v2/enqueue", payload
    )
    logger.info("PagerDuty alert sent")


async def _send_webhook_alert(
    url: str, alert_type: str, message: str, timestamp: str
) -> None:
    payload: Dict[str, Any] = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": timestamp,
        "source": "continuum-backup",
    }
    await asyncio.to_thread(_post_json, url, payload)
    logger.info(f"Webhook alert sent to {url}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
