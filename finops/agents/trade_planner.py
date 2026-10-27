"""
finops/agents/trade_planner.py — Overnight Trade Plan Generator
===============================================================
Computes limit order envelopes, strict invalidation stops, profit targets,
position sizing based on portfolio risk % (e.g. 1.5%), pre-market gap rules,
and event risk detection (e.g. after-hours earnings).
"""

from typing import Dict, Any, List
from finops.core.models import OvernightTradePlan
from finops.core.config import Settings


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
    ) -> OvernightTradePlan:
        """
        Builds a deterministic, actionable overnight trade plan for next regular session.
        """
        lot_size = market_meta.get("lot_size", 1)
        after_hours_earnings = market_meta.get("after_hours_earnings", False)
        atr = technical_indicators.get("atr_14", current_price * 0.025)
        support = technical_indicators.get("support_20d", current_price * 0.96)

        # 1. Action recommendation
        if composite_score >= 70.0 and not after_hours_earnings:
            action = "BUY"
        elif composite_score >= 55.0 or after_hours_earnings:
            action = "WATCH"
        else:
            action = "AVOID"

        # 2. Limit order entry envelope (bid slightly below market towards support)
        # Avoid chasing market open; place limit order in defined band
        entry_low = round(max(current_price * 0.985, support * 1.005), 2)
        entry_high = round(current_price * 1.005, 2)
        if entry_low >= entry_high:
            entry_low = round(current_price * 0.99, 2)
            entry_high = round(current_price * 1.005, 2)

        entry_mid = (entry_low + entry_high) / 2.0

        # 3. Stop loss (invalidation price)
        # Sited below technical support with 1.5x ATR buffer
        raw_stop = min(support - (0.5 * atr), entry_mid - (1.5 * atr))
        stop_loss = round(max(raw_stop, entry_mid * 0.92), 2) # max 8% stop
        
        # Ensure minimum stop gap
        if (entry_mid - stop_loss) < (entry_mid * 0.015):
            stop_loss = round(entry_mid * 0.97, 2)

        risk_per_share = entry_mid - stop_loss

        # 4. Profit targets (Target 1 at 2.5 R:R, Target 2 at 4.0 R:R runner)
        target_1 = round(entry_high + (risk_per_share * self.rr_ratio), 2)
        target_2 = round(entry_high + (risk_per_share * 4.0), 2)
        actual_rr = round((target_1 - entry_high) / (entry_high - stop_loss), 2) if (entry_high - stop_loss) > 0 else self.rr_ratio

        # 5. Position sizing from portfolio risk (e.g. 1.5% of $100k = $1,500 max risk)
        max_dollar_risk = self.portfolio_equity * (self.risk_pct / 100.0)
        raw_shares = int(max_dollar_risk / max(risk_per_share, 0.01))

        # Adjust for board lot constraints (e.g. 100 shares for China A-shares)
        if lot_size > 1:
            shares = max(int(raw_shares // lot_size) * lot_size, lot_size)
        else:
            shares = max(raw_shares, 1)

        # Cap single position capital at 20% of portfolio to avoid excessive concentration
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

        return OvernightTradePlan(
            action=action,
            entry_zone_low=entry_low,
            entry_zone_high=entry_high,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            risk_reward_ratio=actual_rr,
            suggested_shares=shares,
            suggested_capital=suggested_capital,
            position_risk_amount=position_risk_amount,
            window="Pre-Market 08:30-09:30 ET / Regular Open Limit Order",
            gap_rule_pct=self.gap_rule_pct,
            event_risk_flags=event_flags,
            liquidity_rating="HIGH (Tier 1 Volume)",
            portfolio_note=f"Allocates {round(suggested_capital/self.portfolio_equity*100, 1)}% of total equity risking {self.risk_pct}% on stop."
        )
