# Secret Management Alternatives for Trading212 MCP Server

This guide shows secure alternatives to embedding API credentials directly in the Dockerfile.

## The Problem

Embedding secrets in Dockerfile using `ENV` instructions triggers security warnings:

```
⚠️  SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data
```

While acceptable for local development, there are more secure approaches for production use.

---

## Comparison of Approaches

| Method | Security | Complexity | Best For |
|--------|----------|------------|----------|
| ENV in Dockerfile | ⭐ Low | ⭐ Simple | Local dev only |
| Docker Secrets (File Mount) | ⭐⭐⭐⭐ High | ⭐⭐ Medium | Docker Swarm/Compose |
| Build-time Secrets | ⭐⭐⭐ Medium | ⭐⭐ Medium | CI/CD builds |
| Environment Variables at Runtime | ⭐⭐⭐ Medium | ⭐ Simple | Simple deployments |
| External Secret Manager | ⭐⭐⭐⭐⭐ Highest | ⭐⭐⭐⭐ Complex | Production/Enterprise |

---

## Option 1: Docker Secrets with File Mounts (Recommended)

This approach uses Docker's secret mounting feature where secrets are provided as files at runtime.

### Advantages:
✅ Secrets not stored in image
✅ No rebuild needed when rotating credentials
✅ Works with Docker MCP toolkit
✅ Industry best practice

### Implementation:

#### Step 1: Create Secret Files

```bash
# Create a secrets directory
mkdir -p ~/.docker/mcp/secrets

# Create secret files
echo -n "YOUR_API_KEY" > ~/.docker/mcp/secrets/trading212_api_key
echo -n "YOUR_API_SECRET" > ~/.docker/mcp/secrets/trading212_api_secret
echo -n "live" > ~/.docker/mcp/secrets/trading212_environment

# Secure the files
chmod 600 ~/.docker/mcp/secrets/*
```

#### Step 2: Update Dockerfile (Remove ENV secrets)

```dockerfile
# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python unbuffered mode
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY trading212_server.py .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Run the server
CMD ["python", "trading212_server.py"]
```

#### Step 3: Update Server Code to Read from Files

Modify `trading212_server.py` to read from `/run/secrets/` files:

```python
import os
from pathlib import Path

def read_secret(secret_name: str, default: str = "") -> str:
    """
    Read secret from Docker secret file or fall back to environment variable.
    Docker secrets are mounted at /run/secrets/<secret_name>
    """
    # Try Docker secret file first
    secret_file = Path(f"/run/secrets/{secret_name}")
    if secret_file.exists():
        return secret_file.read_text().strip()

    # Fall back to environment variable
    return os.environ.get(secret_name, default)

# Configuration
API_KEY = read_secret("TRADING212_API_KEY", "")
API_SECRET = read_secret("TRADING212_API_SECRET", "")
ENVIRONMENT = read_secret("TRADING212_ENVIRONMENT", "demo")
```

#### Step 4: Update config.yaml

Update `~/.docker/mcp/config.yaml`:

```yaml
servers:
  trading212:
    image: trading212-mcp-server:latest
    secrets:
      TRADING212_API_KEY:
        file: /Users/YOUR_USERNAME/.docker/mcp/secrets/trading212_api_key
      TRADING212_API_SECRET:
        file: /Users/YOUR_USERNAME/.docker/mcp/secrets/trading212_api_secret
      TRADING212_ENVIRONMENT:
        file: /Users/YOUR_USERNAME/.docker/mcp/secrets/trading212_environment
```

#### Step 5: Rebuild and Test

```bash
cd ~/trading212
docker build -t trading212-mcp-server:latest .
```

---

## Option 2: Build-time Secrets (Docker BuildKit)

Uses Docker BuildKit's `--secret` flag to pass secrets during build without storing them in the image.

### Advantages:
✅ Secrets not stored in final image
✅ No secrets in layers
✅ Single build command

### Disadvantages:
❌ Secrets still end up in environment at runtime (just not in image)
❌ Requires rebuild for credential rotation

