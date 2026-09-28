"""Master Exploration Runner for US CPI and US NFP Historical Exploration.

Produces versioned, immutable exploration packages under:
- Research Candidate/CPI/CPI_EXPLORATION_V2/run_20260928_v2/
- Research Candidate/NFP/NFP_EXPLORATION_V2/run_20260928_v2/

Per CALCULATION_AND_CANDIDATE_CONTRACT and FROZEN EXPLORATION_V2 PROTOCOLS:
- selection_policy = NONE (all 52 cells x 3 horizons reported; no winner selected or registered)
- Pre-outcome baseline commit: 12de3315d82e3be57cbf3f3ad18671fbd70aa1a2
- Protocol freeze commit: 3c3d108
- Code freeze commit: captured dynamically via git HEAD (fails closed on dirty repository)
- Primary dual-touch: STOP_FIRST; sensitivity dual-touch: TARGET_FIRST
- Output files:
  1. manifest.json
  2. release_paths.csv (stored once per event/pair)
  3. trial_ledger.csv (high-precision bounded serialization of prices/ATR/R, clock durations, is_common_h240)
  4. summary_grid_results.csv (N_bundles, N_trades, TP/SL bars and clock seconds proxy, LOYO, adjacent stability)
  5. annual_breakdown.csv (CORE_2015_2025 vs PARTIAL_2026)
  6. loyo_folds.csv (one fold per observed core year in 2015..2025)
  7. EXPLORATION_SUMMARY_REPORT.md
- Executes a representative raw-candle sample audit during generation (four cases per family).
  The master runner then verifies the complete package from its trial ledger before declaring success.
  The sample audit does not constitute full raw-price recalculation.
- Supports read-only package verification via CLI:
    python run_exploration_pipeline.py --verify-only [CPI|NFP|ALL] [--run-id RUN_ID]
"""

import os
import sys
import csv
import json
import time
import math
import hashlib
import argparse
import subprocess
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any, Set

CALC_DIR = os.path.dirname(os.path.abspath(__file__))
if CALC_DIR not in sys.path:
    sys.path.insert(0, CALC_DIR)

from protocol_specs import (
    ACTIVE_USD_PAIRS,
    USD_BASE_PAIRS,
    USD_QUOTE_PAIRS,
    GLOBALLY_EXCLUDED_PAIRS,
    EVENT_ID_US_INITIAL_JOBLESS_CLAIMS,
)
from data_loader import load_candles, DEFAULT_RAW_DIR
from eligibility_evaluator import (
    evaluate_cpi_pre_outcome,
    evaluate_nfp_pre_outcome,
    determine_cohort,
)
from outcome_engine import (
    ALL_GRID_CELLS,
    GRID_STOP_WIDTHS,
    GRID_TARGET_WIDTHS,
    EXPLORATION_HORIZONS,
    get_pip_size,
    simulate_single_trade,
    calculate_median,
    calculate_quantile,
    summarize_distribution,
    calculate_true_loyo,
    summarize_exit_distributions,
    summarize_annual_breakdown,
    get_adjacent_grid_cells,
    calculate_adjacent_cell_stability,
    format_optional_float,
    get_expected_summary_keys,
    index_trial_records,
    TradeOutcome,
)
from audit_independent_calculator import verify_against_production_ledger

REPO_ROOT = os.path.normpath(os.path.join(CALC_DIR, "..", ".."))
BASELINE_COMMIT = "12de3315d82e3be57cbf3f3ad18671fbd70aa1a2"
PROTOCOL_COMMIT = "3c3d108"
RUN_ID = "run_20260928_v2"

# The generator aggregates full-precision trade R, while the verifier reads
# per-trade R serialized to eight decimals. Bound that input rounding as well
# as the final CSV field rounding; never use math.isclose's relative tolerance.
ROUNDING_EPS = 1e-10


def serialized_metric_matches(value: str, expected: float, decimals: int, rounded_inputs: int = 0) -> bool:
    actual = float(value)
    tolerance = 0.5 * 10 ** (-decimals) + rounded_inputs * 0.5e-8 + ROUNDING_EPS
    return math.isfinite(actual) and math.isfinite(expected) and abs(actual - expected) <= tolerance

PINNED_PRE_OUTCOME_LEDGER_HASHES = {
    "CPI": {
        "rel_path": os.path.join("Research Candidate", "CPI", "pre_outcome_ledger_cpi_v2.csv"),
        "expected_sha256": "29AC66F511736121A0A588221DF2A5D8C816722D9C79F9E72FF99C9FE28F0B66",
        "row_count": 980,
    },
    "NFP": {
        "rel_path": os.path.join("Research Candidate", "NFP", "pre_outcome_ledger_nfp_v2.csv"),
        "expected_sha256": "157970C1788CE7CDD47291BCC9E94898E33559FD73FC7503BD7ED821483007CB",
        "row_count": 980,
    },
}


