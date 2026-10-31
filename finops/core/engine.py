"""
finops/core/engine.py — Complete Daily Scan Pipeline Orchestrator
=================================================================
Orchestrates Market Scanning -> Factor Scoring -> LLM Deep Dive -> Trade Planning -> Delivery.
"""

import logging
import math
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from finops.core.config import Settings
from finops.core.calendar import MarketCalendarService
from finops.core.models import ScanReport, StockOpportunity
from finops.markets.factory import get_market_plugin
from finops.screener.scorer import ScreenerEngine
from finops.sentiment.news_fetcher import NewsSentimentAggregator
from finops.agents.trade_planner import TradePlanGenerator
from finops.agents.deep_dive import DeepDiveAgent
from finops.delivery.storage import ReportStorage
from finops.delivery.markdown_report import generate_markdown_report

logger = logging.getLogger("finops.core.engine")


class ScanPipeline:
    def __init__(self):
        self.settings = Settings.get()
        self.calendar_service = MarketCalendarService()
        self.screener = ScreenerEngine()
        self.sentiment_aggregator = NewsSentimentAggregator()
        self.trade_planner = TradePlanGenerator()
        self.deep_dive_agent = DeepDiveAgent()
        self.storage = ReportStorage()

    def run_daily_scan(
        self,
        target_markets: Optional[List[str]] = None,
        candidate_limit_per_market: Optional[int] = None,
        force_run: bool = False,
        horizon: str = "daily"
    ) -> ScanReport:
        """
        Executes the end-to-end scanning and analysis pipeline for a specific
        investment horizon ('daily', 'weekly', 'monthly').
        """
        now = datetime.utcnow()
        scan_date_str = now.strftime("%Y-%m-%d")

        if target_markets is None:
            target_markets = self.settings.settings_dict.get("markets", {}).get("enabled", ["us", "cn", "mx"])

        logger.info(f"Starting [{horizon.upper()}] scan for markets: {target_markets} (Force: {force_run})")

        # Determine target trading session from exchange calendar
        try:
            next_session = self.calendar_service.get_next_trading_session()
            target_trade_session = next_session.strftime("%Y-%m-%d (Next Regular Session)")
        except Exception:
            target_trade_session = f"Next Regular Session ({scan_date_str})"

        evaluated_pool: List[Dict[str, Any]] = []
        market_counts: Dict[str, int] = {}
        total_universe_scanned = 0

        # Step 1: Ingest and screen universe across all plug-in markets
        for market_id in target_markets:
            try:
                plugin = get_market_plugin(market_id)
                universe = plugin.get_universe(limit=candidate_limit_per_market)
                total_universe_scanned += len(universe)
                logger.info(f"Scanning market '{market_id}' ({plugin.name}) with {len(universe)} candidate tickers...")

                for item in universe:
                    ticker = item["ticker"]
                    try:
                        mkt_data = plugin.fetch_market_data(ticker)
                        if not mkt_data:
                            continue

                        # Calculate and enforce Alta Bursatilidad / High Liquidity metrics
                        prices_df = mkt_data.get("prices")
                        if prices_df is not None and not prices_df.empty and "Volume" in prices_df.columns:
                            adv_val = prices_df["Volume"].tail(20).mean()
                            adv_20 = float(adv_val) if pd.notna(adv_val) and adv_val > 0 else 250000.0
                            raw_price = mkt_data.get("current_price") or prices_df["Close"].iloc[-1]
                            curr_price = float(raw_price) if pd.notna(raw_price) and raw_price > 0 else 10.0
                            addv = adv_20 * curr_price
                            mkt_data["avg_daily_volume"] = adv_20
                            mkt_data["avg_daily_dollar_volume"] = addv

                            # Enforce liquidity filter if enabled
                            liq_cfg = self.settings.liquidity_filters
                            if liq_cfg.get("enforce_high_liquidity", True):
                                min_vol = liq_cfg.get("min_avg_daily_volume", 200000)
                                min_price = liq_cfg.get("min_share_price", 2.0)
                                max_price = liq_cfg.get("max_share_price", 3500.0)
                                min_dollar_usd = liq_cfg.get("min_avg_dollar_volume_usd", 10000000.0)

                                # Currency-adjusted turnover threshold
                                currency = mkt_data.get("currency", "USD")
                                if currency == "MXN":
                                    min_turnover = min_dollar_usd * 18.0
                                elif currency == "CNY":
                                    min_turnover = min_dollar_usd * 7.2
                                elif currency == "HKD":
                                    min_turnover = min_dollar_usd * 7.8
                                else:
                                    min_turnover = min_dollar_usd

                                if adv_20 < min_vol or addv < min_turnover or curr_price < min_price or curr_price > max_price:
                                    logger.debug(
                                        f"Skipping {ticker} ({market_id}): Below liquidity criteria (ADV: {adv_20:,.0f}, Turnover: {addv:,.0f} {currency})"
                                    )
                                    continue

                        # Fetch news and assess sentiment
                        raw_news = plugin.fetch_recent_news(ticker, limit=4)
                        sent_score, news_items = self.sentiment_aggregator.evaluate_sentiment(raw_news)
                        mkt_data["news_items"] = news_items

                        # Quantitative multi-factor evaluation tailored to horizon
                        evaluated = self.screener.evaluate_candidate(
                            mkt_data,
                            sentiment_score=sent_score,
                            horizon=horizon
                        )
                        evaluated["market_id"] = market_id
                        evaluated_pool.append(evaluated)
                        market_counts[market_id] = market_counts.get(market_id, 0) + 1

                    except Exception as e:
                        logger.warning(f"Failed processing {ticker} in market {market_id}: {e}")
            except Exception as e:
                logger.error(f"Failed running market plugin {market_id}: {e}")

        logger.info(f"Successfully evaluated {len(evaluated_pool)} candidates across {len(market_counts)} markets.")

        # Step 2: Rank candidates and extract Top 20 for this horizon
        top_candidates = self.screener.rank_candidates(evaluated_pool, top_count=20)
        logger.info(f"Identified Top {len(top_candidates)} [{horizon.upper()}] opportunities. Synthesizing deep-dive theses and trade plans...")

        # Step 3: Deep dive and trade plan generation
        top_20_opportunities: List[StockOpportunity] = []

        for rank_idx, item in enumerate(top_candidates, 1):
            mkt = item["market_data"]
            scores = item["scores"]
            tech_indicators = item["technical_indicators"]
            ticker = mkt["ticker"]
            name = mkt["name"]
            sector = mkt.get("sector", "General")
            industry = mkt.get("industry", sector)
            currency = mkt.get("currency", "USD")
            raw_price = mkt.get("current_price")
            if raw_price is None or (isinstance(raw_price, float) and (math.isnan(raw_price) or math.isinf(raw_price) or raw_price <= 0)):
                df_p = item.get("market_data", {}).get("prices")
                if df_p is not None and not df_p.empty and "close" in df_p.columns and not math.isnan(df_p["close"].iloc[-1]):
                    current_price = round(float(df_p["close"].iloc[-1]), 2)
                else:
                    current_price = 100.0
            else:
                current_price = round(float(raw_price), 2)
            market_id = item["market_id"]

            # Compute Trade Plan tailored to horizon
            trade_plan = self.trade_planner.generate_plan(
                ticker=ticker,
                current_price=current_price,
                composite_score=scores.composite_score,
                technical_indicators=tech_indicators,
                market_meta=mkt,
                horizon=horizon
            )

            # Synthesize Deep Dive (Thesis + Bull vs Bear Debate)
            research = self.deep_dive_agent.analyze_stock(
                ticker=ticker,
                name=name,
                sector=sector,
                industry=industry,
                current_price=current_price,
                currency=currency,
                scores=scores,
                news_items=[n.model_dump() for n in mkt.get("news_items", [])],
                technical_data=tech_indicators,
                horizon=horizon
            )

            opp = StockOpportunity(
                rank=rank_idx,
                ticker=ticker,
                name=name,
                market=market_id,
                sector=sector,
                industry=industry,
                current_price=current_price,
                currency=currency,
                market_cap=mkt.get("market_cap", 1e9),
                horizon=horizon,
                scores=scores,
                thesis_summary=research["thesis_summary"],
                bull_case=research["bull_case"],
                bear_case=research["bear_case"],
                catalysts=research["catalysts"],
                key_risks=research["key_risks"],
                trade_plan=trade_plan,
                persona_analysis=research.get("persona_analysis"),
                consensus_confidence_pct=research.get("consensus_confidence_pct", 85.0),
                recent_news=mkt.get("news_items", [])
            )
            top_20_opportunities.append(opp)

        # Step 4: Assemble ScanReport with horizon metadata
        report = ScanReport(
            run_id=f"run_{scan_date_str}_{horizon}_{uuid.uuid4().hex[:8]}",
            scan_date=scan_date_str,
            horizon=horizon,
            market_close_time=now,
            run_triggered_at=now,
            target_trade_session=target_trade_session,
            top_20=top_20_opportunities,
            shortlist_count=len(evaluated_pool),
            scanned_universe_size=total_universe_scanned,
            market_breakdown=market_counts,
            disclaimer=self.settings.compliance.get(
                "disclaimer",
                "Research tool for quantitative modeling only. Not investment advice."
            )
        )

        # Step 5: Generate Markdown and persist artifacts
        md_content = generate_markdown_report(report)
        self.storage.save_scan_report(report, md_content)

        return report
