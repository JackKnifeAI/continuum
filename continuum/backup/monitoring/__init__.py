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
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

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

    Returns metrics suitable for Prometheus, CloudWatch, etc.:
    - backup_duration_seconds_{avg,p50,p95} (histogram approximations)
    - backup_size_bytes_{avg,total}
    - backup_success_total (counter)
    - backup_failure_total (counter)
    - backup_in_progress (gauge)
    - last_backup_age_seconds (gauge, -1 if no backups)
    - rpo_compliant (bool gauge)

    Args:
        config: Optional backup configuration. When provided, metrics are
                populated from the metadata store; otherwise zero-valued
                metrics are returned.

    Returns:
        Dictionary of metric name → value
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_in_progress": 0,
        "backup_duration_seconds_avg": 0.0,
        "backup_duration_seconds_p50": 0.0,
        "backup_duration_seconds_p95": 0.0,
        "backup_size_bytes_avg": 0,
        "backup_size_bytes_total": 0,
        "last_backup_age_seconds": -1,
        "rpo_compliant": True,
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
                metrics["backup_in_progress"] += 1

        completed = [b for b in all_backups if b.completed_at and b.created_at]
        if completed:
            durations = sorted(
                (b.completed_at - b.created_at).total_seconds() for b in completed
            )
            n = len(durations)
            metrics["backup_duration_seconds_avg"] = sum(durations) / n
            metrics["backup_duration_seconds_p50"] = durations[n // 2]
            metrics["backup_duration_seconds_p95"] = durations[int(n * 0.95)]

        sizes = [b.compressed_size_bytes for b in all_backups if b.compressed_size_bytes > 0]
        if sizes:
            metrics["backup_size_bytes_total"] = sum(sizes)
            metrics["backup_size_bytes_avg"] = sum(sizes) // len(sizes)

        successful = [b for b in all_backups if b.status.value in ("completed", "verified")]
        if successful:
            latest = max(successful, key=lambda b: b.created_at)
            age_seconds = (datetime.utcnow() - latest.created_at).total_seconds()
            metrics["last_backup_age_seconds"] = age_seconds
            metrics["rpo_compliant"] = age_seconds <= config.target_rpo_minutes * 60

    except Exception as e:
        logger.error(f"Failed to collect backup metrics: {e}", exc_info=True)

    return metrics


def _post_json(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
    """POST a JSON payload to url. Returns True on HTTP 2xx."""
    data = json.dumps(payload).encode("utf-8")
    merged_headers = {"Content-Type": "application/json"}
    if headers:
        merged_headers.update(headers)
    req = Request(url, data=data, headers=merged_headers)
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except URLError as e:
        logger.error(f"HTTP request to {url} failed: {e}")
        return False


def _send_slack_alert(alert_type: str, message: str) -> None:
    """
    Send alert to Slack via incoming webhook.

    Reads SLACK_WEBHOOK_URL from the environment.
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set; skipping Slack notification")
        return

    icon = ":white_check_mark:" if alert_type == "success" else ":rotating_light:"
    payload: Dict[str, Any] = {
        "text": f"{icon} *Backup {alert_type.upper()}*: {message}"
    }
    _post_json(webhook_url, payload)


def _send_pagerduty_alert(alert_type: str, message: str) -> None:
    """
    Send alert to PagerDuty via Events API v2.

    Reads PAGERDUTY_ROUTING_KEY from the environment.
    Triggers an incident on failure; resolves on success.
    """
    routing_key = os.environ.get("PAGERDUTY_ROUTING_KEY")
    if not routing_key:
        logger.warning("PAGERDUTY_ROUTING_KEY not set; skipping PagerDuty notification")
        return

    event_action = "trigger" if alert_type == "failure" else "resolve"
    payload: Dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": event_action,
        "payload": {
            "summary": message,
            "severity": "critical" if alert_type == "failure" else "info",
            "source": "continuum-backup",
        },
    }
    _post_json("https://events.pagerduty.com/v2/enqueue", payload)


def _send_webhook_alert(alert_type: str, message: str, url: str) -> None:
    """POST a structured JSON alert to a custom webhook URL."""
    payload: Dict[str, Any] = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }
    _post_json(url, payload)


def _send_email_alert(alert_type: str, message: str) -> None:
    """
    Send alert via SMTP.

    Reads from environment:
      SMTP_HOST          — required
      SMTP_PORT          — default 587
      SMTP_USER          — login username
      SMTP_PASSWORD      — login password
      BACKUP_ALERT_FROM  — sender address (falls back to SMTP_USER)
      BACKUP_ALERT_TO    — comma-separated recipient list, required
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("BACKUP_ALERT_FROM") or smtp_user
    to_raw = os.environ.get("BACKUP_ALERT_TO", "")

    if not smtp_host or not to_raw:
        logger.warning("SMTP_HOST or BACKUP_ALERT_TO not set; skipping email notification")
        return

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    to_addrs: List[str] = [a.strip() for a in to_raw.split(",") if a.strip()]

    msg = MIMEText(message)
    msg["Subject"] = f"[Backup {alert_type.upper()}] Continuum Backup Alert"
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
        logger.info(f"Email alert sent to {to_addrs}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending alert: {e}")


async def send_alert(
    alert_type: str,
    message: str,
    config: BackupConfig,
):
    """
    Send alert through configured channels.

    Channel strings in config.notification_channels:
      "slack"          — Slack webhook (SLACK_WEBHOOK_URL env var)
      "email"          — SMTP email (SMTP_HOST / BACKUP_ALERT_TO env vars)
      "pagerduty"      — PagerDuty Events API (PAGERDUTY_ROUTING_KEY env var)
      "webhook:<url>"  — arbitrary HTTP POST endpoint

    Args:
        alert_type: Type of alert ("failure", "warning", "success")
        message: Alert message
        config: Backup configuration with notification channels
    """
    logger.info(f"Sending {alert_type} alert: {message}")

    # Skip if notifications disabled
    if alert_type == "success" and not config.notify_on_success:
        return

    if alert_type == "failure" and not config.notify_on_failure:
        return

    channels = config.notification_channels
    if not channels:
        logger.debug("No notification channels configured")
        return

    for channel in channels:
        try:
            if channel == "slack":
                _send_slack_alert(alert_type, message)
            elif channel == "email":
                _send_email_alert(alert_type, message)
            elif channel == "pagerduty":
                _send_pagerduty_alert(alert_type, message)
            elif channel.startswith("webhook:"):
                webhook_url = channel[len("webhook:"):]
                _send_webhook_alert(alert_type, message, webhook_url)
            else:
                logger.warning(f"Unknown notification channel: {channel!r}")
        except Exception as e:
            logger.error(f"Failed to send alert via {channel!r}: {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
