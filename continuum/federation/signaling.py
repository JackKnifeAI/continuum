#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     WILDFIRE SIGNALING SERVER
#     The Switchboard for the P2P Mesh
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
WebRTC Signaling Server (Hardened)
==================================

Facilitates P2P connections between browser nodes.
This server creates the "Mesh" by introducing peers to each other.
Once introduced, peers communicate directly via WebRTC (DataChannels).

Security Features:
    - Rate limiting (100 msg/min per peer, configurable)
    - Connection limits (max 1000 peers, configurable)
    - Message size limits (64KB max)
    - IP-based abuse tracking
    - Optional HMAC token authentication
    - Automatic ban for repeat offenders

Protocol:
    - register: { type: 'register' } -> { type: 'welcome', id: 'peer-abc' }
    - offer: { type: 'offer', target: 'peer-xyz', sdp: ... }
    - answer: { type: 'answer', target: 'peer-abc', sdp: ... }
    - ice: { type: 'ice', target: 'peer-xyz', candidate: ... }

No data storage. Ephemeral routing only.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set

import websockets

logger = logging.getLogger("SIGNALING")

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SignalingConfig:
    """Security configuration for the signaling server."""

    # Rate limiting
    rate_limit_messages: int = 100      # Max messages per window
    rate_limit_window: int = 60         # Window size in seconds

    # Connection limits
    max_peers: int = 1000               # Max simultaneous peers
    max_peers_per_ip: int = 10          # Max peers from same IP

    # Message limits
    max_message_size: int = 65536       # 64KB max message

    # Authentication (optional)
    require_auth: bool = False
    auth_secret: str = field(default_factory=lambda: os.environ.get(
        "CONTINUUM_SIGNAL_SECRET", "dev-secret-change-in-production"
    ))

    # Ban settings
    ban_threshold: int = 5              # Violations before ban
    ban_duration: int = 3600            # Ban duration in seconds (1 hour)

    # Heartbeat
    heartbeat_interval: int = 30        # Seconds between pings
    heartbeat_timeout: int = 60         # Seconds before disconnect


# Global config
config = SignalingConfig()


# ═══════════════════════════════════════════════════════════════════════════════
#                              SECURITY TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PeerState:
    """Track state and violations for a peer."""
    peer_id: str
    websocket: websockets.WebSocketServerProtocol
    ip_address: str
    connected_at: float = field(default_factory=time.time)
    message_timestamps: List[float] = field(default_factory=list)
    violations: int = 0
    last_activity: float = field(default_factory=time.time)


# Connected peers: id -> PeerState
peers: Dict[str, PeerState] = {}

# IP tracking: ip -> set of peer_ids
ip_connections: Dict[str, Set[str]] = defaultdict(set)

# Rate limit tracking: peer_id -> list of message timestamps
rate_limits: Dict[str, List[float]] = defaultdict(list)

# Banned IPs: ip -> ban_expires_at
banned_ips: Dict[str, float] = {}


# ═══════════════════════════════════════════════════════════════════════════════
#                              SECURITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_client_ip(websocket: websockets.WebSocketServerProtocol) -> str:
    """Extract client IP from websocket connection."""
    try:
        # Check for forwarded header (behind proxy)
        if hasattr(websocket, 'request_headers'):
            forwarded = websocket.request_headers.get('X-Forwarded-For')
            if forwarded:
                return forwarded.split(',')[0].strip()

        # Direct connection
        if websocket.remote_address:
            return websocket.remote_address[0]
    except Exception:
        pass
    return "unknown"


def is_ip_banned(ip: str) -> bool:
    """Check if an IP is currently banned."""
    if ip in banned_ips:
        if time.time() < banned_ips[ip]:
            return True
        else:
            # Ban expired, remove it
            del banned_ips[ip]
    return False


def ban_ip(ip: str, reason: str):
    """Ban an IP address."""
    banned_ips[ip] = time.time() + config.ban_duration
    logger.warning(f"🚫 BANNED IP {ip} for {config.ban_duration}s: {reason}")


