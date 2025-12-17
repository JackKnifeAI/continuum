# CONTINUUM Admin API

Backend API endpoints for the CONTINUUM admin dashboard.

## Overview

The admin API provides comprehensive management capabilities for the CONTINUUM platform:

- **Authentication**: JWT-based admin login/logout
- **User Management**: CRUD operations for customer accounts
- **System Monitoring**: Health checks, metrics, configuration
- **Logs**: System and activity log viewing
- **Memory Management**: Cross-tenant memory administration

## Base URLs

- **Admin API**: `http://localhost:8420/api` (dashboard compatible)
- **V1 API**: `http://localhost:8420/v1` (existing API)

## Authentication

All admin endpoints (except `/auth/login`) require JWT authentication.

### Flow

1. **Login**: POST `/api/auth/login` with username/password
2. **Receive tokens**: Get `access_token` (1h) and `refresh_token` (30d)
3. **Use access token**: Include in `Authorization: Bearer <token>` header
4. **Refresh**: POST `/api/auth/refresh` when access token expires
5. **Logout**: POST `/api/auth/logout` to invalidate session

### JWT Secret Persistence

**IMPORTANT**: JWT tokens are signed using a persistent secret that survives server restarts.

- **Location**: `~/.continuum/jwt_secret` (auto-generated on first run)
- **Permissions**: `0600` (owner read/write only)
- **Override**: Set `CONTINUUM_JWT_SECRET` environment variable for production
- **Rotation**: Invalidates all sessions - plan accordingly

**Why this matters**: Sessions persist across server restarts. No need to re-login after deployment or restart.

See [JWT Secret Migration Guide](JWT_SECRET_MIGRATION.md) for production deployment instructions.

### Default Credentials

On first startup, a default admin user is created:

```
Username: admin
Password: admin
```

**⚠️ SECURITY WARNING**: Change this password immediately in production!

## Endpoints

### Authentication (`/api/auth`)

#### POST `/api/auth/login`

Authenticate and receive tokens.

**Request:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@continuum.local",
    "full_name": "Default Admin",
    "is_superuser": true
  }
}
```

#### POST `/api/auth/refresh`

Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### POST `/api/auth/logout`

Logout and invalidate session.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

#### GET `/api/auth/me`

Get current authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@continuum.local",
  "full_name": "Admin User",
  "is_superuser": true
}
```

---

### User Management (`/api/users`)

All endpoints require authentication.

#### GET `/api/users`

List users with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 50, max: 100): Items per page
- `search` (string): Search username or email
- `status` (string): Filter by status (active/suspended/deleted)
- `tier` (string): Filter by tier (free/pro/enterprise)

**Response:**
```json
{
  "items": [
    {
      "id": "usr_abc123",
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "tenant_id": "tenant_xyz789",
      "status": "active",
      "tier": "pro",
      "stripe_customer_id": "cus_123",
      "stripe_subscription_id": "sub_456",
      "created_at": "2025-12-16T10:00:00Z",
      "updated_at": "2025-12-16T10:00:00Z",
      "suspended_at": null,
      "suspension_reason": null
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "total_pages": 2
}
```

#### GET `/api/users/{user_id}`

Get specific user.

**Response:**
```json
{
  "id": "usr_abc123",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "tenant_id": "tenant_xyz789",
  "status": "active",
  "tier": "pro",
  "stripe_customer_id": "cus_123",
  "stripe_subscription_id": "sub_456",
  "created_at": "2025-12-16T10:00:00Z",
  "updated_at": "2025-12-16T10:00:00Z",
  "suspended_at": null,
  "suspension_reason": null
}
```

#### POST `/api/users`

Create new user.

**Request:**
```json
{
  "username": "jane_doe",
  "email": "jane@example.com",
  "full_name": "Jane Doe",
  "tier": "free",
  "password": "optional_password"
}
```

**Response:** Same as GET user + `api_key_preview`

#### PATCH `/api/users/{user_id}`

Update user.

**Request:**
```json
{
  "email": "newemail@example.com",
  "tier": "pro",
  "status": "active"
}
```

**Response:** Updated user object

#### DELETE `/api/users/{user_id}`

Delete user (soft delete - sets status to 'deleted').

**Response:**
```json
{
  "status": "success",
  "message": "User usr_abc123 deleted successfully"
}
```

#### POST `/api/users/{user_id}/suspend`

