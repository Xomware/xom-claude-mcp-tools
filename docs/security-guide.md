# Security Guide

## Overview

This guide covers security best practices for deploying and managing xom-claude-mcp-tools in production.

## Authentication

### API Keys

- Store in environment variables or secrets manager
- Never commit to version control
- Rotate regularly (at least quarterly)
- Use strong, randomly generated keys (32+ characters)

Example:
```bash
# ❌ Don't do this
export GITHUB_TOKEN="ghp_abc123def456"

# ✅ Use secrets manager
aws secretsmanager get-secret-value --secret-id xom-mcp/github-token
```

### OAuth2 Tokens

- Use short-lived tokens (1 hour recommended)
- Refresh tokens automatically before expiration
- Store refresh tokens securely
- Implement token rotation

```python
# Automatic token refresh
token = await oauth_manager.get_token(scope="repo")  # Auto-refresh if needed
```

### JWT Tokens

- Sign with strong secret (256-bit minimum)
- Include expiration claims
- Validate signature on every request
- Use HS256 or RS256 algorithms

## Encryption

### Data at Rest

Encrypt sensitive data in databases:

```python
from shared.security import EncryptionManager

encryption = EncryptionManager()

# Encrypt sensitive data before storing
encrypted = encryption.encrypt(sensitive_data)
db.insert({"data": encrypted})

# Decrypt when needed
decrypted = encryption.decrypt(encrypted)
```

### Data in Transit

- Always use HTTPS (TLS 1.2+)
- Enable certificate pinning for critical endpoints
- Validate certificate validity
- Use strong ciphers

```python
# HTTPS is enforced by default
async with httpx.AsyncClient(verify=True) as client:
    response = await client.get("https://api.example.com")
```

### Password Hashing

```python
from shared.security import EncryptionManager

encryption = EncryptionManager()

# Hash passwords for storage
hashed = encryption.hash_password(user_password)
db.insert({"password": hashed})

# Verify passwords
if encryption.verify_password(input_password, hashed):
    # Login successful
    pass
```

## Input Validation

### Sanitization

Always validate and sanitize inputs:

```python
def validate_inputs(self, **kwargs):
    """Validate all inputs."""
    # Check required fields
    required_fields = ["repo", "issue_number"]
    for field in required_fields:
        if field not in kwargs:
            raise ValidationError(f"Missing {field}")
    
    # Type checking
    if not isinstance(kwargs["issue_number"], int):
        raise ValidationError("issue_number must be integer")
    
    # Range validation
    if kwargs["issue_number"] < 0:
        raise ValidationError("issue_number must be positive")
    
    # SQL injection prevention (using parameterized queries)
    query = "SELECT * FROM issues WHERE id = :id"
    params = {"id": kwargs["issue_number"]}
    
    return True
```

### SQL Injection Prevention

Always use parameterized queries:

```python
# ❌ Don't do this
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ Do this
from sqlalchemy import text
query = text("SELECT * FROM users WHERE email = :email")
session.execute(query, {"email": email})
```

## Secrets Management

### Environment Variables

```bash
# .env (NEVER commit to version control)
GITHUB_TOKEN=ghp_...
SLACK_BOT_TOKEN=xoxb-...
ENCRYPTION_KEY=...
```

### AWS Secrets Manager

```python
import boto3

secrets_client = boto3.client('secretsmanager')

def get_secret(secret_name):
    try:
        response = secrets_client.get_secret_value(
            SecretId=secret_name
        )
        return response['SecretString']
    except Exception as e:
        logger.error(f"Failed to get secret: {e}")
        raise
```

### Kubernetes Secrets

```bash
# Create secret
kubectl create secret generic mcp-secrets \
  --from-literal=GITHUB_TOKEN=$GITHUB_TOKEN \
  --from-literal=SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN

# Use in deployment
env:
- name: GITHUB_TOKEN
  valueFrom:
    secretKeyRef:
      name: mcp-secrets
      key: GITHUB_TOKEN
```

## Logging and Monitoring

### Don't Log Secrets

