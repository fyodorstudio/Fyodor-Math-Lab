"""
Price-Blind Reconciliation Engine for US ISM Manufacturing PMI (USD:US:840040001:r0)
Verifies calendar inventory, component relationships, S&P Global preceding releases,
co-release collisions, multi-component concordance, and EURUSD H1 candle path continuity.

STRICT CONSTRAINTS:
- Price-Blind: Only reads calendar fields and candle timestamps (column 0).
- Uses stream_candle_timestamps_only to genuinely read solely field-0 Unix timestamps.
- Zero access to or tokenization of Bid/Ask OHLC prices, tick volumes, or spreads.
- Strictly stops before the 2023 chronological boundary (timestamp < 1672531200).
- Validates every adjacent transition: exactly 1 hour or a valid weekend market closure.
- Enforces conservative holdout seal: exit at close of final bar must not exceed split boundary.
- Rejects arbitrary weekday gaps, duplicate/unsorted timestamps, and split boundary crossings.
- No silent default value substitutions for calendar metadata.
"""

import csv
import os
import sys
from typing import Dict, List, Set, Tuple, Optional, Any

from .parsers import stream_candle_timestamps_only, SPLIT_TIMESTAMP
from .candle_coverage import is_valid_weekend_market_closure, SECONDS_IN_H1

DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server"
)


