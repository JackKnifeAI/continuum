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
import logging
import os
import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Any, Dict, List

import httpx

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)

# Thread-safe in-memory metrics store.  Updated by record_backup_metrics() /
# record_restore_metrics() / record_retention_metrics().
_metrics_lock = threading.Lock()
_metrics: Dict[str, Any] = {
    "backup_success_total": 0,
    "backup_failure_total": 0,
    "retention_deletions_total": 0,
    "backup_duration_seconds": [],   # histogram samples
    "backup_size_bytes": [],         # histogram samples
    "restore_duration_seconds": [],  # histogram samples
}


def record_backup_metrics(
    *,
    success: bool,
    duration_seconds: float,
    size_bytes: int,
) -> None:
    """Update backup counters and histograms."""
    with _metrics_lock:
        if success:
            _metrics["backup_success_total"] += 1
        else:
            _metrics["backup_failure_total"] += 1
        _metrics["backup_duration_seconds"].append(duration_seconds)
        _metrics["backup_size_bytes"].append(size_bytes)


def record_restore_metrics(*, duration_seconds: float) -> None:
    """Update restore histogram."""
    with _metrics_lock:
        _metrics["restore_duration_seconds"].append(duration_seconds)


def record_retention_metrics(*, deletions: int) -> None:
    """Increment retention deletion counter."""
    with _metrics_lock:
        _metrics["retention_deletions_total"] += deletions


def _histogram_stats(samples: List[float]) -> Dict[str, Any]:
    if not samples:
        return {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None}
    return {
        "count": len(samples),
        "sum": sum(samples),
        "min": min(samples),
        "max": max(samples),
        "avg": sum(samples) / len(samples),
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

    Returns:
        Dictionary with counters and histogram stats for:
        backup_duration_seconds, backup_size_bytes, backup_success_total,
        backup_failure_total, restore_duration_seconds, retention_deletions_total.
    """
    with _metrics_lock:
        return {
            "backup_success_total": _metrics["backup_success_total"],
            "backup_failure_total": _metrics["backup_failure_total"],
            "retention_deletions_total": _metrics["retention_deletions_total"],
            "backup_duration_seconds": _histogram_stats(
                list(_metrics["backup_duration_seconds"])
            ),
            "backup_size_bytes": _histogram_stats(
                list(_metrics["backup_size_bytes"])
            ),
            "restore_duration_seconds": _histogram_stats(
                list(_metrics["restore_duration_seconds"])
            ),
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
        logger.debug("No notification channels configured")
        return

    for channel in channels:
        try:
            if channel == "slack" or channel.startswith(("http://", "https://")):
                url = (
                    channel
                    if channel.startswith(("http://", "https://"))
                    else os.environ.get("BACKUP_SLACK_WEBHOOK_URL", "")
                )
                if url:
                    await _send_slack_alert(url, alert_type, message)
                else:
                    logger.warning("Slack channel configured but BACKUP_SLACK_WEBHOOK_URL not set")
            elif channel == "webhook":
                url = os.environ.get("BACKUP_WEBHOOK_URL", "")
                if url:
                    await _send_webhook_alert(url, alert_type, message)
                else:
                    logger.warning("Webhook channel configured but BACKUP_WEBHOOK_URL not set")
            elif channel == "email":
                await _send_email_alert(alert_type, message)
            elif channel == "pagerduty":
                routing_key = os.environ.get("BACKUP_PAGERDUTY_ROUTING_KEY", "")
                if routing_key:
                    await _send_pagerduty_alert(routing_key, alert_type, message)
                else:
                    logger.warning("PagerDuty channel configured but BACKUP_PAGERDUTY_ROUTING_KEY not set")
            else:
                logger.warning(f"Unknown notification channel: {channel}")
        except Exception as exc:
            logger.error(f"Failed to send alert via {channel}: {exc}")

async def _send_slack_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """POST a Slack-format message to a webhook URL."""
    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":information_source:"
    )
    payload = {"text": f"{emoji} *Backup {alert_type.upper()}*\n{message}"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()
    logger.info(f"Slack alert sent ({alert_type})")


async def _send_webhook_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """POST a JSON alert payload to a generic webhook URL."""
    payload = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()
    logger.info(f"Webhook alert sent ({alert_type})")


async def _send_pagerduty_alert(routing_key: str, alert_type: str, message: str) -> None:
    """Trigger or resolve a PagerDuty incident via Events API v2."""
    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    payload = {
        "routing_key": routing_key,
        "event_action": "resolve" if alert_type == "success" else "trigger",
        "payload": {
            "summary": message,
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post("https://events.pagerduty.com/v2/enqueue", json=payload)
        resp.raise_for_status()
    logger.info(f"PagerDuty alert sent ({alert_type})")


async def _send_email_alert(alert_type: str, message: str) -> None:
    """Send an alert email via SMTP using environment-variable configuration."""
    host = os.environ.get("BACKUP_SMTP_HOST", "")
    port = int(os.environ.get("BACKUP_SMTP_PORT", "587"))
    user = os.environ.get("BACKUP_SMTP_USER", "")
    password = os.environ.get("BACKUP_SMTP_PASSWORD", "")
    from_addr = os.environ.get("BACKUP_SMTP_FROM", user)
    to_addrs_raw = os.environ.get("BACKUP_SMTP_TO", "")

    if not host or not to_addrs_raw:
        logger.warning("Email channel configured but BACKUP_SMTP_HOST / BACKUP_SMTP_TO not set")
        return

    to_addrs = [a.strip() for a in to_addrs_raw.split(",") if a.strip()]
    subject = f"[Continuum Backup] {alert_type.upper()}: Backup Alert"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)

    # Run blocking SMTP call in a thread to avoid blocking the event loop.
    def _smtp_send() -> None:
        with smtplib.SMTP(host, port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(from_addr, to_addrs, msg.as_string())

    await asyncio.get_event_loop().run_in_executor(None, _smtp_send)
    logger.info(f"Email alert sent ({alert_type}) to {to_addrs}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