```python
# ❌ Don't do this
logger.info(f"Using token: {token}")

# ✅ Do this
logger.info(f"Using token: {encryption.mask_sensitive(token)}")
```

### Audit Logging

```python
def audit_log(action, user, resource, result):
    """Log security-relevant actions."""
    logger.info(f"AUDIT: {action} by {user} on {resource}: {result}")

# Usage
audit_log(
    action="create_issue",
    user="john_doe",
    resource="Xomware/xom-project#123",
    result="success"
)
```

### Monitoring for Suspicious Activity

```python
# Monitor failed authentication attempts
failed_attempts = {}

def check_rate_limit(user):
    current_time = time.time()
    if user in failed_attempts:
        failed_attempts[user] = [
            t for t in failed_attempts[user]
            if current_time - t < 300  # 5 minute window
        ]
        
        if len(failed_attempts[user]) > 5:
            # Lock account or alert security
            logger.error(f"Multiple failed attempts for {user}")
            alert_security(f"Possible brute force attack: {user}")
```

## Access Control

### Role-Based Access Control (RBAC)

```python
class User:
    ROLES = {
        "admin": ["read", "write", "delete", "admin"],
        "editor": ["read", "write"],
        "viewer": ["read"],
    }
    
    def __init__(self, username, role):
        self.username = username
        self.role = role
    
    def can_do(self, action):
        return action in self.ROLES.get(self.role, [])

# Enforce permissions
def create_issue(user, repo, title):
    if not user.can_do("write"):
        raise PermissionError("User cannot create issues")
    # ... create issue
```

### Resource-Based Access Control

```python
def can_access_resource(user, resource):
    """Check if user has access to resource."""
    # Check user's teams
    if resource.team not in user.teams:
        return False
    
    # Check user's permissions
    if resource.permission_level > user.permission_level:
        return False
    
    return True
```

## Network Security

### Firewall Rules

```python
# Kubernetes Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-allow-ingress
spec:
  podSelector:
    matchLabels:
      app: mcp
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: xom-mcp
```

### VPC Configuration

- Separate private and public subnets
- Use NAT gateways for outbound traffic
- Implement security groups and NACLs
- Enable VPC Flow Logs for monitoring

## Dependency Management

### Vulnerability Scanning

```bash
# Scan for vulnerabilities
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

### Keep Dependencies Updated

```bash
# Update packages regularly
pip install --upgrade -r requirements.txt

# Review CHANGELOG
pip show package-name
```

## Deployment Security

### Container Security

```dockerfile
# ✅ Best practices
FROM python:3.11-slim
USER nonroot  # Don't run as root
COPY --chown=nonroot . /app
RUN chmod 755 /app

# ❌ Avoid
FROM python:3.11
COPY . /app
RUN chmod 777 /app  # Too permissive
```

### Secrets Injection

```bash
# ❌ Don't embed in Dockerfile
RUN echo "GITHUB_TOKEN=secret" > .env

# ✅ Use runtime injection
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN xom-mcp:latest
```

## Incident Response

### Security Incident Checklist

1. **Identify**: Detect the security incident
2. **Contain**: Stop the attack and limit damage
3. **Eradicate**: Remove the threat
4. **Recover**: Restore systems to normal operation
5. **Analyze**: Understand what happened
6. **Improve**: Prevent future incidents

### Key Contacts

```
Security Team: security@xomware.com
Incident Response: incident@xomware.com
```

## Compliance

### GDPR Compliance

- Implement data minimization
- Provide data deletion capabilities
- Maintain audit logs
- Implement access controls

### SOC 2 Compliance

- Document security policies
- Implement monitoring and alerting
- Perform regular security audits
- Implement incident response procedures

## Security Checklist

- [ ] All secrets in environment variables/secrets manager
- [ ] No hardcoded credentials in code
- [ ] HTTPS enabled for all external communication
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting enabled
- [ ] Audit logging configured
- [ ] Error messages don't expose sensitive data
- [ ] Dependencies up-to-date and scanned for vulnerabilities
- [ ] Regular backups configured
- [ ] Disaster recovery plan in place
- [ ] Security training completed

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
