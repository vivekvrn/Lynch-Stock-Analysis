import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.kpi_agent import perform_kpi_analysis

def main():
    print("=" * 60)
    print("Testing KPI Scorer locally (Cache-only)")
    print("=" * 60)
    
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX"]
    results = []
    
    for symbol in symbols:
        try:
            metrics = perform_kpi_analysis(symbol)
            print(f"\n[Test] Stock: {symbol}")
            print(f"  EBIT Margin Trend: {metrics.get('ebit_margin_trend')}")
            print(f"  Revenue Growth Trend: {metrics.get('revenue_trend')}")
            print(f"  Analyst Buy %: {metrics.get('analyst_buy_pct')}%")
            print(f"  Analyst Consensus: {metrics.get('analyst_consensus')}")
            print(f"  ROE Trend: {metrics.get('roe_trend')}")
            print(f"  EPS Revision: {metrics.get('eps_revision')}")
            print(f"  Scores: {metrics.get('scores')}")
            print(f"  Total KPI Score: {metrics.get('kpi_score')}/40")
            results.append(metrics)
        except Exception as e:
            print(f"[Test] Failed for {symbol}: {e}")
            
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scored_kpi.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "=" * 60)
    print(f"KPI test complete! Results written to: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
