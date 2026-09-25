"""
Synthetic Unit Tests for Strategy Viability Arithmetic
Verifies trade bid-ask mechanics, cost scenario deductions, 1-sample statistics,
boundary/input validation, and decision gate classification using small synthetic examples.

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
    classify_discovery_outcome,
    classify_holdout_outcome
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
        df = 4, 1-sided p-value approx 0.03757 (< 0.05)
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

        # 1-sided 95% lower bound must be positive because p_value_1sided < 0.05
        self.assertGreater(stats_res["ci_95_1sided_lower"], 0.0)

        # 2-sided 95% interval contains the mean
        self.assertLess(stats_res["ci_95_2sided_lower"], stats_res["mean_return"])
        self.assertGreater(stats_res["ci_95_2sided_upper"], stats_res["mean_return"])

    def test_input_validation_boundary_conditions(self):
        """Verifies proper error handling for non-finite, zero-variance, and malformed inputs."""
        # 1. NaN input raises ValueError
        with self.assertRaises(ValueError) as ctx:
            compute_1sample_viability_statistics([0.001, float("nan"), 0.002])
        self.assertIn("non-finite", str(ctx.exception))

        # 2. Inf input raises ValueError
        with self.assertRaises(ValueError) as ctx:
            compute_1sample_viability_statistics([0.001, float("inf"), 0.002])
        self.assertIn("non-finite", str(ctx.exception))

        # 3. Zero-variance sample (all values identical) raises ValueError
        with self.assertRaises(ValueError) as ctx:
            compute_1sample_viability_statistics([0.005, 0.005, 0.005, 0.005])
        self.assertIn("Zero sample variance", str(ctx.exception))

        # 4. Fewer than 2 observations raises ValueError
        with self.assertRaises(ValueError) as ctx:
            compute_1sample_viability_statistics([0.005])
        self.assertIn("At least 2 observations required", str(ctx.exception))

        # 5. Non-numeric input raises TypeError
        with self.assertRaises(TypeError):
            compute_1sample_viability_statistics([0.001, "invalid_price", 0.002])

    def test_reconciliation_one_sided_p_vs_two_sided_ci(self):
        """
        Demonstrates mathematical reconciliation:
        When 0.025 <= p_1sided < 0.05, the 1-sided 95% lower bound is > 0,
        while the 2-sided 95% lower bound is < 0.
        """
        # Synthetic sample engineered so that t-statistic is between t_0.95 and t_0.975
        # df = 4: t_0.95 = 2.1318, t_0.975 = 2.7764
        # Target t = 2.40 -> p_1sided approx 0.0368 (< 0.05, passes 1-sided test)
        # 1-sided 95% lower bound = mean - 2.1318 * se = se * (2.40 - 2.1318) > 0
        # 2-sided 95% lower bound = mean - 2.7764 * se = se * (2.40 - 2.7764) < 0
        sample = [0.0020, 0.0040, -0.0010, 0.0030, 0.0020]
        res = compute_1sample_viability_statistics(sample)

        self.assertLess(res["p_value_1sided"], 0.05)
        self.assertGreater(res["p_value_1sided"], 0.025)

        # 1-sided 95% bound is strictly positive (matches p < 0.05 test)
        self.assertGreater(res["ci_95_1sided_lower"], 0.0)

        # 2-sided 95% lower bound is negative (covers 2.5% in left tail)
        self.assertLess(res["ci_95_2sided_lower"], 0.0)

    def test_decision_gate_exhaustive_truth_table(self):
        """
        Verifies exhaustive coverage of every decision gate boundary combination.
        """
        # 1. Adverse point estimates (mean <= 0) -> DISCONFIRMED_ADVERSE (regardless of p or win rate)
        self.assertEqual(
            classify_discovery_outcome(mean_net=-0.0001, p_val_1sided=0.01, win_rate=0.60, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "DISCONFIRMED_ADVERSE"
        )
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0, p_val_1sided=0.50, win_rate=0.50, mean_net_friday=0.0, mean_net_non_friday=0.0),
            "DISCONFIRMED_ADVERSE"
        )

        # 2. Statistically underpowered (mean > 0, p >= 0.10) -> INCONCLUSIVE_UNDERPOWERED
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0005, p_val_1sided=0.10, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "INCONCLUSIVE_UNDERPOWERED"
        )
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0010, p_val_1sided=0.25, win_rate=0.58, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "INCONCLUSIVE_UNDERPOWERED"
        )

        # 3. Marginal significance (0.05 <= p < 0.10) -> INCONCLUSIVE_FRAGILE
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0008, p_val_1sided=0.050, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "INCONCLUSIVE_FRAGILE"
        )
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0008, p_val_1sided=0.099, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "INCONCLUSIVE_FRAGILE"
        )

        # 4. p < 0.05 but win rate < 0.50 -> INCONCLUSIVE_FRAGILE
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.48, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "INCONCLUSIVE_FRAGILE"
        )

        # 5. p < 0.05 with 50% - 52.9% win rate -> INCONCLUSIVE_FRAGILE
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.51, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "INCONCLUSIVE_FRAGILE"
        )
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.529, mean_net_friday=0.001, mean_net_non_friday=0.001),
            "INCONCLUSIVE_FRAGILE"
        )

        # 6. p < 0.05, win rate >= 0.53, but Friday subgroup fails (mean <= 0) -> INCONCLUSIVE_FRAGILE
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=-0.0005, mean_net_non_friday=0.0020),
            "INCONCLUSIVE_FRAGILE"
        )

        # 7. p < 0.05, win rate >= 0.53, but Non-Friday subgroup fails (mean <= 0) -> INCONCLUSIVE_FRAGILE
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=0.0020, mean_net_non_friday=-0.0005),
            "INCONCLUSIVE_FRAGILE"
        )

        # 8. p < 0.05, win rate >= 0.53, but subgroup means omitted (None) -> INCONCLUSIVE_FRAGILE
        self.assertEqual(
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=None, mean_net_non_friday=None),
            "INCONCLUSIVE_FRAGILE"
        )

        # 9. Meets all hurdles -> PROMISING_DISCOVERY_CANDIDATE
        outcome = classify_discovery_outcome(
            mean_net=0.0015,
            p_val_1sided=0.02,
            win_rate=0.55,
            mean_net_friday=0.0010,
            mean_net_non_friday=0.0018
        )
        self.assertEqual(outcome, "PROMISING_DISCOVERY_CANDIDATE")
        # Explicit governance confirmation: promising candidate is NOT a registered setup
        self.assertNotEqual(outcome, "REGISTERED_SETUP")

    def test_classify_discovery_outcome_adversarial_validation(self):
        """
        Adversarial tests proving that invalid numeric inputs (NaN, Inf, out-of-range, bool)
        can NEVER pass to PROMISING_DISCOVERY_CANDIDATE and strictly raise ValueError/TypeError.
        Also verifies missing required subgroup means cannot pass.
        """
        # 1. NaN inputs must raise ValueError (specifically tests Codex's blocker)
        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=float("nan"), win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001)

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=float("nan"), mean_net_friday=0.001, mean_net_non_friday=0.001)

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=float("nan"), mean_net_non_friday=0.001)

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=float("nan"))

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=float("nan"), p_val_1sided=0.02, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001)

        # 2. Inf inputs must raise ValueError
        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=float("inf"), win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001)

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=float("inf"), mean_net_friday=0.001, mean_net_non_friday=0.001)

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=float("inf"), mean_net_non_friday=0.001)

        # 3. Out-of-range p-values must raise ValueError
        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=-0.001, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001)

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=1.001, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=0.001)

        # 4. Out-of-range win rates must raise ValueError
        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=-0.01, mean_net_friday=0.001, mean_net_non_friday=0.001)

        with self.assertRaises(ValueError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=1.01, mean_net_friday=0.001, mean_net_non_friday=0.001)

        # 5. Non-numeric and boolean types must raise TypeError
        with self.assertRaises(TypeError):
            classify_discovery_outcome(mean_net="0.0015", p_val_1sided=0.02, win_rate=0.55)

        with self.assertRaises(TypeError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=True, win_rate=0.55)

        with self.assertRaises(TypeError):
            classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=False)

        # 6. Missing subgroup means (None) can never pass to PROMISING_DISCOVERY_CANDIDATE
        res_none_fri = classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=None, mean_net_non_friday=0.001)
        self.assertEqual(res_none_fri, "INCONCLUSIVE_FRAGILE")
        self.assertNotEqual(res_none_fri, "PROMISING_DISCOVERY_CANDIDATE")

        res_none_non_fri = classify_discovery_outcome(mean_net=0.0015, p_val_1sided=0.02, win_rate=0.55, mean_net_friday=0.001, mean_net_non_friday=None)
        self.assertEqual(res_none_non_fri, "INCONCLUSIVE_FRAGILE")
        self.assertNotEqual(res_none_non_fri, "PROMISING_DISCOVERY_CANDIDATE")

    def test_classify_holdout_outcome_all_branches(self):
        """
        Verifies input validation and exhaustive mutually exclusive branches for classify_holdout_outcome.
        """
        # 1. Input validation & error handling
        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=-1, mean_net=0.001, p_val_1sided=0.02, win_rate=0.55)

        with self.assertRaises(TypeError):
            classify_holdout_outcome(n_holdout=15.5, mean_net=0.001, p_val_1sided=0.02, win_rate=0.55)

        with self.assertRaises(TypeError):
            classify_holdout_outcome(n_holdout=True, mean_net=0.001, p_val_1sided=0.02, win_rate=0.55)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=20, mean_net=float("nan"), p_val_1sided=0.02, win_rate=0.55)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=20, mean_net=0.001, p_val_1sided=float("nan"), win_rate=0.55)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=20, mean_net=0.001, p_val_1sided=0.02, win_rate=float("nan"))

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=20, mean_net=0.001, p_val_1sided=-0.01, win_rate=0.55)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=20, mean_net=0.001, p_val_1sided=1.05, win_rate=0.55)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=20, mean_net=0.001, p_val_1sided=0.02, win_rate=1.05)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=20, mean_net=0.001, p_val_1sided=0.02, win_rate=0.55, discovery_mean_sign=0)

        # 2. Branch 1: Sample-deficient (N < 15 evaluated FIRST, before requiring statistical metrics)
        # Zero eligible trades / None statistics handled directly without invented placeholders
        self.assertEqual(
            classify_holdout_outcome(0, None, None, None),
            "HOLDOUT_SAMPLE_DEFICIENT"
        )
        self.assertEqual(
            classify_holdout_outcome(0),
            "HOLDOUT_SAMPLE_DEFICIENT"
        )
        self.assertEqual(
            classify_holdout_outcome(14, None, None, None),
            "HOLDOUT_SAMPLE_DEFICIENT"
        )
        self.assertEqual(
            classify_holdout_outcome(n_holdout=0, mean_net=0.0050, p_val_1sided=0.001, win_rate=0.80),
            "HOLDOUT_SAMPLE_DEFICIENT"
        )
        self.assertEqual(
            classify_holdout_outcome(n_holdout=14, mean_net=0.0050, p_val_1sided=0.001, win_rate=0.80),
            "HOLDOUT_SAMPLE_DEFICIENT"
        )
        self.assertEqual(
            classify_holdout_outcome(n_holdout=14, mean_net=-0.0050, p_val_1sided=0.999, win_rate=0.20),
            "HOLDOUT_SAMPLE_DEFICIENT"
        )

        # For N >= 15, statistical metrics are mandatory; None raises ValueError
        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=15, mean_net=None, p_val_1sided=0.02, win_rate=0.55)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=15, mean_net=0.001, p_val_1sided=None, win_rate=0.55)

        with self.assertRaises(ValueError):
            classify_holdout_outcome(n_holdout=15, mean_net=0.001, p_val_1sided=0.02, win_rate=None)

        # 3. Branch 2: Point estimate flat or negative (N >= 15, mean_net <= 0)
        self.assertEqual(
            classify_holdout_outcome(n_holdout=15, mean_net=-0.0001, p_val_1sided=0.01, win_rate=0.60),
            "HOLDOUT_FAIL"
        )
        self.assertEqual(
            classify_holdout_outcome(n_holdout=25, mean_net=0.0, p_val_1sided=0.50, win_rate=0.50),
            "HOLDOUT_FAIL"
        )

        # 4. Branch 3: Inconclusive (N >= 15, mean_net > 0, but fails statistical or consistency hurdles)
        # 4A. p >= 0.05
        self.assertEqual(
            classify_holdout_outcome(n_holdout=15, mean_net=0.0010, p_val_1sided=0.050, win_rate=0.55),
            "HOLDOUT_INCONCLUSIVE"
        )
        self.assertEqual(
            classify_holdout_outcome(n_holdout=15, mean_net=0.0010, p_val_1sided=0.15, win_rate=0.55),
            "HOLDOUT_INCONCLUSIVE"
        )
        # 4B. Win rate < 50%
        self.assertEqual(
            classify_holdout_outcome(n_holdout=15, mean_net=0.0010, p_val_1sided=0.02, win_rate=0.49),
            "HOLDOUT_INCONCLUSIVE"
        )
        # 4C. Directional sign mismatch
        self.assertEqual(
            classify_holdout_outcome(n_holdout=15, mean_net=0.0010, p_val_1sided=0.02, win_rate=0.55, discovery_mean_sign=-1),
            "HOLDOUT_INCONCLUSIVE"
        )

        # 5. Branch 4: Pass hurdles for demo forward validation
        pass_res = classify_holdout_outcome(
            n_holdout=15,
            mean_net=0.0012,
            p_val_1sided=0.035,
            win_rate=0.52,
            discovery_mean_sign=1
        )
        self.assertEqual(pass_res, "HOLDOUT_PASS_ELIGIBLE_FOR_DEMO")
        # Explicit governance confirmation: pass grants demo validation eligibility, NOT setup registration or proven profit
        self.assertNotEqual(pass_res, "REGISTERED_SETUP")
        self.assertNotEqual(pass_res, "PROVEN_PROFITABLE")

        # Upper sample size (e.g. 45 packages)
        self.assertEqual(
            classify_holdout_outcome(n_holdout=45, mean_net=0.0020, p_val_1sided=0.005, win_rate=0.62),
            "HOLDOUT_PASS_ELIGIBLE_FOR_DEMO"
        )

    def test_docs_markdown_zero_control_characters(self):
        """
        Audits all markdown documents in docs/ to prove zero unexpected ASCII control characters.
        Rejects all bytes < 32 except standard line feed (0x0A) and carriage return (0x0D).
        Specifically guards against escaped LaTeX commands turning into bell (0x07),
        backspace (0x08), tab (0x09), or form feed (0x0C).
        """
        docs_dir = "docs"
        self.assertTrue(os.path.exists(docs_dir), f"Directory {docs_dir} does not exist")

        md_files = [
            os.path.join(root, f)
            for root, _, files in os.walk(docs_dir)
            for f in files if f.endswith(".md")
        ]
        self.assertGreater(len(md_files), 0, "No markdown files found in docs/")

        for file_path in md_files:
            with open(file_path, "rb") as f:
                content = f.read()
            forbidden = [(idx, b) for idx, b in enumerate(content) if b < 32 and b not in (10, 13)]
            self.assertEqual(
                len(forbidden),
                0,
                f"File {file_path} contains {len(forbidden)} forbidden control characters: {forbidden[:10]}"
            )


if __name__ == "__main__":
    unittest.main()

