# 🚀 Production Deployment Guide

## 📋 Overview

Complete guide for deploying Location Podcast Generator to production.

---

## 🎯 Prerequisites

### **Required Tools**
- Docker 24.0+
- Kubernetes 1.28+
- kubectl CLI
- Helm 3.0+
- Git

### **Cloud Resources**
- Kubernetes cluster (AWS EKS, GKE, or AKS)
- PostgreSQL database (managed service recommended)
- Redis cache (managed service recommended)
- Container registry (Docker Hub, GHCR, or ECR)
- Domain name with DNS access
- SSL certificate (Let's Encrypt recommended)

### **API Keys**
- OpenAI API key (for content generation)
- ElevenLabs API key (for audio generation)
- Other API keys as needed

---

## 📦 Deployment Options

### **Option 1: Local Production Testing**

Test production setup locally with Docker Compose:

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your values

# 2. Start services
docker-compose -f docker-compose.prod.yml up -d

# 3. Check status
docker-compose -f docker-compose.prod.yml ps

# 4. View logs
docker-compose -f docker-compose.prod.yml logs -f

# 5. Access services
# Frontend: http://localhost
# Backend: http://localhost:8000
# Grafana: http://localhost:3001
# Prometheus: http://localhost:9090
```

### **Option 2: Kubernetes Production**

Deploy to Kubernetes cluster:

```bash
# 1. Create namespace
kubectl create namespace location-podcast

# 2. Create secrets
kubectl apply -f k8s/secrets-template.yaml
# IMPORTANT: Update secrets with real values first!

# 3. Deploy application
kubectl apply -f k8s/deployment.yaml

# 4. Deploy ingress
kubectl apply -f k8s/ingress.yaml

# 5. Check deployment
kubectl get pods -n location-podcast
kubectl get services -n location-podcast
kubectl get ingress -n location-podcast

# 6. View logs
kubectl logs -f deployment/backend -n location-podcast
kubectl logs -f deployment/frontend -n location-podcast
```

---

## 🔐 Security Setup

### **1. Generate Secrets**

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### **2. Create Kubernetes Secrets**

```bash
# Database credentials
kubectl create secret generic database-credentials \
  --from-literal=url='postgresql://user:pass@host:5432/db' \
  -n location-podcast

# Redis credentials
kubectl create secret generic redis-credentials \
  --from-literal=url='redis://:password@host:6379/0' \
  -n location-podcast

# App secrets
kubectl create secret generic app-secrets \
  --from-literal=secret-key='YOUR_SECRET_KEY' \
  --from-literal=jwt-secret='YOUR_JWT_SECRET' \
  -n location-podcast

# API keys
kubectl create secret generic api-keys \
  --from-literal=openai-api-key='sk-...' \
  --from-literal=elevenlabs-api-key='...' \
  -n location-podcast
```

### **3. SSL/TLS Setup**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

## 📊 Monitoring Setup

### **1. Deploy Prometheus**

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/prometheus-values.yaml
```

### **2. Deploy Grafana**

```bash
# Grafana is included with kube-prometheus-stack
# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Default credentials:
# Username: admin
# Password: prom-operator
```

### **3. Import Dashboards**

1. Access Grafana at http://localhost:3000
2. Go to Dashboards → Import
3. Import dashboards from `monitoring/grafana/dashboards/`

---

## 🔄 CI/CD Setup

### **1. GitHub Actions**

The CI/CD pipeline is configured in `.github/workflows/deploy.yml`

**Required Secrets:**
```bash
# Add to GitHub repository secrets:
KUBE_CONFIG_STAGING      # Base64 encoded kubeconfig for staging
KUBE_CONFIG_PRODUCTION   # Base64 encoded kubeconfig for production
REGISTRY_USERNAME        # Container registry username
REGISTRY_PASSWORD        # Container registry password
```

**To add secrets:**
1. Go to GitHub repository → Settings → Secrets
2. Click "New repository secret"
3. Add each secret

### **2. Manual Deployment**

```bash
# Build images
docker build -t location-podcast/backend:latest ./backend
docker build -t location-podcast/frontend:latest ./frontend

# Push to registry
docker push location-podcast/backend:latest
docker push location-podcast/frontend:latest

# Update Kubernetes
kubectl set image deployment/backend backend=location-podcast/backend:latest -n location-podcast
kubectl set image deployment/frontend frontend=location-podcast/frontend:latest -n location-podcast

# Check rollout status
kubectl rollout status deployment/backend -n location-podcast
kubectl rollout status deployment/frontend -n location-podcast
```

---

## 🧪 Testing Deployment

### **1. Health Checks**

```bash
# Backend health
curl https://api.locationpodcast.com/health

# Frontend health
curl https://locationpodcast.com/health

# Expected response: {"status": "healthy"}
```

### **2. Smoke Tests**

```bash
# Run smoke tests
cd backend
pytest tests/smoke/ --production

# Expected: All tests pass
```

### **3. Load Testing**

```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io/

# Run load test
k6 run tests/load/basic-load-test.js

# Expected: 95th percentile < 2s
```

---

## 📈 Scaling

### **Manual Scaling**

```bash
# Scale backend
kubectl scale deployment/backend --replicas=5 -n location-podcast

# Scale frontend
kubectl scale deployment/frontend --replicas=3 -n location-podcast
```

### **Auto-scaling**

Auto-scaling is configured via HPA (Horizontal Pod Autoscaler):

```bash
# Check HPA status
kubectl get hpa -n location-podcast

# View HPA details
kubectl describe hpa backend-hpa -n location-podcast
```

**Scaling triggers:**
- CPU > 70%
- Memory > 80%
- Custom metrics (queue length, etc.)

---

## 🔧 Troubleshooting

### **Pods Not Starting**

```bash
# Check pod status
kubectl get pods -n location-podcast

# View pod logs
kubectl logs <pod-name> -n location-podcast

# Describe pod
kubectl describe pod <pod-name> -n location-podcast

# Common issues:
# - Image pull errors → Check registry credentials
# - CrashLoopBackOff → Check application logs
# - Pending → Check resource requests/limits
```

### **Database Connection Issues**

```bash
# Test database connection
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql postgresql://user:pass@host:5432/db

# Check database secret
kubectl get secret database-credentials -n location-podcast -o yaml
```

### **High Latency**

```bash
# Check resource usage
kubectl top pods -n location-podcast

# Check HPA status
kubectl get hpa -n location-podcast

# Scale up if needed
kubectl scale deployment/backend --replicas=10 -n location-podcast
```

### **SSL Certificate Issues**

```bash
# Check certificate status
kubectl get certificate -n location-podcast

# Describe certificate
kubectl describe certificate locationpodcast-tls -n location-podcast

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

---

## 🔄 Rollback

### **Rollback Deployment**

```bash
# View rollout history
kubectl rollout history deployment/backend -n location-podcast

# Rollback to previous version
kubectl rollout undo deployment/backend -n location-podcast

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n location-podcast
```

---

## 💾 Backup & Recovery

### **Database Backup**

```bash
# Manual backup
kubectl exec -it <postgres-pod> -n location-podcast -- \
  pg_dump -U postgres locationpodcast > backup.sql

# Restore from backup
kubectl exec -i <postgres-pod> -n location-podcast -- \
  psql -U postgres locationpodcast < backup.sql
```

### **Automated Backups**

Configure automated backups using your cloud provider:
- AWS: RDS automated backups
- GCP: Cloud SQL automated backups
- Azure: Azure Database automated backups

---

## 📞 Support

### **Monitoring Dashboards**
- Grafana: https://grafana.locationpodcast.com
- Prometheus: https://prometheus.locationpodcast.com

### **Logs**
```bash
# Stream all logs
kubectl logs -f -l app=location-podcast -n location-podcast

# Backend logs only
kubectl logs -f deployment/backend -n location-podcast

# Frontend logs only
kubectl logs -f deployment/frontend -n location-podcast
```

### **Metrics**
- Application metrics: `/metrics` endpoint
- Prometheus: http://prometheus:9090
- Grafana: http://grafana:3000

---

## ✅ Go-Live Checklist

### **Pre-Launch**
- [ ] All tests passing (unit, integration, E2E)
- [ ] Load testing completed successfully
- [ ] Security scan passed
- [ ] SSL certificates configured
- [ ] Monitoring and alerting operational
- [ ] Backup strategy implemented
- [ ] Disaster recovery tested
- [ ] Documentation complete

### **Launch Day**
- [ ] Deploy to production
- [ ] Verify all services healthy
- [ ] Run smoke tests
- [ ] Monitor metrics and logs
- [ ] Test critical user flows
- [ ] Verify SSL/HTTPS working
- [ ] Check performance metrics
- [ ] Confirm backups running

### **Post-Launch**
- [ ] Monitor error rates
- [ ] Review performance metrics
- [ ] Check resource utilization
- [ ] Verify auto-scaling working
- [ ] Test disaster recovery
- [ ] Update documentation
- [ ] Collect user feedback
- [ ] Plan next iteration

---

## 🎉 You're Live!

**Congratulations on deploying to production!**

Remember to:
- Monitor metrics regularly
- Review logs for errors
- Keep dependencies updated
- Test disaster recovery procedures
- Gather user feedback
- Iterate and improve

**Good luck!** 🚀
