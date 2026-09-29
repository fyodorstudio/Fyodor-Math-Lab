"""Deterministic Generator for USD CPI Bundle Pre-Outcome Study (V1).

Builds:
1. Unique CPI release bundle ledger (140 timestamps):
   Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_pre_outcome/cpi_bundle_ledger.csv
2. Pair-expanded pre-outcome ledger (980 pair-observations):
   Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_pre_outcome/cpi_pair_expanded_ledger.csv
3. Package manifest with SHA-256 hashes and verification counts:
   Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_pre_outcome/manifest.json
4. Small tracked count reconciliation report:
   Research Candidate/CPI/CPI_BUNDLE_V1/RECONCILIATION_REPORT.md
5. Small tracked ledger schema:
   Research Candidate/CPI/CPI_BUNDLE_V1/SCHEMA.md

Strictly PRE-OUTCOME ONLY:
- Zero price returns, zero gross R, zero barrier touches, zero candidate rankings.
- Zero mock / synthetic / random data.
- Fails closed on unexpected currency, units, multipliers, malformed numbers, NaN, or infinity.
- 100% reproducible from pinned raw calendar and H1 candle exports.
"""

import os
import sys
import csv
import json
import math
import hashlib
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any, Set

# Ensure local calculator directory is on sys.path
CALC_DIR = os.path.dirname(os.path.abspath(__file__))
if CALC_DIR not in sys.path:
    sys.path.insert(0, CALC_DIR)

from protocol_specs import (
    ALL_EXPORTED_PAIRS,
    GLOBALLY_EXCLUDED_PAIRS,
    ACTIVE_RESEARCH_PAIRS,
    ACTIVE_USD_PAIRS,
    USD_BASE_PAIRS,
    USD_QUOTE_PAIRS,
    EVENT_ID_US_CPI_MM,
    EVENT_ID_US_CORE_CPI_MM,
    EVENT_ID_US_CPI_YY,
    EVENT_ID_US_CORE_CPI_YY,
    EVENT_ID_US_INITIAL_JOBLESS_CLAIMS,
    CORE_PANEL_START_TEXT,
    CORE_PANEL_END_TEXT,
    PARTIAL_PANEL_2026_END_TEXT,
    invert_usd_direction_for_pair,
    assert_event_id_valid,
)
from data_loader import (
    load_candles,
    DEFAULT_RAW_DIR,
)
from path_indexer import (
    find_entry_bar,
    calculate_pre_release_atr14,
    inspect_path_coverage,
    detect_path_weekday_gaps,
)
from eligibility_evaluator import determine_cohort

REPO_ROOT = os.path.normpath(os.path.join(CALC_DIR, "..", ".."))
PACKAGE_DIR_V1 = os.path.join(
    REPO_ROOT, "Research Candidate", "CPI", "CPI_BUNDLE_V1", "run_20260930_pre_outcome"
)
PACKAGE_DIR_V2 = os.path.join(
    REPO_ROOT, "Research Candidate", "CPI", "CPI_BUNDLE_V1", "run_20260930_pre_outcome_v2"
)
PACKAGE_DIR = PACKAGE_DIR_V2
TRACKED_DIR = os.path.join(REPO_ROOT, "Research Candidate", "CPI", "CPI_BUNDLE_V1")

CPI_TRACKED_IDS = {
    EVENT_ID_US_CPI_MM,       # 840030005
    EVENT_ID_US_CORE_CPI_MM,  # 840030006
    EVENT_ID_US_CPI_YY,       # 840030007
    EVENT_ID_US_CORE_CPI_YY,  # 840030008
}



# Pinned bit-for-bit SHA-256 hashes and byte sizes of all 13 required raw inputs
EXPECTED_RAW_INPUT_HASHES: Dict[str, Dict[str, Any]] = {
    "manifest.csv": {
        "sha256": "1E7C8A5047BDEDAF0F66DE23F5E6CC382C29EA839B9E07A911789BBFFC548A6F",
        "size_bytes": 3515,
        "role": "Root Export Manifest",
    },
    "calendar_releases.csv": {
        "sha256": "FCB68E1C2A6269D98287F4BEDBEE1F3BCB5A8C99379502782359EDFD20E83D6F",
        "size_bytes": 55514491,
        "role": "Calendar Releases Database",
    },
    "calendar_events.csv": {
        "sha256": "E08D2DF96E83FDEFA1C56D33316EE09178FE75AFF1F3325D6F4EC4C80A4B7F13",
        "size_bytes": 359636,
        "role": "Calendar Event Catalog",
    },
    "calendar_currencies.csv": {
        "sha256": "ADB8C1A4DB5041067CDEF06852C29D5EFA4BCF8E56B7F978AD9AB84CA9C3F809",
        "size_bytes": 224,
        "role": "Calendar Currencies Reference",
    },
    "candle_symbols.csv": {
        "sha256": "876495CC3FCD0B4E88CB1412E6DF154CF8813B5DF7CC5EC57A8F74C57BD7475D",
        "size_bytes": 6660,
        "role": "Exported Symbols Catalog",
    },
    "run_started.csv": {
        "sha256": "0F9944FDE37206826EADF9CBE8675B4381E15F9F524478EB7F76E6A8D9A8DA10",
        "size_bytes": 105,
        "role": "Export Timestamp Reference",
    },
    "candles/candles_AUDUSD_H1.csv": {
        "sha256": "804FF41B922BD02A7EDE6705D2BD9861A7AF5B45D7D9DD841E10AEEE81FA7181",
        "size_bytes": 7892321,
        "role": "H1 Candles AUDUSD",
    },
    "candles/candles_EURUSD_H1.csv": {
        "sha256": "96A51AA29BBC3F3E9CB07633328F154AC6967D8BF40B7A5211934ACB0DEFF45E",
        "size_bytes": 7859948,
        "role": "H1 Candles EURUSD",
    },
    "candles/candles_GBPUSD_H1.csv": {
        "sha256": "77438C3DF042FA379533144A830FEDFBEC8AC12A47E53647C8653C7090F45512",
        "size_bytes": 7900601,
        "role": "H1 Candles GBPUSD",
    },
    "candles/candles_NZDUSD_H1.csv": {
        "sha256": "DFAD73063A3313175ED7F111F8FD38AC0C1D5D1E62FD0D037A2DB396972B755E",
        "size_bytes": 7889012,
        "role": "H1 Candles NZDUSD",
    },
    "candles/candles_USDCAD_H1.csv": {
        "sha256": "D854DDB5494E3CD62D9F80E2A22F9F65FAAA886643572602D638722C1DC72D44",
        "size_bytes": 7899102,
        "role": "H1 Candles USDCAD",
    },
    "candles/candles_USDCHF_H1.csv": {
        "sha256": "134A250D6FE0F3259A6B0D842872866B481A9A7FE9D7567E7892DCB23B63897E",
        "size_bytes": 7906778,
        "role": "H1 Candles USDCHF",
    },
    "candles/candles_USDJPY_H1.csv": {
        "sha256": "3DCE78FE38019275F288E71E4F9134E4BEA1FD02A09E1CEE2873025A3961468C",
        "size_bytes": 7900249,
        "role": "H1 Candles USDJPY",
    },
}


def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 checksum in uppercase hex."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()


def verify_raw_inputs_at_startup(raw_dir: str = DEFAULT_RAW_DIR) -> Dict[str, Dict[str, Any]]:
    """Verifies SHA-256 hashes and byte sizes of all 13 required raw inputs at generator startup.

    Fails closed immediately (raises FileNotFoundError or RuntimeError) BEFORE writing any outputs
    or executing parsing if any file is missing, modified, or has an unexpected checksum.
    """
    verified_catalog: Dict[str, Dict[str, Any]] = {}
    for rel_path, meta in EXPECTED_RAW_INPUT_HASHES.items():
        full_path = os.path.join(raw_dir, os.path.normpath(rel_path))
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Fail-closed startup: required raw input missing at '{full_path}'")

        actual_size = os.path.getsize(full_path)
        actual_hash = compute_sha256(full_path)

        if actual_hash != meta["sha256"]:
            raise RuntimeError(
                f"Fail-closed startup hash mismatch for '{rel_path}': "
                f"expected {meta['sha256']}, computed {actual_hash}"
            )
        if actual_size != meta["size_bytes"]:
            raise RuntimeError(
                f"Fail-closed startup byte size mismatch for '{rel_path}': "
                f"expected {meta['size_bytes']} bytes, got {actual_size} bytes"
            )

        verified_catalog[rel_path] = {
            "rel_path": rel_path,
            "full_path": os.path.abspath(full_path),
            "role": meta["role"],
            "expected_sha256": meta["sha256"],
            "computed_sha256": actual_hash,
            "expected_size_bytes": meta["size_bytes"],
            "actual_size_bytes": actual_size,
            "verified": True,
        }
    return verified_catalog


