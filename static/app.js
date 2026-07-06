document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const analyzeBtn = document.getElementById("analyze-btn");
    const analyzeKpiBtn = document.getElementById("analyze-kpi-btn");
    const stockSelect = document.getElementById("stock-select");
    const spinner = analyzeBtn.querySelector(".spinner");
    const btnText = analyzeBtn.querySelector(".btn-text");
    
    const reportPlaceholder = document.getElementById("report-placeholder");
    const reportContent = document.getElementById("report-content");
    const kpiPlaceholder = document.getElementById("kpi-placeholder");
    const kpiContent = document.getElementById("kpi-content");
    const rankingsTableBody = document.getElementById("rankings-table-body");
    const loadRankingsBtn = document.getElementById("load-rankings-btn");

    // Report Result elements
    const resScore = document.getElementById("res-score");
    const resBarFill = document.getElementById("res-bar-fill");
    const resVerdict = document.getElementById("res-verdict");
    const resCategory = document.getElementById("res-category");
    const resSymbolDisplay = document.getElementById("res-symbol-display");
    const resPriceDisplay = document.getElementById("res-price-display");
    const resPeDisplay = document.getElementById("res-pe-display");

    // Table elements
    const valPeg = document.getElementById("val-peg");
    const scorePeg = document.getElementById("score-peg");
    const valDe = document.getElementById("val-de");
    const scoreDe = document.getElementById("score-de");
    const valCagr = document.getElementById("val-cagr");
    const scoreCagr = document.getElementById("score-cagr");
    const valPeVs = document.getElementById("val-pe-vs");
    const scorePeVs = document.getElementById("score-pe-vs");
    const valNetcash = document.getElementById("val-netcash");
    const scoreNetcash = document.getElementById("score-netcash");
    const valFcf = document.getElementById("val-fcf");
    const scoreFcf = document.getElementById("score-fcf");

    // KPI Report Result elements
    const kpiResScore = document.getElementById("kpi-res-score");
    const kpiResBarFill = document.getElementById("kpi-res-bar-fill");
    const kpiResVerdict = document.getElementById("kpi-res-verdict");
    const kpiSymbolDisplay = document.getElementById("kpi-symbol-display");
    const kpiMarginDisplay = document.getElementById("kpi-margin-display");
    const kpiConsensusDisplay = document.getElementById("kpi-consensus-display");

    // KPI Table elements
    const kpiValEbit = document.getElementById("kpi-val-ebit");
    const kpiScoreEbit = document.getElementById("kpi-score-ebit");
    const kpiValRev = document.getElementById("kpi-val-rev");
    const kpiScoreRev = document.getElementById("kpi-score-rev");
    const kpiValConsensus = document.getElementById("kpi-val-consensus");
    const kpiScoreConsensus = document.getElementById("kpi-score-consensus");
    const kpiValRoe = document.getElementById("kpi-val-roe");
    const kpiScoreRoe = document.getElementById("kpi-score-roe");
    const kpiValEps = document.getElementById("kpi-val-eps");
    const kpiScoreEps = document.getElementById("kpi-score-eps");

    let scoresChartInstance = null;
    let kpiChartInstance = null;

    // TAB CONTROLLER
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
            
            if (targetTab === "rankings-tab") {
                fetchLeaderboard();
            }
        });
    });

    // RUN ANALYSIS EVENT
    analyzeBtn.addEventListener("click", async () => {
        const symbol = stockSelect.value;
        if (!symbol) return;

        // Set Loading State
        analyzeBtn.disabled = true;
        spinner.classList.remove("hidden");
        btnText.textContent = "Analyzing Stock...";
        
        reportPlaceholder.classList.remove("hidden");
        reportContent.classList.add("hidden");

        try {
            const response = await fetch(`/api/analyze?symbol=${symbol}`);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || "Analysis failed");
            }
            
            const data = await response.json();
            populateReport(data);
            
            // Switch view
            reportPlaceholder.classList.add("hidden");
            reportContent.classList.remove("hidden");
        } catch (error) {
            console.error(error);
            alert(`Error running analysis: ${error.message}`);
        } finally {
            // Reset Button State
            analyzeBtn.disabled = false;
            spinner.classList.add("hidden");
            btnText.textContent = "Run Quant Analysis";
        }
    });

    // POPULATE REPORT DOM
    function populateReport(data) {
        const score = data.quant_score || 0;
        const category = data.lynch_category || "Unknown";
        
        // 1. Overall Score & Verdict
        resScore.textContent = score;
        resBarFill.style.width = `${(score / 60) * 100}%`;
        
        // Map Score to Peter Lynch Verdict
        // Note: original BRD scores were out of 100 (60 quant + 40 KPI).
        // Since we are running Agent 1 only, the max score is 60.
        // We scale the original thresholds (80+, 65-79, 50-64, 35-49, <35) to 60-point scale (x 0.6)
        // 80+ out of 100 => 48+ out of 60: STRONG BUY
        // 65-79 out of 100 => 39-47 out of 60: BUY
        // 50-64 out of 100 => 30-38 out of 60: WATCH
        // 35-49 out of 100 => 21-29 out of 60: NEUTRAL
        // <35 out of 100 => <21 out of 60: AVOID
        let verdict = "";
        let verdictClass = "";
        
        if (score >= 48) {
            verdict = "STRONG BUY (Lynch would be highly excited)";
            verdictClass = "accent-emerald";
        } else if (score >= 39) {
            verdict = "BUY (Passes most filters, good risk/reward)";
            verdictClass = "accent-cyan";
        } else if (score >= 30) {
            verdict = "WATCH (Interesting, but wait for better entry)";
            verdictClass = "accent-yellow";
        } else if (score >= 21) {
            verdict = "NEUTRAL (Does not clear Lynch's bar currently)";
            verdictClass = "text-secondary";
        } else {
            verdict = "AVOID (Multiple quantitative red flags present)";
            verdictClass = "accent-red";
        }
        
        resVerdict.textContent = verdict;
        resVerdict.className = `score-context ${verdictClass}`;
        
        // 2. Category Badge & Meta Data
        resCategory.textContent = category;
        resSymbolDisplay.textContent = `Ticker: ${data.symbol}`;
        resPriceDisplay.textContent = `Current Price: $${data.current_price ? data.current_price.toFixed(2) : "N/A"}`;
        resPeDisplay.textContent = `Current P/E: ${data.pe_current ? data.pe_current.toFixed(1) : "N/A"}`;
        
        // Set category badge style
        let catColor = "var(--accent-gray)";
        let catGlow = "rgba(107, 114, 128, 0.25)";
        if (category === "Fast Grower") {
            catColor = "var(--accent-emerald)";
            catGlow = "var(--accent-emerald-glow)";
        } else if (category === "Stalwart") {
            catColor = "var(--accent-cyan)";
            catGlow = "var(--accent-cyan-glow)";
        } else if (category === "Turnaround Candidate") {
            catColor = "var(--accent-red)";
            catGlow = "rgba(239, 68, 68, 0.25)";
        } else if (category === "Slow Grower") {
            catColor = "var(--accent-yellow)";
            catGlow = "rgba(245, 158, 11, 0.25)";
        }
        resCategory.style.color = catColor;
        resCategory.style.borderColor = catColor;
        resCategory.style.backgroundColor = catGlow;
        resCategory.style.boxShadow = `0 0 10px ${catGlow}`;

        // 3. Table values
        const scores = data.scores || {};
        
        valPeg.textContent = data.peg_ratio ? data.peg_ratio.toFixed(2) : "N/A";
        scorePeg.textContent = scores.peg || 0;
        
        valDe.textContent = data.debt_equity ? data.debt_equity.toFixed(3) : "0.0";
        scoreDe.textContent = scores.debt_equity || 0;
        
        valCagr.textContent = `${data.revenue_cagr_5yr ? data.revenue_cagr_5yr.toFixed(1) : "0.0"}%`;
        scoreCagr.textContent = scores.revenue_growth || 0;
        
        const pe_cur = data.pe_current ? data.pe_current.toFixed(1) : "N/A";
        const pe_med = data.pe_5yr_median ? data.pe_5yr_median.toFixed(1) : "N/A";
        valPeVs.textContent = `${pe_cur} / ${pe_med}`;
        scorePeVs.textContent = scores.pe_vs_hist || 0;
        
        valNetcash.textContent = `${data.net_cash_pct_mcap ? data.net_cash_pct_mcap.toFixed(1) : "0.0"}%`;
        scoreNetcash.textContent = scores.net_cash || 0;
        
        valFcf.textContent = `${data.fcf_conversion ? data.fcf_conversion.toFixed(1) : "0.0"}%`;
        scoreFcf.textContent = scores.fcf || 0;

        // 4. Update Chart
        renderChart(scores);
    }

    // RENDER CHART.JS BAR CHART
    function renderChart(scores) {
        const ctx = document.getElementById("scores-chart").getContext("2d");
        
        const metrics = ["PEG Ratio", "Debt/Equity", "5yr CAGR", "PE vs Median", "Net Cash %", "FCF Conversion"];
        const maxScores = [15, 12, 12, 10, 6, 5];
        const currentScores = [
            scores.peg || 0,
            scores.debt_equity || 0,
            scores.revenue_growth || 0,
            scores.pe_vs_hist || 0,
            scores.net_cash || 0,
            scores.fcf || 0
        ];

        if (scoresChartInstance) {
            scoresChartInstance.destroy();
        }

        scoresChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: metrics,
                datasets: [
                    {
                        label: "Score",
                        data: currentScores,
                        backgroundColor: "rgba(6, 182, 212, 0.4)",
                        borderColor: "rgba(6, 182, 212, 1)",
                        borderWidth: 1.5,
                        borderRadius: 4,
                        barThickness: 18,
                    },
                    {
                        label: "Max Possible",
                        data: maxScores,
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                        borderColor: "rgba(255, 255, 255, 0.15)",
                        borderWidth: 1,
                        borderRadius: 4,
                        barThickness: 18,
                    }
                ]
            },
            options: {
                responsive: true,
                indexAxis: "y", // Horizontal bars
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: "#9ca3af",
                            font: { family: "Outfit" }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { color: "#9ca3af" },
                        max: 15,
                        beginAtZero: true
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: "#f3f4f6",
                            font: { family: "Outfit", size: 11 }
                        }
                    }
                }
            }
        });
    }

    // RUN KPI ANALYSIS EVENT
    analyzeKpiBtn.addEventListener("click", async () => {
        const symbol = stockSelect.value;
        if (!symbol) return;

        // Set Loading State
        analyzeKpiBtn.disabled = true;
        const spinnerKpi = analyzeKpiBtn.querySelector(".spinner") || analyzeKpiBtn.querySelector("span:not(.btn-text)");
        const btnTextKpi = analyzeKpiBtn.querySelector(".btn-text");
        
        let showSpinner = spinnerKpi;
        if (showSpinner) showSpinner.classList.remove("hidden");
        if (btnTextKpi) btnTextKpi.textContent = "Analyzing KPIs...";
        
        kpiPlaceholder.classList.remove("hidden");
        kpiContent.classList.add("hidden");

        try {
            const response = await fetch(`/api/kpi?symbol=${symbol}`);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || "KPI Analysis failed");
            }
            
            const data = await response.json();
            populateKpiReport(data);
            
            // Switch view
            kpiPlaceholder.classList.add("hidden");
            kpiContent.classList.remove("hidden");
        } catch (error) {
            console.error(error);
            alert(`Error running KPI analysis: ${error.message}`);
        } finally {
            // Reset Button State
            analyzeKpiBtn.disabled = false;
            if (showSpinner) showSpinner.classList.add("hidden");
            if (btnTextKpi) btnTextKpi.textContent = "Run KPI Analysis";
        }
    });

    // POPULATE KPI REPORT DOM
    function populateKpiReport(data) {
        const score = data.kpi_score || 0;
        kpiResScore.textContent = score;
        kpiResBarFill.style.width = `${(score / 40) * 100}%`;

        let verdict = "";
        let verdictClass = "";
        if (score >= 32) {
            verdict = "EXCELLENT (Strong operational momentum)";
            verdictClass = "accent-emerald";
        } else if (score >= 24) {
            verdict = "GOOD (Healthy growth and margins)";
            verdictClass = "accent-cyan";
        } else if (score >= 16) {
            verdict = "MODERATE (Stable but some headwinds)";
            verdictClass = "accent-yellow";
        } else {
            verdict = "WEAK (Multiple operational red flags)";
            verdictClass = "accent-red";
        }
        kpiResVerdict.textContent = verdict;
        kpiResVerdict.className = `score-context ${verdictClass}`;

        kpiSymbolDisplay.textContent = `Ticker: ${data.symbol}`;
        kpiMarginDisplay.textContent = `EBIT Margin Trend: ${data.ebit_margin_trend.toUpperCase()}`;
        kpiConsensusDisplay.textContent = `Analyst Consensus: ${data.analyst_consensus} (${data.analyst_buy_pct}% Buy)`;

        const scores = data.scores || {};
        kpiValEbit.textContent = data.ebit_margin_trend.toUpperCase();
        kpiScoreEbit.textContent = scores.ebit_margin || 0;

        kpiValRev.textContent = data.revenue_trend.toUpperCase();
        kpiScoreRev.textContent = scores.revenue_trend || 0;

        kpiValConsensus.textContent = `${data.analyst_buy_pct}% Buy`;
        kpiScoreConsensus.textContent = scores.analyst_consensus || 0;

        kpiValRoe.textContent = `${data.roe_trend.toUpperCase()}`;
        kpiScoreRoe.textContent = scores.roe_trend || 0;

        kpiValEps.textContent = data.eps_revision.toUpperCase();
        kpiScoreEps.textContent = scores.eps_revision || 0;

        renderKpiChart(scores);
    }

    // RENDER KPI CHART
    function renderKpiChart(scores) {
        const ctx = document.getElementById("kpi-scores-chart").getContext("2d");
        const metrics = ["EBIT Margin", "Revenue Growth", "Consensus", "ROE Trend", "EPS Revision"];
        const maxScores = [12, 10, 8, 6, 4];
        const currentScores = [
            scores.ebit_margin || 0,
            scores.revenue_trend || 0,
            scores.analyst_consensus || 0,
            scores.roe_trend || 0,
            scores.eps_revision || 0
        ];

        if (kpiChartInstance) {
            kpiChartInstance.destroy();
        }

        kpiChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: metrics,
                datasets: [
                    {
                        label: "KPI Score",
                        data: currentScores,
                        backgroundColor: "rgba(16, 185, 129, 0.4)",
                        borderColor: "rgba(16, 185, 129, 1)",
                        borderWidth: 1.5,
                        borderRadius: 4,
                        barThickness: 18,
                    },
                    {
                        label: "Max Possible",
                        data: maxScores,
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                        borderColor: "rgba(255, 255, 255, 0.15)",
                        borderWidth: 1,
                        borderRadius: 4,
                        barThickness: 18,
                    }
                ]
            },
            options: {
                responsive: true,
                indexAxis: "y",
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: "#9ca3af",
                            font: { family: "Outfit" }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { color: "#9ca3af" },
                        max: 12,
                        beginAtZero: true
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: "#f3f4f6",
                            font: { family: "Outfit", size: 11 }
                        }
                    }
                }
            }
        });
    }

    // FETCH LEADERBOARD
    async function fetchLeaderboard() {
        try {
            const response = await fetch("/api/rankings");
            if (!response.ok) throw new Error("Failed to load rankings");
            
            const list = await response.json();
            renderLeaderboard(list);
        } catch (error) {
            console.error(error);
            rankingsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--accent-red);">Error loading rankings: ${error.message}</td></tr>`;
        }
    }

    // RENDER LEADERBOARD TABLE
    function renderLeaderboard(list) {
        if (!list || list.length === 0) {
            rankingsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No records found. Run analysis first.</td></tr>`;
            return;
        }

        rankingsTableBody.innerHTML = "";
        list.forEach((stock, index) => {
            const quantScore = stock.quant_score || 0;
            const kpiScore = stock.kpi_score || 0;
            const compositeScore = stock.composite_score || 0;
            
            let verdict = stock.verdict || "NEUTRAL";
            let verdictClass = "verdict-neutral";
            
            if (verdict === "STRONG BUY") verdictClass = "verdict-strongbuy";
            else if (verdict === "BUY") verdictClass = "verdict-buy";
            else if (verdict === "WATCH") verdictClass = "verdict-watch";
            else if (verdict === "NEUTRAL") verdictClass = "verdict-neutral";
            else if (verdict === "AVOID") verdictClass = "verdict-avoid";

            const row = document.createElement("tr");
            row.innerHTML = `
                <td><span class="rank-badge">${index + 1}</span></td>
                <td style="font-weight: 600; font-family: 'Outfit'; color: var(--accent-cyan);">${stock.symbol}</td>
                <td>${stock.lynch_category}</td>
                <td style="font-weight: 600; color: var(--accent-cyan);">${quantScore}/60</td>
                <td style="font-weight: 600; color: var(--accent-emerald);">${kpiScore}/40</td>
                <td style="font-weight: 700; color: var(--text-primary); font-size: 1.05rem;">${compositeScore}/100</td>
                <td><span class="verdict-badge ${verdictClass}">${verdict}</span></td>
            `;
            rankingsTableBody.appendChild(row);
        });
    }
});
