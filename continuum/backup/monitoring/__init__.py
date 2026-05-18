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
import smtplib
import urllib.request
from datetime import datetime, timedelta
from email.message import EmailMessage
from threading import Lock
from typing import Any, Dict, List

from ..types import BackupConfig, BackupHealth

# ---------------------------------------------------------------------------
# Module-level metrics registry
# ---------------------------------------------------------------------------

_metrics_lock = Lock()
_counters: Dict[str, int] = {
    "backup_success_total": 0,
    "backup_failure_total": 0,
    "restore_success_total": 0,
    "restore_failure_total": 0,
    "retention_deletions_total": 0,
}
_histograms: Dict[str, List[float]] = {
    "backup_duration_seconds": [],
    "backup_size_bytes": [],
    "restore_duration_seconds": [],
}


def record_backup_result(*, success: bool, duration_seconds: float, size_bytes: int) -> None:
    """Update backup counters and duration/size histograms."""
    with _metrics_lock:
        if success:
            _counters["backup_success_total"] += 1
        else:
            _counters["backup_failure_total"] += 1
        _histograms["backup_duration_seconds"].append(duration_seconds)
        _histograms["backup_size_bytes"].append(float(size_bytes))


def record_restore_result(*, success: bool, duration_seconds: float) -> None:
    """Update restore counters and duration histogram."""
    with _metrics_lock:
        if success:
            _counters["restore_success_total"] += 1
        else:
            _counters["restore_failure_total"] += 1
        _histograms["restore_duration_seconds"].append(duration_seconds)


def record_retention_deletion(count: int = 1) -> None:
    """Increment the retention deletions counter."""
    with _metrics_lock:
        _counters["retention_deletions_total"] += count


def _histogram_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
    return {
        "count": len(values),
        "sum": sum(values),
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
    }

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


def get_backup_metrics() -> Dict[str, Any]:
    """
    Get backup system metrics for monitoring.

    Returns metrics suitable for Prometheus, CloudWatch, etc.

    Returns:
        Dictionary of metrics with counters and histogram summaries.
    """
    with _metrics_lock:
        return {
            **_counters,
            **{
                name: _histogram_stats(list(values))
                for name, values in _histograms.items()
            },
        }


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
        logger.debug("No notification channels configured; skipping alert dispatch")
        return

    for channel in channels:
        try:
            await _dispatch_channel(channel, alert_type, message)
        except Exception as e:
            logger.error(f"Alert dispatch failed for channel {channel!r}: {e}")


async def _dispatch_channel(channel: str, alert_type: str, message: str) -> None:
    """
    Route an alert to a single notification channel.

    Channel formats:
      slack:<webhook_url>
      webhook:<url>         (POST JSON body)
      email:<smtp_url>      (smtp://user:pass@host:port/from@x.com/to@x.com)
    """
    import asyncio

    if channel.startswith("slack:"):
        url = channel[len("slack:"):]
        payload = json.dumps({
            "text": f"*[{alert_type.upper()}]* {message}",
        }).encode()
        await asyncio.to_thread(_http_post, url, payload, "application/json")

    elif channel.startswith("webhook:"):
        url = channel[len("webhook:"):]
        payload = json.dumps({
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }).encode()
        await asyncio.to_thread(_http_post, url, payload, "application/json")

    elif channel.startswith("email:"):
        # smtp://user:pass@host:port/from@example.com/to@example.com
        spec = channel[len("email:"):]
        await asyncio.to_thread(_send_smtp, spec, alert_type, message)

    else:
        logger.warning(f"Unknown notification channel scheme: {channel!r}")


def _http_post(url: str, body: bytes, content_type: str) -> None:
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        logger.debug(f"Notification POST {url} -> HTTP {resp.status}")


def _send_smtp(spec: str, alert_type: str, message: str) -> None:
    """Send an email alert via SMTP.

    spec format: smtp://user:pass@host:port/from@example.com/to@example.com
    """
    from urllib.parse import urlparse

    parsed = urlparse(spec)
    host = parsed.hostname or "localhost"
    port = parsed.port or 587
    user = parsed.username or ""
    password = parsed.password or ""

    path_parts = parsed.path.lstrip("/").split("/")
    if len(path_parts) < 2:
        raise ValueError(f"email channel spec must include /from/to path, got: {spec!r}")
    from_addr, to_addr = path_parts[0], path_parts[1]

    msg = EmailMessage()
    msg["Subject"] = f"[Continuum Backup {alert_type.upper()}] Alert"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(message)

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        if user:
            smtp.login(user, password)
        smtp.send_message(msg)
    logger.debug(f"Email alert sent to {to_addr}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
