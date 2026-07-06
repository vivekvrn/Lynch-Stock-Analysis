from pydantic import BaseModel, Field, conint
from typing import Dict, Optional
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from tools.alphavantage_tools import (
    get_company_overview,
    get_balance_sheet,
    get_income_statement,
    get_cash_flow,
    get_monthly_prices,
    get_earnings
)
from scoring.quant_scorer import evaluate_stock_metrics

# Define Pydantic output schemas for structured output support

class MetricScores(BaseModel):
    peg: conint(ge=0, le=15) = Field(description="Score for PEG Ratio (0-15)")
    debt_equity: conint(ge=0, le=12) = Field(description="Score for Debt/Equity (0-12)")
    revenue_growth: conint(ge=0, le=12) = Field(description="Score for 5yr Revenue CAGR (0-12)")
    pe_vs_hist: conint(ge=0, le=10) = Field(description="Score for P/E vs 5yr Median (0-10)")
    net_cash: conint(ge=0, le=6) = Field(description="Score for Net Cash % Market Cap (0-6)")
    fcf: conint(ge=0, le=5) = Field(description="Score for FCF Conversion (0-5)")

class StockQuantScore(BaseModel):
    symbol: str = Field(description="Ticker symbol of the stock")
    current_price: Optional[float] = Field(description="Current price of the stock")
    pe_current: Optional[float] = Field(description="Current P/E ratio")
    pe_5yr_median: Optional[float] = Field(description="5-year median P/E ratio")
    peg_ratio: Optional[float] = Field(description="PEG ratio")
    debt_equity: float = Field(description="Long-term Debt/Equity ratio")
    revenue_cagr_5yr: float = Field(description="5-year Revenue CAGR percentage")
    net_cash_pct_mcap: float = Field(description="Net cash as a percentage of market cap")
    fcf_conversion: float = Field(description="Free Cash Flow conversion percentage")
    scores: MetricScores = Field(description="Breakdown of scores for each metric")
    quant_score: conint(ge=0, le=60) = Field(description="Total quantitative score out of 60")
    lynch_category: str = Field(description="Peter Lynch category: Stalwart, Fast Grower, Slow Grower, Turnaround Candidate")

# Helper function to perform the entire math analysis at once
def perform_lynch_analysis(symbol: str) -> dict:
    """
    Perform a complete Peter Lynch quantitative analysis on a stock by calling
    the individual Alpha Vantage tools and passing their outputs to the scoring engine.
    This helper guarantees arithmetic accuracy.
    """
    print(f"[Analysis Tool] Starting Peter Lynch analysis for {symbol}")
    overview = get_company_overview(symbol)
    balance_sheet = get_balance_sheet(symbol)
    income_statement = get_income_statement(symbol)
    cash_flow = get_cash_flow(symbol)
    monthly_prices = get_monthly_prices(symbol)
    earnings = get_earnings(symbol)
    
    # Calculate price from monthly_prices (use the last available month's close)
    current_price = None
    time_series = monthly_prices.get("Monthly Time Series", {})
    if time_series:
        latest_month = sorted(time_series.keys())[-1]
        try:
            current_price = float(time_series[latest_month].get("4. close", 0.0))
        except (ValueError, TypeError):
            pass
            
    metrics = evaluate_stock_metrics(
        symbol=symbol,
        overview=overview,
        balance_sheet=balance_sheet,
        income_statement=income_statement,
        cash_flow=cash_flow,
        monthly_prices=monthly_prices,
        earnings=earnings
    )
    
    if current_price:
        metrics["current_price"] = current_price
        
    return metrics

def create_quant_agent() -> LlmAgent:
    """
    Instantiate and return the Lynch Quantitative Analyser Agent.
    """
    # Wrap the python functions as ADK tools
    tools = [
        FunctionTool(func=get_company_overview),
        FunctionTool(func=get_balance_sheet),
        FunctionTool(func=get_income_statement),
        FunctionTool(func=get_cash_flow),
        FunctionTool(func=get_monthly_prices),
        FunctionTool(func=get_earnings),
        FunctionTool(func=perform_lynch_analysis)
    ]
    
    # Enforce strict tool allowlist programmatically at registration
    ALLOWED_QUANT_TOOLS = {
        "get_company_overview",
        "get_balance_sheet",
        "get_income_statement",
        "get_cash_flow",
        "get_monthly_prices",
        "get_earnings",
        "perform_lynch_analysis"
    }
    
    for tool in tools:
        if tool.name not in ALLOWED_QUANT_TOOLS:
            raise ValueError(f"Unauthorized tool registration attempt: {tool.name}")
            
    system_instruction = (
        "You are a professional Peter Lynch quantitative stock analyst specializing in NASDAQ stocks. "
        "Your goal is to evaluate a given stock ticker and output its detailed scoring profile.\n\n"
        "To perform this analysis:\n"
        "1. Call `perform_lynch_analysis` with the given stock symbol. This is the primary tool to gather all metrics "
        "and calculate the final scores.\n"
        "2. If `perform_lynch_analysis` fails or you need to inspect individual components, call the specific tools "
        "(`get_company_overview`, `get_balance_sheet`, etc.) directly.\n"
        "3. Output a single JSON object conforming exactly to the required output schema. Do not write any explanatory "
        "prose before or after the JSON block.\n\n"
        "GROUNDING ENFORCEMENT:\n"
        "Every numeric value in your JSON output MUST originate directly from a tool call result. If a metric or numeric "
        "value is unavailable from the tools, you MUST return null (do not guess, estimate, or assume zero). Pydantic validation "
        "will handle null values appropriately. Confident hallucinations on missing metrics are strictly prohibited."
    )
    
    agent = LlmAgent(
        name="lynch_quant_agent",
        model="gemini-2.0-flash",
        instruction=system_instruction,
        tools=tools,
        output_schema=StockQuantScore
    )
    
    return agent
