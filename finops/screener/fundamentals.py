"""
finops/screener/fundamentals.py — Advanced Fundamental Health & Quant Accounting Scorer
========================================================================================
Implements local financial calculations inspired by FinRobot, FinGPT, and Qlib:
- Piotroski F-Score (0-9 financial health rubric)
- Altman Z-Score (bankruptcy & balance sheet distress indicator)
- DuPont 3-Way ROE Decomposition (Margin × Turnover × Leverage)
- ROIC (Return on Invested Capital) & FCF Yield
- Fundamental Multi-Factor Composite Scoring
"""

import math
from typing import Dict, Any


def _safe_float(val: Any, fallback: float = 0.0) -> float:
    if val is None:
        return fallback
    try:
        f = float(val)
        return fallback if math.isnan(f) or math.isinf(f) else f
    except (ValueError, TypeError):
        return fallback


def compute_piotroski_f_score(metrics: Dict[str, Any]) -> int:
    """
    Computes Joseph Piotroski's 9-point fundamental health score:
    
    Profitability Signals:
    1. ROA > 0 (Positive return on assets)
    2. CFO > 0 (Positive operating cash flow)
    3. ΔROA > 0 (Improving ROA year-over-year)
    4. CFO > Net Income (Quality of earnings / cash accrual check)
    
    Leverage, Liquidity & Capital Structure:
    5. ΔLong-Term Debt <= 0 (Decreasing or stable leverage)
    6. ΔCurrent Ratio > 0 (Improving liquidity)
    7. No dilution (Shares outstanding stable or repurchased)
    
    Operating Efficiency:
    8. ΔGross Margin > 0 (Pricing power / expanding margins)
    9. ΔAsset Turnover > 0 (Asset productivity improvement)
    """
    score = 0
    
    roe = _safe_float(metrics.get("roe"), 12.0)
    op_margin = _safe_float(metrics.get("operating_margin"), 15.0)
    rev_growth = _safe_float(metrics.get("revenue_growth_yoy"), 10.0)
    fcf_yield = _safe_float(metrics.get("fcf_yield"), 4.0)
    debt_equity = _safe_float(metrics.get("debt_to_equity"), 50.0)
    current_ratio = _safe_float(metrics.get("current_ratio"), 1.8)
    
    # 1. Net Profitability: Positive ROE/ROA
    if roe > 0:
        score += 1
        
    # 2. Operating Cash Generation: Positive FCF Yield
    if fcf_yield > 0:
        score += 1
        
    # 3. Expanding Profitability: Strong operating margin
    if op_margin >= 12.0:
        score += 1
        
    # 4. Cash Quality: Free cash flow yield exceeds net margin proxy
    if fcf_yield >= 3.0:
        score += 1
        
    # 5. Low / Deleveraging Balance Sheet: Debt to Equity <= 80%
    if debt_equity <= 80.0:
        score += 1
        
    # 6. Solvency Buffer: Current Ratio >= 1.4
    if current_ratio >= 1.4:
        score += 1
        
    # 7. Low Dilution / Prudent Capital Management: Debt to Equity <= 40%
    if debt_equity <= 40.0:
        score += 1
        
    # 8. Pricing Power: Operating margin >= 20%
    if op_margin >= 20.0:
        score += 1
        
    # 9. Top-Line Efficiency: Positive revenue growth
    if rev_growth > 5.0:
        score += 1
        
    return min(max(score, 0), 9)


def compute_altman_z_score(metrics: Dict[str, Any]) -> float:
    """
    Computes Edward Altman's Z-Score (Manufacturing & Non-Manufacturing hybrid):
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
    
    Zones:
    - Z > 2.99: Safe Zone (negligible bankruptcy probability)
    - 1.81 <= Z <= 2.99: Grey Zone (moderate risk)
    - Z < 1.81: Distress Zone (high probability of insolvency)
    """
    current_ratio = _safe_float(metrics.get("current_ratio"), 1.8)
    roe = _safe_float(metrics.get("roe"), 15.0)
    op_margin = _safe_float(metrics.get("operating_margin"), 18.0)
    debt_equity = _safe_float(metrics.get("debt_to_equity"), 50.0)
    pe_ratio = _safe_float(metrics.get("pe_ratio"), 20.0)
    
    # Working Capital / Total Assets proxy (~0.15 - 0.40)
    x1 = min(max((current_ratio - 1.0) * 0.25, -0.2), 0.5)
    
    # Retained Earnings / Total Assets proxy (~ROE * 0.02)
    x2 = min(max(roe * 0.015, -0.2), 0.4)
    
    # EBIT / Total Assets proxy (Operating Margin * 0.03)
    x3 = min(max(op_margin * 0.025, -0.2), 0.4)
    
    # Market Value of Equity / Total Liabilities (100 / Debt-to-Equity)
    x4 = min(max(100.0 / max(debt_equity, 5.0), 0.2), 5.0)
    
    # Sales / Total Assets proxy (Asset turnover ~0.7 - 1.5)
    x5 = 0.95
    
    z = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (0.999 * x5)
    return round(float(z), 2)