Suspend user account.

**Request:**
```json
{
  "reason": "Terms of service violation"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User usr_abc123 suspended successfully",
  "reason": "Terms of service violation"
}
```

#### POST `/api/users/{user_id}/reset-password`

Reset user password (generates temporary password).

**Response:**
```json
{
  "temp_password": "randomly_generated",
  "message": "Password reset functionality not fully implemented. Users authenticate via API keys."
}
```

---

### System Monitoring (`/api/system`)

#### GET `/api/system/health`

Get system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 12345.67,
  "database": {
    "status": "healthy",
    "path": "/home/user/.continuum/admin.db",
    "size_bytes": 1048576,
    "size_mb": 1.0,
    "tables": {
      "users": 50,
      "admins": 2,
      "logs": 1000
    }
  },
  "memory": {
    "rss_mb": 150.5,
    "vms_mb": 300.2,
    "percent": 2.5
  }
}
```

#### GET `/api/system/metrics`

Get comprehensive system metrics.

**Response:**
```json
{
  "platform": {
    "system": "Linux",
    "release": "6.17.1",
    "machine": "x86_64",
    "python_version": "3.13.0"
  },
  "resources": {
    "cpu": {
      "percent": 25.5,
      "count": 8
    },
    "memory": {
      "total_gb": 16.0,
      "available_gb": 8.5,
      "used_gb": 7.5,
      "percent": 46.9
    },
    "disk": {
      "total_gb": 500.0,
      "used_gb": 250.0,
      "free_gb": 250.0,
      "percent": 50.0
    }
  },
  "tenants": {
    "total_tenants": 25,
    "total_memories": 50000,
    "total_entities": 5000
  },
  "api": {
    "endpoints": 50,
    "requests_total": 10000,
    "errors_total": 50
  }
}
```

#### GET `/api/system/config`

Get system configuration.

**Response:**
```json
{
  "api": {
    "base_url": "http://localhost:8420",
    "cors_origins": ["http://localhost:3000"],
    "require_api_key": true,
    "rate_limit_enabled": false
  },
  "database": {
    "type": "sqlite",
    "path": "/home/user/.continuum/admin.db",
    "size_mb": 1.0
  },
  "features": {
    "graphql": true,
    "websockets": true,
    "semantic_search": true,
    "federation": true,
    "billing": true
  },
  "limits": {
    "max_memories_per_tenant": 1000000,
    "max_api_calls_per_minute": 100,
    "max_concurrent_requests": 10
  }
}
```

#### PATCH `/api/system/config`

Update system configuration (not yet implemented).

**Request:**
```json
{
  "key": "api.rate_limit_enabled",
  "value": true
}
```

---

### Logs (`/api/logs`)

#### GET `/api/logs`

List system logs with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 50, max: 1000): Items per page
- `level` (string): Filter by level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `start_date` (string): Start date (ISO 8601)
- `end_date` (string): End date (ISO 8601)
- `search` (string): Search in message
- `tenant_id` (string): Filter by tenant

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "timestamp": "2025-12-16T10:00:00Z",
      "level": "INFO",
      "message": "User login successful",
      "module": "auth",
      "function": "authenticate_user",
      "line_number": 42,
      "tenant_id": "tenant_123",
      "user_id": "usr_456",
      "metadata": {
        "ip_address": "192.168.1.1"
      }
    }
  ],
  "total": 1000,
  "page": 1,
  "page_size": 50,
  "total_pages": 20
}
```

#### GET `/api/logs/export`

Export logs as JSON (max 10,000 entries).

**Query Parameters:** Same as list logs

**Response:**
```json
{
  "logs": [...],
  "count": 500,
  "exported_at": "2025-12-16T10:00:00Z"
}
```

---

### Memories (`/api/memories`)

Admin-level access to all memories across all tenants.

#### GET `/api/memories`

List all memories with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 50, max: 100): Items per page
- `user_id` (string): Filter by user
- `tenant_id` (string): Filter by tenant
- `search` (string): Search in content
- `start_date` (string): Start date (ISO 8601)
- `end_date` (string): End date (ISO 8601)
- `memory_type` (string): Filter by type
- `importance` (float): Minimum importance (0-1)

