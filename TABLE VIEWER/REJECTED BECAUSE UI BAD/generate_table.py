"""
Full-History Exploratory EURUSD H1 Macro-Event Viewer & Atlas Builder (2015–2026)

Owner's Scope Decision:
- Full unblinded exploratory inspection across the entire pinned history (2015 to 2026-09-23).
- 2023–2026 price concealment is removed for THIS exploratory viewer.
- Explicit governance notice: 2023–2026 cannot later be claimed as an untouched historical holdout
  for rules selected with this tool. Future forward testing requires fresh demo/live terminal data.
- EURUSD H1 only; cross-symbol research is explicitly deferred.

Accounting Fix:
- Co-releases (German Ifo Climate + Expectations; US Retail Sales Headline + Core) are evaluated
  as single co-release event episodes. Each simultaneous co-release contributes exactly ONE episode
  and ONE price path to sample size and statistics.
- Pre-2023 Ifo represents 40 actionable episodes (not 80).
- Pre-2023 Retail Sales represents 49 trade episodes (not 98).
- The 157 pre-2023 cohort memberships correspond to exactly 149 distinct release timestamps.
"""

import csv
from datetime import datetime, timezone
import json
import math
import os
import statistics
import sys
from typing import Dict, List, Any, Optional, Tuple

MAX_HORIZONS = 60
SPLIT_TIMESTAMP = 1672531200  # 2023-01-01 00:00:00 broker trade-server time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDLE_PATH = os.path.join(
    BASE_DIR,
    "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server",
    "candles", "candles_EURUSD_H1.csv"
)
CALENDAR_PATH = os.path.join(
    BASE_DIR,
    "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server",
    "calendar_releases.csv"
)
PHASE1_PATH = os.path.join(BASE_DIR, "evidence", "trials", "phase1", "phase1_exploration.json")
IFO_PATH = os.path.join(BASE_DIR, "evidence", "trials", "ifo", "ifo_pilot_ledger.json")
RETAIL_SALES_PATH = os.path.join(BASE_DIR, "evidence", "trials", "retail_sales", "retail_sales_pre2023_discovery.json")
OUTPUT_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "table_viewer.html")

# Verified Series Metadata
SERIES_METADATA = {
    "USD:US:840030005:r0": {
        "event_id": 840030005,
        "name": "USD CPI m/m",
        "family": "US inflation",
        "unit": "%",
        "digits": 1
    },
    "USD:US:840030006:r0": {
        "event_id": 840030006,
        "name": "USD Core CPI m/m",
        "family": "US inflation",
        "unit": "%",
        "digits": 1
    },
    "USD:US:840010001:r0": {
        "event_id": 840010001,
        "name": "USD Core PCE m/m",
        "family": "US inflation",
        "unit": "%",
        "digits": 1
    },
    "USD:US:840030016:r0": {
        "event_id": 840030016,
        "name": "USD Nonfarm Payrolls",
        "family": "US labor",
        "unit": "k",
        "digits": 0
    },
    "EUR:DE:276030003:r0": {
        "event_id": 276030003,
        "name": "Ifo Business Climate",
        "family": "German Ifo",
        "unit": "pts",
        "digits": 1
    },
    "EUR:DE:276030001:r0": {
        "event_id": 276030001,
        "name": "Ifo Business Expectations",
        "family": "German Ifo",
        "unit": "pts",
        "digits": 1
    },
    "USD:US:840020010:r0": {
        "event_id": 840020010,
        "name": "Retail Sales m/m",
        "family": "US Retail Sales",
        "unit": "%",
        "digits": 1
    },
    "USD:US:840020011:r0": {
        "event_id": 840020011,
        "name": "Core Retail Sales m/m",
        "family": "US Retail Sales",
        "unit": "%",
        "digits": 1
    },
    "USD:US:840040001:r0": {
        "event_id": 840040001,
        "name": "ISM Manufacturing PMI",
        "family": "US ISM Manufacturing PMI",
        "unit": "pts",
        "digits": 1
    }
}


def quantile_type7(data: List[float], p: float = 0.75) -> float:
    """Hyndman-Fan Type 7 linear interpolation quantile: index = (N - 1) * p."""
    n = len(data)
    if n == 0:
        return 0.0
    if n == 1:
        return float(data[0])
    idx = (n - 1) * p
    i = int(idx)
    frac = idx - i
    if i >= n - 1:
        return float(data[-1])
    return data[i] + frac * (data[i + 1] - data[i])


def compute_directional_change_pct(
    entry_open: float,
    close_price: float,
    direction: int
) -> float:
    """Gross directional EURUSD price change (%) from entry open to candle close."""
    if entry_open <= 0 or close_price <= 0:
        raise ValueError(f"Prices must be strictly positive: entry_open={entry_open}, close_price={close_price}")
    if direction not in (1, -1):
        raise ValueError(f"Direction must be +1 (Long) or -1 (Short), got {direction}")
    return direction * ((close_price - entry_open) / entry_open) * 100.0


def load_all_candles(candle_path: str = CANDLE_PATH) -> Tuple[List[List[Any]], Dict[int, int]]:
    """Loads all 72,967 EURUSD H1 candles across the entire export period."""
    candles = []
    ts_to_idx = {}
    with open(candle_path, "r", encoding="utf-8") as f:
        header = f.readline()
        if not header:
            raise ValueError(f"Empty candle file: {candle_path}")
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            ts = int(parts[0])
            o = float(parts[1])
            h = float(parts[2])
            l = float(parts[3])
            c = float(parts[4])
            ts_to_idx[ts] = len(candles)
            candles.append([ts, o, h, l, c])
    return candles, ts_to_idx


