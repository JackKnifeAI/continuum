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
Webhook Request Signing
========================

HMAC-SHA256 signing and verification for webhook security.

Security Features:
    - HMAC-SHA256 signatures
    - Timestamp-based replay protection
    - Constant-time comparison to prevent timing attacks

Usage:
    # Sending webhooks (CONTINUUM side)
    signer = WebhookSigner(secret="webhook_secret")
    headers = signer.generate_headers(payload)

    # Receiving webhooks (client side)
    is_valid = verify_webhook_signature(
        payload=request_body,
        signature=request.headers['X-Continuum-Signature'],
        timestamp=request.headers['X-Continuum-Timestamp'],
        secret=webhook_secret,
        max_age=300  # 5 minutes
    )
"""

import hmac
import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class WebhookSigner:
    """
    Signs webhook payloads with HMAC-SHA256.

    The signature is computed over:
        timestamp + "." + json.dumps(payload, sort_keys=True)

    This ensures:
        1. Payload integrity - any modification invalidates signature
        2. Timestamp binding - replays with old signatures are rejected
        3. Canonical form - JSON key order doesn't affect signature
    """

    def __init__(self, secret: str):
        """
        Initialize signer with webhook secret.

        Args:
            secret: Webhook secret key
        """
        self.secret = secret.encode('utf-8')

    def sign(self, payload: Dict[str, Any], timestamp: Optional[int] = None) -> tuple[str, int]:
        """
        Generate HMAC-SHA256 signature for payload.

        Args:
            payload: Event payload dictionary
            timestamp: Unix timestamp (defaults to current time)

        Returns:
            Tuple of (signature_hex, timestamp)

        Example:
            signature, ts = signer.sign({"event": "memory.created"})
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Create canonical message: timestamp.{json_payload}
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        message = f"{timestamp}.{canonical_payload}"

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature, timestamp

    def generate_headers(
        self,
        payload: Dict[str, Any],
        delivery_id: str,
        event: str
    ) -> Dict[str, str]:
        """
        Generate complete webhook headers.

        Args:
            payload: Event payload
            delivery_id: Unique delivery identifier
            event: Event type (e.g., "memory.created")

        Returns:
            Dictionary of HTTP headers

        Example:
            headers = signer.generate_headers(
                payload={"memory_id": "123"},
                delivery_id="del_abc123",
                event="memory.created"
            )
        """
        signature, timestamp = self.sign(payload)

        return {
            "X-Continuum-Signature": signature,
            "X-Continuum-Timestamp": str(timestamp),
            "X-Continuum-Event": event,
            "X-Continuum-Delivery": delivery_id,
            "Content-Type": "application/json",
            "User-Agent": "CONTINUUM-Webhooks/1.0"
        }


def verify_webhook_signature(
    payload: Dict[str, Any],
    signature: str,
    timestamp: str,
    secret: str,
    max_age: int = 300
) -> bool:
    """
    Verify webhook signature (for clients receiving webhooks).

    Args:
        payload: Request body as dictionary
        signature: X-Continuum-Signature header value
        timestamp: X-Continuum-Timestamp header value
        secret: Your webhook secret
        max_age: Maximum age in seconds (default 5 minutes)

    Returns:
        True if signature is valid and not replayed, False otherwise

    Example:
        is_valid = verify_webhook_signature(
            payload=request.json(),
            signature=request.headers.get('X-Continuum-Signature'),
            timestamp=request.headers.get('X-Continuum-Timestamp'),
            secret=os.environ['WEBHOOK_SECRET']
        )
        if not is_valid:
            return {"error": "Invalid signature"}, 401

    Security Notes:
        - Uses constant-time comparison to prevent timing attacks
        - Rejects requests older than max_age to prevent replay
        - Validates timestamp format before processing
    """
    try:
        # Parse timestamp
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False

    # Check for replay attacks
    current_time = int(time.time())
    if abs(current_time - ts) > max_age:
        return False

    # Compute expected signature
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    message = f"{ts}.{canonical_payload}"

    expected_signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


def generate_webhook_headers(
    payload: Dict[str, Any],
    secret: str,
    delivery_id: str,
    event: str
) -> Dict[str, str]:
    """
    Convenience function to generate webhook headers.

    Args:
        payload: Event payload
        secret: Webhook secret
        delivery_id: Unique delivery identifier
        event: Event type

    Returns:
        Dictionary of HTTP headers
    """
    signer = WebhookSigner(secret)
    return signer.generate_headers(payload, delivery_id, event)


class SignatureVerificationError(Exception):
    """Raised when signature verification fails."""
    pass


class ReplayAttackError(SignatureVerificationError):
    """Raised when timestamp indicates potential replay attack."""
    pass

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
