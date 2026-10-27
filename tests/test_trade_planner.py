"""
tests/test_trade_planner.py — Unit Tests for Overnight Trade Plan Generator
"""

from finops.agents.trade_planner import TradePlanGenerator


def test_trade_plan_position_sizing_us():
    planner = TradePlanGenerator()
    tech_data = {
        "atr_14": 3.5,
        "support_20d": 140.0
    }
    market_meta = {
        "lot_size": 1,
        "after_hours_earnings": False
    }

    plan = planner.generate_plan(
        ticker="NVDA",
        current_price=145.0,
        composite_score=88.5,
        technical_indicators=tech_data,
        market_meta=market_meta
    )

    assert plan.action == "BUY"
    assert plan.entry_zone_low < plan.entry_zone_high
    assert plan.stop_loss < plan.entry_zone_low
    assert plan.target_1 > plan.entry_zone_high
    assert plan.suggested_shares > 0
    # Position risk amount should be approximately 1.5% of $100k = $1,500
    assert 500 <= plan.position_risk_amount <= 2000
    assert plan.risk_reward_ratio >= 2.0


def test_trade_plan_cn_board_lots():
    planner = TradePlanGenerator()
    tech_data = {
        "atr_14": 25.0,
        "support_20d": 1500.0
    }
    market_meta = {
        "lot_size": 100,
        "daily_price_limit_pct": 10.0,
        "after_hours_earnings": False
    }

    plan = planner.generate_plan(
        ticker="600519",
        current_price=1550.0,
        composite_score=90.0,
        technical_indicators=tech_data,
        market_meta=market_meta
    )

    # Must respect 100-share lot size constraint for China A-shares
    assert plan.suggested_shares % 100 == 0
    assert len(plan.event_risk_flags) > 0
