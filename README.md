# Peter Lynch Stock Analyser — Multi-Agent Equity Research Platform

A multi-agent quantitative equity research system built using the **Google Agent Development Kit (ADK)** and the **Model Context Protocol (MCP)**. The platform automatically evaluates NASDAQ stocks against Peter Lynch's core investment principles combined with IT-sector key quality metrics, rendering findings on an interactive web dashboard.

> [!WARNING]
> **Disclaimer & Project Status**: This project is a Proof of Concept (POC) / prototype demonstration built for **educational purposes only**. It does **not** constitute financial, investment, or legal advice, nor is it a recommendation to buy or sell any security.
> 
> * **Methodology & Book Attribution**: The quantitative screening framework implemented in this tool is based on the public investment principles and heuristics described in books by Peter Lynch (such as *One Up on Wall Street*). This project is an independent educational implementation of these concepts and is not affiliated with, sponsored by, or endorsed by Peter Lynch or any publishers.
> * **Future Roadmap**: The stock universe is currently limited and will be expanded in future releases.
> * **Qualitative Criteria**: More qualitative parameters for fundamental analysis (such as earnings call transcript parsing, management guidance analysis, and macroeconomic indicators) will be added in subsequent phases.

---

## 1. System Features
* **Agent 1 (Lynch Quantitative Analyser)**: Aggregates financial statements and evaluates fundamental valuation (PEG, Debt/Equity, Median PE, etc.) out of 60 points.
* **Agent 2 (IT Sector KPI Analyser)**: Scores operational efficiency, consensus growth projections, and EPS revision trends out of 40 points.
* **Agent 3 (Ranking Engine & Visualizer)**: Integrates scores from both agents, generates composite rankings, assigns verdicts, and outputs clean, self-contained HTML research reports.
* **Interactive Dashboard**: A responsive, web-based UI with tabs for fundamental analysis, operational KPI breakdowns, interactive Chart.js visualizations, and a universe leaderboard.
* **Robust Security Guardrails**: Includes indirect prompt injection defense, strict tool allowlists, Pydantic-validated agent handoffs, grounding prompts, and XSS sanitization.

---

## 2. Technical Documentation

For in-depth details about the platform architecture, agent prompt instructions, data flow layouts, and scoring formulas, please refer to the technical docs:
👉 **[documentation.md](file:///c:/Users/Welcome/Documents/Vivek_Coding/Stock_Research_Agent_PeterLynch/documentation.md)**

---

## 3. Project Structure

```
Stock_Research_Agent_PeterLynch/
│
├── run_agent.py                 # Runner script / Starts FastAPI server
├── server.py                    # Backend server (FastAPI, schema validation, compliance audit)
├── requirements.txt             # Project dependencies (google-adk, yfinance, requests, mcp, etc.)
├── .env                         # Local configuration secrets (API keys - IGNORED by git)
├── .env.template                # Template for environment keys (COMMITTED to git)
├── .gitignore                   # Excludes credential files, venv, and binary caches
├── README.md                    # Core project landing page
├── documentation.md             # In-depth technical architecture and workflows
│
├── agent/
│   ├── quant_agent.py           # Agent 1 ADK definition and output schema
│   └── kpi_agent.py             # Agent 2 ADK definition and output schema
│
├── tools/
│   ├── __init__.py
│   └── alphavantage_tools.py    # Alpha Vantage API wrapper with prompt injection sanitization
│
├── scoring/
│   ├── quant_scorer.py          # Math calculations for quantitative valuation scoring (60 pts)
│   └── kpi_scorer.py            # Math calculations for IT sector operational metrics (40 pts)
│
├── data/
│   ├── scored_quant.json        # Compiled output scores for Agent 1
│   ├── scored_kpi.json          # Compiled output scores for Agent 2
│   └── cache/                   # API response caches (IGNORED by git)
│
├── static/
│   ├── index.html               # Main frontend entry point
│   ├── style.css                # Custom CSS (sleek glassmorphic theme)
│   └── app.js                   # Client-side routing, logic, and Chart.js integration
│
└── scratch/
    ├── generate_mock_cache.py   # Populates local caches with offline mock data
    ├── test_scoring.py          # Offline test for fundamental scoring
    ├── test_kpi_scorer.py       # Offline test for KPI scoring
    ├── test_security_guardrails.py # Test suite for security checks and inputs
    ├── test_mcp_client.py       # Validates local stdio connection to Alpha Vantage MCP server
    ├── test_mcp_connection.py   # Validates remote SSE connection
    └── run_evals.py             # Evaluation test runner checking output against ground truth
```

---

## 4. Setup & Installation

### Prerequisite: Install `uv`
This project uses `uv` for python environment management. If you don't have it installed:
```powershell
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install Dependencies
Set up the virtual environment and install dependencies:
```bash
uv venv --python 3.12
uv pip install -r requirements.txt
```

### Configure Secrets (.env Setup)
To prevent committing sensitive API keys to GitHub, the `.env` file is excluded from git tracking. To configure your keys:

1. Copy the `.env.template` file to a new file named `.env`:
   ```bash
   copy .env.template .env
   ```
2. Open `.env` in a text editor.
3. Replace the placeholder values with your actual credentials:
   * **`GOOGLE_API_KEY`**: Get a Gemini API Key from [Google AI Studio](https://aistudio.google.com/).
   * **`ALPHAVANTAGE_API_KEY`**: Get a free API Key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).

---

## 5. Running the Project

### Option A: Local Calculation Test (Offline / No Keys Required)
Verify the pure mathematical calculations and scoring rubrics using cached mock data:
```bash
uv run python scratch/test_scoring.py
uv run python scratch/test_kpi_scorer.py
```
To run the full validation suite check against ground-truth data:
```bash
uv run python scratch/run_evals.py
```
To test system security check compliance (XSS, injections, allowlists):
```bash
uv run python scratch/test_security_guardrails.py
```

### Option B: Run the Full Platform (Dashboard Web Server)
To run the backend server and open the web dashboard:
```bash
uv run python run_agent.py --server
```
Once started, navigate to **`http://localhost:8000`** in your browser. From here you can:
1. Select a ticker and run **Quant Analysis** (fundamental checks).
2. Run **KPI Analysis** (operational quality metrics).
3. View scores, metric charts, and check the combined **Universe Leaderboard**.
