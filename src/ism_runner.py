"""
Pre-2023 Calculation Runner & Output Schema for US ISM Manufacturing PMI on EURUSD
Pre-price directional strategy viability calculation runner, H1 active bar resolution,
trade execution engine across 5 frozen cost scenarios, and deterministic output schema.

CRITICAL RESEARCH INTEGRITY GOVERNANCE & FILE BOUNDARY DISCLOSURES:
- Default discussion and read-only state. Candidate prices remain sealed prior to formal freeze packet.
- Empirical execution on pinned candidate candle prices is strictly prohibited prior to formal freeze.
- Post-2022 holdout data (timestamp >= 1672531200) is strictly sealed during pre-2023 discovery.
- File Boundary Disclosures (No byte-level non-reading claim):
  1. Full-file SHA-256 hashing reads all raw bytes from byte 0 to EOF, including the post-2022
     holdout portion, but treats data strictly as an opaque binary stream without parsing prices
     or inspecting outcomes.
  2. The CSV calculation path buffers the raw text of the first post-split line into memory,
     but inspects field 0 before tokenizing and breaks immediately: post-split price columns
     are never parsed, converted to floats, or analyzed.
- Zero synthetic data injected into real analysis, zero outcome faking, zero lookahead.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
import math
import os
import json
import csv
from datetime import datetime, timezone
import hashlib
import subprocess
from scipy import stats

from .parsers import SPLIT_TIMESTAMP
from .candle_coverage import (
    SECONDS_IN_H1,
    is_valid_weekend_market_closure,
)

RUNNER_IMPLEMENTATION_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
PROTOCOL_REFERENCE = "docs/DRAFT_ISM_PMI_PROTOCOL.md"
DEFAULT_INSTRUMENT = "EURUSD"
PINNED_CANDLE_FILENAME = "candles_EURUSD_H1.csv"
HARD_SPLIT_TIMESTAMP = SPLIT_TIMESTAMP  # 1672531200 (2023-01-01 00:00:00 broker server time)

HEADLINE_EVENT_ID = "840040001"
EURUSD_PIP_SIZE = 0.00010
EURUSD_POINT = 0.00001
EURUSD_POINTS_PER_PIP = 10

# Expected pinned sources specified in the draft protocol
EXPECTED_PINNED_SOURCES = {
    "calendar_releases": {
        "path": "data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv",
        "sha256": "76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e"
    },
    "calendar_events": {
        "path": "data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_events.csv",
        "sha256": "e08d2df96e83fdefa1c56d33316ee09178fe75aff1f3325d6f4ec4c80a4b7f13"
    },
    "candle_symbols": {
        "path": "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candle_symbols.csv",
        "sha256": "3b067061adbb6e941be26006f9451e853a91cd622479e78387b32102a43755b1"
    },
    "raw_candles_eurusd": {
        "path": "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv",
        "sha256": "893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5"
    }
}

# Pre-2023 Sample Accounting Reference Constants
FROZEN_ISM_TOTAL_PRE2023 = 96
FROZEN_ISM_COMPLETE_AFP = 67
FROZEN_ISM_INCOMPLETE = 29
FROZEN_ISM_ACTIONABLE = 66
FROZEN_ISM_POSITIVE_SURPRISE = 28
FROZEN_ISM_NEGATIVE_SURPRISE = 38
FROZEN_ISM_ZERO_SURPRISE = 1

# Standard 5 Assumed-Cost Sensitivity Scenarios (cost in pips deducted once)
COST_SCENARIOS = {
    "Scenario_A": 0.0,   # 0.0 pips / 0 pts
    "Scenario_B": 0.5,   # 0.5 pips / 5 pts
    "Scenario_C": 1.0,   # 1.0 pip  / 10 pts (PRIMARY SCREENING HURDLE)
    "Scenario_D": 2.0,   # 2.0 pips / 20 pts
    "Scenario_E": 3.0    # 3.0 pips / 30 pts (Combined sensitivity hurdle)
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
    """
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_implementation_provenance() -> Dict[str, Any]:
    """
    Dynamically inspects Git repository state to record the exact implementation identity.
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
        status_lines = [line for line in res_status.stdout.strip().splitlines() if line.strip()]
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
    In-memory index of valid H1 candle bars.
    Strictly seals timestamps >= split_timestamp (1672531200) during pre-2023 discovery.
    Validates monotonicity, rejects duplicates, and resolves active H1 paths across
    legitimate weekend market closures.
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
        self._sorted_bars: List[CandleBar] = []
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
            self._sorted_bars.append(bar)
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
        Standard Python file stream iteration buffers the line of text up to newline.
        For the first post-split row encountering timestamp >= split_timestamp, the raw text
        is buffered into memory before column 0 can be parsed.

        LOGICAL PARSING ISOLATION:
        Before tokenizing the line or parsing columns 1..N, the runner extracts solely
        field-0 integer timestamp. If ts >= split_timestamp, the loop breaks immediately.
        Columns 1..N of post-split rows are NEVER converted to floats or stored.
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

                comma_idx = line.find(",")
                ts_str = line[:comma_idx] if comma_idx != -1 else line
                try:
                    ts = int(ts_str)
                except ValueError:
                    raise ValueError(f"Line {line_num}: Malformed timestamp field '{ts_str}'")

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

    def resolve_active_h1_path(
        self,
        entry_ts: int,
        num_bars: int = 24
    ) -> Tuple[List[CandleBar], bool]:
        """
        Resolves a sequence of num_bars active consecutive H1 candles starting at entry_ts.
        Steps over valid weekend market closures using is_valid_weekend_market_closure.
        Rejects arbitrary weekday gaps, unsorted timestamps, and paths exceeding split boundary.

        Returns (bars, crosses_weekend).
        """
        if entry_ts not in self._bars_by_ts:
            raise KeyError(f"Entry candle bar at timestamp {entry_ts} not found in price index")

        entry_idx = self._sorted_timestamps.index(entry_ts)
        available_bars = len(self._sorted_bars) - entry_idx

        if available_bars < num_bars:
            raise ValueError(
                f"Insufficient forward active bars from entry {entry_ts}: "
                f"required {num_bars}, available {available_bars}"
            )

        candidate_bars = self._sorted_bars[entry_idx : entry_idx + num_bars]
        path_ts = [b.timestamp for b in candidate_bars]

        # Validate path boundaries and transitions
        crosses_weekend = False
        for i in range(len(path_ts)):
            ts = path_ts[i]
            if ts >= self.split_timestamp:
                raise PermissionError(
                    f"Bar at path index {i} ({ts}) crosses split boundary {self.split_timestamp}"
                )

        # Split-boundary exit close check:
        # Final active bar opens at path_ts[-1] and closes at path_ts[-1] + 3600.
        exit_close_ts = path_ts[-1] + SECONDS_IN_H1
        if exit_close_ts > self.split_timestamp:
            raise PermissionError(
                f"Exit close timestamp {exit_close_ts} extends beyond split boundary {self.split_timestamp}"
            )

        # Validate adjacent transitions
        for i in range(len(path_ts) - 1):
            t1, t2 = path_ts[i], path_ts[i + 1]
            if t2 <= t1:
                raise ValueError(f"Duplicate or unsorted timestamps in path: {t1} -> {t2}")

            diff = t2 - t1
            if diff == SECONDS_IN_H1:
                continue

            # Non-3600 transition: must be legitimate weekend closure
            is_weekend, reason = is_valid_weekend_market_closure(t1, t2)
            if not is_weekend:
                is_weekend2, reason2 = is_valid_weekend_market_closure(t1 + SECONDS_IN_H1, t2)
                if not is_weekend2:
                    raise ValueError(
                        f"Invalid gap between bar {i} and {i+1} ({t1} -> {t2}, {diff/3600:.1f}h): {reason}"
                    )
            crosses_weekend = True

        return candidate_bars, crosses_weekend


def load_ism_packages_from_calendar_csv(
    calendar_csv_path: str,
    split_timestamp: int = HARD_SPLIT_TIMESTAMP
) -> Dict[str, Any]:
    """
    Parses pre-2023 calendar releases for US ISM Manufacturing PMI (event_id 840040001).
    Performs deterministic sample accounting without reading prices.

    Accounting categories:
    - total_pre2023: 96
    - complete_afp: 67
    - missing_forecast: 29
    - actionable: 66
    - positive_surprise: 28 (S_H > 0, Hawkish USD -> Short EURUSD)
    - negative_surprise: 38 (S_H < 0, Dovish USD -> Long EURUSD)
    - zero_surprise: 1 (S_H == 0, Consensus match -> Excluded)
    """
    releases: List[Dict[str, Any]] = []

    with open(calendar_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("event_id") == HEADLINE_EVENT_ID:
                ts = int(row["timestamp"])
                if ts < split_timestamp:
                    releases.append(row)

    releases.sort(key=lambda r: int(r["timestamp"]))
    total_count = len(releases)

    complete_afp: List[Dict[str, Any]] = []
    missing_forecast: List[Dict[str, Any]] = []

    for r in releases:
        act = r.get("actual_raw_scaled_1e6", "")
        fc = r.get("forecast_raw_scaled_1e6", "")
        prev = r.get("previous_raw_scaled_1e6", "")
        if act != "" and fc != "" and prev != "":
            complete_afp.append(r)
        else:
            missing_forecast.append(r)

    positive_pkgs: List[Dict[str, Any]] = []
    negative_pkgs: List[Dict[str, Any]] = []
    zero_pkgs: List[Dict[str, Any]] = []

    for r in complete_afp:
        act_val = int(r["actual_raw_scaled_1e6"])
        fc_val = int(r["forecast_raw_scaled_1e6"])
        prev_val = int(r["previous_raw_scaled_1e6"])
        surp = act_val - fc_val
        rel_ts = int(r["timestamp"])
        dt = datetime.fromtimestamp(rel_ts, tz=timezone.utc)
        weekday = dt.strftime("%A")
        entry_ts = rel_ts + SECONDS_IN_H1

        pkg_info = {
            "timestamp": rel_ts,
            "timestamp_server_text": r.get("timestamp_server_text", ""),
            "weekday": weekday,
            "actual_scaled": act_val,
            "forecast_scaled": fc_val,
            "previous_scaled": prev_val,
            "surprise_scaled": surp,
            "entry_timestamp": entry_ts,
        }

        if surp > 0:
            pkg_info["direction"] = -1
            pkg_info["direction_label"] = "SHORT_EURUSD"
            positive_pkgs.append(pkg_info)
        elif surp < 0:
            pkg_info["direction"] = 1
            pkg_info["direction_label"] = "LONG_EURUSD"
            negative_pkgs.append(pkg_info)
        else:
            pkg_info["direction"] = 0
            pkg_info["direction_label"] = "ZERO_SURPRISE_EXCLUDED"
            zero_pkgs.append(pkg_info)

    actionable_pkgs = positive_pkgs + negative_pkgs
    actionable_pkgs.sort(key=lambda p: p["timestamp"])

    return {
        "event_id": HEADLINE_EVENT_ID,
        "event_name": "ISM Manufacturing PMI",
        "split_timestamp": split_timestamp,
        "sample_accounting": {
            "total_pre2023_releases": total_count,
            "complete_afp_releases": len(complete_afp),
            "missing_forecast_releases": len(missing_forecast),
            "actionable_releases": len(actionable_pkgs),
            "positive_surprises": len(positive_pkgs),
            "negative_surprises": len(negative_pkgs),
            "zero_surprises": len(zero_pkgs)
        },
        "actionable_packages": actionable_pkgs,
        "zero_surprise_packages": zero_pkgs,
        "missing_forecast_packages": missing_forecast
    }


def compute_pip_statistics(
    pip_returns: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Computes 1-sample Student's t viability statistics on pip returns.
    Primary test: H0: mu <= 0 vs H1: mu > 0 (1-sided).

    Input Validation:
    - Rejects non-finite values (NaN, Inf).
    - Requires at least 2 observations.
    - Zero variance fails closed (returns is_valid=False, error string).
    """
    if not isinstance(pip_returns, (list, tuple)):
        raise TypeError("pip_returns must be a list or tuple of numeric values")

    n = len(pip_returns)
    if n < 2:
        return {
            "is_valid": False,
            "error": f"Sample size {n} is insufficient for t-distribution statistics (minimum 2 required)",
            "sample_size": n
        }

    for idx, r in enumerate(pip_returns):
        if not isinstance(r, (int, float)):
            return {
                "is_valid": False,
                "error": f"Return at index {idx} is non-numeric: {r}",
                "sample_size": n
            }
        if math.isnan(r) or math.isinf(r):
            return {
                "is_valid": False,
                "error": f"Return at index {idx} is non-finite ({r})",
                "sample_size": n
            }

    mean_pips = sum(pip_returns) / n
    variance = sum((r - mean_pips) ** 2 for r in pip_returns) / (n - 1)
    std_dev = math.sqrt(variance)
    std_err = std_dev / math.sqrt(n)

    if std_err == 0.0 or variance == 0.0:
        return {
            "is_valid": False,
            "error": "Zero sample variance: all pip return observations are identical; t-statistic and p-value are undefined",
            "sample_size": n,
            "mean_pips": mean_pips,
            "std_dev": 0.0,
            "std_error": 0.0
        }

    t_stat = mean_pips / std_err
    p_val_1sided = float(1.0 - stats.t.cdf(t_stat, df=n - 1))

    # 1-sided 95% lower confidence bound: [ci_95_1sided_lower, infinity)
    crit_t_95_1sided = float(stats.t.ppf(1.0 - alpha, df=n - 1))
    ci_95_1sided_lower = mean_pips - crit_t_95_1sided * std_err

    # 2-sided 95% confidence interval for mu
    crit_t_95_2sided = float(stats.t.ppf(1.0 - alpha / 2.0, df=n - 1))
    ci_95_2sided_lower = mean_pips - crit_t_95_2sided * std_err
    ci_95_2sided_upper = mean_pips + crit_t_95_2sided * std_err

    # Win rate (proportion of strictly positive returns)
    wins = sum(1 for r in pip_returns if r > 0.0)
    win_rate = wins / n

    return {
        "is_valid": True,
        "sample_size": n,
        "mean_pips": mean_pips,
        "std_dev": std_dev,
        "std_error": std_err,
        "t_statistic": t_stat,
        "p_value_1sided": p_val_1sided,
        "ci_95_1sided_lower": ci_95_1sided_lower,
        "ci_95_2sided_lower": ci_95_2sided_lower,
        "ci_95_2sided_upper": ci_95_2sided_upper,
        "ci_2sided_lower": ci_95_2sided_lower,
        "ci_2sided_upper": ci_95_2sided_upper,
        "win_count": wins,
        "win_rate": win_rate
    }