def build_event_episodes(
    calendar_path: str = CALENDAR_PATH,
    phase1_path: str = PHASE1_PATH,
    ifo_path: str = IFO_PATH,
    retail_sales_path: str = RETAIL_SALES_PATH,
    candles: Optional[List[List[Any]]] = None,
    ts_to_idx: Optional[Dict[int, int]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Constructs distinct event episodes across 2015–2026.
    Co-releases (German Ifo Climate + Expectations; Retail Sales Headline + Core) form
    ONE episode per timestamp, contributing exactly ONE price path.
    """
    if candles is None or ts_to_idx is None:
        candles, ts_to_idx = load_all_candles()

    total_candles = len(candles)

    # 1. Load archived artifacts
    with open(phase1_path, "r", encoding="utf-8") as f:
        p1_data = json.load(f)
    with open(ifo_path, "r", encoding="utf-8") as f:
        ifo_data = json.load(f)
    with open(retail_sales_path, "r", encoding="utf-8") as f:
        rs_data = json.load(f)

    # Archived index mappings
    p1_archived = {}
    for sid in ["USD:US:840030005:r0", "USD:US:840030006:r0", "USD:US:840010001:r0", "USD:US:840030016:r0"]:
        for p in p1_data["eurusdOutcomes"][sid]["individualEventPaths"]:
            p1_archived[(sid, p["timestamp"])] = p

    ifo_actionable = {r["timestamp"]: r for r in ifo_data["actionableRows"]}
    ifo_all_packages = {p["timestamp"]: p for p in ifo_data["allPackages"]}
    rs_trade_episodes = {ep["package_timestamp"]: ep for ep in rs_data["trade_episodes"]}

    # 2. Ingest raw calendar rows for target series
    raw_by_series = {sid: [] for sid in SERIES_METADATA}
    with open(calendar_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["revision"]) != 0:
                continue
            eid = int(row["event_id"])
            for sid, meta in SERIES_METADATA.items():
                if meta["event_id"] == eid:
                    raw_by_series[sid].append(row)

    for sid in raw_by_series:
        raw_by_series[sid].sort(key=lambda r: int(r["timestamp"]))

    # Helper function to compute 60-horizon price changes (both raw and directional)
    def compute_price_paths(entry_ts: int, direction: int) -> Tuple[Optional[List[Optional[float]]], Optional[List[Optional[float]]], bool, int]:
        if entry_ts not in ts_to_idx:
            return None, None, False, 0
        eidx = ts_to_idx[entry_ts]
        entry_open = candles[eidx][1]
        raw_path = []
        dir_path = [] if direction != 0 else None
        is_truncated = False
        avail_bars = 0
        for h in range(MAX_HORIZONS):
            target_idx = eidx + h
            if target_idx >= total_candles:
                raw_path.append(None)
                if dir_path is not None:
                    dir_path.append(None)
                is_truncated = True
                continue
            c_bar = candles[target_idx]
            close_p = c_bar[4]
            raw_pct = ((close_p - entry_open) / entry_open) * 100.0
            raw_path.append(round(raw_pct, 4))
            if dir_path is not None:
                pct = compute_directional_change_pct(entry_open, close_p, direction)
                dir_path.append(round(pct, 4))
            avail_bars += 1
        return raw_path, dir_path, is_truncated, avail_bars

    episodes = []

    # -------------------------------------------------------------
    # A. US INFLATION: CPI & Core CPI (Co-released) + Core PCE
    # -------------------------------------------------------------
    # Group CPI m/m and Core CPI m/m by release timestamp
    cpi_releases = {int(r["timestamp"]): r for r in raw_by_series["USD:US:840030005:r0"]}
    core_cpi_releases = {int(r["timestamp"]): r for r in raw_by_series["USD:US:840030006:r0"]}
    all_cpi_ts = sorted(list(set(list(cpi_releases.keys()) + list(core_cpi_releases.keys()))))

    # Prior history for walk-forward scoring
    cpi_history = []
    core_cpi_history = []

    for ts in all_cpi_ts:
        c_row = cpi_releases.get(ts)
        cc_row = core_cpi_releases.get(ts)
        server_text = c_row["timestamp_server_text"] if c_row else (cc_row["timestamp_server_text"] if cc_row else "")
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        is_pre2023 = (ts < SPLIT_TIMESTAMP)

        components = []
        c_score = None
        cc_score = None

        # CPI Headline Component
        if c_row:
            arch = p1_archived.get(("USD:US:840030005:r0", ts))
            if is_pre2023 and arch:
                a, f, p = arch["actual"], arch["forecast"], arch["previous"]
                s = round(arch["surpriseDelta"], 1)
                m = round(arch["momentumDelta"], 1) if arch["momentumDelta"] is not None else None
                c_score = arch["surpriseScore"]
                score_expl = False
            else:
                a = float(c_row["actual"]) if c_row["actual"] != "" else None
                f = float(c_row["forecast"]) if c_row["forecast"] != "" else None
                p = float(c_row["previous"]) if c_row["previous"] != "" else None
                s = round(a - f, 1) if (a is not None and f is not None) else None
                m = round(a - p, 1) if (a is not None and p is not None) else None
                score_expl = not is_pre2023
                if a is not None and f is not None and p is not None:
                    delta = a - f
                    if abs(delta) <= 1e-6:
                        c_score = 1 if len(cpi_history) >= 20 else None
                    elif len(cpi_history) < 20:
                        c_score = None
                    else:
                        p75 = quantile_type7(sorted(cpi_history), 0.75)
                        c_score = 3 if delta > p75 else (2 if delta > 0 else (-3 if abs(delta) > p75 else -2))
                else:
                    c_score = None

            if s is not None and abs(s) > 1e-6:
                cpi_history.append(abs(s))

            components.append({
                "series_id": "USD:US:840030005:r0",
                "name": "USD CPI m/m",
                "actual": a, "forecast": f, "previous": p,
                "surprise": s, "momentum": m,
                "unit": "%", "score": c_score, "score_is_exploratory": score_expl
            })

        # Core CPI Component
        if cc_row:
            arch = p1_archived.get(("USD:US:840030006:r0", ts))
            if is_pre2023 and arch:
                a, f, p = arch["actual"], arch["forecast"], arch["previous"]
                s = round(arch["surpriseDelta"], 1)
                m = round(arch["momentumDelta"], 1) if arch["momentumDelta"] is not None else None
                cc_score = arch["surpriseScore"]
                score_expl = False
            else:
                a = float(cc_row["actual"]) if cc_row["actual"] != "" else None
                f = float(cc_row["forecast"]) if cc_row["forecast"] != "" else None
                p = float(cc_row["previous"]) if cc_row["previous"] != "" else None
                s = round(a - f, 1) if (a is not None and f is not None) else None
                m = round(a - p, 1) if (a is not None and p is not None) else None
                score_expl = not is_pre2023
                if a is not None and f is not None and p is not None:
                    delta = a - f
                    if abs(delta) <= 1e-6:
                        cc_score = 1 if len(core_cpi_history) >= 20 else None
                    elif len(core_cpi_history) < 20:
                        cc_score = None
                    else:
                        p75 = quantile_type7(sorted(core_cpi_history), 0.75)
                        cc_score = 3 if delta > p75 else (2 if delta > 0 else (-3 if abs(delta) > p75 else -2))
                else:
                    cc_score = None

            if s is not None and abs(s) > 1e-6:
                core_cpi_history.append(abs(s))

            components.append({
                "series_id": "USD:US:840030006:r0",
                "name": "USD Core CPI m/m",
                "actual": a, "forecast": f, "previous": p,
                "surprise": s, "momentum": m,
                "unit": "%", "score": cc_score, "score_is_exploratory": score_expl
            })

        # Determine qualifying cohorts
        cohort_tags = []
        if c_score == 3: cohort_tags.append("Headline CPI (+3)")
        if c_score == -3: cohort_tags.append("Headline CPI (-3)")
        if cc_score == 3: cohort_tags.append("Core CPI (+3)")
        if cc_score == -3: cohort_tags.append("Core CPI (-3)")

        # Direction logic: If both qualify with opposite signs, it's conflicting; otherwise follow qualifying score
        is_eligible = len(cohort_tags) > 0
        direction = 0
        direction_label = "—"
        if ("Headline CPI (+3)" in cohort_tags or "Core CPI (+3)" in cohort_tags) and ("Headline CPI (-3)" in cohort_tags or "Core CPI (-3)" in cohort_tags):
            direction = 0
            direction_label = "CONFLICTING"
        elif "Headline CPI (+3)" in cohort_tags or "Core CPI (+3)" in cohort_tags:
            direction = -1
            direction_label = "SHORT"
        elif "Headline CPI (-3)" in cohort_tags or "Core CPI (-3)" in cohort_tags:
            direction = 1
            direction_label = "LONG"

        rel_bar_ts = ts - (ts % 3600)
        rel_idx = ts_to_idx.get(rel_bar_ts)
        entry_ts = ts if ts % 3600 == 0 else ts + (3600 - ts % 3600)
        c_idx = ts_to_idx.get(entry_ts)
        raw_path, path, is_trunc, avail_h = compute_price_paths(entry_ts, direction)

        is_strong_pos = (c_score == 3 or cc_score == 3)
        is_strong_neg = (c_score == -3 or cc_score == -3)
        disposition = ("CONFLICTING_OPPOSITE_SCORES" if direction_label == "CONFLICTING"
                       else (f"QUALIFIED ({direction_label})" if is_eligible
                             else ("SCORED_NON_EXTREME" if any(c["score"] is not None for c in components) else "UNSCORED_EARLY_HISTORY")))

        episodes.append({
            "episode_id": f"US_CPI_{ts}",
            "family": "US inflation",
            "event_name": "USD CPI & Core CPI m/m",
            "timestamp": ts,
            "timestamp_server_text": server_text,
            "year": year,
            "is_pre2023": is_pre2023,
            "components": components,
            "cohort_tags": cohort_tags,
            "is_eligible": is_eligible,
            "direction": direction,
            "direction_label": direction_label,
            "disposition": disposition,
            "entry_timestamp": entry_ts,
            "release_candle_index": rel_idx,
            "candle_index": c_idx,
            "raw_price_path": raw_path,
            "price_path": path,
            "is_truncated": is_trunc,
            "available_horizons": avail_h,
            "is_strong_positive": is_strong_pos,
            "is_strong_negative": is_strong_neg
        })

    # Core PCE Component Series
    pce_releases = raw_by_series["USD:US:840010001:r0"]
    pce_history = []
    for r in pce_releases:
        ts = int(r["timestamp"])
        server_text = r["timestamp_server_text"]
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        is_pre2023 = (ts < SPLIT_TIMESTAMP)

        arch = p1_archived.get(("USD:US:840010001:r0", ts))
        if is_pre2023 and arch:
            a, f, p = arch["actual"], arch["forecast"], arch["previous"]
            s = round(arch["surpriseDelta"], 1)
            m = round(arch["momentumDelta"], 1) if arch["momentumDelta"] is not None else None
            score = arch["surpriseScore"]
            score_expl = False
        else:
            a = float(r["actual"]) if r["actual"] != "" else None
            f = float(r["forecast"]) if r["forecast"] != "" else None
            p = float(r["previous"]) if r["previous"] != "" else None
            s = round(a - f, 1) if (a is not None and f is not None) else None
            m = round(a - p, 1) if (a is not None and p is not None) else None
            score_expl = not is_pre2023
            if a is not None and f is not None and p is not None:
                delta = a - f
                if abs(delta) <= 1e-6:
                    score = 1 if len(pce_history) >= 20 else None
                elif len(pce_history) < 20:
                    score = None
                else:
                    p75 = quantile_type7(sorted(pce_history), 0.75)
                    score = 3 if delta > p75 else (2 if delta > 0 else (-3 if abs(delta) > p75 else -2))
            else:
                score = None

        if s is not None and abs(s) > 1e-6:
            pce_history.append(abs(s))

        cohort_tags = []
        if score == 3: cohort_tags.append("Core PCE (+3)")
        if score == -3: cohort_tags.append("Core PCE (-3)")

        is_eligible = len(cohort_tags) > 0
        direction = -1 if score == 3 else (1 if score == -3 else 0)
        direction_label = "SHORT" if score == 3 else ("LONG" if score == -3 else "—")

        rel_bar_ts = ts - (ts % 3600)
        rel_idx = ts_to_idx.get(rel_bar_ts)
        entry_ts = ts if ts % 3600 == 0 else ts + (3600 - ts % 3600)
        c_idx = ts_to_idx.get(entry_ts)
        raw_path, path, is_trunc, avail_h = compute_price_paths(entry_ts, direction)

        is_strong_pos = (score == 3)
        is_strong_neg = (score == -3)
        disposition = f"QUALIFIED ({direction_label})" if is_eligible else ("SCORED_NON_EXTREME" if score is not None else "UNSCORED_EARLY_HISTORY")

        episodes.append({
            "episode_id": f"US_PCE_{ts}",
            "family": "US inflation",
            "event_name": "USD Core PCE m/m",
            "timestamp": ts,
            "timestamp_server_text": server_text,
            "year": year,
            "is_pre2023": is_pre2023,
            "components": [{
                "series_id": "USD:US:840010001:r0",
                "name": "USD Core PCE m/m",
                "actual": a, "forecast": f, "previous": p,
                "surprise": s, "momentum": m,
                "unit": "%", "score": score, "score_is_exploratory": score_expl
            }],
            "cohort_tags": cohort_tags,
            "is_eligible": is_eligible,
            "direction": direction,
            "direction_label": direction_label,
            "disposition": disposition,
            "entry_timestamp": entry_ts,
            "release_candle_index": rel_idx,
            "candle_index": c_idx,
            "raw_price_path": raw_path,
            "price_path": path,
            "is_truncated": is_trunc,
            "available_horizons": avail_h,
            "is_strong_positive": is_strong_pos,
            "is_strong_negative": is_strong_neg
        })

    # -------------------------------------------------------------
    # B. US LABOR: Nonfarm Payrolls
    # -------------------------------------------------------------
    nfp_releases = raw_by_series["USD:US:840030016:r0"]
    nfp_history = []
    for r in nfp_releases:
        ts = int(r["timestamp"])
        server_text = r["timestamp_server_text"]
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        is_pre2023 = (ts < SPLIT_TIMESTAMP)

        arch = p1_archived.get(("USD:US:840030016:r0", ts))
        if is_pre2023 and arch:
            a, f, p = arch["actual"], arch["forecast"], arch["previous"]
            s = arch["surpriseDelta"]
            m = arch["momentumDelta"]
            score = arch["surpriseScore"]
            score_expl = False
        else:
            a = float(r["actual"]) if r["actual"] != "" else None
            f = float(r["forecast"]) if r["forecast"] != "" else None
            p = float(r["previous"]) if r["previous"] != "" else None
            s = int(a - f) if (a is not None and f is not None) else None
            m = int(a - p) if (a is not None and p is not None) else None
            score_expl = not is_pre2023
            if a is not None and f is not None and p is not None:
                delta = a - f
                if abs(delta) <= 1e-6:
                    score = 1 if len(nfp_history) >= 20 else None
                elif len(nfp_history) < 20:
                    score = None
                else:
                    p75 = quantile_type7(sorted(nfp_history), 0.75)
                    score = 3 if delta > p75 else (2 if delta > 0 else (-3 if abs(delta) > p75 else -2))
            else:
                score = None

        if s is not None and abs(s) > 1e-6:
            nfp_history.append(abs(s))

        cohort_tags = []
        if score == 3: cohort_tags.append("NFP (+3)")
        if score == -3: cohort_tags.append("NFP (-3)")

        is_eligible = len(cohort_tags) > 0
        direction = -1 if score == 3 else (1 if score == -3 else 0)
        direction_label = "SHORT" if score == 3 else ("LONG" if score == -3 else "—")

        rel_bar_ts = ts - (ts % 3600)
        rel_idx = ts_to_idx.get(rel_bar_ts)
        entry_ts = ts if ts % 3600 == 0 else ts + (3600 - ts % 3600)
        c_idx = ts_to_idx.get(entry_ts)
        raw_path, path, is_trunc, avail_h = compute_price_paths(entry_ts, direction)

        is_strong_pos = (score == 3)
        is_strong_neg = (score == -3)
        disposition = f"QUALIFIED ({direction_label})" if is_eligible else ("SCORED_NON_EXTREME" if score is not None else "UNSCORED_EARLY_HISTORY")

        episodes.append({
            "episode_id": f"US_NFP_{ts}",
            "family": "US labor",
            "event_name": "USD Nonfarm Payrolls",
            "timestamp": ts,
            "timestamp_server_text": server_text,
            "year": year,
            "is_pre2023": is_pre2023,
            "components": [{
                "series_id": "USD:US:840030016:r0",
                "name": "USD Nonfarm Payrolls",
                "actual": a, "forecast": f, "previous": p,
                "surprise": s, "momentum": m,
                "unit": "k", "score": score, "score_is_exploratory": score_expl
            }],
            "cohort_tags": cohort_tags,
            "is_eligible": is_eligible,
            "direction": direction,
            "direction_label": direction_label,
            "disposition": disposition,
            "entry_timestamp": entry_ts,
            "release_candle_index": rel_idx,
            "candle_index": c_idx,
            "raw_price_path": raw_path,
            "price_path": path,
            "is_truncated": is_trunc,
            "available_horizons": avail_h,
            "is_strong_positive": is_strong_pos,
            "is_strong_negative": is_strong_neg
        })

    # -------------------------------------------------------------
    # C. GERMAN IFO: Climate + Expectations (ONE Co-Release Episode)
    # -------------------------------------------------------------
    ifo_c_rels = {int(r["timestamp"]): r for r in raw_by_series["EUR:DE:276030003:r0"]}
    ifo_e_rels = {int(r["timestamp"]): r for r in raw_by_series["EUR:DE:276030001:r0"]}
    all_ifo_ts = sorted(list(set(list(ifo_c_rels.keys()) + list(ifo_e_rels.keys()))))

    for ts in all_ifo_ts:
        c_row = ifo_c_rels.get(ts)
        e_row = ifo_e_rels.get(ts)
        server_text = c_row["timestamp_server_text"] if c_row else (e_row["timestamp_server_text"] if e_row else "")
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        is_pre2023 = (ts < SPLIT_TIMESTAMP)

        c_a = float(c_row["actual"]) if c_row and c_row["actual"] != "" else None
        c_f = float(c_row["forecast"]) if c_row and c_row["forecast"] != "" else None
        c_p = float(c_row["previous"]) if c_row and c_row["previous"] != "" else None
        c_s = round(c_a - c_f, 1) if (c_a is not None and c_f is not None) else None
        c_m = round(c_a - c_p, 1) if (c_a is not None and c_p is not None) else None

        e_a = float(e_row["actual"]) if e_row and e_row["actual"] != "" else None
        e_f = float(e_row["forecast"]) if e_row and e_row["forecast"] != "" else None
        e_p = float(e_row["previous"]) if e_row and e_row["previous"] != "" else None
        e_s = round(e_a - e_f, 1) if (e_a is not None and e_f is not None) else None
        e_m = round(e_a - e_p, 1) if (e_a is not None and e_p is not None) else None

        components = [
            {"series_id": "EUR:DE:276030003:r0", "name": "Ifo Business Climate", "actual": c_a, "forecast": c_f, "previous": c_p, "surprise": c_s, "momentum": c_m, "unit": "pts", "score": None, "score_is_exploratory": False},
            {"series_id": "EUR:DE:276030001:r0", "name": "Ifo Business Expectations", "actual": e_a, "forecast": e_f, "previous": e_p, "surprise": e_s, "momentum": e_m, "unit": "pts", "score": None, "score_is_exploratory": False}
        ]

        if is_pre2023:
            arch_act = ifo_actionable.get(ts)
            arch_pkg = ifo_all_packages.get(ts)
            if arch_act:
                is_eligible = True
                direction = 1 if arch_act["actionableDirection"] == "LONG" else -1
                direction_label = arch_act["actionableDirection"]
                entry_ts = arch_act["pairCoverage"]["entryTimestamp"]
                disposition = "ACTIONABLE_STRICT_AGREEMENT"
            else:
                is_eligible = False
                direction = 0
                direction_label = "—"
                rem = ts % 14400
                entry_ts = ts + (14400 if rem == 0 else (14400 - rem))
                disposition = arch_pkg["disposition"] if arch_pkg else "NOT_ELIGIBLE"
        else:
            if c_f is None or e_f is None or c_a is None or e_a is None:
                disposition = "MISSING_CONSENSUS"
                is_eligible = False
                direction = 0
                direction_label = "—"
            elif c_s > 0 and e_s > 0:
                disposition = "STRICT_AGREEMENT (LONG)"
                is_eligible = True
                direction = 1
                direction_label = "LONG"
            elif c_s < 0 and e_s < 0:
                disposition = "STRICT_AGREEMENT (SHORT)"
                is_eligible = True
                direction = -1
                direction_label = "SHORT"
            elif (c_s > 0 and e_s < 0) or (c_s < 0 and e_s > 0):
                disposition = "CONFLICTING_EXPECTATIONS"
                is_eligible = False
                direction = 0
                direction_label = "—"
            else:
                disposition = "ZERO_SURPRISE"
                is_eligible = False
                direction = 0
                direction_label = "—"

            rem = ts % 14400
            entry_ts = ts + (14400 if rem == 0 else (14400 - rem))

        cohort_tags = ["German Ifo (Climate + Expectations)"] if is_eligible else []
        rel_bar_ts = ts - (ts % 3600)
        rel_idx = ts_to_idx.get(rel_bar_ts)
        c_idx = ts_to_idx.get(entry_ts)
        raw_path, path, is_trunc, avail_h = compute_price_paths(entry_ts, direction)

        is_strong_pos = (c_s > 0 and e_s > 0) if (c_s is not None and e_s is not None) else False
        is_strong_neg = (c_s < 0 and e_s < 0) if (c_s is not None and e_s is not None) else False

        episodes.append({
            "episode_id": f"DE_IFO_{ts}",
            "family": "German Ifo",
            "event_name": "German Ifo (Climate & Expectations)",
            "timestamp": ts,
            "timestamp_server_text": server_text,
            "year": year,
            "is_pre2023": is_pre2023,
            "components": components,
            "cohort_tags": cohort_tags,
            "is_eligible": is_eligible,
            "direction": direction,
            "direction_label": direction_label,
            "disposition": disposition,
            "entry_timestamp": entry_ts,
            "release_candle_index": rel_idx,
            "candle_index": c_idx,
            "raw_price_path": raw_path,
            "price_path": path,
            "is_truncated": is_trunc,
            "available_horizons": avail_h,
            "is_strong_positive": is_strong_pos,
            "is_strong_negative": is_strong_neg
        })

    # -------------------------------------------------------------
    # D. US RETAIL SALES: Headline + Core (ONE Co-Release Episode)
    # -------------------------------------------------------------
    rs_h_rels = {int(r["timestamp"]): r for r in raw_by_series["USD:US:840020010:r0"]}
    rs_c_rels = {int(r["timestamp"]): r for r in raw_by_series["USD:US:840020011:r0"]}
    all_rs_ts = sorted(list(set(list(rs_h_rels.keys()) + list(rs_c_rels.keys()))))

    for ts in all_rs_ts:
        h_row = rs_h_rels.get(ts)
        c_row = rs_c_rels.get(ts)
        server_text = h_row["timestamp_server_text"] if h_row else (c_row["timestamp_server_text"] if c_row else "")
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        is_pre2023 = (ts < SPLIT_TIMESTAMP)

        h_a = float(h_row["actual"]) if h_row and h_row["actual"] != "" else None
        h_f = float(h_row["forecast"]) if h_row and h_row["forecast"] != "" else None
        h_p = float(h_row["previous"]) if h_row and h_row["previous"] != "" else None
        h_s = round(h_a - h_f, 1) if (h_a is not None and h_f is not None) else None
        h_m = round(h_a - h_p, 1) if (h_a is not None and h_p is not None) else None

        c_a = float(c_row["actual"]) if c_row and c_row["actual"] != "" else None
        c_f = float(c_row["forecast"]) if c_row and c_row["forecast"] != "" else None
        c_p = float(c_row["previous"]) if c_row and c_row["previous"] != "" else None
        c_s = round(c_a - c_f, 1) if (c_a is not None and c_f is not None) else None
        c_m = round(c_a - c_p, 1) if (c_a is not None and c_p is not None) else None

        components = [
            {"series_id": "USD:US:840020010:r0", "name": "Retail Sales m/m", "actual": h_a, "forecast": h_f, "previous": h_p, "surprise": h_s, "momentum": h_m, "unit": "%", "score": None, "score_is_exploratory": False},
            {"series_id": "USD:US:840020011:r0", "name": "Core Retail Sales m/m", "actual": c_a, "forecast": c_f, "previous": c_p, "surprise": c_s, "momentum": c_m, "unit": "%", "score": None, "score_is_exploratory": False}
        ]

        if is_pre2023:
            arch_ep = rs_trade_episodes.get(ts)
            if arch_ep:
                is_eligible = True
                direction = arch_ep["direction"]
                direction_label = arch_ep["direction_label"]
                entry_ts = arch_ep["entry_timestamp"]
                disposition = arch_ep["sign_category"]
            else:
                is_eligible = False
                direction = 0
                direction_label = "—"
                rem = ts % 14400
                entry_ts = ts + (14400 if rem == 0 else (14400 - rem))
                if h_f is None or c_f is None: disposition = "MISSING_FORECAST"
                elif (h_s > 0 and c_s < 0) or (h_s < 0 and c_s > 0): disposition = "ACTIVE_CONFLICT"
                elif h_s == 0 and c_s == 0: disposition = "BOTH_ZERO"
                else: disposition = "ONE_ZERO"
        else:
            if h_f is None or c_f is None or h_a is None or c_a is None:
                disposition = "MISSING_FORECAST"
                is_eligible = False
                direction = 0
                direction_label = "—"
            elif h_s > 0 and c_s > 0:
                disposition = "STRICT_AGREE_POS (SHORT EURUSD)"
                is_eligible = True
                direction = -1
                direction_label = "SHORT"
            elif h_s < 0 and c_s < 0:
                disposition = "STRICT_AGREE_NEG (LONG EURUSD)"
                is_eligible = True
                direction = 1
                direction_label = "LONG"
            elif (h_s > 0 and c_s < 0) or (h_s < 0 and c_s > 0):
                disposition = "ACTIVE_CONFLICT"
                is_eligible = False
                direction = 0
                direction_label = "—"
            elif h_s == 0 and c_s == 0:
                disposition = "BOTH_ZERO"
                is_eligible = False
                direction = 0
                direction_label = "—"
            else:
                disposition = "ONE_ZERO"
                is_eligible = False
                direction = 0
                direction_label = "—"

            rem = ts % 14400
            entry_ts = ts + (14400 if rem == 0 else (14400 - rem))

        cohort_tags = ["US Retail Sales (Headline + Core)"] if is_eligible else []
        rel_bar_ts = ts - (ts % 3600)
        rel_idx = ts_to_idx.get(rel_bar_ts)
        c_idx = ts_to_idx.get(entry_ts)
        raw_path, path, is_trunc, avail_h = compute_price_paths(entry_ts, direction)

        is_strong_pos = (h_s > 0 and c_s > 0) if (h_s is not None and c_s is not None) else False
        is_strong_neg = (h_s < 0 and c_s < 0) if (h_s is not None and c_s is not None) else False

        episodes.append({
            "episode_id": f"US_RS_{ts}",
            "family": "US Retail Sales",
            "event_name": "US Retail Sales (Headline & Core)",
            "timestamp": ts,
            "timestamp_server_text": server_text,
            "year": year,
            "is_pre2023": is_pre2023,
            "components": components,
            "cohort_tags": cohort_tags,
            "is_eligible": is_eligible,
            "direction": direction,
            "direction_label": direction_label,
            "disposition": disposition,
            "entry_timestamp": entry_ts,
            "release_candle_index": rel_idx,
            "candle_index": c_idx,
            "raw_price_path": raw_path,
            "price_path": path,
            "is_truncated": is_trunc,
            "available_horizons": avail_h,
            "is_strong_positive": is_strong_pos,
            "is_strong_negative": is_strong_neg
        })

    # -------------------------------------------------------------
    # E. US ISM MANUFACTURING PMI: Headline Release (Descriptive Exploration)
    # -------------------------------------------------------------
    ism_releases = raw_by_series["USD:US:840040001:r0"]
    for r in ism_releases:
        ts = int(r["timestamp"])
        server_text = r["timestamp_server_text"]
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        is_pre2023 = (ts < SPLIT_TIMESTAMP)

        a = float(r["actual"]) if r["actual"] != "" else None
        f = float(r["forecast"]) if r["forecast"] != "" else None
        p = float(r["previous"]) if r["previous"] != "" else None
        s = round(a - f, 1) if (a is not None and f is not None) else None
        m = round(a - p, 1) if (a is not None and p is not None) else None

        if a is None or f is None or p is None:
            disposition = "MISSING_FORECAST"
            is_eligible = False
            direction = 0
            direction_label = "—"
        elif s > 0:
            disposition = "POSITIVE_SURPRISE (SHORT EURUSD)"
            is_eligible = True
            direction = -1
            direction_label = "SHORT"
        elif s < 0:
            disposition = "NEGATIVE_SURPRISE (LONG EURUSD)"
            is_eligible = True
            direction = 1
            direction_label = "LONG"
        else:
            disposition = "ZERO_SURPRISE"
            is_eligible = False
            direction = 0
            direction_label = "—"

        # Protocol temporal delay: T_entry = T_release + 3600 (18:00 server time)
        entry_ts = ts + 3600
        cohort_tags = ["ISM Manufacturing PMI (Headline)"] if is_eligible else []
        rel_bar_ts = ts - (ts % 3600)
        rel_idx = ts_to_idx.get(rel_bar_ts)
        c_idx = ts_to_idx.get(entry_ts)
        raw_path, path, is_trunc, avail_h = compute_price_paths(entry_ts, direction)

        is_strong_pos = (s > 0) if s is not None else False
        is_strong_neg = (s < 0) if s is not None else False

        episodes.append({
            "episode_id": f"US_ISM_{ts}",
            "family": "US ISM Manufacturing PMI",
            "event_name": "ISM Manufacturing PMI",
            "timestamp": ts,
            "timestamp_server_text": server_text,
            "year": year,
            "is_pre2023": is_pre2023,
            "components": [{
                "series_id": "USD:US:840040001:r0",
                "name": "ISM Manufacturing PMI",
                "actual": a, "forecast": f, "previous": p,
                "surprise": s, "momentum": m,
                "unit": "pts", "score": None, "score_is_exploratory": False
            }],
            "cohort_tags": cohort_tags,
            "is_eligible": is_eligible,
            "direction": direction,
            "direction_label": direction_label,
            "disposition": disposition,
            "entry_timestamp": entry_ts,
            "release_candle_index": rel_idx,
            "candle_index": c_idx,
            "raw_price_path": raw_path,
            "price_path": path,
            "is_truncated": is_trunc,
            "available_horizons": avail_h,
            "is_strong_positive": is_strong_pos,
            "is_strong_negative": is_strong_neg
        })

    episodes.sort(key=lambda ep: ep["timestamp"])

    metadata = {
        "export_date": "2026-09-23",
        "total_candles": total_candles,
        "earliest_candle_ts": candles[0][0],
        "latest_candle_ts": candles[-1][0],
        "total_distinct_episodes": len(episodes),
        "total_raw_calendar_rows": sum(len(raw_by_series[s]) for s in raw_by_series)
    }

    return episodes, metadata


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EURUSD H1 Macro-Event Price & Release Atlas (2015–2026)</title>
  <style>
    :root {
      --bg: #0b1120;
      --card-bg: #1e293b;
      --card-sub: #131d31;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --pos: #22c55e;
      --pos-bg: rgba(34, 197, 94, 0.15);
      --pos-text: #4ade80;
      --neg: #ef4444;
      --neg-bg: rgba(239, 68, 68, 0.15);
      --neg-text: #f87171;
      --neutral-bg: #1e293b;
      --neutral-text: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.45;
      padding: 16px 20px;
    }
    header { margin-bottom: 14px; }
    h1 {
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .badge-static {
      font-size: 0.6875rem;
      background: #334155;
      color: #38bdf8;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
    }
    .badge-holdout-forfeit {
      font-size: 0.6875rem;
      background: rgba(239, 68, 68, 0.2);
      color: #fca5a5;
      border: 1px solid rgba(239, 68, 68, 0.4);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
    }
    .subtitle { color: var(--text-muted); font-size: 0.8125rem; margin-top: 3px; }
    .notice-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-left: 4px solid var(--accent);
      border-radius: 6px;
      padding: 10px 14px;
      margin-bottom: 14px;
      font-size: 0.78125rem;
      color: var(--text-muted);
    }
    .notice-box strong { color: var(--text); }
    .notice-box ul { margin: 4px 0 0 16px; }
    .notice-box li { margin-bottom: 2px; }
    .controls-bar {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 14px;
      flex-wrap: wrap;
      background: var(--card-sub);
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--border);
    }
    .control-group { display: flex; align-items: center; gap: 6px; }
    label { font-size: 0.8125rem; font-weight: 600; color: var(--text); }
    select {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 5px 10px;
      border-radius: 5px;
      font-size: 0.8125rem;
      outline: none;
      cursor: pointer;
    }
    select:focus { border-color: var(--accent); }
    .metrics-banner {
      display: flex;
      gap: 12px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }
    .metric-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 6px 12px;
      flex: 1;
      min-width: 140px;
    }
    .metric-card .label {
      font-size: 0.65625rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
    }
    .metric-card .value {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text);
      margin-top: 2px;
      font-variant-numeric: tabular-nums;
    }
    .metric-card .subtext { font-size: 0.65625rem; color: var(--text-muted); }
    .chart-container-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px 14px;
      margin-bottom: 16px;
    }
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      flex-wrap: wrap;
      gap: 8px;
    }
    .chart-title { font-size: 0.9375rem; font-weight: 700; color: var(--accent); }
    .chart-info { font-size: 0.75rem; color: var(--text-muted); }
    .canvas-wrapper {
      position: relative;
      width: 100%;
      height: 380px;
      background: #070d17;
      border: 1px solid var(--border);
      border-radius: 4px;
      overflow: hidden;
    }
    canvas { display: block; width: 100%; height: 100%; }
    .chart-tooltip {
      position: absolute;
      display: none;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid var(--accent);
      border-radius: 4px;
      padding: 6px 10px;
      font-size: 0.6875rem;
      pointer-events: none;
      z-index: 100;
      color: #fff;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
      line-height: 1.35;
    }
    .section-title {
      font-size: 0.875rem;
      font-weight: 700;
      margin: 16px 0 6px 0;
      color: var(--accent);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .table-container {
      width: 100%;
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--card-bg);
      margin-bottom: 14px;
    }
    table {
      border-collapse: separate;
      border-spacing: 0;
      width: max-content;
      font-size: 0.71875rem;
      font-variant-numeric: tabular-nums;
    }
    th, td {
      padding: 5px 8px;
      text-align: right;
      border-bottom: 1px solid var(--border);
      border-right: 1px solid var(--border);
      white-space: nowrap;
    }
    th {
      background: #1e293b;
      font-weight: 600;
      color: var(--text-muted);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    th.col-sticky, td.col-sticky { position: sticky; left: 0; z-index: 20; background: #1e293b; text-align: left; }
    th.col-sticky-2, td.col-sticky-2 { position: sticky; left: 110px; z-index: 20; background: #1e293b; text-align: left; }
    th.col-sticky-3, td.col-sticky-3 { position: sticky; left: 320px; z-index: 20; background: #1e293b; text-align: center; }
    th.col-sticky-4, td.col-sticky-4 { position: sticky; left: 410px; z-index: 20; background: #1e293b; text-align: center; border-right: 2px solid var(--accent); }
    thead tr th.col-sticky, thead tr th.col-sticky-2, thead tr th.col-sticky-3, thead tr th.col-sticky-4 { z-index: 30; }
    tr:hover td { filter: brightness(1.15); }
    .cell-pos { background: var(--pos-bg); color: var(--pos-text); font-weight: 500; }
    .cell-neg { background: var(--neg-bg); color: var(--neg-text); font-weight: 500; }
    .cell-zero { background: var(--neutral-bg); color: var(--neutral-text); }
    .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.65625rem; font-weight: 600; }
    .badge-short { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }
    .badge-long { background: rgba(34, 197, 94, 0.2); color: #86efac; }
    .badge-var { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; }
    .btn-select {
      background: #334155;
      color: #fff;
      border: 1px solid var(--border);
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 0.65625rem;
      cursor: pointer;
    }
    .btn-select:hover { background: #475569; border-color: var(--accent); }
    .btn-active { background: var(--accent) !important; color: #0b1120 !important; font-weight: 700; }
    .component-chip {
      display: inline-block;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 3px;
      padding: 1px 5px;
      margin: 1px 2px;
      font-size: 0.65625rem;
    }
    footer {
      margin-top: 16px;
      color: var(--text-muted);
      font-size: 0.71875rem;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 10px;
    }
  </style>
</head>
<body>

  <header>
    <h1>
      EURUSD H1 Macro-Event Price & Release Atlas
      <span class="badge-static">STATIC SNAPSHOT: 2026-09-23 (2026 is partial)</span>
      <span class="badge-holdout-forfeit">FULL-HISTORY EXPLORATION (2023–2026 UNBLINDED)</span>
    </h1>
    <p class="subtitle">Complete pinned EURUSD H1 candlestick atlas (2015–2026) across 825 distinct event releases and 1,260 calendar components</p>
  </header>

  <div class="notice-box">
    <strong>Owner's Scope Decision & Scientific Boundary Governance:</strong>
    <ul>
      <li><strong>Holdout Forfeiture Warning:</strong> In accordance with the Owner's scope decision, 2023–2026 price concealment has been removed for this exploratory atlas. <em>Once these prices are inspected, 2023–2026 cannot later be claimed as an untouched historical holdout for rules selected with this viewer.</em> Future demo data will provide the fresh forward test.</li>
      <li><strong>Accounting Integrity:</strong> Simultaneous co-releases (German Ifo Climate + Expectations; Retail Sales Headline + Core) form <strong>ONE distinct event episode</strong> and contribute exactly <strong>ONE price path</strong> to statistics (40 Ifo episodes, not 80; 49 Retail Sales episodes, not 98).</li>
      <li><strong>Descriptive Displacement Only:</strong> Cell values reflect gross close-to-entry directional displacement (%). This is <strong>NOT</strong> a win rate, TP-before-SL probability, or net profit. Zero spreads, commissions, or slippage are deducted.</li>
      <li><strong>US ISM Manufacturing PMI:</strong> Evaluated strictly as descriptive exploration, <strong>NOT</strong> as an approved trading rule.</li>
      <li><strong>Candlestick Representation:</strong> Releases inside an H1 bar are drawn with the containing bar identified; exact within-candle tick execution is not faked. All times are broker-server time.</li>
    </ul>
  </div>

  <div class="controls-bar">
    <div class="control-group">
      <label for="familyFilter">Family:</label>
      <select id="familyFilter" onchange="onFilterChange()">
        <option value="ALL">All Families</option>
        <option value="US inflation">US inflation</option>
        <option value="US labor">US labor</option>
        <option value="German Ifo">German Ifo</option>
        <option value="US Retail Sales">US Retail Sales</option>
        <option value="US ISM Manufacturing PMI">US ISM Manufacturing PMI</option>
      </select>
    </div>

    <div class="control-group">
      <label for="yearFilter">Year:</label>
      <select id="yearFilter" onchange="onFilterChange()">
        <option value="ALL">All Years (2015–2026)</option>
        <option value="2015">2015</option>
        <option value="2016">2016</option>
        <option value="2017">2017</option>
        <option value="2018">2018</option>
        <option value="2019">2019</option>
        <option value="2020">2020</option>
        <option value="2021">2021</option>
        <option value="2022">2022</option>
        <option value="2023">2023</option>
        <option value="2024">2024</option>
        <option value="2025">2025</option>
        <option value="2026">2026 (partial snapshot)</option>
      </select>
    </div>

    <div class="control-group">
      <label for="cohortFilter">Cohort / Status:</label>
      <select id="cohortFilter" onchange="onFilterChange()">
        <option value="ALL">All Episodes / Dispositions</option>
        <option value="ELIGIBLE">Eligible / Actionable Cohorts Only</option>
        <option value="PLUS3">Score +3 / Strong Positive Surprise</option>
        <option value="MINUS3">Score -3 / Strong Negative Surprise</option>
        <option value="SCORED">All Scored Episodes (Scores ±1, ±2, ±3)</option>
        <option value="NEUTRAL">Neutral / Score-Null / Excluded</option>
      </select>
    </div>

    <div class="control-group" style="flex: 1; min-width: 280px;">
      <label for="episodeSelect">Selected Release:</label>
      <select id="episodeSelect" style="width: 100%;" onchange="onEpisodeSelectChange()">
        <!-- Injected dynamically -->
      </select>
    </div>
  </div>

  <div class="metrics-banner" id="metricsBanner"></div>

  <!-- Candlestick Chart Card -->
  <div class="chart-container-card">
    <div class="chart-header">
      <span class="chart-title" id="chartEpisodeTitle">Individual H1 Candlestick Trajectory (Loading...)</span>
      <span class="chart-info" id="chartEpisodeInfo"></span>
    </div>
    <div class="canvas-wrapper" id="canvasWrapper">
      <canvas id="candleCanvas"></canvas>
      <div class="chart-tooltip" id="chartTooltip"></div>
    </div>
  </div>

  <!-- Summary Table -->
  <div class="section-title">
    <span>1. H1–H60 Response Profile Summary (Recalculated from Underlying Distinct Episodes)</span>
    <span id="summaryCohortCount" style="font-size: 0.71875rem; color: var(--text-muted); font-weight: normal;"></span>
  </div>

  <div class="table-container">
    <table id="summaryTable">
      <thead>
        <tr id="summaryHeaderRow">
          <th class="col-sticky">Family</th>
          <th class="col-sticky-2">Cohort</th>
          <th class="col-sticky-3">Direction</th>
          <th class="col-sticky-4">Eligible N</th>
          <!-- H1 - H60 columns injected dynamically -->
        </tr>
      </thead>
      <tbody id="summaryTableBody"></tbody>
    </table>
  </div>

  <!-- Event Ledger Table -->
  <div class="section-title">
    <span>2. Macroeconomic Event Release Ledger (Selected Filter)</span>
    <span id="ledgerCount" style="font-size: 0.71875rem; color: var(--text-muted); font-weight: normal;"></span>
  </div>

  <div class="table-container" style="max-height: 480px; overflow-y: auto;">
    <table id="ledgerTable" style="width: 100%;">
      <thead>
        <tr>
          <th style="text-align: left;">Server Date/Time</th>
          <th style="text-align: left;">Event / Family</th>
          <th style="text-align: left;">Calendar Components (A / F / P / S / M)</th>
          <th style="text-align: left;">Disposition / Status</th>
          <th>Direction</th>
          <th>Entry Time</th>
          <th>Available H</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="ledgerTableBody"></tbody>
    </table>
  </div>

  <footer>
    <span>Data Source: Pinned Elev8 MT5 Server Export (<code>calendar_releases.csv</code>, <code>candles_EURUSD_H1.csv</code>)</span>
    <span>Generated by <code>TABLE VIEWER/generate_table.py</code> | Offline Candlestick Atlas</span>
  </footer>

  <script>
    const PAYLOAD = __DATA_JSON__;
    const CANDLES = PAYLOAD.candles;
    const EPISODES = PAYLOAD.episodes;
    const COHORTS = PAYLOAD.cohorts;

    let selectedEpisode = null;

    function initSummaryHeaders() {
      const headerRow = document.getElementById("summaryHeaderRow");
      for (let h = 1; h <= 60; h++) {
        const th = document.createElement("th");
        th.textContent = "H" + h;
        th.title = "Horizon H" + h + " (Close of active H1 bar " + h + " post-entry)";
        headerRow.appendChild(th);
      }
    }

    function computeMedian(arr) {
      if (!arr || arr.length === 0) return null;
      const sorted = [...arr].sort((a, b) => a - b);
      const mid = Math.floor(sorted.length / 2);
      return sorted.length % 2 === 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2.0;
    }

    function computeMean(arr) {
      if (!arr || arr.length === 0) return null;
      return arr.reduce((a, b) => a + b, 0) / arr.length;
    }

    function onFilterChange() {
      const fam = document.getElementById("familyFilter").value;
      const yr = document.getElementById("yearFilter").value;
      const coh = document.getElementById("cohortFilter").value;

      const filtered = EPISODES.filter(ep => {
        if (fam !== "ALL" && ep.family !== fam) return false;
        if (yr !== "ALL" && ep.year !== parseInt(yr)) return false;
        if (coh === "ELIGIBLE" && !ep.is_eligible) return false;
        if (coh === "PLUS3" && !ep.is_strong_positive) return false;
        if (coh === "MINUS3" && !ep.is_strong_negative) return false;
        if (coh === "SCORED" && (!ep.components.some(c => c.score !== null))) return false;
        if (coh === "NEUTRAL" && ep.is_eligible) return false;
        return true;
      });

      updateMetricsBanner(filtered);
      renderSummaryTable(filtered, fam);
      populateEpisodeDropdown(filtered);
      renderLedgerTable(filtered);

      if (filtered.length > 0) {
        if (!selectedEpisode || !filtered.some(ep => ep.episode_id === selectedEpisode.episode_id)) {
          selectEpisode(filtered[0]);
        } else {
          drawChart();
        }
      } else {
        selectedEpisode = null;
        clearChart();
      }
    }

    function populateEpisodeDropdown(filtered) {
      const select = document.getElementById("episodeSelect");
      select.innerHTML = "";
      filtered.forEach(ep => {
        const opt = document.createElement("option");
        opt.value = ep.episode_id;
        const dir = ep.direction_label !== "—" ? ` [${ep.direction_label}]` : "";
        opt.textContent = `${ep.timestamp_server_text} - ${ep.event_name}${dir}`;
        if (selectedEpisode && ep.episode_id === selectedEpisode.episode_id) opt.selected = true;
        select.appendChild(opt);
      });
    }

    function onEpisodeSelectChange() {
      const epId = document.getElementById("episodeSelect").value;
      const found = EPISODES.find(ep => ep.episode_id === epId);
      if (found) selectEpisode(found);
    }

    function selectEpisode(ep) {
      selectedEpisode = ep;
      document.getElementById("episodeSelect").value = ep.episode_id;
      document.getElementById("chartEpisodeTitle").textContent = `${ep.event_name} (${ep.timestamp_server_text})`;
      document.getElementById("chartEpisodeInfo").textContent = `Direction: ${ep.direction_label} | Disposition: ${ep.disposition} | Available: ${ep.available_horizons}/60 H1 bars`;
      drawChart();

      // Highlight active button in ledger
      document.querySelectorAll(".btn-select").forEach(b => b.classList.remove("btn-active"));
      const btn = document.getElementById("btn-select-" + ep.episode_id);
      if (btn) btn.classList.add("btn-active");
    }

    function updateMetricsBanner(filtered) {
      const banner = document.getElementById("metricsBanner");
      const distinctTs = new Set(filtered.map(ep => ep.timestamp)).size;
      const totalEpisodes = filtered.length;
      const eligibleEpisodes = filtered.filter(ep => ep.is_eligible).length;
      const totalRawRows = filtered.reduce((acc, ep) => acc + ep.components.length, 0);

      const posCount = filtered.filter(ep => ep.direction === -1).length;
      const negCount = filtered.filter(ep => ep.direction === 1).length;

      banner.innerHTML = `
        <div class="metric-card">
          <div class="label">Distinct Release Times</div>
          <div class="value">${distinctTs}</div>
          <div class="subtext">Simultaneous releases = 1 time</div>
        </div>
        <div class="metric-card">
          <div class="label">Distinct Event Episodes</div>
          <div class="value" style="color: var(--accent);">${totalEpisodes}</div>
          <div class="subtext">1 co-release = 1 episode</div>
        </div>
        <div class="metric-card">
          <div class="label">Raw Calendar Rows</div>
          <div class="value">${totalRawRows}</div>
          <div class="subtext">Underlying indicator components</div>
        </div>
        <div class="metric-card">
          <div class="label">Eligible Cohort Episodes</div>
          <div class="value" style="color: #4ade80;">${eligibleEpisodes}</div>
          <div class="subtext">Met actionable rule criteria</div>
        </div>
        <div class="metric-card">
          <div class="label">Directional Breakdown</div>
          <div class="value" style="font-size: 1rem; margin-top: 4px;">
            <span style="color: #f87171;">Short: ${posCount}</span> | 
            <span style="color: #4ade80;">Long: ${negCount}</span>
          </div>
          <div class="subtext">Neutral / Ineligible: ${totalEpisodes - (posCount + negCount)}</div>
        </div>
      `;
    }

    function renderSummaryTable(filtered, famFilter) {
      const tbody = document.getElementById("summaryTableBody");
      tbody.innerHTML = "";

      const activeCohorts = COHORTS.filter(c => famFilter === "ALL" || c.family === famFilter);
      document.getElementById("summaryCohortCount").textContent = "Showing " + activeCohorts.length + " cohorts";

      activeCohorts.forEach(cohort => {
        const tr = document.createElement("tr");

        // Sticky columns
        const tdFam = document.createElement("td");
        tdFam.className = "col-sticky";
        tdFam.textContent = cohort.family;
        tr.appendChild(tdFam);

        const tdName = document.createElement("td");
        tdName.className = "col-sticky-2";
        tdName.innerHTML = "<strong>" + cohort.cohort_name + "</strong>";
        tr.appendChild(tdName);

        const tdDir = document.createElement("td");
        tdDir.className = "col-sticky-3";
        let badgeClass = "badge-var";
        if (cohort.proposed_direction === "SHORT") badgeClass = "badge-short";
        else if (cohort.proposed_direction === "LONG") badgeClass = "badge-long";
        tdDir.innerHTML = `<span class="badge ${badgeClass}">${cohort.proposed_direction}</span>`;
        tr.appendChild(tdDir);

        // Find distinct eligible episodes matching this cohort tag
        const cohortEpisodes = filtered.filter(ep => ep.is_eligible && ep.cohort_tags.includes(cohort.cohort_name) && (ep.price_path !== null || ep.raw_price_path !== null));
        const tdN = document.createElement("td");
        tdN.className = "col-sticky-4";
        tdN.textContent = cohortEpisodes.length;
        tr.appendChild(tdN);

        if (cohortEpisodes.length === 0) {
          for (let h = 1; h <= 60; h++) {
            const td = document.createElement("td");
            td.textContent = "—";
            td.className = "cell-zero";
            tr.appendChild(td);
          }
        } else {
          // Recompute median dynamically for each horizon from underlying distinct episodes
          for (let h = 0; h < 60; h++) {
            const td = document.createElement("td");
            const hNum = h + 1;
            const values = cohortEpisodes
              .map(ep => {
                if (ep.price_path !== null && ep.direction !== 0) return ep.price_path[h];
                if (ep.raw_price_path !== null && ep.raw_price_path[h] !== null) {
                  let dir = 0;
                  if (cohort.proposed_direction === "SHORT") dir = -1;
                  else if (cohort.proposed_direction === "LONG") dir = 1;
                  else dir = ep.direction;
                  return dir !== 0 ? Math.round(dir * ep.raw_price_path[h] * 10000) / 10000 : null;
                }
                return null;
              })
              .filter(v => v !== null && v !== undefined);

            if (values.length > 0) {
              const med = computeMedian(values);
              const mean = computeMean(values);
              const sign = med > 0 ? "+" : "";
              td.textContent = sign + med.toFixed(4) + "%";

              if (med > 0) td.className = "cell-pos";
              else if (med < 0) td.className = "cell-neg";
              else td.className = "cell-zero";

              td.title = `${cohort.cohort_name} | H${hNum}\\nMedian Directional Change: ${sign}${med.toFixed(4)}%\\nMean Directional Change: ${(mean > 0 ? "+" : "")}${mean.toFixed(4)}%\\nAvailable N: ${values.length}/${cohortEpisodes.length}`;
            } else {
              td.textContent = "—";
              td.className = "cell-zero";
              td.title = `Horizon H${hNum}: Path truncated near export cutoff`;
            }
            tr.appendChild(td);
          }
        }

        tbody.appendChild(tr);
      });
    }

    function renderLedgerTable(filtered) {
      const tbody = document.getElementById("ledgerTableBody");
      tbody.innerHTML = "";
      document.getElementById("ledgerCount").textContent = "Displaying " + filtered.length + " distinct event episodes";

      filtered.forEach(ep => {
        const tr = document.createElement("tr");

        // Date/Time
        const tdDt = document.createElement("td");
        tdDt.style.textAlign = "left";
        tdDt.textContent = ep.timestamp_server_text;
        tr.appendChild(tdDt);

        // Event / Family
        const tdEv = document.createElement("td");
        tdEv.style.textAlign = "left";
        tdEv.innerHTML = `<strong>${ep.event_name}</strong><br><span style="color: var(--text-muted); font-size: 0.65625rem;">${ep.family}</span>`;
        tr.appendChild(tdEv);

        // Components
        const tdComp = document.createElement("td");
        tdComp.style.textAlign = "left";
        let compHtml = "";
        ep.components.forEach(c => {
          const a = c.actual !== null ? c.actual : "—";
          const f = c.forecast !== null ? c.forecast : "—";
          const p = c.previous !== null ? c.previous : "—";
          const s = c.surprise !== null ? (c.surprise > 0 ? "+" : "") + c.surprise : "—";
          const sc = c.score !== null ? ` | Score: ${c.score > 0 ? "+" : ""}${c.score}` : "";
          compHtml += `<div class="component-chip"><strong>${c.name}:</strong> A:${a} F:${f} P:${p} S:${s}${sc} ${c.unit}</div><br>`;
        });
        tdComp.innerHTML = compHtml;
        tr.appendChild(tdComp);

        // Disposition
        const tdDisp = document.createElement("td");
        tdDisp.style.textAlign = "left";
        tdDisp.textContent = ep.disposition;
        tr.appendChild(tdDisp);

        // Direction
        const tdDir = document.createElement("td");
        tdDir.textContent = ep.direction_label;
        if (ep.direction_label === "SHORT") tdDir.style.color = "#fca5a5";
        else if (ep.direction_label === "LONG") tdDir.style.color = "#86efac";
        tr.appendChild(tdDir);

        // Entry Time
        const tdEntry = document.createElement("td");
        tdEntry.textContent = ep.entry_timestamp || "—";
        tr.appendChild(tdEntry);

        // Available H
        const tdAvail = document.createElement("td");
        tdAvail.textContent = `${ep.available_horizons}/60`;
        if (ep.is_truncated) tdAvail.style.color = "#fca5a5";
        tr.appendChild(tdAvail);

        // Action
        const tdAct = document.createElement("td");
        const btnClass = (selectedEpisode && ep.episode_id === selectedEpisode.episode_id) ? "btn-select btn-active" : "btn-select";
        tdAct.innerHTML = `<button class="${btnClass}" id="btn-select-${ep.episode_id}" onclick='selectEpisodeById("${ep.episode_id}")'>View Chart</button>`;
        tr.appendChild(tdAct);

        tbody.appendChild(tr);
      });
    }

    function selectEpisodeById(epId) {
      const ep = EPISODES.find(e => e.episode_id === epId);
      if (ep) {
        selectEpisode(ep);
        document.getElementById("canvasWrapper").scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }

    // -------------------------------------------------------------
    // Candlestick Canvas Renderer
    // -------------------------------------------------------------
    function clearChart() {
      const canvas = document.getElementById("candleCanvas");
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    function drawChart() {
      if (!selectedEpisode) return;

      const canvas = document.getElementById("candleCanvas");
      const wrapper = document.getElementById("canvasWrapper");
      const width = wrapper.clientWidth;
      const height = wrapper.clientHeight;
      const dpr = window.devicePixelRatio || 1;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      const ctx = canvas.getContext("2d");
      ctx.scale(dpr, dpr);

      const ep = selectedEpisode;
      const relTs = ep.timestamp;

      // Find release candle index
      const relIdx = (ep.release_candle_index !== undefined && ep.release_candle_index !== null)
        ? ep.release_candle_index
        : Math.max(0, CANDLES.findIndex(c => c[0] >= (ep.timestamp - (ep.timestamp % 3600))));
      const preBarsCount = 12;
      const startIdx = Math.max(0, relIdx - preBarsCount);
      const entryIdx = (ep.candle_index !== undefined && ep.candle_index !== null)
        ? ep.candle_index
        : (relIdx + 1);
      const endIdx = Math.min(CANDLES.length - 1, entryIdx + 59);

      const chartCandles = [];
      for (let i = startIdx; i <= endIdx; i++) {
        const c = CANDLES[i];
        let label = "";
        let isRelBar = (i === relIdx);
        let isEntryBar = (i === entryIdx);

        if (i < relIdx) label = `Pre-${relIdx - i}`;
        else if (i === relIdx) label = "Release";
        else if (i > relIdx && i < entryIdx) label = `Rel+${i - relIdx}`;
        else if (i >= entryIdx) label = `H${i - entryIdx + 1}`;

        chartCandles.push({
          idx: i,
          ts: c[0],
          o: c[1], h: c[2], l: c[3], c: c[4],
          label: label,
          isReleaseBar: isRelBar,
          isEntryBar: isEntryBar
        });
      }

      if (chartCandles.length === 0) return;

      // Price extents
      let minP = Math.min(...chartCandles.map(c => c.l));
      let maxP = Math.max(...chartCandles.map(c => c.h));
      const pad = (maxP - minP) * 0.08 || 0.0010;
      minP -= pad;
      maxP += pad;

      const chartArea = { left: 10, right: width - 75, top: 25, bottom: height - 35 };
      const plotW = chartArea.right - chartArea.left;
      const plotH = chartArea.bottom - chartArea.top;

      const nBars = chartCandles.length;
      const barW = Math.max(3, Math.min(14, (plotW / nBars) * 0.75));
      const stepX = plotW / nBars;

      function getY(p) { return chartArea.bottom - ((p - minP) / (maxP - minP)) * plotH; }
      function getX(i) { return chartArea.left + i * stepX + stepX / 2; }

      // Draw background grid lines
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      const nGrid = 6;
      for (let g = 0; g <= nGrid; g++) {
        const p = minP + (g / nGrid) * (maxP - minP);
        const y = getY(p);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.stroke();

        ctx.fillStyle = "#64748b";
        ctx.font = "9px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(p.toFixed(5), chartArea.right + 6, y + 3);
      }

      // Draw Entry Open Reference Line
      if (entryIdx < CANDLES.length) {
        const entryOpen = CANDLES[entryIdx][1];
        const entryY = getY(entryOpen);
        ctx.strokeStyle = "#38bdf8";
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(chartArea.left, entryY);
        ctx.lineTo(chartArea.right, entryY);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold 9px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(`Entry Open: ${entryOpen.toFixed(5)}`, chartArea.left + 6, entryY - 4);
      }

      // Draw Candlesticks & Highlights
      chartCandles.forEach((bar, i) => {
        const x = getX(i);
        const yO = getY(bar.o);
        const yC = getY(bar.c);
        const yH = getY(bar.h);
        const yL = getY(bar.l);

        // Highlight Release-Containing Bar
        if (bar.isReleaseBar) {
          ctx.fillStyle = "rgba(56, 189, 248, 0.12)";
          ctx.fillRect(x - stepX / 2, chartArea.top, stepX, plotH);

          ctx.strokeStyle = "#38bdf8";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(x, chartArea.top);
          ctx.lineTo(x, chartArea.bottom);
          ctx.stroke();

          ctx.fillStyle = "#38bdf8";
          ctx.font = "bold 9px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText("Release", x, chartArea.top - 6);
        }

        // Highlight H1 Entry Bar
        if (bar.isEntryBar) {
          ctx.fillStyle = "rgba(34, 197, 94, 0.12)";
          ctx.fillRect(x - stepX / 2, chartArea.top, stepX, plotH);

          ctx.fillStyle = "#86efac";
          ctx.font = "bold 9px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText("H1", x, chartArea.top - 6);
        }

        // Weekend Market Closure separator
        if (i > 0 && (bar.ts - chartCandles[i - 1].ts) > 3600) {
          ctx.strokeStyle = "#475569";
          ctx.setLineDash([2, 3]);
          ctx.beginPath();
          ctx.moveTo(x - stepX / 2, chartArea.top);
          ctx.lineTo(x - stepX / 2, chartArea.bottom);
          ctx.stroke();
          ctx.setLineDash([]);
        }

        // Candle Wick
        const isBull = bar.c >= bar.o;
        ctx.strokeStyle = isBull ? "#22c55e" : "#ef4444";
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, yH);
        ctx.lineTo(x, yL);
        ctx.stroke();

        // Candle Body
        ctx.fillStyle = isBull ? "#22c55e" : "#ef4444";
        const topBody = Math.min(yO, yC);
        const bodyH = Math.max(1.5, Math.abs(yC - yO));
        ctx.fillRect(x - barW / 2, topBody, barW, bodyH);

        // Horizon labels on X-axis (every 6th bar + H1 + Release)
        if (bar.isReleaseBar || bar.isEntryBar || (bar.label.startsWith("H") && parseInt(bar.label.slice(1)) % 6 === 0)) {
          ctx.fillStyle = bar.isEntryBar ? "#86efac" : (bar.isReleaseBar ? "#38bdf8" : "#94a3b8");
          ctx.font = "8px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(bar.label, x, chartArea.bottom + 12);
        }
      });

      // Mouse Hover Crosshair & Tooltip
      canvas.onmousemove = function(e) {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const tooltip = document.getElementById("chartTooltip");

        if (mouseX >= chartArea.left && mouseX <= chartArea.right && mouseY >= chartArea.top && mouseY <= chartArea.bottom) {
          const hoveredIdx = Math.floor((mouseX - chartArea.left) / stepX);
          if (hoveredIdx >= 0 && hoveredIdx < chartCandles.length) {
            const bar = chartCandles[hoveredIdx];
            const d = new Date(bar.ts * 1000).toISOString().replace("T", " ").slice(0, 19);
            const entryOpen = (entryIdx < CANDLES.length) ? CANDLES[entryIdx][1] : bar.o;
            const diffPct = ((bar.c - entryOpen) / entryOpen) * 100.0;
            const dirPct = ep.direction !== 0 ? ep.direction * diffPct : diffPct;

            const relNote = bar.isReleaseBar ? "<br><span style='color: #38bdf8;'>* Release occurred within this H1 bar (exact execution tick unknown)</span>" : "";
            tooltip.style.display = "block";
            tooltip.style.left = (e.clientX - rect.left + 15) + "px";
            tooltip.style.top = (e.clientY - rect.top - 20) + "px";
            tooltip.innerHTML = `
              <strong>${bar.label} (${d})</strong><br>
              O: ${bar.o.toFixed(5)}  H: ${bar.h.toFixed(5)}<br>
              L: ${bar.l.toFixed(5)}  C: ${bar.c.toFixed(5)}<br>
              Directional: ${(dirPct > 0 ? "+" : "")}${dirPct.toFixed(4)}%${relNote}
            `;
          }
        } else {
          tooltip.style.display = "none";
        }
      };

      canvas.onmouseleave = function() {
        document.getElementById("chartTooltip").style.display = "none";
      };
    }

    window.addEventListener("resize", () => { if (selectedEpisode) drawChart(); });

    // Initial load
    initSummaryHeaders();
    onFilterChange();
  </script>
</body>
</html>
"""


def generate_html_viewer(
    episodes: List[Dict[str, Any]],
    candles: List[List[Any]],
    output_filepath: str = OUTPUT_HTML_PATH
) -> str:
    """Renders standalone offline HTML viewer embedding all candles and distinct episodes."""
    cohort_definitions = [
        {"family": "US inflation", "cohort_name": "Headline CPI (+3)", "series_id": "USD:US:840030005:r0", "proposed_direction": "SHORT"},
        {"family": "US inflation", "cohort_name": "Headline CPI (-3)", "series_id": "USD:US:840030005:r0", "proposed_direction": "LONG"},
        {"family": "US inflation", "cohort_name": "Core CPI (+3)", "series_id": "USD:US:840030006:r0", "proposed_direction": "SHORT"},
        {"family": "US inflation", "cohort_name": "Core CPI (-3)", "series_id": "USD:US:840030006:r0", "proposed_direction": "LONG"},
        {"family": "US inflation", "cohort_name": "Core PCE (+3)", "series_id": "USD:US:840010001:r0", "proposed_direction": "SHORT"},
        {"family": "US inflation", "cohort_name": "Core PCE (-3)", "series_id": "USD:US:840010001:r0", "proposed_direction": "LONG"},
        {"family": "US labor", "cohort_name": "NFP (+3)", "series_id": "USD:US:840030016:r0", "proposed_direction": "SHORT"},
        {"family": "US labor", "cohort_name": "NFP (-3)", "series_id": "USD:US:840030016:r0", "proposed_direction": "LONG"},
        {"family": "German Ifo", "cohort_name": "German Ifo (Climate + Expectations)", "series_id": "EUR:DE:276030003:r0 + 276030001:r0", "proposed_direction": "VARIABLE"},
        {"family": "US Retail Sales", "cohort_name": "US Retail Sales (Headline + Core)", "series_id": "USD:US:840020010:r0 + 840020011:r0", "proposed_direction": "VARIABLE"},
        {"family": "US ISM Manufacturing PMI", "cohort_name": "ISM Manufacturing PMI (Headline)", "series_id": "USD:US:840040001:r0", "proposed_direction": "VARIABLE"}
    ]

    payload = {
        "export_date": "2026-09-23",
        "cohorts": cohort_definitions,
        "candles": candles,
        "episodes": episodes
    }

    data_json = json.dumps(payload, separators=(',', ':'))
    html_content = HTML_TEMPLATE.replace("__DATA_JSON__", data_json)

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_filepath


def main():
    print(f"Loading full EURUSD H1 candle series from {CANDLE_PATH}...")
    candles, ts_to_idx = load_all_candles()
    print(f"Loaded {len(candles)} candles. Timestamp range: {candles[0][0]} to {candles[-1][0]}.")

    print(f"Building distinct event episodes across 2015–2026 from {CALENDAR_PATH}...")
    episodes, meta = build_event_episodes(candles=candles, ts_to_idx=ts_to_idx)
    print(f"Built {len(episodes)} distinct event episodes across {meta['total_raw_calendar_rows']} raw calendar rows.")

    print(f"Generating full-history offline HTML viewer at {OUTPUT_HTML_PATH}...")
    generate_html_viewer(episodes, candles, OUTPUT_HTML_PATH)
    print("Done! Viewer generated successfully.")

    # Yearly accounting breakdown
    print("\n" + "=" * 95)
    print(f"{'Year':6} | {'Distinct Episodes':18} | {'Raw Calendar Rows':18} | {'Eligible Episodes':18} | Notes")
    print("-" * 95)
    for yr in range(2015, 2027):
        yr_eps = [e for e in episodes if e["year"] == yr]
        raw_rows = sum(len(e["components"]) for e in yr_eps)
        elig = sum(1 for e in yr_eps if e["is_eligible"])
        note = "Pre-2023 Historical Period" if yr < 2023 else ("Unblinded Exploratory Period" if yr < 2026 else "Partial Snapshot (to 2026-09-23)")
        print(f"{yr:6d} | {len(yr_eps):18d} | {raw_rows:18d} | {elig:18d} | {note}")
    print("=" * 95)


if __name__ == "__main__":
    main()
