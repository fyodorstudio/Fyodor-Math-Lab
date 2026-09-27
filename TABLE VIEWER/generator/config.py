"""
Configuration, metadata, and directory paths for Macroeconomic Event Displacement Table Generator.
"""

import os
from typing import Dict, Any, List, Optional


def find_repo_root(start_dir: Optional[str] = None) -> str:
    """Finds the Macro Research repo root by walking upwards until data/pinned exists."""
    curr = os.path.abspath(start_dir or os.path.dirname(__file__))
    while True:
        if os.path.exists(os.path.join(curr, "data", "pinned")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            raise FileNotFoundError("Could not locate Macro Research repo root containing data/pinned")
        curr = parent


BASE_DIR = find_repo_root(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server")
CANDLES_DIR = os.path.join(DATA_DIR, "candles")
CALENDAR_PATH = os.path.join(DATA_DIR, "calendar_releases.csv")
VIEWER_DIR = os.path.join(BASE_DIR, "TABLE VIEWER")
OUTPUT_HTML_PATH = os.path.join(VIEWER_DIR, "table_viewer.html")
CPI_SETUP_DIR = os.path.join(VIEWER_DIR, "cpi_setup")
CPI_LEDGER_PATH = os.path.join(CPI_SETUP_DIR, "cpi_trade_ledger.json")

# The 19 full-history FX pairs
PAIRS = [
    "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "EURGBP", "EURAUD", "EURCAD", "EURCHF", "EURNZD",
    "AUDJPY", "CHFJPY", "GBPCHF", "AUDCAD", "AUDCHF", "AUDNZD"
]

# Pair descriptions & Base / Quote classification
PAIR_METADATA: Dict[str, Dict[str, Any]] = {
    "EURUSD": {"desc": "EUR/USD (Base: EUR, Quote: USD)", "base": "EUR", "quote": "USD", "pip": 0.00010, "digits": 5},
    "USDJPY": {"desc": "USD/JPY (Base: USD, Quote: JPY)", "base": "USD", "quote": "JPY", "pip": 0.010, "digits": 3},
    "GBPUSD": {"desc": "GBP/USD (Base: GBP, Quote: USD)", "base": "GBP", "quote": "USD", "pip": 0.00010, "digits": 5},
    "AUDUSD": {"desc": "AUD/USD (Base: AUD, Quote: USD)", "base": "AUD", "quote": "USD", "pip": 0.00010, "digits": 5},
    "USDCAD": {"desc": "USD/CAD (Base: USD, Quote: CAD)", "base": "USD", "quote": "CAD", "pip": 0.00010, "digits": 5},
    "USDCHF": {"desc": "USD/CHF (Base: USD, Quote: CHF)", "base": "USD", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "NZDUSD": {"desc": "NZD/USD (Base: NZD, Quote: USD)", "base": "NZD", "quote": "USD", "pip": 0.00010, "digits": 5},
    "EURJPY": {"desc": "EUR/JPY (Base: EUR, Quote: JPY)", "base": "EUR", "quote": "JPY", "pip": 0.010, "digits": 3},
    "EURGBP": {"desc": "EUR/GBP (Base: EUR, Quote: GBP)", "base": "EUR", "quote": "GBP", "pip": 0.00010, "digits": 5},
    "EURAUD": {"desc": "EUR/AUD (Base: EUR, Quote: AUD)", "base": "EUR", "quote": "AUD", "pip": 0.00010, "digits": 5},
    "EURCAD": {"desc": "EUR/CAD (Base: EUR, Quote: CAD)", "base": "EUR", "quote": "CAD", "pip": 0.00010, "digits": 5},
    "EURCHF": {"desc": "EUR/CHF (Base: EUR, Quote: CHF)", "base": "EUR", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "EURNZD": {"desc": "EUR/NZD (Base: EUR, Quote: NZD)", "base": "EUR", "quote": "NZD", "pip": 0.00010, "digits": 5},
    "AUDJPY": {"desc": "AUD/JPY (Base: AUD, Quote: JPY)", "base": "AUD", "quote": "JPY", "pip": 0.010, "digits": 3},
    "CHFJPY": {"desc": "CHF/JPY (Base: CHF, Quote: JPY)", "base": "CHF", "quote": "JPY", "pip": 0.010, "digits": 3},
    "GBPCHF": {"desc": "GBP/CHF (Base: GBP, Quote: CHF)", "base": "GBP", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "AUDCAD": {"desc": "AUD/CAD (Base: AUD, Quote: CAD)", "base": "AUD", "quote": "CAD", "pip": 0.00010, "digits": 5},
    "AUDCHF": {"desc": "AUD/CHF (Base: AUD, Quote: CHF)", "base": "AUD", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "AUDNZD": {"desc": "AUD/NZD (Base: AUD, Quote: NZD)", "base": "AUD", "quote": "NZD", "pip": 0.00010, "digits": 5}
}

EVENT_FAMILIES: Dict[str, Dict[str, Any]] = {
    "US_INFLATION": {
        "label": "US INFLATION",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840030005", "840030006", "840010001"]  # CPI, Core CPI, Core PCE
    },
    "US_LABOR": {
        "label": "US LABOR",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840030016"]  # Nonfarm Payrolls
    },
    "US_RETAIL_SALES": {
        "label": "US RETAIL SALES",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840020010", "840020011"]  # Retail Sales m/m, Core Retail Sales m/m
    },
    "GERMAN_IFO": {
        "label": "GERMAN IFO",
        "affected": "EUR pairs: EURUSD, EURGBP, EURJPY, EURAUD, EURCAD, EURCHF, EURNZD",
        "series": ["276030003", "276030001"]  # Ifo Climate, Expectations
    },
    "US_ISM_PMI": {
        "label": "US ISM PMI",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840040001"]  # ISM Mfg PMI
    }
}

SERIES_NAMES: Dict[str, Dict[str, Any]] = {
    "840030005": {"name": "USD CPI m/m", "unit": "%", "digits": 1},
    "840030006": {"name": "USD Core CPI m/m", "unit": "%", "digits": 1},
    "840010001": {"name": "USD Core PCE m/m", "unit": "%", "digits": 1},
    "840030016": {"name": "USD Nonfarm Payrolls", "unit": "k", "digits": 0},
    "840020010": {"name": "Retail Sales m/m", "unit": "%", "digits": 1},
    "840020011": {"name": "Core Retail Sales m/m", "unit": "%", "digits": 1},
    "276030003": {"name": "Ifo Business Climate", "unit": "pts", "digits": 1},
    "276030001": {"name": "Ifo Business Expectations", "unit": "pts", "digits": 1},
    "840040001": {"name": "ISM Manufacturing PMI", "unit": "pts", "digits": 1}
}

# Display Approval Gate for Historical Results Table
# Approved by Codex for display of audited historical CPI results only.
CODEX_DISPLAY_APPROVED: bool = True
