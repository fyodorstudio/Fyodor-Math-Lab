"""
Macroeconomic Package-Level Eligibility Ledger
Builds the price-blind package ledger for US Retail Sales & Core Retail Sales on EURUSD.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import os

from .parsers import stream_calendar_releases, SPLIT_TIMESTAMP
from .candle_coverage import CandleTimestampIndex, SECONDS_IN_H4

HEADLINE_EID = "840020010"
CORE_EID = "840020011"


def compute_entry_timestamp(release_ts: int) -> int:
    """
    Computes the Open timestamp of the next completed H4 bar following release.
    H4 bars start at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00.
    15:30:00 -> 16:00:00 (release_ts + 1800, 30-min delay)
    16:30:00 -> 20:00:00 (release_ts + 12600, 210-min / 3.5h delay)
    """
    remainder = release_ts % SECONDS_IN_H4
    if remainder == 0:
        return release_ts
    return release_ts + (SECONDS_IN_H4 - remainder)


def build_retail_sales_package_ledger(
    calendar_csv_path: str,
    candle_csv_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs the complete price-blind package-level eligibility ledger.
    """
    # 1. Load all pre-2023 calendar releases grouped by timestamp
    by_timestamp: Dict[int, List[Dict[str, Any]]] = {}
    for row in stream_calendar_releases(calendar_csv_path, max_timestamp=SPLIT_TIMESTAMP):
        ts = row["timestamp"]
        if ts not in by_timestamp:
            by_timestamp[ts] = []
        by_timestamp[ts].append(row)

    # 2. Identify packages containing Retail Sales m/m
    retail_timestamps = sorted([
        ts for ts, rows in by_timestamp.items()
        if any(str(r["event_id"]) == HEADLINE_EID for r in rows)
    ])

    # 3. Load candle index if path provided
    candle_index = CandleTimestampIndex(candle_csv_path) if candle_csv_path and os.path.exists(candle_csv_path) else None

    # 4. Process each package
    packages: List[Dict[str, Any]] = []

    for ts in retail_timestamps:
        rows = by_timestamp[ts]
        currencies = sorted(list(set(r["currency"] for r in rows)))
        colliding = [c for c in currencies if c != "USD"]
        has_collision = len(colliding) > 0

        h_row = next(r for r in rows if str(r["event_id"]) == HEADLINE_EID)
        c_row = next((r for r in rows if str(r["event_id"]) == CORE_EID), None)

        # Parse date & weekday
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        weekday = dt.strftime("%A")

        # Completeness check
        h_afp = bool(
            h_row["actual"] != "" and h_row["actual"] is not None and
            h_row["forecast"] != "" and h_row["forecast"] is not None and
            h_row["previous"] != "" and h_row["previous"] is not None
        )
        c_afp = bool(
            c_row is not None and
            c_row["actual"] != "" and c_row["actual"] is not None and
            c_row["forecast"] != "" and c_row["forecast"] is not None and
            c_row["previous"] != "" and c_row["previous"] is not None
        )
        joint_afp = h_afp and c_afp

        # Surprises (Actual - Forecast)
        h_diff = None
        c_diff = None
        category = "MISSING_FORECAST"

        if joint_afp:
            ha = h_row["actual_raw_scaled_1e6"] if h_row["actual_raw_scaled_1e6"] is not None else round(float(h_row["actual"]) * 1e6)
            hf = h_row["forecast_raw_scaled_1e6"] if h_row["forecast_raw_scaled_1e6"] is not None else round(float(h_row["forecast"]) * 1e6)
            ca = c_row["actual_raw_scaled_1e6"] if c_row["actual_raw_scaled_1e6"] is not None else round(float(c_row["actual"]) * 1e6)
            cf = c_row["forecast_raw_scaled_1e6"] if c_row["forecast_raw_scaled_1e6"] is not None else round(float(c_row["forecast"]) * 1e6)

            h_diff = ha - hf
            c_diff = ca - cf

            if h_diff > 0 and c_diff > 0:
                category = "STRICT_AGREE_POS"
            elif h_diff < 0 and c_diff < 0:
                category = "STRICT_AGREE_NEG"
            elif (h_diff > 0 and c_diff < 0) or (h_diff < 0 and c_diff > 0):
                category = "ACTIVE_CONFLICT"
            elif h_diff == 0 and c_diff == 0:
                category = "BOTH_ZERO"
            else:
                category = "ONE_ZERO"

        # Execution timing
        entry_ts = compute_entry_timestamp(ts)
        entry_delay_minutes = (entry_ts - ts) // 60

        # Candle coverage evaluation
        h6_cov = None
        h12_cov = None
        pre_lookback_audit = None
        h6_later_usd = 0
        h6_later_eur = 0
        h12_later_usd = 0
        h12_later_eur = 0

        if candle_index:
            # Pure forward paths
            h6_cov = candle_index.evaluate_forward_horizon(entry_ts, horizon_h4=6)
            h12_cov = candle_index.evaluate_forward_horizon(entry_ts, horizon_h4=12)

            # Separate diagnostic for pre-entry lookback
            pre_lookback_audit = candle_index.audit_pre_entry_lookback(entry_ts, target_h4_blocks=14)

            # Count subsequent releases between entry and exit
            if h6_cov["is_complete"] and h6_cov["exit_timestamp"]:
                exit_h6 = h6_cov["exit_timestamp"]
                for other_ts in by_timestamp:
                    if entry_ts < other_ts <= exit_h6:
                        other_currs = set(r["currency"] for r in by_timestamp[other_ts])
                        if "USD" in other_currs:
                            h6_later_usd += 1
                        if "EUR" in other_currs:
                            h6_later_eur += 1

            if h12_cov["is_complete"] and h12_cov["exit_timestamp"]:
                exit_h12 = h12_cov["exit_timestamp"]
                for other_ts in by_timestamp:
                    if entry_ts < other_ts <= exit_h12:
                        other_currs = set(r["currency"] for r in by_timestamp[other_ts])
                        if "USD" in other_currs:
                            h12_later_usd += 1
                        if "EUR" in other_currs:
                            h12_later_eur += 1

        packages.append({
            "timestamp": ts,
            "timestamp_server_text": h_row["timestamp_server_text"],
            "year": year,
            "weekday": weekday,
            "co_released_events_count": len(rows),
            "currencies": currencies,
            "has_cross_currency_collision": has_collision,
            "colliding_currencies": colliding,
            "headline_actual": h_row["actual"],
            "headline_forecast": h_row["forecast"],
            "headline_previous": h_row["previous"],
            "headline_diff_scaled": h_diff,
            "core_actual": c_row["actual"] if c_row else None,
            "core_forecast": c_row["forecast"] if c_row else None,
            "core_previous": c_row["previous"] if c_row else None,
            "core_diff_scaled": c_diff,
            "joint_afp_complete": joint_afp,
            "sign_category": category,
            "entry_timestamp": entry_ts,
            "entry_delay_minutes": entry_delay_minutes,
            "h6_coverage": h6_cov,
            "h12_coverage": h12_cov,
            "pre_lookback_audit": pre_lookback_audit,
            "h6_later_usd_packages": h6_later_usd if h6_cov and h6_cov["is_complete"] else None,
            "h6_later_eur_packages": h6_later_eur if h6_cov and h6_cov["is_complete"] else None,
            "h12_later_usd_packages": h12_later_usd if h12_cov and h12_cov["is_complete"] else None,
            "h12_later_eur_packages": h12_later_eur if h12_cov and h12_cov["is_complete"] else None,
        })

    # Summary statistics
    total_pkgs = len(packages)
    afp_pkgs = [p for p in packages if p["joint_afp_complete"]]
    n_afp = len(afp_pkgs)

    # Contingency distribution
    cat_counts: Dict[str, int] = {}
    for p in packages:
        cat = p["sign_category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Year distribution
    year_distribution: Dict[int, Dict[str, int]] = {}
    for p in packages:
        yr = p["year"]
        if yr not in year_distribution:
            year_distribution[yr] = {"total": 0, "complete_afp": 0}
        year_distribution[yr]["total"] += 1
        if p["joint_afp_complete"]:
            year_distribution[yr]["complete_afp"] += 1

    # Collision statistics
    collision_count_all = sum(1 for p in packages if p["has_cross_currency_collision"])
    collision_count_afp = sum(1 for p in afp_pkgs if p["has_cross_currency_collision"])

    # Forward path completion on complete AFP packages
    h6_complete_afp = sum(1 for p in afp_pkgs if p["h6_coverage"] and p["h6_coverage"]["is_complete"])
    h12_complete_afp = sum(1 for p in afp_pkgs if p["h12_coverage"] and p["h12_coverage"]["is_complete"])
    h6_cross_weekend_afp = sum(1 for p in afp_pkgs if p["h6_coverage"] and p["h6_coverage"]["crosses_weekend"])
    h12_cross_weekend_afp = sum(1 for p in afp_pkgs if p["h12_coverage"] and p["h12_coverage"]["crosses_weekend"])

    return {
        "total_packages": total_pkgs,
        "complete_joint_afp_packages": n_afp,
        "sign_distribution": cat_counts,
        "year_distribution": year_distribution,
        "cross_currency_collisions": {
            "all_pre2023": {"count": collision_count_all, "pct": collision_count_all / total_pkgs if total_pkgs else 0},
            "complete_afp": {"count": collision_count_afp, "pct": collision_count_afp / n_afp if n_afp else 0},
        },
        "forward_coverage_complete_afp": {
            "h6_clean_count": h6_complete_afp,
            "h6_clean_pct": h6_complete_afp / n_afp if n_afp else 0,
            "h6_weekend_crossings": h6_cross_weekend_afp,
            "h6_weekend_pct": h6_cross_weekend_afp / n_afp if n_afp else 0,
            "h12_clean_count": h12_complete_afp,
            "h12_clean_pct": h12_complete_afp / n_afp if n_afp else 0,
            "h12_weekend_crossings": h12_cross_weekend_afp,
            "h12_weekend_pct": h12_cross_weekend_afp / n_afp if n_afp else 0,
        },
        "packages": packages
    }


if __name__ == "__main__":
    cal_file = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv"
    eur_file = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv"
    res = build_retail_sales_package_ledger(cal_file, eur_file)
    print("Package ledger built successfully:")
    print(f"Total packages: {res['total_packages']}")
    print(f"Complete Joint AFP: {res['complete_joint_afp_packages']}")
    print(f"Sign distribution: {res['sign_distribution']}")
    print(f"Collisions: {res['cross_currency_collisions']}")
    print(f"Forward coverage: {res['forward_coverage_complete_afp']}")
