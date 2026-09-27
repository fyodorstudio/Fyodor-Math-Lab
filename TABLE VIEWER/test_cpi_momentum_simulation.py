"""
Unit Tests for CPI Momentum Historical Simulation (A-P Momentum, H60 Expiry)
Location: TABLE VIEWER/test_cpi_momentum_simulation.py

Independent Synthetic Fixtures & Audit Verifications:
1. Pinned input SHA-256 cryptographic provenance.
2. Complete 277-episode decision ledger reconciliation (cpi_momentum_decision_ledger.csv).
3. Baseline ledger hash immutability (verifies baseline A-F files are byte-for-byte untouched).
4. Synthetic tests for missing, equal, and zero A/P values.
5. Synthetic test for absent forecast (F) still eligible under A-P momentum.
6. Synthetic test for revised_previous disagreement and audit retention without substitution.
7. Synthetic test for Retail Sales collision exclusion vs non-Retail coincident releases.
8. Synthetic test for exact-hour entry requirement and missing entry bar explicit error.
9. Synthetic test for incomplete H60 path explicit error.
10. Synthetic test for strictly-before pre-release ATR14 lookback.
11. Synthetic test for stop/target ambiguity (STOP_FIRST vs TARGET_FIRST).
12. Synthetic test for gap fills (adverse stop gap at worse open, favorable target gap capped).
13. Synthetic test for H60 timeout labeling (exits at Bar 60 with TIMEOUT_H60).
14. Real-world independent spot-checks against pinned data (disagreement episode, ambiguous episode, latest exit, unforecasted episode, best trade).
15. Path continuity audit (zero unexpected missing-data gaps, weekend closures accounted).
"""

import unittest
import os
import csv
import json
import hashlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cpi_momentum_simulation import (
    CALENDAR_PATH,
    CANDLES_PATH,
    DEFAULT_OUTPUT_DIR,
    BASELINE_SETUP_DIR,
    load_candles,
    load_calendar_by_ts,
    audit_calendar_integrity,
    reconcile_and_identify_candidates_ap,
    compute_atr14,
    simulate_trade_path,
    is_weekend_closure,
    audit_path_continuity,
    verify_pinned_inputs_or_fail,
    run_full_momentum_simulation_suite,
    PIP_SIZE
)

EXPECTED_CALENDAR_SHA256 = "76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e"
EXPECTED_CANDLES_SHA256 = "893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5"

EXPECTED_BASELINE_DECISION_SHA256 = "bfad2993c8bd42cc12ce7435115eccc00b42f9650efbc8a784410df6179d9f07"
EXPECTED_BASELINE_TRADE_CSV_SHA256 = "1832ea88849e9c8e89fd99e4cb165ac423d3d94bb43991d9c2a6870b5cf03b53"
EXPECTED_BASELINE_TRADE_JSON_SHA256 = "a43f483547d424571f240fd7b9cb77c22200403ec2c7047909d423e7a710a65f"


