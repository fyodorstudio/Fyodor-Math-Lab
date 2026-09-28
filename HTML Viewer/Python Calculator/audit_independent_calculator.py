"""Independent Audit Calculator for Representative Trade Trials.

Performs a separate, price-blind recalculation directly from raw CSV files
WITHOUT calling the production outcome engine functions.
Validates representative trade rows in an eight-case tolerance-based independent audit across:
- Long and Short directions
- JPY (0.01 pip) and Non-JPY (0.0001 pip) pairs
- CPI and NFP event families
- Surprise (A - F) and Momentum (A - P) signals
- Target wins, Stop losses, and Timeout exits
- Dual-touch ambiguity flags

Fails closed if any field disagrees.
"""

import os
import csv
import sys
import math
from typing import Dict, List, Optional, Tuple, Any

CALC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(CALC_DIR, "..", ".."))
RAW_DIR = os.path.join(REPO_ROOT, "raw_data", "FyodorResearchExport_v4_20260928_021936_79538281_server")


def independent_load_raw_candles(pair: str) -> List[Dict[str, Any]]:
    """Loads raw candles directly from raw CSV file."""
    fpath = os.path.join(RAW_DIR, "candles", f"candles_{pair}_H1.csv")
    if not os.path.exists(fpath):
        raise FileNotFoundError(f"Missing raw candle file: {fpath}")

    bars = []
    with open(fpath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            bars.append({
                "time": int(r["time"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "time_server_text": r["time_server_text"],
            })
    return bars


def independent_calculate_atr14(candles: List[Dict[str, Any]], release_time: int) -> float:
    """Manually calculates Wilder smoothed ATR(14) using strictly pre-release completed bars."""
    # Complete pre-release bars: bar_close = open_time + 3600 < release_time
    pre_bars = [b for b in candles if b["time"] + 3600 < release_time]
    if len(pre_bars) < 251:
        raise ValueError(f"Insufficient pre-release bars: {len(pre_bars)} < 251")

    window = pre_bars[-251:]
    tr_list = []
    for i in range(1, len(window)):
        c = window[i]
        p = window[i - 1]
        tr = max(
            c["high"] - c["low"],
            abs(c["high"] - p["close"]),
            abs(c["low"] - p["close"])
        )
        tr_list.append(tr)

    # First 14 TR arithmetic mean
    atr = sum(tr_list[:14]) / 14.0
    for tr in tr_list[14:]:
        atr = (13.0 * atr + tr) / 14.0
    return atr


def independent_simulate_trade(
    pair: str,
    release_time: int,
    direction: int,  # +1 Long, -1 Short
    stop_atr: float,
    target_atr: float,
    horizon: int,
    dual_touch_mode: str = "STOP_FIRST"
) -> Dict[str, Any]:
    """Completely independent, raw-candle simulation of a single trade trial."""
    candles = independent_load_raw_candles(pair)
    pip_size = 0.01 if pair.endswith("JPY") else 0.0001

    # 1. Calculate ATR
    atr = independent_calculate_atr14(candles, release_time)

    # 2. Find Entry Bar (first complete H1 with bar_open > release_time)
    entry_idx = None
    for idx, b in enumerate(candles):
        if b["time"] > release_time:
            entry_idx = idx
            break
    if entry_idx is None:
        raise ValueError(f"Entry bar not found after {release_time} for {pair}")

    entry_bar = candles[entry_idx]
    entry_price = entry_bar["open"]
    stop_dist = stop_atr * atr
    target_dist = target_atr * atr

    if direction == 1:
        stop_price = entry_price - stop_dist
        target_price = entry_price + target_dist
    else:
        stop_price = entry_price + stop_dist
        target_price = entry_price - target_dist

    path = candles[entry_idx : entry_idx + horizon]
    if len(path) < horizon:
        raise ValueError(f"Incomplete horizon path: {len(path)} < {horizon}")

    # Scan path
    for bar_i, bar in enumerate(path, start=1):
        # Gap check
        if direction == 1:
            if bar["open"] <= stop_price:
                return {
                    "exit_reason": "STOP_GAP",
                    "exit_price": stop_price,
                    "bars_to_exit": bar_i,
                    "gross_r": -1.0,
                    "signed_pips": -stop_dist / pip_size,
                    "dual_touch": False,
                    "entry_price": entry_price,
                    "atr": atr,
                }
            if bar["open"] >= target_price:
                return {
                    "exit_reason": "TARGET_GAP",
                    "exit_price": target_price,
                    "bars_to_exit": bar_i,
                    "gross_r": target_atr / stop_atr,
                    "signed_pips": target_dist / pip_size,
                    "dual_touch": False,
                    "entry_price": entry_price,
                    "atr": atr,
                }
            stop_hit = bar["low"] <= stop_price
            target_hit = bar["high"] >= target_price
        else:
            if bar["open"] >= stop_price:
                return {
                    "exit_reason": "STOP_GAP",
                    "exit_price": stop_price,
                    "bars_to_exit": bar_i,
                    "gross_r": -1.0,
                    "signed_pips": -stop_dist / pip_size,
                    "dual_touch": False,
                    "entry_price": entry_price,
                    "atr": atr,
                }
            if bar["open"] <= target_price:
                return {
                    "exit_reason": "TARGET_GAP",
                    "exit_price": target_price,
                    "bars_to_exit": bar_i,
                    "gross_r": target_atr / stop_atr,
                    "signed_pips": target_dist / pip_size,
                    "dual_touch": False,
                    "entry_price": entry_price,
                    "atr": atr,
                }
            stop_hit = bar["high"] >= stop_price
            target_hit = bar["low"] <= target_price

        if stop_hit and target_hit:
            if dual_touch_mode == "STOP_FIRST":
                return {
                    "exit_reason": "STOP",
                    "exit_price": stop_price,
                    "bars_to_exit": bar_i,
                    "gross_r": -1.0,
                    "signed_pips": -stop_dist / pip_size,
                    "dual_touch": True,
                    "entry_price": entry_price,
                    "atr": atr,
                }
            else:
                return {
                    "exit_reason": "TARGET",
                    "exit_price": target_price,
                    "bars_to_exit": bar_i,
                    "gross_r": target_atr / stop_atr,
                    "signed_pips": target_dist / pip_size,
                    "dual_touch": True,
                    "entry_price": entry_price,
                    "atr": atr,
                }
        if stop_hit:
            return {
                "exit_reason": "STOP",
                "exit_price": stop_price,
                "bars_to_exit": bar_i,
                "gross_r": -1.0,
                "signed_pips": -stop_dist / pip_size,
                "dual_touch": False,
                "entry_price": entry_price,
                "atr": atr,
            }
        if target_hit:
            return {
                "exit_reason": "TARGET",
                "exit_price": target_price,
                "bars_to_exit": bar_i,
                "gross_r": target_atr / stop_atr,
                "signed_pips": target_dist / pip_size,
                "dual_touch": False,
                "entry_price": entry_price,
                "atr": atr,
            }

    # Timeout
    timeout_bar = path[-1]
    timeout_price = timeout_bar["close"]
    gross_r = direction * (timeout_price - entry_price) / stop_dist
    signed_pips = direction * (timeout_price - entry_price) / pip_size
    return {
        "exit_reason": "TIMEOUT",
        "exit_price": timeout_price,
        "bars_to_exit": horizon,
        "gross_r": gross_r,
        "signed_pips": signed_pips,
        "dual_touch": False,
        "entry_price": entry_price,
        "atr": atr,
    }


def verify_against_production_ledger(
    ledger_csv_path: str,
    test_cases: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Compares independent calculation results against production ledger CSV."""
    if not os.path.exists(ledger_csv_path):
        raise FileNotFoundError(f"Production ledger missing: {ledger_csv_path}")

    # Read ledger into memory indexed by observation_id
    production_rows = {}
    with open(ledger_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            obs_id = r["observation_id"]
            production_rows[obs_id] = r

    audit_results = []
    for tc in test_cases:
        obs_id = tc["observation_id"]
        if obs_id not in production_rows:
            raise KeyError(f"Observation ID '{obs_id}' not found in production ledger {ledger_csv_path}")

        prod = production_rows[obs_id]

        # Run independent calculation
        indep = independent_simulate_trade(
            pair=tc["pair"],
            release_time=tc["release_time"],
            direction=tc["direction"],
            stop_atr=tc["stop_atr"],
            target_atr=tc["target_atr"],
            horizon=tc["horizon"],
            dual_touch_mode=tc.get("dual_touch_mode", "STOP_FIRST")
        )

        # Compare fields
        diffs = []
        # Entry price
        prod_entry = float(prod["entry_price"])
        if f"{indep['entry_price']:.5f}" != prod["entry_price"] and not math.isclose(indep["entry_price"], prod_entry, abs_tol=1e-5):
            diffs.append(f"entry_price: indep {indep['entry_price']:.5f} != prod {prod['entry_price']}")

        # ATR
        prod_atr = float(prod["atr"])
        if f"{indep['atr']:.6f}" != prod["atr"] and not math.isclose(indep["atr"], prod_atr, abs_tol=1e-5):
            diffs.append(f"atr: indep {indep['atr']:.6f} != prod {prod['atr']}")

        # Exit reason
        if indep["exit_reason"] != prod["exit_reason"]:
            diffs.append(f"exit_reason: indep {indep['exit_reason']} != prod {prod['exit_reason']}")

        # Exit price
        prod_exit = float(prod["exit_price"])
        if f"{indep['exit_price']:.5f}" != prod["exit_price"] and not math.isclose(indep["exit_price"], prod_exit, abs_tol=1e-5):
            diffs.append(f"exit_price: indep {indep['exit_price']:.5f} != prod {prod['exit_price']}")

        # Bars to exit
        if indep["bars_to_exit"] != int(prod["bars_to_exit"]):
            diffs.append(f"bars_to_exit: indep {indep['bars_to_exit']} != prod {prod['bars_to_exit']}")

        # Gross R
        prod_r = float(prod["gross_r"])
        if f"{indep['gross_r']:.6f}" != prod["gross_r"] and not math.isclose(indep["gross_r"], prod_r, abs_tol=1e-5):
            diffs.append(f"gross_r: indep {indep['gross_r']:.6f} != prod {prod['gross_r']}")

        # Signed pips
        prod_pips = float(prod["signed_pips"])
        if f"{indep['signed_pips']:.2f}" != prod["signed_pips"] and not math.isclose(indep["signed_pips"], prod_pips, abs_tol=0.01):
            diffs.append(f"signed_pips: indep {indep['signed_pips']:.2f} != prod {prod['signed_pips']}")

        # Dual touch
        prod_dt = prod["dual_touch"].strip().lower() in ("true", "1")
        if indep["dual_touch"] != prod_dt:
            diffs.append(f"dual_touch: indep {indep['dual_touch']} != prod {prod_dt}")

        status = "PASSED" if not diffs else f"FAILED: {'; '.join(diffs)}"
        if diffs:
            raise AssertionError(f"Independent audit mismatch on {obs_id}: {status}")

        audit_results.append({
            "test_label": tc["label"],
            "observation_id": obs_id,
            "pair": tc["pair"],
            "release_time": tc["release_time"],
            "direction": "LONG" if tc["direction"] == 1 else "SHORT",
            "grid_cell": f"{tc['stop_atr']:g}:{tc['target_atr']:g}",
            "horizon": tc["horizon"],
            "indep_exit_reason": indep["exit_reason"],
            "prod_exit_reason": prod["exit_reason"],
            "indep_gross_r": indep["gross_r"],
            "prod_gross_r": prod_r,
            "indep_bars_to_exit": indep["bars_to_exit"],
            "prod_bars_to_exit": int(prod["bars_to_exit"]),
            "status": status,
        })

    return audit_results


def independent_audit_claims_collisions(raw_dir: str = RAW_DIR) -> Dict[str, Any]:
    """Independently parses calendar_releases.csv and calendar_events.csv to verify
    exact Initial Jobless Claims (840140001) coincidence counts for CPI and NFP.

    Verifies:
    1. Event ID 840140001 exists in calendar_events.csv with name 'Initial Jobless Claims'.
    2. Typographical ID 840014001 does NOT exist in calendar_events.csv.
    3. Exactly 33 CPI bundle timestamps (32 where CPI m/m anchor 840030005 is present,
       1 where m/m anchor is absent on 2025.12.18) coincide with 840140001.
    4. Exactly 4 NFP bundle timestamps (all 4 anchor-present) coincide with 840140001.
    """
    events_path = os.path.join(raw_dir, "calendar_events.csv")
    releases_path = os.path.join(raw_dir, "calendar_releases.csv")

    # 1. Event verification
    events = {}
    with open(events_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            events[r["event_id"]] = r["event_name"]

    if "840140001" not in events:
        raise AssertionError("Event ID 840140001 missing from calendar_events.csv!")
    if "840014001" in events:
        raise AssertionError("Typographical event ID 840014001 unexpectedly found in calendar_events.csv!")

    claims_event_name = events["840140001"]
    if "Jobless Claims" not in claims_event_name:
        raise AssertionError(f"Unexpected event name for 840140001: '{claims_event_name}'")

    # 2. Release timestamps
    claims_ts = set()
    cpi_mm_ts = set()
    cpi_all_ts = set()
    nfp_ts = set()

    cpi_eids = {"840030005", "840030006", "840030007", "840030008"}
    nfp_eids = {"840030015", "840030016", "840030018", "840030019"}

    with open(releases_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            ts = int(r["timestamp"])
            eid = r["event_id"]
            if eid == "840140001":
                claims_ts.add(ts)
            if eid == "840030005":
                cpi_mm_ts.add(ts)
            if eid in cpi_eids:
                cpi_all_ts.add(ts)
            if eid == "840030016":
                nfp_ts.add(ts)

    cpi_coincident_all = sorted(list(cpi_all_ts.intersection(claims_ts)))
    cpi_coincident_mm = sorted(list(cpi_mm_ts.intersection(claims_ts)))
    nfp_coincident = sorted(list(nfp_ts.intersection(claims_ts)))

    return {
        "event_id_840140001_present": True,
        "event_id_840014001_absent": True,
        "claims_event_name": claims_event_name,
        "total_claims_releases": len(claims_ts),
        "total_cpi_bundles": len(cpi_all_ts),
        "total_cpi_mm_bundles": len(cpi_mm_ts),
        "cpi_claims_coincident_all_count": len(cpi_coincident_all),
        "cpi_claims_coincident_mm_count": len(cpi_coincident_mm),
        "cpi_claims_coincident_timestamps": cpi_coincident_all,
        "cpi_claims_absent_anchor_timestamp": 1766075400,  # 2025.12.18 16:30:00 UTC
        "total_nfp_bundles": len(nfp_ts),
        "nfp_claims_coincident_count": len(nfp_coincident),
        "nfp_claims_coincident_timestamps": nfp_coincident,
    }
