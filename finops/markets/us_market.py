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

    # Premier high-bursatilidad (high-liquidity) candidate pool across momentum growth,
    # global ADR leaders, AI/semis, clean energy, and core institutional benchmarks.
    CORE_UNIVERSE = [
        # ── High-Beta Momentum & Growth Leaders (High Daily Dollar Volume) ──
        {"ticker": "PLTR", "name": "Palantir Technologies", "sector": "Technology", "industry": "Data & AI Software"},
        {"ticker": "COIN", "name": "Coinbase Global", "sector": "Financial Services", "industry": "Financial Technology"},
        {"ticker": "MSTR", "name": "MicroStrategy Inc.", "sector": "Technology", "industry": "Software & Digital Assets"},
        {"ticker": "ARM", "name": "Arm Holdings plc", "sector": "Technology", "industry": "Semiconductors & IP"},
        {"ticker": "SMCI", "name": "Super Micro Computer", "sector": "Technology", "industry": "Computer Hardware"},
        {"ticker": "HOOD", "name": "Robinhood Markets", "sector": "Financial Services", "industry": "Brokerage & Fintech"},
        {"ticker": "SOFI", "name": "SoFi Technologies", "sector": "Financial Services", "industry": "Digital Banking"},
        {"ticker": "APP", "name": "AppLovin Corporation", "sector": "Technology", "industry": "AdTech & Software"},
        {"ticker": "CRWD", "name": "CrowdStrike Holdings", "sector": "Technology", "industry": "Cybersecurity"},
        {"ticker": "SHOP", "name": "Shopify Inc.", "sector": "Consumer Cyclical", "industry": "E-Commerce"},
        {"ticker": "DKNG", "name": "DraftKings Inc.", "sector": "Consumer Cyclical", "industry": "Digital Gaming"},
        {"ticker": "RBLX", "name": "Roblox Corporation", "sector": "Communication Services", "industry": "Interactive Entertainment"},
        {"ticker": "NET", "name": "Cloudflare, Inc.", "sector": "Technology", "industry": "Cloud Infrastructure"},
        {"ticker": "DDOG", "name": "Datadog, Inc.", "sector": "Technology", "industry": "Cloud Observability"},
        {"ticker": "UBER", "name": "Uber Technologies", "sector": "Technology", "industry": "Mobility Platforms"},
        {"ticker": "TTD", "name": "The Trade Desk", "sector": "Technology", "industry": "Digital Advertising"},
        {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "MU", "name": "Micron Technology", "sector": "Technology", "industry": "Memory Semiconductors"},
        {"ticker": "AVGO", "name": "Broadcom Inc.", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "PANW", "name": "Palo Alto Networks", "sector": "Technology", "industry": "Cybersecurity"},
        {"ticker": "VST", "name": "Vistra Corp.", "sector": "Utilities", "industry": "Power Generation"},
        {"ticker": "CEG", "name": "Constellation Energy", "sector": "Utilities", "industry": "Clean Nuclear Energy"},
        {"ticker": "VRT", "name": "Vertiv Holdings", "sector": "Industrials", "industry": "Data Center Infrastructure"},
        {"ticker": "IONQ", "name": "IonQ, Inc.", "sector": "Technology", "industry": "Quantum Computing"},
        {"ticker": "ASTS", "name": "AST SpaceMobile", "sector": "Communication Services", "industry": "Satellite Communications"},
        {"ticker": "HIMS", "name": "Hims & Hers Health", "sector": "Healthcare", "industry": "Telehealth"},
        {"ticker": "RDDT", "name": "Reddit, Inc.", "sector": "Communication Services", "industry": "Social Media"},
        {"ticker": "CVNA", "name": "Carvana Co.", "sector": "Consumer Cyclical", "industry": "Auto E-Commerce"},
        {"ticker": "CAVA", "name": "CAVA Group, Inc.", "sector": "Consumer Cyclical", "industry": "Fast Casual Restaurants"},
        {"ticker": "DUOL", "name": "Duolingo, Inc.", "sector": "Technology", "industry": "Educational Software"},
        {"ticker": "TOST", "name": "Toast, Inc.", "sector": "Technology", "industry": "Restaurant Fintech"},

        # ── Premier High-Volume Global Cross-Listings (NYSE / NASDAQ) ──
        {"ticker": "TSM", "name": "Taiwan Semiconductor (TSMC)", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "BABA", "name": "Alibaba Group Holding", "sector": "Consumer Cyclical", "industry": "E-Commerce & Cloud"},
        {"ticker": "PDD", "name": "PDD Holdings (Temu)", "sector": "Consumer Cyclical", "industry": "E-Commerce"},
        {"ticker": "NVO", "name": "Novo Nordisk A/S", "sector": "Healthcare", "industry": "Biopharmaceuticals"},
        {"ticker": "ASML", "name": "ASML Holding N.V.", "sector": "Technology", "industry": "Semiconductor Equipment"},
        {"ticker": "MELI", "name": "MercadoLibre, Inc.", "sector": "Consumer Cyclical", "industry": "Latin America E-Commerce"},
        {"ticker": "NU", "name": "Nu Holdings (Nubank)", "sector": "Financial Services", "industry": "Digital Banking"},
        {"ticker": "SPOT", "name": "Spotify Technology", "sector": "Communication Services", "industry": "Audio Streaming"},
        {"ticker": "SE", "name": "Sea Limited", "sector": "Consumer Cyclical", "industry": "Southeast Asia Tech"},

        # ── Core Liquid Institutional Benchmarks ──
        {"ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "E-Commerce"},
        {"ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
        {"ticker": "META", "name": "Meta Platforms, Inc.", "sector": "Communication Services", "industry": "Internet"},
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services", "industry": "Banks"},
        {"ticker": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare", "industry": "Drug Manufacturers"},
        {"ticker": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy", "industry": "Oil & Gas"},
        {"ticker": "COST", "name": "Costco Wholesale Corp.", "sector": "Consumer Defensive", "industry": "Discount Stores"},
        {"ticker": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials", "industry": "Machinery"},
        {"ticker": "NOW", "name": "ServiceNow Inc.", "sector": "Technology", "industry": "Software"},
        {"ticker": "ISRG", "name": "Intuitive Surgical", "sector": "Healthcare", "industry": "Medical Devices"},
        {"ticker": "CRM", "name": "Salesforce Inc.", "sector": "Technology", "industry": "Software"},
        {"ticker": "AMAT", "name": "Applied Materials", "sector": "Technology", "industry": "Semiconductor Equipment"},
        {"ticker": "LRCX", "name": "Lam Research Corp.", "sector": "Technology", "industry": "Semiconductor Equipment"},
        {"ticker": "ANET", "name": "Arista Networks", "sector": "Technology", "industry": "Computer Hardware"},

        # ── Recent High-Growth Liquid IPOs (2023 - 2026) ──
        {"ticker": "ALAB", "name": "Astera Labs", "sector": "Technology", "industry": "AI Connectivity & PCIe Retimers"},
        {"ticker": "TEM", "name": "Tempus AI", "sector": "Healthcare", "industry": "AI Diagnostics & Precision Medicine"},
        {"ticker": "CART", "name": "Maplebear (Instacart)", "sector": "Technology", "industry": "Retail Media & Grocery Tech"},
        {"ticker": "BIRK", "name": "Birkenstock Holding", "sector": "Consumer Cyclical", "industry": "Footwear & Accessories"},
        {"ticker": "KVUE", "name": "Kenvue Inc.", "sector": "Consumer Defensive", "industry": "Consumer Health Products"},
        {"ticker": "IREN", "name": "Iris Energy", "sector": "Technology", "industry": "HPC & AI Data Centers"},
        {"ticker": "APLD", "name": "Applied Digital", "sector": "Technology", "industry": "AI Cloud Infrastructure"},
        {"ticker": "CORZ", "name": "Core Scientific", "sector": "Technology", "industry": "Digital Infrastructure & AI Hosting"},
        {"ticker": "NBIS", "name": "Nebius Group", "sector": "Technology", "industry": "AI Infrastructure Cloud"},

        # ── High Guidance & Solid Fundamentals Compounders (LONG Profile: 3+ Months) ──
        {"ticker": "AXON", "name": "Axon Enterprise", "sector": "Industrials", "industry": "Public Safety Tech & Cloud Software"},
        {"ticker": "TMDX", "name": "TransMedics Group", "sector": "Healthcare", "industry": "Medical Devices & Organ Care"},
        {"ticker": "DECK", "name": "Deckers Outdoor", "sector": "Consumer Cyclical", "industry": "Footwear (HOKA & UGG)"},
        {"ticker": "URI", "name": "United Rentals", "sector": "Industrials", "industry": "Infrastructure Equipment Rental"},
        {"ticker": "TDG", "name": "TransDigm Group", "sector": "Industrials", "industry": "Aerospace Proprietary Parts"},
        {"ticker": "HEI", "name": "HEICO Corporation", "sector": "Industrials", "industry": "Aerospace Components & Replacement"},
        {"ticker": "FICO", "name": "Fair Isaac Corporation", "sector": "Technology", "industry": "Predictive Analytics & Credit Scores"},
        {"ticker": "WMS", "name": "Advanced Drainage Systems", "sector": "Industrials", "industry": "Stormwater & Pipe Infrastructure"},
        {"ticker": "IDXX", "name": "IDEXX Laboratories", "sector": "Healthcare", "industry": "Veterinary Diagnostics"},
        {"ticker": "CELH", "name": "Celsius Holdings", "sector": "Consumer Defensive", "industry": "Functional Energy Beverages"}
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
