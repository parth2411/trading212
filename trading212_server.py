#!/usr/bin/env python3
"""
Simple Trading212 MCP Server - Access your Trading212 account data, portfolio, orders, and trading history
"""
import os
import sys
import logging
import base64
from datetime import datetime, timezone
from pathlib import Path
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path("/app/.env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger = logging.getLogger("trading212-server")
    logger.info("Loaded environment variables from .env file")

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("trading212-server")

# Initialize MCP server
mcp = FastMCP("trading212")

# Configuration
API_KEY = os.environ.get("TRADING212_API_KEY", "")
API_SECRET = os.environ.get("TRADING212_API_SECRET", "")
ENVIRONMENT = os.environ.get("TRADING212_ENVIRONMENT", "live")  # demo or live

# Base URLs
DEMO_BASE_URL = "https://demo.trading212.com/api/v0"
LIVE_BASE_URL = "https://live.trading212.com/api/v0"

def get_base_url():
    """Get the base URL based on environment."""
    return LIVE_BASE_URL if ENVIRONMENT.lower() == "live" else DEMO_BASE_URL

def get_auth_header():
    """Generate Basic Auth header from API key and secret."""
    if not API_KEY or not API_SECRET:
        return ""
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded}"

async def make_request(method: str, endpoint: str, data: str = ""):
    """Make an HTTP request to Trading212 API."""
    if not API_KEY or not API_SECRET:
        return "❌ Error: API_KEY and API_SECRET environment variables not set"
    
    base_url = get_base_url()
    url = f"{base_url}{endpoint}"
    auth_header = get_auth_header()
    
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                import json
                json_data = json.loads(data) if data else {}
                response = await client.post(url, headers=headers, json=json_data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            elif method == "PUT":
                import json
                json_data = json.loads(data) if data else {}
                response = await client.put(url, headers=headers, json=json_data)
            else:
                return f"❌ Error: Unsupported method {method}"
            
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_msg = e.response.text if e.response.text else str(e)
        return f"❌ API Error ({e.response.status_code}): {error_msg}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def format_currency(value):
    """Format currency value."""
    try:
        return f"${float(value):,.2f}"
    except:
        return str(value)

# === MCP TOOLS ===

@mcp.tool()
async def get_account_info() -> str:
    """Get your Trading212 account information including ID, currency, and cash balance."""
    logger.info("Fetching account info")
    
    try:
        result = await make_request("GET", "/equity/account/info")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        return f"""📊 Account Information:
- Account ID: {result.get('id', 'N/A')}
- Currency: {result.get('currencyCode', 'N/A')}
- Cash Available: {format_currency(result.get('cash', 0))}

Environment: {ENVIRONMENT.upper()}"""
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_account_cash() -> str:
    """Get detailed cash balance information for your Trading212 account."""
    logger.info("Fetching account cash")
    
    try:
        result = await make_request("GET", "/equity/account/cash")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        return f"""💰 Cash Balance:
- Free: {format_currency(result.get('free', 0))}
- Invested: {format_currency(result.get('invested', 0))}
- Profit/Loss: {format_currency(result.get('ppl', 0))}
- Result: {format_currency(result.get('result', 0))}
- Total: {format_currency(result.get('total', 0))}
- Blocked: {format_currency(result.get('blocked', 0))}
- Pieppl: {format_currency(result.get('pieppl', 0))}

Environment: {ENVIRONMENT.upper()}"""
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_portfolio() -> str:
    """Get all open positions in your Trading212 portfolio with current values and profit/loss."""
    logger.info("Fetching portfolio positions")
    
    try:
        result = await make_request("GET", "/equity/portfolio")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        if not result:
            return "📊 Portfolio is empty"
        
        output = "📊 Portfolio Positions:\n\n"
        for position in result:
            ticker = position.get('ticker', 'N/A')
            quantity = position.get('quantity', 0)
            avg_price = position.get('averagePrice', 0)
            current_price = position.get('currentPrice', 0)
            ppl = position.get('ppl', 0)
            ppl_percent = (ppl / (avg_price * quantity) * 100) if avg_price * quantity > 0 else 0
            
            output += f"""📈 {ticker}
   Quantity: {quantity}
   Avg Price: {format_currency(avg_price)}
   Current: {format_currency(current_price)}
   P/L: {format_currency(ppl)} ({ppl_percent:+.2f}%)
   
"""
        
        return output + f"Environment: {ENVIRONMENT.upper()}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_position(ticker: str = "") -> str:
    """Get detailed information about a specific position in your portfolio by ticker symbol."""
    if not ticker.strip():
        return "❌ Error: Ticker symbol is required"
    
    logger.info(f"Fetching position for {ticker}")
    
    try:
        result = await make_request("GET", f"/equity/portfolio/{ticker}")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        ticker_name = result.get('ticker', 'N/A')
        quantity = result.get('quantity', 0)
        avg_price = result.get('averagePrice', 0)
        current_price = result.get('currentPrice', 0)
        ppl = result.get('ppl', 0)
        initial_fill_date = result.get('initialFillDate', 'N/A')
        max_buy = result.get('maxBuy', 0)
        max_sell = result.get('maxSell', 0)
        
        return f"""📈 Position Details: {ticker_name}

📊 Holdings:
- Quantity: {quantity}
- Average Price: {format_currency(avg_price)}
- Current Price: {format_currency(current_price)}
- Total Value: {format_currency(quantity * current_price)}

💰 Performance:
- P/L: {format_currency(ppl)}
- Return: {(ppl / (avg_price * quantity) * 100) if avg_price * quantity > 0 else 0:+.2f}%

📅 Details:
- Initial Fill: {initial_fill_date}
- Max Buy: {max_buy}
- Max Sell: {max_sell}

Environment: {ENVIRONMENT.upper()}"""
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def list_exchanges() -> str:
    """List all available stock exchanges and their trading schedules."""
    logger.info("Fetching exchanges")
    
    try:
        result = await make_request("GET", "/equity/metadata/exchanges")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        if not result:
            return "📊 No exchanges found"
        
        output = "🌐 Available Exchanges:\n\n"
        for exchange in result:
            name = exchange.get('name', 'N/A')
            exchange_id = exchange.get('id', 'N/A')
            working_schedules = exchange.get('workingSchedules', [])
            
            output += f"📍 {name} (ID: {exchange_id})\n"
            if working_schedules:
                output += "   Trading Hours:\n"
                for schedule in working_schedules[:3]:
                    output += f"   - {schedule.get('openTime', 'N/A')} to {schedule.get('closeTime', 'N/A')}\n"
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def search_instruments(query: str = "") -> str:
    """Search for tradable instruments (stocks, ETFs) by name or ticker symbol."""
    if not query.strip():
        return "❌ Error: Search query is required"
    
    logger.info(f"Searching instruments for: {query}")
    
    try:
        result = await make_request("GET", "/equity/metadata/instruments")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        query_lower = query.lower()
        matches = [
            inst for inst in result 
            if query_lower in inst.get('ticker', '').lower() or 
               query_lower in inst.get('name', '').lower()
        ]
        
        if not matches:
            return f"🔍 No instruments found matching '{query}'"
        
        output = f"🔍 Search Results for '{query}':\n\n"
        for inst in matches[:10]:
            ticker = inst.get('ticker', 'N/A')
            name = inst.get('name', 'N/A')
            currency = inst.get('currencyCode', 'N/A')
            inst_type = inst.get('type', 'N/A')
            
            output += f"📊 {ticker} - {name}\n"
            output += f"   Type: {inst_type} | Currency: {currency}\n\n"
        
        if len(matches) > 10:
            output += f"... and {len(matches) - 10} more results\n"
        
        return output
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_active_orders() -> str:
    """List all active (pending) orders in your Trading212 account."""
    logger.info("Fetching active orders")
    
    try:
        result = await make_request("GET", "/equity/orders")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        if not result:
            return "📋 No active orders"
        
        output = "📋 Active Orders:\n\n"
        for order in result:
            order_id = order.get('id', 'N/A')
            ticker = order.get('ticker', 'N/A')
            order_type = order.get('type', 'N/A')
            quantity = order.get('quantity', 0)
            limit_price = order.get('limitPrice', 0)
            stop_price = order.get('stopPrice', 0)
            status = order.get('status', 'N/A')
            created = order.get('createdOn', 'N/A')
            
            output += f"""⚡ Order #{order_id}
   Ticker: {ticker}
   Type: {order_type}
   Quantity: {quantity}
   Status: {status}"""
            
            if limit_price:
                output += f"\n   Limit Price: {format_currency(limit_price)}"
            if stop_price:
                output += f"\n   Stop Price: {format_currency(stop_price)}"
            
            output += f"\n   Created: {created}\n\n"
        
        return output + f"Environment: {ENVIRONMENT.upper()}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_order(order_id: str = "") -> str:
    """Get detailed information about a specific order by order ID."""
    if not order_id.strip():
        return "❌ Error: Order ID is required"
    
    logger.info(f"Fetching order {order_id}")
    
    try:
        result = await make_request("GET", f"/equity/orders/{order_id}")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        order_id_val = result.get('id', 'N/A')
        ticker = result.get('ticker', 'N/A')
        order_type = result.get('type', 'N/A')
        quantity = result.get('quantity', 0)
        filled_quantity = result.get('filledQuantity', 0)
        limit_price = result.get('limitPrice', 0)
        stop_price = result.get('stopPrice', 0)
        status = result.get('status', 'N/A')
        created = result.get('createdOn', 'N/A')
        
        output = f"""📋 Order Details:

Order ID: {order_id_val}
Ticker: {ticker}
Type: {order_type}
Status: {status}

Quantities:
- Requested: {quantity}
- Filled: {filled_quantity}
"""
        
        if limit_price:
            output += f"Limit Price: {format_currency(limit_price)}\n"
        if stop_price:
            output += f"Stop Price: {format_currency(stop_price)}\n"
        
        output += f"Created: {created}\n"
        output += f"\nEnvironment: {ENVIRONMENT.upper()}"
        
        return output
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def place_market_order(ticker: str = "", quantity: str = "") -> str:
    """Place a market order to buy or sell a stock (positive quantity = buy, negative = sell). Only works for LIVE environment."""
    if not ticker.strip():
        return "❌ Error: Ticker symbol is required"
    if not quantity.strip():
        return "❌ Error: Quantity is required"
    
    logger.info(f"Placing market order: {ticker} x {quantity}")
    
    try:
        quantity_float = float(quantity)
        
        order_data = {
            "ticker": ticker,
            "quantity": quantity_float
        }
        
        import json
        result = await make_request("POST", "/equity/orders/market", json.dumps(order_data))
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        order_id = result.get('id', 'N/A')
        status = result.get('status', 'N/A')
        
        return f"""✅ Market Order Placed:

Order ID: {order_id}
Ticker: {ticker}
Quantity: {quantity_float}
Status: {status}
Type: MARKET

Environment: {ENVIRONMENT.upper()}"""
    except ValueError:
        return f"❌ Error: Invalid quantity value: {quantity}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def place_limit_order(ticker: str = "", quantity: str = "", limit_price: str = "", time_validity: str = "DAY") -> str:
    """Place a limit order to buy or sell at a specific price (positive quantity = buy, negative = sell)."""
    if not ticker.strip():
        return "❌ Error: Ticker symbol is required"
    if not quantity.strip():
        return "❌ Error: Quantity is required"
    if not limit_price.strip():
        return "❌ Error: Limit price is required"
    
    logger.info(f"Placing limit order: {ticker} x {quantity} @ {limit_price}")
    
    try:
        quantity_float = float(quantity)
        limit_price_float = float(limit_price)
        
        order_data = {
            "ticker": ticker,
            "quantity": quantity_float,
            "limitPrice": limit_price_float,
            "timeValidity": time_validity
        }
        
        import json
        result = await make_request("POST", "/equity/orders/limit", json.dumps(order_data))
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        order_id = result.get('id', 'N/A')
        status = result.get('status', 'N/A')
        
        return f"""✅ Limit Order Placed:

Order ID: {order_id}
Ticker: {ticker}
Quantity: {quantity_float}
Limit Price: {format_currency(limit_price_float)}
Time Validity: {time_validity}
Status: {status}

Environment: {ENVIRONMENT.upper()}"""
    except ValueError:
        return f"❌ Error: Invalid numeric value"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def place_stop_order(ticker: str = "", quantity: str = "", stop_price: str = "", time_validity: str = "DAY") -> str:
    """Place a stop order that triggers a market order when price reaches stop price (positive = buy stop, negative = sell/stop-loss)."""
    if not ticker.strip():
        return "❌ Error: Ticker symbol is required"
    if not quantity.strip():
        return "❌ Error: Quantity is required"
    if not stop_price.strip():
        return "❌ Error: Stop price is required"
    
    logger.info(f"Placing stop order: {ticker} x {quantity} @ {stop_price}")
    
    try:
        quantity_float = float(quantity)
        stop_price_float = float(stop_price)
        
        order_data = {
            "ticker": ticker,
            "quantity": quantity_float,
            "stopPrice": stop_price_float,
            "timeValidity": time_validity
        }
        
        import json
        result = await make_request("POST", "/equity/orders/stop", json.dumps(order_data))
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        order_id = result.get('id', 'N/A')
        status = result.get('status', 'N/A')
        
        return f"""✅ Stop Order Placed:

Order ID: {order_id}
Ticker: {ticker}
Quantity: {quantity_float}
Stop Price: {format_currency(stop_price_float)}
Time Validity: {time_validity}
Status: {status}

Environment: {ENVIRONMENT.upper()}"""
    except ValueError:
        return f"❌ Error: Invalid numeric value"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def cancel_order(order_id: str = "") -> str:
    """Cancel an active order by order ID."""
    if not order_id.strip():
        return "❌ Error: Order ID is required"
    
    logger.info(f"Cancelling order {order_id}")
    
    try:
        result = await make_request("DELETE", f"/equity/orders/{order_id}")
        
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        return f"✅ Order {order_id} cancelled successfully\n\nEnvironment: {ENVIRONMENT.upper()}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_order_history(ticker: str = "", limit: str = "50") -> str:
    """Get historical orders with optional ticker filter and limit (max 50)."""
    logger.info("Fetching order history")
    
    try:
        limit_int = min(int(limit) if limit.strip() else 50, 50)
        
        endpoint = f"/equity/history/orders?limit={limit_int}"
        if ticker.strip():
            endpoint += f"&ticker={ticker}"
        
        result = await make_request("GET", endpoint)
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        if not result or not result.get('items'):
            return "📋 No order history found"
        
        output = "📋 Order History:\n\n"
        for order in result.get('items', []):
            order_id = order.get('id', 'N/A')
            ticker_val = order.get('ticker', 'N/A')
            order_type = order.get('type', 'N/A')
            quantity = order.get('filledQuantity', order.get('quantity', 0))
            fill_price = order.get('fillPrice', 0)
            status = order.get('status', 'N/A')
            created = order.get('dateCreated', 'N/A')
            
            output += f"""📊 {ticker_val} - {order_type}
   Order ID: {order_id}
   Quantity: {quantity}
   Fill Price: {format_currency(fill_price) if fill_price else 'N/A'}
   Status: {status}
   Date: {created}
   
"""
        
        return output + f"Environment: {ENVIRONMENT.upper()}"
    except ValueError:
        return f"❌ Error: Invalid limit value: {limit}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_dividends(ticker: str = "", limit: str = "50") -> str:
    """Get dividend payment history with optional ticker filter."""
    logger.info("Fetching dividend history")
    
    try:
        limit_int = min(int(limit) if limit.strip() else 50, 50)
        
        endpoint = f"/history/dividends?limit={limit_int}"
        if ticker.strip():
            endpoint += f"&ticker={ticker}"
        
        result = await make_request("GET", endpoint)
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        if not result or not result.get('items'):
            return "💰 No dividend history found"
        
        output = "💰 Dividend History:\n\n"
        total = 0
        for dividend in result.get('items', []):
            ticker_val = dividend.get('ticker', 'N/A')
            amount = dividend.get('amount', 0)
            amount_in_euro = dividend.get('amountInEuro', 0)
            paid_on = dividend.get('paidOn', 'N/A')
            dividend_type = dividend.get('type', 'N/A')
            quantity = dividend.get('quantity', 0)
            
            output += f"""💵 {ticker_val}
   Amount: {format_currency(amount)}
   Quantity: {quantity}
   Type: {dividend_type}
   Paid On: {paid_on}
   
"""
            total += amount
        
        output += f"\n💰 Total Dividends: {format_currency(total)}\n"
        output += f"Environment: {ENVIRONMENT.upper()}"
        
        return output
    except ValueError:
        return f"❌ Error: Invalid limit value: {limit}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_transactions(limit: str = "50") -> str:
    """Get recent account transactions (deposits, withdrawals, fees, etc)."""
    logger.info("Fetching transactions")
    
    try:
        limit_int = min(int(limit) if limit.strip() else 50, 50)
        
        result = await make_request("GET", f"/history/transactions?limit={limit_int}")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        if not result or not result.get('items'):
            return "📊 No transactions found"
        
        output = "📊 Recent Transactions:\n\n"
        for transaction in result.get('items', []):
            trans_type = transaction.get('type', 'N/A')
            amount = transaction.get('amount', 0)
            date_time = transaction.get('dateTime', 'N/A')
            reference = transaction.get('reference', 'N/A')
            
            output += f"""💳 {trans_type}
   Amount: {format_currency(amount)}
   Date: {date_time}
   Reference: {reference}
   
"""
        
        return output + f"Environment: {ENVIRONMENT.upper()}"
    except ValueError:
        return f"❌ Error: Invalid limit value: {limit}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def list_pies() -> str:
    """List all investment pies (custom portfolios) in your Trading212 account."""
    logger.info("Fetching pies")
    
    try:
        result = await make_request("GET", "/equity/pies")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        if not result:
            return "🥧 No pies found"
        
        output = "🥧 Investment Pies:\n\n"
        for pie in result:
            pie_id = pie.get('id', 'N/A')
            name = pie.get('name', 'N/A')
            status = pie.get('status', 'N/A')
            goal = pie.get('goal', 0)
            result_val = pie.get('result', 0)
            instruments_count = len(pie.get('instruments', []))
            
            output += f"""📊 {name} (ID: {pie_id})
   Status: {status}
   Instruments: {instruments_count}
   Goal: {format_currency(goal)}
   Result: {format_currency(result_val)}
   
"""
        
        return output + f"Environment: {ENVIRONMENT.upper()}"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_pie(pie_id: str = "") -> str:
    """Get detailed information about a specific investment pie by ID."""
    if not pie_id.strip():
        return "❌ Error: Pie ID is required"
    
    logger.info(f"Fetching pie {pie_id}")
    
    try:
        result = await make_request("GET", f"/equity/pies/{pie_id}")
        if isinstance(result, str) and result.startswith("❌"):
            return result
        
        pie_id_val = result.get('id', 'N/A')
        name = result.get('name', 'N/A')
        status = result.get('status', 'N/A')
        goal = result.get('goal', 0)
        result_val = result.get('result', 0)
        cash = result.get('cash', 0)
        dividend_action = result.get('dividendCashAction', 'N/A')
        instruments = result.get('instruments', [])
        
        output = f"""🥧 Pie Details: {name}

ID: {pie_id_val}
Status: {status}

💰 Finances:
- Goal: {format_currency(goal)}
- Result: {format_currency(result_val)}
- Cash: {format_currency(cash)}
- Dividend Action: {dividend_action}

📊 Holdings ({len(instruments)} instruments):
"""
        
        for inst in instruments:
            ticker = inst.get('ticker', 'N/A')
            shares = inst.get('shares', 0)
            expected_share = inst.get('expectedShare', 0)
            output += f"  • {ticker}: {shares} shares ({expected_share}%)\n"
        
        output += f"\nEnvironment: {ENVIRONMENT.upper()}"
        
        return output
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Trading212 MCP server...")
    
    if not API_KEY:
        logger.warning("TRADING212_API_KEY not set")
    if not API_SECRET:
        logger.warning("TRADING212_API_SECRET not set")
    
    logger.info(f"Environment: {ENVIRONMENT.upper()} ({get_base_url()})")
    
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)