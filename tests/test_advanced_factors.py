"""
tests/test_advanced_factors.py — Tests for Piotroski, Altman Z, DuPont, ADX, Bollinger, CMF & Backtester
"""

import pandas as pd
import numpy as np
import pytest

from finops.screener.fundamentals import (
    compute_piotroski_f_score,
    compute_altman_z_score,
    compute_dupont_analysis,
    compute_roic,
    evaluate_all_fundamentals
)
from finops.screener.technicals import (
    calculate_adx,
    calculate_bollinger_bands,
    calculate_chaikin_money_flow,
    calculate_stochastic,
    compute_technical_indicators
)
from finops.backtest.engine import BacktestEngine


def test_piotroski_f_score():
    # Strong company: positive ROE, high FCF, strong margins, conservative debt, high current ratio
    strong_data = {
        "roe": 28.0,
        "fcf_yield": 6.5,
        "operating_margin": 32.0,
        "debt_to_equity": 25.0,
        "current_ratio": 2.4,
        "revenue_growth_yoy": 22.0
    }
    score_strong = compute_piotroski_f_score(strong_data)
    assert score_strong >= 8, f"Expected strong F-Score >= 8, got {score_strong}"

    # Weak / distressed company: negative ROE, negative FCF, thin margins, high leverage
    weak_data = {
        "roe": -15.0,
        "fcf_yield": -3.0,
        "operating_margin": 2.0,
        "debt_to_equity": 220.0,
        "current_ratio": 0.8,
        "revenue_growth_yoy": -8.0
    }
    score_weak = compute_piotroski_f_score(weak_data)
    assert score_weak <= 2, f"Expected weak F-Score <= 2, got {score_weak}"


def test_altman_z_score_and_master_evaluator():
    safe_data = {
        "current_ratio": 2.8,
        "roe": 26.0,
        "operating_margin": 28.0,
        "debt_to_equity": 20.0,
        "pe_ratio": 24.0,
        "fcf_yield": 5.5,
        "revenue_growth_yoy": 18.0
    }
    z_safe = compute_altman_z_score(safe_data)
    assert z_safe >= 2.99, f"Expected Safe Z-score >= 2.99, got {z_safe}"

    eval_safe = evaluate_all_fundamentals(safe_data)
    assert eval_safe["z_zone"] == "Safe"
    assert eval_safe["piotroski_f_score"] >= 8
    assert eval_safe["fundamental_score"] >= 80.0

    distress_data = {
        "current_ratio": 0.6,
        "roe": -25.0,
        "operating_margin": -10.0,
        "debt_to_equity": 250.0,
        "pe_ratio": 8.0,
        "fcf_yield": -4.0,
        "revenue_growth_yoy": -15.0
    }
    z_distress = compute_altman_z_score(distress_data)
    assert z_distress < 1.81, f"Expected Distress Z-score < 1.81, got {z_distress}"

    eval_distress = evaluate_all_fundamentals(distress_data)
    assert eval_distress["z_zone"] == "Distress"
    assert eval_distress["piotroski_f_score"] <= 2


def test_dupont_and_roic():
    company = {
        "operating_margin": 24.0,
        "roe": 28.0,
        "debt_to_equity": 40.0
    }
    dupont = compute_dupont_analysis(company)
    assert "implied_roe" in dupont
    assert "net_profit_margin_pct" in dupont
    assert "equity_multiplier" in dupont
    assert "asset_turnover" in dupont
    assert dupont["implied_roe"] == 28.0
    assert dupont["equity_multiplier"] == 1.4

    roic = compute_roic(company)
    assert roic > 0.0


def test_advanced_technical_indicators():
    np.random.seed(42)
    t = np.linspace(0, 10, 100)
    prices = 100 + 5 * t + np.sin(t) * 4
    highs = prices + np.random.uniform(1, 3, 100)
    lows = prices - np.random.uniform(1, 3, 100)
    opens = prices + np.random.uniform(-1, 1, 100)
    volumes = np.random.uniform(500000, 2000000, 100)

    df = pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": prices,
        "Volume": volumes
    })

    # Test ADX (returns adx, plus_di, minus_di)
    adx, plus_di, minus_di = calculate_adx(df, period=14)
    assert len(adx) == 100
    assert adx.iloc[-1] >= 0.0

    # Test Bollinger Bands (returns middle, upper, lower, pct_b, bandwidth)
    middle, upper, lower, pct_b, bandwidth = calculate_bollinger_bands(df["Close"], period=20, num_std=2.0)
    assert len(pct_b) == 100
    assert len(bandwidth) == 100

    # Test CMF (returns Series)
    cmf = calculate_chaikin_money_flow(df, period=20)
    assert len(cmf) == 100

    # Test Stochastic (returns k_fast, d_slow)
    k_fast, d_slow = calculate_stochastic(df, k_period=14, d_period=3)
    assert len(k_fast) == 100
    assert len(d_slow) == 100

    # Full technical indicator suite
    full_indicators = compute_technical_indicators(df)
    assert "adx_14" in full_indicators
    assert "trend_strength" in full_indicators
    assert "cmf_20" in full_indicators
    assert "bb_pct_b" in full_indicators
    assert "bb_bandwidth" in full_indicators
    assert "stoch_k" in full_indicators


def test_backtest_engine():
    engine = BacktestEngine()
    results = engine.run_backtest(max_reports=10)
    assert "total_trades_analyzed" in results
    assert "win_rate_pct" in results
    assert "profit_factor" in results
    assert "avg_trade_return_pct" in results
    assert "performance_by_horizon" in results
    assert "performance_by_market" in results
    assert results["total_trades_analyzed"] > 0
