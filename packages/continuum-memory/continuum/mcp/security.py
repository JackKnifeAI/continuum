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
CONTINUUM MCP Security

Authentication, rate limiting, input validation, and anti-tool-poisoning protection.
"""

import re
import time
import hashlib
import secrets
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import json

from continuum.core.auth import (
    authenticate,
    verify_pi_phi,
    generate_client_id as core_generate_client_id,
    AuthenticationError as CoreAuthenticationError,
)
from .config import get_mcp_config


class SecurityError(Exception):
    """Base class for security-related errors."""
    pass


class AuthenticationError(SecurityError, CoreAuthenticationError):
    """Authentication failed."""
    pass


class RateLimitError(SecurityError):
    """Rate limit exceeded."""
    pass


class ValidationError(SecurityError):
    """Input validation failed."""
    pass


class ToolPoisoningError(SecurityError):
    """Potential tool poisoning attack detected."""
    pass


def authenticate_client(
    api_key: Optional[str] = None,
    pi_phi_verification: Optional[float] = None
) -> bool:
    """
    Authenticate a client connection using shared auth utilities.

    Authentication can be done via:
    1. API key (standard authentication)
    2. π×φ verification (CONTINUUM instance authentication)
    3. Both (strongest authentication)

    Args:
        api_key: Client's API key
        pi_phi_verification: π×φ value for verification

    Returns:
        True if authenticated

    Raises:
        AuthenticationError: If authentication fails
    """
    config = get_mcp_config()

    try:
        return authenticate(
            api_key=api_key,
            pi_phi_verification=pi_phi_verification,
            valid_api_keys=config.api_keys if config.api_keys else None,
            require_pi_phi=config.require_pi_phi,
        )
    except CoreAuthenticationError as e:
        raise AuthenticationError(str(e)) from e


class RateLimiter:
    """
    Token bucket rate limiter per client.

    Implements a token bucket algorithm with burst capacity.
    Each client gets their own bucket based on client_id.
    """

    def __init__(
        self,
        rate: int = 60,  # requests per minute
        burst: int = 10,  # burst allowance
    ):
        """
        Initialize rate limiter.

        Args:
            rate: Requests allowed per minute
            burst: Burst capacity (extra tokens)
        """
        self.rate = rate
        self.burst = burst
        self.buckets: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "tokens": burst,
                "last_update": time.time(),
            }
        )

    def allow_request(self, client_id: str) -> bool:
        """
        Check if request is allowed for client.

        Args:
            client_id: Unique client identifier

        Returns:
            True if request allowed

        Raises:
            RateLimitError: If rate limit exceeded
        """
        bucket = self.buckets[client_id]
        now = time.time()

        # Calculate tokens to add based on elapsed time
        elapsed = now - bucket["last_update"]
        tokens_to_add = elapsed * (self.rate / 60.0)  # rate per second

        # Update bucket
        bucket["tokens"] = min(self.burst, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now

        # Check if we have tokens
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            return True
        else:
            raise RateLimitError(
                f"Rate limit exceeded for client {client_id}. "
                f"Try again in {int(60 / self.rate)} seconds."
            )

    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit statistics for a client."""
        bucket = self.buckets[client_id]
        return {
            "client_id": client_id,
            "tokens_available": bucket["tokens"],
            "rate_per_minute": self.rate,
            "burst_capacity": self.burst,
        }


def validate_input(
    value: Any,
    max_length: Optional[int] = None,
    allowed_pattern: Optional[str] = None,
    forbidden_patterns: Optional[List[str]] = None,
    field_name: str = "input",
) -> Any:
    """
    Validate and sanitize input.

    Protects against:
    - Injection attacks (SQL, command, etc.)
    - Excessively long inputs
    - Malicious patterns
    - Tool poisoning attempts

    Args:
        value: Value to validate
        max_length: Maximum allowed length for strings
        allowed_pattern: Regex pattern that input must match
        forbidden_patterns: List of regex patterns that input must NOT match
        field_name: Name of field being validated (for error messages)

    Returns:
        Validated value

    Raises:
        ValidationError: If validation fails
    """
    # Type-specific validation
    if isinstance(value, str):
        # Check length
        if max_length and len(value) > max_length:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {max_length} characters"
            )

        # Check for null bytes
        if "\x00" in value:
            raise ValidationError(f"{field_name} contains null bytes")

        # Check allowed pattern
        if allowed_pattern and not re.match(allowed_pattern, value):
            raise ValidationError(f"{field_name} does not match allowed pattern")

        # Check forbidden patterns
        if forbidden_patterns:
            for pattern in forbidden_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValidationError(
                        f"{field_name} contains forbidden pattern: {pattern}"
                    )

        # Anti-SQL injection
        sql_patterns = [
            r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE)\s+",
            r"--",
            r"/\*.*\*/",
            r"'\s*OR\s+'",
            r"'\s*=\s*'",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    f"{field_name} contains potential SQL injection pattern"
                )

        # Anti-command injection
        cmd_patterns = [
            r"[;&|`$]",  # Shell metacharacters
            r"\$\(",  # Command substitution
            r"\.\./",  # Path traversal
        ]
        for pattern in cmd_patterns:
            if re.search(pattern, value):
                raise ValidationError(
                    f"{field_name} contains potential command injection pattern"
                )

    elif isinstance(value, (int, float)):
        # Numeric validation
        if max_length:
            if abs(value) > max_length:
                raise ValidationError(f"{field_name} exceeds maximum value of {max_length}")

    elif isinstance(value, dict):
        # Recursive validation for dictionaries
        for k, v in value.items():
            validate_input(k, max_length=100, field_name=f"{field_name}.key")
            validate_input(v, max_length=max_length, field_name=f"{field_name}.{k}")

    elif isinstance(value, list):
        # Recursive validation for lists
        if max_length and len(value) > max_length:
            raise ValidationError(f"{field_name} list exceeds maximum length")
        for i, item in enumerate(value):
            validate_input(item, max_length=max_length, field_name=f"{field_name}[{i}]")

    return value


