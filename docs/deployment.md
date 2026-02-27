# Deployment Guide

## Overview

This guide covers deploying xom-claude-mcp-tools to production environments using Docker, Kubernetes, and Terraform.

## Prerequisites

- Docker and Docker Compose installed
- kubectl configured (for Kubernetes deployments)
- Terraform installed (for AWS deployments)
- AWS CLI configured (for AWS deployments)
- Git for version control

## Quick Start

### Local Development with Docker Compose

1. **Clone and setup**
```bash
git clone https://github.com/Xomware/xom-claude-mcp-tools.git
cd xom-claude-mcp-tools
cp .env.example .env
# Edit .env with your credentials
```

2. **Start services**
```bash
cd deployment
docker-compose up -d
```

3. **Verify services**
```bash
curl http://localhost:8001/health  # GitHub MCP
curl http://localhost:8002/health  # Slack MCP
curl http://localhost:8003/health  # Database MCP
curl http://localhost:8004/health  # Xomware API MCP
```

4. **Stop services**
```bash
docker-compose down
```

## Docker Deployment

### Building Images

```bash
# Build all images
docker-compose build

# Build specific image
docker build -t xom-mcp:github-1.0 -f tools/github-mcp/Dockerfile .
```

### Docker Registry

```bash
# Tag image
docker tag xom-mcp:github-1.0 registry.example.com/xom-mcp:github-1.0

# Push to registry
docker push registry.example.com/xom-mcp:github-1.0

# Pull from registry
docker pull registry.example.com/xom-mcp:github-1.0
```

### Running Standalone

```bash
# Run GitHub MCP
docker run \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -p 8001:8001 \
  -p 9001:9001 \
  xom-mcp:github-latest

# Run with volume
docker run \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -v $(pwd)/logs:/app/logs \
  -p 8001:8001 \
  xom-mcp:github-latest
```

## Kubernetes Deployment

### Prerequisites

```bash
# Create namespace
kubectl create namespace xom-mcp

# Create secrets
kubectl create secret generic mcp-secrets \
  --from-literal=GITHUB_TOKEN=$GITHUB_TOKEN \
  --from-literal=SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  --from-literal=DB_PASSWORD=$DB_PASSWORD \
  -n xom-mcp
```

### Deploy All Services

```bash
# Apply all configurations
kubectl apply -f deployment/kubernetes/

# Verify deployment
kubectl get pods -n xom-mcp
kubectl get services -n xom-mcp
```

### Deploy Individual Services

```bash
# Deploy GitHub MCP
kubectl apply -f deployment/kubernetes/deployments.yaml \
  -l app=github-mcp

# Check status
kubectl describe deployment github-mcp -n xom-mcp
kubectl logs -f deployment/github-mcp -n xom-mcp
```

### Scaling

```bash
# Scale GitHub MCP to 3 replicas
kubectl scale deployment github-mcp --replicas=3 -n xom-mcp

# Verify scaling
kubectl get pods -n xom-mcp
```

### Rolling Update

```bash
# Update image
kubectl set image deployment/github-mcp \
  github-mcp=xom-mcp:github-1.1 \
  -n xom-mcp

# Monitor rollout
kubectl rollout status deployment/github-mcp -n xom-mcp

# Rollback if needed
kubectl rollout undo deployment/github-mcp -n xom-mcp
```

## AWS Deployment with Terraform

### Prerequisites

```bash
# Configure AWS
aws configure

# Install Terraform
terraform version

# Set up Terraform backend
aws s3 mb s3://xom-terraform-state
aws dynamodb create-table \
  --table-name terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Configure Terraform

```bash
cd deployment/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
vim terraform.tfvars
```

### Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply deployment
terraform apply tfplan

# Get outputs
terraform output
```

### Managing Infrastructure

```bash
# Validate configuration
terraform validate

# Format configuration
terraform fmt -recursive

# Destroy infrastructure
terraform destroy
```

## Environment-Specific Deployments

### Development Environment

