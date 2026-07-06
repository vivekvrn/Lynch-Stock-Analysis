import numpy as np
from datetime import datetime

def parse_float(val, default=0.0):
    """Safely parse a string value to float, handling 'None' or invalid inputs."""
    if val is None or str(val).strip().lower() in ("none", "null", "-", ""):
        return default
    try:
        return float(val)
    except ValueError:
        return default

def calculate_debt_equity(balance_sheet):
    """
    Calculate Debt/Equity ratio.
    D/E = Long-term Debt / Equity.
    """
    reports = balance_sheet.get("annualReports", [])
    if not reports:
        reports = balance_sheet.get("quarterlyReports", [])
        
    if not reports:
        return 0.0, 0 # returns score=0, value=0.0
        
    latest = reports[0]
    long_term_debt = parse_float(latest.get("longTermDebt"))
    shareholder_equity = parse_float(latest.get("totalShareholderEquity"))
    
    if shareholder_equity <= 0:
        return 999.0, 0 # High D/E if equity is negative/zero
        
    de_ratio = long_term_debt / shareholder_equity
    
    # Scoring: <0.3=12 | 0.3-0.5=9 | 0.5-0.8=5 | >0.8=0
    if de_ratio < 0.3:
        score = 12
    elif de_ratio <= 0.5:
        score = 9
    elif de_ratio <= 0.8:
        score = 5
    else:
        score = 0
        
    return de_ratio, score

def calculate_revenue_cagr(income_statement):
    """
    Calculate 5-year Revenue CAGR.
    CAGR = (Rev_current / Rev_5yr_ago) ** (1/5) - 1
    """
    reports = income_statement.get("annualReports", [])
    if not reports:
        return 0.0, 0
        
    # Get total revenues in chronological order (earliest first)
    revenues = []
    for r in reversed(reports):
        rev = parse_float(r.get("totalRevenue"))
        if rev > 0:
            revenues.append(rev)
            
    if len(revenues) < 2:
        return 0.0, 0
        
    # Determine the number of periods
    num_years = min(len(revenues) - 1, 5)
    r_start = revenues[-num_years - 1]
    r_end = revenues[-1]
    
    if r_start <= 0 or r_end <= 0:
        return 0.0, 0
        
    cagr = (r_end / r_start) ** (1.0 / num_years) - 1.0
    cagr_pct = cagr * 100
    
    # Scoring: >20%=12 | 15-20%=9 | 10-15%=6 | 5-10%=3 | <5%=0
    if cagr_pct > 20:
        score = 12
    elif cagr_pct >= 15:
        score = 9
    elif cagr_pct >= 10:
        score = 6
    elif cagr_pct >= 5:
        score = 3
    else:
        score = 0
        
    return cagr_pct, score

def calculate_net_cash_pct(balance_sheet, overview):
    """
    Calculate Net Cash % of Market Cap.
    Formula: (Cash - Debt) / Mkt Cap
    Cash = cashAndCashEquivalentsAtCarryingValue + shortTermInvestments
    Debt = longTermDebt + shortTermDebt (or currentDebt)
    """
    reports = balance_sheet.get("annualReports", [])
    if not reports:
        reports = balance_sheet.get("quarterlyReports", [])
        
    mcap = parse_float(overview.get("MarketCapitalization"))
    if not reports or mcap <= 0:
        return 0.0, 0
        
    latest = reports[0]
    cash = parse_float(latest.get("cashAndCashEquivalentsAtCarryingValue")) + parse_float(latest.get("shortTermInvestments"))
    debt = parse_float(latest.get("longTermDebt")) + parse_float(latest.get("shortTermDebt"))
    
    net_cash = cash - debt
    net_cash_pct = (net_cash / mcap) * 100
    
    # Scoring: >20%=6 | 10-20%=4 | 0-10%=2 | Net debt (net_cash <= 0) = 0
    if net_cash <= 0:
        score = 0
    elif net_cash_pct > 20:
        score = 6
    elif net_cash_pct >= 10:
        score = 4
    else:
        score = 2
        
    return net_cash_pct, score

