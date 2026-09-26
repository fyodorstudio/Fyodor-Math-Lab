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
9. Fail-closed behavior (s=0, NaN/inf, undefined stats, sample count mismatch).
10. Strict safety guard prohibiting reading pinned candidate candles without explicit authorization.

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
    HARD_SPLIT_TIMESTAMP,
    HEADLINE_EVENT_ID,
    EURUSD_PIP_SIZE,
    COST_SCENARIOS,
    FROZEN_ISM_TOTAL_PRE2023,
    FROZEN_ISM_COMPLETE_AFP,
    FROZEN_ISM_INCOMPLETE,
    FROZEN_ISM_ACTIONABLE,
    FROZEN_ISM_POSITIVE_SURPRISE,
    FROZEN_ISM_NEGATIVE_SURPRISE,
    FROZEN_ISM_ZERO_SURPRISE,
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
        base_ts = 1500000000  # arbitrary pre-2023 timestamp

        # Create 24 consecutive H1 candles
        bars = []
        for i in range(24):
            ts = base_ts + i * SECONDS_IN_H1
            # Entry open at 1.10000, final close at 1.09000 (drop of 100 pips)
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
        res_short = runner.execute_from_fixtures(pkg_short, price_index, expected_sample_size=None)
        ep_short = res_short["primary_24h1_results"]["episodes"][0]
        self.assertAlmostEqual(ep_short["gross_pips"], 100.0, places=5)
        # Scenario C net pips = 100.0 - 1.0 = 99.0
        self.assertAlmostEqual(ep_short["net_pips_by_scenario"]["Scenario_C"], 99.0, places=5)

        # 2. Dovish Long EURUSD: entry open 1.10000, exit close 1.09000 -> price dropped 100 pips -> -100 gross pips
        pkg_long = [{
            "timestamp": base_ts - SECONDS_IN_H1,
            "entry_timestamp": base_ts,
            "direction": 1,
            "direction_label": "LONG_EURUSD",
            "weekday": "Tuesday"
        }]
        res_long = runner.execute_from_fixtures(pkg_long, price_index, expected_sample_size=None)
        ep_long = res_long["primary_24h1_results"]["episodes"][0]
        self.assertAlmostEqual(ep_long["gross_pips"], -100.0, places=5)
        # Scenario C net pips = -100.0 - 1.0 = -101.0
        self.assertAlmostEqual(ep_long["net_pips_by_scenario"]["Scenario_C"], -101.0, places=5)

    def test_cost_deducted_once_across_scenarios(self):
        """
        Verifies that fixed friction is deducted exactly ONCE directly from gross pips.
        """
        runner = IsmCalculationRunner()
        base_ts = 1500000000

        # Construct 24 bars: Open 1.10000, Close 1.10500 (+50 pips for Long)
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
        res = runner.execute_from_fixtures(pkg, price_index, expected_sample_size=None)
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
        Friday 2021-10-01 18:00 (timestamp 1633111200):
        - Friday bars: 18:00, 19:00, 20:00, 21:00, 22:00 (5 bars: 1633111200 to 1633125600)
        - Weekend gap: Friday 23:00 to Sunday 23:00 (timestamp 1633129200 -> 1633302000, 48h gap)
        - Sunday/Monday bars: 19 bars from Sunday 23:00 (1633302000 to 1633366800)
        Total 24 active bars.
        """
        runner = IsmCalculationRunner()
        fri_entry_ts = 1633111200  # 2021-10-01 18:00:00 UTC (Friday)

        bars = []
        # 5 Friday bars (18:00, 19:00, 20:00, 21:00, 22:00)
        for i in range(5):
            ts = fri_entry_ts + i * SECONDS_IN_H1
            bars.append(create_synthetic_candle(ts, 1.16000, 1.16000))

        # Sunday 23:00 resume
        sun_resume_ts = 1633302000  # 2021-10-03 23:00:00 UTC (Sunday 23:00)
        # 19 Sunday/Monday bars
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
        Tests that an arbitrary weekday gap (e.g. Wednesday 18:00 to Friday 18:00 missing Thursday)
        is rejected by resolve_active_h1_path.
        """
        # Wednesday 2021-09-29 18:00:00 UTC
        wed_entry_ts = 1632938400
        bars = []
        for i in range(5):
            bars.append(create_synthetic_candle(wed_entry_ts + i * SECONDS_IN_H1, 1.16000, 1.16000))
        # Jump 48 hours to Friday
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
        1. A bar at or beyond split timestamp cannot be added to CandlePriceIndex.
        2. A trade whose 24th active bar opens at 1672527600 (2022-12-31 23:00:00)
           has exit close at 1672531200 <= 1672531200 -> VALID.
        3. A trade whose 24th active bar opens at 1672531200 has exit close at 1672534800 > split -> REJECTED.
        """
        # 1. Bar at split rejected
        with self.assertRaises(PermissionError):
            CandlePriceIndex.from_bars([create_synthetic_candle(HARD_SPLIT_TIMESTAMP, 1.05000, 1.05000)])

        # 2. 24 bars ending exactly at 2022-12-31 23:00:00 (ts = 1672531200 - 3600 = 1672527600)
        # Entry starts 23 hours earlier at 1672527600 - 23 * 3600 = 1672444800
        start_ts = HARD_SPLIT_TIMESTAMP - 24 * SECONDS_IN_H1
        valid_bars = [create_synthetic_candle(start_ts + i * SECONDS_IN_H1, 1.05000, 1.05000) for i in range(24)]
        valid_index = CandlePriceIndex.from_bars(valid_bars)
        resolved, _ = valid_index.resolve_active_h1_path(start_ts, num_bars=24)
        self.assertEqual(len(resolved), 24)
        self.assertEqual(resolved[-1].timestamp + SECONDS_IN_H1, HARD_SPLIT_TIMESTAMP)

        # 3. Path whose exit close exceeds split:
        # If we have 23 bars before split, resolving 24 bars raises ValueError due to insufficient bars
        with self.assertRaises(ValueError):
            valid_index.resolve_active_h1_path(start_ts + SECONDS_IN_H1, num_bars=24)

    def test_sample_accounting_from_synthetic_calendar(self):
        """
        Tests load_ism_packages_from_calendar_csv on a synthetic CSV containing:
        - 96 releases total
        - 29 incomplete (missing forecast)
        - 67 complete A/F/P: 28 positive, 38 negative, 1 zero surprise
        - 66 actionable (zero surprise excluded)
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write("event_id,timestamp,timestamp_server_text,actual_raw_scaled_1e6,forecast_raw_scaled_1e6,previous_raw_scaled_1e6\n")

            base_ts = 1420070400  # 2015-01-01 UTC
            step_ts = 25 * 86400  # ~25 days apart
            # 29 incomplete
            for i in range(29):
                ts = base_ts + i * step_ts
                tmp.write(f"{HEADLINE_EVENT_ID},{ts},date_{i},50000000,,49000000\n")

            # 28 positive surprises
            for i in range(28):
                ts = base_ts + (29 + i) * step_ts
                tmp.write(f"{HEADLINE_EVENT_ID},{ts},date_{29+i},55000000,50000000,49000000\n")

            # 38 negative surprises
            for i in range(38):
                ts = base_ts + (29 + 28 + i) * step_ts
                tmp.write(f"{HEADLINE_EVENT_ID},{ts},date_{57+i},45000000,50000000,49000000\n")

            # 1 zero surprise
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
            # Check directions
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
        expected_p_1sided = float(1.0 - stats.t.cdf(expected_t, df=n - 1))
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
        Tests that every mathematical scenario maps to exactly one mutually exclusive case:
        - Case 1: mean_gross <= 0 -> DISCONFIRMED_ADVERSE
        - Case 2: mean_gross > 0 and mean_net_c <= 0 -> INCONCLUSIVE_FRICTION_DECAY
        - Case 3: mean_net_c > 0 and p >= 0.10 -> INCONCLUSIVE_INSUFFICIENT_EVIDENCE
        - Case 4: mean_net_c > 0 and 0.05 <= p < 0.10 -> INCONCLUSIVE_FRAGILE
        - Case 5: mean_net_c > 0 and p < 0.05 -> PROMISING_DISCOVERY_CANDIDATE
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
        # Zero variance: s=0.0
        fc_zero_var = classify_ism_discovery_outcome(
            mean_gross_pips=5.0, mean_net_pips_c=4.0, p_value_c=0.01, sample_std_c=0.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(fc_zero_var["disposition"], "FAIL_CLOSED_INVALID")
        self.assertFalse(fc_zero_var["is_promising"])

        # NaN return
        fc_nan = classify_ism_discovery_outcome(
            mean_gross_pips=float("nan"), mean_net_pips_c=4.0, p_value_c=0.01, sample_std_c=10.0,
            sample_size=66, expected_sample_size=66
        )
        self.assertEqual(fc_nan["disposition"], "FAIL_CLOSED_INVALID")
        self.assertFalse(fc_nan["is_promising"])

        # Sample size mismatch (e.g. 50 instead of 66)
        fc_mismatch = classify_ism_discovery_outcome(
            mean_gross_pips=5.0, mean_net_pips_c=4.0, p_value_c=0.01, sample_std_c=10.0,
            sample_size=50, expected_sample_size=66
        )
        self.assertEqual(fc_mismatch["disposition"], "FAIL_CLOSED_INVALID")
        self.assertFalse(fc_mismatch["is_promising"])

        # compute_pip_statistics on identical values (zero variance)
        res_zero = compute_pip_statistics([5.0] * 20)
        self.assertFalse(res_zero["is_valid"])
        self.assertIn("Zero sample variance", res_zero["error"])

        # compute_pip_statistics on sample with NaN
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


if __name__ == "__main__":
    unittest.main()
