"""
finops/markets/base.py — Abstract Market Plug-in Interface
==========================================================
Enables adding new international markets as isolated plug-ins (e.g. US, CN, MX, HK).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd


class BaseMarketPlugin(ABC):
    """
    Standard interface every market plug-in must implement.
    """

    def __init__(self, market_id: str, config: Dict[str, Any]):
        self.market_id = market_id
        self.config = config
        self.name = config.get("name", market_id.upper())
        self.currency = config.get("currency", "USD")
        self.timezone_str = config.get("timezone", "UTC")

    @abstractmethod
    def get_universe(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Returns list of candidate stocks in the market.
        Each item: {'ticker': str, 'name': str, 'sector': str, 'industry': str}
        """
        pass

    @abstractmethod
    def fetch_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches price history and raw fundamental metrics for a given stock.
        Returns dict with:
          - 'prices': pd.DataFrame (Date, Open, High, Low, Close, Volume)
          - 'fundamentals': dict (pe, roe, fcf, debt_to_equity, margins, etc.)
          - 'info': dict (market_cap, sector, industry, name)
        """
        pass

    @abstractmethod
    def fetch_recent_news(self, ticker: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetches recent news items or announcements for ticker.
        """
        pass
