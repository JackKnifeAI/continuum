# CONTINUUM Observability Runbook

Operational guide for troubleshooting and maintaining the observability stack.

## Quick Reference

### Service Health Checks

```bash
# OTEL Collector
curl http://localhost:13133

# Jaeger
curl http://localhost:14269

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health
```

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| No traces in Jaeger | Exporter not configured | Check `OTEL_EXPORTER_TYPE` and `OTEL_ENDPOINT` |
| High memory usage | Too many traces | Reduce `OTEL_SAMPLING_RATE` |
| Slow API responses | Tracing overhead | Check sampling rate, reduce span attributes |
| Missing trace context | Propagation issue | Verify `OTEL_PROPAGATORS` configuration |
| Collector not receiving | Network issue | Check firewall, docker network connectivity |

## Troubleshooting Workflows

### Issue: No Traces Appearing in Jaeger

**Steps:**

1. **Check application is exporting traces**
   ```bash
   # Look for OTLP export logs
   tail -f /var/log/continuum/api.log | grep -i otel
   ```

2. **Verify OTEL Collector is running**
   ```bash
   docker ps | grep otel-collector
   curl http://localhost:13133
   ```

3. **Check Collector is receiving traces**
   ```bash
   # View Collector logs
   docker logs continuum-otel-collector --tail 100 -f

   # Should see: "Traces received"
   ```

4. **Verify Jaeger is receiving from Collector**
   ```bash
   docker logs continuum-jaeger --tail 100 -f
   ```

5. **Check application configuration**
   ```bash
   echo $OTEL_EXPORTER_TYPE  # Should be "otlp" or "jaeger"
   echo $OTEL_ENDPOINT       # Should be collector endpoint
   ```

6. **Test with console exporter**
   ```bash
   # Temporarily switch to console exporter
   export OTEL_EXPORTER_TYPE=console

   # Restart application
   # Traces should print to stdout
   ```

### Issue: High Memory Usage

**Symptoms:**
- Application memory grows over time
- OOM kills
- Slow garbage collection

**Diagnosis:**

```python
# Check span processor queue size
from continuum.observability import get_tracer
provider = get_tracer("test")._tracer_provider

# Get processor stats (if available)
for processor in provider._active_span_processor._span_processors:
    print(f"Queue size: {processor._queue.qsize()}")
```

**Solutions:**

1. **Reduce sampling rate**
   ```bash
   export OTEL_SAMPLING_RATE=0.01  # 1% instead of 100%
   ```

2. **Increase batch export frequency**
   ```bash
   export OTEL_BSP_SCHEDULE_DELAY=1000  # Export every 1s instead of 5s
   ```

3. **Reduce queue size**
   ```bash
   export OTEL_BSP_MAX_QUEUE_SIZE=1024  # Default is 2048
   ```

4. **Limit span attributes**
   ```bash
   export OTEL_MAX_ATTRIBUTES_PER_SPAN=32  # Default is 128
   ```

5. **Enable memory limiter in Collector**
   ```yaml
   # otel-collector-config.yaml
   processors:
     memory_limiter:
       check_interval: 1s
       limit_mib: 512
   ```

### Issue: Traces Not Propagating Between Services

**Symptoms:**
- Traces appear as separate, unrelated spans
- No parent-child relationship between services
- Missing downstream service spans

**Diagnosis:**

```python
# In service A (caller)
from continuum.observability.context import get_traceparent
headers = inject_trace_context()
print(f"Traceparent: {headers.get('traceparent')}")

# In service B (callee)
from continuum.observability.context import extract_trace_context
ctx = extract_trace_context(request.headers)
print(f"Extracted context: {ctx}")
```

**Solutions:**

1. **Verify propagators match on both sides**
   ```bash
   # Both services should have same propagators
   export OTEL_PROPAGATORS=tracecontext,baggage
   ```

2. **Check headers are being sent**
   ```python
   # Service A
   headers = inject_trace_context()
   print(f"Sending headers: {headers}")  # Should contain 'traceparent'

   response = httpx.post(url, headers=headers)
   ```

3. **Check headers are being read**
   ```python
   # Service B
   @app.post("/endpoint")
   async def endpoint(request: Request):
       print(f"Received headers: {dict(request.headers)}")
       ctx = extract_trace_context(dict(request.headers))
       # ...
   ```

4. **Verify middleware order**
   ```python
   # Tracing middleware should be early in chain
   app.add_middleware(TracingMiddleware)  # First
   app.add_middleware(CORSMiddleware)     # After
   ```

### Issue: Slow API Responses After Adding Tracing

**Symptoms:**
- Increased latency after enabling tracing
- P95/P99 latencies significantly higher

**Diagnosis:**

```bash
# Compare with/without tracing
export OTEL_EXPORTER_TYPE=console  # Minimal overhead
# vs
export OTEL_EXPORTER_TYPE=otlp
```

**Solutions:**

1. **Use async exporters**
   - Already default with `BatchSpanProcessor`

2. **Reduce sampling for high-traffic endpoints**
   ```python
   # Custom sampling for specific routes
   from continuum.observability.sampling import get_ratio_sampler

   if request.path == "/high-traffic":
       # Sample only 1%
       init_telemetry(sampler=get_ratio_sampler(0.01))
   ```

3. **Limit span attribute size**
   ```python
   # Don't capture large payloads
   if len(request_body) > 1000:
       span.set_attribute("request.body", "<large payload>")
   else:
       span.set_attribute("request.body", request_body)
   ```

4. **Disable span events for high-frequency logs**
   ```python
   # Don't add every log as span event
   setup_logging(add_span_events=False)
   ```

### Issue: Collector Dropping Spans

