"""
Price-Blind Candle Timestamp Coverage & Continuity Resolver
Inspects EURUSD H1 candles reading strictly column 0 (time).
Zero access to OHLC prices, tick volumes, or spreads.
Enforces the chronological split boundary at 1672531200.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from .parsers import stream_candle_timestamps_only, SPLIT_TIMESTAMP

SECONDS_IN_H1 = 3600
SECONDS_IN_H4 = 14400


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
        An H4 block starting at h4_start_ts requires 4 consecutive H1 bars:
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

    def evaluate_holding_horizon(
        self,
        entry_ts: int,
        horizon_h4: int
    ) -> Dict[str, Any]:
        """
        Evaluates forward completion for horizon_h4 blocks starting at entry_ts.
        Steps through consecutive active H4 blocks until horizon_h4 completed blocks are accumulated,
        or fails closed on missing bars, gaps, or split boundary crossings.
        """
        if entry_ts % SECONDS_IN_H4 != 0:
            raise ValueError(f"Entry timestamp {entry_ts} is not on an H4 boundary")

        current_h4 = entry_ts
        completed_blocks = 0
        crosses_weekend = False
        crosses_split = False
        has_missing_h1 = False
        missing_ts: List[int] = []

        # Iterate active market bars
        # A 6 H4 horizon requires 6 completed H4 blocks = 24 active hours
        # A 12 H4 horizon requires 12 completed H4 blocks = 48 active hours
        # In FX, weekend closure is between Friday ~23:00/24:00 and Sunday ~23:00/00:00 (approx 48h wall clock gap)
        max_search_h4 = horizon_h4 * 4  # safety limit to prevent infinite loops

        for _ in range(max_search_h4):
            if completed_blocks == horizon_h4:
                break

            # If current_h4 reaches or exceeds split, mark violation
            if current_h4 >= self.split_timestamp:
                crosses_split = True
                break

            # Check if this H4 block is present
            is_complete, missing = self.check_h4_block(current_h4)

            if is_complete:
                completed_blocks += 1
                # Next contiguous H4
                current_h4 += SECONDS_IN_H4
            else:
                # If block is missing, check if it's a weekend closure or a missing bar
                # Friday close to Sunday/Monday open is typically a gap of ~48 hours
                # Check if first H1 bar exists
                if current_h4 not in self.timestamps_set:
                    # Let's see if this is a weekend jump: find next available bar in timestamps_list
                    # Binary search or scan
                    import bisect
                    idx = bisect.bisect_right(self.timestamps_list, current_h4)
                    if idx >= len(self.timestamps_list):
                        # End of data reached
                        has_missing_h1 = True
                        break
                    next_avail_ts = self.timestamps_list[idx]
                    gap_hours = (next_avail_ts - current_h4) / SECONDS_IN_H1

                    if 24 <= gap_hours <= 72:
                        # Typical weekend closure gap
                        crosses_weekend = True
                        # Advance current_h4 to the H4 block of next_avail_ts
                        current_h4 = (next_avail_ts // SECONDS_IN_H4) * SECONDS_IN_H4
                    else:
                        # Weekday missing bar or irregular gap
                        has_missing_h1 = True
                        missing_ts.append(current_h4)
                        break
                else:
                    # Block had some constituent H1 missing
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
