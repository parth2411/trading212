# Trading212 MCP Server

Access your Trading212 account data, portfolio, orders, and trading history through Claude Desktop using the Model Context Protocol (MCP).

## Quick Start

```bash
# 1. Clone/navigate to the project
cd ~/trading212

# 2. Set up credentials
cp .env.example .env
nano .env  # Add your Trading212 API credentials

# 3. Build Docker image
docker build -t trading212-mcp-server:latest .

# 4. Restart Claude Desktop
# Quit and reopen Claude Desktop completely
```

## Features

✅ **17 Trading212 Tools** available in Claude Desktop
✅ **Secure .env Management** - No Docker warnings
✅ **Live & Demo Support** - Test safely with demo account

## Documentation

- **[SETUP.md](SETUP.md)** - Complete step-by-step setup guide
- **[ENV_SETUP.md](ENV_SETUP.md)** - How to manage credentials with `.env`
- **[SECRET_MANAGEMENT.md](SECRET_MANAGEMENT.md)** - Advanced security options

## Available Tools

**Account:** `get_account_info`, `get_account_cash`
**Portfolio:** `get_portfolio`, `get_position`
**Market Data:** `list_exchanges`, `search_instruments`
**Orders:** `get_active_orders`, `get_order`, `place_market_order`, `place_limit_order`, `place_stop_order`, `cancel_order`, `get_order_history`
**History:** `get_dividends`, `get_transactions`
**Pies:** `list_pies`, `get_pie`

## Requirements

- Docker Desktop
- Docker MCP Toolkit
- Claude Desktop
- Trading212 account (Invest or ISA)
- Trading212 API credentials

## Getting API Credentials

1. Log into Trading212: https://www.trading212.com/
2. Go to **Settings → API (Beta)**
3. Generate API Key
4. Copy both Key and Secret to `.env`

## Usage

Ask Claude Desktop:
- "Show me my Trading212 portfolio"
- "What's my account balance?"
- "Search for Tesla stock"

## Troubleshooting

See [SETUP.md](SETUP.md) for detailed troubleshooting.

**Quick fixes:**
- Verify Docker Desktop is running
- Rebuild: `docker build -t trading212-mcp-server:latest .`
- Restart Claude Desktop completely (Cmd+Q)

## Resources

- [Trading212 API Docs](https://docs.trading212.com/api)
- [Docker MCP Toolkit](https://docs.docker.com/mcp/)


**⚠️ Important:** Live environment executes real trades. Use demo for testing!

