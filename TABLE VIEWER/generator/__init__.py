"""
Macroeconomic Event Displacement Table Generator package.
"""

from .config import (
    find_repo_root,
    BASE_DIR,
    DATA_DIR,
    CANDLES_DIR,
    CALENDAR_PATH,
    OUTPUT_HTML_PATH,
    CPI_LEDGER_PATH,
    CPI_SETUP_DIR,
    PAIRS,
    PAIR_METADATA,
    EVENT_FAMILIES,
    SERIES_NAMES,
    CODEX_DISPLAY_APPROVED
)
from .calendar import parse_calendar_episodes
from .candles import load_candles, compute_pips_for_episodes
from .cpi_ledger import load_cpi_ledger_data, prepare_cpi_presentation_data, render_cpi_section
from .rendering import build_html

__all__ = [
    "find_repo_root",
    "BASE_DIR",
    "DATA_DIR",
    "CANDLES_DIR",
    "CALENDAR_PATH",
    "OUTPUT_HTML_PATH",
    "CPI_LEDGER_PATH",
    "CPI_SETUP_DIR",
    "PAIRS",
    "PAIR_METADATA",
    "EVENT_FAMILIES",
    "SERIES_NAMES",
    "CODEX_DISPLAY_APPROVED",
    "parse_calendar_episodes",
    "load_candles",
    "compute_pips_for_episodes",
    "load_cpi_ledger_data",
    "prepare_cpi_presentation_data",
    "render_cpi_section",
    "build_html"
]
