# JWT Secret Migration Guide

## Overview

**Issue**: Prior to this fix, `JWT_SECRET` was regenerated on every server restart, invalidating all active admin sessions.

**Fix**: JWT secret now persists in `~/.continuum/jwt_secret` across restarts.

**Impact**: Admin users no longer need to re-login after server restart.

---

## For New Deployments

No action needed! The JWT secret will be automatically generated on first run and persisted.

When you start the CONTINUUM API server for the first time, you'll see:

```
🔐 Generated new JWT secret: /home/user/.continuum/jwt_secret
⚠️  IMPORTANT: Back up this file to avoid session invalidation on server restart
    For production: Set CONTINUUM_JWT_SECRET environment variable
```

**Recommendation**: Back up the `~/.continuum/jwt_secret` file to your secrets management system.

---

## For Existing Deployments

### Automatic Migration

If you're already running CONTINUUM, the fix will automatically apply:

1. **First restart after upgrade**: A new JWT secret will be generated and persisted
2. **Effect**: All existing admin sessions will be invalidated (one-time)
3. **After that**: Sessions will persist across restarts as expected

### Manual Migration (Production)

For production deployments, you should set the JWT secret explicitly:

#### Option 1: Environment Variable (Recommended)

```bash
# Generate a secure secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in your environment
export CONTINUUM_JWT_SECRET="your_generated_secret_here"

# Or add to systemd service
Environment=CONTINUUM_JWT_SECRET=your_generated_secret_here
```

#### Option 2: Pre-create Secret File

```bash
# Generate secret
SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Save to file
mkdir -p ~/.continuum
echo "$SECRET" > ~/.continuum/jwt_secret
chmod 600 ~/.continuum/jwt_secret

# Verify
ls -la ~/.continuum/jwt_secret
# Should show: -rw------- (owner read/write only)
```

---

## Security Best Practices

### File Permissions

The JWT secret file is automatically created with `0600` permissions (owner read/write only):

```bash
# Verify permissions
ls -la ~/.continuum/jwt_secret
# Expected: -rw-------

# Fix if needed
chmod 600 ~/.continuum/jwt_secret
```

### Backup Strategy

The JWT secret should be backed up securely:

```bash
# Backup to encrypted location
cp ~/.continuum/jwt_secret /secure/backup/location/

# Or store in secrets manager
aws secretsmanager create-secret \
  --name continuum/jwt-secret \
  --secret-string "$(cat ~/.continuum/jwt_secret)"
```

### Secret Rotation

To rotate the JWT secret (invalidates all sessions):

```bash
# Option 1: Delete file (new secret generated on next start)
rm ~/.continuum/jwt_secret
# Restart server

# Option 2: Replace with new secret
python -c "import secrets; print(secrets.token_urlsafe(32))" > ~/.continuum/jwt_secret
chmod 600 ~/.continuum/jwt_secret
# Restart server

# Option 3: Update environment variable
export CONTINUUM_JWT_SECRET="new_secret_here"
# Restart server
```

**Note**: Rotating the secret will log out all admin users. Plan accordingly.

---

## Production Deployment

### Docker

```dockerfile
# Dockerfile
ENV CONTINUUM_JWT_SECRET=${JWT_SECRET}
```

```bash
# docker-compose.yml
services:
  continuum:
    environment:
      - CONTINUUM_JWT_SECRET=${JWT_SECRET}
```

```bash
# .env file (do not commit!)
JWT_SECRET=your_secret_here
```

### Kubernetes

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: continuum-jwt
type: Opaque
stringData:
  jwt-secret: your_secret_here
```

```yaml
# deployment.yaml
env:
  - name: CONTINUUM_JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: continuum-jwt
        key: jwt-secret
```

### Systemd

```ini
# /etc/systemd/system/continuum.service
[Service]
Environment=CONTINUUM_JWT_SECRET=your_secret_here
# Or use EnvironmentFile=/etc/continuum/secrets.env
```

---

## Troubleshooting

### Sessions invalidated after restart

**Cause**: JWT secret changed between restarts.

**Solution**: Verify secret persistence:

```bash
# Check if file exists and has correct permissions
ls -la ~/.continuum/jwt_secret

# Check if environment variable is set
echo $CONTINUUM_JWT_SECRET

# Verify secret is stable across restarts
cat ~/.continuum/jwt_secret  # Before restart
# Restart server
cat ~/.continuum/jwt_secret  # After restart
# Should be identical
```

### "Cannot read JWT secret" error

**Cause**: File permissions issue or corrupted file.

**Solution**:

```bash
# Check permissions
ls -la ~/.continuum/jwt_secret

# Fix permissions
chmod 600 ~/.continuum/jwt_secret

# If corrupted, regenerate
rm ~/.continuum/jwt_secret
# Restart server (will generate new secret)
```

### Different secrets on different servers

**Cause**: Each server generated its own secret.

**Solution**: Share the secret across servers:

```bash
# On primary server
cat ~/.continuum/jwt_secret

# On other servers
echo "secret_from_primary" > ~/.continuum/jwt_secret
chmod 600 ~/.continuum/jwt_secret
# Restart
```

**Better solution**: Use environment variable or secrets manager.

---

## Migration Checklist

### Development

- [ ] Upgrade CONTINUUM to version with fix
- [ ] Restart server (secret auto-generated)
- [ ] Verify secret file exists: `~/.continuum/jwt_secret`
- [ ] Verify permissions: `ls -la ~/.continuum/jwt_secret` (should be `-rw-------`)
- [ ] Test: Login, restart server, verify still logged in

### Production

- [ ] Generate production JWT secret
- [ ] Store in secrets manager (Vault, AWS Secrets Manager, etc.)
- [ ] Set `CONTINUUM_JWT_SECRET` environment variable
- [ ] Deploy updated code
- [ ] Restart server
- [ ] Verify sessions persist across restart
- [ ] Document secret location in runbook
- [ ] Schedule secret rotation (quarterly recommended)

---

## FAQs

**Q: Do I need to rotate the JWT secret?**

A: Yes, as a security best practice. Quarterly rotation is recommended. Note that rotation invalidates all active sessions.

**Q: Can I use the same secret across multiple environments?**

A: No! Each environment (dev, staging, production) should have its own unique secret.

**Q: What happens if I lose the JWT secret?**

A: All admin sessions will be invalidated. Users will need to log in again. Generate a new secret and restart the server.

**Q: Can I use a different secret format?**

A: The secret can be any string, but we recommend 256-bit base64-urlsafe format (generated by `secrets.token_urlsafe(32)`).

**Q: Is the JWT secret encrypted on disk?**

A: No, it's stored in plaintext with restrictive file permissions (0600). For additional security, use an encrypted filesystem or secrets manager.

---

## Related Documentation

- [Security Policy](../SECURITY.md)
- [Deployment Guide](DEPLOYMENT_SECURITY.md)
- [Environment Configuration](../.env.example)

---

**Last Updated**: 2025-12-16

**Status**: CRITICAL FIX - Applied before PyPI republish
