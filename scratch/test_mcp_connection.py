import asyncio
import os
import traceback
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession

load_dotenv()

async def test_conn():
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        print("[Error] ALPHAVANTAGE_API_KEY is not set.")
        return
        
    url = f"https://mcp.alphavantage.co/mcp?apikey={api_key}"
    print(f"Connecting to: {url}")
    
    try:
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Initialized successfully!")
                tools_res = await session.list_tools()
                print(f"Tools: {[t.name for t in tools_res.tools]}")
    except Exception as e:
        print("Exception caught:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conn())