def classify_ism_discovery_outcome(
    mean_gross_pips: Optional[float],
    mean_net_pips_c: Optional[float],
    p_value_c: Optional[float],
    sample_std_c: Optional[float],
    sample_size: int,
    expected_sample_size: Optional[int] = 66
) -> Dict[str, Any]:
    """
    Classifies the pre-2023 discovery outcome into exactly one mutually exclusive case
    in accordance with Section 7 of docs/DRAFT_ISM_PMI_PROTOCOL.md.

    Cases:
    - Fail-Closed: s(C) == 0, non-finite values, undefined statistics, or sample size mismatch.
    - Case 1: mean_gross_pips <= 0.0 -> DISCONFIRMED_ADVERSE
    - Case 2: mean_gross_pips > 0.0 and mean_net_pips_c <= 0.0 -> INCONCLUSIVE_FRICTION_DECAY
    - Case 3: mean_net_pips_c > 0.0 and p_value_c >= 0.10 -> INCONCLUSIVE_INSUFFICIENT_EVIDENCE
    - Case 4: mean_net_pips_c > 0.0 and 0.05 <= p_value_c < 0.10 -> INCONCLUSIVE_FRAGILE
    - Case 5: mean_net_pips_c > 0.0 and p_value_c < 0.05 -> PROMISING_DISCOVERY_CANDIDATE
    """
    # 1. Fail-closed boundary checks
    is_malformed = (
        mean_gross_pips is None or math.isnan(mean_gross_pips) or math.isinf(mean_gross_pips) or
        mean_net_pips_c is None or math.isnan(mean_net_pips_c) or math.isinf(mean_net_pips_c) or
        p_value_c is None or math.isnan(p_value_c) or math.isinf(p_value_c) or
        sample_std_c is None or math.isnan(sample_std_c) or math.isinf(sample_std_c) or sample_std_c <= 0.0 or
        (expected_sample_size is not None and sample_size != expected_sample_size)
    )

    if is_malformed:
        fail_reasons = []
        if sample_std_c is not None and sample_std_c <= 0.0:
            fail_reasons.append("zero sample variance (s=0)")
        if expected_sample_size is not None and sample_size != expected_sample_size:
            fail_reasons.append(f"sample size mismatch ({sample_size} != {expected_sample_size})")
        if any(v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))
               for v in [mean_gross_pips, mean_net_pips_c, p_value_c, sample_std_c]):
            fail_reasons.append("non-finite or undefined statistical estimates")

        reason_str = "; ".join(fail_reasons) if fail_reasons else "malformed data"
        return {
            "case_id": "Fail-Closed",
            "disposition": "FAIL_CLOSED_INVALID",
            "verdict": f"Execution or Data Failure: {reason_str}. Fails closed. Post-2022 holdout remains SEALED.",
            "is_promising": False
        }

    # 2. Mutually exclusive cases
    if mean_gross_pips <= 0.0:
        return {
            "case_id": "Case 1",
            "disposition": "DISCONFIRMED_ADVERSE",
            "verdict": (
                "Adverse Point Estimate: Gross post-announcement drift is non-positive even before transaction friction. "
                "Primary hypothesis disconfirmed. Post-2022 holdout remains SEALED. Investigation concluded."
            ),
            "is_promising": False
        }
    elif mean_gross_pips > 0.0 and mean_net_pips_c <= 0.0:
        return {
            "case_id": "Case 2",
            "disposition": "INCONCLUSIVE_FRICTION_DECAY",
            "verdict": (
                "Friction Decay: Gross drift is positive, but net drift is eliminated after standard 1.0-pip friction. "
                "Candidate lacks commercial viability. Post-2022 holdout remains SEALED. Investigation concluded."
            ),
            "is_promising": False
        }
    elif mean_net_pips_c > 0.0 and p_value_c >= 0.10:
        return {
            "case_id": "Case 3",
            "disposition": "INCONCLUSIVE_INSUFFICIENT_EVIDENCE",
            "verdict": (
                "Insufficient Evidence: Positive point estimate, but indistinguishable from random noise (p >= 0.10); "
                "insufficient evidence to reject the null hypothesis. Post-2022 holdout remains SEALED. Investigation concluded."
            ),
            "is_promising": False
        }
    elif mean_net_pips_c > 0.0 and 0.05 <= p_value_c < 0.10:
        return {
            "case_id": "Case 4",
            "disposition": "INCONCLUSIVE_FRAGILE",
            "verdict": (
                "Marginally Significant: Positive point estimate, but fails standard p < 0.05 threshold. "
                "Post-2022 holdout remains SEALED."
            ),
            "is_promising": False
        }
    elif mean_net_pips_c > 0.0 and p_value_c < 0.05:
        return {
            "case_id": "Case 5",
            "disposition": "PROMISING_DISCOVERY_CANDIDATE",
            "verdict": (
                "Promising Discovery Candidate: Statistically significant positive Scenario C net pips. "
                "NOT A REGISTERED SETUP. Earns the right to post-2022 holdout review."
            ),
            "is_promising": True
        }
    else:
        # Mathematical fallback (cannot be reached with real numbers)
        return {
            "case_id": "Fail-Closed",
            "disposition": "FAIL_CLOSED_INVALID",
            "verdict": "Unclassified mathematical boundary. Fails closed.",
            "is_promising": False
        }


