"""
finops/core/models.py — Data Schemas and Typed Models
=====================================================
Strict Pydantic schemas representing factor scores, multi-agent theses,
overnight trade plans, and daily Top 20 opportunities.
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class FactorScores(BaseModel):
    # Normalized Sub-Scores (0 to 100)
    fundamental_score: float = Field(default=50.0, description="Composite fundamental score (0-100)")
    trend_score: float = Field(default=50.0, description="Composite trend and momentum score (0-100)")
    sentiment_score: float = Field(default=50.0, description="Composite sentiment score (0-100)")
    composite_score: float = Field(default=50.0, description="Overall weighted multi-factor ranking score (0-100)")

    # Raw metrics for explainability
    revenue_growth_yoy: Optional[float] = None
    operating_margin: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    fcf_yield: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None

    # Quantitative Accounting & Solvency Indicators
    piotroski_f_score: Optional[int] = Field(default=None, description="Piotroski 9-point financial health score (0-9)")
    altman_z_score: Optional[float] = Field(default=None, description="Altman Z-Score financial distress metric")
    z_zone: Optional[str] = Field(default="Safe", description="Altman Z distress classification (Safe, Grey, Distress)")

    # Technical & Institutional Flow raw metrics
    price_vs_ma200_pct: Optional[float] = None
    golden_cross: Optional[bool] = None
    ribbon_aligned: Optional[bool] = None
    rsi_14d: Optional[float] = None
    stoch_k: Optional[float] = None
    macd_histogram: Optional[float] = None
    adx_14: Optional[float] = None
    trend_strength: Optional[str] = None
    volume_surge_ratio: Optional[float] = None
    cmf_20: Optional[float] = None
    money_flow_regime: Optional[str] = None
    bollinger_pct_b: Optional[float] = None
    bollinger_bandwidth: Optional[float] = None


class OvernightTradePlan(BaseModel):
    action: Literal["BUY", "WATCH", "AVOID"] = Field(
        description="Action recommendation for next regular session"
    )
    horizon: Literal["daily", "weekly", "monthly"] = Field(
        default="daily",
        description="Investment horizon: daily (1-3 days), weekly (1-4 weeks), monthly (3-12 months)"
    )
    holding_period: str = Field(
        default="1-3 Days",
        description="Expected holding period duration"
    )
    entry_zone_low: float = Field(description="Lower limit order envelope boundary")
    entry_zone_high: float = Field(description="Upper limit order envelope boundary")
    stop_loss: float = Field(description="Strict invalidation stop price")
    target_1: float = Field(description="Primary technical profit target (Conservative)")
    target_2: float = Field(description="Extended profit target (Momentum runner)")
    risk_reward_ratio: float = Field(description="Expected R:R ratio against Target 1")
    
    suggested_shares: int = Field(description="Calculated share quantity based on portfolio risk %")
    suggested_capital: float = Field(description="Total capital allocated for the trade")
    position_risk_amount: float = Field(description="Monetary risk if stopped out (Capital risked)")
    
    window: str = Field(
        default="Pre-Market 08:30-09:30 ET / Regular Open Limit Order",
        description="Target execution order window"
    )
    gap_rule_pct: float = Field(
        default=3.5,
        description="If market gaps beyond this percentage, cancel order and re-evaluate"
    )
    event_risk_flags: List[str] = Field(
        default_factory=list,
        description="Scheduled risk catalysts (After-hours earnings, FDA, Fed, ex-dividend)"
    )
    liquidity_rating: str = Field(
        default="HIGH",
        description="ADV rating and typical bid-ask spread"
    )
    portfolio_note: Optional[str] = None


class NewsItem(BaseModel):
    title: str
    source: str
    url: Optional[str] = None
    published_at: Optional[str] = None
    sentiment: Literal["BULLISH", "NEUTRAL", "BEARISH"] = "NEUTRAL"


class StockOpportunity(BaseModel):
    rank: int = Field(description="Daily rank #1 to #20")
    ticker: str
    name: str
    market: Literal["us", "cn", "mx"]
    sector: str
    industry: str
    current_price: float
    currency: str = "USD"
    market_cap: float
    horizon: Literal["daily", "weekly", "monthly"] = Field(
        default="daily",
        description="Investment horizon profile"
    )
    scores: FactorScores

    thesis_summary: str = Field(description="Concise 2-3 sentence investment thesis")
    bull_case: str = Field(description="Primary bullish catalyst and growth driver")
    bear_case: str = Field(description="Key risks, failure modes, and headwinds")
    catalysts: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)

    trade_plan: OvernightTradePlan
    persona_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Multi-agent quantitative personas (Buffett Value, Lynch Growth, Simons Momentum, Forensic Bear)"
    )
    consensus_confidence_pct: float = Field(
        default=85.0,
        description="Multi-agent consensus confidence score (0-100%)"
    )
    sentiment_summary: Optional[str] = None
    recent_news: List[NewsItem] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScanReport(BaseModel):
    run_id: str
    scan_date: str # YYYY-MM-DD
    horizon: str = Field(default="daily", description="Timeframe horizon: daily, weekly, or monthly")
    market_close_time: datetime
    run_triggered_at: datetime
    target_trade_session: str
    top_20: List[StockOpportunity]
    shortlist_count: int
    scanned_universe_size: int
    market_breakdown: Dict[str, int]
    disclaimer: str
