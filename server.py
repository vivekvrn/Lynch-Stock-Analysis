import os
import json
import html
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from agent.quant_agent import perform_lynch_analysis, StockQuantScore
from agent.kpi_agent import perform_kpi_analysis, StockKPIScore

def escape_html_strings(data):
    if isinstance(data, dict):
        return {k: escape_html_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [escape_html_strings(v) for v in data]
    elif isinstance(data, str):
        return html.escape(data)
    return data

def audit_score(symbol: str, score_type: str, agent_score: int) -> str:
    try:
        if score_type == "quant":
            expected = perform_lynch_analysis(symbol).get("quant_score", 0)
        else:
            expected = perform_kpi_analysis(symbol).get("kpi_score", 0)
        return "AUDIT_MISMATCH" if abs(agent_score - expected) > 2 else "AUDIT_OK"
    except Exception as e:
        return f"AUDIT_ERROR: {e}"

app = FastAPI(title="Peter Lynch Stock Analyser API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
RANKINGS_FILE = os.path.join(os.path.dirname(__file__), "data", "scored_quant.json")
KPI_RANKINGS_FILE = os.path.join(os.path.dirname(__file__), "data", "scored_kpi.json")

def _update_rankings_file(new_stock_data):
    """
    Load the rankings file, add/update the analyzed stock data,
    sort by quant_score descending, and save it back.
    """
    os.makedirs(os.path.dirname(RANKINGS_FILE), exist_ok=True)
    stocks = []
    
    if os.path.exists(RANKINGS_FILE):
        try:
            with open(RANKINGS_FILE, "r") as f:
                stocks = json.load(f)
                if not isinstance(stocks, list):
                    stocks = []
        except Exception as e:
            print(f"[Server] Warning: Failed to read rankings file: {e}")
            
    # Filter out existing entry for this stock
    symbol = new_stock_data.get("symbol", "").upper()
    stocks = [s for s in stocks if s.get("symbol", "").upper() != symbol]
    
    # Append new data
    stocks.append(new_stock_data)
    
    # Sort by score descending
    stocks.sort(key=lambda s: s.get("quant_score", 0), reverse=True)
    
    try:
        with open(RANKINGS_FILE, "w") as f:
            json.dump(stocks, f, indent=2)
    except Exception as e:
        print(f"[Server] Error: Failed to write rankings file: {e}")

def _update_kpi_rankings_file(new_stock_data):
    """
    Load the KPI rankings file, add/update the analyzed stock data,
    sort by kpi_score descending, and save it back.
    """
    os.makedirs(os.path.dirname(KPI_RANKINGS_FILE), exist_ok=True)
    stocks = []
    
    if os.path.exists(KPI_RANKINGS_FILE):
        try:
            with open(KPI_RANKINGS_FILE, "r") as f:
                stocks = json.load(f)
                if not isinstance(stocks, list):
                    stocks = []
        except Exception as e:
            print(f"[Server] Warning: Failed to read KPI rankings file: {e}")
            
    # Filter out existing entry for this stock
    symbol = new_stock_data.get("symbol", "").upper()
    stocks = [s for s in stocks if s.get("symbol", "").upper() != symbol]
    
    # Append new data
    stocks.append(new_stock_data)
    
    # Sort by score descending
    stocks.sort(key=lambda s: s.get("kpi_score", 0), reverse=True)
    
    try:
        with open(KPI_RANKINGS_FILE, "w") as f:
            json.dump(stocks, f, indent=2)
    except Exception as e:
        print(f"[Server] Error: Failed to write KPI rankings file: {e}")

# API Endpoints

@app.get("/api/analyze")
def analyze_stock(symbol: str):
    """Run Peter Lynch quantitative analysis on a stock."""
    symbol = symbol.strip().upper()
    if not symbol:
        return JSONResponse(status_code=400, content={"error": "Symbol parameter is required"})
        
    try:
        # Run analysis (hits cache if available, else fetches from Alpha Vantage)
        result = perform_lynch_analysis(symbol)
        
        # Schema-validated handoff
        validated_data = StockQuantScore(**result).dict()
        
        # Score derivability audit
        audit_status = audit_score(symbol, "quant", validated_data.get("quant_score", 0))
        validated_data["audit_status"] = audit_status
        
        # HTML output escaping
        safe_data = escape_html_strings(validated_data)
        
        # Save to the global rankings list
        _update_rankings_file(safe_data)
        
        return safe_data
    except Exception as e:
        print(f"[Server] Error analyzing {symbol}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/kpi")
def analyze_kpi(symbol: str):
    """Run Peter Lynch IT KPI analysis on a stock."""
    symbol = symbol.strip().upper()
    if not symbol:
        return JSONResponse(status_code=400, content={"error": "Symbol parameter is required"})
        
    try:
        # Run KPI analysis (hits cache if available)
        result = perform_kpi_analysis(symbol)
        
        # Schema-validated handoff
        validated_data = StockKPIScore(**result).dict()
        
        # Score derivability audit
        audit_status = audit_score(symbol, "kpi", validated_data.get("kpi_score", 0))
        validated_data["audit_status"] = audit_status
        
        # HTML output escaping
        safe_data = escape_html_strings(validated_data)
        
        # Save to the global KPI rankings list
        _update_kpi_rankings_file(safe_data)
        
        return safe_data
    except Exception as e:
        print(f"[Server] Error analyzing KPI for {symbol}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/rankings")
def get_rankings():
    """Retrieve the combined sorted rankings of all analyzed stocks."""
    quant_stocks = []
    if os.path.exists(RANKINGS_FILE):
        try:
            with open(RANKINGS_FILE, "r") as f:
                quant_stocks = json.load(f)
        except Exception as e:
            print(f"[Server] Warning: Failed to read quant rankings: {e}")

    kpi_stocks = []
    if os.path.exists(KPI_RANKINGS_FILE):
        try:
            with open(KPI_RANKINGS_FILE, "r") as f:
                kpi_stocks = json.load(f)
        except Exception as e:
            print(f"[Server] Warning: Failed to read KPI rankings: {e}")

    quant_map = {s.get("symbol", "").upper(): s for s in quant_stocks}
    kpi_map = {s.get("symbol", "").upper(): s for s in kpi_stocks}

    all_symbols = set(quant_map.keys()) | set(kpi_map.keys())
    combined = []

    for sym in all_symbols:
        q_data = quant_map.get(sym, {})
        k_data = kpi_map.get(sym, {})

        quant_score = q_data.get("quant_score", 0)
        kpi_score = k_data.get("kpi_score", 0)
        composite_score = quant_score + kpi_score

        combined.append({
            "symbol": sym,
            "lynch_category": q_data.get("lynch_category") or "Unknown",
            "pe_current": q_data.get("pe_current"),
            "pe_5yr_median": q_data.get("pe_5yr_median"),
            "quant_score": quant_score,
            "kpi_score": kpi_score,
            "composite_score": composite_score,
            "verdict": get_verdict_for_score(composite_score)
        })

    # Sort by composite score descending
    combined.sort(key=lambda s: s.get("composite_score", 0), reverse=True)
    return combined

def get_verdict_for_score(score):
    if score >= 80:
        return "STRONG BUY"
    elif score >= 65:
        return "BUY"
    elif score >= 50:
        return "WATCH"
    elif score >= 35:
        return "NEUTRAL"
    else:
        return "AVOID"


# Serve Static Files

# Serve index.html at root
@app.get("/")
def read_root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_file):
        return JSONResponse(status_code=404, content={"error": "Frontend static assets not found. Build static files."})
    return FileResponse(index_file)

# Mount static folder
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
