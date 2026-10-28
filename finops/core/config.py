"""
finops/core/config.py — Configuration Loader
============================================
Loads settings and market registries from YAML with environment overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_yaml(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Settings:
    _instance = None

    def __init__(self):
        root = get_project_root()
        self.settings_dict = load_yaml(root / "config" / "settings.yaml")
        self.markets_dict = load_yaml(root / "config" / "markets.yaml")

    @classmethod
    def get(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

    @property
    def app(self) -> Dict[str, Any]:
        return self.settings_dict.get("app", {})

    @property
    def horizons(self) -> Dict[str, Any]:
        return self.settings_dict.get("horizons", {})

    @property
    def liquidity_filters(self) -> Dict[str, Any]:
        return self.settings_dict.get("liquidity_filters", {})

    @property
    def scoring(self) -> Dict[str, Any]:
        return self.settings_dict.get("scoring", {})

    @property
    def trade_plan(self) -> Dict[str, Any]:
        return self.settings_dict.get("trade_plan", {})

    @property
    def llm(self) -> Dict[str, Any]:
        return self.settings_dict.get("llm", {})

    @property
    def delivery(self) -> Dict[str, Any]:
        return self.settings_dict.get("delivery", {})

    @property
    def compliance(self) -> Dict[str, Any]:
        return self.settings_dict.get("compliance", {})

    @property
    def market_definitions(self) -> Dict[str, Any]:
        return self.markets_dict.get("markets", {})