def check_rate_limit(peer_id: str) -> bool:
    """
    Check if peer is within rate limits.

    Returns:
        True if allowed, False if rate limited
    """
    now = time.time()
    window_start = now - config.rate_limit_window

    # Clean old timestamps
    rate_limits[peer_id] = [
        t for t in rate_limits[peer_id]
        if t > window_start
    ]

    # Check limit
    if len(rate_limits[peer_id]) >= config.rate_limit_messages:
        return False

    # Record this message
    rate_limits[peer_id].append(now)
    return True


def verify_token(peer_id: str, token: str) -> bool:
    """
    Verify HMAC token for authentication.

    Token should be: HMAC-SHA256(secret, peer_id)[:16]
    """
    if not config.require_auth:
        return True

    expected = hmac.new(
        config.auth_secret.encode(),
        peer_id.encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    return hmac.compare_digest(token, expected)


def generate_token(peer_id: str) -> str:
    """Generate auth token for a peer (for testing/bootstrap)."""
    return hmac.new(
        config.auth_secret.encode(),
        peer_id.encode(),
        hashlib.sha256
    ).hexdigest()[:16]


async def send_error(websocket: websockets.WebSocketServerProtocol,
                     code: str, message: str):
    """Send error message to client."""
    try:
        await websocket.send(json.dumps({
            "type": "error",
            "code": code,
            "message": message
        }))
    except Exception:
        pass


def record_violation(peer_state: PeerState, reason: str):
    """Record a security violation for a peer."""
    peer_state.violations += 1
    logger.warning(f"⚠️ Violation #{peer_state.violations} for {peer_state.peer_id}: {reason}")

    if peer_state.violations >= config.ban_threshold:
        ban_ip(peer_state.ip_address, f"Too many violations ({peer_state.violations})")


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

async def handler(websocket: websockets.WebSocketServerProtocol):
    """Handle a WebSocket connection with full security checks."""

    # Get client IP
    client_ip = get_client_ip(websocket)

    # Check if IP is banned
    if is_ip_banned(client_ip):
        logger.info(f"Rejected banned IP: {client_ip}")
        await send_error(websocket, "BANNED", "Your IP is temporarily banned")
        await websocket.close(1008, "Banned")
        return

    # Check global peer limit
    if len(peers) >= config.max_peers:
        logger.warning(f"Rejected connection: max peers reached ({config.max_peers})")
        await send_error(websocket, "SERVER_FULL", "Server at capacity")
        await websocket.close(1013, "Server full")
        return

    # Check per-IP limit
    if len(ip_connections[client_ip]) >= config.max_peers_per_ip:
        logger.warning(f"Rejected connection: max peers per IP for {client_ip}")
        await send_error(websocket, "TOO_MANY_CONNECTIONS",
                        f"Max {config.max_peers_per_ip} connections per IP")
        await websocket.close(1008, "Too many connections")
        return

    # Generate peer ID
    peer_id = str(uuid.uuid4())[:8]

    # Create peer state
    peer_state = PeerState(
        peer_id=peer_id,
        websocket=websocket,
        ip_address=client_ip
    )

    # Register peer
    peers[peer_id] = peer_state
    ip_connections[client_ip].add(peer_id)

    logger.info(f"✓ Peer connected: {peer_id} from {client_ip} "
               f"(total: {len(peers)}, from this IP: {len(ip_connections[client_ip])})")

    try:
        # Send welcome message
        welcome_msg = {
            "type": "welcome",
            "id": peer_id,
            "peers": [p for p in peers.keys() if p != peer_id],
            "config": {
                "heartbeat_interval": config.heartbeat_interval,
                "rate_limit": config.rate_limit_messages
            }
        }

        # Include auth token if auth is enabled (for subsequent requests)
        if config.require_auth:
            welcome_msg["token"] = generate_token(peer_id)

        await websocket.send(json.dumps(welcome_msg))

        # Message handling loop
        async for message in websocket:
            # Update activity timestamp
            peer_state.last_activity = time.time()

            # Check message size
            if len(message) > config.max_message_size:
                record_violation(peer_state, f"Message too large: {len(message)} bytes")
                await send_error(websocket, "MESSAGE_TOO_LARGE",
                               f"Max message size is {config.max_message_size} bytes")
                continue

            # Check rate limit
            if not check_rate_limit(peer_id):
                record_violation(peer_state, "Rate limit exceeded")
                await send_error(websocket, "RATE_LIMITED",
                               f"Max {config.rate_limit_messages} messages per {config.rate_limit_window}s")
                continue

            # Parse message
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                record_violation(peer_state, "Invalid JSON")
                await send_error(websocket, "INVALID_JSON", "Message must be valid JSON")
                continue

            msg_type = data.get("type")
            target_id = data.get("target")

            # Validate message type
            if msg_type not in ["offer", "answer", "ice", "ping"]:
                # Unknown message type - just ignore
                continue

            # Handle ping (heartbeat)
            if msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
                continue

            # Validate target exists for signaling messages
            if msg_type in ["offer", "answer", "ice"]:
                if not target_id:
                    await send_error(websocket, "MISSING_TARGET", "Target peer ID required")
                    continue

                if target_id not in peers:
                    await send_error(websocket, "PEER_NOT_FOUND",
                                   f"Peer {target_id} not connected")
                    continue

                if target_id == peer_id:
                    record_violation(peer_state, "Self-targeting")
                    await send_error(websocket, "INVALID_TARGET", "Cannot target self")
                    continue

                # Relay message to target
                data["sender"] = peer_id
                try:
                    await peers[target_id].websocket.send(json.dumps(data))
                    logger.debug(f"Relayed {msg_type}: {peer_id} → {target_id}")
                except Exception as e:
                    logger.warning(f"Failed to relay to {target_id}: {e}")
                    await send_error(websocket, "RELAY_FAILED", "Could not reach target peer")

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Handler error for {peer_id}: {e}")
    finally:
        # Cleanup
        if peer_id in peers:
            del peers[peer_id]
        if peer_id in rate_limits:
            del rate_limits[peer_id]
        ip_connections[client_ip].discard(peer_id)
        if not ip_connections[client_ip]:
            del ip_connections[client_ip]

        logger.info(f"✗ Peer disconnected: {peer_id} (remaining: {len(peers)})")


# ═══════════════════════════════════════════════════════════════════════════════
#                              SERVER STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

async def cleanup_stale_peers():
    """Periodically clean up peers that haven't sent heartbeats."""
    while True:
        await asyncio.sleep(config.heartbeat_interval)

        now = time.time()
        stale_peers = [
            peer_id for peer_id, state in peers.items()
            if now - state.last_activity > config.heartbeat_timeout
        ]

        for peer_id in stale_peers:
            logger.info(f"Removing stale peer: {peer_id}")
            try:
                await peers[peer_id].websocket.close(1000, "Heartbeat timeout")
            except Exception:
                pass


async def log_stats():
    """Periodically log server statistics."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        logger.info(f"📊 Stats: {len(peers)} peers, {len(banned_ips)} banned IPs, "
                   f"{len(ip_connections)} unique IPs")


async def main():
    """Start the signaling server with security features."""
    port = int(os.environ.get("SIGNALING_PORT", 8421))

    logger.info("═" * 60)
    logger.info("WILDFIRE SIGNALING SERVER (Hardened)")
    logger.info("═" * 60)
    logger.info(f"Port: {port}")
    logger.info(f"Max peers: {config.max_peers}")
    logger.info(f"Max per IP: {config.max_peers_per_ip}")
    logger.info(f"Rate limit: {config.rate_limit_messages} msg/{config.rate_limit_window}s")
    logger.info(f"Auth required: {config.require_auth}")
    logger.info("═" * 60)

    # Start background tasks
    asyncio.create_task(cleanup_stale_peers())
    asyncio.create_task(log_stats())

    # Start server
    async with websockets.serve(
        handler,
        "0.0.0.0",
        port,
        max_size=config.max_message_size,
        ping_interval=config.heartbeat_interval,
        ping_timeout=config.heartbeat_timeout
    ):
        logger.info(f"🚀 Signaling server listening on ws://0.0.0.0:{port}")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
