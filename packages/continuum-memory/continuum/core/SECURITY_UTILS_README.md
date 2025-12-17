# Security Utilities - Quick Reference

**Location**: `continuum/core/security_utils.py`

Unified security utilities for all CONTINUUM modules. Use these functions to maintain consistency and security best practices.

---

## Quick Start

```python
from continuum.core.security_utils import (
    hash_credential,
    verify_credential,
    validate_string_input,
    setup_secure_logging,
    get_env_secret,
)

# Hash API keys/passwords
hashed = hash_credential("user_password")

# Verify credentials
is_valid = verify_credential("user_password", hashed)

# Validate user input
safe_input = validate_string_input(
    user_input,
    field_name="username",
    max_length=100,
    check_injections=True
)

# Load secrets securely
api_key = get_env_secret("STRIPE_API_KEY", required=True, min_length=20)

# Enable secure logging
setup_secure_logging(level="INFO", redact_emails=True)
```

---

## Credential Hashing

### hash_credential(credential, iterations=100_000)

Hash credentials using PBKDF2-HMAC-SHA256.

**Use for:**
- API keys
- Passwords
- Tokens
- Any secret that needs secure storage

**Example:**
```python
from continuum.core.security_utils import hash_credential

api_key = "cm_abc123def456"
hashed = hash_credential(api_key)
# Returns: "salt_hex:hash_hex"

# Store in database
db.execute("INSERT INTO api_keys (key_hash) VALUES (?)", (hashed,))
```

**Security:**
- 100,000 iterations (OWASP 2024 recommendation)
- Random 256-bit salt per hash
- Constant-time comparison

### verify_credential(credential, stored_hash)

Verify credential against stored hash.

**Example:**
```python
from continuum.core.security_utils import verify_credential

user_input = "cm_abc123def456"
stored_hash = "abc123...def456:789ghi...012jkl"

if verify_credential(user_input, stored_hash):
    print("Valid credential")
else:
    print("Invalid credential")
```

**Security:**
- Timing-attack resistant
- Handles both PBKDF2 and legacy SHA-256 hashes

---

## Input Validation

### validate_string_input(value, field_name, options...)

Validate and sanitize string input to prevent injection attacks.

**Parameters:**
- `value` (str): Input to validate
- `field_name` (str): Field name for error messages
- `max_length` (int, optional): Maximum length
- `min_length` (int, optional): Minimum length
- `allowed_pattern` (str, optional): Regex pattern input must match
- `forbidden_patterns` (list, optional): List of forbidden patterns
- `check_injections` (bool): Check for SQL/command injection (default: True)

**Example:**
```python
from continuum.core.security_utils import validate_string_input, ValidationError

try:
    # Validate username
    username = validate_string_input(
        user_input,
        field_name="username",
        max_length=50,
        min_length=3,
        allowed_pattern=r'^[a-zA-Z0-9_-]+$'
    )

    # Validate email
    email = validate_string_input(
        email_input,
        field_name="email",
        max_length=100
    )

except ValidationError as e:
    print(f"Invalid input: {e}")
```

**Protects against:**
- SQL injection: `'; DROP TABLE users--`
- Command injection: `; rm -rf /`
- Path traversal: `../../etc/passwd`
- Null byte attacks: `\x00`

### validate_entity_type(entity_type)

Validate entity type against whitelist.

**Example:**
```python
from continuum.core.security_utils import validate_entity_type

entity_type = validate_entity_type("concept")  # Valid
entity_type = validate_entity_type("malicious")  # Raises ValidationError

# Valid entity types:
# concept, decision, session, person, project, tool, event, location, organization
```

---

## Environment Variables

### get_env_secret(key, required=True, min_length=None)

Load secrets from environment with validation.

**Example:**
```python
from continuum.core.security_utils import get_env_secret

# Required secret
api_key = get_env_secret("STRIPE_API_KEY", required=True, min_length=20)

# Optional secret with default
password = get_env_secret("DB_PASSWORD", required=False, default="changeme")
```

**Raises:**
- `ValueError` if required secret is missing
- `ValueError` if secret is too short

### load_env_file(env_path=None)

Load environment variables from .env file.

**Example:**
```python
from continuum.core.security_utils import load_env_file
from pathlib import Path

# Load from default location (.env in project root)
load_env_file()

# Load from specific path
load_env_file(Path("/etc/continuum/.env"))
```

**Requires:**
```bash
pip install python-dotenv
```

---

## Secure Logging

### SecureLogFilter(redact_emails=False)

Logging filter that automatically redacts sensitive data.

**Redacts:**
- API keys: `cm_*, sk-*, pk_*`
- Passwords: `password=secret`
- Tokens: `Bearer abc123`
- Email addresses (optional)

