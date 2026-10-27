# 🦅 finOps — Daily Stock Opportunities Platform (Top 20)

Institutional quantitative stock scanning, multi-factor ranking, and overnight trade planning platform for **United States**, **China Mainland A-Shares**, and **Mexico BMV (Bolsa Mexicana de Valores)**.

Designed after open-source architectures (`daily_stock_analysis`, `TradingAgents`, `ai-hedge-fund`) with a deterministic quantitative engine first, multi-agent LLM debate, and a cyber-glass web dashboard styled after the **stemOS Teacher Portal**.

---

## 🏛️ System Architecture

```
                   ┌────────────────────────────────────────┐
  Schedule (daily) │  Exchange Close + 5h (21:00 ET / XNYS) │
                   └───────────────────┬────────────────────┘
                                       ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 1. MULTI-MARKET UNIVERSE & DATA (Modular Plug-in Layer)                │
 │    - United States: NYSE & NASDAQ (yfinance / OpenBB adapter)          │
 │    - China A-Shares: SSE & SZSE (akshare / yfinance, T+1, price limits)│
 │    - Mexico BMV: S&P/BMV IPC (yfinance .MX, MXN currency, XMEX)        │
 │    - Extensible plugin interface (BaseMarketPlugin)                    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 2. DETERMINISTIC QUANTITATIVE SCREENER & FACTOR SCORING               │
 │    - Fundamentals (50%): Rev growth, operating margins, ROE, FCF, D/E  │
 │    - Trend/Momentum (35%): MA50/200, Golden Cross, 14D RSI, MACD, Vol │
 │    - Sentiment (15%): News catalysts, Reddit, Xueqiu, East Money      │
 │    - Sector & Market Normalization -> Shortlist -> Top 20 Candidates   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 3. DEEP DIVE & OVERNIGHT TRADE PLAN GENERATOR                          │
 │    - Multi-Agent Debate: Bull Researcher vs. Bear Researcher           │
 │    - Limit Order Entry Envelope (bid buffer towards technical support) │
 │    - Strict Invalidation Stop Loss (1.5x ATR & 20-day swing low)       │
 │    - Profit Targets: Target 1 (Conservative 2.5x R:R) & Target 2 Runner│
 │    - Position Sizing: Configurable portfolio risk rule (1.5% max risk) │
 │    - Pre-Market Gap Rule: Cancel limit order if opening gaps > 3.5%    │
 │    - Event Risk Flags: After-hours earnings releases, board lot limits │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 4. DELIVERY & DASHBOARD                                                │
 │    - Markdown & JSON daily report archiving (data/reports/)            │
 │    - Cyber-Glass Interactive Web Dashboard (stemOS design tokens)      │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Installation
Ensure `uv` is installed, then clone and initialize:
```bash
git clone https://github.com/yepzhi/finOps.git
cd finOps
uv sync
```

### 2. Run the Daily Scan
Run the complete scanning and analysis pipeline across all enabled markets:
```bash
# Run full scan across US, China, and Mexico
uv run python -m finops.cli scan

# Run test scan with 5 candidates per market
uv run python -m finops.cli scan --limit 5

# Run scan strictly for a specific market
uv run python -m finops.cli scan --market us
uv run python -m finops.cli scan --market cn
uv run python -m finops.cli scan --market mx
```

### 3. Verify Exchange Schedule & Run Trigger
Calculate the exact `close + 5 hours` trigger time based on exchange calendars (`exchange_calendars` handles early closures, holidays, weekends, and dynamic daylight saving time automatically):
```bash
uv run python -m finops.cli schedule --offset 5.0
```

### 4. Launch the Interactive Web Dashboard
Serve the cyber-glass dashboard on `http://localhost:8080`:
```bash
uv run python -m finops.cli serve --port 8080
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

---

## 📋 Overnight Trade Plan Schema

For each of the Top 20 opportunities, an actionable plan for the **next regular session** is generated:

| Field | Description | Formula / Rule |
|---|---|---|
| **Action** | Action directive | `BUY` (Score >= 70 & no event block), `WATCH` (55-69), `AVOID` (< 55) |
| **Limit Entry Zone** | Price envelope for limit orders | Bid envelope between Support buffer and Current Price |
| **Invalidation Stop** | Price where thesis is wrong | Sited below 20-day swing low with 1.5x ATR buffer |
| **Target 1 (Conservative)** | Primary technical target | `Entry + (RiskPerShare * 2.5)` (Minimum 1:2.5 R:R) |
| **Target 2 (Runner)** | Extended momentum target | `Entry + (RiskPerShare * 4.0)` |
| **Position Sizing** | Calculated share quantity | `(PortfolioEquity * RiskPct) / (Entry - Stop)` |
| **Pre-Market Gap Rule** | Order cancellation threshold | If pre-market gaps > **3.5%** beyond limit entry, cancel order |
| **Event Risk Flags** | High volatility catalysts | Flags after-hours earnings releases and board lot constraints |

---

## 🧪 Testing

Run the test suite:
```bash
uv run pytest
```

---

## ⚖️ Legal & Compliance Disclaimer

> **DISCLAIMER:** This software is an algorithmic quantitative research platform developed strictly for simulation and educational modeling purposes. It **DOES NOT** provide financial, investment, legal, or tax advice. No automated order execution is conducted. Trading stocks involves substantial risk of loss. Overnight trade plans represent quantitative scenario models with limit envelopes and strict stop-loss bounds.
