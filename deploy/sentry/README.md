# Sentry Integration for CONTINUUM

This directory contains Sentry configuration for error tracking and performance monitoring in CONTINUUM.

## Overview

Sentry provides:
- **Error Tracking**: Automatic capture of exceptions with full stack traces
- **Performance Monitoring**: Transaction tracking for API endpoints and operations
- **Release Tracking**: Tie errors to specific git commits/releases
- **Environment Separation**: Separate error tracking for dev, staging, prod
- **User Context**: Track errors by tenant/instance (anonymized)
- **Custom Tags**: Filter by operation type, model, federation peer
- **Breadcrumbs**: Debug trail leading to errors
- **Sensitive Data Scrubbing**: Automatic removal of memory content, API keys

## Setup

### 1. Create Sentry Project

1. Sign up at [sentry.io](https://sentry.io)
2. Create a new project:
   - **Platform**: Python
   - **Project Name**: continuum
   - **Team**: Your team name
3. Copy the **DSN** (Data Source Name)

### 2. Install Sentry SDK

```bash
# Install Sentry with FastAPI integration
pip install 'sentry-sdk[fastapi]'

# Or add to requirements.txt
echo 'sentry-sdk[fastapi]>=1.40.0' >> requirements.txt
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Set these environment variables in your deployment:

```bash
# Required: Sentry DSN
export SENTRY_DSN="https://your-key@o123456.ingest.sentry.io/123456"

# Optional: Environment (default: development)
export CONTINUUM_ENV="production"  # or "staging", "development"

# Optional: Release version (auto-detected from git if not set)
export CONTINUUM_RELEASE="v0.2.0"

# Optional: Server name for identification
export CONTINUUM_SERVER_NAME="continuum-prod-1"

# Optional: Performance sampling rate (0.0-1.0, default: 0.1 = 10%)
export SENTRY_TRACES_SAMPLE_RATE="0.1"
```

### 4. Environment-Specific Configuration

**Development:**
```bash
export CONTINUUM_ENV="development"
export SENTRY_TRACES_SAMPLE_RATE="0.0"  # Disable performance tracking
# Optional: Don't set SENTRY_DSN to disable Sentry entirely
```

**Staging:**
```bash
export CONTINUUM_ENV="staging"
export SENTRY_TRACES_SAMPLE_RATE="0.5"  # 50% sampling
```

**Production:**
```bash
export CONTINUUM_ENV="production"
export SENTRY_TRACES_SAMPLE_RATE="0.1"  # 10% sampling (reduce overhead)
```

## Usage

### Automatic Error Tracking

The integration automatically captures:
- **API Errors**: All FastAPI exceptions
- **Database Errors**: SQLAlchemy exceptions
- **Cache Errors**: Redis exceptions
- **Async Errors**: asyncio exceptions
- **CLI Errors**: Command-line errors

No additional code needed - errors are captured automatically!

### Manual Error Capture

For custom error tracking:

```python
from continuum.core.sentry_integration import (
    capture_exception,
    capture_memory_error,
    set_user_context,
    set_operation_context,
    add_breadcrumb,
)

# Capture an exception
try:
    # Your code
    pass
except Exception as e:
    capture_exception(e, level="error", extra={"query": "..."})

# Capture memory operation error
try:
    # Memory operation
    pass
except Exception as e:
    capture_memory_error(
        e,
        operation="recall",
        tenant_id="user_123",
        query="warp drive",
    )

# Set user context (anonymized by default)
set_user_context(tenant_id="user_123", instance_id="claude-001")

# Set operation context
set_operation_context(
    operation="recall",
    model_type="claude-opus-4.5",
    memory_operation="semantic_search",
)

# Add debugging breadcrumbs
add_breadcrumb(
    message="Starting recall operation",
    category="memory",
    level="info",
    data={"query_length": 50},
)
```

### Performance Monitoring

Track operation performance:

```python
from continuum.core.sentry_integration import PerformanceTransaction, monitor_performance

# Context manager
with PerformanceTransaction("memory.recall", "Semantic search recall"):
    # Your code
    result = perform_recall(query)

# Decorator
@monitor_performance("memory.learn", "Extract concepts from conversation")
async def learn(conversation):
    # Your code
    pass
```

## Sensitive Data Protection

The integration **automatically scrubs** sensitive data:

### Removed Data:
- Memory content (user messages, AI responses)
- API keys and tokens
- Passwords
- Request bodies containing messages

### Preserved Data:
- Stack traces
- Error types and messages
- Operation metadata (operation type, tenant ID hash)
- Performance metrics
- Database query patterns (not data)

### Configuration:

The scrubbing happens in `scrub_sensitive_data()` function in `continuum/core/sentry_integration.py`.

To customize, edit the scrubbing logic:

```python
def scrub_sensitive_data(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Add custom scrubbing logic here
    pass
```

## Rate Limiting

To avoid exceeding Sentry quotas:

### Error Sampling
```python
# In init_sentry()
sample_rate=1.0  # Capture 100% of errors (default)
```

For high-traffic deployments, reduce to 0.5 (50%) or 0.1 (10%).

### Performance Sampling
```bash
# Environment variable
export SENTRY_TRACES_SAMPLE_RATE="0.1"  # 10% of transactions
```

Reduce in production to minimize overhead.

### Ignored Errors

These errors are **automatically ignored**:
- `KeyboardInterrupt`
- `SystemExit`
- `CancelledError` (asyncio)
- `TimeoutError` (expected)

Add more in `should_ignore_error()` function.

## Release Tracking

### Automatic Release Creation

Releases are automatically created from:
1. **Environment variable**: `CONTINUUM_RELEASE`
2. **Git commit**: `git-{short_hash}`
3. **Package version**: `v{version}` from `__version__`

### Manual Release Creation

Using Sentry CLI:

```bash
# Install Sentry CLI
curl -sL https://sentry.io/get-cli/ | bash

# Login
sentry-cli login

# Create release
export VERSION=$(git rev-parse --short HEAD)
sentry-cli releases new -p continuum "git-$VERSION"

# Upload source files
sentry-cli releases files "git-$VERSION" upload-sourcemaps ./continuum

# Finalize release
sentry-cli releases finalize "git-$VERSION"

# Associate commits
sentry-cli releases set-commits "git-$VERSION" --auto
```

### CI/CD Integration

**GitHub Actions:**

```yaml
- name: Create Sentry release
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: jackknifeai
    SENTRY_PROJECT: continuum
  run: |
    VERSION=$(git rev-parse --short HEAD)
    sentry-cli releases new -p continuum "git-$VERSION"
    sentry-cli releases set-commits "git-$VERSION" --auto
    sentry-cli releases finalize "git-$VERSION"
```

## Error Grouping Rules

Configure in Sentry UI (**Settings → Processing → Issue Grouping**):

### Fingerprint Rules

Group errors by operation type:

```yaml
# Group all recall errors together
error.type:"RecallError" -> recall-errors

# Group by tenant (use hash to anonymize)
tags.tenant_id_hash:* -> tenant-{{ tags.tenant_id_hash }}

# Group federation errors by peer
tags.federation_peer:* -> federation-{{ tags.federation_peer }}
```

### Stack Trace Rules

```yaml
# Ignore internal framework frames
function:uvicorn.* -> ignore
function:fastapi.routing.* -> ignore

# Focus on CONTINUUM code
path:**/continuum/** -> group
```

## Dashboard Setup

### Recommended Dashboards

1. **Error Overview**
   - Total errors (by environment)
   - Error rate (errors/min)
   - Top 10 errors
   - Errors by operation type

2. **Performance**
   - Average transaction duration
   - P50/P95/P99 latency
   - Throughput (transactions/min)
   - Slowest operations

3. **Tenant Health**
   - Errors by tenant (anonymized)
   - Top error-prone tenants
   - Tenant-specific performance

### Query Examples

**Errors by operation:**
```
operation:recall OR operation:learn OR operation:sync
```

**High-severity errors:**
```
level:error AND environment:production
```

**Federation errors:**
```
tags.federation_peer:* AND NOT tags.federation_peer:""
```

## Alerts

Configure alerts in Sentry UI (**Alerts → Create Alert Rule**):

### Recommended Alerts

1. **High Error Rate**
   - Condition: Error count > 100 in 5 minutes
   - Action: Email + Slack
   - Environment: production

2. **New Error Type**
   - Condition: First seen error
   - Action: Email + Slack
   - Environment: production

3. **Performance Degradation**
   - Condition: P95 latency > 5s for 10 minutes
   - Action: Email
   - Environment: production

4. **Database Errors**
   - Condition: Error message contains "database"
   - Action: PagerDuty
   - Environment: production

## Debugging

### Check Sentry Status

```python
from continuum.core.sentry_integration import get_status

status = get_status()
print(status)
# {
#   "available": true,
#   "enabled": true,
#   "environment": "production",
#   "release": "git-abc123",
#   "sample_rate": 1.0,
#   "traces_sample_rate": 0.1
# }
```

### Test Error Capture

```bash
# Test CLI error capture
continuum verify  # Should succeed
continuum search "test" --federated  # May trigger errors if federation not configured

# Test API error capture
curl -X POST http://localhost:8420/v1/recall \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'  # Should trigger validation error
```

### View Errors in Sentry

1. Go to [sentry.io](https://sentry.io)
2. Select **Projects → continuum**
3. View **Issues** tab
4. Check for test errors

## Troubleshooting

### Sentry Not Initializing

**Problem**: "Sentry initialized: env=development" not shown in logs

**Solution**:
1. Check `SENTRY_DSN` is set: `echo $SENTRY_DSN`
2. Check sentry-sdk installed: `pip show sentry-sdk`
3. Check imports: `python -c "import sentry_sdk; print('OK')"`

### Errors Not Appearing in Sentry

**Problem**: Errors logged locally but not in Sentry

**Solution**:
1. Check sampling rate: `export SENTRY_SAMPLE_RATE=1.0`
2. Check error is not ignored (see `should_ignore_error()`)
3. Check network connectivity to Sentry
4. Call `flush()` before shutdown to ensure events are sent

### Too Many Events

**Problem**: Approaching Sentry quota limits

**Solution**:
1. Reduce error sampling: `sample_rate=0.5`
2. Reduce trace sampling: `traces_sample_rate=0.05`
3. Add more ignored errors
4. Filter noisy errors in Sentry UI

### Missing Source Context

**Problem**: Stack traces don't show source code

**Solution**:
1. Upload source files with Sentry CLI
2. Ensure release matches deployed version
3. Check `sentry.properties` configuration

## Performance Impact

Sentry integration adds minimal overhead:

- **Error Capture**: ~1-5ms per error
- **Performance Tracking**: ~0.1-0.5ms per transaction (when sampled)
- **Breadcrumbs**: ~0.01ms per breadcrumb

For production, recommended settings:
```bash
export SENTRY_TRACES_SAMPLE_RATE="0.1"  # 10% sampling
```

This provides good visibility with <0.5% performance impact.

## Security Notes

1. **Never commit** `SENTRY_DSN` to git
2. **Use environment variables** for all secrets
3. **Review scrubbing rules** before production deployment
4. **Anonymize tenant IDs** (enabled by default)
5. **Restrict Sentry project access** to authorized team members
6. **Rotate DSN** if accidentally exposed

## Integration Checklist

- [ ] Sentry project created
- [ ] DSN obtained and stored securely
- [ ] `sentry-sdk[fastapi]` installed
- [ ] Environment variables configured
- [ ] Tested error capture (dev environment)
- [ ] Verified sensitive data scrubbing
- [ ] Configured error grouping rules
- [ ] Set up dashboards
- [ ] Configured alerts
- [ ] Integrated with CI/CD (optional)
- [ ] Documented for team
- [ ] Tested in staging
- [ ] Deployed to production

## Support

- **Sentry Docs**: https://docs.sentry.io/platforms/python/
- **CONTINUUM Integration**: `continuum/core/sentry_integration.py`
- **Issues**: https://github.com/JackKnifeAI/continuum/issues

---

**Note**: This integration follows CONTINUUM's π×φ principles - designed for optimal error signal extraction while minimizing noise, operating at the "edge of chaos" between perfect monitoring and quota limits.
