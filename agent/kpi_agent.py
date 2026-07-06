from pydantic import BaseModel, Field, conint
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from tools.alphavantage_tools import (
    get_company_overview,
    get_balance_sheet,
    get_income_statement,
    get_earnings
)
from scoring.kpi_scorer import evaluate_kpi_metrics

class KPIScores(BaseModel):
    ebit_margin: conint(ge=0, le=12) = Field(description="Score for EBIT Margin Trend (0-12)")
    revenue_trend: conint(ge=0, le=10) = Field(description="Score for Revenue Growth Trend (0-10)")
    analyst_consensus: conint(ge=0, le=8) = Field(description="Score for Analyst Consensus (0-8)")
    roe_trend: conint(ge=0, le=6) = Field(description="Score for ROE Trend (0-6)")
    eps_revision: conint(ge=0, le=4) = Field(description="Score for EPS Revision Direction (0-4)")

class StockKPIScore(BaseModel):
    symbol: str = Field(description="Ticker symbol of the stock")
    ebit_margin_trend: str = Field(description="EBIT margin trend: expanding, stable, declining")
    revenue_trend: str = Field(description="Revenue growth trend: accel, stable, decel, decel 1qtr, decel 2+ qtrs")
    analyst_buy_pct: float = Field(description="Percentage of buy recommendations (0-100)")
    analyst_consensus: str = Field(description="Consensus classification: StrongBuy, Buy, Hold, Sell")
    roe_trend: str = Field(description="ROE trend: improving, stable, declining")
    eps_revision: str = Field(description="EPS revision direction: upward, downward, no_change")
    scores: KPIScores = Field(description="Breakdown of KPI scores")
    kpi_score: conint(ge=0, le=40) = Field(description="Total KPI score out of 40")
    kpi_score_pct: float = Field(description="KPI score as percentage of max possible score (0-100)")

def perform_kpi_analysis(symbol: str) -> dict:
    """
    Perform a complete Peter Lynch IT KPI analysis on a stock by calling
    the individual Alpha Vantage tools and passing their outputs to the scoring engine.
    """
    print(f"[KPI Tool] Starting IT KPI analysis for {symbol}")
    overview = get_company_overview(symbol)
    balance_sheet = get_balance_sheet(symbol)
    income_statement = get_income_statement(symbol)
    earnings = get_earnings(symbol)
    
    metrics = evaluate_kpi_metrics(
        symbol=symbol,
        overview=overview,
        balance_sheet=balance_sheet,
        income_statement=income_statement,
        earnings=earnings
    )
    return metrics

def create_kpi_agent() -> LlmAgent:
    """
    Instantiate and return the Lynch IT KPI Analyser Agent.
    """
    tools = [
        FunctionTool(func=get_company_overview),
        FunctionTool(func=get_balance_sheet),
        FunctionTool(func=get_income_statement),
        FunctionTool(func=get_earnings),
        FunctionTool(func=perform_kpi_analysis)
    ]
    
    # Enforce strict tool allowlist programmatically at registration
    ALLOWED_KPI_TOOLS = {
        "get_company_overview",
        "get_balance_sheet",
        "get_income_statement",
        "get_earnings",
        "perform_kpi_analysis"
    }
    
    for tool in tools:
        if tool.name not in ALLOWED_KPI_TOOLS:
            raise ValueError(f"Unauthorized tool registration attempt: {tool.name}")
            
    system_instruction = (
        "You are a professional Peter Lynch stock analyst specializing in stock KPIs and analyst estimates for NASDAQ stocks. "
        "Your goal is to evaluate a given stock ticker and output its detailed KPI scoring profile.\n\n"
        "To perform this analysis:\n"
        "1. Call `perform_kpi_analysis` with the given stock symbol. This is the primary tool to gather all metrics "
        "and calculate the final KPI scores.\n"
        "2. If `perform_kpi_analysis` fails or you need to inspect individual components, call the specific tools "
        "(`get_company_overview`, `get_balance_sheet`, etc.) directly.\n"
        "3. Output a single JSON object conforming exactly to the required output schema. Do not write any explanatory "
        "prose before or after the JSON block.\n\n"
        "GROUNDING ENFORCEMENT:\n"
        "Every numeric value in your JSON output MUST originate directly from a tool call result. If a metric or numeric "
        "value is unavailable from the tools, you MUST return null (do not guess, estimate, or assume zero). Pydantic validation "
        "will handle null values appropriately. Confident hallucinations on missing metrics are strictly prohibited."
    )
    
    agent = LlmAgent(
        name="it_kpi_agent",
        model="gemini-2.0-flash",
        instruction=system_instruction,
        tools=tools,
        output_schema=StockKPIScore
    )
    
    return agent
