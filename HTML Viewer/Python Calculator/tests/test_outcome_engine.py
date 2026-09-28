"""Unit tests for the Outcome Engine using synthetic fixtures.

Validates per CALCULATION_AND_CANDIDATE_CONTRACT:
1. Both pair directions (Long +1, Short -1)
2. ATR and H1 indexing (entry candle is Bar 1)
3. Target-only touch
4. Stop-only touch
5. Timeout exit at Bar Hmax close
6. Opening gaps beyond barriers
7. Dual-touch ambiguity resolution under STOP_FIRST vs TARGET_FIRST
8. Short gross R arithmetic
9. Horizon boundaries (H60, H120, H240)
10. MFE and MAE excursion bounds
11. Even-N median and nearest-rank p75/p90
12. Count reconciliation (Wins + Losses + Timeouts == Eligible N)
"""

import unittest
from unittest.mock import ANY, patch
import sys
import os
from typing import Dict, Any, List, Set, Tuple, Optional
from collections import defaultdict

CALC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if CALC_DIR not in sys.path:
    sys.path.insert(0, CALC_DIR)

from models import CandleBar
from outcome_engine import (
    GridCell,
    ALL_GRID_CELLS,
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
    ACTIVE_USD_PAIRS,
)
from run_exploration_pipeline import (
    check_package_immutability,
    verify_existing_package,
    verify_raw_provenance,
    run_pipeline,
    RUN_ID,
)


def make_bar(
    idx: int,
    open_p: float,
    high_p: float,
    low_p: float,
    close_p: float,
    time_str: str = "2020.01.01 00:00:00",
    timestamp: Optional[int] = None,
) -> CandleBar:
    """Helper to create a synthetic CandleBar with valid OHLC geometry."""
    ts = timestamp if timestamp is not None else (1577836800 + idx * 3600)
    return CandleBar(
        timestamp=ts,
        open=open_p,
        high=high_p,
        low=low_p,
        close=close_p,
        tick_volume=100,
        spread=10,
        real_volume=0,
        symbol="EURUSD",
        time_server_text=time_str,
        complete_at_export=True,
    )