### Implementation:

#### Step 1: Create Dockerfile with Build Secrets

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY trading212_server.py .

# Create user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Read secrets at build time and set as ENV
# These will be available at runtime but not visible in image layers
RUN --mount=type=secret,id=api_key \
    --mount=type=secret,id=api_secret \
    --mount=type=secret,id=environment \
    echo "export TRADING212_API_KEY=$(cat /run/secrets/api_key)" >> ~/.bashrc && \
    echo "export TRADING212_API_SECRET=$(cat /run/secrets/api_secret)" >> ~/.bashrc && \
    echo "export TRADING212_ENVIRONMENT=$(cat /run/secrets/environment)" >> ~/.bashrc

CMD ["python", "trading212_server.py"]
```

#### Step 2: Build with Secrets

```bash
# Create secret files
echo -n "YOUR_API_KEY" > /tmp/api_key
echo -n "YOUR_API_SECRET" > /tmp/api_secret
echo -n "live" > /tmp/environment

# Build with secrets
DOCKER_BUILDKIT=1 docker build \
  --secret id=api_key,src=/tmp/api_key \
  --secret id=api_secret,src=/tmp/api_secret \
  --secret id=environment,src=/tmp/environment \
  -t trading212-mcp-server:latest .

# Clean up secret files
rm /tmp/api_key /tmp/api_secret /tmp/environment
```

---

## Option 3: Runtime Environment Variables

Pass secrets as environment variables when running the container (not during build).

### Advantages:
✅ Simple to implement
✅ Secrets not in image
✅ Easy credential rotation

### Disadvantages:
❌ Need to modify how Docker MCP gateway starts containers
❌ Variables visible in `docker inspect`

### Implementation:

#### Step 1: Clean Dockerfile (No secrets)

Use the Dockerfile from Option 1 (no ENV secrets).

#### Step 2: Update config.yaml

```yaml
servers:
  trading212:
    image: trading212-mcp-server:latest
    environment:
      TRADING212_API_KEY: "${TRADING212_API_KEY}"
      TRADING212_API_SECRET: "${TRADING212_API_SECRET}"
      TRADING212_ENVIRONMENT: "live"
```

#### Step 3: Set Environment Variables in Shell

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export TRADING212_API_KEY="your_api_key"
export TRADING212_API_SECRET="your_api_secret"
```

Then reload:
```bash
source ~/.zshrc
```

#### Step 4: Restart Claude Desktop

Claude Desktop will read the environment variables from your shell.

---

## Option 4: .env File (Simple but Less Secure)

Use a `.env` file that's loaded at runtime.

### Implementation:

#### Step 1: Create .env file

```bash
cat > ~/.docker/mcp/.env << 'EOF'
TRADING212_API_KEY=your_api_key
TRADING212_API_SECRET=your_api_secret
TRADING212_ENVIRONMENT=live
EOF

chmod 600 ~/.docker/mcp/.env
```

#### Step 2: Add to .gitignore

```bash
echo ".env" >> ~/.docker/mcp/.gitignore
```

#### Step 3: Update config.yaml

```yaml
servers:
  trading212:
    image: trading212-mcp-server:latest
    env_file: /Users/YOUR_USERNAME/.docker/mcp/.env
```

---

## Option 5: External Secret Manager (Production)

Use services like HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault.

### Advantages:
✅ Enterprise-grade security
✅ Centralized secret management
✅ Audit logging
✅ Automatic rotation

### Disadvantages:
❌ Complex setup
❌ Additional infrastructure
❌ May incur costs

### High-Level Implementation:

1. Store secrets in secret manager
2. Modify server to fetch secrets from manager API at startup
3. Use IAM roles/service accounts for authentication
4. Implement secret caching and rotation logic

Example with AWS Secrets Manager:

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

