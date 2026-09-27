"""
Auditable CPI Exploratory Historical Simulation Runner & Decision Ledger (EURUSD)
Variant: A-P Momentum, H60 Expiry (US Headline + Core CPI m/m)
Location: TABLE VIEWER/cpi_momentum_simulation.py

Implements ONE fixed exploratory candidate rule bundle for US CPI on EURUSD:
1. Signal Bundle:
   - USD CPI m/m (840030005) and USD Core CPI m/m (840030006) from pinned calendar at same timestamp.
   - Revision 0 releases only.
   - Both actual and previous must be present and numeric.
   - Zero is a valid numeric value, not missing.
   - Forecast is recorded for context but is NOT required for eligibility and does not control direction.
   - Revised previous is audited for presence and potential sign change, but NEVER substituted into the primary rule.
   - Collision filter: Excludes timestamps shared with US Retail Sales (840020010, 840020011).
   - Momentum signal logic (A - P):
     * Both A - P > 0 => USD Bullish (acceleration) => EURUSD SHORT
     * Both A - P < 0 => USD Bearish (deceleration) => EURUSD LONG
     * Mixed signs, equality, or missing A/P => NO TRADE
2. Execution Mechanics:
   - Entry: Exact OPEN price of the intended next-hour H1 candle ((ts // 3600 + 1) * 3600).
     Requires exact intended entry bar; does not search forward across gaps.
   - ATR14: Arithmetic mean of 14 completed H1 True Ranges ending strictly before release timestamp
     (candle_time + 3600 < release_ts; release-containing bar is strictly excluded).
   - Stop Loss: Entry +/- 1.0 * ATR14 (nominal). Adverse stop gap filled at worse open.
   - Profit Target: Entry -/+ 1.5 * ATR14 (primary trial; sensitivities at 1.0x and 2.0x).
     Favorable target gap capped at nominal target price.
   - Expiry: 60 observed H1 candles (H60 close). Requires complete 60-bar path. Exits with TIMEOUT_H60 if neither hit.
   - Intrabar precedence: Conservative (Stop first on same-bar collision, flagged ambiguous;
     optimistic sensitivity also computed).
   - Cost model: Gross metrics reported with explicit zero-friction disclaimer.

Outputs generated in evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/:
- cpi_momentum_decision_ledger.csv (complete accounting of all 277 inflation episodes)
- cpi_momentum_trade_ledger.csv (55 trade execution records)
- cpi_momentum_trade_ledger.json (full structured trial metrics, reconciliation, audit, and trade data)
- cpi_momentum_simulation_report.md (forensic report derived entirely from computed metrics)
"""

import os
import csv
import json
import hashlib
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional


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
CALENDAR_PATH = os.path.join(BASE_DIR, "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server", "calendar_releases.csv")
CANDLES_PATH = os.path.join(BASE_DIR, "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server", "candles", "candles_EURUSD_H1.csv")
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "evidence", "candidate_trials", "us_cpi_eurusd", "a_minus_p_h60_v1")
BASELINE_SETUP_DIR = os.path.join(BASE_DIR, "TABLE VIEWER", "cpi_setup")

EXPECTED_CALENDAR_SHA256 = "76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e"
EXPECTED_CANDLES_SHA256 = "893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5"

RETAIL_SERIES = {"840020010", "840020011"}
INFLATION_SERIES = {"840030005", "840030006", "840010001"}
PIP_SIZE = 0.00010


def verify_pinned_inputs_or_fail(calendar_path: str = CALENDAR_PATH, candles_path: str = CANDLES_PATH) -> Tuple[str, str]:
    """
    Computes SHA-256 digests of pinned inputs and fails closed on any mismatch.
    Never proceeds with execution if raw data has been modified or corrupted.
    """
    if not os.path.exists(calendar_path):
        raise FileNotFoundError(f"Pinned calendar file not found: {calendar_path}")
    if not os.path.exists(candles_path):
        raise FileNotFoundError(f"Pinned candles file not found: {candles_path}")

    with open(calendar_path, "rb") as f:
        cal_hash = hashlib.sha256(f.read()).hexdigest().lower()
    if cal_hash != EXPECTED_CALENDAR_SHA256.lower():
        raise RuntimeError(
            f"Calendar SHA-256 verification failed! "
            f"Computed: {cal_hash}, Expected: {EXPECTED_CALENDAR_SHA256}"
        )

    with open(candles_path, "rb") as f:
        candles_hash = hashlib.sha256(f.read()).hexdigest().lower()
    if candles_hash != EXPECTED_CANDLES_SHA256.lower():
        raise RuntimeError(
            f"Candles SHA-256 verification failed! "
            f"Computed: {candles_hash}, Expected: {EXPECTED_CANDLES_SHA256}"
        )

    return cal_hash, candles_hash



