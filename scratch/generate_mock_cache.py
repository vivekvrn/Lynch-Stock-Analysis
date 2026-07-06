import os
import json
from datetime import datetime, timedelta

STOCK_UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX"]
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache")

# Custom baseline data for each stock to make them realistic
BASE_METRICS = {
    "AAPL": {"pe": 28.5, "peg": 1.45, "mcap": 3000000000000, "debt": 95000000000, "cash": 160000000000, "growth": 8.0, "ebit_trend": "stable", "rev_trend": "stable", "buy_pct": 72.0, "roe_trend": "stable", "eps_revision": "no_change"},
    "MSFT": {"pe": 32.0, "peg": 1.60, "mcap": 3200000000000, "debt": 75000000000, "cash": 110000000000, "growth": 12.0, "ebit_trend": "expanding", "rev_trend": "stable", "buy_pct": 82.0, "roe_trend": "improving", "eps_revision": "upward"},
    "GOOGL": {"pe": 23.5, "peg": 1.10, "mcap": 2000000000000, "debt": 28000000000, "cash": 120000000000, "growth": 14.0, "ebit_trend": "expanding", "rev_trend": "accel", "buy_pct": 78.0, "roe_trend": "improving", "eps_revision": "upward"},
    "AMZN": {"pe": 40.0, "peg": 1.25, "mcap": 1900000000000, "debt": 130000000000, "cash": 85000000000, "growth": 18.0, "ebit_trend": "stable", "rev_trend": "accel", "buy_pct": 85.0, "roe_trend": "improving", "eps_revision": "upward"},
    "NVDA": {"pe": 65.0, "peg": 0.45, "mcap": 2800000000000, "debt": 11000000000, "cash": 35000000000, "growth": 45.0, "ebit_trend": "expanding", "rev_trend": "accel", "buy_pct": 92.0, "roe_trend": "improving", "eps_revision": "upward"},
    "META": {"pe": 24.0, "peg": 0.95, "mcap": 1200000000000, "debt": 18000000000, "cash": 65000000000, "growth": 16.0, "ebit_trend": "expanding", "rev_trend": "stable", "buy_pct": 79.0, "roe_trend": "improving", "eps_revision": "upward"},
    "TSLA": {"pe": 55.0, "peg": 2.20, "mcap": 600000000000, "debt": 5000000000, "cash": 26000000000, "growth": 10.0, "ebit_trend": "declining", "rev_trend": "decel", "buy_pct": 45.0, "roe_trend": "declining", "eps_revision": "downward"},
    "NFLX": {"pe": 36.0, "peg": 1.15, "mcap": 270000000000, "debt": 14000000000, "cash": 7000000000, "growth": 15.0, "ebit_trend": "stable", "rev_trend": "stable", "buy_pct": 65.0, "roe_trend": "stable", "eps_revision": "no_change"}
}

