# PostHog Analytics Integration for CONTINUUM

## Overview

CONTINUUM uses PostHog for privacy-first product analytics. This integration tracks usage patterns while maintaining GDPR compliance and user privacy.

## Quick Start

### 1. Install PostHog SDK

```bash
pip install posthog
```

### 2. Set Environment Variables

```bash
export POSTHOG_API_KEY="your_project_api_key"
export POSTHOG_HOST="https://app.posthog.com"  # or your self-hosted instance
export CONTINUUM_ANALYTICS_ENABLED="true"
```

### 3. Configure Analytics

Create `continuum_analytics.json` in your project:

```json
{
  "api_key": "your_api_key",
  "host": "https://app.posthog.com",
  "enabled": true,
  "anonymize_users": true,
  "opt_out": false
}
```

Or use environment variables (takes precedence):
- `POSTHOG_API_KEY` - Your PostHog API key
- `POSTHOG_HOST` - PostHog instance URL
- `CONTINUUM_ANALYTICS_ENABLED` - Enable/disable analytics
- `CONTINUUM_ANALYTICS_OPT_OUT` - User opt-out flag

## Privacy Guarantees

### What We Track

1. **User Events** (anonymized)
   - Signup, login, session start/end
   - User plan and account age
   - Feature usage patterns

2. **Memory Operations**
   - Create, read, update, delete operations
   - Search queries (length only, not content)
   - Memory types and counts

3. **Federation Activity**
   - Join, sync, disconnect events
   - Data exchanged (volume, not content)
   - Node connectivity

4. **API Performance**
   - Request method, endpoint, status code
   - Response times
   - Error rates

5. **CLI Usage**
   - Command execution
   - Success/failure rates
   - Execution times

### What We DON'T Track

- **NO PII**: Email, name, phone, address, IP
- **NO Content**: Memory content, search queries, messages
- **NO Passwords**: Authentication credentials
- **NO Financial**: Credit cards, payment info

### Privacy Features

1. **User Anonymization**: SHA-256 hashed user IDs
2. **No IP Tracking**: `capture_ip: false`
3. **Opt-Out**: `CONTINUUM_ANALYTICS_OPT_OUT=true`
4. **PII Filtering**: Automatic removal of sensitive fields
5. **GDPR Compliant**: Data deletion, export, consent

## Events Reference

### User Lifecycle

```python
from continuum.core.analytics import track_user_signup, track_user_login

# User signup
track_user_signup("user_123", plan="pro")

# User login
track_user_login("user_123")
```

### Memory Operations

```python
from continuum.core.analytics import (
    track_memory_create,
    track_memory_read,
    track_memory_search,
)

# Create memory
track_memory_create("user_123", memory_type="concept", size_bytes=1024)

# Search memories
track_memory_search("user_123", query="warp drive", results_count=10, duration_ms=45.2)
```

### Federation

```python
from continuum.core.analytics import (
    track_federation_join,
    track_federation_sync,
)

# Join federation
track_federation_join("user_123", node_id="node_456")

# Sync with federation
track_federation_sync("user_123", pushed=100, pulled=50, duration_ms=1234.5)
```

### API Tracking (Automatic)

```python
from fastapi import FastAPI
from continuum.api.middleware import AnalyticsMiddleware

app = FastAPI()
app.add_middleware(AnalyticsMiddleware)

# All API requests now automatically tracked
```

### CLI Tracking (Automatic)

CLI commands are automatically tracked when executed:

```bash
continuum search "warp drive"  # Tracked as "cli_command"
continuum sync                 # Tracked with duration and success
```

## User Properties

Track user characteristics for segmentation:

```python
from continuum.core.analytics import get_analytics

analytics = get_analytics()
analytics.identify("user_123", {
    "plan": "pro",
    "account_age": 30,
    "total_memories": 1500,
    "federation_participant": True,
})
```

### Standard Properties

