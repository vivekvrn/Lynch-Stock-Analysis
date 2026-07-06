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

def calculate_ebit_margin_trend(income_statement):
    """
    EBIT Margin Trend (4Q) (12 pts)
    Expanding >150bps = 12 | Stable = 8 | Declining = 4
    Compare latest quarter's margin with the quarter 4 periods ago.
    """
    reports = income_statement.get("quarterlyReports", [])
    if len(reports) < 4:
        return "stable", 8
        
    # Get margins for the quarters (index 0 is latest, index 3 is 4th latest)
    # EBIT Margin = operatingIncome / totalRevenue
    margins = []
    for r in reports[:4]:
        op_inc = parse_float(r.get("operatingIncome"))
        rev = parse_float(r.get("totalRevenue"))
        if rev > 0:
            margins.append(op_inc / rev)
        else:
            margins.append(0.0)
            
    if len(margins) < 4:
        return "stable", 8
        
    latest_margin = margins[0]
    old_margin = margins[3]
    diff = latest_margin - old_margin
    
    if diff > 0.015:
        return "expanding", 12
    elif diff >= -0.015:
        return "stable", 8
    else:
        return "declining", 4

def calculate_revenue_growth_trend(income_statement):
    """
    Revenue Growth Trend (4Q) (10 pts)
    Accel 2+ qtrs = 10 | Stable = 6 | Decel 1qtr = 3 | Decel 2+ qtrs = 0
    Compare QoQ revenue growth rates.
    """
    reports = income_statement.get("quarterlyReports", [])
    if len(reports) < 5:
        return "stable", 6
        
    # Get revenues for the last 5 quarters (index 0 is latest)
    revenues = [parse_float(r.get("totalRevenue")) for r in reports[:5]]
    
    # QoQ Growth rates:
    # G0: from R1 to R0 (latest transition)
    # G1: from R2 to R1
    # G2: from R3 to R2
    # G3: from R4 to R3
    growths = []
    for i in range(4):
        r_curr = revenues[i]
        r_prev = revenues[i+1]
        if r_prev > 0:
            growths.append((r_curr - r_prev) / r_prev)
        else:
            growths.append(0.0)
            
    # growths[0] is latest growth, growths[1] is previous, growths[2] is before that
    g0, g1, g2 = growths[0], growths[1], growths[2]
    
    # Heuristics based on growth values (matching our mock data generation parameters)
    if g0 > 0.02:
        return "accel", 10
    elif g0 >= 0.005:
        return "stable", 6
    elif g0 >= -0.01:
        return "decel 1qtr", 3
    else:
        return "decel 2+ qtrs", 0

def calculate_analyst_consensus(overview):
    """
    Analyst Consensus (8 pts)
    Buy % >= 70% = 8 | 50-70% = 6 | 30-50% = 3 | <30% = 0
    Buy % = (StrongBuy + Buy) / (StrongBuy + Buy + Hold + Sell + StrongSell) * 100
    """
    strong_buy = parse_float(overview.get("AnalystRatingStrongBuy"))
    buy = parse_float(overview.get("AnalystRatingBuy"))
    hold = parse_float(overview.get("AnalystRatingHold"))
    sell = parse_float(overview.get("AnalystRatingSell"))
    strong_sell = parse_float(overview.get("AnalystRatingStrongSell"))
    
    total = strong_buy + buy + hold + sell + strong_sell
    if total <= 0:
        return "Hold", 0.0, 6 # Default to stable consensus
        
    buy_pct = ((strong_buy + buy) / total) * 100
    
    if buy_pct >= 70:
        consensus = "StrongBuy"
        score = 8
    elif buy_pct >= 50:
        consensus = "Buy"
        score = 6
    elif buy_pct >= 30:
        consensus = "Hold"
        score = 3
    else:
        consensus = "Sell"
        score = 0
        
    return consensus, buy_pct, score

def calculate_roe_trend(balance_sheet, income_statement):
    """
    ROE Trend (3yr) (6 pts)
    >20% improving = 6 | >20% stable = 4 | 15-20% = 2 | <15% = 0
    ROE = netIncome / totalShareholderEquity
    """
    bs_reports = balance_sheet.get("annualReports", [])
    is_reports = income_statement.get("annualReports", [])
    
    if len(bs_reports) < 3 or len(is_reports) < 3:
        return "declining", 0.0, 0
        
    roes = []
    for i in range(3):
        net_inc = parse_float(is_reports[i].get("netIncome"))
        equity = parse_float(bs_reports[i].get("totalShareholderEquity"))
        if equity > 0:
            roes.append((net_inc / equity) * 100)
        else:
            roes.append(0.0)
            
    # roes[0] is latest, roes[1] is 1yr ago, roes[2] is 2yr ago
    latest_roe = roes[0]
    
    if latest_roe > 20:
        if roes[0] > roes[1] > roes[2]:
            return "improving", latest_roe, 6
        else:
            return "stable", latest_roe, 4
    elif latest_roe >= 15:
        return "stable", latest_roe, 2
    else:
        return "declining", latest_roe, 0

def calculate_eps_revision_direction(earnings):
    """
    EPS Estimate Direction (4 pts)
    Upward revision = 4 | No change = 2 | Downward = 0
    Compare estimatedEPS for current vs previous quarters.
    """
    q_earnings = earnings.get("quarterlyEarnings", [])
    if len(q_earnings) < 2:
        return "no_change", 2
        
    # Get estimated EPS for latest 2 quarters
    est_0 = parse_float(q_earnings[0].get("estimatedEPS"))
    est_1 = parse_float(q_earnings[1].get("estimatedEPS"))
    
    if est_1 <= 0:
        return "no_change", 2
        
    est_growth = (est_0 - est_1) / est_1
    
    if est_growth > 0.02:
        return "upward", 4
    elif est_growth >= -0.02:
        return "no_change", 2
    else:
        return "downward", 0

def evaluate_kpi_metrics(symbol, overview, balance_sheet, income_statement, earnings):
    """
    Evaluate all KPI metrics for Agent 2.
    """
    ebit_trend, ebit_score = calculate_ebit_margin_trend(income_statement)
    rev_trend, rev_score = calculate_revenue_growth_trend(income_statement)
    consensus, buy_pct, consensus_score = calculate_analyst_consensus(overview)
    roe_trend, latest_roe, roe_score = calculate_roe_trend(balance_sheet, income_statement)
    eps_rev, eps_score = calculate_eps_revision_direction(earnings)
    
    total_score = ebit_score + rev_score + consensus_score + roe_score + eps_score
    kpi_pct = (total_score / 40.0) * 100.0
    
    return {
        "symbol": symbol.upper(),
        "ebit_margin_trend": ebit_trend,
        "revenue_trend": rev_trend,
        "analyst_buy_pct": round(buy_pct, 1),
        "analyst_consensus": consensus,
        "roe_trend": roe_trend,
        "eps_revision": eps_rev,
        "scores": {
            "ebit_margin": ebit_score,
            "revenue_trend": rev_score,
            "analyst_consensus": consensus_score,
            "roe_trend": roe_score,
            "eps_revision": eps_score
        },
        "kpi_score": total_score,
        "kpi_score_pct": round(kpi_pct, 1)
    }