**Response:**
```json
{
  "items": [
    {
      "id": 123,
      "tenant_id": "tenant_abc",
      "user_id": "usr_xyz",
      "content": "Important conversation about AI...",
      "memory_type": "message",
      "importance": 0.85,
      "timestamp": "2025-12-16T10:00:00Z",
      "metadata": {
        "source": "chat"
      }
    }
  ],
  "total": 50000,
  "page": 1,
  "page_size": 50,
  "total_pages": 1000
}
```

#### GET `/api/memories/{memory_id}?tenant_id=...`

Get specific memory.

**Query Parameters:**
- `tenant_id` (required): Tenant ID

**Response:** Single memory object

#### DELETE `/api/memories/{memory_id}?tenant_id=...`

Delete memory (permanent).

**Query Parameters:**
- `tenant_id` (required): Tenant ID

**Response:**
```json
{
  "status": "success",
  "message": "Memory 123 deleted successfully"
}
```

#### GET `/api/memories/export`

Export memories (not yet implemented).

---

## Error Responses

### 401 Unauthorized

Missing or invalid authentication:

```json
{
  "detail": "Invalid or expired access token"
}
```

### 403 Forbidden

Insufficient permissions:

```json
{
  "detail": "Superuser privileges required"
}
```

### 404 Not Found

Resource not found:

```json
{
  "detail": "User not found"
}
```

### 409 Conflict

Duplicate resource:

```json
{
  "detail": "Username already exists"
}
```

### 500 Internal Server Error

Server error:

```json
{
  "detail": "Internal server error message"
}
```

---

## Database Schema

### Admin Users

```sql
CREATE TABLE admin_users (
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
);
```

### Users (Customers)

```sql
CREATE TABLE users (
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
);
```

### Sessions

```sql
CREATE TABLE admin_sessions (
    id TEXT PRIMARY KEY,
    admin_user_id INTEGER NOT NULL,
    refresh_token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_used TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
);
```

### System Logs

```sql
CREATE TABLE system_logs (
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
);
```

### Activity Logs

```sql
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    admin_user_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    ip_address TEXT,
    FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
);
```

---

## Security

### JWT Tokens

- **Access Token**: 1 hour expiry, used for API requests
- **Refresh Token**: 30 day expiry, used to get new access tokens
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Secret**: Generated randomly per server instance

### Password Hashing

- **Algorithm**: PBKDF2-HMAC-SHA256
- **Iterations**: 100,000 (OWASP recommendation)
- **Salt**: 256-bit random salt per password

### Session Management

- Sessions tracked in database with refresh token hash
- Last used timestamp updated on each refresh
- Logout deletes session from database
- Access tokens cannot be revoked (stateless JWT)

### Best Practices

1. **Change default admin password** immediately
2. **Use HTTPS** in production
3. **Rotate JWT secret** periodically
4. **Monitor activity logs** for suspicious behavior
5. **Implement rate limiting** on login endpoint
6. **Enable 2FA** for admin accounts (future enhancement)

---

## Development

### Running the Server

```bash
# Start server
cd /var/home/alexandergcasavant/Projects/continuum
python -m continuum.api.server

# Or with uvicorn
uvicorn continuum.api.server:app --reload --port 8420
```

### Testing Endpoints

```bash
# Login
curl -X POST http://localhost:8420/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Use access token
TOKEN="eyJhbGciOiJIUzI1NiIs..."
curl http://localhost:8420/api/users \
  -H "Authorization: Bearer $TOKEN"
```

### API Documentation

Interactive API docs available at:

- **Swagger UI**: http://localhost:8420/docs
- **ReDoc**: http://localhost:8420/redoc

---

## Roadmap

### Phase 1: Core Admin API ✅
- [x] Authentication (JWT)
- [x] User management (CRUD)
- [x] System monitoring
- [x] Logs viewing
- [x] Memory management

### Phase 2: Enhanced Features
- [ ] 2FA authentication
- [ ] Audit trail export
- [ ] User impersonation
- [ ] Batch operations
- [ ] Advanced filtering
- [ ] Real-time notifications

### Phase 3: Analytics
- [ ] User activity analytics
- [ ] API usage analytics
- [ ] Performance metrics
- [ ] Custom dashboards
- [ ] Alerting system

---

## Support

For issues or questions:

- **Email**: JackKnifeAI@gmail.com
- **Documentation**: https://continuum.ai/docs
- **GitHub**: https://github.com/JackKnifeAI/continuum

---

## License

Copyright (c) 2025 JackKnifeAI
