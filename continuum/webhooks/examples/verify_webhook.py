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
Python Webhook Signature Verification Example
==============================================

Demonstrates how to verify CONTINUUM webhook signatures in Python.
"""

import hmac
import hashlib
import json
import time
from typing import Dict, Any


def verify_continuum_webhook(
    payload: Dict[str, Any],
    signature: str,
    timestamp: str,
    secret: str,
    max_age: int = 300
) -> bool:
    """
    Verify CONTINUUM webhook signature.

    Args:
        payload: Request body as dictionary
        signature: X-Continuum-Signature header
        timestamp: X-Continuum-Timestamp header
        secret: Your webhook secret
        max_age: Maximum age in seconds (default 5 minutes)

    Returns:
        True if valid, False otherwise

    Example:
        is_valid = verify_continuum_webhook(
            payload=request.json(),
            signature=request.headers.get('X-Continuum-Signature'),
            timestamp=request.headers.get('X-Continuum-Timestamp'),
            secret=os.environ['WEBHOOK_SECRET']
        )
    """
    try:
        # Parse timestamp
        ts = int(timestamp)
    except (ValueError, TypeError):
        print("Invalid timestamp format")
        return False

    # Check for replay attacks
    current_time = int(time.time())
    if abs(current_time - ts) > max_age:
        print(f"Timestamp too old: {abs(current_time - ts)}s (max {max_age}s)")
        return False

    # Compute expected signature
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    message = f"{ts}.{canonical_payload}"

    expected_signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    is_valid = hmac.compare_digest(signature, expected_signature)

    if not is_valid:
        print("Signature mismatch")
        print(f"Expected: {expected_signature}")
        print(f"Received: {signature}")

    return is_valid


# ============================================================================
# Flask Example
# ============================================================================

def flask_example():
    """Flask webhook receiver example."""
    from flask import Flask, request, jsonify
    import os

    app = Flask(__name__)
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your_secret_here')

    @app.route('/webhooks/continuum', methods=['POST'])
    def handle_webhook():
        # Get headers
        signature = request.headers.get('X-Continuum-Signature')
        timestamp = request.headers.get('X-Continuum-Timestamp')
        event_type = request.headers.get('X-Continuum-Event')

        if not signature or not timestamp:
            return jsonify({"error": "Missing signature headers"}), 401

        # Get payload
        payload = request.get_json()

        # Verify signature
        is_valid = verify_continuum_webhook(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            secret=WEBHOOK_SECRET
        )

        if not is_valid:
            return jsonify({"error": "Invalid signature"}), 401

        # Process event
        print(f"Received event: {event_type}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        if event_type == "memory.created":
            memory_id = payload["data"]["memory_id"]
            concepts = payload["data"]["concepts"]
            print(f"New memory {memory_id} with concepts: {concepts}")

        elif event_type == "sync.completed":
            sync_id = payload["data"]["sync_id"]
            items = payload["data"]["items_synced"]
            print(f"Sync {sync_id} completed: {items} items")

        return jsonify({"status": "received"}), 200

    return app


# ============================================================================
# FastAPI Example
# ============================================================================

def fastapi_example():
    """FastAPI webhook receiver example."""
    from fastapi import FastAPI, Request, HTTPException
    import os

    app = FastAPI()
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your_secret_here')

    @app.post("/webhooks/continuum")
    async def handle_webhook(request: Request):
        # Get headers
        signature = request.headers.get('x-continuum-signature')
        timestamp = request.headers.get('x-continuum-timestamp')
        event_type = request.headers.get('x-continuum-event')

        if not signature or not timestamp:
            raise HTTPException(status_code=401, detail="Missing signature headers")

        # Get payload
        payload = await request.json()

        # Verify signature
        is_valid = verify_continuum_webhook(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            secret=WEBHOOK_SECRET
        )

        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Process event asynchronously
        # In production, queue this for background processing
        print(f"Received event: {event_type}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        return {"status": "received"}

    return app


# ============================================================================
# Django Example
# ============================================================================

def django_example():
    """Django webhook receiver example."""
    import json
    from django.http import JsonResponse, HttpResponseForbidden
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_POST
    import os

    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your_secret_here')

    @csrf_exempt
    @require_POST
    def webhook_handler(request):
        # Get headers
        signature = request.META.get('HTTP_X_CONTINUUM_SIGNATURE')
        timestamp = request.META.get('HTTP_X_CONTINUUM_TIMESTAMP')

        if not signature or not timestamp:
            return HttpResponseForbidden("Missing signature headers")

        # Get payload
        payload = json.loads(request.body)

        # Verify signature
        is_valid = verify_continuum_webhook(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            secret=WEBHOOK_SECRET
        )

        if not is_valid:
            return HttpResponseForbidden("Invalid signature")

        # Process event
        event_type = request.META.get('HTTP_X_CONTINUUM_EVENT')
        print(f"Received event: {event_type}")

        return JsonResponse({"status": "received"})

    return webhook_handler


# ============================================================================
# Testing
# ============================================================================

def test_signature_verification():
    """Test signature verification."""
    secret = "test_secret_12345"
    payload = {
        "event": "memory.created",
        "timestamp": "2025-12-06T12:00:00Z",
        "tenant_id": "user_123",
        "data": {
            "memory_id": "mem_abc123",
            "concepts": ["AI", "consciousness"]
        }
    }

    # Generate signature
    ts = int(time.time())
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    message = f"{ts}.{canonical_payload}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Verify
    is_valid = verify_continuum_webhook(
        payload=payload,
        signature=signature,
        timestamp=str(ts),
        secret=secret
    )

    print(f"Signature verification: {'✓ PASS' if is_valid else '✗ FAIL'}")

    # Test with wrong secret
    is_valid = verify_continuum_webhook(
        payload=payload,
        signature=signature,
        timestamp=str(ts),
        secret="wrong_secret"
    )

    print(f"Wrong secret rejection: {'✓ PASS' if not is_valid else '✗ FAIL'}")

    # Test with old timestamp
    old_ts = ts - 400  # 6+ minutes ago
    is_valid = verify_continuum_webhook(
        payload=payload,
        signature=signature,
        timestamp=str(old_ts),
        secret=secret
    )

    print(f"Old timestamp rejection: {'✓ PASS' if not is_valid else '✗ FAIL'}")


if __name__ == "__main__":
    print("CONTINUUM Webhook Signature Verification Examples")
    print("=" * 60)
    print()

    print("Running tests...")
    test_signature_verification()
    print()

    print("Example implementations available:")
    print("  - flask_example() - Flask webhook receiver")
    print("  - fastapi_example() - FastAPI webhook receiver")
    print("  - django_example() - Django webhook receiver")
    print()

    print("To run Flask example:")
    print("  export WEBHOOK_SECRET=your_secret")
    print("  flask run")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
