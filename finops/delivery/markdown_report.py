"""
finops/delivery/markdown_report.py — Markdown Report Generator
==============================================================
Renders high-clarity daily Top 20 opportunities reports with overnight trade plans.
"""

from finops.core.models import ScanReport


def generate_markdown_report(report: ScanReport) -> str:
    horizon_label = {
        "daily": "⚡ DAILY (1-3 Days Holding Period)",
        "weekly": "📈 WEEKLY (1-4 Weeks Holding Period)",
        "monthly": "🏛️ LONG-TERM (3-12 Months Compounding Horizon)"
    }.get(report.horizon, report.horizon.upper())

    lines = [
        f"# 🦅 finOps Stock Opportunities Report (Top 20) — {horizon_label}",
        f"",
        f"**Date:** {report.scan_date}  ",
        f"**Horizon Mode:** `{report.horizon.upper()}` ({horizon_label})  ",
        f"**Run Trigger:** NYSE/NASDAQ Close + 5.0h ({report.run_triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')})  ",
        f"**Target Execution Session:** {report.target_trade_session}  ",
        f"**Scanned Universe:** {report.scanned_universe_size} stocks across US, China A-Shares, and Mexico BMV  ",
        f"**Shortlist Analyzed:** {report.shortlist_count} stocks  ",
        f"",
        f"---",
        f"",
        f"## 🏆 Executive Summary: Top 20 Opportunities & Trade Plans ({report.horizon.capitalize()} Horizon)",
        f"",
        f"| Rank | Ticker | Name | Market | Price | Score | Horizon | Action | Limit Entry Zone | Stop Loss | Target 1 | R:R |",
        f"| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    for opp in report.top_20:
        p = opp.trade_plan
        curr = opp.currency
        lines.append(
            f"| **#{opp.rank}** | **{opp.ticker}** | {opp.name} | {opp.market.upper()} | "
            f"{curr} {opp.current_price:.2f} | **{opp.scores.composite_score:.1f}** | "
            f"{p.horizon.capitalize()} ({p.holding_period}) | `{p.action}` | "
            f"{curr} {p.entry_zone_low:.2f} - {p.entry_zone_high:.2f} | "
            f"{curr} {p.stop_loss:.2f} | {curr} {p.target_1:.2f} | **{p.risk_reward_ratio:.1f}x** |"
        )

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 🔬 In-Depth Analysis & Overnight Trade Directives",
        f""
    ])

    for opp in report.top_20:
        p = opp.trade_plan
        s = opp.scores
        curr = opp.currency

        lines.extend([
            f"### #{opp.rank} — {opp.ticker}: {opp.name} ({opp.sector})",
            f"",
            f"**Current Price:** {curr} {opp.current_price:.2f} | **Action Directive:** `{p.action}`  ",
            f"**Quantitative Breakdown:** Composite **{s.composite_score:.1f}** "
            f"(Fundamental: {s.fundamental_score:.1f} | Trend: {s.trend_score:.1f} | Sentiment: {s.sentiment_score:.1f})",
            f"",
            f"**Investment Thesis:**  ",
            f"> {opp.thesis_summary}",
            f"",
            f"#### 📋 Trade Plan ({p.horizon.capitalize()} Horizon)",
            f"- **Horizon & Duration:** **{p.horizon.capitalize()}** (Estimated holding period: **{p.holding_period}**)",
            f"- **Action:** `{p.action}`",
            f"- **Execution Envelope:** Limit order between **{curr} {p.entry_zone_low:.2f}** and **{curr} {p.entry_zone_high:.2f}**",
            f"- **Invalidation Stop Loss:** **{curr} {p.stop_loss:.2f}** (Strict thesis exit)",
            f"- **Primary Target 1:** **{curr} {p.target_1:.2f}** (Expected R:R: **{p.risk_reward_ratio:.1f}x**)",
            f"- **Extended Target 2 (Runner):** **{curr} {p.target_2:.2f}**",
            f"- **Suggested Sizing:** **{p.suggested_shares} shares** (Capital: {curr} {p.suggested_capital:,.2f} | Risk: {curr} {p.position_risk_amount:,.2f})",
            f"- **Execution Window:** {p.window}",
            f"- **Pre-Market Gap Rule:** If price opens > **{p.gap_rule_pct}%** beyond entry zone, cancel limit order immediately.",
        ])

        if p.event_risk_flags:
            lines.append(f"- **Event Risk Catalysts:**")
            for flag in p.event_risk_flags:
                lines.append(f"  - ⚠️ *{flag}*")

        lines.extend([
            f"",
            f"#### ⚖️ Bull vs Bear Debate",
            f"- **🐂 Bull Case:** {opp.bull_case}",
            f"- **🐻 Bear Case:** {opp.bear_case}",
            f"",
            f"**Key Catalysts:**",
            "".join([f"- {c}\n" for c in opp.catalysts]),
            f"**Key Downside Risks:**",
            "".join([f"- {r}\n" for r in opp.key_risks]),
            f"",
            f"---"
        ])

    lines.extend([
        f"",
        f"## ⚖️ Legal & Compliance Disclaimer",
        f"",
        f"> {report.disclaimer}",
        f""
    ])

    return "\n".join(lines)
