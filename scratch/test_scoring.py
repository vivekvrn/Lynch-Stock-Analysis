import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.quant_agent import perform_lynch_analysis

def main():
    print("=" * 60)
    print("Testing Peter Lynch Scoring Calculations locally (Cache-only)")
    print("=" * 60)
    
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX"]
    results = []
    
    for symbol in symbols:
        try:
            metrics = perform_lynch_analysis(symbol)
            print(f"\n[Test] Stock: {symbol}")
            print(f"  Current Price: {metrics.get('current_price')}")
            print(f"  Current PE: {metrics.get('pe_current')}")
            print(f"  5yr Median PE: {metrics.get('pe_5yr_median')}")
            print(f"  PEG Ratio: {metrics.get('peg_ratio')}")
            print(f"  Debt/Equity: {round(metrics.get('debt_equity'), 3)}")
            print(f"  Revenue CAGR (5yr): {round(metrics.get('revenue_cagr_5yr'), 2)}%")
            print(f"  Net Cash % Mkt Cap: {round(metrics.get('net_cash_pct_mcap'), 2)}%")
            print(f"  FCF Conversion: {round(metrics.get('fcf_conversion'), 2)}%")
            print(f"  Scores: {metrics.get('scores')}")
            print(f"  Total Quant Score: {metrics.get('quant_score')}/60")
            print(f"  Lynch Category: {metrics.get('lynch_category')}")
            results.append(metrics)
        except Exception as e:
            print(f"[Test] Failed for {symbol}: {e}")
            
    # Save the output directly as scored_quant.json so it serves as a valid run output
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scored_quant.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "=" * 60)
    print(f"Scoring test complete! Results written to: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
