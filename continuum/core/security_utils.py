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
CONTINUUM Security Utilities
=============================

Unified security patterns and utilities used across all modules.

Provides:
- Credential hashing (PBKDF2)
- Input validation
- Rate limiting patterns
- Secure logging
- Environment variable handling
- Constant-time comparison
"""

import os
import re
import hmac
import hashlib
import secrets
import logging
from typing import Any, Optional, Dict, List
from pathlib import Path
from dataclasses import dataclass


logger = logging.getLogger(__name__)


# =============================================================================
# CREDENTIAL HASHING (PBKDF2)
# =============================================================================

PBKDF2_ITERATIONS = 100_000  # OWASP recommendation for 2024
PBKDF2_SALT_LENGTH = 32  # 256 bits


def hash_credential(credential: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    """
    Hash a credential using PBKDF2-HMAC-SHA256.

    SECURITY: Uses random salt and OWASP-recommended iterations.

    Args:
        credential: Plain text credential (API key, password, etc.)
        iterations: Number of PBKDF2 iterations (default: 100,000)

    Returns:
        Hash in format: salt_hex:hash_hex

    Example:
        >>> hashed = hash_credential("cm_my_api_key_12345")
        >>> print(hashed)
        'abc123...def456:789ghi...012jkl'
    """
    salt = os.urandom(PBKDF2_SALT_LENGTH)
    key_hash = hashlib.pbkdf2_hmac(
        'sha256',
        credential.encode('utf-8'),
        salt,
        iterations
    )
    return salt.hex() + ':' + key_hash.hex()


def verify_credential(credential: str, stored_hash: str, iterations: int = PBKDF2_ITERATIONS) -> bool:
    """
    Verify a credential against stored PBKDF2 hash.

    SECURITY: Uses constant-time comparison to prevent timing attacks.

    Args:
        credential: Plain text credential to verify
        stored_hash: Stored hash in format salt_hex:hash_hex
        iterations: Number of PBKDF2 iterations (default: 100,000)

    Returns:
        True if credential matches, False otherwise

    Example:
        >>> stored = hash_credential("my_secret")
        >>> verify_credential("my_secret", stored)
        True
        >>> verify_credential("wrong_secret", stored)
        False
    """
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        key_hash = hashlib.pbkdf2_hmac(
            'sha256',
            credential.encode('utf-8'),
            salt,
            iterations
        )
        return constant_time_compare(key_hash.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.

    Args:
        a: First string
        b: Second string

    Returns:
        True if strings match, False otherwise
    """
    return hmac.compare_digest(a, b)


# =============================================================================
# INPUT VALIDATION
# =============================================================================

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


def validate_string_input(
    value: str,
    field_name: str = "input",
    max_length: Optional[int] = None,
    min_length: Optional[int] = None,
    allowed_pattern: Optional[str] = None,
    forbidden_patterns: Optional[List[str]] = None,
    allow_null_bytes: bool = False,
    check_injections: bool = True,
) -> str:
    """
    Validate and sanitize string input.

    Protects against:
    - SQL injection
    - Command injection
    - Path traversal
    - Null byte attacks
    - Excessively long inputs

    Args:
        value: String to validate
        field_name: Name of field (for error messages)
        max_length: Maximum allowed length
        min_length: Minimum required length
        allowed_pattern: Regex pattern that input must match
        forbidden_patterns: List of regex patterns that input must NOT match
        allow_null_bytes: Whether to allow null bytes (default: False)
        check_injections: Whether to check for injection patterns (default: True)

    Returns:
        Validated string

    Raises:
        ValidationError: If validation fails

    Example:
        >>> validate_string_input("user@example.com", "email", max_length=100)
        'user@example.com'
        >>> validate_string_input("'; DROP TABLE users--", "username")
        ValidationError: username contains potential SQL injection pattern
    """
    # Type check
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    # Length checks
    if max_length and len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length}")

    if min_length and len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")

    # Null byte check
    if not allow_null_bytes and '\x00' in value:
        raise ValidationError(f"{field_name} contains null bytes")

    # Pattern validation
    if allowed_pattern and not re.match(allowed_pattern, value):
        raise ValidationError(f"{field_name} does not match allowed pattern")

    if forbidden_patterns:
        for pattern in forbidden_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"{field_name} contains forbidden pattern")

    # Injection checks
    if check_injections:
        # SQL injection patterns
        sql_patterns = [
            r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE)\s+",
            r"--",
            r"/\*.*\*/",
            r"'\s*OR\s+'",
            r"'\s*=\s*'",
            r"UNION\s+SELECT",
            r"1\s*=\s*1",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"{field_name} contains potential SQL injection pattern")

        # Command injection patterns
        cmd_patterns = [
            r"[;&|`$]",  # Shell metacharacters
            r"\$\(",     # Command substitution
            r"\.\./",    # Path traversal
        ]
        for pattern in cmd_patterns:
            if re.search(pattern, value):
                raise ValidationError(f"{field_name} contains potential command injection pattern")

    return value


