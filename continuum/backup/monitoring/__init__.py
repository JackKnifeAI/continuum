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
from collections import defaultdict
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from threading import Lock
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)

# Module-level metric accumulators (thread-safe)
_metrics_lock = Lock()
_metrics: Dict[str, Any] = {
    "backup_duration_seconds": [],
    "backup_size_bytes": [],
    "backup_success_total": 0,
    "backup_failure_total": 0,
    "restore_duration_seconds": [],
    "retention_deletions_total": 0,
}


def record_metric(name: str, value: float) -> None:
    """Record a single metric observation. Called by backup/restore/retention code."""
    with _metrics_lock:
        if isinstance(_metrics.get(name), list):
            _metrics[name].append(value)
        elif name in _metrics:
            _metrics[name] += value
        else:
            logger.warning(f"Unknown metric: {name}")


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

    Returns metrics suitable for Prometheus, CloudWatch, etc. Histogram
    metrics include count/sum/p50/p95/p99 derived from in-process
    observations recorded via :func:`record_metric`.

    Returns:
        Dictionary of metrics
    """
    with _metrics_lock:
        result: Dict[str, Any] = {}

        for key, val in _metrics.items():
            if isinstance(val, list):
                observations = list(val)
                if observations:
                    sorted_obs = sorted(observations)
                    n = len(sorted_obs)
                    result[key] = {
                        "count": n,
                        "sum": sum(sorted_obs),
                        "p50": sorted_obs[int(n * 0.50)],
                        "p95": sorted_obs[int(n * 0.95)],
                        "p99": sorted_obs[min(int(n * 0.99), n - 1)],
                    }
                else:
                    result[key] = {"count": 0, "sum": 0.0}
            else:
                result[key] = val

    return result


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
        logger.info("No notification channels configured")
        return

    for channel in channels:
        try:
            if channel.startswith(("http://", "https://")):
                await _send_webhook(channel, alert_type, message)
            elif channel.startswith("pagerduty:"):
                routing_key = channel[len("pagerduty:"):]
                await _send_pagerduty(routing_key, alert_type, message)
            elif "@" in channel:
                await _send_email(channel, alert_type, message)
            else:
                logger.warning(f"Unrecognised notification channel format: {channel!r}")
        except Exception as exc:
            logger.error(f"Failed to send alert via {channel!r}: {exc}", exc_info=True)

async def _send_webhook(url: str, alert_type: str, message: str) -> None:
    """POST JSON payload to a Slack-compatible or generic webhook URL."""
    import asyncio

    payload = json.dumps({
        "text": f"[{alert_type.upper()}] {message}",
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }).encode()

    def _post() -> None:
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 202, 204):
                raise RuntimeError(f"Webhook returned HTTP {resp.status}")

    await asyncio.get_event_loop().run_in_executor(None, _post)
    logger.info(f"Alert sent to webhook: {url}")


async def _send_pagerduty(routing_key: str, alert_type: str, message: str) -> None:
    """Send an event to PagerDuty via the Events API v2."""
    import asyncio

    severity_map = {"failure": "error", "warning": "warning", "success": "info"}
    payload = json.dumps({
        "routing_key": routing_key,
        "event_action": "trigger" if alert_type == "failure" else "resolve",
        "payload": {
            "summary": message,
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }).encode()

    def _post() -> None:
        req = Request(
            "https://events.pagerduty.com/v2/enqueue",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 202):
                raise RuntimeError(f"PagerDuty returned HTTP {resp.status}")

    await asyncio.get_event_loop().run_in_executor(None, _post)
    logger.info(f"Alert sent to PagerDuty (key: ...{routing_key[-4:]})")


async def _send_email(
    to_address: str,
    alert_type: str,
    message: str,
) -> None:
    """Send alert email via SMTP (config from env: SMTP_HOST, SMTP_PORT, SMTP_FROM)."""
    import asyncio

    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", "25"))
    from_address = os.environ.get("SMTP_FROM", f"continuum-backup@{smtp_host}")

    msg = MIMEText(
        f"Continuum Backup Alert\n\nType: {alert_type.upper()}\n\n{message}\n\n"
        f"Timestamp: {datetime.utcnow().isoformat()}"
    )
    msg["Subject"] = f"[Continuum Backup] {alert_type.upper()}: {message[:60]}"
    msg["From"] = from_address
    msg["To"] = to_address

    def _send() -> None:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            smtp.sendmail(from_address, [to_address], msg.as_string())

    await asyncio.get_event_loop().run_in_executor(None, _send)
    logger.info(f"Alert email sent to {to_address}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