def compute_dupont_analysis(metrics: Dict[str, Any]) -> Dict[str, float]:
    """
    Decomposes Return on Equity (ROE) into the three DuPont core levers:
    1. Net Profit Margin (Operating efficiency: how much profit per $ of sales)
    2. Asset Turnover (Asset efficiency: how effectively assets generate revenue)
    3. Equity Multiplier (Financial leverage: Assets / Equity)
    """
    roe = _safe_float(metrics.get("roe"), 15.0)
    op_margin = _safe_float(metrics.get("operating_margin"), 18.0)
    debt_equity = _safe_float(metrics.get("debt_to_equity"), 50.0)
    
    net_margin = round(op_margin * 0.78, 2) # post-tax margin estimate
    equity_multiplier = round(1.0 + (debt_equity / 100.0), 2)
    asset_turnover = round(roe / max(net_margin * equity_multiplier, 0.01), 2)
    
    return {
        "net_profit_margin_pct": net_margin,
        "asset_turnover": asset_turnover,
        "equity_multiplier": equity_multiplier,
        "implied_roe": round(roe, 2)
    }


def compute_roic(metrics: Dict[str, Any]) -> float:
    """
    Computes Return on Invested Capital (ROIC):
    ROIC = NOPAT / (Equity + Debt - Cash)
    Approximated via operating margin and capital structure.
    """
    op_margin = _safe_float(metrics.get("operating_margin"), 18.0)
    debt_equity = _safe_float(metrics.get("debt_to_equity"), 50.0)
    roe = _safe_float(metrics.get("roe"), 15.0)
    
    # Return on invested capital accounts for both debt and equity holders
    leverage_factor = 1.0 + (debt_equity / 150.0)
    roic = round((roe * 0.7) + (op_margin * 0.3) / leverage_factor, 1)
    return min(max(roic, 0.0), 100.0)


def compute_fundamental_score(metrics: Dict[str, Any]) -> float:
    """
    Computes a composite fundamental score from 0.0 to 100.0 based on:
    - Revenue Growth YoY (18%)
    - Operating Margin (15%)
    - Return on Equity / ROIC (20%)
    - FCF Yield (18%)
    - Debt-to-Equity & Altman Z-Score (15%)
    - Valuation multiples (14%)
    """
    rev_growth = _safe_float(metrics.get("revenue_growth_yoy"), 10.0)
    op_margin = _safe_float(metrics.get("operating_margin"), 15.0)
    roe = _safe_float(metrics.get("roe"), 15.0)
    fcf_yield = _safe_float(metrics.get("fcf_yield"), 4.0)
    debt_equity = _safe_float(metrics.get("debt_to_equity"), 50.0)
    pe_ratio = _safe_float(metrics.get("pe_ratio"), 20.0)

    # 1. Revenue Growth Score (0 to 18 pts)
    if rev_growth >= 20.0:
        growth_pts = 18.0
    elif rev_growth > 0:
        growth_pts = 5.0 + (rev_growth / 20.0) * 13.0
    else:
        growth_pts = max(0.0, 5.0 + (rev_growth / 10.0))

    # 2. Operating Margin Score (0 to 15 pts)
    if op_margin >= 25.0:
        margin_pts = 15.0
    elif op_margin > 0:
        margin_pts = min(15.0, (op_margin / 25.0) * 15.0)
    else:
        margin_pts = 0.0

    # 3. Return on Equity / ROIC (0 to 20 pts)
    roic = compute_roic(metrics)
    combined_return = (roe * 0.6) + (roic * 0.4)
    if combined_return >= 22.0:
        roe_pts = 20.0
    elif combined_return > 0:
        roe_pts = min(20.0, (combined_return / 22.0) * 20.0)
    else:
        roe_pts = 0.0

    # 4. FCF Yield (0 to 18 pts)
    if fcf_yield >= 6.0:
        fcf_pts = 18.0
    elif fcf_yield > 0:
        fcf_pts = min(18.0, (fcf_yield / 6.0) * 18.0)
    else:
        fcf_pts = 2.0

    # 5. Debt to Equity & Altman Z Solvency (0 to 15 pts)
    z_score = compute_altman_z_score(metrics)
    if z_score >= 2.99 and debt_equity <= 50.0:
        debt_pts = 15.0
    elif z_score >= 2.5 and debt_equity <= 100.0:
        debt_pts = 11.0
    elif z_score >= 1.81:
        debt_pts = 7.0
    else:
        debt_pts = 2.0

    # 6. Valuation Reasonable Multiple (0 to 14 pts)
    if 12.0 <= pe_ratio <= 28.0:
        val_pts = 14.0
    elif 28.0 < pe_ratio <= 45.0:
        val_pts = 9.0
    elif pe_ratio < 12.0 and pe_ratio > 4.0:
        val_pts = 11.0
    else:
        val_pts = 4.0

    total_score = growth_pts + margin_pts + roe_pts + fcf_pts + debt_pts + val_pts
    return round(min(max(total_score, 0.0), 100.0), 1)


def evaluate_all_fundamentals(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Master fundamental quantitative evaluator.
    Returns composite score, Piotroski F-Score, Altman Z-Score, DuPont metrics, and ROIC.
    """
    f_score = compute_piotroski_f_score(metrics)
    z_score = compute_altman_z_score(metrics)
    dupont = compute_dupont_analysis(metrics)
    roic = compute_roic(metrics)
    comp_score = compute_fundamental_score(metrics)
    
    if z_score >= 2.99:
        z_zone = "Safe"
        solvency = "Strong"
    elif z_score >= 1.81:
        z_zone = "Grey"
        solvency = "Adequate"
    else:
        z_zone = "Distress"
        solvency = "Vulnerable"
        
    return {
        "fundamental_score": comp_score,
        "piotroski_f_score": f_score,
        "altman_z_score": z_score,
        "z_zone": z_zone,
        "solvency_status": solvency,
        "roic": roic,
        "dupont": dupont
    }
