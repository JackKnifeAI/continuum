# CONTINUUM Monitoring Infrastructure - Summary

## Overview

Comprehensive production-grade monitoring infrastructure for CONTINUUM, providing real-time visibility into API performance, memory operations, federation health, and system resources.

## Components Created

### 1. Grafana Dashboards (3)

#### **continuum.json** - System Overview Dashboard
**16 Panels Total**

**Key Metrics:**
- Health Score gauge (composite: API errors 40%, federation 30%, memory 15%, disk 15%)
- API request rate (req/sec by method/endpoint)
- Error rate with 1% threshold alert
- API latency (p50/p95/p99 percentiles)
- Memory operations (store/query/delete ops/sec)
- Federation sync latency and queue depth by peer
- Cache hit rate percentage
- Business KPIs: active users (24h), total memories, queries/day, storage growth
- System resources: CPU%, memory bytes, disk usage vs limit
- Recent alerts feed

**Use Case:** Executive/ops team real-time system health monitoring

---

#### **api.json** - API Performance Deep-Dive Dashboard
**12 Panels Total**

**Key Metrics:**
- Request rate breakdowns (by endpoint, by method)
- Latency percentiles (p50/p95/p99) per endpoint
- Error rate per endpoint
- Error breakdown by HTTP status code
- Error percentage with 1% threshold visualization
- Request/response size distributions (p95)
- Top 10 tenants by request volume
- Active connection count

**Alerts:**
- Error rate > 1% for 5 minutes (critical)
- p95 latency > 500ms for 5 minutes (warning)

**Use Case:** API team performance optimization and debugging

---

#### **federation.json** - Federation Health Dashboard
**12 Panels Total**

**Key Metrics:**
- Peer topology graph (visual network map)
- Peer health status (healthy count + percentage gauge)
- Per-peer sync latency with 1-minute threshold
- Message queue depth per peer
- Sync operations/sec (by operation type)
- Conflict resolution rate and types
- Bandwidth usage (sent/received bytes/sec)
- Connection errors by type and peer
- Peer discovery events
- Data consistency score (100% - conflict rate)
- Peer uptime table

**Alerts:**
- Sync latency > 1 minute for 5 minutes
- < 50% peers healthy

**Use Case:** Federation team monitoring distributed sync health

---

### 2. Prometheus Configuration

#### **prometheus.yml** - Scrape Configuration
**7 Scrape Jobs:**
- `continuum` - API server (10s interval)
- `continuum-federation` - Federation nodes (15s interval)
- `prometheus` - Self-monitoring
- `node` - System metrics (CPU/memory/disk)
- `database` - DB metrics (if enabled)
- `blackbox` - Endpoint health checks
- `continuum-peers` - Dynamic peer discovery via file_sd

**Features:**
- 30-day retention
- Alertmanager integration
- Remote write/read support (commented, ready for VictoriaMetrics)
- External labels (cluster, environment)

---

#### **alerts.yml** - Alert Rules
**5 Alert Groups, 20+ Alerts Total**

**Critical Alerts (6):**
1. `APIDown` - API unreachable for 1 minute
2. `HighErrorRate` - Error rate > 1% for 5 minutes
3. `HighP99Latency` - P99 latency > 2s for 5 minutes
4. `FederationSyncLag` - Sync latency > 1 minute
5. `PeerUnhealthy` - Individual peer down for 2 minutes
6. `LowPeerHealth` - < 50% peers healthy for 5 minutes
7. `HighMemoryUsage` - Memory > 90% for 5 minutes
8. `CriticalDiskUsage` - Disk > 95% for 2 minutes

**Warning Alerts (6):**
1. `HighP95Latency` - P95 latency > 500ms for 5 minutes
2. `HighCPUUsage` - CPU > 80% for 5 minutes
3. `HighDiskUsage` - Disk > 80% for 5 minutes
4. `HighMessageQueueDepth` - > 1000 messages queued
5. `HighConflictRate` - > 1 conflict/sec for 10 minutes
6. `LowCacheHitRate` - < 50% for 10 minutes

**Info Alerts (3):**
1. `NoActiveUsers` - No activity for 30 minutes
2. `LowQueryRate` - < 0.1 queries/sec for 30 minutes
3. `StorageGrowthAnomalous` - > 10GB change in 1 hour

**Health Score Alerts:**
1. `LowHealthScore` - Overall health < 70% for 10 minutes
2. `CriticalHealthScore` - Overall health < 50% for 5 minutes

---

### 3. Docker Compose Stack

#### **docker-compose.monitoring.yml**
**5 Services:**
1. **Prometheus** (:9090) - Metrics storage and alerting
2. **Grafana** (:3000) - Visualization and dashboards
3. **Alertmanager** (:9093) - Alert routing and notification
4. **Node Exporter** (:9100) - System metrics
5. **Blackbox Exporter** (:9115) - Endpoint health checks

**Optional:**
6. VictoriaMetrics - Long-term storage (12-month retention, commented)

**Features:**
- Automatic restart on failure
- Persistent volumes for data
- Internal monitoring network
- Auto-provisioned datasources and dashboards