def calculate_fcf_conversion(cash_flow, income_statement):
    """
    Calculate FCF Conversion.
    Formula: Operating Cash Flow / Net Profit
    """
    cf_reports = cash_flow.get("annualReports", [])
    inc_reports = income_statement.get("annualReports", [])
    
    if not cf_reports or not inc_reports:
        return 0.0, 0
        
    ocf = parse_float(cf_reports[0].get("operatingCashflow"))
    net_profit = parse_float(inc_reports[0].get("netIncome"))
    
    if net_profit <= 0:
        # If profit is negative, check OCF. If OCF is also negative, 0 conversion.
        # If OCF is positive but profit is negative, FCF conversion is high but we penalize it as 0 or low due to lack of profit.
        return 0.0, 0
        
    fcf_conv = (ocf / net_profit) * 100
    
    # Scoring: >85%=5 | 70-85%=4 | 55-70%=2 | <55%=0
    if fcf_conv > 85:
        score = 5
    elif fcf_conv >= 70:
        score = 4
    elif fcf_conv >= 55:
        score = 2
    else:
        score = 0
        
    return fcf_conv, score

def calculate_historical_pe_median(monthly_prices, earnings):
    """
    Calculate 5-year historical median PE ratio.
    For each historical month end in the last 60 months:
      - TTM EPS = Sum of last 4 quarters of EPS reported on or before that month end date
      - PE = Month-end Close Price / TTM EPS
    Then find the median PE across all 60 months.
    """
    time_series = monthly_prices.get("Monthly Time Series", {})
    quarterly_earnings = earnings.get("quarterlyEarnings", [])
    
    if not time_series or not quarterly_earnings:
        return None
        
    # Sort monthly prices by date (ascending)
    sorted_months = sorted(time_series.keys())
    # Keep only the last 60 months
    if len(sorted_months) > 60:
        sorted_months = sorted_months[-60:]
        
    pe_ratios = []
    
    # Sort quarterly earnings by fiscal date ending (ascending)
    # Each item has 'fiscalDateEnding' and 'reportedEPS'
    sorted_earnings = []
    for eq in quarterly_earnings:
        try:
            date_obj = datetime.strptime(eq["fiscalDateEnding"], "%Y-%m-%d").date()
            eps = parse_float(eq["reportedEPS"])
            sorted_earnings.append((date_obj, eps))
        except (ValueError, KeyError):
            continue
            
    sorted_earnings.sort(key=lambda x: x[0])
    
    for m_str in sorted_months:
        try:
            m_date = datetime.strptime(m_str, "%Y-%m-%d").date()
            close_price = parse_float(time_series[m_str].get("4. close"))
            
            # Find the TTM EPS for this month: sum of 4 quarters ending on or before m_date
            relevant_quarters = [q for q in sorted_earnings if q[0] <= m_date]
            if len(relevant_quarters) < 4:
                continue
                
            # Get the last 4 quarters
            last_4_quarters = relevant_quarters[-4:]
            ttm_eps = sum(q[1] for q in last_4_quarters)
            
            if ttm_eps > 0 and close_price > 0:
                pe = close_price / ttm_eps
                pe_ratios.append(pe)
        except Exception as e:
            # print(f"Error calculating PE for {m_str}: {e}")
            continue
            
    if not pe_ratios:
        return None
        
    return float(np.median(pe_ratios))

def score_pe_vs_median(current_pe, median_pe):
    """
    Score PE vs 5yr Median.
    Ratio = Current PE / 5yr Median PE.
    Scoring: <0.85=10 | 0.85-1.0=8 | 1.0-1.15=5 | 1.15-1.3=2 | >1.3=0
    """
    if median_pe is None or median_pe <= 0 or current_pe <= 0:
        return 0
        
    ratio = current_pe / median_pe
    
    if ratio < 0.85:
        return 10
    elif ratio <= 1.0:
        return 8
    elif ratio <= 1.15:
        return 5
    elif ratio <= 1.3:
        return 2
    else:
        return 0

