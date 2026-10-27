"""
tests/test_screener.py — Unit Tests for Quantitative Screener & Calendars
"""

import pandas as pd
import numpy as np
from datetime import date
from finops.screener.technicals import compute_technical_indicators
from finops.screener.fundamentals import compute_fundamental_score
from finops.core.calendar import MarketCalendarService
from finops.markets.factory import get_market_plugin


def test_calendar_service_us():
    cal = MarketCalendarService("XNYS")
    assert cal is not None
    next_s = cal.get_next_trading_session()
    assert isinstance(next_s, date)


def test_technical_indicators():
    # Synthetic trending price series
    prices = np.linspace(100, 150, 100)
    df = pd.DataFrame({
        "Open": prices * 0.99,
        "High": prices * 1.02,
        "Low": prices * 0.98,
        "Close": prices,
        "Volume": [1000000] * 100
    })
    indicators = compute_technical_indicators(df)
    assert "trend_score" in indicators
    assert indicators["trend_score"] > 50.0 # Bullish trend should score above neutral
    assert indicators["price_vs_ma200_pct"] >= 0.0
    assert indicators["rsi_14d"] >= 0.0


def test_fundamental_scorer():
    strong_company = {
        "revenue_growth_yoy": 25.0,
        "operating_margin": 30.0,
        "roe": 28.0,
        "fcf_yield": 6.5,
        "debt_to_equity": 30.0,
        "pe_ratio": 22.0
    }
    score = compute_fundamental_score(strong_company)
    assert score >= 80.0, f"Expected high score for strong company, got {score}"

    weak_company = {
        "revenue_growth_yoy": -5.0,
        "operating_margin": 2.0,
        "roe": 1.0,
        "fcf_yield": -1.0,
        "debt_to_equity": 250.0,
        "pe_ratio": 95.0
    }
    weak_score = compute_fundamental_score(weak_company)
    assert weak_score < 40.0, f"Expected low score for weak company, got {weak_score}"


def test_market_plugins():
    for market_id in ["us", "cn", "mx"]:
        plugin = get_market_plugin(market_id)
        universe = plugin.get_universe()
        assert len(universe) > 0, f"Market {market_id} universe should not be empty"
        assert "ticker" in universe[0]
