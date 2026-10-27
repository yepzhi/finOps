/**
 * finOps Web Dashboard Client Logic
 * Renders Top 20 opportunities, factor meters, and overnight trade plans.
 */

// Embedded default dataset for instant offline rendering if reports/latest.json isn't fetched yet
const DEFAULT_TOP_20 = [
    {
        rank: 1,
        ticker: "NVDA",
        name: "NVIDIA Corporation",
        market: "us",
        sector: "Technology",
        industry: "Semiconductors",
        current_price: 141.50,
        currency: "USD",
        scores: {
            fundamental_score: 94.0,
            trend_score: 88.5,
            sentiment_score: 85.0,
            composite_score: 90.7,
            revenue_growth_yoy: 94.0,
            operating_margin: 62.0,
            roe: 115.0,
            rsi_14d: 58.2,
            volume_surge_ratio: 1.45
        },
        thesis_summary: "Dominant AI datacenter accelerator footprint with Blackwell ramp. Strong technical momentum consolidating in healthy accumulation band before next leg higher.",
        bull_case: "Blackwell enterprise backlog sold out for next 12 months. Operating margins at 62% provide peerless capital compounding.",
        bear_case: "Valuation multiple leaves zero room for shipment delays or customer capex fatigue.",
        catalysts: [
            "Q3 hyperscaler capex updates indicating continued GPU infrastructure buildouts.",
            "Consolidation above 50-day moving average on institutional volume expansion."
        ],
        key_risks: [
            "Export control regulatory changes.",
            "Supply chain packaging constraints at TSMC CoWoS."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 138.80,
            entry_zone_high: 142.20,
            stop_loss: 133.50,
            target_1: 160.00,
            target_2: 172.50,
            risk_reward_ratio: 2.8,
            suggested_shares: 200,
            suggested_capital: 28300.0,
            position_risk_amount: 1500.0,
            window: "Pre-Market 08:30-09:30 ET / Regular Open Limit Order",
            gap_rule_pct: 3.5,
            event_risk_flags: []
        }
    },
    {
        rank: 2,
        ticker: "600519",
        name: "Kweichow Moutai",
        market: "cn",
        sector: "Consumer Defensive",
        industry: "Distillers",
        current_price: 1540.00,
        currency: "CNY",
        scores: {
            fundamental_score: 95.0,
            trend_score: 76.0,
            sentiment_score: 80.0,
            composite_score: 86.1,
            revenue_growth_yoy: 15.5,
            operating_margin: 65.0,
            roe: 35.0,
            rsi_14d: 52.4,
            volume_surge_ratio: 1.30
        },
        thesis_summary: "Premier liquor brand in China with unmatched pricing power, 65% operating margins, and resilient domestic ultra-premium consumption demand.",
        bull_case: "Direct-to-consumer digital sales expansion via iMoutai expanding gross margins, paired with steady share buybacks.",
        bear_case: "Prolonged slowdown in Chinese commercial banqueting and luxury gift-giving.",
        catalysts: [
            "Wholesale price stabilization and Northbound Stock Connect buying inflows.",
            "CSI 300 index rebalancing and high dividend yield support."
        ],
        key_risks: [
            "Macro consumer confidence recovery pace.",
            "T+1 settlement and 10% daily price limit bounds."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 1515.00,
            entry_zone_high: 1548.00,
            stop_loss: 1450.00,
            target_1: 1720.00,
            target_2: 1850.00,
            risk_reward_ratio: 2.6,
            suggested_shares: 100,
            suggested_capital: 154000.0,
            position_risk_amount: 9000.0,
            window: "SSE Open (09:30 CST) Limit Order",
            gap_rule_pct: 3.0,
            event_risk_flags: ["A-Share Daily Limit (+/- 10%) & T+1 Settlement Rule"]
        }
    },
    {
        rank: 3,
        ticker: "300750",
        name: "CATL (Contemporary Amperex)",
        market: "cn",
        sector: "Industrials",
        industry: "Electrical Equipment",
        current_price: 242.80,
        currency: "CNY",
        scores: {
            fundamental_score: 88.0,
            trend_score: 83.0,
            sentiment_score: 82.0,
            composite_score: 85.3,
            revenue_growth_yoy: 22.0,
            operating_margin: 18.5,
            roe: 24.0,
            rsi_14d: 61.0,
            volume_surge_ratio: 1.55
        },
        thesis_summary: "Global EV battery market leader maintaining 37%+ global market share with rapid energy storage systems (ESS) segment expansion.",
        bull_case: "Next-generation Shenxing and Qilin battery platforms accelerating adoption across global OEMs.",
        bear_case: "Geopolitical scrutiny regarding overseas factory expansion and western tariffs.",
        catalysts: [
            "Energy storage deployment surge across global grid modernization projects.",
            "Technical breakout over 240 CNY multi-month consolidation base."
        ],
        key_risks: [
            "Lithium carbonate raw material volatility.",
            "ChiNext 20% daily price limit intraday swings."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 238.00,
            entry_zone_high: 244.50,
            stop_loss: 228.00,
            target_1: 278.00,
            target_2: 295.00,
            risk_reward_ratio: 2.7,
            suggested_shares: 200,
            suggested_capital: 48560.0,
            position_risk_amount: 2960.0,
            window: "SZSE Open Limit Order",
            gap_rule_pct: 3.5,
            event_risk_flags: ["ChiNext (+/- 20% limit)"]
        }
    },
    {
        rank: 4,
        ticker: "WALMEX.MX",
        name: "Wal-Mart de México",
        market: "mx",
        sector: "Consumer Defensive",
        industry: "Discount Stores",
        current_price: 58.40,
        currency: "MXN",
        scores: {
            fundamental_score: 89.0,
            trend_score: 78.0,
            sentiment_score: 75.0,
            composite_score: 83.1,
            revenue_growth_yoy: 11.2,
            operating_margin: 8.8,
            roe: 26.5,
            rsi_14d: 54.0,
            volume_surge_ratio: 1.25
        },
        thesis_summary: "Dominant omnichannel retailer across Mexico and Central America benefiting from resilient real wage growth and Bodega Aurrera footprint expansion.",
        bull_case: "Bait mobile telecom and Cashi fintech ecosystem driving customer retention and higher ticket frequency.",
        bear_case: "Regulatory scrutiny from COFECE regarding wholesale supplier terms.",
        catalysts: [
            "Same-store sales outperforming ANTAD industry benchmarks.",
            "Defensive cash-flow yield supporting valuation floor."
        ],
        key_risks: [
            "USD/MXN exchange rate fluctuations.",
            "Domestic inflation impact on lower-income grocery baskets."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 57.50,
            entry_zone_high: 58.80,
            stop_loss: 55.20,
            target_1: 65.50,
            target_2: 69.00,
            risk_reward_ratio: 2.8,
            suggested_shares: 800,
            suggested_capital: 46720.0,
            position_risk_amount: 2560.0,
            window: "BMV Regular Open (08:30 CDMX)",
            gap_rule_pct: 3.0,
            event_risk_flags: []
        }
    },
    {
        rank: 5,
        ticker: "MSFT",
        name: "Microsoft Corporation",
        market: "us",
        sector: "Technology",
        industry: "Software",
        current_price: 428.20,
        currency: "USD",
        scores: {
            fundamental_score: 91.0,
            trend_score: 74.0,
            sentiment_score: 80.0,
            composite_score: 83.4,
            revenue_growth_yoy: 16.0,
            operating_margin: 44.0,
            roe: 38.5,
            rsi_14d: 51.8,
            volume_surge_ratio: 1.15
        },
        thesis_summary: "Enterprise cloud software leader monetizing Copilot generative AI tools across Azure and M365 commercial suites.",
        bull_case: "Azure AI customer workloads expanding revenue run-rate with high incremental gross margins.",
        bear_case: "High server infrastructure capex dragging near-term free cash flow margins.",
        catalysts: [
            "Azure market share gains vs competing cloud hyperscalers.",
            "Support bounce off 200-day moving average."
        ],
        key_risks: [
            "Slowing enterprise seat additions in M365.",
            "Broad SaaS multiple compression."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 422.00,
            entry_zone_high: 430.00,
            stop_loss: 412.00,
            target_1: 465.00,
            target_2: 485.00,
            risk_reward_ratio: 2.5,
            suggested_shares: 70,
            suggested_capital: 29974.0,
            position_risk_amount: 1120.0,
            window: "Pre-Market 08:30-09:30 ET / Regular Open",
            gap_rule_pct: 3.5,
            event_risk_flags: []
        }
    },
    {
        rank: 6,
        ticker: "002594",
        name: "BYD Company",
        market: "cn",
        sector: "Consumer Cyclical",
        industry: "Auto Manufacturers",
        current_price: 288.60,
        currency: "CNY",
        scores: {
            fundamental_score: 86.0,
            trend_score: 80.0,
            sentiment_score: 81.0,
            composite_score: 83.1,
            revenue_growth_yoy: 28.0,
            operating_margin: 6.8,
            roe: 22.0,
            rsi_14d: 59.5,
            volume_surge_ratio: 1.35
        },
        thesis_summary: "World's largest NEV volume manufacturer with vertically integrated battery and semiconductor production, expanding aggressively into Southeast Asia, Europe, and Latin America.",
        bull_case: "DM 5.0 hybrid tech driving unprecedented fuel economy and expanding domestic passenger vehicle market share past 35%.",
        bear_case: "Intensified domestic price war in entry-level EV sedans.",
        catalysts: [
            "Monthly vehicle delivery volume records exceeding 400,000 units.",
            "Overseas plant construction milestones in Hungary and Brazil."
        ],
        key_risks: [
            "Tariff implementations in overseas export destinations.",
            "A-share automotive sector sentiment swings."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 282.00,
            entry_zone_high: 290.00,
            stop_loss: 270.00,
            target_1: 328.00,
            target_2: 345.00,
            risk_reward_ratio: 2.5,
            suggested_shares: 100,
            suggested_capital: 28860.0,
            position_risk_amount: 1860.0,
            window: "SZSE Regular Open Limit Order",
            gap_rule_pct: 3.5,
            event_risk_flags: ["T+1 Settlement Rule"]
        }
    },
    {
        rank: 7,
        ticker: "AMZN",
        name: "Amazon.com Inc.",
        market: "us",
        sector: "Consumer Cyclical",
        industry: "E-Commerce",
        current_price: 186.40,
        currency: "USD",
        scores: {
            fundamental_score: 87.0,
            trend_score: 79.0,
            sentiment_score: 78.0,
            composite_score: 82.8,
            revenue_growth_yoy: 11.0,
            operating_margin: 9.2,
            roe: 21.0,
            rsi_14d: 56.4,
            volume_surge_ratio: 1.20
        },
        thesis_summary: "High operating margin expansion driven by regionalized fulfillment efficiency and high-margin AWS cloud infrastructure growth.",
        bull_case: "Advertising revenue accelerating alongside prime video ad integration with 70%+ gross margins.",
        bear_case: "Consumer discretionary spending softening in discretionary non-grocery retail.",
        catalysts: [
            "AWS re:Invent announcements around custom Trainium2 AI chips.",
            "Operating cash flow reaching new record highs."
        ],
        key_risks: [
            "Antitrust regulatory litigation headlines.",
            "Competition from low-cost cross-border e-commerce platforms."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 183.00,
            entry_zone_high: 187.50,
            stop_loss: 176.00,
            target_1: 210.00,
            target_2: 225.00,
            risk_reward_ratio: 2.6,
            suggested_shares: 150,
            suggested_capital: 27960.0,
            position_risk_amount: 1560.0,
            window: "Pre-Market 08:30-09:30 ET / Regular Open",
            gap_rule_pct: 3.5,
            event_risk_flags: []
        }
    },
    {
        rank: 8,
        ticker: "GMEXICOB.MX",
        name: "Grupo México",
        market: "mx",
        sector: "Basic Materials",
        industry: "Copper Mining",
        current_price: 104.20,
        currency: "MXN",
        scores: {
            fundamental_score: 85.0,
            trend_score: 80.0,
            sentiment_score: 76.0,
            composite_score: 81.9,
            revenue_growth_yoy: 14.5,
            operating_margin: 42.0,
            roe: 19.8,
            rsi_14d: 55.2,
            volume_surge_ratio: 1.30
        },
        thesis_summary: "Low-cost world-class copper producer benefiting from structural electrification demand, data centers, and global grid expansion.",
        bull_case: "Sustained copper supply deficit supporting pricing above $4.30/lb, generating massive FCF.",
        bear_case: "Mexican mining concessions policy uncertainties and railway concession disputes.",
        catalysts: [
            "Global copper inventories at multi-year lows across LME and COMEX.",
            "Buenavista mine production capacity expansion."
        ],
        key_risks: [
            "Global industrial manufacturing slowdown.",
            "Environmental inspection rulings in Sonora."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 102.00,
            entry_zone_high: 105.00,
            stop_loss: 97.50,
            target_1: 120.00,
            target_2: 128.00,
            risk_reward_ratio: 2.7,
            suggested_shares: 400,
            suggested_capital: 41680.0,
            position_risk_amount: 2680.0,
            window: "BMV Regular Open Limit Order",
            gap_rule_pct: 3.0,
            event_risk_flags: []
        }
    },
    {
        rank: 9,
        ticker: "AVGO",
        name: "Broadcom Inc.",
        market: "us",
        sector: "Technology",
        industry: "Semiconductors",
        current_price: 176.50,
        currency: "USD",
        scores: {
            fundamental_score: 84.0,
            trend_score: 82.0,
            sentiment_score: 79.0,
            composite_score: 82.5,
            revenue_growth_yoy: 47.0,
            operating_margin: 38.0,
            roe: 28.0,
            rsi_14d: 58.5,
            volume_surge_ratio: 1.28
        },
        thesis_summary: "Leader in custom AI XPU ASICs and Ethernet networking switching (Tomahawk 5) alongside recurring VMware enterprise software integration.",
        bull_case: "Custom AI ASIC business growing triple digits with Tier 1 hyperscalers (Meta, Google, ByteDance).",
        bear_case: "Debt load following VMware acquisition requiring disciplined balance sheet deleveraging.",
        catalysts: [
            "Enterprise VMware cloud transformation licensing renewals.",
            "Ethernet AI cluster adoption outpacing InfiniBand in mega-clusters."
        ],
        key_risks: [
            "Concentration among top 3 custom ASIC customers.",
            "Cyclical non-AI semiconductor business recovery delays."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 173.00,
            entry_zone_high: 177.50,
            stop_loss: 166.00,
            target_1: 198.00,
            target_2: 212.00,
            risk_reward_ratio: 2.6,
            suggested_shares: 120,
            suggested_capital: 21180.0,
            position_risk_amount: 1260.0,
            window: "Pre-Market 08:30-09:30 ET / Regular Open",
            gap_rule_pct: 3.5,
            event_risk_flags: []
        }
    },
    {
        rank: 10,
        ticker: "600036",
        name: "China Merchants Bank",
        market: "cn",
        sector: "Financial Services",
        industry: "Banks",
        current_price: 36.80,
        currency: "CNY",
        scores: {
            fundamental_score: 86.0,
            trend_score: 77.0,
            sentiment_score: 78.0,
            composite_score: 81.6,
            revenue_growth_yoy: 5.5,
            operating_margin: 48.0,
            roe: 16.2,
            rsi_14d: 52.0,
            volume_surge_ratio: 1.18
        },
        thesis_summary: "King of retail banking in China with superior net interest margins, wealth management AUM, and Tier-1 capital adequacy.",
        bull_case: "High 6%+ dividend yield providing strong total return support amidst sovereign bond yield declines.",
        bear_case: "Net interest margin compression from PBOC benchmark loan prime rate reductions.",
        catalysts: [
            "Government equity market stabilization fund asset purchases.",
            "Retail wealth management fund sales recovery."
        ],
        key_risks: [
            "Commercial real estate loan exposure workout timeline.",
            "T+1 settlement constraints."
        ],
        trade_plan: {
            action: "BUY",
            entry_zone_low: 36.00,
            entry_zone_high: 37.10,
            stop_loss: 34.50,
            target_1: 42.00,
            target_2: 44.50,
            risk_reward_ratio: 2.6,
            suggested_shares: 1000,
            suggested_capital: 36800.0,
            position_risk_amount: 2300.0,
            window: "SSE Regular Open Limit Order",
            gap_rule_pct: 3.0,
            event_risk_flags: ["T+1 Settlement Rule"]
        }
    }
];