```yaml
# .env.dev
LOG_LEVEL=DEBUG
DB_INSTANCE_CLASS=db.t3.micro
ECS_DESIRED_COUNT=1
ENABLE_PR_REVIEW=true
ENABLE_ISSUE_MANAGEMENT=true
```

```bash
# Deploy dev
cd deployment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Staging Environment

```bash
# Deploy staging
kubectl apply -f deployment/kubernetes/ \
  -f deployment/kubernetes/staging/ \
  -n xom-mcp-staging
```

### Production Environment

```bash
# Deploy production (with multi-AZ, backups, etc.)
terraform apply -var="environment=prod" -var="db_multi_az=true"
```

## Monitoring and Logging

### Prometheus Metrics

Access metrics dashboard:
```
http://localhost:9090
```

View metrics for a tool:
```
http://localhost:9090/targets
```

### CloudWatch Logs (AWS)

```bash
# View logs
aws logs tail /ecs/xom-mcp --follow

# Get logs
aws logs get-log-events \
  --log-group-name /ecs/xom-mcp \
  --log-stream-name github-mcp/github-mcp/123abc
```

### Kubernetes Logs

```bash
# View pod logs
kubectl logs -f deployment/github-mcp -n xom-mcp

# View logs with timestamps
kubectl logs -f deployment/github-mcp -n xom-mcp --timestamps=true

# Tail logs from multiple pods
kubectl logs -f -l app=github-mcp -n xom-mcp
```

## Health Checks

### Health Endpoint

All services expose `/health`:
```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "github": "healthy",
    "database": "healthy"
  }
}
```

### Readiness/Liveness Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8001
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8001
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Database Management

### PostgreSQL Backup

```bash
# Manual backup
docker exec xom-postgres pg_dump -U xomware xomware > backup.sql

# Restore backup
cat backup.sql | docker exec -i xom-postgres psql -U xomware xomware
```

### AWS RDS Backup

```bash
# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier xom-mcp-db \
  --db-snapshot-identifier xom-mcp-backup-$(date +%Y%m%d)

# List snapshots
aws rds describe-db-snapshots --db-instance-identifier xom-mcp-db
```

### Database Migrations

```bash
# Using Alembic
alembic upgrade head

# Manual migration
docker exec xom-database-mcp python -m tools.database_mcp.migrate
```

## SSL/TLS Configuration

### Self-Signed Certificates

```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem -out cert.pem -days 365 -nodes

# Use in Docker
docker run -v $(pwd)/cert.pem:/app/cert.pem -p 443:443 xom-mcp
```

### Let's Encrypt with Kubernetes

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@xomware.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs xom-github-mcp
kubectl logs -f deployment/github-mcp -n xom-mcp

# Check port availability
netstat -tlnp | grep 8001

# Check disk space
df -h

# Check memory
free -h
```

### Database Connection Issues

```bash
# Test database connection
docker exec xom-database-mcp \
  psql -h postgres -U xomware -d xomware -c "SELECT 1"

# Check database logs
docker logs xom-postgres

# Verify credentials
echo $DB_PASSWORD
```

### Performance Issues

```bash
# Monitor CPU and memory
docker stats

# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Analyze slow queries
kubectl logs -f deployment/database-mcp -n xom-mcp | grep "slow"
```

## Backup and Recovery

### Backup Strategy

```bash
# Daily backups
0 2 * * * /scripts/backup.sh

# Weekly off-site backup
0 3 * * 0 /scripts/backup-offsite.sh
```

### Disaster Recovery

```bash
# Test recovery procedures monthly
1. Stop all services
2. Restore from backup
3. Verify all services are operational
4. Check data integrity
```

## Security Hardening

### Network Security

```bash
# Restrict ingress to specific IPs
kubectl set env deployment/github-mcp \
  ALLOWED_IPs="10.0.0.0/8" \
  -n xom-mcp
```

### Pod Security

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
```

## Cost Optimization

- Use t3 instances for non-production
- Enable auto-scaling based on metrics
- Use spot instances where appropriate
- Implement resource requests and limits
- Regular cost audits

## References

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [AWS Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws-security.html)
