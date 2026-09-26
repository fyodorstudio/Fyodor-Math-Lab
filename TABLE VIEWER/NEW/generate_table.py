"""
Macroeconomic Event Displacement Table Generator (Light Mode - Numerical Correctness Baseline)
Generates an auditable, light-mode HTML table viewer in TABLE VIEWER/NEW/table_viewer.html.

Numerical Governance & Strict Logic:
1. BASE GOOD = GREEN vs QUOTE GOOD = GREEN viewing choices:
   - BASE mode: signed pips = (Hn close - entry open) / pip size.
   - QUOTE mode: signed pips = -(Hn close - entry open) / pip size.
   - Color is a pure price-direction viewing choice; zero automatic macro-bias multiplication.
2. Distinct N Accounting:
   - Calendar Episodes matching family/year.
   - Episodes with Complete A/F/P for every component.
   - Episodes with an Available Price Path for the selected pair.
   - Median Population choice: "Complete A/F/P only" (default) vs "All priced releases".
   - Median ignores missing values ('--'), never treats them as zero, and reports exact horizon-specific N.
3. 2019-04-29 15:30 Core PCE Preservation:
   - Both Core PCE records (March 2019 and February 2019 periods) are preserved and stacked with period labels.
   - Remains exactly ONE release-time episode (2019 Inflation N=23).
4. Rigorous Distinction of Calendar Rows, Family Episodes (839), and Distinct Timestamps (825 with 14 cross-family collisions: 12 Inflation + Retail, 2 Labor + Retail).
"""

import csv
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CANDLES_DIR = os.path.join(BASE_DIR, "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server", "candles")
CALENDAR_PATH = os.path.join(BASE_DIR, "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server", "calendar_releases.csv")
OUTPUT_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "table_viewer.html")

# The 19 full-history FX pairs
PAIRS = [
    "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "EURGBP", "EURAUD", "EURCAD", "EURCHF", "EURNZD",
    "AUDJPY", "CHFJPY", "GBPCHF", "AUDCAD", "AUDCHF", "AUDNZD"
]

