"""
Price-Blind Reconciliation Engine for US ISM Manufacturing PMI (USD:US:840040001:r0)
Verifies calendar inventory, component relationships, S&P Global preceding releases,
co-release collisions, and EURUSD H1 candle path continuity.

STRICT CONSTRAINTS:
- Price-Blind: Only reads calendar fields and candle timestamps (column 0).
- Zero access to OHLC prices, volumes, spreads, or price returns.
- Enforces pre-2023 chronological boundary (timestamp < 1672531200).
"""

import csv
import os
import sys
from typing import Dict, List, Set, Tuple, Optional, Any

SPLIT_TIMESTAMP = 1672531200  # 2023-01-01 00:00:00 server time
SECONDS_IN_H1 = 3600

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
    """
    target_ids = {"840040001", "840040002", "840040004", "840040006", "840020002", "840030005", "840500001"}
    metadata: Dict[str, Dict[str, Any]] = {}

    with open(events_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = row.get("event_id")
            if eid in target_ids:
                metadata[eid] = {
                    "event_id": eid,
                    "event_name": row.get("event_name", ""),
                    "event_code": row.get("event_code", ""),
                    "sector": row.get("sector", ""),
                    "sector_code": int(row.get("sector_code", 8)) if row.get("sector_code") else 8,
                    "unit": row.get("unit", ""),
                    "unit_code": int(row.get("unit_code", 0)) if row.get("unit_code") else 0,
                    "importance": row.get("importance", ""),
                    "importance_code": int(row.get("importance_code", 0)) if row.get("importance_code") else 0,
                }

    return metadata


def audit_candle_paths_from_timestamps(
    candle_timestamps: List[int],
    complete_ism_ts: List[int]
) -> Dict[str, Any]:
    """
    Evaluates forward active H1 candle path completeness for 24 and 48 active bars.
    STRICTLY PRICE-BLIND: only takes a list of candle timestamps.

    Exit rule: The trade enters at the Open of the H1 bar at T_entry = T_release + 3600.
    The trade is held for H active H1 bars (bars idx through idx + H - 1).
    The trade exits at the Close of the final active H1 bar (idx + H - 1).
    Valid weekend market closures are stepped over in bar indexing.
    """
    candle_ts_sorted = sorted(candle_timestamps)
    ts_to_idx = {ts: idx for idx, ts in enumerate(candle_ts_sorted)}

    paths_24_ok = 0
    paths_48_ok = 0
    weekend_cross_24 = 0
    weekend_cross_48 = 0
    path_details = []

    for r_ts in sorted(complete_ism_ts):
        entry_ts = r_ts + 3600
        if entry_ts not in ts_to_idx:
            continue

        idx = ts_to_idx[entry_ts]

        # 24 active bars
        is_24_ok = (idx + 24 <= len(candle_ts_sorted))
        cross_24 = False
        exit_bar_24_open = None
        if is_24_ok:
            paths_24_ok += 1
            bars_24 = candle_ts_sorted[idx:idx + 24]
            cross_24 = any(bars_24[i + 1] - bars_24[i] > SECONDS_IN_H1 for i in range(len(bars_24) - 1))
            if cross_24:
                weekend_cross_24 += 1
            # Final active bar open is bars_24[-1]
            # Exit occurs at close of bars_24[-1]
            exit_bar_24_open = bars_24[-1]

        # 48 active bars
        is_48_ok = (idx + 48 <= len(candle_ts_sorted))
        cross_48 = False
        exit_bar_48_open = None
        if is_48_ok:
            paths_48_ok += 1
            bars_48 = candle_ts_sorted[idx:idx + 48]
            cross_48 = any(bars_48[i + 1] - bars_48[i] > SECONDS_IN_H1 for i in range(len(bars_48) - 1))
            if cross_48:
                weekend_cross_48 += 1
            exit_bar_48_open = bars_48[-1]

        path_details.append({
            "release_ts": r_ts,
            "entry_ts": entry_ts,
            "is_24_complete": is_24_ok,
            "crosses_weekend_24": cross_24,
            "final_bar_open_24": exit_bar_24_open,
            "is_48_complete": is_48_ok,
            "crosses_weekend_48": cross_48,
            "final_bar_open_48": exit_bar_48_open,
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
    """
    cal_releases_path = os.path.join(data_dir, "calendar_releases.csv")
    cal_events_path = os.path.join(data_dir, "calendar_events.csv")
    candle_path = os.path.join(data_dir, "candles", "candles_EURUSD_H1.csv")

    all_releases, by_event = load_pre2023_releases(cal_releases_path)
    ism_audit = audit_ism_headline(by_event)
    pp_matrix = audit_headline_prices_paid_matrix(by_event, ism_audit["complete_afp_releases"])
    sp_audit = audit_sp_global(by_event, by_event.get("840040001", []), ism_audit["actionable_timestamps"])
    cs_audit = audit_construction_spending(by_event, by_event.get("840040001", []))
    collisions = audit_foreign_currency_collisions(all_releases, by_event.get("840040001", []), ism_audit["actionable_timestamps"])
    metadata = audit_calendar_metadata(cal_events_path)

    # Read candle timestamps PRICE-BLIND (time column only)
    candle_timestamps: List[int] = []
    with open(candle_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candle_timestamps.append(int(row["time"]))

    path_audit = audit_candle_paths_from_timestamps(candle_timestamps, list(ism_audit["complete_timestamps"]))

    return {
        "ism_audit": ism_audit,
        "pp_matrix": pp_matrix,
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