- `plan`: "free", "pro", "enterprise"
- `account_age`: Days since signup
- `total_memories`: Number of stored memories
- `federation_participant`: Boolean
- `signup_date`: ISO 8601 timestamp

## Feature Flags

Control feature rollouts and A/B testing:

```python
from continuum.core.analytics import get_analytics

analytics = get_analytics()

# Check single flag
if analytics.get_feature_flag("user_123", "beta_features", default=False):
    # Enable beta features
    pass

# Get all flags
flags = analytics.get_feature_flags("user_123")
if flags.get("new_search_algorithm"):
    # Use new search
    pass
```

### Available Flags

1. **beta_features** - Early access to beta features
2. **new_search_algorithm** - Enhanced semantic search
3. **federation_v2** - Next-gen federation protocol
4. **enhanced_analytics** - Additional tracking events
5. **realtime_sync** - Realtime federation sync

## Dashboard Templates

### 1. Product Overview

**Metrics:**
- Daily/Weekly/Monthly Active Users
- Signup rate and growth
- User retention (7-day, 30-day)
- Feature adoption rates

**Insights:**
```sql
-- Daily Active Users
SELECT count(DISTINCT user_id)
FROM events
WHERE event = 'session_start'
AND timestamp > now() - interval '1 day'

-- Retention Rate (7-day)
SELECT count(DISTINCT user_id) / (
  SELECT count(DISTINCT user_id)
  FROM events
  WHERE event = 'user_signup'
  AND timestamp > now() - interval '8 days'
  AND timestamp < now() - interval '7 days'
) as retention_rate
FROM events
WHERE event = 'session_start'
AND timestamp > now() - interval '1 day'
```

### 2. Memory Analytics

**Metrics:**
- Memories created per day
- Average searches per user
- Search result quality
- Memory type distribution

**Insights:**
```sql
-- Average memories per user
SELECT avg(memory_count) FROM (
  SELECT user_id, count(*) as memory_count
  FROM events
  WHERE event = 'memory_create'
  GROUP BY user_id
)

-- Search performance
SELECT
  avg(properties.duration_ms) as avg_duration,
  percentile(properties.duration_ms, 0.95) as p95_duration
FROM events
WHERE event = 'memory_search'
```

### 3. Federation Analytics

**Metrics:**
- Active federation nodes
- Sync frequency and volume
- Contribution ratios
- Sync errors

**Insights:**
```sql
-- Federation participation rate
SELECT
  count(DISTINCT user_id) FILTER (WHERE properties.federation_participant = true) /
  count(DISTINCT user_id) as participation_rate
FROM events
WHERE event = 'user_login'

-- Average sync volume
SELECT
  avg(properties.pushed + properties.pulled) as avg_records_synced
FROM events
WHERE event = 'federation_sync'
```

### 4. API Performance

**Metrics:**
- Requests per second
- Average response time
- P95/P99 response times
- Error rates by endpoint

**Insights:**
```sql
-- API error rate
SELECT
  count(*) FILTER (WHERE properties.status_code >= 500) / count(*) as error_rate
FROM events
WHERE event = 'api_request'

-- Slowest endpoints
SELECT
  properties.endpoint,
  avg(properties.duration_ms) as avg_duration,
  percentile(properties.duration_ms, 0.95) as p95_duration
FROM events
WHERE event = 'api_request'
GROUP BY properties.endpoint
ORDER BY avg_duration DESC
LIMIT 10
```

### 5. User Journey

**Funnel Analysis:**
1. User signup → 100%
2. First memory created → ?%
3. First search → ?%
4. Federation join → ?%
5. Active user (7+ days) → ?%

**Insights:**
```sql
-- Time to first memory
SELECT avg(
  first_memory.timestamp - signup.timestamp
) as avg_time_to_first_memory
FROM events signup
JOIN events first_memory ON signup.user_id = first_memory.user_id
WHERE signup.event = 'user_signup'
AND first_memory.event = 'memory_create'
AND first_memory.timestamp = (
  SELECT min(timestamp)
  FROM events
  WHERE user_id = signup.user_id
  AND event = 'memory_create'
)
```

