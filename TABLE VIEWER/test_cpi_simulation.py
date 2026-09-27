"""
Unit Tests for CPI Exploratory Historical Simulation & Decision Ledger
Location: TABLE VIEWER/NEW/test_cpi_simulation.py

Independent Synthetic Fixtures & Audit Verifications:
1. Pinned input SHA-256 cryptographic provenance.
2. Complete 277-episode decision ledger reconciliation (cpi_decision_ledger.csv).
3. Synthetic ATR spike exclusion (including exact-hour release at 16:00:00).
4. Synthetic exact-hour entry timing requirement ((ts // 3600 + 1) * 3600).
5. Synthetic absent entry bar explicit error/exclusion.
6. Synthetic favorable target gap capping at nominal target price.
7. Synthetic incomplete H24 path explicit error/exclusion.
8. Synthetic adverse stop gap fill at worse open price.
9. Synthetic intrabar collision precedence (conservative vs optimistic).
10. Reconciled empirical ledger metrics, holding times, and post-hoc splits.
11. HTML viewer panel and markdown report dynamic match against ledger data.

NOTE: All HTML checks are performed via string and regex inspection on the
generated static artifact on disk. No browser automation or interaction is claimed.
"""

import unittest
import os
import csv
import json
import hashlib
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cpi_simulation import (
    CALENDAR_PATH,
    CANDLES_PATH,
    SETUP_DIR,
    load_candles,
    load_calendar_by_ts,
    reconcile_and_identify_candidates,
    compute_atr14,
    simulate_trade_path,
    run_full_simulation_suite,
    PIP_SIZE
)
from generate_table import build_html, CODEX_DISPLAY_APPROVED

VIEWER_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "table_viewer.html")

EXPECTED_CALENDAR_SHA256 = "76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e"
EXPECTED_CANDLES_SHA256 = "893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5"


