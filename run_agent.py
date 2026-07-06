import os
import json
import asyncio
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from agent.quant_agent import create_quant_agent

load_dotenv()

STOCK_UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX"]
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "data", "scored_quant.json")

def extract_json_from_events(events):
    """
    Extract the final text output from the event stream and attempt to parse it
    as a JSON object.
    """
    text_content = ""
    for event in events:
        # Check if the event has content and parts
        if event.content and hasattr(event.content, "parts") and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    text_content += part.text
                    
    # Clean up the output string to find the JSON block
    text_content = text_content.strip()
    if not text_content:
        return None
        
    # Attempt to extract JSON from markdown code block if present
    if "```json" in text_content:
        try:
            block = text_content.split("```json")[1].split("```")[0].strip()
            return json.loads(block)
        except Exception:
            pass
            
    # Try parsing the entire content directly
    try:
        return json.loads(text_content)
    except json.JSONDecodeError:
        print(f"[Warning] Failed to parse raw text directly as JSON: {text_content[:200]}...")
        
    return None

async def run_pipeline():
    # Ensure GOOGLE_API_KEY is present
    if not os.getenv("GOOGLE_API_KEY"):
        print("[Error] GOOGLE_API_KEY is not set in the environment or .env file.")
        return
        
    print("=" * 60)
    print("Starting Peter Lynch NASDAQ Stock Analysis Pipeline (Phase 1)")
    print(f"Stocks to analyse: {', '.join(STOCK_UNIVERSE)}")
    print("=" * 60)
    
    agent = create_quant_agent()
    runner = InMemoryRunner(agent=agent)
    
    results = []
    
    for symbol in STOCK_UNIVERSE:
        print(f"\n[Pipeline] Analysing {symbol}...")
        prompt = f"Run Peter Lynch quantitative analysis for stock symbol: {symbol}"
        
        try:
            # InMemoryRunner.run_debug is a coroutine and returns a list of Events
            events = await runner.run_debug(prompt)
            
            # Extract JSON output
            data = extract_json_from_events(events)
            
            if data:
                print(f"[Pipeline] Success! {symbol} Score: {data.get('quant_score')}/60 | Category: {data.get('lynch_category')}")
                results.append(data)
            else:
                print(f"[Pipeline] Error: Could not extract structured JSON output for {symbol}.")
                
        except Exception as e:
            print(f"[Pipeline] Failed to process {symbol}: {e}")
            
    # Save results to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    try:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)
        print("\n" + "=" * 60)
        print(f"Pipeline complete! Output written to: {OUTPUT_FILE}")
        print("=" * 60)
    except Exception as e:
        print(f"[Pipeline] Failed to save output to {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    import sys
    if "--server" in sys.argv:
        import uvicorn
        print("Starting FastAPI Backend Server at http://127.0.0.1:8000...")
        uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
    else:
        asyncio.run(run_pipeline())
