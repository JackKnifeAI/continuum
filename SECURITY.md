# Security Policy

## Supported Versions

Currently supporting security updates for:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

1. **Email**: Send details to the project maintainer (contact info in README)
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Updates**: Weekly until resolved
- **Fix Timeline**: Critical issues within 7 days, others within 30 days

### Disclosure Policy

- We request 90 days before public disclosure
- We'll credit you in the security advisory (unless you prefer anonymity)
- We may offer recognition in CONTRIBUTORS.md

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version
2. **Secure Configuration**:
   - Set strong `CONTINUUM_SECRET_KEY`
   - Restrict `CONTINUUM_CORS_ORIGINS`
   - Enable `CONTINUUM_REQUIRE_API_KEY=true`
3. **Environment Secrets**:
   - Never commit `.env` files
   - Use secrets management in production
   - Rotate API keys quarterly
4. **Network Security**:
   - Deploy behind HTTPS
   - Use firewall rules
   - Implement rate limiting

### For Developers

1. **Code Review**: All security-sensitive changes require review
2. **Testing**: Run security tests before merging
3. **Dependencies**: Keep dependencies updated
4. **Static Analysis**: Run `bandit` and `safety` checks

## Security Features

### Implemented

- ✅ Parameterized SQL queries (SQL injection protection)
- ✅ PBKDF2 API key hashing (100k iterations)
- ✅ Multi-tenant data isolation
- ✅ Input validation (Pydantic schemas)
- ✅ CORS configuration
- ✅ Rate limiting (stub - Redis recommended)
- ✅ Message signing (federation)
- ✅ TLS/HTTPS support

### Roadmap

- ⏳ Admin role-based access control (Q1 2026)
- ⏳ WebSocket authentication (Q1 2026)
- ⏳ Database encryption at rest (Q2 2026)
- ⏳ Audit logging (Q2 2026)
- ⏳ Intrusion detection (Q3 2026)

## Security Audit

Last comprehensive audit: **2025-12-06**

Full audit report: [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md)

### Key Findings

- **Critical**: 2 (fixed)
- **High**: 4 (2 fixed, 2 planned)
- **Medium**: 4 (documented)
- **Low**: 2 (informational)

## Responsible Disclosure

We appreciate security researchers who responsibly disclose vulnerabilities. We commit to:

1. Prompt acknowledgment
2. Transparent communication
3. Timely fixes
4. Public credit (with permission)

## Security Contacts

- **Primary**: Project maintainer (see README)
- **Response Time**: 48 hours
- **PGP Key**: Available on request

## Security Considerations

### Data Privacy

CONTINUUM handles potentially sensitive AI memory data. Consider these security practices:

#### 1. Local-First by Default

```python
# Data stored locally - you control access
memory = Continuum(storage_path="./secure_data")
```

**Best Practices**:
- Store database files on encrypted filesystems
- Set restrictive file permissions (0600)
- Avoid storing sensitive data in cleartext

#### 2. Encryption at Rest (Optional)

```python
# Enable encryption for sensitive deployments
from continuum import Continuum

encryption_key = os.environ.get('CONTINUUM_ENCRYPTION_KEY')  # 32-byte key
memory = Continuum(
    storage_path="./data",
    encryption_key=encryption_key.encode()
)
```

**Key Management**:
- Store keys in environment variables or key management systems
- Never commit keys to version control
- Rotate keys periodically
- Use different keys for different environments

#### 3. Database File Permissions

Ensure SQLite database files have restrictive permissions:

```bash
# Set permissions after creation
chmod 600 ./data/continuum.db

# Verify
ls -la ./data/continuum.db
# Should show: -rw------- (owner read/write only)
```

### Network Security

#### PostgreSQL Backend

When using PostgreSQL in production:

```python
# Use TLS/SSL connections
memory = Continuum(
    storage_backend="postgresql",
    connection_string="postgresql://user:pass@localhost/db?sslmode=require"
)
```

**Best Practices**:
- Always use `sslmode=require` or `sslmode=verify-full`
- Use strong passwords (minimum 20 characters)
- Restrict database access by IP (pg_hba.conf)
- Enable PostgreSQL audit logging
- Regular security updates

#### Multi-Instance Coordination

When coordinating across network:

```python
# Secure coordination (future feature)
memory = Continuum(
    coordination_url="https://coord.example.com",
    api_key=os.environ.get('CONTINUUM_API_KEY'),
    tls_verify=True
)
```

**Best Practices**:
- Use HTTPS for all network communication
- Authenticate instances with API keys or certificates
- Rate limit sync requests
- Monitor for unusual sync patterns

### Input Validation

CONTINUUM sanitizes inputs, but be aware:

#### 1. Text Length Limits

```python
# Extremely long inputs are rejected
try:
    memory.learn("A" * 10_000_000)  # Will raise ValidationError
except ValidationError:
    pass
```

#### 2. SQL Injection Protection

All queries use parameterized statements:

```python
# Safe - parameters are escaped
memory.recall("user's input with 'quotes'")

# Internal implementation uses:
cursor.execute("SELECT * FROM concepts WHERE name LIKE ?", (query,))
```

#### 3. Path Traversal Protection

Storage paths are validated:

```python
# Dangerous - rejected
memory = Continuum(storage_path="../../etc/passwd")  # ValidationError

# Safe - contained within allowed directory
memory = Continuum(storage_path="./data")
```

### Authentication and Authorization

#### Current State (v0.1.x)

CONTINUUM v0.1 has **no built-in authentication**. Security model:

