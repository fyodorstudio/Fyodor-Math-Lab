"""Path and Horizon Indexing for Macro Releases.

Calculates:
- Next-H1 entry bar open strictly after release timestamp (with entry delay)
- Pre-release ATR(14) using Wilder smoothing over strictly completed pre-release bars:
  (bar_open + 3600 STRICTLY LESS than release_timestamp, per Contract)
- H60 / H120 / H240 continuous market bar coverage
- Weekday gap detection enforcing documented trading session rules

Zero lookahead is strictly enforced.
Validation inspects OHLC structure but NEVER calculates price returns or trade outcomes.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from models import CandleBar


def find_entry_bar(
    candles: List[CandleBar], release_timestamp: int
) -> Tuple[Optional[int], Optional[CandleBar], Optional[int]]:
    """Locates the earliest complete H1 candle with bar_open > release_timestamp.
    
    Returns:
        (entry_bar_idx, entry_bar, entry_delay_seconds)
    """
    for idx, bar in enumerate(candles):
        if bar.timestamp > release_timestamp:
            delay = bar.timestamp - release_timestamp
            return idx, bar, delay
    return None, None, None


def calculate_pre_release_atr14(
    candles: List[CandleBar], release_timestamp: int
) -> Tuple[bool, Optional[float], int]:
    """Calculates pre-release ATR(14) with Wilder smoothing.
    
    Per Contract:
    1. Select all bars whose close (bar_open + 3600s) is STRICTLY LESS than release_timestamp:
       (bar_open + 3600 < release_timestamp).
    2. Requires at least 251 usable bars to form 250 true ranges.
    3. Take the last 251 bars (providing 250 TR transitions).
    4. TR_i = max(high_i - low_i, abs(high_i - close_{i-1}), abs(low_i - close_{i-1})).
    5. Seed ATR = arithmetic mean of the first 14 TR values.
    6. For each subsequent TR: ATR_new = (13 * ATR_old + TR) / 14.
    7. Strictly zero lookahead: release candle, candle closing exactly at release,
       and entry candle are strictly excluded.
    
    Returns:
        (has_atr_warmup, final_atr_value, usable_pre_bars_count)
    """
    # Strict inequality per contract: close < release_timestamp
    pre_bars = [b for b in candles if b.timestamp + 3600 < release_timestamp]
    n_pre = len(pre_bars)
    
    if n_pre < 251:
        return False, None, n_pre
    
    # Use the most recent 251 bars for 250 TRs
    window = pre_bars[-251:]
    
    # Calculate 250 TR values
    tr_values: List[float] = []
    for i in range(1, len(window)):
        curr = window[i]
        prev = window[i - 1]
        tr = max(
            curr.high - curr.low,
            abs(curr.high - prev.close),
            abs(curr.low - prev.close)
        )
        tr_values.append(tr)
        
    if len(tr_values) != 250:
        return False, None, n_pre
        
    # Seed with arithmetic mean of first 14 TRs
    atr = sum(tr_values[:14]) / 14.0
    
    # Wilder smoothing for remaining 236 TRs
    for tr in tr_values[14:]:
        atr = (13.0 * atr + tr) / 14.0
        
    return True, atr, n_pre


def inspect_path_coverage(
    candles: List[CandleBar], entry_idx: Optional[int]
) -> Dict[str, Any]:
    """Inspects raw path bar counts starting with entry_idx as bar 1."""
    if entry_idx is None:
        return {
            "has_h60": False,
            "has_h120": False,
            "has_h240": False,
            "remaining_bars": 0
        }
        
    remaining = len(candles) - entry_idx
    return {
        "has_h60": remaining >= 60,
        "has_h120": remaining >= 120,
        "has_h240": remaining >= 240,
        "remaining_bars": remaining
    }


def is_regular_weekend(dt1: datetime, dt2: datetime) -> bool:
    """Bounded Regular Weekend check:
    Starts Friday evening (>= 20:00), ends Sunday (>= 21:00) or Monday (<= 03:00).
    Strictly bounded: 45.0 <= diff_hours <= 55.0.
    Rejects extended outages (e.g. 10-day Friday-to-Monday outage).
    """
    diff_sec = (dt2 - dt1).total_seconds()
    if diff_sec <= 0:
        return False
    diff_hours = diff_sec / 3600.0
    if dt1.weekday() == 4 and dt1.hour >= 20:
        if (dt2.weekday() == 6 and dt2.hour >= 21) or (dt2.weekday() == 0 and dt2.hour <= 3):
            if 45.0 <= diff_hours <= 55.0:
                return True
    return False


def is_scheduled_market_closure(dt1: datetime, dt2: datetime) -> bool:
    """Checks whether a gap between two bars corresponds to a scheduled market closure.
    
    Documented Session Rules (Narrow & Bounded):
    - Bounded Regular Weekend:
      Starts Friday evening (>= 20:00), ends Sunday (>= 21:00) or Monday (<= 03:00).
      Strictly bounded: 45.0 <= diff_hours <= 55.0.
      Rejects extended outages (e.g. 10-day Friday-to-Monday outage).
    - Bounded Christmas Holiday:
      Spans Christmas Eve (Dec 24 evening >= 18:00), Christmas Day (Dec 25), and Boxing Day (Dec 26),
      or Friday evening before Christmas if Christmas falls on/adjacent to weekend.
      Weekday morning hours on Dec 24 (e.g. 09:00) are normal trading hours and rejected as closures.
      Must end by Dec 26, or Dec 27/28 if weekend adjoining.
      Strictly bounded: diff_hours <= 84.0.
      Rejects arbitrary weekday gaps (e.g. 6-day Dec 22-28 gap).
    - Bounded New Year Holiday:
      Spans New Year's Eve (Dec 31 evening >= 18:00) and New Year's Day (Jan 1) through Jan 2 (or Jan 3/4 if weekend adjoining).
      Must start on Dec 31 (hour >= 18), Jan 1, or Friday Dec 29/30 (hour >= 20).
      Must end by Jan 2 (or Jan 3/4 if weekend adjoining).
      Strictly bounded: diff_hours <= 84.0.
    """
    if is_regular_weekend(dt1, dt2):
        return True

    diff_sec = (dt2 - dt1).total_seconds()
    if diff_sec <= 0:
        return False
    diff_hours = diff_sec / 3600.0

    # 2. Bounded Christmas Holiday:
    # Dec 24 start requires hour >= 18 (trading occurs morning/afternoon of Christmas Eve).
    if dt1.month == 12 and dt1.day in (22, 23, 24, 25):
        if dt2.month == 12 and dt2.day in (25, 26, 27, 28):
            is_valid_christmas_start = (
                (dt1.day == 24 and dt1.hour >= 18)
                or (dt1.day == 25)
                or (dt1.weekday() == 4 and dt1.day in (22, 23) and dt1.hour >= 20)
            )
            if is_valid_christmas_start and diff_hours <= 84.0:
                return True

    # 3. Bounded New Year Holiday:
    # Dec 31 start requires hour >= 18.
    if (dt1.month == 12 and dt1.day in (29, 30, 31)) or (dt1.month == 1 and dt1.day == 1):
        if dt2.month == 1 and dt2.day in (1, 2, 3, 4, 5):
            is_valid_ny_start = (
                (dt1.month == 12 and dt1.day == 31 and dt1.hour >= 18)
                or (dt1.month == 1 and dt1.day == 1)
                or (dt1.weekday() == 4 and dt1.month == 12 and dt1.day in (29, 30) and dt1.hour >= 20)
            )
            if is_valid_ny_start and diff_hours <= 84.0:
                return True

    return False


def detect_path_weekday_gaps(
    candles: List[CandleBar],
    entry_idx: Optional[int],
    horizon_bars: int = 240,
    allow_scheduled_holidays: bool = True
) -> Tuple[int, int]:
    """Detects missing weekday bars along an observed path.
    
    Args:
        candles: Complete list of symbol candles.
        entry_idx: Starting entry candle index.
        horizon_bars: Number of market bars in horizon (60, 120, 240).
        allow_scheduled_holidays: If True, treats Christmas/New Year scheduled closures as valid.
                                  If False, only bounded regular weekends are treated as valid.
        
    Returns:
        (unscheduled_weekday_gap_count, max_unscheduled_weekday_gap_seconds)
    """
    if entry_idx is None or entry_idx + horizon_bars > len(candles):
        return 0, 0
        
    path = candles[entry_idx : entry_idx + horizon_bars]
    gap_count = 0
    max_gap_sec = 0
    
    for i in range(len(path) - 1):
        b1 = path[i]
        b2 = path[i + 1]
        diff_sec = b2.timestamp - b1.timestamp
        if diff_sec > 3600:
            dt1 = datetime.strptime(b1.time_server_text, "%Y.%m.%d %H:%M:%S")
            dt2 = datetime.strptime(b2.time_server_text, "%Y.%m.%d %H:%M:%S")
            
            # Check scheduled market closure
            if allow_scheduled_holidays and is_scheduled_market_closure(dt1, dt2):
                continue
            elif not allow_scheduled_holidays and is_regular_weekend(dt1, dt2):
                continue
                
            gap_count += 1
            if diff_sec > max_gap_sec:
                max_gap_sec = diff_sec
                
    return gap_count, max_gap_sec