# Pair descriptions & Base / Quote classification
PAIR_METADATA = {
    "EURUSD": {"desc": "EUR/USD (Base: EUR, Quote: USD)", "base": "EUR", "quote": "USD", "pip": 0.00010, "digits": 5},
    "USDJPY": {"desc": "USD/JPY (Base: USD, Quote: JPY)", "base": "USD", "quote": "JPY", "pip": 0.010, "digits": 3},
    "GBPUSD": {"desc": "GBP/USD (Base: GBP, Quote: USD)", "base": "GBP", "quote": "USD", "pip": 0.00010, "digits": 5},
    "AUDUSD": {"desc": "AUD/USD (Base: AUD, Quote: USD)", "base": "AUD", "quote": "USD", "pip": 0.00010, "digits": 5},
    "USDCAD": {"desc": "USD/CAD (Base: USD, Quote: CAD)", "base": "USD", "quote": "CAD", "pip": 0.00010, "digits": 5},
    "USDCHF": {"desc": "USD/CHF (Base: USD, Quote: CHF)", "base": "USD", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "NZDUSD": {"desc": "NZD/USD (Base: NZD, Quote: USD)", "base": "NZD", "quote": "USD", "pip": 0.00010, "digits": 5},
    "EURJPY": {"desc": "EUR/JPY (Base: EUR, Quote: JPY)", "base": "EUR", "quote": "JPY", "pip": 0.010, "digits": 3},
    "EURGBP": {"desc": "EUR/GBP (Base: EUR, Quote: GBP)", "base": "EUR", "quote": "GBP", "pip": 0.00010, "digits": 5},
    "EURAUD": {"desc": "EUR/AUD (Base: EUR, Quote: AUD)", "base": "EUR", "quote": "AUD", "pip": 0.00010, "digits": 5},
    "EURCAD": {"desc": "EUR/CAD (Base: EUR, Quote: CAD)", "base": "EUR", "quote": "CAD", "pip": 0.00010, "digits": 5},
    "EURCHF": {"desc": "EUR/CHF (Base: EUR, Quote: CHF)", "base": "EUR", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "EURNZD": {"desc": "EUR/NZD (Base: EUR, Quote: NZD)", "base": "EUR", "quote": "NZD", "pip": 0.00010, "digits": 5},
    "AUDJPY": {"desc": "AUD/JPY (Base: AUD, Quote: JPY)", "base": "AUD", "quote": "JPY", "pip": 0.010, "digits": 3},
    "CHFJPY": {"desc": "CHF/JPY (Base: CHF, Quote: JPY)", "base": "CHF", "quote": "JPY", "pip": 0.010, "digits": 3},
    "GBPCHF": {"desc": "GBP/CHF (Base: GBP, Quote: CHF)", "base": "GBP", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "AUDCAD": {"desc": "AUD/CAD (Base: AUD, Quote: CAD)", "base": "AUD", "quote": "CAD", "pip": 0.00010, "digits": 5},
    "AUDCHF": {"desc": "AUD/CHF (Base: AUD, Quote: CHF)", "base": "AUD", "quote": "CHF", "pip": 0.00010, "digits": 5},
    "AUDNZD": {"desc": "AUD/NZD (Base: AUD, Quote: NZD)", "base": "AUD", "quote": "NZD", "pip": 0.00010, "digits": 5}
}

EVENT_FAMILIES = {
    "US_INFLATION": {
        "label": "US INFLATION",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840030005", "840030006", "840010001"]  # CPI, Core CPI, Core PCE
    },
    "US_LABOR": {
        "label": "US LABOR",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840030016"]  # Nonfarm Payrolls
    },
    "US_RETAIL_SALES": {
        "label": "US RETAIL SALES",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840020010", "840020011"]  # Retail Sales m/m, Core Retail Sales m/m
    },
    "GERMAN_IFO": {
        "label": "GERMAN IFO",
        "affected": "EUR pairs: EURUSD, EURGBP, EURJPY, EURAUD, EURCAD, EURCHF, EURNZD",
        "series": ["276030003", "276030001"]  # Ifo Climate, Expectations
    },
    "US_ISM_PMI": {
        "label": "US ISM PMI",
        "affected": "USD pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD",
        "series": ["840040001"]  # ISM Mfg PMI
    }
}

SERIES_NAMES = {
    "840030005": {"name": "USD CPI m/m", "unit": "%", "digits": 1},
    "840030006": {"name": "USD Core CPI m/m", "unit": "%", "digits": 1},
    "840010001": {"name": "USD Core PCE m/m", "unit": "%", "digits": 1},
    "840030016": {"name": "USD Nonfarm Payrolls", "unit": "k", "digits": 0},
    "840020010": {"name": "Retail Sales m/m", "unit": "%", "digits": 1},
    "840020011": {"name": "Core Retail Sales m/m", "unit": "%", "digits": 1},
    "276030003": {"name": "Ifo Business Climate", "unit": "pts", "digits": 1},
    "276030001": {"name": "Ifo Business Expectations", "unit": "pts", "digits": 1},
    "840040001": {"name": "ISM Manufacturing PMI", "unit": "pts", "digits": 1}
}


def load_candles():
    """Loads all specified FX pairs into indexed lookup structures."""
    print(f"Loading candle files for {len(PAIRS)} pairs...")
    t0 = time.time()
    candles_db = {}
    for pair in PAIRS:
        csv_file = os.path.join(CANDLES_DIR, f"candles_{pair}_H1.csv")
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


def parse_calendar_episodes():
    """
    Parses raw calendar releases and groups them into distinct (family, timestamp) episodes.
    Preserves multiple component records for the same event_id (e.g. 2019-04-29 Core PCE).
    Distinguishes:
    - 839 total family episodes across the 5 families.
    - 825 distinct timestamps across all 5 families (14 coincident timestamps: 12 Inflation + Retail, 2 Labor + Retail).
    - 634 complete A/F/P episodes.
    """
    print("Ingesting calendar releases...")
    all_target_eids = set()
    eid_to_fam = {}
    for fam_key, fam_info in EVENT_FAMILIES.items():
        for eid in fam_info["series"]:
            all_target_eids.add(eid)
            eid_to_fam[eid] = fam_key

    # Group raw records strictly by (family, timestamp)
    fam_ts_rows = defaultdict(list)
    with open(CALENDAR_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["revision"] != "0":
                continue
            eid = r["event_id"]
            if eid in all_target_eids:
                fam_key = eid_to_fam[eid]
                ts = int(r["timestamp"])
                fam_ts_rows[(fam_key, ts)].append(r)

    # Identify all cross-family coincident timestamps across the 5 families
    ts_fams = defaultdict(set)
    for (f_k, t_s) in fam_ts_rows.keys():
        ts_fams[t_s].add(f_k)
    shared_ts_set = set(t_s for t_s, fams in ts_fams.items() if len(fams) > 1)

    episodes = []

    for (fam_key, ts), rows in sorted(fam_ts_rows.items(), key=lambda item: (item[0][0], item[0][1])):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        year = dt.year
        dt_str = dt.strftime("%Y.%m.%d %H:%M")

        # Entry timestamp: start of the next active H1 candle bar
        entry_ts = ts if ts % 3600 == 0 else ts + (3600 - ts % 3600)

        # Check completeness of A/F/P for all components in this episode
        is_complete_afp = True
        for r in rows:
            a = r["actual"].strip()
            f_val = r["forecast"].strip()
            p = r["previous"].strip()
            if not a or not f_val or not p:
                is_complete_afp = False
                break

        # Check if multiple records share the same event_id (e.g. 2019-04-29 Core PCE)
        eid_counts = defaultdict(int)
        for r in rows:
            eid_counts[r["event_id"]] += 1

        # Sort rows deterministically: by series order in family, then by period descending
        series_order = {eid: idx for idx, eid in enumerate(EVENT_FAMILIES[fam_key]["series"])}
        rows.sort(key=lambda r: (series_order.get(r["event_id"], 99), -int(r.get("period", 0) or 0)))

        # CPI response condition classification (strictly for US_INFLATION)
        # Requires headline CPI (840030005) and core CPI (840030006) both present with non-empty A and F
        # Excludes Core PCE (840010001); does not use previous/momentum/price movement
        cpi_group = None
        if fam_key == "US_INFLATION":
            row_head = next((r for r in rows if r["event_id"] == "840030005"), None)
            row_core = next((r for r in rows if r["event_id"] == "840030006"), None)
            if row_head and row_core:
                a_h = row_head["actual"].strip()
                f_h = row_head["forecast"].strip()
                a_c = row_core["actual"].strip()
                f_c = row_core["forecast"].strip()
                if a_h and f_h and a_c and f_c:
                    s_h = round(float(a_h) - float(f_h), 4)
                    s_c = round(float(a_c) - float(f_c), 4)
                    if s_h > 0 and s_c > 0:
                        cpi_group = "BOTH_ABOVE"
                    elif s_h < 0 and s_c < 0:
                        cpi_group = "BOTH_BELOW"
                    else:
                        cpi_group = "MIXED_ZERO"

        is_shared_timestamp = (ts in shared_ts_set)

        indicators = []
        for r in rows:
            eid = r["event_id"]
            meta = SERIES_NAMES[eid]
            name = meta["name"]
            # If multiple records share the same event_id, append period identifier
            if eid_counts[eid] > 1:
                period_text = r.get("period_server_text", "")
                if period_text:
                    period_label = period_text[:7].replace(".", "-")  # e.g. 2019-03
                    name = f"{meta['name']} ({period_label})"
                else:
                    name = f"{meta['name']} [id:{r.get('value_id', '')}]"

            a_str = r["actual"].strip()
            f_str = r["forecast"].strip()
            p_str = r["previous"].strip()

            a = float(a_str) if a_str else None
            f_val = float(f_str) if f_str else None
            p = float(p_str) if p_str else None

            s = round(a - f_val, meta["digits"]) if (a is not None and f_val is not None) else None
            m = round(a - p, meta["digits"]) if (a is not None and p is not None) else None

            indicators.append({
                "name": name,
                "actual": f"{a:.{meta['digits']}f}" if a is not None else "--",
                "forecast": f"{f_val:.{meta['digits']}f}" if f_val is not None else "--",
                "previous": f"{p:.{meta['digits']}f}" if p is not None else "--",
                "surprise": f"{s:+.{meta['digits']}f}" if s is not None else "--",
                "momentum": f"{m:+.{meta['digits']}f}" if m is not None else "--",
                "unit": meta["unit"],
                "raw_s": s,
                "raw_m": m
            })

        episodes.append({
            "ts": ts,
            "entry_ts": entry_ts,
            "dt_str": dt_str,
            "year": year,
            "family": fam_key,
            "is_complete_afp": is_complete_afp,
            "is_shared_timestamp": is_shared_timestamp,
            "cpi_group": cpi_group,
            "indicators": indicators
        })

    print(f"Constructed {len(episodes)} family episodes (expected 839).")
    return episodes


def compute_pips_for_episodes(episodes, candles_db):
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
                        # Raw BASE pip displacement: (Close - Open) / pip_size
                        diff_pips = round((close_p - entry_open) / pip_size, 1)
                        pips.append(diff_pips)
                    else:
                        pips.append(None)
                pair_pips[pair] = pips
            else:
                pair_pips[pair] = None

        ep["pips"] = pair_pips

    print(f"Computed displacements in {time.time() - t0:.2f}s")
    return episodes


def build_html(episodes_data):
    """Generates the clean Light Mode standalone HTML table viewer."""
    print("Generating HTML table viewer...")

    # Compact JSON data
    data_json = json.dumps({
        "pairs": PAIRS,
        "pair_meta": PAIR_METADATA,
        "families": EVENT_FAMILIES,
        "episodes": episodes_data
    })

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Macroeconomic Event Displacement Table Viewer</title>
<style>
  /* --- Reset & Base Typography --- */
  *, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    background-color: #f8fafc;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    line-height: 1.4;
    padding: 24px;
    min-width: 1200px;
  }}

  /* --- Top Header Card --- */
  .header-card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
  }}

  .header-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 14px;
    margin-bottom: 18px;
  }}

  .title-group h1 {{
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.02em;
  }}

  .title-group p {{
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
  }}

  .view-controls-right {{
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  .mode-toggle-group {{
    display: flex;
    align-items: center;
    gap: 4px;
    background: #f1f5f9;
    padding: 3px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
  }}

  .mode-btn {{
    background: none;
    border: none;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 700;
    color: #64748b;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}

  .mode-btn.active {{
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  }}

  /* --- Selectors Grid --- */
  .selectors-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: flex-end;
  }}

  .control-group {{
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 170px;
    flex: 1 1 180px;
  }}

  .reset-group {{
    flex: 0 0 auto;
  }}

  .control-group label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #475569;
  }}

  .control-select {{
    width: 100%;
    padding: 8px 12px;
    font-size: 13px;
    color: #0f172a;
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    outline: none;
    cursor: pointer;
    transition: border-color 0.15s ease;
  }}

  .control-select:focus {{
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }}

  .control-select:disabled {{
    background-color: #f1f5f9;
    color: #94a3b8;
    cursor: not-allowed;
  }}

  .reset-btn {{
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    color: #dc2626;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    height: 38px;
  }}

  .reset-btn:hover {{
    background: #fee2e2;
  }}

  /* --- Status / Accounting Banner --- */
  .status-banner {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 20px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
  }}

  .status-badges {{
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }}

  .badge {{
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }}

  .badge-primary {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}
  .badge-secondary {{ background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }}
  .badge-green {{ background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }}
  .badge-purple {{ background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }}
  .badge-amber {{ background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }}

  .accounting-note {{
    font-size: 11px;
    color: #64748b;
    margin-top: 4px;
  }}

  .legend {{
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 11px;
    color: #64748b;
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .legend-box {{
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid rgba(0,0,0,0.1);
  }}

  .box-green {{ background-color: #dcfce7; }}
  .box-red {{ background-color: #fee2e2; }}
  .box-gray {{ background-color: #f1f5f9; }}

  /* --- Empty State Prompt --- */
  .empty-state {{
    background: #ffffff;
    border: 2px dashed #cbd5e1;
    border-radius: 8px;
    padding: 60px 30px;
    text-align: center;
    margin-top: 10px;
  }}

  .empty-state h3 {{
    font-size: 16px;
    font-weight: 700;
    color: #334155;
    margin-bottom: 6px;
  }}

  .empty-state p {{
    font-size: 13px;
    color: #64748b;
    max-width: 480px;
    margin: 0 auto;
  }}

  /* --- Table Container & Styling --- */
  .table-outer {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    overflow: auto;
    max-height: calc(100vh - 250px);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }}

  table {{
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    text-align: right;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
  }}

  /* Sticky Headers */
  thead th {{
    position: sticky;
    top: 0;
    background: #f8fafc;
    color: #475569;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 10px 8px;
    border-bottom: 2px solid #cbd5e1;
    border-right: 1px solid #e2e8f0;
    z-index: 10;
    white-space: nowrap;
  }}

  tbody td {{
    padding: 6px 8px;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #f1f5f9;
    white-space: nowrap;
  }}

  tbody tr:hover {{
    filter: brightness(0.97);
  }}

  /* Sticky Left Columns */
  .sticky-col-1 {{
    position: sticky;
    left: 0;
    z-index: 5;
    background: #ffffff;
    text-align: center;
    width: 42px;
    min-width: 42px;
    font-weight: 600;
    color: #64748b;
    border-right: 1px solid #cbd5e1 !important;
  }}

  .sticky-col-2 {{
    position: sticky;
    left: 42px;
    z-index: 5;
    background: #ffffff;
    text-align: left;
    width: 130px;
    min-width: 130px;
    font-weight: 600;
    color: #0f172a;
    border-right: 1px solid #cbd5e1 !important;
  }}

  .sticky-col-3 {{
    position: sticky;
    left: 172px;
    z-index: 5;
    background: #ffffff;
    text-align: left;
    min-width: 220px;
    border-right: 1px solid #cbd5e1 !important;
  }}

  .sticky-col-afpsm {{
    position: sticky;
    z-index: 5;
    background: #ffffff;
    border-right: 1px solid #cbd5e1 !important;
  }}

  .sticky-col-4 {{ left: 392px; width: 65px; min-width: 65px; }} /* A */
  .sticky-col-5 {{ left: 457px; width: 65px; min-width: 65px; }} /* F */
  .sticky-col-6 {{ left: 522px; width: 65px; min-width: 65px; }} /* P */
  .sticky-col-7 {{ left: 587px; width: 65px; min-width: 65px; }} /* S */
  .sticky-col-8 {{ left: 652px; width: 65px; min-width: 65px; border-right: 2px solid #94a3b8 !important; }} /* M */

  /* Header sticky left priority */
  thead th.sticky-col-1, thead th.sticky-col-2, thead th.sticky-col-3,
  thead th.sticky-col-4, thead th.sticky-col-5, thead th.sticky-col-6,
  thead th.sticky-col-7, thead th.sticky-col-8 {{
    z-index: 20;
    background: #f1f5f9;
  }}

  /* Stacked components inside rows */
  .stacked-row {{
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}

  .stacked-line {{
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  /* Data Value Cells */
  .pip-cell {{
    min-width: 58px;
    font-weight: 500;
  }}

  .cell-pos {{
    background-color: #dcfce7;
    color: #15803d;
  }}

  .cell-neg {{
    background-color: #fee2e2;
    color: #b91c1c;
  }}

  .cell-zero {{
    background-color: #f1f5f9;
    color: #64748b;
  }}

  .cell-na {{
    background-color: #f8fafc;
    color: #94a3b8;
    text-align: center;
  }}

  /* Sticky Footer / Median & Conditioned Summary Rows */
  tfoot tr {{
    background: #f1f5f9;
  }}

  tfoot td {{
    position: sticky;
    bottom: 0;
    background: #f1f5f9;
    font-weight: 700;
    color: #0f172a;
    border-top: 1px solid #cbd5e1;
    border-bottom: none;
    z-index: 10;
  }}

  tfoot tr.foot-single-median td {{
    bottom: 0;
    border-top: 2px solid #94a3b8;
  }}

  tfoot tr.foot-cpi-p10 td {{
    bottom: 112px;
    border-top: 2px solid #94a3b8;
  }}
  tfoot tr.foot-cpi-p50 td {{
    bottom: 84px;
    border-top: 1px solid #cbd5e1;
  }}
  tfoot tr.foot-cpi-p90 td {{
    bottom: 56px;
    border-top: 1px solid #cbd5e1;
  }}
  tfoot tr.foot-cpi-pos td {{
    bottom: 28px;
    border-top: 1px solid #cbd5e1;
  }}
  tfoot tr.foot-cpi-n td {{
    bottom: 0;
    border-top: 1px solid #cbd5e1;
    border-bottom: 2px solid #94a3b8;
  }}

  tfoot td.sticky-col-1, tfoot td.sticky-col-2, tfoot td.sticky-col-3,
  tfoot td.sticky-col-4, tfoot td.sticky-col-5, tfoot td.sticky-col-6,
  tfoot td.sticky-col-7, tfoot td.sticky-col-8 {{
    z-index: 25;
    background: #e2e8f0;
  }}

  /* Methodology / Restrained Sample Note */
  .methodology-note {{
    margin-top: 14px;
    padding: 12px 18px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 11px;
    color: #334155;
    line-height: 1.5;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }}

  .methodology-note.small-n {{
    background: #fffbeb;
    border-color: #fde68a;
    color: #92400e;
  }}
</style>
</head>
<body>

<div class="header-card">
  <div class="header-top">
    <div class="title-group">
      <h1>Macroeconomic Event Displacement Table</h1>
      <p id="subTitleText">H1–H60 Signed Pip Displacements from Entry Open &bull; Base Good = Green</p>
    </div>
    <div class="view-controls-right">
      <div class="mode-toggle-group">
        <button id="btnModeBase" class="mode-btn active" title="BASE mode: signed pips = (Hn close - entry open) / pip size. Price up is positive (Green).">
          BASE GOOD = GREEN
        </button>
        <button id="btnModeQuote" class="mode-btn" title="QUOTE mode: signed pips = -(Hn close - entry open) / pip size. Price down is positive (Green).">
          QUOTE GOOD = GREEN
        </button>
      </div>
    </div>
  </div>

  <div class="selectors-grid">
    <!-- Pair Selector -->
    <div class="control-group">
      <label for="selPair">Currency Pair</label>
      <select id="selPair" class="control-select">
        <option value="">-- Select Pair --</option>
      </select>
    </div>

    <!-- Year Selector -->
    <div class="control-group">
      <label for="selYear">Release Year</label>
      <select id="selYear" class="control-select">
        <option value="">-- Select Year --</option>
        <option value="ALL">All Years (2015–2026)</option>
        <option value="2026">2026 (Partial to Sept 23)</option>
        <option value="2025">2025</option>
        <option value="2024">2024</option>
        <option value="2023">2023</option>
        <option value="2022">2022</option>
        <option value="2021">2021</option>
        <option value="2020">2020</option>
        <option value="2019">2019</option>
        <option value="2018">2018</option>
        <option value="2017">2017</option>
        <option value="2016">2016</option>
        <option value="2015">2015</option>
      </select>
    </div>

    <!-- Event Family Selector -->
    <div class="control-group">
      <label for="selFamily">Event Family</label>
      <select id="selFamily" class="control-select">
        <option value="">-- Select Event Family --</option>
      </select>
    </div>

    <!-- CPI Response Selector (EURUSD & US_INFLATION only) -->
    <div class="control-group" id="cpiResponseGroup">
      <label for="selCpiResponse">CPI Response (EURUSD Only)</label>
      <select id="selCpiResponse" class="control-select" disabled>
        <option value="ALL">All inflation episodes</option>
        <option value="BOTH_ABOVE">CPI, both above forecast (A−F &gt; 0)</option>
        <option value="BOTH_BELOW">CPI, both below forecast (A−F &lt; 0)</option>
        <option value="MIXED_ZERO">CPI, mixed or zero</option>
      </select>
      <span id="cpiSelectorInfo" style="font-size: 11px; font-weight: 600; color: #2563eb; margin-top: 3px; display: none;"></span>
    </div>

    <!-- Episode (N) Selector -->
    <div class="control-group">
      <label for="selEpisode">Episode Filter</label>
      <select id="selEpisode" class="control-select" disabled>
        <option value="ALL">Select filters first</option>
      </select>
    </div>

    <!-- Median Population Option -->
    <div class="control-group">
      <label for="selMedianPop">Median Basis</label>
      <select id="selMedianPop" class="control-select">
        <option value="COMPLETE_AFP">Complete A/F/P only (default)</option>
        <option value="ALL_PRICED">All priced releases (descriptive)</option>
      </select>
    </div>

    <!-- Reset -->
    <div class="reset-group">
      <button id="btnReset" class="reset-btn">Reset</button>
    </div>
  </div>
</div>

<!-- Status / Accounting Banner -->
<div id="statusBanner" class="status-banner" style="display: none;">
  <div>
    <div class="status-badges">
      <span id="badgePair" class="badge badge-primary">Pair</span>
      <span id="badgeFamily" class="badge badge-secondary">Family</span>
      <span id="badgeYear" class="badge badge-secondary">Year</span>
      <span id="badgeCalendarN" class="badge badge-purple">Calendar N = 0</span>
      <span id="badgeCompleteAfpN" class="badge badge-green">Complete A/F/P = 0</span>
      <span id="badgePricedN" class="badge badge-amber">Priced N = 0</span>
      <span id="badgeCpiCondition" class="badge badge-purple" style="display: none;"></span>
      <span id="badgeCpiSharedExcl" class="badge badge-secondary" style="display: none;"></span>
      <span id="badgeSmallNSample" class="badge badge-amber" style="display: none;">Small N (&lt;10)</span>
    </div>
    <div class="accounting-note">
      Pinned dataset: 839 family episodes across 825 distinct timestamps (14 cross-family collisions: 12 Inflation + Retail, 2 Labor + Retail). F = Forecast; -- = absent in the pinned source. All release rows remain visible.
    </div>
  </div>
  <div class="legend">
    <div class="legend-item">
      <span class="legend-box box-green"></span>
      <span id="legendGreenText">Positive (+Pips)</span>
    </div>
    <div class="legend-item">
      <span class="legend-box box-red"></span>
      <span id="legendRedText">Negative (-Pips)</span>
    </div>
    <div class="legend-item">
      <span class="legend-box box-gray"></span>
      <span>0.0 Neutral</span>
    </div>
    <div class="legend-item">
      <span style="font-weight:700; color:#94a3b8;">--</span>
      <span>Unpriced / Missing</span>
    </div>
  </div>
</div>

<!-- Empty State Display -->
<div id="emptyState" class="empty-state">
  <h3>Select Pair, Year, and Event Family Above</h3>
  <p>The table remains clean and hidden until all three selectors are chosen. Once selected, exact N accounting (Calendar, Complete A/F/P, Priced) and H1–H60 pip displacements will render immediately.</p>
</div>

<!-- Data Table Container -->
<div id="tableContainer" class="table-outer" style="display: none;">
  <table id="dataTable">
    <thead>
      <tr>
        <th class="sticky-col-1">#</th>
        <th class="sticky-col-2">Date / Time</th>
        <th class="sticky-col-3">Indicator(s)</th>
        <th class="sticky-col-afpsm sticky-col-4">A</th>
        <th class="sticky-col-afpsm sticky-col-5" title="F = Forecast; -- = absent in the pinned source.">F</th>
        <th class="sticky-col-afpsm sticky-col-6">P</th>
        <th class="sticky-col-afpsm sticky-col-7">S</th>
        <th class="sticky-col-afpsm sticky-col-8">M</th>
        <!-- H1..H60 headers will be dynamically inserted here -->
      </tr>
    </thead>
    <tbody id="tableBody">
      <!-- Data rows inserted here -->
    </tbody>
    <tfoot id="tableFoot">
      <!-- Median summary row inserted here -->
    </tfoot>
  </table>
</div>

<!-- Descriptive Methodology & Restrained Sample Note -->
<div id="cpiMethodologyNote" class="methodology-note" style="display: none;">
  <p id="cpiMethodologyText"></p>
</div>

<script>
  // Embedded dataset
  const DB = {data_json};

  let viewingMode = 'BASE'; // 'BASE' or 'QUOTE'
  let medianPopulation = 'COMPLETE_AFP'; // 'COMPLETE_AFP' or 'ALL_PRICED'

  // DOM Elements
  const selPair = document.getElementById('selPair');
  const selYear = document.getElementById('selYear');
  const selFamily = document.getElementById('selFamily');
  const selCpiResponse = document.getElementById('selCpiResponse');
  const cpiSelectorInfo = document.getElementById('cpiSelectorInfo');
  const selEpisode = document.getElementById('selEpisode');
  const selMedianPop = document.getElementById('selMedianPop');
  const btnReset = document.getElementById('btnReset');
  const btnModeBase = document.getElementById('btnModeBase');
  const btnModeQuote = document.getElementById('btnModeQuote');
  const subTitleText = document.getElementById('subTitleText');

  const statusBanner = document.getElementById('statusBanner');
  const badgePair = document.getElementById('badgePair');
  const badgeFamily = document.getElementById('badgeFamily');
  const badgeYear = document.getElementById('badgeYear');
  const badgeCalendarN = document.getElementById('badgeCalendarN');
  const badgeCompleteAfpN = document.getElementById('badgeCompleteAfpN');
  const badgePricedN = document.getElementById('badgePricedN');
  const badgeCpiCondition = document.getElementById('badgeCpiCondition');
  const badgeCpiSharedExcl = document.getElementById('badgeCpiSharedExcl');
  const badgeSmallNSample = document.getElementById('badgeSmallNSample');
  const legendGreenText = document.getElementById('legendGreenText');
  const legendRedText = document.getElementById('legendRedText');

  const emptyState = document.getElementById('emptyState');
  const tableContainer = document.getElementById('tableContainer');
  const dataTable = document.getElementById('dataTable');
  const tableBody = document.getElementById('tableBody');
  const tableFoot = document.getElementById('tableFoot');
  const cpiMethodologyNote = document.getElementById('cpiMethodologyNote');
  const cpiMethodologyText = document.getElementById('cpiMethodologyText');

  // Type-7 Linear Interpolation Percentile: pos = (n - 1) * p
  function computeType7Percentile(sortedVals, p) {{
    const n = sortedVals.length;
    if (n === 0) return null;
    if (n === 1) return sortedVals[0];
    const pos = (n - 1) * p;
    const k = Math.floor(pos);
    const d = pos - k;
    if (k >= n - 1) return sortedVals[n - 1];
    return sortedVals[k] + d * (sortedVals[k + 1] - sortedVals[k]);
  }}

  // Initialize Selectors
  function initSelectors() {{
    // 1. Populate Pairs
    DB.pairs.forEach(p => {{
      const meta = DB.pair_meta[p];
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = meta.desc;
      selPair.appendChild(opt);
    }});

    // 2. Populate Event Families with Affected Pairs Note
    Object.keys(DB.families).forEach(k => {{
      const fam = DB.families[k];
      const opt = document.createElement('option');
      opt.value = k;
      opt.textContent = fam.label + ' (' + fam.affected + ')';
      selFamily.appendChild(opt);
    }});

    // 3. Build H1..H60 header th elements once
    const headerRow = dataTable.querySelector('thead tr');
    for (let h = 1; h <= 60; h++) {{
      const th = document.createElement('th');
      th.className = 'pip-cell';
      th.textContent = 'H' + h;
      headerRow.appendChild(th);
    }}
  }}

  // Filter episodes based on selections
  function getFilteredEpisodes() {{
    const pair = selPair.value;
    const year = selYear.value;
    const family = selFamily.value;
    const cpiResp = selCpiResponse ? selCpiResponse.value : 'ALL';

    if (!pair || !year || !family) return [];

    const isConditionedCpi = (pair === 'EURUSD' && family === 'US_INFLATION' && cpiResp && cpiResp !== 'ALL');

    return DB.episodes.filter(ep => {{
      if (ep.family !== family) return false;
      if (year !== 'ALL' && ep.year !== parseInt(year, 10)) return false;
      if (isConditionedCpi) {{
        if (ep.is_shared_timestamp) return false; // Exclude cross-family collisions
        if (ep.cpi_group !== cpiResp) return false; // Match conditioned group
      }}
      return true;
    }});
  }}

  // Update Episode Selector options based on available filtered episodes
  function updateEpisodeSelector(filtered, pair) {{
    selEpisode.innerHTML = '';
    if (!filtered || filtered.length === 0) {{
      selEpisode.disabled = true;
      const opt = document.createElement('option');
      opt.value = 'ALL';
      opt.textContent = '0 Episodes Found';
      selEpisode.appendChild(opt);
      return;
    }}

    selEpisode.disabled = false;
    const pricedCount = filtered.filter(ep => ep.pips && ep.pips[pair] !== null).length;

    const allOpt = document.createElement('option');
    allOpt.value = 'ALL';
    allOpt.textContent = 'All Episodes (Calendar N=' + filtered.length + ', Priced N=' + pricedCount + ')';
    selEpisode.appendChild(allOpt);

    filtered.forEach((ep, idx) => {{
      const opt = document.createElement('option');
      opt.value = ep.ts;
      let label = (idx + 1) + '. ' + ep.dt_str;
      if (ep.indicators.length > 0) {{
        const indNames = ep.indicators.map(i => i.name).join(', ');
        label += ' — ' + indNames;
      }}
      if (!ep.pips || ep.pips[pair] === null) {{
        label += ' [No Price Data]';
      }}
      opt.textContent = label;
      selEpisode.appendChild(opt);
    }});
  }}

  // Compute signed pips based on BASE vs QUOTE mode
  // BASE mode: signed pips = (Hn close - entry open) / pip size = rawPip
  // QUOTE mode: signed pips = -(Hn close - entry open) / pip size = -rawPip
  function getSignedPips(rawPip, mode) {{
    if (rawPip === null || rawPip === undefined) return null;
    return mode === 'BASE' ? rawPip : -rawPip;
  }}

  // Render Table
  function render() {{
    const pair = selPair.value;
    const year = selYear.value;
    const family = selFamily.value;

    // Check if all primary filters are selected
    if (!pair || !year || !family) {{
      emptyState.style.display = 'block';
      statusBanner.style.display = 'none';
      tableContainer.style.display = 'none';
      selEpisode.disabled = true;
      selEpisode.innerHTML = '<option value="ALL">Select filters above first</option>';
      selCpiResponse.disabled = true;
      cpiSelectorInfo.style.display = 'none';
      cpiMethodologyNote.style.display = 'none';
      return;
    }}

    // Enable CPI Response selector strictly for EURUSD & US_INFLATION
    const isCpiApplicable = (pair === 'EURUSD' && family === 'US_INFLATION');
    if (isCpiApplicable) {{
      selCpiResponse.disabled = false;
    }} else {{
      selCpiResponse.disabled = true;
      selCpiResponse.value = 'ALL';
    }}

    const cpiResp = selCpiResponse.value;
    const isConditionedCpi = (isCpiApplicable && cpiResp !== 'ALL');

    const filtered = getFilteredEpisodes();
    if (filtered.length === 0) {{
      emptyState.style.display = 'block';
      emptyState.querySelector('h3').textContent = 'No Episodes Found';
      emptyState.querySelector('p').textContent = 'No macroeconomic releases were recorded for this combination in the pinned dataset.';
      statusBanner.style.display = 'none';
      tableContainer.style.display = 'none';
      selEpisode.disabled = true;
      selEpisode.innerHTML = '<option value="ALL">0 Episodes Found</option>';
      cpiMethodologyNote.style.display = 'none';
      return;
    }}

    emptyState.style.display = 'none';
    statusBanner.style.display = 'flex';
    tableContainer.style.display = 'block';

    const meta = DB.pair_meta[pair];
    const calendarN = filtered.length;
    const completeAfpN = filtered.filter(ep => ep.is_complete_afp).length;
    const pricedN = filtered.filter(ep => ep.pips && ep.pips[pair] !== null).length;

    // Update Status Banner
    badgePair.textContent = 'Pair: ' + pair + ' (' + meta.base + '/' + meta.quote + ')';
    badgeFamily.textContent = 'Family: ' + DB.families[family].label;
    badgeYear.textContent = 'Year: ' + (year === 'ALL' ? '2015–2026' : year);
    badgeCalendarN.textContent = 'Calendar Episodes: ' + calendarN;
    badgeCompleteAfpN.textContent = 'Complete A/F/P: ' + completeAfpN;
    badgePricedN.textContent = 'Priced (' + pair + '): ' + pricedN;

    if (viewingMode === 'BASE') {{
      subTitleText.textContent = 'H1–H60 Signed Pip Displacements &bull; BASE Mode (' + meta.base + ' Strength / Price Up = Green)';
      legendGreenText.textContent = meta.base + ' Good / Up (+Pips)';
      legendRedText.textContent = meta.base + ' Bad / Down (-Pips)';
    }} else {{
      subTitleText.textContent = 'H1–H60 Signed Pip Displacements &bull; QUOTE Mode (' + meta.quote + ' Strength / Price Down = Green)';
      legendGreenText.textContent = meta.quote + ' Good / Down (+Pips)';
      legendRedText.textContent = meta.quote + ' Bad / Up (-Pips)';
    }}

    // Conditioned CPI UI Information
    if (isConditionedCpi) {{
      let ruleText = '';
      let condLabel = '';
      if (cpiResp === 'BOTH_ABOVE') {{
        ruleText = 'Headline & Core CPI present; unshared timestamp; both A−F > 0. (Excludes Core PCE)';
        condLabel = 'Both Above (A−F > 0)';
      }} else if (cpiResp === 'BOTH_BELOW') {{
        ruleText = 'Headline & Core CPI present; unshared timestamp; both A−F < 0. (Excludes Core PCE)';
        condLabel = 'Both Below (A−F < 0)';
      }} else if (cpiResp === 'MIXED_ZERO') {{
        ruleText = 'Headline & Core CPI present; unshared timestamp; neither above nor below holds. (Excludes Core PCE)';
        condLabel = 'Mixed / Zero';
      }}

      const excludedSharedCount = DB.episodes.filter(ep => {{
        if (ep.family !== 'US_INFLATION') return false;
        if (year !== 'ALL' && ep.year !== parseInt(year, 10)) return false;
        return ep.is_shared_timestamp;
      }}).length;

      cpiSelectorInfo.style.display = 'block';
      cpiSelectorInfo.textContent = 'Rule: ' + ruleText + ' | Eligible N = ' + filtered.length + ' (Excluded ' + excludedSharedCount + ' shared)';

      badgeCpiCondition.style.display = 'inline-flex';
      badgeCpiCondition.textContent = 'Condition: ' + condLabel;

      badgeCpiSharedExcl.style.display = 'inline-flex';
      badgeCpiSharedExcl.textContent = 'Shared Collisions Excluded: ' + excludedSharedCount;

      if (filtered.length < 10) {{
        badgeSmallNSample.style.display = 'inline-flex';
        badgeSmallNSample.textContent = 'Caution: Small N = ' + filtered.length + ' (<10)';
        cpiMethodologyNote.className = 'methodology-note small-n';
        cpiMethodologyText.innerHTML = '<strong>Small Sample Caution:</strong> This conditioned CPI subset contains N = ' + filtered.length + ' (&lt;10) priced episodes. Descriptive sample percentiles (P10, P50 median, P90) have high sampling variability in small samples and do not represent confidence intervals or guaranteed trading bounds. The full 2015–2026 series is exploratory; later years are not an untouched holdout.';
      }} else {{
        badgeSmallNSample.style.display = 'none';
        cpiMethodologyNote.className = 'methodology-note';
        cpiMethodologyText.innerHTML = '<strong>Descriptive Methodology Note:</strong> P10, P50 (median), and P90 are empirical sample percentiles computed using Type-7 linear interpolation at position (N−1)×p. They describe historical sample dispersion and do not represent confidence intervals or predictive trading bounds. The full 2015–2026 series is exploratory; later years are not an untouched holdout.';
      }}
      cpiMethodologyNote.style.display = 'block';
    }} else {{
      cpiSelectorInfo.style.display = 'none';
      badgeCpiCondition.style.display = 'none';
      badgeCpiSharedExcl.style.display = 'none';
      badgeSmallNSample.style.display = 'none';
      cpiMethodologyNote.style.display = 'none';
    }}

    // Filter to selected single episode if specified
    const selectedEpTs = selEpisode.value;
    let episodesToRender = filtered;
    if (selectedEpTs && selectedEpTs !== 'ALL') {{
      const single = filtered.filter(ep => ep.ts === parseInt(selectedEpTs, 10));
      if (single.length > 0) episodesToRender = single;
    }}

    // Clear Body
    tableBody.innerHTML = '';

    // Collect horizon values for summary calculation across qualifying episodes
    const horizonValues = Array.from({{ length: 60 }}, () => []);

    episodesToRender.forEach((ep, idx) => {{
      const tr = document.createElement('tr');
      const hasPriceData = (ep.pips && ep.pips[pair] !== null);
      const rawPips = hasPriceData ? ep.pips[pair] : null;

      // Col 1: #
      const tdIdx = document.createElement('td');
      tdIdx.className = 'sticky-col-1';
      tdIdx.textContent = (idx + 1);
      tr.appendChild(tdIdx);

      // Col 2: Date / Time
      const tdDate = document.createElement('td');
      tdDate.className = 'sticky-col-2';
      tdDate.textContent = ep.dt_str;
      tr.appendChild(tdDate);

      // Col 3: Indicators (Stacked)
      const tdInd = document.createElement('td');
      tdInd.className = 'sticky-col-3';
      const indDiv = document.createElement('div');
      indDiv.className = 'stacked-row';
      ep.indicators.forEach(ind => {{
        const line = document.createElement('div');
        line.className = 'stacked-line';
        line.textContent = ind.name;
        indDiv.appendChild(line);
      }});
      tdInd.appendChild(indDiv);
      tr.appendChild(tdInd);

      // Columns 4-8: A, F, P, S, M (Stacked)
      ['actual', 'forecast', 'previous', 'surprise', 'momentum'].forEach((field, fIdx) => {{
        const td = document.createElement('td');
        td.className = 'sticky-col-afpsm sticky-col-' + (fIdx + 4);
        const fDiv = document.createElement('div');
        fDiv.className = 'stacked-row';
        ep.indicators.forEach(ind => {{
          const line = document.createElement('div');
          line.className = 'stacked-line';
          line.textContent = ind[field];
          if (field === 'surprise' && ind.raw_s !== null && ind.raw_s !== undefined) {{
            if (ind.raw_s > 0) line.style.color = '#15803d';
            else if (ind.raw_s < 0) line.style.color = '#b91c1c';
          }}
          fDiv.appendChild(line);
        }});
        td.appendChild(fDiv);
        tr.appendChild(td);
      }});

      // Horizons H1..H60
      for (let h = 0; h < 60; h++) {{
        const tdH = document.createElement('td');
        tdH.className = 'pip-cell';

        if (rawPips && rawPips[h] !== null && rawPips[h] !== undefined) {{
          const signedVal = getSignedPips(rawPips[h], viewingMode);

          // Check if this episode qualifies for median population (or conditioned view)
          if (isConditionedCpi || medianPopulation === 'ALL_PRICED' || (medianPopulation === 'COMPLETE_AFP' && ep.is_complete_afp)) {{
            horizonValues[h].push(signedVal);
          }}

          const signStr = signedVal > 0 ? '+' : '';
          tdH.textContent = signStr + signedVal.toFixed(1);

          if (signedVal > 0) tdH.className += ' cell-pos';
          else if (signedVal < 0) tdH.className += ' cell-neg';
          else tdH.className += ' cell-zero';

          tdH.title = 'H' + (h + 1) + ': ' + signStr + signedVal.toFixed(1) + ' pips (' + viewingMode + ' mode)';
        }} else {{
          tdH.className += ' cell-na';
          tdH.textContent = '--';
          tdH.title = 'H' + (h + 1) + ': No price data / post-cutoff';
        }}
        tr.appendChild(tdH);
      }}

      tableBody.appendChild(tr);
    }});

    // Footer Rendering
    tableFoot.innerHTML = '';
    if (!isConditionedCpi) {{
      // Single Median Row (Standard descriptive view)
      const trFoot = document.createElement('tr');
      trFoot.className = 'foot-single-median';

      const tdF1 = document.createElement('td');
      tdF1.className = 'sticky-col-1';
      tdF1.textContent = 'M';
      trFoot.appendChild(tdF1);

      const tdF2 = document.createElement('td');
      tdF2.className = 'sticky-col-2';
      tdF2.textContent = 'MEDIAN';
      trFoot.appendChild(tdF2);

      const tdF3 = document.createElement('td');
      tdF3.className = 'sticky-col-3';
      const qualifyingEpisodes = episodesToRender.filter(e => {{
        const hasPrice = e.pips && e.pips[pair] !== null;
        if (!hasPrice) return false;
        if (medianPopulation === 'COMPLETE_AFP') return e.is_complete_afp;
        return true;
      }});
      const footerPricedN = qualifyingEpisodes.length;

      if (medianPopulation === 'COMPLETE_AFP') {{
        tdF3.textContent = 'Complete A/F/P only (Priced N=' + footerPricedN + ')';
      }} else {{
        tdF3.textContent = 'All priced releases (Priced N=' + footerPricedN + ')';
      }}
      trFoot.appendChild(tdF3);

      for (let i = 4; i <= 8; i++) {{
        const td = document.createElement('td');
        td.className = 'sticky-col-afpsm sticky-col-' + i;
        td.textContent = '--';
        trFoot.appendChild(td);
      }}

      for (let h = 0; h < 60; h++) {{
        const tdH = document.createElement('td');
        tdH.className = 'pip-cell';
        const vals = horizonValues[h];

        if (vals && vals.length > 0) {{
          vals.sort((a, b) => a - b);
          const mid = Math.floor(vals.length / 2);
          const med = vals.length % 2 !== 0 ? vals[mid] : (vals[mid - 1] + vals[mid]) / 2;
          const signStr = med > 0 ? '+' : '';
          tdH.textContent = signStr + med.toFixed(1);

          if (med > 0) tdH.className += ' cell-pos';
          else if (med < 0) tdH.className += ' cell-neg';
          else tdH.className += ' cell-zero';

          tdH.title = 'Median H' + (h + 1) + ': ' + signStr + med.toFixed(1) + ' pips (N=' + vals.length + ')';
        }} else {{
          tdH.className += ' cell-na';
          tdH.textContent = '--';
          tdH.title = 'Median H' + (h + 1) + ': -- (N=0)';
        }}
        trFoot.appendChild(tdH);
      }}

      tableFoot.appendChild(trFoot);
    }} else {{
      // FIVE Conditioned CPI Summary Rows
      const rowConfigs = [
        {{ key: 'p10', label1: 'P10', label2: 'P10 PIPS', label3: 'P10 signed pips (Type-7)', cls: 'foot-cpi-p10' }},
        {{ key: 'p50', label1: 'P50', label2: 'P50 (MEDIAN)', label3: 'P50 signed pips (median)', cls: 'foot-cpi-p50' }},
        {{ key: 'p90', label1: 'P90', label2: 'P90 PIPS', label3: 'P90 signed pips (Type-7)', cls: 'foot-cpi-p90' }},
        {{ key: 'pos', label1: 'POS%', label2: 'POSITIVE %', label3: 'Positive in selected BASE/QUOTE mode', cls: 'foot-cpi-pos' }},
        {{ key: 'n', label1: 'N', label2: 'COUNT', label3: 'Available N', cls: 'foot-cpi-n' }}
      ];

      const hMetrics = [];
      for (let h = 0; h < 60; h++) {{
        const vals = horizonValues[h];
        const n = vals ? vals.length : 0;
        if (n === 0) {{
          hMetrics.push({{ n: 0, p10: null, p50: null, p90: null, posFreq: null }});
        }} else {{
          const sorted = vals.slice().sort((a, b) => a - b);
          const p10 = computeType7Percentile(sorted, 0.10);
          const p50 = computeType7Percentile(sorted, 0.50);
          const p90 = computeType7Percentile(sorted, 0.90);
          const posCount = sorted.filter(v => v > 0).length;
          const posFreq = (posCount / n) * 100;
          hMetrics.push({{ n: n, p10: p10, p50: p50, p90: p90, posFreq: posFreq, posCount: posCount }});
        }}
      }}

      rowConfigs.forEach(rc => {{
        const tr = document.createElement('tr');
        tr.className = rc.cls;

        const td1 = document.createElement('td');
        td1.className = 'sticky-col-1';
        td1.textContent = rc.label1;
        tr.appendChild(td1);

        const td2 = document.createElement('td');
        td2.className = 'sticky-col-2';
        td2.textContent = rc.label2;
        tr.appendChild(td2);

        const td3 = document.createElement('td');
        td3.className = 'sticky-col-3';
        td3.textContent = rc.label3;
        tr.appendChild(td3);

        for (let i = 4; i <= 8; i++) {{
          const td = document.createElement('td');
          td.className = 'sticky-col-afpsm sticky-col-' + i;
          td.textContent = '--';
          tr.appendChild(td);
        }}

        for (let h = 0; h < 60; h++) {{
          const tdH = document.createElement('td');
          tdH.className = 'pip-cell';
          const m = hMetrics[h];

          if (rc.key === 'p10' || rc.key === 'p50' || rc.key === 'p90') {{
            const val = m[rc.key];
            if (val !== null && val !== undefined) {{
              const signStr = val > 0 ? '+' : '';
              tdH.textContent = signStr + val.toFixed(1);
              if (val > 0) tdH.className += ' cell-pos';
              else if (val < 0) tdH.className += ' cell-neg';
              else tdH.className += ' cell-zero';
              tdH.title = rc.label1 + ' H' + (h + 1) + ': ' + signStr + val.toFixed(1) + ' pips (N=' + m.n + ')';
            }} else {{
              tdH.className += ' cell-na';
              tdH.textContent = '--';
              tdH.title = rc.label1 + ' H' + (h + 1) + ': -- (N=0)';
            }}
          }} else if (rc.key === 'pos') {{
            if (m.posFreq !== null && m.posFreq !== undefined) {{
              tdH.textContent = m.posFreq.toFixed(1) + '%';
              if (m.posFreq > 50.0) tdH.className += ' cell-pos';
              else if (m.posFreq < 50.0) tdH.className += ' cell-neg';
              else tdH.className += ' cell-zero';
              tdH.title = 'Positive % H' + (h + 1) + ': ' + m.posFreq.toFixed(1) + '% (' + m.posCount + '/' + m.n + ' > 0 pips in ' + viewingMode + ' mode)';
            }} else {{
              tdH.className += ' cell-na';
              tdH.textContent = '--';
              tdH.title = 'Positive % H' + (h + 1) + ': -- (N=0)';
            }}
          }} else if (rc.key === 'n') {{
            tdH.textContent = m.n.toString();
            tdH.title = 'Available N H' + (h + 1) + ': ' + m.n;
          }}

          tr.appendChild(tdH);
        }}

        tableFoot.appendChild(tr);
      }});
    }}
  }}

  // Event Listeners
  selPair.addEventListener('change', () => {{
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  }});

  selYear.addEventListener('change', () => {{
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  }});

  selFamily.addEventListener('change', () => {{
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  }});

  selCpiResponse.addEventListener('change', () => {{
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  }});

  selEpisode.addEventListener('change', () => {{
    render();
  }});

  selMedianPop.addEventListener('change', () => {{
    medianPopulation = selMedianPop.value;
    render();
  }});

  btnModeBase.addEventListener('click', () => {{
    viewingMode = 'BASE';
    btnModeBase.classList.add('active');
    btnModeQuote.classList.remove('active');
    render();
  }});

  btnModeQuote.addEventListener('click', () => {{
    viewingMode = 'QUOTE';
    btnModeQuote.classList.add('active');
    btnModeBase.classList.remove('active');
    render();
  }});

  btnReset.addEventListener('click', () => {{
    selPair.value = '';
    selYear.value = '';
    selFamily.value = '';
    selCpiResponse.value = 'ALL';
    selCpiResponse.disabled = true;
    selEpisode.value = 'ALL';
    selEpisode.disabled = true;
    selMedianPop.value = 'COMPLETE_AFP';
    medianPopulation = 'COMPLETE_AFP';
    viewingMode = 'BASE';
    btnModeBase.classList.add('active');
    btnModeQuote.classList.remove('active');
    render();
  }});

  // Initial Run
  initSelectors();
  render();
</script>
</body>
</html>
"""

    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated standalone HTML table viewer successfully at: {OUTPUT_HTML_PATH}")
    print(f"HTML File Size: {os.path.getsize(OUTPUT_HTML_PATH) / 1024:.1f} KB")


def main():
    candles_db = load_candles()
    episodes = parse_calendar_episodes()
    episodes_with_pips = compute_pips_for_episodes(episodes, candles_db)
    build_html(episodes_with_pips)


if __name__ == "__main__":
    main()