---

### 4. Application Metrics

#### **continuum/api/middleware/metrics.py** - API Metrics Middleware
**FastAPI Middleware for automatic instrumentation**

**Tracked Metrics:**
- `continuum_api_requests_total` - Counter (method, endpoint, status, tenant)
- `continuum_api_errors_total` - Counter (4xx/5xx errors)
- `continuum_api_request_duration_seconds` - Histogram (p50/p95/p99)
- `continuum_api_request_size_bytes` - Histogram
- `continuum_api_response_size_bytes` - Histogram
- `continuum_api_active_connections` - Gauge

**Features:**
- Path normalization (UUIDs/IDs → `{id}` to prevent cardinality explosion)
- Automatic error tracking
- Exception handling
- `/metrics` endpoint handler

**Usage:**
```python
from continuum.api.middleware import PrometheusMiddleware, metrics_endpoint

app.add_middleware(PrometheusMiddleware)

@app.get("/metrics")
async def metrics():
    return metrics_endpoint()
```

---

#### **continuum/core/metrics.py** - Application Metrics
**40+ Metric Definitions**

**Memory Metrics (5):**
- `continuum_memory_operations_total` - Counter
- `continuum_memory_operations_errors_total` - Counter
- `continuum_memory_operation_duration_seconds` - Histogram
- `continuum_memories_total` - Gauge (per tenant)
- `continuum_storage_bytes` - Gauge (per tenant)

**Cache Metrics (4):**
- `continuum_cache_hits_total` - Counter
- `continuum_cache_misses_total` - Counter
- `continuum_cache_size_bytes` - Gauge
- `continuum_cache_entries` - Gauge

**Federation Metrics (12):**
- `continuum_federation_peers_total` - Gauge
- `continuum_federation_peers_healthy` - Gauge
- `continuum_federation_peer_healthy` - Gauge (per peer)
- `continuum_federation_sync_latency_seconds` - Gauge (per peer)
- `continuum_federation_queue_depth` - Gauge (per peer)
- `continuum_federation_sync_operations_total` - Counter
- `continuum_federation_conflicts_total` - Counter
- `continuum_federation_bytes_sent/received` - Counter
- `continuum_federation_connection_errors_total` - Counter
- `continuum_federation_discovery_events_total` - Counter
- `continuum_federation_peer_uptime_seconds` - Gauge
- `continuum_federation_peer_connections` - Gauge (connection matrix)

**System Metrics (4):**
- `continuum_memory_usage_bytes` - Gauge
- `continuum_memory_limit_bytes` - Gauge
- `continuum_disk_usage_bytes` - Gauge
- `continuum_disk_limit_bytes` - Gauge

**Helper Functions:**
- `update_system_metrics()` - Auto-update CPU/memory/disk
- `update_storage_metrics(tenant, path)` - Update storage per tenant
- `update_memory_count(tenant, count)` - Update memory count

**Context Manager:**
```python
with track_operation('store', tenant_id='user123'):
    # Operation automatically timed and counted
    pass
```

**Decorator:**
```python
@track_cache('embedding')
def get_embedding(text):
    return embedding, cache_hit
```

---

### 5. Configuration Files

#### **alertmanager/config.yml**
- Routing tree (critical, API, federation, ops, info)
- Inhibit rules (suppress redundant alerts)
- 5 receiver configurations (webhook, Slack, email, PagerDuty ready)
- Smart grouping (by alertname, cluster, service)

#### **blackbox/config.yml**
- HTTP 2xx probe
- HTTP POST probe
- API health check (validates JSON response)
- TCP connect probe
- ICMP ping probe

#### **prometheus/peers/example.json**
- File-based service discovery template
- Dynamic peer registration

#### **grafana/provisioning/**
- Auto-provision Prometheus datasource
- Auto-load dashboards on startup

---

### 6. Documentation

#### **README.md** - Complete Setup Guide
**Sections:**
- Quick start (3 commands to deploy)
- Architecture diagram
- Dashboard descriptions
- Metrics reference (40+ metrics documented)
- Alert rules (20+ alerts with thresholds)
- Instrumentation examples
- Configuration guides
- Troubleshooting
- Production deployment (HA, security, scaling)

---

## Metrics Summary

### API Metrics
- **Request tracking:** Rate, latency (p50/p95/p99), size, active connections
- **Error tracking:** 4xx/5xx by endpoint/status/tenant
- **Coverage:** All HTTP methods, normalized paths, per-tenant isolation

### Memory Operations
- **Operations:** Store, query, delete (count, latency, errors)
- **Storage:** Total memories, bytes used (per tenant)
- **Cache:** Hit/miss rate, size, entry count

### Federation
- **Health:** Peer count, health status, uptime
- **Sync:** Latency, queue depth, operation rate
- **Conflicts:** Resolution rate, types
- **Network:** Bandwidth, connection errors, discovery events
- **Topology:** Connection matrix for network visualization

