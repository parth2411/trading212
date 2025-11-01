# Trading212 MCP Server Setup Guide

This guide provides step-by-step instructions to set up the Trading212 MCP (Model Context Protocol) server for use with Claude Desktop using Docker MCP Toolkit.

## Overview

The Trading212 MCP Server allows you to access your Trading212 account data, portfolio, orders, and trading history through Claude Desktop. It provides 17 tools for comprehensive account management.

## Prerequisites

- Docker Desktop installed and running
- Docker MCP Toolkit installed
- Claude Desktop installed
- Trading212 account (Invest or ISA account - API not available for CFD accounts)
- Trading212 API credentials (API Key and Secret)

## Table of Contents

1. [Get Trading212 API Credentials](#1-get-trading212-api-credentials)
2. [Project Structure](#2-project-structure)
3. [Create Server Files](#3-create-server-files)
4. [Configure Docker MCP](#4-configure-docker-mcp)
5. [Build Docker Image](#5-build-docker-image)
6. [Configure Claude Desktop](#6-configure-claude-desktop)
7. [Testing](#7-testing)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Get Trading212 API Credentials

### Step 1.1: Access API Settings

1. Log into your Trading212 account at https://www.trading212.com/
2. Navigate to **Settings → API (Beta)**
3. **Note**: API access is only available for General Invest and Stock & Shares ISA accounts

### Step 1.2: Generate API Key

1. Click **"Generate API Key"**
2. **IMPORTANT**: Copy both the **API Key** and **API Secret** immediately
3. The API Secret is shown **only once** and cannot be retrieved later
4. Store them securely

### Step 1.3: Test Credentials

Test your credentials work before proceeding:

```bash
# Replace YOUR_API_KEY and YOUR_API_SECRET with your actual credentials
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Basic $(echo -n 'YOUR_API_KEY:YOUR_API_SECRET' | base64)" \
  "https://live.trading212.com/api/v0/equity/account/info"
```

**Expected Result**: `HTTP Status: 200` with your account information in JSON format.

---

## 2. Project Structure

Create the following directory structure:

```
~/trading212/
├── Dockerfile
├── trading212_server.py
├── requirements.txt
└── SETUP.md (this file)

~/.docker/mcp/
├── catalogs/
│   └── mycustomcatalog.yaml
├── config.yaml
└── registry.yaml
```

---

## 3. Create Server Files

### Step 3.1: Create Project Directory

```bash
mkdir -p ~/trading212
cd ~/trading212
```

### Step 3.2: Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
mcp[cli]>=1.2.0
httpx
python-dotenv
EOF
```

### Step 3.3: Create trading212_server.py

Create the server file (the full Python code is already in your project at `~/trading212/trading212_server.py`).

### Step 3.4: Create .env File

Create a `.env` file to store your API credentials securely:

```bash
cat > .env << 'EOF'
TRADING212_API_KEY=your_actual_api_key_here
TRADING212_API_SECRET=your_actual_api_secret_here
TRADING212_ENVIRONMENT=live
EOF
```

**IMPORTANT**: Edit the `.env` file and replace:
- `your_actual_api_key_here` with your actual Trading212 API Key
- `your_actual_api_secret_here` with your actual Trading212 API Secret
- Set `TRADING212_ENVIRONMENT` to either `live` or `demo`

### Step 3.5: Create .gitignore

Protect your credentials from being committed to git:

```bash
cat > .gitignore << 'EOF'
# Environment variables (contains sensitive API credentials)
.env

# Python
__pycache__/
*.py[cod]

# Docker
*.log

# IDE
.vscode/
.idea/
EOF
```

### Step 3.6: Create Dockerfile

The Dockerfile will copy and use the `.env` file:

```bash
cat > Dockerfile << 'EOF'
# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python unbuffered mode
ENV PYTHONUNBUFFERED=1

# Note: Credentials are loaded from .env file at runtime
# See .env.example for required variables

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY trading212_server.py .

# Copy .env file (contains credentials)
COPY .env .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Run the server
CMD ["python", "trading212_server.py"]
EOF
```

**Note**: This approach uses `.env` for secret management - no warnings, clean separation of credentials from code. See [ENV_SETUP.md](ENV_SETUP.md) for details.

---

## 4. Configure Docker MCP

### Step 4.1: Create MCP Directory Structure

```bash
mkdir -p ~/.docker/mcp/catalogs
```

### Step 4.2: Create Custom Catalog

Create `~/.docker/mcp/catalogs/mycustomcatalog.yaml`:

```bash
cat > ~/.docker/mcp/catalogs/mycustomcatalog.yaml << 'EOF'
version: 2
name: custom
displayName: Custom MCP Servers
registry:
  trading212:
    description: "Access your Trading212 account data, portfolio, orders, and trading history"
    title: "Trading212"
    type: server
    dateAdded: "2025-10-17T00:00:00Z"
    image: trading212-mcp-server:latest
    ref: ""
    readme: ""
    toolsUrl: ""
    source: ""
    upstream: ""
    icon: ""
    tools:
      - name: get_account_info
      - name: get_account_cash
      - name: get_portfolio
      - name: get_position
      - name: list_exchanges
      - name: search_instruments
      - name: get_active_orders
      - name: get_order
      - name: place_market_order
      - name: place_limit_order
      - name: place_stop_order
      - name: cancel_order
      - name: get_order_history
      - name: get_dividends
      - name: get_transactions
      - name: list_pies
      - name: get_pie
    metadata:
      category: finance
      tags:
        - trading
        - stocks
        - portfolio
        - investment
        - finance
      license: MIT
      owner: local
EOF
```

### Step 4.3: Create Config File

Create `~/.docker/mcp/config.yaml`:

```bash
cat > ~/.docker/mcp/config.yaml << 'EOF'
servers:
  trading212:
    image: trading212-mcp-server:latest
EOF
```

### Step 4.4: Create Registry File

Create `~/.docker/mcp/registry.yaml`:

```bash
cat > ~/.docker/mcp/registry.yaml << 'EOF'
registry:
  trading212:
    ref: ""
EOF
```

**Note**: If you already have other servers in your registry, just add the `trading212` entry to your existing file.

---

## 5. Build Docker Image

### Step 5.1: Navigate to Project Directory

```bash
cd ~/trading212
```

### Step 5.2: Build the Docker Image

```bash
docker build -t trading212-mcp-server:latest .
```

**Expected Output**: You'll see build logs.

**Note about Security Warnings**: You may see these warnings:
```
⚠️  SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data
```

These warnings are expected and **safe to ignore for local development**. If you want to implement more secure secret management (recommended for production), see [SECRET_MANAGEMENT.md](SECRET_MANAGEMENT.md) for alternatives including Docker Secrets, build-time secrets, and external secret managers.

### Step 5.3: Verify Image Built Successfully

```bash
docker images | grep trading212
```

**Expected Output**:
```
trading212-mcp-server    latest    <image-id>    <time>    289MB
```

### Step 5.4: Test the Image

```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | docker run -i --rm trading212-mcp-server:latest
```

**Expected Output**: You should see:
- `Environment: LIVE` (or DEMO)
- No warnings about missing API keys
- JSON response with server info

---

## 6. Configure Claude Desktop

### Step 6.1: Locate Claude Desktop Config

The config file is located at:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Step 6.2: Update Configuration

Edit the file (or create it if it doesn't exist):

```json
{
  "mcpServers": {
    "mcp-toolkit-gateway": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "/Users/YOUR_USERNAME/.docker/mcp:/mcp",
        "docker/mcp-gateway",
        "--catalog=/mcp/catalogs/docker-mcp.yaml",
        "--catalog=/mcp/catalogs/mycustomcatalog.yaml",
        "--config=/mcp/config.yaml",
        "--registry=/mcp/registry.yaml",
        "--tools-config=/mcp/tools.yaml",
        "--transport=stdio"
      ]
    }
  }
}
```

**IMPORTANT**: Replace `YOUR_USERNAME` with your actual macOS username.

### Step 6.3: Restart Claude Desktop

1. **Completely quit** Claude Desktop (Cmd+Q, don't just close the window)
2. Reopen Claude Desktop
3. Wait a few seconds for the MCP gateway to initialize

---

## 7. Testing

### Step 7.1: Verify Server is Listed

Check that your server is registered:

```bash
docker mcp server ls
```

**Expected Output**: Should include `trading212` in the list.

### Step 7.2: Test Gateway Integration

```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | docker run -i --rm -v /var/run/docker.sock:/var/run/docker.sock -v ~/.docker/mcp:/mcp docker/mcp-gateway --catalog=/mcp/catalogs/mycustomcatalog.yaml --config=/mcp/config.yaml --registry=/mcp/registry.yaml --transport=stdio 2>&1 | grep trading212
```

**Expected Output**: Should show trading212 starting with `Environment: LIVE` and listing 17 tools.

### Step 7.3: Test in Claude Desktop

In Claude Desktop, try asking:
```
Can you show me my Trading212 portfolio?
```

or

```
What tools do you have available for Trading212?
```

You should see 17 Trading212 tools available:
- Account tools: `get_account_info`, `get_account_cash`
- Portfolio tools: `get_portfolio`, `get_position`
- Market data: `list_exchanges`, `search_instruments`
- Orders: `get_active_orders`, `get_order`, `place_market_order`, `place_limit_order`, `place_stop_order`, `cancel_order`, `get_order_history`
- History: `get_dividends`, `get_transactions`
- Pies: `list_pies`, `get_pie`

---

## 8. Troubleshooting

### Issue: Tools Not Appearing in Claude Desktop

**Solution**:
1. Completely quit Claude Desktop (Cmd+Q)
2. Verify Docker Desktop is running
3. Check the image exists: `docker images | grep trading212`
4. Rebuild the image: `docker build -t trading212-mcp-server:latest .`
5. Restart Claude Desktop

### Issue: 401 Authentication Error

**Symptoms**: API returns "401 Unauthorized"

**Solution**:
1. Verify your API credentials are correct
2. Test credentials with curl (see Step 1.3)
3. Check if you deleted the correct API key in Trading212
4. Regenerate API credentials in Trading212
5. Update Dockerfile with new credentials
6. Rebuild image: `docker build -t trading212-mcp-server:latest .`

### Issue: Empty Environment Variables

**Symptoms**: Logs show `-e  -e  -e` or warnings about missing API keys

**Solution**:
- Credentials are embedded in the Docker image (in Dockerfile)
- Do NOT use `secrets` in the catalog file
- Do NOT use `environment` or `env` in config.yaml
- The credentials should be in the Dockerfile as `ENV` directives

### Issue: Docker Build Warnings About Secrets

**Symptoms**:
```
SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data
```

**Explanation**: This warning is expected. For local development, embedding credentials in the Docker image is acceptable. For production, you would use Docker secrets or environment variables passed at runtime.

**Solution**: This warning can be safely ignored for local use.

### Issue: Server Not Starting

**Check Logs**:
```bash
docker logs $(docker ps -a | grep trading212 | awk '{print $1}' | head -1)
```

### Issue: API Rate Limiting

Trading212 may have rate limits. If you hit them:
- Wait a few minutes
- Reduce the frequency of requests

---

## Available Tools

### Account Information
- `get_account_info` - Get account ID, currency, and balance
- `get_account_cash` - Get detailed cash breakdown

### Portfolio Management
- `get_portfolio` - View all open positions
- `get_position` - Get detailed position information for a specific ticker

### Market Data
- `list_exchanges` - List available stock exchanges
- `search_instruments` - Search for tradable instruments by name/ticker

### Order Management
- `get_active_orders` - List all pending orders
- `get_order` - Get details of a specific order
- `place_market_order` - Place market order (LIVE only)
- `place_limit_order` - Place limit order
- `place_stop_order` - Place stop/stop-loss order
- `cancel_order` - Cancel an active order
- `get_order_history` - View historical orders

### Transaction History
- `get_dividends` - View dividend payment history
- `get_transactions` - View account transactions

### Pies (Investment Portfolios)
- `list_pies` - List all investment pies
- `get_pie` - Get detailed pie information

---

## Security Notes

1. **API Credentials**: Keep your API Key and Secret secure. Never commit them to version control.
2. **Live vs Demo**: Use the demo environment for testing. Only use live when you're confident.
3. **IP Restrictions**: Consider enabling IP restrictions in Trading212 for additional security.
4. **Order Placement**: Be extremely careful with order placement tools - they execute real trades in live mode!

---

## Environment Variables

The following environment variables are set in the Dockerfile:

- `TRADING212_API_KEY` - Your Trading212 API Key
- `TRADING212_API_SECRET` - Your Trading212 API Secret
- `TRADING212_ENVIRONMENT` - Either "live" or "demo"

---

## Updating Credentials

If you need to update your API credentials:

1. Edit `~/trading212/Dockerfile`
2. Update the `ENV` variables (lines 11-13)
3. Rebuild the image:
   ```bash
   cd ~/trading212
   docker build -t trading212-mcp-server:latest .
   ```
4. Restart Claude Desktop

---

## Additional Resources

- Trading212 API Documentation: https://docs.trading212.com/api
- Trading212 API Reference: https://t212public-api-docs.redoc.ly/
- Docker MCP Toolkit: https://docs.docker.com/mcp/
- MCP Specification: https://modelcontextprotocol.io/

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#8-troubleshooting) section
2. Verify all steps were followed correctly
3. Check Docker Desktop and Claude Desktop logs
4. Ensure Trading212 API access is enabled for your account

---

## Version History

- **v1.0** (2025-10-18) - Initial setup with 17 Trading212 tools

---

**Happy Trading!** 🚀