def validate_entity_type(entity_type: str) -> str:
    """
    Validate entity type against whitelist.

    Args:
        entity_type: Entity type to validate

    Returns:
        Validated entity type

    Raises:
        ValidationError: If entity type is invalid
    """
    VALID_ENTITY_TYPES = {
        'concept', 'decision', 'session', 'person', 'project',
        'tool', 'event', 'location', 'organization'
    }

    if entity_type not in VALID_ENTITY_TYPES:
        raise ValidationError(
            f"Invalid entity_type. Must be one of: {', '.join(sorted(VALID_ENTITY_TYPES))}"
        )

    return entity_type


# =============================================================================
# SECURE ENVIRONMENT VARIABLE HANDLING
# =============================================================================

def get_env_secret(
    key: str,
    required: bool = True,
    default: Optional[str] = None,
    min_length: Optional[int] = None,
) -> Optional[str]:
    """
    Get a secret from environment variables with validation.

    Args:
        key: Environment variable name
        required: Whether the variable is required
        default: Default value if not found
        min_length: Minimum length for secret

    Returns:
        Secret value or default

    Raises:
        ValueError: If required secret is missing or too short

    Example:
        >>> api_key = get_env_secret("OPENAI_API_KEY", required=True, min_length=20)
    """
    value = os.environ.get(key, default)

    if required and not value:
        raise ValueError(f"Required secret {key} not set in environment")

    if value and min_length and len(value) < min_length:
        raise ValueError(f"Secret {key} must be at least {min_length} characters")

    return value


def load_env_file(env_path: Optional[Path] = None):
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file (defaults to .env in project root)

    Example:
        >>> load_env_file()  # Loads .env from project root
    """
    if env_path is None:
        # Try to find .env in project root
        env_path = Path.cwd() / ".env"

    if not env_path.exists():
        logger.debug(f"No .env file found at {env_path}")
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    except ImportError:
        logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")


# =============================================================================
# SECURE LOGGING
# =============================================================================

class SecureLogFilter(logging.Filter):
    """
    Logging filter to redact sensitive data.

    Redacts:
    - API keys (patterns like cm_*, sk-*, pk_*)
    - Passwords
    - Tokens
    - Email addresses (optional)
    """

    def __init__(self, redact_emails: bool = False):
        """
        Initialize secure log filter.

        Args:
            redact_emails: Whether to redact email addresses
        """
        super().__init__()
        self.redact_emails = redact_emails

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive data from log record"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            msg = record.msg

            # Redact API keys
            msg = re.sub(r'\b(cm_|sk-|pk_)[A-Za-z0-9_-]+', r'\1***REDACTED***', msg)

            # Redact generic tokens/secrets
            msg = re.sub(
                r'(api[_-]?key|password|secret|token)["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
                r'\1=***REDACTED***',
                msg,
                flags=re.IGNORECASE
            )

            # Redact Bearer tokens
            msg = re.sub(r'Bearer\s+[A-Za-z0-9_-]+', 'Bearer ***REDACTED***', msg)

            # Optionally redact email addresses
            if self.redact_emails:
                msg = re.sub(
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    '***@***.***',
                    msg
                )

            record.msg = msg

        return True


def setup_secure_logging(
    level: str = "INFO",
    redact_emails: bool = False,
    log_file: Optional[Path] = None,
):
    """
    Setup secure logging with automatic redaction.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        redact_emails: Whether to redact email addresses
        log_file: Optional file path for logging

    Example:
        >>> setup_secure_logging(level="INFO", redact_emails=True)
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Add secure filter
    secure_filter = SecureLogFilter(redact_emails=redact_emails)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(secure_filter)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.addFilter(secure_filter)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


# =============================================================================
# TOKEN GENERATION
# =============================================================================

