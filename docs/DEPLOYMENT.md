# Production Deployment Guide

## Architecture Overview

```
GitHub Repo → CI/CD Pipeline → Docker Registry → Kubernetes Cluster
                                                        ↓
                                                   LoadBalancer
                                                        ↓
                                    ┌───────────────────┼───────────────────┐
                                    ┓                   ↓                   ↓
                                  Pod 1              Pod 2              Pod 3
                                (API Server)      (API Server)      (API Server)
                                    ↓                   ↓                   ↓
                                    └───────────────────┼───────────────────┘
                                                        ↓
                                            Prometheus Monitoring
                                                        ↓
                                            Grafana Dashboards
```

## Prerequisites

1. **Kubernetes Cluster** (EKS, GKE, AKS, or local Kind)
   - Kubernetes 1.20+
   - kubectl configured

2. **Container Registry**
   - Docker Hub (already configured)
   - Images: `sumanasri813/user-dropoff-detection:latest`

3. **Monitoring Stack** (Optional but recommended)
   - Prometheus
   - Grafana

## Environment Template

Copy the root [.env.example](/workspaces/user-dropoff-detection/.env.example) file for local development, or use [mlops/configs/secrets_template/env.template](/workspaces/user-dropoff-detection/mlops/configs/secrets_template/env.template) for deployment-oriented secret injection.

Required production values to set explicitly:
- `SESSION_SECRET_KEY`
- `JWT_SECRET_KEY`
- `API_KEY`
- `FLASK_ENV=production` or `ENABLE_SECURITY_HARDENING=true`

## Step 1: Deploy to Kubernetes

```bash
# Clone repository
git clone https://github.com/sumanasri813-source/user-dropoff-detection.git
cd user-dropoff-detection

# Apply all manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get all -n user-dropoff
```

## Step 2: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n user-dropoff

# Port forward to test locally
kubectl port-forward -n user-dropoff svc/user-dropoff-api 8000:80

# Test health endpoint
curl http://localhost:8000/health

# Test prediction endpoint
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

## Step 3: Set Up Monitoring

### Install Prometheus Operator (if not already installed)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values - <<EOF
prometheus:
  prometheusSpec:
    serviceMonitorSelectorNilUsesHelmValues: false
grafana:
  adminPassword: "your-secure-password"
EOF
```

### Deploy ServiceMonitor

```bash
kubectl apply -f k8s/servicemonitor.yaml
```

### Access Grafana

```bash
kubectl port-forward -n monitoring svc/prometheus-community-grafana 3000:80

# Open http://localhost:3000
# Default: admin / your-secure-password
```

## Step 4: Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py \
  --host http://localhost:8000 \
  --users 100 \
  --spawn-rate 10

# Open http://localhost:8089 for Locust web UI
```

## Scaling Considerations

The deployment includes:
- **HorizontalPodAutoscaler**: Auto-scales between 3-10 replicas
- **Resource Requests/Limits**: 100m-500m CPU, 256Mi-512Mi RAM
- **Pod Anti-Affinity**: Spreads pods across nodes
- **Liveness/Readiness Probes**: Ensures healthy pods

Monitor scaling:
```bash
kubectl get hpa -n user-dropoff -w
```

## CI/CD Pipeline

Automatic deployment workflow:
1. Commit to `main` branch
2. GitHub Actions builds Docker image
3. Image published to Docker Hub
4. **Manual kubectl apply** to update K8s cluster

For fully automated deployment to K8s, update your GitHub Actions workflow to include:

```yaml
- name: Deploy to K8s
  env:
    KUBECONFIG: ${{ secrets.KUBECONFIG }}
  run: |
    kubectl apply -f k8s/
    kubectl rollout status deploy/user-dropoff-api -n user-dropoff
```

## Production Checklist

- [ ] Kubernetes cluster configured
- [ ] Images published to Docker Hub
- [ ] Manifests reviewed and customized
- [ ] `SESSION_SECRET_KEY` and `JWT_SECRET_KEY` set to different values
- [ ] `FLASK_ENV=production` or `ENABLE_SECURITY_HARDENING=true` set
- [ ] Admin login/session flow verified over HTTPS
- [ ] CSRF cookie and `X-CSRF-Token` header verified for admin deletes
- [ ] HSTS enabled on admin routes
- [ ] Monitoring stack deployed (optional)
- [ ] Load testing completed
- [ ] Health checks passing
- [ ] Auto-scaling tested
- [ ] Backup/disaster recovery plan

## Troubleshooting

```bash
# View pod logs
kubectl logs -n user-dropoff -l app=user-dropoff-api -f

# Describe failing pod
kubectl describe pod -n user-dropoff <pod-name>

# Check events
kubectl get events -n user-dropoff --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n user-dropoff
```

## Next Steps

1. **Helm Chart**: Package for easier deployment
2. **GitOps**: Use ArgoCD for declarative deployment
3. **Service Mesh**: Add Istio for advanced traffic management
4. **Logging**: Deploy ELK stack for centralized logging
5. **Security**: Implement network policies and RBAC

## App-Specific Security Notes

- The admin dashboard uses a secure Flask session cookie and CSRF token.
- Keep the admin UI behind HTTPS and avoid exposing it through public static hosting.
- Keep public docs in `docs/public/` and protected admin pages in `docs/private/`.
- Use the deployment checklist in the repository README before promoting to production.

## Support

For issues or questions:
- Check Kubernetes logs: `kubectl logs -n user-dropoff -l app=user-dropoff-api`
- Review ServiceMonitor: `kubectl get servicemonitor -n user-dropoff`
- Verify ConfigMap: `kubectl get cm -n user-dropoff -o yaml`
