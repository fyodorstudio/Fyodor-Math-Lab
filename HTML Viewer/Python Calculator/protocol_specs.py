"""Protocol specifications and constants for US CPI and US NFP research.

Defines exact MT5 calendar event IDs, units, universe boundaries,
direction hypotheses, and signal derivation logic.
"""

from typing import Optional, Tuple, Dict, Set


# =====================================================================
# FX UNIVERSE DEFINITIONS & BOUNDARIES
# =====================================================================

ALL_EXPORTED_PAIRS: Tuple[str, ...] = (
    "AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD",
    "NZDCAD", "NZDCHF", "NZDJPY"
)

# 9 globally excluded pairs due to truncated broker history starting Nov 2025.
# NEVER admitted into active research, candidate denominators, or trade denominators.
GLOBALLY_EXCLUDED_PAIRS: Tuple[str, ...] = (
    "CADCHF", "CADJPY", "GBPAUD", "GBPCAD", "GBPJPY",
    "GBPNZD", "NZDCAD", "NZDCHF", "NZDJPY"
)

# Active research universe (19 pairs)
ACTIVE_RESEARCH_PAIRS: Tuple[str, ...] = tuple(
    p for p in ALL_EXPORTED_PAIRS if p not in GLOBALLY_EXCLUDED_PAIRS
)

# Active relevant pairs for USD releases (CPI and NFP) - exactly 7 pairs
ACTIVE_USD_PAIRS: Tuple[str, ...] = (
    "AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"
)

USD_BASE_PAIRS: Set[str] = {"USDCAD", "USDCHF", "USDJPY"}
USD_QUOTE_PAIRS: Set[str] = {"AUDUSD", "EURUSD", "GBPUSD", "NZDUSD"}

PIP_SIZES: Dict[str, float] = {
    "AUDUSD": 0.0001,
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "NZDUSD": 0.0001,
    "USDCAD": 0.0001,
    "USDCHF": 0.0001,
    "USDJPY": 0.01,
}

# =====================================================================
# EXACT CALENDAR EVENT DEFINITIONS (Verified from V4 Snapshot)
# =====================================================================

# US CPI Family (Sector: CALENDAR_SECTOR_PRICES)
EVENT_ID_US_CPI_MM = "840030005"         # CPI m/m (unit: percent, digits: 1)
EVENT_ID_US_CORE_CPI_MM = "840030006"    # Core CPI m/m (unit: percent, digits: 1)
EVENT_ID_US_CPI_YY = "840030007"         # CPI y/y (unit: percent, digits: 1)
EVENT_ID_US_CORE_CPI_YY = "840030008"    # Core CPI y/y (unit: percent, digits: 1)

CPI_CONSTITUENT_IDS: Set[str] = {
    EVENT_ID_US_CPI_MM,
    EVENT_ID_US_CORE_CPI_MM,
    EVENT_ID_US_CPI_YY,
    EVENT_ID_US_CORE_CPI_YY,
}

# US NFP Family (Jobs Report) (Sector: CALENDAR_SECTOR_JOBS)
EVENT_ID_US_UNEMPLOYMENT_RATE = "840030015"       # Unemployment Rate (unit: percent, digits: 1)
EVENT_ID_US_NONFARM_PAYROLLS = "840030016"        # Nonfarm Payrolls (unit: jobs, multiplier: thousands)
EVENT_ID_US_AVG_HOURLY_EARNINGS_MM = "840030018"  # Avg Hourly Earnings m/m (unit: percent, digits: 1)
EVENT_ID_US_AVG_HOURLY_EARNINGS_YY = "840030019"  # Avg Hourly Earnings y/y (unit: percent, digits: 1)

NFP_CONSTITUENT_IDS: Set[str] = {
    EVENT_ID_US_NONFARM_PAYROLLS,
    EVENT_ID_US_UNEMPLOYMENT_RATE,
    EVENT_ID_US_AVG_HOURLY_EARNINGS_MM,
    EVENT_ID_US_AVG_HOURLY_EARNINGS_YY,
}

# Coincident Collision Event IDs (Strictly Verified from V4 Snapshot calendar_events.csv)
EVENT_ID_US_INITIAL_JOBLESS_CLAIMS = "840140001"   # Initial Jobless Claims (USD, verified)
EVENT_ID_US_TRADE_BALANCE = "840020001"           # US Trade Balance (USD, verified)
EVENT_ID_CAD_EMPLOYMENT_CHANGE = "124010011"      # CAD Employment Change (CAD, verified)
EVENT_ID_CAD_UNEMPLOYMENT_RATE = "124010014"      # CAD Unemployment Rate (CAD, verified)

# V2 Versioned Protocol & Run Identifiers
CPI_V2_PROTOCOL_ID = "CPI_EXPLORATION_V2"
NFP_V2_PROTOCOL_ID = "NFP_EXPLORATION_V2"
V2_RUN_ID = "run_20260928_v2"

# =====================================================================
# TEMPORAL BOUNDARIES
# =====================================================================

CORE_PANEL_START_TEXT = "2015.01.01 00:00:00"
CORE_PANEL_END_TEXT = "2025.12.31 23:59:59"
PARTIAL_PANEL_2026_END_TEXT = "2026.08.31 23:59:59"

# =====================================================================
# SIGNAL DERIVATION & ZERO / MISSING INTEGRITY LOGIC
# =====================================================================

def compute_difference(minuend: Optional[float], subtrahend: Optional[float]) -> Optional[float]:
    """Computes arithmetic difference (A - B) without coercing missing values to zero.
    
    Zero and missing are strictly distinct states.
    If either value is None, the result is strictly None.
    """
    if minuend is None or subtrahend is None:
        return None
    return round(minuend - subtrahend, 6)


def classify_signal_state(diff: Optional[float]) -> str:
    """Classifies a derived difference into strict non-overlapping states."""
    if diff is None:
        return "MISSING"
    if diff > 1e-9:
        return "POSITIVE"
    if diff < -1e-9:
        return "NEGATIVE"
    return "ZERO"


def invert_usd_direction_for_pair(usd_direction: Optional[int], pair: str) -> Optional[int]:
    """Maps USD currency direction (+1 = USD strength, -1 = USD weakness) to pair direction.
    
    For Base USD pairs (USDCAD, USDCHF, USDJPY):
      USD strength (+1) -> Long pair (+1)
      USD weakness (-1) -> Short pair (-1)
      
    For Quote USD pairs (AUDUSD, EURUSD, GBPUSD, NZDUSD):
      USD strength (+1) -> Short pair (-1)
      USD weakness (-1) -> Long pair (+1)
    """
    if usd_direction is None:
        return None
    
    if pair in USD_BASE_PAIRS:
        return usd_direction
    elif pair in USD_QUOTE_PAIRS:
        return -usd_direction
    else:
        raise ValueError(f"Pair {pair} is not an approved active USD pair.")


def assert_event_id_valid(event_id: str, raw_dir: str) -> bool:
    """Validates that an event ID genuinely exists in the raw calendar_events.csv.
    
    Fails loudly if the ID does not exist, preventing typographical errors or invented IDs.
    Returns True if valid.
    """
    import os
    import csv
    events_path = os.path.join(raw_dir, "calendar_events.csv")
    if not os.path.exists(events_path):
        raise FileNotFoundError(f"calendar_events.csv not found at {events_path}")
    
    with open(events_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("event_id") == event_id:
                return True
    raise ValueError(f"CRITICAL: Event ID '{event_id}' does NOT exist in {events_path}!")