class IsmCalculationRunner:
    """
    Auditable calculation runner for US ISM Manufacturing PMI on EURUSD.
    Executes pre-2023 directional strategy under 5 frozen cost scenarios.
    """
    def __init__(self, split_timestamp: int = HARD_SPLIT_TIMESTAMP):
        self.split_timestamp = split_timestamp

    def execute_from_fixtures(
        self,
        actionable_packages: List[Dict[str, Any]],
        price_index: CandlePriceIndex,
        expected_sample_size: Optional[int] = FROZEN_ISM_ACTIONABLE,
        sample_accounting: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes strategy calculation entirely from in-memory synthetic packages and price index.
        Ideal for pure price-blind unit tests without reading pinned historical files.
        """
        episodes_24h1: List[Dict[str, Any]] = []
        episodes_48h1: List[Dict[str, Any]] = []

        gross_pips_24: List[float] = []
        scenarios_net_pips_24: Dict[str, List[float]] = {sc: [] for sc in COST_SCENARIOS}

        friday_sc_c_pips_24: List[float] = []
        non_friday_sc_c_pips_24: List[float] = []

        gross_pips_48: List[float] = []
        scenarios_net_pips_48: Dict[str, List[float]] = {sc: [] for sc in COST_SCENARIOS}

        for pkg in actionable_packages:
            rel_ts = pkg["timestamp"]
            entry_ts = pkg.get("entry_timestamp", rel_ts + SECONDS_IN_H1)
            direction = pkg["direction"]
            dir_label = pkg.get("direction_label", "SHORT_EURUSD" if direction == -1 else "LONG_EURUSD")
            weekday = pkg.get("weekday", datetime.fromtimestamp(rel_ts, tz=timezone.utc).strftime("%A"))

            # 1. Primary 24-Active-H1 Horizon
            bars_24, crosses_weekend_24 = price_index.resolve_active_h1_path(entry_ts, num_bars=24)
            entry_bar = bars_24[0]
            exit_bar_24 = bars_24[23]

            open_price = entry_bar.open
            close_price_24 = exit_bar_24.close

            # Gross Directional Pip Return
            gross_pip_24 = direction * (close_price_24 - open_price) / EURUSD_PIP_SIZE
            gross_pips_24.append(gross_pip_24)

            # 5 Cost Scenarios (cost deducted once in pips)
            trade_net_pips_24: Dict[str, float] = {}
            for sc_name, sc_cost in COST_SCENARIOS.items():
                net_p = gross_pip_24 - sc_cost
                trade_net_pips_24[sc_name] = net_p
                scenarios_net_pips_24[sc_name].append(net_p)

            # Subgroup collection (Friday vs Non-Friday)
            if weekday == "Friday":
                friday_sc_c_pips_24.append(trade_net_pips_24["Scenario_C"])
            else:
                non_friday_sc_c_pips_24.append(trade_net_pips_24["Scenario_C"])

            episode_24 = {
                "release_timestamp": rel_ts,
                "weekday": weekday,
                "direction": direction,
                "direction_label": dir_label,
                "entry_timestamp": entry_ts,
                "entry_open_price": open_price,
                "exit_bar_timestamp": exit_bar_24.timestamp,
                "exit_close_timestamp": exit_bar_24.timestamp + SECONDS_IN_H1,
                "exit_close_price": close_price_24,
                "crosses_weekend": crosses_weekend_24,
                "gross_pips": gross_pip_24,
                "net_pips_by_scenario": trade_net_pips_24,
                "is_win_scenario_c": trade_net_pips_24["Scenario_C"] > 0.0
            }
            episodes_24h1.append(episode_24)

            # 2. Descriptive 48-Active-H1 Horizon (if available)
            try:
                bars_48, crosses_weekend_48 = price_index.resolve_active_h1_path(entry_ts, num_bars=48)
                exit_bar_48 = bars_48[47]
                close_price_48 = exit_bar_48.close
                gross_pip_48 = direction * (close_price_48 - open_price) / EURUSD_PIP_SIZE
                gross_pips_48.append(gross_pip_48)

                trade_net_pips_48: Dict[str, float] = {}
                for sc_name, sc_cost in COST_SCENARIOS.items():
                    net_p = gross_pip_48 - sc_cost
                    trade_net_pips_48[sc_name] = net_p
                    scenarios_net_pips_48[sc_name].append(net_p)

                episodes_48h1.append({
                    "release_timestamp": rel_ts,
                    "weekday": weekday,
                    "direction": direction,
                    "direction_label": dir_label,
                    "entry_timestamp": entry_ts,
                    "entry_open_price": open_price,
                    "exit_bar_timestamp": exit_bar_48.timestamp,
                    "exit_close_timestamp": exit_bar_48.timestamp + SECONDS_IN_H1,
                    "exit_close_price": close_price_48,
                    "crosses_weekend": crosses_weekend_48,
                    "gross_pips": gross_pip_48,
                    "net_pips_by_scenario": trade_net_pips_48,
                    "is_win_scenario_c": trade_net_pips_48["Scenario_C"] > 0.0
                })
            except Exception:
                # 48-H1 is exploratory; if unavailable, skip without breaking primary
                pass

        # Compute Primary Summary Statistics (24-H1)
        primary_scenario_stats: Dict[str, Any] = {}
        for sc_name in COST_SCENARIOS:
            primary_scenario_stats[sc_name] = compute_pip_statistics(scenarios_net_pips_24[sc_name])

        mean_gross_24 = sum(gross_pips_24) / len(gross_pips_24) if gross_pips_24 else None
        sc_c_stats = primary_scenario_stats.get("Scenario_C", {})

        mean_c = sc_c_stats.get("mean_pips") if sc_c_stats.get("is_valid") else None
        p_val_c = sc_c_stats.get("p_value_1sided") if sc_c_stats.get("is_valid") else None
        std_dev_c = sc_c_stats.get("std_dev") if sc_c_stats.get("is_valid") else None

        # Mutually exclusive decision classification
        decision_classification = classify_ism_discovery_outcome(
            mean_gross_pips=mean_gross_24,
            mean_net_pips_c=mean_c,
            p_value_c=p_val_c,
            sample_std_c=std_dev_c,
            sample_size=len(actionable_packages),
            expected_sample_size=expected_sample_size
        )

        # Descriptive Subgroup Summaries
        friday_stats = compute_pip_statistics(friday_sc_c_pips_24) if friday_sc_c_pips_24 else None
        non_friday_stats = compute_pip_statistics(non_friday_sc_c_pips_24) if non_friday_sc_c_pips_24 else None

        # Descriptive 48-H1 Summary
        descriptive_48_stats: Dict[str, Any] = {}
        for sc_name in COST_SCENARIOS:
            if scenarios_net_pips_48[sc_name]:
                descriptive_48_stats[sc_name] = compute_pip_statistics(scenarios_net_pips_48[sc_name])

        mean_gross_48 = sum(gross_pips_48) / len(gross_pips_48) if gross_pips_48 else None

        provenance = get_implementation_provenance()

        return {
            "schema_version": SCHEMA_VERSION,
            "runner_version": RUNNER_IMPLEMENTATION_VERSION,
            "protocol_reference": PROTOCOL_REFERENCE,
            "instrument": DEFAULT_INSTRUMENT,
            "split_timestamp": self.split_timestamp,
            "provenance": provenance,
            "candle_source_metadata": price_index.source_metadata,
            "sample_accounting": sample_accounting or {
                "actionable_releases": len(actionable_packages)
            },
            "primary_24h1_results": {
                "horizon_active_bars": 24,
                "mean_gross_pips": mean_gross_24,
                "scenarios": primary_scenario_stats,
                "episodes": episodes_24h1
            },
            "descriptive_subgroups_24h1": {
                "governance_note": "Reported strictly as descriptive diagnostics; non-promotable.",
                "friday_subgroup_scenario_c": friday_stats,
                "non_friday_subgroup_scenario_c": non_friday_stats
            },
            "descriptive_48h1_results": {
                "governance_note": "Exploratory diagnostic only. No separate setup registration claim.",
                "horizon_active_bars": 48,
                "mean_gross_pips": mean_gross_48,
                "scenarios": descriptive_48_stats,
                "episodes": episodes_48h1
            },
            "decision_block": {
                "primary_screening_scenario": "Scenario_C",
                "primary_estimand_friction_pips": 1.0,
                "case_id": decision_classification["case_id"],
                "disposition": decision_classification["disposition"],
                "scientific_verdict": decision_classification["verdict"],
                "is_promising_candidate": decision_classification["is_promising"]
            }
        }

    def execute_from_paths(
        self,
        calendar_path: str,
        candle_path: str,
        allow_unblinded_run: bool = False,
        output_json_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes discovery calculation from CSV files on disk.
        Enforces strict safety guard: cannot read pinned candidate candle file without
        allow_unblinded_run=True.
        """
        # Load calendar packages
        cal_data = load_ism_packages_from_calendar_csv(
            calendar_csv_path=calendar_path,
            split_timestamp=self.split_timestamp
        )

        # Load candle prices
        price_index = CandlePriceIndex.from_csv(
            filepath=candle_path,
            split_timestamp=self.split_timestamp,
            allow_unblinded_run=allow_unblinded_run
        )

        result = self.execute_from_fixtures(
            actionable_packages=cal_data["actionable_packages"],
            price_index=price_index,
            expected_sample_size=FROZEN_ISM_ACTIONABLE,
            sample_accounting=cal_data["sample_accounting"]
        )

        if output_json_path:
            out_dir = os.path.dirname(os.path.abspath(output_json_path))
            os.makedirs(out_dir, exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

        return result
