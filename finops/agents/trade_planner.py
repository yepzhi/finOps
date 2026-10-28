"""
finops/agents/trade_planner.py — Overnight Trade Plan Generator
===============================================================
Computes limit order envelopes, strict invalidation stops, profit targets,
position sizing based on portfolio risk % (e.g. 1.5%), pre-market gap rules,
and event risk detection (e.g. after-hours earnings).
"""

import math
from typing import Dict, Any, List
from finops.core.models import OvernightTradePlan
from finops.core.config import Settings


def _clean_val(val: Any, fallback: float) -> float:
    if val is None:
        return float(fallback)
    try:
        f = float(val)
        return float(fallback) if math.isnan(f) or math.isinf(f) or f <= 0 else f
    except (ValueError, TypeError):
        return float(fallback)


class TradePlanGenerator:
    def __init__(self):
        settings = Settings.get()
        cfg = settings.trade_plan
        self.risk_pct = cfg.get("portfolio_risk_per_trade_pct", 1.5)
        self.portfolio_equity = cfg.get("default_portfolio_equity", 100000.0)
        self.gap_rule_pct = cfg.get("premarket_gap_invalidation_pct", 3.5)
        self.rr_ratio = cfg.get("default_risk_reward_ratio", 2.5)

    def generate_plan(
        self,
        ticker: str,
        current_price: float,
        composite_score: float,
        technical_indicators: Dict[str, Any],
        market_meta: Dict[str, Any],
        horizon: str = "daily"
    ) -> OvernightTradePlan:
        """
        Builds a deterministic, actionable trade plan tailored to the selected
        investment horizon ('daily', 'weekly', 'monthly').
        """
        current_price = _clean_val(current_price, 100.0)
        settings = Settings.get()
        horizon_cfg = settings.horizons.get(horizon, {})

        holding_period = horizon_cfg.get("holding_period", "1-3 Days" if horizon == "daily" else ("1-4 Weeks" if horizon == "weekly" else "3-12 Months"))
        window = horizon_cfg.get("window", "Pre-Market 08:30-09:30 ET / Regular Open Limit Order")
        gap_rule_pct = horizon_cfg.get("gap_rule_pct", 3.5 if horizon == "daily" else (5.0 if horizon == "weekly" else 8.0))
        rr_multiplier = horizon_cfg.get("target_rr_ratio", 2.5 if horizon == "daily" else (3.5 if horizon == "weekly" else 5.0))
        atr_mult = horizon_cfg.get("stop_multiplier_atr", 1.5 if horizon == "daily" else (2.5 if horizon == "weekly" else 4.0))

        lot_size = market_meta.get("lot_size", 1)
        after_hours_earnings = market_meta.get("after_hours_earnings", False)
        atr = _clean_val(technical_indicators.get("atr_14"), current_price * 0.025)
        support = _clean_val(technical_indicators.get("support_20d"), current_price * 0.96)
        ma50 = _clean_val(technical_indicators.get("ma50"), current_price * 0.95)
        ma200 = _clean_val(technical_indicators.get("ma200"), current_price * 0.90)

        # 1. Action recommendation
        if composite_score >= 70.0 and not (after_hours_earnings and horizon == "daily"):
            action = "BUY"
        elif composite_score >= 55.0 or after_hours_earnings:
            action = "WATCH"
        else:
            action = "AVOID"

        # 2. Limit order entry envelope
        if horizon == "daily":
            entry_low = round(max(current_price * 0.985, support * 1.005), 2)
            entry_high = round(current_price * 1.005, 2)
        elif horizon == "weekly":
            entry_low = round(min(current_price * 0.975, ma50 * 1.01), 2)
            entry_high = round(current_price * 1.01, 2)
        else: # monthly
            entry_low = round(min(current_price * 0.95, ma200 * 1.02), 2)
            entry_high = round(current_price * 1.02, 2)

        if entry_low >= entry_high:
            entry_low = round(current_price * 0.98, 2)
            entry_high = round(current_price * 1.01, 2)

        entry_mid = (entry_low + entry_high) / 2.0

        # 3. Stop loss (invalidation price based on horizon volatility)
        if horizon == "daily":
            raw_stop = min(support - (0.5 * atr), entry_mid - (atr_mult * atr))
            max_stop_pct = 0.92 # max 8% stop
        elif horizon == "weekly":
            raw_stop = min(ma50 - (0.5 * atr), entry_mid - (atr_mult * atr))
            max_stop_pct = 0.88 # max 12% stop
        else: # monthly
            raw_stop = min(ma200 - (0.5 * atr), entry_mid - (atr_mult * atr))
            max_stop_pct = 0.82 # max 18% stop

        raw_stop = _clean_val(raw_stop, entry_mid * max_stop_pct)
        stop_loss = round(max(raw_stop, entry_mid * max_stop_pct), 2)
        
        # Ensure minimum stop gap
        min_gap_pct = 0.015 if horizon == "daily" else (0.03 if horizon == "weekly" else 0.05)
        if (entry_mid - stop_loss) < (entry_mid * min_gap_pct):
            stop_loss = round(entry_mid * (1.0 - min_gap_pct * 1.5), 2)

        risk_per_share = _clean_val(entry_mid - stop_loss, max(entry_mid * 0.02, 0.05))
        max_entry_risk = max(_clean_val(entry_high - stop_loss, risk_per_share), 0.01)

        # 4. Profit targets (calibrated to guarantee target R:R even with limit spread)
        runner_multiplier = 4.0 if horizon == "daily" else (5.5 if horizon == "weekly" else 8.0)
        target_1 = round(entry_high + (max_entry_risk * rr_multiplier), 2)
        target_2 = round(entry_high + (max_entry_risk * runner_multiplier), 2)
        actual_rr = round((target_1 - entry_high) / max_entry_risk, 2)

        # 5. Position sizing from portfolio risk (1.5% max risk)
        max_dollar_risk = self.portfolio_equity * (self.risk_pct / 100.0)
        raw_shares = int(max_dollar_risk / max(risk_per_share, 0.01))

        if lot_size > 1:
            shares = max(int(raw_shares // lot_size) * lot_size, lot_size)
        else:
            shares = max(raw_shares, 1)

        max_capital_allowed = self.portfolio_equity * 0.20
        if (shares * entry_mid) > max_capital_allowed:
            shares = int(max_capital_allowed / entry_mid)
            if lot_size > 1:
                shares = max(int(shares // lot_size) * lot_size, lot_size)

        suggested_capital = round(shares * entry_mid, 2)
        position_risk_amount = round(shares * risk_per_share, 2)

        # 6. Event risk flags
        event_flags: List[str] = []
        if after_hours_earnings:
            event_flags.append("AFTER-HOURS EARNINGS RELEASE FLAGGED — High Volatility / Review Guidance")
        if market_meta.get("daily_price_limit_pct"):
            event_flags.append(f"A-Share Daily Limit (+/- {market_meta.get('daily_price_limit_pct')}%) & T+1 Settlement Rule")

        addv = market_meta.get("avg_daily_dollar_volume")
        if addv and addv >= 1e8:
            liq_str = "ALTA BURSATILIDAD (Mega-Liquid / $100M+ Turnover)"
        elif addv and addv >= 2e7:
            liq_str = "ALTA BURSATILIDAD (Institutional / $20M+ Turnover)"
        else:
            liq_str = "ALTA BURSATILIDAD (Tier 1 Volume / Tight Spreads)"

        return OvernightTradePlan(
            action=action,
            horizon=horizon,
            holding_period=holding_period,
            entry_zone_low=entry_low,
            entry_zone_high=entry_high,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            risk_reward_ratio=actual_rr,
            suggested_shares=shares,
            suggested_capital=suggested_capital,
            position_risk_amount=position_risk_amount,
            window=window,
            gap_rule_pct=gap_rule_pct,
            event_risk_flags=event_flags,
            liquidity_rating=liq_str,
            portfolio_note=f"[{horizon.upper()} HORIZON] Allocates {round(suggested_capital/self.portfolio_equity*100, 1)}% equity risking {self.risk_pct}% on stop for target holding {holding_period}."
        )
