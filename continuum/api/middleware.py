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
API middleware for authentication, rate limiting, and other cross-cutting concerns.
"""

import hashlib
import hmac
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Header


# =============================================================================
# CONFIGURATION
# =============================================================================

# Configurable API key requirement
REQUIRE_API_KEY = True  # Set to False to disable API key requirement

# Database path - defaults to ~/.continuum/api_keys.db
DEFAULT_API_KEYS_DB = Path.home() / ".continuum" / "api_keys.db"


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

def get_api_keys_db_path() -> Path:
    """Get the API keys database path, creating directory if needed."""
    db_path = DEFAULT_API_KEYS_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_api_keys_db():
    """Initialize API keys database with schema."""
    db_path = get_api_keys_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key_hash TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT,
            name TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_key(key: str) -> str:
    """
    Hash an API key for secure storage using PBKDF2-HMAC-SHA256.

    SECURITY: Uses 100,000 iterations with random salt per OWASP guidelines.

    Args:
        key: Raw API key string

    Returns:
        Hash in format: salt_hex:hash_hex
    """
    import os
    salt = os.urandom(32)  # 256-bit random salt
    key_hash = hashlib.pbkdf2_hmac(
        'sha256',
        key.encode('utf-8'),
        salt,
        100000  # 100k iterations (OWASP recommendation for 2024)
    )
    return salt.hex() + ':' + key_hash.hex()


def verify_key(key: str, stored_hash: str) -> bool:
    """
    Verify API key against stored PBKDF2 hash.

    Args:
        key: Plain text API key to verify
        stored_hash: Stored hash in format salt_hex:hash_hex

    Returns:
        True if key matches, False otherwise
    """
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        key_hash = hashlib.pbkdf2_hmac(
            'sha256',
            key.encode('utf-8'),
            salt,
            100000
        )
        return hmac.compare_digest(key_hash.hex(), hash_hex)
    except (ValueError, AttributeError):
        # Fallback for old SHA-256 hashes (backwards compatibility)
        # TODO: Remove after migration
        old_hash = hashlib.sha256(key.encode()).hexdigest()
        return hmac.compare_digest(old_hash, stored_hash)


def validate_api_key(key: str) -> Optional[str]:
    """
    Validate an API key and return the associated tenant ID.

    SECURITY: Uses constant-time comparison and PBKDF2 verification.

    Args:
        key: API key to validate

    Returns:
        Tenant ID if key is valid, None otherwise
    """
    init_api_keys_db()
    db_path = get_api_keys_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Fetch all keys (necessary because of salted hashes)
    # In production, consider caching or indexed lookup
    c.execute("SELECT key_hash, tenant_id FROM api_keys")
    rows = c.fetchall()

    for stored_hash, tenant_id in rows:
        if verify_key(key, stored_hash):
            # Update last_used timestamp
            c.execute(
                "UPDATE api_keys SET last_used = ? WHERE key_hash = ?",
                (datetime.now().isoformat(), stored_hash)
            )
            conn.commit()
            conn.close()
            return tenant_id

    conn.close()
    return None


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

async def get_tenant_from_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency to validate API key and extract tenant ID.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Tenant ID

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If API keys are disabled, use a default tenant
    if not REQUIRE_API_KEY:
        return "default"

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header required",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    tenant_id = validate_api_key(x_api_key)
    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return tenant_id


async def optional_tenant_from_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Optional API key validation - returns default tenant if no key provided.

    Useful for endpoints that can work with or without authentication.

    Args:
        x_api_key: Optional API key from X-API-Key header

    Returns:
        Tenant ID (or "default" if no key)
    """
    if not x_api_key:
        return "default"

    tenant_id = validate_api_key(x_api_key)
    if not tenant_id:
        return "default"

    return tenant_id


# =============================================================================
# AUTHENTICATION MIDDLEWARE
# =============================================================================

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Optional


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant_id from X-API-Key header and set in request.state.

    This middleware must run BEFORE BillingMiddleware to ensure tenant_id is available.
    """

    async def dispatch(self, request: Request, call_next):
        """Extract tenant_id from X-API-Key and store in request.state"""

        # Get API key from header
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")

        if api_key:
            # Validate and get tenant_id
            tenant_id = validate_api_key(api_key)
            if tenant_id:
                # Store in request.state for downstream middleware
                request.state.api_key_tenant_id = tenant_id
                request.state.tenant_id = tenant_id

        # Continue processing
        response = await call_next(request)
        return response


# =============================================================================
# RATE LIMITING (STUB)
# =============================================================================

class RateLimiter:
    """
    Rate limiting stub for future implementation.

    TODO: Implement token bucket or sliding window rate limiting
    per tenant/API key. Consider using Redis for distributed rate limiting.
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        # Stub: actual implementation would track request counts

    async def check_rate_limit(self, tenant_id: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            tenant_id: Tenant to check

        Returns:
            True if within limit, raises HTTPException if exceeded

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Stub: always allow for now
        # TODO: Implement actual rate limiting logic
        return True


# Global rate limiter instance (currently a stub)
rate_limiter = RateLimiter(requests_per_minute=60)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