**Symptoms:**
- Collector logs show dropped spans
- Gaps in trace timelines

**Diagnosis:**

```bash
# Check Collector metrics
curl http://localhost:8888/metrics | grep dropped

# Look for these metrics:
# otelcol_processor_dropped_spans
# otelcol_exporter_send_failed_spans
```

**Solutions:**

1. **Increase Collector memory**
   ```yaml
   # docker-compose.otel.yml
   services:
     otel-collector:
       deploy:
         resources:
           limits:
             memory: 2G  # Increase from 1G
   ```

2. **Increase queue size**
   ```yaml
   # otel-collector-config.yaml
   exporters:
     jaeger:
       sending_queue:
         queue_size: 10000
   ```

3. **Add more Collector instances**
   ```yaml
   # docker-compose.otel.yml
   services:
     otel-collector-1:
       # ...
     otel-collector-2:
       # ...
   ```

4. **Increase batch size**
   ```yaml
   processors:
     batch:
       send_batch_size: 2048
       send_batch_max_size: 4096
   ```

## Monitoring Queries

### Prometheus Queries

```promql
# Request rate by endpoint
rate(continuum_requests_total[5m])

# Error rate
rate(continuum_errors_total[5m]) / rate(continuum_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(continuum_request_duration_seconds_bucket[5m]))

# Memory operations per second
rate(continuum_memory_operations_total[5m])

# Cache hit ratio
continuum_cache_hits_total / (continuum_cache_hits_total + continuum_cache_misses_total)

# Active federation peers
continuum_federation_active_peers

# Database slow queries
rate(continuum_db_slow_queries_total[5m])
```

### Jaeger Queries

```
# Find traces with errors
http.status_code >= 400

# Find slow traces
duration > 1s

# Find traces for specific tenant
tenant.id="user_123"

# Find memory recall operations
operation="memory.recall"

# Find traces with cache misses
cache.hit=false
```

## Performance Baselines

### Expected Overhead

| Configuration | Overhead | Use Case |
|--------------|----------|----------|
| Console exporter, 100% sampling | ~1-2% | Development |
| OTLP exporter, 100% sampling | ~2-5% | Development/Staging |
| OTLP exporter, 10% sampling | ~0.5-1% | Production |
| OTLP exporter, 1% sampling | ~0.1-0.2% | High-traffic production |

### Typical Trace Volumes

| Requests/sec | Sampling Rate | Traces/sec | Daily Traces |
|-------------|---------------|------------|--------------|
| 10 | 100% | 10 | 864,000 |
| 100 | 10% | 10 | 864,000 |
| 1,000 | 1% | 10 | 864,000 |
| 10,000 | 0.1% | 10 | 864,000 |

**Goal**: Keep trace volume under 1M/day for cost-effective storage.

## Maintenance Tasks

### Daily

- Check Collector health: `curl http://localhost:13133`
- Review error traces in Jaeger
- Check for trace gaps or missing services

### Weekly

- Review P95/P99 latencies in Grafana
- Check Collector dropped spans metric
- Review slow query traces
- Check disk usage for trace storage

### Monthly

- Adjust sampling rates based on traffic
- Review and optimize span attributes
- Update dashboards and alerts
- Clean up old traces (if manual retention)

## Alerting Rules

### Prometheus Alerts

```yaml
groups:
  - name: continuum_observability
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(continuum_errors_total[5m]) > 10
        for: 5m
        annotations:
          summary: High error rate detected

      # Slow requests
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(continuum_request_duration_seconds_bucket[5m])) > 1
        for: 10m
        annotations:
          summary: P95 latency above 1s

      # Collector dropping spans
      - alert: CollectorDroppingSpans
        expr: rate(otelcol_processor_dropped_spans[5m]) > 100
        for: 5m
        annotations:
          summary: OTEL Collector dropping spans

      # Memory operations failing
      - alert: MemoryOperationErrors
        expr: rate(continuum_memory_operation_errors_total[5m]) > 5
        for: 5m
        annotations:
          summary: Memory operation errors detected

      # Low cache hit ratio
      - alert: LowCacheHitRatio
        expr: continuum_cache_hit_ratio < 0.5
        for: 15m
        annotations:
          summary: Cache hit ratio below 50%
```

## Emergency Procedures

### Disable Tracing in Emergency

If tracing is causing production issues:

```bash
# Option 1: Set to always-off sampler
export OTEL_SAMPLING_RATE=0.0

# Option 2: Disable exporters (traces buffered in memory only)
export OTEL_EXPORTER_TYPE=none

# Option 3: Skip telemetry initialization
export OTEL_DISABLED=true

# Restart application
systemctl restart continuum-api
```

### Collector Overload

If Collector is overloaded:

```bash
# Stop Collector temporarily
docker stop continuum-otel-collector

# Applications will buffer traces locally (up to queue size)
# Restart Collector when ready
docker start continuum-otel-collector
```

### Clear Trace Storage

If running out of disk space:

```bash
# Jaeger (delete old traces)
docker exec continuum-jaeger sh -c "rm -rf /badger/data"
docker restart continuum-jaeger

# Tempo (delete old blocks)
docker exec continuum-tempo sh -c "rm -rf /tmp/tempo/blocks/*"
docker restart continuum-tempo
```

## Support Contacts

- **Observability Team**: observability@continuum.ai
- **On-Call**: +1-555-OTEL-SOS
- **Slack**: #continuum-observability
- **Documentation**: https://docs.continuum.ai/observability

## Additional Resources

- [OpenTelemetry Troubleshooting](https://opentelemetry.io/docs/collector/troubleshooting/)
- [Jaeger Performance Tuning](https://www.jaegertracing.io/docs/latest/performance-tuning/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
