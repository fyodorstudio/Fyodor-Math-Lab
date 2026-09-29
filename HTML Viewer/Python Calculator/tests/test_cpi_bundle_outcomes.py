"""Unit and Audit Tests for USD CPI Same-Time Bundle Outcome Engine.

Test suite verifying:
1. Input hashes (fail-closed check)
2. Five independent raw-candle hand-recomputations
3. Generated outcome artifact existence and manifest checksum integrity
4. Candidate trade denominators and eligibility waterfalls
5. Full summary grid mathematical reconciliation across all 29,952 rows
6. Dual-touch ambiguity resolution boundary (STOP_FIRST vs TARGET_FIRST)
7. Opening gap boundary behavior
8. Timeout bar-close pricing boundary
9. Showcase Case 2 dual-touch on Bar 2 in trial ledger
"""

import os
import sys
import csv
import json
import math
import hashlib
import unittest
from collections import defaultdict

CALC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if CALC_DIR not in sys.path:
    sys.path.insert(0, CALC_DIR)

from data_loader import load_candles, DEFAULT_RAW_DIR
from protocol_specs import ACTIVE_USD_PAIRS
from outcome_engine import simulate_single_trade, get_pip_size, ALL_GRID_CELLS, CandleBar
from audit_raw_csv_ohlc import run_all_five_showcase_audits, verify_audit_against_trial_ledger
from run_cpi_bundle_outcomes import (
    REPO_ROOT,
    OUTCOMES_DIR,
    PRE_OUTCOME_DIR,
    EXPECTED_RAW_INPUT_HASHES,
    compute_sha256,
)


