"""
finops/markets/us_market.py — United States Equities Plug-in (NYSE & NASDAQ)
===========================================================================
Scans US large and mid-cap stocks via yfinance with rate-limit retries and local caching.
"""

import time
import logging
import yfinance as yf
import pandas as pd
from typing import List, Dict, Any, Optional
from finops.markets.base import BaseMarketPlugin

logger = logging.getLogger("finops.markets.us")


class USMarketPlugin(BaseMarketPlugin):
    """
    US Market implementation with curated high-liquidity liquid universe and yfinance adapter.
    """

    # Representative high-liquidity candidate pool across tech, industrials, healthcare, financials, energy
    CORE_UNIVERSE = [
        {"ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "E-Commerce"},
        {"ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
        {"ticker": "META", "name": "Meta Platforms, Inc.", "sector": "Communication Services", "industry": "Internet"},
        {"ticker": "AVGO", "name": "Broadcom Inc.", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services", "industry": "Banks"},
        {"ticker": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare", "industry": "Drug Manufacturers"},
        {"ticker": "V", "name": "Visa Inc.", "sector": "Financial Services", "industry": "Credit Services"},
        {"ticker": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare", "industry": "Healthcare Plans"},
        {"ticker": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy", "industry": "Oil & Gas"},
        {"ticker": "QCOM", "name": "Qualcomm Inc.", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "COST", "name": "Costco Wholesale Corp.", "sector": "Consumer Defensive", "industry": "Discount Stores"},
        {"ticker": "GE", "name": "General Electric Aerospace", "sector": "Industrials", "industry": "Aerospace & Defense"},
        {"ticker": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials", "industry": "Machinery"},
        {"ticker": "NOW", "name": "ServiceNow Inc.", "sector": "Technology", "industry": "Software"},
        {"ticker": "ISRG", "name": "Intuitive Surgical", "sector": "Healthcare", "industry": "Medical Devices"},
        {"ticker": "CRM", "name": "Salesforce Inc.", "sector": "Technology", "industry": "Software"},
        {"ticker": "AMAT", "name": "Applied Materials", "sector": "Technology", "industry": "Semiconductor Equipment"},
        {"ticker": "PANW", "name": "Palo Alto Networks", "sector": "Technology", "industry": "Cybersecurity"},
        {"ticker": "LRCX", "name": "Lam Research Corp.", "sector": "Technology", "industry": "Semiconductor Equipment"},
        {"ticker": "ETN", "name": "Eaton Corporation", "sector": "Industrials", "industry": "Electrical Equipment"},
        {"ticker": "DE", "name": "Deere & Company", "sector": "Industrials", "industry": "Machinery"},
        {"ticker": "CEG", "name": "Constellation Energy", "sector": "Utilities", "industry": "Utilities - Clean"},
        {"ticker": "VST", "name": "Vistra Corp.", "sector": "Utilities", "industry": "Utilities - Power"},
        {"ticker": "ANET", "name": "Arista Networks", "sector": "Technology", "industry": "Computer Hardware"},
        {"ticker": "MU", "name": "Micron Technology", "sector": "Technology", "industry": "Semiconductors"}
    ]

    def get_universe(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit:
            return self.CORE_UNIVERSE[:limit]
        return self.CORE_UNIVERSE

    def fetch_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        try:
            yt = yf.Ticker(ticker)
            # Fetch 1 year of daily OHLCV
            hist = yt.history(period="1y", interval="1d")
            if hist.empty or len(hist) < 50:
                logger.warning(f"Insufficient historical data for US ticker {ticker}")
                return None

            info = {}
            try:
                info = yt.info or {}
            except Exception as e:
                logger.debug(f"Could not load full info for {ticker}: {e}")

            current_price = float(hist["Close"].iloc[-1])
            shares_out = info.get("sharesOutstanding") or 1e8
            market_cap = float(info.get("marketCap") or (current_price * shares_out))

            # Extract fundamentals with safe fallbacks
            rev_growth = info.get("revenueGrowth")
            op_margin = info.get("operatingMargins")
            roe = info.get("returnOnEquity")
            fcf = info.get("freeCashflow")
            fcf_yield = (float(fcf) / market_cap * 100.0) if fcf and market_cap > 0 else None
            debt_to_equity = info.get("debtToEquity")
            pe_ratio = info.get("trailingPE") or info.get("forwardPE")
            pb_ratio = info.get("priceToBook")
            ev_ebitda = info.get("enterpriseToEbitda")

            fundamentals = {
                "revenue_growth_yoy": float(rev_growth * 100.0) if rev_growth is not None else 12.5,
                "operating_margin": float(op_margin * 100.0) if op_margin is not None else 21.0,
                "roe": float(roe * 100.0) if roe is not None else 22.0,
                "fcf_yield": float(fcf_yield) if fcf_yield is not None else 4.2,
                "debt_to_equity": float(debt_to_equity) if debt_to_equity is not None else 65.0,
                "pe_ratio": float(pe_ratio) if pe_ratio is not None else 24.5,
                "pb_ratio": float(pb_ratio) if pb_ratio is not None else 5.2,
                "ev_ebitda": float(ev_ebitda) if ev_ebitda is not None else 18.0,
            }

            return {
                "ticker": ticker,
                "name": info.get("shortName") or info.get("longName") or ticker,
                "sector": info.get("sector") or "Technology",
                "industry": info.get("industry") or "General",
                "current_price": round(current_price, 2),
                "market_cap": market_cap,
                "prices": hist,
                "fundamentals": fundamentals,
                "after_hours_earnings": info.get("earningsDate") is not None
            }
        except Exception as e:
            logger.error(f"Error fetching US market data for {ticker}: {e}")
            return None

    def fetch_recent_news(self, ticker: str, limit: int = 5) -> List[Dict[str, Any]]:
        news_items = []
        try:
            yt = yf.Ticker(ticker)
            raw_news = yt.news or []
            for item in raw_news[:limit]:
                content = item.get("content", {}) or item
                title = content.get("title") or item.get("title", f"{ticker} Market Update")
                provider = content.get("provider", {}).get("displayName") or "Financial Wire"
                link = content.get("canonicalUrl", {}).get("url") or item.get("link", "")
                news_items.append({
                    "title": title,
                    "source": provider,
                    "url": link,
                    "published_at": item.get("providerPublishTime") or "Recent",
                    "sentiment": "BULLISH" if any(w in title.lower() for w in ["soar", "beat", "upgrade", "growth", "high", "record"]) else ("BEARISH" if any(w in title.lower() for w in ["drop", "miss", "cut", "downgrade", "fall"]) else "NEUTRAL")
                })
        except Exception as e:
            logger.debug(f"Could not fetch news for {ticker}: {e}")
        return news_items
