# CONTINUUM Monitoring Stack

Comprehensive monitoring infrastructure for CONTINUUM using Prometheus, Grafana, and Alertmanager.

## Overview

The monitoring stack provides:

- **Real-time metrics** - API performance, memory operations, federation health
- **Visual dashboards** - 3 pre-configured Grafana dashboards
- **Alerting** - 20+ alert rules for critical conditions
- **Long-term storage** - 30-day retention (configurable)
- **System metrics** - CPU, memory, disk, network

## Architecture

```
┌─────────────┐
│  CONTINUUM  │──┐
│   API:8000  │  │
└─────────────┘  │
                 │ /metrics
┌─────────────┐  │
│ Federation  │──┤
│  Nodes      │  │
└─────────────┘  │
                 ▼
         ┌──────────────┐
         │  Prometheus  │──────┐
         │    :9090     │      │
         └──────────────┘      │
                 │              │
                 │ scrape       │ alerts
                 ▼              ▼
         ┌──────────────┐  ┌──────────────┐
         │   Grafana    │  │ Alertmanager │
         │    :3000     │  │    :9093     │
         └──────────────┘  └──────────────┘
```

## Quick Start

### 1. Start Monitoring Stack

```bash
cd deploy/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Configure CONTINUUM API

Add to your FastAPI app:

```python
from continuum.api.middleware import PrometheusMiddleware, metrics_endpoint

