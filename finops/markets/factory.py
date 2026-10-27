"""
finops/markets/factory.py — Market Plug-in Factory
==================================================
Instantiates market plug-ins based on market ID. New markets can be registered dynamically.
"""

from typing import Dict, Type
from finops.markets.base import BaseMarketPlugin
from finops.markets.us_market import USMarketPlugin
from finops.markets.cn_market import CNMarketPlugin
from finops.markets.mx_market import MXMarketPlugin
from finops.core.config import Settings

_PLUGIN_REGISTRY: Dict[str, Type[BaseMarketPlugin]] = {
    "us": USMarketPlugin,
    "cn": CNMarketPlugin,
    "mx": MXMarketPlugin,
}


def register_market_plugin(market_id: str, plugin_cls: Type[BaseMarketPlugin]):
    """Registers a new market plug-in dynamically."""
    _PLUGIN_REGISTRY[market_id.lower()] = plugin_cls


def get_market_plugin(market_id: str) -> BaseMarketPlugin:
    """Instantiates a market plug-in using configured settings."""
    market_id = market_id.lower()
    if market_id not in _PLUGIN_REGISTRY:
        raise ValueError(f"Unknown market '{market_id}'. Available: {list(_PLUGIN_REGISTRY.keys())}")

    settings = Settings.get()
    market_cfg = settings.market_definitions.get(market_id, {})
    plugin_cls = _PLUGIN_REGISTRY[market_id]
    return plugin_cls(market_id=market_id, config=market_cfg)
