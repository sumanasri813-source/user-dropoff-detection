# Monitoring and Observability

## Metrics Exposed

The API exposes Prometheus metrics at `/metrics` endpoint:

### Request Metrics
- `api_requests_total`: Total requests by method and endpoint
- `api_request_duration_seconds`: Request duration histogram
- `api_responses_by_status`: Responses grouped by HTTP status

### Model Metrics
- `model_predictions_total`: Total predictions made
- `model_prediction_latency_seconds`: Prediction latency
- `model_dropoff_probability_distribution`: Distribution of predicted probabilities

### System Metrics
- `process_cpu_seconds_total`: CPU usage
- `process_resident_memory_bytes`: Memory usage
- `python_gc_collections_total`: Garbage collection

## Prometheus Configuration

Add this to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'user-dropoff-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - user-dropoff
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: user-dropoff-api
      - source_labels: [__meta_kubernetes_pod_container_port_name]
        action: keep
        regex: http
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
```

## Grafana Dashboards

Import these dashboard IDs:
- **Node Exporter**: 1860 (Node metrics)
- **Kubernetes**: 7249 (K8s metrics)
- **Custom API**: See `monitoring/grafana-dashboard.json`

## Key Alerts

```yaml
groups:
- name: user-dropoff-api
  rules:
  - alert: APIHighErrorRate
    expr: rate(api_responses_by_status{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High API error rate detected"
      
  - alert: APIPredictionLatency
    expr: histogram_quantile(0.95, api_request_duration_seconds) > 2
    for: 10m
    annotations:
      summary: "P95 prediction latency > 2s"
      
  - alert: ModelDriftDetected
    expr: abs(model_drift_distance) > 0.3
    for: 30m
    annotations:
      summary: "Data drift detected in model predictions"
```

## Health Checks

### Liveness (Pod alive?)
```
GET /health → 200 OK
```

### Readiness (Ready to serve traffic?)
```
GET /health → 200 OK with model_loaded: true
```

## Dashboards to Create

1. **Request Rate & Latency**
   - Requests/sec
   - P50, P95, P99 latencies
   - Error rate

2. **Model Performance**
   - Predictions/sec
   - Prediction distribution
   - Model load time

3. **Resource Utilization**
   - CPU and Memory usage
   - Pod count
   - Network I/O

4. **Data Quality**
   - Input feature distributions
   - Prediction confidence
   - Drift indicators

## SLOs (Service Level Objectives)

- **Availability**: 99.9% uptime
- **Latency**: P99 < 1000ms
- **Error Rate**: < 0.1% (1 in 1000 requests)
- **Model Freshness**: Model updated daily

## Logging

Logs are collected from pods:
```bash
kubectl logs -n user-dropoff -l app=user-dropoff-api -f
```

For centralized logging, deploy ELK stack:
```bash
docker-compose -f monitoring/elk-compose.yml up -d
```

## Custom Metrics Example

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
prediction_counter = Counter(
    'model_predictions_total',
    'Total predictions made',
    ['status']
)

prediction_latency = Histogram(
    'model_prediction_latency_seconds',
    'Prediction latency in seconds'
)

# Use in code
@app.route('/predict', methods=['POST'])
def predict():
    start = time.time()
    try:
        result = model.predict(data)
        prediction_counter.labels(status='success').inc()
        prediction_latency.observe(time.time() - start)
        return result
    except Exception as e:
        prediction_counter.labels(status='error').inc()
        raise
```

## Useful Prometheus Queries

```promql
# Request rate (requests/sec)
rate(api_requests_total[5m])

# Error rate percentage
(rate(api_responses_by_status{status=~"5.."}[5m]) / rate(api_responses_by_status[5m])) * 100

# P95 latency
histogram_quantile(0.95, api_request_duration_seconds)

# Pod memory usage
container_memory_usage_bytes{pod="user-dropoff-api"}

# CPU utilization
rate(container_cpu_usage_seconds_total{pod="user-dropoff-api"}[5m])
```

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kubernetes Monitoring](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-metrics-pipeline/)
