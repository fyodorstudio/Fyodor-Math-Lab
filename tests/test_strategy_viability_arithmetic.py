"""
Synthetic Unit Tests for Strategy Viability Arithmetic
Verifies trade bid-ask mechanics, cost scenario deductions, 1-sample statistics,
and decision gate classification using small, hand-checkable synthetic examples.

Zero reading of candidate prices or holdout candle files.
"""

import unittest
import math
import os
import csv

from src.strategy_viability import (
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

PINNED_CANDLE_SYMBOLS_PATH = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candle_symbols.csv"


class TestStrategyViabilityArithmetic(unittest.TestCase):

    def test_provenance_and_constants(self):
        """Verifies point and pip conventions against pinned export metadata."""
        self.assertEqual(EURUSD_DIGITS, 5)
        self.assertEqual(EURUSD_POINT, 0.00001)
        self.assertEqual(EURUSD_POINTS_PER_PIP, 10)

        # Verify against candle_symbols.csv if present
        if os.path.exists(PINNED_CANDLE_SYMBOLS_PATH):
            with open(PINNED_CANDLE_SYMBOLS_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                eurusd_rows = [r for r in reader if r.get("canonical_symbol") == "EURUSD"]
                self.assertEqual(len(eurusd_rows), 1)
                row = eurusd_rows[0]
                self.assertEqual(int(row["symbol_digits"]), 5)
                self.assertAlmostEqual(float(row["point"]), 0.00001, places=7)

    def test_executable_trade_prices_and_returns_long(self):
        """Hand-checkable bid-ask execution test for a Long trade (direction = +1)."""
        entry_bid = 1.10000
        exit_bid = 1.10200
        direction = 1

        # 1. Zero cost / frictionless
        entry_p, exit_p = compute_executable_trade_prices(entry_bid, exit_bid, direction, spread_points=0)
        self.assertEqual(entry_p, 1.10000)
        self.assertEqual(exit_p, 1.10200)

        pips_gross = compute_directional_profit_pips(entry_bid, exit_bid, direction, spread_points=0)
        self.assertAlmostEqual(pips_gross, 20.0, places=4)

        ret_gross = compute_directional_log_return(entry_bid, exit_bid, direction, spread_points=0)
        self.assertAlmostEqual(ret_gross, math.log(1.10200 / 1.10000), places=8)

        # 2. Standard 10-point spread (1.0 pip = 0.00010)
        # Long enters at Ask = 1.10000 + 0.00010 = 1.10010, exits at Bid = 1.10200
        entry_p_net, exit_p_net = compute_executable_trade_prices(entry_bid, exit_bid, direction, spread_points=10)
        self.assertAlmostEqual(entry_p_net, 1.10010, places=6)
        self.assertAlmostEqual(exit_p_net, 1.10200, places=6)

        pips_net = compute_directional_profit_pips(entry_bid, exit_bid, direction, spread_points=10)
        self.assertAlmostEqual(pips_net, 19.0, places=4)
        self.assertAlmostEqual(pips_gross - pips_net, 1.0, places=4)

        ret_net = compute_directional_log_return(entry_bid, exit_bid, direction, spread_points=10)
        self.assertAlmostEqual(ret_net, math.log(1.10200 / 1.10010), places=8)

    def test_executable_trade_prices_and_returns_short(self):
        """Hand-checkable bid-ask execution test for a Short trade (direction = -1)."""
        entry_bid = 1.10200
        exit_bid = 1.10000
        direction = -1

        # 1. Zero cost / frictionless
        entry_p, exit_p = compute_executable_trade_prices(entry_bid, exit_bid, direction, spread_points=0)
        self.assertEqual(entry_p, 1.10200)
        self.assertEqual(exit_p, 1.10000)

        pips_gross = compute_directional_profit_pips(entry_bid, exit_bid, direction, spread_points=0)
        self.assertAlmostEqual(pips_gross, 20.0, places=4)

        ret_gross = compute_directional_log_return(entry_bid, exit_bid, direction, spread_points=0)
        self.assertAlmostEqual(ret_gross, math.log(1.10200 / 1.10000), places=8)

        # 2. Standard 10-point spread (1.0 pip = 0.00010)
        # Short enters at Bid = 1.10200, exits at Ask = 1.10000 + 0.00010 = 1.10010
        entry_p_net, exit_p_net = compute_executable_trade_prices(entry_bid, exit_bid, direction, spread_points=10)
        self.assertAlmostEqual(entry_p_net, 1.10200, places=6)
        self.assertAlmostEqual(exit_p_net, 1.10010, places=6)

        pips_net = compute_directional_profit_pips(entry_bid, exit_bid, direction, spread_points=10)
        self.assertAlmostEqual(pips_net, 19.0, places=4)
        self.assertAlmostEqual(pips_gross - pips_net, 1.0, places=4)

        ret_net = compute_directional_log_return(entry_bid, exit_bid, direction, spread_points=10)
        self.assertAlmostEqual(ret_net, math.log(1.10200 / 1.10010), places=8)

    def test_hand_checkable_1sample_viability_statistics(self):
        """
        Hand-checkable synthetic calculation:
        Sample: [0.0020, 0.0040, -0.0010, 0.0030, 0.0020]
        N = 5
        Mean = 0.0100 / 5 = 0.0020
        SS = 0^2 + 0.002^2 + (-0.003)^2 + 0.001^2 + 0^2 = 0.000014
        Variance = 0.000014 / 4 = 0.0000035
        std_dev = sqrt(0.0000035) approx 0.0018708287
        std_err = sqrt(0.0000035 / 5) approx 0.0008366600
        t_stat = 0.0020 / std_err approx 2.3904572
        df = 4, 1-sided p-value approx 0.03799 (< 0.05)
        Win rate: 4/5 = 80.0%
        """
        sample = [0.0020, 0.0040, -0.0010, 0.0030, 0.0020]
        stats_res = compute_1sample_viability_statistics(sample)

        self.assertEqual(stats_res["sample_size"], 5)
        self.assertAlmostEqual(stats_res["mean_return"], 0.0020, places=6)
        self.assertAlmostEqual(stats_res["std_dev"], math.sqrt(0.0000035), places=6)
        self.assertAlmostEqual(stats_res["std_error"], math.sqrt(0.0000035 / 5), places=6)
        self.assertAlmostEqual(stats_res["t_statistic"], 0.0020 / math.sqrt(0.0000035 / 5), places=4)
        self.assertAlmostEqual(stats_res["p_value_1sided"], 0.03757, places=4)
        self.assertAlmostEqual(stats_res["win_rate"], 0.80, places=4)

        # Confidence interval contains the true sample mean
        self.assertLess(stats_res["ci_95_lower"], stats_res["mean_return"])
        self.assertGreater(stats_res["ci_95_upper"], stats_res["mean_return"])

    def test_decision_gate_classification(self):
        """Verifies exact classification logic across pre-specified decision gates."""
        # 1. Negative return -> Disconfirmed
        self.assertEqual(
            classify_discovery_outcome(mean_net_standard=-0.0005, p_val_1sided=0.04, win_rate=0.48, ci_lower=-0.0010),
            "DISCONFIRMED_NEGATIVE"
        )
        # 2. Positive return but p >= 0.10 -> Disconfirmed
        self.assertEqual(
            classify_discovery_outcome(mean_net_standard=0.0005, p_val_1sided=0.15, win_rate=0.55, ci_lower=-0.0002),
            "DISCONFIRMED_NEGATIVE"
        )
        # 3. Positive return, 0.05 <= p < 0.10 -> Inconclusive / Fragile
        self.assertEqual(
            classify_discovery_outcome(mean_net_standard=0.0008, p_val_1sided=0.07, win_rate=0.54, ci_lower=-0.0001),
            "INCONCLUSIVE_FRAGILE"
        )
        # 4. Positive return, p < 0.05, but win rate < 0.53 -> Inconclusive / Fragile
        self.assertEqual(
            classify_discovery_outcome(mean_net_standard=0.0012, p_val_1sided=0.03, win_rate=0.49, ci_lower=0.0001),
            "INCONCLUSIVE_FRAGILE"
        )
        # 5. Robust discovery result: positive under Scenario 2, p < 0.05, win rate >= 0.53
        # -> Candidate for holdout verification (NOT a registered setup)
        outcome = classify_discovery_outcome(
            mean_net_standard=0.0015, p_val_1sided=0.02, win_rate=0.58, ci_lower=0.0002
        )
        self.assertEqual(outcome, "PROMISING_DISCOVERY_CANDIDATE_FOR_HOLDOUT")
        self.assertNotEqual(outcome, "REGISTERED_SETUP")


if __name__ == "__main__":
    unittest.main()
