# Production Architecture & Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                        │
│  Code → Commits → Branches → Pull Requests → CI/CD Workflow     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓ (Automated on push)
┌──────────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                          │
│  ├─ Test (pytest on Python 3.11)                                │
│  ├─ Build (Docker image)                                         │
│  └─ Publish (Docker Hub + GHCR)                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓ (Manual or automated)
┌──────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            user-dropoff Namespace                        │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  ┌──────┐  ┌──────┐  ┌──────┐                           │    │
│  │  │ Pod1 │  │ Pod2 │  │ Pod3 │ (Auto-scaling 3-10)      │    │
│  │  │ API  │  │ API  │  │ API  │                           │    │
│  │  └──────┘  └──────┘  └──────┘                           │    │
│  │      ↓         ↓         ↓                               │    │
│  │      └─────────┼─────────┘                               │    │
│  │              ↓                                           │    │
│  │       LoadBalancer Service (port 80/443)                │    │
│  │              ↓                                           │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  ConfigMap  │  ServiceAccount  │  RBAC                 │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Prometheus ServiceMonitor (metrics collection)         │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │     Monitoring & Observability        │
        ├──────────────────────────────────────┤
        │  ├─ Prometheus (metrics)             │
        │  ├─ Grafana (dashboards)             │
        │  └─ Alerts (PagerDuty integration)   │
        └──────────────────────────────────────┘
```

## Technology Stack

### Development
- **Language**: Python 3.11/3.12
- **Framework**: Flask 2.3.0
- **ML Library**: scikit-learn 1.3.2
- **Data**: pandas 2.2.3, numpy 1.26.4

### Containerization
- **Runtime**: Docker (Python 3.11-slim)
- **WSGI Server**: Gunicorn (4 workers, 2 threads)
- **Security**: Non-root user, minimal base image

### Orchestration
- **Platform**: Kubernetes 1.20+
- **Package Manager**: Helm 3.0+
- **Auto-scaling**: Horizontal Pod Autoscaler (HPA)

### CI/CD
- **VCS**: GitHub
- **Pipeline**: GitHub Actions
- **Registries**: Docker Hub + GHCR

### Monitoring
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logging**: Container logs (stdout/stderr)
- **Tracing**: Optional (Jaeger/Zipkin)

## Deployment Patterns

### Development
```bash
# Local development with Flask debug server
python -m src.api.app

# With hot reload
export FLASK_ENV=development
python -m src.api.app
```

### Testing
```bash
# Unit tests
pytest tests/

# Load testing
locust -f tests/load/locustfile.py --host http://localhost:8000

# Integration tests
pytest tests/integration/ -v
```

### Production (Docker)
```bash
# Build
docker build -t user-dropoff-detection:latest .

# Run
docker run -d \
  -p 8000:8000 \
  -e APP_ENV=production \
  --name dropoff-api \
  user-dropoff-detection:latest
```

### Production (Kubernetes)
```bash
# Apply manifests
kubectl apply -f k8s/

# Or with Helm
helm install user-dropoff ./helm/user-dropoff-detection
```

## Scalability

### Horizontal Scaling
- **Min Replicas**: 3 (availability)
- **Max Replicas**: 10 (cost control)
- **Scale Trigger**: 70% CPU or 80% Memory
- **Scale Strategy**: RollingUpdate (zero downtime)

### Vertical Scaling
- **CPU Request**: 100m
- **CPU Limit**: 500m
- **Memory Request**: 256Mi
- **Memory Limit**: 512Mi

Can be adjusted in `k8s/deployment.yaml` or Helm `values.yaml`

## High Availability

- **Pod Anti-Affinity**: Spreads pods across nodes
- **Liveness Probe**: Restarts unhealthy pods
- **Readiness Probe**: Removes unready pods from load balancer
- **RollingUpdate**: Zero-downtime deployments
- **Health Checks**: Comprehensive `/health` endpoint

## Security

### Network
- Non-root user (UID 1000)
- Resource limits preventing DoS
- RBAC with minimal permissions
- Service accounts per deployment

### Image
- Python 3.11-slim (minimal attack surface)
- No sudo or shell access
- Read-only root filesystem (optional)
- Frequent dependency updates via CI/CD

### Secrets
- GitHub Actions secrets for credentials
- Environment-based configuration
- No hardcoded secrets in code/images

## Disaster Recovery

### Backup Strategy
- Container images: Stored in Docker Hub + GHCR
- Configuration: Version controlled in Git
- Model artifacts: Embedded in image
- Data: Kubernetes ConfigMaps

### Recovery Procedures
```bash
# Rollback to previous version
kubectl rollout history deploy/user-dropoff-api -n user-dropoff
kubectl rollout undo deploy/user-dropoff-api -n user-dropoff --to-revision=1

# Manual pod restart
kubectl delete pod <pod-name> -n user-dropoff

# Full namespace recovery
kubectl create namespace user-dropoff
kubectl apply -f k8s/
```

## Cost Optimization

### Current (Production)
- 3 pods × 0.1 CPU + 256Mi RAM = ~$20-30/month on EKS/GKE
- Auto-scaling: Up to 10 pods during peak = ~$60-80/month

### Optimization Opportunities
- Reserved instances for baseline (3 pods)
- Spot instances for burstable (7 pods)
- Regional deployments for cost arbitrage
- Scheduled scaling (night downtime)

## Monitoring SLOs

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Availability | 99.9% | < 99% |
| Latency (P95) | 500ms | > 1000ms |
| Error Rate | < 0.1% | > 1% |
| CPU Utilization | 50% avg | > 80% |
| Memory Utilization | 40% avg | > 80% |

## Future Roadmap

1. **Q2 2026**: GitOps integration (ArgoCD)
2. **Q3 2026**: Service mesh (Istio) for advanced traffic management
3. **Q4 2026**: Multi-region deployment
4. **Q1 2027**: ML model versioning and A/B testing

## Operating Procedures

### Deployment
```bash
git commit -m "feature: new model version"
git push origin main
# CI/CD automatically builds and publishes
kubectl apply -f k8s/ # or helm upgrade
```

### Monitoring
```bash
# Check metrics
kubectl get hpa -n user-dropoff -w

# View real-time logs
kubectl logs -n user-dropoff -l app=user-dropoff-api -f

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80
```

### Troubleshooting
```bash
# Pod stuck in pending
kubectl describe pod <pod-name> -n user-dropoff

# OOM killer (memory issues)
kubectl top pods -n user-dropoff

# Check events
kubectl get events -n user-dropoff --sort-by='.lastTimestamp'
```

## References

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Helm Documentation](https://helm.sh/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [CNCF Cloud Native Trail Map](https://cncf.io/blog/2021/12/13/cncf-cloud-native-trail-map-v2-0-launched/) 
