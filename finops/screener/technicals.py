"""
finops/screener/technicals.py — Quantitative Technical Analysis & Trend Scorer
==============================================================================
Calculates moving averages, RSI, MACD, volume surges, ATR, and technical scores.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates 14-period Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculates MACD line, Signal line, and MACD Histogram."""
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR) for volatility and stop-loss envelope."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def compute_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes all trend, momentum, volatility and support/resistance metrics.
    Requires DataFrame with Open, High, Low, Close, Volume.
    """
    if df.empty or len(df) < 30:
        return {
            "trend_score": 50.0,
            "ma50": 0.0,
            "ma200": 0.0,
            "price_vs_ma200_pct": 0.0,
            "golden_cross": False,
            "rsi_14d": 50.0,
            "macd_histogram": 0.0,
            "volume_surge_ratio": 1.0,
            "atr_14": 1.0,
            "support_20d": float(df["Close"].iloc[-1]) * 0.95 if not df.empty else 100.0,
            "resistance_20d": float(df["Close"].iloc[-1]) * 1.05 if not df.empty else 100.0,
        }

    close = df["Close"]
    volume = df["Volume"]

    # Moving averages
    ma50 = close.rolling(window=min(50, len(close))).mean()
    ma200 = close.rolling(window=min(200, len(close))).mean()

    curr_close = float(close.iloc[-1])
    curr_ma50 = float(ma50.iloc[-1])
    curr_ma200 = float(ma200.iloc[-1])

    price_vs_ma200_pct = ((curr_close - curr_ma200) / curr_ma200) * 100.0 if curr_ma200 > 0 else 0.0
    golden_cross = curr_ma50 > curr_ma200

    # RSI
    rsi_series = calculate_rsi(close, period=14)
    curr_rsi = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0

    # MACD
    _, _, hist_series = calculate_macd(close)
    curr_macd_hist = float(hist_series.iloc[-1]) if not np.isnan(hist_series.iloc[-1]) else 0.0

    # Volume surge
    vol_20d = volume.rolling(window=min(20, len(volume))).mean()
    curr_vol = float(volume.iloc[-1])
    curr_vol_avg = float(vol_20d.iloc[-1]) if float(vol_20d.iloc[-1]) > 0 else 1.0
    volume_surge_ratio = curr_vol / curr_vol_avg if curr_vol_avg > 0 else 1.0

    # ATR
    atr_series = calculate_atr(df, period=14)
    curr_atr = float(atr_series.iloc[-1]) if not np.isnan(atr_series.iloc[-1]) else curr_close * 0.02

    # Support / Resistance (20-day swing low and high)
    support_20d = float(df["Low"].tail(20).min())
    resistance_20d = float(df["High"].tail(20).max())

    # Calculate trend score (0 to 100)
    # 1. Price above MA200: up to 30 pts
    ma200_pts = min(max((price_vs_ma200_pct + 10) * 1.5, 0), 30)

    # 2. Golden Cross: 20 pts if True, 5 pts if False
    golden_pts = 20.0 if golden_cross else 5.0

    # 3. RSI sweet spot (ideal accumulation between 45 and 65): up to 25 pts
    if 45 <= curr_rsi <= 65:
        rsi_pts = 25.0
    elif 35 <= curr_rsi < 45 or 65 < curr_rsi <= 75:
        rsi_pts = 18.0
    elif curr_rsi > 75: # Overbought
        rsi_pts = 8.0
    else: # Severely oversold
        rsi_pts = 10.0

    # 4. MACD Histogram momentum: up to 15 pts
    macd_pts = 15.0 if curr_macd_hist > 0 else 5.0

    # 5. Volume surge footprint: up to 10 pts
    vol_pts = min(volume_surge_ratio * 7.5, 10.0)

    trend_score = min(max(ma200_pts + golden_pts + rsi_pts + macd_pts + vol_pts, 0.0), 100.0)

    return {
        "trend_score": round(trend_score, 1),
        "ma50": round(curr_ma50, 2),
        "ma200": round(curr_ma200, 2),
        "price_vs_ma200_pct": round(price_vs_ma200_pct, 2),
        "golden_cross": golden_cross,
        "rsi_14d": round(curr_rsi, 1),
        "macd_histogram": round(curr_macd_hist, 3),
        "volume_surge_ratio": round(volume_surge_ratio, 2),
        "atr_14": round(curr_atr, 2),
        "support_20d": round(support_20d, 2),
        "resistance_20d": round(resistance_20d, 2),
    }
