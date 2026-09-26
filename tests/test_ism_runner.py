"""
Synthetic Unit Tests for Pre-2023 ISM PMI Calculation Runner
Verifies:
1. Both trade directions (Hawkish/Short EURUSD, Dovish/Long EURUSD).
2. Cost deducted once (Scenario C 1.0 pip = 10 pts, minus fixed friction once).
3. 24-active-H1 path stepping across valid weekend market closures.
4. Adversarial weekday gap rejection.
5. Split boundary exit-close convention (exit close <= 1672531200).
6. Sample accounting on synthetic calendar packages (96 total, 67 complete, 66 actionable, 1 zero excluded).
7. One-sample t-test, p-value, and confidence interval arithmetic.
8. Every mutually exclusive decision category (Cases 1 through 5).
9. Fail-closed boundary behavior (s=0, NaN/inf, undefined stats, sample count mismatch).
10. Strict safety guard prohibiting reading pinned candidate candles without explicit authorization.
11. 1-pip break-even case with exact integer-point safe arithmetic.
12. scipy.stats.t.sf survival function for one-sided p-value precision.
13. Descriptive 48-H1 fails closed on broken or missing paths (no silent omission).
14. Preflight rejects bad calendar SHA-256 before reading candles.
15. Preflight rejects bad candle SHA-256 before parsing prices.
16. Preflight rejects calendar count mismatches before parsing prices.
17. Preflight rejects missing, uncommitted, pending, or commit-mismatched freeze packets.
18. Preflight rejects dirty implementation state.
19. End-to-end synthetic CSV test of execute_from_paths with post-split malformed sentinel.
20. Immutable output behavior: rejects overwriting an existing discovery artifact.

Zero empirical candidate candle prices are parsed or executed in this test suite.
"""

import unittest
import math
import tempfile
import os
from datetime import datetime, timezone
from scipy import stats

from src.ism_runner import (
    CandleBar,
    CandlePriceIndex,
    IsmCalculationRunner,
    load_ism_packages_from_calendar_csv,
    compute_pip_statistics,
    classify_ism_discovery_outcome,
    preflight_verification,
    verify_freeze_packet_authorization,
    HARD_SPLIT_TIMESTAMP,
    HEADLINE_EVENT_ID,
    EURUSD_POINT,
    EURUSD_POINTS_PER_PIP,
    EURUSD_PIP_SIZE,
    COST_SCENARIOS,
    COST_SCENARIOS_POINTS,
    FROZEN_ISM_TOTAL_PRE2023,
    FROZEN_ISM_COMPLETE_AFP,
    FROZEN_ISM_INCOMPLETE,
    FROZEN_ISM_ACTIONABLE,
    FROZEN_ISM_POSITIVE_SURPRISE,
    FROZEN_ISM_NEGATIVE_SURPRISE,
    FROZEN_ISM_ZERO_SURPRISE,
    EXPECTED_PINNED_SOURCES,
    PROTOCOL_REFERENCE
)
from src.candle_coverage import SECONDS_IN_H1


def create_synthetic_candle(ts: int, open_p: float, close_p: float, spread: int = 10) -> CandleBar:
    high_p = max(open_p, close_p) + 0.0005
    low_p = min(open_p, close_p) - 0.0005
    return CandleBar(
        timestamp=ts,
        open=open_p,
        high=high_p,
        low=low_p,
        close=close_p,
        spread=spread,
        tick_volume=100,
        real_volume=0
    )


