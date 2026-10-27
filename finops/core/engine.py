"""
finops/core/engine.py — Complete Daily Scan Pipeline Orchestrator
=================================================================
Orchestrates Market Scanning -> Factor Scoring -> LLM Deep Dive -> Trade Planning -> Delivery.
"""

import logging
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
        force_run: bool = False
    ) -> ScanReport:
        """
        Executes the end-to-end scanning and analysis pipeline.
        """
        now = datetime.utcnow()
        scan_date_str = now.strftime("%Y-%m-%d")

        if target_markets is None:
            target_markets = self.settings.settings_dict.get("markets", {}).get("enabled", ["us", "cn", "mx"])

        logger.info(f"Starting daily scan for markets: {target_markets} (Force: {force_run})")

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

                        # Fetch news and assess sentiment
                        raw_news = plugin.fetch_recent_news(ticker, limit=4)
                        sent_score, news_items = self.sentiment_aggregator.evaluate_sentiment(raw_news)
                        mkt_data["news_items"] = news_items

                        # Quantitative multi-factor evaluation
                        evaluated = self.screener.evaluate_candidate(mkt_data, sentiment_score=sent_score)
                        evaluated["market_id"] = market_id
                        evaluated_pool.append(evaluated)
                        market_counts[market_id] = market_counts.get(market_id, 0) + 1

                    except Exception as e:
                        logger.warning(f"Failed processing {ticker} in market {market_id}: {e}")
            except Exception as e:
                logger.error(f"Failed running market plugin {market_id}: {e}")

        logger.info(f"Successfully evaluated {len(evaluated_pool)} candidates across {len(market_counts)} markets.")

        # Step 2: Rank candidates and extract Top 20
        top_candidates = self.screener.rank_candidates(evaluated_pool, top_count=20)
        logger.info(f"Identified Top {len(top_candidates)} opportunities. Synthesizing deep-dive theses and trade plans...")

        # Step 3: Deep dive and overnight trade plan generation
        top_20_opportunities: List[StockOpportunity] = []

        for rank_idx, item in enumerate(top_candidates, 1):
            mkt = item["market_data"]
            scores = item["scores"]
            tech_indicators = item["technical_indicators"]
            ticker = mkt["ticker"]
            name = mkt["name"]
            sector = mkt["sector"]
            industry = mkt["industry"]
            current_price = mkt["current_price"]
            currency = mkt.get("currency", "USD")
            market_id = item["market_id"]

            # Compute Overnight Trade Plan
            trade_plan = self.trade_planner.generate_plan(
                ticker=ticker,
                current_price=current_price,
                composite_score=scores.composite_score,
                technical_indicators=tech_indicators,
                market_meta=mkt
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
                technical_data=tech_indicators
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
                scores=scores,
                thesis_summary=research["thesis_summary"],
                bull_case=research["bull_case"],
                bear_case=research["bear_case"],
                catalysts=research["catalysts"],
                key_risks=research["key_risks"],
                trade_plan=trade_plan,
                recent_news=mkt.get("news_items", [])
            )
            top_20_opportunities.append(opp)

        # Step 4: Assemble ScanReport
        report = ScanReport(
            run_id=f"run_{scan_date_str}_{uuid.uuid4().hex[:8]}",
            scan_date=scan_date_str,
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