## Self-Hosted PostHog

For privacy and data sovereignty, use self-hosted PostHog:

### Docker Compose Setup

```yaml
version: '3.8'
services:
  posthog:
    image: posthog/posthog:latest
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=your_secret_key
      - SITE_URL=https://posthog.yourdomain.com
      - DISABLE_SECURE_SSL_REDIRECT=1
    volumes:
      - posthog-data:/var/lib/postgresql/data

volumes:
  posthog-data:
```

Then configure CONTINUUM:

```bash
export POSTHOG_HOST="https://posthog.yourdomain.com"
export POSTHOG_API_KEY="your_project_key"
```

## Opt-Out Mechanism

Users can opt out of analytics:

### Environment Variable

```bash
export CONTINUUM_ANALYTICS_OPT_OUT=true
```

### Configuration File

```json
{
  "opt_out": true
}
```

### Programmatic

```python
from continuum.core.analytics import AnalyticsConfig, set_analytics, Analytics

config = AnalyticsConfig(opt_out=True)
set_analytics(Analytics(config))
```

## GDPR Compliance

### Data Deletion

Request deletion of all analytics data:

```python
# In PostHog UI: Settings → Data Management → Delete Person
# Or via API:
import requests

requests.post(
    "https://app.posthog.com/api/person/{user_id}/delete_person/",
    headers={"Authorization": f"Bearer {api_key}"}
)
```

### Data Export

Export all user data:

```python
# In PostHog UI: Settings → Data Management → Export Data
# Or query events API:
import requests

response = requests.get(
    "https://app.posthog.com/api/event",
    params={"distinct_id": "user_id"},
    headers={"Authorization": f"Bearer {api_key}"}
)
```

### Consent Management

Track consent status:

```python
analytics.identify("user_123", {
    "analytics_consent": True,
    "consent_date": "2025-12-06T00:00:00Z"
})
```

## Testing

### Disable in Development

```bash
export CONTINUUM_ANALYTICS_ENABLED=false
```

### Mock Analytics

```python
from continuum.core.analytics import set_analytics, Analytics, AnalyticsConfig

# Create disabled analytics instance
config = AnalyticsConfig(enabled=False)
set_analytics(Analytics(config))

# All tracking calls will be no-ops
```

### Debug Mode

```python
import logging

logging.getLogger("continuum.core.analytics").setLevel(logging.DEBUG)
```

## Performance Considerations

1. **Batching**: Events are batched (default: 10) before sending
2. **Async**: Non-blocking event capture
3. **Flush Interval**: 10 seconds by default
4. **Feature Flag Cache**: 5-minute polling interval

### Custom Configuration

```python
config = AnalyticsConfig(
    batch_size=20,           # Batch more events
    flush_interval=5.0,      # Flush more frequently
    poll_interval=600,       # Poll flags every 10 minutes
)
```

## Troubleshooting

### Analytics Not Working

1. Check API key is set:
   ```bash
   echo $POSTHOG_API_KEY
   ```

2. Verify enabled:
   ```bash
   echo $CONTINUUM_ANALYTICS_ENABLED
   ```

3. Check logs:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. Test connection:
   ```python
   from continuum.core.analytics import get_analytics

   analytics = get_analytics()
   analytics.track("test_user", "test_event", {"test": True})
   analytics.flush()
   ```

### Feature Flags Not Loading

1. Verify feature flag polling is enabled
2. Check network connectivity to PostHog
3. Ensure user is identified before checking flags

## Support

For issues:
- GitHub Issues: https://github.com/JackKnifeAI/continuum/issues
- Documentation: https://continuum.jackknife.ai/docs/analytics
- PostHog Docs: https://posthog.com/docs

## License

Analytics integration follows CONTINUUM's Apache-2.0 license.
PostHog is MIT licensed.
