"""
Macroeconomic Event Displacement Table Generator (Light Mode)
Generates a self-contained, light-mode HTML table viewer in TABLE VIEWER/NEW/table_viewer.html.

Features:
- Pure Light Mode (white background, slate borders, dark text).
- Selectors: Pair, Year, Event Family, and dynamic N Episode selector.
- Strict Gating: Table remains clean and hidden until Pair, Year, and Event Family are selected.
- Integrated A/F/P/S/M metrics directly inside table columns.
- Co-releases (e.g. CPI + Core CPI, Retail Sales + Core) stacked cleanly per episode.
- Horizon columns H1 through H60 in exact pip displacement.
- Inversion / USD-aligned coloring (Hawkish USD move is positive/green, dovish is red; inverted for USD-quote pairs).
- Toggle for Event-Aligned Pips vs Raw Pair Pips.
- Sticky pinned left columns for easy horizontal scrolling.
- 2026 partial data handled cleanly with '--'.
"""

import csv
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
FULL_PAIRS = [
    "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "EURGBP", "EURAUD", "EURCAD", "EURCHF", "EURNZD",
    "AUDJPY", "CHFJPY", "GBPCHF", "AUDCAD", "AUDCHF", "AUDNZD"
]

# Pair descriptions & USD / EUR base/quote classification
PAIR_METADATA = {
    "EURUSD": {"desc": "EUR/USD (Euro / US Dollar)", "usd_role": "quote", "eur_role": "base", "pip": 0.00010, "digits": 5},
    "USDJPY": {"desc": "USD/JPY (US Dollar / Japanese Yen)", "usd_role": "base", "eur_role": None, "pip": 0.010, "digits": 3},
    "GBPUSD": {"desc": "GBP/USD (British Pound / US Dollar)", "usd_role": "quote", "eur_role": None, "pip": 0.00010, "digits": 5},
    "AUDUSD": {"desc": "AUD/USD (Australian Dollar / US Dollar)", "usd_role": "quote", "eur_role": None, "pip": 0.00010, "digits": 5},
    "USDCAD": {"desc": "USD/CAD (US Dollar / Canadian Dollar)", "usd_role": "base", "eur_role": None, "pip": 0.00010, "digits": 5},
    "USDCHF": {"desc": "USD/CHF (US Dollar / Swiss Franc)", "usd_role": "base", "eur_role": None, "pip": 0.00010, "digits": 5},
    "NZDUSD": {"desc": "NZD/USD (New Zealand Dollar / US Dollar)", "usd_role": "quote", "eur_role": None, "pip": 0.00010, "digits": 5},
    "EURJPY": {"desc": "EUR/JPY (Euro / Japanese Yen)", "usd_role": None, "eur_role": "base", "pip": 0.010, "digits": 3},
    "EURGBP": {"desc": "EUR/GBP (Euro / British Pound)", "usd_role": None, "eur_role": "base", "pip": 0.00010, "digits": 5},
    "EURAUD": {"desc": "EUR/AUD (Euro / Australian Dollar)", "usd_role": None, "eur_role": "base", "pip": 0.00010, "digits": 5},
    "EURCAD": {"desc": "EUR/CAD (Euro / Canadian Dollar)", "usd_role": None, "eur_role": "base", "pip": 0.00010, "digits": 5},
    "EURCHF": {"desc": "EUR/CHF (Euro / Swiss Franc)", "usd_role": None, "eur_role": "base", "pip": 0.00010, "digits": 5},
    "EURNZD": {"desc": "EUR/NZD (Euro / New Zealand Dollar)", "usd_role": None, "eur_role": "base", "pip": 0.00010, "digits": 5},
    "AUDJPY": {"desc": "AUD/JPY (Australian Dollar / Japanese Yen)", "usd_role": None, "eur_role": None, "pip": 0.010, "digits": 3},
    "CHFJPY": {"desc": "CHF/JPY (Swiss Franc / Japanese Yen)", "usd_role": None, "eur_role": None, "pip": 0.010, "digits": 3},
    "GBPCHF": {"desc": "GBP/CHF (British Pound / Swiss Franc)", "usd_role": None, "eur_role": None, "pip": 0.00010, "digits": 5},
    "AUDCAD": {"desc": "AUD/CAD (Australian Dollar / Canadian Dollar)", "usd_role": None, "eur_role": None, "pip": 0.00010, "digits": 5},
    "AUDCHF": {"desc": "AUD/CHF (Australian Dollar / Swiss Franc)", "usd_role": None, "eur_role": None, "pip": 0.00010, "digits": 5},
    "AUDNZD": {"desc": "AUD/NZD (Australian Dollar / New Zealand Dollar)", "usd_role": None, "eur_role": None, "pip": 0.00010, "digits": 5},
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
    """Loads all 19 full FX pairs into indexed lookup structures."""
    print("Loading candle files for 19 full pairs...")
    t0 = time.time()
    candles_db = {}
    for pair in FULL_PAIRS:
        csv_file = os.path.join(CANDLES_DIR, f"candles_{pair}_H1.csv")
        c_list = []
        ts_map = {}
        with open(csv_file, "r", encoding="utf-8") as f:
            f.readline()
            for line in f:
                parts = line.split(",")
                ts = int(parts[0])
                ts_map[ts] = len(c_list)
                c_list.append((ts, float(parts[1]), float(parts[4])))  # ts, open, close
        candles_db[pair] = (c_list, ts_map)
    print(f"Loaded 19 pairs in {time.time() - t0:.2f}s")
    return candles_db


def parse_calendar_episodes():
    """Parses raw calendar releases and groups them into distinct event episodes."""
    print("Ingesting calendar releases...")
    all_target_eids = set()
    for fam in EVENT_FAMILIES.values():
        all_target_eids.update(fam["series"])

    by_ts_eid = {}
    with open(CALENDAR_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["revision"] != "0":
                continue
            eid = r["event_id"]
            if eid in all_target_eids:
                ts = int(r["timestamp"])
                by_ts_eid.setdefault(ts, {})[eid] = r

    episodes = []

    # 1. Process each event family
    for fam_key, fam_info in EVENT_FAMILIES.items():
        fam_eids = set(fam_info["series"])

        for ts in sorted(by_ts_eid.keys()):
            present_eids = [eid for eid in fam_eids if eid in by_ts_eid[ts]]
            if not present_eids:
                continue

            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            year = dt.year
            dt_str = dt.strftime("%Y.%m.%d %H:%M")

            # Entry timestamp: start of the next active H1 candle bar
            entry_ts = ts if ts % 3600 == 0 else ts + (3600 - ts % 3600)

            # Build indicator rows
            indicators = []
            surprises = []
            for eid in fam_info["series"]:
                if eid in by_ts_eid[ts]:
                    r = by_ts_eid[ts][eid]
                    meta = SERIES_NAMES[eid]
                    a = float(r["actual"]) if r["actual"] != "" else None
                    f_val = float(r["forecast"]) if r["forecast"] != "" else None
                    p = float(r["previous"]) if r["previous"] != "" else None
                    s = round(a - f_val, meta["digits"]) if (a is not None and f_val is not None) else None
                    m = round(a - p, meta["digits"]) if (a is not None and p is not None) else None

                    indicators.append({
                        "name": meta["name"],
                        "actual": f"{a:.{meta['digits']}f}" if a is not None else "--",
                        "forecast": f"{f_val:.{meta['digits']}f}" if f_val is not None else "--",
                        "previous": f"{p:.{meta['digits']}f}" if p is not None else "--",
                        "surprise": f"{s:+.{meta['digits']}f}" if s is not None else "--",
                        "momentum": f"{m:+.{meta['digits']}f}" if m is not None else "--",
                        "unit": meta["unit"],
                        "raw_s": s
                    })
                    if s is not None:
                        surprises.append(s)

            # Determine macro bias
            # For USD events: +1 = USD Bullish (Hawkish), -1 = USD Bearish (Dovish), 0 = Neutral/Mixed
            # For EUR events (German Ifo): +1 = EUR Bullish, -1 = EUR Bearish, 0 = Neutral
            bias = 0
            if fam_key in ("US_INFLATION", "US_RETAIL_SALES", "GERMAN_IFO"):
                if len(surprises) >= 2:
                    if surprises[0] > 0 and surprises[1] >= 0:
                        bias = 1
                    elif surprises[0] >= 0 and surprises[1] > 0:
                        bias = 1
                    elif surprises[0] < 0 and surprises[1] <= 0:
                        bias = -1
                    elif surprises[0] <= 0 and surprises[1] < 0:
                        bias = -1
                    else:
                        bias = 0
                elif len(surprises) == 1:
                    bias = 1 if surprises[0] > 0 else (-1 if surprises[0] < 0 else 0)
            elif fam_key in ("US_LABOR", "US_ISM_PMI"):
                if len(surprises) >= 1:
                    bias = 1 if surprises[0] > 0 else (-1 if surprises[0] < 0 else 0)

            bias_label = "BULLISH" if bias == 1 else ("BEARISH" if bias == -1 else "NEUTRAL")

            episodes.append({
                "ts": ts,
                "entry_ts": entry_ts,
                "dt_str": dt_str,
                "year": year,
                "family": fam_key,
                "bias": bias,
                "bias_label": bias_label,
                "indicators": indicators
            })

    print(f"Constructed {len(episodes)} total event episodes across all families.")
    return episodes


def compute_pips_for_episodes(episodes, candles_db):
    """Computes H1..H60 pip displacements from entry open for each episode across all pairs."""
    print("Computing H1..H60 pip displacements across all pairs...")
    t0 = time.time()

    for ep in episodes:
        e_ts = ep["entry_ts"]
        pair_pips = {}

        for pair in FULL_PAIRS:
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
                        # Raw pip displacement: (Close - Open) / pip_size
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
        "pairs": FULL_PAIRS,
        "pair_meta": PAIR_METADATA,
        "families": EVENT_FAMILIES,
        "episodes": episodes_data
    })

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Macro Event Displacement Table Viewer</title>
<style>
  /* --- Reset & Typography --- */
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

  .mode-toggle-group {{
    display: flex;
    align-items: center;
    gap: 8px;
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
    font-weight: 600;
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

  /* --- Controls / Selectors Grid --- */
  .selectors-grid {{
    display: grid;
    grid-template-columns: 240px 180px 340px 260px auto;
    gap: 16px;
    align-items: flex-end;
  }}

  .control-group {{
    display: flex;
    flex-direction: column;
    gap: 5px;
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

  /* --- Summary & Guidance Banner --- */
  .status-banner {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 20px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .status-badges {{
    display: flex;
    gap: 12px;
    align-items: center;
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
  .badge-neutral {{ background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }}

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

  /* Table Header Sticky */
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

  /* Frozen / Sticky Left Columns */
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
    min-width: 170px;
    border-right: 1px solid #cbd5e1 !important;
  }}

  .sticky-col-afpsm {{
    position: sticky;
    z-index: 5;
    background: #ffffff;
    border-right: 1px solid #cbd5e1 !important;
  }}

  .sticky-col-4 {{ left: 342px; width: 65px; min-width: 65px; }} /* A */
  .sticky-col-5 {{ left: 407px; width: 65px; min-width: 65px; }} /* F */
  .sticky-col-6 {{ left: 472px; width: 65px; min-width: 65px; }} /* P */
  .sticky-col-7 {{ left: 537px; width: 65px; min-width: 65px; }} /* S */
  .sticky-col-8 {{ left: 602px; width: 65px; min-width: 65px; border-right: 2px solid #94a3b8 !important; }} /* M */

  /* Frozen headers have higher z-index */
  thead th.sticky-col-1, thead th.sticky-col-2, thead th.sticky-col-3,
  thead th.sticky-col-4, thead th.sticky-col-5, thead th.sticky-col-6,
  thead th.sticky-col-7, thead th.sticky-col-8 {{
    z-index: 20;
    background: #f1f5f9;
  }}

  /* Stacked components styling */
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
    color: #cbd5e1;
    text-align: center;
  }}

  /* Summary Median Footer Row */
  tfoot td {{
    position: sticky;
    bottom: 0;
    background: #f1f5f9;
    font-weight: 700;
    color: #0f172a;
    border-top: 2px solid #94a3b8;
    border-bottom: none;
    z-index: 10;
  }}

  tfoot td.sticky-col-1, tfoot td.sticky-col-2, tfoot td.sticky-col-3,
  tfoot td.sticky-col-4, tfoot td.sticky-col-5, tfoot td.sticky-col-6,
  tfoot td.sticky-col-7, tfoot td.sticky-col-8 {{
    z-index: 25;
    background: #e2e8f0;
  }}
</style>
</head>
<body>

<div class="header-card">
  <div class="header-top">
    <div class="title-group">
      <h1>Macroeconomic Event Displacement Table</h1>
      <p>Clean, Light-Mode Atlas displaying H1–H60 Pip Displacements & Release Fundamentals</p>
    </div>
    <div class="mode-toggle-group">
      <button id="btnModeAligned" class="mode-btn active" title="Color green if price moved in favor of the macroeconomic surprise">
        USD-Aligned Pips (USD Good = Green)
      </button>
      <button id="btnModeRaw" class="mode-btn" title="Literal price move (Close &gt; Open is Green, Close &lt; Open is Red)">
        Raw Pair Pips (Up = Green)
      </button>
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

    <!-- N Selector -->
    <div class="control-group">
      <label for="selEpisode">Episode (N)</label>
      <select id="selEpisode" class="control-select" disabled>
        <option value="ALL">Select filters first</option>
      </select>
    </div>

    <!-- Reset -->
    <div>
      <button id="btnReset" class="reset-btn">Reset</button>
    </div>
  </div>
</div>

<!-- Status / Summary Banner -->
<div id="statusBanner" class="status-banner" style="display: none;">
  <div class="status-badges">
    <span id="badgePair" class="badge badge-primary">Pair</span>
    <span id="badgeFamily" class="badge badge-secondary">Family</span>
    <span id="badgeYear" class="badge badge-secondary">Year</span>
    <span id="badgeN" class="badge badge-neutral">N = 0 Episodes</span>
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
      <span>0.0 Flat</span>
    </div>
    <div class="legend-item">
      <span style="font-weight:700; color:#94a3b8;">--</span>
      <span>Post-Cutoff / Missing</span>
    </div>
  </div>
</div>

<!-- Empty State Display -->
<div id="emptyState" class="empty-state">
  <h3>Select Pair, Year, and Event Family Above</h3>
  <p>The table remains clean and hidden until all three selectors are specified. Once chosen, the exact episode count (N) and H1–H60 trajectory will render immediately.</p>
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
        <th class="sticky-col-afpsm sticky-col-5">F</th>
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

<script>
  // Embedded dataset
  const DB = {data_json};

  let displayMode = 'ALIGNED'; // 'ALIGNED' or 'RAW'

  // DOM Elements
  const selPair = document.getElementById('selPair');
  const selYear = document.getElementById('selYear');
  const selFamily = document.getElementById('selFamily');
  const selEpisode = document.getElementById('selEpisode');
  const btnReset = document.getElementById('btnReset');
  const btnModeAligned = document.getElementById('btnModeAligned');
  const btnModeRaw = document.getElementById('btnModeRaw');

  const statusBanner = document.getElementById('statusBanner');
  const badgePair = document.getElementById('badgePair');
  const badgeFamily = document.getElementById('badgeFamily');
  const badgeYear = document.getElementById('badgeYear');
  const badgeN = document.getElementById('badgeN');
  const legendGreenText = document.getElementById('legendGreenText');
  const legendRedText = document.getElementById('legendRedText');

  const emptyState = document.getElementById('emptyState');
  const tableContainer = document.getElementById('tableContainer');
  const dataTable = document.getElementById('dataTable');
  const tableBody = document.getElementById('tableBody');
  const tableFoot = document.getElementById('tableFoot');

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

    if (!pair || !year || !family) return [];

    return DB.episodes.filter(ep => {{
      if (ep.family !== family) return false;
      if (year !== 'ALL' && ep.year !== parseInt(year, 10)) return false;
      return true;
    }});
  }}

  // Update Episode Selector options based on available filtered episodes
  function updateEpisodeSelector(filtered) {{
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
    const allOpt = document.createElement('option');
    allOpt.value = 'ALL';
    allOpt.textContent = 'All Episodes (N = ' + filtered.length + ')';
    selEpisode.appendChild(allOpt);

    filtered.forEach((ep, idx) => {{
      const opt = document.createElement('option');
      opt.value = ep.ts;
      let label = (idx + 1) + '. ' + ep.dt_str;
      if (ep.indicators.length > 0 && ep.indicators[0].surprise !== '--') {{
        label += ' (S: ' + ep.indicators[0].surprise + ')';
      }}
      opt.textContent = label;
      selEpisode.appendChild(opt);
    }});
  }}

  // Determine multiplier for USD/EUR alignment
  function getAlignmentMultiplier(pair, ep) {{
    if (displayMode === 'RAW') return 1;

    const meta = DB.pair_meta[pair];
    if (ep.family.startsWith('US_')) {{
      const bias = ep.bias; // +1 = USD Bullish, -1 = USD Bearish
      if (bias === 0) return 1;
      // If pair has USD as base (USDJPY): Price up = USD rally -> multiplier = bias
      if (meta.usd_role === 'base') return bias;
      // If pair has USD as quote (EURUSD): Price down = USD rally -> multiplier = -bias
      if (meta.usd_role === 'quote') return -bias;
      return 1;
    }} else if (ep.family === 'GERMAN_IFO') {{
      const bias = ep.bias; // +1 = EUR Bullish, -1 = EUR Bearish
      if (bias === 0) return 1;
      if (meta.eur_role === 'base') return bias;
      if (meta.eur_role === 'quote') return -bias;
      return 1;
    }}
    return 1;
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
      return;
    }}

    const filtered = getFilteredEpisodes();
    if (filtered.length === 0) {{
      emptyState.style.display = 'block';
      emptyState.querySelector('h3').textContent = 'No Episodes Found';
      emptyState.querySelector('p').textContent = 'No macroeconomic releases were recorded for this combination in the pinned dataset.';
      statusBanner.style.display = 'none';
      tableContainer.style.display = 'none';
      selEpisode.disabled = true;
      selEpisode.innerHTML = '<option value="ALL">0 Episodes Found</option>';
      return;
    }}

    emptyState.style.display = 'none';
    statusBanner.style.display = 'flex';
    tableContainer.style.display = 'block';

    // Update Status Banner
    badgePair.textContent = 'Pair: ' + pair;
    badgeFamily.textContent = DB.families[family].label;
    badgeYear.textContent = 'Year: ' + (year === 'ALL' ? '2015–2026' : year);
    badgeN.textContent = 'N = ' + filtered.length + ' Episodes';

    if (displayMode === 'ALIGNED') {{
      legendGreenText.textContent = 'In Favor of Event (+Pips)';
      legendRedText.textContent = 'Against Event (-Pips)';
    }} else {{
      legendGreenText.textContent = 'Price Up (+Pips)';
      legendRedText.textContent = 'Price Down (-Pips)';
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

    // Collect horizon values for Median calculation across displayed episodes
    const horizonValues = Array.from({{ length: 60 }}, () => []);

    episodesToRender.forEach((ep, idx) => {{
      const tr = document.createElement('tr');
      const mult = getAlignmentMultiplier(pair, ep);

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
          if (field === 'surprise' && ind.raw_s !== null) {{
            if (ind.raw_s > 0) line.style.color = '#15803d';
            else if (ind.raw_s < 0) line.style.color = '#b91c1c';
          }}
          fDiv.appendChild(line);
        }});
        td.appendChild(fDiv);
        tr.appendChild(td);
      }});

      // Horizons H1..H60
      const rawPips = (ep.pips && ep.pips[pair]) ? ep.pips[pair] : null;

      for (let h = 0; h < 60; h++) {{
        const tdH = document.createElement('td');
        tdH.className = 'pip-cell';

        if (rawPips && rawPips[h] !== null && rawPips[h] !== undefined) {{
          const val = Math.round((rawPips[h] * mult) * 10) / 10;
          horizonValues[h].push(val);

          const signStr = val > 0 ? '+' : '';
          tdH.textContent = signStr + val.toFixed(1);

          if (val > 0) tdH.className += ' cell-pos';
          else if (val < 0) tdH.className += ' cell-neg';
          else tdH.className += ' cell-zero';

          tdH.title = 'H' + (h + 1) + ': ' + signStr + val.toFixed(1) + ' pips';
        }} else {{
          tdH.className += ' cell-na';
          tdH.textContent = '--';
          tdH.title = 'H' + (h + 1) + ': Data cutoff / unobserved';
        }}
        tr.appendChild(tdH);
      }}

      tableBody.appendChild(tr);
    }});

    // Footer: Median Row (Rendered if displaying 2 or more episodes)
    tableFoot.innerHTML = '';
    if (episodesToRender.length > 1) {{
      const trFoot = document.createElement('tr');

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
      tdF3.textContent = 'All N=' + episodesToRender.length + ' Episodes';
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
        if (vals.length > 0) {{
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
        }}
        trFoot.appendChild(tdH);
      }}

      tableFoot.appendChild(trFoot);
    }}
  }}

  // Event Listeners
  selPair.addEventListener('change', () => {{
    updateEpisodeSelector(getFilteredEpisodes());
    render();
  }});

  selYear.addEventListener('change', () => {{
    updateEpisodeSelector(getFilteredEpisodes());
    render();
  }});

  selFamily.addEventListener('change', () => {{
    updateEpisodeSelector(getFilteredEpisodes());
    render();
  }});

  selEpisode.addEventListener('change', () => {{
    render();
  }});

  btnModeAligned.addEventListener('click', () => {{
    displayMode = 'ALIGNED';
    btnModeAligned.classList.add('active');
    btnModeRaw.classList.remove('active');
    render();
  }});

  btnModeRaw.addEventListener('click', () => {{
    displayMode = 'RAW';
    btnModeRaw.classList.add('active');
    btnModeAligned.classList.remove('active');
    render();
  }});

  btnReset.addEventListener('click', () => {{
    selPair.value = '';
    selYear.value = '';
    selFamily.value = '';
    selEpisode.value = 'ALL';
    selEpisode.disabled = true;
    displayMode = 'ALIGNED';
    btnModeAligned.classList.add('active');
    btnModeRaw.classList.remove('active');
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