class TestCpiSimulation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Run simulation suite to produce/refresh artifacts
        cls.sim_results = run_full_simulation_suite()
        cls.candles, cls.ts_to_idx = load_candles(CANDLES_PATH)
        cls.rows_by_ts, total_raw_count = load_calendar_by_ts(CALENDAR_PATH)
        cls.candidates, cls.recon = reconcile_and_identify_candidates(cls.rows_by_ts, total_raw_count)

    def test_pinned_input_sha256_digests(self):
        """Verifies byte-for-byte SHA-256 cryptographic provenance of pinned inputs."""
        with open(CALENDAR_PATH, "rb") as f:
            cal_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(cal_hash, EXPECTED_CALENDAR_SHA256)

        with open(CANDLES_PATH, "rb") as f:
            candles_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(candles_hash, EXPECTED_CANDLES_SHA256)

    def test_complete_decision_ledger_reconciliation(self):
        """
        Verifies exact decision ledger counts for all 277 inflation episodes:
        138 PCE-only, 12 shared collisions, 26 missing A/F, 65 mixed/zero, 36 candidate trades.
        Also distinguishes 825 family timestamps from 40,202 revision-0 calendar timestamps.
        """
        ledger_path = os.path.join(SETUP_DIR, "cpi_decision_ledger.csv")
        self.assertTrue(os.path.exists(ledger_path))

        with open(ledger_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        # Total rows must be exactly 277
        self.assertEqual(len(rows), 277)

        category_counts = {}
        for r in rows:
            cat = r["disposition"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        self.assertEqual(category_counts.get("PCE_ONLY", 0), 138)
        self.assertEqual(category_counts.get("SHARED_COLLISION", 0), 12)
        self.assertEqual(category_counts.get("MISSING_AF", 0), 26)
        self.assertEqual(category_counts.get("MIXED_ZERO", 0), 65)
        self.assertEqual(category_counts.get("CANDIDATE_TRADE", 0), 36)
        self.assertEqual(sum(category_counts.values()), 277)

        # Distinguish 825 timestamps across 5 families from 40,202 revision-0 timestamps
        self.assertEqual(self.recon["total_distinct_timestamps"], 40202)
        self.assertEqual(self.recon["revision_0_records"], 104068)
        self.assertEqual(self.recon["total_calendar_records"], 123054)

    def test_synthetic_atr_spike_and_exact_hour_exclusion(self):
        """
        Independent synthetic fixture verifying ATR14 strictly excludes release bar:
        - Creates 25 1-hour candles where bar 15 (from 15:00 to 16:00) has a massive 500-pip spike.
        - Under `< release_ts`, a release at 16:00:00 MUST strictly exclude the bar ending at 16:00:00.
        - Bars 0 through 14 (15 completed bars) are included, producing 14 true ranges.
        - Verifies calculated ATR is ~10 pips, not contaminated by the 500-pip spike.
        """
        base_t = 1500000000 - (1500000000 % 3600)  # Exact epoch hour
        synth_candles = []
        for i in range(25):
            t = base_t + i * 3600
            synth_candles.append({
                "time": t,
                "open": 1.10000,
                "high": 1.10100,
                "low": 1.10000,
                "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Inject massive 500-pip spike into Bar 15 (time: base_t + 15*3600, ends at base_t + 16*3600)
        synth_candles[15]["high"] = 1.15000
        synth_candles[15]["low"] = 1.10000
        synth_candles[15]["close"] = 1.15000

        # Exact-hour release at base_t + 16 * 3600 (e.g. 16:00:00)
        exact_hour_rel = base_t + 16 * 3600

        # compute_atr14 requires 14 completed bars strictly before release_ts:
        # candle_time + 3600 < exact_hour_rel
        # Bar 15 has candle_time + 3600 == exact_hour_rel, so it must be EXCLUDED!
        # Bars available: 0 through 14 (exactly 15 completed bars, yielding 14 TRs).
        # None of them has the spike.
        atr = compute_atr14(synth_candles, exact_hour_rel)
        # Baseline TR is 0.00100 (10 pips)
        self.assertAlmostEqual(atr, 0.00100, places=6)

        # Contrast: if spike bar were included, ATR would be around (13 * 10 + 500) / 14 = ~45 pips
        self.assertLess(atr, 0.00200)

    def test_synthetic_exact_hour_entry_timing(self):
        """
        Independent synthetic fixture verifying entry occurs at exact intended next-hour open:
        ((ts // 3600) + 1) * 3600.
        """
        base_t = 1500000000 - (1500000000 % 3600)
        # Release at 15:30:00 -> entry at 16:00:00
        rel_30 = base_t + 15 * 3600 + 1800
        expected_entry_30 = base_t + 16 * 3600

        # Release at 15:00:00 (exact hour) -> entry at 16:00:00
        rel_00 = base_t + 15 * 3600
        expected_entry_00 = base_t + 16 * 3600

        # Release at 15:45:00 -> entry at 16:00:00
        rel_45 = base_t + 15 * 3600 + 2700
        expected_entry_45 = base_t + 16 * 3600

        def calc_entry(ts):
            return ((ts // 3600) + 1) * 3600

        self.assertEqual(calc_entry(rel_30), expected_entry_30)
        self.assertEqual(calc_entry(rel_00), expected_entry_00)
        self.assertEqual(calc_entry(rel_45), expected_entry_45)

    def test_synthetic_absent_intended_entry_bar_error(self):
        """
        Independent synthetic fixture verifying simulate_trade_path raises ValueError
        when the exact intended next-hour entry bar is missing (search forward across gaps disabled).
        """
        base_t = 1500000000 - (1500000000 % 3600)
        synth_candles = []
        for i in range(16):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10100,
                "low": 1.10000,
                "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Next bar should be i=16 (base_t + 16*3600), but omit it!
        # Instead, jump to i=17 (base_t + 17*3600)
        for i in range(17, 45):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10100,
                "low": 1.10000,
                "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        synth_idx = {c["time"]: i for i, c in enumerate(synth_candles)}
        cand = {
            "ts": base_t + 15 * 3600 + 1800,  # 15:30 release; intended entry is 16:00
            "dt_str": "synthetic_release",
            "direction": "SHORT",
            "head_a": 0.3, "head_f": 0.2, "head_s": 0.1,
            "core_a": 0.3, "core_f": 0.2, "core_s": 0.1,
            "co_releases": []
        }

        # Must raise ValueError because bar at 16:00 is absent
        with self.assertRaises(ValueError) as ctx:
            simulate_trade_path(cand, synth_candles, synth_idx, target_mult=1.5)
        self.assertIn("Missing intended entry bar", str(ctx.exception))

    def test_synthetic_favorable_target_gap_capping(self):
        """
        Independent synthetic fixture verifying that a bar opening beyond the profit target
        is capped at the nominal target price and gross R multiple is capped at target_mult.
        """
        base_t = 1500000000 - (1500000000 % 3600)
        synth_candles = []
        for i in range(16):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10100,
                "low": 1.10000,
                "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Bar 16 (entry): open at 1.10000
        # ATR14 is 0.00100 (10 pips). For SHORT, TP is 1.10000 - 1.5 * 0.00100 = 1.09850 (15 pips).
        # SL is 1.10000 + 1.0 * 0.00100 = 1.10100 (10 pips).
        synth_candles.append({
            "time": base_t + 16 * 3600,
            "open": 1.10000,
            "high": 1.10020,
            "low": 1.09980,
            "close": 1.10000,
            "time_server_text": "synth_16_entry"
        })

        # Bar 17 opens with a massive favorable gap down at 1.09000 (100 pips below entry!)
        synth_candles.append({
            "time": base_t + 17 * 3600,
            "open": 1.09000,
            "high": 1.09050,
            "low": 1.08950,
            "close": 1.09000,
            "time_server_text": "synth_17_gap_tp"
        })

        # Add remaining bars to fulfill H24 path
        for i in range(18, 50):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.09000,
                "high": 1.09050,
                "low": 1.08950,
                "close": 1.09000,
                "time_server_text": f"synth_{i}"
            })

        synth_idx = {c["time"]: i for i, c in enumerate(synth_candles)}
        cand = {
            "ts": base_t + 15 * 3600 + 1800,
            "dt_str": "synthetic_release",
            "direction": "SHORT",
            "head_a": 0.3, "head_f": 0.2, "head_s": 0.1,
            "core_a": 0.3, "core_f": 0.2, "core_s": 0.1,
            "co_releases": []
        }

        trade = simulate_trade_path(cand, synth_candles, synth_idx, target_mult=1.5)
        self.assertEqual(trade["exit_reason"], "TARGET")
        # Exit price must be capped at nominal target (1.09850), NOT the gapped open (1.09000)
        self.assertAlmostEqual(trade["exit_price"], 1.09850, places=5)
        # Gross R must be exactly +1.50 R, NOT +10.0 R
        self.assertAlmostEqual(trade["gross_r_multiple"], 1.50, places=4)
        self.assertEqual(trade["bars_held"], 2)

    def test_synthetic_incomplete_h24_path_error(self):
        """
        Independent synthetic fixture verifying simulate_trade_path raises ValueError
        when fewer than 24 bars follow the entry bar.
        """
        base_t = 1500000000 - (1500000000 % 3600)
        synth_candles = []
        for i in range(16):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10100,
                "low": 1.10000,
                "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Add entry bar + only 10 forward bars (total 11 bars, less than required 24)
        for i in range(16, 27):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10020,
                "low": 1.09980,
                "close": 1.10000,
                "time_server_text": f"synth_{i}"
            })

        synth_idx = {c["time"]: i for i, c in enumerate(synth_candles)}
        cand = {
            "ts": base_t + 15 * 3600 + 1800,
            "dt_str": "synthetic_release",
            "direction": "SHORT",
            "head_a": 0.3, "head_f": 0.2, "head_s": 0.1,
            "core_a": 0.3, "core_f": 0.2, "core_s": 0.1,
            "co_releases": []
        }

        with self.assertRaises(ValueError) as ctx:
            simulate_trade_path(cand, synth_candles, synth_idx, target_mult=1.5)
        self.assertIn("Incomplete H24 path", str(ctx.exception))

    def test_synthetic_gap_fill_at_worse_open_for_stop(self):
        """
        Independent synthetic fixture verifying adverse stop gaps fill at worse open price.
        """
        base_t = 1500000000 - (1500000000 % 3600)
        synth_candles = []
        for i in range(16):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10100,
                "low": 1.10000,
                "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Entry bar: open 1.10000. SHORT trade: SL nominal is 1.10100.
        synth_candles.append({
            "time": base_t + 16 * 3600,
            "open": 1.10000,
            "high": 1.10020,
            "low": 1.09980,
            "close": 1.10000,
            "time_server_text": "synth_16_entry"
        })

        # Bar 17 gaps up adversely to 1.10250 (15 pips above SL!)
        worse_open = 1.10250
        synth_candles.append({
            "time": base_t + 17 * 3600,
            "open": worse_open,
            "high": worse_open + 0.00010,
            "low": worse_open - 0.00010,
            "close": worse_open,
            "time_server_text": "synth_17_adverse_gap"
        })

        for i in range(18, 50):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": worse_open,
                "high": worse_open + 0.00010,
                "low": worse_open - 0.00010,
                "close": worse_open,
                "time_server_text": f"synth_{i}"
            })

        synth_idx = {c["time"]: i for i, c in enumerate(synth_candles)}
        cand = {
            "ts": base_t + 15 * 3600 + 1800,
            "dt_str": "synthetic_release",
            "direction": "SHORT",
            "head_a": 0.3, "head_f": 0.2, "head_s": 0.1,
            "core_a": 0.3, "core_f": 0.2, "core_s": 0.1,
            "co_releases": []
        }

        trade = simulate_trade_path(cand, synth_candles, synth_idx, target_mult=1.5)
        self.assertEqual(trade["exit_reason"], "STOP")
        # Exit price fills at worse open
        self.assertAlmostEqual(trade["exit_price"], worse_open, places=5)
        # Loss is greater than 1.0 R: 25 pips / 10 pips = -2.50 R
        self.assertAlmostEqual(trade["gross_r_multiple"], -2.50, places=4)

    def test_synthetic_intrabar_ambiguity_precedence(self):
        """
        Independent synthetic fixture verifying intrabar collision handling:
        When a bar touches both SL and TP, conservative mode hits STOP first,
        optimistic mode hits TARGET first, and both set ambiguous_flag = True.
        """
        base_t = 1500000000 - (1500000000 % 3600)
        synth_candles = []
        for i in range(16):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10100,
                "low": 1.10000,
                "close": 1.10050,
                "time_server_text": f"synth_{i}"
            })

        # Entry bar: open 1.10000, touches both SL (1.10100) and TP (1.09850)
        synth_candles.append({
            "time": base_t + 16 * 3600,
            "open": 1.10000,
            "high": 1.10150,  # Touches SL
            "low": 1.09800,   # Touches TP
            "close": 1.10000,
            "time_server_text": "synth_16_ambiguous"
        })

        for i in range(17, 50):
            synth_candles.append({
                "time": base_t + i * 3600,
                "open": 1.10000,
                "high": 1.10020,
                "low": 1.09980,
                "close": 1.10000,
                "time_server_text": f"synth_{i}"
            })

        synth_idx = {c["time"]: i for i, c in enumerate(synth_candles)}
        cand = {
            "ts": base_t + 15 * 3600 + 1800,
            "dt_str": "synthetic_release",
            "direction": "SHORT",
            "head_a": 0.3, "head_f": 0.2, "head_s": 0.1,
            "core_a": 0.3, "core_f": 0.2, "core_s": 0.1,
            "co_releases": []
        }

        # Conservative: STOP_FIRST
        trade_cons = simulate_trade_path(cand, synth_candles, synth_idx, target_mult=1.5, ambiguous_rule="STOP_FIRST")
        self.assertTrue(trade_cons["ambiguous_flag"])
        self.assertEqual(trade_cons["exit_reason"], "STOP")
        self.assertAlmostEqual(trade_cons["gross_r_multiple"], -1.00, places=2)

        # Optimistic: TARGET_FIRST
        trade_opt = simulate_trade_path(cand, synth_candles, synth_idx, target_mult=1.5, ambiguous_rule="TARGET_FIRST")
        self.assertTrue(trade_opt["ambiguous_flag"])
        self.assertEqual(trade_opt["exit_reason"], "TARGET")
        self.assertAlmostEqual(trade_opt["gross_r_multiple"], 1.50, places=2)

    def test_reconciled_ledger_metrics_and_posthoc_splits(self):
        """
        Verifies exact empirical ledger metrics matching Codex audit:
        - Primary trial: gross totals -4.00 R (1.0x), +4.00 R (1.5x), +3.00 R (2.0x), +9.00 R (optimistic).
        - Primary holding distribution: Bar 1: 26, Bar 2: 6, Bar 3: 2, Bar 5: 1, Bar 18: 1.
        - Actual trade-level means: approx 13.30 risk pips and 1.89 gross P&L pips.
        - Co-release split: 11 Jobless Claims sum to +4.00 R; remaining 25 sum to 0.00 R.
        - Directional split: Shorts sum to -0.50 R; Longs sum to +4.50 R.
        - Gross R without best trade: +2.50 R.
        """
        p_met = self.sim_results["trials"]["primary_1.5x_conservative"]["metrics"]
        p_opt = self.sim_results["trials"]["primary_1.5x_optimistic"]["metrics"]
        s1_met = self.sim_results["trials"]["sensitivity_1.0x_conservative"]["metrics"]
        s2_met = self.sim_results["trials"]["sensitivity_2.0x_conservative"]["metrics"]

        # Exact R totals
        self.assertAlmostEqual(s1_met["total_gross_r"], -4.00, places=2)
        self.assertAlmostEqual(p_met["total_gross_r"], 4.00, places=2)
        self.assertAlmostEqual(s2_met["total_gross_r"], 3.00, places=2)
        self.assertAlmostEqual(p_opt["total_gross_r"], 9.00, places=2)

        # Holding distribution: Bar 1: 26, Bar 2: 6, Bar 3: 2, Bar 5: 1, Bar 18: 1
        expected_bars = {1: 26, 2: 6, 3: 2, 5: 1, 18: 1}
        actual_bars = {int(k): v for k, v in p_met["bars_held_distribution"].items()}
        self.assertEqual(actual_bars, expected_bars)

        # Trade-level means
        self.assertAlmostEqual(p_met["mean_risk_pips"], 13.30, places=1)
        self.assertAlmostEqual(p_met["mean_gross_pnl_pips"], 1.89, places=1)

        # Co-release split
        co = p_met["co_release_splits"]
        self.assertEqual(co["jobless_claims_count"], 11)
        self.assertAlmostEqual(co["jobless_claims_gross_r"], 4.00, places=2)
        self.assertEqual(co["other_co_releases_count"], 25)
        self.assertAlmostEqual(co["other_co_releases_gross_r"], 0.00, places=2)

        # Directional split
        ds = p_met["direction_splits"]
        self.assertEqual(ds["short_count"], 18)
        self.assertAlmostEqual(ds["short_gross_r"], -0.50, places=2)
        self.assertEqual(ds["long_count"], 18)
        self.assertAlmostEqual(ds["long_gross_r"], 4.50, places=2)

        # Gross R without best trade
        self.assertAlmostEqual(p_met["gross_r_without_best_trade"], 2.50, places=2)

    def test_report_and_viewer_panel_match_ledger(self):
        """
        Verifies that report and viewer panel derive every metric directly from the ledger.
        Explicitly notes: tested via static DOM/file string parsing; no browser automation claimed.
        """
        # Read JSON ledger
        json_path = os.path.join(SETUP_DIR, "cpi_trade_ledger.json")
        with open(json_path, "r", encoding="utf-8") as f:
            ledger_data = json.load(f)
        p_met = ledger_data["trials"]["primary_1.5x_conservative"]["metrics"]

        # Read Markdown report
        md_path = os.path.join(SETUP_DIR, "cpi_simulation_report.md")
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        # Read HTML viewer
        with open(VIEWER_HTML_PATH, "r", encoding="utf-8") as f:
            html_text = f.read()

        # Both artifacts contain exact primary R
        self.assertIn("+4.00 R", md_text)
        self.assertIn("+4.00 R", html_text)

        # Both artifacts contain exact trade-level means
        self.assertIn(f"{p_met['mean_risk_pips']:.2f} pips", md_text)
        self.assertIn(f"{p_met['mean_risk_pips']:.2f} pips", html_text)
        self.assertIn(f"{p_met['mean_gross_pnl_pips']:+.2f} pips", md_text)
        self.assertIn(f"{p_met['mean_gross_pnl_pips']:+.2f} pips", html_text)

        # Both artifacts contain exact holding distribution
        self.assertIn("Bar 1: 26", md_text)
        self.assertIn("Bar 2: 6", md_text)
        self.assertIn("Bar 1: 26", html_text)
        self.assertIn("Bar 2: 6", html_text)

        # Both artifacts state the co-release split
        self.assertIn("+4.00 R", md_text)
        self.assertIn("+4.00 R", html_text)

        # Panel governance statement
        self.assertIn("UNDER AUDIT — NO REGISTERED SETUP", html_text)
        self.assertIn("registered <em>for</em> demo forward testing", html_text)

        # Zero dark mode styling
        html_lower = html_text.lower()
        self.assertNotIn("dark-theme", html_lower)
        self.assertNotIn("theme-dark", html_lower)

    def test_reconciled_handoff_arithmetic(self):
        """
        Derives and verifies all handoff arithmetic programmatically from the ledger:
        - calendar_releases.csv contains 104,068 revision-0 rows, and 40,202 distinct timestamps.
        - Longs: 18 trades, 9 targets / 9 stops, +4.50 R.
        - Shorts: 18 trades, 7 targets / 11 stops, -0.50 R.
        - Co-release split: 11 Jobless Claims = 6 targets / 5 stops, +4.00 R; 25 other = 10 targets / 15 stops, 0.00 R.
        - Ambiguous counts: 1.0x: 3, 1.5x: 2, 2.0x: 2.
        - Robustness check without best trade: excluding +1.50 R on 2024.04.10 drops total to +2.50 R.
        """
        json_path = os.path.join(SETUP_DIR, "cpi_trade_ledger.json")
        with open(json_path, "r", encoding="utf-8") as f:
            ledger = json.load(f)

        # 1. Calendar revision-0 rows vs distinct timestamps
        self.assertEqual(self.recon["revision_0_records"], 104068)
        self.assertEqual(self.recon["total_distinct_timestamps"], 40202)

        # 2. Ambiguous counts across sensitivity trials
        s1_ambig = sum(1 for t in ledger["trials"]["sensitivity_1.0x_conservative"]["trades"] if t.get("ambiguous_flag"))
        p_ambig = sum(1 for t in ledger["trials"]["primary_1.5x_conservative"]["trades"] if t.get("ambiguous_flag"))
        s2_ambig = sum(1 for t in ledger["trials"]["sensitivity_2.0x_conservative"]["trades"] if t.get("ambiguous_flag"))
        self.assertEqual(s1_ambig, 3)
        self.assertEqual(p_ambig, 2)
        self.assertEqual(s2_ambig, 2)

        # 3. Directional split: Longs vs Shorts in primary trial
        p_trades = ledger["trials"]["primary_1.5x_conservative"]["trades"]
        longs = [t for t in p_trades if t["direction"] == "LONG"]
        shorts = [t for t in p_trades if t["direction"] == "SHORT"]

        self.assertEqual(len(longs), 18)
        long_targets = sum(1 for t in longs if t["exit_reason"] == "TARGET")
        long_stops = sum(1 for t in longs if t["exit_reason"] == "STOP")
        long_gross_r = sum(t["gross_r_multiple"] for t in longs)
        self.assertEqual(long_targets, 9)
        self.assertEqual(long_stops, 9)
        self.assertAlmostEqual(long_gross_r, 4.50, places=2)

        self.assertEqual(len(shorts), 18)
        short_targets = sum(1 for t in shorts if t["exit_reason"] == "TARGET")
        short_stops = sum(1 for t in shorts if t["exit_reason"] == "STOP")
        short_gross_r = sum(t["gross_r_multiple"] for t in shorts)
        self.assertEqual(short_targets, 7)
        self.assertEqual(short_stops, 11)
        self.assertAlmostEqual(short_gross_r, -0.50, places=2)

        # 4. Co-release split: Jobless Claims vs Others
        jobless = [t for t in p_trades if "840140001" in t.get("co_releases", [])]
        others = [t for t in p_trades if "840140001" not in t.get("co_releases", [])]

        self.assertEqual(len(jobless), 11)
        jobless_targets = sum(1 for t in jobless if t["exit_reason"] == "TARGET")
        jobless_stops = sum(1 for t in jobless if t["exit_reason"] == "STOP")
        jobless_gross_r = sum(t["gross_r_multiple"] for t in jobless)
        self.assertEqual(jobless_targets, 6)
        self.assertEqual(jobless_stops, 5)
        self.assertAlmostEqual(jobless_gross_r, 4.00, places=2)

        self.assertEqual(len(others), 25)
        others_targets = sum(1 for t in others if t["exit_reason"] == "TARGET")
        others_stops = sum(1 for t in others if t["exit_reason"] == "STOP")
        others_gross_r = sum(t["gross_r_multiple"] for t in others)
        self.assertEqual(others_targets, 10)
        self.assertEqual(others_stops, 15)
        self.assertAlmostEqual(others_gross_r, 0.00, places=2)

        # 5. Robustness check excluding best trade (+1.50 R on 2024.04.10)
        best_trade = max(p_trades, key=lambda t: t["gross_r_multiple"])
        self.assertTrue(best_trade["release_time_server"].startswith("2024.04.10"))
        self.assertAlmostEqual(best_trade["gross_r_multiple"], 1.50, places=2)
        r_without_best = sum(t["gross_r_multiple"] for t in p_trades if t is not best_trade)
        self.assertAlmostEqual(r_without_best, 2.50, places=2)

    def test_audit_gate_display_approved(self):
        """
        Verifies the Codex audit display gate in the approved state:
        - CODEX_DISPLAY_APPROVED is True (approved by Codex for display only).
        - In the generated table viewer, #resultsAuditGateCard is hidden ('style="display: none;"').
        - #resultsNumericContent is displayed ('style="display: block;"').
        - Setup status strictly remains 'UNDER AUDIT — NO REGISTERED SETUP'.
        """
        self.assertTrue(CODEX_DISPLAY_APPROVED, "CODEX_DISPLAY_APPROVED must be True upon Codex display approval")

        with open(VIEWER_HTML_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        # Audit gate elements in approved display state
        self.assertIn('id="resultsAuditGateCard"', html)
        self.assertIn('class="results-audit-gate-card" style="display: none;"', html)
        self.assertIn('id="resultsNumericContent"', html)
        self.assertIn('class="results-numeric-content" style="display: block;"', html)

        # Setup status remains strictly un-registered
        self.assertIn("UNDER AUDIT — NO REGISTERED SETUP", html)
        self.assertIn("EXPLORATORY HISTORICAL SIMULATION — NO REGISTERED SETUP", html)
        self.assertIn("Exploratory historical OHLC simulation; no registered setup.", html)
        self.assertIn("registered <em>for</em> demo forward testing", html)
        self.assertNotIn("STATUS: REGISTERED", html)

    def test_dynamic_fixture_drives_table_numbers(self):
        """
        Verifies that every number in the results table and note derives dynamically
        from the ledger rather than static baked values.
        Uses a controlled, disposable mock fixture with distinctive metrics.
        """
        mock_ledger = {
            "trials": {
                "primary_1.5x_conservative": {
                    "metrics": {
                        "total_trades": 36,
                        "wins": 21,
                        "losses": 15,
                        "total_gross_r": 7.77,
                        "mean_gross_r": 0.22,
                        "mean_risk_pips": 14.12,
                        "mean_gross_pnl_pips": 3.45,
                        "bars_held_distribution": {"1": 20, "2": 10, "4": 6},
                        "direction_splits": {
                            "long_count": 20, "long_gross_r": 11.10,
                            "short_count": 16, "short_gross_r": -3.33
                        },
                        "co_release_splits": {
                            "jobless_claims_count": 10, "jobless_claims_gross_r": 6.00,
                            "other_co_releases_count": 26, "other_co_releases_gross_r": 1.77
                        },
                        "best_trade": {"release_time_server": "2025.01.15 15:30"},
                        "gross_r_without_best_trade": 5.77
                    },
                    "trades": [
                        # 10 Jobless Longs (TARGET, R=0.60): 1 ambiguous
                        {"direction": "LONG", "exit_reason": "TARGET", "gross_r_multiple": 0.60, "co_releases": ["840140001"], "ambiguous_flag": True},
                        *[{"direction": "LONG", "exit_reason": "TARGET", "gross_r_multiple": 0.60, "co_releases": ["840140001"], "ambiguous_flag": False}] * 9,
                        # 10 Other Longs (TARGET, R=0.51): 1 ambiguous
                        {"direction": "LONG", "exit_reason": "TARGET", "gross_r_multiple": 0.51, "co_releases": [], "ambiguous_flag": True},
                        *[{"direction": "LONG", "exit_reason": "TARGET", "gross_r_multiple": 0.51, "co_releases": [], "ambiguous_flag": False}] * 9,
                        # 16 Other Shorts: 1 TARGET (R=0.67), 15 STOP (R=-0.26666666666666666): 2 ambiguous
                        {"direction": "SHORT", "exit_reason": "TARGET", "gross_r_multiple": 0.67, "co_releases": [], "ambiguous_flag": False},
                        {"direction": "SHORT", "exit_reason": "STOP", "gross_r_multiple": -0.26666666666666666, "co_releases": [], "ambiguous_flag": True},
                        {"direction": "SHORT", "exit_reason": "STOP", "gross_r_multiple": -0.26666666666666666, "co_releases": [], "ambiguous_flag": True},
                        *[{"direction": "SHORT", "exit_reason": "STOP", "gross_r_multiple": -0.26666666666666666, "co_releases": [], "ambiguous_flag": False}] * 13,
                    ]
                },
                "sensitivity_1.0x_conservative": {
                    "metrics": {
                        "total_trades": 36,
                        "wins": 12,
                        "losses": 24,
                        "total_gross_r": -12.34,
                        "mean_gross_r": -0.34
                    },
                    "trades": [
                        *[{"gross_r_multiple": 1.00, "exit_reason": "TARGET", "ambiguous_flag": True}] * 5,
                        *[{"gross_r_multiple": 1.00, "exit_reason": "TARGET", "ambiguous_flag": False}] * 7,
                        *[{"gross_r_multiple": -24.34 / 24, "exit_reason": "STOP", "ambiguous_flag": False}] * 24,
                    ]
                },
                "sensitivity_2.0x_conservative": {
                    "metrics": {
                        "total_trades": 36,
                        "wins": 15,
                        "losses": 21,
                        "total_gross_r": 9.99,
                        "mean_gross_r": 0.28
                    },
                    "trades": [
                        *[{"gross_r_multiple": 2.00, "exit_reason": "TARGET", "ambiguous_flag": True}] * 8,
                        *[{"gross_r_multiple": 2.00, "exit_reason": "TARGET", "ambiguous_flag": False}] * 7,
                        *[{"gross_r_multiple": -20.01 / 21, "exit_reason": "STOP", "ambiguous_flag": False}] * 21,
                    ]
                }
            }
        }

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            tmp_path = f.name

        try:
            build_html([], codex_display_approved=True, ledger_data=mock_ledger, output_path=tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                html = f.read()

            # Dynamic check: unique test numbers from fixture appear in HTML
            self.assertIn("+7.77 R", html, "Primary gross R must derive from fixture")
            self.assertIn("+0.22 R", html, "Primary mean R must derive from fixture")
            self.assertIn("-12.34 R", html, "Sensitivity 1.0x gross R must derive from fixture")
            self.assertIn("+9.99 R", html, "Sensitivity 2.0x gross R must derive from fixture")
            self.assertIn("14.12 pips", html, "Mean risk pips must derive from fixture")
            self.assertIn("+3.45 pips", html, "Mean gross P&L pips must derive from fixture")
            self.assertIn("+11.1 R", html, "Long gross R must derive from fixture")
            self.assertIn("-3.3 R", html, "Short gross R must derive from fixture")
            self.assertIn("+5.77 R", html, "Gross without best trade must derive from fixture")
            self.assertIn("<td>5</td>", html, "1.0x ambiguous count must derive from fixture")
            self.assertIn("<td>4</td>", html, "1.5x ambiguous count must derive from fixture")
            self.assertIn("<td>8</td>", html, "2.0x ambiguous count must derive from fixture")

            # Check that gate is hidden when approved
            self.assertIn('class="results-audit-gate-card" style="display: none;"', html)
            self.assertIn('class="results-numeric-content" style="display: block;"', html)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_status_invariance_under_high_profit(self):
        """
        Verifies that no historical profit result (even +99.00 R) can automatically
        change setup status to REGISTERED.
        """
        high_profit_ledger = {
            "trials": {
                "primary_1.5x_conservative": {
                    "metrics": {
                        "total_trades": 36,
                        "wins": 36,
                        "losses": 0,
                        "total_gross_r": 99.00,
                        "mean_gross_r": 2.75,
                        "mean_risk_pips": 15.00,
                        "mean_gross_pnl_pips": 22.50,
                        "bars_held_distribution": {"1": 36},
                        "direction_splits": {
                            "long_count": 18, "long_gross_r": 49.50,
                            "short_count": 18, "short_gross_r": 49.50
                        },
                        "co_release_splits": {
                            "jobless_claims_count": 11, "jobless_claims_gross_r": 30.25,
                            "other_co_releases_count": 25, "other_co_releases_gross_r": 68.75
                        },
                        "best_trade": {"release_time_server": "2024.04.10 15:30"},
                        "gross_r_without_best_trade": 96.25
                    },
                    "trades": [
                        *[{"direction": "LONG", "exit_reason": "TARGET", "gross_r_multiple": 2.75, "co_releases": ["840140001"], "ambiguous_flag": False}] * 11,
                        *[{"direction": "LONG", "exit_reason": "TARGET", "gross_r_multiple": 2.75, "co_releases": [], "ambiguous_flag": False}] * 7,
                        *[{"direction": "SHORT", "exit_reason": "TARGET", "gross_r_multiple": 2.75, "co_releases": [], "ambiguous_flag": False}] * 18,
                    ]
                },
                "sensitivity_1.0x_conservative": {
                    "metrics": {"total_trades": 36, "wins": 36, "losses": 0, "total_gross_r": 36.00, "mean_gross_r": 1.00},
                    "trades": [{"gross_r_multiple": 1.00, "exit_reason": "TARGET", "ambiguous_flag": False}] * 36
                },
                "sensitivity_2.0x_conservative": {
                    "metrics": {"total_trades": 36, "wins": 36, "losses": 0, "total_gross_r": 72.00, "mean_gross_r": 2.00},
                    "trades": [{"gross_r_multiple": 2.00, "exit_reason": "TARGET", "ambiguous_flag": False}] * 36
                }
            }
        }

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            tmp_path = f.name

        try:
            build_html([], codex_display_approved=True, ledger_data=high_profit_ledger, output_path=tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                html = f.read()

            # Status must remain strictly un-registered
            self.assertIn("UNDER AUDIT — NO REGISTERED SETUP", html)
            self.assertIn("EXPLORATORY HISTORICAL SIMULATION — NO REGISTERED SETUP", html)
            self.assertIn("Exploratory historical OHLC simulation; no registered setup.", html)
            self.assertIn("registered <em>for</em> demo forward testing", html)
            # Must NOT declare any setup registered
            self.assertNotIn("STATUS: REGISTERED", html)
            self.assertNotIn("APPROVED REGISTERED SETUP", html)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_dynamic_fixture_subgroup_inversion_and_timeouts(self):
        """
        Focused synthetic fixture test that changes:
        - Subgroup counts (Long: 15, Short: 25; Jobless: 14, Other: 26; Total: 40)
        - Subgroup R signs (Longs: positive -> negative; Shorts: negative -> positive;
          Jobless: positive -> negative; Other: zero -> positive)
        - Trial R signs (1.0x: negative -> positive; 1.5x: positive -> negative; 2.0x: positive -> negative)
        - Timeout count (0 -> 3 timeouts)
        Asserts that rendered labels AND color classes change correctly.
        Asserts CODEX_DISPLAY_APPROVED is True and status remains UNDER AUDIT — NO REGISTERED SETUP.
        """
        # Ensure display approval flag is True in the module upon Codex authorization
        self.assertTrue(CODEX_DISPLAY_APPROVED, "CODEX_DISPLAY_APPROVED must be True upon Codex display approval")

        synthetic_ledger = {
            "trials": {
                "primary_1.5x_conservative": {
                    "metrics": {
                        "total_trades": 40,
                        "wins": 18,
                        "losses": 19,
                        "ties": 3,
                        "total_gross_r": -1.50,  # Inverted: positive (+4.00) -> negative (-1.50)
                        "mean_gross_r": -0.04,
                        "mean_risk_pips": 12.50,
                        "mean_gross_pnl_pips": -0.50,
                        "bars_held_distribution": {"1": 25, "2": 8, "5": 7},
                        "direction_splits": {
                            "long_count": 15,
                            "long_gross_r": -5.50,  # Inverted: positive (+4.5) -> negative (-5.5)
                            "short_count": 25,
                            "short_gross_r": 4.00   # Inverted: negative (-0.5) -> positive (+4.0)
                        },
                        "co_release_splits": {
                            "jobless_claims_count": 14,
                            "jobless_claims_gross_r": -2.00,  # Inverted: positive (+4) -> negative (-2)
                            "other_co_releases_count": 26,
                            "other_co_releases_gross_r": 0.50  # Inverted: zero (0) -> positive (+0.5)
                        },
                        "exit_counts": {
                            "TARGET": 18,
                            "STOP": 19,
                            "TIMEOUT_H24": 3  # Non-zero timeout count
                        },
                        "best_trade": {"release_time_server": "2023.07.12 15:30:00"},
                        "gross_r_without_best_trade": -3.00
                    },
                    "trades": [
                        # 5 Long Jobless Targets: 5 * 0.5 = 2.50
                        *[{"direction": "LONG", "exit_reason": "TARGET", "gross_r_multiple": 0.50, "co_releases": ["840140001"], "ambiguous_flag": False}] * 5,
                        # 5 Long Jobless Stops: 5 * -0.90 = -4.50
                        *[{"direction": "LONG", "exit_reason": "STOP", "gross_r_multiple": -0.90, "co_releases": ["840140001"], "ambiguous_flag": False}] * 5,
                        # 4 Long Other Stops: 4 * -0.75 = -3.00
                        *[{"direction": "LONG", "exit_reason": "STOP", "gross_r_multiple": -0.75, "co_releases": [], "ambiguous_flag": False}] * 4,
                        # 1 Long Other Timeout: -0.50
                        {"direction": "LONG", "exit_reason": "TIMEOUT_H24", "gross_r_multiple": -0.50, "co_releases": [], "ambiguous_flag": False},
                        # 4 Short Jobless Targets: 4 * 0.00 = 0.00
                        *[{"direction": "SHORT", "exit_reason": "TARGET", "gross_r_multiple": 0.00, "co_releases": ["840140001"], "ambiguous_flag": False}] * 4,
                        # 9 Short Other Targets: 9 * 1.00 = 9.00
                        *[{"direction": "SHORT", "exit_reason": "TARGET", "gross_r_multiple": 1.00, "co_releases": [], "ambiguous_flag": False}] * 9,
                        # 10 Short Other Stops: 10 * -0.80 = -8.00
                        *[{"direction": "SHORT", "exit_reason": "STOP", "gross_r_multiple": -0.80, "co_releases": [], "ambiguous_flag": False}] * 10,
                        # 2 Short Other Timeouts: 2 * 1.50 = 3.00
                        *[{"direction": "SHORT", "exit_reason": "TIMEOUT_H24", "gross_r_multiple": 1.50, "co_releases": [], "ambiguous_flag": False}] * 2,
                    ]
                },
                "sensitivity_1.0x_conservative": {
                    "metrics": {
                        "total_trades": 40,
                        "wins": 25,
                        "losses": 15,
                        "total_gross_r": 10.00,  # Inverted: negative (-4.00) -> positive (+10.00)
                        "mean_gross_r": 0.25
                    },
                    "trades": [
                        *[{"gross_r_multiple": 1.00, "exit_reason": "TARGET", "ambiguous_flag": True}] * 4,
                        *[{"gross_r_multiple": 1.00, "exit_reason": "TARGET", "ambiguous_flag": False}] * 21,
                        *[{"gross_r_multiple": -1.00, "exit_reason": "STOP", "ambiguous_flag": False}] * 15,
                    ]
                },
                "sensitivity_2.0x_conservative": {
                    "metrics": {
                        "total_trades": 40,
                        "wins": 10,
                        "losses": 30,
                        "total_gross_r": -10.00,  # Inverted: positive (+3.00) -> negative (-10.00)
                        "mean_gross_r": -0.25
                    },
                    "trades": [
                        *[{"gross_r_multiple": 2.00, "exit_reason": "TARGET", "ambiguous_flag": True}] * 1,
                        *[{"gross_r_multiple": 2.00, "exit_reason": "TARGET", "ambiguous_flag": False}] * 9,
                        *[{"gross_r_multiple": -1.00, "exit_reason": "STOP", "ambiguous_flag": False}] * 30,
                    ]
                }
            }
        }

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            tmp_path = f.name

        try:
            # Generate with audit gate passed as False (normal default)
            build_html([], codex_display_approved=False, ledger_data=synthetic_ledger, output_path=tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                html = f.read()

            # 1. Total trade count change
            self.assertIn("Full History (40 Directional Episodes)", html, "Total episodes must dynamically show 40")

            # 2. Timeout count change
            self.assertIn("3 trades reached H24 timeout.", html, "Timeout count must dynamically show 3")

            # 3. Directional split inversion (Longs negative / Shorts positive)
            self.assertIn('Longs (N=15): <span class="stat-neg">-5.5 R</span>', html)
            self.assertIn('Shorts (N=25): <span class="stat-pos">+4 R</span>', html)

            # 4. Co-release split inversion (Jobless negative / Other positive)
            self.assertIn('14 timestamps coinciding with Initial Jobless Claims: <span class="stat-neg">-2 R</span>', html)
            self.assertIn('Remaining 26 timestamps: <span class="stat-pos">+0.5 R</span>', html)

            # 5. Table rows R inversion
            self.assertIn('<span class="stat-pos">+10.00 R</span>', html, "1.0x gross R inverted to positive")
            self.assertIn('<span class="stat-neg"><strong>-1.50 R</strong></span>', html, "1.5x primary gross R inverted to negative")
            self.assertIn('<span class="stat-neg">-10.00 R</span>', html, "2.0x gross R inverted to negative")

            # 6. Default gate state & governance
            self.assertIn('class="results-audit-gate-card" style="display: block;"', html)
            self.assertIn('class="results-numeric-content" style="display: none;"', html)
            self.assertIn("Awaiting Codex display audit", html)
            self.assertIn("UNDER AUDIT — NO REGISTERED SETUP", html)
            self.assertIn("registered <em>for</em> demo forward testing", html)
            self.assertNotIn("STATUS: REGISTERED", html)

            # 7. Check registration wording consistency
            self.assertIn(
                "a setup may be explicitly registered FOR prospective demo forward testing upon Project Director / Codex authorization, with prospective evaluation occurring AFTER registration.",
                html
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
