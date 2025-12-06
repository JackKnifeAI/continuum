"""
API middleware for authentication, rate limiting, and other cross-cutting concerns.
"""

import hashlib
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
    Hash an API key for secure storage.

    Args:
        key: Raw API key string

    Returns:
        SHA-256 hex digest of the key
    """
    return hashlib.sha256(key.encode()).hexdigest()


def validate_api_key(key: str) -> Optional[str]:
    """
    Validate an API key and return the associated tenant ID.

    Args:
        key: API key to validate

    Returns:
        Tenant ID if key is valid, None otherwise
    """
    init_api_keys_db()

    key_hash = hash_key(key)
    db_path = get_api_keys_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT tenant_id FROM api_keys WHERE key_hash = ?", (key_hash,))
    row = c.fetchone()

    if row:
        # Update last_used timestamp
        c.execute(
            "UPDATE api_keys SET last_used = ? WHERE key_hash = ?",
            (datetime.now().isoformat(), key_hash)
        )
        conn.commit()
        conn.close()
        return row[0]

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
