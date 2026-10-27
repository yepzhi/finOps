"""
finops/screener/scorer.py — Multi-Factor Screener & Ranking Engine
==================================================================
Combines fundamental, technical trend, and sentiment factors with configurable weights.
Deterministic scoring first, producing an explainable Top 20 ranking.
"""

import logging
from typing import List, Dict, Any
from finops.screener.technicals import compute_technical_indicators
from finops.screener.fundamentals import evaluate_all_fundamentals
from finops.core.models import FactorScores
from finops.core.config import Settings

logger = logging.getLogger("finops.screener.scorer")


class ScreenerEngine:
    def __init__(self):
        self.settings = Settings.get()
        weights = self.settings.scoring.get("weights", {})
        self.default_w_fund = weights.get("fundamental", 0.50)
        self.default_w_trend = weights.get("trend", 0.35)
        self.default_w_sent = weights.get("sentiment", 0.15)

    def evaluate_candidate(
        self,
        market_data: Dict[str, Any],
        sentiment_score: float = 65.0,
        horizon: str = "daily"
    ) -> Dict[str, Any]:
        """
        Calculates all sub-scores and composite multi-factor score for a single stock candidate
        tailored to the chosen investment horizon ('daily', 'weekly', 'monthly').
        """
        prices = market_data.get("prices")
        tech_indicators = compute_technical_indicators(prices)
        
        raw_fund = market_data.get("fundamentals", {})
        fund_eval = evaluate_all_fundamentals(raw_fund)
        fund_score = fund_eval["fundamental_score"]
        trend_score = tech_indicators["trend_score"]

        # Retrieve horizon-specific factor weights
        horizon_cfg = self.settings.horizons.get(horizon, {})
        weights = horizon_cfg.get("weights", {})
        w_fund = weights.get("fundamental", self.default_w_fund)
        w_trend = weights.get("trend", self.default_w_trend)
        w_sent = weights.get("sentiment", self.default_w_sent)

        # Composite weighted score for this horizon
        composite = (fund_score * w_fund) + (trend_score * w_trend) + (sentiment_score * w_sent)
        composite = round(min(max(composite, 0.0), 100.0), 1)

        scores = FactorScores(
            fundamental_score=fund_score,
            trend_score=trend_score,
            sentiment_score=sentiment_score,
            composite_score=composite,
            revenue_growth_yoy=raw_fund.get("revenue_growth_yoy"),
            operating_margin=raw_fund.get("operating_margin"),
            roe=raw_fund.get("roe"),
            roic=fund_eval.get("roic"),
            fcf_yield=raw_fund.get("fcf_yield"),
            debt_to_equity=raw_fund.get("debt_to_equity"),
            current_ratio=raw_fund.get("current_ratio"),
            pe_ratio=raw_fund.get("pe_ratio"),
            pb_ratio=raw_fund.get("pb_ratio"),
            ev_ebitda=raw_fund.get("ev_ebitda"),
            piotroski_f_score=fund_eval.get("piotroski_f_score"),
            altman_z_score=fund_eval.get("altman_z_score"),
            z_zone=fund_eval.get("z_zone"),
            price_vs_ma200_pct=tech_indicators.get("price_vs_ma200_pct"),
            golden_cross=tech_indicators.get("golden_cross"),
            ribbon_aligned=tech_indicators.get("ribbon_aligned"),
            rsi_14d=tech_indicators.get("rsi_14d"),
            stoch_k=tech_indicators.get("stoch_k"),
            macd_histogram=tech_indicators.get("macd_histogram"),
            adx_14=tech_indicators.get("adx_14"),
            trend_strength=tech_indicators.get("trend_strength"),
            volume_surge_ratio=tech_indicators.get("volume_surge_ratio"),
            cmf_20=tech_indicators.get("cmf_20"),
            money_flow_regime=tech_indicators.get("money_flow_regime"),
            bollinger_pct_b=tech_indicators.get("bb_pct_b"),
            bollinger_bandwidth=tech_indicators.get("bb_bandwidth")
        )

        return {
            "market_data": market_data,
            "scores": scores,
            "technical_indicators": tech_indicators,
            "composite_score": composite
        }

    def rank_candidates(self, evaluated_candidates: List[Dict[str, Any]], top_count: int = 20) -> List[Dict[str, Any]]:
        """
        Ranks candidates by composite score descending and returns Top N.
        """
        sorted_candidates = sorted(
            evaluated_candidates,
            key=lambda x: x["composite_score"],
            reverse=True
        )
        return sorted_candidates[:top_count]