- **File system permissions** control access
- **Process isolation** separates instances
- **No network API** in default configuration

#### Future (v0.2+)

REST API will include:

- **API key authentication** for service mode
- **Role-based access control** for multi-tenant deployments
- **Audit logging** of all operations
- **Rate limiting** to prevent abuse

### Dependency Security

#### Automated Scanning

We use:
- **Dependabot** - Automatic dependency updates
- **pip-audit** - Python package vulnerability scanning
- **Safety** - Check known security vulnerabilities

#### Manual Review

```bash
# Check for known vulnerabilities
pip-audit

# Update dependencies
pip install --upgrade continuum-memory
```

### Secure Coding Practices

#### 1. No Secrets in Code

```python
# BAD - hardcoded credentials
memory = Continuum(
    connection_string="postgresql://admin:password123@localhost/db"
)

# GOOD - environment variables
memory = Continuum(
    connection_string=os.environ.get('DATABASE_URL')
)
```

#### 2. Proper Error Handling

```python
# Don't expose internal details in errors
try:
    memory.recall("query")
except Exception as e:
    # BAD: log.error(f"Database error: {e}")  # Might expose structure
    log.error("Query failed")  # GOOD: Generic message
    raise ContinuumError("Query failed") from e
```

#### 3. Secure Defaults

CONTINUUM uses secure defaults:
- SQLite databases created with 0600 permissions
- Connections time out after 30 seconds
- Query limits prevent resource exhaustion
- Auto-optimize prevents unbounded growth

## Security Features

### Current (v0.1.x)

- ✅ Parameterized SQL queries (SQL injection protection)
- ✅ Input validation and sanitization
- ✅ Path traversal protection
- ✅ Restrictive file permissions
- ✅ Optional encryption at rest
- ✅ Resource limits (query size, text length)
- ✅ Transaction isolation (ACID compliance)

### Planned (v0.2+)

- 🔄 API key authentication
- 🔄 Role-based access control (RBAC)
- 🔄 Audit logging
- 🔄 Rate limiting
- 🔄 TLS/SSL for all network communication
- 🔄 Secrets management integration (Vault, etc.)
- 🔄 Two-factor authentication (2FA)

## Threat Model

### In Scope

**Data Confidentiality**:
- Unauthorized access to knowledge graph
- Interception of sync traffic (PostgreSQL backend)
- Exposure of sensitive concepts/entities

**Data Integrity**:
- Tampering with stored knowledge
- SQL injection attacks
- Malicious input corruption

**Availability**:
- Resource exhaustion (DoS)
- Database corruption
- Sync failures causing data loss

### Out of Scope (Current Version)

- Physical access to server
- Compromised host operating system
- Side-channel attacks
- Attacks requiring root/admin privileges
- Social engineering

## Security Checklist

### Development

- [ ] All inputs validated
- [ ] Parameterized queries used
- [ ] No secrets in code
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies scanned for vulnerabilities
- [ ] Code reviewed for security issues

### Deployment

- [ ] Database files have 0600 permissions
- [ ] Encryption enabled for sensitive data
- [ ] TLS/SSL used for PostgreSQL connections
- [ ] Environment variables used for secrets
- [ ] Regular backups configured
- [ ] Logs monitored for suspicious activity
- [ ] Security updates applied promptly

### Production

- [ ] Access logs reviewed regularly
- [ ] Dependency updates automated
- [ ] Incident response plan in place
- [ ] Regular security audits scheduled
- [ ] Backup restoration tested
- [ ] Key rotation scheduled

## Vulnerability Disclosure Timeline

1. **T+0**: Vulnerability reported
2. **T+48h**: Acknowledgment sent to reporter
3. **T+5d**: Initial assessment and severity rating
4. **T+30d**: Fix developed and tested (critical issues)
5. **T+90d**: Fix developed and tested (non-critical issues)
6. **T+Fix**: Security advisory published
7. **T+Fix+7d**: Public disclosure (coordinated with reporter)

## Security Best Practices for Users

### Minimum Security Configuration

```python
import os
from continuum import Continuum

# Use environment variables for sensitive config
memory = Continuum(
    storage_path=os.environ.get('CONTINUUM_DATA_PATH', './data'),
    encryption_key=os.environ.get('CONTINUUM_ENCRYPTION_KEY'),
)

# Set restrictive permissions
import os
os.chmod('./data/continuum.db', 0o600)
```

### Production Security Configuration

```python
import os
from continuum import Continuum

memory = Continuum(
    storage_backend="postgresql",
    connection_string=os.environ.get('DATABASE_URL'),  # Uses TLS
    instance_id=f"production-{os.environ.get('HOSTNAME')}",
    encryption_key=os.environ.get('CONTINUUM_ENCRYPTION_KEY')
)

# Enable audit logging
import logging
logging.basicConfig(
    filename='/var/log/continuum/audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Regular Maintenance

```python
# Periodic backups
import shutil
from datetime import datetime

def backup_memory():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"./backups/continuum_{timestamp}.db"
    memory.backup(backup_path)

    # Verify backup
    backup_memory = Continuum(storage_path=backup_path)
    assert backup_memory.get_stats()['concepts'] > 0
    backup_memory.close()

# Run weekly
import schedule
schedule.every().week.do(backup_memory)
```

## Contact

**Security Team**: security@continuum-project.org

**PGP Key**: [Coming Soon]

**Response Time**: 48 hours for acknowledgment

---

**Security is everyone's responsibility. Report vulnerabilities responsibly.**
