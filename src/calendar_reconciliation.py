"""
Independent Calendar Reconciliation Module
Forensic audit and identity reconciliation for US Retail Sales & Core Retail Sales.
"""

from typing import Dict, Any, List
from .parsers import stream_calendar_releases, SPLIT_TIMESTAMP

HEADLINE_EVENT_ID = "840020010"
CORE_EVENT_ID = "840020011"
HEADLINE_SERIES_KEY = "USD:US:840020010:r0"
CORE_SERIES_KEY = "USD:US:840020011:r0"


def reconcile_retail_sales_series(calendar_csv_path: str) -> Dict[str, Any]:
    """
    Performs independent forensic reconciliation of:
    - USD:US:840020010:r0 (Retail Sales m/m)
    - USD:US:840020011:r0 (Core Retail Sales m/m)
    """
    headline_all: List[Dict[str, Any]] = []
    core_all: List[Dict[str, Any]] = []

    # Stream full calendar (without timestamp cap initially to verify total vs pre-2023)
    for row in stream_calendar_releases(calendar_csv_path, max_timestamp=None):
        eid = str(row["event_id"])
        if eid == HEADLINE_EVENT_ID:
            headline_all.append(row)
        elif eid == CORE_EVENT_ID:
            core_all.append(row)

    # Filter pre-2023
    headline_pre = [r for r in headline_all if r["timestamp"] < SPLIT_TIMESTAMP]
    core_pre = [r for r in core_all if r["timestamp"] < SPLIT_TIMESTAMP]

    headline_post = [r for r in headline_all if r["timestamp"] >= SPLIT_TIMESTAMP]
    core_post = [r for r in core_all if r["timestamp"] >= SPLIT_TIMESTAMP]

    # Reconcile identities & metadata
    h_meta = headline_pre[0] if headline_pre else {}
    c_meta = core_pre[0] if core_pre else {}

    # Check revision distribution
    h_revisions = set(r["revision"] for r in headline_pre)
    c_revisions = set(r["revision"] for r in core_pre)

    # Single-series completeness (pre-2023)
    def is_complete_afp(r: Dict[str, Any]) -> bool:
        return (
            r["actual"] != "" and r["actual"] is not None and
            r["forecast"] != "" and r["forecast"] is not None and
            r["previous"] != "" and r["previous"] is not None
        )

    h_afp_count = sum(1 for r in headline_pre if is_complete_afp(r))
    c_afp_count = sum(1 for r in core_pre if is_complete_afp(r))

    # Joint package completeness
    h_by_ts = {r["timestamp"]: r for r in headline_pre}
    c_by_ts = {r["timestamp"]: r for r in core_pre}

    all_timestamps = sorted(set(h_by_ts.keys()) | set(c_by_ts.keys()))
    both_timestamps = sorted(set(h_by_ts.keys()) & set(c_by_ts.keys()))
    only_h_timestamps = sorted(set(h_by_ts.keys()) - set(c_by_ts.keys()))
    only_c_timestamps = sorted(set(c_by_ts.keys()) - set(h_by_ts.keys()))

    joint_afp_count = 0
    missing_forecast_count = 0

    for ts in both_timestamps:
        h = h_by_ts[ts]
        c = c_by_ts[ts]
        h_ok = is_complete_afp(h)
        c_ok = is_complete_afp(c)
        if h_ok and c_ok:
            joint_afp_count += 1
        elif (h["forecast"] == "" or h["forecast"] is None) and (c["forecast"] == "" or c["forecast"] is None):
            missing_forecast_count += 1

    return {
        "headline": {
            "series_key": HEADLINE_SERIES_KEY,
            "event_id": HEADLINE_EVENT_ID,
            "event_name": h_meta.get("event_name"),
            "event_code": h_meta.get("event_code"),
            "currency": h_meta.get("currency"),
            "country_code": h_meta.get("country_code"),
            "unit": h_meta.get("unit"),
            "multiplier": h_meta.get("multiplier"),
            "digits": h_meta.get("digits"),
            "importance": h_meta.get("importance"),
            "sector": h_meta.get("sector"),
            "frequency": h_meta.get("frequency"),
            "source_url": h_meta.get("source_url"),
            "revisions_seen": sorted(list(h_revisions)),
            "total_releases": len(headline_all),
            "pre2023_releases": len(headline_pre),
            "post2022_sealed_releases": len(headline_post),
            "complete_afp_pre2023": h_afp_count,
            "missing_forecast_pre2023": len(headline_pre) - h_afp_count
        },
        "core": {
            "series_key": CORE_SERIES_KEY,
            "event_id": CORE_EVENT_ID,
            "event_name": c_meta.get("event_name"),
            "event_code": c_meta.get("event_code"),
            "currency": c_meta.get("currency"),
            "country_code": c_meta.get("country_code"),
            "unit": c_meta.get("unit"),
            "multiplier": c_meta.get("multiplier"),
            "digits": c_meta.get("digits"),
            "importance": c_meta.get("importance"),
            "sector": c_meta.get("sector"),
            "frequency": c_meta.get("frequency"),
            "source_url": c_meta.get("source_url"),
            "revisions_seen": sorted(list(c_revisions)),
            "total_releases": len(core_all),
            "pre2023_releases": len(core_pre),
            "post2022_sealed_releases": len(core_post),
            "complete_afp_pre2023": c_afp_count,
            "missing_forecast_pre2023": len(core_pre) - c_afp_count
        },
        "joint_package": {
            "total_distinct_timestamps": len(all_timestamps),
            "co_released_timestamps": len(both_timestamps),
            "headline_only_timestamps": len(only_h_timestamps),
            "core_only_timestamps": len(only_c_timestamps),
            "joint_complete_afp": joint_afp_count,
            "joint_missing_forecast": missing_forecast_count,
            "joint_completeness_ratio": joint_afp_count / len(all_timestamps) if all_timestamps else 0.0
        }
    }
