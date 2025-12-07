# Sentry Integration Summary

## Overview

Sentry error tracking and performance monitoring has been fully integrated into CONTINUUM.

**Status**: ✅ Complete

**Version**: 0.3.0

**Date**: 2025-12-06

---

## Files Created

### 1. Core Integration

**`continuum/core/sentry_integration.py`** (717 lines)
- Complete Sentry SDK wrapper
- Automatic error capture with scrubbing
- Performance transaction monitoring
- User context management
- Breadcrumb tracking
- Custom integrations (FastAPI, SQLAlchemy, Redis, asyncio)

**Key Features**:
- ✅ Automatic sensitive data scrubbing (messages, API keys, passwords)
- ✅ User anonymization (tenant IDs hashed by default)
- ✅ Custom tags (operation, model_type, memory_operation, federation_peer)
- ✅ Performance monitoring with decorators
- ✅ Environment-aware (dev, staging, prod)
- ✅ Release tracking (git commits or version tags)
- ✅ Rate limiting support
- ✅ Breadcrumb debugging trail
- ✅ Context managers for transactions
- ✅ Health check and status API

### 2. API Integration

**Updated: `continuum/api/server.py`**
- Sentry initialization in lifespan manager
- Automatic error capture for all API endpoints
- Clean shutdown with event flushing

**Changes**:
```python
# Added imports
from continuum.core.sentry_integration import init_sentry, close as close_sentry

# In lifespan startup
sentry_enabled = init_sentry(
    environment=os.environ.get("CONTINUUM_ENV", "development"),
    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
)

# In lifespan shutdown
if sentry_enabled:
    close_sentry()
```

### 3. CLI Integration

**Updated: `continuum/cli/main.py`**
- Sentry initialization for CLI errors
- Automatic error capture with command context
- Zero-overhead when DSN not configured

**Changes**:
```python
# Added imports
from continuum.core.sentry_integration import init_sentry, capture_exception, is_enabled

# Initialize on module load if SENTRY_DSN set
if os.environ.get("SENTRY_DSN"):
    init_sentry(
        sample_rate=1.0,           # Capture all CLI errors
        traces_sample_rate=0.0,    # No performance tracking
    )

# In main() exception handler
if is_enabled():
    capture_exception(e, tags={"cli_command": sys.argv[1]})
```

### 4. Configuration Files

**`deploy/sentry/sentry.properties`**
- Sentry CLI configuration
- Organization and project settings
- Release and deployment configuration
- Source file upload settings

**`deploy/sentry/.env.example`**
- Environment variable template
- All Sentry configuration options
- Comments explaining each setting

### 5. Documentation

**`deploy/sentry/README.md`** (550+ lines)
- Complete setup guide
- Environment-specific configuration
- Usage examples
- Sensitive data protection
- Rate limiting strategies
- Release tracking
- Error grouping rules
- Dashboard setup
- Alert configuration
- Debugging guide
- Troubleshooting
- Security notes

**`deploy/sentry/INTEGRATION_GUIDE.md`** (450+ lines)
- Quick reference for developers
- Code examples for every use case
- API endpoint pattern
- Database operation pattern
- Background job pattern
- Best practices
- Testing guide
- Common troubleshooting

### 6. Deployment Tools

**`deploy/sentry/create_release.sh`** (executable)
- Automated Sentry release creation
- Source file upload
- Git commit association
- Deployment notifications
- Colorized output

**`deploy/sentry/docker-compose.example.yml`**
- Docker Compose setup with Sentry
- Environment variable configuration
- Health checks
- Logging configuration

**`deploy/sentry/github-actions.example.yml`**
- Complete CI/CD workflow
- Automated release creation
- Deployment to staging/production
- Sentry deployment notifications
- Smoke tests

### 7. Error Grouping

**`deploy/sentry/grouping_rules.yaml`**
- Custom fingerprint rules
- Stack trace grouping rules
- Title customization
- Merge rules for similar errors
- Custom attributes extraction

### 8. Dependencies

**Updated: `requirements.txt`**
```txt
sentry-sdk[fastapi]>=1.40.0
```

