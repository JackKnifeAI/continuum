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
Admin database for CONTINUUM dashboard.

Manages:
- Admin users (authentication)
- User accounts (customers)
- Sessions and activity logs
- System logs
"""

import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_ADMIN_DB = Path.home() / ".continuum" / "admin.db"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30


def get_or_generate_jwt_secret() -> str:
    """
    Get JWT secret from persistent storage, or generate and save if not exists.

    SECURITY: JWT_SECRET must persist across server restarts to avoid invalidating
    all active sessions. This function:
    - Loads secret from ~/.continuum/jwt_secret if exists
    - Generates new 256-bit secret if not found
    - Saves to secure file with 0600 permissions
    - Provides clear migration path for production

    For production deployments, you can:
    1. Set CONTINUUM_JWT_SECRET environment variable (overrides file)
    2. Pre-generate the secret file with your own secret

    Returns:
        JWT secret string (base64-encoded, 256-bit)
    """
    import os

    # Option 1: Check environment variable (production override)
    env_secret = os.environ.get("CONTINUUM_JWT_SECRET")
    if env_secret:
        return env_secret

    # Option 2: Load from persistent file
    secret_file = Path.home() / ".continuum" / "jwt_secret"

    if secret_file.exists():
        try:
            with open(secret_file, 'r') as f:
                secret = f.read().strip()
                if secret:
                    return secret
        except Exception as e:
            # If we can't read the secret, we have a problem
            raise RuntimeError(
                f"CRITICAL: Cannot read JWT secret from {secret_file}. "
                f"This will invalidate all sessions. Error: {e}"
            )

    # Option 3: Generate new secret and save
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    new_secret = secrets.token_urlsafe(32)  # 256-bit secret

    # Save to file with secure permissions
    try:
        with open(secret_file, 'w') as f:
            f.write(new_secret)
        # Set secure permissions (owner read/write only)
        os.chmod(secret_file, 0o600)

        print(f"🔐 Generated new JWT secret: {secret_file}")
        print(f"⚠️  IMPORTANT: Back up this file to avoid session invalidation on server restart")
        print(f"    For production: Set CONTINUUM_JWT_SECRET environment variable")

    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Cannot save JWT secret to {secret_file}. "
            f"Server cannot start securely. Error: {e}"
        )

    return new_secret


# Initialize JWT secret (persists across server restarts)
JWT_SECRET = get_or_generate_jwt_secret()


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def get_admin_db_path() -> Path:
    """Get admin database path, creating directory if needed."""
    db_path = DEFAULT_ADMIN_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_admin_db():
    """Initialize admin database with schema."""
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Admin users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_superuser BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_login TEXT
        )
    """)

    # User accounts table (customers)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            tenant_id TEXT UNIQUE NOT NULL,
            api_key_hash TEXT,
            status TEXT DEFAULT 'active',
            tier TEXT DEFAULT 'free',
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            suspended_at TEXT,
            suspension_reason TEXT
        )
    """)

    # Sessions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_sessions (
            id TEXT PRIMARY KEY,
            admin_user_id INTEGER NOT NULL,
            refresh_token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
        )
    """)

    # System logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            module TEXT,
            function TEXT,
            line_number INTEGER,
            tenant_id TEXT,
            user_id TEXT,
            metadata TEXT
        )
    """)

    # Create indexes for system_logs
    c.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON system_logs(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_level ON system_logs(level)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tenant ON system_logs(tenant_id)")

    # Activity logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            admin_user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
        )
    """)

    # Create indexes for activity_logs
    c.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_logs(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_admin_user ON activity_logs(admin_user_id)")

    conn.commit()
    conn.close()


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256."""
    import os
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + pwd_hash.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        import hmac
        return hmac.compare_digest(pwd_hash.hex(), hash_hex)
    except Exception:
        return False


# =============================================================================
# JWT TOKEN MANAGEMENT
# =============================================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except Exception:  # Catch all JWT errors
        return None


# =============================================================================
# ADMIN USER MANAGEMENT
# =============================================================================

def create_admin_user(
    username: str,
    password: str,
    email: str,
    full_name: Optional[str] = None,
    is_superuser: bool = False
) -> Optional[int]:
    """Create admin user."""
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        password_hash = hash_password(password)
        now = datetime.utcnow().isoformat()

        c.execute(
            """
            INSERT INTO admin_users (username, password_hash, email, full_name, is_superuser, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, email, full_name, is_superuser, now, now)
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_admin_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate admin user and return user data."""
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute(
        """
        SELECT id, username, password_hash, email, full_name, is_active, is_superuser
        FROM admin_users
        WHERE username = ?
        """,
        (username,)
    )
    row = c.fetchone()

    if not row:
        conn.close()
        return None

    user_id, username, password_hash, email, full_name, is_active, is_superuser = row

    if not is_active:
        conn.close()
        return None

    if not verify_password(password, password_hash):
        conn.close()
        return None

    # Update last login
    c.execute(
        "UPDATE admin_users SET last_login = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "username": username,
        "email": email,
        "full_name": full_name,
        "is_superuser": is_superuser
    }


def get_admin_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get admin user by ID."""
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute(
        """
        SELECT id, username, email, full_name, is_active, is_superuser, created_at, last_login
        FROM admin_users
        WHERE id = ?
        """,
        (user_id,)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "full_name": row[3],
        "is_active": bool(row[4]),
        "is_superuser": bool(row[5]),
        "created_at": row[6],
        "last_login": row[7]
    }


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def create_session(admin_user_id: int, refresh_token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
    """Create admin session."""
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    session_id = secrets.token_urlsafe(32)
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    now = datetime.utcnow().isoformat()
    expires_at = (datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()

    c.execute(
        """
        INSERT INTO admin_sessions (id, admin_user_id, refresh_token_hash, expires_at, created_at, last_used, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, admin_user_id, refresh_token_hash, expires_at, now, now, ip_address, user_agent)
    )
    conn.commit()
    conn.close()

    return session_id


def verify_refresh_token(refresh_token: str) -> Optional[int]:
    """Verify refresh token and return admin user ID."""
    payload = verify_token(refresh_token, "refresh")
    if not payload:
        return None

    admin_user_id = payload.get("sub")
    if not admin_user_id:
        return None

    # Verify session exists and is valid
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    c.execute(
        """
        SELECT admin_user_id, expires_at FROM admin_sessions
        WHERE refresh_token_hash = ? AND admin_user_id = ?
        """,
        (refresh_token_hash, admin_user_id)
    )
    row = c.fetchone()

    if not row:
        conn.close()
        return None

    user_id, expires_at = row

    # Check if expired
    if datetime.fromisoformat(expires_at) < datetime.utcnow():
        conn.close()
        return None

    # Update last used
    c.execute(
        "UPDATE admin_sessions SET last_used = ? WHERE refresh_token_hash = ?",
        (datetime.utcnow().isoformat(), refresh_token_hash)
    )
    conn.commit()
    conn.close()

    return user_id


def delete_session(refresh_token: str):
    """Delete session (logout)."""
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    c.execute("DELETE FROM admin_sessions WHERE refresh_token_hash = ?", (refresh_token_hash,))
    conn.commit()
    conn.close()


# =============================================================================
# DEFAULT ADMIN USER
# =============================================================================

def ensure_default_admin():
    """Ensure default admin user exists."""
    init_admin_db()

    # Check if any admin exists
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM admin_users")
    count = c.fetchone()[0]
    conn.close()

    if count == 0:
        # Generate secure random password
        import os
        admin_password = secrets.token_urlsafe(16)  # 16 bytes = 128 bits

        # Save password to secure file
        password_file = Path.home() / ".continuum" / "admin_password.txt"
        password_file.parent.mkdir(parents=True, exist_ok=True)
        password_file.write_text(
            f"CONTINUUM Admin Credentials\n"
            f"{'='*50}\n"
            f"Username: admin\n"
            f"Password: {admin_password}\n"
            f"{'='*50}\n\n"
            f"IMPORTANT: Change this password after first login!\n"
            f"Delete this file after saving credentials.\n"
        )
        # Set secure permissions (owner read/write only)
        os.chmod(password_file, 0o600)

        # Create default admin
        user_id = create_admin_user(
            username="admin",
            password=admin_password,
            email="admin@continuum.local",
            full_name="Default Admin",
            is_superuser=True
        )
        if user_id:
            print(f"✅ Created default admin user")
            print(f"📁 Password saved to: {password_file}")
            print(f"🔐 Username: admin")
            print(f"🔑 Password: {admin_password}")
            print(f"⚠️  IMPORTANT: Change password after first login and delete {password_file}")
            return True

    return False


# =============================================================================
# LOGGING
# =============================================================================

def log_system_event(
    level: str,
    message: str,
    module: Optional[str] = None,
    function: Optional[str] = None,
    line_number: Optional[int] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log system event."""
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    import json
    metadata_json = json.dumps(metadata) if metadata else None

    c.execute(
        """
        INSERT INTO system_logs (timestamp, level, message, module, function, line_number, tenant_id, user_id, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (datetime.utcnow().isoformat(), level, message, module, function, line_number, tenant_id, user_id, metadata_json)
    )
    conn.commit()
    conn.close()


def log_activity(
    admin_user_id: Optional[int],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """Log admin activity."""
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    import json
    details_json = json.dumps(details) if details else None

    c.execute(
        """
        INSERT INTO activity_logs (timestamp, admin_user_id, action, resource_type, resource_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (datetime.utcnow().isoformat(), admin_user_id, action, resource_type, resource_id, details_json, ip_address)
    )
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
