import os
import json
import time
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache")

FUNCTION_TO_MCP_TOOL = {
    "OVERVIEW": "COMPANY_OVERVIEW",
    "BALANCE_SHEET": "BALANCE_SHEET",
    "INCOME_STATEMENT": "INCOME_STATEMENT",
    "CASH_FLOW": "CASH_FLOW",
    "TIME_SERIES_MONTHLY": "TIME_SERIES_MONTHLY",
    "EARNINGS": "EARNINGS"
}

def _get_api_key():
    """Retrieve Alpha Vantage API Key from environment."""
    return os.getenv("ALPHAVANTAGE_API_KEY", "DEMO_KEY")

async def _call_mcp_server(tool_name, arguments):
    api_key = _get_api_key()
    server_params = StdioServerParameters(
        command="uvx",
        args=["--from", "marketdata-mcp-server", "marketdata-mcp", api_key],
        env=os.environ.copy()
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.call_tool("TOOL_CALL", arguments={
                "tool_name": tool_name,
                "arguments": arguments
            })
            if response.isError:
                print(f"[AlphaVantage MCP] Tool call error: {response.content}")
                return {}
            try:
                text_content = response.content[0].text
                return json.loads(text_content)
            except Exception as e:
                print(f"[AlphaVantage MCP] Failed to parse response JSON: {e}")
                return {}

def _fetch_from_api(params):
    """
    Perform a request to Alpha Vantage using the MCP server.
    """
    time.sleep(0.5) # Sleep 0.5s to respect rate limits
    
    api_function = params.get("function")
    mcp_tool = FUNCTION_TO_MCP_TOOL.get(api_function, api_function)
    
    symbol = params.get("symbol")
    arguments = {"symbol": symbol}
    
    # Copy other arguments if they exist
    for k, v in params.items():
        if k not in ["function", "symbol", "apikey"]:
            arguments[k] = v
            
    print(f"[AlphaVantage MCP] Fetching: {mcp_tool} for {symbol}")
    
    try:
        data = asyncio.run(_call_mcp_server(mcp_tool, arguments))
    except Exception as e:
        print(f"[AlphaVantage MCP] Connection/Execution failed: {e}")
        data = {}
        
    return data

import re

def sanitize_free_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    # Strip HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Defense against indirect prompt injections
    injection_patterns = [
        r'(?i)ignore\s+previous\s+instructions',
        r'(?i)ignore\s+all\s+instructions',
        r'(?i)you\s+must\s+now',
        r'(?i)system\s+command',
        r'(?i)instead\s+of\s+doing',
        r'(?i)override\s+rules'
    ]
    for pattern in injection_patterns:
        text = re.sub(pattern, '[REDACTED_POTENTIAL_INJECTION]', text)
    # Truncate to safe length
    return text[:1000]

def sanitize_dict_strings(data):
    if isinstance(data, dict):
        return {k: sanitize_dict_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict_strings(v) for v in data]
    elif isinstance(data, str):
        return sanitize_free_text(data)
    return data

def _get_cached_data(symbol, function, params_builder):
    """
    Get data from local JSON cache if available.
    Otherwise fetch from API and save to cache.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{symbol.upper()}_{function.upper()}.json")
    
    data = None
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cached_content = json.load(f)
                # Ensure it's not a rate-limit note or error message saved by accident
                if "Note" not in cached_content and "Error Message" not in cached_content and cached_content:
                    # print(f"[Cache] Hit for {symbol} - {function}")
                    data = cached_content
        except Exception as e:
            print(f"[Cache] Error reading cache file {cache_file}: {e}")
            
    if data is None:
        # Cache miss or invalid cache: fetch from API
        params = params_builder()
        params["apikey"] = _get_api_key()
        data = _fetch_from_api(params)
        
        # Only save to cache if we got a valid response without warnings/errors
        if data and "Note" not in data and "Error Message" not in data:
            try:
                with open(cache_file, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"[Cache] Saved for {symbol} - {function}")
            except Exception as e:
                print(f"[Cache] Error writing cache file {cache_file}: {e}")
                
    return sanitize_dict_strings(data)

# Exported Tool Functions

def get_company_overview(symbol: str) -> dict:
    """
    Fetch general company overview and valuation ratios (including PE, PEG, Market Cap).
    """
    def builder():
        return {"function": "OVERVIEW", "symbol": symbol}
    return _get_cached_data(symbol, "OVERVIEW", builder)

def get_balance_sheet(symbol: str) -> dict:
    """
    Fetch company balance sheet containing historical assets, liabilities, debt, and equity.
    """
    def builder():
        return {"function": "BALANCE_SHEET", "symbol": symbol}
    return _get_cached_data(symbol, "BALANCE_SHEET", builder)

def get_income_statement(symbol: str) -> dict:
    """
    Fetch company income statement containing historical revenues and net incomes.
    """
    def builder():
        return {"function": "INCOME_STATEMENT", "symbol": symbol}
    return _get_cached_data(symbol, "INCOME_STATEMENT", builder)

def get_cash_flow(symbol: str) -> dict:
    """
    Fetch company cash flow statement containing historical operating cash flow.
    """
    def builder():
        return {"function": "CASH_FLOW", "symbol": symbol}
    return _get_cached_data(symbol, "CASH_FLOW", builder)

def get_monthly_prices(symbol: str) -> dict:
    """
    Fetch historical monthly price series to calculate long-term historical price trends.
    """
    def builder():
        return {"function": "TIME_SERIES_MONTHLY", "symbol": symbol}
    return _get_cached_data(symbol, "TIME_SERIES_MONTHLY", builder)

def get_earnings(symbol: str) -> dict:
    """
    Fetch historical quarterly and annual earnings per share (EPS).
    """
    def builder():
        return {"function": "EARNINGS", "symbol": symbol}
    return _get_cached_data(symbol, "EARNINGS", builder)