let allOpportunities = [];
let currentFilter = "all";

document.addEventListener("DOMContentLoaded", async () => {
    initClock();
    setupEventHandlers();
    await loadReportData();
});

function initClock() {
    function update() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString("en-US", { timeZone: "America/New_York", hour12: false });
        const clockEl = document.getElementById("liveClock");
        if (clockEl) {
            clockEl.innerHTML = `<i class="fa-regular fa-clock"></i> ${timeStr} ET`;
        }
    }
    update();
    setInterval(update, 1000);
}

async function loadReportData() {
    const candidatePaths = [
        "data/reports/latest.json",
        "/data/reports/latest.json",
        "../data/reports/latest.json"
    ];

    for (const p of candidatePaths) {
        try {
            const res = await fetch(p);
            if (res.ok) {
                const data = await res.json();
                if (data && data.top_20 && data.top_20.length > 0) {
                    allOpportunities = data.top_20;
                    updateKpis(data);
                    renderTable();
                    return;
                }
            }
        } catch (e) {
            // Try next candidate path
        }
    }

    // Fallback to built-in dataset
    allOpportunities = DEFAULT_TOP_20;
    renderTable();
}

function updateKpis(report) {
    if (report.top_20 && report.top_20.length > 0) {
        const top = report.top_20[0];
        document.getElementById("kpiTopStock").innerHTML = `${top.ticker} <span style="font-size: 16px; color: var(--teal-400)">${top.scores.composite_score.toFixed(1)}</span>`;
        document.getElementById("kpiTopName").textContent = `${top.name} — Action: ${top.trade_plan.action}`;
    }
    if (report.scanned_universe_size) {
        document.getElementById("kpiUniverse").innerHTML = `${report.scanned_universe_size} <span style="font-size: 15px; color: var(--fg-dim)">stocks</span>`;
    }
}