# Add middleware
app.add_middleware(PrometheusMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return metrics_endpoint()
```

### 3. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 4. Import Dashboards

Dashboards are in `grafana/dashboards/`:
- `continuum.json` - System overview
- `api.json` - API performance deep-dive
- `federation.json` - Federation health

Import via Grafana UI: Configuration → Dashboards → Import

## Dashboards

### Overview Dashboard (`continuum.json`)

Key metrics at a glance:

- **Health Score** - Composite score (API errors, federation health, resources)
- **Request Rate** - Requests/sec by endpoint and method
- **Error Rate** - 4xx/5xx errors with alerting
- **Latency** - p50/p95/p99 percentiles
- **Memory Ops** - Store/query/delete operations
- **Federation** - Sync latency, queue depth, peer status
- **Business** - Active users, memories stored, queries/day
- **System** - CPU, memory, disk usage

**Health Score Formula:**
```
Health = (
  (1 - error_rate) * 40% +
  (healthy_peers / total_peers) * 30% +
  (1 - memory_usage) * 15% +
  (1 - disk_usage) * 15%
) * 100
```

### API Performance Dashboard (`api.json`)

Deep-dive into API metrics:

- **Request Rate** - By endpoint and method
- **Latency Percentiles** - p50/p95/p99 by endpoint
- **Error Breakdown** - By status code and endpoint
- **Error Percentage** - With 1% threshold visualization
- **Request/Response Size** - p95 sizes
- **Tenant Activity** - Top 10 tenants by request volume
- **Active Connections** - Real-time connection count

**Alerts:**
- Error rate > 1% for 5 minutes
- p95 latency > 500ms for 5 minutes

### Federation Health Dashboard (`federation.json`)

Federation topology and health:

- **Peer Topology** - Visual graph of peer connections
- **Peer Health** - Healthy count and percentage
- **Sync Latency** - Per-peer sync lag
- **Message Queue** - Queue depth by peer
- **Sync Operations** - Operations/sec by type
- **Conflicts** - Conflict resolution rate
- **Bandwidth** - Bytes sent/received
- **Connection Errors** - Error types and rates
- **Data Consistency** - Overall consistency score

**Alerts:**
- Sync latency > 1 minute for 5 minutes
- Less than 50% peers healthy

## Metrics Reference

### API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `continuum_api_requests_total` | Counter | Total requests (by method, endpoint, status, tenant) |
| `continuum_api_errors_total` | Counter | Total errors 4xx/5xx |
| `continuum_api_request_duration_seconds` | Histogram | Request latency |
| `continuum_api_request_size_bytes` | Histogram | Request body size |
| `continuum_api_response_size_bytes` | Histogram | Response body size |
| `continuum_api_active_connections` | Gauge | Current active connections |

### Memory Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `continuum_memory_operations_total` | Counter | Total operations (store/query/delete) |
| `continuum_memory_operations_errors_total` | Counter | Operation errors |
| `continuum_memory_operation_duration_seconds` | Histogram | Operation latency |
| `continuum_memories_total` | Gauge | Total memories stored |
| `continuum_storage_bytes` | Gauge | Storage used per tenant |

### Cache Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `continuum_cache_hits_total` | Counter | Cache hits |
| `continuum_cache_misses_total` | Counter | Cache misses |
| `continuum_cache_size_bytes` | Gauge | Cache size |
| `continuum_cache_entries` | Gauge | Cache entry count |

### Federation Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `continuum_federation_peers_total` | Gauge | Total peers |
| `continuum_federation_peers_healthy` | Gauge | Healthy peer count |
| `continuum_federation_sync_latency_seconds` | Gauge | Sync lag per peer |
| `continuum_federation_queue_depth` | Gauge | Message queue depth |
| `continuum_federation_sync_operations_total` | Counter | Sync operations |
| `continuum_federation_conflicts_total` | Counter | Conflicts resolved |
| `continuum_federation_bytes_sent` | Counter | Bytes sent to peers |
| `continuum_federation_bytes_received` | Counter | Bytes received |

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `continuum_memory_usage_bytes` | Gauge | Process memory usage |
| `continuum_memory_limit_bytes` | Gauge | System memory limit |
| `continuum_disk_usage_bytes` | Gauge | Disk usage |
| `continuum_disk_limit_bytes` | Gauge | Disk capacity |

## Alert Rules

### Critical Alerts

- **APIDown** - API unreachable for 1 minute
- **HighErrorRate** - Error rate > 1% for 5 minutes
- **HighP99Latency** - P99 latency > 2s for 5 minutes
- **FederationSyncLag** - Sync latency > 1 minute
- **PeerUnhealthy** - Individual peer unhealthy for 2 minutes
- **LowPeerHealth** - <50% peers healthy for 5 minutes
- **HighMemoryUsage** - Memory > 90% for 5 minutes
- **CriticalDiskUsage** - Disk > 95% for 2 minutes

### Warning Alerts

- **HighP95Latency** - P95 latency > 500ms for 5 minutes
- **HighCPUUsage** - CPU > 80% for 5 minutes
- **HighDiskUsage** - Disk > 80% for 5 minutes
- **HighMessageQueueDepth** - >1000 messages queued
- **HighConflictRate** - >1 conflict/sec for 10 minutes
- **LowCacheHitRate** - <50% for 10 minutes

### Info Alerts

- **NoActiveUsers** - No activity for 30 minutes
- **LowQueryRate** - <0.1 queries/sec for 30 minutes
- **StorageGrowthAnomalous** - >10GB change in 1 hour

## Instrumentation Examples

### Track Memory Operation

```python
from continuum.core.metrics import track_operation

with track_operation('store', tenant_id='user123'):
    # Store memory
    memory_store.add(memory)
```

### Track Cache Hit/Miss

```python
from continuum.core.metrics import cache_hits_total, cache_misses_total

result = cache.get(key)
if result:
    cache_hits_total.labels(cache_type='embedding').inc()
else:
    cache_misses_total.labels(cache_type='embedding').inc()
```

### Update System Metrics

```python
from continuum.core.metrics import update_system_metrics

# Call periodically (e.g., every 30s)
update_system_metrics()
```

### Update Federation Metrics

```python
from continuum.core.metrics import (
    federation_sync_latency_seconds,
    federation_queue_depth
)

# After sync operation
federation_sync_latency_seconds.labels(peer_id='peer-1').set(latency)
federation_queue_depth.labels(peer_id='peer-1').set(queue_len)
```

## Configuration

### Prometheus Scrape Intervals

Edit `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'continuum'
    scrape_interval: 10s  # API metrics (frequent)
  - job_name: 'continuum-federation'
    scrape_interval: 15s  # Federation metrics
```

### Alert Thresholds

Edit `prometheus/alerts.yml`:

```yaml
- alert: HighErrorRate
  expr: |
    (sum(rate(continuum_api_errors_total[5m])) /
     sum(rate(continuum_api_requests_total[5m]))) * 100 > 1
  for: 5m  # Adjust alert duration
```

### Retention Period

Edit `docker-compose.monitoring.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # Change retention
```

## Troubleshooting

### Metrics Not Appearing

1. Check `/metrics` endpoint returns data:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify Prometheus is scraping:
   ```bash
   # Check targets in Prometheus UI
   http://localhost:9090/targets
   ```

3. Check middleware is added:
   ```python
   app.add_middleware(PrometheusMiddleware)
   ```

### Dashboard Shows No Data

1. Verify Prometheus data source in Grafana:
   - Configuration → Data Sources → Prometheus
   - URL: `http://prometheus:9090`

2. Check time range in dashboard (upper right)

3. Verify metrics exist in Prometheus:
   ```
   http://localhost:9090/graph
   # Search: continuum_api_requests_total
   ```

### Alerts Not Firing

1. Check alert rules loaded:
   ```bash
   curl http://localhost:9090/api/v1/rules
   ```

2. Verify Alertmanager connected:
   ```
   http://localhost:9090/alerts
   ```

3. Check alert rule evaluation:
   ```
   http://localhost:9090/graph
   # Paste alert expression
   ```

## Production Deployment

### High Availability

For production, run multiple Prometheus instances with remote storage:

```yaml
# Add to prometheus.yml
remote_write:
  - url: "http://victoriametrics:8428/api/v1/write"

# Uncomment in docker-compose.monitoring.yml
victoriametrics:
  image: victoriametrics/victoria-metrics:latest
  command:
    - '-retentionPeriod=12'  # 12 months
```

### Security

1. **Enable authentication** in Grafana:
   ```yaml
   environment:
     - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
     - GF_AUTH_ANONYMOUS_ENABLED=false
   ```

2. **Secure Prometheus** with TLS and basic auth

3. **Network isolation** - Use internal Docker network

### Scaling

- **Federation** - Scrape from multiple Prometheus instances
- **Sharding** - Shard metrics by tenant or service
- **Sampling** - Reduce scrape frequency for less critical metrics

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/dashboards/)

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.monitoring.yml logs`
- Prometheus targets: http://localhost:9090/targets
- Grafana explore: http://localhost:3000/explore
