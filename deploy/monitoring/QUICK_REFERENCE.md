# CONTINUUM Monitoring - Quick Reference

## Start Monitoring

```bash
cd deploy/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| API Metrics | http://localhost:8000/metrics | - |

## Dashboards

1. **CONTINUUM Overview** - System health score, API/federation/business metrics
2. **API Performance** - Request rates, latencies, errors by endpoint
3. **Federation Health** - Peer topology, sync latency, conflicts

## Key Alerts

| Alert | Threshold | Duration |
|-------|-----------|----------|
| APIDown | API unreachable | 1 min |
| HighErrorRate | > 1% | 5 min |
| HighP95Latency | > 500ms | 5 min |
| FederationSyncLag | > 1 minute | 5 min |
| HighMemoryUsage | > 90% | 5 min |
| CriticalDiskUsage | > 95% | 2 min |

## Metrics Categories

- **API:** 6 metrics (requests, errors, latency, size, connections)
- **Memory:** 5 metrics (operations, errors, count, storage)
- **Cache:** 4 metrics (hits, misses, size, entries)
- **Federation:** 12 metrics (peers, sync, conflicts, bandwidth)
- **System:** 4 metrics (CPU, memory, disk)

## Integration Checklist

- [ ] Add PrometheusMiddleware to FastAPI app
- [ ] Add /metrics endpoint
- [ ] Instrument memory operations with track_operation()
- [ ] Add periodic update_system_metrics() task
- [ ] Configure alertmanager receivers (Slack/email)
- [ ] Test alert firing with load testing

## Useful Commands

```bash
# View logs
docker-compose -f docker-compose.monitoring.yml logs -f

# Restart service
docker-compose -f docker-compose.monitoring.yml restart grafana

# Stop all
docker-compose -f docker-compose.monitoring.yml down

# Check metrics endpoint
curl http://localhost:8000/metrics

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload
```

## Troubleshooting

**No metrics in Grafana?**
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify /metrics endpoint works: `curl http://localhost:8000/metrics`
3. Check time range in Grafana dashboard

**Alerts not firing?**
1. Check alert rules: http://localhost:9090/alerts
2. Verify thresholds in prometheus/alerts.yml
3. Check Alertmanager: http://localhost:9093

**Dashboard shows no data?**
1. Verify Prometheus datasource in Grafana settings
2. Check metrics exist: http://localhost:9090/graph
3. Ensure correct time range selected

## Files Created

```
deploy/monitoring/
├── grafana/dashboards/         # 3 dashboard JSON files
├── prometheus/                 # Config + alerts + peer discovery
├── alertmanager/               # Alert routing
├── blackbox/                   # Health checks
└── docker-compose.monitoring.yml

continuum/
├── api/middleware/metrics.py   # PrometheusMiddleware
└── core/metrics.py             # 40+ application metrics
```

## Health Score Formula

```
Health = (
  (1 - API_error_rate) * 40% +
  (healthy_peers / total_peers) * 30% +
  (1 - memory_usage_percent) * 15% +
  (1 - disk_usage_percent) * 15%
) * 100
```

Target: > 90% (green), 70-90% (yellow), < 70% (red)
