# Kubernetes Deployment

Production-grade Kubernetes manifests for the User Dropoff Detection API.

## Prerequisites

- Kubernetes cluster (1.20+)
- `kubectl` configured to access your cluster
- Docker images published to registry (automated via CI/CD)

## Deployment

### 1. Create namespace and resources

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### 2. Verify deployment

```bash
kubectl get pods -n user-dropoff
kubectl get svc -n user-dropoff
kubectl logs -n user-dropoff -l app=user-dropoff-api -f
```

### 3. Test the API

```bash
# Port forward to access locally
kubectl port-forward -n user-dropoff svc/user-dropoff-api 8000:80

# In another terminal
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "session_duration_minutes": 15,
    "pages_visited": 5,
    "items_added": 2,
    "items_removed": 0,
    "price_sensitivity_percentile": 65
  }'
```

## Configuration

All configuration is managed via `configmap.yaml`. Update environment variables there before deployment.

## Scaling

The HorizontalPodAutoscaler (HPA) automatically scales the deployment based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Min replicas: 3
- Max replicas: 10

Monitor scaling:
```bash
kubectl get hpa -n user-dropoff -w
```

## Health Checks

- **Liveness Probe**: Restarts pod if unhealthy (`/health` endpoint)
- **Readiness Probe**: Removes from load balancer if not ready

## Security

- Non-root user enforcement (UID 1000)
- Resource limits and requests
- RBAC service account with minimal permissions
- Pod anti-affinity for availability

## Monitoring

Prometheus metrics are exposed at `:8000/metrics`. See `/docs/MONITORING.md` for integration steps.

## Troubleshooting

```bash
# Check pod status
kubectl describe pod -n user-dropoff <pod-name>

# View logs
kubectl logs -n user-dropoff <pod-name>

# Check events
kubectl get events -n user-dropoff
```

## Cleanup

```bash
kubectl delete namespace user-dropoff
```