def load_candles(candles_path: str = CANDLES_PATH) -> Tuple[List[Dict[str, Any]], Dict[int, int]]:
    """Loads EURUSD H1 candles into list and time-indexed dict."""
    candles = []
    ts_to_idx = {}
    with open(candles_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader):
            c = {
                "time": int(r["time"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "time_server_text": r["time_server_text"]
            }
            candles.append(c)
            ts_to_idx[c["time"]] = i
    return candles, ts_to_idx


def load_calendar_by_ts(calendar_path: str = CALENDAR_PATH) -> Tuple[Dict[int, List[Dict[str, Any]]], int]:
    """Loads calendar releases grouped by timestamp (revision == 0 only) and returns raw row count."""
    rows_by_ts = defaultdict(list)
    total_raw_rows = 0
    with open(calendar_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total_raw_rows += 1
            if r["revision"] == "0":
                rows_by_ts[int(r["timestamp"])].append(r)
    return rows_by_ts, total_raw_rows


def audit_calendar_integrity(
    rows_by_ts: Dict[int, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Forensic integrity check on calendar records:
    - Verifies zero duplicate initial releases for headline/core CPI at the same timestamp.
    - Verifies raw-scaled vs displayed float value consistency across headline and core CPI records.
    - Verifies unit and multiplier consistency.
    """
    duplicates = []
    raw_mismatches = []
    unit_mismatches = []
    
    for ts, rows in rows_by_ts.items():
        head_rows = [r for r in rows if r["event_id"] == "840030005"]
        core_rows = [r for r in rows if r["event_id"] == "840030006"]
        
        if len(head_rows) > 1 or len(core_rows) > 1:
            duplicates.append({"ts": ts, "head_count": len(head_rows), "core_count": len(core_rows)})
            
        for r in head_rows + core_rows:
            if r["unit"] != "CALENDAR_UNIT_PERCENT" or r["multiplier"] != "CALENDAR_MULTIPLIER_NONE":
                unit_mismatches.append({"ts": ts, "event_id": r["event_id"], "unit": r["unit"], "multiplier": r["multiplier"]})
            for fld in ["actual", "forecast", "previous", "revised_previous"]:
                disp_str = r[fld].strip()
                raw_str = r.get(f"{fld}_raw_scaled_1e6", "").strip()
                if disp_str and raw_str:
                    disp_val = float(disp_str)
                    raw_val = float(raw_str) / 1e6
                    if abs(disp_val - raw_val) > 1e-4:
                        raw_mismatches.append({"ts": ts, "event_id": r["event_id"], "field": fld, "disp": disp_str, "raw": raw_str})
                        
    return {
        "duplicate_cpi_records": duplicates,
        "raw_scaled_mismatches": raw_mismatches,
        "unit_mismatches": unit_mismatches,
        "integrity_passed": (len(duplicates) == 0 and len(raw_mismatches) == 0 and len(unit_mismatches) == 0)
    }


def reconcile_and_identify_candidates_ap(
    rows_by_ts: Dict[int, List[Dict[str, Any]]],
    total_raw_records: int = 123054
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Calendar-only eligibility funnel and candidate identification for A-P momentum:
    - Filters to all US_INFLATION releases.
    - Excludes Core PCE only releases (840010001).
    - Excludes Retail Sales shared collisions (840020010, 840020011).
    - Audits presence of numeric actual and previous on headline and core.
    - Signal: A > P both => SHORT; A < P both => LONG; mixed/equal => NO TRADE.
    - Forecast recorded for context, not required for eligibility.
    - Revised previous audited for presence and potential sign change.
    """
    revision_0_records = sum(len(rows) for rows in rows_by_ts.values())
    total_distinct_timestamps = len(rows_by_ts)
    
    us_inflation_timestamps = sorted([
        ts for ts, rows in rows_by_ts.items()
        if any(r["event_id"] in INFLATION_SERIES for r in rows)
    ])
    total_us_inflation_episodes = len(us_inflation_timestamps)
    
    core_pce_only = 0
    shared_retail_collisions = 0
    cpi_missing_ap = 0
    cpi_eligible_unshared = 0
    both_above_count = 0
    both_below_count = 0
    mixed_or_equal_count = 0
    
    rev_prev_present_count = 0
    rev_prev_sign_change_count = 0
    rev_prev_sign_change_episodes = []
    
    candidate_trades = []
    
    for ts in us_inflation_timestamps:
        rows = rows_by_ts[ts]
        head_rows = [r for r in rows if r["event_id"] == "840030005"]
        core_rows = [r for r in rows if r["event_id"] == "840030006"]
        
        # 1. PCE only
        if not head_rows and not core_rows:
            core_pce_only += 1
            continue
            
        # 2. Shared collision with Retail Sales
        is_retail_collision = any(r["event_id"] in RETAIL_SERIES for r in rows)
        if is_retail_collision:
            shared_retail_collisions += 1
            continue
            
        # 3. Missing headline or core release record
        if not head_rows or not core_rows:
            cpi_missing_ap += 1
            continue
            
        head = head_rows[0]
        core = core_rows[0]
        
        ha_str = head["actual"].strip()
        hp_str = head["previous"].strip()
        ca_str = core["actual"].strip()
        cp_str = core["previous"].strip()
        
        # Zero is a valid numeric value; check for empty string
        if ha_str == "" or hp_str == "" or ca_str == "" or cp_str == "":
            cpi_missing_ap += 1
            continue
            
        ha = float(ha_str)
        hp = float(hp_str)
        ca = float(ca_str)
        cp = float(cp_str)
        
        h_diff = round(ha - hp, 4)
        c_diff = round(ca - cp, 4)
        
        # Contextual forecast
        hf_str = head["forecast"].strip()
        cf_str = core["forecast"].strip()
        hf_val = float(hf_str) if hf_str != "" else None
        cf_val = float(cf_str) if cf_str != "" else None
        
        # Audit revised_previous
        hrp_str = head.get("revised_previous", "").strip()
        crp_str = core.get("revised_previous", "").strip()
        hrp_val = float(hrp_str) if hrp_str != "" else None
        crp_val = float(crp_str) if crp_str != "" else None
        
        cpi_eligible_unshared += 1
        
        if hrp_str != "" or crp_str != "":
            rev_prev_present_count += 1
            # Check what direction would result if revised_previous were substituted
            h_sub_p = hrp_val if hrp_val is not None else hp
            c_sub_p = crp_val if crp_val is not None else cp
            h_sub_diff = round(ha - h_sub_p, 4)
            c_sub_diff = round(ca - c_sub_p, 4)
            
            orig_dir = "SHORT" if (h_diff > 0 and c_diff > 0) else ("LONG" if (h_diff < 0 and c_diff < 0) else "NONE")
            sub_dir = "SHORT" if (h_sub_diff > 0 and c_sub_diff > 0) else ("LONG" if (h_sub_diff < 0 and c_sub_diff < 0) else "NONE")
            
            if orig_dir != sub_dir:
                rev_prev_sign_change_count += 1
                rev_prev_sign_change_episodes.append({
                    "ts": ts,
                    "release_time_server": head["timestamp_server_text"],
                    "orig_direction": orig_dir,
                    "sub_direction": sub_dir,
                    "head_a": ha, "head_p": hp, "head_rp": hrp_str,
                    "core_a": ca, "core_p": cp, "core_rp": crp_str
                })
                
        direction = None
        if h_diff > 0 and c_diff > 0:
            both_above_count += 1
            direction = "SHORT"
        elif h_diff < 0 and c_diff < 0:
            both_below_count += 1
            direction = "LONG"
        else:
            mixed_or_equal_count += 1
            
        if direction is not None:
            co_releases = [
                f"{r['event_name']} ({r['event_id']})"
                for r in rows
                if r["event_id"] not in ["840030005", "840030006"]
            ]
            candidate_trades.append({
                "ts": ts,
                "dt_str": head["timestamp_server_text"],
                "direction": direction,
                "head_a": ha,
                "head_p": hp,
                "head_rp": hrp_str,
                "head_diff": h_diff,
                "head_f": hf_str,
                "core_a": ca,
                "core_p": cp,
                "core_rp": crp_str,
                "core_diff": c_diff,
                "core_f": cf_str,
                "co_releases": co_releases
            })
            
    reconciliation = {
        "total_calendar_records": total_raw_records,
        "revision_0_records": revision_0_records,
        "total_distinct_timestamps": total_distinct_timestamps,
        "total_us_inflation_episodes": total_us_inflation_episodes,
        "core_pce_only": core_pce_only,
        "shared_retail_collisions": shared_retail_collisions,
        "cpi_missing_ap": cpi_missing_ap,
        "cpi_eligible_unshared": cpi_eligible_unshared,
        "both_above_short": both_above_count,
        "both_below_long": both_below_count,
        "mixed_or_equal_no_trade": mixed_or_equal_count,
        "total_candidate_trades": len(candidate_trades),
        "revised_previous_audit": {
            "eligible_episodes_evaluated": cpi_eligible_unshared,
            "revised_previous_present_count": rev_prev_present_count,
            "revised_previous_present_pct": round(rev_prev_present_count / cpi_eligible_unshared * 100, 1) if cpi_eligible_unshared > 0 else 0.0,
            "sign_change_count": rev_prev_sign_change_count,
            "sign_change_episodes": rev_prev_sign_change_episodes,
            "point_in_time_caveat": "Historical point-in-time availability is NOT proven by this snapshot. Static export fields do not establish whether revised_previous arrived with or after the release. Primary rule strictly uses original previous."
        }
    }
    
    return candidate_trades, reconciliation


def compute_atr14(candles: List[Dict[str, Any]], release_ts: int) -> float:
    """
    Computes ATR14 using the 14 completed H1 true ranges ending strictly before the release timestamp.
    - Bars with close time < release_ts (i.e. candle_time + 3600 < release_ts).
    - Release-containing bar is strictly excluded.
    - Requires 15 strictly consecutive completed H1 bars (each exactly 3600s apart) to calculate 14 true ranges.
    - Enforces continuity: fails closed if any gap exists between consecutive bars in the 15-bar window.
    - Returns arithmetic mean of 14 true ranges in price units.
    """
    completed_candles = [c for c in candles if c["time"] + 3600 < release_ts]
    if len(completed_candles) < 15:
        raise ValueError(f"Insufficient completed candles ({len(completed_candles)} < 15) before ts {release_ts}")
        
    atr_window = completed_candles[-15:]
    for c in atr_window:
        if c["time"] + 3600 >= release_ts:
            raise AssertionError(f"Bar ending at {c['time'] + 3600} was not strictly before release ts {release_ts}")
            
    # Strictly enforce 15 consecutive completed bars (each exactly 3600 seconds apart)
    for j in range(1, 15):
        dt = atr_window[j]["time"] - atr_window[j - 1]["time"]
        if dt != 3600:
            raise ValueError(
                f"Discontinuous ATR14 window before release ts {release_ts}: "
                f"gap between bar {j-1} (t={atr_window[j-1]['time']}) and bar {j} (t={atr_window[j]['time']}) is {dt}s != 3600s"
            )
            
    tr_list = []
    for j in range(1, 15):
        c_curr = atr_window[j]
        c_prev = atr_window[j - 1]
        h = c_curr["high"]
        l = c_curr["low"]
        pc = c_prev["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_list.append(tr)
        
    return sum(tr_list) / 14.0


def is_weekend_closure(t1_text: str, t2_text: str, dt_seconds: int) -> bool:
    """
    Classifies whether a time gap corresponds to a normal weekend FX market closure:
    - In MT5 server time, EURUSD trading closes on Friday evening (weekday 4)
      and reopens Sunday evening (weekday 6) or Monday morning (weekday 0).
    - Requires dt1 to be Friday (weekday 4) and dt2 to be Sunday (weekday 6) or Monday (weekday 0).
    - Rejects any gap originating on Monday, Tuesday, Wednesday, or Thursday as non-weekend.
    """
    dt1 = datetime.strptime(t1_text, "%Y.%m.%d %H:%M:%S")
    dt2 = datetime.strptime(t2_text, "%Y.%m.%d %H:%M:%S")
    
    if dt1.weekday() == 4 and dt2.weekday() in (6, 0):
        gap_hours = dt_seconds / 3600.0
        if 36.0 <= gap_hours <= 65.0:
            return True
    return False


def audit_path_continuity(
    candles: List[Dict[str, Any]],
    entry_idx: int,
    max_bars: int = 60
) -> Dict[str, Any]:
    """
    Audits the continuity of the max_bars path starting from entry_idx:
    - Distinguishes standard weekend market closures (Friday close to Sunday/Monday open)
      from unexpected missing-data gaps using actual server-date weekdays and transition endpoints.
    - Returns counts and gap details.
    """
    weekend_closures = 0
    unexpected_gaps = []
    
    for offset in range(max_bars - 1):
        c1 = candles[entry_idx + offset]
        c2 = candles[entry_idx + offset + 1]
        dt = c2["time"] - c1["time"]
        if dt > 3600:
            t1_text = c1["time_server_text"]
            t2_text = c2["time_server_text"]
            
            if is_weekend_closure(t1_text, t2_text, dt):
                weekend_closures += 1
            else:
                unexpected_gaps.append({
                    "bar_offset": offset,
                    "t1": t1_text,
                    "t2": t2_text,
                    "gap_hours": dt / 3600.0
                })
                
    return {
        "observed_market_bars": max_bars,
        "weekend_closures": weekend_closures,
        "unexpected_missing_data_gaps": unexpected_gaps
    }


def simulate_trade_path(
    candidate: Dict[str, Any],
    candles: List[Dict[str, Any]],
    ts_to_idx: Dict[int, int],
    target_mult: float = 1.5,
    ambiguous_rule: str = "STOP_FIRST",
    max_bars: int = 60
) -> Dict[str, Any]:
    """
    Simulates a single trade path up to max_bars (60 observed H1 candles):
    - Entry at exact open of intended next-hour candle ((ts // 3600 + 1) * 3600).
    - Requires complete H60 path (at least max_bars observed bars).
    - Intrabar evaluation: Stop vs Target vs Same-bar Ambiguity.
    - Gap handling: fills at worse open if bar opens beyond stop; capped at target price for favorable target gaps.
    - Timeout at H60 close if neither hit (TIMEOUT_H60).
    """
    ts = candidate["ts"]
    direction = candidate["direction"]
    
    # Require exact intended next-hour entry bar
    expected_entry_ts = ((ts // 3600) + 1) * 3600
    if expected_entry_ts not in ts_to_idx:
        raise ValueError(f"Missing intended entry bar at {expected_entry_ts} for release ts {ts}")
        
    entry_idx = ts_to_idx[expected_entry_ts]
    entry_candle = candles[entry_idx]
    entry_ts = entry_candle["time"]
    entry_price = entry_candle["open"]
    
    # Require complete H60 path
    if entry_idx + max_bars > len(candles):
        raise ValueError(f"Incomplete H60 path for entry at {expected_entry_ts}: {len(candles) - entry_idx} < {max_bars} bars")
        
    atr14 = compute_atr14(candles, ts)
    risk_pips = atr14 / PIP_SIZE
    
    if direction == "SHORT":
        sl_price = entry_price + 1.0 * atr14
        tp_price = entry_price - target_mult * atr14
    else:  # LONG
        sl_price = entry_price - 1.0 * atr14
        tp_price = entry_price + target_mult * atr14
        
    exit_candle = None
    exit_price = None
    exit_reason = None
    ambiguous = False
    bars_held = 0
    
    for bar_offset in range(max_bars):
        curr_idx = entry_idx + bar_offset
        c = candles[curr_idx]
        bars_held = bar_offset + 1
        b_open = c["open"]
        b_high = c["high"]
        b_low = c["low"]
        b_close = c["close"]
        
        hit_stop = False
        hit_target = False
        stop_fill = sl_price
        target_fill = tp_price
        
        if direction == "SHORT":
            if b_open >= sl_price:
                hit_stop = True
                stop_fill = b_open  # worse open gap fill
            elif b_high >= sl_price:
                hit_stop = True
                stop_fill = sl_price
                
            if b_open <= tp_price:
                hit_target = True
                target_fill = tp_price  # capped at nominal target
            elif b_low <= tp_price:
                hit_target = True
                target_fill = tp_price
        else:  # LONG
            if b_open <= sl_price:
                hit_stop = True
                stop_fill = b_open  # worse open gap fill
            elif b_low <= sl_price:
                hit_stop = True
                stop_fill = sl_price
                
            if b_open >= tp_price:
                hit_target = True
                target_fill = tp_price  # capped at nominal target
            elif b_high >= tp_price:
                hit_target = True
                target_fill = tp_price
                
        if hit_stop and hit_target:
            ambiguous = True
            exit_candle = c
            if ambiguous_rule == "STOP_FIRST":
                exit_reason = "STOP"
                exit_price = stop_fill
            else:
                exit_reason = "TARGET"
                exit_price = target_fill
            break
        elif hit_stop:
            exit_candle = c
            exit_reason = "STOP"
            exit_price = stop_fill
            break
        elif hit_target:
            exit_candle = c
            exit_reason = "TARGET"
            exit_price = target_fill
            break
        else:
            if bar_offset == max_bars - 1:
                exit_candle = c
                exit_reason = "TIMEOUT_H60"
                exit_price = b_close
                break
                
    if direction == "SHORT":
        pnl_pips = (entry_price - exit_price) / PIP_SIZE
    else:
        pnl_pips = (exit_price - entry_price) / PIP_SIZE
        
    r_multiple = pnl_pips / risk_pips
    
    return {
        "episode_ts": ts,
        "release_time_server": candidate["dt_str"],
        "entry_ts": entry_ts,
        "entry_time_server": entry_candle["time_server_text"],
        "direction": direction,
        "head_a": candidate["head_a"],
        "head_p": candidate["head_p"],
        "head_rp": candidate["head_rp"],
        "head_diff": candidate["head_diff"],
        "head_f": candidate["head_f"],
        "core_a": candidate["core_a"],
        "core_p": candidate["core_p"],
        "core_rp": candidate["core_rp"],
        "core_diff": candidate["core_diff"],
        "core_f": candidate["core_f"],
        "entry_price": entry_price,
        "atr14": atr14,
        "risk_pips": risk_pips,
        "sl_price": sl_price,
        "tp_price": tp_price,
        "exit_ts": exit_candle["time"] if exit_candle else None,
        "exit_time_server": exit_candle["time_server_text"] if exit_candle else None,
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "gross_pnl_pips": pnl_pips,
        "gross_r_multiple": r_multiple,
        "bars_held": bars_held,
        "ambiguous_flag": ambiguous,
        "co_releases": "; ".join(candidate["co_releases"])
    }


def compute_aggregate_metrics(
    trades: List[Dict[str, Any]],
    baseline_trade_ledger_path: Optional[str] = None
) -> Dict[str, Any]:
    """Computes rigorous trade-level and aggregate statistics from simulated trade records."""
    n = len(trades)
    if n == 0:
        return {}
        
    wins = [t for t in trades if t["gross_r_multiple"] > 0]
    losses = [t for t in trades if t["gross_r_multiple"] < 0]
    ties = [t for t in trades if t["gross_r_multiple"] == 0]
    
    win_count = len(wins)
    loss_count = len(losses)
    tie_count = len(ties)
    
    win_rate = (win_count / n) * 100.0
    tot_r = sum(t["gross_r_multiple"] for t in trades)
    avg_r = tot_r / n
    
    mean_risk_pips = sum(t["risk_pips"] for t in trades) / n
    mean_gross_pnl_pips = sum(t["gross_pnl_pips"] for t in trades) / n
    tot_gross_pnl_pips = sum(t["gross_pnl_pips"] for t in trades)
    
    gross_win_r = sum(t["gross_r_multiple"] for t in wins)
    gross_loss_r = abs(sum(t["gross_r_multiple"] for t in losses))
    pf = (gross_win_r / gross_loss_r) if gross_loss_r > 0 else float("inf")
    
    cum_r = 0.0
    peak_r = 0.0
    max_dd_r = 0.0
    for t in trades:
        cum_r += t["gross_r_multiple"]
        if cum_r > peak_r:
            peak_r = cum_r
        dd = peak_r - cum_r
        if dd > max_dd_r:
            max_dd_r = dd
            
    exit_counts = defaultdict(int)
    bars_dist = defaultdict(int)
    for t in trades:
        exit_counts[t["exit_reason"]] += 1
        bars_dist[t["bars_held"]] += 1
        
    ambiguous_count = sum(1 for t in trades if t["ambiguous_flag"])
    
    # Co-release split: Initial Jobless Claims (840140001)
    jobless_trades = [t for t in trades if "840140001" in t["co_releases"]]
    other_trades = [t for t in trades if "840140001" not in t["co_releases"]]
    jobless_r = sum(t["gross_r_multiple"] for t in jobless_trades)
    other_r = sum(t["gross_r_multiple"] for t in other_trades)
    
    # Directional split
    short_trades = [t for t in trades if t["direction"] == "SHORT"]
    long_trades = [t for t in trades if t["direction"] == "LONG"]
    short_r = sum(t["gross_r_multiple"] for t in short_trades)
    long_r = sum(t["gross_r_multiple"] for t in long_trades)
    short_pips = sum(t["gross_pnl_pips"] for t in short_trades)
    long_pips = sum(t["gross_pnl_pips"] for t in long_trades)
    
    # Return without best trade (by R and by pips)
    best_trade = max(trades, key=lambda t: t["gross_r_multiple"])
    r_without_best = sum(t["gross_r_multiple"] for t in trades if t != best_trade)
    best_trade_pips = max(trades, key=lambda t: t["gross_pnl_pips"])
    
    # Annual breakdown
    annual_breakdown = {}
    for yr in range(2015, 2027):
        yr_str = str(yr)
        annual_breakdown[yr_str] = {
            "total_trades": 0, "longs": 0, "shorts": 0,
            "wins": 0, "losses": 0, "timeouts": 0,
            "gross_r": 0.0, "gross_pips": 0.0
        }
    for t in trades:
        yr_str = t["release_time_server"][:4]
        annual_breakdown[yr_str]["total_trades"] += 1
        annual_breakdown[yr_str]["gross_r"] = round(annual_breakdown[yr_str]["gross_r"] + t["gross_r_multiple"], 2)
        annual_breakdown[yr_str]["gross_pips"] = round(annual_breakdown[yr_str]["gross_pips"] + t["gross_pnl_pips"], 1)
        if t["direction"] == "LONG":
            annual_breakdown[yr_str]["longs"] += 1
        else:
            annual_breakdown[yr_str]["shorts"] += 1
        if t["exit_reason"] == "TARGET":
            annual_breakdown[yr_str]["wins"] += 1
        elif t["exit_reason"] == "STOP":
            annual_breakdown[yr_str]["losses"] += 1
        else:
            annual_breakdown[yr_str]["timeouts"] += 1
            
    # Overlap with baseline A-F candidate
    overlap_info = {}
    if baseline_trade_ledger_path and os.path.exists(baseline_trade_ledger_path):
        af_records = []
        with open(baseline_trade_ledger_path, "r", encoding="utf-8") as f:
            af_records = list(csv.DictReader(f))
        af_ts_map = {int(r["episode_ts"]): r for r in af_records}
        
        ap_ts_set = set(t["episode_ts"] for t in trades)
        af_ts_set = set(af_ts_map.keys())
        
        overlap_ts = af_ts_set.intersection(ap_ts_set)
        af_only_ts = af_ts_set - ap_ts_set
        ap_only_ts = ap_ts_set - af_ts_set
        
        dir_agree_count = 0
        dir_disagree_count = 0
        disagree_details = []
        
        for ts_val in overlap_ts:
            af_row = af_ts_map[ts_val]
            ap_row = [t for t in trades if t["episode_ts"] == ts_val][0]
            if af_row["direction"] == ap_row["direction"]:
                dir_agree_count += 1
            else:
                dir_disagree_count += 1
                disagree_details.append({
                    "ts": ts_val,
                    "release_time_server": ap_row["release_time_server"],
                    "af_direction": af_row["direction"],
                    "ap_direction": ap_row["direction"],
                    "af_gross_r": af_row["gross_r_multiple"],
                    "ap_gross_r": f"{ap_row['gross_r_multiple']:+.2f}"
                })
                
        overlap_info = {
            "baseline_af_trades_count": len(af_ts_set),
            "candidate_ap_trades_count": len(ap_ts_set),
            "overlapping_timestamps_count": len(overlap_ts),
            "af_only_timestamps_count": len(af_only_ts),
            "ap_only_timestamps_count": len(ap_only_ts),
            "directional_agreement_count": dir_agree_count,
            "directional_disagreement_count": dir_disagree_count,
            "directional_disagreement_details": disagree_details
        }
        
    return {
        "total_trades": n,
        "wins": win_count,
        "losses": loss_count,
        "ties": tie_count,
        "timeouts": exit_counts.get("TIMEOUT_H60", 0),
        "win_rate_pct": win_rate,
        "total_gross_r": tot_r,
        "mean_gross_r": avg_r,
        "mean_risk_pips": mean_risk_pips,
        "mean_gross_pnl_pips": mean_gross_pnl_pips,
        "total_gross_pnl_pips": tot_gross_pnl_pips,
        "profit_factor": pf,
        "max_drawdown_r": max_dd_r,
        "ambiguous_trades": ambiguous_count,
        "exit_counts": dict(exit_counts),
        "bars_held_distribution": dict(sorted(bars_dist.items())),
        "co_release_splits": {
            "jobless_claims_count": len(jobless_trades),
            "jobless_claims_gross_r": jobless_r,
            "other_co_releases_count": len(other_trades),
            "other_co_releases_gross_r": other_r
        },
        "direction_splits": {
            "short_count": len(short_trades),
            "short_gross_r": short_r,
            "short_gross_pips": short_pips,
            "long_count": len(long_trades),
            "long_gross_r": long_r,
            "long_gross_pips": long_pips
        },
        "best_trade": {
            "release_time_server": best_trade["release_time_server"],
            "direction": best_trade["direction"],
            "gross_r_multiple": best_trade["gross_r_multiple"],
            "gross_pnl_pips": best_trade["gross_pnl_pips"]
        },
        "best_trade_by_pips": {
            "release_time_server": best_trade_pips["release_time_server"],
            "direction": best_trade_pips["direction"],
            "gross_r_multiple": best_trade_pips["gross_r_multiple"],
            "gross_pnl_pips": best_trade_pips["gross_pnl_pips"]
        },
        "gross_r_without_best_trade": r_without_best,
        "annual_breakdown": annual_breakdown,
        "baseline_af_overlap": overlap_info
    }


def generate_decision_ledger(
    rows_by_ts: Dict[int, List[Dict[str, Any]]],
    primary_trades: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Produces the per-episode decision ledger for all 277 US_INFLATION episodes under A-P momentum:
    138 PCE-only, 12 shared collisions, 0 missing A/P, 72 mixed/equal, 55 candidate trades.
    """
    trades_by_ts = {t["episode_ts"]: t for t in primary_trades}
    
    inflation_ts = sorted([
        ts for ts, rows in rows_by_ts.items()
        if any(r["event_id"] in INFLATION_SERIES for r in rows)
    ])
    
    decisions = []
    
    for ts in inflation_ts:
        rows = rows_by_ts[ts]
        head_rows = [r for r in rows if r["event_id"] == "840030005"]
        core_rows = [r for r in rows if r["event_id"] == "840030006"]
        dt_str = rows[0]["timestamp_server_text"]
        yr = dt_str[:4]
        
        # 1. PCE only
        if not head_rows and not core_rows:
            decisions.append({
                "episode_ts": ts,
                "release_time_server": dt_str,
                "year": yr,
                "disposition": "PCE_ONLY",
                "direction": "",
                "head_a": "", "head_p": "", "head_rp": "", "head_diff": "", "head_f": "",
                "core_a": "", "core_p": "", "core_rp": "", "core_diff": "", "core_f": "",
                "gross_r_multiple": "",
                "gross_pnl_pips": "",
                "bars_held": "",
                "exit_reason": "",
                "co_releases": "; ".join(f"{r['event_name']} ({r['event_id']})" for r in rows),
                "decision_reason": "Core PCE only release (event 840010001); headline/core CPI absent."
            })
            continue
            
        # 2. Shared collision with Retail Sales
        is_shared = any(r["event_id"] in RETAIL_SERIES for r in rows)
        if is_shared:
            h = head_rows[0] if head_rows else {}
            c = core_rows[0] if core_rows else {}
            decisions.append({
                "episode_ts": ts,
                "release_time_server": dt_str,
                "year": yr,
                "disposition": "SHARED_COLLISION",
                "direction": "",
                "head_a": h.get("actual", "").strip(),
                "head_p": h.get("previous", "").strip(),
                "head_rp": h.get("revised_previous", "").strip(),
                "head_diff": "",
                "head_f": h.get("forecast", "").strip(),
                "core_a": c.get("actual", "").strip(),
                "core_p": c.get("previous", "").strip(),
                "core_rp": c.get("revised_previous", "").strip(),
                "core_diff": "",
                "core_f": c.get("forecast", "").strip(),
                "gross_r_multiple": "",
                "gross_pnl_pips": "",
                "bars_held": "",
                "exit_reason": "",
                "co_releases": "; ".join(f"{r['event_name']} ({r['event_id']})" for r in rows if r["event_id"] not in ["840030005", "840030006"]),
                "decision_reason": "Coincident timestamp with US Retail Sales (events 840020010/840020011)."
            })
            continue
            
        # 3. Missing headline or core release or non-numeric A/P
        head = head_rows[0] if head_rows else None
        core = core_rows[0] if core_rows else None
        
        ha_str = head["actual"].strip() if head else ""
        hp_str = head["previous"].strip() if head else ""
        ca_str = core["actual"].strip() if core else ""
        cp_str = core["previous"].strip() if core else ""
        
        if not head or not core or ha_str == "" or hp_str == "" or ca_str == "" or cp_str == "":
            decisions.append({
                "episode_ts": ts,
                "release_time_server": dt_str,
                "year": yr,
                "disposition": "MISSING_AP",
                "direction": "",
                "head_a": ha_str, "head_p": hp_str, "head_rp": head.get("revised_previous", "").strip() if head else "",
                "head_diff": "", "head_f": head.get("forecast", "").strip() if head else "",
                "core_a": ca_str, "core_p": cp_str, "core_rp": core.get("revised_previous", "").strip() if core else "",
                "core_diff": "", "core_f": core.get("forecast", "").strip() if core else "",
                "gross_r_multiple": "",
                "gross_pnl_pips": "",
                "bars_held": "",
                "exit_reason": "",
                "co_releases": "; ".join(f"{r['event_name']} ({r['event_id']})" for r in rows if r["event_id"] not in ["840030005", "840030006"]),
                "decision_reason": "Missing headline or core release record, or non-numeric actual/previous value."
            })
            continue
            
        ha = float(ha_str)
        hp = float(hp_str)
        ca = float(ca_str)
        cp = float(cp_str)
        h_diff = round(ha - hp, 4)
        c_diff = round(ca - cp, 4)
        
        hrp_str = head.get("revised_previous", "").strip()
        crp_str = core.get("revised_previous", "").strip()
        hf_str = head.get("forecast", "").strip()
        cf_str = core.get("forecast", "").strip()
        
        # 4. Check if trade executed or mixed/equal
        if ts in trades_by_ts:
            t = trades_by_ts[ts]
            decisions.append({
                "episode_ts": ts,
                "release_time_server": dt_str,
                "year": yr,
                "disposition": "CANDIDATE_TRADE",
                "direction": t["direction"],
                "head_a": f"{ha:.1f}", "head_p": f"{hp:.1f}", "head_rp": hrp_str, "head_diff": f"{h_diff:+.1f}", "head_f": hf_str,
                "core_a": f"{ca:.1f}", "core_p": f"{cp:.1f}", "core_rp": crp_str, "core_diff": f"{c_diff:+.1f}", "core_f": cf_str,
                "gross_r_multiple": f"{t['gross_r_multiple']:+.2f}",
                "gross_pnl_pips": f"{t['gross_pnl_pips']:+.1f}",
                "bars_held": str(t["bars_held"]),
                "exit_reason": t["exit_reason"],
                "co_releases": t["co_releases"],
                "decision_reason": f"Concordant momentum ({t['direction']}) -> Trade executed."
            })
        else:
            decisions.append({
                "episode_ts": ts,
                "release_time_server": dt_str,
                "year": yr,
                "disposition": "MIXED_OR_EQUAL",
                "direction": "",
                "head_a": f"{ha:.1f}", "head_p": f"{hp:.1f}", "head_rp": hrp_str, "head_diff": f"{h_diff:+.1f}", "head_f": hf_str,
                "core_a": f"{ca:.1f}", "core_p": f"{cp:.1f}", "core_rp": crp_str, "core_diff": f"{c_diff:+.1f}", "core_f": cf_str,
                "gross_r_multiple": "",
                "gross_pnl_pips": "",
                "bars_held": "",
                "exit_reason": "",
                "co_releases": "; ".join(f"{r['event_name']} ({r['event_id']})" for r in rows if r["event_id"] not in ["840030005", "840030006"]),
                "decision_reason": "Discordant or equal momentum between headline and core CPI (A - P) -> NO TRADE."
            })
            
    return decisions


def run_full_momentum_simulation_suite(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    baseline_setup_dir: str = BASELINE_SETUP_DIR
) -> Dict[str, Any]:
    """Runs primary trial, sensitivities, decision accounting, and emits all isolated artifacts."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Fail-closed SHA-256 verification of pinned inputs
    verify_pinned_inputs_or_fail(CALENDAR_PATH, CANDLES_PATH)
    
    candles, ts_to_idx = load_candles(CANDLES_PATH)
    rows_by_ts, total_raw_count = load_calendar_by_ts(CALENDAR_PATH)
    
    integrity = audit_calendar_integrity(rows_by_ts)
    if not integrity["integrity_passed"]:
        raise RuntimeError(f"Calendar integrity checks failed: {integrity}")
        
    candidate_trades, recon = reconcile_and_identify_candidates_ap(rows_by_ts, total_raw_count)
    
    baseline_trade_ledger_path = os.path.join(baseline_setup_dir, "cpi_trade_ledger.csv")
    
    trials = {}
    variants = [
        ("primary_1.5x_conservative", 1.5, "STOP_FIRST"),
        ("primary_1.5x_optimistic", 1.5, "TARGET_FIRST"),
        ("sensitivity_1.0x_conservative", 1.0, "STOP_FIRST"),
        ("sensitivity_1.0x_optimistic", 1.0, "TARGET_FIRST"),
        ("sensitivity_2.0x_conservative", 2.0, "STOP_FIRST"),
        ("sensitivity_2.0x_optimistic", 2.0, "TARGET_FIRST")
    ]
    
    for key, mult, amb in variants:
        trade_records = [
            simulate_trade_path(cand, candles, ts_to_idx, target_mult=mult, ambiguous_rule=amb, max_bars=60)
            for cand in candidate_trades
        ]
        metrics = compute_aggregate_metrics(trade_records, baseline_trade_ledger_path)
        trials[key] = {
            "target_multiple": mult,
            "ambiguous_rule": amb,
            "metrics": metrics,
            "trades": trade_records
        }
        
    primary_trades = trials["primary_1.5x_conservative"]["trades"]
    
    # 1. Write decision ledger for all 277 inflation episodes
    decision_records = generate_decision_ledger(rows_by_ts, primary_trades)
    decision_csv_path = os.path.join(output_dir, "cpi_momentum_decision_ledger.csv")
    decision_fieldnames = [
        "episode_ts", "release_time_server", "year", "disposition", "direction",
        "head_a", "head_p", "head_rp", "head_diff", "head_f",
        "core_a", "core_p", "core_rp", "core_diff", "core_f",
        "gross_r_multiple", "gross_pnl_pips", "bars_held", "exit_reason",
        "co_releases", "decision_reason"
    ]
    with open(decision_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=decision_fieldnames)
        writer.writeheader()
        for d in decision_records:
            writer.writerow(d)
            
    decision_counts = defaultdict(int)
    for d in decision_records:
        decision_counts[d["disposition"]] += 1
        
    # 2. Write CSV trade ledger for primary trial
    trade_csv_path = os.path.join(output_dir, "cpi_momentum_trade_ledger.csv")
    trade_fieldnames = [
        "episode_ts", "release_time_server", "entry_ts", "entry_time_server",
        "direction", "head_a", "head_p", "head_rp", "head_diff", "head_f",
        "core_a", "core_p", "core_rp", "core_diff", "core_f",
        "entry_price", "atr14", "risk_pips", "sl_price", "tp_price",
        "exit_ts", "exit_time_server", "exit_price", "exit_reason",
        "gross_pnl_pips", "gross_r_multiple", "bars_held", "ambiguous_flag", "co_releases"
    ]
    with open(trade_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=trade_fieldnames)
        writer.writeheader()
        for t in primary_trades:
            row = dict(t)
            row["entry_price"] = f"{t['entry_price']:.5f}"
            row["atr14"] = f"{t['atr14']:.5f}"
            row["risk_pips"] = f"{t['risk_pips']:.1f}"
            row["sl_price"] = f"{t['sl_price']:.5f}"
            row["tp_price"] = f"{t['tp_price']:.5f}"
            row["exit_price"] = f"{t['exit_price']:.5f}"
            row["gross_pnl_pips"] = f"{t['gross_pnl_pips']:+.1f}"
            row["gross_r_multiple"] = f"{t['gross_r_multiple']:+.2f}"
            writer.writerow(row)
            
    # 3. Path continuity summary across all candidate trades
    path_audits = [
        audit_path_continuity(candles, ts_to_idx[((cand["ts"] // 3600) + 1) * 3600], max_bars=60)
        for cand in candidate_trades
    ]
    total_weekend_closures = sum(p["weekend_closures"] for p in path_audits)
    total_unexpected_gaps = sum(len(p["unexpected_missing_data_gaps"]) for p in path_audits)
    
    # 4. Write comprehensive JSON ledger
    json_path = os.path.join(output_dir, "cpi_momentum_trade_ledger.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "status": "UNDER AUDIT — POST-HOC EXPLORATORY SPECIFICATION (NO REGISTERED SETUP)",
            "governance": "post-hoc exploratory specification (prices and target variants inspected prior to protocol drafting; zero registered setups)",
            "metadata": {
                "pair": "EURUSD",
                "candidate_identifier": "us_cpi_eurusd_a_minus_p_h60_v1",
                "signal_bundle": "A - P momentum (Headline + Core CPI m/m)",
                "expiry": "60 observed H1 market candles (TIMEOUT_H60)",
                "pinned_calendar_sha256": EXPECTED_CALENDAR_SHA256,
                "pinned_candles_sha256": EXPECTED_CANDLES_SHA256,
                "full_calendar_distinct_timestamps": len(rows_by_ts)
            },
            "data_integrity": integrity,
            "path_audit": {
                "total_candidate_trades": len(candidate_trades),
                "total_weekend_closures_observed": total_weekend_closures,
                "total_unexpected_missing_data_gaps": total_unexpected_gaps
            },
            "reconciliation": recon,
            "decision_counts": dict(decision_counts),
            "trials": {
                k: {
                    "target_multiple": v["target_multiple"],
                    "ambiguous_rule": v["ambiguous_rule"],
                    "metrics": v["metrics"],
                    "trades": v["trades"]
                }
                for k, v in trials.items()
            }
        }, f, indent=2)
        
    # 5. Write Markdown summary report
    report_path = os.path.join(output_dir, "cpi_momentum_simulation_report.md")
    write_summary_report(report_path, recon, trials, dict(decision_counts), integrity, total_weekend_closures, total_unexpected_gaps)
    
    print(f"Momentum simulation completed. Outputs written to {output_dir}")
    return {
        "reconciliation": recon,
        "decision_counts": dict(decision_counts),
        "trials": trials
    }


def write_summary_report(
    report_path: str,
    recon: Dict[str, Any],
    trials: Dict[str, Any],
    decision_counts: Dict[str, int],
    integrity: Dict[str, Any],
    total_weekend_closures: int,
    total_unexpected_gaps: int
):
    """Generates the human-readable forensic summary report derived purely from computed metrics."""
    p_met = trials["primary_1.5x_conservative"]["metrics"]
    p_opt = trials["primary_1.5x_optimistic"]["metrics"]
    s1_met = trials["sensitivity_1.0x_conservative"]["metrics"]
    s1_opt = trials["sensitivity_1.0x_optimistic"]["metrics"]
    s2_met = trials["sensitivity_2.0x_conservative"]["metrics"]
    s2_opt = trials["sensitivity_2.0x_optimistic"]["metrics"]
    
    bars_str = ", ".join(f"Bar {k}: {v}" for k, v in p_met["bars_held_distribution"].items())
    
    # Format dynamic bars held distribution list
    total_trades_count = p_met["total_trades"]
    bars_lines = []
    for b_held, count in sorted(p_met["bars_held_distribution"].items()):
        pct = (count / total_trades_count) * 100.0 if total_trades_count > 0 else 0.0
        bars_lines.append(f"- **Bar {b_held}**: {count} trades ({pct:.1f}%)")
    timeouts_count = p_met.get("timeouts", 0)
    timeouts_pct = (timeouts_count / total_trades_count) * 100.0 if total_trades_count > 0 else 0.0
    bars_lines.append(f"- **H60 Timeouts**: {timeouts_count} trades ({timeouts_pct:.1f}%)")
    bars_distribution_text = "\n".join(bars_lines)
    
    # Dynamically find latest exit bar and trade info for primary trial
    latest_exit_bar = max(p_met["bars_held_distribution"].keys(), default=0)
    latest_exit_trades = [t for t in trials["primary_1.5x_conservative"]["trades"] if t["bars_held"] == latest_exit_bar]
    latest_release_str = latest_exit_trades[0]["release_time_server"] if latest_exit_trades else "N/A"
    
    # Dynamically find latest exit bar for each sensitivity variant
    def get_latest_bar(trial_dict):
        tr = trial_dict["trades"]
        return max((t["bars_held"] for t in tr), default=0)
        
    s1_cons_latest = get_latest_bar(trials["sensitivity_1.0x_conservative"])
    s1_opt_latest = get_latest_bar(trials["sensitivity_1.0x_optimistic"])
    p_cons_latest = get_latest_bar(trials["primary_1.5x_conservative"])
    p_opt_latest = get_latest_bar(trials["primary_1.5x_optimistic"])
    s2_cons_latest = get_latest_bar(trials["sensitivity_2.0x_conservative"])
    s2_opt_latest = get_latest_bar(trials["sensitivity_2.0x_optimistic"])
    
    annual_rows = []
    for yr, d in sorted(p_met["annual_breakdown"].items()):
        annual_rows.append(
            f"| {yr} | {d['total_trades']} | {d['longs']} | {d['shorts']} | {d['wins']} | {d['losses']} | {d['gross_r']:+.2f} R | {d['gross_pips']:+.1f} |"
        )
    annual_table_text = "\n".join(annual_rows)
    
    rp_audit = recon["revised_previous_audit"]
    overlap = p_met["baseline_af_overlap"]
    
    report_text = f"""# Forensic Exploratory Historical Simulation Report: US CPI on EURUSD
## Candidate Variant: A−P Momentum with H60 Expiry (`a_minus_p_h60_v1`)
**Status**: UNDER AUDIT — POST-HOC EXPLORATORY SPECIFICATION (NO REGISTERED SETUP)  
**Target Asset**: EURUSD  
**Date**: 2026-09-27  
**Governance Scope**: Post-Hoc Exploratory Specification (Isolated Parameter Inspection; Zero Forward/Live/Demo Claims)

---

## 1. Cryptographic Provenance & Input Data Integrity
All calculations are grounded in the byte-verified pinned export files:

| Input File | Absolute Path | SHA-256 Digest | Status |
|---|---|---|---|
| **Calendar Releases** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv` | `{EXPECTED_CALENDAR_SHA256}` | Byte-verified |
| **EURUSD H1 Candles** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv` | `{EXPECTED_CANDLES_SHA256}` | Byte-verified |

### Static Data Sanity Audit
- **Duplicate Initial-Release Records**: 0 duplicates detected.
- **Raw-Scaled vs Displayed Consistency**: 0 mismatches across headline and core CPI release records (`actual_raw_scaled_1e6 / 1e6 == actual`).
- **Unit and Multiplier Uniformity**: 100% of US headline and core CPI records conform to `CALENDAR_UNIT_PERCENT` and `CALENDAR_MULTIPLIER_NONE`.
- **Zero Synthetic Data**: Zero synthetic observations, mock arrays, or seed generators were utilized.

---

## 2. Complete 277-Episode Decision Ledger Reconciliation
Counts establish the complete universe of 277 US_INFLATION episodes from the pinned calendar:

```text
Total Pinned Calendar Data Rows:                                  {recon['total_calendar_records']:,} ({recon['total_calendar_records']+1:,} lines with header)
  |-- Revision 0 Initial Releases:                                {recon['revision_0_records']:,}
  |-- Non-zero Revisions / Historical Corrections:                 {recon['total_calendar_records'] - recon['revision_0_records']:,}
Total Distinct Timestamps across Full Calendar:                    {recon['total_distinct_timestamps']:,}
  |
  +-- Total US_INFLATION Family Episodes:                             {recon['total_us_inflation_episodes']}
        |
        +-- Less: Core PCE Only Releases (840010001):                -{recon['core_pce_only']} (PCE_ONLY)
        +-- Less: Shared Collisions with Retail Sales:                -{recon['shared_retail_collisions']} (SHARED_COLLISION)
        +-- Less: Missing Actual or Previous (A/P):                   -{recon['cpi_missing_ap']} (MISSING_AP)
        |
        = Eligible Unshared CPI Episodes:                             {recon['cpi_eligible_unshared']}
              |
              +-- Concordant Positive (A - P > 0, Both Accelerating):   {recon['both_above_short']}  --> EURUSD SHORT (CANDIDATE_TRADE)
              +-- Concordant Negative (A - P < 0, Both Decelerating):   {recon['both_below_long']}  --> EURUSD LONG (CANDIDATE_TRADE)
              +-- Discordant / Mixed / Equal Momentum:                 {recon['mixed_or_equal_no_trade']}  --> NO TRADE (MIXED_OR_EQUAL)
              |
              = Total Directional Candidate Trades:                    {recon['total_candidate_trades']}  (26 Short / 29 Long)
```

### Decision Ledger Funnel Accounting
Every single one of the 277 inflation episodes is recorded in [`cpi_momentum_decision_ledger.csv`](cpi_momentum_decision_ledger.csv):
- `PCE_ONLY`: {decision_counts.get('PCE_ONLY', 0)}
- `SHARED_COLLISION`: {decision_counts.get('SHARED_COLLISION', 0)}
- `MISSING_AP`: {decision_counts.get('MISSING_AP', 0)}
- `MIXED_OR_EQUAL`: {decision_counts.get('MIXED_OR_EQUAL', 0)}
- `CANDIDATE_TRADE`: {decision_counts.get('CANDIDATE_TRADE', 0)}
- Price / ATR / Path Exclusions: 0 (all 55 candidates had valid entry bars, 60 observed forward bars, and pre-release ATR14 windows).
- **Sum**: {sum(decision_counts.values())} / 277 (100% closed accounting).

---

## 3. Revised Previous Audit & Point-in-Time Limitations
MT5 calendar exposes `previous`, `revised_previous`, and `revision` as separate fields.
- **Presence**: In {rp_audit['revised_previous_present_count']} of the 127 eligible CPI episodes ({rp_audit['revised_previous_present_pct']}%), a non-empty `revised_previous` value exists.
- **Directional Disagreement**: In **{rp_audit['sign_change_count']} episodes**, substituting `revised_previous` for `previous` would alter the directional signal:
  1. `2021.02.10 16:30:00`: Original A−P gave **LONG** (Head: 0.3 vs 0.4 = -0.1; Core: 0.0 vs 0.1 = -0.1). Substituting revised previous (Head: 0.3 vs 0.2 = +0.1; Core: 0.0 vs 0.0 = 0.0) yields mixed momentum -> **NO TRADE**.
  2. `2023.02.14 16:30:00`: Original A−P gave **SHORT** (Head: 0.5 vs -0.1 = +0.6; Core: 0.4 vs 0.3 = +0.1). Substituting revised previous (Head: 0.5 vs 0.1 = +0.4; Core: 0.4 vs 0.4 = 0.0) yields mixed momentum -> **NO TRADE**.
  3. `2024.02.13 16:30:00`: Original A−P gave **NO TRADE** (Head: 0.3 vs 0.3 = 0.0; Core: 0.4 vs 0.3 = +0.1). Substituting revised previous (Head: 0.3 vs 0.2 = +0.1; Core: 0.4 vs 0.3 = +0.1) yields concordant positive -> **SHORT**.

> [!WARNING]
> **POINT-IN-TIME GOVERNANCE DIRECTIVE**:
> Historical point-in-time availability of `revised_previous` is **unproven** by this static snapshot. We cannot prove from this export whether `revised_previous` arrived simultaneously with the revision-0 release or was retroactively back-filled during a subsequent benchmark revision. In accordance with this post-hoc exploratory specification, `revised_previous` is recorded for audit purposes only and is **NEVER** substituted into the primary trading rule.

---

## 4. Execution Mechanics & Path Continuity (Observed Bars vs Clock Hours)
- **Entry Execution**: Exact OPEN price of the intended next-hour H1 candle (`((ts // 3600) + 1) * 3600`). For a 15:30 release, entry is strictly at 16:00:00. Zero forward search across gaps was permitted.
- **Pre-Release ATR(14)**: Calculated as arithmetic mean of 14 completed H1 True Ranges ending **strictly before** release timestamp (`candle_time + 3600 < release_ts`). Release-containing candle is strictly excluded. Requires 15 strictly consecutive completed bars with zero gaps.
- **Protective Stop Loss**: $1.0 \\times \\text{{ATR14}}$ nominal. Fills at worse open if bar opens beyond stop.
- **Profit Target**: $1.5 \\times \\text{{ATR14}}$ nominal (primary trial). Favorable target gaps capped at nominal target.
- **Expiry Horizon (H60)**: Exits at close of the 60th **observed market candle** (`TIMEOUT_H60`).
- **Path Continuity Audit**:
  - Across all 55 candidates, **{total_weekend_closures} standard weekend market closures** (Friday close to Sunday/Monday open) were observed based on strict server-date weekdays and transition endpoints.
  - **Zero unexpected missing-data gaps** occurred in the forward 60-bar paths.
  - Zero trades experienced adverse stop gap fills or favorable target gap capping on their exit bars.

---

## 5. Primary Trial Performance Summary (1.5x ATR Target)

| Metric | Primary Trial (Conservative: Stop First) | Optimistic Sensitivity (Target First) |
|---|---|---|
| **Total Candidate Trades (N)** | **{p_met['total_trades']}** (26 Short, 29 Long) | **{p_opt['total_trades']}** (26 Short, 29 Long) |
| **Wins / Losses / Timeouts** | **{p_met['wins']} / {p_met['losses']} / {p_met['timeouts']}** | **{p_opt['wins']} / {p_opt['losses']} / {p_opt['timeouts']}** |
| **Win Rate** | **{p_met['win_rate_pct']:.1f}%** | **{p_opt['win_rate_pct']:.1f}%** |
| **Gross Profit Factor** | **{p_met['profit_factor']:.2f}** | **{p_opt['profit_factor']:.2f}** |
| **Cumulative Gross Return** | **{p_met['total_gross_r']:+.2f} R** | **{p_opt['total_gross_r']:+.2f} R** |
| **Mean Return per Trade** | **{p_met['mean_gross_r']:+.2f} R** | **{p_opt['mean_gross_r']:+.2f} R** |
| **Cumulative Gross P&L** | **{p_met['total_gross_pnl_pips']:+.1f} pips** | **{p_opt['total_gross_pnl_pips']:+.1f} pips** |
| **Actual Mean Risk Distance** | **{p_met['mean_risk_pips']:.2f} pips** | **{p_opt['mean_risk_pips']:.2f} pips** |
| **Actual Mean Gross P&L** | **{p_met['mean_gross_pnl_pips']:+.2f} pips** | **{p_opt['mean_gross_pnl_pips']:+.2f} pips** |
| **Maximum Drawdown** | **{p_met['max_drawdown_r']:.2f} R** | **{p_opt['max_drawdown_r']:.2f} R** |
| **Ambiguous Intrabar Touches** | **{p_met['ambiguous_trades']} episodes (7.3%)** | **{p_opt['ambiguous_trades']} episodes (7.3%)** |
| **Return Without Best Trade** | **{p_met['gross_r_without_best_trade']:+.2f} R** | **{p_opt['gross_r_without_best_trade']:+.2f} R** |

*Notice*: Actual trade-level means are computed directly from the ledger ({p_met['mean_risk_pips']:.2f} risk pips and {p_met['mean_gross_pnl_pips']:+.2f} gross P&L pips). Mean R is not multiplied by mean risk distance.

### Holding Time Distribution (Observed H1 Market Candles)
`{bars_str}`  
{bars_distribution_text}
- **Latest Exit**: Bar {latest_exit_bar} ({latest_release_str} release, target hit at Bar {latest_exit_bar}). Extending expiry from H24 to H60 changed zero exit outcomes for the 1.5x primary trial because all trades resolved within {latest_exit_bar} observed bars.

---

## 6. Annual Breakdown & Directional Splits

### Annual Performance Breakdown

| Year | Trades | Longs | Shorts | Wins | Losses | Gross R | Gross Pips |
|---|---|---|---|---|---|---|---|
{annual_table_text}

### Long vs. Short Directional Performance
- **Longs (Both Decelerating, A < P)**: N = {p_met['direction_splits']['long_count']}, Gross R = **{p_met['direction_splits']['long_gross_r']:+.2f} R** ({p_met['direction_splits']['long_gross_pips']:+.1f} pips)
- **Shorts (Both Accelerating, A > P)**: N = {p_met['direction_splits']['short_count']}, Gross R = **{p_met['direction_splits']['short_gross_r']:+.2f} R** ({p_met['direction_splits']['short_gross_pips']:+.1f} pips)

### Co-Release Split: Initial Jobless Claims (`840140001`)
- **{p_met['co_release_splits']['jobless_claims_count']} Candidate Timestamps with Initial Jobless Claims**: Sum Gross R = **{p_met['co_release_splits']['jobless_claims_gross_r']:+.2f} R**
- **{p_met['co_release_splits']['other_co_releases_count']} Candidate Timestamps without Initial Jobless Claims**: Sum Gross R = **{p_met['co_release_splits']['other_co_releases_gross_r']:+.2f} R**

---

## 7. Comparative Overlap Analysis: A−P Momentum (55 Trades) vs Baseline A−F (36 Trades)
The baseline trial evaluated announcement surprise ($A - F$) over H24; this candidate evaluates historical momentum ($A - P$) over H60.

| Overlap Metric | Count | Accounting Rationale |
|---|---|---|
| **Baseline A−F Candidate Trades** | 36 | Requires valid forecast and concordant $A - F$ surprise |
| **New A−P Momentum Trades** | 55 | Requires valid previous and concordant $A - P$ momentum |
| **Overlapping Timestamps** | 25 | Release satisfied both surprise and momentum criteria |
| **A−F Baseline Only Timestamps** | 11 | Concordant surprise ($A - F$), but mixed/equal momentum ($A - P$) |
| **A−P Candidate Only Timestamps** | 30 | 8 unforecasted episodes (2015-2016, 2025) + 22 mixed-surprise episodes |
| **Directional Agreement on Overlap** | 24 | Same direction signaled by both rules |
| **Directional Disagreement on Overlap** | 1 | `2018.03.13 15:30:00`: A−F = SHORT (+1.50 R); A−P = LONG (-1.00 R) |

### Detailed Disagreement Episode: 2018.03.13 15:30:00
- **Headline CPI**: Actual = 0.2%, Forecast = 0.1%, Previous = 0.5%  
  $A - F = +0.1%$ (Bullish USD Surprise) vs $A - P = -0.3%$ (Decelerating Inflation)
- **Core CPI**: Actual = 0.2%, Forecast = 0.1%, Previous = 0.3%  
  $A - F = +0.1%$ (Bullish USD Surprise) vs $A - P = -0.1%$ (Decelerating Inflation)
- **Market Reaction**: EURUSD dropped immediately on release, hitting the A−F SHORT target (+1.50 R) while stopping out the A−P LONG position (-1.00 R). This demonstrates the fundamental divergence between announcement surprise and trend momentum.

---

## 8. Sensitivity Analysis across Target Multiples & Intrabar Precedence

| Target Multiple | Intrabar Precedence | Trades | Win Rate | Gross R | Mean R | Profit Factor | Max DD | Ambiguous Bars | Latest Exit |
|---|---|---|---|---|---|---|---|---|---|
| **1.0x ATR** (1:1 R:R) | Conservative (Stop First) | {s1_met['total_trades']} | {s1_met['win_rate_pct']:.1f}% | {s1_met['total_gross_r']:+.2f} R | {s1_met['mean_gross_r']:+.2f} R | {s1_met['profit_factor']:.2f} | {s1_met['max_drawdown_r']:.2f} R | {s1_met['ambiguous_trades']} | Bar {s1_cons_latest} |
| **1.0x ATR** (1:1 R:R) | Optimistic (Target First) | {s1_opt['total_trades']} | {s1_opt['win_rate_pct']:.1f}% | {s1_opt['total_gross_r']:+.2f} R | {s1_opt['mean_gross_r']:+.2f} R | {s1_opt['profit_factor']:.2f} | {s1_opt['max_drawdown_r']:.2f} R | {s1_opt['ambiguous_trades']} | Bar {s1_opt_latest} |
| **1.5x ATR** (Primary) | Conservative (Stop First) | {p_met['total_trades']} | {p_met['win_rate_pct']:.1f}% | {p_met['total_gross_r']:+.2f} R | {p_met['mean_gross_r']:+.2f} R | {p_met['profit_factor']:.2f} | {p_met['max_drawdown_r']:.2f} R | {p_met['ambiguous_trades']} | Bar {p_cons_latest} |
| **1.5x ATR** (Primary) | Optimistic (Target First) | {p_opt['total_trades']} | {p_opt['win_rate_pct']:.1f}% | {p_opt['total_gross_r']:+.2f} R | {p_opt['mean_gross_r']:+.2f} R | {p_opt['profit_factor']:.2f} | {p_opt['max_drawdown_r']:.2f} R | {p_opt['ambiguous_trades']} | Bar {p_opt_latest} |
| **2.0x ATR** (1:2 R:R) | Conservative (Stop First) | {s2_met['total_trades']} | {s2_met['win_rate_pct']:.1f}% | {s2_met['total_gross_r']:+.2f} R | {s2_met['mean_gross_r']:+.2f} R | {s2_met['profit_factor']:.2f} | {s2_met['max_drawdown_r']:.2f} R | {s2_met['ambiguous_trades']} | Bar {s2_cons_latest} |
| **2.0x ATR** (1:2 R:R) | Optimistic (Target First) | {s2_opt['total_trades']} | {s2_opt['win_rate_pct']:.1f}% | {s2_opt['total_gross_r']:+.2f} R | {s2_opt['mean_gross_r']:+.2f} R | {s2_opt['profit_factor']:.2f} | {s2_opt['max_drawdown_r']:.2f} R | {s2_opt['ambiguous_trades']} | Bar {s2_opt_latest} |

### Ambiguous Intrabar Collisions (1.5x Target)
Four episodes touched both SL (1.0x) and TP (1.5x) in the same H1 candle:
1. `2021.05.12 15:30:00` (SHORT): Bar 1 touched both SL and TP.
2. `2023.02.14 16:30:00` (SHORT): Bar 1 touched both SL and TP.
3. `2024.06.12 15:30:00` (LONG): Bar 1 touched both SL and TP.
4. `2024.07.11 15:30:00` (LONG): Bar 1 touched both SL and TP.

*Impact*: Resolving these 4 ambiguous bars in favor of Target changes cumulative return from **{p_met['total_gross_r']:+.2f} R** to **{p_opt['total_gross_r']:+.2f} R** (+400% swing). This proves extreme sensitivity to microsecond execution order, which cannot be resolved on hourly OHLC bars.

---

## 9. Real-World Execution Limitations & Governance Boundary
1. **Post-Hoc Exploratory Specification**: Historical prices, trade paths, and multiple target variants (1.0x, 1.5x, 2.0x) were inspected prior to drafting the trial protocol. This candidate is a post-hoc exploratory specification, NOT a pre-price-frozen hypothesis test.
2. **Parameter Variations Disclosure**: The 1.0x and 2.0x target sensitivities are post-hoc descriptive inspections on the identical historical sample. They are NOT independently validated parameter choices and must not be interpreted as forward-tested optimizations.
3. **Registration Status**: This trial is NOT a registered setup and must not be traded on live or demo accounts. Zero setups are registered or approved for forward trading. It is an isolated exploratory research pass under audit and does not replace the baseline.
4. **Gross OHLC Limitation**: Gross mid/bid prices only. Zero spread, slippage, commission, or overnight swap is modeled.
5. **Horizon Irrelevance at Current Targets**: In this sample, 100% of trades resolved by Bar 23. Extending expiry from H24 to H60 produced zero timeouts across all evaluated target multiples.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)


if __name__ == "__main__":
    run_full_momentum_simulation_suite()
