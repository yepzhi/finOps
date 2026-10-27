"""
finops/screener/fundamentals.py — Fundamental Health & Quality Scorer
=====================================================================
Scores company profitability, capital efficiency, balance sheet safety, and valuation.
"""

from typing import Dict, Any


def compute_fundamental_score(metrics: Dict[str, Any]) -> float:
    """
    Computes a composite fundamental score from 0.0 to 100.0 based on:
    - Revenue Growth YoY (20%)
    - Operating Margin (15%)
    - Return on Equity (20%)
    - FCF Yield (20%)
    - Debt-to-Equity discipline (10%)
    - Valuation multiples (15%)
    """
    rev_growth = metrics.get("revenue_growth_yoy", 10.0)
    op_margin = metrics.get("operating_margin", 15.0)
    roe = metrics.get("roe", 15.0)
    fcf_yield = metrics.get("fcf_yield", 4.0)
    debt_equity = metrics.get("debt_to_equity", 50.0)
    pe_ratio = metrics.get("pe_ratio", 20.0)

    # 1. Revenue Growth Score (0 to 20 pts)
    # >20% = 20 pts, 10% = 14 pts, 0% = 6 pts, negative = 0 pts
    if rev_growth >= 20.0:
        growth_pts = 20.0
    elif rev_growth > 0:
        growth_pts = 6.0 + (rev_growth / 20.0) * 14.0
    else:
        growth_pts = max(0.0, 6.0 + (rev_growth / 10.0))

    # 2. Operating Margin Score (0 to 15 pts)
    # >25% = 15 pts, 15% = 10 pts, <5% = 3 pts
    if op_margin >= 25.0:
        margin_pts = 15.0
    elif op_margin > 0:
        margin_pts = min(15.0, (op_margin / 25.0) * 15.0)
    else:
        margin_pts = 0.0

    # 3. Return on Equity (ROE) (0 to 20 pts)
    # >25% = 20 pts, 15% = 13 pts, <5% = 3 pts
    if roe >= 25.0:
        roe_pts = 20.0
    elif roe > 0:
        roe_pts = min(20.0, (roe / 25.0) * 20.0)
    else:
        roe_pts = 0.0

    # 4. FCF Yield (0 to 20 pts)
    # >6% = 20 pts, 3-6% = 14 pts, <1% = 4 pts
    if fcf_yield >= 6.0:
        fcf_pts = 20.0
    elif fcf_yield > 0:
        fcf_pts = min(20.0, (fcf_yield / 6.0) * 20.0)
    else:
        fcf_pts = 2.0

    # 5. Debt to Equity (0 to 10 pts, lower is better)
    # <50 = 10 pts, 50-100 = 7 pts, >200 = 2 pts
    if debt_equity <= 40.0:
        debt_pts = 10.0
    elif debt_equity <= 100.0:
        debt_pts = 7.0
    elif debt_equity <= 200.0:
        debt_pts = 4.0
    else:
        debt_pts = 1.0

    # 6. Valuation Reasonable Multiple (0 to 15 pts)
    # PE between 12 and 28 is healthy sweet spot
    if 12.0 <= pe_ratio <= 28.0:
        val_pts = 15.0
    elif 28.0 < pe_ratio <= 45.0:
        val_pts = 10.0
    elif pe_ratio < 12.0 and pe_ratio > 4.0:
        val_pts = 12.0
    else:
        val_pts = 5.0

    total_score = growth_pts + margin_pts + roe_pts + fcf_pts + debt_pts + val_pts
    return round(min(max(total_score, 0.0), 100.0), 1)