**Example:**
```python
import logging
from continuum.core.security_utils import SecureLogFilter

# Add filter to handler
handler = logging.StreamHandler()
handler.addFilter(SecureLogFilter(redact_emails=True))

logger = logging.getLogger(__name__)
logger.addHandler(handler)

# This will be redacted automatically
logger.info("API key: cm_abc123def456")
# Logs: "API key: cm_***REDACTED***"
```

### setup_secure_logging(level, redact_emails, log_file)

Setup secure logging with automatic redaction.

**Example:**
```python
from continuum.core.security_utils import setup_secure_logging
from pathlib import Path

setup_secure_logging(
    level="INFO",
    redact_emails=True,
    log_file=Path("~/.continuum/logs/app.log")
)

# All logging is now secure
import logging
logger = logging.getLogger(__name__)
logger.info("Secret: sk-abc123")  # Auto-redacted
```

---

## Connection String Builders

### build_postgres_url(user, password, host, port, database, sslmode)

Build secure PostgreSQL connection URL.

**Example:**
```python
from continuum.core.security_utils import build_postgres_url

url = build_postgres_url(
    user="db_user",
    password="pass@123!",  # Special chars are escaped
    host="localhost",
    port=5432,
    database="continuum",
    sslmode="require"  # Default: require
)

# Returns: postgresql://db_user:pass%40123%21@localhost:5432/continuum?sslmode=require

# Use with SQLAlchemy or psycopg2
import psycopg2
conn = psycopg2.connect(url)
```

**Security:**
- Escapes special characters in user/password
- Prevents connection string injection
- Enforces SSL by default

### build_redis_url(host, port, db, password, username, ssl)

Build secure Redis connection URL.

**Example:**
```python
from continuum.core.security_utils import build_redis_url

url = build_redis_url(
    host="localhost",
    port=6379,
    db=0,
    password="redis_secret",
    username=None,  # Redis 6+ only
    ssl=True
)

# Returns: rediss://:redis_secret@localhost:6379/0

import redis
client = redis.from_url(url)
```

**Security:**
- Uses `rediss://` for TLS connections
- Escapes password special characters
- Supports Redis 6+ ACL (username)

---

## Token Generation

### generate_api_key(prefix="cm", length=32)

Generate cryptographically secure API key.

**Example:**
```python
from continuum.core.security_utils import generate_api_key

api_key = generate_api_key(prefix="cm", length=32)
# Returns: cm_abc123def456...

# For different key types
stripe_key = generate_api_key(prefix="sk", length=32)
public_key = generate_api_key(prefix="pk", length=24)
```

**Security:**
- Uses `secrets.token_urlsafe()` (cryptographically secure)
- URL-safe base64 encoding
- Unpredictable

### generate_webhook_secret(length=32)

Generate secure webhook secret.

**Example:**
```python
from continuum.core.security_utils import generate_webhook_secret

webhook_secret = generate_webhook_secret(32)
# Returns: 64-char hex string

# Use for webhook verification
import os
os.environ["WEBHOOK_SECRET"] = webhook_secret
```

---

## Webhook Verification

### verify_webhook_signature(payload, signature, secret, algorithm)

Verify webhook signature using HMAC.

**Parameters:**
- `payload` (bytes): Request body (raw bytes)
- `signature` (str): Signature from webhook header
- `secret` (str): Webhook secret
- `algorithm` (str): Hash algorithm (default: sha256)
- `header_prefix` (str): Signature prefix (default: "sha256=")

**Example:**
```python
from continuum.core.security_utils import verify_webhook_signature

# FastAPI webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    # Get raw body
    payload = await request.body()

    # Get signature from header
    signature = request.headers.get("X-Hub-Signature-256")

    # Verify
    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(401, "Invalid signature")

    # Process webhook
    data = await request.json()
    ...
```

**Security:**
- HMAC-based verification
- Constant-time comparison
- Supports multiple hash algorithms (sha256, sha512)

**Supported Webhook Formats:**
- GitHub: `sha256=abc123...`
- Stripe: Uses built-in Stripe verification
- Generic: `sha256=abc123...` or just `abc123...`

---

## Migration Examples

### From API Middleware

**Before:**
```python
# continuum/api/middleware.py
def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
```

**After:**
```python
from continuum.core.security_utils import hash_credential

def hash_key(key: str) -> str:
    return hash_credential(key)
```

### From MCP Security

**Before:**
```python
# continuum/mcp/security.py
def validate_input(value, max_length=None):
    if len(value) > max_length:
        raise ValidationError()
    # ... more validation
```

**After:**
```python
from continuum.core.security_utils import validate_string_input

value = validate_string_input(
    value,
    field_name="input",
    max_length=max_length,
    check_injections=True
)
```

### From PostgreSQL Backend

**Before:**
```python
# continuum/storage/postgres_backend.py
conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
```

**After:**
```python
from continuum.core.security_utils import build_postgres_url

conn_str = build_postgres_url(user, password, host, port, database, sslmode="require")
```

