"""Reusable Calendar and H1 Candle Loader for Fyodor Macro Research.

Enforces:
- Strict pair whitelist (19 active pairs; 9 excluded pairs strictly rejected)
- OHLC geometric validity and monotonic timestamps
- Atomic same-timestamp release bundling
- Safe handling of missing vs zero calendar values
- Zero outcome / price return calculations (strictly PRE-OUTCOME)
"""

import os
import csv
import json
from typing import Dict, List, Optional, Tuple, Set, Any

from models import CandleBar, CalendarRelease, ReleaseBundle
from protocol_specs import (
    ALL_EXPORTED_PAIRS,
    GLOBALLY_EXCLUDED_PAIRS,
    ACTIVE_RESEARCH_PAIRS,
    ACTIVE_USD_PAIRS,
    CPI_CONSTITUENT_IDS,
    NFP_CONSTITUENT_IDS,
)

DEFAULT_RAW_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "raw_data",
        "FyodorResearchExport_v4_20260928_021936_79538281_server",
    )
)


def assert_pair_active(symbol: str) -> None:
    """Raises ValueError if a symbol is in the globally excluded set."""
    if symbol in GLOBALLY_EXCLUDED_PAIRS:
        raise ValueError(
            f"Symbol '{symbol}' is globally excluded from research due to truncated history. "
            f"It must never be admitted into active candidate or trade denominators."
        )
    if symbol not in ACTIVE_RESEARCH_PAIRS:
        raise ValueError(f"Symbol '{symbol}' is not recognized in the approved 19-pair active universe.")


def parse_optional_float(val: str) -> Optional[float]:
    """Parses a float string, strictly distinguishing empty string / missing from 0.0."""
    val = val.strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def load_manifest(raw_dir: str = DEFAULT_RAW_DIR) -> Dict[str, str]:
    """Loads manifest.csv key-value pairs."""
    manifest_path = os.path.join(raw_dir, "manifest.csv")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
        
    res = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= 2:
                res[row[0]] = row[1]
    return res


