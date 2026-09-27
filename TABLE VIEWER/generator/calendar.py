"""
Calendar release parsing and episode aggregation.
"""

import csv
from collections import defaultdict
from datetime import datetime, timezone
import os
from typing import Dict, List, Any, Optional

from .config import CALENDAR_PATH, EVENT_FAMILIES, SERIES_NAMES


def parse_calendar_episodes(calendar_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parses raw calendar releases and groups them into distinct (family, timestamp) episodes.
    Preserves multiple component records for the same event_id (e.g. 2019-04-29 Core PCE).
    Distinguishes:
    - 839 total family episodes across the 5 families.
    - 825 distinct timestamps across all 5 families (14 coincident timestamps: 12 Inflation + Retail, 2 Labor + Retail).
    - 634 complete A/F/P episodes.
    """
    path = calendar_path or CALENDAR_PATH
    print("Ingesting calendar releases...")
    all_target_eids = set()
    eid_to_fam = {}
    for fam_key, fam_info in EVENT_FAMILIES.items():
        for eid in fam_info["series"]:
            all_target_eids.add(eid)
            eid_to_fam[eid] = fam_key

    # Group raw records strictly by (family, timestamp)
    fam_ts_rows = defaultdict(list)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
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
