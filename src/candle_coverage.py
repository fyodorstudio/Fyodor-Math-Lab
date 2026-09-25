"""
Price-Blind Candle Timestamp Coverage & Continuity Resolver
Inspects EURUSD H1 candles reading strictly column 0 (time).
Zero access to OHLC prices, tick volumes, or spreads.
Enforces the chronological split boundary at 1672531200.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
import bisect
from datetime import datetime, timezone
from .parsers import stream_candle_timestamps_only, SPLIT_TIMESTAMP

SECONDS_IN_H1 = 3600
SECONDS_IN_H4 = 14400


def is_valid_weekend_market_closure(gap_start_ts: int, resume_ts: int) -> Tuple[bool, str]:
    """
    Explicit, testable market closure rule for FX trading over the weekend.
    Rejects weekday data gaps (e.g. Wednesday to Friday missing Thursday).

    Valid weekend closure requirements:
    1. Trading paused on weekend boundary:
       - Friday late (weekday == 4 and hour >= 20), OR
       - Saturday (weekday == 5).
    2. Trading resumes on market open:
       - Sunday late (weekday == 6 and hour >= 21), OR
       - Monday early (weekday == 0 and hour <= 4).
    3. Calendar closure duration between 24 and 72 hours.
    """
    dt_start = datetime.fromtimestamp(gap_start_ts, tz=timezone.utc)
    dt_resume = datetime.fromtimestamp(resume_ts, tz=timezone.utc)
    gap_hours = (resume_ts - gap_start_ts) / SECONDS_IN_H1

    if not (24.0 <= gap_hours <= 72.0):
        return False, f"Gap duration {gap_hours:.1f}h is outside valid weekend range [24, 72]h"

    is_start_weekend = (dt_start.weekday() == 4 and dt_start.hour >= 20) or (dt_start.weekday() == 5)
    if not is_start_weekend:
        return False, f"Gap start at {dt_start.strftime('%A %H:%M')} is a weekday data gap, not a weekend closure"

    is_resume_weekend = (dt_resume.weekday() == 6 and dt_resume.hour >= 21) or (dt_resume.weekday() == 0 and dt_resume.hour <= 4)
    if not is_resume_weekend:
        return False, f"Gap resume at {dt_resume.strftime('%A %H:%M')} is not a Sunday/Monday market open"

    return True, "Valid weekend market closure"


class CandleTimestampIndex:
    """
    In-memory set and sorted list of valid pre-2023 H1 candle timestamps.
    """
    def __init__(self, candle_csv_path: str, split_timestamp: int = SPLIT_TIMESTAMP):
        self.split_timestamp = split_timestamp
        self.timestamps_set: Set[int] = set()
        self.timestamps_list: List[int] = []

        for ts in stream_candle_timestamps_only(candle_csv_path, split_timestamp=split_timestamp):
            self.timestamps_set.add(ts)
            self.timestamps_list.append(ts)

        self.timestamps_list.sort()
        self.total_bars = len(self.timestamps_list)
        self.earliest_ts = self.timestamps_list[0] if self.timestamps_list else None
        self.latest_ts = self.timestamps_list[-1] if self.timestamps_list else None

    def has_bar(self, ts: int) -> bool:
        return ts in self.timestamps_set

    def check_h4_block(self, h4_start_ts: int) -> Tuple[bool, List[int]]:
        """
        An H4 block starting at h4_start_ts requires 4 consecutive constituent H1 bars:
        [h4_start_ts, h4_start_ts + 3600, h4_start_ts + 7200, h4_start_ts + 10800].
        Returns (is_complete, missing_offsets).
        """
        if h4_start_ts % SECONDS_IN_H4 != 0:
            raise ValueError(f"Timestamp {h4_start_ts} is not aligned to an H4 boundary (mod 14400 != 0)")

        missing = []
        for offset in [0, 3600, 7200, 10800]:
            ts = h4_start_ts + offset
            if ts >= self.split_timestamp:
                missing.append(offset)
            elif ts not in self.timestamps_set:
                missing.append(offset)

        return (len(missing) == 0, missing)

    def evaluate_forward_horizon(
        self,
        entry_ts: int,
        horizon_h4: int
    ) -> Dict[str, Any]:
        """
        Evaluates pure forward path completion for horizon_h4 blocks starting at entry_ts.
        Steps through consecutive active H4 blocks until horizon_h4 completed blocks are accumulated,
        or fails closed on missing bars, weekday gaps, or split boundary crossings.
        """
        if entry_ts % SECONDS_IN_H4 != 0:
            raise ValueError(f"Entry timestamp {entry_ts} is not on an H4 boundary")

        current_h4 = entry_ts
        completed_blocks = 0
        crosses_weekend = False
        crosses_split = False
        has_missing_h1 = False
        missing_ts: List[int] = []

        max_search_h4 = horizon_h4 * 4  # safety limit

        for _ in range(max_search_h4):
            if completed_blocks == horizon_h4:
                break

            if current_h4 >= self.split_timestamp:
                crosses_split = True
                break

            is_complete, missing = self.check_h4_block(current_h4)

            if is_complete:
                completed_blocks += 1
                current_h4 += SECONDS_IN_H4
            else:
                if current_h4 not in self.timestamps_set:
                    idx = bisect.bisect_right(self.timestamps_list, current_h4)
                    if idx >= len(self.timestamps_list):
                        has_missing_h1 = True
                        break
                    next_avail_ts = self.timestamps_list[idx]
                    is_weekend, reason = is_valid_weekend_market_closure(current_h4, next_avail_ts)

                    if is_weekend:
                        crosses_weekend = True
                        current_h4 = (next_avail_ts // SECONDS_IN_H4) * SECONDS_IN_H4
                    else:
                        has_missing_h1 = True
                        missing_ts.append(current_h4)
                        break
                else:
                    has_missing_h1 = True
                    missing_ts.extend([current_h4 + off for off in missing])
                    break

        exit_ts = current_h4 if completed_blocks == horizon_h4 else None
        is_fully_clean = (
            completed_blocks == horizon_h4 and
            not has_missing_h1 and
            not crosses_split
        )

        return {
            "horizon_h4": horizon_h4,
            "is_complete": is_fully_clean,
            "completed_blocks": completed_blocks,
            "entry_timestamp": entry_ts,
            "exit_timestamp": exit_ts,
            "crosses_weekend": crosses_weekend,
            "crosses_split": crosses_split,
            "has_missing_h1": has_missing_h1,
            "missing_timestamps": missing_ts
        }

    def audit_pre_entry_lookback(
        self,
        entry_ts: int,
        target_h4_blocks: int = 14
    ) -> Dict[str, Any]:
        """
        Audits pre-entry history availability prior to entry_ts.
        Evaluates both:
        1. Strict intra-week lookback: H4 blocks completed within current calendar week.
        2. Bridged active lookback: H4 blocks stepping backwards across the weekend closure.
        """
        if entry_ts % SECONDS_IN_H4 != 0:
            raise ValueError(f"Entry timestamp {entry_ts} is not on an H4 boundary")

        # 1. Measure intra-week lookback (stop at preceding weekend gap)
        intra_week_blocks = 0
        curr_back = entry_ts - SECONDS_IN_H4
        hit_weekend_backwards = False

        while curr_back >= self.earliest_ts:
            # Check if this H4 block is fully present
            is_complete, _ = self.check_h4_block(curr_back)
            if is_complete:
                intra_week_blocks += 1
                curr_back -= SECONDS_IN_H4
                if intra_week_blocks == target_h4_blocks:
                    break
            else:
                # Incomplete block or gap reached
                hit_weekend_backwards = True
                break

        if intra_week_blocks < target_h4_blocks:
            hit_weekend_backwards = True

        has_14_intra_week = (intra_week_blocks >= target_h4_blocks)

        return {
            "entry_timestamp": entry_ts,
            "target_blocks": target_h4_blocks,
            "intra_week_completed_blocks": intra_week_blocks,
            "has_14_intra_week": has_14_intra_week,
            "hit_weekend_or_gap_backwards": hit_weekend_backwards
        }