def score_peg_ratio(peg_ratio):
    """
    Score PEG Ratio.
    Scoring: <=0.5=15 | 0.5-1.0=12 | 1.0-1.5=8 | 1.5-2.0=4 | >2.0=0
    """
    if peg_ratio <= 0:
        return 0
    elif peg_ratio <= 0.5:
        return 15
    elif peg_ratio <= 1.0:
        return 12
    elif peg_ratio <= 1.5:
        return 8
    elif peg_ratio <= 2.0:
        return 4
    else:
        return 0

def get_lynch_category(peg, de, cagr):
    """
    Categorize stock using Peter Lynch's stock classifications:
    - Fast Grower: High revenue growth (>20% CAGR)
    - Stalwart: Large, solid growth (10-20% CAGR, moderate debt)
    - Slow Grower: Low growth (<5% CAGR)
    - Asset Play: (Placeholder category or other parameters)
    - Turnaround: (High debt or negative growth, but improving - simplified logic here)
    """
    if cagr > 20:
        return "Fast Grower"
    elif cagr >= 10:
        return "Stalwart"
    elif cagr >= 5:
        return "Slow Grower"
    else:
        if de > 1.5:
            return "Turnaround Candidate"
        else:
            return "Slow Grower"

def evaluate_stock_metrics(symbol, overview, balance_sheet, income_statement, cash_flow, monthly_prices, earnings):
    """
    Process all metrics for a given stock and return a dictionary of scores, values,
    and a final Lynch Quantitative score (out of 60).
    """
    # 1. PEG Ratio
    peg_val = parse_float(overview.get("PEGRatio"), default=-1.0)
    peg_score = score_peg_ratio(peg_val)
    
    # 2. Debt / Equity
    de_val, de_score = calculate_debt_equity(balance_sheet)
    
    # 3. Revenue CAGR (5yr)
    cagr_val, cagr_score = calculate_revenue_cagr(income_statement)
    
    # 4. P/E vs 5yr Median
    current_pe = parse_float(overview.get("PERatio"), default=-1.0)
    median_pe = calculate_historical_pe_median(monthly_prices, earnings)
    pe_vs_hist_score = score_pe_vs_median(current_pe, median_pe)
    
    # 5. Net Cash % of Market Cap
    net_cash_pct, net_cash_score = calculate_net_cash_pct(balance_sheet, overview)
    
    # 6. FCF Conversion
    fcf_conv_val, fcf_score = calculate_fcf_conversion(cash_flow, income_statement)
    
    # Calculate total score out of 60
    total_score = peg_score + de_score + cagr_score + pe_vs_hist_score + net_cash_score + fcf_score
    
    # Categorization
    category = get_lynch_category(peg_val, de_val, cagr_val)
    
    return {
        "symbol": symbol.upper(),
        "current_price": parse_float(overview.get("52WeekHigh")), # fallback to current price in overview, wait, let's see. Overview doesn't have current price directly, let's use BookValue or something, or we can get it from monthly_prices close.
        "pe_current": current_pe if current_pe > 0 else None,
        "pe_5yr_median": median_pe,
        "peg_ratio": peg_val if peg_val > 0 else None,
        "debt_equity": de_val,
        "revenue_cagr_5yr": cagr_val,
        "net_cash_pct_mcap": net_cash_pct,
        "fcf_conversion": fcf_conv_val,
        "scores": {
            "peg": peg_score,
            "debt_equity": de_score,
            "revenue_growth": cagr_score,
            "pe_vs_hist": pe_vs_hist_score,
            "net_cash": net_cash_score,
            "fcf": fcf_score
        },
        "quant_score": total_score,
        "lynch_category": category
    }