def load_pre2023_releases(
    calendar_csv_path: str,
    split_timestamp: int = SPLIT_TIMESTAMP
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Load pre-2023 calendar releases, grouping by event_id.
    """
    all_releases: List[Dict[str, Any]] = []
    by_event: Dict[str, List[Dict[str, Any]]] = {}

    with open(calendar_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = int(row["timestamp"])
            if ts < split_timestamp:
                all_releases.append(row)
                eid = row["event_id"]
                if eid not in by_event:
                    by_event[eid] = []
                by_event[eid].append(row)

    return all_releases, by_event


def audit_ism_headline(
    by_event: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Audits US ISM Manufacturing PMI (840040001) headline inventory and surprises.
    """
    releases = by_event.get("840040001", [])
    releases.sort(key=lambda r: int(r["timestamp"]))

    total_releases = len(releases)
    complete_afp: List[Dict[str, Any]] = []
    incomplete: List[Dict[str, Any]] = []

    for r in releases:
        act = r["actual_raw_scaled_1e6"]
        fc = r["forecast_raw_scaled_1e6"]
        prev = r["previous_raw_scaled_1e6"]
        if act != "" and fc != "" and prev != "":
            complete_afp.append(r)
        else:
            incomplete.append(r)

    pos_surprises: List[Dict[str, Any]] = []
    neg_surprises: List[Dict[str, Any]] = []
    zero_surprises: List[Dict[str, Any]] = []

    for r in complete_afp:
        act_val = int(r["actual_raw_scaled_1e6"])
        fc_val = int(r["forecast_raw_scaled_1e6"])
        surp = act_val - fc_val
        if surp > 0:
            pos_surprises.append(r)
        elif surp < 0:
            neg_surprises.append(r)
        else:
            zero_surprises.append(r)

    actionable = pos_surprises + neg_surprises
    actionable_ts = set(int(r["timestamp"]) for r in actionable)
    complete_ts = set(int(r["timestamp"]) for r in complete_afp)

    return {
        "event_id": "840040001",
        "total_pre2023": total_releases,
        "complete_afp_count": len(complete_afp),
        "incomplete_count": len(incomplete),
        "positive_count": len(pos_surprises),
        "negative_count": len(neg_surprises),
        "zero_count": len(zero_surprises),
        "actionable_count": len(actionable),
        "complete_afp_releases": complete_afp,
        "actionable_timestamps": actionable_ts,
        "complete_timestamps": complete_ts,
        "zero_surprise_releases": zero_surprises,
    }


def audit_headline_prices_paid_matrix(
    by_event: Dict[str, List[Dict[str, Any]]],
    complete_afp: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Computes joint surprise matrix between Headline (840040001) and Prices Paid (840040002)
    using raw scaled integers (actual_raw_scaled_1e6 - forecast_raw_scaled_1e6).
    """
    pp_by_ts = {int(r["timestamp"]): r for r in by_event.get("840040002", [])}

    matrix = {
        "POS/POS": 0,
        "POS/NEG": 0,
        "POS/ZERO": 0,
        "NEG/POS": 0,
        "NEG/NEG": 0,
        "NEG/ZERO": 0,
        "ZERO/POS": 0,
        "ZERO/NEG": 0,
        "ZERO/ZERO": 0,
    }

    for r in complete_afp:
        ts = int(r["timestamp"])
        h_act = int(r["actual_raw_scaled_1e6"])
        h_fc = int(r["forecast_raw_scaled_1e6"])
        h_surp = h_act - h_fc

        pp = pp_by_ts.get(ts)
        if pp and pp["actual_raw_scaled_1e6"] != "" and pp["forecast_raw_scaled_1e6"] != "":
            p_act = int(pp["actual_raw_scaled_1e6"])
            p_fc = int(pp["forecast_raw_scaled_1e6"])
            p_surp = p_act - p_fc

            h_sign = "POS" if h_surp > 0 else ("NEG" if h_surp < 0 else "ZERO")
            p_sign = "POS" if p_surp > 0 else ("NEG" if p_surp < 0 else "ZERO")
            matrix[f"{h_sign}/{p_sign}"] += 1

    return matrix


def audit_multi_component_concordance(
    by_event: Dict[str, List[Dict[str, Any]]],
    ism_audit: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Reconciles multi-component surprise signs across Headline (840040001),
    Employment (840040004), New Orders (840040006), and Prices Paid (840040002).

    Requirements:
    - Complete A/F/P for each series included in the comparison.
    - Nonzero headline surprise (S_H != 0).
    """
    h_map = {int(r["timestamp"]): r for r in by_event.get("840040001", [])}
    pp_map = {int(r["timestamp"]): r for r in by_event.get("840040002", [])}
    emp_map = {int(r["timestamp"]): r for r in by_event.get("840040004", [])}
    no_map = {int(r["timestamp"]): r for r in by_event.get("840040006", [])}

    def is_afp(r: Optional[Dict[str, Any]]) -> bool:
        return (
            r is not None and
            r.get("actual_raw_scaled_1e6") not in (None, "") and
            r.get("forecast_raw_scaled_1e6") not in (None, "") and
            r.get("previous_raw_scaled_1e6") not in (None, "")
        )

    def get_surp(r: Dict[str, Any]) -> int:
        return int(r["actual_raw_scaled_1e6"]) - int(r["forecast_raw_scaled_1e6"])

    actionable_ts = ism_audit.get("actionable_timestamps", set())

    # 1. Headline + Employment + New Orders
    hen_packages: List[int] = []
    hen_pos: List[int] = []
    hen_neg: List[int] = []
    hen_opposite: List[int] = []
    hen_neutral: List[int] = []
    for ts in sorted(actionable_ts):
        h, e, n = h_map.get(ts), emp_map.get(ts), no_map.get(ts)
        if is_afp(h) and is_afp(e) and is_afp(n):
            hs, es, ns = get_surp(h), get_surp(e), get_surp(n)
            is_pos = (hs > 0 and es > 0 and ns > 0)
            is_neg = (hs < 0 and es < 0 and ns < 0)
            hen_packages.append(ts)
            if is_pos:
                hen_pos.append(ts)
            elif is_neg:
                hen_neg.append(ts)
            elif (es == 0 or ns == 0):
                hen_neutral.append(ts)
            else:
                hen_opposite.append(ts)

    # 2. Headline + Prices Paid + Employment
    hpe_packages: List[int] = []
    hpe_pos: List[int] = []
    hpe_neg: List[int] = []
    hpe_opposite: List[int] = []
    hpe_neutral: List[int] = []
    for ts in sorted(actionable_ts):
        h, p, e = h_map.get(ts), pp_map.get(ts), emp_map.get(ts)
        if is_afp(h) and is_afp(p) and is_afp(e):
            hs, ps, es = get_surp(h), get_surp(p), get_surp(e)
            is_pos = (hs > 0 and ps > 0 and es > 0)
            is_neg = (hs < 0 and ps < 0 and es < 0)
            hpe_packages.append(ts)
            if is_pos:
                hpe_pos.append(ts)
            elif is_neg:
                hpe_neg.append(ts)
            elif (ps == 0 or es == 0):
                hpe_neutral.append(ts)
            else:
                hpe_opposite.append(ts)

    # 3. All Four Components (Headline + Prices Paid + Employment + New Orders)
    c4_packages: List[int] = []
    c4_pos: List[int] = []
    c4_neg: List[int] = []
    c4_opposite: List[int] = []
    c4_neutral: List[int] = []
    for ts in sorted(actionable_ts):
        h, p, e, n = h_map.get(ts), pp_map.get(ts), emp_map.get(ts), no_map.get(ts)
        if is_afp(h) and is_afp(p) and is_afp(e) and is_afp(n):
            hs, ps, es, ns = get_surp(h), get_surp(p), get_surp(e), get_surp(n)
            is_pos = (hs > 0 and ps > 0 and es > 0 and ns > 0)
            is_neg = (hs < 0 and ps < 0 and es < 0 and ns < 0)
            c4_packages.append(ts)
            if is_pos:
                c4_pos.append(ts)
            elif is_neg:
                c4_neg.append(ts)
            elif (ps == 0 or es == 0 or ns == 0):
                c4_neutral.append(ts)
            else:
                c4_opposite.append(ts)

    return {
        "headline_emp_neworders": {
            "complete_packages": len(hen_packages),
            "concordant_total": len(hen_pos) + len(hen_neg),
            "concordant_positive": len(hen_pos),
            "concordant_negative": len(hen_neg),
            "discordant_total": len(hen_opposite) + len(hen_neutral),
            "opposite_sign_total": len(hen_opposite),
            "neutral_component_total": len(hen_neutral),
        },
        "headline_prices_paid_emp": {
            "complete_packages": len(hpe_packages),
            "concordant_total": len(hpe_pos) + len(hpe_neg),
            "concordant_positive": len(hpe_pos),
            "concordant_negative": len(hpe_neg),
            "discordant_total": len(hpe_opposite) + len(hpe_neutral),
            "opposite_sign_total": len(hpe_opposite),
            "neutral_component_total": len(hpe_neutral),
        },
        "all_four_components": {
            "complete_packages": len(c4_packages),
            "concordant_total": len(c4_pos) + len(c4_neg),
            "concordant_positive": len(c4_pos),
            "concordant_negative": len(c4_neg),
            "discordant_total": len(c4_opposite) + len(c4_neutral),
            "opposite_sign_total": len(c4_opposite),
            "neutral_component_total": len(c4_neutral),
        },
    }


def audit_sp_global(
    by_event: Dict[str, List[Dict[str, Any]]],
    ism_releases: List[Dict[str, Any]],
    actionable_ts: Set[int]
) -> Dict[str, Any]:
    """
    Audits preceding S&P Global (840500001) releases for both revision 1 and revision 3.
    Checks timing lead (exact 900 seconds prior) and forecast availability.
    """
    sp_all = by_event.get("840500001", [])
    sp_rev1 = [r for r in sp_all if r["revision"] == "1"]
    sp_rev3 = [r for r in sp_all if r["revision"] == "3"]

    sp_rev1_with_fc = [r for r in sp_rev1 if r["forecast_raw_scaled_1e6"] != ""]
    sp_rev3_with_fc = [r for r in sp_rev3 if r["forecast_raw_scaled_1e6"] != ""]

    sp_rev3_by_ts = {int(r["timestamp"]): r for r in sp_rev3}

    rev3_exact_900s_all = 0
    rev3_exact_900s_with_fc_all = 0
    rev3_exact_900s_actionable = 0
    rev3_exact_900s_with_fc_actionable = 0
    dates_not_900s: List[Dict[str, Any]] = []

    for r in ism_releases:
        ts = int(r["timestamp"])
        target_sp_ts = ts - 900
        is_act = ts in actionable_ts

        if target_sp_ts in sp_rev3_by_ts:
            rev3_exact_900s_all += 1
            has_fc = (sp_rev3_by_ts[target_sp_ts]["forecast_raw_scaled_1e6"] != "")
            if has_fc:
                rev3_exact_900s_with_fc_all += 1
            if is_act:
                rev3_exact_900s_actionable += 1
                if has_fc:
                    rev3_exact_900s_with_fc_actionable += 1
        else:
            dates_not_900s.append({
                "ism_timestamp": ts,
                "ism_date_text": r.get("timestamp_server_text", "")
            })

    return {
        "rev1_total": len(sp_rev1),
        "rev1_forecasts_populated": len(sp_rev1_with_fc),
        "rev3_total": len(sp_rev3),
        "rev3_forecasts_populated": len(sp_rev3_with_fc),
        "rev3_exact_900s_all": rev3_exact_900s_all,
        "rev3_exact_900s_with_fc_all": rev3_exact_900s_with_fc_all,
        "rev3_exact_900s_actionable": rev3_exact_900s_actionable,
        "rev3_exact_900s_with_fc_actionable": rev3_exact_900s_with_fc_actionable,
        "dates_not_900s": dates_not_900s,
    }


def audit_construction_spending(
    by_event: Dict[str, List[Dict[str, Any]]],
    ism_releases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Audits Construction Spending (840020002) co-release with ISM.
    """
    cs_rows = by_event.get("840020002", [])
    cs_by_ts = {int(r["timestamp"]): r for r in cs_rows}

    co_releases = sum(1 for r in ism_releases if int(r["timestamp"]) in cs_by_ts)

    return {
        "event_id": "840020002",
        "event_name": "Construction Spending m/m",
        "total_pre2023": len(cs_rows),
        "co_releases_with_ism": co_releases,
        "total_ism_releases": len(ism_releases),
    }


def audit_foreign_currency_collisions(
    all_releases: List[Dict[str, Any]],
    ism_releases: List[Dict[str, Any]],
    actionable_ts: Set[int]
) -> List[Dict[str, Any]]:
    """
    Finds non-USD releases at the identical timestamp as ISM releases.
    """
    ism_ts_set = set(int(r["timestamp"]) for r in ism_releases)
    collisions: List[Dict[str, Any]] = []

    for r in all_releases:
        ts = int(r["timestamp"])
        if ts in ism_ts_set and r["currency"] != "USD":
            collisions.append({
                "timestamp": ts,
                "timestamp_server_text": r.get("timestamp_server_text", ""),
                "currency": r["currency"],
                "event_id": r["event_id"],
                "event_name": r.get("event_name", ""),
                "is_actionable": ts in actionable_ts
            })

    # Sort by timestamp
    collisions.sort(key=lambda c: c["timestamp"])
    return collisions


def audit_calendar_metadata(events_csv_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Audits calendar metadata definitions from calendar_events.csv.
    Strictly forbids silent default value substitutions for missing fields.
    """
    target_ids = {"840040001", "840040002", "840040004", "840040006", "840020002", "840030005", "840500001"}
    required_fields = ["sector", "sector_code", "unit", "unit_code", "importance", "importance_code"]
    metadata: Dict[str, Dict[str, Any]] = {}

    with open(events_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = row.get("event_id")
            if eid in target_ids:
                # Check for missing or empty required fields
                for field in required_fields:
                    val = row.get(field)
                    if val is None or val == "":
                        raise ValueError(f"Event {eid}: Missing or empty required metadata field '{field}'")

                try:
                    sec_code = int(row["sector_code"])
                    u_code = int(row["unit_code"])
                    imp_code = int(row["importance_code"])
                except ValueError as e:
                    raise ValueError(f"Event {eid}: Non-integer code in metadata: {e}")

                metadata[eid] = {
                    "event_id": eid,
                    "event_name": row.get("event_name", ""),
                    "event_code": row.get("event_code", ""),
                    "sector": row["sector"],
                    "sector_code": sec_code,
                    "unit": row["unit"],
                    "unit_code": u_code,
                    "importance": row["importance"],
                    "importance_code": imp_code,
                }

    return metadata


def validate_h1_path_transitions(
    path_bars: List[int],
    split_timestamp: int = SPLIT_TIMESTAMP
) -> Tuple[bool, bool, str]:
    """
    Validates every adjacent H1 path transition in a proposed bar sequence.
    Returns (is_valid, crosses_weekend, failure_reason).

    Requirements:
    1. Every bar must open strictly before split_timestamp.
    2. Timestamps must be strictly monotonic (no duplicates, no unsorted pairs).
    3. Every transition must be:
       - Exactly 3600 seconds (1 active trading hour), OR
       - A legitimate weekend market closure verified by is_valid_weekend_market_closure.
    4. Arbitrary weekday gaps are rejected.
    5. Split-boundary convention for exit at close of final H1 bar:
       An active H1 bar that opens at path_bars[-1] spans [path_bars[-1], path_bars[-1] + 3600).
       Its close timestamp is exit_close_ts = path_bars[-1] + SECONDS_IN_H1.
       Under the conservative holdout seal, the exit execution must not extend beyond split_timestamp
       (exit_close_ts <= split_timestamp). If exit_close_ts > split_timestamp, the trade's holding
       period extends into the post-2022 holdout.
    """
    if not path_bars:
        return False, False, "Empty path bars"

    crosses_weekend = False

    for i in range(len(path_bars)):
        ts = path_bars[i]
        if ts >= split_timestamp:
            return False, False, f"Bar at index {i} (timestamp {ts}) is at or beyond split {split_timestamp}"

    # Split-boundary convention for exit at the close of the final H1 bar
    exit_close_ts = path_bars[-1] + SECONDS_IN_H1
    if exit_close_ts > split_timestamp:
        return False, False, f"Exit close timestamp {exit_close_ts} extends beyond split boundary {split_timestamp}"

    for i in range(len(path_bars) - 1):
        t1, t2 = path_bars[i], path_bars[i + 1]

        if t2 <= t1:
            return False, False, f"Duplicate or unsorted timestamps at index {i}: t1={t1}, t2={t2}"

        diff = t2 - t1
        if diff == SECONDS_IN_H1:
            continue

        # Non-3600 gap: validate as legitimate weekend closure
        is_weekend, reason = is_valid_weekend_market_closure(t1, t2)
        if not is_weekend:
            # Also test t1 + 3600 in case gap_start_ts was defined as the first missing bar
            is_weekend2, reason2 = is_valid_weekend_market_closure(t1 + SECONDS_IN_H1, t2)
            if not is_weekend2:
                return False, False, f"Invalid gap between index {i} and {i+1} ({t1} -> {t2}, {diff/3600:.1f}h): {reason}"

        crosses_weekend = True

    return True, crosses_weekend, "Valid path"


def audit_candle_paths_from_timestamps(
    candle_timestamps: List[int],
    complete_ism_ts: List[int],
    split_timestamp: int = SPLIT_TIMESTAMP
) -> Dict[str, Any]:
    """
    Evaluates forward active H1 candle path completeness for 24 and 48 active bars.
    STRICTLY PRICE-BLIND: only operates on Unix timestamps.

    Exit rule: The trade enters at the Open of the H1 bar at T_entry = T_release + 3600.
    The trade is held for H active H1 bars (bars idx through idx + H - 1).
    The trade exits at the Close of the final active H1 bar (idx + H - 1).
    Valid weekend market closures are stepped over in bar indexing.
    Rejects any path encountering arbitrary weekday gaps, unsorted timestamps,
    or crossing into the post-2022 holdout.
    """
    # Verify input timestamps: strictly pre-split and strictly sorted
    for i in range(len(candle_timestamps)):
        if candle_timestamps[i] >= split_timestamp:
            raise ValueError(f"Candle timestamp at index {i} ({candle_timestamps[i]}) exceeds split {split_timestamp}")

    for i in range(len(candle_timestamps) - 1):
        if candle_timestamps[i + 1] <= candle_timestamps[i]:
            raise ValueError(
                f"Duplicate or unsorted candle timestamps at index {i}: "
                f"{candle_timestamps[i]} -> {candle_timestamps[i+1]}"
            )

    ts_to_idx = {ts: idx for idx, ts in enumerate(candle_timestamps)}

    paths_24_ok = 0
    paths_48_ok = 0
    weekend_cross_24 = 0
    weekend_cross_48 = 0
    path_details = []

    for r_ts in sorted(complete_ism_ts):
        entry_ts = r_ts + SECONDS_IN_H1

        if entry_ts >= split_timestamp:
            path_details.append({
                "release_ts": r_ts,
                "entry_ts": entry_ts,
                "error": "Entry at or beyond split boundary"
            })
            continue

        if entry_ts not in ts_to_idx:
            path_details.append({
                "release_ts": r_ts,
                "entry_ts": entry_ts,
                "error": "Entry timestamp not in candle series"
            })
            continue

        idx = ts_to_idx[entry_ts]

        # 24 active bars
        is_24_ok = False
        cross_24 = False
        exit_bar_24_open = None
        exit_bar_24_close = None
        if idx + 24 <= len(candle_timestamps):
            bars_24 = candle_timestamps[idx:idx + 24]
            valid_24, cross_24, reason_24 = validate_h1_path_transitions(bars_24, split_timestamp=split_timestamp)
            if valid_24:
                is_24_ok = True
                paths_24_ok += 1
                if cross_24:
                    weekend_cross_24 += 1
                exit_bar_24_open = bars_24[-1]
                exit_bar_24_close = bars_24[-1] + SECONDS_IN_H1

        # 48 active bars
        is_48_ok = False
        cross_48 = False
        exit_bar_48_open = None
        exit_bar_48_close = None
        if idx + 48 <= len(candle_timestamps):
            bars_48 = candle_timestamps[idx:idx + 48]
            valid_48, cross_48, reason_48 = validate_h1_path_transitions(bars_48, split_timestamp=split_timestamp)
            if valid_48:
                is_48_ok = True
                paths_48_ok += 1
                if cross_48:
                    weekend_cross_48 += 1
                exit_bar_48_open = bars_48[-1]
                exit_bar_48_close = bars_48[-1] + SECONDS_IN_H1

        path_details.append({
            "release_ts": r_ts,
            "entry_ts": entry_ts,
            "is_24_complete": is_24_ok,
            "crosses_weekend_24": cross_24,
            "final_bar_open_24": exit_bar_24_open,
            "final_bar_close_24": exit_bar_24_close,
            "is_48_complete": is_48_ok,
            "crosses_weekend_48": cross_48,
            "final_bar_open_48": exit_bar_48_open,
            "final_bar_close_48": exit_bar_48_close,
        })

    return {
        "evaluated_packages": len(complete_ism_ts),
        "paths_24_complete": paths_24_ok,
        "weekend_cross_24": weekend_cross_24,
        "paths_48_complete": paths_48_ok,
        "weekend_cross_48": weekend_cross_48,
        "details": path_details,
    }


def run_full_reconciliation(data_dir: str = DEFAULT_DATA_DIR) -> Dict[str, Any]:
    """
    Runs full price-blind reconciliation on pinned files.
    Genuinely extracts only timestamp column 0, stops before the 2023 split,
    and never tokenizes OHLC/spread/volume fields.
    """
    cal_releases_path = os.path.join(data_dir, "calendar_releases.csv")
    cal_events_path = os.path.join(data_dir, "calendar_events.csv")
    candle_path = os.path.join(data_dir, "candles", "candles_EURUSD_H1.csv")

    all_releases, by_event = load_pre2023_releases(cal_releases_path)
    ism_audit = audit_ism_headline(by_event)
    pp_matrix = audit_headline_prices_paid_matrix(by_event, ism_audit["complete_afp_releases"])
    multi_comp = audit_multi_component_concordance(by_event, ism_audit)
    sp_audit = audit_sp_global(by_event, by_event.get("840040001", []), ism_audit["actionable_timestamps"])
    cs_audit = audit_construction_spending(by_event, by_event.get("840040001", []))
    collisions = audit_foreign_currency_collisions(all_releases, by_event.get("840040001", []), ism_audit["actionable_timestamps"])
    metadata = audit_calendar_metadata(cal_events_path)

    # Read candle timestamps STRICTLY PRICE-BLIND via stream_candle_timestamps_only
    # Extracts ONLY the field-0 substring before the first comma
    # Stops before 1672531200; never tokenizes columns 1..N
    candle_timestamps = list(stream_candle_timestamps_only(candle_path, split_timestamp=SPLIT_TIMESTAMP))

    path_audit = audit_candle_paths_from_timestamps(
        candle_timestamps,
        list(ism_audit["complete_timestamps"]),
        split_timestamp=SPLIT_TIMESTAMP
    )

    return {
        "ism_audit": ism_audit,
        "pp_matrix": pp_matrix,
        "multi_component_concordance": multi_comp,
        "sp_audit": sp_audit,
        "cs_audit": cs_audit,
        "collisions": collisions,
        "metadata": metadata,
        "path_audit": path_audit,
    }


def main():
    report = run_full_reconciliation()
    ism = report["ism_audit"]
    pp = report["pp_matrix"]
    mc = report["multi_component_concordance"]
    sp = report["sp_audit"]
    cs = report["cs_audit"]
    collisions = report["collisions"]
    meta = report["metadata"]
    paths = report["path_audit"]

    print("================================================================================")
    print("PRICE-BLIND FORENSIC RECONCILIATION REPORT: US ISM MANUFACTURING PMI")
    print("================================================================================")
    print(f"Total Pre-2023 Headline Releases: {ism['total_pre2023']}")
    print(f"Complete A/F/P Packages: {ism['complete_afp_count']}")
    print(f"Incomplete (Missing Forecasts): {ism['incomplete_count']}")
    print(f"Positive Surprises (>0): {ism['positive_count']}")
    print(f"Negative Surprises (<0): {ism['negative_count']}")
    print(f"Zero Surprises (==0): {ism['zero_count']}")
    print(f"Actionable Packages (S_H != 0): {ism['actionable_count']}")

    print("\n--- HEADLINE x PRICES PAID SURPRISE MATRIX (RAW SCALED INTEGERS) ---")
    for k in ["POS/POS", "POS/NEG", "POS/ZERO", "NEG/POS", "NEG/NEG", "NEG/ZERO", "ZERO/POS", "ZERO/NEG", "ZERO/ZERO"]:
        if pp.get(k, 0) > 0:
            print(f"  {k}: {pp[k]}")

    print("\n--- MULTI-COMPONENT CONCORDANCE AUDIT (COMPLETE A/F/P & NONZERO S_H) ---")
    hen = mc["headline_emp_neworders"]
    print(f"  Headline + Employment + New Orders:")
    print(f"    Complete Packages: {hen['complete_packages']}")
    print(f"    Concordant: {hen['concordant_total']} (Positive: {hen['concordant_positive']}, Negative: {hen['concordant_negative']})")
    print(f"    Discordant / Non-Concordant: {hen['discordant_total']} (Opposite Sign: {hen['opposite_sign_total']}, Neutral Component: {hen['neutral_component_total']})")

    hpe = mc["headline_prices_paid_emp"]
    print(f"  Headline + Prices Paid + Employment:")
    print(f"    Complete Packages: {hpe['complete_packages']}")
    print(f"    Concordant: {hpe['concordant_total']} (Positive: {hpe['concordant_positive']}, Negative: {hpe['concordant_negative']})")
    print(f"    Discordant / Non-Concordant: {hpe['discordant_total']} (Opposite Sign: {hpe['opposite_sign_total']}, Neutral Component: {hpe['neutral_component_total']})")

    c4 = mc["all_four_components"]
    print(f"  All Four Components (Headline + Prices Paid + Employment + New Orders):")
    print(f"    Complete Packages: {c4['complete_packages']}")
    print(f"    Concordant: {c4['concordant_total']} (Positive: {c4['concordant_positive']}, Negative: {c4['concordant_negative']})")
    print(f"    Discordant / Non-Concordant: {c4['discordant_total']} (Opposite Sign: {c4['opposite_sign_total']}, Neutral Component: {c4['neutral_component_total']})")

    print("\n--- S&P GLOBAL MANUFACTURING PMI (840500001) AUDIT ---")
    print(f"  Revision 1: Total Pre-2023 Rows: {sp['rev1_total']}, Populated Forecasts: {sp['rev1_forecasts_populated']}")
    print(f"  Revision 3: Total Pre-2023 Rows: {sp['rev3_total']}, Populated Forecasts: {sp['rev3_forecasts_populated']}")
    print(f"  Rev 3 exactly 900s before ISM: {sp['rev3_exact_900s_all']}/{ism['total_pre2023']}")
    print(f"  Rev 3 exactly 900s before ISM with Forecast: {sp['rev3_exact_900s_with_fc_all']}/{ism['total_pre2023']}")
    print(f"  Rev 3 exactly 900s before Actionable ISM (N=66): {sp['rev3_exact_900s_actionable']}/66")
    print(f"  Rev 3 exactly 900s before Actionable ISM with Forecast: {sp['rev3_exact_900s_with_fc_actionable']}/66")

    print("\n--- CONSTRUCTION SPENDING (840020002) CO-RELEASE AUDIT ---")
    print(f"  Co-releases at same second: {cs['co_releases_with_ism']}/{cs['total_ism_releases']}")

    print("\n--- FOREIGN CURRENCY COLLISIONS AT ISM TIMESTAMPS ---")
    for c in collisions:
        print(f"  ts={c['timestamp']} ({c['timestamp_server_text']}) | Ccy: {c['currency']} | Event {c['event_id']}: {c['event_name']} | Actionable: {c['is_actionable']}")

    print("\n--- EURUSD H1 CANDLE PATH COMPLETENESS ---")
    print(f"  24 Active H1 Bars: {paths['paths_24_complete']}/{paths['evaluated_packages']} Complete (Weekend gaps: {paths['weekend_cross_24']})")
    print(f"  48 Active H1 Bars: {paths['paths_48_complete']}/{paths['evaluated_packages']} Complete (Weekend gaps: {paths['weekend_cross_48']})")
    print("================================================================================")


if __name__ == "__main__":
    main()
