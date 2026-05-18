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
import os
import smtplib
import urllib.request
from datetime import datetime, timedelta
from email.mime.text import MIMEText
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
        config: Optional backup configuration to read live metrics from metadata store.

    Returns:
        Dictionary of metrics with histogram summaries and counters.
    """

    def _histogram(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    metrics: Dict[str, Any] = {
        "backup_duration_seconds": _histogram([]),
        "backup_size_bytes": _histogram([]),
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "restore_duration_seconds": _histogram([]),
        "retention_deletions_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore

        store = MetadataStore(config.metadata_db_path)
        all_backups = store.list_backups()

        durations: List[float] = []
        sizes: List[float] = []

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if backup.compressed_size_bytes > 0:
                sizes.append(float(backup.compressed_size_bytes))

            if backup.completed_at and backup.created_at:
                durations.append((backup.completed_at - backup.created_at).total_seconds())

        metrics["backup_duration_seconds"] = _histogram(durations)
        metrics["backup_size_bytes"] = _histogram(sizes)

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

    sent = False
    for channel in config.notification_channels:
        try:
            if channel.startswith("http://") or channel.startswith("https://"):
                _send_webhook(channel, alert_type, message)
                sent = True
            elif channel == "slack":
                webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
                if webhook_url:
                    _send_slack(webhook_url, alert_type, message)
                    sent = True
                else:
                    logger.warning("SLACK_WEBHOOK_URL not set; skipping Slack alert")
            elif channel == "pagerduty":
                routing_key = os.environ.get("PAGERDUTY_ROUTING_KEY", "")
                if routing_key:
                    _send_pagerduty(routing_key, alert_type, message)
                    sent = True
                else:
                    logger.warning("PAGERDUTY_ROUTING_KEY not set; skipping PagerDuty alert")
            elif channel == "email":
                _send_email(alert_type, message)
                sent = True
            else:
                logger.warning(f"Unknown notification channel: {channel!r}")
        except Exception as e:
            logger.error(f"Failed to send alert via {channel!r}: {e}")

    if not sent:
        logger.warning(f"No notification channels delivered alert: {message}")

def _send_webhook(url: str, alert_type: str, message: str) -> None:
    """POST a JSON alert payload to a custom webhook URL."""
    payload = json.dumps({"alert_type": alert_type, "message": message}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info(f"Webhook alert sent to {url!r}: HTTP {resp.status}")


def _send_slack(webhook_url: str, alert_type: str, message: str) -> None:
    """Send an alert to a Slack incoming webhook."""
    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":bell:"
    )
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info(f"Slack alert sent: HTTP {resp.status}")


def _send_pagerduty(routing_key: str, alert_type: str, message: str) -> None:
    """Trigger or resolve a PagerDuty incident via Events API v2."""
    event_action = "resolve" if alert_type == "success" else "trigger"
    severity = "error" if alert_type == "failure" else "warning"
    payload = json.dumps(
        {
            "routing_key": routing_key,
            "event_action": event_action,
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "continuum-backup",
            },
        }
    ).encode()
    req = urllib.request.Request(
        "https://events.pagerduty.com/v2/enqueue",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info(f"PagerDuty alert sent: HTTP {resp.status}")


def _send_email(alert_type: str, message: str) -> None:
    """Send an email alert via SMTP using environment-variable configuration.

    Required env vars: SMTP_HOST, SMTP_FROM, SMTP_TO
    Optional env vars: SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD
    """
    host = os.environ.get("SMTP_HOST", "")
    from_addr = os.environ.get("SMTP_FROM", "")
    to_addr = os.environ.get("SMTP_TO", "")
    if not (host and from_addr and to_addr):
        logger.warning("SMTP_HOST / SMTP_FROM / SMTP_TO not set; skipping email alert")
        return

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", from_addr)
    password = os.environ.get("SMTP_PASSWORD", "")

    subject = f"[Continuum Backup] {alert_type.upper()}"
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        if password:
            smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], msg.as_string())

    logger.info(f"Email alert sent to {to_addr!r}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
