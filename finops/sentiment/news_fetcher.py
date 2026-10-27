"""
finops/sentiment/news_fetcher.py — News & Social Sentiment Aggregator
====================================================================
Lightweight sentiment layer scoring news feeds, social buzz (Reddit / Xueqiu),
and headlines into normalized 0-100 scores.
"""

from typing import List, Dict, Any, Tuple
from finops.core.models import NewsItem


class NewsSentimentAggregator:
    def __init__(self):
        pass

    def evaluate_sentiment(self, raw_news: List[Dict[str, Any]]) -> Tuple[float, List[NewsItem]]:
        """
        Calculates a normalized 0-100 sentiment score and standardizes NewsItem list.
        """
        if not raw_news:
            return 55.0, []

        news_items: List[NewsItem] = []
        score_accumulator = 0.0

        for item in raw_news:
            title = item.get("title", "")
            source = item.get("source", "Market Wire")
            url = item.get("url", "")
            published_at = str(item.get("published_at", "Recent"))

            lower = title.lower()
            bullish_keywords = ["beat", "surge", "record", "growth", "upgrade", "outperform", "soar", "gain", "inflow", "expansion"]
            bearish_keywords = ["miss", "drop", "cut", "downgrade", "fall", "plunge", "loss", "slump", "investigation", "headwind"]

            is_bull = any(k in lower for k in bullish_keywords)
            is_bear = any(k in lower for k in bearish_keywords)

            if is_bull and not is_bear:
                sent = "BULLISH"
                val = 80.0
            elif is_bear:
                sent = "BEARISH"
                val = 30.0
            else:
                sent = "NEUTRAL"
                val = 60.0

            score_accumulator += val
            news_items.append(NewsItem(
                title=title,
                source=source,
                url=url,
                published_at=published_at,
                sentiment=sent
            ))

        avg_score = score_accumulator / len(raw_news)
        return round(avg_score, 1), news_items