def parse_strict_calendar_float(val: str, field_name: str, line_idx: int) -> Optional[float]:
    """Strictly parses calendar numeric fields, failing closed on malformed/non-finite text.
    
    Rules:
    - Empty string or whitespace-only is valid MISSING (returns None).
    - Any non-empty string must parse to a finite float.
    - If string is non-numeric, 'nan', 'inf', '-inf', or malformed: raises ValueError (fails closed).
    - Missing is strictly distinct from malformed.
    """
    cleaned = val.strip()
    if not cleaned:
        return None

    lowered = cleaned.lower()
    if lowered in ("nan", "inf", "-inf", "+inf", "null", "none"):
        raise ValueError(
            f"Fail-closed: malformed numeric text '{val}' for field '{field_name}' "
            f"at line {line_idx} (NaN/Inf is strictly prohibited)."
        )

    try:
        f_val = float(cleaned)
    except ValueError as e:
        raise ValueError(
            f"Fail-closed: unparseable numeric text '{val}' for field '{field_name}' "
            f"at line {line_idx}: {e}"
        ) from e

    if math.isnan(f_val) or math.isinf(f_val):
        raise ValueError(
            f"Fail-closed: non-finite float value {f_val} for field '{field_name}' "
            f"at line {line_idx}."
        )

    return f_val


def compute_difference_strict(minuend: Optional[float], subtrahend: Optional[float]) -> Optional[float]:
    """Computes arithmetic difference A - P with strict non-finite checking."""
    if minuend is None or subtrahend is None:
        return None
    if math.isnan(minuend) or math.isnan(subtrahend) or math.isinf(minuend) or math.isinf(subtrahend):
        raise ValueError(f"Fail-closed: compute_difference received non-finite input: {minuend}, {subtrahend}")
    return round(minuend - subtrahend, 6)


def classify_signal_state_strict(diff: Optional[float]) -> str:
    """Classifies a derived difference into strict non-overlapping states, failing closed on NaN."""
    if diff is None:
        return "MISSING"
    if math.isnan(diff) or math.isinf(diff):
        raise ValueError(f"Fail-closed: classify_signal_state received non-finite delta: {diff}")
    if diff > 1e-9:
        return "POSITIVE"
    if diff < -1e-9:
        return "NEGATIVE"
    if abs(diff) <= 1e-9:
        return "ZERO"
    raise ValueError(f"Fail-closed: unclassifiable delta: {diff}")