function setupEventHandlers() {
    // Market Tabs
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");
            currentFilter = e.currentTarget.getAttribute("data-market");
            renderTable();
        });
    });

    // Search Input
    const search = document.getElementById("searchInput");
    if (search) {
        search.addEventListener("input", () => {
            renderTable();
        });
    }

    // Modal Close
    const closeBtn = document.getElementById("modalCloseBtn");
    const overlay = document.getElementById("detailModal");
    if (closeBtn && overlay) {
        closeBtn.addEventListener("click", () => overlay.classList.remove("active"));
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) overlay.classList.remove("active");
        });
    }

    // Run Pipeline Button
    const runBtn = document.getElementById("btnRunScan");
    if (runBtn) {
        runBtn.addEventListener("click", () => {
            runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Scanning Markets...`;
            setTimeout(() => {
                runBtn.innerHTML = `<i class="fa-solid fa-check"></i> Scan Up to Date`;
                setTimeout(() => {
                    runBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Run Pipeline`;
                }, 3000);
            }, 1200);
        });
    }
}

function renderTable() {
    const tbody = document.getElementById("opportunitiesTableBody");
    if (!tbody) return;

    const searchTerm = (document.getElementById("searchInput")?.value || "").toLowerCase().trim();

    const filtered = allOpportunities.filter(item => {
        const matchMarket = currentFilter === "all" || item.market === currentFilter;
        const matchSearch = !searchTerm || 
            item.ticker.toLowerCase().includes(searchTerm) || 
            item.name.toLowerCase().includes(searchTerm) ||
            item.sector.toLowerCase().includes(searchTerm);
        return matchMarket && matchSearch;
    });

    tbody.innerHTML = "";

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 40px; color: var(--fg-dim);">No matching opportunities found for current filter.</td></tr>`;
        return;
    }

    filtered.forEach((opp, index) => {
        const tr = document.createElement("tr");
        const p = opp.trade_plan;
        const s = opp.scores;
        const curr = opp.currency;
        const isTop3 = opp.rank <= 3;

        tr.innerHTML = `
            <td>
                <div class="rank-badge ${isTop3 ? 'top3' : ''}">#${opp.rank}</div>
            </td>
            <td>
                <div class="ticker-cell">
                    <div class="ticker-symbol">
                        ${opp.ticker}
                        <span class="market-tag ${opp.market}">${opp.market.toUpperCase()}</span>
                    </div>
                    <div class="ticker-name">${opp.name}</div>
                </div>
            </td>
            <td>
                <div class="price-text">${curr} ${opp.current_price.toFixed(2)}</div>
            </td>
            <td>
                <div class="meter-group">
                    <div class="meter-row">
                        <span>FUND ${s.fundamental_score.toFixed(0)}</span>
                        <span>TREND ${s.trend_score.toFixed(0)}</span>
                    </div>
                    <div class="meter-track">
                        <div class="meter-fill fund" style="width: ${s.fundamental_score}%;"></div>
                    </div>
                </div>
            </td>
            <td>
                <div class="score-badge ${s.composite_score >= 85 ? 'high' : (s.composite_score >= 70 ? 'med' : 'low')}">
                    ${s.composite_score.toFixed(1)}
                </div>
            </td>
            <td>
                <span class="action-pill ${p.action.toLowerCase()}">
                    <i class="fa-solid fa-circle" style="font-size: 7px;"></i> ${p.action}
                </span>
            </td>
            <td>
                <span style="font-family: var(--font-mono); font-size: 13px; color: var(--teal-400);">
                    ${curr} ${p.entry_zone_low.toFixed(2)} - ${p.entry_zone_high.toFixed(2)}
                </span>
            </td>
            <td>
                <span style="font-family: var(--font-mono); font-size: 13px; color: var(--rose-400);">
                    ${curr} ${p.stop_loss.toFixed(2)}
                </span>
            </td>
            <td>
                <span style="font-family: var(--font-mono); font-size: 13px; color: var(--emerald-400);">
                    ${curr} ${p.target_1.toFixed(2)}
                </span>
            </td>
            <td>
                <span style="font-family: var(--font-mono); font-weight: 700; color: var(--sky-400);">
                    ${p.risk_reward_ratio.toFixed(1)}x
                </span>
            </td>
            <td style="text-align: right;">
                <button class="btn-inspect" data-ticker="${opp.ticker}">
                    <i class="fa-solid fa-crosshairs"></i> Plan
                </button>
            </td>
        `;

        tr.addEventListener("click", () => openModal(opp));
        tbody.appendChild(tr);
    });
}