secrets = get_secret('trading212/credentials')
API_KEY = secrets['api_key']
API_SECRET = secrets['api_secret']
```

---

## Recommended Approach for Different Scenarios

### Local Development
✅ **Current approach** (ENV in Dockerfile) - Simple and acceptable
⚠️ Warning can be ignored

### Team Development
✅ **Option 1** (Docker Secrets with Files) - Good balance of security and simplicity
✅ **Option 4** (.env file) - Simple, just ensure .env is in .gitignore

### Production Deployment
✅ **Option 1** (Docker Secrets) - For Docker Swarm/Kubernetes
✅ **Option 5** (External Secret Manager) - For enterprise/cloud deployments

---

## Migration Guide: Current to Option 1 (Docker Secrets)

If you want to migrate from your current setup to the more secure Docker Secrets approach:

### Step-by-Step Migration:

```bash
# 1. Create secrets directory
mkdir -p ~/.docker/mcp/secrets

# 2. Create secret files (replace with your actual values)
echo -n "YOUR_API_KEY" > ~/.docker/mcp/secrets/trading212_api_key
echo -n "YOUR_API_SECRET" > ~/.docker/mcp/secrets/trading212_api_secret
echo -n "live" > ~/.docker/mcp/secrets/trading212_environment

# 3. Secure the files
chmod 600 ~/.docker/mcp/secrets/*

# 4. Backup current Dockerfile
cp ~/trading212/Dockerfile ~/trading212/Dockerfile.backup

# 5. Update Dockerfile (remove ENV lines 11-13)
# Use Dockerfile.secrets as reference

# 6. Update server code to read from files
# Use trading212_server_secrets.py as reference

# 7. Rebuild image
cd ~/trading212
docker build -t trading212-mcp-server:latest .

# 8. Test
docker run -i --rm \
  -v ~/.docker/mcp/secrets/trading212_api_key:/run/secrets/TRADING212_API_KEY \
  -v ~/.docker/mcp/secrets/trading212_api_secret:/run/secrets/TRADING212_API_SECRET \
  -v ~/.docker/mcp/secrets/trading212_environment:/run/secrets/TRADING212_ENVIRONMENT \
  trading212-mcp-server:latest

# 9. Update config.yaml with secret mounts

# 10. Restart Claude Desktop
```

---

## Security Best Practices

Regardless of which approach you choose:

1. **Never commit secrets to version control**
   ```bash
   echo "*.env" >> .gitignore
   echo "secrets/" >> .gitignore
   echo "*.key" >> .gitignore
   echo "*.secret" >> .gitignore
   ```

2. **Use strong file permissions**
   ```bash
   chmod 600 ~/.docker/mcp/secrets/*
   ```

3. **Rotate credentials regularly**
   - Trading212 allows you to revoke and regenerate API keys
   - Update secrets and rebuild/restart

4. **Use different credentials for different environments**
   - Separate keys for development and production
   - Use demo account for testing

5. **Enable IP restrictions** (if supported)
   - Trading212 supports IP whitelisting for API keys
   - Limit access to your known IPs

6. **Monitor API usage**
   - Regularly check Trading212 API logs
   - Set up alerts for unusual activity

---

## Troubleshooting

### Secrets not being read

**Check file paths:**
```bash
ls -la ~/.docker/mcp/secrets/
```

**Verify file permissions:**
```bash
chmod 600 ~/.docker/mcp/secrets/*
```

**Test secret reading:**
```bash
cat ~/.docker/mcp/secrets/trading212_api_key
```

### Container can't access secret files

**Ensure correct mount paths:**
- Host: `~/.docker/mcp/secrets/trading212_api_key`
- Container: `/run/secrets/TRADING212_API_KEY`

**Check Docker volume mounts:**
```bash
docker inspect <container_id> | grep Mounts -A 20
```

---

## Conclusion

For your use case (local development with Claude Desktop):
- **Current approach** with ENV in Dockerfile is fine and the warnings can be ignored
- For slightly better security without much complexity, use **Option 1 (Docker Secrets with Files)**
- For production use, implement **Option 5 (External Secret Manager)**

The warnings are there to make you aware of security implications, but they don't prevent the image from working. Choose the approach that balances security needs with complexity for your specific use case.
