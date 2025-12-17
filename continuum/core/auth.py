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
CONTINUUM Shared Authentication

Unified authentication utilities used by both CLI and MCP server.
"""

import os
import hashlib
from typing import Optional, List
from pathlib import Path

from .constants import PI_PHI


class AuthenticationError(Exception):
    """Authentication failed."""
    pass


def verify_pi_phi(value: float, tolerance: float = 1e-10) -> bool:
    """
    Verify π×φ constant for CONTINUUM instance authentication.

    Args:
        value: Value to verify
        tolerance: Allowed floating-point tolerance

    Returns:
        True if value matches PI_PHI within tolerance

    Example:
        >>> verify_pi_phi(5.083203692315260)
        True
        >>> verify_pi_phi(5.0)
        False
    """
    return abs(value - PI_PHI) < tolerance


def verify_api_key(api_key: str, valid_keys: List[str]) -> bool:
    """
    Verify API key against list of valid keys.

    Args:
        api_key: API key to verify
        valid_keys: List of valid API keys

    Returns:
        True if API key is valid
    """
    if not valid_keys:
        # No keys configured - development mode
        return True
    return api_key in valid_keys


def authenticate(
    api_key: Optional[str] = None,
    pi_phi_verification: Optional[float] = None,
    valid_api_keys: Optional[List[str]] = None,
    require_pi_phi: bool = True,
) -> bool:
    """
    Unified authentication function.

    Authentication can be done via:
    1. API key (standard authentication)
    2. π×φ verification (CONTINUUM instance authentication)
    3. Both (strongest authentication)

    Args:
        api_key: Client's API key
        pi_phi_verification: π×φ value for verification
        valid_api_keys: List of valid API keys (None = dev mode)
        require_pi_phi: Whether to require π×φ verification

    Returns:
        True if authenticated

    Raises:
        AuthenticationError: If authentication fails
    """
    # Development mode - no auth required
    if not valid_api_keys and not require_pi_phi:
        return True

    # Verify API key if provided
    api_key_valid = False
    if api_key and valid_api_keys:
        api_key_valid = verify_api_key(api_key, valid_api_keys)

    # Verify π×φ if provided
    pi_phi_valid = False
    if pi_phi_verification is not None:
        pi_phi_valid = verify_pi_phi(pi_phi_verification)

    # Determine if authentication succeeds
    if require_pi_phi and valid_api_keys:
        # Both required
        if not api_key_valid:
            raise AuthenticationError("Invalid API key")
        if not pi_phi_valid:
            raise AuthenticationError("Invalid π×φ verification")
        return True

    elif require_pi_phi:
        # Only π×φ required
        if not pi_phi_valid:
            raise AuthenticationError("Invalid π×φ verification")
        return True

    elif valid_api_keys:
        # Only API key required
        if not api_key_valid:
            raise AuthenticationError("Invalid API key")
        return True

    # If we get here, no authentication was provided
    raise AuthenticationError("Authentication required")


def load_api_keys_from_env() -> List[str]:
    """
    Load API keys from environment variables.

    Checks both CONTINUUM_API_KEY (single) and CONTINUUM_API_KEYS (comma-separated).

    Returns:
        List of API keys
    """
    keys = []

    # Single key
    env_api_key = os.getenv("CONTINUUM_API_KEY")
    if env_api_key:
        keys.append(env_api_key)

    # Multiple keys (comma-separated)
    env_api_keys = os.getenv("CONTINUUM_API_KEYS")
    if env_api_keys:
        keys.extend(k.strip() for k in env_api_keys.split(","))

    return keys


def generate_client_id(user_agent: str = "unknown", ip_address: str = "unknown") -> str:
    """
    Generate a consistent client ID from request information.

    Args:
        user_agent: Client user agent string
        ip_address: Client IP address

    Returns:
        Hashed client identifier (16 chars)
    """
    # Combine relevant request info
    client_data = f"{user_agent}:{ip_address}"

    # Hash to create consistent ID
    return hashlib.sha256(client_data.encode()).hexdigest()[:16]


def get_require_pi_phi_from_env() -> bool:
    """
    Get π×φ requirement from environment variable.

    Returns:
        True if CONTINUUM_REQUIRE_PI_PHI is set to "true" (case-insensitive)
    """
    value = os.getenv("CONTINUUM_REQUIRE_PI_PHI", "true")
    return value.lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