def generate_mock_data():
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"Generating mock cache in: {CACHE_DIR}")
    
    today = datetime.today()
    
    for symbol, base in BASE_METRICS.items():
        print(f"Generating cache files for {symbol}...")
        
        # Calculate rating counts based on buy_pct
        buy_pct = base["buy_pct"]
        strong_buy = int(buy_pct * 0.4)
        buy = int(buy_pct * 0.6)
        hold = int((100 - buy_pct) * 0.7)
        sell = int((100 - buy_pct) * 0.2)
        strong_sell = int((100 - buy_pct) * 0.1)
        
        # 1. OVERVIEW
        overview = {
            "Symbol": symbol,
            "AssetType": "Common Stock",
            "Name": f"{symbol} Inc. Mock Company",
            "MarketCapitalization": str(base["mcap"]),
            "PERatio": str(base["pe"]),
            "PEGRatio": str(base["peg"]),
            "BookValue": "75.5",
            "EPS": str(round(base["mcap"] / base["pe"] / 1000000000, 2)),
            "52WeekHigh": str(round(base["mcap"] / 10000000000 * 1.1, 2)),
            "AnalystTargetPrice": str(round(base["mcap"] / 10000000000 * 1.25, 2)),
            "AnalystRatingStrongBuy": str(strong_buy),
            "AnalystRatingBuy": str(buy),
            "AnalystRatingHold": str(hold),
            "AnalystRatingSell": str(sell),
            "AnalystRatingStrongSell": str(strong_sell)
        }
        with open(os.path.join(CACHE_DIR, f"{symbol}_OVERVIEW.json"), "w") as f:
            json.dump(overview, f, indent=2)
            
        # 2. BALANCE SHEET
        # Generate 3 years of historical shareholder equity for ROE Trend calculation
        annual_BS_reports = []
        for i in range(3):
            year = 2025 - i
            equity_factor = 0.95 ** i
            annual_BS_reports.append({
                "fiscalDateEnding": f"{year}-12-31",
                "reportedCurrency": "USD",
                "cashAndCashEquivalentsAtCarryingValue": str(base["cash"]),
                "shortTermInvestments": str(int(base["cash"] * 0.3)),
                "longTermDebt": str(base["debt"]),
                "shortTermDebt": str(int(base["debt"] * 0.1)),
                "totalShareholderEquity": str(int(base["mcap"] * 0.15 * equity_factor))
            })
            
        balance_sheet = {
            "symbol": symbol,
            "annualReports": annual_BS_reports,
            "quarterlyReports": []
        }
        with open(os.path.join(CACHE_DIR, f"{symbol}_BALANCE_SHEET.json"), "w") as f:
            json.dump(balance_sheet, f, indent=2)
            
        # 3. INCOME STATEMENT
        # Generate 6 years of annual reports for Agent 1 and 8 quarters of quarterly reports for Agent 2
        annual_IS_reports = []
        rev_current = base["mcap"] * 0.12 # assume 12% revenue to mcap
        net_current = rev_current * 0.22 # assume 22% net margin
        
        # Annual reports
        for i in range(6):
            year = 2025 - i
            growth_factor = (1 + (base["growth"] / 100)) ** i
            rev = int(rev_current / growth_factor)
            
            # Mock net margin based on ROE Trend (improving/stable/declining)
            net_factor = 1.0
            if base["roe_trend"] == "improving" and i > 0:
                net_factor = 0.95 ** i
            elif base["roe_trend"] == "declining" and i > 0:
                net_factor = 1.05 ** i
                
            net = int(net_current * net_factor / growth_factor)
            
            annual_IS_reports.append({
                "fiscalDateEnding": f"{year}-12-31",
                "reportedCurrency": "USD",
                "totalRevenue": str(rev),
                "netIncome": str(net)
            })
            
        # Quarterly reports (last 8 quarters, index 0 is latest Q1)
        quarterly_IS_reports = []
        q_rev_base = rev_current / 4
        
        for q in range(8):
            q_date = today - timedelta(days=90 * q)
            q_str = q_date.strftime("%Y-%m-%d")
            
            # Revenue trend: accel, stable, decel
            rev_factor = 1.0
            if base["rev_trend"] == "accel":
                # Accelerating QoQ: Q1 > Q2 > Q3 > Q4 (reverse order in loop)
                rev_factor = 1.03 ** (8 - q)
            elif base["rev_trend"] == "decel":
                rev_factor = 0.96 ** (8 - q)
            else:
                rev_factor = 1.01 ** (8 - q)
                
            q_rev = int(q_rev_base * rev_factor)
            
            # EBIT / Operating Income trend: expanding, stable, declining
            ebit_margin = 0.20 # 20% baseline
            if base["ebit_trend"] == "expanding":
                # Margin expands as we go to latest quarters (q decreases)
                ebit_margin = 0.24 - (0.02 * q) # Q1: 24%, Q2: 22%, Q3: 20%, Q4: 18%...
            elif base["ebit_trend"] == "declining":
                ebit_margin = 0.15 + (0.02 * q) # Q1: 15%, Q2: 17%, Q3: 19%...
            else:
                ebit_margin = 0.20 # Q1-Q8 stable
                
            q_op_inc = int(q_rev * ebit_margin)
            
            quarterly_IS_reports.append({
                "fiscalDateEnding": q_str,
                "reportedCurrency": "USD",
                "totalRevenue": str(q_rev),
                "operatingIncome": str(q_op_inc),
                "netIncome": str(int(q_op_inc * 0.7))
            })
            
        income_statement = {
            "symbol": symbol,
            "annualReports": annual_IS_reports,
            "quarterlyReports": quarterly_IS_reports
        }
        with open(os.path.join(CACHE_DIR, f"{symbol}_INCOME_STATEMENT.json"), "w") as f:
            json.dump(income_statement, f, indent=2)
            
        # 4. CASH FLOW
        cash_flow = {
            "symbol": symbol,
            "annualReports": [
                {
                    "fiscalDateEnding": "2025-12-31",
                    "reportedCurrency": "USD",
                    "operatingCashflow": str(int(net_current * 1.15))
                }
            ],
            "quarterlyReports": []
        }
        with open(os.path.join(CACHE_DIR, f"{symbol}_CASH_FLOW.json"), "w") as f:
            json.dump(cash_flow, f, indent=2)
            
        # 5. TIME_SERIES_MONTHLY & 6. EARNINGS
        monthly_time_series = {}
        quarterly_earnings = []
        
        baseline_price = base["mcap"] / 10000000000
        baseline_eps = baseline_price / base["pe"]
        
        for m in range(60):
            m_date = today - timedelta(days=30 * m)
            m_str = m_date.strftime("%Y-%m-%d")
            growth_factor = (1 + (base["growth"] / 100)) ** (m / 12)
            price = baseline_price / growth_factor
            monthly_time_series[m_str] = {
                "4. close": str(round(price, 2))
            }
            
        # Generate quarterly earnings with estimatedEPS
        for q in range(24):
            q_date = today - timedelta(days=90 * q)
            q_str = q_date.strftime("%Y-%m-%d")
            
            growth_factor = (1 + (base["growth"] / 100)) ** (q / 4)
            reported_eps = (baseline_eps / 4) / growth_factor
            
            # EPS Revision Trend: upward, downward, no_change
            eps_factor = 1.0
            if base["eps_revision"] == "upward":
                # Estimates rising as we approach Q1 (q decreases)
                eps_factor = 1.02 ** (24 - q)
            elif base["eps_revision"] == "downward":
                eps_factor = 0.98 ** (24 - q)
                
            est_eps = reported_eps * eps_factor * 0.95 # estimated usually slightly lower than reported for positive surprises
            
            quarterly_earnings.append({
                "fiscalDateEnding": q_str,
                "reportedEPS": str(round(reported_eps, 4)),
                "estimatedEPS": str(round(est_eps, 4)),
                "surprise": str(round(reported_eps - est_eps, 4)),
                "surprisePercentage": str(round(((reported_eps - est_eps)/est_eps)*100, 4)) if est_eps else "0.0"
            })
            
        monthly_prices = {
            "Meta Data": {},
            "Monthly Time Series": monthly_time_series
        }
        with open(os.path.join(CACHE_DIR, f"{symbol}_TIME_SERIES_MONTHLY.json"), "w") as f:
            json.dump(monthly_prices, f, indent=2)
            
        earnings = {
            "symbol": symbol,
            "annualEarnings": [],
            "quarterlyEarnings": quarterly_earnings
        }
        with open(os.path.join(CACHE_DIR, f"{symbol}_EARNINGS.json"), "w") as f:
            json.dump(earnings, f, indent=2)
            
    print("Mock cache generation complete!")

if __name__ == "__main__":
    generate_mock_data()
