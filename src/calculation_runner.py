"""
Auditable Calculation Runner & Output Schema for US Retail Sales EURUSD
Pre-price directional strategy viability calculation runner, H1-to-H4 bar aggregation,
trade execution engine across 5 frozen cost scenarios, and deterministic output schema.

CRITICAL RESEARCH INTEGRITY GOVERNANCE & FILE BOUNDARY DISCLOSURES:
- Default discussion and read-only state. Candidate prices remain sealed prior to formal protocol freeze.
- Empirical execution on pinned candidate candle prices is strictly prohibited prior to formal freeze.
- Post-2022 holdout data (timestamp >= 1672531200) is strictly sealed during pre-2023 discovery.
- File Boundary Disclosures (No byte-level non-reading claim):
  1. Full-file SHA-256 hashing reads all raw bytes from byte 0 to EOF, including the post-2022
     holdout portion, but treats data strictly as an opaque binary stream without parsing prices
     or inspecting outcomes.
  2. The CSV calculation path buffers the raw text of the first post-split line into memory,
     but inspects field 0 before tokenizing and breaks immediately: post-split price columns
     are never parsed, converted to floats, or analyzed.
- Zero synthetic data, zero outcome faking, zero lookahead.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
import math
import os
import json
from datetime import datetime, timezone
import bisect
import hashlib
import subprocess

from .parsers import SPLIT_TIMESTAMP, stream_calendar_releases
from .candle_coverage import (
    SECONDS_IN_H1,
    SECONDS_IN_H4,
    is_valid_weekend_market_closure
)
from .package_ledger import (
    HEADLINE_EID,
    CORE_EID,
    compute_entry_timestamp,
    build_retail_sales_package_ledger
)
from .strategy_viability import (
    EURUSD_DIGITS,
    EURUSD_POINT,
    EURUSD_POINTS_PER_PIP,
    FROZEN_COST_SCENARIOS,
    compute_executable_trade_prices,
    compute_directional_log_return,
    compute_directional_profit_pips,
    compute_1sample_viability_statistics,
    classify_discovery_outcome
)

RUNNER_IMPLEMENTATION_VERSION = "1.1.0"
SCHEMA_VERSION = "1.1.0"
PROTOCOL_REFERENCE = "docs/DRAFT_RETAIL_SALES_PROTOCOL.md"
DEFAULT_INSTRUMENT = "EURUSD"
PINNED_CANDLE_FILENAME = "candles_EURUSD_H1.csv"
HARD_SPLIT_TIMESTAMP = SPLIT_TIMESTAMP  # 1672531200 (2023-01-01 00:00:00 broker server time)
GIT_COMMIT_BASELINE = "dc35609"  # Historical parent commit; dynamic inspection used for implementation identity

# Expected pinned sources specified in the frozen protocol
EXPECTED_PINNED_SOURCES = {
    "calendar_releases": {
        "path": "data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv",
        "sha256": "76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e"
    },
    "raw_candles_eurusd": {
        "path": "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv",
        "sha256": "893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5"
    },
    "prior_inventory": {
        "path": "evidence/inventory/fms_episodes.jsonl",
        "sha256": "37df7880a2bc36dbbce06b4a6ba39f7bd962a4c1c92eb2ce64cb71a886de55d2"
    }
}


def compute_file_sha256(filepath: str) -> str:
    """
    Computes SHA-256 cryptographic digest of a file on disk reading in 64KB binary chunks.

    FORENSIC BOUNDARY DISCLOSURE (NO BYTE-LEVEL NON-READING CLAIM):
    Full-file SHA-256 hashing reads all raw bytes of the file from byte 0 to EOF,
    including the post-2022 holdout portion of the file. However, this process treats
    the file strictly as an opaque stream of raw binary bytes: it does NOT parse ASCII/UTF-8
    text, does NOT tokenize CSV rows or columns, does NOT convert or decode OHLC prices,
    and does NOT inspect trade returns or outcomes.
    We do NOT claim byte-level non-reading for cryptographic hashing; full-file integrity
    verification inherently requires hashing the entire file.
    """
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_implementation_provenance() -> Dict[str, Any]:
    """
    Dynamically inspects Git repository state to record the exact implementation identity.
    Git cleanliness reports strictly Git working tree state (COMMITTED_CLEAN vs UNCOMMITTED_CHANGES).
    Formal protocol freeze approval is never inferred from Git status and is recorded separately
    by human/Codex audit review before execution.
    """
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    try:
        res_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, cwd=repo_dir
        )
        head_commit = res_head.stdout.strip()
    except Exception:
        head_commit = "UNKNOWN"

    try:
        res_status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, cwd=repo_dir
        )
        status_lines = [l for l in res_status.stdout.strip().splitlines() if l.strip()]
        is_dirty = len(status_lines) > 0
    except Exception:
        is_dirty = True

    git_checkout_state = "COMMITTED_CLEAN" if (not is_dirty and head_commit != "UNKNOWN") else "UNCOMMITTED_CHANGES"

    return {
        "runner_implementation_version": RUNNER_IMPLEMENTATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "git_checkout_state": git_checkout_state,
        "git_head_commit": head_commit,
        "git_status_clean": not is_dirty,
        "has_uncommitted_changes": is_dirty
    }

# Frozen pre-2023 candidate package accounting totals
FROZEN_TOTAL_PACKAGES = 96
FROZEN_STRICT_COUNT = 49
FROZEN_STRICT_POS = 27
FROZEN_STRICT_NEG = 22
FROZEN_MISSING_FORECAST = 28
FROZEN_ACTIVE_CONFLICT = 9
FROZEN_BOTH_ZERO = 2
FROZEN_ONE_ZERO = 8

VALID_SIGN_CATEGORIES = {
    "STRICT_AGREE_POS",
    "STRICT_AGREE_NEG",
    "MISSING_FORECAST",
    "ACTIVE_CONFLICT",
    "BOTH_ZERO",
    "ONE_ZERO"
}


@dataclass(frozen=True)
class CandleBar:
    """
    Typed, immutable representation of a single H1 candle bar.
    Strictly validates timestamp, price bounds, spread, and volumes.
    """
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    spread: int = 0
    tick_volume: int = 0
    real_volume: int = 0

    def __post_init__(self):
        if isinstance(self.timestamp, bool) or not isinstance(self.timestamp, int):
            raise TypeError(f"timestamp must be an integer, got {type(self.timestamp).__name__}")

        for field_name in ("open", "high", "low", "close"):
            val = getattr(self, field_name)
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise TypeError(f"{field_name} must be numeric, got {type(val).__name__}")
            f_val = float(val)
            if math.isnan(f_val) or math.isinf(f_val) or f_val <= 0.0:
                raise ValueError(f"{field_name} must be a finite positive number, got {val}")

        if self.high < self.low:
            raise ValueError(f"high ({self.high}) cannot be less than low ({self.low})")
        if self.high < max(self.open, self.close):
            raise ValueError(f"high ({self.high}) cannot be less than open ({self.open}) or close ({self.close})")
        if self.low > min(self.open, self.close):
            raise ValueError(f"low ({self.low}) cannot be greater than open ({self.open}) or close ({self.close})")

        if isinstance(self.spread, bool) or not isinstance(self.spread, int) or self.spread < 0:
            raise ValueError(f"spread must be a non-negative integer, got {self.spread}")

        if isinstance(self.tick_volume, bool) or not isinstance(self.tick_volume, int) or self.tick_volume < 0:
            raise ValueError(f"tick_volume must be a non-negative integer, got {self.tick_volume}")

        if isinstance(self.real_volume, bool) or not isinstance(self.real_volume, int) or self.real_volume < 0:
            raise ValueError(f"real_volume must be a non-negative integer, got {self.real_volume}")


class CandlePriceIndex:
    """
    In-memory store of valid H1 candle bars.
    Strictly seals timestamps >= split_timestamp (1672531200) during pre-2023 discovery.
    Validates monotonicity, rejects duplicates, and provides H4 block and forward horizon resolution
    using an explicit weekend market-closure rule.
    """
    def __init__(
        self,
        bars: Optional[List[CandleBar]] = None,
        split_timestamp: int = HARD_SPLIT_TIMESTAMP
    ):
        if split_timestamp > HARD_SPLIT_TIMESTAMP:
            raise PermissionError(
                f"Cannot override split boundary beyond {HARD_SPLIT_TIMESTAMP} during pre-2023 discovery."
            )
        self.split_timestamp = split_timestamp
        self._bars_by_ts: Dict[int, CandleBar] = {}
        self._sorted_timestamps: List[int] = []
        self.source_metadata: Dict[str, Any] = {
            "source_type": "SYNTHETIC_FIXTURE",
            "source_description": "In-memory CandleBar fixture list",
            "source_path": None,
            "source_sha256": None,
            "pinned_source_verified": False
        }

        if bars:
            self._load_bars(bars)

    def _load_bars(self, bars: List[CandleBar]) -> None:
        prev_ts: Optional[int] = None
        for bar in bars:
            if bar.timestamp >= self.split_timestamp:
                raise PermissionError(
                    f"Timestamp {bar.timestamp} crosses into the strictly sealed post-2022 holdout "
                    f"(split={self.split_timestamp}). Access denied during pre-2023 discovery."
                )
            if bar.timestamp in self._bars_by_ts:
                raise ValueError(f"Duplicate candle timestamp encountered: {bar.timestamp}")
            if prev_ts is not None and bar.timestamp <= prev_ts:
                raise ValueError(
                    f"Candle timestamps must be strictly monotonically increasing. Found {prev_ts} >= {bar.timestamp}"
                )
            self._bars_by_ts[bar.timestamp] = bar
            self._sorted_timestamps.append(bar.timestamp)
            prev_ts = bar.timestamp

    @classmethod
    def from_bars(
        cls,
        bars: List[CandleBar],
        split_timestamp: int = HARD_SPLIT_TIMESTAMP,
        source_description: str = "In-memory CandleBar fixture list"
    ) -> "CandlePriceIndex":
        """Constructs an index from an explicit list of CandleBar objects."""
        index = cls(bars=bars, split_timestamp=split_timestamp)
        index.source_metadata = {
            "source_type": "SYNTHETIC_FIXTURE",
            "source_description": source_description,
            "source_path": None,
            "source_sha256": None,
            "pinned_source_verified": False
        }
        return index

    @classmethod
    def from_csv(
        cls,
        filepath: str,
        split_timestamp: int = HARD_SPLIT_TIMESTAMP,
        allow_unblinded_run: bool = False
    ) -> "CandlePriceIndex":
        """
        Parses candle bars from a CSV file.
        Enforces safety guard: reading pinned candidate candle files is forbidden unless
        allow_unblinded_run=True is explicitly supplied.

        PHYSICAL FILE I/O BOUNDARY DISCLOSURE:
        Standard Python file stream iteration (`for line in f:` / `f.readline()`) buffers
        the entire line of text into memory up to the newline character. For the first
        post-split row encountering timestamp >= split_timestamp, the raw text of that
        line is buffered into Python memory before column 0 can be inspected.
        We do NOT claim a byte-level hardware or OS kernel isolation boundary that ceases
        disk reads prior to the newline.

        LOGICAL PARSING ISOLATION:
        Before tokenizing the line or parsing columns 1..N, the runner extracts solely
        the field-0 substring before the first comma (`line[:comma_idx]`) and parses
        it as an integer timestamp. If `ts >= split_timestamp`, the loop halts immediately
        (`break`). Columns 1..N (Bid/Ask OHLC prices, tick volumes, spreads, real volumes)
        of post-split rows are NEVER parsed as floats or ints, NEVER stored in data structures,
        and NEVER exposed to any strategy logic, indicator, or return calculation.
        """
        if split_timestamp > HARD_SPLIT_TIMESTAMP:
            raise PermissionError(
                f"Cannot override split boundary beyond {HARD_SPLIT_TIMESTAMP} during pre-2023 discovery."
            )

        norm_path = os.path.normpath(filepath).replace("\\", "/")
        if not allow_unblinded_run:
            if "data/pinned" in norm_path or PINNED_CANDLE_FILENAME in norm_path:
                raise PermissionError(
                    "Unblinded empirical execution on pinned candidate candle prices is strictly prohibited "
                    "prior to protocol freeze. Pinned candidate prices remain sealed."
                )

        # Compute SHA-256 of the CSV file actually used
        actual_sha256 = compute_file_sha256(filepath)
        expected_pinned_sha = EXPECTED_PINNED_SOURCES["raw_candles_eurusd"]["sha256"]
        is_verified_pinned = (actual_sha256 == expected_pinned_sha)

        bars: List[CandleBar] = []
        with open(filepath, "r", encoding="utf-8") as f:
            header_line = f.readline()
            if not header_line:
                raise ValueError(f"Empty candle file: {filepath}")

            cols = [c.strip() for c in header_line.split(",")]
            expected_prefix = ["time", "open", "high", "low", "close"]
            for idx, exp in enumerate(expected_prefix):
                if idx >= len(cols) or cols[idx] != exp:
                    raise ValueError(
                        f"Expected column {idx} to be '{exp}', got '{cols[idx] if idx < len(cols) else 'EOF'}'"
                    )

            for line_num, line in enumerate(f, start=2):
                line = line.strip()
                if not line:
                    continue

                # Inspect column 0 BEFORE parsing any other columns or price data
                comma_idx = line.find(",")
                ts_str = line[:comma_idx] if comma_idx != -1 else line
                try:
                    ts = int(ts_str)
                except ValueError:
                    raise ValueError(f"Line {line_num}: Malformed timestamp field '{ts_str}'")

                # Logical parsing isolation barrier:
                # Standard Python file I/O buffered the raw text of this line into memory,
                # but solely column 0 was converted to integer timestamp.
                # Because ts >= split_timestamp, the loop breaks immediately:
                # columns 1..N of this post-split row are never parsed, converted, or stored.
                if ts >= split_timestamp:
                    break

                parts = line.split(",")
                if len(parts) < 5:
                    raise ValueError(f"Line {line_num}: Insufficient candle fields (expected >= 5, got {len(parts)})")

                o = float(parts[1])
                h = float(parts[2])
                l = float(parts[3])
                c = float(parts[4])
                spread = int(parts[6]) if len(parts) > 6 and parts[6] != "" else 0
                tick_vol = int(parts[5]) if len(parts) > 5 and parts[5] != "" else 0
                real_vol = int(parts[7]) if len(parts) > 7 and parts[7] != "" else 0

                bars.append(CandleBar(
                    timestamp=ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    spread=spread,
                    tick_volume=tick_vol,
                    real_volume=real_vol
                ))

        source_type = "PINNED_SOURCE" if is_verified_pinned else "NON_PINNED_INPUT"
        index = cls(bars=bars, split_timestamp=split_timestamp)
        index.source_metadata = {
            "source_type": source_type,
            "source_description": os.path.basename(filepath),
            "source_path": norm_path,
            "source_sha256": actual_sha256,
            "pinned_source_verified": is_verified_pinned
        }
        return index

    def has_bar(self, ts: int) -> bool:
        return ts in self._bars_by_ts

    def get_bar(self, ts: int) -> CandleBar:
        if ts not in self._bars_by_ts:
            raise KeyError(f"Candle bar at timestamp {ts} not found in index")
        return self._bars_by_ts[ts]

    def check_h4_block(self, h4_start_ts: int) -> Tuple[bool, List[CandleBar], List[int]]:
        """
        An H4 block starting at h4_start_ts requires 4 consecutive constituent H1 bars:
        [h4_start_ts, h4_start_ts + 3600, h4_start_ts + 7200, h4_start_ts + 10800].
        Returns (is_complete, constituent_bars, missing_offsets).
        """
        if h4_start_ts % SECONDS_IN_H4 != 0:
            raise ValueError(f"Timestamp {h4_start_ts} is not aligned to an H4 boundary (mod 14400 != 0)")

        missing: List[int] = []
        bars: List[CandleBar] = []
        for offset in [0, 3600, 7200, 10800]:
            ts = h4_start_ts + offset
            if ts >= self.split_timestamp:
                missing.append(offset)
            elif ts not in self._bars_by_ts:
                missing.append(offset)
            else:
                bars.append(self._bars_by_ts[ts])

        return (len(missing) == 0, bars, missing)

    def resolve_horizon_bars(
        self,
        entry_ts: int,
        horizon_h4: int
    ) -> Dict[str, Any]:
        """
        Resolves forward active H4 blocks for horizon_h4 starting at entry_ts.
        Steps across valid weekend closures using an explicit market closure rule.
        Fails closed on missing constituent bars, unexpected weekday gaps, or split crossings.
        """
        if entry_ts % SECONDS_IN_H4 != 0:
            raise ValueError(f"Entry timestamp {entry_ts} is not aligned to an H4 boundary")

        current_h4 = entry_ts
        completed_blocks = 0
        crosses_weekend = False
        crosses_split = False
        has_missing_h1 = False
        missing_ts: List[int] = []
        blocks_bars: List[List[CandleBar]] = []

        max_search = horizon_h4 * 4

        for _ in range(max_search):
            if completed_blocks == horizon_h4:
                break

            if current_h4 >= self.split_timestamp:
                crosses_split = True
                break

            is_complete, bars, missing = self.check_h4_block(current_h4)

            if is_complete:
                completed_blocks += 1
                blocks_bars.append(bars)
                current_h4 += SECONDS_IN_H4
            else:
                if current_h4 not in self._bars_by_ts:
                    idx = bisect.bisect_right(self._sorted_timestamps, current_h4)
                    if idx >= len(self._sorted_timestamps):
                        has_missing_h1 = True
                        break
                    next_avail_ts = self._sorted_timestamps[idx]

                    # Test explicit market closure rule (rejects weekday data gaps)
                    is_weekend, reason = is_valid_weekend_market_closure(current_h4, next_avail_ts)

                    if is_weekend:
                        crosses_weekend = True
                        current_h4 = (next_avail_ts // SECONDS_IN_H4) * SECONDS_IN_H4
                    else:
                        has_missing_h1 = True
                        missing_ts.append(current_h4)
                        break
                else:
                    has_missing_h1 = True
                    missing_ts.extend([current_h4 + off for off in missing])
                    break

        is_clean = (
            completed_blocks == horizon_h4 and
            not has_missing_h1 and
            not crosses_split
        )

        entry_bar = blocks_bars[0][0] if is_clean else None
        exit_bar = blocks_bars[-1][3] if is_clean else None
        exit_boundary_ts = current_h4 if is_clean else None

        return {
            "horizon_h4": horizon_h4,
            "is_complete": is_clean,
            "completed_blocks": completed_blocks,
            "entry_timestamp": entry_ts,
            "exit_timestamp": exit_boundary_ts,
            "entry_bar": entry_bar,
            "exit_bar": exit_bar,
            "crosses_weekend": crosses_weekend,
            "crosses_split": crosses_split,
            "has_missing_h1": has_missing_h1,
            "missing_timestamps": missing_ts,
            "blocks_bars": blocks_bars
        }


def execute_single_trade_across_scenarios(
    entry_bar: CandleBar,
    exit_bar: CandleBar,
    direction: int,
    point_size: float = EURUSD_POINT,
    points_per_pip: int = EURUSD_POINTS_PER_PIP
) -> Dict[str, Dict[str, Any]]:
    """
    Executes a single directional trade across all 5 frozen cost scenarios A through E.
    Returns dictionary keyed by scenario ID with net_return, net_pips, is_win, entry_price, exit_price.
    """
    results: Dict[str, Dict[str, Any]] = {}
    for sc_id, sc_meta in FROZEN_COST_SCENARIOS.items():
        spread_pts = sc_meta["points"]
        entry_p, exit_p = compute_executable_trade_prices(
            entry_bid=entry_bar.open,
            exit_bid=exit_bar.close,
            direction=direction,
            spread_points=spread_pts,
            point_size=point_size
        )
        net_ret = compute_directional_log_return(
            entry_bid=entry_bar.open,
            exit_bid=exit_bar.close,
            direction=direction,
            spread_points=spread_pts,
            point_size=point_size
        )
        net_pips = compute_directional_profit_pips(
            entry_bid=entry_bar.open,
            exit_bid=exit_bar.close,
            direction=direction,
            spread_points=spread_pts,
            point_size=point_size,
            points_per_pip=points_per_pip
        )
        results[sc_id] = {
            "scenario_points": spread_pts,
            "scenario_pips": sc_meta["pips"],
            "entry_price": entry_p,
            "exit_price": exit_p,
            "net_return": net_ret,
            "net_pips": net_pips,
            "is_win": net_ret > 0.0
        }
    return results


def summarize_trade_metrics(
    trades_scenarios: List[Dict[str, Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Computes 1-sample statistics and summary metrics across all 5 scenarios
    for a given list of trade scenario outputs.
    Handles zero sample variance by populating std_dev=0.0 and setting undefined t-statistic/p-value to None.
    """
    summary: Dict[str, Any] = {}
    for sc_id in FROZEN_COST_SCENARIOS.keys():
        returns = [t[sc_id]["net_return"] for t in trades_scenarios]
        pips = [t[sc_id]["net_pips"] for t in trades_scenarios]
        n = len(returns)

        if n >= 2:
            try:
                stats = compute_1sample_viability_statistics(returns)
                summary[sc_id] = {
                    "sample_size": n,
                    "mean_net_return": stats["mean_return"],
                    "mean_net_pips": sum(pips) / n,
                    "std_dev": stats["std_dev"],
                    "std_error": stats["std_error"],
                    "t_statistic": stats["t_statistic"],
                    "p_value_1sided": stats["p_value_1sided"],
                    "ci_95_1sided_lower": stats["ci_95_1sided_lower"],
                    "ci_95_2sided_lower": stats["ci_95_2sided_lower"],
                    "ci_95_2sided_upper": stats["ci_95_2sided_upper"],
                    "win_rate": stats["win_rate"]
                }
            except ValueError as e:
                if "Zero sample variance" in str(e):
                    mean_r = sum(returns) / n
                    summary[sc_id] = {
                        "sample_size": n,
                        "mean_net_return": mean_r,
                        "mean_net_pips": sum(pips) / n,
                        "std_dev": 0.0,
                        "std_error": 0.0,
                        "t_statistic": None,
                        "p_value_1sided": None,
                        "ci_95_1sided_lower": None,
                        "ci_95_2sided_lower": None,
                        "ci_95_2sided_upper": None,
                        "win_rate": sum(1 for r in returns if r > 0) / n
                    }
                else:
                    raise
        elif n == 1:
            summary[sc_id] = {
                "sample_size": 1,
                "mean_net_return": returns[0],
                "mean_net_pips": pips[0],
                "std_dev": None,
                "std_error": None,
                "t_statistic": None,
                "p_value_1sided": None,
                "ci_95_1sided_lower": None,
                "ci_95_2sided_lower": None,
                "ci_95_2sided_upper": None,
                "win_rate": 1.0 if returns[0] > 0 else 0.0
            }
        else:
            summary[sc_id] = {
                "sample_size": 0,
                "mean_net_return": None,
                "mean_net_pips": None,
                "std_dev": None,
                "std_error": None,
                "t_statistic": None,
                "p_value_1sided": None,
                "ci_95_1sided_lower": None,
                "ci_95_2sided_lower": None,
                "ci_95_2sided_upper": None,
                "win_rate": None
            }
    return summary