### System Resources
- **Process:** CPU%, memory (RSS)
- **Disk:** Usage, capacity, growth rate
- **Node:** Via node_exporter (disk I/O, network, etc.)

### Business KPIs
- **Users:** Active users (24h window)
- **Data:** Total memories stored, storage growth
- **Activity:** Queries/day, operation distribution

---

## Alert Coverage

### Availability (2 alerts)
- API down detection (1 minute)
- Peer health monitoring (< 50% healthy)

### Performance (4 alerts)
- Error rate threshold (1%)
- Latency thresholds (p95: 500ms, p99: 2s)
- Federation sync lag (1 minute)

### Resources (4 alerts)
- CPU utilization (80%)
- Memory usage (90%)
- Disk usage (80% warning, 95% critical)

### Federation (3 alerts)
- Individual peer health
- Sync latency
- Message queue depth (1000 messages)

### Data Quality (2 alerts)
- Conflict rate (1/sec)
- Cache hit rate (< 50%)

### Business (3 alerts)
- User activity (30 minutes no activity)
- Query rate (< 0.1/sec)
- Anomalous storage growth (> 10GB/hour)

---

## Integration Points

### Required Changes to CONTINUUM

**1. Add metrics middleware to API server:**
```python
# continuum/api/server.py
from continuum.api.middleware import PrometheusMiddleware, metrics_endpoint

app.add_middleware(PrometheusMiddleware)

@app.get("/metrics")
async def metrics():
    return metrics_endpoint()
```

**2. Add metrics to memory operations:**
```python
# continuum/core/memory.py
from continuum.core.metrics import track_operation, update_memory_count

class MemoryStore:
    def add(self, memory, tenant_id):
        with track_operation('store', tenant_id=tenant_id):
            # existing code
            pass
        update_memory_count(tenant_id, self.count())
```

**3. Add periodic system metrics update:**
```python
# Add background task
from continuum.core.metrics import update_system_metrics

@app.on_event("startup")
async def start_metrics_updater():
    asyncio.create_task(metrics_loop())

async def metrics_loop():
    while True:
        update_system_metrics()
        await asyncio.sleep(30)
```

---

## Dependencies

**Python packages to add to requirements.txt:**
```
prometheus-client>=0.19.0
psutil>=5.9.0
```

**Docker services:**
- Prometheus (included in stack)
- Grafana (included in stack)
- Alertmanager (included in stack)
- Node Exporter (included in stack)
- Blackbox Exporter (included in stack)

---

## Deployment Checklist

- [x] Dashboards created (3)
- [x] Alert rules defined (20+)
- [x] Prometheus configuration
- [x] Docker compose stack
- [x] Metrics middleware
- [x] Application metrics
- [x] Alertmanager routing
- [x] Documentation
- [ ] Add middleware to API server
- [ ] Instrument memory operations
- [ ] Add system metrics updater
- [ ] Configure alert receivers (Slack/email)
- [ ] Test monitoring stack
- [ ] Load test with alerts

---

## Quick Start Commands

```bash
# 1. Start monitoring stack
cd deploy/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# 2. Verify services
docker-compose -f docker-compose.monitoring.yml ps

# 3. Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Alertmanager: http://localhost:9093

# 4. Check metrics endpoint (after instrumenting API)
curl http://localhost:8000/metrics

# 5. View logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

---

## Next Steps

1. **Instrument API** - Add PrometheusMiddleware to FastAPI app
2. **Instrument Memory** - Add track_operation to memory operations
3. **System Metrics** - Add periodic update_system_metrics() task
4. **Test Alerts** - Generate load to trigger alert conditions
5. **Configure Notifications** - Set up Slack/email/PagerDuty in alertmanager
6. **Production Deploy** - Review security, HA, scaling considerations

---

## File Structure

```
deploy/monitoring/
├── README.md                              # Complete setup guide
├── MONITORING_SUMMARY.md                  # This file
├── docker-compose.monitoring.yml          # Monitoring stack
│
├── grafana/
│   ├── dashboards/
│   │   ├── continuum.json                # System overview
│   │   ├── api.json                      # API performance
│   │   └── federation.json               # Federation health
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml            # Auto-provision datasource
│       └── dashboards/
│           └── dashboards.yml            # Auto-load dashboards
│
├── prometheus/
│   ├── prometheus.yml                    # Scrape configuration
│   ├── alerts.yml                        # Alert rules (20+)
│   └── peers/
│       └── example.json                  # Dynamic peer discovery
│
├── alertmanager/
│   └── config.yml                        # Alert routing
│
└── blackbox/
    └── config.yml                        # Endpoint health checks

continuum/
├── api/middleware/
│   ├── __init__.py                       # Updated with metrics
│   └── metrics.py                        # PrometheusMiddleware
│
└── core/
    └── metrics.py                        # Application metrics (40+)
```

---

**Status:** Monitoring infrastructure complete and ready for integration.
**Total Metrics:** 40+ application metrics, standard process/node metrics
**Total Alerts:** 20+ alert rules across 5 categories
**Dashboards:** 3 production-ready Grafana dashboards (40 panels total)