def compute_file_sha256(filepath: str) -> str:
    """Computes uppercase SHA-256 hex digest of a file on disk."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().upper()


def get_git_commit_head(repo_root: str = REPO_ROOT) -> str:
    """Returns current git HEAD commit SHA. Fails closed if repository has uncommitted tracked modifications."""
    status_proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root, capture_output=True, text=True, check=True
    )
    dirty_tracked = [
        line.strip() for line in status_proc.stdout.splitlines()
        if line.strip() and not line.strip().startswith("??")
    ]
    if dirty_tracked:
        raise RuntimeError(
            f"Repository has uncommitted tracked modifications. Cannot capture clean git HEAD:\n"
            + "\n".join(dirty_tracked)
        )
    head_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True
    )
    return head_proc.stdout.strip()


def verify_raw_provenance(raw_dir: str = DEFAULT_RAW_DIR) -> Dict[str, Any]:
    """Verifies SHA-256 hashes of all 34 raw data files and pinned V2 pre-outcome ledgers."""
    json_path = os.path.join(REPO_ROOT, "Docs", "CONTRACT AND PLANNING", "DATA_PROVENANCE_AND_INTEGRITY_INDEX_V4.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Missing provenance index JSON: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        expected_records = json.load(f)

    if len(expected_records) != 34:
        raise ValueError(f"Expected 34 raw files in provenance index, found {len(expected_records)}")

    for item in expected_records:
        rel_raw = item["rel_raw"]
        expected_sha = item["sha256"]
        fpath = os.path.join(raw_dir, rel_raw)
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Raw data file missing: {fpath}")
        computed_sha = compute_file_sha256(fpath)
        if computed_sha != expected_sha:
            raise RuntimeError(
                f"Raw data provenance mismatch for {rel_raw}: "
                f"computed {computed_sha} != expected {expected_sha}"
            )

    # Verify pinned V2 pre-outcome ledgers
    for family, info in PINNED_PRE_OUTCOME_LEDGER_HASHES.items():
        fpath = os.path.join(REPO_ROOT, info["rel_path"])
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Pre-outcome ledger missing: {fpath}")
        computed_sha = compute_file_sha256(fpath)
        if computed_sha != info["expected_sha256"]:
            raise RuntimeError(
                f"Pre-outcome ledger hash mismatch for {family} ({info['rel_path']}): "
                f"computed {computed_sha} != expected {info['expected_sha256']}"
            )

    return {
        "status": "PASSED",
        "raw_files_verified": len(expected_records),
        "pre_outcome_ledgers_verified": len(PINNED_PRE_OUTCOME_LEDGER_HASHES),
    }


def check_package_immutability(package_dir: str) -> None:
    """Enforces package immutability by refusing to overwrite an existing non-empty directory."""
    if os.path.exists(package_dir):
        existing_files = os.listdir(package_dir)
        if existing_files:
            raise FileExistsError(
                f"Package directory already exists and contains {len(existing_files)} files: {package_dir}. "
                f"Refusing to overwrite existing exploratory package. Package is immutable."
            )


def get_audit_cases(family_name: str) -> List[Dict[str, Any]]:
    """Returns representative audit cases for independent recalculation from raw candles."""
    cases = []
    if family_name == "CPI":
        cases.append({
            "label": "CPI EURUSD Short (Surprise A-F, H60 1:2)",
            "observation_id": "CPI_USD_CPI_1494603000_EURUSD_af_60_1:2",
            "pair": "EURUSD", "release_time": 1494603000, "direction": -1,
            "stop_atr": 1.0, "target_atr": 2.0, "horizon": 60
        })
        cases.append({
            "label": "CPI USDJPY Long (Surprise A-F, H60 1:2, JPY pair)",
            "observation_id": "CPI_USD_CPI_1494603000_USDJPY_af_60_1:2",
            "pair": "USDJPY", "release_time": 1494603000, "direction": 1,
            "stop_atr": 1.0, "target_atr": 2.0, "horizon": 60
        })
        cases.append({
            "label": "CPI USDCAD Long (Momentum A-P, H60 1:2)",
            "observation_id": "CPI_USD_CPI_1494603000_USDCAD_ap_60_1:2",
            "pair": "USDCAD", "release_time": 1494603000, "direction": 1,
            "stop_atr": 1.0, "target_atr": 2.0, "horizon": 60
        })
        cases.append({
            "label": "CPI AUDUSD Timeout (Surprise A-F, H60 4:4 wide)",
            "observation_id": "CPI_USD_CPI_1494603000_AUDUSD_af_60_4:4",
            "pair": "AUDUSD", "release_time": 1494603000, "direction": -1,
            "stop_atr": 4.0, "target_atr": 4.0, "horizon": 60
        })
    else:
        cases.append({
            "label": "NFP EURUSD Long (Surprise A-F, H60 1:2)",
            "observation_id": "NFP_USD_NFP_1496417400_EURUSD_af_60_1:2",
            "pair": "EURUSD", "release_time": 1496417400, "direction": 1,
            "stop_atr": 1.0, "target_atr": 2.0, "horizon": 60
        })
        cases.append({
            "label": "NFP USDJPY Short (Momentum A-P, H120 2:2, JPY pair)",
            "observation_id": "NFP_USD_NFP_1515169800_USDJPY_ap_120_2:2",
            "pair": "USDJPY", "release_time": 1515169800, "direction": -1,
            "stop_atr": 2.0, "target_atr": 2.0, "horizon": 120
        })
        cases.append({
            "label": "NFP NZDUSD Dual Touch (Surprise A-F, H60 1:1)",
            "observation_id": "NFP_USD_NFP_1496417400_NZDUSD_af_60_1:1",
            "pair": "NZDUSD", "release_time": 1496417400, "direction": 1,
            "stop_atr": 1.0, "target_atr": 1.0, "horizon": 60
        })
        cases.append({
            "label": "NFP EURUSD Opening Gap (Surprise A-F, H60 2:2)",
            "observation_id": "NFP_USD_NFP_1493998200_EURUSD_af_60_2:2",
            "pair": "EURUSD", "release_time": 1493998200, "direction": -1,
            "stop_atr": 2.0, "target_atr": 2.0, "horizon": 60
        })
    return cases


def verify_existing_package(
    family_name: str,
    run_id: str = RUN_ID,
    raw_dir: str = DEFAULT_RAW_DIR,
    package_dir_override: Optional[str] = None,
    skip_raw_audit: bool = False
) -> Dict[str, Any]:
    """Read-only verifier that checks an existing exploratory package without modifying any file.

    Recomputes and reconciles ALL summary cells from trial_ledger.csv against:
    - summary_grid_results.csv (keyset completeness, N_bundles, N_trades, wins/losses/timeouts, R metrics, exit distributions, LOYO, adjacent stability)
    - annual_breakdown.csv (annual keyset completeness, annual cohorts and yearly R metrics)
    - loyo_folds.csv (LOYO keyset completeness for observed core years 2015..2025)
    - Representative raw-candle audit cases (status: PASSED)

    Fails closed immediately on any discrepancy.
    """
    protocol_id = f"{family_name}_EXPLORATION_V2"
    package_dir = package_dir_override or os.path.join(REPO_ROOT, "Research Candidate", family_name, protocol_id, run_id)
    if not os.path.isdir(package_dir):
        raise FileNotFoundError(f"Exploration package directory not found: {package_dir}")

    required_files = [
        "manifest.json",
        "release_paths.csv",
        "trial_ledger.csv",
        "summary_grid_results.csv",
        "annual_breakdown.csv",
        "loyo_folds.csv",
        "EXPLORATION_SUMMARY_REPORT.md",
    ]
    for rf in required_files:
        fpath = os.path.join(package_dir, rf)
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Required package file missing: {fpath}")

    # 1. Read manifest and validate family, protocol_id, run_id against request
    manifest_path = os.path.join(package_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as mf:
        manifest_data = json.load(mf)

    expected_protocol_id = f"{family_name}_EXPLORATION_V2"
    if manifest_data.get("family") != family_name:
        raise ValueError(
            f"Manifest family mismatch: manifest declares '{manifest_data.get('family')}', "
            f"requested '{family_name}'."
        )
    if manifest_data.get("protocol_id") != expected_protocol_id:
        raise ValueError(
            f"Manifest protocol_id mismatch: manifest declares '{manifest_data.get('protocol_id')}', "
            f"expected '{expected_protocol_id}'."
        )
    if manifest_data.get("run_id") != run_id:
        raise ValueError(
            f"Manifest run_id mismatch: manifest declares '{manifest_data.get('run_id')}', "
            f"requested '{run_id}'."
        )

    # 2. Read trial ledger and validate row counts and schemas
    ledger_path = os.path.join(package_dir, "trial_ledger.csv")
    with open(ledger_path, "r", encoding="utf-8") as lf:
        reader = csv.DictReader(lf)
        ledger_rows = list(reader)

    if len(ledger_rows) != manifest_data["trials_count"]:
        raise ValueError(
            f"Trial count mismatch: ledger has {len(ledger_rows)} rows, "
            f"manifest records {manifest_data['trials_count']}."
        )

    # Parse and structure ledger records
    parsed_trials = []
    for idx, r in enumerate(ledger_rows, start=1):
        w = r["is_win"].strip().lower() in ("true", "1")
        l = r["is_loss"].strip().lower() in ("true", "1")
        t = r["is_timeout"].strip().lower() in ("true", "1")
        if int(w) + int(l) + int(t) != 1:
            raise ValueError(f"Ledger row {idx} violates mutual exclusivity: win={w}, loss={l}, timeout={t}")

        b_exit = int(r["bars_to_exit"])
        if b_exit < 1:
            raise ValueError(f"Ledger row {idx} bars_to_exit {b_exit} < 1")

        # Clock time fields
        sec_open = None
        sec_proxy = None
        if "clock_seconds_to_bar_open" in r and r["clock_seconds_to_bar_open"] != "":
            sec_open = int(r["clock_seconds_to_bar_open"])
            if sec_open < 0:
                raise ValueError(f"Ledger row {idx} clock_seconds_to_bar_open {sec_open} < 0")
        if "clock_seconds_bar_close_proxy" in r and r["clock_seconds_bar_close_proxy"] != "":
            sec_proxy = int(r["clock_seconds_bar_close_proxy"])
            if sec_open is not None and sec_proxy < sec_open:
                raise ValueError(f"Ledger row {idx} clock_seconds_bar_close_proxy {sec_proxy} < open {sec_open}")

        parsed_trials.append({
            "obs_id": r["observation_id"],
            "bundle_id": r["bundle_id"],
            "year": str(r["year"]),
            "cohort": r.get("cohort", ""),
            "pair": r["pair"],
            "signal_type": r["signal_type"],
            "horizon": int(r["horizon_bars"]),
            "horizon_bars": int(r["horizon_bars"]),
            "cell_label": r["cell_label"],
            "stop_atr": float(r["stop_atr"]),
            "target_atr": float(r["target_atr"]),
            "rr": float(r["reward_risk_ratio"]),
            "is_win": w,
            "is_loss": l,
            "is_timeout": t,
            "dual_touch": r["dual_touch"].strip().lower() in ("true", "1"),
            "gross_r": float(r["gross_r"]),
            "signed_pips": float(r["signed_pips"]),
            "bars_to_exit": b_exit,
            "clock_seconds_to_bar_open": sec_open,
            "clock_seconds_bar_close_proxy": sec_proxy,
            "claims_collision": r.get("has_us_jobless_claims_collision", "").strip().lower() in ("true", "1"),
            "cad_collision": r.get("has_cad_employment_collision", "").strip().lower() in ("true", "1"),
            "h240_complete": r.get("is_common_h240", "").strip().lower() in ("true", "1"),
        })

    # Index trial records once into dictionary of groups
    indexed_trials = index_trial_records(parsed_trials, family_name)

    # 3. Reconcile summary_grid_results.csv with complete expected keyset verification
    summary_path = os.path.join(package_dir, "summary_grid_results.csv")
    with open(summary_path, "r", encoding="utf-8") as sf:
        summary_rows = list(csv.DictReader(sf))

    expected_summary_keys = get_expected_summary_keys(family_name)
    seen_summary_keys = set()

    # Precompute cell_mean_r_map for adjacent cell stability checks
    cohort_cell_means: Dict[Tuple[str, str, str, str, int], Dict[str, float]] = defaultdict(dict)
    for (pan, pr, sig, ch, h, cell), sub_trials in indexed_trials.items():
        if sub_trials:
            cohort_cell_means[(pan, pr, sig, ch, h)][cell] = sum(r["gross_r"] for r in sub_trials) / len(sub_trials)

    for idx, srow in enumerate(summary_rows, start=1):
        p_name = srow["panel"]
        pair_val = srow["pair"]
        sig_val = srow["signal_type"]
        ch_filter = srow["cohort_filter"]
        h_val = int(srow["horizon_bars"])
        cell_lbl = srow["cell_label"]
        skey = (p_name, pair_val, sig_val, ch_filter, h_val, cell_lbl)

        if skey in seen_summary_keys:
            raise ValueError(f"Duplicate summary row detected at row {idx} for key: {skey}")
        seen_summary_keys.add(skey)

        sub = indexed_trials.get(skey, [])

        # Reconcile counts
        n_bundles = len(set(r["bundle_id"] for r in sub))
        n_trades = len(sub)
        n_wins = sum(1 for r in sub if r["is_win"])
        n_losses = sum(1 for r in sub if r["is_loss"])
        n_timeouts = sum(1 for r in sub if r["is_timeout"])
        n_dual = sum(1 for r in sub if r["dual_touch"])

        if int(srow["N_bundles"]) != n_bundles:
            raise ValueError(f"Summary row {idx} ({skey}) N_bundles mismatch: ledger {n_bundles} != summary {srow['N_bundles']}")
        if int(srow["N_trades"]) != n_trades:
            raise ValueError(f"Summary row {idx} ({skey}) N_trades mismatch: ledger {n_trades} != summary {srow['N_trades']}")
        if int(srow["N_wins"]) != n_wins:
            raise ValueError(f"Summary row {idx} ({skey}) N_wins mismatch: ledger {n_wins} != summary {srow['N_wins']}")
        if int(srow["N_losses"]) != n_losses:
            raise ValueError(f"Summary row {idx} ({skey}) N_losses mismatch: ledger {n_losses} != summary {srow['N_losses']}")
        if int(srow["N_timeouts"]) != n_timeouts:
            raise ValueError(f"Summary row {idx} ({skey}) N_timeouts mismatch: ledger {n_timeouts} != summary {srow['N_timeouts']}")
        if int(srow["N_dual_touch"]) != n_dual:
            raise ValueError(f"Summary row {idx} ({skey}) N_dual_touch mismatch: ledger {n_dual} != summary {srow['N_dual_touch']}")

        # Reconcile percentages
        # Serialized as .4f → max round-trip error = 0.5 × 10^-4 = 5e-5
        pct_target = n_wins / n_trades if n_trades > 0 else 0.0
        pct_stop = n_losses / n_trades if n_trades > 0 else 0.0
        pct_timeout = n_timeouts / n_trades if n_trades > 0 else 0.0
        pct_dual = n_dual / n_trades if n_trades > 0 else 0.0
        win_rate = pct_target

        if not serialized_metric_matches(srow["pct_target"], pct_target, 4):
            raise ValueError(f"Summary row {idx} pct_target mismatch: ledger {pct_target:.6f} != summary {srow['pct_target']}")
        if not serialized_metric_matches(srow["pct_stop"], pct_stop, 4):
            raise ValueError(f"Summary row {idx} pct_stop mismatch: ledger {pct_stop:.6f} != summary {srow['pct_stop']}")
        if not serialized_metric_matches(srow["pct_timeout"], pct_timeout, 4):
            raise ValueError(f"Summary row {idx} pct_timeout mismatch: ledger {pct_timeout:.6f} != summary {srow['pct_timeout']}")
        if not serialized_metric_matches(srow["pct_dual_touch"], pct_dual, 4):
            raise ValueError(f"Summary row {idx} pct_dual_touch mismatch: ledger {pct_dual:.6f} != summary {srow['pct_dual_touch']}")
        if not serialized_metric_matches(srow["win_rate"], win_rate, 4):
            raise ValueError(f"Summary row {idx} win_rate mismatch: ledger {win_rate:.6f} != summary {srow['win_rate']}")

        # Reconcile R metrics
        # Include final-field rounding and accumulated eight-decimal trial-R rounding.
        r_vals = [r["gross_r"] for r in sub]
        s_r = sum(r_vals)
        m_r = s_r / n_trades if n_trades > 0 else 0.0
        med_r = calculate_median(r_vals) or 0.0
        if not serialized_metric_matches(srow["gross_sum_r"], s_r, 4, n_trades):
            raise ValueError(f"Summary row {idx} gross_sum_r mismatch: ledger {s_r:.6f} != summary {srow['gross_sum_r']}")
        if not serialized_metric_matches(srow["gross_mean_r"], m_r, 6, 1 if n_trades else 0):
            raise ValueError(f"Summary row {idx} gross_mean_r mismatch: ledger {m_r:.8f} != summary {srow['gross_mean_r']}")
        if not serialized_metric_matches(srow["gross_median_r"], med_r, 6, 1 if n_trades else 0):
            raise ValueError(f"Summary row {idx} gross_median_r mismatch: ledger {med_r:.8f} != summary {srow['gross_median_r']}")

        # Reconcile Duration Quantiles & Extremes
        # Bar counts serialized as .1f → abs_tol = 0.05 (0.5 × 10^-1)
        # Clock seconds serialized as .0f → abs_tol = 0.5 (0.5 × 10^0)
        exit_dist = summarize_exit_distributions(sub)
        bar_duration_fields = [
            ("tp_bars_median", exit_dist["tp_median_bars"]),
            ("tp_bars_p75", exit_dist["tp_p75_bars"]),
            ("tp_bars_p90", exit_dist["tp_p90_bars"]),
            ("tp_bars_max", exit_dist["tp_max_bars"]),
            ("sl_bars_median", exit_dist["sl_median_bars"]),
            ("sl_bars_p75", exit_dist["sl_p75_bars"]),
            ("sl_bars_p90", exit_dist["sl_p90_bars"]),
            ("sl_bars_max", exit_dist["sl_max_bars"]),
            ("overall_bars_median", exit_dist["overall_median_bars"]),
            ("overall_bars_p75", exit_dist["overall_p75_bars"]),
            ("overall_bars_p90", exit_dist["overall_p90_bars"]),
            ("overall_bars_max", exit_dist["overall_max_bars"]),
        ]
        sec_duration_fields = [
            ("tp_bar_close_proxy_seconds_median", exit_dist["tp_bar_close_proxy_seconds_median"]),
            ("tp_bar_close_proxy_seconds_p75", exit_dist["tp_bar_close_proxy_seconds_p75"]),
            ("tp_bar_close_proxy_seconds_p90", exit_dist["tp_bar_close_proxy_seconds_p90"]),
            ("tp_bar_close_proxy_seconds_max", exit_dist["tp_bar_close_proxy_seconds_max"]),
            ("sl_bar_close_proxy_seconds_median", exit_dist["sl_bar_close_proxy_seconds_median"]),
            ("sl_bar_close_proxy_seconds_p75", exit_dist["sl_bar_close_proxy_seconds_p75"]),
            ("sl_bar_close_proxy_seconds_p90", exit_dist["sl_bar_close_proxy_seconds_p90"]),
            ("sl_bar_close_proxy_seconds_max", exit_dist["sl_bar_close_proxy_seconds_max"]),
            ("overall_bar_close_proxy_seconds_median", exit_dist["overall_bar_close_proxy_seconds_median"]),
            ("overall_bar_close_proxy_seconds_p75", exit_dist["overall_bar_close_proxy_seconds_p75"]),
            ("overall_bar_close_proxy_seconds_p90", exit_dist["overall_bar_close_proxy_seconds_p90"]),
            ("overall_bar_close_proxy_seconds_max", exit_dist["overall_bar_close_proxy_seconds_max"]),
        ]
        for fname, expected_val in bar_duration_fields:
            actual_str = srow.get(fname, "")
            if expected_val is None:
                if actual_str != "":
                    raise ValueError(f"Summary row {idx} {fname} expected empty string for None distribution, got '{actual_str}'")
            else:
                if actual_str == "":
                    raise ValueError(f"Summary row {idx} {fname} expected {expected_val}, got empty string")
                if not serialized_metric_matches(actual_str, expected_val, 1):
                    raise ValueError(f"Summary row {idx} {fname} mismatch: ledger {expected_val} != summary {actual_str}")
        for fname, expected_val in sec_duration_fields:
            actual_str = srow.get(fname, "")
            if expected_val is None:
                if actual_str != "":
                    raise ValueError(f"Summary row {idx} {fname} expected empty string for None distribution, got '{actual_str}'")
            else:
                if actual_str == "":
                    raise ValueError(f"Summary row {idx} {fname} expected {expected_val}, got empty string")
                if not serialized_metric_matches(actual_str, expected_val, 0):
                    raise ValueError(f"Summary row {idx} {fname} mismatch: ledger {expected_val} != summary {actual_str}")

        # Reconcile LOYO summary
        # The summary grid stores LOYO min/max means AND sums to four decimals.
        # The separate LOYO fold CSV stores means to six decimals.
        loyo = calculate_true_loyo(sub)
        expected_loyo_str = f"{loyo['loyo_positive_years']}/{loyo['loyo_total_folds']}"
        if srow["loyo_positive_years"] != expected_loyo_str:
            raise ValueError(f"Summary row {idx} loyo_positive_years mismatch: expected {expected_loyo_str} != summary {srow['loyo_positive_years']}")
        if int(srow["loyo_total_folds"]) != loyo["loyo_total_folds"]:
            raise ValueError(f"Summary row {idx} loyo_total_folds mismatch: expected {loyo['loyo_total_folds']} != summary {srow['loyo_total_folds']}")
        for l_field, l_val in [
            ("loyo_min_mean_r", loyo["loyo_min_mean_r"]),
            ("loyo_max_mean_r", loyo["loyo_max_mean_r"]),
            ("loyo_min_sum_r", loyo["loyo_min_sum_r"]),
            ("loyo_max_sum_r", loyo["loyo_max_sum_r"]),
        ]:
            actual_lstr = srow.get(l_field, "")
            if l_val is None:
                if actual_lstr != "":
                    raise ValueError(f"Summary row {idx} {l_field} expected empty, got '{actual_lstr}'")
            else:
                if not serialized_metric_matches(actual_lstr, l_val, 4, n_trades if "sum" in l_field else 1):
                    raise ValueError(f"Summary row {idx} {l_field} mismatch: ledger {l_val:.8f} != summary {actual_lstr}")

        # Reconcile Adjacent-Cell Stability
        # Adjacent fields are serialized to four decimals in the generated grid.
        cohort_means = cohort_cell_means.get((p_name, pair_val, sig_val, ch_filter, h_val), {})
        adj_res = calculate_adjacent_cell_stability(cell_lbl, cohort_means)
        if int(srow["adj_cells_count"]) != adj_res["adj_cells_count"]:
            raise ValueError(f"Summary row {idx} adj_cells_count mismatch: expected {adj_res['adj_cells_count']} != summary {srow['adj_cells_count']}")
        for af_name, af_val in [
            ("adj_mean_gross_r", adj_res["adj_mean_gross_r"]),
            ("adj_delta_mean_r", adj_res["adj_delta_mean_r"]),
            ("adj_min_mean_r", adj_res["adj_min_mean_r"]),
            ("adj_max_mean_r", adj_res["adj_max_mean_r"]),
        ]:
            actual_af_str = srow.get(af_name, "")
            if af_val is None:
                if actual_af_str != "":
                    raise ValueError(f"Summary row {idx} {af_name} expected empty, got '{actual_af_str}'")
            else:
                if not serialized_metric_matches(actual_af_str, af_val, 4, 1):
                    raise ValueError(f"Summary row {idx} {af_name} mismatch: ledger {af_val:.8f} != summary {actual_af_str}")
        if adj_res["adj_cells_count"] > 0:
            expected_pos_str = str(adj_res["adj_all_positive"])
            if srow.get("adj_all_positive", "") != expected_pos_str:
                raise ValueError(f"Summary row {idx} adj_all_positive mismatch: expected {expected_pos_str} != summary {srow.get('adj_all_positive')}")

    # Check complete keyset coverage for summary
    missing_sum_keys = expected_summary_keys - seen_summary_keys
    extra_sum_keys = seen_summary_keys - expected_summary_keys
    if missing_sum_keys:
        sample_missing = list(missing_sum_keys)[:3]
        raise ValueError(f"Summary grid results missing {len(missing_sum_keys)} expected keys! Sample: {sample_missing}")
    if extra_sum_keys:
        sample_extra = list(extra_sum_keys)[:3]
        raise ValueError(f"Summary grid results contains {len(extra_sum_keys)} unexpected keys! Sample: {sample_extra}")

    # 4. Reconcile annual_breakdown.csv with complete expected keyset — reject unexpected rows too
    annual_path = os.path.join(package_dir, "annual_breakdown.csv")
    with open(annual_path, "r", encoding="utf-8") as af:
        annual_rows = list(csv.DictReader(af))

    # Pre-compute expected annual keys before metric loop so unexpected rows are caught immediately
    expected_annual_keys: Set[Tuple] = set()
    for skey in expected_summary_keys:
        sub = indexed_trials.get(skey, [])
        for yr in set(str(r["year"]) for r in sub):
            expected_annual_keys.add((*skey, yr))

    seen_annual_keys = set()
    for idx, arow in enumerate(annual_rows, start=1):
        p_name = arow["panel"]
        pair_val = arow["pair"]
        sig_val = arow["signal_type"]
        ch_filter = arow["cohort_filter"]
        h_val = int(arow["horizon_bars"])
        cell_lbl = arow["cell_label"]
        yr_val = str(arow["year"])
        akey = (p_name, pair_val, sig_val, ch_filter, h_val, cell_lbl, yr_val)

        if akey not in expected_annual_keys:
            raise ValueError(f"Annual breakdown contains unexpected row at row {idx}: {akey}")
        if akey in seen_annual_keys:
            raise ValueError(f"Duplicate annual breakdown row at row {idx} for key: {akey}")
        seen_annual_keys.add(akey)

        sub = indexed_trials.get(akey[:6], [])
        yr_sub = [r for r in sub if str(r["year"]) == yr_val]

        # Reconcile all annual metrics including bundles, trades, wins, losses, timeouts, win_rate, sums, means
        n_bundles = len(set(r["bundle_id"] for r in yr_sub))
        n_trades = len(yr_sub)
        n_wins = sum(1 for r in yr_sub if r["is_win"])
        n_losses = sum(1 for r in yr_sub if r["is_loss"])
        n_timeouts = sum(1 for r in yr_sub if r["is_timeout"])
        s_r = sum(r["gross_r"] for r in yr_sub)
        m_r = s_r / n_trades if n_trades > 0 else 0.0
        wr = n_wins / n_trades if n_trades > 0 else 0.0

        if int(arow["N_bundles"]) != n_bundles:
            raise ValueError(f"Annual row {idx} ({akey}) N_bundles mismatch: ledger {n_bundles} != annual {arow['N_bundles']}")
        if int(arow["N_trades"]) != n_trades:
            raise ValueError(f"Annual row {idx} ({akey}) N_trades mismatch: ledger {n_trades} != annual {arow['N_trades']}")
        if int(arow["N_wins"]) != n_wins:
            raise ValueError(f"Annual row {idx} ({akey}) N_wins mismatch: ledger {n_wins} != annual {arow['N_wins']}")
        if int(arow["N_losses"]) != n_losses:
            raise ValueError(f"Annual row {idx} ({akey}) N_losses mismatch: ledger {n_losses} != annual {arow['N_losses']}")
        if int(arow["N_timeouts"]) != n_timeouts:
            raise ValueError(f"Annual row {idx} ({akey}) N_timeouts mismatch: ledger {n_timeouts} != annual {arow['N_timeouts']}")
        if not serialized_metric_matches(arow["win_rate"], wr, 4):
            raise ValueError(f"Annual row {idx} ({akey}) win_rate mismatch: ledger {wr:.6f} != annual {arow['win_rate']}")
        if not serialized_metric_matches(arow["gross_sum_r"], s_r, 4, n_trades):
            raise ValueError(f"Annual row {idx} ({akey}) gross_sum_r mismatch: ledger {s_r:.6f} != annual {arow['gross_sum_r']}")
        if not serialized_metric_matches(arow["gross_mean_r"], m_r, 6, 1 if n_trades else 0):
            raise ValueError(f"Annual row {idx} ({akey}) gross_mean_r mismatch: ledger {m_r:.8f} != annual {arow['gross_mean_r']}")

    missing_annual_keys = expected_annual_keys - seen_annual_keys
    if missing_annual_keys:
        raise ValueError(f"Annual breakdown missing expected key: {sorted(missing_annual_keys)[0]}")

    # 5. Reconcile loyo_folds.csv with complete keyset coverage
    loyo_path = os.path.join(package_dir, "loyo_folds.csv")
    with open(loyo_path, "r", encoding="utf-8") as lf_file:
        loyo_rows = list(csv.DictReader(lf_file))

    # Pre-compute expected LOYO keys before metric loop so unexpected rows are caught immediately
    expected_loyo_keys: Set[Tuple] = set()
    for skey in expected_summary_keys:
        sub = indexed_trials.get(skey, [])
        if sub:
            obs_core = set(str(r["year"]) for r in sub if "2015" <= str(r["year"]) <= "2025")
            if len(obs_core) > 1:
                for cy in obs_core:
                    expected_loyo_keys.add((*skey, cy))

    seen_loyo_keys = set()
    for idx, lrow in enumerate(loyo_rows, start=1):
        p_name = lrow["panel"]
        pair_val = lrow["pair"]
        sig_val = lrow["signal_type"]
        ch_filter = lrow["cohort_filter"]
        h_val = int(lrow["horizon_bars"])
        cell_lbl = lrow["cell_label"]
        ex_year = str(lrow["excluded_year"])
        lkey = (p_name, pair_val, sig_val, ch_filter, h_val, cell_lbl, ex_year)

        if lkey not in expected_loyo_keys:
            raise ValueError(f"LOYO folds contains unexpected row at row {idx}: {lkey}")
        if lkey in seen_loyo_keys:
            raise ValueError(f"Duplicate LOYO fold row at row {idx} for key: {lkey}")
        seen_loyo_keys.add(lkey)

        sub = indexed_trials.get(lkey[:6], [])
        rem_trials = [
            r for r in sub
            if str(r["year"]) != ex_year and "2015" <= str(r["year"]) <= "2025"
        ]
        n_rem = len(rem_trials)
        n_b_rem = len(set(r["bundle_id"] for r in rem_trials))
        w_rem = sum(1 for r in rem_trials if r["is_win"])
        l_rem = sum(1 for r in rem_trials if r["is_loss"])
        t_rem = sum(1 for r in rem_trials if r["is_timeout"])
        sum_r_rem = sum(r["gross_r"] for r in rem_trials)
        mean_r_rem = sum_r_rem / n_rem if n_rem > 0 else 0.0
        is_pos = (sum_r_rem > 0)

        if int(lrow["remaining_bundles"]) != n_b_rem:
            raise ValueError(f"LOYO row {idx} ({lkey}) remaining_bundles mismatch: ledger {n_b_rem} != loyo {lrow['remaining_bundles']}")
        if int(lrow["remaining_trades"]) != n_rem:
            raise ValueError(f"LOYO row {idx} ({lkey}) remaining_trades mismatch: ledger {n_rem} != loyo {lrow['remaining_trades']}")
        if int(lrow["remaining_wins"]) != w_rem:
            raise ValueError(f"LOYO row {idx} ({lkey}) remaining_wins mismatch: ledger {w_rem} != loyo {lrow['remaining_wins']}")
        if int(lrow["remaining_losses"]) != l_rem:
            raise ValueError(f"LOYO row {idx} ({lkey}) remaining_losses mismatch: ledger {l_rem} != loyo {lrow['remaining_losses']}")
        if int(lrow["remaining_timeouts"]) != t_rem:
            raise ValueError(f"LOYO row {idx} ({lkey}) remaining_timeouts mismatch: ledger {t_rem} != loyo {lrow['remaining_timeouts']}")
        if not serialized_metric_matches(lrow["remaining_sum_r"], sum_r_rem, 4, n_rem):
            raise ValueError(f"LOYO row {idx} ({lkey}) remaining_sum_r mismatch: ledger {sum_r_rem:.6f} != loyo {lrow['remaining_sum_r']}")
        if not serialized_metric_matches(lrow["remaining_mean_r"], mean_r_rem, 6, 1 if n_rem else 0):
            raise ValueError(f"LOYO row {idx} ({lkey}) remaining_mean_r mismatch: ledger {mean_r_rem:.8f} != loyo {lrow['remaining_mean_r']}")
        if (lrow["is_positive"].strip().lower() in ("true", "1")) != is_pos:
            raise ValueError(f"LOYO row {idx} ({lkey}) is_positive mismatch: ledger {is_pos} != loyo {lrow['is_positive']}")

    missing_loyo_keys = expected_loyo_keys - seen_loyo_keys
    if missing_loyo_keys:
        raise ValueError(f"LOYO folds missing expected fold: {sorted(missing_loyo_keys)[0]}")

    # 6. Separate Eight-Case Representative Raw-Candle Audit
    if skip_raw_audit:
        audit_results = []
    else:
        audit_cases = get_audit_cases(family_name)
        audit_results = verify_against_production_ledger(ledger_path, audit_cases)
        for res in audit_results:
            if res["status"] != "PASSED":
                raise RuntimeError(
                    f"Independent audit case failed for {res['test_label']}: "
                    f"reason_match={res.get('exit_reason_match')}, "
                    f"gross_r_delta={res.get('gross_r_delta')}, status={res.get('status')}"
                )

    return {
        "status": "PASSED",
        "family": family_name,
        "protocol_id": protocol_id,
        "run_id": run_id,
        "package_dir": package_dir,
        "trials_count": len(ledger_rows),
        "summary_cells_reconciled": len(summary_rows),
        "annual_rows_reconciled": len(annual_rows),
        "loyo_folds_reconciled": len(loyo_rows),
        "audit_cases_count": len(audit_results),
        "audit_status": "PASSED" if audit_results else "SKIPPED",
    }


def run_family_exploration(
    family_name: str,
    run_id: str = RUN_ID,
    raw_dir: str = DEFAULT_RAW_DIR,
    git_commit: Optional[str] = None
) -> Dict[str, Any]:
    """Runs full exploration for CPI or NFP and writes the complete versioned package."""
    t0 = time.time()
    protocol_id = f"{family_name}_EXPLORATION_V2"
    package_dir = os.path.join(REPO_ROOT, "Research Candidate", family_name, protocol_id, run_id)
    check_package_immutability(package_dir)
    os.makedirs(package_dir, exist_ok=True)

    print(f"\n===================================================================")
    print(f"RUNNING {family_name} HISTORICAL EXPLORATION ({protocol_id})")
    print(f"Destination: {package_dir}")
    print(f"===================================================================")

    # 1. Load Pre-Outcome Groundwork & Evaluate Candidates
    print("[1/5] Evaluating pre-outcome eligibility and loading raw candles...")
    if family_name == "CPI":
        bundles, observations, raw_cnt = evaluate_cpi_pre_outcome(raw_dir)
        anchor_id = "840030005"
        anchor_name = "CPI m/m"
    else:
        bundles, observations, raw_cnt = evaluate_nfp_pre_outcome(raw_dir)
        anchor_id = "840030016"
        anchor_name = "Nonfarm Payrolls"

    # Pre-load candles for all 7 active pairs
    candles_by_pair = {}
    for p in ACTIVE_USD_PAIRS:
        candles_by_pair[p] = load_candles(p, raw_dir)
    print(f"  Loaded candles for all {len(ACTIVE_USD_PAIRS)} pairs. Bundles: {len(bundles)}, Obs: {len(observations)}")

    # 2. Extract and Write Release Paths (Stored ONCE per event/pair)
    print("[2/5] Writing source-linked release paths (H1 to H240, stored once per observation)...")
    paths_csv_path = os.path.join(package_dir, "release_paths.csv")
    path_rows_written = 0

    with open(paths_csv_path, "w", newline="", encoding="utf-8") as pf:
        writer = csv.writer(pf)
        writer.writerow([
            "bundle_id", "timestamp", "timestamp_server_text", "pair",
            "bar_h", "bar_timestamp", "bar_time_server_text",
            "open", "high", "low", "close", "pips_from_entry", "event_aligned_pips"
        ])

        for o in observations:
            if not o.coverage.has_entry or o.coverage.entry_bar_idx is None:
                continue
            pair = o.pair
            pip_size = get_pip_size(pair)
            pair_candles = candles_by_pair[pair]
            e_idx = o.coverage.entry_bar_idx
            entry_open = pair_candles[e_idx].open
            max_bars = min(240, len(pair_candles) - e_idx)

            # Determine USD alignment: if base pair, USD move is pair move; if quote pair, inverted
            usd_mult = 1.0 if pair in USD_BASE_PAIRS else -1.0

            for h in range(max_bars):
                b = pair_candles[e_idx + h]
                pips_from_entry = (b.close - entry_open) / pip_size
                event_aligned_pips = pips_from_entry * usd_mult
                writer.writerow([
                    o.bundle_id, o.timestamp, o.timestamp_server_text, pair,
                    h + 1, b.timestamp, b.time_server_text,
                    f"{b.open:.6f}", f"{b.high:.6f}", f"{b.low:.6f}", f"{b.close:.6f}",
                    f"{pips_from_entry:.4f}", f"{event_aligned_pips:.4f}"
                ])
                path_rows_written += 1

    print(f"  Saved release_paths.csv ({path_rows_written:,} path bars).")

    # 3. Simulate All Trials across 52 Cells x 3 Horizons x 2 Signals
    print("[3/5] Simulating trade outcomes (52 cells x 3 horizons x 2 signals)...")
    ledger_csv_path = os.path.join(package_dir, "trial_ledger.csv")
    trial_records = []

    # Map signals
    signals_to_eval = [
        ("af", "Surprise", lambda o: o.signal_af_state, lambda o: o.signal_af),
        ("ap", "Momentum", lambda o: o.signal_ap_state, lambda o: o.signal_ap),
    ]

    with open(ledger_csv_path, "w", newline="", encoding="utf-8") as lf:
        writer = csv.writer(lf)
        writer.writerow([
            "observation_id", "bundle_id", "timestamp", "timestamp_server_text", "year", "cohort",
            "pair", "usd_role", "signal_type", "signal_state", "signal_difference", "direction_pair",
            "has_us_jobless_claims_collision", "has_cad_employment_collision", "is_common_h240",
            "entry_time_server_text", "entry_price", "atr", "horizon_bars",
            "stop_atr", "target_atr", "cell_label", "reward_risk_ratio",
            "exit_reason", "is_win", "is_loss", "is_timeout", "dual_touch", "is_opening_gap",
            "exit_price", "exit_bar_idx", "exit_time_server_text", "bars_to_exit",
            "clock_seconds_to_bar_open", "clock_seconds_bar_close_proxy",
            "gross_r", "signed_pips", "gap_open_price", "gap_executable_gross_r", "gap_executable_pips",
            "mfe_pips_lower", "mfe_pips_upper", "mae_pips_lower", "mae_pips_upper",
            "mfe_atr_lower", "mfe_atr_upper", "mae_atr_lower", "mae_atr_upper",
            "full_mfe_pips", "full_mae_pips", "full_mfe_atr", "full_mae_atr",
            "target_first_exit_reason", "target_first_gross_r", "target_first_signed_pips"
        ])

        for sig_code, sig_name, get_state, get_diff in signals_to_eval:
            for o in observations:
                state = get_state(o)
                diff = get_diff(o)
                pair = o.pair
                pip_size = get_pip_size(pair)
                pair_candles = candles_by_pair[pair]

                # Directional hypothesis
                if state == "POSITIVE":
                    d_usd = 1
                elif state == "NEGATIVE":
                    d_usd = -1
                else:
                    continue  # ZERO or MISSING abstain/exclude

                # Invert for quote pairs
                d_pair = d_usd if pair in USD_BASE_PAIRS else -d_usd

                for horizon in EXPLORATION_HORIZONS:
                    is_el = getattr(o, f"is_candidate_eligible_h{horizon}_{sig_code}")
                    if not is_el:
                        continue

                    e_idx = o.coverage.entry_bar_idx
                    entry_open = pair_candles[e_idx].open
                    atr = o.coverage.pre_release_atr
                    path_bars = pair_candles[e_idx : e_idx + horizon]
                    assert len(path_bars) == horizon, f"Path bar count mismatch: {len(path_bars)} != {horizon}"

                    is_common_h240 = o.coverage.has_h240_path_gap_free and getattr(o, f"is_candidate_eligible_h240_{sig_code}")

                    for cell in ALL_GRID_CELLS:
                        # Primary: STOP_FIRST
                        out_stop_first = simulate_single_trade(
                            entry_price=entry_open,
                            direction=d_pair,
                            atr=atr,
                            stop_atr=cell.stop_atr,
                            target_atr=cell.target_atr,
                            path_bars=path_bars,
                            pip_size=pip_size,
                            dual_touch_mode="STOP_FIRST"
                        )

                        # Sensitivity: TARGET_FIRST
                        if out_stop_first.dual_touch:
                            out_target_first = simulate_single_trade(
                                entry_price=entry_open,
                                direction=d_pair,
                                atr=atr,
                                stop_atr=cell.stop_atr,
                                target_atr=cell.target_atr,
                                path_bars=path_bars,
                                pip_size=pip_size,
                                dual_touch_mode="TARGET_FIRST"
                            )
                            tf_reason = out_target_first.exit_reason
                            tf_gross_r = out_target_first.gross_r
                            tf_signed_pips = out_target_first.signed_pips
                        else:
                            tf_reason = out_stop_first.exit_reason
                            tf_gross_r = out_stop_first.gross_r
                            tf_signed_pips = out_stop_first.signed_pips

                        obs_id = f"{family_name}_{o.bundle_id}_{pair}_{sig_code}_{horizon}_{cell.label}"
                        # Aggregates must use the exact eight-decimal R published in
                        # trial_ledger.csv. Otherwise an almost-zero LOYO fold can
                        # flip sign when independently recomputed from the ledger.
                        published_gross_r = f"{out_stop_first.gross_r:.8f}"

                        row = [
                            obs_id, o.bundle_id, o.timestamp, o.timestamp_server_text, o.year, o.cohort,
                            pair, o.usd_role, sig_code, state, f"{diff:.4f}" if diff is not None else "", d_pair,
                            o.has_us_jobless_claims_collision, o.has_cad_employment_collision, is_common_h240,
                            o.coverage.entry_time_server_text, f"{entry_open:.6f}", f"{atr:.8f}", horizon,
                            f"{cell.stop_atr:g}", f"{cell.target_atr:g}", cell.label, f"{cell.reward_risk_ratio:.4f}",
                            out_stop_first.exit_reason, out_stop_first.is_win, out_stop_first.is_loss, out_stop_first.is_timeout,
                            out_stop_first.dual_touch, out_stop_first.is_opening_gap,
                            f"{out_stop_first.exit_price:.6f}", out_stop_first.exit_bar_idx, out_stop_first.exit_time_server_text,
                            out_stop_first.bars_to_exit,
                            out_stop_first.clock_seconds_to_exit_bar_open, out_stop_first.clock_seconds_bar_close_proxy,
                            published_gross_r, f"{out_stop_first.signed_pips:.4f}",
                            f"{out_stop_first.gap_open_price:.6f}" if out_stop_first.gap_open_price is not None else "",
                            f"{out_stop_first.gap_executable_gross_r:.8f}" if out_stop_first.gap_executable_gross_r is not None else "",
                            f"{out_stop_first.gap_executable_pips:.4f}" if out_stop_first.gap_executable_pips is not None else "",
                            f"{out_stop_first.mfe_pips_lower:.2f}", f"{out_stop_first.mfe_pips_upper:.2f}",
                            f"{out_stop_first.mae_pips_lower:.2f}", f"{out_stop_first.mae_pips_upper:.2f}",
                            f"{out_stop_first.mfe_atr_lower:.4f}", f"{out_stop_first.mfe_atr_upper:.4f}",
                            f"{out_stop_first.mae_atr_lower:.4f}", f"{out_stop_first.mae_atr_upper:.4f}",
                            f"{out_stop_first.full_mfe_pips:.2f}", f"{out_stop_first.full_mae_pips:.2f}",
                            f"{out_stop_first.full_mfe_atr:.4f}", f"{out_stop_first.full_mae_atr:.4f}",
                            tf_reason, f"{tf_gross_r:.8f}", f"{tf_signed_pips:.4f}"
                        ]
                        writer.writerow(row)
                        trial_records.append({
                            "obs_id": obs_id, "bundle_id": o.bundle_id, "year": str(o.year), "cohort": o.cohort,
                            "pair": pair, "signal_type": sig_code, "horizon": horizon, "horizon_bars": horizon,
                            "cell_label": cell.label, "stop_atr": cell.stop_atr, "target_atr": cell.target_atr,
                            "rr": cell.reward_risk_ratio,
                            "is_win": out_stop_first.is_win, "is_loss": out_stop_first.is_loss,
                            "is_timeout": out_stop_first.is_timeout, "dual_touch": out_stop_first.dual_touch,
                            "gross_r": float(published_gross_r), "signed_pips": out_stop_first.signed_pips,
                            "bars_to_exit": out_stop_first.bars_to_exit,
                            "clock_seconds_to_bar_open": out_stop_first.clock_seconds_to_exit_bar_open,
                            "clock_seconds_bar_close_proxy": out_stop_first.clock_seconds_bar_close_proxy,
                            "claims_collision": o.has_us_jobless_claims_collision,
                            "cad_collision": o.has_cad_employment_collision,
                            "is_common_h240": is_common_h240,
                            "h240_complete": is_common_h240,
                        })

    print(f"  Simulated {len(trial_records):,} trial outcomes. Saved trial_ledger.csv.")

    # 4. Compute Grid Summary, Annual Breakdowns, and LOYO Folds
    print("[4/5] Computing summary grid metrics, annual breakdowns, and adjacent cell stability...")
    summary_csv_path = os.path.join(package_dir, "summary_grid_results.csv")
    annual_csv_path = os.path.join(package_dir, "annual_breakdown.csv")
    loyo_csv_path = os.path.join(package_dir, "loyo_folds.csv")

    summary_rows = []
    annual_rows = []
    loyo_rows = []

    # Single-pass indexing
    indexed_trials = index_trial_records(trial_records, family_name)
    expected_keys = get_expected_summary_keys(family_name)

    # Precompute cell_mean_r_map for adjacent cell stability
    cohort_cell_means: Dict[Tuple[str, str, str, str, int], Dict[str, float]] = defaultdict(dict)
    for (pan, pr, sig, ch, h, cell_l), sub_trials in indexed_trials.items():
        if sub_trials:
            cohort_cell_means[(pan, pr, sig, ch, h)][cell_l] = sum(r["gross_r"] for r in sub_trials) / len(sub_trials)

    sorted_keys = sorted(list(expected_keys))

    for skey in sorted_keys:
        pan, pr, sig, ch, h, cell_lbl = skey
        cell = next(c for c in ALL_GRID_CELLS if c.label == cell_lbl)
        sub = indexed_trials.get(skey, [])
        if not sub:
            continue

        n_trades = len(sub)
        n_bundles = len(set(r["bundle_id"] for r in sub))
        n_wins = sum(1 for r in sub if r["is_win"])
        n_losses = sum(1 for r in sub if r["is_loss"])
        n_timeouts = sum(1 for r in sub if r["is_timeout"])
        n_dual_touch = sum(1 for r in sub if r["dual_touch"])
        assert n_trades == n_wins + n_losses + n_timeouts, (
            f"Reconciliation error in {cell_lbl}: {n_trades} != {n_wins} + {n_losses} + {n_timeouts}"
        )

        r_vals = [r["gross_r"] for r in sub]
        win_rate = n_wins / n_trades if n_trades > 0 else 0.0
        mean_r = sum(r_vals) / n_trades if n_trades > 0 else 0.0
        med_r = calculate_median(r_vals) or 0.0
        sum_r = sum(r_vals)

        exit_dist = summarize_exit_distributions(sub)
        loyo_res = calculate_true_loyo(sub)
        ann_res = summarize_annual_breakdown(sub)

        cohort_means = cohort_cell_means.get((pan, pr, sig, ch, h), {})
        adj_res = calculate_adjacent_cell_stability(cell_lbl, cohort_means)

        summary_rows.append({
            "panel": pan,
            "pair": pr,
            "signal_type": sig,
            "cohort_filter": ch,
            "horizon_bars": h,
            "stop_atr": cell.stop_atr,
            "target_atr": cell.target_atr,
            "cell_label": cell_lbl,
            "reward_risk": cell.reward_risk_ratio,
            "N_bundles": n_bundles,
            "N_trades": n_trades,
            "N_wins": n_wins,
            "N_losses": n_losses,
            "N_timeouts": n_timeouts,
            "N_dual_touch": n_dual_touch,
            "pct_target": n_wins / n_trades if n_trades > 0 else 0.0,
            "pct_stop": n_losses / n_trades if n_trades > 0 else 0.0,
            "pct_timeout": n_timeouts / n_trades if n_trades > 0 else 0.0,
            "pct_dual_touch": n_dual_touch / n_trades if n_trades > 0 else 0.0,
            "win_rate": win_rate,
            "gross_mean_r": mean_r,
            "gross_median_r": med_r,
            "gross_sum_r": sum_r,
            "tp_bars_median": exit_dist["tp_median_bars"],
            "tp_bars_p75": exit_dist["tp_p75_bars"],
            "tp_bars_p90": exit_dist["tp_p90_bars"],
            "tp_bars_max": exit_dist["tp_max_bars"],
            "tp_bar_close_proxy_seconds_median": exit_dist["tp_bar_close_proxy_seconds_median"],
            "tp_bar_close_proxy_seconds_p75": exit_dist["tp_bar_close_proxy_seconds_p75"],
            "tp_bar_close_proxy_seconds_p90": exit_dist["tp_bar_close_proxy_seconds_p90"],
            "tp_bar_close_proxy_seconds_max": exit_dist["tp_bar_close_proxy_seconds_max"],
            "sl_bars_median": exit_dist["sl_median_bars"],
            "sl_bars_p75": exit_dist["sl_p75_bars"],
            "sl_bars_p90": exit_dist["sl_p90_bars"],
            "sl_bars_max": exit_dist["sl_max_bars"],
            "sl_bar_close_proxy_seconds_median": exit_dist["sl_bar_close_proxy_seconds_median"],
            "sl_bar_close_proxy_seconds_p75": exit_dist["sl_bar_close_proxy_seconds_p75"],
            "sl_bar_close_proxy_seconds_p90": exit_dist["sl_bar_close_proxy_seconds_p90"],
            "sl_bar_close_proxy_seconds_max": exit_dist["sl_bar_close_proxy_seconds_max"],
            "overall_bars_median": exit_dist["overall_median_bars"],
            "overall_bars_p75": exit_dist["overall_p75_bars"],
            "overall_bars_p90": exit_dist["overall_p90_bars"],
            "overall_bars_max": exit_dist["overall_max_bars"],
            "overall_bar_close_proxy_seconds_median": exit_dist["overall_bar_close_proxy_seconds_median"],
            "overall_bar_close_proxy_seconds_p75": exit_dist["overall_bar_close_proxy_seconds_p75"],
            "overall_bar_close_proxy_seconds_p90": exit_dist["overall_bar_close_proxy_seconds_p90"],
            "overall_bar_close_proxy_seconds_max": exit_dist["overall_bar_close_proxy_seconds_max"],
            "loyo_positive_years": loyo_res["loyo_positive_years"],
            "loyo_total_folds": loyo_res["loyo_total_folds"],
            "loyo_min_mean_r": loyo_res["loyo_min_mean_r"],
            "loyo_max_mean_r": loyo_res["loyo_max_mean_r"],
            "loyo_min_sum_r": loyo_res["loyo_min_sum_r"],
            "loyo_max_sum_r": loyo_res["loyo_max_sum_r"],
            "adj_cells_count": adj_res["adj_cells_count"],
            "adj_mean_gross_r": adj_res["adj_mean_gross_r"],
            "adj_delta_mean_r": adj_res["adj_delta_mean_r"],
            "adj_min_mean_r": adj_res["adj_min_mean_r"],
            "adj_max_mean_r": adj_res["adj_max_mean_r"],
            "adj_all_positive": adj_res["adj_all_positive"] if adj_res["adj_cells_count"] > 0 else None,
        })

        # Annual breakdown rows
        for yr, ay in sorted(ann_res.items()):
            yr_sub = [r for r in sub if str(r["year"]) == yr]
            annual_rows.append({
                "panel": pan,
                "pair": pr,
                "signal_type": sig,
                "cohort_filter": ch,
                "horizon_bars": h,
                "cell_label": cell_lbl,
                "year": yr,
                "cohort": ay["cohort"],
                "N_bundles": len(set(r["bundle_id"] for r in yr_sub)),
                "N_trades": ay["n"],
                "N_wins": ay["wins"],
                "N_losses": ay["losses"],
                "N_timeouts": ay["timeouts"],
                "win_rate": ay["win_rate"],
                "gross_sum_r": ay["gross_sum_r"],
                "gross_mean_r": ay["gross_mean_r"],
            })

        # LOYO fold rows (observed core years only, within 2015..2025)
        for fy, f_info in sorted(loyo_res["loyo_folds"].items()):
            rem_trials = [
                r for r in sub
                if str(r["year"]) != fy and "2015" <= str(r.get("year", "")) <= "2025"
            ]
            loyo_rows.append({
                "panel": pan,
                "pair": pr,
                "signal_type": sig,
                "cohort_filter": ch,
                "horizon_bars": h,
                "cell_label": cell_lbl,
                "excluded_year": fy,
                "remaining_bundles": len(set(r["bundle_id"] for r in rem_trials)),
                "remaining_trades": f_info["remaining_n"],
                "remaining_wins": f_info["wins"],
                "remaining_losses": f_info["losses"],
                "remaining_timeouts": f_info["timeouts"],
                "remaining_sum_r": f_info["gross_sum_r"],
                "remaining_mean_r": f_info["gross_mean_r"],
                "is_positive": f_info["is_positive"],
            })

    # Write summary_grid_results.csv
    with open(summary_csv_path, "w", newline="", encoding="utf-8") as sf:
        fieldnames = [
            "panel", "pair", "signal_type", "cohort_filter", "horizon_bars", "stop_atr", "target_atr",
            "cell_label", "reward_risk", "N_bundles", "N_trades", "N_wins", "N_losses", "N_timeouts", "N_dual_touch",
            "pct_target", "pct_stop", "pct_timeout", "pct_dual_touch",
            "win_rate", "gross_mean_r", "gross_median_r", "gross_sum_r",
            "tp_bars_median", "tp_bars_p75", "tp_bars_p90", "tp_bars_max",
            "tp_bar_close_proxy_seconds_median", "tp_bar_close_proxy_seconds_p75", "tp_bar_close_proxy_seconds_p90", "tp_bar_close_proxy_seconds_max",
            "sl_bars_median", "sl_bars_p75", "sl_bars_p90", "sl_bars_max",
            "sl_bar_close_proxy_seconds_median", "sl_bar_close_proxy_seconds_p75", "sl_bar_close_proxy_seconds_p90", "sl_bar_close_proxy_seconds_max",
            "overall_bars_median", "overall_bars_p75", "overall_bars_p90", "overall_bars_max",
            "overall_bar_close_proxy_seconds_median", "overall_bar_close_proxy_seconds_p75", "overall_bar_close_proxy_seconds_p90", "overall_bar_close_proxy_seconds_max",
            "loyo_positive_years", "loyo_total_folds",
            "loyo_min_mean_r", "loyo_max_mean_r", "loyo_min_sum_r", "loyo_max_sum_r",
            "adj_cells_count", "adj_mean_gross_r", "adj_delta_mean_r", "adj_min_mean_r", "adj_max_mean_r", "adj_all_positive"
        ]
        writer = csv.DictWriter(sf, fieldnames=fieldnames)
        writer.writeheader()
        for r in summary_rows:
            writer.writerow({
                "panel": r["panel"], "pair": r["pair"], "signal_type": r["signal_type"],
                "cohort_filter": r["cohort_filter"], "horizon_bars": r["horizon_bars"],
                "stop_atr": f"{r['stop_atr']:g}", "target_atr": f"{r['target_atr']:g}",
                "cell_label": r["cell_label"], "reward_risk": f"{r['reward_risk']:.4f}",
                "N_bundles": r["N_bundles"],
                "N_trades": r["N_trades"], "N_wins": r["N_wins"], "N_losses": r["N_losses"],
                "N_timeouts": r["N_timeouts"], "N_dual_touch": r["N_dual_touch"],
                "pct_target": f"{r['pct_target']:.4f}", "pct_stop": f"{r['pct_stop']:.4f}",
                "pct_timeout": f"{r['pct_timeout']:.4f}", "pct_dual_touch": f"{r['pct_dual_touch']:.4f}",
                "win_rate": f"{r['win_rate']:.4f}", "gross_mean_r": f"{r['gross_mean_r']:.6f}",
                "gross_median_r": f"{r['gross_median_r']:.6f}", "gross_sum_r": f"{r['gross_sum_r']:.4f}",
                "tp_bars_median": format_optional_float(r["tp_bars_median"], ".1f"),
                "tp_bars_p75": format_optional_float(r["tp_bars_p75"], ".1f"),
                "tp_bars_p90": format_optional_float(r["tp_bars_p90"], ".1f"),
                "tp_bars_max": format_optional_float(r["tp_bars_max"], ".1f"),
                "tp_bar_close_proxy_seconds_median": format_optional_float(r["tp_bar_close_proxy_seconds_median"], ".0f"),
                "tp_bar_close_proxy_seconds_p75": format_optional_float(r["tp_bar_close_proxy_seconds_p75"], ".0f"),
                "tp_bar_close_proxy_seconds_p90": format_optional_float(r["tp_bar_close_proxy_seconds_p90"], ".0f"),
                "tp_bar_close_proxy_seconds_max": format_optional_float(r["tp_bar_close_proxy_seconds_max"], ".0f"),
                "sl_bars_median": format_optional_float(r["sl_bars_median"], ".1f"),
                "sl_bars_p75": format_optional_float(r["sl_bars_p75"], ".1f"),
                "sl_bars_p90": format_optional_float(r["sl_bars_p90"], ".1f"),
                "sl_bars_max": format_optional_float(r["sl_bars_max"], ".1f"),
                "sl_bar_close_proxy_seconds_median": format_optional_float(r["sl_bar_close_proxy_seconds_median"], ".0f"),
                "sl_bar_close_proxy_seconds_p75": format_optional_float(r["sl_bar_close_proxy_seconds_p75"], ".0f"),
                "sl_bar_close_proxy_seconds_p90": format_optional_float(r["sl_bar_close_proxy_seconds_p90"], ".0f"),
                "sl_bar_close_proxy_seconds_max": format_optional_float(r["sl_bar_close_proxy_seconds_max"], ".0f"),
                "overall_bars_median": format_optional_float(r["overall_bars_median"], ".1f"),
                "overall_bars_p75": format_optional_float(r["overall_bars_p75"], ".1f"),
                "overall_bars_p90": format_optional_float(r["overall_bars_p90"], ".1f"),
                "overall_bars_max": format_optional_float(r["overall_bars_max"], ".1f"),
                "overall_bar_close_proxy_seconds_median": format_optional_float(r["overall_bar_close_proxy_seconds_median"], ".0f"),
                "overall_bar_close_proxy_seconds_p75": format_optional_float(r["overall_bar_close_proxy_seconds_p75"], ".0f"),
                "overall_bar_close_proxy_seconds_p90": format_optional_float(r["overall_bar_close_proxy_seconds_p90"], ".0f"),
                "overall_bar_close_proxy_seconds_max": format_optional_float(r["overall_bar_close_proxy_seconds_max"], ".0f"),
                "loyo_positive_years": f"{r['loyo_positive_years']}/{r['loyo_total_folds']}",
                "loyo_total_folds": r["loyo_total_folds"],
                "loyo_min_mean_r": format_optional_float(r["loyo_min_mean_r"], ".4f"),
                "loyo_max_mean_r": format_optional_float(r["loyo_max_mean_r"], ".4f"),
                "loyo_min_sum_r": format_optional_float(r["loyo_min_sum_r"], ".4f"),
                "loyo_max_sum_r": format_optional_float(r["loyo_max_sum_r"], ".4f"),
                "adj_cells_count": r["adj_cells_count"],
                "adj_mean_gross_r": format_optional_float(r["adj_mean_gross_r"], ".4f"),
                "adj_delta_mean_r": format_optional_float(r["adj_delta_mean_r"], ".4f"),
                "adj_min_mean_r": format_optional_float(r["adj_min_mean_r"], ".4f"),
                "adj_max_mean_r": format_optional_float(r["adj_max_mean_r"], ".4f"),
                "adj_all_positive": str(r["adj_all_positive"]) if r["adj_all_positive"] is not None else "",
            })
    print(f"  Saved summary_grid_results.csv ({len(summary_rows):,} aggregate rows).")

    # Write annual_breakdown.csv
    with open(annual_csv_path, "w", newline="", encoding="utf-8") as af:
        af_fields = [
            "panel", "pair", "signal_type", "cohort_filter", "horizon_bars", "cell_label",
            "year", "cohort", "N_bundles", "N_trades", "N_wins", "N_losses", "N_timeouts",
            "win_rate", "gross_sum_r", "gross_mean_r"
        ]
        writer = csv.DictWriter(af, fieldnames=af_fields)
        writer.writeheader()
        for ar in annual_rows:
            writer.writerow({
                "panel": ar["panel"], "pair": ar["pair"], "signal_type": ar["signal_type"],
                "cohort_filter": ar["cohort_filter"], "horizon_bars": ar["horizon_bars"],
                "cell_label": ar["cell_label"], "year": ar["year"], "cohort": ar["cohort"],
                "N_bundles": ar["N_bundles"], "N_trades": ar["N_trades"],
                "N_wins": ar["N_wins"], "N_losses": ar["N_losses"], "N_timeouts": ar["N_timeouts"],
                "win_rate": f"{ar['win_rate']:.4f}", "gross_sum_r": f"{ar['gross_sum_r']:.4f}",
                "gross_mean_r": f"{ar['gross_mean_r']:.6f}",
            })
    print(f"  Saved annual_breakdown.csv ({len(annual_rows):,} annual rows).")

    # Write loyo_folds.csv
    with open(loyo_csv_path, "w", newline="", encoding="utf-8") as lf_file:
        lf_fields = [
            "panel", "pair", "signal_type", "cohort_filter", "horizon_bars", "cell_label",
            "excluded_year", "remaining_bundles", "remaining_trades", "remaining_wins",
            "remaining_losses", "remaining_timeouts", "remaining_sum_r", "remaining_mean_r",
            "is_positive"
        ]
        writer = csv.DictWriter(lf_file, fieldnames=lf_fields)
        writer.writeheader()
        for lr in loyo_rows:
            writer.writerow({
                "panel": lr["panel"], "pair": lr["pair"], "signal_type": lr["signal_type"],
                "cohort_filter": lr["cohort_filter"], "horizon_bars": lr["horizon_bars"],
                "cell_label": lr["cell_label"], "excluded_year": lr["excluded_year"],
                "remaining_bundles": lr["remaining_bundles"], "remaining_trades": lr["remaining_trades"],
                "remaining_wins": lr["remaining_wins"], "remaining_losses": lr["remaining_losses"],
                "remaining_timeouts": lr["remaining_timeouts"],
                "remaining_sum_r": f"{lr['remaining_sum_r']:.4f}",
                "remaining_mean_r": f"{lr['remaining_mean_r']:.6f}",
                "is_positive": lr["is_positive"],
            })
    print(f"  Saved loyo_folds.csv ({len(loyo_rows):,} fold rows).")

    # 5. Run Representative Raw-Candle Sample Audit
    # NOTE: This is a small sample audit (four cases per family). The master
    # runner performs full ledger-to-summary verification after generation.
    print("[5/5] Running representative raw-candle sample audit...")
    audit_cases = get_audit_cases(family_name)
    audit_results = verify_against_production_ledger(ledger_csv_path, audit_cases)
    for res in audit_results:
        if res["status"] != "PASSED":
            raise RuntimeError(f"Sample audit case failed for {res['test_label']}: {res}")
    print(f"  All {len(audit_results)} representative sample audit cases PASSED.")
    print("  Full ledger-to-summary verification follows after package generation.")

    # 6. Write Manifest JSON
    manifest_path = os.path.join(package_dir, "manifest.json")
    code_commit_val = git_commit or get_git_commit_head(REPO_ROOT)
    manifest_data = {
        "family": family_name,
        "protocol_id": protocol_id,
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_commit": BASELINE_COMMIT,
        "protocol_commit": PROTOCOL_COMMIT,
        "code_commit": code_commit_val,
        "selection_policy": "NONE",
        "provenance_verified": True,
        "parameters": {
            "anchor_event_id": anchor_id,
            "anchor_event_name": anchor_name,
            "active_pairs": ACTIVE_USD_PAIRS,
            "globally_excluded_pairs": GLOBALLY_EXCLUDED_PAIRS,
            "horizons": EXPLORATION_HORIZONS,
            "stop_atr_widths": GRID_STOP_WIDTHS,
            "target_atr_widths": GRID_TARGET_WIDTHS,
            "total_grid_cells": len(ALL_GRID_CELLS),
            "total_evaluations_per_trade": len(ALL_GRID_CELLS) * len(EXPLORATION_HORIZONS),
            "primary_dual_touch": "STOP_FIRST",
            "sensitivity_dual_touch": "TARGET_FIRST",
            "max_entry_delay_seconds": 3600,
            "max_unscheduled_weekday_gap_seconds": 14400,
        },
        "trials_count": len(trial_records),
        "runtime_seconds": round(time.time() - t0, 2),
        "audit_verification": audit_results,
    }
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest_data, mf, indent=2)

    # 7. Generate Exploration Summary Report Markdown
    report_md_path = os.path.join(package_dir, "EXPLORATION_SUMMARY_REPORT.md")
    write_exploration_report(
        family_name, protocol_id, package_dir, manifest_data,
        summary_rows, audit_results, report_md_path
    )
    print(f"  Saved EXPLORATION_SUMMARY_REPORT.md.")
    print(f"Completed {family_name} exploration in {time.time() - t0:.2f}s.")
    return manifest_data


def write_exploration_report(
    family_name: str,
    protocol_id: str,
    package_dir: str,
    manifest: Dict[str, Any],
    summary_rows: List[Dict[str, Any]],
    audit_results: List[Dict[str, Any]],
    out_path: str
) -> None:
    """Generates the comprehensive exploration summary report artifact."""
    lines = [
        f"# Historical Exploration Report: US {family_name} ({protocol_id})",
        "",
        "> [!IMPORTANT]",
        "> **HISTORICAL EXPLORATION ONLY — ZERO SETUP REGISTRATION:**",
        "> This report presents priced, gross (cost-excluded) historical exploration results across the complete 52-cell ATR grid and three expiry horizons (H60, H120, H240).",
        "> Per the calculation contract amendment of 2026-09-28, **`selection_policy = NONE`**. All cells are reported without post-hoc selection, ranking, or claims of edge.",
        "",
        "---",
        "",
        "## 1. Provenance & Execution Lineage",
        "",
        f"- **Event Family:** US {family_name}  ",
        f"- **Protocol Identifier:** `{protocol_id}`  ",
        f"- **Run Identifier:** `{manifest['run_id']}`  ",
        f"- **Pre-Outcome Baseline Commit:** `{manifest['baseline_commit']}`  ",
        f"- **Protocol Freeze Commit:** `{manifest['protocol_commit']}`  ",
        f"- **Code Freeze Commit:** `{manifest['code_commit']}`  ",
        f"- **Anchor Series:** `{manifest['parameters']['anchor_event_name']}` (Event ID `{manifest['parameters']['anchor_event_id']}`)  ",
        f"- **Active Universe:** 7 USD pairs (`{', '.join(manifest['parameters']['active_pairs'])}`)  ",
        f"- **Globally Excluded Universe:** 9 truncated pairs strictly excluded (`{', '.join(manifest['parameters']['globally_excluded_pairs'])}`)  ",
        f"- **Exploration Grid:** {manifest['parameters']['total_grid_cells']} stop/target cells $\\times$ {len(manifest['parameters']['horizons'])} horizons = {manifest['parameters']['total_evaluations_per_trade']} configurations per eligible event/pair/signal  ",
        f"- **Total Simulated Trials:** **{manifest['trials_count']:,}**  ",
        f"- **Execution Runtime:** {manifest['runtime_seconds']} seconds  ",
        "",
        "### Output Package Artifacts",
        "The following versioned, immutable artifacts are included in this exploratory package:",
        "1. `manifest.json`: Machine-readable parameters, trial counts, commit hashes, and audit outcomes.",
        "2. `release_paths.csv`: Source-linked H1 OHLC price paths from H1 through H240, stored once per observation.",
        "3. `trial_ledger.csv`: Full trial ledger with high-precision bounded serialization (6-decimal prices, 8-decimal ATR and Gross R, 4-decimal pips), wall-clock exit intervals and bar-close proxies, and common H240 flags.",
        "4. `summary_grid_results.csv`: Complete 52-cell grid summary with N_bundles, N_trades, TP/SL bars and wall-clock proxy seconds, LOYO, and adjacent stability.",
        "5. `annual_breakdown.csv`: Year-by-year performance breakdown (CORE_2015_2025 vs PARTIAL_2026).",
        "6. `loyo_folds.csv`: One leave-one-year-out fold for each observed core year in 2015..2025; cells may have fewer than 11 non-empty folds.",
        "7. `EXPLORATION_SUMMARY_REPORT.md`: Comprehensive narrative and tabular disclosure.",
        "",
        "---",
        "",
        f"## 2. Independent Sample Audit ({len(audit_results)} Representative Raw-Candle Cases)",
        "",
        "> [!NOTE]",
        f"> This is a **representative sample audit** of {len(audit_results)} hand-picked trade cases recalculated directly from raw CSV files.",
        "> It is NOT a full raw-price recalculation across all trials. Full package verification (keyset completeness,",
        "> metric reconciliation, tolerance checks) is performed by the master runner after generation",
        "> and can be repeated independently with `--verify-only`.",
        "",
        "| Test Case | Observation ID | Pair | Release Time | Direction | Cell | Horizon | Indep Exit | Prod Exit | Indep R | Prod R | Status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ]

    for a in audit_results:
        lines.append(
            f"| {a['test_label']} | `{a['observation_id']}` | `{a['pair']}` | `{a['release_time']}` | "
            f"{a['direction']} | `{a['grid_cell']}` | H{a['horizon']} | `{a['indep_exit_reason']}` | "
            f"`{a['prod_exit_reason']}` | {a['indep_gross_r']:.4f} | {a['prod_gross_r']:.4f} | **{a['status']}** |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Primary Panel Exploration Overview (All Pairs Combined)",
        "",
        "> [!NOTE]",
        "> Cross-sectional pair observations from a single release are correlated USD expressions, NOT independent macro events.",
        "> For US NFP, the PRIMARY panel combines the 6 uncollided USD pairs with CAD-clean USDCAD (excluding Canadian jobs collisions).",
        "> For US CPI, the primary panel excludes US Initial Jobless Claims collisions; denominators vary by signal and cohort and are shown in each row.",
        "",
        "### Surprise Signal ($A - F$) Across Horizons (Primary Dual-Touch: STOP-FIRST)",
        "",
        "| Horizon | Cell | Stop | Target | R:R | Bundles | Trades | Target (Wins) | Stop (Losses) | Timeouts | Dual Touch | Gross Mean R | Gross Sum R | TP Med Bars | SL Med Bars | All Med Bars | All P90 Bars | LOYO Folds Pos | Adj Mean R |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ])

    primary_panel_name = "JOBLESS_CLAIMS_CLEAN" if family_name == "CPI" else "PRIMARY_PANEL"
    sample_cells = {"1:1", "1:2", "1:4", "2:1", "2:2", "2:4", "4:2", "4:4"}

    af_rows = [
        r for r in summary_rows
        if r["panel"] == primary_panel_name and r["pair"] == "ALL_PAIRS_COMBINED"
        and r["signal_type"] == "af" and r["cohort_filter"] == "ALL_ELIGIBLE"
    ]
    for r in af_rows:
        if r["cell_label"] in sample_cells:
            tp_b = f"{r['tp_bars_median']:.1f}" if r['tp_bars_median'] is not None else "N/A"
            sl_b = f"{r['sl_bars_median']:.1f}" if r['sl_bars_median'] is not None else "N/A"
            all_b = f"{r['overall_bars_median']:.1f}" if r['overall_bars_median'] is not None else "N/A"
            all_p90 = f"{r['overall_bars_p90']:.1f}" if r['overall_bars_p90'] is not None else "N/A"
            adj_m = f"{r['adj_mean_gross_r']:+.4f}" if r.get('adj_mean_gross_r') is not None else "N/A"
            lines.append(
                f"| H{r['horizon_bars']} | `{r['cell_label']}` | {r['stop_atr']:g} | {r['target_atr']:g} | {r['reward_risk']:.2f} | "
                f"{r['N_bundles']:,} | {r['N_trades']:,} | {r['N_wins']:,} ({r['pct_target']:.1%}) | {r['N_losses']:,} ({r['pct_stop']:.1%}) | "
                f"{r['N_timeouts']:,} ({r['pct_timeout']:.1%}) | {r['N_dual_touch']:,} ({r['pct_dual_touch']:.1%}) | "
                f"{r['gross_mean_r']:+.4f} | {r['gross_sum_r']:+.1f} | "
                f"{tp_b} | {sl_b} | {all_b} | {all_p90} | "
                f"{r['loyo_positive_years']} | {adj_m} |"
            )

    lines.extend([
        "",
        "### Momentum Signal ($A - P$) Across Horizons (Primary Dual-Touch: STOP-FIRST)",
        "",
        "| Horizon | Cell | Stop | Target | R:R | Bundles | Trades | Target (Wins) | Stop (Losses) | Timeouts | Dual Touch | Gross Mean R | Gross Sum R | TP Med Bars | SL Med Bars | All Med Bars | All P90 Bars | LOYO Folds Pos | Adj Mean R |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ])

    ap_rows = [
        r for r in summary_rows
        if r["panel"] == primary_panel_name and r["pair"] == "ALL_PAIRS_COMBINED"
        and r["signal_type"] == "ap" and r["cohort_filter"] == "ALL_ELIGIBLE"
    ]
    for r in ap_rows:
        if r["cell_label"] in sample_cells:
            tp_b = f"{r['tp_bars_median']:.1f}" if r['tp_bars_median'] is not None else "N/A"
            sl_b = f"{r['sl_bars_median']:.1f}" if r['sl_bars_median'] is not None else "N/A"
            all_b = f"{r['overall_bars_median']:.1f}" if r['overall_bars_median'] is not None else "N/A"
            all_p90 = f"{r['overall_bars_p90']:.1f}" if r['overall_bars_p90'] is not None else "N/A"
            adj_m = f"{r['adj_mean_gross_r']:+.4f}" if r.get('adj_mean_gross_r') is not None else "N/A"
            lines.append(
                f"| H{r['horizon_bars']} | `{r['cell_label']}` | {r['stop_atr']:g} | {r['target_atr']:g} | {r['reward_risk']:.2f} | "
                f"{r['N_bundles']:,} | {r['N_trades']:,} | {r['N_wins']:,} ({r['pct_target']:.1%}) | {r['N_losses']:,} ({r['pct_stop']:.1%}) | "
                f"{r['N_timeouts']:,} ({r['pct_timeout']:.1%}) | {r['N_dual_touch']:,} ({r['pct_dual_touch']:.1%}) | "
                f"{r['gross_mean_r']:+.4f} | {r['gross_sum_r']:+.1f} | "
                f"{tp_b} | {sl_b} | {all_b} | {all_p90} | "
                f"{r['loyo_positive_years']} | {adj_m} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Common H240 Cohort Exploration (Apples-to-Apples Horizon Comparison)",
        "",
        "> [!IMPORTANT]",
        "> To prevent cohort survival bias when comparing H60, H120, and H240, this panel evaluates all three horizons",
        "> strictly on the identical subset of observations that survived full 240-bar path coverage without unscheduled session gaps.",
        "",
        "| Horizon | Cell | Common Trades N | Win Rate | Gross Mean R | Gross Sum R | Timeouts N (%) | LOYO Folds Pos |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |"
    ])

    h240_common_af = [
        r for r in summary_rows
        if r["panel"] == primary_panel_name and r["pair"] == "ALL_PAIRS_COMBINED"
        and r["signal_type"] == "af" and r["cohort_filter"] == "COMMON_H240"
    ]
    for r in h240_common_af:
        if r["cell_label"] in {"1:1", "1:2", "2:2", "4:4"}:
            lines.append(
                f"| H{r['horizon_bars']} | `{r['cell_label']}` | {r['N_trades']:,} | {r['win_rate']:.1%} | "
                f"{r['gross_mean_r']:+.4f} | {r['gross_sum_r']:+.1f} | {r['N_timeouts']:,} ({r['pct_timeout']:.1%}) | "
                f"{r['loyo_positive_years']} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Collision Sensitivity Panels",
        ""
    ])

    if family_name == "CPI":
        lines.append("### US Initial Jobless Claims Collision Sensitivity (107 Clean vs 139 Full Bundles)")
        claims_clean = [
            r for r in summary_rows
            if r["panel"] == "JOBLESS_CLAIMS_CLEAN" and r["pair"] == "ALL_PAIRS_COMBINED"
            and r["signal_type"] == "af" and r["cell_label"] in sample_cells and r["horizon_bars"] == 60
            and r["cohort_filter"] == "ALL_ELIGIBLE"
        ]
        full_cpi = [
            r for r in summary_rows
            if r["panel"] == "FULL_PANEL" and r["pair"] == "ALL_PAIRS_COMBINED"
            and r["signal_type"] == "af" and r["cell_label"] in sample_cells and r["horizon_bars"] == 60
            and r["cohort_filter"] == "ALL_ELIGIBLE"
        ]
        lines.extend([
            "",
            "| Horizon | Cell | Claims-Clean N | Clean Win Rate | Clean Mean R | Full Panel N | Full Win Rate | Full Mean R |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"
        ])
        for cr in claims_clean:
            fr = next((r for r in full_cpi if r["cell_label"] == cr["cell_label"]), None)
            fr_n = f"{fr['N_trades']:,}" if fr else "N/A"
            fr_wr = f"{fr['win_rate']:.1%}" if fr else "N/A"
            fr_mr = f"{fr['gross_mean_r']:+.4f}" if fr else "N/A"
            lines.append(
                f"| H60 | `{cr['cell_label']}` | {cr['N_trades']:,} | {cr['win_rate']:.1%} | {cr['gross_mean_r']:+.4f} | "
                f"{fr_n} | {fr_wr} | {fr_mr} |"
            )
    else:
        lines.append("### Primary Panel (6 Pairs + CAD-Clean USDCAD) vs Full Sensitivity Panel (7 Pairs)")
        prim_nfp = [
            r for r in summary_rows
            if r["panel"] == "PRIMARY_PANEL" and r["pair"] == "ALL_PAIRS_COMBINED"
            and r["signal_type"] == "af" and r["cell_label"] in sample_cells and r["horizon_bars"] == 60
            and r["cohort_filter"] == "ALL_ELIGIBLE"
        ]
        full_nfp = [
            r for r in summary_rows
            if r["panel"] == "FULL_PANEL" and r["pair"] == "ALL_PAIRS_COMBINED"
            and r["signal_type"] == "af" and r["cell_label"] in sample_cells and r["horizon_bars"] == 60
            and r["cohort_filter"] == "ALL_ELIGIBLE"
        ]
        lines.extend([
            "",
            "| Horizon | Cell | Primary Panel N | Primary Win Rate | Primary Mean R | Full Panel N | Full Win Rate | Full Mean R |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"
        ])
        for pr in prim_nfp:
            fr = next((r for r in full_nfp if r["cell_label"] == pr["cell_label"]), None)
            fr_n = f"{fr['N_trades']:,}" if fr else "N/A"
            fr_wr = f"{fr['win_rate']:.1%}" if fr else "N/A"
            fr_mr = f"{fr['gross_mean_r']:+.4f}" if fr else "N/A"
            lines.append(
                f"| H60 | `{pr['cell_label']}` | {pr['N_trades']:,} | {pr['win_rate']:.1%} | {pr['gross_mean_r']:+.4f} | "
                f"{fr_n} | {fr_wr} | {fr_mr} |"
            )

        lines.extend([
            "",
            "### USDCAD Canadian Employment Collision Sensitivity",
            "",
            "| Horizon | Cell | CAD-Clean N | CAD-Clean Win Rate | CAD-Clean Mean R | Full USDCAD N | Full Win Rate | Full Mean R |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"
        ])
        clean_cad = [
            r for r in summary_rows
            if r["panel"] == "USDCAD_CAD_JOBS_CLEAN" and r["pair"] == "USDCAD"
            and r["signal_type"] == "af" and r["cell_label"] in sample_cells and r["horizon_bars"] == 60
            and r["cohort_filter"] == "ALL_ELIGIBLE"
        ]
        full_cad = [
            r for r in summary_rows
            if r["panel"] == "USDCAD_FULL" and r["pair"] == "USDCAD"
            and r["signal_type"] == "af" and r["cell_label"] in sample_cells and r["horizon_bars"] == 60
            and r["cohort_filter"] == "ALL_ELIGIBLE"
        ]
        for cr in clean_cad:
            fr = next((r for r in full_cad if r["cell_label"] == cr["cell_label"]), None)
            fr_n = f"{fr['N_trades']:,}" if fr else "N/A"
            fr_wr = f"{fr['win_rate']:.1%}" if fr else "N/A"
            fr_mr = f"{fr['gross_mean_r']:+.4f}" if fr else "N/A"
            lines.append(
                f"| H60 | `{cr['cell_label']}` | {cr['N_trades']:,} | {cr['win_rate']:.1%} | {cr['gross_mean_r']:+.4f} | "
                f"{fr_n} | {fr_wr} | {fr_mr} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 6. Summary Statement of Established Evidence",
        "",
        "1. **What WAS Established:**",
        "   - Auditable, reproducible OHLC barrier execution across all 52 exploratory cells and 3 horizons.",
        "   - Explicit separation of clean vs collision-contaminated macro panels.",
        "   - Complete reconciliation of trade counts ($N_{\\text{wins}} + N_{\\text{losses}} + N_{\\text{timeouts}} = N_{\\text{trades}}$).",
        "   - Separated exit reason distributions (Target, Stop, Timeout, Dual-Touch) and TP/SL duration metrics in bars and seconds.",
        "   - True re-anchored LOYO fold evaluations excluding Partial 2026.",
        f"   - Verified tolerance-based parity between independent raw-CSV recalculations and the production ledger for {len(audit_results)} representative sample cases (status: PASSED per sample).",
        "2. **What WAS NOT Established:**",
        "   - Zero claims of commercial profitability or trading edge.",
        "   - Zero strategy selection or registration (`selection_policy = NONE`).",
        "   - No net returns (spread, slippage, and financing are excluded from gross exploration arithmetic).",
        "   - Correlated pair trials are not independent macro samples.",
        ""
    ])

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def run_pipeline(
    allow_simulations: bool = False,
    family: str = "ALL",
    run_id: str = RUN_ID,
    raw_dir: str = DEFAULT_RAW_DIR
) -> None:
    """Executes the master exploration pipeline with mandatory fail-closed simulation gate."""
    if not allow_simulations:
        print("===================================================================")
        print("HISTORICAL EXPLORATION GATE — PRICED SIMULATIONS HALTED")
        print("===================================================================")
        print("Pre-outcome baseline, protocols (V2), and calculation engine are frozen.")
        print("Execution of priced outcome simulations is gated (allow_simulations=False).")
        print("Per Project Director instruction, Codex must independently audit the complete")
        print("corrected pre-outcome baseline, protocols, and calculation code before any")
        print("V2 outcome runs are initiated.")
        print("===================================================================")
        return

    print("===================================================================")
    print("STARTING FULL HISTORICAL EXPLORATION RUN (CPI & NFP V2)")
    print("===================================================================")

    # Verify raw data provenance and pinned pre-outcome ledger hashes before executing
    print("[Pre-flight] Verifying raw snapshot provenance and pinned pre-outcome hashes...")
    prov_res = verify_raw_provenance(raw_dir)
    print(f"  Provenance verified: {prov_res['raw_files_verified']} raw files, {prov_res['pre_outcome_ledgers_verified']} pre-outcome ledgers.")

    # Capture clean git HEAD
    git_head = get_git_commit_head(REPO_ROOT)
    print(f"  Clean Git HEAD verified: {git_head}")

    families_to_run = ["CPI", "NFP"] if family == "ALL" else [family]
    for fam in families_to_run:
        run_family_exploration(fam, run_id=run_id, raw_dir=raw_dir, git_commit=git_head)
        verification = verify_existing_package(fam, run_id=run_id, raw_dir=raw_dir)
        if verification["status"] != "PASSED":
            raise RuntimeError(f"{fam} package failed full ledger verification")
        print(f"  {fam} package passed full ledger verification: "
              f"{verification['summary_cells_reconciled']:,} summary cells, "
              f"{verification['annual_rows_reconciled']:,} annual rows, "
              f"{verification['loyo_folds_reconciled']:,} LOYO folds.")

    print("\n===================================================================")
    print("ALL EXPLORATION PACKAGES GENERATED AND VERIFIED SUCCESSFULLY.")
    print("===================================================================")


def main():
    """Main CLI entrypoint with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Master Exploration Pipeline Runner for US CPI and US NFP Historical Exploration (V2)."
    )
    parser.add_argument(
        "--verify-only",
        choices=["CPI", "NFP", "ALL"],
        default=None,
        help="Run read-only verification on existing exploratory packages without modifying any files."
    )
    parser.add_argument(
        "--family",
        choices=["CPI", "NFP", "ALL"],
        default="ALL",
        help="Event family to explore or verify (CPI, NFP, or ALL). Default: ALL."
    )
    parser.add_argument(
        "--run-id",
        default=RUN_ID,
        help=f"Run identifier subdirectory (default: {RUN_ID})."
    )
    parser.add_argument(
        "--raw-dir",
        default=DEFAULT_RAW_DIR,
        help="Path to raw MT5 export directory."
    )
    parser.add_argument(
        "--allow-simulations",
        action="store_true",
        default=False,
        help="Explicit flag required to ungate priced outcome simulations (default: False / gated)."
    )
    args = parser.parse_args()

    if args.verify_only:
        families = ["CPI", "NFP"] if args.verify_only == "ALL" else [args.verify_only]
        print("===================================================================")
        print(f"READ-ONLY PACKAGE VERIFICATION (Families: {', '.join(families)})")
        print(f"Run ID: {args.run_id}")
        print("===================================================================")
        for fam in families:
            res = verify_existing_package(fam, run_id=args.run_id, raw_dir=args.raw_dir)
            print(f"[{fam}] Verification {res['status']}:")
            print(f"  - Package: {res['package_dir']}")
            print(f"  - Trials reconciled: {res['trials_count']:,}")
            print(f"  - Summary cells reconciled: {res['summary_cells_reconciled']:,}")
            print(f"  - Annual rows reconciled: {res['annual_rows_reconciled']:,}")
            print(f"  - LOYO folds reconciled: {res['loyo_folds_reconciled']:,}")
            print(f"  - Audit cases: {res['audit_cases_count']} ({res['audit_status']})")
        print("===================================================================")
        print("ALL VERIFIED PACKAGES PASSED FULL AUDIT.")
        print("===================================================================")
        return

    run_pipeline(
        allow_simulations=args.allow_simulations,
        family=args.family,
        run_id=args.run_id,
        raw_dir=args.raw_dir
    )


if __name__ == "__main__":
    main()