def load_candle_symbols(raw_dir: str = DEFAULT_RAW_DIR) -> Dict[str, Dict[str, Any]]:
    """Loads candle_symbols.csv records keyed by canonical symbol."""
    path = os.path.join(raw_dir, "candle_symbols.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"candle_symbols.csv not found at {path}")
        
    res = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            res[row["canonical_symbol"]] = row
    return res


def load_candles(
    symbol: str,
    raw_dir: str = DEFAULT_RAW_DIR,
    allow_excluded_for_audit: bool = False,
    validate_ohlc: bool = True,
) -> List[CandleBar]:
    """Loads H1 candle bars for a symbol.
    
    Args:
        symbol: Canonical FX pair name.
        raw_dir: Path to raw export root directory.
        allow_excluded_for_audit: If False, raises ValueError for excluded pairs.
        validate_ohlc: If True, validates bar geometry and timestamp monotonicity.
        
    Returns:
        List of verified CandleBar instances.
    """
    if not allow_excluded_for_audit:
        assert_pair_active(symbol)
        
    file_path = os.path.join(raw_dir, "candles", f"candles_{symbol}_H1.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Candle file not found for {symbol} at {file_path}")
        
    bars: List[CandleBar] = []
    prev_ts = -1
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_num, row in enumerate(reader, start=2):
            ts = int(row["time"])
            open_p = float(row["open"])
            high_p = float(row["high"])
            low_p = float(row["low"])
            close_p = float(row["close"])
            tick_vol = int(row["tick_volume"])
            spread = int(row["spread"])
            real_vol = int(row["real_volume"])
            sym = row["source_symbol"]
            ts_text = row["time_server_text"]
            complete = row["complete_at_export"].lower() == "true"
            
            bar = CandleBar(
                timestamp=ts,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                tick_volume=tick_vol,
                spread=spread,
                real_volume=real_vol,
                symbol=sym,
                time_server_text=ts_text,
                complete_at_export=complete,
            )
            
            if validate_ohlc:
                if not bar.validate_ohlc():
                    raise ValueError(
                        f"OHLC violation at {symbol} line {line_num} ({ts_text}): "
                        f"O={open_p}, H={high_p}, L={low_p}, C={close_p}"
                    )
                if ts <= prev_ts:
                    raise ValueError(
                        f"Non-monotonic or duplicate timestamp at {symbol} line {line_num}: "
                        f"current={ts} ({ts_text}), previous={prev_ts}"
                    )
                    
            prev_ts = ts
            bars.append(bar)
            
    return bars


def load_calendar_releases(
    currency: str = "USD",
    raw_dir: str = DEFAULT_RAW_DIR,
) -> List[CalendarRelease]:
    """Loads all calendar releases for a specific currency."""
    path = os.path.join(raw_dir, "calendar_releases.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"calendar_releases.csv not found at {path}")
        
    releases: List[CalendarRelease] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["currency"] != currency:
                continue
                
            rel = CalendarRelease(
                event_id=row["event_id"],
                value_id=row["value_id"],
                timestamp=int(row["timestamp"]),
                timestamp_server_text=row["timestamp_server_text"],
                currency=row["currency"],
                country_code=row["country_code"],
                event_name=row["event_name"],
                importance=row["importance"],
                actual=parse_optional_float(row["actual"]),
                forecast=parse_optional_float(row["forecast"]),
                previous=parse_optional_float(row["previous"]),
                revised_previous=parse_optional_float(row["revised_previous"]),
                period_server_text=row["period_server_text"],
                unit=row["unit"],
                unit_code=int(row["unit_code"]) if "unit_code" in row and row["unit_code"] else 0,
                multiplier=row["multiplier"],
                multiplier_code=int(row["multiplier_code"]) if "multiplier_code" in row and row["multiplier_code"] else 0,
                digits=int(row["digits"]) if "digits" in row and row["digits"] else 0,
                raw_actual_str=row["actual"],
                raw_forecast_str=row["forecast"],
                raw_previous_str=row["previous"],
                raw_revised_previous_str=row["revised_previous"],
            )
            releases.append(rel)
            
    return releases


def load_all_releases_by_timestamp(
    raw_dir: str = DEFAULT_RAW_DIR,
) -> Dict[int, List[CalendarRelease]]:
    """Loads releases indexed by timestamp across ALL currencies to identify cross-currency collisions."""
    path = os.path.join(raw_dir, "calendar_releases.csv")
    releases_by_ts: Dict[int, List[CalendarRelease]] = {}
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = int(row["timestamp"])
            rel = CalendarRelease(
                event_id=row["event_id"],
                value_id=row["value_id"],
                timestamp=ts,
                timestamp_server_text=row["timestamp_server_text"],
                currency=row["currency"],
                country_code=row["country_code"],
                event_name=row["event_name"],
                importance=row["importance"],
                actual=parse_optional_float(row["actual"]),
                forecast=parse_optional_float(row["forecast"]),
                previous=parse_optional_float(row["previous"]),
                revised_previous=parse_optional_float(row["revised_previous"]),
                period_server_text=row["period_server_text"],
                unit=row["unit"],
                unit_code=int(row["unit_code"]) if "unit_code" in row and row["unit_code"] else 0,
                multiplier=row["multiplier"],
                multiplier_code=int(row["multiplier_code"]) if "multiplier_code" in row and row["multiplier_code"] else 0,
                digits=int(row["digits"]) if "digits" in row and row["digits"] else 0,
                raw_actual_str=row["actual"],
                raw_forecast_str=row["forecast"],
                raw_previous_str=row["previous"],
                raw_revised_previous_str=row["revised_previous"],
            )
            if ts not in releases_by_ts:
                releases_by_ts[ts] = []
            releases_by_ts[ts].append(rel)
            
    return releases_by_ts


def create_release_bundles(
    family: str,
    target_event_ids: Set[str],
    currency_releases: List[CalendarRelease],
    all_releases_by_ts: Optional[Dict[int, List[CalendarRelease]]] = None,
) -> List[ReleaseBundle]:
    """Groups releases into atomic same-timestamp bundles for a specified family."""
    # Group target releases by timestamp
    bundles_map: Dict[int, ReleaseBundle] = {}
    
    for r in currency_releases:
        if r.event_id in target_event_ids:
            ts = r.timestamp
            if ts not in bundles_map:
                bundles_map[ts] = ReleaseBundle(
                    timestamp=ts,
                    timestamp_server_text=r.timestamp_server_text,
                    currency=r.currency,
                    family=family,
                )
            bundles_map[ts].constituents[r.event_id] = r
            
    # Attach coincident external releases if supplied
    if all_releases_by_ts:
        for ts, bundle in bundles_map.items():
            if ts in all_releases_by_ts:
                # Include releases not in the bundle's own constituents
                coincident = [
                    x for x in all_releases_by_ts[ts]
                    if x.event_id not in bundle.constituents
                ]
                bundle.coincident_releases = coincident
                
    # Return sorted by timestamp
    return [bundles_map[ts] for ts in sorted(bundles_map.keys())]
