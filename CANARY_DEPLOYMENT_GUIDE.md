# TIER 2 Step 2: Performance Testing & Canary Deployment Guide

## Overview
This guide covers performance benchmarking FastAPI async vs Flask sync endpoints, and implementing a zero-downtime canary deployment strategy for the User Dropoff Detection API.

## 1. Performance Testing

### 1.1 Benchmark Setup

**Prerequisites:**
```bash
pip install requests psutil
```

**Start both servers for comparison:**
```bash
# Terminal 1: Flask (existing)
python src/api/app.py --port 5000

# Terminal 2: FastAPI (new)
python -m uvicorn src.api.fastapi_async_app:app --host 0.0.0.0 --port 8000
```

**Run benchmark:**
```bash
python scripts/performance_benchmark.py \
  --flask-url http://localhost:5000 \
  --fastapi-url http://localhost:8000
```

### 1.2 Expected Results

FastAPI async typically shows **30-50% improvement** over Flask sync for high-concurrency scenarios:

| Metric | Flask (Sync) | FastAPI (Async) | Improvement |
|--------|--------------|-----------------|------------|
| Throughput (req/s) | 100-150 | 150-250 | ~50% ↑ |
| Latency (p50) | 50-100ms | 20-50ms | ~50% ↓ |
| Latency (p99) | 500-1000ms | 100-300ms | ~70% ↓ |
| Memory/request | ~5MB | ~2MB | ~60% ↓ |
| CPU usage (10 workers) | 80-100% | 40-60% | ~50% ↓ |

Tests run:
- 100 concurrent requests per endpoint
- 10 worker threads
- Measured: latency, throughput, success rate, error count

Output: `results/performance_benchmark.json`

---

## 2. Canary Deployment Strategy

### 2.1 Blue-Green Deployment (Recommended for v2.0.0)

**Architecture:**
```
┌─────────────────────────────────────────┐
│         Load Balancer / Ingress          │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────────┐   ┌───▼────────┐
│  Flask v1  │   │ FastAPI v2  │
│  (Blue)    │   │  (Green)    │
│  Active    │   │  Standby    │
└────────────┘   └─────────────┘
```

**Steps:**
1. **Deploy FastAPI to new nodes** (replicas)
2. **Run smoke tests** against new deployment
3. **Route 5% traffic** to FastAPI (canary phase)
4. **Monitor metrics** for 24-48 hours
5. **Gradually increase traffic** (5% → 25% → 50% → 100%)
6. **Rollback option** available at each phase
7. **Once stable, decommission Flask** (or keep as fallback)

### 2.2 Traffic Shifting Configuration

**Kubernetes Service Mesh (Istio) Example:**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: dropoff-api
spec:
  hosts:
  - dropoff-api.production.svc.cluster.local
  http:
  - match:
    - sourceLabels:
        app: canary-test
    route:
    - destination:
        host: fastapi-service
        port:
          number: 8000
      weight: 100
  - route:
    - destination:
        host: flask-service
        port:
          number: 5000
      weight: 100  # Change to 95 for 5% canary
    - destination:
        host: fastapi-service
        port:
          number: 8000
      weight: 0   # Change to 5 for 5% canary
