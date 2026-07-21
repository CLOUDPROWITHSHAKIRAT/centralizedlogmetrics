# AWS GitOps Observability Lab

A production-style GitOps lab demonstrating centralized observability across simulated multi-cluster Kubernetes environments on a single AWS EKS cluster. Built for conference demos and hands-on learning.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Platform Stack](#platform-stack)
- [Application Services](#application-services)
- [Multi-Environment Setup](#multi-environment-setup)
- [Simulated Multi-Cluster Observability](#simulated-multi-cluster-observability)
- [CI/CD Pipeline](#cicd-pipeline)
- [Accessing the Applications](#accessing-the-applications)
- [Payment Service API Reference](#payment-service-api-reference)
- [Metrics Reference](#metrics-reference)
- [Useful Queries](#useful-queries)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)

---

## Overview

This lab deploys a realistic microservices payment system with full observability (metrics, logs, traces) using a GitOps workflow. Everything is declared in Git and reconciled automatically by Argo CD.

Key capabilities demonstrated:

- GitOps delivery with Argo CD and Helm
- Centralized metrics with Prometheus and Grafana
- Centralized log aggregation with Loki and Grafana Alloy
- Simulated multi-cluster observability using namespace-based `cluster` labels
- Realistic incident scenarios: payment failures, fraud timeouts, slow dependencies, CPU spikes
- Interactive traffic generator UI for live dashboard demos
- GitHub Actions CI building and pushing images to Amazon ECR

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS EKS Cluster (core-eks-dev)              │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  dev ns      │  │  qa ns       │  │  prod ns             │  │
│  │              │  │              │  │                      │  │
│  │ payment-     │  │ payment-     │  │ payment-service      │  │
│  │ frontend     │  │ frontend     │  │ payment-frontend     │  │
│  │ payment-     │  │ payment-     │  │                      │  │
│  │ service      │  │ service      │  │                      │  │
│  │ fraud-       │  │              │  │                      │  │
│  │ service      │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  monitoring ns                                           │   │
│  │  Prometheus · Grafana · Loki · Alloy · Promtail          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  argocd ns   │  │  ingress-    │                            │
│  │  Argo CD     │  │  nginx ns    │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘

Traffic flow:
Browser → AWS ELB → ingress-nginx → payment-frontend
                                  → payment-service → fraud-service
```

### Service Call Chain

```
payment-frontend  →  /payment/pay   →  payment-service  →  fraud-service /check
                                                              ↓
                                                    approved / delayed / blocked
```

---

## Repository Structure

```
.
├── .github/
│   └── workflows/
│       ├── build-payment-service.yml     # CI: build & push payment-service to ECR
│       ├── build-payment-frontend.yml    # CI: build & push payment-frontend to ECR
│       └── build-fraud-service.yml       # CI: build & push fraud-service to ECR
│
└── aws-gitops-lab/
    ├── applications/                     # Helm charts per service per environment
    │   ├── payment-service/
    │   │   ├── dev/                      # Chart for dev namespace
    │   │   ├── qa/                       # Chart for qa namespace
    │   │   └── prod/                     # Chart for prod namespace
    │   ├── payment-frontend/
    │   │   ├── dev/
    │   │   ├── qa/
    │   │   └── prod/
    │   └── fraud-service/
    │       └── dev/
    │
    ├── platform/                         # Platform infrastructure Helm charts
    │   ├── alloy/                        # Grafana Alloy (log collection & forwarding)
    │   ├── argocd/
    │   │   └── metrics/                  # Argo CD Prometheus metrics services
    │   ├── grafana/                      # Grafana (dashboards, SMTP, persistence)
    │   ├── ingress-nginx/                # NGINX Ingress Controller
    │   ├── loki/                         # Grafana Loki (log storage)
    │   ├── prometheus/                   # Prometheus (metrics collection)
    │   └── promtail/                     # Promtail (legacy log agent)
    │
    └── services/                         # Application source code
        ├── payment-service/              # FastAPI payment backend
        │   ├── app/
        │   │   ├── main.py
        │   │   ├── logging_config.py     # Structured JSON logging
        │   │   ├── metrics.py            # Prometheus metrics definitions
        │   │   ├── routes/
        │   │   │   ├── payment.py        # /pay /pay/error /pay/slow
        │   │   │   ├── health.py         # /health
        │   │   │   ├── metrics.py        # /metrics (Prometheus endpoint)
        │   │   │   └── admin.py          # /cpu /memory (spike simulation)
        │   │   └── services/
        │   │       └── payment_processor.py  # Calls fraud-service
        │   ├── Dockerfile
        │   └── requirements.txt
        │
        ├── payment-frontend/             # Static HTML UI served by nginx
        │   ├── index.html                # Traffic generator + manual actions
        │   ├── nginx.conf                # Serves /payment-ui/, /payment-ui-qa/, /payment-ui-prod/
        │   └── Dockerfile
        │
        └── fraud-service/               # FastAPI fraud check microservice
            ├── app.py                   # /health /check (approves, delays, blocks)
            ├── Dockerfile
            └── requirements.txt
```

---

## Platform Stack

| Component | Purpose | Namespace |
|-----------|---------|-----------|
| Argo CD | GitOps controller — syncs Git to cluster | `argocd` |
| ingress-nginx | Ingress controller — routes external traffic | `ingress-nginx` |
| Prometheus | Metrics collection and storage | `monitoring` |
| Grafana | Dashboards and visualization | `monitoring` |
| Loki | Log aggregation and storage | `logging` |
| Grafana Alloy | Log collector — scrapes pods, enriches labels | `monitoring` |
| Promtail | Legacy log agent (supplementary) | `monitoring` |
| kube-state-metrics | Kubernetes object metrics | `monitoring` |
| prometheus-node-exporter | Node-level CPU/memory/disk metrics | `monitoring` |

---

## Application Services

### payment-service

A FastAPI application simulating a payment processing backend. Emits structured JSON logs and Prometheus metrics on every request.

**Endpoints:**

| Path | Description |
|------|-------------|
| `GET /` | Service status |
| `GET /pay` | Successful payment — calls fraud-service |
| `GET /pay/error` | Simulated payment failure (fraud timeout) |
| `GET /pay/slow` | Slow payment — adds 3s artificial delay |
| `GET /cpu` | CPU spike — runs hot loop for 10 seconds |
| `GET /memory` | Memory spike — allocates 100MB for 5 seconds |
| `GET /health` | Health check |
| `GET /metrics` | Prometheus metrics endpoint |

### fraud-service

An internal FastAPI service that simulates fraud detection. Called by payment-service on every transaction. Never exposed via Ingress (ClusterIP only).

**Behavior (random):**
- 60% → `approved`
- 20% → `delayed` (3s sleep)
- 20% → `blocked` (suspicious_transaction)

### payment-frontend

A static HTML/JavaScript UI served by nginx. Provides:
- Manual buttons for each incident scenario
- A configurable traffic generator (1–50 req/sec)
- Three traffic patterns: Normal, Incident, Errors only
- Live sent/failed counters

---

## Multi-Environment Setup

Each application is deployed to three namespaces on the same EKS cluster, each managed by a separate Argo CD application:

| Argo CD App | Namespace | Ingress Path |
|-------------|-----------|--------------|
| `payment-service-dev` | `dev` | `/payment` |
| `payment-service-qa` | `qa` | `/payment-qa` |
| `payment-service-prod` | `prod` | `/payment-prod` |
| `payment-frontend-dev` | `dev` | `/payment-ui` |
| `payment-frontend-qa` | `qa` | `/payment-ui-qa` |
| `payment-frontend-prod` | `prod` | `/payment-ui-prod` |
| `fraud-service-dev` | `dev` | None (internal only) |

Each environment has its own `values.yaml` with environment-specific configuration (image tag, replica count, ingress path, cluster label).

---

## Simulated Multi-Cluster Observability

Since this lab runs on a single EKS cluster, namespace labels are used to simulate three separate clusters in Grafana dashboards.

### Log labels (Alloy)

Grafana Alloy applies namespace-to-cluster relabeling before forwarding to Loki:

```
namespace=dev   → cluster=core-eks-dev
namespace=qa    → cluster=core-eks-qa
namespace=prod  → cluster=core-eks-prod
```

Query logs by cluster in Grafana:
```logql
{cluster="core-eks-prod", app="payment-service"} |= "ERROR"
{cluster="core-eks-qa", app="payment-service"}
```

### Metric labels (Prometheus)

Prometheus applies namespace-to-cluster relabeling in the `kubernetes-service-endpoints` scrape job:

```
namespace=dev   → cluster=core-eks-dev
namespace=qa    → cluster=core-eks-qa
namespace=prod  → cluster=core-eks-prod
```

Additionally, pod labels `cluster` and `environment` are set directly in each environment's `values.yaml` and propagated to all pods via the Deployment template.

Query metrics by cluster in Grafana:
```promql
sum(rate(payment_requests_total[5m])) by (cluster)
sum(rate(payment_failures_total[5m])) by (cluster, reason)
```

Use this as a Grafana dashboard variable:
```promql
label_values(payment_requests_total, cluster)
```

---

## CI/CD Pipeline

GitHub Actions workflows build and push Docker images to Amazon ECR on every push to `main` that touches the relevant service directory.

| Workflow | Trigger Path | ECR Repository |
|----------|-------------|----------------|
| `build-payment-service.yml` | `aws-gitops-lab/services/payment-service/**` | `payment-service` |
| `build-payment-frontend.yml` | `aws-gitops-lab/services/payment-frontend/**` | `payment-frontend` |
| `build-fraud-service.yml` | `aws-gitops-lab/services/fraud-service/**` | `fraud-service` |

All workflows authenticate to AWS via OIDC using an IAM role (`GitHubActionsECRRole`) — no long-lived credentials stored in GitHub secrets.

Image tag is pinned to `v1`. To deploy a new version, update the `tag` field in the relevant `values.yaml` and let Argo CD sync.

---

## Accessing the Applications

Get the ingress load balancer address:

```bash
kubectl get svc -n ingress-nginx
```

Use the `EXTERNAL-IP` value:

| Environment | URL |
|-------------|-----|
| Dev frontend | `http://<ELB>/payment-ui/` |
| QA frontend | `http://<ELB>/payment-ui-qa/` |
| Prod frontend | `http://<ELB>/payment-ui-prod/` |
| Dev payment API | `http://<ELB>/payment/` |
| QA payment API | `http://<ELB>/payment-qa/` |
| Prod payment API | `http://<ELB>/payment-prod/` |

---

## Payment Service API Reference

All paths below are relative to the ingress prefix (e.g. `/payment` for dev).

### `GET /pay`
Processes a successful payment. Calls fraud-service internally.

**Response:**
```json
{
  "payment": "success",
  "transaction": {
    "transaction_id": "TXN-A1B2C3D4",
    "customer_id": "CUS-54321",
    "amount": 24500,
    "currency": "NGN",
    "fraud_check": "approved",
    "fraud_reason": ""
  },
  "duration_ms": 187.43
}
```

### `GET /pay/error`
Simulates a fraud service timeout. Returns HTTP 500.

**Response:**
```json
{"payment": "failed", "error": "fraud_service_timeout"}
```

### `GET /pay/slow`
Simulates a slow dependency. Adds a 3-second delay before responding.

### `GET /cpu`
Triggers a 10-second CPU spike. Useful for testing CPU-based alerts.

### `GET /health`
Returns service health status.

---

## Metrics Reference

All metrics are exposed at `/metrics` on each payment-service pod.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `payment_requests_total` | Counter | `status` (success/error/slow) | Total payment requests |
| `payment_failures_total` | Counter | `reason` | Total failed payments |
| `payment_latency_seconds` | Histogram | — | Request latency distribution |
| `payment_inflight_requests` | Gauge | — | Requests currently in progress |

### Argo CD Metrics

Exposed via dedicated metrics services in the `argocd` namespace:

| Metric | Description |
|--------|-------------|
| `argocd_app_info` | Application metadata |
| `argocd_app_health_status` | Health status per app |
| `argocd_app_sync_status` | Sync status per app |
| `argocd_app_reconcile_count` | Reconcile activity |

---

## Useful Queries

### Prometheus (PromQL)

```promql
# Request rate by cluster
sum(rate(payment_requests_total[5m])) by (cluster)

# Error rate by cluster
sum(rate(payment_requests_total{status="error"}[5m])) by (cluster)

# p95 latency
histogram_quantile(0.95, sum(rate(payment_latency_seconds_bucket[5m])) by (le, cluster))

# Inflight requests
payment_inflight_requests

# Apps out of sync
argocd_app_sync_status{sync_status!="Synced"}

# Unhealthy apps
argocd_app_health_status{health_status!="Healthy"}

# Node count
count(up{job="prometheus-node-exporter"})

# All scrape jobs (for debugging)
count by (job) (up)
```

### Loki (LogQL)

```logql
# All payment-service logs from prod
{cluster="core-eks-prod", app="payment-service"}

# Errors only from QA
{cluster="core-eks-qa", app="payment-service"} |= "ERROR"

# Slow payment warnings
{app="payment-service"} |= "SLOW"

# Fraud service blocks
{app="payment-service"} |= "fraud_service_timeout"

# JSON structured logs
{app="payment-service"} | json | status="FAILED"
```

---

## Prerequisites

- AWS EKS cluster (tested on 1.30)
- `kubectl` configured to the cluster
- Argo CD installed in the `argocd` namespace
- Amazon ECR repositories created for `payment-service`, `payment-frontend`, `fraud-service`
- IAM role `GitHubActionsECRRole` with OIDC trust for this GitHub repository
- `gp2` or `gp3` StorageClass available for persistent volumes

---

## Getting Started

1. **Fork and clone this repository**

2. **Update AWS account ID** — replace `632638637624` with your account ID in:
   - All `values.yaml` files under `applications/`
   - All GitHub Actions workflow files under `.github/workflows/`

3. **Push to main** — GitHub Actions will build and push images to ECR

4. **Create Argo CD applications** pointing to each chart path:
   - `aws-gitops-lab/applications/payment-service/dev` → namespace `dev`
   - `aws-gitops-lab/applications/payment-service/qa` → namespace `qa`
   - `aws-gitops-lab/applications/payment-service/prod` → namespace `prod`
   - `aws-gitops-lab/applications/payment-frontend/dev` → namespace `dev`
   - `aws-gitops-lab/applications/payment-frontend/qa` → namespace `qa`
   - `aws-gitops-lab/applications/payment-frontend/prod` → namespace `prod`
   - `aws-gitops-lab/applications/fraud-service/dev` → namespace `dev`
   - `aws-gitops-lab/platform/prometheus` → namespace `monitoring`
   - `aws-gitops-lab/platform/grafana` → namespace `monitoring`
   - `aws-gitops-lab/platform/loki` → namespace `logging`
   - `aws-gitops-lab/platform/alloy` → namespace `monitoring`
   - `aws-gitops-lab/platform/ingress-nginx` → namespace `ingress-nginx`

5. **Enable auto-sync with self-heal and create namespace** on all apps

6. **Apply Argo CD metrics services:**
   ```bash
   kubectl apply -f aws-gitops-lab/platform/argocd/metrics/argocd-metrics-services.yaml
   ```

7. **Open the payment frontend** and start generating traffic to populate dashboards

---

## Grafana SMTP Alerts

Grafana is configured to send alert emails via Gmail SMTP. Credentials are loaded from a Kubernetes secret named `grafana-smtp` in the `monitoring` namespace:

```bash
kubectl create secret generic grafana-smtp \
  --from-literal=GF_SMTP_USER=your@gmail.com \
  --from-literal=GF_SMTP_PASSWORD=your-app-password \
  -n monitoring
```

Grafana persistence is enabled with a 10Gi `gp2` PVC so dashboards and configuration survive pod restarts and redeployments.