class TestOutcomeEngine(unittest.TestCase):
    def test_master_runner_requires_full_verification_before_success(self):
        """A sample audit alone must never allow the master runner to report success."""
        module = "run_exploration_pipeline"
        with patch(f"{module}.verify_raw_provenance", return_value={
            "raw_files_verified": 34, "pre_outcome_ledgers_verified": 2
        }), patch(f"{module}.get_git_commit_head", return_value="test-commit"), \
             patch(f"{module}.run_family_exploration") as generate, \
             patch(f"{module}.verify_existing_package", side_effect=ValueError("bad aggregate")) as verify:
            with self.assertRaisesRegex(ValueError, "bad aggregate"):
                run_pipeline(allow_simulations=True, family="CPI", run_id="synthetic")
            generate.assert_called_once()
            verify.assert_called_once_with("CPI", run_id="synthetic", raw_dir=ANY)

    """Synthetic unit tests for trade outcome simulation."""

    def test_grid_cell_generation(self):
        """Verify 52 unique cells with correct reward-to-risk ratios."""
        self.assertEqual(len(ALL_GRID_CELLS), 52)
        # 4:4 cell check
        c_4_4 = next(c for c in ALL_GRID_CELLS if c.stop_atr == 4.0 and c.target_atr == 4.0)
        self.assertEqual(c_4_4.label, "4:4")
        self.assertEqual(c_4_4.reward_risk_ratio, 1.0)

        # 2:1 cell check
        c_2_1 = next(c for c in ALL_GRID_CELLS if c.stop_atr == 2.0 and c.target_atr == 1.0)
        self.assertEqual(c_2_1.label, "2:1")
        self.assertEqual(c_2_1.reward_risk_ratio, 0.5)

        # 1:4 cell check
        c_1_4 = next(c for c in ALL_GRID_CELLS if c.stop_atr == 1.0 and c.target_atr == 4.0)
        self.assertEqual(c_1_4.label, "1:4")
        self.assertEqual(c_1_4.reward_risk_ratio, 4.0)

    def test_target_only_touch_long(self):
        """Verify Long target hit without stop touch."""
        # Entry at 1.1000, ATR = 0.0050. Stop 1 ATR (1.0950), Target 2 ATR (1.1100).
        # Bar 1: 1.1000 -> 1.1040 (no touch)
        # Bar 2: 1.1030 -> 1.1110 (touches 1.1100 target, low 1.1010 does not touch stop)
        b1 = make_bar(1, 1.1000, 1.1040, 1.0980, 1.1030)
        b2 = make_bar(2, 1.1030, 1.1110, 1.1010, 1.1090)
        path = [b1, b2]

        out = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=path, pip_size=0.0001
        )
        self.assertTrue(out.is_win)
        self.assertFalse(out.is_loss)
        self.assertFalse(out.is_timeout)
        self.assertEqual(out.exit_reason, "TARGET")
        self.assertEqual(out.exit_bar_idx, 2)
        self.assertAlmostEqual(out.gross_r, 2.0)  # +2R
        self.assertAlmostEqual(out.signed_pips, 100.0)  # +100 pips

    def test_stop_only_touch_long(self):
        """Verify Long stop hit without target touch."""
        # Entry 1.1000, ATR = 0.0050. Stop 1 ATR (1.0950), Target 2 ATR (1.1100).
        # Bar 1: 1.1000 -> low 1.0940 (touches stop 1.0950, high 1.1020 does not touch target)
        b1 = make_bar(1, 1.1000, 1.1020, 1.0940, 1.0960)
        path = [b1]

        out = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=path, pip_size=0.0001
        )
        self.assertFalse(out.is_win)
        self.assertTrue(out.is_loss)
        self.assertEqual(out.exit_reason, "STOP")
        self.assertEqual(out.exit_bar_idx, 1)
        self.assertAlmostEqual(out.gross_r, -1.0)  # -1R
        self.assertAlmostEqual(out.signed_pips, -50.0)  # -50 pips

    def test_short_direction_arithmetic(self):
        """Verify Short direction: target is below entry, stop is above entry."""
        # Entry 1.1000, ATR = 0.0050. Stop 2 ATR (1.1100), Target 1 ATR (1.0950).
        # Short Win: price drops to 1.0940.
        b1 = make_bar(1, 1.1000, 1.1020, 1.0940, 1.0960)
        out_win = simulate_single_trade(
            entry_price=1.1000, direction=-1, atr=0.0050,
            stop_atr=2.0, target_atr=1.0, path_bars=[b1], pip_size=0.0001
        )
        self.assertTrue(out_win.is_win)
        self.assertEqual(out_win.exit_reason, "TARGET")
        self.assertAlmostEqual(out_win.gross_r, 0.5)  # 1/2 = +0.5R
        self.assertAlmostEqual(out_win.signed_pips, 50.0)  # +50 pips

        # Short Loss: price rallies to 1.1120.
        b2 = make_bar(1, 1.1000, 1.1120, 1.0980, 1.1110)
        out_loss = simulate_single_trade(
            entry_price=1.1000, direction=-1, atr=0.0050,
            stop_atr=2.0, target_atr=1.0, path_bars=[b2], pip_size=0.0001
        )
        self.assertTrue(out_loss.is_loss)
        self.assertEqual(out_loss.exit_reason, "STOP")
        self.assertAlmostEqual(out_loss.gross_r, -1.0)  # -1R
        self.assertAlmostEqual(out_loss.signed_pips, -100.0)  # -100 pips

    def test_timeout_exit(self):
        """Verify Timeout exit at close of Bar Hmax."""
        # Entry 1.1000, ATR = 0.0050. Stop 1.0950, Target 1.1100.
        # Neither stop nor target hit across 3 bars; exits at close of Bar 3 (1.1030).
        b1 = make_bar(1, 1.1000, 1.1040, 1.0970, 1.1010)
        b2 = make_bar(2, 1.1010, 1.1050, 1.0980, 1.1020)
        b3 = make_bar(3, 1.1020, 1.1060, 1.0980, 1.1030)
        path = [b1, b2, b3]

        out = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=path, pip_size=0.0001
        )
        self.assertTrue(out.is_timeout)
        self.assertFalse(out.is_win)
        self.assertFalse(out.is_loss)
        self.assertEqual(out.exit_reason, "TIMEOUT")
        self.assertEqual(out.exit_bar_idx, 3)
        self.assertAlmostEqual(out.exit_price, 1.1030)
        self.assertAlmostEqual(out.signed_pips, 30.0)  # (1.1030 - 1.1000)/0.0001 = +30 pips
        self.assertAlmostEqual(out.gross_r, 0.6)  # 30 / 50 = +0.6R

    def test_dual_touch_stop_first_vs_target_first(self):
        """Verify dual-touch ambiguity: STOP_FIRST gives loss, TARGET_FIRST gives win."""
        # Entry 1.1000, ATR = 0.0050. Stop 1 ATR (1.0950), Target 1 ATR (1.1050).
        # Bar 1 has high 1.1060 and low 1.0940 (touches both).
        b1 = make_bar(1, 1.1000, 1.1060, 1.0940, 1.1000)

        # Primary: STOP_FIRST
        out_primary = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=1.0, path_bars=[b1], pip_size=0.0001,
            dual_touch_mode="STOP_FIRST"
        )
        self.assertTrue(out_primary.dual_touch)
        self.assertFalse(out_primary.is_win)
        self.assertTrue(out_primary.is_loss)
        self.assertEqual(out_primary.exit_reason, "STOP")
        self.assertAlmostEqual(out_primary.gross_r, -1.0)

        # Sensitivity: TARGET_FIRST
        out_sens = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=1.0, path_bars=[b1], pip_size=0.0001,
            dual_touch_mode="TARGET_FIRST"
        )
        self.assertTrue(out_sens.dual_touch)
        self.assertTrue(out_sens.is_win)
        self.assertFalse(out_sens.is_loss)
        self.assertEqual(out_sens.exit_reason, "TARGET")
        self.assertAlmostEqual(out_sens.gross_r, 1.0)

    def test_opening_gap_beyond_barrier(self):
        """Verify opening gap: nominal proxy credits threshold; gap price recorded for sensitivity.

        For opening-gap exits, execution occurs at the bar open (the gap-open price is observable
        at bar open). Therefore clock_seconds_bar_close_proxy must equal clock_seconds_to_exit_bar_open
        (exact), NOT clock_seconds_to_exit_bar_close (which would be for intrabar touches).
        """
        # Entry 1.1000, ATR = 0.0050. Stop 1 ATR (1.0950), Target 2 ATR (1.1100).
        # Bar 1: ordinary (entry candle, timestamp t0)
        # Bar 2 opens at 1.0920 (gaps below 1.0950 stop). timestamp t0 + 3600.
        t0 = 1577836800
        b1 = make_bar(1, 1.1000, 1.1040, 1.0980, 1.1010, timestamp=t0)
        b2 = make_bar(2, 1.0920, 1.0940, 1.0900, 1.0930, timestamp=t0 + 3600)

        out = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=[b1, b2], pip_size=0.0001
        )
        self.assertTrue(out.is_opening_gap)
        self.assertEqual(out.exit_reason, "STOP_GAP")
        self.assertAlmostEqual(out.gross_r, -1.0)  # Primary nominal proxy
        self.assertAlmostEqual(out.signed_pips, -50.0)  # Primary nominal pips
        self.assertAlmostEqual(out.gap_open_price, 1.0920)
        self.assertAlmostEqual(out.gap_executable_gross_r, -1.6)  # (1.0920 - 1.1000)/0.0050 = -1.6R
        self.assertAlmostEqual(out.gap_executable_pips, -80.0)

        # Opening-gap exit: clock proxy = bar_open_sec (exact), NOT bar_close_sec
        # Bar 2 open is t0 + 3600 - t0 = 3600 seconds from entry.
        self.assertEqual(out.clock_seconds_to_exit_bar_open, 3600)
        self.assertEqual(out.clock_seconds_to_exit_bar_close, 7200)  # bar close is 1 hour later
        # CRITICAL: proxy equals bar_open (exact), unlike intrabar touches where proxy = bar_close
        self.assertEqual(out.clock_seconds_bar_close_proxy, 3600)
        self.assertNotEqual(out.clock_seconds_bar_close_proxy, out.clock_seconds_to_exit_bar_close)

    def test_horizon_boundaries_h60_h120_h240(self):
        """Verify that a target hit at bar 80 is a timeout at H60, but a win at H120 and H240."""
        # Build 120 bars: bars 1-79 stay between barriers; bar 80 hits target.
        bars = []
        for i in range(1, 121):
            if i == 80:
                bars.append(make_bar(i, 1.1000, 1.1150, 1.0980, 1.1120))  # hits 1.1100 target
            else:
                bars.append(make_bar(i, 1.1000, 1.1040, 1.0980, 1.1010))

        # At H60: path is first 60 bars -> TIMEOUT
        out_60 = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=bars[:60], pip_size=0.0001
        )
        self.assertTrue(out_60.is_timeout)
        self.assertEqual(out_60.exit_reason, "TIMEOUT")
        self.assertEqual(out_60.bars_to_exit, 60)

        # At H120: path is 120 bars -> TARGET at Bar 80
        out_120 = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=bars[:120], pip_size=0.0001
        )
        self.assertTrue(out_120.is_win)
        self.assertEqual(out_120.exit_reason, "TARGET")
        self.assertEqual(out_120.bars_to_exit, 80)

    def test_mfe_mae_bounds(self):
        """Verify excursion bounds (guaranteed lower bound and OHLC upper bound)."""
        # Entry 1.1000, ATR = 0.0050. Stop 1 ATR (1.0950), Target 2 ATR (1.1100).
        # Bar 1: high 1.1040 (+40 pips), low 1.0990 (-10 pips)
        # Bar 2: high 1.1120 (+120 pips, hits 1.1100 target), low 1.0960 (-40 pips)
        b1 = make_bar(1, 1.1000, 1.1040, 1.0990, 1.1020)
        b2 = make_bar(2, 1.1020, 1.1120, 1.0960, 1.1080)
        path = [b1, b2]

        out = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=path, pip_size=0.0001
        )
        self.assertEqual(out.exit_reason, "TARGET")
        # Target was reached (+100 pips guaranteed lower bound)
        self.assertAlmostEqual(out.mfe_pips_lower, 100.0)
        # Upper bound includes exit bar high 1.1120 (+120 pips)
        self.assertAlmostEqual(out.mfe_pips_upper, 120.0)
        # For adverse: prior bar low was 1.0990 (10 pips adverse). Exit bar low 1.0960 may have been post-target.
        self.assertAlmostEqual(out.mae_pips_lower, 10.0)
        self.assertAlmostEqual(out.mae_pips_upper, 40.0)

    def test_even_n_median_and_nearest_rank_quantiles(self):
        """Verify even-N median and nearest-rank quantiles per contract."""
        # Even N = 4: [1.0, 2.0, 3.0, 4.0]
        # median = (2.0 + 3.0)/2 = 2.5
        vals_even = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(calculate_median(vals_even), 2.5)

        # Odd N = 5: [1.0, 2.0, 3.0, 4.0, 5.0]
        # median = 3.0
        vals_odd = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(calculate_median(vals_odd), 3.0)

        # Nearest-rank: ceil(q * N)
        # N = 4: p75 = ceil(0.75 * 4) = 3 -> index 2 -> 3.0
        # N = 4: p90 = ceil(0.90 * 4) = 4 -> index 3 -> 4.0
        self.assertAlmostEqual(calculate_quantile(vals_even, 0.75), 3.0)
        self.assertAlmostEqual(calculate_quantile(vals_even, 0.90), 4.0)

        # N = 10: [1..10]
        # p75 = ceil(0.75 * 10) = 8 -> 8.0
        # p90 = ceil(0.90 * 10) = 9 -> 9.0
        vals_10 = [float(i) for i in range(1, 11)]
        self.assertAlmostEqual(calculate_quantile(vals_10, 0.75), 8.0)
        self.assertAlmostEqual(calculate_quantile(vals_10, 0.90), 9.0)

    def test_pip_size_mapping(self):
        """Verify pip size mapping for JPY vs non-JPY."""
        self.assertEqual(get_pip_size("USDJPY"), 0.01)
        self.assertEqual(get_pip_size("EURJPY"), 0.01)
        self.assertEqual(get_pip_size("EURUSD"), 0.0001)
        self.assertEqual(get_pip_size("GBPUSD"), 0.0001)
        self.assertEqual(get_pip_size("USDCAD"), 0.01 if "JPY" in "USDCAD" else 0.0001)
        self.assertEqual(get_pip_size("USDCHF"), 0.0001)

    def test_true_loyo_calculation(self):
        """Verify true Leave-One-Year-Out cross-validation re-anchoring."""
        trials = []
        # Create 10 trades per year for 2015..2025
        for y in range(2015, 2026):
            for i in range(10):
                if y == 2025:
                    # Negative year in 2025: 2 wins (+2R), 8 losses (-1R) -> Net -4R
                    is_win = (i < 2)
                    gross_r = 2.0 if is_win else -1.0
                else:
                    # Positive years 2015..2024: 6 wins (+2R), 4 losses (-1R) -> Net +8R
                    is_win = (i < 6)
                    gross_r = 2.0 if is_win else -1.0
                trials.append({
                    "year": str(y),
                    "is_win": is_win,
                    "is_loss": not is_win,
                    "is_timeout": False,
                    "gross_r": gross_r,
                })

        # Add 2026 partial year trades (must be excluded from LOYO folds)
        for i in range(10):
            trials.append({
                "year": "2026",
                "is_win": True,
                "is_loss": False,
                "is_timeout": False,
                "gross_r": 2.0,
            })

        loyo = calculate_true_loyo(trials)
        self.assertEqual(loyo["loyo_total_folds"], 11)
        self.assertNotIn("2026", loyo["loyo_folds"], "Partial year 2026 must be strictly excluded from LOYO folds")

        # When 2025 is excluded: remaining is 10 years * +8R = +80R / 100 trades = +0.80R
        fold_2025 = loyo["loyo_folds"]["2025"]
        self.assertEqual(fold_2025["remaining_n"], 100)
        self.assertAlmostEqual(fold_2025["gross_sum_r"], 80.0)
        self.assertAlmostEqual(fold_2025["gross_mean_r"], 0.80)
        self.assertTrue(fold_2025["is_positive"])

        # When 2015 is excluded: remaining is 9 years * +8R + 1 year * (-4R) = +68R / 100 trades = +0.68R
        fold_2015 = loyo["loyo_folds"]["2015"]
        self.assertEqual(fold_2015["remaining_n"], 100)
        self.assertAlmostEqual(fold_2015["gross_sum_r"], 68.0)
        self.assertAlmostEqual(fold_2015["gross_mean_r"], 0.68)
        self.assertTrue(fold_2015["is_positive"])

        self.assertEqual(loyo["loyo_positive_years"], 11)
        self.assertAlmostEqual(loyo["loyo_min_mean_r"], 0.68)
        self.assertAlmostEqual(loyo["loyo_max_mean_r"], 0.80)
        self.assertAlmostEqual(loyo["loyo_min_sum_r"], 68.0)
        self.assertAlmostEqual(loyo["loyo_max_sum_r"], 80.0)

    def test_summarize_exit_distributions(self):
        """Verify separated duration distributions for wins (TP) and losses (SL)."""
        trials = [
            {"is_win": True, "is_loss": False, "is_timeout": False, "bars_to_exit": 10},
            {"is_win": True, "is_loss": False, "is_timeout": False, "bars_to_exit": 20},
            {"is_win": False, "is_loss": True, "is_timeout": False, "bars_to_exit": 4},
            {"is_win": False, "is_loss": True, "is_timeout": False, "bars_to_exit": 8},
            {"is_win": False, "is_loss": True, "is_timeout": False, "bars_to_exit": 12},
            {"is_win": False, "is_loss": False, "is_timeout": True, "bars_to_exit": 60},
        ]
        dist = summarize_exit_distributions(trials)
        self.assertEqual(dist["tp_n"], 2)
        self.assertAlmostEqual(dist["tp_median_bars"], 15.0)
        self.assertAlmostEqual(dist["tp_max_bars"], 20.0)

        self.assertEqual(dist["sl_n"], 3)
        self.assertAlmostEqual(dist["sl_median_bars"], 8.0)
        self.assertAlmostEqual(dist["sl_max_bars"], 12.0)

        self.assertEqual(dist["to_n"], 1)
        self.assertEqual(dist["to_bars"], 60)

        self.assertAlmostEqual(dist["overall_median_bars"], 11.0)  # [4, 8, 10, 12, 20, 60] -> (10+12)/2 = 11.0

    def test_check_package_immutability(self):
        """Verify package immutability check refuses overwrite on non-empty dirs."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # 1. Empty directory: should succeed
            check_package_immutability(td)

            # 2. Non-existent path: should succeed
            check_package_immutability(os.path.join(td, "sub_dir"))

            # 3. Non-empty directory: must raise FileExistsError
            dummy_file = os.path.join(td, "manifest.json")
            with open(dummy_file, "w") as f:
                f.write("{}")
            with self.assertRaises(FileExistsError):
                check_package_immutability(td)

    def test_summarize_annual_breakdown(self):
        """Verify annual breakdown cohorts and calculations."""
        trials = [
            {"year": "2020", "is_win": True, "is_loss": False, "is_timeout": False, "gross_r": 1.5},
            {"year": "2020", "is_win": False, "is_loss": True, "is_timeout": False, "gross_r": -1.0},
            {"year": "2026", "is_win": True, "is_loss": False, "is_timeout": False, "gross_r": 2.0},
        ]
        ann = summarize_annual_breakdown(trials)
        self.assertIn("2020", ann)
        self.assertEqual(ann["2020"]["cohort"], "CORE_2015_2025")
        self.assertEqual(ann["2020"]["n"], 2)
        self.assertEqual(ann["2020"]["wins"], 1)
        self.assertEqual(ann["2020"]["losses"], 1)
        self.assertAlmostEqual(ann["2020"]["gross_sum_r"], 0.5)
        self.assertAlmostEqual(ann["2020"]["gross_mean_r"], 0.25)

        self.assertIn("2026", ann)
        self.assertEqual(ann["2026"]["cohort"], "PARTIAL_2026")
        self.assertEqual(ann["2026"]["n"], 1)
        self.assertAlmostEqual(ann["2026"]["gross_sum_r"], 2.0)

    def test_get_adjacent_grid_cells(self):
        """Verify orthogonal adjacent cell boundaries and neighborhood topology."""
        # 1. Corner cell 1:1 -> 2 neighbors (2:1 and 1:1.25)
        c_1_1 = GridCell(stop_atr=1.0, target_atr=1.0)
        adj_1_1 = get_adjacent_grid_cells(c_1_1)
        labels_1_1 = set(c.label for c in adj_1_1)
        self.assertEqual(len(adj_1_1), 2)
        self.assertEqual(labels_1_1, {"2:1", "1:1.25"})

        # 2. Corner cell 4:4 -> 2 neighbors (3:4 and 4:3.75)
        c_4_4 = GridCell(stop_atr=4.0, target_atr=4.0)
        adj_4_4 = get_adjacent_grid_cells(c_4_4)
        labels_4_4 = set(c.label for c in adj_4_4)
        self.assertEqual(len(adj_4_4), 2)
        self.assertEqual(labels_4_4, {"3:4", "4:3.75"})

        # 3. Interior cell 2:2 -> 4 neighbors (1:2, 3:2, 2:1.75, 2:2.25)
        c_2_2 = GridCell(stop_atr=2.0, target_atr=2.0)
        adj_2_2 = get_adjacent_grid_cells(c_2_2)
        labels_2_2 = set(c.label for c in adj_2_2)
        self.assertEqual(len(adj_2_2), 4)
        self.assertEqual(labels_2_2, {"1:2", "3:2", "2:1.75", "2:2.25"})

        # 4. Edge cell 1:2 -> 3 neighbors (2:2, 1:1.75, 1:2.25)
        c_1_2 = GridCell(stop_atr=1.0, target_atr=2.0)
        adj_1_2 = get_adjacent_grid_cells(c_1_2)
        labels_1_2 = set(c.label for c in adj_1_2)
        self.assertEqual(len(adj_1_2), 3)
        self.assertEqual(labels_1_2, {"2:2", "1:1.75", "1:2.25"})

    def test_calculate_adjacent_cell_stability(self):
        """Verify adjacent-cell stability calculation, mean R, delta, and positivity check."""
        # Simulated mean R map for interior cell 2:2 and its neighbors
        mean_r_map = {
            "2:2": 0.50,
            "1:2": 0.40,
            "3:2": 0.60,
            "2:1.75": 0.30,
            "2:2.25": 0.70,
        }
        res = calculate_adjacent_cell_stability("2:2", mean_r_map)
        self.assertEqual(res["adj_cells_count"], 4)
        # Average of [0.40, 0.60, 0.30, 0.70] = 2.0 / 4 = 0.50
        self.assertAlmostEqual(res["adj_mean_gross_r"], 0.50)
        self.assertAlmostEqual(res["adj_delta_mean_r"], 0.0)  # 0.50 - 0.50 = 0.0
        self.assertAlmostEqual(res["adj_min_mean_r"], 0.30)
        self.assertAlmostEqual(res["adj_max_mean_r"], 0.70)
        self.assertTrue(res["adj_all_positive"])

        # Test with one negative neighbor
        mean_r_map_neg = {
            "2:2": 0.50,
            "1:2": -0.10,
            "3:2": 0.60,
            "2:1.75": 0.30,
            "2:2.25": 0.70,
        }
        res_neg = calculate_adjacent_cell_stability("2:2", mean_r_map_neg)
        self.assertFalse(res_neg["adj_all_positive"])

        # Unknown cell label must raise ValueError
        with self.assertRaises(ValueError):
            calculate_adjacent_cell_stability("99:99", mean_r_map)

    def test_format_optional_float(self):
        """Verify format_optional_float serializes None and NaN as empty string, and floats correctly."""
        self.assertEqual(format_optional_float(None), "")
        self.assertEqual(format_optional_float(float("nan")), "")
        self.assertEqual(format_optional_float(1.23456, ".2f"), "1.23")
        self.assertEqual(format_optional_float(0.0, ".1f"), "0.0")
        self.assertEqual(format_optional_float(150.0, ".0f"), "150")

    def test_summarize_exit_distributions_clock_time(self):
        """Verify bars and clock seconds distributions for wins and losses."""
        trials = [
            {"is_win": True, "is_loss": False, "is_timeout": False, "bars_to_exit": 2},
            {"is_win": True, "is_loss": False, "is_timeout": False, "bars_to_exit": 4},
            {"is_win": False, "is_loss": True, "is_timeout": False, "bars_to_exit": 6},
        ]
        dist = summarize_exit_distributions(trials)
        # Win: [2, 4] -> median bars = 3.0, median seconds = 3 * 3600 = 10800
        self.assertAlmostEqual(dist["tp_median_bars"], 3.0)
        self.assertAlmostEqual(dist["tp_median_seconds"], 10800.0)
        self.assertAlmostEqual(dist["tp_max_seconds"], 14400.0)

        # Loss: [6] -> median bars = 6.0, median seconds = 6 * 3600 = 21600
        self.assertAlmostEqual(dist["sl_median_bars"], 6.0)
        self.assertAlmostEqual(dist["sl_median_seconds"], 21600.0)

        # Empty wins test: ensure None returned rather than 0.0
        no_win_trials = [
            {"is_win": False, "is_loss": True, "is_timeout": False, "bars_to_exit": 5}
        ]
        no_win_dist = summarize_exit_distributions(no_win_trials)
        self.assertIsNone(no_win_dist["tp_median_bars"])
        self.assertIsNone(no_win_dist["tp_median_seconds"])
        self.assertIsNone(no_win_dist["tp_max_bars"])
        self.assertEqual(format_optional_float(no_win_dist["tp_median_bars"]), "")
    def test_synthetic_friday_to_monday_path(self):
        """Verify that wall-clock duration correctly accounts for weekend gap, failing old bars*3600 formula."""
        # Entry candle: Friday 2020-01-03 20:00:00 UTC (timestamp = 1578081600)
        t0 = 1578081600
        # Bar 1: Friday 20:00 - 21:00 (timestamp t0)
        b1 = make_bar(0, 1.1000, 1.1020, 1.0980, 1.1010, time_str="2020.01.03 20:00:00", timestamp=t0)
        # Bar 2: Friday 21:00 - 22:00 (timestamp t0 + 3600)
        b2 = make_bar(1, 1.1010, 1.1030, 1.0990, 1.1020, time_str="2020.01.03 21:00:00", timestamp=t0 + 3600)
        # Weekend closure: Friday 22:00 to Sunday 22:00 = 48 hours = 172,800 seconds
        t_sun = t0 + 7200 + 172800  # 1578261600 (Sunday 22:00:00)
        # Bar 3: Sunday 22:00 - 23:00 (touches target 1.1100)
        b3 = make_bar(2, 1.1020, 1.1110, 1.1000, 1.1090, time_str="2020.01.05 22:00:00", timestamp=t_sun)

        path = [b1, b2, b3]

        out = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=path, pip_size=0.0001
        )
        self.assertTrue(out.is_win)
        self.assertEqual(out.exit_reason, "TARGET")
        self.assertEqual(out.bars_to_exit, 3)

        # Old formula only counted observed trading bars: 3 * 3600 = 10,800s
        old_bars_seconds = out.bars_to_exit * 3600
        self.assertEqual(old_bars_seconds, 10800)

        # Actual wall-clock seconds from entry open:
        # Exit bar open = t_sun -> t_sun - t0 = 180,000s (50 hours)
        # Exit bar close = t_sun + 3600 -> 183,600s (51 hours)
        self.assertEqual(out.clock_seconds_to_exit_bar_open, 180000)
        self.assertEqual(out.clock_seconds_to_exit_bar_close, 183600)
        self.assertEqual(out.clock_seconds_bar_close_proxy, 183600)

        # Explicitly assert that the old formula fails and is strictly different
        self.assertNotEqual(out.clock_seconds_bar_close_proxy, old_bars_seconds)
        self.assertGreater(out.clock_seconds_bar_close_proxy, old_bars_seconds)

        # Also test TIMEOUT exit on the same path
        # If neither target nor stop hit across 3 bars, timeout occurs at close of Bar 3
        b3_no_hit = make_bar(2, 1.1020, 1.1040, 1.1000, 1.1030, time_str="2020.01.05 22:00:00", timestamp=t_sun)
        out_to = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=[b1, b2, b3_no_hit], pip_size=0.0001
        )
        self.assertTrue(out_to.is_timeout)
        self.assertEqual(out_to.exit_reason, "TIMEOUT")
        self.assertEqual(out_to.bars_to_exit, 3)
        self.assertEqual(out_to.clock_seconds_to_exit_bar_open, 180000)
        self.assertEqual(out_to.clock_seconds_to_exit_bar_close, 183600)
        self.assertEqual(out_to.clock_seconds_bar_close_proxy, 183600)
        self.assertNotEqual(out_to.clock_seconds_bar_close_proxy, old_bars_seconds)

    def test_run_id_wired_consistently(self):
        """Verify that run-id is consistently respected by verification and manifest matching."""
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as td:
            # Create a synthetic package with custom run-id
            custom_run_id = "test_run_2026_custom"
            custom_dir = os.path.join(td, custom_run_id)
            os.makedirs(custom_dir, exist_ok=True)
            _build_valid_synthetic_package(custom_dir, family="CPI")

            # Update manifest to declare custom run-id
            mpath = os.path.join(custom_dir, "manifest.json")
            with open(mpath, "r", encoding="utf-8") as f:
                mdata = json.load(f)
            mdata["run_id"] = custom_run_id
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(mdata, f)

            # Verification succeeds with custom run_id directory
            res = verify_existing_package("CPI", run_id=custom_run_id, package_dir_override=custom_dir, skip_raw_audit=True)
            self.assertEqual(res["status"], "PASSED")
            self.assertEqual(res["run_id"], custom_run_id)

    def test_single_pass_indexing_and_performance(self):
        """Verify that index_trial_records correctly groups trials into panels and cohorts efficiently."""
        trials = []
        for i in range(100):
            trials.append({
                "pair": "EURUSD",
                "signal_type": "af",
                "horizon": 60,
                "cell_label": "1:1",
                "claims_collision": (i % 2 == 0),
                "is_common_h240": True,
                "gross_r": 1.0,
            })
            trials.append({
                "pair": "GBPUSD",
                "signal_type": "ap",
                "horizon": 120,
                "cell_label": "2:2",
                "claims_collision": False,
                "is_common_h240": False,
                "gross_r": -1.0,
            })

        indexed = index_trial_records(trials, "CPI")

        # EURUSD in FULL_PANEL
        eur_all = indexed.get(("FULL_PANEL", "EURUSD", "af", "ALL_ELIGIBLE", 60, "1:1"), [])
        self.assertEqual(len(eur_all), 100)

        eur_clean = indexed.get(("JOBLESS_CLAIMS_CLEAN", "EURUSD", "af", "ALL_ELIGIBLE", 60, "1:1"), [])
        self.assertEqual(len(eur_clean), 50)  # half had claims collision

        eur_common = indexed.get(("FULL_PANEL", "EURUSD", "af", "COMMON_H240", 60, "1:1"), [])
        self.assertEqual(len(eur_common), 100)

        # Full panel combined pairs check
        full_all = indexed.get(("FULL_PANEL", "ALL_PAIRS_COMBINED", "af", "ALL_ELIGIBLE", 60, "1:1"), [])
        self.assertEqual(len(full_all), 100)

        # GBPUSD in COMMON_H240
        gbp_common = indexed.get(("FULL_PANEL", "GBPUSD", "ap", "COMMON_H240", 120, "2:2"), [])
        self.assertEqual(len(gbp_common), 0)  # is_common_h240 was False

    def test_verify_existing_package_synthetic_complete_success(self):
        """Verify that a complete, valid synthetic package passes read-only verification with 100% reconciliation."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            _build_valid_synthetic_package(td, family="CPI")
            res = verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertEqual(res["status"], "PASSED")
            self.assertEqual(res["trials_count"], 2)
            self.assertEqual(res["summary_cells_reconciled"], len(get_expected_summary_keys("CPI")))

    def test_verify_existing_package_fails_on_corrupted_metrics(self):
        """Verify that altered metrics (wins, percentages, duration, adjacent stability) fail closed."""
        import tempfile
        import csv

        # 1. Corrupted N_wins
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            sum_path = os.path.join(td, "summary_grid_results.csv")
            rows = list(pkg["summary_rows"])
            target_idx = next(i for i, r in enumerate(rows) if r["cell_label"] == "1:1" and int(r["N_trades"]) > 0)
            rows[target_idx] = dict(rows[target_idx])
            rows[target_idx]["N_wins"] = "99"  # False claim
            with open(sum_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["summary_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("N_wins mismatch", str(ctx.exception))

        # 2. Corrupted win_rate
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            sum_path = os.path.join(td, "summary_grid_results.csv")
            rows = list(pkg["summary_rows"])
            target_idx = next(i for i, r in enumerate(rows) if r["cell_label"] == "1:1" and int(r["N_trades"]) > 0)
            rows[target_idx] = dict(rows[target_idx])
            rows[target_idx]["win_rate"] = "0.9999"
            with open(sum_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["summary_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("win_rate mismatch", str(ctx.exception))

        # 3. Corrupted duration proxy seconds
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            sum_path = os.path.join(td, "summary_grid_results.csv")
            rows = list(pkg["summary_rows"])
            target_idx = next(i for i, r in enumerate(rows) if r["cell_label"] == "1:1" and int(r["N_trades"]) > 0)
            rows[target_idx] = dict(rows[target_idx])
            rows[target_idx]["tp_bar_close_proxy_seconds_median"] = "99999"
            with open(sum_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["summary_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("tp_bar_close_proxy_seconds_median mismatch", str(ctx.exception))

        # 4. Corrupted adjacent cell stability
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            sum_path = os.path.join(td, "summary_grid_results.csv")
            rows = list(pkg["summary_rows"])
            target_idx = next(i for i, r in enumerate(rows) if r["cell_label"] == "1:1" and int(r["N_trades"]) > 0)
            rows[target_idx] = dict(rows[target_idx])
            rows[target_idx]["adj_cells_count"] = "3"  # False claim
            with open(sum_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["summary_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("adj_cells_count mismatch", str(ctx.exception))

    def test_verify_existing_package_fails_on_missing_or_duplicate_summary_keys(self):
        """Verify that missing or duplicate summary grid rows fail closed."""
        import tempfile
        import csv

        # 1. Missing summary row
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            sum_path = os.path.join(td, "summary_grid_results.csv")
            rows = pkg["summary_rows"][:-1]  # drop last row
            with open(sum_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["summary_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Summary grid results missing 1 expected keys", str(ctx.exception))

        # 2. Duplicate summary row
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            sum_path = os.path.join(td, "summary_grid_results.csv")
            rows = [pkg["summary_rows"][0]] + pkg["summary_rows"]  # duplicate first row
            with open(sum_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["summary_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Duplicate summary row detected", str(ctx.exception))

    def test_verify_existing_package_fails_on_corrupted_annual_breakdown(self):
        """Verify that corrupted, missing, or duplicate annual breakdown rows fail closed."""
        import tempfile
        import csv

        # 1. Corrupted gross_mean_r in annual breakdown
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            ann_path = os.path.join(td, "annual_breakdown.csv")
            rows = list(pkg["annual_rows"])
            rows[0] = dict(rows[0])
            rows[0]["gross_mean_r"] = "9.999999"
            with open(ann_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["annual_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("gross_mean_r mismatch", str(ctx.exception))

        # 2. Missing annual row
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            ann_path = os.path.join(td, "annual_breakdown.csv")
            rows = pkg["annual_rows"][:-1]  # drop one
            with open(ann_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["annual_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Annual breakdown missing expected key", str(ctx.exception))

        # 3. Duplicate annual row
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            ann_path = os.path.join(td, "annual_breakdown.csv")
            rows = [pkg["annual_rows"][0]] + pkg["annual_rows"]
            with open(ann_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["annual_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Duplicate annual breakdown row", str(ctx.exception))

    def test_verify_existing_package_fails_on_corrupted_loyo_folds(self):
        """Verify that corrupted, missing, or duplicate LOYO fold rows fail closed."""
        import tempfile
        import csv

        # 1. Corrupted remaining_mean_r
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            loyo_path = os.path.join(td, "loyo_folds.csv")
            rows = list(pkg["loyo_rows"])
            rows[0] = dict(rows[0])
            rows[0]["remaining_mean_r"] = "-8.888888"
            with open(loyo_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["loyo_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("remaining_mean_r mismatch", str(ctx.exception))

        # 2. Missing LOYO fold row
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            loyo_path = os.path.join(td, "loyo_folds.csv")
            rows = pkg["loyo_rows"][:-1]  # drop one
            with open(loyo_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["loyo_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("LOYO folds missing expected fold", str(ctx.exception))

        # 3. Duplicate LOYO fold row
        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            loyo_path = os.path.join(td, "loyo_folds.csv")
            rows = [pkg["loyo_rows"][0]] + pkg["loyo_rows"]
            with open(loyo_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["loyo_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Duplicate LOYO fold row", str(ctx.exception))
    def test_verify_existing_package_rejects_extra_annual_rows(self):
        """Verify that an extra unexpected annual row is rejected (not silently accepted)."""
        import tempfile
        import csv

        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            ann_path = os.path.join(td, "annual_breakdown.csv")
            # Inject a syntactically valid but completely unexpected extra annual row
            extra_row = dict(pkg["annual_rows"][0])
            extra_row["year"] = "2099"  # Impossible year, not in trial ledger
            rows = list(pkg["annual_rows"]) + [extra_row]
            with open(ann_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["annual_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Annual breakdown contains unexpected row", str(ctx.exception))

    def test_verify_existing_package_rejects_extra_loyo_rows(self):
        """Verify that an extra unexpected LOYO fold row is rejected (not silently accepted)."""
        import tempfile
        import csv

        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            loyo_path = os.path.join(td, "loyo_folds.csv")
            # Inject an extra row with an impossible excluded_year
            extra_row = dict(pkg["loyo_rows"][0])
            extra_row["excluded_year"] = "2099"  # Not a valid excluded year in any fold
            rows = list(pkg["loyo_rows"]) + [extra_row]
            with open(loyo_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["loyo_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("LOYO folds contains unexpected row", str(ctx.exception))

    def test_verify_existing_package_rejects_manifest_mismatches(self):
        """Verify that manifest family, protocol_id, and run_id mismatches fail closed."""
        import tempfile
        import json
        import csv

        # 1. Family mismatch
        with tempfile.TemporaryDirectory() as td:
            _build_valid_synthetic_package(td, family="CPI")
            mpath = os.path.join(td, "manifest.json")
            with open(mpath, "r", encoding="utf-8") as f:
                mdata = json.load(f)
            mdata["family"] = "NFP"  # Wrong family
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(mdata, f)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Manifest family mismatch", str(ctx.exception))

        # 2. protocol_id mismatch
        with tempfile.TemporaryDirectory() as td:
            _build_valid_synthetic_package(td, family="CPI")
            mpath = os.path.join(td, "manifest.json")
            with open(mpath, "r", encoding="utf-8") as f:
                mdata = json.load(f)
            mdata["protocol_id"] = "CPI_EXPLORATION_V1"  # Wrong version
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(mdata, f)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Manifest protocol_id mismatch", str(ctx.exception))

        # 3. run_id mismatch
        with tempfile.TemporaryDirectory() as td:
            _build_valid_synthetic_package(td, family="CPI")
            mpath = os.path.join(td, "manifest.json")
            with open(mpath, "r", encoding="utf-8") as f:
                mdata = json.load(f)
            mdata["run_id"] = "run_99999999_v2"  # Wrong run_id
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(mdata, f)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("Manifest run_id mismatch", str(ctx.exception))

    def test_verify_tolerance_regression_sum_r_previously_passed(self):
        """Verify a gross_sum_r discrepancy that previously slipped through the old 1e-3 tolerance
        now correctly fails under the tightened 5e-5 tolerance.

        Old tolerance was abs_tol=1e-3 (0.001 R). New tolerance is 5e-5 (0.00005 R).
        A discrepancy of 0.0005 R (within old 1e-3, outside new 5e-5) must now fail closed.
        """
        import tempfile
        import csv

        with tempfile.TemporaryDirectory() as td:
            pkg = _build_valid_synthetic_package(td, family="CPI")
            sum_path = os.path.join(td, "summary_grid_results.csv")
            rows = list(pkg["summary_rows"])
            # Find any row with N_trades > 0
            target_idx = next(i for i, r in enumerate(rows) if int(r["N_trades"]) > 0)
            rows[target_idx] = dict(rows[target_idx])
            orig_sum_r = float(rows[target_idx]["gross_sum_r"])
            # Inject a discrepancy of 0.0005 R: within old 1e-3 tolerance but outside new 5e-5
            rows[target_idx]["gross_sum_r"] = f"{orig_sum_r + 0.0005:.4f}"
            with open(sum_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=pkg["summary_fields"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                verify_existing_package("CPI", package_dir_override=td, skip_raw_audit=True)
            self.assertIn("gross_sum_r mismatch", str(ctx.exception))

    def test_verify_intrabar_touch_uses_bar_close_proxy(self):
        """Verify intrabar touch exits (TARGET/STOP) use bar_close_sec for clock_seconds_bar_close_proxy,
        contrasting with opening-gap exits that use bar_open_sec."""
        t0 = 1577836800
        b1 = make_bar(0, 1.1000, 1.1060, 1.0980, 1.1010,
                      time_str="2020.01.01 00:00:00", timestamp=t0)
        # Bar 2 triggers intrabar TARGET hit (high >= 1.1100). timestamp = t0 + 3600.
        b2 = make_bar(1, 1.1020, 1.1110, 1.1010, 1.1080,
                      time_str="2020.01.01 01:00:00", timestamp=t0 + 3600)

        out = simulate_single_trade(
            entry_price=1.1000, direction=1, atr=0.0050,
            stop_atr=1.0, target_atr=2.0, path_bars=[b1, b2], pip_size=0.0001
        )
        self.assertTrue(out.is_win)
        self.assertEqual(out.exit_reason, "TARGET")
        self.assertFalse(out.is_opening_gap)

        # For intrabar touch: bar_open_sec = t0+3600 - t0 = 3600; bar_close_sec = 7200
        self.assertEqual(out.clock_seconds_to_exit_bar_open, 3600)
        self.assertEqual(out.clock_seconds_to_exit_bar_close, 7200)
        # CRITICAL: intrabar touch proxy = bar_close (upper bound), NOT bar_open
        self.assertEqual(out.clock_seconds_bar_close_proxy, 7200)
        self.assertNotEqual(out.clock_seconds_bar_close_proxy, out.clock_seconds_to_exit_bar_open)


def _build_valid_synthetic_package(td: str, family: str = "CPI") -> Dict[str, Any]:
    """Helper that creates a complete, 100% internally consistent synthetic package in directory td."""
    import json
    import csv

    manifest_data = {
        "family": family,
        "protocol_id": f"{family}_EXPLORATION_V2",
        "run_id": RUN_ID,  # Must match default run_id passed to verify_existing_package
        "trials_count": 2,
        "audit_verification": []
    }
    with open(os.path.join(td, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    with open(os.path.join(td, "release_paths.csv"), "w", encoding="utf-8") as f:
        f.write("dummy\n")

    with open(os.path.join(td, "EXPLORATION_SUMMARY_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("# Synthetic Report\n")

    ledger_header = [
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
    ]
    row1 = [
        "CPI_100_EURUSD_af_60_1:1", "100", "1500000000", "2017.07.14", "2017", "CORE_2015_2025",
        "EURUSD", "QUOTE", "af", "POSITIVE", "0.2", "-1",
        "False", "False", "True",
        "2017.07.14 17:00:00", "1.140000", "0.00500000", "60",
        "1", "1", "1:1", "1.0000",
        "TARGET", "True", "False", "False", "False", "False",
        "1.135000", "5", "2017.07.14 22:00:00", "5",
        "14400", "18000",
        "1.00000000", "50.0000", "", "", "",
        "0.0", "50.0", "0.0", "10.0",
        "0.0", "1.0", "0.0", "0.2",
        "50.0", "10.0", "1.0", "0.2",
        "TARGET", "1.00000000", "50.0000"
    ]
    row2 = [
        "CPI_101_EURUSD_af_60_1:1", "101", "1505000000", "2018.09.14", "2018", "CORE_2015_2025",
        "EURUSD", "QUOTE", "af", "POSITIVE", "0.1", "-1",
        "False", "False", "True",
        "2018.09.14 17:00:00", "1.190000", "0.00500000", "60",
        "1", "1", "1:1", "1.0000",
        "STOP", "False", "True", "False", "False", "False",
        "1.195000", "3", "2018.09.14 20:00:00", "3",
        "7200", "10800",
        "-1.00000000", "-50.0000", "", "", "",
        "0.0", "10.0", "0.0", "50.0",
        "0.0", "0.2", "0.0", "1.0",
        "10.0", "50.0", "0.2", "1.0",
        "STOP", "-1.00000000", "-50.0000"
    ]
    with open(os.path.join(td, "trial_ledger.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(ledger_header)
        w.writerow(row1)
        w.writerow(row2)

    trial_records = [
        {
            "obs_id": row1[0], "bundle_id": row1[1], "year": row1[4], "cohort": row1[5],
            "pair": row1[6], "signal_type": row1[8], "horizon": int(row1[18]), "horizon_bars": int(row1[18]),
            "cell_label": row1[21], "stop_atr": float(row1[19]), "target_atr": float(row1[20]),
            "rr": float(row1[22]),
            "is_win": True, "is_loss": False, "is_timeout": False, "dual_touch": False,
            "gross_r": float(row1[35]), "signed_pips": float(row1[36]),
            "bars_to_exit": int(row1[32]),
            "clock_seconds_to_bar_open": int(row1[33]),
            "clock_seconds_bar_close_proxy": int(row1[34]),
            "claims_collision": False, "cad_collision": False, "is_common_h240": True, "h240_complete": True
        },
        {
            "obs_id": row2[0], "bundle_id": row2[1], "year": row2[4], "cohort": row2[5],
            "pair": row2[6], "signal_type": row2[8], "horizon": int(row2[18]), "horizon_bars": int(row2[18]),
            "cell_label": row2[21], "stop_atr": float(row2[19]), "target_atr": float(row2[20]),
            "rr": float(row2[22]),
            "is_win": False, "is_loss": True, "is_timeout": False, "dual_touch": False,
            "gross_r": float(row2[35]), "signed_pips": float(row2[36]),
            "bars_to_exit": int(row2[32]),
            "clock_seconds_to_bar_open": int(row2[33]),
            "clock_seconds_bar_close_proxy": int(row2[34]),
            "claims_collision": False, "cad_collision": False, "is_common_h240": True, "h240_complete": True
        }
    ]

    indexed_trials = index_trial_records(trial_records, family)
    expected_keys = get_expected_summary_keys(family)

    summary_fields = [
        "panel", "pair", "signal_type", "cohort_filter", "horizon_bars", "stop_atr", "target_atr",
        "cell_label", "reward_risk", "N_bundles", "N_trades", "N_wins", "N_losses", "N_timeouts", "N_dual_touch",
        "pct_target", "pct_stop", "pct_timeout", "pct_dual_touch",
        "win_rate", "gross_mean_r", "gross_median_r", "gross_sum_r",
        "tp_bars_median", "tp_bars_p75", "tp_bars_p90", "tp_bars_max",
        "tp_bar_close_proxy_seconds_median", "tp_bar_close_proxy_seconds_p75",
        "tp_bar_close_proxy_seconds_p90", "tp_bar_close_proxy_seconds_max",
        "sl_bars_median", "sl_bars_p75", "sl_bars_p90", "sl_bars_max",
        "sl_bar_close_proxy_seconds_median", "sl_bar_close_proxy_seconds_p75",
        "sl_bar_close_proxy_seconds_p90", "sl_bar_close_proxy_seconds_max",
        "overall_bars_median", "overall_bars_p75", "overall_bars_p90", "overall_bars_max",
        "overall_bar_close_proxy_seconds_median", "overall_bar_close_proxy_seconds_p75",
        "overall_bar_close_proxy_seconds_p90", "overall_bar_close_proxy_seconds_max",
        "loyo_positive_years", "loyo_total_folds",
        "loyo_min_mean_r", "loyo_max_mean_r", "loyo_min_sum_r", "loyo_max_sum_r",
        "adj_cells_count", "adj_mean_gross_r", "adj_delta_mean_r", "adj_min_mean_r", "adj_max_mean_r", "adj_all_positive"
    ]

    summary_rows = []
    annual_rows = []
    loyo_rows = []

    # Precompute cell_mean_r_map for adjacent cell stability
    cohort_cell_means: Dict[Tuple[str, str, str, str, int], Dict[str, float]] = defaultdict(dict)
    for (pan, pr, sig, ch, h, cell_l), sub_trials in indexed_trials.items():
        if sub_trials:
            cohort_cell_means[(pan, pr, sig, ch, h)][cell_l] = sum(r["gross_r"] for r in sub_trials) / len(sub_trials)

    for skey in sorted(list(expected_keys)):
        pan, pr, sig, ch, h, cell_lbl = skey
        cell = next(c for c in ALL_GRID_CELLS if c.label == cell_lbl)
        sub = indexed_trials.get(skey, [])
        cohort_means = cohort_cell_means.get((pan, pr, sig, ch, h), {})
        adj = calculate_adjacent_cell_stability(cell_lbl, cohort_means)

        if sub:
            n_trades = len(sub)
            n_bundles = len(set(r["bundle_id"] for r in sub))
            n_wins = sum(1 for r in sub if r["is_win"])
            n_losses = sum(1 for r in sub if r["is_loss"])
            n_timeouts = sum(1 for r in sub if r["is_timeout"])
            n_dual = sum(1 for r in sub if r["dual_touch"])
            r_vals = [r["gross_r"] for r in sub]
            dist = summarize_exit_distributions(sub)
            loyo = calculate_true_loyo(sub)
            ann = summarize_annual_breakdown(sub)

            s_row = {
                "panel": pan, "pair": pr, "signal_type": sig, "cohort_filter": ch, "horizon_bars": str(h),
                "stop_atr": str(cell.stop_atr), "target_atr": str(cell.target_atr), "cell_label": cell_lbl,
                "reward_risk": f"{cell.reward_risk_ratio:.4f}",
                "N_bundles": str(n_bundles), "N_trades": str(n_trades), "N_wins": str(n_wins),
                "N_losses": str(n_losses), "N_timeouts": str(n_timeouts), "N_dual_touch": str(n_dual),
                "pct_target": f"{n_wins / n_trades:.4f}",
                "pct_stop": f"{n_losses / n_trades:.4f}",
                "pct_timeout": f"{n_timeouts / n_trades:.4f}",
                "pct_dual_touch": f"{n_dual / n_trades:.4f}",
                "win_rate": f"{n_wins / n_trades:.4f}",
                "gross_mean_r": f"{sum(r_vals) / n_trades:.6f}",
                "gross_median_r": f"{calculate_median(r_vals):.6f}",
                "gross_sum_r": f"{sum(r_vals):.4f}",
                "tp_bars_median": format_optional_float(dist["tp_median_bars"], ".1f"),
                "tp_bars_p75": format_optional_float(dist["tp_p75_bars"], ".1f"),
                "tp_bars_p90": format_optional_float(dist["tp_p90_bars"], ".1f"),
                "tp_bars_max": format_optional_float(dist["tp_max_bars"], ".1f"),
                "tp_bar_close_proxy_seconds_median": format_optional_float(dist["tp_bar_close_proxy_seconds_median"], ".0f"),
                "tp_bar_close_proxy_seconds_p75": format_optional_float(dist["tp_bar_close_proxy_seconds_p75"], ".0f"),
                "tp_bar_close_proxy_seconds_p90": format_optional_float(dist["tp_bar_close_proxy_seconds_p90"], ".0f"),
                "tp_bar_close_proxy_seconds_max": format_optional_float(dist["tp_bar_close_proxy_seconds_max"], ".0f"),
                "sl_bars_median": format_optional_float(dist["sl_median_bars"], ".1f"),
                "sl_bars_p75": format_optional_float(dist["sl_p75_bars"], ".1f"),
                "sl_bars_p90": format_optional_float(dist["sl_p90_bars"], ".1f"),
                "sl_bars_max": format_optional_float(dist["sl_max_bars"], ".1f"),
                "sl_bar_close_proxy_seconds_median": format_optional_float(dist["sl_bar_close_proxy_seconds_median"], ".0f"),
                "sl_bar_close_proxy_seconds_p75": format_optional_float(dist["sl_bar_close_proxy_seconds_p75"], ".0f"),
                "sl_bar_close_proxy_seconds_p90": format_optional_float(dist["sl_bar_close_proxy_seconds_p90"], ".0f"),
                "sl_bar_close_proxy_seconds_max": format_optional_float(dist["sl_bar_close_proxy_seconds_max"], ".0f"),
                "overall_bars_median": format_optional_float(dist["overall_median_bars"], ".1f"),
                "overall_bars_p75": format_optional_float(dist["overall_p75_bars"], ".1f"),
                "overall_bars_p90": format_optional_float(dist["overall_p90_bars"], ".1f"),
                "overall_bars_max": format_optional_float(dist["overall_max_bars"], ".1f"),
                "overall_bar_close_proxy_seconds_median": format_optional_float(dist["overall_bar_close_proxy_seconds_median"], ".0f"),
                "overall_bar_close_proxy_seconds_p75": format_optional_float(dist["overall_bar_close_proxy_seconds_p75"], ".0f"),
                "overall_bar_close_proxy_seconds_p90": format_optional_float(dist["overall_bar_close_proxy_seconds_p90"], ".0f"),
                "overall_bar_close_proxy_seconds_max": format_optional_float(dist["overall_bar_close_proxy_seconds_max"], ".0f"),
                "loyo_positive_years": f"{loyo['loyo_positive_years']}/{loyo['loyo_total_folds']}",
                "loyo_total_folds": str(loyo["loyo_total_folds"]),
                "loyo_min_mean_r": format_optional_float(loyo["loyo_min_mean_r"], ".4f"),
                "loyo_max_mean_r": format_optional_float(loyo["loyo_max_mean_r"], ".4f"),
                "loyo_min_sum_r": format_optional_float(loyo["loyo_min_sum_r"], ".4f"),
                "loyo_max_sum_r": format_optional_float(loyo["loyo_max_sum_r"], ".4f"),
                "adj_cells_count": str(adj["adj_cells_count"]),
                "adj_mean_gross_r": format_optional_float(adj["adj_mean_gross_r"], ".6f"),
                "adj_delta_mean_r": format_optional_float(adj["adj_delta_mean_r"], ".6f"),
                "adj_min_mean_r": format_optional_float(adj["adj_min_mean_r"], ".6f"),
                "adj_max_mean_r": format_optional_float(adj["adj_max_mean_r"], ".6f"),
                "adj_all_positive": str(adj["adj_all_positive"]) if adj["adj_cells_count"] > 0 else "",
            }
            summary_rows.append(s_row)

            for yr, ay in sorted(ann.items()):
                yr_sub = [r for r in sub if str(r["year"]) == yr]
                annual_rows.append({
                    "panel": pan, "pair": pr, "signal_type": sig, "cohort_filter": ch, "horizon_bars": str(h),
                    "cell_label": cell_lbl, "year": yr, "cohort": ay["cohort"],
                    "N_bundles": str(len(set(r["bundle_id"] for r in yr_sub))),
                    "N_trades": str(ay["n"]), "N_wins": str(ay["wins"]), "N_losses": str(ay["losses"]),
                    "N_timeouts": str(ay["timeouts"]),
                    "win_rate": f"{ay['win_rate']:.4f}",
                    "gross_sum_r": f"{ay['gross_sum_r']:.4f}",
                    "gross_mean_r": f"{ay['gross_mean_r']:.6f}"
                })

            for fy, f_info in sorted(loyo["loyo_folds"].items()):
                rem_trials = [r for r in sub if str(r["year"]) != fy and "2015" <= str(r.get("year", "")) <= "2025"]
                loyo_rows.append({
                    "panel": pan, "pair": pr, "signal_type": sig, "cohort_filter": ch, "horizon_bars": str(h),
                    "cell_label": cell_lbl, "excluded_year": fy,
                    "remaining_bundles": str(len(set(r["bundle_id"] for r in rem_trials))),
                    "remaining_trades": str(f_info["remaining_n"]),
                    "remaining_wins": str(f_info["wins"]),
                    "remaining_losses": str(f_info["losses"]),
                    "remaining_timeouts": str(f_info["timeouts"]),
                    "remaining_sum_r": f"{f_info['gross_sum_r']:.4f}",
                    "remaining_mean_r": f"{f_info['gross_mean_r']:.6f}",
                    "is_positive": str(f_info["is_positive"])
                })
        else:
            s_row = {
                "panel": pan, "pair": pr, "signal_type": sig, "cohort_filter": ch, "horizon_bars": str(h),
                "stop_atr": str(cell.stop_atr), "target_atr": str(cell.target_atr), "cell_label": cell_lbl,
                "reward_risk": f"{cell.reward_risk_ratio:.4f}",
                "N_bundles": "0", "N_trades": "0", "N_wins": "0", "N_losses": "0", "N_timeouts": "0", "N_dual_touch": "0",
                "pct_target": "0.0000", "pct_stop": "0.0000", "pct_timeout": "0.0000", "pct_dual_touch": "0.0000",
                "win_rate": "0.0000", "gross_mean_r": "0.000000", "gross_median_r": "0.000000", "gross_sum_r": "0.0000",
                "tp_bars_median": "", "tp_bars_p75": "", "tp_bars_p90": "", "tp_bars_max": "",
                "tp_bar_close_proxy_seconds_median": "", "tp_bar_close_proxy_seconds_p75": "",
                "tp_bar_close_proxy_seconds_p90": "", "tp_bar_close_proxy_seconds_max": "",
                "sl_bars_median": "", "sl_bars_p75": "", "sl_bars_p90": "", "sl_bars_max": "",
                "sl_bar_close_proxy_seconds_median": "", "sl_bar_close_proxy_seconds_p75": "",
                "sl_bar_close_proxy_seconds_p90": "", "sl_bar_close_proxy_seconds_max": "",
                "overall_bars_median": "", "overall_bars_p75": "", "overall_bars_p90": "", "overall_bars_max": "",
                "overall_bar_close_proxy_seconds_median": "", "overall_bar_close_proxy_seconds_p75": "",
                "overall_bar_close_proxy_seconds_p90": "", "overall_bar_close_proxy_seconds_max": "",
                "loyo_positive_years": "0/0", "loyo_total_folds": "0",
                "loyo_min_mean_r": "", "loyo_max_mean_r": "", "loyo_min_sum_r": "", "loyo_max_sum_r": "",
                "adj_cells_count": str(adj["adj_cells_count"]),
                "adj_mean_gross_r": format_optional_float(adj["adj_mean_gross_r"], ".6f"),
                "adj_delta_mean_r": format_optional_float(adj["adj_delta_mean_r"], ".6f"),
                "adj_min_mean_r": format_optional_float(adj["adj_min_mean_r"], ".6f"),
                "adj_max_mean_r": format_optional_float(adj["adj_max_mean_r"], ".6f"),
                "adj_all_positive": str(adj["adj_all_positive"]) if adj["adj_cells_count"] > 0 else "",
            }
            summary_rows.append(s_row)

    with open(os.path.join(td, "summary_grid_results.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=summary_fields)
        w.writeheader()
        w.writerows(summary_rows)

    annual_fields = [
        "panel", "pair", "signal_type", "cohort_filter", "horizon_bars", "cell_label",
        "year", "cohort", "N_bundles", "N_trades", "N_wins", "N_losses", "N_timeouts",
        "win_rate", "gross_sum_r", "gross_mean_r"
    ]
    with open(os.path.join(td, "annual_breakdown.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=annual_fields)
        w.writeheader()
        w.writerows(annual_rows)

    loyo_fields = [
        "panel", "pair", "signal_type", "cohort_filter", "horizon_bars", "cell_label",
        "excluded_year", "remaining_bundles", "remaining_trades", "remaining_wins",
        "remaining_losses", "remaining_timeouts", "remaining_sum_r", "remaining_mean_r",
        "is_positive"
    ]
    with open(os.path.join(td, "loyo_folds.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=loyo_fields)
        w.writeheader()
        w.writerows(loyo_rows)

    return {
        "summary_fields": summary_fields,
        "summary_rows": summary_rows,
        "annual_fields": annual_fields,
        "annual_rows": annual_rows,
        "loyo_fields": loyo_fields,
        "loyo_rows": loyo_rows,
    }


if __name__ == "__main__":
    unittest.main()