---

## Testing

### Unit Tests

```python
import pytest
from continuum.core.security_utils import *

def test_hash_credential():
    """Test credential hashing"""
    hashed = hash_credential("test_secret")
    assert verify_credential("test_secret", hashed)
    assert not verify_credential("wrong_secret", hashed)

    # Verify unique salts
    hash1 = hash_credential("same")
    hash2 = hash_credential("same")
    assert hash1 != hash2

def test_input_validation():
    """Test input validation"""
    # Valid input
    result = validate_string_input("hello", "test", max_length=10)
    assert result == "hello"

    # SQL injection
    with pytest.raises(ValidationError):
        validate_string_input("'; DROP TABLE--", "test")

    # Command injection
    with pytest.raises(ValidationError):
        validate_string_input("; rm -rf /", "test")

def test_webhook_verification():
    """Test webhook signature verification"""
    import hmac
    import hashlib

    payload = b'{"event": "test"}'
    secret = "webhook_secret"

    # Generate valid signature
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(payload, f"sha256={sig}", secret)

    # Invalid signature
    assert not verify_webhook_signature(payload, "sha256=invalid", secret)
```

---

## Best Practices

### 1. Always Validate User Input

```python
# BAD
name = request.json["name"]
db.execute(f"SELECT * FROM users WHERE name = '{name}'")

# GOOD
from continuum.core.security_utils import validate_string_input

name = validate_string_input(
    request.json["name"],
    field_name="name",
    max_length=100
)
db.execute("SELECT * FROM users WHERE name = ?", (name,))
```

### 2. Never Log Secrets

```python
# BAD
logger.info(f"API key: {api_key}")

# GOOD
from continuum.core.security_utils import setup_secure_logging

setup_secure_logging()  # Auto-redacts secrets
logger.info(f"API key: {api_key}")  # Logged as: "API key: cm_***REDACTED***"
```

### 3. Use Environment Variables for Secrets

```python
# BAD
STRIPE_KEY = "sk_live_abc123..."

# GOOD
from continuum.core.security_utils import get_env_secret

STRIPE_KEY = get_env_secret("STRIPE_SECRET_KEY", required=True, min_length=20)
```

### 4. Build Connection Strings Securely

```python
# BAD
db_url = f"postgresql://{user}:{password}@{host}/{db}"

# GOOD
from continuum.core.security_utils import build_postgres_url

db_url = build_postgres_url(user, password, host, 5432, db, sslmode="require")
```

### 5. Verify Webhook Signatures

```python
# BAD
data = await request.json()
process_webhook(data)  # No verification!

# GOOD
from continuum.core.security_utils import verify_webhook_signature

payload = await request.body()
signature = request.headers.get("X-Signature")

if not verify_webhook_signature(payload, signature, SECRET):
    raise HTTPException(401, "Invalid signature")

data = await request.json()
process_webhook(data)
```

---

## FAQ

### Q: Should I use this for all password hashing?

**A:** Yes! `hash_credential()` is suitable for:
- API keys
- User passwords
- Tokens
- Any credential that needs secure storage

It uses PBKDF2 with 100k iterations, which is the OWASP 2024 recommendation.

### Q: Can I adjust the number of iterations?

**A:** Yes, but not recommended unless you have specific performance constraints:

```python
# Custom iterations (not recommended)
hashed = hash_credential("password", iterations=200_000)
verified = verify_credential("password", hashed, iterations=200_000)
```

### Q: How do I migrate existing SHA-256 hashes?

**A:** `verify_credential()` has backwards compatibility:

```python
# Works with both old and new hashes
old_hash = "abc123..."  # SHA-256 (no salt)
new_hash = "salt:hash"  # PBKDF2 (with salt)

verify_credential("password", old_hash)  # Works
verify_credential("password", new_hash)  # Works
```

Then re-hash on next login:
```python
if verify_credential(password, stored_hash):
    # Update to new format
    if ':' not in stored_hash:
        new_hash = hash_credential(password)
        update_database(user_id, new_hash)
```

### Q: What if I need to disable injection checks?

**A:** Use `check_injections=False` (not recommended):

```python
# Only if you trust the input source
validate_string_input(
    trusted_input,
    field_name="data",
    check_injections=False
)
```

### Q: How do I test webhook verification locally?

**A:** Generate test signatures:

```python
import hmac
import hashlib

payload = b'{"test": "data"}'
secret = "test_secret"

signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
print(f"Test signature: sha256={signature}")

# Use in request
headers = {"X-Signature": f"sha256={signature}"}
```

---

## Support

For security issues or questions:
- File an issue: [GitHub Issues]
- Security vulnerabilities: Email security@continuum.ai
- Documentation: See `/docs/SECURITY_AUDIT.md`

---

**Last Updated**: 2025-12-06
**Module Version**: 1.0.0