**Updated: `pyproject.toml`**
```toml
[project.optional-dependencies]
monitoring = [
    "sentry-sdk[fastapi]>=1.40.0",
]
```

Install with:
```bash
pip install continuum-memory[monitoring]
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install 'sentry-sdk[fastapi]>=1.40.0'
```

### 2. Set Environment Variables

```bash
export SENTRY_DSN="https://your-key@o123456.ingest.sentry.io/123456"
export CONTINUUM_ENV="production"
export SENTRY_TRACES_SAMPLE_RATE="0.1"
```

### 3. Run Application

Sentry is automatically initialized on startup:

```bash
# API Server
uvicorn continuum.api.server:app --host 0.0.0.0 --port 8420

# CLI
continuum search "test query"
```

### 4. Verify Integration

```python
from continuum.core.sentry_integration import get_status

status = get_status()
print(status)
# {
#   "available": true,
#   "enabled": true,
#   "environment": "production",
#   "release": "git-abc123",
#   ...
# }
```

### 5. Test Error Capture

```bash
# Trigger a test error
curl -X POST http://localhost:8420/v1/recall \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```

Check Sentry dashboard for captured error.

---

## Features

### Automatic Error Tracking

- ✅ **API Errors**: All FastAPI exceptions captured
- ✅ **Database Errors**: SQLAlchemy errors with query context
- ✅ **Cache Errors**: Redis connection and operation errors
- ✅ **Async Errors**: asyncio exceptions and cancellations
- ✅ **CLI Errors**: Command-line errors with command context

### Performance Monitoring

- ✅ **Transaction Tracking**: Monitor operation latency
- ✅ **Span Tracking**: Break down operations into steps
- ✅ **Sampling Control**: Configurable sampling rate (default 10%)
- ✅ **Context Managers**: Easy performance tracking
- ✅ **Decorators**: Monitor functions with `@monitor_performance`

### Sensitive Data Protection

**Automatically Scrubbed**:
- Memory content (user messages, AI responses)
- API keys and tokens
- Passwords
- Request bodies containing messages

**Preserved**:
- Stack traces
- Error types and messages
- Operation metadata
- Performance metrics

### Custom Tags

Available for filtering in Sentry:

- `operation`: Memory operation type (recall, learn, sync, etc.)
- `model_type`: AI model being used
- `memory_operation`: Specific memory operation
- `federation_peer`: Federation peer identifier
- `environment`: Environment (dev, staging, prod)
- `release`: Release version

### User Context

- Tenant ID (anonymized by default)
- Instance ID (for multi-instance tracking)
- Server name

### Breadcrumbs

Debugging trail showing:
- Operation start/end
- Database queries
- Cache operations
- API calls
- Validation steps

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SENTRY_DSN` | Sentry DSN | None | Yes (to enable) |
| `CONTINUUM_ENV` | Environment name | `development` | No |
| `CONTINUUM_RELEASE` | Release version | Auto-detected | No |
| `CONTINUUM_SERVER_NAME` | Server identifier | Hostname | No |
| `SENTRY_TRACES_SAMPLE_RATE` | Performance sampling | `0.1` | No |

### Sampling Rates

**Error Sampling** (default: 100%)
- Development: `1.0` (100%)
- Staging: `1.0` (100%)
- Production: `1.0` (100%) - errors are rare

**Performance Sampling** (default: 10%)
- Development: `0.0` (disabled)
- Staging: `0.5` (50%)
- Production: `0.1` (10%) - reduce overhead

---

## Integration Points

### 1. API Routes

```python
from continuum.core.sentry_integration import (
    capture_exception,
    set_user_context,
    set_operation_context,
)

@router.post("/v1/recall")
async def recall(request: RecallRequest):
    set_user_context(tenant_id=request.tenant_id)
    set_operation_context(operation="recall")

    try:
        return await perform_recall(request)
    except Exception as e:
        capture_exception(e)
        raise
```

### 2. Memory Operations

```python
from continuum.core.sentry_integration import capture_memory_error

try:
    result = await recall(query)
