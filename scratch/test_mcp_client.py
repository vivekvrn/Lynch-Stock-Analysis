import asyncio
import os
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

async def main():
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        print("ALPHAVANTAGE_API_KEY is not set in environment or .env file.")
        return

    print("Connecting to Alpha Vantage MCP server...")
    server_params = StdioServerParameters(
        command="uvx",
        args=["--from", "marketdata-mcp-server", "marketdata-mcp", api_key],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Session initialized successfully!")
            
            # Test calling a tool using TOOL_CALL with the correct nested arguments structure
            print("\nCalling COMPANY_OVERVIEW for AAPL via TOOL_CALL (nested arguments)...")
            call_res = await session.call_tool("TOOL_CALL", arguments={
                "tool_name": "COMPANY_OVERVIEW",
                "arguments": {
                    "symbol": "AAPL"
                }
            })
            print("TOOL_CALL status error:", call_res.isError)
            print("TOOL_CALL output content:")
            try:
                # Parse as JSON if possible to verify
                data = json.loads(call_res.content[0].text)
                print(json.dumps(data, indent=2)[:500])
            except Exception as e:
                print(call_res.content[0].text[:500])

if __name__ == "__main__":
    asyncio.run(main())