def detect_tool_poisoning(
    user_input: str,
    ai_response: Optional[str] = None,
) -> bool:
    """
    Detect potential tool poisoning attacks.

    Tool poisoning: Adversaries inject malicious instructions into context
    that trick the AI into executing unintended tools or leaking data.

    Detection patterns:
    - Suspicious instructions to "ignore previous instructions"
    - Attempts to override system prompts
    - Requests to execute specific tools
    - Data exfiltration attempts

    Args:
        user_input: User's input message
        ai_response: AI's response (optional)

    Returns:
        True if potential attack detected

    Raises:
        ToolPoisoningError: If attack detected and blocking is enabled
    """
    # Patterns indicating potential tool poisoning
    poisoning_patterns = [
        r"ignore (previous|all|prior) instructions",
        r"disregard (previous|all|prior) (instructions|rules)",
        r"new instructions:",
        r"system(:|prompt:)",
        r"you are now",
        r"act as if",
        r"pretend (you are|to be)",
        r"role(play)?:\s*you are",
        r"execute (this )?tool:",
        r"call (this )?function:",
        r"send (all|my) (data|information|memory) to",
        r"export (all )?data to",
        r"reveal (the |your )?(api[ _]?key|password|secret)",
    ]

    # Check user input
    for pattern in poisoning_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            raise ToolPoisoningError(
                f"Potential tool poisoning detected: pattern '{pattern}' found in input"
            )

    # Check AI response if provided
    if ai_response:
        # Detect if AI is revealing sensitive info
        sensitive_patterns = [
            r"api[_ ]?key[:\s]+[a-zA-Z0-9_-]{20,}",
            r"password[:\s]+\S+",
            r"secret[:\s]+\S+",
            r"token[:\s]+[a-zA-Z0-9_-]{20,}",
        ]
        for pattern in sensitive_patterns:
            if re.search(pattern, ai_response, re.IGNORECASE):
                raise ToolPoisoningError(
                    f"Potential data leak detected: sensitive pattern found in response"
                )

    return False


class AuditLogger:
    """
    Audit logger for security events and operations.

    Logs all MCP operations with timestamps, client IDs, and results.
    """

    def __init__(self, log_path: Path):
        """Initialize audit logger."""
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        event_type: str,
        client_id: str,
        details: Dict[str, Any],
        success: bool = True,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event (e.g., "tool_call", "authentication")
            client_id: Client identifier
            details: Event details
            success: Whether operation succeeded
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "client_id": client_id,
            "success": success,
            "details": details,
        }

        # Append to log file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent audit events.

        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            client_id: Filter by client ID

        Returns:
            List of audit events
        """
        if not self.log_path.exists():
            return []

        events = []
        with open(self.log_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    # Apply filters
                    if event_type and event["event_type"] != event_type:
                        continue
                    if client_id and event["client_id"] != client_id:
                        continue
                    events.append(event)
                except json.JSONDecodeError:
                    continue

        # Return most recent events
        return events[-limit:]


def generate_client_id(request_info: Dict[str, Any]) -> str:
    """
    Generate a consistent client ID from request information.

    Args:
        request_info: Request metadata (headers, IP, etc.)

    Returns:
        Hashed client identifier
    """
    # Use shared auth utility
    return core_generate_client_id(
        user_agent=request_info.get("user_agent", "unknown"),
        ip_address=request_info.get("ip_address", "unknown"),
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