except Exception as e:
    capture_memory_error(
        e,
        operation="recall",
        tenant_id=tenant_id,
        query=query[:100],
    )
    raise
```

### 3. Performance Monitoring

```python
from continuum.core.sentry_integration import PerformanceTransaction

with PerformanceTransaction("memory.recall", tenant_id):
    # Your operation here
    pass
```

### 4. Breadcrumbs

```python
from continuum.core.sentry_integration import add_breadcrumb

add_breadcrumb(
    message="Starting database query",
    category="database",
    level="info",
    data={"table": "concepts"},
)
```

---

## Deployment

### Development

```bash
# Disable Sentry (no DSN set)
uvicorn continuum.api.server:app --reload
```

### Staging

```bash
export SENTRY_DSN="your-dsn"
export CONTINUUM_ENV="staging"
export SENTRY_TRACES_SAMPLE_RATE="0.5"

uvicorn continuum.api.server:app --host 0.0.0.0
```

### Production

```bash
export SENTRY_DSN="your-dsn"
export CONTINUUM_ENV="production"
export CONTINUUM_RELEASE="v0.3.0"
export SENTRY_TRACES_SAMPLE_RATE="0.1"

# Create Sentry release
./deploy/sentry/create_release.sh v0.3.0

# Deploy
uvicorn continuum.api.server:app --host 0.0.0.0
```

---

## Testing

### Unit Tests

```python
# Disable Sentry in tests
import os
os.environ.pop("SENTRY_DSN", None)
```

### Integration Tests

```python
# Mock Sentry
from unittest.mock import patch

@patch('continuum.core.sentry_integration.capture_exception')
def test_error_capture(mock_capture):
    # Your test
    pass
```

---

## Monitoring

### Sentry Dashboard

View at: `https://sentry.io/organizations/jackknifeai/projects/continuum/`

**Key Views**:
- Issues: All errors grouped
- Performance: Transaction latency
- Releases: Errors by release version
- Alerts: Configured alert rules

### Key Metrics

- **Error Rate**: Errors per minute
- **P95 Latency**: 95th percentile response time
- **Crash-Free Sessions**: % of sessions without errors
- **Affected Users**: Unique tenants with errors

---

## Next Steps

### For Developers

1. Read `deploy/sentry/INTEGRATION_GUIDE.md`
2. Add error capture to your code
3. Add performance monitoring to key operations
4. Test with development Sentry project

### For DevOps

1. Set up Sentry project
2. Configure environment variables
3. Set up alerts
4. Integrate with CI/CD
5. Create dashboards

### For Production

1. ✅ Install dependencies
2. ✅ Configure environment variables
3. ✅ Create Sentry release
4. ✅ Deploy application
5. ✅ Monitor errors
6. ✅ Set up alerts
7. ✅ Review weekly

---

## Support

**Documentation**:
- Setup: `deploy/sentry/README.md`
- Integration: `deploy/sentry/INTEGRATION_GUIDE.md`
- Code: `continuum/core/sentry_integration.py`

**External**:
- Sentry Docs: https://docs.sentry.io/platforms/python/
- FastAPI Integration: https://docs.sentry.io/platforms/python/integrations/fastapi/
- Sentry CLI: https://docs.sentry.io/cli/

**Issues**:
- CONTINUUM: https://github.com/JackKnifeAI/continuum/issues
- Sentry: https://github.com/getsentry/sentry-python/issues

---

## Changelog

### v0.3.0 (2025-12-06)

**Added**:
- Complete Sentry integration
- Automatic error capture
- Performance monitoring
- Sensitive data scrubbing
- User context management
- Custom tags and breadcrumbs
- API and CLI integration
- Deployment tools
- Comprehensive documentation

**Changed**:
- Added `sentry-sdk[fastapi]` dependency
- Updated API server startup
- Updated CLI error handling

**Security**:
- Automatic scrubbing of sensitive data
- User anonymization by default
- No PII sent to Sentry

---

## License

Apache-2.0

---

**Generated**: 2025-12-06

**Version**: 0.3.0

**Integration**: Complete ✅