class TestCpiBundleOutcomes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manifest_path = os.path.join(OUTCOMES_DIR, "manifest.json")
        cls.has_artifacts = os.path.exists(cls.manifest_path)
        if cls.has_artifacts:
            with open(cls.manifest_path, "r", encoding="utf-8") as f:
                cls.manifest = json.load(f)

    def test_01_raw_input_hashes(self):
        """Verifies all 15 raw inputs and pre-outcome ledgers match pinned hashes."""
        for path, expected in EXPECTED_RAW_INPUT_HASHES.items():
            self.assertTrue(os.path.exists(path), f"Missing file: {path}")
            actual = compute_sha256(path)
            self.assertEqual(actual, expected, f"Hash mismatch for {path}")

    def test_02_independent_raw_audit_to_production_ledger(self):
        """Directly compares independently derived raw-candle metrics against production trial ledger rows."""
        self.assertTrue(self.has_artifacts)
        trial_path = os.path.join(OUTCOMES_DIR, "trial_ledger.csv")
        self.assertTrue(os.path.exists(trial_path))
        results = verify_audit_against_trial_ledger(trial_path, DEFAULT_RAW_DIR)
        self.assertEqual(len(results), 6)
        for res in results:
            self.assertEqual(res["status"], "SOURCE_TO_LEDGER_MATCH_VERIFIED", f"Case {res['label']} failed ledger match")

    def test_03_artifact_manifest_integrity(self):
        """Verifies all generated outcome files exist and their SHA-256 matches manifest.json."""
        self.assertTrue(self.has_artifacts, "Manifest does not exist")
        artifacts = self.manifest["generated_artifacts"]

        for fname, info in artifacts.items():
            fpath = os.path.join(OUTCOMES_DIR, fname)
            self.assertTrue(os.path.exists(fpath), f"Artifact missing: {fpath}")
            self.assertEqual(os.path.getsize(fpath), info["size_bytes"], f"Size mismatch for {fname}")
            actual_sha = compute_sha256(fpath)
            self.assertEqual(actual_sha, info["sha256"], f"SHA256 mismatch for {fname}")

    def test_04_trial_ledger_denominators(self):
        """Verifies trial ledger candidate trade denominators and row counts."""
        self.assertTrue(self.has_artifacts)
        trial_path = os.path.join(OUTCOMES_DIR, "trial_ledger.csv")
        self.assertTrue(os.path.exists(trial_path))

        comp_counts = {}
        with open(trial_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Count for H60 cell 1:1 to get unique trade count per comparison
                if r["horizon_bars"] == "60" and r["cell_label"] == "1:1":
                    cid = r["comparison_id"]
                    comp_counts[cid] = comp_counts.get(cid, 0) + 1

        self.assertEqual(comp_counts.get("CANDIDATE_1_HEADLINE_MM"), 859)
        self.assertEqual(comp_counts.get("CANDIDATE_2_CORE_MM_LED"), 656)
        self.assertEqual(comp_counts.get("CANDIDATE_3_CONCORDANT_MM"), 411)
        self.assertEqual(comp_counts.get("CANDIDATE_4_CONFLICT_FILTERED_HEADLINE"), 663)
        self.assertEqual(comp_counts.get("CONFLICT_SUBSTUDY_A_HEADLINE"), 196)
        self.assertEqual(comp_counts.get("CONFLICT_SUBSTUDY_B_CORE"), 196)

        # Total trials: (859 + 656 + 411 + 663 + 196 + 196) * 3 horizons * 52 cells = 2,981 * 156 = 465,036
        total_unique_trades = 859 + 656 + 411 + 663 + 196 + 196
        self.assertEqual(total_unique_trades, 2981)
        self.assertEqual(total_unique_trades * 3 * 52, 465036)

    def test_05_internal_summary_arithmetic_identities(self):
        """Verifies full summary grid (all 29,952 rows) internal mathematical partition and dual-touch identities."""
        self.assertTrue(self.has_artifacts)
        summary_path = os.path.join(OUTCOMES_DIR, "summary_grid_results.csv")
        self.assertTrue(os.path.exists(summary_path))

        with open(summary_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        # Expected total rows: 2 panels * 8 pairs * 6 comparisons * 2 cohort filters * 3 horizons * 52 cells = 29,952
        self.assertEqual(len(rows), 29952)

        # Full reconciliation across all 29,952 rows (zero sampling truncation)
        for r in rows:
            nt = int(r["N_trades"])
            nw = int(r["N_wins"])
            nl = int(r["N_losses"])
            nto = int(r["N_timeouts"])
            ndt = int(r["N_dual_touch"])

            # Stop-First partition identity
            self.assertEqual(nt, nw + nl + nto, f"SF Trade count mismatch in {r['cell_label']}")

            # Target-First partition identity
            tf_nw = int(r["tf_N_wins"])
            tf_nl = int(r["tf_N_losses"])
            tf_nto = int(r["tf_N_timeouts"])
            self.assertEqual(nt, tf_nw + tf_nl + tf_nto, f"TF Trade count mismatch in {r['cell_label']}")

            # Dual-touch swap identity: dual touch converts loss to win under Target-First
            self.assertEqual(tf_nw, nw + ndt, f"TF Win count mismatch in {r['cell_label']}")
            self.assertEqual(tf_nl, nl - ndt, f"TF Loss count mismatch in {r['cell_label']}")
            self.assertEqual(tf_nto, nto, f"TF Timeout count mismatch in {r['cell_label']}")

            # Delta identities
            delta_mean = float(r["delta_tf_sf_mean_r"])
            tf_mean = float(r["tf_gross_mean_r"])
            sf_mean = float(r["gross_mean_r"])
            self.assertAlmostEqual(delta_mean, tf_mean - sf_mean, places=5)

            delta_sum = float(r["delta_tf_sf_sum_r"])
            tf_sum = float(r["tf_gross_sum_r"])
            sf_sum = float(r["gross_sum_r"])
            self.assertAlmostEqual(delta_sum, tf_sum - sf_sum, places=3)

    def test_06_dual_touch_boundary(self):
        """Synthetic test: verifies STOP_FIRST vs TARGET_FIRST on identical dual-touch bar."""
        bars = [
            CandleBar(
                timestamp=1000, open=1.1000, high=1.1050, low=1.0950, close=1.1000,
                tick_volume=10, spread=1, real_volume=0, symbol="EURUSD",
                time_server_text="2026.01.01 00:00:00", complete_at_export=True
            )
        ]
        # Long, entry=1.1000, atr=0.0020, stop_atr=1.0 (stop=1.0980), target_atr=1.0 (target=1.1020)
        # Bar high is 1.1050 (>=1.1020), low is 1.0950 (<=1.0980) -> dual touch!
        out_sf = simulate_single_trade(1.1000, 1, 0.0020, 1.0, 1.0, bars, 0.0001, "STOP_FIRST")
        out_tf = simulate_single_trade(1.1000, 1, 0.0020, 1.0, 1.0, bars, 0.0001, "TARGET_FIRST")

        self.assertTrue(out_sf.dual_touch)
        self.assertTrue(out_tf.dual_touch)
        self.assertEqual(out_sf.exit_reason, "STOP")
        self.assertEqual(out_sf.gross_r, -1.0)
        self.assertEqual(out_tf.exit_reason, "TARGET")
        self.assertEqual(out_tf.gross_r, 1.0)

    def test_07_opening_gap_boundary(self):
        """Synthetic test: verifies opening gap detection and nominal vs executable R."""
        bars = [
            # Entry candle
            CandleBar(
                timestamp=1000, open=1.1000, high=1.1010, low=1.0990, close=1.1000,
                tick_volume=10, spread=1, real_volume=0, symbol="EURUSD",
                time_server_text="2026.01.01 00:00:00", complete_at_export=True
            ),
            # Gap bar: opens below stop price (stop price = 1.1000 - 0.0020 = 1.0980)
            CandleBar(
                timestamp=4600, open=1.0950, high=1.0960, low=1.0940, close=1.0955,
                tick_volume=10, spread=1, real_volume=0, symbol="EURUSD",
                time_server_text="2026.01.01 01:00:00", complete_at_export=True
            )
        ]
        out = simulate_single_trade(1.1000, 1, 0.0020, 1.0, 1.0, bars, 0.0001, "STOP_FIRST")
        self.assertTrue(out.is_opening_gap)
        self.assertEqual(out.exit_reason, "STOP_GAP")
        self.assertEqual(out.exit_price, 1.0980)  # Nominal stop
        self.assertEqual(out.gross_r, -1.0)  # Nominal R
        self.assertEqual(out.gap_open_price, 1.0950)  # Gap execution
        self.assertAlmostEqual(out.gap_executable_pips, -50.0, places=5)  # (1.0950 - 1.1000) / 0.0001
        self.assertAlmostEqual(out.gap_executable_gross_r, -2.5, places=5)  # (1.0950 - 1.1000) / 0.0020

    def test_08_timeout_boundary(self):
        """Synthetic test: verifies timeout exit price matches final bar close."""
        bars = [
            CandleBar(
                timestamp=1000, open=1.1000, high=1.1010, low=1.0990, close=1.1005,
                tick_volume=10, spread=1, real_volume=0, symbol="EURUSD",
                time_server_text="2026.01.01 00:00:00", complete_at_export=True
            ),
            CandleBar(
                timestamp=4600, open=1.1005, high=1.1015, low=1.0995, close=1.1010,
                tick_volume=10, spread=1, real_volume=0, symbol="EURUSD",
                time_server_text="2026.01.01 01:00:00", complete_at_export=True
            )
        ]
        # ATR=0.0100, Stop ATR=2.0 (stop=1.0800), Target ATR=2.0 (target=1.1200) -> neither touched
        out = simulate_single_trade(1.1000, 1, 0.0100, 2.0, 2.0, bars, 0.0001, "STOP_FIRST")
        self.assertEqual(out.exit_reason, "TIMEOUT")
        self.assertEqual(out.exit_price, 1.1010)
        self.assertEqual(out.bars_to_exit, 2)
        # Gross R = (1.1010 - 1.1000) / 0.0200 = 0.0010 / 0.0200 = +0.05R
        self.assertAlmostEqual(out.gross_r, 0.05, places=6)

    def test_09_case_2_dual_touch_eurusd(self):
        """Verifies Case 2 (2024.06.12 EURUSD H60 1:2) dual touch on Bar 2 in trial ledger."""
        self.assertTrue(self.has_artifacts)
        trial_path = os.path.join(OUTCOMES_DIR, "trial_ledger.csv")
        self.assertTrue(os.path.exists(trial_path))

        target_row = None
        with open(trial_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if (
                    r["pair"] == "EURUSD"
                    and r["timestamp_server_text"].startswith("2024.06.12")
                    and r["horizon_bars"] == "60"
                    and r["cell_label"] == "1:2"
                    and r["comparison_id"] == "CANDIDATE_1_HEADLINE_MM"
                ):
                    target_row = r
                    break

        self.assertIsNotNone(target_row, "Target trial row not found in trial ledger")
        self.assertEqual(target_row["dual_touch"], "True")
        self.assertEqual(target_row["exit_bar_idx"], "2")
        self.assertEqual(target_row["exit_reason"], "STOP")
        self.assertAlmostEqual(float(target_row["gross_r"]), -1.0, places=6)
        self.assertEqual(target_row["target_first_exit_reason"], "TARGET")
        self.assertAlmostEqual(float(target_row["target_first_gross_r"]), 2.0, places=6)

    def test_10_true_trial_ledger_to_summary_reconciliation(self):
        """Independently groups trial_ledger.csv and verifies N, wins, losses, timeouts, dual touches, SF sum R, and TF sum R against all 29,952 summary rows."""
        self.assertTrue(self.has_artifacts)
        trial_path = os.path.join(OUTCOMES_DIR, "trial_ledger.csv")
        summary_path = os.path.join(OUTCOMES_DIR, "summary_grid_results.csv")
        self.assertTrue(os.path.exists(trial_path))
        self.assertTrue(os.path.exists(summary_path))

        # Independently aggregate trial rows into cell buckets
        agg = defaultdict(lambda: {
            "n": 0,
            "sf_wins": 0,
            "sf_losses": 0,
            "sf_timeouts": 0,
            "sf_dual_touch": 0,
            "sf_sum_r": 0.0,
            "tf_wins": 0,
            "tf_losses": 0,
            "tf_timeouts": 0,
            "tf_sum_r": 0.0,
        })

        with open(trial_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cid = r["comparison_id"]
                h = int(r["horizon_bars"])
                cell_lbl = r["cell_label"]
                pair = r["pair"]
                claims = (r["coincident_claims_collision"].strip().lower() in ("true", "1"))
                sf_win = (r["is_win"].strip().lower() in ("true", "1"))
                sf_loss = (r["is_loss"].strip().lower() in ("true", "1"))
                sf_timeout = (r["is_timeout"].strip().lower() in ("true", "1"))
                dt = (r["dual_touch"].strip().lower() in ("true", "1"))
                sf_r = float(r["gross_r"])
                tf_reason = r["target_first_exit_reason"]
                tf_win = (tf_reason in ("TARGET", "TARGET_GAP"))
                tf_loss = (tf_reason in ("STOP", "STOP_GAP"))
                tf_timeout = (tf_reason == "TIMEOUT")
                tf_r = float(r["target_first_gross_r"])

                panels = ["FULL_PANEL"]
                if not claims:
                    panels.append("JOBLESS_CLAIMS_CLEAN")

                pair_keys = [pair, "ALL_PAIRS_COMBINED"]
                cohorts = ["ALL_ELIGIBLE", "COMMON_H240"]

                for pan in panels:
                    for pr in pair_keys:
                        for ch in cohorts:
                            acc = agg[(pan, pr, cid, ch, h, cell_lbl)]
                            acc["n"] += 1
                            if sf_win:
                                acc["sf_wins"] += 1
                            if sf_loss:
                                acc["sf_losses"] += 1
                            if sf_timeout:
                                acc["sf_timeouts"] += 1
                            if dt:
                                acc["sf_dual_touch"] += 1
                            acc["sf_sum_r"] += sf_r
                            if tf_win:
                                acc["tf_wins"] += 1
                            if tf_loss:
                                acc["tf_losses"] += 1
                            if tf_timeout:
                                acc["tf_timeouts"] += 1
                            acc["tf_sum_r"] += tf_r

        with open(summary_path, "r", encoding="utf-8") as f:
            summary_rows = list(csv.DictReader(f))

        self.assertEqual(len(summary_rows), 29952)

        for s in summary_rows:
            key = (
                s["panel"],
                s["pair"],
                s["comparison_id"],
                s["cohort_filter"],
                int(s["horizon_bars"]),
                s["cell_label"],
            )
            acc = agg[key]
            self.assertEqual(int(s["N_trades"]), acc["n"], f"N mismatch for {key}")
            self.assertEqual(int(s["N_wins"]), acc["sf_wins"], f"SF Wins mismatch for {key}")
            self.assertEqual(int(s["N_losses"]), acc["sf_losses"], f"SF Losses mismatch for {key}")
            self.assertEqual(int(s["N_timeouts"]), acc["sf_timeouts"], f"SF Timeouts mismatch for {key}")
            self.assertEqual(int(s["N_dual_touch"]), acc["sf_dual_touch"], f"Dual touch mismatch for {key}")
            self.assertAlmostEqual(float(s["gross_sum_r"]), acc["sf_sum_r"], places=3, msg=f"SF Sum R mismatch for {key}")
            self.assertEqual(int(s["tf_N_wins"]), acc["tf_wins"], f"TF Wins mismatch for {key}")
            self.assertEqual(int(s["tf_N_losses"]), acc["tf_losses"], f"TF Losses mismatch for {key}")
            self.assertEqual(int(s["tf_N_timeouts"]), acc["tf_timeouts"], f"TF Timeouts mismatch for {key}")
            self.assertAlmostEqual(float(s["tf_gross_sum_r"]), acc["tf_sum_r"], places=3, msg=f"TF Sum R mismatch for {key}")

    def test_11_v2_to_v3_comparison_artifact(self):
        """Verifies machine-readable v2_to_v3_comparison.json metrics and invariants."""
        self.assertTrue(self.has_artifacts)
        comp_path = os.path.join(OUTCOMES_DIR, "v2_to_v3_comparison.json")
        self.assertTrue(os.path.exists(comp_path))

        with open(comp_path, "r", encoding="utf-8") as f:
            comp = json.load(f)

        tm = comp["trial_level_metrics"]
        sm = comp["summary_level_metrics"]

        # Pre-release ATR was converted from .6f to repr across all 465,036 trials
        self.assertEqual(tm["changed_atr_inputs"], 465036)
        # Due to unrounded ATR precision, exactly 246 borderline trials flipped classification
        self.assertEqual(tm["changed_stop_target_classifications"], 246)
        # Exactly 858 exit bars shifted timing
        self.assertEqual(tm["changed_exit_bars"], 858)
        self.assertEqual(tm["changed_stop_first_r_values"], 5008)
        self.assertEqual(tm["changed_target_first_r_values"], 5038)
        # Invariant: 0 trade count changes across all 29,952 summary cells
        self.assertEqual(sm["changed_trade_counts"], 0)
        self.assertEqual(sm["changed_classification_counts"], 1856)
        self.assertEqual(sm["changed_summary_cells"], 5642)


if __name__ == "__main__":
    unittest.main()