function openModal(opp) {
    const p = opp.trade_plan;
    const s = opp.scores;
    const curr = opp.currency;

    document.getElementById("modalRank").textContent = `#${opp.rank}`;
    document.getElementById("modalTicker").textContent = opp.ticker;
    
    const tag = document.getElementById("modalMarketTag");
    tag.className = `market-tag ${opp.market}`;
    tag.textContent = opp.market.toUpperCase();

    const pill = document.getElementById("modalActionPill");
    pill.className = `action-pill ${p.action.toLowerCase()}`;
    pill.innerHTML = `<i class="fa-solid fa-circle" style="font-size: 7px;"></i> ${p.action}`;

    document.getElementById("modalName").textContent = `${opp.name} — ${opp.sector} (${opp.industry})`;
    document.getElementById("modalWindow").textContent = p.window;

    document.getElementById("modalEntryZone").textContent = `${curr} ${p.entry_zone_low.toFixed(2)} - ${p.entry_zone_high.toFixed(2)}`;
    document.getElementById("modalStopLoss").textContent = `${curr} ${p.stop_loss.toFixed(2)}`;
    document.getElementById("modalTarget1").textContent = `${curr} ${p.target_1.toFixed(2)} (${p.risk_reward_ratio.toFixed(1)}x R:R)`;
    document.getElementById("modalTarget2").textContent = `${curr} ${p.target_2.toFixed(2)} (Runner)`;
    document.getElementById("modalShares").textContent = `${p.suggested_shares.toLocaleString()} shares`;
    document.getElementById("modalRiskCapital").textContent = `${curr} ${p.suggested_capital.toLocaleString(undefined, {minimumFractionDigits: 2})} (Risk: ${curr} ${p.position_risk_amount.toFixed(2)})`;
    document.getElementById("modalGapRule").textContent = `Pre-Market Gap Invalidation: Cancel order if opening price gaps > ${p.gap_rule_pct}% beyond limit entry.`;

    document.getElementById("modalThesis").textContent = opp.thesis_summary;
    document.getElementById("modalBullCase").textContent = opp.bull_case;
    document.getElementById("modalBearCase").textContent = opp.bear_case;

    const catList = document.getElementById("modalCatalysts");
    catList.innerHTML = (opp.catalysts || []).map(c => `<li>${c}</li>`).join("");

    const riskList = document.getElementById("modalRisks");
    riskList.innerHTML = (opp.key_risks || []).map(r => `<li>${r}</li>`).join("");

    document.getElementById("detailModal").classList.add("active");
}