class TestCpiMomentumSimulation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sim_results = run_full_momentum_simulation_suite()
        cls.candles, cls.ts_to_idx = load_candles(CANDLES_PATH)
        cls.rows_by_ts, total_raw_count = load_calendar_by_ts(CALENDAR_PATH)
        cls.candidates, cls.recon = reconcile_and_identify_candidates_ap(cls.rows_by_ts, total_raw_count)

    def test_01_pinned_input_sha256_digests(self):
        """Verifies byte-for-byte SHA-256 cryptographic provenance of pinned inputs."""
        with open(CALENDAR_PATH, "rb") as f:
            cal_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(cal_hash.lower(), EXPECTED_CALENDAR_SHA256.lower())

        with open(CANDLES_PATH, "rb") as f:
            candles_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(candles_hash.lower(), EXPECTED_CANDLES_SHA256.lower())

    def test_02_baseline_ledger_hash_invariance(self):
        """
        Verifies that running the new momentum trial left the baseline A-F ledgers
        byte-for-byte untouched and identical to their expected SHA-256 hashes.
        """
        b_dec = os.path.join(BASELINE_SETUP_DIR, "cpi_decision_ledger.csv")
        b_tr_csv = os.path.join(BASELINE_SETUP_DIR, "cpi_trade_ledger.csv")
        b_tr_json = os.path.join(BASELINE_SETUP_DIR, "cpi_trade_ledger.json")

        self.assertTrue(os.path.exists(b_dec), "Baseline decision ledger missing")
        self.assertTrue(os.path.exists(b_tr_csv), "Baseline trade CSV missing")
        self.assertTrue(os.path.exists(b_tr_json), "Baseline trade JSON missing")

        with open(b_dec, "rb") as f:
            h_dec = hashlib.sha256(f.read()).hexdigest().lower()
        with open(b_tr_csv, "rb") as f:
            h_tr_csv = hashlib.sha256(f.read()).hexdigest().lower()
        with open(b_tr_json, "rb") as f:
            h_tr_json = hashlib.sha256(f.read()).hexdigest().lower()

        self.assertEqual(h_dec, EXPECTED_BASELINE_DECISION_SHA256.lower())
        self.assertEqual(h_tr_csv, EXPECTED_BASELINE_TRADE_CSV_SHA256.lower())
        self.assertEqual(h_tr_json, EXPECTED_BASELINE_TRADE_JSON_SHA256.lower())

    def test_03_calendar_data_integrity(self):
        """Verifies zero duplicate releases, zero unit mismatches, and raw-scaled consistency."""
        integrity = audit_calendar_integrity(self.rows_by_ts)
        self.assertTrue(integrity["integrity_passed"])
        self.assertEqual(len(integrity["duplicate_cpi_records"]), 0)
        self.assertEqual(len(integrity["raw_scaled_mismatches"]), 0)
        self.assertEqual(len(integrity["unit_mismatches"]), 0)

    def test_04_decision_ledger_reconciliation(self):
        """
        Verifies exact 277-episode decision ledger reconciliation:
        138 PCE-only, 12 Retail collisions, 0 missing A/P, 72 mixed/equal, 55 candidate trades.
        """
        ledger_path = os.path.join(DEFAULT_OUTPUT_DIR, "cpi_momentum_decision_ledger.csv")
        self.assertTrue(os.path.exists(ledger_path))

        with open(ledger_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 277)
        counts = {}
        for r in rows:
            disp = r["disposition"]
            counts[disp] = counts.get(disp, 0) + 1

        self.assertEqual(counts.get("PCE_ONLY", 0), 138)
        self.assertEqual(counts.get("SHARED_COLLISION", 0), 12)
        self.assertEqual(counts.get("MISSING_AP", 0), 0)
        self.assertEqual(counts.get("MIXED_OR_EQUAL", 0), 72)
        self.assertEqual(counts.get("CANDIDATE_TRADE", 0), 55)
        self.assertEqual(sum(counts.values()), 277)

    def test_05_trade_ledger_counts_and_metrics(self):
        """Verifies trade counts, win rate, gross R, and direction splits on primary trial."""
        trades = self.sim_results["trials"]["primary_1.5x_conservative"]["trades"]
        metrics = self.sim_results["trials"]["primary_1.5x_conservative"]["metrics"]

        self.assertEqual(len(trades), 55)
        self.assertEqual(metrics["total_trades"], 55)
        self.assertEqual(metrics["wins"], 23)
        self.assertEqual(metrics["losses"], 32)
        self.assertEqual(metrics["timeouts"], 0)
        self.assertAlmostEqual(metrics["win_rate_pct"], 41.818, places=2)
        self.assertAlmostEqual(metrics["total_gross_r"], 2.50, places=2)
        self.assertEqual(metrics["ambiguous_trades"], 4)

        # Direction splits
        self.assertEqual(metrics["direction_splits"]["short_count"], 26)
        self.assertEqual(metrics["direction_splits"]["long_count"], 29)
        self.assertAlmostEqual(metrics["direction_splits"]["short_gross_r"], 4.00, places=2)
        self.assertAlmostEqual(metrics["direction_splits"]["long_gross_r"], -1.50, places=2)

    def test_06_synthetic_missing_equal_zero_ap(self):
        """
        Synthetic fixture testing signal logic:
        - Missing A or P -> NO TRADE (MISSING_AP)
        - Zero is a valid numeric value, NOT missing (e.g. A=0.0, P=-0.1 is valid positive momentum)
        - Equal A and P (A - P == 0) -> NO TRADE (MIXED_OR_EQUAL)
        - Mixed signs -> NO TRADE (MIXED_OR_EQUAL)
        """
        # 1. Zero value handling
        mock_rows_zero = {
            1000000: [
                {"event_id": "840030005", "actual": "0.0", "previous": "-0.1", "forecast": "0.1", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840030006", "actual": "0.2", "previous": "0.1", "forecast": "0.2", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"}
            ]
        }
        cands, recon = reconcile_and_identify_candidates_ap(mock_rows_zero, total_raw_records=2)
        self.assertEqual(len(cands), 1)
        self.assertEqual(cands[0]["direction"], "SHORT")  # Both A > P (0.0 > -0.1 and 0.2 > 0.1)

        # 2. Equality handling (A == P)
        mock_rows_equal = {
            1000000: [
                {"event_id": "840030005", "actual": "0.2", "previous": "0.2", "forecast": "", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840030006", "actual": "0.3", "previous": "0.1", "forecast": "", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"}
            ]
        }
        cands, recon = reconcile_and_identify_candidates_ap(mock_rows_equal, total_raw_records=2)
        self.assertEqual(len(cands), 0)
        self.assertEqual(recon["mixed_or_equal_no_trade"], 1)

        # 3. Missing string handling
        mock_rows_missing = {
            1000000: [
                {"event_id": "840030005", "actual": "", "previous": "0.2", "forecast": "", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840030006", "actual": "0.3", "previous": "0.1", "forecast": "", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"}
            ]
        }
        cands, recon = reconcile_and_identify_candidates_ap(mock_rows_missing, total_raw_records=2)
        self.assertEqual(len(cands), 0)
        self.assertEqual(recon["cpi_missing_ap"], 1)

    def test_07_synthetic_absent_f_still_eligible(self):
        """
        Synthetic fixture verifying that when forecast (F) is completely empty,
        the episode remains 100% eligible under A-P momentum.
        """
        mock_rows = {
            1000000: [
                {"event_id": "840030005", "actual": "0.1", "previous": "0.3", "forecast": "", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840030006", "actual": "0.1", "previous": "0.2", "forecast": "", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"}
            ]
        }
        cands, recon = reconcile_and_identify_candidates_ap(mock_rows, total_raw_records=2)
        self.assertEqual(len(cands), 1)
        self.assertEqual(cands[0]["direction"], "LONG")  # Both A < P
        self.assertEqual(cands[0]["head_f"], "")
        self.assertEqual(cands[0]["core_f"], "")

    def test_08_synthetic_revised_previous_disagreement(self):
        """
        Synthetic fixture verifying:
        - revised_previous is audited and tracked.
        - Primary signal strictly uses original previous and does NOT substitute revised_previous.
        """
        # In this mock, original A-P gives SHORT (0.3 > 0.1 and 0.3 > 0.1)
        # But revised_previous gives NO TRADE (0.3 vs 0.4 = -0.1 and 0.3 vs 0.1 = +0.2 -> mixed)
        mock_rows = {
            1000000: [
                {"event_id": "840030005", "actual": "0.3", "previous": "0.1", "revised_previous": "0.4", "forecast": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840030006", "actual": "0.3", "previous": "0.1", "revised_previous": "0.1", "forecast": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"}
            ]
        }
        cands, recon = reconcile_and_identify_candidates_ap(mock_rows, total_raw_records=2)
        self.assertEqual(len(cands), 1)
        self.assertEqual(cands[0]["direction"], "SHORT")  # Primary signal preserved!
        self.assertEqual(recon["revised_previous_audit"]["sign_change_count"], 1)

    def test_09_synthetic_retail_collision_exclusion(self):
        """
        Synthetic fixture verifying that Retail Sales collision events (840020010, 840020011)
        are excluded, while other co-releases (e.g. 840140001 Jobless Claims) are preserved.
        """
        # 1. Retail Sales collision
        mock_collision = {
            1000000: [
                {"event_id": "840030005", "actual": "0.3", "previous": "0.1", "forecast": "0.1", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840030006", "actual": "0.3", "previous": "0.1", "forecast": "0.1", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840020010", "actual": "0.5", "previous": "0.2", "forecast": "0.3", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"}
            ]
        }
        cands, recon = reconcile_and_identify_candidates_ap(mock_collision, total_raw_records=3)
        self.assertEqual(len(cands), 0)
        self.assertEqual(recon["shared_retail_collisions"], 1)

        # 2. Co-release with Initial Jobless Claims (not excluded)
        mock_claims = {
            1000000: [
                {"event_id": "840030005", "actual": "0.3", "previous": "0.1", "forecast": "0.1", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "event_name": "CPI m/m", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840030006", "actual": "0.3", "previous": "0.1", "forecast": "0.1", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "event_name": "Core CPI m/m", "unit": "CALENDAR_UNIT_PERCENT", "multiplier": "CALENDAR_MULTIPLIER_NONE"},
                {"event_id": "840140001", "actual": "220", "previous": "225", "forecast": "222", "revised_previous": "", "timestamp_server_text": "mock_ts", "revision": "0", "event_name": "Initial Jobless Claims", "unit": "CALENDAR_UNIT_NONE", "multiplier": "CALENDAR_MULTIPLIER_THOUSANDS"}
            ]
        }
        cands, recon = reconcile_and_identify_candidates_ap(mock_claims, total_raw_records=3)
        self.assertEqual(len(cands), 1)
        self.assertIn("840140001", cands[0]["co_releases"][0])

    def test_10_synthetic_exact_entry_and_missing_bar_error(self):
        """
        Synthetic fixture verifying entry occurs at ((ts // 3600) + 1) * 3600
        and raises ValueError if the intended entry candle is missing.
        """
        base_t = 1600000000 - (1600000000 % 3600)
        release_ts = base_t + 1800  # 15:30:00
        expected_entry_ts = base_t + 3600  # 16:00:00

        # Build 100 bars
        synth_candles = []
        ts_to_idx = {}
        for i in range(100):
            t = base_t - 20 * 3600 + i * 3600
            c = {
                "time": t, "open": 1.10000, "high": 1.10100, "low": 1.09900, "close": 1.10000,
                "time_server_text": f"synth_{i}"
            }
            synth_candles.append(c)
            ts_to_idx[t] = i

        cand = {
            "ts": release_ts, "dt_str": "mock_release", "direction": "SHORT",
            "head_a": 0.3, "head_p": 0.1, "head_rp": "", "head_diff": 0.2, "head_f": "",
            "core_a": 0.3, "core_p": 0.1, "core_rp": "", "core_diff": 0.2, "core_f": "",
            "co_releases": []
        }

        # Valid entry
        sim = simulate_trade_path(cand, synth_candles, ts_to_idx, max_bars=60)
        self.assertEqual(sim["entry_ts"], expected_entry_ts)

        # Missing entry bar in ts_to_idx must raise ValueError
        del ts_to_idx[expected_entry_ts]
        with self.assertRaises(ValueError):
            simulate_trade_path(cand, synth_candles, ts_to_idx, max_bars=60)

    def test_11_synthetic_incomplete_h60_path_error(self):
        """Verifies that an incomplete H60 path (< 60 bars) raises ValueError."""
        base_t = 1600000000 - (1600000000 % 3600)
        release_ts = base_t + 1800
        expected_entry_ts = base_t + 3600

        # Provide only 30 bars after entry
        synth_candles = []
        ts_to_idx = {}
        for i in range(45):
            t = base_t - 15 * 3600 + i * 3600
            c = {
                "time": t, "open": 1.10000, "high": 1.10100, "low": 1.09900, "close": 1.10000,
                "time_server_text": f"synth_{i}"
            }
            synth_candles.append(c)
            ts_to_idx[t] = i

        cand = {
            "ts": release_ts, "dt_str": "mock_release", "direction": "SHORT",
            "head_a": 0.3, "head_p": 0.1, "head_rp": "", "head_diff": 0.2, "head_f": "",
            "core_a": 0.3, "core_p": 0.1, "core_rp": "", "core_diff": 0.2, "core_f": "",
            "co_releases": []
        }
        with self.assertRaises(ValueError):
            simulate_trade_path(cand, synth_candles, ts_to_idx, max_bars=60)

    def test_12_synthetic_pre_release_atr14_strictly_before(self):
        """
        Verifies ATR14 calculation strictly excludes the release-containing bar
        under candle_time + 3600 < release_ts.
        """
        base_t = 1600000000 - (1600000000 % 3600)
        exact_hour_release = base_t + 16 * 3600

        synth_candles = []
        for i in range(25):
            t = base_t + i * 3600
            synth_candles.append({
                "time": t, "open": 1.10000, "high": 1.10100, "low": 1.10000, "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Inject 500-pip spike into Bar 15 (starts at 15:00, ends at 16:00)
        synth_candles[15]["high"] = 1.15000
        synth_candles[15]["low"] = 1.10000
        synth_candles[15]["close"] = 1.15000

        # Release at 16:00:00 must exclude Bar 15!
        atr = compute_atr14(synth_candles, exact_hour_release)
        self.assertAlmostEqual(atr, 0.00100, places=6)

    def test_13_synthetic_stop_target_ambiguity(self):
        """
        Synthetic fixture verifying ambiguous intrabar touch:
        - When high touches SL and low touches TP in same candle:
          * ambiguous_flag is set to True.
          * STOP_FIRST resolves to STOP.
          * TARGET_FIRST resolves to TARGET.
        """
        base_t = 1600000000 - (1600000000 % 3600)
        release_ts = base_t + 1800
        entry_ts = base_t + 3600

        synth_candles = []
        ts_to_idx = {}
        for i in range(100):
            t = base_t - 20 * 3600 + i * 3600
            # Normal bars with 10 pip TR
            c = {
                "time": t, "open": 1.10000, "high": 1.10100, "low": 1.10000, "close": 1.10050,
                "time_server_text": f"synth_{i}"
            }
            synth_candles.append(c)
            ts_to_idx[t] = i

        # ATR14 is 10 pips (0.00100).
        # For SHORT, entry=1.10000:
        # SL = 1.10000 + 0.00100 = 1.10100
        # TP = 1.10000 - 0.00150 = 1.09850
        # Inject wide range into entry bar: high=1.10150 (touches SL), low=1.09800 (touches TP)
        entry_idx = ts_to_idx[entry_ts]
        synth_candles[entry_idx]["high"] = 1.10150
        synth_candles[entry_idx]["low"] = 1.09800

        cand = {
            "ts": release_ts, "dt_str": "mock_release", "direction": "SHORT",
            "head_a": 0.3, "head_p": 0.1, "head_rp": "", "head_diff": 0.2, "head_f": "",
            "core_a": 0.3, "core_p": 0.1, "core_rp": "", "core_diff": 0.2, "core_f": "",
            "co_releases": []
        }

        # Test STOP_FIRST
        sim_stop = simulate_trade_path(cand, synth_candles, ts_to_idx, target_mult=1.5, ambiguous_rule="STOP_FIRST", max_bars=60)
        self.assertTrue(sim_stop["ambiguous_flag"])
        self.assertEqual(sim_stop["exit_reason"], "STOP")
        self.assertAlmostEqual(sim_stop["gross_r_multiple"], -1.0, places=2)

        # Test TARGET_FIRST
        sim_target = simulate_trade_path(cand, synth_candles, ts_to_idx, target_mult=1.5, ambiguous_rule="TARGET_FIRST", max_bars=60)
        self.assertTrue(sim_target["ambiguous_flag"])
        self.assertEqual(sim_target["exit_reason"], "TARGET")
        self.assertAlmostEqual(sim_target["gross_r_multiple"], +1.5, places=2)

    def test_14_synthetic_gap_fills(self):
        """
        Synthetic fixture verifying gap fills:
        - Adverse stop gap: bar opens beyond SL -> filled at worse open price.
        - Favorable target gap: bar opens beyond TP -> capped at nominal target price.
        """
        base_t = 1600000000 - (1600000000 % 3600)
        release_ts = base_t + 1800
        entry_ts = base_t + 3600

        synth_candles = []
        ts_to_idx = {}
        for i in range(100):
            t = base_t - 20 * 3600 + i * 3600
            c = {
                "time": t, "open": 1.10000, "high": 1.10100, "low": 1.10000, "close": 1.10050,
                "time_server_text": f"synth_{i}"
            }
            synth_candles.append(c)
            ts_to_idx[t] = i

        entry_idx = ts_to_idx[entry_ts]
        # Keep entry bar narrow so it does not prematurely hit SL/TP
        synth_candles[entry_idx]["high"] = 1.10020
        synth_candles[entry_idx]["low"] = 1.09980

        cand = {
            "ts": release_ts, "dt_str": "mock_release", "direction": "SHORT",
            "head_a": 0.3, "head_p": 0.1, "head_rp": "", "head_diff": 0.2, "head_f": "",
            "core_a": 0.3, "core_p": 0.1, "core_rp": "", "core_diff": 0.2, "core_f": "",
            "co_releases": []
        }

        # 1. Adverse stop gap on Bar 2 (open at 1.10250, while SL is 1.10100)
        synth_candles[entry_idx + 1]["open"] = 1.10250
        synth_candles[entry_idx + 1]["high"] = 1.10300
        synth_candles[entry_idx + 1]["low"] = 1.10200
        synth_candles[entry_idx + 1]["close"] = 1.10250

        sim_gap = simulate_trade_path(cand, synth_candles, ts_to_idx, target_mult=1.5, ambiguous_rule="STOP_FIRST", max_bars=60)
        self.assertEqual(sim_gap["exit_reason"], "STOP")
        self.assertAlmostEqual(sim_gap["exit_price"], 1.10250, places=5)  # Filled at worse open!
        self.assertAlmostEqual(sim_gap["gross_r_multiple"], -2.5, places=2)  # Worse than -1.0 R

        # 2. Reset Bar 2 and test favorable target gap on Bar 2 (open at 1.09700, while TP is 1.09850)
        synth_candles[entry_idx + 1]["open"] = 1.09700
        synth_candles[entry_idx + 1]["high"] = 1.09750
        synth_candles[entry_idx + 1]["low"] = 1.09650
        synth_candles[entry_idx + 1]["close"] = 1.09700

        sim_tp_gap = simulate_trade_path(cand, synth_candles, ts_to_idx, target_mult=1.5, ambiguous_rule="STOP_FIRST", max_bars=60)
        self.assertEqual(sim_tp_gap["exit_reason"], "TARGET")
        self.assertAlmostEqual(sim_tp_gap["exit_price"], 1.09850, places=5)  # Capped at nominal TP!
        self.assertAlmostEqual(sim_tp_gap["gross_r_multiple"], +1.5, places=2)

    def test_15_synthetic_h60_timeout_labeling(self):
        """
        Synthetic fixture verifying that when neither SL nor TP is triggered,
        the trade exits after 60 observed bars at Bar 60 close with label TIMEOUT_H60 (NOT TIMEOUT_H24).
        """
        base_t = 1600000000 - (1600000000 % 3600)
        release_ts = base_t + 1800
        entry_ts = base_t + 3600

        # 100 bars where price stays strictly between SL and TP
        synth_candles = []
        ts_to_idx = {}
        for i in range(100):
            t = base_t - 20 * 3600 + i * 3600
            c = {
                "time": t, "open": 1.10000, "high": 1.10050, "low": 1.09950, "close": 1.10000,
                "time_server_text": f"synth_{i}"
            }
            synth_candles.append(c)
            ts_to_idx[t] = i

        # Modify Bar 60 close to 1.10020
        entry_idx = ts_to_idx[entry_ts]
        synth_candles[entry_idx + 59]["close"] = 1.10020

        cand = {
            "ts": release_ts, "dt_str": "mock_release", "direction": "SHORT",
            "head_a": 0.3, "head_p": 0.1, "head_rp": "", "head_diff": 0.2, "head_f": "",
            "core_a": 0.3, "core_p": 0.1, "core_rp": "", "core_diff": 0.2, "core_f": "",
            "co_releases": []
        }

        sim_to = simulate_trade_path(cand, synth_candles, ts_to_idx, target_mult=1.5, ambiguous_rule="STOP_FIRST", max_bars=60)
        self.assertEqual(sim_to["exit_reason"], "TIMEOUT_H60")
        self.assertEqual(sim_to["bars_held"], 60)
        self.assertAlmostEqual(sim_to["exit_price"], 1.10020, places=5)

    def test_16_real_world_independent_spot_checks(self):
        """
        Independently spot-checks 5 distinct historical episodes against raw pinned files:
        1. 2018.03.13 15:30:00 (Directional disagreement with baseline A-F).
        2. 2021.05.12 15:30:00 (Intrabar ambiguous collision episode).
        3. 2020.12.10 16:30:00 (Latest exit episode at Bar 23).
        4. 2015.01.16 16:30:00 (Unforecasted 2015 episode, previously MISSING_AF).
        5. 2025.04.10 15:30:00 (Best trade by pips: +36.8 pips, +1.50 R).
        """
        trades_map = {t["release_time_server"]: t for t in self.sim_results["trials"]["primary_1.5x_conservative"]["trades"]}

        # 1. 2018.03.13: A-F was SHORT, A-P was LONG
        t1 = trades_map["2018.03.13 15:30:00"]
        self.assertEqual(t1["direction"], "LONG")
        self.assertEqual(t1["exit_reason"], "STOP")
        self.assertEqual(t1["bars_held"], 1)
        self.assertAlmostEqual(t1["gross_r_multiple"], -1.0, places=2)

        # 2. 2021.05.12: Ambiguous bar 1
        t2 = trades_map["2021.05.12 15:30:00"]
        self.assertEqual(t2["direction"], "SHORT")
        self.assertTrue(t2["ambiguous_flag"])
        self.assertEqual(t2["exit_reason"], "STOP")
        self.assertEqual(t2["bars_held"], 1)
        self.assertAlmostEqual(t2["gross_r_multiple"], -1.0, places=2)

        # 3. 2021.02.10: Latest exit at Bar 23
        t3 = trades_map["2021.02.10 16:30:00"]
        self.assertEqual(t3["direction"], "LONG")
        self.assertEqual(t3["exit_reason"], "TARGET")
        self.assertEqual(t3["bars_held"], 23)
        self.assertAlmostEqual(t3["gross_r_multiple"], +1.5, places=2)

        # 4. 2015.01.16: Unforecasted 2015 release (proves inclusion of unforecasted episode)
        t4 = trades_map["2015.01.16 16:30:00"]
        self.assertEqual(t4["direction"], "LONG")
        self.assertEqual(t4["head_f"], "")
        self.assertEqual(t4["exit_reason"], "STOP")
        self.assertEqual(t4["bars_held"], 1)
        self.assertAlmostEqual(t4["gross_r_multiple"], -1.0, places=2)

        # 5. 2025.04.10: Best trade by pips
        t5 = trades_map["2025.04.10 15:30:00"]
        self.assertEqual(t5["direction"], "LONG")
        self.assertEqual(t5["exit_reason"], "TARGET")
        self.assertEqual(t5["bars_held"], 1)
        self.assertAlmostEqual(t5["gross_pnl_pips"], 36.8, places=1)
        self.assertAlmostEqual(t5["gross_r_multiple"], +1.5, places=2)

    def test_17_path_continuity_and_gaps(self):
        """Verifies zero unexpected gaps across all 55 candidates and accounts for weekend closures."""
        json_path = os.path.join(DEFAULT_OUTPUT_DIR, "cpi_momentum_trade_ledger.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        path_audit = data["path_audit"]
        self.assertEqual(path_audit["total_candidate_trades"], 55)
        self.assertEqual(path_audit["total_unexpected_missing_data_gaps"], 0)
        self.assertEqual(path_audit["total_weekend_closures_observed"], 37)

    def test_18_reconcile_reported_figures_against_ledgers(self):
        """
        Reconciles reported figures directly against computed ledger metrics:
        - Mean risk is ~12.20 pips (not 15.68 pips).
        - Optimistic profit factor is ~1.45.
        - Optimistic max drawdown is ~6.00 R.
        - Jobless claims coincide with 8 candidate trades (not 16).
        - Markdown report text matches computed figures.
        """
        metrics = self.sim_results["trials"]["primary_1.5x_conservative"]["metrics"]
        metrics_opt = self.sim_results["trials"]["primary_1.5x_optimistic"]["metrics"]

        # Mean risk distance
        self.assertAlmostEqual(metrics["mean_risk_pips"], 12.20, places=2)
        self.assertAlmostEqual(metrics_opt["mean_risk_pips"], 12.20, places=2)

        # Optimistic profit factor and drawdown
        self.assertAlmostEqual(metrics_opt["profit_factor"], 1.45, places=2)
        self.assertAlmostEqual(metrics_opt["max_drawdown_r"], 6.00, places=2)

        # Co-release split: Initial Jobless Claims (8 trades, not 16)
        self.assertEqual(metrics["co_release_splits"]["jobless_claims_count"], 8)
        self.assertEqual(metrics["co_release_splits"]["other_co_releases_count"], 47)
        self.assertAlmostEqual(metrics["co_release_splits"]["jobless_claims_gross_r"], 4.50, places=2)
        self.assertAlmostEqual(metrics["co_release_splits"]["other_co_releases_gross_r"], -2.00, places=2)

        # Verify markdown report text contains these exact figures
        report_path = os.path.join(DEFAULT_OUTPUT_DIR, "cpi_momentum_simulation_report.md")
        with open(report_path, "r", encoding="utf-8") as f:
            report_text = f.read()

        self.assertIn("12.20 pips", report_text)
        self.assertIn("1.45", report_text)
        self.assertIn("6.00 R", report_text)
        self.assertIn("8 Candidate Timestamps with Initial Jobless Claims", report_text)
        self.assertIn("47 Candidate Timestamps without Initial Jobless Claims", report_text)
        self.assertIn("Bar 1**: 43 trades (78.2%)", report_text)
        self.assertIn("Bar 2**: 8 trades (14.5%)", report_text)
        self.assertIn("Bar 5**: 2 trades (3.6%)", report_text)
        self.assertIn("Bar 18**: 1 trades (1.8%)", report_text)
        self.assertIn("Bar 23**: 1 trades (1.8%)", report_text)
        self.assertIn("H60 Timeouts**: 0 trades (0.0%)", report_text)

    def test_19_governance_wording_audit(self):
        """
        Audits governance wording across report and protocol files:
        - Labels trial as 'post-hoc exploratory specification', NOT pre-price-frozen.
        - Discloses prior inspection of prices, paths, and target multiple variations.
        - Disclaims independent validation for 1.0x or 2.0x target sensitivities.
        - Confirms zero registered setups.
        """
        protocol_path = os.path.join(DEFAULT_OUTPUT_DIR, "protocol.md")
        with open(protocol_path, "r", encoding="utf-8") as f:
            proto_text = f.read()

        self.assertIn("Post-Hoc Exploratory Specification", proto_text)
        self.assertIn("inspected prior to drafting this protocol document", proto_text)
        self.assertIn("pre-price-frozen hypothesis test", proto_text)
        self.assertTrue("not a registered setup" in proto_text.lower().replace("*", ""))
        self.assertIn("must not be traded", proto_text)
        self.assertNotIn("frozen protocol", proto_text)

        report_path = os.path.join(DEFAULT_OUTPUT_DIR, "cpi_momentum_simulation_report.md")
        with open(report_path, "r", encoding="utf-8") as f:
            report_text = f.read()

        self.assertIn("POST-HOC EXPLORATORY SPECIFICATION", report_text)
        self.assertIn("NOT independently validated parameter choices", report_text)
        self.assertTrue("not a registered setup" in report_text.lower().replace("*", ""))
        self.assertIn("must not be traded", report_text)
        self.assertNotIn("frozen protocol", report_text)

    def test_20_synthetic_weekend_gap_classifier(self):
        """
        Synthetic fixture testing the weekend-gap classifier:
        - A weekday 23:00 gap (Wednesday 23:00 to Thursday 02:00) is NOT a weekend closure.
        - A Friday-to-Sunday/Monday closure IS classified as a weekend closure.
        - Confirms 37 observed weekend closures and 0 unexpected gaps on disk.
        """
        # 1. Weekday 23:00 gap (Wednesday 23:00 to Thursday 02:00)
        wed_gap = is_weekend_closure("2024.01.10 23:00:00", "2024.01.11 02:00:00", 3 * 3600)
        self.assertFalse(wed_gap)

        # 2. Weekday Thursday 23:00 to Friday 05:00
        thu_gap = is_weekend_closure("2024.01.11 23:00:00", "2024.01.12 05:00:00", 6 * 3600)
        self.assertFalse(thu_gap)

        # 3. Friday 23:00 to Sunday 23:00 (Weekend)
        fri_sun_gap = is_weekend_closure("2024.01.12 23:00:00", "2024.01.14 23:00:00", 48 * 3600)
        self.assertTrue(fri_sun_gap)

        # 4. Friday 23:00 to Monday 00:00 (Weekend)
        fri_mon_gap = is_weekend_closure("2024.01.12 23:00:00", "2024.01.15 00:00:00", 49 * 3600)
        self.assertTrue(fri_mon_gap)

        # 5. Synthetic candles path audit showing Wednesday gap is flagged as unexpected gap
        synth_candles = []
        base_t = 1704927600  # 2024.01.10 23:00:00 (Wednesday)
        synth_candles.append({"time": base_t, "time_server_text": "2024.01.10 23:00:00"})
        # 3-hour gap to Thursday 02:00
        synth_candles.append({"time": base_t + 3 * 3600, "time_server_text": "2024.01.11 02:00:00"})
        for i in range(2, 60):
            synth_candles.append({"time": base_t + (i + 2) * 3600, "time_server_text": f"synth_{i}"})

        audit = audit_path_continuity(synth_candles, entry_idx=0, max_bars=60)
        self.assertEqual(audit["weekend_closures"], 0)
        self.assertEqual(len(audit["unexpected_missing_data_gaps"]), 1)
        self.assertEqual(audit["unexpected_missing_data_gaps"][0]["gap_hours"], 3.0)

    def test_21_fail_closed_on_sha256_mismatch_and_integrity(self):
        """
        Verifies runner fails closed on SHA-256 mismatch or calendar integrity failure.
        """
        # Test verify_pinned_inputs_or_fail with non-existent file
        with self.assertRaises(FileNotFoundError):
            verify_pinned_inputs_or_fail("non_existent_calendar.csv", CANDLES_PATH)

        # Test verify_pinned_inputs_or_fail with mismatched content
        import tempfile
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            tf.write("corrupted content")
            temp_path = tf.name

        try:
            with self.assertRaises(RuntimeError) as ctx:
                verify_pinned_inputs_or_fail(temp_path, CANDLES_PATH)
            self.assertIn("Calendar SHA-256 verification failed", str(ctx.exception))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_22_synthetic_atr14_consecutive_continuity(self):
        """
        Verifies that compute_atr14 strictly enforces 15 consecutive completed bars
        and fails closed on missing bars in the pre-release window.
        """
        base_t = 1600000000 - (1600000000 % 3600)
        release_ts = base_t + 20 * 3600 + 1800  # release at 20:30

        # Build 20 bars where bar 7 has a gap (time jumps by 7200 instead of 3600)
        discontinuous_candles = []
        for i in range(20):
            t = base_t + i * 3600
            if i >= 8:
                t += 3600  # inject 1-hour gap
            discontinuous_candles.append({
                "time": t, "open": 1.10000, "high": 1.10100, "low": 1.10000, "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Must raise ValueError with 'Discontinuous ATR14 window'
        with self.assertRaises(ValueError) as ctx:
            compute_atr14(discontinuous_candles, release_ts)
        self.assertIn("Discontinuous ATR14 window", str(ctx.exception))

        # Conversely, all 55 real candidate trades must pass without error
        for cand in self.candidates:
            atr = compute_atr14(self.candles, cand["ts"])
            self.assertGreater(atr, 0.0)


if __name__ == "__main__":
    unittest.main()

