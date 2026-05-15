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
import smtplib
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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


def get_backup_metrics(config: Optional["BackupConfig"] = None) -> Dict[str, Any]:
    """
    Get backup system metrics for monitoring.

    Returns metrics suitable for Prometheus, CloudWatch, etc.

    Args:
        config: Backup configuration (required to query live metrics)

    Returns:
        Dictionary of metrics with counters and histograms
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_duration_seconds": {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None},
        "backup_size_bytes": {"count": 0, "sum": 0, "min": None, "max": None, "avg": None},
        "restore_duration_seconds": {"count": 0, "sum": 0.0},
        "retention_deletions_total": 0,
        "last_backup_timestamp": None,
        "total_storage_used_bytes": 0,
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

            metrics["total_storage_used_bytes"] += backup.compressed_size_bytes

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                d = metrics["backup_duration_seconds"]
                d["count"] += 1
                d["sum"] += duration
                d["min"] = min(d["min"], duration) if d["min"] is not None else duration
                d["max"] = max(d["max"], duration) if d["max"] is not None else duration

            if backup.compressed_size_bytes > 0:
                s = metrics["backup_size_bytes"]
                size = backup.compressed_size_bytes
                s["count"] += 1
                s["sum"] += size
                s["min"] = min(s["min"], size) if s["min"] is not None else size
                s["max"] = max(s["max"], size) if s["max"] is not None else size

        d = metrics["backup_duration_seconds"]
        if d["count"] > 0:
            d["avg"] = d["sum"] / d["count"]

        s = metrics["backup_size_bytes"]
        if s["count"] > 0:
            s["avg"] = s["sum"] / s["count"]

        if all_backups:
            latest = max(all_backups, key=lambda b: b.created_at)
            metrics["last_backup_timestamp"] = latest.created_at.isoformat()

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

    payload: Dict[str, Any] = {
        "alert_type": alert_type,
        "message": message,
        "tenant_id": config.tenant_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    for channel in config.notification_channels:
        try:
            await _dispatch_alert(channel, alert_type, message, payload)
        except Exception as e:
            logger.error(f"Failed to send alert to channel {channel!r}: {e}")

async def _dispatch_alert(
    channel: str,
    alert_type: str,
    message: str,
    payload: Dict[str, Any],
) -> None:
    """Dispatch an alert to a specific notification channel."""
    parsed = urllib.parse.urlparse(channel)

    if parsed.scheme in ("http", "https"):
        await _send_webhook(channel, alert_type, message, payload)
    elif channel.startswith("mailto:"):
        email_addr = channel[len("mailto:"):]
        await _send_email(email_addr, alert_type, message)
    else:
        logger.warning(f"Unknown notification channel format {channel!r}: {message}")


async def _send_webhook(
    url: str,
    alert_type: str,
    message: str,
    payload: Dict[str, Any],
) -> None:
    """Send alert via HTTP webhook. Supports generic JSON and Slack webhooks."""
    is_slack = "hooks.slack.com" in url

    if is_slack:
        color = {"failure": "danger", "warning": "warning", "success": "good"}.get(alert_type, "#439FE0")
        body = json.dumps({
            "attachments": [{
                "color": color,
                "title": f"Backup Alert: {alert_type.upper()}",
                "text": message,
                "footer": f"Tenant: {payload.get('tenant_id', 'unknown')}",
                "ts": int(datetime.utcnow().timestamp()),
            }]
        }).encode()
    else:
        body = json.dumps(payload).encode()

    def _post() -> int:
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.status

    status = await asyncio.to_thread(_post)
    logger.info(f"Webhook alert sent to {url!r}: HTTP {status}")


async def _send_email(
    email_addr: str,
    alert_type: str,
    message: str,
) -> None:
    """Send alert via email using localhost SMTP relay (port 25)."""
    def _send() -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Continuum Backup] {alert_type.upper()} Alert"
        msg["From"] = "continuum-backup@localhost"
        msg["To"] = email_addr
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP("localhost", 25, timeout=10) as smtp:
            smtp.sendmail("continuum-backup@localhost", [email_addr], msg.as_string())

    await asyncio.to_thread(_send)
    logger.info(f"Email alert sent to {email_addr!r}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