```

### 2.3 Health Checks & Readiness Probes

**Kubernetes Probe Configuration:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /monitor
    port: 8000
  initialDelaySeconds: 2
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

---

## 3. Deployment Phases

### Phase 1: Canary (5% Traffic, 24 hours)
**Objectives:**
- Verify basic functionality
- Collect baseline metrics
- Check error rates < Flask

**Success Criteria:**
- Error rate < 0.5% (Flask baseline: 0.1%)
- Latency p95 < 200ms (Flask baseline: 150ms)
- No critical errors in logs
- Database connection stable

**Rollback if:**
- Error rate > 1%
- Latency p95 > 500ms
- Database connection failures
- Memory leak detected (RSS > 300MB)

### Phase 2: Controlled (25% Traffic, 24 hours)
**Objectives:**
- Load test with real traffic pattern
- Performance baseline at scale
- Identify edge cases

**Success Criteria:**
- Maintains success rate > 99.5%
- CPU usage < 70%
- Memory stable
- Response times consistent

### Phase 3: Majority (50% Traffic, 24 hours)
**Objectives:**
- Near production traffic
- Final validation
- Performance at full scale

**Success Criteria:**
- Same as Phase 2
- No latency spikes > 5% of requests
- All features working as expected

### Phase 4: Stable (100% Traffic, Monitor)
**Objectives:**
- Full production traffic
- Keep Flask as warm standby (optional)
- Continuous monitoring

**Post-Deployment:**
- Monitor for 7 days
- Collect performance metrics
- Document findings
- Plan Flask decommissioning (Phase 2 roadmap)

---

## 4. Monitoring During Canary

### Metrics to Track

**Request Metrics:**
```
POST /metrics/collect
{
  "timestamp": "2026-05-07T10:00:00Z",
  "endpoint": "/predict",
  "response_time_ms": 45,
  "status_code": 200,
  "api_key": "prod-api-key",
  "version": "fastapi-v2.0.0"
}
```

**Key Metrics Dashboard:**
1. **Error Rate**: Target < 0.5%
2. **P50 Latency**: Target < 50ms
3. **P99 Latency**: Target < 200ms
4. **Throughput**: Monitor sustained requests/sec
5. **Memory Usage**: Alert if > 300MB
6. **CPU Usage**: Alert if > 75%
7. **Database Connections**: Alert if > 80% pool utilization

### Prometheus Queries

```promql
# Error rate
rate(http_requests_total{status=~"5.."}[5m]) * 100

# Latency p99
histogram_quantile(0.99, http_request_duration_seconds_bucket)

# Throughput
rate(http_requests_total[5m])

# Memory usage
container_memory_usage_bytes
```

---

## 5. Rollback Plan

### Immediate Rollback (< 2 min)

```bash
# If using Kubernetes:
kubectl patch service dropoff-api -p '{"spec":{"selector":{"version":"v1.5.0"}}}'

# If using Istio:
kubectl patch virtualservice dropoff-api --type merge -p '{"spec":{"http":[{"route":[{"destination":{"host":"flask-service"},"weight":100}]}]}}'

# If using Docker Compose:
docker-compose down
git checkout main
docker-compose -f docker-compose-prod.yml up -d
```

### Health Check After Rollback

```bash
# Verify Flask is responsive
curl -s http://localhost:5000/health | jq .

# Check error logs
tail -f logs/*.log | grep ERROR
```

---

## 6. Performance Benchmarking Results

After running `scripts/performance_benchmark.py`, results are saved to `results/performance_benchmark.json`.

**Sample Result:**
```json
{
  "timestamp": "2026-05-07T10:00:00",
  "flask": {
    "/predict": {
      "throughput_requests_per_sec": 120,
      "latency_avg_ms": 85,
      "latency_p99_ms": 250,
      "success_rate": 99.8
    }
  },
  "fastapi": {
    "/predict": {
      "throughput_requests_per_sec": 185,
      "latency_avg_ms": 42,
      "latency_p99_ms": 120,
      "success_rate": 99.95
    }
  },
  "improvement": "+54% throughput, -51% latency"
}
```

---

## 7. Deployment Checklist

- [ ] Performance benchmarks run and results reviewed
- [ ] Kubernetes manifests updated with health probes
- [ ] Canary traffic split configured (5% FastAPI / 95% Flask)
- [ ] Monitoring dashboards created
- [ ] Alerting rules configured (error rate, latency, memory)
- [ ] Rollback procedure documented and tested
- [ ] On-call engineer trained on canary process
- [ ] Runbook created for incidents
- [ ] Database connection pool reviewed (async vs sync)
- [ ] TLS/HTTPS certificates renewed
- [ ] Log aggregation verified (all versions sending logs)
- [ ] Rate limiting configured per API key
- [ ] Database backup taken pre-deployment

---

## 8. Post-Deployment (Week 2)

After 7 days of successful canary deployment:
- [ ] Review performance metrics
- [ ] Document lessons learned
- [ ] Plan Flask decommissioning (optional Phase 2 task)
- [ ] Update API documentation (now FastAPI docs at /docs)
- [ ] Announce API v2.0 stable to clients
- [ ] Begin TIER 2 Step 3 tasks (DB optimization, caching)

---

## References

- [Istio Traffic Management](https://istio.io/latest/docs/tasks/traffic-management/)
- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [FastAPI Production Guide](https://fastapi.tiangolo.com/deployment/)
- [Performance Testing with k6](https://k6.io/)