def generate_api_key(prefix: str = "cm", length: int = 32) -> str:
    """
    Generate a secure random API key.

    Args:
        prefix: Key prefix (e.g., "cm" for continuum)
        length: Length of random portion

    Returns:
        API key in format: prefix_base64urlsafe

    Example:
        >>> key = generate_api_key("cm", 32)
        >>> print(key)
        'cm_abc123def456...'
    """
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}_{random_part}"


def generate_webhook_secret(length: int = 32) -> str:
    """
    Generate a secure random webhook secret.

    Args:
        length: Length of secret in bytes

    Returns:
        Hex-encoded secret

    Example:
        >>> secret = generate_webhook_secret(32)
        >>> print(len(secret))
        64  # 32 bytes = 64 hex chars
    """
    return secrets.token_hex(length)


# =============================================================================
# URL PARAMETER ENCODING
# =============================================================================

def escape_connection_string_param(param: str) -> str:
    """
    Escape special characters in connection string parameters.

    Prevents connection string injection via username/password.

    Args:
        param: Parameter to escape (username, password, etc.)

    Returns:
        URL-encoded parameter

    Example:
        >>> escape_connection_string_param("user@host")
        'user%40host'
    """
    from urllib.parse import quote_plus
    return quote_plus(param)


def build_postgres_url(
    user: str,
    password: str,
    host: str,
    port: int,
    database: str,
    sslmode: str = "require"
) -> str:
    """
    Build a secure PostgreSQL connection URL.

    SECURITY: Escapes user/password to prevent connection string injection.

    Args:
        user: Database username
        password: Database password
        host: Database host
        port: Database port
        database: Database name
        sslmode: SSL mode (require, verify-ca, verify-full)

    Returns:
        PostgreSQL connection URL

    Example:
        >>> url = build_postgres_url("user", "pass@123", "localhost", 5432, "db")
        >>> print(url)
        'postgresql://user:pass%40123@localhost:5432/db?sslmode=require'
    """
    user_escaped = escape_connection_string_param(user)
    password_escaped = escape_connection_string_param(password)

    return f"postgresql://{user_escaped}:{password_escaped}@{host}:{port}/{database}?sslmode={sslmode}"


# =============================================================================
# REDIS CONNECTION SECURITY
# =============================================================================

def build_redis_url(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    username: Optional[str] = None,
    ssl: bool = False,
) -> str:
    """
    Build a secure Redis connection URL.

    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        password: Redis password (if AUTH enabled)
        username: Redis username (Redis 6+)
        ssl: Whether to use TLS

    Returns:
        Redis connection URL

    Example:
        >>> url = build_redis_url(password="secret", ssl=True)
        >>> print(url)
        'rediss://:secret@localhost:6379/0'
    """
    scheme = "rediss" if ssl else "redis"

    if username and password:
        auth = f"{escape_connection_string_param(username)}:{escape_connection_string_param(password)}"
    elif password:
        auth = f":{escape_connection_string_param(password)}"
    else:
        auth = ""

    if auth:
        return f"{scheme}://{auth}@{host}:{port}/{db}"
    else:
        return f"{scheme}://{host}:{port}/{db}"


# =============================================================================
# WEBHOOK SIGNATURE VERIFICATION
# =============================================================================

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256",
    header_prefix: str = "sha256="
) -> bool:
    """
    Verify webhook signature using HMAC.

    Args:
        payload: Request body (raw bytes)
        signature: Signature from webhook header
        secret: Webhook secret
        algorithm: Hash algorithm (sha256, sha512)
        header_prefix: Prefix in signature header (e.g., "sha256=")

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> payload = b'{"event": "test"}'
        >>> secret = "my_webhook_secret"
        >>> signature = "sha256=abc123..."
        >>> verify_webhook_signature(payload, signature, secret)
        True
    """
    # Remove prefix if present
    if signature.startswith(header_prefix):
        signature = signature[len(header_prefix):]

    # Compute expected signature
    hash_func = getattr(hashlib, algorithm)
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hash_func
    ).hexdigest()

    # Constant-time comparison
    return constant_time_compare(signature, expected_signature)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Credential hashing
    'hash_credential',
    'verify_credential',
    'constant_time_compare',

    # Input validation
    'ValidationError',
    'validate_string_input',
    'validate_entity_type',

    # Environment variables
    'get_env_secret',
    'load_env_file',

    # Logging
    'SecureLogFilter',
    'setup_secure_logging',

    # Token generation
    'generate_api_key',
    'generate_webhook_secret',

    # URL building
    'escape_connection_string_param',
    'build_postgres_url',
    'build_redis_url',

    # Webhook verification
    'verify_webhook_signature',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