class RetailSalesCalculationRunner:
    """
    Auditable calculation runner for US Retail Sales EURUSD directional strategy viability.
    Enforces:
    1. Pre-price discovery boundary (zero execution on pinned prices by default).
    2. Strict denominator accounting: exactly 49 pre-2023 strict-concordance packages.
    3. Exactly one outcome per independent release package.
    4. Deterministic output schema with complete cryptographic provenance and versioning.
    """
    def __init__(self, allow_unblinded_run: bool = False):
        self.allow_unblinded_run = allow_unblinded_run

    def evaluate_packages(
        self,
        packages: List[Dict[str, Any]],
        candle_index: CandlePriceIndex,
        calendar_source_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes the pre-price viability calculation across eligible packages.
        Fails closed unless the pre-2023 package accounting matches all specified totals:
        96 packages; 49 strict (27 positive, 22 negative); exclusions 28/9/2/8.
        Rejects unknown categories, corrupted release timestamps, and undefined statistics.
        """
        # 1. Enforce split boundary on all packages
        for p in packages:
            ts = p["timestamp"]
            if ts >= candle_index.split_timestamp:
                raise PermissionError(
                    f"Package timestamp {ts} crosses into the strictly sealed post-2022 holdout "
                    f"(split={candle_index.split_timestamp})."
                )

        # 2. Package accounting and categorization with strict validation
        seen_timestamps: Set[int] = set()
        strict_pkgs: List[Dict[str, Any]] = []
        missing_forecast_count = 0
        active_conflict_count = 0
        both_zero_count = 0
        one_zero_count = 0

        for p in sorted(packages, key=lambda x: x["timestamp"]):
            ts = p["timestamp"]
            if ts in seen_timestamps:
                raise ValueError(f"Duplicate package timestamp encountered: {ts}")
            seen_timestamps.add(ts)

            cat = p.get("sign_category")
            if cat not in VALID_SIGN_CATEGORIES:
                raise ValueError(
                    f"Unknown package category '{cat}' at package timestamp {ts}. "
                    f"Valid categories: {sorted(list(VALID_SIGN_CATEGORIES))}"
                )

            if cat in ("STRICT_AGREE_POS", "STRICT_AGREE_NEG"):
                strict_pkgs.append(p)
            elif cat == "MISSING_FORECAST":
                missing_forecast_count += 1
            elif cat == "ACTIVE_CONFLICT":
                active_conflict_count += 1
            elif cat == "BOTH_ZERO":
                both_zero_count += 1
            elif cat == "ONE_ZERO":
                one_zero_count += 1

        strict_pos_count = sum(1 for p in strict_pkgs if p["sign_category"] == "STRICT_AGREE_POS")
        strict_neg_count = sum(1 for p in strict_pkgs if p["sign_category"] == "STRICT_AGREE_NEG")
        total_strict = len(strict_pkgs)
        total_packages = len(packages)

        # Fail closed unless the frozen pre-2023 package accounting matches all specified totals
        if (
            total_packages != FROZEN_TOTAL_PACKAGES or
            total_strict != FROZEN_STRICT_COUNT or
            strict_pos_count != FROZEN_STRICT_POS or
            strict_neg_count != FROZEN_STRICT_NEG or
            missing_forecast_count != FROZEN_MISSING_FORECAST or
            active_conflict_count != FROZEN_ACTIVE_CONFLICT or
            both_zero_count != FROZEN_BOTH_ZERO or
            one_zero_count != FROZEN_ONE_ZERO
        ):
            raise ValueError(
                f"Frozen pre-2023 package accounting validation failed. Expected: "
                f"Total={FROZEN_TOTAL_PACKAGES}, Strict={FROZEN_STRICT_COUNT} (POS={FROZEN_STRICT_POS}, NEG={FROZEN_STRICT_NEG}), "
                f"MissingForecast={FROZEN_MISSING_FORECAST}, ActiveConflict={FROZEN_ACTIVE_CONFLICT}, "
                f"BothZero={FROZEN_BOTH_ZERO}, OneZero={FROZEN_ONE_ZERO}. "
                f"Observed: Total={total_packages}, Strict={total_strict} (POS={strict_pos_count}, NEG={strict_neg_count}), "
                f"MissingForecast={missing_forecast_count}, ActiveConflict={active_conflict_count}, "
                f"BothZero={both_zero_count}, OneZero={one_zero_count}."
            )

        # 3. Process each eligible package
        trade_episodes: List[Dict[str, Any]] = []
        h6_all_trade_scenarios: List[Dict[str, Dict[str, Any]]] = []
        h12_all_trade_scenarios: List[Dict[str, Dict[str, Any]]] = []

        h6_friday_scenarios: List[Dict[str, Dict[str, Any]]] = []
        h6_non_friday_scenarios: List[Dict[str, Dict[str, Any]]] = []
        h6_collision_scenarios: List[Dict[str, Dict[str, Any]]] = []
        h6_clean_scenarios: List[Dict[str, Dict[str, Any]]] = []

        h12_friday_scenarios: List[Dict[str, Dict[str, Any]]] = []
        h12_non_friday_scenarios: List[Dict[str, Dict[str, Any]]] = []
        h12_collision_scenarios: List[Dict[str, Dict[str, Any]]] = []
        h12_clean_scenarios: List[Dict[str, Dict[str, Any]]] = []

        for p in strict_pkgs:
            pkg_ts = p["timestamp"]

            # Validate or recompute release-derived entry timestamp
            expected_entry_ts = compute_entry_timestamp(pkg_ts)
            if "entry_timestamp" in p and p["entry_timestamp"] != expected_entry_ts:
                raise ValueError(
                    f"Package at timestamp {pkg_ts} has corrupted or mismatching entry_timestamp: "
                    f"got {p['entry_timestamp']}, expected {expected_entry_ts}"
                )
            entry_ts = expected_entry_ts

            # Validate or recompute release-derived weekday
            expected_weekday = datetime.fromtimestamp(pkg_ts, tz=timezone.utc).strftime("%A")
            if "weekday" in p and p["weekday"] != expected_weekday:
                raise ValueError(
                    f"Package at timestamp {pkg_ts} has corrupted or mismatching weekday: "
                    f"got {p['weekday']}, expected {expected_weekday}"
                )
            weekday = expected_weekday

            # Validate or recompute cross-currency collision flag
            if "currencies" in p:
                expected_collision = any(c != "USD" for c in p["currencies"])
                if "has_cross_currency_collision" in p and p["has_cross_currency_collision"] != expected_collision:
                    raise ValueError(
                        f"Package at timestamp {pkg_ts} has corrupted has_cross_currency_collision flag: "
                        f"got {p['has_cross_currency_collision']}, expected {expected_collision}"
                    )
                has_collision = expected_collision
            else:
                has_collision = p.get("has_cross_currency_collision", False)

            cat = p["sign_category"]

            # Directional mapping:
            # Hawkish (POS) -> Short (-1)
            # Dovish (NEG) -> Long (+1)
            if cat == "STRICT_AGREE_POS":
                direction = -1
                dir_label = "SHORT"
            elif cat == "STRICT_AGREE_NEG":
                direction = 1
                dir_label = "LONG"
            else:
                raise ValueError(f"Package at {pkg_ts} has unexpected category {cat}")

            # Resolve 6-H4 horizon bars
            h6_res = candle_index.resolve_horizon_bars(entry_ts, horizon_h4=6)
            if not h6_res["is_complete"]:
                raise RuntimeError(
                    f"Forward 6-H4 path incomplete for package at {pkg_ts}: "
                    f"missing timestamps {h6_res['missing_timestamps']}"
                )

            entry_bar_h6 = h6_res["entry_bar"]
            exit_bar_h6 = h6_res["exit_bar"]
            h6_scenarios = execute_single_trade_across_scenarios(
                entry_bar=entry_bar_h6,
                exit_bar=exit_bar_h6,
                direction=direction
            )

            # Resolve 12-H4 horizon bars
            h12_res = candle_index.resolve_horizon_bars(entry_ts, horizon_h4=12)
            if not h12_res["is_complete"]:
                raise RuntimeError(
                    f"Forward 12-H4 path incomplete for package at {pkg_ts}: "
                    f"missing timestamps {h12_res['missing_timestamps']}"
                )

            entry_bar_h12 = h12_res["entry_bar"]
            exit_bar_h12 = h12_res["exit_bar"]
            h12_scenarios = execute_single_trade_across_scenarios(
                entry_bar=entry_bar_h12,
                exit_bar=exit_bar_h12,
                direction=direction
            )

            episode_record = {
                "package_timestamp": pkg_ts,
                "weekday": weekday,
                "has_cross_currency_collision": has_collision,
                "sign_category": cat,
                "direction": direction,
                "direction_label": dir_label,
                "entry_timestamp": entry_ts,
                "entry_delay_minutes": (entry_ts - pkg_ts) // 60,
                "h6": {
                    "exit_boundary_timestamp": h6_res["exit_timestamp"],
                    "exit_bar_timestamp": exit_bar_h6.timestamp,
                    "entry_bid": entry_bar_h6.open,
                    "exit_bid": exit_bar_h6.close,
                    "crosses_weekend": h6_res["crosses_weekend"],
                    "recorded_spread_entry": entry_bar_h6.spread,
                    "recorded_spread_exit": exit_bar_h6.spread,
                    "scenarios": h6_scenarios
                },
                "h12": {
                    "exit_boundary_timestamp": h12_res["exit_timestamp"],
                    "exit_bar_timestamp": exit_bar_h12.timestamp,
                    "entry_bid": entry_bar_h12.open,
                    "exit_bid": exit_bar_h12.close,
                    "crosses_weekend": h12_res["crosses_weekend"],
                    "recorded_spread_entry": entry_bar_h12.spread,
                    "recorded_spread_exit": exit_bar_h12.spread,
                    "scenarios": h12_scenarios
                }
            }
            trade_episodes.append(episode_record)

            # Collect scenarios for aggregation
            h6_all_trade_scenarios.append(h6_scenarios)
            h12_all_trade_scenarios.append(h12_scenarios)

            if weekday == "Friday":
                h6_friday_scenarios.append(h6_scenarios)
                h12_friday_scenarios.append(h12_scenarios)
            else:
                h6_non_friday_scenarios.append(h6_scenarios)
                h12_non_friday_scenarios.append(h12_scenarios)

            if has_collision:
                h6_collision_scenarios.append(h6_scenarios)
                h12_collision_scenarios.append(h12_scenarios)
            else:
                h6_clean_scenarios.append(h6_scenarios)
                h12_clean_scenarios.append(h12_scenarios)

        # 4. Summary metrics
        primary_results_6h4 = summarize_trade_metrics(h6_all_trade_scenarios)
        subgroup_results_6h4 = {
            "friday_subgroup": summarize_trade_metrics(h6_friday_scenarios),
            "non_friday_subgroup": summarize_trade_metrics(h6_non_friday_scenarios),
            "collision_subgroup": summarize_trade_metrics(h6_collision_scenarios),
            "clean_subgroup": summarize_trade_metrics(h6_clean_scenarios)
        }

        descriptive_results_12h4 = {
            "governance_note": (
                "Exploratory and descriptive persistence diagnostic only. "
                "No separate setup registration claim, no secondary hypothesis gate, "
                "and no family-wise error adjustment."
            ),
            "all_trades": summarize_trade_metrics(h12_all_trade_scenarios),
            "subgroups": {
                "friday_subgroup": summarize_trade_metrics(h12_friday_scenarios),
                "non_friday_subgroup": summarize_trade_metrics(h12_non_friday_scenarios),
                "collision_subgroup": summarize_trade_metrics(h12_collision_scenarios),
                "clean_subgroup": summarize_trade_metrics(h12_clean_scenarios)
            }
        }

        # 5. Pre-price decision gate classification under Scenario C (10 pts)
        primary_sc_c = primary_results_6h4.get("Scenario_C_10pts", {})
        mean_c = primary_sc_c.get("mean_net_return")
        p_val_c = primary_sc_c.get("p_value_1sided")
        win_rate_c = primary_sc_c.get("win_rate")
        std_dev_c = primary_sc_c.get("std_dev")

        mean_fri_c = subgroup_results_6h4["friday_subgroup"]["Scenario_C_10pts"].get("mean_net_return")
        mean_non_fri_c = subgroup_results_6h4["non_friday_subgroup"]["Scenario_C_10pts"].get("mean_net_return")

        # Fail explicitly on undefined primary statistics; do not invent a verdict
        if mean_c is None or p_val_c is None or win_rate_c is None or std_dev_c == 0.0 or primary_sc_c.get("t_statistic") is None:
            raise RuntimeError(
                f"Primary viability statistics under Scenario C are undefined "
                f"(mean={mean_c}, std_dev={std_dev_c}, p_value={p_val_c}, win_rate={win_rate_c}). "
                f"Cannot evaluate automated discovery disposition. Halted for explicit protocol review."
            )

        disposition = classify_discovery_outcome(
            mean_net=mean_c,
            p_val_1sided=p_val_c,
            win_rate=win_rate_c,
            mean_net_friday=mean_fri_c,
            mean_net_non_friday=mean_non_fri_c
        )

        downstream_actions = {
            "DISCONFIRMED_ADVERSE": (
                "Adverse point estimate: strategy produces negative or flat drift under Scenario C (10 pts). "
                "Directional hypothesis disconfirmed. Investigation concluded. Post-2022 holdout remains sealed."
            ),
            "INCONCLUSIVE_UNDERPOWERED": (
                "Statistically underpowered: positive point estimate observed, but indistinguishable from random drift (p >= 0.10). "
                "Insufficient evidence. Investigation concluded. Post-2022 holdout remains sealed."
            ),
            "INCONCLUSIVE_FRAGILE": (
                "Inconclusive fragile: positive point estimate observed with p < 0.10, but fails secondary hurdles "
                "(p >= 0.05, win rate < 53%, or non-positive subgroup mean). Candidate cannot advance. Post-2022 holdout remains sealed."
            ),
            "PROMISING_DISCOVERY_CANDIDATE": (
                "Promising discovery candidate: satisfies all pre-price discovery hurdles under Scenario C (10 pts). "
                "NOT A REGISTERED SETUP. Earns eligibility for formal post-2022 holdout verification under the frozen protocol."
            )
        }

        decision_block = {
            "primary_scenario": "Scenario_C_10pts",
            "disposition": disposition,
            "hurdle_evaluation": {
                "mean_net_positive": mean_c > 0.0,
                "p_value_below_05": p_val_c < 0.05,
                "p_value_below_10": p_val_c < 0.10,
                "win_rate_above_53": win_rate_c >= 0.53,
                "friday_mean_positive": (mean_fri_c > 0.0) if mean_fri_c is not None else False,
                "non_friday_mean_positive": (mean_non_fri_c > 0.0) if mean_non_fri_c is not None else False,
            },
            "scientific_verdict": downstream_actions.get(disposition, "Under evaluation")
        }

        # Determine verified provenance of inputs
        if calendar_source_metadata is None:
            calendar_source_metadata = {
                "source_type": "SYNTHETIC_FIXTURE",
                "source_description": "In-memory synthetic package list",
                "source_path": None,
                "source_sha256": None,
                "pinned_source_verified": False
            }

        candle_source_metadata = getattr(candle_index, "source_metadata", {
            "source_type": "SYNTHETIC_FIXTURE",
            "source_description": "In-memory candle fixture",
            "source_path": None,
            "source_sha256": None,
            "pinned_source_verified": False
        })

        cal_type = calendar_source_metadata.get("source_type", "UNKNOWN")
        candle_type = candle_source_metadata.get("source_type", "UNKNOWN")
        is_cal_pinned = bool(calendar_source_metadata.get("pinned_source_verified", False))
        is_candle_pinned = bool(candle_source_metadata.get("pinned_source_verified", False))
        all_pinned_verified = is_cal_pinned and is_candle_pinned

        if all_pinned_verified:
            prov_classification = "VERIFIED_PINNED_SOURCES"
        elif cal_type == "NON_PINNED_INPUT" or candle_type == "NON_PINNED_INPUT":
            prov_classification = "NON_PINNED_INPUT"
        else:
            prov_classification = "SYNTHETIC_FIXTURE"

        is_synthetic_run = (cal_type == "SYNTHETIC_FIXTURE" or candle_type == "SYNTHETIC_FIXTURE")
        is_non_pinned_run = (cal_type == "NON_PINNED_INPUT" or candle_type == "NON_PINNED_INPUT")

        impl_prov = get_implementation_provenance()

        # 6. Complete, deterministic output schema with cryptographic provenance
        schema_output: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "metadata": {
                "protocol_reference": PROTOCOL_REFERENCE,
                "runner_implementation_version": RUNNER_IMPLEMENTATION_VERSION,
                "implementation_identity": impl_prov,
                "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "instrument": DEFAULT_INSTRUMENT,
                "split_timestamp": candle_index.split_timestamp,
                "symbol_specification": {
                    "symbol_digits": EURUSD_DIGITS,
                    "point_size": EURUSD_POINT,
                    "points_per_pip": EURUSD_POINTS_PER_PIP,
                    "headline_event_id": HEADLINE_EID,
                    "core_event_id": CORE_EID
                },
                "provenance": {
                    "provenance_classification": prov_classification,
                    "is_synthetic_fixture_run": is_synthetic_run,
                    "is_non_pinned_input_run": is_non_pinned_run,
                    "pinned_sources_verified": all_pinned_verified,
                    "expected_pinned_sources": EXPECTED_PINNED_SOURCES,
                    "verified_sources_used": {
                        "calendar": calendar_source_metadata,
                        "candles": candle_source_metadata
                    }
                },
                "primary_hurdle": "Scenario_C_10pts",
                "primary_horizon": "6-H4 (24 active trading hours)",
                "descriptive_horizon": "12-H4 (48 active trading hours)",
                "total_cost_scenarios_evaluated": len(FROZEN_COST_SCENARIOS)
            },
            "package_accounting": {
                "total_packages_evaluated": len(packages),
                "strict_concordance_count": total_strict,
                "strict_pos_count": strict_pos_count,
                "strict_neg_count": strict_neg_count,
                "excluded_missing_forecast_count": missing_forecast_count,
                "excluded_active_conflict_count": active_conflict_count,
                "excluded_both_zero_count": both_zero_count,
                "excluded_one_zero_count": one_zero_count,
                "evaluated_trade_count": len(trade_episodes)
            },
            "trade_episodes": trade_episodes,
            "primary_results_6h4": primary_results_6h4,
            "subgroup_results_6h4": subgroup_results_6h4,
            "descriptive_results_12h4": descriptive_results_12h4,
            "decision_classification": decision_block,
            "governance_notice": (
                "Historical screening calculation only. "
                "Not verified broker profitability. "
                "Not authorized for live or unvalidated demo trading."
            )
        }

        return schema_output

    def evaluate_ledger(
        self,
        ledger: Dict[str, Any],
        candle_index: CandlePriceIndex,
        calendar_source_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluates packages from a pre-built package ledger dictionary."""
        if calendar_source_metadata is None:
            calendar_source_metadata = ledger.get("calendar_source_metadata")
        return self.evaluate_packages(
            packages=ledger["packages"],
            candle_index=candle_index,
            calendar_source_metadata=calendar_source_metadata
        )

    def execute_from_paths(
        self,
        calendar_path: str,
        candle_path: str,
        allow_unblinded_run: bool = False
    ) -> Dict[str, Any]:
        """
        Formal empirical entry point for executing pre-price calculation from filepaths.

        FAIL-CLOSED SAFETY GATES:
        1. Protocol Freeze & Unblinding Permission (CHECKED FIRST BEFORE TOUCHING FILES):
           Empirical execution on candidate data is strictly prohibited prior to formal protocol freeze.
           With default allow_unblinded_run=False, neither input file is opened, hashed, or touched.
        2. Pinned Source Verification (CHECKED AFTER UNBLINDING PERMISSION, BEFORE CALCULATION):
           Both the calendar file and the candle file MUST strictly match their expected
           pinned SHA-256 digests. Non-pinned CSV files are rejected immediately before
           ledger construction or outcome calculation. Non-pinned inputs cannot receive
           a formal discovery disposition merely because package counts match.
           (Synthetic fixture evaluation remains available through evaluate_packages).
        """
        # Gate 1: Check explicit unblinding authorization FIRST before touching or hashing either file
        effective_unblinded = allow_unblinded_run or self.allow_unblinded_run
        if not effective_unblinded:
            raise PermissionError(
                "Unblinded empirical execution is strictly prohibited prior to formal protocol freeze. "
                "Candidate inputs remain sealed and untouched."
            )

        # Gate 2: Compute SHA-256 hashes of both actual input files on disk
        cal_sha256 = compute_file_sha256(calendar_path)
        exp_cal_sha = EXPECTED_PINNED_SOURCES["calendar_releases"]["sha256"]
        cal_is_pinned = (cal_sha256 == exp_cal_sha)

        candle_sha256 = compute_file_sha256(candle_path)
        exp_candle_sha = EXPECTED_PINNED_SOURCES["raw_candles_eurusd"]["sha256"]
        candle_is_pinned = (candle_sha256 == exp_candle_sha)

        # Gate 3: Fail closed immediately if either file is not the verified pinned source
        if not cal_is_pinned or not candle_is_pinned:
            mismatches = []
            if not cal_is_pinned:
                mismatches.append(
                    f"Calendar file '{calendar_path}' SHA-256 '{cal_sha256}' does not match "
                    f"expected pinned hash '{exp_cal_sha}'"
                )
            if not candle_is_pinned:
                mismatches.append(
                    f"Candle file '{candle_path}' SHA-256 '{candle_sha256}' does not match "
                    f"expected pinned hash '{exp_candle_sha}'"
                )
            raise ValueError(
                f"Formal empirical execution via execute_from_paths rejected non-pinned input: "
                f"{'; '.join(mismatches)}. Non-pinned CSV files cannot receive a formal discovery "
                f"disposition merely because package counts match. Synthetic fixture evaluation "
                f"must use evaluate_packages directly."
            )

        calendar_meta = {
            "source_type": "PINNED_SOURCE",
            "source_description": os.path.basename(calendar_path),
            "source_path": os.path.normpath(calendar_path).replace("\\", "/"),
            "source_sha256": cal_sha256,
            "pinned_source_verified": True
        }

        ledger = build_retail_sales_package_ledger(calendar_path)
        candle_index = CandlePriceIndex.from_csv(
            candle_path,
            split_timestamp=HARD_SPLIT_TIMESTAMP,
            allow_unblinded_run=effective_unblinded
        )
        return self.evaluate_packages(
            packages=ledger["packages"],
            candle_index=candle_index,
            calendar_source_metadata=calendar_meta
        )


def serialize_runner_output(output: Dict[str, Any], indent: int = 2) -> str:
    """Serializes runner output schema to a deterministic JSON string."""
    return json.dumps(output, indent=indent)
