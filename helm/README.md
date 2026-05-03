# Helm Chart for User Dropoff Detection API

A production-ready Helm chart for deploying the User Dropoff Detection API to Kubernetes.

## Quick Start

```bash
# Install chart
helm install user-dropoff ./helm/user-dropoff-detection

# Verify deployment
helm status user-dropoff
```

## Configuration

### values.yaml

```yaml
replicaCount: 3

image:
  repository: sumanasri813/user-dropoff-detection
  tag: latest
  pullPolicy: Always

service:
  type: LoadBalancer
  port: 80
  targetPort: 8000

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Usage

```bash
# Install
helm install user-dropoff ./helm/user-dropoff-detection

# Upgrade
helm upgrade user-dropoff ./helm/user-dropoff-detection

# Uninstall
helm uninstall user-dropoff

# Template (dry-run)
helm template user-dropoff ./helm/user-dropoff-detection

# Values
helm show values ./helm/user-dropoff-detection
```

## Chart Structure

```
helm/user-dropoff-detection/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── configmap.yaml
│   └── _helpers.tpl
└── README.md
```