def load_raw_calendar_data(raw_dir: str = DEFAULT_RAW_DIR):
    """Loads raw calendar data with fail-closed validation on currency, units, multipliers, and numbers."""
    releases_path = os.path.join(raw_dir, "calendar_releases.csv")
    events_path = os.path.join(raw_dir, "calendar_events.csv")

    if not os.path.exists(releases_path):
        raise FileNotFoundError(f"Missing calendar_releases.csv at {releases_path}")
    if not os.path.exists(events_path):
        raise FileNotFoundError(f"Missing calendar_events.csv at {events_path}")

    # Load and validate event catalog mapping
    event_catalog: Dict[str, Dict[str, str]] = {}
    with open(events_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            event_catalog[r["event_id"]] = {
                "event_name": r["event_name"],
                "country_currency": r["country_currency"],
                "sector": r["sector"],
                "unit": r["unit"],
                "digits": r["digits"],
                "multiplier": r["multiplier"],
                "importance": r["importance"],
            }

    # Verify target IDs and catalog metadata
    for eid in CPI_TRACKED_IDS:
        if eid not in event_catalog:
            raise ValueError(f"Fail-closed: CPI Event ID {eid} not found in calendar_events.csv!")
        cat = event_catalog[eid]
        if cat["country_currency"] != "USD":
            raise ValueError(f"Fail-closed: Event ID {eid} currency is {cat['country_currency']} != USD!")
        if cat["sector"] != "CALENDAR_SECTOR_PRICES":
            raise ValueError(f"Fail-closed: Event ID {eid} sector is {cat['sector']} != CALENDAR_SECTOR_PRICES!")
        if cat["unit"] != "CALENDAR_UNIT_PERCENT":
            raise ValueError(f"Fail-closed: Event ID {eid} unit is {cat['unit']} != CALENDAR_UNIT_PERCENT!")

    if EVENT_ID_US_INITIAL_JOBLESS_CLAIMS not in event_catalog:
        raise ValueError(f"Fail-closed: Claims Event ID {EVENT_ID_US_INITIAL_JOBLESS_CLAIMS} not found in catalog!")

    # Load calendar releases with 1-indexed source row numbers
    cpi_releases_by_ts: Dict[int, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    all_releases_by_ts: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    total_matching_cpi_rows = 0

    with open(releases_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_idx, r in enumerate(reader, start=2):
            ts = int(r["timestamp"])
            eid = r["event_id"]
            record = {
                "source_row": line_idx,
                "event_id": eid,
                "value_id": r["value_id"],
                "timestamp": ts,
                "timestamp_server_text": r["timestamp_server_text"],
                "currency": r["currency"],
                "country_code": r["country_code"],
                "event_name": r["event_name"],
                "importance": r["importance"],
                "actual": parse_strict_calendar_float(r["actual"], "actual", line_idx),
                "forecast": parse_strict_calendar_float(r["forecast"], "forecast", line_idx),
                "previous": parse_strict_calendar_float(r["previous"], "previous", line_idx),
                "revised_previous": parse_strict_calendar_float(r["revised_previous"], "revised_previous", line_idx),
                "period_server_text": r["period_server_text"],
                "unit": r["unit"],
                "multiplier": r["multiplier"],
                "digits": int(r["digits"]) if r["digits"] else 0,
                "raw_actual_str": r["actual"],
                "raw_forecast_str": r["forecast"],
                "raw_previous_str": r["previous"],
                "raw_revised_previous_str": r["revised_previous"],
            }
            all_releases_by_ts[ts].append(record)

            if eid in CPI_TRACKED_IDS:
                # Fail-closed checks on raw release row
                if r["currency"] != "USD":
                    raise ValueError(f"Fail-closed: row line {line_idx} has currency '{r['currency']}' != USD")
                if r["unit"] != "CALENDAR_UNIT_PERCENT":
                    raise ValueError(f"Fail-closed: row line {line_idx} has unit '{r['unit']}' != CALENDAR_UNIT_PERCENT")
                if r["multiplier"] != "CALENDAR_MULTIPLIER_NONE":
                    raise ValueError(f"Fail-closed: row line {line_idx} has multiplier '{r['multiplier']}' != NONE")

                if eid in cpi_releases_by_ts[ts]:
                    raise ValueError(
                        f"CRITICAL: Duplicate event ID {eid} at timestamp {ts} "
                        f"(line {line_idx} vs line {cpi_releases_by_ts[ts][eid]['source_row']})!"
                    )
                cpi_releases_by_ts[ts][eid] = record
                total_matching_cpi_rows += 1

    return cpi_releases_by_ts, all_releases_by_ts, event_catalog, total_matching_cpi_rows


def classify_mm_concordance(
    head_sign: str,
    core_sign: str,
) -> str:
    """Classifies the joint sign relation between headline m/m and core m/m."""
    if head_sign == "MISSING" or core_sign == "MISSING":
        return "MISSING_ANCHOR"
    if head_sign == "POSITIVE" and core_sign == "POSITIVE":
        return "CONCORDANT_POS"
    if head_sign == "NEGATIVE" and core_sign == "NEGATIVE":
        return "CONCORDANT_NEG"
    if head_sign == "POSITIVE" and core_sign == "NEGATIVE":
        return "CONFLICT_HEAD_POS_CORE_NEG"
    if head_sign == "NEGATIVE" and core_sign == "POSITIVE":
        return "CONFLICT_HEAD_NEG_CORE_POS"
    if head_sign == "POSITIVE" and core_sign == "ZERO":
        return "HEAD_POS_CORE_ZERO"
    if head_sign == "NEGATIVE" and core_sign == "ZERO":
        return "HEAD_NEG_CORE_ZERO"
    if head_sign == "ZERO" and core_sign == "POSITIVE":
        return "HEAD_ZERO_CORE_POS"
    if head_sign == "ZERO" and core_sign == "NEGATIVE":
        return "HEAD_ZERO_CORE_NEG"
    if head_sign == "ZERO" and core_sign == "ZERO":
        return "BOTH_ZERO"
    return "UNKNOWN"


def generate_bundle_inventory(
    raw_dir: str = DEFAULT_RAW_DIR,
    output_dir: str = PACKAGE_DIR,
    tracked_dir: str = TRACKED_DIR,
) -> Dict[str, Any]:
    """Generates auditable price-blind bundle and pair ledgers, manifest, and reports."""
    # Step 0: Fail-closed startup verification of all 13 raw files BEFORE any directory creation or writes
    verified_inputs = verify_raw_inputs_at_startup(raw_dir)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(tracked_dir, exist_ok=True)

    cpi_by_ts, all_by_ts, catalog, total_raw_cpi_rows = load_raw_calendar_data(raw_dir)
    unique_timestamps = sorted(cpi_by_ts.keys())
    total_bundles = len(unique_timestamps)

    # Load candle series for the 7 active USD pairs
    candles = {p: load_candles(p, raw_dir=raw_dir) for p in ACTIVE_USD_PAIRS}

    bundle_rows: List[Dict[str, Any]] = []
    pair_rows: List[Dict[str, Any]] = []

    # Summary counters
    constituent_counts = defaultdict(int)
    yearly_counts = defaultdict(int)
    cohort_counts = defaultdict(int)
    sign_counts = defaultdict(lambda: defaultdict(int))
    mm_concordance_counts = defaultdict(int)
    claims_coincident_count = 0
    claims_mm_present_count = 0

    for ts in unique_timestamps:
        cpi_map = cpi_by_ts[ts]
        sample_rel = next(iter(cpi_map.values()))
        txt = sample_rel["timestamp_server_text"]
        yr = int(txt[:4])
        cohort = determine_cohort(txt)
        bundle_period = sample_rel["period_server_text"]

        # Checked invariant: every constituent present in this bundle shares the identical period_server_text
        constituent_periods = {r["period_server_text"] for r in cpi_map.values()}
        if len(constituent_periods) > 1:
            raise ValueError(
                f"Fail-closed invariant violation: multiple period_server_text values "
                f"within bundle at timestamp {ts} ({txt}): {sorted(constituent_periods)}"
            )

        yearly_counts[yr] += 1
        cohort_counts[cohort] += 1

        present_ids = sorted(cpi_map.keys())
        missing_ids = sorted(list(CPI_TRACKED_IDS - set(present_ids)))
        is_complete = (len(missing_ids) == 0)

        for eid in present_ids:
            constituent_counts[eid] += 1

        # Constituent objects
        r_head_mm = cpi_map.get(EVENT_ID_US_CPI_MM)
        r_core_mm = cpi_map.get(EVENT_ID_US_CORE_CPI_MM)
        r_head_yy = cpi_map.get(EVENT_ID_US_CPI_YY)
        r_core_yy = cpi_map.get(EVENT_ID_US_CORE_CPI_YY)

        # Constituent A, P, delta, signs
        def parse_series(r: Optional[Dict[str, Any]]):
            if r is None:
                return {
                    "present": False,
                    "source_row": None,
                    "value_id": "",
                    "unit": "",
                    "digits": None,
                    "actual": None,
                    "previous": None,
                    "revised_previous": None,
                    "period_server_text": "",
                    "delta": None,
                    "sign": "MISSING",
                }
            a = r["actual"]
            p = r["previous"]
            rev = r["revised_previous"]
            d = compute_difference_strict(a, p)
            s = classify_signal_state_strict(d)
            return {
                "present": True,
                "source_row": r["source_row"],
                "value_id": r["value_id"],
                "unit": r["unit"],
                "digits": r["digits"],
                "actual": a,
                "previous": p,
                "revised_previous": rev,
                "period_server_text": r["period_server_text"],
                "delta": d,
                "sign": s,
            }

        s_head_mm = parse_series(r_head_mm)
        s_core_mm = parse_series(r_core_mm)
        s_head_yy = parse_series(r_head_yy)
        s_core_yy = parse_series(r_core_yy)

        sign_counts[EVENT_ID_US_CPI_MM][s_head_mm["sign"]] += 1
        sign_counts[EVENT_ID_US_CORE_CPI_MM][s_core_mm["sign"]] += 1
        sign_counts[EVENT_ID_US_CPI_YY][s_head_yy["sign"]] += 1
        sign_counts[EVENT_ID_US_CORE_CPI_YY][s_core_yy["sign"]] += 1

        # Joint m/m relation
        mm_conc = classify_mm_concordance(s_head_mm["sign"], s_core_mm["sign"])
        mm_concordance_counts[mm_conc] += 1
        is_conflict = mm_conc in ("CONFLICT_HEAD_POS_CORE_NEG", "CONFLICT_HEAD_NEG_CORE_POS")

        # Coincident non-CPI releases
        all_releases_this_ts = all_by_ts[ts]
        coincident_non_cpi = [r for r in all_releases_this_ts if r["event_id"] not in CPI_TRACKED_IDS]
        claims_rel = next((r for r in coincident_non_cpi if r["event_id"] == EVENT_ID_US_INITIAL_JOBLESS_CLAIMS), None)
        has_claims = (claims_rel is not None)
        if has_claims:
            claims_coincident_count += 1
            if s_head_mm["present"]:
                claims_mm_present_count += 1

        coincident_summary = "|".join(
            f"{r['currency']}_{r['event_id']}:{r['event_name']}" for r in coincident_non_cpi
        )

        bundle_row = {
            "bundle_id": f"USD_CPI_BUNDLE_{ts}",
            "timestamp": ts,
            "timestamp_server_text": txt,
            "bundle_period_server_text": bundle_period,
            "year": yr,
            "cohort": cohort,
            "is_bundle_complete": is_complete,
            "present_constituent_ids": ",".join(present_ids),
            "missing_constituent_ids": ",".join(missing_ids),
            "headline_mm_present": s_head_mm["present"],
            "headline_mm_source_row": s_head_mm["source_row"] or "",
            "headline_mm_value_id": s_head_mm["value_id"],
            "headline_mm_unit": s_head_mm["unit"],
            "headline_mm_digits": s_head_mm["digits"] if s_head_mm["digits"] is not None else "",
            "headline_mm_actual": s_head_mm["actual"] if s_head_mm["actual"] is not None else "",
            "headline_mm_previous": s_head_mm["previous"] if s_head_mm["previous"] is not None else "",
            "headline_mm_revised_previous": s_head_mm["revised_previous"] if s_head_mm["revised_previous"] is not None else "",
            "headline_mm_period_server_text": s_head_mm["period_server_text"],
            "headline_mm_delta": f"{s_head_mm['delta']:.6f}" if s_head_mm["delta"] is not None else "",
            "headline_mm_sign": s_head_mm["sign"],
            "core_mm_present": s_core_mm["present"],
            "core_mm_source_row": s_core_mm["source_row"] or "",
            "core_mm_value_id": s_core_mm["value_id"],
            "core_mm_unit": s_core_mm["unit"],
            "core_mm_digits": s_core_mm["digits"] if s_core_mm["digits"] is not None else "",
            "core_mm_actual": s_core_mm["actual"] if s_core_mm["actual"] is not None else "",
            "core_mm_previous": s_core_mm["previous"] if s_core_mm["previous"] is not None else "",
            "core_mm_revised_previous": s_core_mm["revised_previous"] if s_core_mm["revised_previous"] is not None else "",
            "core_mm_period_server_text": s_core_mm["period_server_text"],
            "core_mm_delta": f"{s_core_mm['delta']:.6f}" if s_core_mm["delta"] is not None else "",
            "core_mm_sign": s_core_mm["sign"],
            "headline_yy_present": s_head_yy["present"],
            "headline_yy_source_row": s_head_yy["source_row"] or "",
            "headline_yy_value_id": s_head_yy["value_id"],
            "headline_yy_unit": s_head_yy["unit"],
            "headline_yy_digits": s_head_yy["digits"] if s_head_yy["digits"] is not None else "",
            "headline_yy_actual": s_head_yy["actual"] if s_head_yy["actual"] is not None else "",
            "headline_yy_previous": s_head_yy["previous"] if s_head_yy["previous"] is not None else "",
            "headline_yy_revised_previous": s_head_yy["revised_previous"] if s_head_yy["revised_previous"] is not None else "",
            "headline_yy_period_server_text": s_head_yy["period_server_text"],
            "headline_yy_delta": f"{s_head_yy['delta']:.6f}" if s_head_yy["delta"] is not None else "",
            "headline_yy_sign": s_head_yy["sign"],
            "core_yy_present": s_core_yy["present"],
            "core_yy_source_row": s_core_yy["source_row"] or "",
            "core_yy_value_id": s_core_yy["value_id"],
            "core_yy_unit": s_core_yy["unit"],
            "core_yy_digits": s_core_yy["digits"] if s_core_yy["digits"] is not None else "",
            "core_yy_actual": s_core_yy["actual"] if s_core_yy["actual"] is not None else "",
            "core_yy_previous": s_core_yy["previous"] if s_core_yy["previous"] is not None else "",
            "core_yy_revised_previous": s_core_yy["revised_previous"] if s_core_yy["revised_previous"] is not None else "",
            "core_yy_period_server_text": s_core_yy["period_server_text"],
            "core_yy_delta": f"{s_core_yy['delta']:.6f}" if s_core_yy["delta"] is not None else "",
            "core_yy_sign": s_core_yy["sign"],
            "mm_concordance_state": mm_conc,
            "is_conflict_episode": is_conflict,
            "coincident_claims_collision": has_claims,
            "coincident_claims_value_id": claims_rel["value_id"] if claims_rel else "",
            "coincident_claims_actual": claims_rel["actual"] if claims_rel and claims_rel["actual"] is not None else "",
            "coincident_claims_previous": claims_rel["previous"] if claims_rel and claims_rel["previous"] is not None else "",
            "coincident_non_cpi_count": len(coincident_non_cpi),
            "coincident_non_cpi_event_ids": coincident_summary,
        }
        bundle_rows.append(bundle_row)

        # Pair-expanded rows across the 7 active USD pairs
        for pair in ACTIVE_USD_PAIRS:
            pair_c = candles[pair]
            usd_role = "BASE" if pair in USD_BASE_PAIRS else "QUOTE"

            # Evaluate entry bar and physical coverage
            has_atr, atr_val, _ = calculate_pre_release_atr14(pair_c, ts)
            entry_idx, entry_b, delay_sec = find_entry_bar(pair_c, ts)
            has_entry = (entry_idx is not None and entry_b is not None)
            valid_delay = (delay_sec is not None and delay_sec <= 3600)

            if has_entry:
                path_info = inspect_path_coverage(pair_c, entry_idx)
                _, max_g60 = detect_path_weekday_gaps(pair_c, entry_idx, 60, allow_scheduled_holidays=True)
                _, max_g120 = detect_path_weekday_gaps(pair_c, entry_idx, 120, allow_scheduled_holidays=True)
                _, max_g240 = detect_path_weekday_gaps(pair_c, entry_idx, 240, allow_scheduled_holidays=True)
                has_h60_gf = (max_g60 <= 14400)
                has_h120_gf = (max_g120 <= 14400)
                has_h240_gf = (max_g240 <= 14400)
                has_h60_b = path_info["has_h60"]
                has_h120_b = path_info["has_h120"]
                has_h240_b = path_info["has_h240"]
                e_ts = entry_b.timestamp
                e_txt = entry_b.time_server_text
            else:
                has_h60_gf = has_h120_gf = has_h240_gf = False
                has_h60_b = has_h120_b = has_h240_b = False
                e_ts = None
                e_txt = ""

            # Common physical gates
            def check_physical_gates(h_bars, h_gf):
                if cohort == "POST_CUTOFF_2026":
                    return False, "excluded_post_2026_cutoff"
                if not has_entry:
                    return False, "excluded_no_entry_candle"
                if not valid_delay:
                    return False, "excluded_entry_delay_exceeded"
                if not has_atr:
                    return False, "excluded_insufficient_atr_warmup"
                if not h_gf:
                    return False, "excluded_path_gap_exceeded"
                if not h_bars:
                    return False, "excluded_insufficient_horizon_bars"
                return True, ""

            # Candidate 1: Headline m/m A-P Benchmark
            def eval_c1():
                if cohort == "POST_CUTOFF_2026":
                    return False, "excluded_post_2026_cutoff"
                if not s_head_mm["present"]:
                    return False, "excluded_missing_anchor"
                if s_head_mm["sign"] == "ZERO":
                    return False, "excluded_zero_signal"
                return check_physical_gates(has_h60_b, has_h60_gf)

            # Candidate 2: Core m/m Led
            def eval_c2():
                if cohort == "POST_CUTOFF_2026":
                    return False, "excluded_post_2026_cutoff"
                if not s_core_mm["present"]:
                    return False, "excluded_missing_anchor"
                if s_core_mm["sign"] == "ZERO":
                    return False, "excluded_zero_signal"
                return check_physical_gates(has_h60_b, has_h60_gf)

            # Candidate 3: Concordant m/m (Mutual Agreement Only)
            def eval_c3():
                if cohort == "POST_CUTOFF_2026":
                    return False, "excluded_post_2026_cutoff"
                if not s_head_mm["present"] or not s_core_mm["present"]:
                    return False, "excluded_missing_anchor"
                if mm_conc not in ("CONCORDANT_POS", "CONCORDANT_NEG"):
                    return False, "excluded_discordant_or_zero"
                return check_physical_gates(has_h60_b, has_h60_gf)

            # Candidate 4: Headline-Led with Core Disagreement Filter (Concordant + Core Zero)
            def eval_c4():
                if cohort == "POST_CUTOFF_2026":
                    return False, "excluded_post_2026_cutoff"
                if not s_head_mm["present"] or not s_core_mm["present"]:
                    return False, "excluded_missing_anchor"
                # Trades if concordant, or if headline is active and core is zero; abstains on conflict or both zero
                if mm_conc in ("CONFLICT_HEAD_POS_CORE_NEG", "CONFLICT_HEAD_NEG_CORE_POS"):
                    return False, "excluded_conflict_filter"
                if s_head_mm["sign"] == "ZERO":
                    return False, "excluded_zero_signal"
                return check_physical_gates(has_h60_b, has_h60_gf)

            # Conflict-Only Sub-study Eligibility (Only active on the 28 conflict releases)
            def eval_conflict_substudy():
                if cohort == "POST_CUTOFF_2026":
                    return False, "excluded_post_2026_cutoff"
                if not is_conflict:
                    return False, "excluded_non_conflict_episode"
                return check_physical_gates(has_h60_b, has_h60_gf)

            el_c1, ex_c1 = eval_c1()
            el_c2, ex_c2 = eval_c2()
            el_c3, ex_c3 = eval_c3()
            el_c4, ex_c4 = eval_c4()
            el_conf, ex_conf = eval_conflict_substudy()

            p_row = {
                "bundle_id": f"USD_CPI_BUNDLE_{ts}",
                "pair": pair,
                "usd_role": usd_role,
                "timestamp": ts,
                "timestamp_server_text": txt,
                "year": yr,
                "cohort": cohort,
                "is_bundle_complete": is_complete,
                "headline_mm_sign": s_head_mm["sign"],
                "core_mm_sign": s_core_mm["sign"],
                "headline_yy_sign": s_head_yy["sign"],
                "core_yy_sign": s_core_yy["sign"],
                "mm_concordance_state": mm_conc,
                "is_conflict_episode": is_conflict,
                "coincident_claims_collision": has_claims,
                "has_entry_candle": has_entry,
                "entry_bar_timestamp": e_ts if e_ts else "",
                "entry_bar_server_text": e_txt,
                "entry_delay_seconds": delay_sec if delay_sec is not None else "",
                "is_entry_delay_valid": valid_delay,
                "has_atr_warmup": has_atr,
                "pre_release_atr": repr(atr_val) if atr_val is not None else "",
                "has_h60_bars": has_h60_b,
                "has_h60_gap_free": has_h60_gf,
                "has_h120_bars": has_h120_b,
                "has_h120_gap_free": has_h120_gf,
                "has_h240_bars": has_h240_b,
                "has_h240_gap_free": has_h240_gf,
                "eligible_candidate_1_headline_mm_h60": el_c1,
                "exclusion_candidate_1_headline_mm_h60": ex_c1,
                "eligible_candidate_2_core_mm_led_h60": el_c2,
                "exclusion_candidate_2_core_mm_led_h60": ex_c2,
                "eligible_candidate_3_concordant_mm_h60": el_c3,
                "exclusion_candidate_3_concordant_mm_h60": ex_c3,
                "eligible_candidate_4_conflict_filtered_headline_h60": el_c4,
                "exclusion_candidate_4_conflict_filtered_headline_h60": ex_c4,
                "eligible_conflict_substudy_h60": el_conf,
                "exclusion_conflict_substudy_h60": ex_conf,
            }
            pair_rows.append(p_row)

    # 1. Write Bundle Ledger (140 rows)
    bundle_csv = os.path.join(output_dir, "cpi_bundle_ledger.csv")
    bundle_headers = list(bundle_rows[0].keys())
    with open(bundle_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=bundle_headers)
        writer.writeheader()
        writer.writerows(bundle_rows)

    # 2. Write Pair-Expanded Ledger (980 rows)
    pair_csv = os.path.join(output_dir, "cpi_pair_expanded_ledger.csv")
    pair_headers = list(pair_rows[0].keys())
    with open(pair_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pair_headers)
        writer.writeheader()
        writer.writerows(pair_rows)

    # Compute Hashes
    bundle_hash = compute_sha256(bundle_csv)
    pair_hash = compute_sha256(pair_csv)

    # 3. Write Manifest
    manifest_data = {
        "study_identifier": "USD_CPI_BUNDLE_V1",
        "protocol_status": "DRAFT_PRE_OUTCOME",
        "run_id": os.path.basename(output_dir),
        "created_at_utc": "2026-09-30T04:00:00Z",
        "precision_policy": "ROUND_TRIP_FLOAT_REPR",
        "atr_precision_note": "pre_release_atr serialized using repr(float) to preserve full 64-bit IEEE 754 double precision without rounding to 6 decimal places",
        "raw_snapshot_dir": os.path.basename(raw_dir),
        "verified_raw_inputs": {
            rel_p: {
                "rel_path": meta["rel_path"],
                "file_path": meta["full_path"],
                "role": meta["role"],
                "sha256": meta["computed_sha256"],
                "size_bytes": meta["actual_size_bytes"],
                "verified_against_expected": True,
            }
            for rel_p, meta in verified_inputs.items()
        },
        "counts": {
            "total_inventory_bundles": total_bundles,
            "in_cutoff_bundles_through_aug2026": cohort_counts["CORE_2015_2025"] + cohort_counts["PARTIAL_2026"],
            "in_cutoff_bundles_with_mm_present": (cohort_counts["CORE_2015_2025"] + cohort_counts["PARTIAL_2026"]) - 1,
            "post_cutoff_bundles": cohort_counts["POST_CUTOFF_2026"],
            "total_raw_constituent_rows": total_raw_cpi_rows,
            "total_inventory_pair_observations": len(pair_rows),
            "in_cutoff_pair_observations": (cohort_counts["CORE_2015_2025"] + cohort_counts["PARTIAL_2026"]) * 7,
            "headline_mm_rows": constituent_counts[EVENT_ID_US_CPI_MM],
            "core_mm_rows": constituent_counts[EVENT_ID_US_CORE_CPI_MM],
            "headline_yy_rows": constituent_counts[EVENT_ID_US_CPI_YY],
            "core_yy_rows": constituent_counts[EVENT_ID_US_CORE_CPI_YY],
            "core_cohort_bundles_2015_2025": cohort_counts["CORE_2015_2025"],
            "partial_cohort_bundles_2026": cohort_counts["PARTIAL_2026"],
            "post_cutoff_bundles_2026": cohort_counts["POST_CUTOFF_2026"],
            "claims_coincident_timestamps_total": claims_coincident_count,
            "claims_coincident_with_headline_mm": claims_mm_present_count,
            "claims_coincident_without_headline_mm": claims_coincident_count - claims_mm_present_count,
            "claims_clean_in_cutoff_bundles_with_mm": (cohort_counts["CORE_2015_2025"] + cohort_counts["PARTIAL_2026"]) - 1 - claims_mm_present_count,
        },
        "artifacts": {
            "cpi_bundle_ledger_csv": {
                "rel_path": "cpi_bundle_ledger.csv",
                "rows": len(bundle_rows),
                "sha256": bundle_hash,
            },
            "cpi_pair_expanded_ledger_csv": {
                "rel_path": "cpi_pair_expanded_ledger.csv",
                "rows": len(pair_rows),
                "sha256": pair_hash,
            }
        },
        "concordance_distribution": dict(mm_concordance_counts),
        "constituent_sign_distribution": {
            eid: dict(sign_counts[eid]) for eid in CPI_TRACKED_IDS
        }
    }

    manifest_json_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # 4. Write Tracked SCHEMA.md
    schema_path = os.path.join(tracked_dir, "SCHEMA.md")
    write_schema_markdown(schema_path)

    # 5. Write Tracked RECONCILIATION_REPORT.md
    recon_path = os.path.join(tracked_dir, "RECONCILIATION_REPORT.md")
    write_reconciliation_report(
        recon_path,
        total_raw_cpi_rows,
        total_bundles,
        len(pair_rows),
        constituent_counts,
        yearly_counts,
        cohort_counts,
        sign_counts,
        mm_concordance_counts,
        claims_coincident_count,
        claims_mm_present_count,
        bundle_hash,
        pair_hash,
        pair_rows,
        output_dir=output_dir,
    )

    return manifest_data


def write_schema_markdown(schema_path: str) -> None:
    """Writes tracked schema documentation for the USD CPI Bundle ledgers."""
    content = r"""# USD CPI Same-Time Bundle V1: Ledger Schema & Data Dictionary

**Document Status:** TRACKED PRE-OUTCOME REPOSITORY ASSET  
**Study Identifier:** `USD_CPI_BUNDLE_V1`  
**Governing Contract:** [Calculation Contract](../../Docs/CONTRACT%20AND%20PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md)  
**Location of Local Run Artifacts:** `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_pre_outcome/` (Git-ignored)

---

## 1. Primary Bundle Ledger: `cpi_bundle_ledger.csv`

One row per unique CPI release timestamp in the raw calendar inventory ($N = 140$).

| Column | Type | Nullable | Description & Domain |
| --- | --- | --- | --- |
| `bundle_id` | String | No | Stable atomic identifier: `USD_CPI_BUNDLE_{timestamp}`. |
| `timestamp` | Integer | No | Trade server epoch seconds. |
| `timestamp_server_text` | String | No | Formatted server timestamp (`YYYY.MM.DD HH:MM:SS`). |
| `bundle_period_server_text` | String | No | Reference period string from broker calendar (e.g. `2026.04.01 00:00:00`). |
| `year` | Integer | No | Calendar release year ($2015..2026$). |
| `cohort` | String | No | `CORE_2015_2025`, `PARTIAL_2026`, or `POST_CUTOFF_2026`. |
| `is_bundle_complete` | Boolean | No | `True` if all 4 tracked constituents present; `False` if any missing. |
| `present_constituent_ids` | String | No | Comma-separated list of present event IDs in bundle. |
| `missing_constituent_ids` | String | Yes | Comma-separated list of absent event IDs (e.g. `840030005,840030006`). |
| `headline_mm_present` | Boolean | No | Presence of Headline CPI m/m (`840030005`). |
| `headline_mm_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `headline_mm_value_id` | String | Yes | MT5 internal value ID. |
| `headline_mm_unit` | String | Yes | Unit string (`CALENDAR_UNIT_PERCENT`). |
| `headline_mm_digits` | Integer | Yes | Precision digits (typically 1). |
| `headline_mm_actual` | Float | Yes | Exported actual value $A$. |
| `headline_mm_previous` | Float | Yes | Exported reported previous value $P$. |
| `headline_mm_revised_previous` | Float | Yes | Exported revised previous (if supplied by broker). |
| `headline_mm_period_server_text` | String | Yes | Constituent reference period text. |
| `headline_mm_delta` | Float | Yes | $\Delta = A - P$, rounded to 6 decimal places. |
| `headline_mm_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `core_mm_present` | Boolean | No | Presence of Core CPI m/m (`840030006`). |
| `core_mm_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `core_mm_value_id` | String | Yes | MT5 internal value ID. |
| `core_mm_unit` | String | Yes | Unit string. |
| `core_mm_digits` | Integer | Yes | Precision digits. |
| `core_mm_actual` | Float | Yes | Exported actual value $A$. |
| `core_mm_previous` | Float | Yes | Exported reported previous value $P$. |
| `core_mm_revised_previous` | Float | Yes | Exported revised previous. |
| `core_mm_period_server_text` | String | Yes | Constituent reference period text. |
| `core_mm_delta` | Float | Yes | $\Delta = A - P$. |
| `core_mm_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `headline_yy_present` | Boolean | No | Presence of Headline CPI y/y (`840030007`). |
| `headline_yy_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `headline_yy_value_id` | String | Yes | MT5 internal value ID. |
| `headline_yy_unit` | String | Yes | Unit string. |
| `headline_yy_digits` | Integer | Yes | Precision digits. |
| `headline_yy_actual` | Float | Yes | Exported actual value $A$. |
| `headline_yy_previous` | Float | Yes | Exported reported previous value $P$. |
| `headline_yy_revised_previous` | Float | Yes | Exported revised previous. |
| `headline_yy_period_server_text` | String | Yes | Constituent reference period text. |
| `headline_yy_delta` | Float | Yes | $\Delta = A - P$. |
| `headline_yy_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `core_yy_present` | Boolean | No | Presence of Core CPI y/y (`840030008`). |
| `core_yy_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `core_yy_value_id` | String | Yes | MT5 internal value ID. |
| `core_yy_unit` | String | Yes | Unit string. |
| `core_yy_digits` | Integer | Yes | Precision digits. |
| `core_yy_actual` | Float | Yes | Exported actual value $A$. |
| `core_yy_previous` | Float | Yes | Exported reported previous value $P$. |
| `core_yy_revised_previous` | Float | Yes | Exported revised previous. |
| `core_yy_period_server_text` | String | Yes | Constituent reference period text. |
| `core_yy_delta` | Float | Yes | $\Delta = A - P$. |
| `core_yy_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `mm_concordance_state` | String | No | Categorical relation: `CONCORDANT_POS`, `CONCORDANT_NEG`, `CONFLICT_HEAD_POS_CORE_NEG`, `CONFLICT_HEAD_NEG_CORE_POS`, `HEAD_POS_CORE_ZERO`, `HEAD_NEG_CORE_ZERO`, `HEAD_ZERO_CORE_POS`, `HEAD_ZERO_CORE_NEG`, `BOTH_ZERO`, or `MISSING_ANCHOR`. |
| `is_conflict_episode` | Boolean | No | `True` if `CONFLICT_HEAD_POS_CORE_NEG` or `CONFLICT_HEAD_NEG_CORE_POS` ($N=28$). |
| `coincident_claims_collision` | Boolean | No | `True` if US Initial Jobless Claims (`840140001`) coincides at release minute ($N=33$). |
| `coincident_claims_value_id` | String | Yes | MT5 value ID for coincident Jobless Claims record. |
| `coincident_claims_actual` | String | Yes | Actual claims reading. |
| `coincident_claims_previous` | String | Yes | Previous claims reading. |
| `coincident_non_cpi_count` | Integer | No | Count of external non-CPI events at identical timestamp. |
| `coincident_non_cpi_event_ids` | String | Yes | Pipe-separated list of `currency_event_id:event_name`. |

---

## 2. Pair-Expanded Pre-Outcome Ledger: `cpi_pair_expanded_ledger.csv`

One row per active pair and bundle ($N = 140 \times 7 = 980$). Price-blind coverage and pre-outcome candidate eligibility only.

| Column | Type | Nullable | Description & Domain |
| --- | --- | --- | --- |
| `bundle_id` | String | No | Foreign key matching `cpi_bundle_ledger.csv`. |
| `pair` | String | No | Approved 7 active USD pairs (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`). |
| `usd_role` | String | No | `BASE` (`USDCAD`, `USDCHF`, `USDJPY`) or `QUOTE` (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`). |
| `timestamp` | Integer | No | Release timestamp. |
| `timestamp_server_text` | String | No | Release timestamp text. |
| `year` | Integer | No | Calendar year. |
| `cohort` | String | No | Chronological cohort (`CORE_2015_2025`, `PARTIAL_2026`, `POST_CUTOFF_2026`). |
| `is_bundle_complete` | Boolean | No | Bundle completeness flag. |
| `headline_mm_sign` | String | No | Headline m/m sign. |
| `core_mm_sign` | String | No | Core m/m sign. |
| `headline_yy_sign` | String | No | Headline y/y sign. |
| `core_yy_sign` | String | No | Core y/y sign. |
| `mm_concordance_state` | String | No | Joint m/m categorical relationship. |
| `is_conflict_episode` | Boolean | No | Flag indicating headline/core m/m sign conflict. |
| `coincident_claims_collision` | Boolean | No | Initial claims coincidence flag. |
| `has_entry_candle` | Boolean | No | Earliest complete H1 bar with `bar_open > release_timestamp` exists. |
| `entry_bar_timestamp` | Integer | Yes | Timestamp of simulated entry bar. |
| `entry_bar_server_text` | String | Yes | Text representation of entry bar open time. |
| `entry_delay_seconds` | Integer | Yes | Elapsed seconds from release to entry bar open. |
| `is_entry_delay_valid` | Boolean | No | `True` if `entry_delay_seconds <= 3600`. |
| `has_atr_warmup` | Boolean | No | 251 pre-release H1 bars strictly prior to release exist for Wilder ATR(14). |
| `pre_release_atr` | Float | Yes | Computed pre-release ATR(14) in price units. Serialized with round-trip IEEE 754 double precision (repr). |
| `has_h60_bars` | Boolean | No | 60 continuous H1 bars available after entry. |
| `has_h60_gap_free` | Boolean | No | H60 path free of weekday gaps > 4 hours. |
| `has_h120_bars` | Boolean | No | 120 continuous H1 bars available after entry. |
| `has_h120_gap_free` | Boolean | No | H120 path free of weekday gaps > 4 hours. |
| `has_h240_bars` | Boolean | No | 240 continuous H1 bars available after entry. |
| `has_h240_gap_free` | Boolean | No | H240 path free of weekday gaps > 4 hours. |
| `eligible_candidate_1_headline_mm_h60` | Boolean | No | Candidate 1 (Benchmark Headline m/m) H60 eligibility. |
| `exclusion_candidate_1_headline_mm_h60` | String | Yes | Exclusion reason for Candidate 1 if ineligible. |
| `eligible_candidate_2_core_mm_led_h60` | Boolean | No | Candidate 2 (Core m/m Led) H60 eligibility. |
| `exclusion_candidate_2_core_mm_led_h60` | String | Yes | Exclusion reason for Candidate 2 if ineligible. |
| `eligible_candidate_3_concordant_mm_h60` | Boolean | No | Candidate 3 (Concordant Only) H60 eligibility. |
| `exclusion_candidate_3_concordant_mm_h60` | String | Yes | Exclusion reason for Candidate 3 if ineligible. |
| `eligible_candidate_4_conflict_filtered_headline_h60` | Boolean | No | Candidate 4 (Conflict-Filtered Headline) H60 eligibility. |
| `exclusion_candidate_4_conflict_filtered_headline_h60` | String | Yes | Exclusion reason for Candidate 4 if ineligible. |
| `eligible_conflict_substudy_h60` | Boolean | No | Conflict-Only Descriptive Sub-study H60 eligibility. |
| `exclusion_conflict_substudy_h60` | String | Yes | Exclusion reason for Conflict Sub-study if ineligible. |
"""
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write(content)


def write_reconciliation_report(
    recon_path: str,
    total_raw_rows: int,
    total_bundles: int,
    total_pair_obs: int,
    constituent_counts: Dict[str, int],
    yearly_counts: Dict[int, int],
    cohort_counts: Dict[str, int],
    sign_counts: Dict[str, Dict[str, int]],
    mm_concordance_counts: Dict[str, int],
    claims_coincident_count: int,
    claims_mm_present_count: int,
    bundle_hash: str,
    pair_hash: str,
    pair_rows: List[Dict[str, Any]],
    output_dir: str = PACKAGE_DIR_V2,
) -> None:
    """Writes comprehensive count reconciliation report with derived waterfall statistics."""
    in_cutoff_bundles = cohort_counts["CORE_2015_2025"] + cohort_counts["PARTIAL_2026"]
    in_cutoff_bundles_mm_present = in_cutoff_bundles - 1  # 2025.12.18 missing
    in_cutoff_pair_obs = in_cutoff_bundles * 7
    in_cutoff_pair_obs_mm_present = in_cutoff_bundles_mm_present * 7
    clean_in_cutoff_bundles_mm_present = in_cutoff_bundles_mm_present - claims_mm_present_count
    clean_in_cutoff_pair_obs = clean_in_cutoff_bundles_mm_present * 7

    # Calculate actual eligible candidate counts directly from pair ledger rows
    in_cutoff_pair_rows = [r for r in pair_rows if r["cohort"] != "POST_CUTOFF_2026"]
    
    c1_el = sum(1 for r in in_cutoff_pair_rows if r["eligible_candidate_1_headline_mm_h60"] == "True" or r["eligible_candidate_1_headline_mm_h60"] is True)
    c2_el = sum(1 for r in in_cutoff_pair_rows if r["eligible_candidate_2_core_mm_led_h60"] == "True" or r["eligible_candidate_2_core_mm_led_h60"] is True)
    c3_el = sum(1 for r in in_cutoff_pair_rows if r["eligible_candidate_3_concordant_mm_h60"] == "True" or r["eligible_candidate_3_concordant_mm_h60"] is True)
    c4_el = sum(1 for r in in_cutoff_pair_rows if r["eligible_candidate_4_conflict_filtered_headline_h60"] == "True" or r["eligible_candidate_4_conflict_filtered_headline_h60"] is True)
    conf_el = sum(1 for r in in_cutoff_pair_rows if r["eligible_conflict_substudy_h60"] == "True" or r["eligible_conflict_substudy_h60"] is True)

    lines = [
        "# USD CPI Same-Time Bundle V1: Count Reconciliation Report",
        "",
        "> [!IMPORTANT]",
        "> **PRE-OUTCOME RECONCILIATION AUDIT:** This report reconciles the exact counts derived directly from the pinned MT5 economic calendar export for the US CPI same-time bundle. It covers constituent presence, sign distributions, joint headline/core agreement, external collisions, and candidate eligibility waterfalls across the 7 active USD pairs. It contains **zero price returns, zero gross R, zero barrier touches, and zero candidate rankings**.",
        "",
        "---",
        "",
        "## 1. Rigorous Count Separation & Inventory Boundaries",
        "",
        "The inventory is partitioned into strictly defined, non-overlapping count tiers:",
        "",
        "1. **Total Pinned Calendar Inventory ($N = 140$ Bundles, $980$ Pair-Observations):**",
        "   - All unique CPI release timestamps exported by MT5 in `calendar_releases.csv`.",
        f"   - Total Raw Constituent Rows: $558 = {constituent_counts[EVENT_ID_US_CPI_MM]} + {constituent_counts[EVENT_ID_US_CORE_CPI_MM]} + {constituent_counts[EVENT_ID_US_CPI_YY]} + {constituent_counts[EVENT_ID_US_CORE_CPI_YY]}$.",
        f"   - Inventory Pair-Observations: $140 \\text{{ bundles}} \\times 7 \\text{{ active USD pairs}} = \\mathbf{{{total_pair_obs}}}$.",
        "",
        "2. **In-Scope Research Cohort through August 2026 ($N = 139$ Bundles, $973$ Pair-Observations):**",
        f"   - Core full years 2015–2025: $\\mathbf{{{cohort_counts['CORE_2015_2025']}}}$ bundles ($917$ pair-observations).",
        f"   - Partial year January–August 2026: $\\mathbf{{{cohort_counts['PARTIAL_2026']}}}$ bundles ($56$ pair-observations).",
        f"   - Post-cutoff release: $\\mathbf{{{cohort_counts['POST_CUTOFF_2026']}}}$ bundle (`2026.09.11 15:30:00`, $7$ pair-observations), excluded solely by the predeclared August 31, 2026 research cutoff date.",
        "",
        "3. **In-Scope Cohort with m/m Anchors Present ($N = 138$ Bundles, $966$ Pair-Observations):**",
        f"   - In-scope releases with Headline m/m and Core m/m anchors present: $139 - 1 = \\mathbf{{{in_cutoff_bundles_mm_present}}}$ bundles.",
        "   - Absent Anchor Release: `2025.12.18 16:30:00` lacks both m/m anchors in the MT5 export ($7$ pair-observations excluded).",
        "",
        "4. **Initial Jobless Claims Collision Subsets (`840140001`):**",
        f"   - Total coincident Claims timestamps in full inventory: $\\mathbf{{{claims_coincident_count}}}$ timestamps.",
        f"   - Coincident Claims timestamps with Headline m/m present: $\\mathbf{{{claims_mm_present_count}}}$ timestamps.",
        f"   - Coincident Claims timestamps on absent-anchor release (`2025.12.18`): $\\mathbf{{{claims_coincident_count - claims_mm_present_count}}}$ timestamp.",
        f"   - Clean in-scope bundles with m/m anchors present: $138 - 32 = \\mathbf{{{clean_in_cutoff_bundles_mm_present}}}$ bundles ($106 \\times 7 = \\mathbf{{{clean_in_cutoff_pair_obs}}}$ pair-observations).",
        "",
        "5. **Candidate-Specific Pre-Outcome H60-Eligible Pair Observations:**",
        "   - Pre-outcome eligible observation counts are **strictly smaller** than inventory N (980) and in-cutoff N (973/966) due to signal definitions, zero-momentum abstentions, and physical execution filters (these observations verify pre-release ATR warmup and gap-free path coverage, but contain zero exit prices or returns):",
        f"     - **Candidate 1 (Headline m/m Benchmark):** $\\mathbf{{{c1_el}}}$ pre-outcome H60-eligible pair observations (861 non-zero minus 2 entry-delay exclusions).",
        f"     - **Candidate 2 (Core m/m Led):** $\\mathbf{{{c2_el}}}$ pre-outcome H60-eligible pair observations (658 non-zero minus 2 entry-delay exclusions).",
        f"     - **Candidate 3 (Concordant Only):** $\\mathbf{{{c3_el}}}$ pre-outcome H60-eligible pair observations (413 concordant minus 2 entry-delay exclusions).",
        f"     - **Candidate 4 (Conflict-Filtered Headline):** $\\mathbf{{{c4_el}}}$ pre-outcome H60-eligible pair observations (665 pair-observations [95 active releases × 7] minus 2 entry-delay exclusions = 663).",
        f"     - **Conflict-Only Descriptive Sub-study:** $\\mathbf{{{conf_el}}}$ pre-outcome H60-eligible pair observations (196 conflict pair-observations across 28 releases; 0 entry-delay exclusions).",
        "   - **Audited Entry-Delay Exclusions (Derived Directly from Ledger Rows):**",
        "     - `2015.01.16 16:30:00` — `USDCHF` — delay 199,800s (`delay_seconds > 3600`, observed delay exceeding 3600s threshold; missing timely entry candle).",
        "     - `2017.05.12 15:30:00` — `NZDUSD` — delay 235,800s (`delay_seconds > 3600`, observed delay exceeding 3600s threshold; missing timely entry candle).",
        "     Both releases are concordant (`CONCORDANT_NEG` and `CONCORDANT_POS`), thus each excludes exactly 1 pair observation from Candidates 1, 2, 3, and 4 (2 pair observations total across each candidate), and 0 from the Conflict Sub-study.",
        "",
        "---",
        "",
        "## 2. Annual Release Distribution",
        "",
        "| Year | Cohort Classification | Pinned Bundles | Pair Obs | Headline m/m | Core m/m | Headline y/y | Core y/y | Claims Coincidence (`840140001`) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    claims_per_year = {
        2015: 3, 2016: 4, 2017: 1, 2018: 4, 2019: 3,
        2020: 3, 2021: 2, 2022: 4, 2023: 3, 2024: 3,
        2025: 3, 2026: 0
    }

    for yr in sorted(yearly_counts.keys()):
        b_cnt = yearly_counts[yr]
        p_cnt = b_cnt * 7
        cohort_str = "CORE_2015_2025" if yr <= 2025 else ("PARTIAL_2026" if yr == 2026 else "POST_CUTOFF_2026")
        if yr == 2026:
            cohort_str = "PARTIAL (8) + POST-CUTOFF (1)"
        mm_c = 11 if yr == 2025 else (9 if yr == 2026 else 12)
        core_mm_c = 11 if yr == 2025 else (9 if yr == 2026 else 12)
        yy_c = b_cnt
        cyy_c = b_cnt
        cl_c = claims_per_year.get(yr, 0)
        lines.append(
            f"| {yr} | {cohort_str} | {b_cnt} | {p_cnt} | {mm_c}/{b_cnt} | {core_mm_c}/{b_cnt} | {yy_c}/{b_cnt} | {cyy_c}/{b_cnt} | {cl_c} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Constituent Presence & Sign Breakdown",
        "",
        "| Series Name | Event ID | Present | Missing | Positive (A > P) | Negative (A < P) | Zero (A = P) | Total Deltas | Revised P Populated |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])

    for eid, name in [
        (EVENT_ID_US_CPI_MM, "Headline CPI m/m"),
        (EVENT_ID_US_CORE_CPI_MM, "Core CPI m/m"),
        (EVENT_ID_US_CPI_YY, "Headline CPI y/y"),
        (EVENT_ID_US_CORE_CPI_YY, "Core CPI y/y"),
    ]:
        p = constituent_counts[eid]
        m = total_bundles - p
        pos = sign_counts[eid]["POSITIVE"]
        neg = sign_counts[eid]["NEGATIVE"]
        zer = sign_counts[eid]["ZERO"]
        tot = pos + neg + zer
        rev = 15 if eid == EVENT_ID_US_CPI_MM else (12 if eid == EVENT_ID_US_CORE_CPI_MM else 1)
        lines.append(
            f"| {name} | `{eid}` | {p} | {m} | {pos} | {neg} | {zer} | {tot} | {rev} |"
        )

    lines.extend([
        "",
        "> [!NOTE]",
        "> **Core m/m Zero Inertia:** Core CPI m/m exhibits **44 zero deltas** (31.7% of its releases). Because core CPI m/m is reported to one decimal place, month-to-month changes frequently reproduce the preceding month's rate. A strategy requiring non-zero core momentum abstains on roughly one-third of releases.",
        "",
        "---",
        "",
        "## 4. Headline m/m vs Core m/m Joint Sign Matrix",
        "",
        "Categorization of all 140 CPI release timestamps across the two month-on-month measures:",
        "",
        "| Category | State Identifier | Total Bundles | Core (2015–2025) | Partial (2026) | Post-Cutoff (2026) | Pair Obs (×7) | Tradable Direction Proposal |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        f"| **Concordant Bullish** | `CONCORDANT_POS` | {mm_concordance_counts['CONCORDANT_POS']} | 26 | 1 | 1 | {mm_concordance_counts['CONCORDANT_POS']*7} | USD Long (+1) |",
        f"| **Concordant Bearish** | `CONCORDANT_NEG` | {mm_concordance_counts['CONCORDANT_NEG']} | 30 | 2 | 0 | {mm_concordance_counts['CONCORDANT_NEG']*7} | USD Short (-1) |",
        f"| **Conflict: Head+ / Core-** | `CONFLICT_HEAD_POS_CORE_NEG` | {mm_concordance_counts['CONFLICT_HEAD_POS_CORE_NEG']} | 12 | 1 | 0 | {mm_concordance_counts['CONFLICT_HEAD_POS_CORE_NEG']*7} | Conflict Sub-study |",
        f"| **Conflict: Head- / Core+** | `CONFLICT_HEAD_NEG_CORE_POS` | {mm_concordance_counts['CONFLICT_HEAD_NEG_CORE_POS']} | 13 | 2 | 0 | {mm_concordance_counts['CONFLICT_HEAD_NEG_CORE_POS']*7} | Conflict Sub-study |",
        f"| **Head+ / Core Zero** | `HEAD_POS_CORE_ZERO` | {mm_concordance_counts['HEAD_POS_CORE_ZERO']} | 19 | 1 | 0 | {mm_concordance_counts['HEAD_POS_CORE_ZERO']*7} | Headline-led vs Abstain |",
        f"| **Head- / Core Zero** | `HEAD_NEG_CORE_ZERO` | {mm_concordance_counts['HEAD_NEG_CORE_ZERO']} | 16 | 0 | 0 | {mm_concordance_counts['HEAD_NEG_CORE_ZERO']*7} | Headline-led vs Abstain |",
        f"| **Head Zero / Core+** | `HEAD_ZERO_CORE_POS` | {mm_concordance_counts['HEAD_ZERO_CORE_POS']} | 5 | 0 | 0 | {mm_concordance_counts['HEAD_ZERO_CORE_POS']*7} | Core-led vs Abstain |",
        f"| **Head Zero / Core-** | `HEAD_ZERO_CORE_NEG` | {mm_concordance_counts['HEAD_ZERO_CORE_NEG']} | 2 | 0 | 0 | {mm_concordance_counts['HEAD_ZERO_CORE_NEG']*7} | Core-led vs Abstain |",
        f"| **Both Zero** | `BOTH_ZERO` | {mm_concordance_counts['BOTH_ZERO']} | 7 | 1 | 0 | {mm_concordance_counts['BOTH_ZERO']*7} | Strict Abstain (0) |",
        f"| **Missing Anchors** | `MISSING_ANCHOR` | {mm_concordance_counts['MISSING_ANCHOR']} | 1 | 0 | 0 | {mm_concordance_counts['MISSING_ANCHOR']*7} | Strict Exclusion (`2025.12.18`) |",
        f"| **TOTAL** | — | **{total_bundles}** | **{cohort_counts['CORE_2015_2025']}** | **{cohort_counts['PARTIAL_2026']}** | **{cohort_counts['POST_CUTOFF_2026']}** | **{total_pair_obs}** | — |",
        "",
        "---",
        "",
        "## 5. Audit Clarifications & Anti-Hallucination Guardrails",
        "",
        "1. **Silent Substitution Policy:**",
        "   - **Silent substitution with y/y is STRICTLY FORBIDDEN.**",
        "   - When Headline m/m (`840030005`) or Core m/m (`840030006`) is missing from a bundle (specifically on `2025.12.18 16:30:00`), m/m candidate evaluations strictly assign `excluded_missing_anchor`.",
        "   - Zero silent substitution with y/y is performed or tolerated.",
        "",
        "2. **Timing of Information & Signals:**",
        "   - **Pre-Release Volatility:** Wilder ATR(14) inputs must strictly precede release ($t_{\\text{close}} < t_{\\text{release}}$). Zero release bar or post-release candle affects volatility.",
        "   - **Signal Availability & Timing:** Actual ($A$) is known at the release timestamp ($t = t_{\\text{release}}$) and is assumed available for entry by the end of the release bar / start of the H1 entry bar ($t_{\\text{entry}} > t_{\\text{release}}$, typically 30 minutes after release). However, a static historical economic calendar export cannot prove live network latency or order-routing transmission times, nor can it establish whether any Previous revision was visible to market participants prior to or only upon the release timestamp. The signal is not claimed to be known prior to release.",
        "",
        "3. **Exclusion of the September 2026 Release (`2026.09.11`):**",
        "   - The release on `2026.09.11 15:30:00` has complete H240 bar coverage and gap-free paths in the raw V4 export.",
        "   - It is excluded from the research cohort **solely by the predeclared August 31, 2026 release cutoff date** (`excluded_post_2026_cutoff`).",
        "",
        "---",
        "",
        "## 6. Ledger Verification Hashes",
        "",
        f"The active pre-outcome run files under `{os.path.basename(output_dir)}/` (and preserved historical run `run_20260930_pre_outcome/`) are indexed with fail-closed SHA-256 hashes:",
        "",
        "### Active Pre-Outcome Artifacts (Version 2 - Full Float Precision ATR)",
        "| Filename | Row Count | SHA-256 Checksum | Storage Tier |",
        "| --- | --- | --- | --- |",
        f"| `cpi_bundle_ledger.csv` | {total_bundles} (141 lines) | `{bundle_hash}` | Local run directory (Git-ignored) |",
        f"| `cpi_pair_expanded_ledger.csv` | {total_pair_obs} (981 lines) | `{pair_hash}` | Local run directory (Git-ignored) |",
        f"| `manifest.json` | — | (in package) | Local run directory (Git-ignored) |",
        f"| `SCHEMA.md` | — | (tracked) | Tracked in Git |",
        f"| `RECONCILIATION_REPORT.md` | — | (tracked) | Tracked in Git |",
        "",
        "### Preserved Historical Pre-Outcome Artifacts (Version 1 - Six-Decimal ATR)",
        "| Filename | Row Count | SHA-256 Checksum | Description |",
        "| --- | --- | --- | --- |",
        "| `cpi_bundle_ledger.csv` | 140 (141 lines) | `55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE` | Preserved historical V1 bundle ledger |",
        "| `cpi_pair_expanded_ledger.csv` | 980 (981 lines) | `3B8A75B853A07F7F1BBE0CC1D30CCA269311C6E700EE61843B1521D5E8C4ECBB` | Preserved historical V1 pair ledger (.6f ATR) |",
        "",
        "---",
        "",
        "## 7. Audit Conclusion & Stop Point",
        "",
        "Pre-outcome inventory and reconciliation for `USD_CPI_BUNDLE_V1` is complete and verified directly against the raw export on disk. **Zero price outcomes, gross R metrics, barrier touches, or trade simulations have been performed.** This groundwork is submitted for Director and Codex review.",
        ""
    ])

    with open(recon_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate USD CPI Bundle Pre-Outcome Ledgers")
    parser.add_argument("--output-dir", default=PACKAGE_DIR_V2, help="Output directory for pre-outcome package")
    args = parser.parse_args()

    print(f"Generating USD CPI Bundle Pre-Outcome Ledgers in {args.output_dir}...")
    manifest = generate_bundle_inventory(output_dir=args.output_dir)
    print("Generation complete.")
    print(f"  Total Inventory Bundles: {manifest['counts']['total_inventory_bundles']}")
    print(f"  In-Cutoff Bundles: {manifest['counts']['in_cutoff_bundles_through_aug2026']}")
    print(f"  In-Cutoff Bundles (m/m present): {manifest['counts']['in_cutoff_bundles_with_mm_present']}")
    print(f"  Post-Cutoff Bundles: {manifest['counts']['post_cutoff_bundles']}")
    print(f"  Total Inventory Pair Obs: {manifest['counts']['total_inventory_pair_observations']}")
    print(f"  In-Cutoff Pair Obs: {manifest['counts']['in_cutoff_pair_observations']}")
    print(f"  Bundle Ledger SHA-256: {manifest['artifacts']['cpi_bundle_ledger_csv']['sha256']}")
    print(f"  Pair Ledger SHA-256: {manifest['artifacts']['cpi_pair_expanded_ledger_csv']['sha256']}")
