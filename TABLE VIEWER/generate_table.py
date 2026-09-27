"""
Macroeconomic Event Displacement Table Generator Entry Point.
Auditable, light-mode HTML table viewer generator.
"""

import os
import sys

# Ensure local package import works when invoked directly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from generator import (
    load_candles,
    parse_calendar_episodes,
    compute_pips_for_episodes,
    build_html,
    CODEX_DISPLAY_APPROVED,
    OUTPUT_HTML_PATH,
    PAIRS,
    PAIR_METADATA,
    EVENT_FAMILIES
)


def main():
    candles_db = load_candles()
    episodes = parse_calendar_episodes()
    episodes_with_pips = compute_pips_for_episodes(episodes, candles_db)
    build_html(episodes_with_pips)


if __name__ == "__main__":
    main()
