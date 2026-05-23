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
import urllib.parse
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
        config: Optional backup configuration for metadata access

    Returns:
        Dictionary of metrics with counters and histogram summaries
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_duration_seconds_count": 0,
        "backup_duration_seconds_sum": 0.0,
        "backup_duration_seconds_p50": 0.0,
        "backup_duration_seconds_p95": 0.0,
        "backup_size_bytes_count": 0,
        "backup_size_bytes_sum": 0,
        "backup_size_bytes_p50": 0,
        "backup_size_bytes_p95": 0,
        "restore_duration_seconds_count": 0,
        "restore_duration_seconds_sum": 0.0,
        "retention_deletions_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore

        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        durations: List[float] = []
        sizes: List[int] = []

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if backup.completed_at and backup.created_at:
                durations.append(
                    (backup.completed_at - backup.created_at).total_seconds()
                )

            if backup.compressed_size_bytes:
                sizes.append(backup.compressed_size_bytes)

        def _histogram_stats(values: list, prefix: str) -> None:
            if not values:
                return
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            metrics[f"{prefix}_count"] = n
            metrics[f"{prefix}_sum"] = sum(sorted_vals)
            metrics[f"{prefix}_p50"] = sorted_vals[int(n * 0.50)]
            metrics[f"{prefix}_p95"] = sorted_vals[min(int(n * 0.95), n - 1)]

        _histogram_stats(durations, "backup_duration_seconds")
        _histogram_stats(sizes, "backup_size_bytes")

        logger.debug(
            f"Collected metrics: {metrics['backup_success_total']} successes, "
            f"{metrics['backup_failure_total']} failures"
        )

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}", exc_info=True)

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

    for channel in config.notification_channels:
        try:
            if channel.startswith("http://") or channel.startswith("https://"):
                _send_webhook(channel, alert_type, message)
            elif channel.startswith("smtp://"):
                _send_smtp_alert(channel, alert_type, message)
            else:
                logger.warning(f"Unknown notification channel format: {channel!r}")
        except Exception as e:
            logger.error(f"Failed to send alert to {channel!r}: {e}", exc_info=True)

    if not config.notification_channels:
        logger.warning(f"No notification channels configured — alert dropped: {message}")

def _send_webhook(url: str, alert_type: str, message: str) -> None:
    """POST a JSON alert payload to a webhook URL (Slack-compatible or generic)."""
    is_slack = "hooks.slack.com" in url

    if is_slack:
        payload = {"text": f"[{alert_type.upper()}] {message}"}
    else:
        payload = {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info(f"Webhook alert sent to {url!r}: HTTP {resp.status}")


def _send_smtp_alert(smtp_url: str, alert_type: str, message: str) -> None:
    """Send an email alert via SMTP URL.

    URL format: smtp://user:password@host:port/recipient@example.com
    """
    parsed = urllib.parse.urlparse(smtp_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 25
    user = urllib.parse.unquote(parsed.username or "")
    password = urllib.parse.unquote(parsed.password or "")
    recipient = parsed.path.lstrip("/")

    if not recipient:
        logger.warning("SMTP channel missing recipient in URL path")
        return

    subject = f"[Backup {alert_type.upper()}] Alert"
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = user or f"backup@{host}"
    msg["To"] = recipient

    with smtplib.SMTP(host, port, timeout=10) as server:
        if user and password:
            server.starttls()
            server.login(user, password)
        server.sendmail(msg["From"], [recipient], msg.as_string())

    logger.info(f"Email alert sent to {recipient!r} via {host}:{port}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
