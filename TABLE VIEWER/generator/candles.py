"""
H1 Candle loading and H1..H60 pip displacement computation.
"""

import os
import time
from typing import Dict, List, Any, Tuple, Optional

from .config import PAIRS, PAIR_METADATA, CANDLES_DIR


def load_candles(pairs: Optional[List[str]] = None, candles_dir: Optional[str] = None) -> Dict[str, Tuple[List[Tuple[int, float, float]], Dict[int, int]]]:
    """Loads all specified FX pairs into indexed lookup structures."""
    target_pairs = pairs or PAIRS
    c_dir = candles_dir or CANDLES_DIR
    print(f"Loading candle files for {len(target_pairs)} pairs...")
    t0 = time.time()
    candles_db = {}
    for pair in target_pairs:
        csv_file = os.path.join(c_dir, f"candles_{pair}_H1.csv")
        c_list = []
        ts_map = {}
        if os.path.exists(csv_file):
            with open(csv_file, "r", encoding="utf-8") as f:
                f.readline()
                for line in f:
                    parts = line.split(",")
                    ts = int(parts[0])
                    ts_map[ts] = len(c_list)
                    c_list.append((ts, float(parts[1]), float(parts[4])))  # ts, open, close
        candles_db[pair] = (c_list, ts_map)
    print(f"Loaded candle files in {time.time() - t0:.2f}s")
    return candles_db


def compute_pips_for_episodes(episodes: List[Dict[str, Any]], candles_db: Dict[str, Tuple[List[Tuple[int, float, float]], Dict[int, int]]]) -> List[Dict[str, Any]]:
    """
    Computes H1..H60 raw pip displacements from entry open for each episode across all pairs.
    Raw pips = (Hn close - entry open) / pip_size.
    If pair has no data for that timestamp (e.g. CADJPY before late 2025), stores None.
    If forward bar is beyond data cutoff (late 2026), stores None.
    """
    print("Computing H1..H60 raw pip displacements across all pairs...")
    t0 = time.time()

    for ep in episodes:
        e_ts = ep["entry_ts"]
        pair_pips = {}

        for pair in PAIRS:
            c_list, ts_map = candles_db[pair]
            pip_size = PAIR_METADATA[pair]["pip"]

            if e_ts in ts_map:
                eidx = ts_map[e_ts]
                entry_open = c_list[eidx][1]
                pips = []
                for h in range(60):
                    tidx = eidx + h
                    if tidx < len(c_list):
                        close_p = c_list[tidx][2]
                        # Raw BASE pip displacement: (Close - Open) / pip_size (unrounded for percentile computation)
                        diff_pips = round((close_p - entry_open) / pip_size, 4)
                        pips.append(diff_pips)
                    else:
                        pips.append(None)
                pair_pips[pair] = pips
            else:
                pair_pips[pair] = None

        ep["pips"] = pair_pips

    print(f"Computed displacements in {time.time() - t0:.2f}s")
    return episodes