class TestIsmRunner(unittest.TestCase):

    def test_both_trade_directions(self):
        """
        Tests directional return arithmetic for both directions:
        - Hawkish shock (S_H > 0): Short EURUSD (direction = -1).
          If close < open, profit is positive.
        - Dovish shock (S_H < 0): Long EURUSD (direction = +1).
          If close > open, profit is positive.
        """
        runner = IsmCalculationRunner()
        base_ts = 1500000000

        bars = []
        for i in range(24):
            ts = base_ts + i * SECONDS_IN_H1
            o = 1.10000 if i == 0 else 1.09500
            c = 1.09000 if i == 23 else 1.09500
            bars.append(create_synthetic_candle(ts, o, c))

        price_index = CandlePriceIndex.from_bars(bars)

        # 1. Hawkish Short EURUSD: entry open 1.10000, exit close 1.09000 -> price dropped 100 pips -> +100 gross pips
        pkg_short = [{
            "timestamp": base_ts - SECONDS_IN_H1,
            "entry_timestamp": base_ts,
            "direction": -1,
            "direction_label": "SHORT_EURUSD",
            "weekday": "Tuesday"
        }]
        res_short = runner.execute_from_fixtures(
            pkg_short, price_index, expected_sample_size=None, require_48h1_completeness=False
        )
        ep_short = res_short["primary_24h1_results"]["episodes"][0]
        self.assertAlmostEqual(ep_short["gross_pips"], 100.0, places=5)
        self.assertAlmostEqual(ep_short["net_pips_by_scenario"]["Scenario_C"], 99.0, places=5)

        # 2. Dovish Long EURUSD: entry open 1.10000, exit close 1.09000 -> price dropped 100 pips -> -100 gross pips
        pkg_long = [{
            "timestamp": base_ts - SECONDS_IN_H1,
            "entry_timestamp": base_ts,
            "direction": 1,
            "direction_label": "LONG_EURUSD",
            "weekday": "Tuesday"
        }]
        res_long = runner.execute_from_fixtures(
            pkg_long, price_index, expected_sample_size=None, require_48h1_completeness=False
        )
        ep_long = res_long["primary_24h1_results"]["episodes"][0]
        self.assertAlmostEqual(ep_long["gross_pips"], -100.0, places=5)
        self.assertAlmostEqual(ep_long["net_pips_by_scenario"]["Scenario_C"], -101.0, places=5)

    def test_cost_deducted_once_across_scenarios(self):
        """
        Verifies that fixed friction is deducted exactly ONCE directly from gross pips.
        """
        runner = IsmCalculationRunner()
        base_ts = 1500000000

        bars = []
        for i in range(24):
            ts = base_ts + i * SECONDS_IN_H1
            o = 1.10000 if i == 0 else 1.10200
            c = 1.10500 if i == 23 else 1.10200
            bars.append(create_synthetic_candle(ts, o, c))

        price_index = CandlePriceIndex.from_bars(bars)
        pkg = [{
            "timestamp": base_ts - SECONDS_IN_H1,
            "entry_timestamp": base_ts,
            "direction": 1,
            "direction_label": "LONG_EURUSD",
            "weekday": "Wednesday"
        }]
        res = runner.execute_from_fixtures(
            pkg, price_index, expected_sample_size=None, require_48h1_completeness=False
        )
        ep = res["primary_24h1_results"]["episodes"][0]

        gross = ep["gross_pips"]
        self.assertAlmostEqual(gross, 50.0, places=5)
        self.assertAlmostEqual(ep["net_pips_by_scenario"]["Scenario_A"], 50.0 - 0.0, places=5)
        self.assertAlmostEqual(ep["net_pips_by_scenario"]["Scenario_B"], 50.0 - 0.5, places=5)
        self.assertAlmostEqual(ep["net_pips_by_scenario"]["Scenario_C"], 50.0 - 1.0, places=5)
        self.assertAlmostEqual(ep["net_pips_by_scenario"]["Scenario_D"], 50.0 - 2.0, places=5)
        self.assertAlmostEqual(ep["net_pips_by_scenario"]["Scenario_E"], 50.0 - 3.0, places=5)

    def test_24_active_h1_path_crossing_valid_weekend(self):
        """
        Tests resolving 24 active H1 bars across a Friday-to-Sunday weekend closure.
        """
        fri_entry_ts = 1633111200  # 2021-10-01 18:00:00 UTC (Friday)

        bars = []
        for i in range(5):
            ts = fri_entry_ts + i * SECONDS_IN_H1
            bars.append(create_synthetic_candle(ts, 1.16000, 1.16000))

        sun_resume_ts = 1633302000  # 2021-10-03 23:00:00 UTC (Sunday 23:00)
        for i in range(19):
            ts = sun_resume_ts + i * SECONDS_IN_H1
            bars.append(create_synthetic_candle(ts, 1.16000, 1.16000))

        self.assertEqual(len(bars), 24)
        price_index = CandlePriceIndex.from_bars(bars)

        resolved_bars, crosses_weekend = price_index.resolve_active_h1_path(fri_entry_ts, num_bars=24)
        self.assertEqual(len(resolved_bars), 24)
        self.assertTrue(crosses_weekend)
        self.assertEqual(resolved_bars[0].timestamp, fri_entry_ts)
        self.assertEqual(resolved_bars[4].timestamp, fri_entry_ts + 4 * SECONDS_IN_H1)
        self.assertEqual(resolved_bars[5].timestamp, sun_resume_ts)
        self.assertEqual(resolved_bars[23].timestamp, sun_resume_ts + 18 * SECONDS_IN_H1)

    def test_invalid_weekday_gap_rejection(self):
        """
        Tests that an arbitrary weekday gap is rejected by resolve_active_h1_path.
        """
        wed_entry_ts = 1632938400
        bars = []
        for i in range(5):
            bars.append(create_synthetic_candle(wed_entry_ts + i * SECONDS_IN_H1, 1.16000, 1.16000))
        fri_ts = wed_entry_ts + 5 * SECONDS_IN_H1 + 48 * SECONDS_IN_H1
        for i in range(19):
            bars.append(create_synthetic_candle(fri_ts + i * SECONDS_IN_H1, 1.16000, 1.16000))

        price_index = CandlePriceIndex.from_bars(bars)
        with self.assertRaises(ValueError) as ctx:
            price_index.resolve_active_h1_path(wed_entry_ts, num_bars=24)
        self.assertIn("Invalid gap", str(ctx.exception))

    def test_split_boundary_exit_close_handling(self):
        """
        Tests strict split boundary exit close constraint:
        SPLIT_TIMESTAMP = 1672531200 (2023-01-01 00:00:00 broker server time).
        """
        with self.assertRaises(PermissionError):
            CandlePriceIndex.from_bars([create_synthetic_candle(HARD_SPLIT_TIMESTAMP, 1.05000, 1.05000)])

        start_ts = HARD_SPLIT_TIMESTAMP - 24 * SECONDS_IN_H1
        valid_bars = [create_synthetic_candle(start_ts + i * SECONDS_IN_H1, 1.05000, 1.05000) for i in range(24)]
        valid_index = CandlePriceIndex.from_bars(valid_bars)
        resolved, _ = valid_index.resolve_active_h1_path(start_ts, num_bars=24)
        self.assertEqual(len(resolved), 24)
        self.assertEqual(resolved[-1].timestamp + SECONDS_IN_H1, HARD_SPLIT_TIMESTAMP)

        with self.assertRaises(ValueError):
            valid_index.resolve_active_h1_path(start_ts + SECONDS_IN_H1, num_bars=24)

    def test_sample_accounting_from_synthetic_calendar(self):
        """
        Tests load_ism_packages_from_calendar_csv on a synthetic CSV.
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write("event_id,timestamp,timestamp_server_text,actual_raw_scaled_1e6,forecast_raw_scaled_1e6,previous_raw_scaled_1e6\n")

            base_ts = 1420070400  # 2015-01-01 UTC
            step_ts = 25 * 86400  # ~25 days apart
            for i in range(29):
                ts = base_ts + i * step_ts
                tmp.write(f"{HEADLINE_EVENT_ID},{ts},date_{i},50000000,,49000000\n")

            for i in range(28):
                ts = base_ts + (29 + i) * step_ts
                tmp.write(f"{HEADLINE_EVENT_ID},{ts},date_{29+i},55000000,50000000,49000000\n")

            for i in range(38):
                ts = base_ts + (29 + 28 + i) * step_ts
                tmp.write(f"{HEADLINE_EVENT_ID},{ts},date_{57+i},45000000,50000000,49000000\n")

            ts_zero = base_ts + 95 * step_ts
            tmp.write(f"{HEADLINE_EVENT_ID},{ts_zero},date_95,50000000,50000000,49000000\n")

        try:
            cal_data = load_ism_packages_from_calendar_csv(tmp_path, split_timestamp=HARD_SPLIT_TIMESTAMP)
            acc = cal_data["sample_accounting"]
            self.assertEqual(acc["total_pre2023_releases"], 96)
            self.assertEqual(acc["complete_afp_releases"], 67)
            self.assertEqual(acc["missing_forecast_releases"], 29)
            self.assertEqual(acc["positive_surprises"], 28)
            self.assertEqual(acc["negative_surprises"], 38)
            self.assertEqual(acc["zero_surprises"], 1)
            self.assertEqual(acc["actionable_releases"], 66)

            actionable = cal_data["actionable_packages"]
            self.assertEqual(len(actionable), 66)
            for p in actionable[:28]:
                self.assertEqual(p["direction"], -1)
                self.assertEqual(p["direction_label"], "SHORT_EURUSD")
            for p in actionable[28:]:
                self.assertEqual(p["direction"], 1)
                self.assertEqual(p["direction_label"], "LONG_EURUSD")

            zeros = cal_data["zero_surprise_packages"]
            self.assertEqual(len(zeros), 1)
            self.assertEqual(zeros[0]["direction"], 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_pip_statistics_and_confidence_interval_arithmetic(self):
        """
        Tests compute_pip_statistics against exact scipy.stats calculations.
        """
        sample = [12.5, -4.0, 8.2, 15.1, -1.0, 6.4, 22.0, -8.5, 11.2, 5.0]
        n = len(sample)
        expected_mean = sum(sample) / n
        expected_var = sum((x - expected_mean) ** 2 for x in sample) / (n - 1)
        expected_std = math.sqrt(expected_var)
        expected_se = expected_std / math.sqrt(n)
        expected_t = expected_mean / expected_se
        expected_p_1sided = float(stats.t.sf(expected_t, df=n - 1))
        expected_ci_2sided_lower = expected_mean - float(stats.t.ppf(0.975, df=n - 1)) * expected_se
        expected_ci_2sided_upper = expected_mean + float(stats.t.ppf(0.975, df=n - 1)) * expected_se

        res = compute_pip_statistics(sample)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["sample_size"], n)
        self.assertAlmostEqual(res["mean_pips"], expected_mean, places=6)
        self.assertAlmostEqual(res["std_dev"], expected_std, places=6)
        self.assertAlmostEqual(res["std_error"], expected_se, places=6)
        self.assertAlmostEqual(res["t_statistic"], expected_t, places=6)
        self.assertAlmostEqual(res["p_value_1sided"], expected_p_1sided, places=6)
        self.assertAlmostEqual(res["ci_2sided_lower"], expected_ci_2sided_lower, places=6)
        self.assertAlmostEqual(res["ci_2sided_upper"], expected_ci_2sided_upper, places=6)
        self.assertEqual(res["win_count"], 7)
        self.assertAlmostEqual(res["win_rate"], 0.70, places=6)

    def test_mutually_exclusive_decision_categories(self):
        """
        Tests that every mathematical scenario maps to exactly one mutually exclusive case.
        """
        # Case 1: mean gross <= 0.0
        c1 = classify_ism_discovery_outcome(
            mean_gross_pips=-0.5, mean_net_pips_c=-1.5, p_value_c=0.85, sample_std_c=10.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(c1["case_id"], "Case 1")
        self.assertEqual(c1["disposition"], "DISCONFIRMED_ADVERSE")
        self.assertFalse(c1["is_promising"])

        # Case 2: mean gross > 0.0 but mean net c <= 0.0
        c2 = classify_ism_discovery_outcome(
            mean_gross_pips=0.6, mean_net_pips_c=-0.4, p_value_c=0.65, sample_std_c=10.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(c2["case_id"], "Case 2")
        self.assertEqual(c2["disposition"], "INCONCLUSIVE_FRICTION_DECAY")
        self.assertFalse(c2["is_promising"])

        # Case 3: mean net c > 0.0 and p >= 0.10 (insufficient evidence)
        c3 = classify_ism_discovery_outcome(
            mean_gross_pips=2.5, mean_net_pips_c=1.5, p_value_c=0.15, sample_std_c=12.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(c3["case_id"], "Case 3")
        self.assertEqual(c3["disposition"], "INCONCLUSIVE_INSUFFICIENT_EVIDENCE")
        self.assertFalse(c3["is_promising"])

        # Case 4: mean net c > 0.0 and 0.05 <= p < 0.10 (fragile)
        c4 = classify_ism_discovery_outcome(
            mean_gross_pips=3.2, mean_net_pips_c=2.2, p_value_c=0.07, sample_std_c=11.5,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(c4["case_id"], "Case 4")
        self.assertEqual(c4["disposition"], "INCONCLUSIVE_FRAGILE")
        self.assertFalse(c4["is_promising"])

        # Case 5: mean net c > 0.0 and p < 0.05 (promising candidate)
        c5 = classify_ism_discovery_outcome(
            mean_gross_pips=5.0, mean_net_pips_c=4.0, p_value_c=0.012, sample_std_c=13.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(c5["case_id"], "Case 5")
        self.assertEqual(c5["disposition"], "PROMISING_DISCOVERY_CANDIDATE")
        self.assertTrue(c5["is_promising"])

    def test_fail_closed_boundary_behavior(self):
        """
        Tests that zero variance, NaN/inf, undefined stats, and sample count mismatches
        fail closed and NEVER evaluate to PROMISING_DISCOVERY_CANDIDATE.
        """
        fc_zero_var = classify_ism_discovery_outcome(
            mean_gross_pips=5.0, mean_net_pips_c=4.0, p_value_c=0.01, sample_std_c=0.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(fc_zero_var["disposition"], "FAIL_CLOSED_INVALID")
        self.assertFalse(fc_zero_var["is_promising"])

        fc_nan = classify_ism_discovery_outcome(
            mean_gross_pips=float("nan"), mean_net_pips_c=4.0, p_value_c=0.01, sample_std_c=10.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(fc_nan["disposition"], "FAIL_CLOSED_INVALID")
        self.assertFalse(fc_nan["is_promising"])

        fc_mismatch = classify_ism_discovery_outcome(
            mean_gross_pips=5.0, mean_net_pips_c=4.0, p_value_c=0.01, sample_std_c=10.0,
            sample_size=50, expected_sample_size=66
        )
        self.assertEqual(fc_mismatch["disposition"], "FAIL_CLOSED_INVALID")
        self.assertFalse(fc_mismatch["is_promising"])

        res_zero = compute_pip_statistics([5.0] * 20)
        self.assertFalse(res_zero["is_valid"])
        self.assertIn("Zero sample variance", res_zero["error"])

        res_nan = compute_pip_statistics([1.0, 2.0, float("nan"), 4.0])
        self.assertFalse(res_nan["is_valid"])
        self.assertIn("non-finite", res_nan["error"])

    def test_safety_guard_prohibits_reading_pinned_candidate_candles(self):
        """
        Verifies that CandlePriceIndex.from_csv and IsmCalculationRunner.execute_from_paths
        refuse to read pinned candidate candles when allow_unblinded_run=False.
        """
        pinned_path = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv"
        with self.assertRaises(PermissionError) as ctx:
            CandlePriceIndex.from_csv(pinned_path, allow_unblinded_run=False)
        self.assertIn("Unblinded empirical execution", str(ctx.exception))

        runner = IsmCalculationRunner()
        with self.assertRaises(PermissionError):
            runner.execute_from_paths(
                calendar_path="data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv",
                candle_path=pinned_path,
                allow_unblinded_run=False
            )

    def test_break_even_1pip_point_safe_arithmetic(self):
        """
        Tests the 1-pip break-even case with exact integer broker point arithmetic.
        Verifies that a move of exactly 10 broker points (1.0 pip) generates exactly 0.0 net pips
        under Scenario C, and is strictly NOT classified as a win.
        """
        runner = IsmCalculationRunner()
        base_ts = 1500000000

        # Create 24 bars: Open 1.10010, Close 1.10000 (drop of 10 points / 1 pip)
        bars = []
        for i in range(24):
            ts = base_ts + i * SECONDS_IN_H1
            o = 1.10010 if i == 0 else 1.10005
            c = 1.10000 if i == 23 else 1.10005
            bars.append(create_synthetic_candle(ts, o, c))

        price_index = CandlePriceIndex.from_bars(bars)

        # 1. Hawkish Short: direction = -1
        # Gross points = (-1) * (110000 - 110010) = +10 points = 1.0 pip
        # Scenario C net points = 10 - 10 = 0 points = 0.0 pips
        pkg_short = [{
            "timestamp": base_ts - SECONDS_IN_H1,
            "entry_timestamp": base_ts,
            "direction": -1,
            "direction_label": "SHORT_EURUSD",
            "weekday": "Monday"
        }]
        res = runner.execute_from_fixtures(
            pkg_short, price_index, expected_sample_size=None, require_48h1_completeness=False
        )
        ep = res["primary_24h1_results"]["episodes"][0]
        self.assertEqual(ep["gross_pips"], 1.0)
        self.assertEqual(ep["net_pips_by_scenario"]["Scenario_C"], 0.0)
        self.assertFalse(ep["is_win_scenario_c"])

        # 2. Dovish Long: direction = +1
        # Open 1.10000, Close 1.10010 -> +10 points = 1.0 pip
        bars_long = []
        for i in range(24):
            ts = base_ts + i * SECONDS_IN_H1
            o = 1.10000 if i == 0 else 1.10005
            c = 1.10010 if i == 23 else 1.10005
            bars_long.append(create_synthetic_candle(ts, o, c))
        index_long = CandlePriceIndex.from_bars(bars_long)

        pkg_long = [{
            "timestamp": base_ts - SECONDS_IN_H1,
            "entry_timestamp": base_ts,
            "direction": 1,
            "direction_label": "LONG_EURUSD",
            "weekday": "Monday"
        }]
        res_l = runner.execute_from_fixtures(
            pkg_long, index_long, expected_sample_size=None, require_48h1_completeness=False
        )
        ep_l = res_l["primary_24h1_results"]["episodes"][0]
        self.assertEqual(ep_l["gross_pips"], 1.0)
        self.assertEqual(ep_l["net_pips_by_scenario"]["Scenario_C"], 0.0)
        self.assertFalse(ep_l["is_win_scenario_c"])

        # 3. Test win rate in compute_pip_statistics on [0.0, 1.0, -1.0]
        stats_sample = compute_pip_statistics([0.0, 1.0, -1.0])
        self.assertTrue(stats_sample["is_valid"])
        self.assertEqual(stats_sample["win_count"], 1)  # only 1.0 is a win, 0.0 is break-even
        self.assertAlmostEqual(stats_sample["win_rate"], 1.0 / 3.0, places=6)

    def test_scipy_survival_function_p_value(self):
        """
        Verifies that compute_pip_statistics utilizes scipy.stats.t.sf directly.
        """
        sample = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        res = compute_pip_statistics(sample)
        t_stat = res["t_statistic"]
        expected_sf = float(stats.t.sf(t_stat, df=len(sample) - 1))
        self.assertEqual(res["p_value_1sided"], expected_sf)

    def test_descriptive_48h1_fails_closed_on_broken_path(self):
        """
        Verifies that when require_48h1_completeness=True, any broken or missing 48-H1 path
        fails closed with an error rather than being silently omitted.
        """
        runner = IsmCalculationRunner()
        base_ts = 1500000000

        # Only provide 24 bars, so 48-H1 path is incomplete
        bars = [create_synthetic_candle(base_ts + i * SECONDS_IN_H1, 1.10000, 1.10000) for i in range(24)]
        price_index = CandlePriceIndex.from_bars(bars)

        pkg = [{
            "timestamp": base_ts - SECONDS_IN_H1,
            "entry_timestamp": base_ts,
            "direction": 1,
            "direction_label": "LONG_EURUSD",
            "weekday": "Tuesday"
        }]

        # With require_48h1_completeness=True (default for discovery), must fail closed
        with self.assertRaises(ValueError) as ctx:
            runner.execute_from_fixtures(pkg, price_index, expected_sample_size=None, require_48h1_completeness=True)
        self.assertIn("Insufficient forward active bars", str(ctx.exception))

    def test_preflight_rejects_bad_calendar_sha256(self):
        """
        Verifies preflight rejects calendar file with mismatched SHA-256 before opening candle file.
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as cal_tmp:
            cal_tmp.write("dummy,calendar\n")
            cal_path = cal_tmp.name

        try:
            with self.assertRaises(ValueError) as ctx:
                preflight_verification(
                    calendar_path=cal_path,
                    candle_path="nonexistent_candle.csv",
                    is_synthetic_test=True,
                    expected_calendar_sha256="0000000000000000000000000000000000000000000000000000000000000000"
                )
            self.assertIn("does not match expected approved hash", str(ctx.exception))
        finally:
            if os.path.exists(cal_path):
                os.remove(cal_path)

    def test_preflight_rejects_bad_candle_sha256(self):
        """
        Verifies preflight rejects candle file with mismatched SHA-256 before parsing prices.
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as cal_tmp:
            cal_tmp.write("event_id,timestamp,timestamp_server_text,actual_raw_scaled_1e6,forecast_raw_scaled_1e6,previous_raw_scaled_1e6\n")
            cal_path = cal_tmp.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as candle_tmp:
            candle_tmp.write("time,open,high,low,close\n")
            candle_path = candle_tmp.name

        try:
            from src.ism_runner import compute_file_sha256
            cal_sha = compute_file_sha256(cal_path)

            with self.assertRaises(ValueError) as ctx:
                preflight_verification(
                    calendar_path=cal_path,
                    candle_path=candle_path,
                    is_synthetic_test=True,
                    expected_calendar_sha256=cal_sha,
                    expected_candle_sha256="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                )
            self.assertIn("EURUSD candle file", str(ctx.exception))
            self.assertIn("does not match expected approved hash", str(ctx.exception))
        finally:
            if os.path.exists(cal_path):
                os.remove(cal_path)
            if os.path.exists(candle_path):
                os.remove(candle_path)

    def test_preflight_rejects_bad_calendar_counts(self):
        """
        Verifies preflight rejects calendar with wrong release counts before parsing candle prices.
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as cal_tmp:
            cal_tmp.write("event_id,timestamp,actual_raw_scaled_1e6,forecast_raw_scaled_1e6,previous_raw_scaled_1e6\n")
            cal_tmp.write(f"{HEADLINE_EVENT_ID},1500000000,50000000,48000000,49000000\n")
            cal_path = cal_tmp.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as candle_tmp:
            candle_tmp.write("time,open,high,low,close\n")
            candle_path = candle_tmp.name

        from src.ism_runner import get_implementation_provenance
        prov = get_implementation_provenance()
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".md") as pkt_tmp:
            pkt_tmp.write(
                f"# ISM Freeze Packet\n"
                f"> GOVERNANCE STATUS: AUTHORIZED FOR PRE-2023 DISCOVERY RUN ONLY\n"
                f"Protocol: docs/DRAFT_ISM_PMI_PROTOCOL.md\n"
                f"Runner Commit: {prov['git_head_commit']}\n"
            )
            pkt_path = pkt_tmp.name

        try:
            from src.ism_runner import compute_file_sha256
            cal_sha = compute_file_sha256(cal_path)
            candle_sha = compute_file_sha256(candle_path)

            with self.assertRaises(ValueError) as ctx:
                preflight_verification(
                    calendar_path=cal_path,
                    candle_path=candle_path,
                    is_synthetic_test=False,
                    expected_calendar_sha256=cal_sha,
                    expected_candle_sha256=candle_sha,
                    allow_unblinded_run=True,
                    freeze_packet_path=pkt_path,
                    check_freeze_git=False,
                    force_dirty_check=False
                )
            self.assertIn("calendar sample accounting mismatch", str(ctx.exception))
        finally:
            if os.path.exists(cal_path):
                os.remove(cal_path)
            if os.path.exists(candle_path):
                os.remove(candle_path)
            if os.path.exists(pkt_path):
                os.remove(pkt_path)

    def test_preflight_rejects_missing_or_unapproved_freeze_packet(self):
        """
        Verifies preflight rejects execution without an authorized freeze packet.
        """
        # 1. Bare boolean allow_unblinded_run=True without freeze packet
        with self.assertRaises(PermissionError) as ctx1:
            preflight_verification(
                calendar_path="data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv",
                candle_path="data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv",
                allow_unblinded_run=True,
                freeze_packet_path=None,
                is_synthetic_test=False
            )
        self.assertIn("requires an explicit committed freeze packet", str(ctx1.exception))

        # 2. Non-existent freeze packet
        with self.assertRaises(FileNotFoundError):
            verify_freeze_packet_authorization("nonexistent_freeze_packet.md", check_git_committed=False)

        # 3. Freeze packet with PENDING status
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".md") as pkt_tmp:
            pkt_tmp.write("# ISM Freeze Packet\n> GOVERNANCE STATUS: PENDING APPROVAL\nProtocol: docs/DRAFT_ISM_PMI_PROTOCOL.md\nCommit: b06ce62\n")
            pkt_path = pkt_tmp.name

        try:
            with self.assertRaises(PermissionError) as ctx3:
                verify_freeze_packet_authorization(pkt_path, check_git_committed=False)
            self.assertIn("governance status is not authorized", str(ctx3.exception))
        finally:
            if os.path.exists(pkt_path):
                os.remove(pkt_path)

        # 4. Freeze packet referencing wrong runner commit
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".md") as pkt_tmp2:
            pkt_tmp2.write("# ISM Freeze Packet\n> GOVERNANCE STATUS: AUTHORIZED FOR PRE-2023 DISCOVERY RUN ONLY\nProtocol: docs/DRAFT_ISM_PMI_PROTOCOL.md\nRunner Commit: 0000000\n")
            pkt_path2 = pkt_tmp2.name

        try:
            with self.assertRaises(PermissionError) as ctx4:
                verify_freeze_packet_authorization(
                    pkt_path2,
                    expected_runner_commit="b06ce62",
                    check_git_committed=False
                )
            self.assertIn("does not reference approved runner commit", str(ctx4.exception))
        finally:
            if os.path.exists(pkt_path2):
                os.remove(pkt_path2)

    def test_preflight_rejects_dirty_implementation_state(self):
        """
        Verifies preflight rejects execution when Git working tree is dirty.
        """
        with self.assertRaises(RuntimeError) as ctx:
            preflight_verification(
                calendar_path="dummy.csv",
                candle_path="dummy.csv",
                is_synthetic_test=True,
                force_dirty_check=True
            )
        self.assertIn("Implementation state is dirty", str(ctx.exception))

    def test_end_to_end_synthetic_csv_with_post_split_sentinel(self):
        """
        End-to-end synthetic test of execute_from_paths:
        - Synthetic calendar CSV with actionable packages.
        - Synthetic candle CSV with valid bars covering 48 active hours for all packages,
          followed by a post-split row at 1672531200 containing malformed non-numeric sentinel text.
        - Verifies that execute_from_paths runs completely, outputs deterministic JSON,
          and NEVER parses or converts the post-split price sentinel.
        """
        runner = IsmCalculationRunner()
        base_ts = 1500000000

        # Create synthetic calendar CSV with 2 actionable releases (1 pos, 1 neg)
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as cal_f:
            cal_f.write("event_id,timestamp,timestamp_server_text,actual_raw_scaled_1e6,forecast_raw_scaled_1e6,previous_raw_scaled_1e6\n")
            cal_f.write(f"{HEADLINE_EVENT_ID},{base_ts},date_0,55000000,50000000,49000000\n")
            rel_ts_2 = base_ts + 100 * SECONDS_IN_H1
            cal_f.write(f"{HEADLINE_EVENT_ID},{rel_ts_2},date_1,45000000,50000000,49000000\n")
            cal_csv_path = cal_f.name

        # Create synthetic candle CSV covering both episodes (48 bars each)
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as candle_f:
            candle_f.write("time,open,high,low,close,tick_volume,spread,real_volume\n")

            # Bars for episode 1 (from base_ts + 3600 for 50 bars)
            e1_entry = base_ts + SECONDS_IN_H1
            for i in range(50):
                ts = e1_entry + i * SECONDS_IN_H1
                candle_f.write(f"{ts},1.10000,1.10500,1.09500,1.09800,100,10,0\n")

            # Bars for episode 2 (from rel_ts_2 + 3600 for 50 bars)
            e2_entry = rel_ts_2 + SECONDS_IN_H1
            for i in range(50):
                ts = e2_entry + i * SECONDS_IN_H1
                candle_f.write(f"{ts},1.10000,1.10500,1.09500,1.10200,100,10,0\n")

            # Post-split row with MALFORMED NON-NUMERIC PRICE SENTINEL
            # If the parser ever tokenized or converted columns 1..N of post-split rows,
            # this would raise ValueError: could not convert string to float: 'SENTINEL_NON_NUMERIC'
            candle_f.write(f"{HARD_SPLIT_TIMESTAMP},SENTINEL_OPEN,SENTINEL_HIGH,SENTINEL_LOW,SENTINEL_CLOSE,0,0,0\n")
            candle_csv_path = candle_f.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as out_f:
            out_json_path = out_f.name
        # Remove output file so execute_from_paths can create it cleanly
        os.remove(out_json_path)

        try:
            result = runner.execute_from_paths(
                calendar_path=cal_csv_path,
                candle_path=candle_csv_path,
                allow_unblinded_run=True,
                is_synthetic_test=True,
                output_json_path=out_json_path,
                expected_sample_size=None,
                require_48h1_completeness=True
            )

            # Assert execution succeeded without crashing on the post-split sentinel
            self.assertEqual(result["schema_version"], "1.0.0")
            episodes = result["primary_24h1_results"]["episodes"]
            self.assertEqual(len(episodes), 2)
            self.assertTrue(os.path.isfile(out_json_path))

            # Verify episode 1 arithmetic
            ep1 = episodes[0]
            self.assertEqual(ep1["direction"], -1)
            self.assertEqual(ep1["entry_open_price"], 1.10000)
            self.assertEqual(ep1["exit_close_price"], 1.09800)
            # drop of 20 pips for short -> +20 gross pips
            self.assertEqual(ep1["gross_pips"], 20.0)
            self.assertEqual(ep1["net_pips_by_scenario"]["Scenario_C"], 19.0)
            self.assertTrue(ep1["is_win_scenario_c"])

            # Verify 48-H1 episodes were resolved
            episodes_48 = result["descriptive_48h1_results"]["episodes"]
            self.assertEqual(len(episodes_48), 2)

        finally:
            if os.path.exists(cal_csv_path):
                os.remove(cal_csv_path)
            if os.path.exists(candle_csv_path):
                os.remove(candle_csv_path)
            if os.path.exists(out_json_path):
                os.remove(out_json_path)

    def test_immutable_output_file_cannot_be_overwritten(self):
        """
        Verifies that execute_from_paths raises FileExistsError if the output file already exists.
        """
        runner = IsmCalculationRunner()
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as out_tmp:
            out_tmp.write('{"existing": "record"}\n')
            out_path = out_tmp.name

        try:
            with self.assertRaises(FileExistsError) as ctx:
                runner.execute_from_paths(
                    calendar_path="dummy_cal.csv",
                    candle_path="dummy_candle.csv",
                    is_synthetic_test=True,
                    output_json_path=out_path
                )
            self.assertIn("already exists", str(ctx.exception))
            self.assertIn("Overwriting discovery artifacts is strictly prohibited", str(ctx.exception))
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)


if __name__ == "__main__":
    unittest.main()
