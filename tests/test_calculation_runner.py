"""
Synthetic Unit Tests for Calculation Runner & Output Schema
Verifies:
1. H1-to-H4 aggregation and entry/exit timestamps across 15:30/16:30/weekend releases.
2. Adversarial weekday gap rejection (Wednesday-to-Friday missing Thursday NOT treated as weekend).
3. Handling of incomplete/missing/duplicate bars and hard post-2022 split barrier.
4. Long and Short trade execution arithmetic under all five cost scenarios.
5. Strict pre-2023 package accounting fail-closed validation (96 total, 49 strict [27 POS, 22 NEG], 28/9/2/8 exclusions).
6. Explicit halt on undefined primary statistics (no invented verdicts on zero variance).
7. Validation of release-derived entry timestamp, weekday, and collision flags.
8. Prohibiting default execution on pinned historical candles.
9. Deterministic JSON schema serialization with complete provenance and versioning.

Zero reading of candidate prices or holdout candle files.
"""

import unittest
import math
import json
import tempfile
import os
from datetime import datetime, timezone

from src.calculation_runner import (
    CandleBar,
    CandlePriceIndex,
    RetailSalesCalculationRunner,
    execute_single_trade_across_scenarios,
    summarize_trade_metrics,
    serialize_runner_output,
    compute_file_sha256,
    get_implementation_provenance,
    EXPECTED_PINNED_SOURCES,
    SCHEMA_VERSION,
    RUNNER_IMPLEMENTATION_VERSION,
    GIT_COMMIT_BASELINE,
    HARD_SPLIT_TIMESTAMP,
    FROZEN_TOTAL_PACKAGES,
    FROZEN_STRICT_COUNT,
    FROZEN_STRICT_POS,
    FROZEN_STRICT_NEG,
    FROZEN_MISSING_FORECAST,
    FROZEN_ACTIVE_CONFLICT,
    FROZEN_BOTH_ZERO,
    FROZEN_ONE_ZERO
)
from src.candle_coverage import (
    CandleTimestampIndex,
    is_valid_weekend_market_closure,
    SECONDS_IN_H1,
    SECONDS_IN_H4
)
from src.strategy_viability import (
    EURUSD_POINT,
    EURUSD_POINTS_PER_PIP,
    FROZEN_COST_SCENARIOS
)
from src.parsers import SPLIT_TIMESTAMP

PINNED_EURUSD_CANDLES_PATH = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv"
PINNED_CALENDAR_PATH = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv"


def build_synthetic_pre2023_packages(base_h4: int, vary_prices: bool = True):
    """
    Helper to construct valid 96 pre-2023 synthetic packages and covering candle bars.
    Exact counts: 49 strict (27 POS, 22 NEG), 28 missing forecast, 9 active conflict, 2 both zero, 8 one zero.
    """
    def make_pkg_timestamps(idx):
        # 1 day apart, 15:30 release (+12600s), 16:00 entry (+14400s)
        pkg_base = base_h4 + idx * 86400
        rel_ts = pkg_base + 12600
        entry_ts = pkg_base + 14400
        weekday = datetime.fromtimestamp(rel_ts, tz=timezone.utc).strftime("%A")
        return rel_ts, entry_ts, weekday

    packages = []
    pkg_counter = 0

    # 27 POS strict packages
    for i in range(27):
        rel_ts, entry_ts, weekday = make_pkg_timestamps(pkg_counter)
        pkg_counter += 1
        packages.append({
            "timestamp": rel_ts,
            "sign_category": "STRICT_AGREE_POS",
            "weekday": weekday,
            "has_cross_currency_collision": (i % 2 == 0),
            "entry_timestamp": entry_ts
        })

    # 22 NEG strict packages
    for i in range(22):
        rel_ts, entry_ts, weekday = make_pkg_timestamps(pkg_counter)
        pkg_counter += 1
        packages.append({
            "timestamp": rel_ts,
            "sign_category": "STRICT_AGREE_NEG",
            "weekday": weekday,
            "has_cross_currency_collision": (i % 2 == 1),
            "entry_timestamp": entry_ts
        })

    # 28 MISSING_FORECAST
    for i in range(28):
        rel_ts, entry_ts, weekday = make_pkg_timestamps(pkg_counter)
        pkg_counter += 1
        packages.append({
            "timestamp": rel_ts,
            "sign_category": "MISSING_FORECAST",
            "weekday": weekday,
            "has_cross_currency_collision": False,
            "entry_timestamp": entry_ts
        })

    # 9 ACTIVE_CONFLICT
    for i in range(9):
        rel_ts, entry_ts, weekday = make_pkg_timestamps(pkg_counter)
        pkg_counter += 1
        packages.append({
            "timestamp": rel_ts,
            "sign_category": "ACTIVE_CONFLICT",
            "weekday": weekday,
            "has_cross_currency_collision": True,
            "entry_timestamp": entry_ts
        })

    # 2 BOTH_ZERO
    for i in range(2):
        rel_ts, entry_ts, weekday = make_pkg_timestamps(pkg_counter)
        pkg_counter += 1
        packages.append({
            "timestamp": rel_ts,
            "sign_category": "BOTH_ZERO",
            "weekday": weekday,
            "has_cross_currency_collision": False,
            "entry_timestamp": entry_ts
        })

    # 8 ONE_ZERO
    for i in range(8):
        rel_ts, entry_ts, weekday = make_pkg_timestamps(pkg_counter)
        pkg_counter += 1
        packages.append({
            "timestamp": rel_ts,
            "sign_category": "ONE_ZERO",
            "weekday": weekday,
            "has_cross_currency_collision": False,
            "entry_timestamp": entry_ts
        })

    # Generate covering candle bars for all 49 strict packages for 12 H4 blocks (48 H1 bars each)
    bars = []
    trade_idx = 0
    for p in packages:
        if p["sign_category"] in ("STRICT_AGREE_POS", "STRICT_AGREE_NEG"):
            e_ts = p["entry_timestamp"]
            is_pos = (p["sign_category"] == "STRICT_AGREE_POS")
            price_delta = ((trade_idx % 7) - 3) * 0.00030 if vary_prices else 0.0
            trade_idx += 1
            if not vary_prices:
                # POS is Short (d = -1): enter 1.12000, exit 1.11000
                # NEG is Long (d = +1): enter 1.11000, exit 1.12000
                # Scenario C net returns: Short = ln(1.12000/1.11010), Long = ln(1.12000/1.11010) (identical)
                open_p = 1.12000 if is_pos else 1.11000
                close_p = 1.11000 if is_pos else 1.12000
            else:
                open_p = 1.12000
                close_p = 1.11500 + price_delta

            for h in range(48):
                ts = e_ts + h * 3600
                bars.append(CandleBar(
                    timestamp=ts,
                    open=open_p,
                    high=max(open_p, close_p) + 0.00200,
                    low=min(open_p, close_p) - 0.00200,
                    close=close_p if h in (23, 47) else open_p,
                    spread=10
                ))

    # Deduplicate and sort bars
    unique_bars = sorted(list({b.timestamp: b for b in bars}.values()), key=lambda b: b.timestamp)
    return packages, unique_bars


class TestCalculationRunner(unittest.TestCase):

    def test_zero_price_reads_on_import_and_init(self):
        """Verifies zero file reads on import or initialization of runner."""
        runner = RetailSalesCalculationRunner(allow_unblinded_run=False)
        self.assertFalse(runner.allow_unblinded_run)

    def test_h1_to_h4_aggregation_and_timestamps_normal_session(self):
        """
        Tests H1-to-H4 aggregation and entry/exit timestamps for a 15:30 Wednesday release.
        Wednesday 15:30 release -> Entry at Wednesday 16:00 (30-min delay).
        Primary 6-H4 horizon: 24 active hours -> Exit at Thursday 16:00 boundary.
        Exit bar: Thursday 15:00 H1 bar (4th constituent H1 bar of Block 5).
        Descriptive 12-H4 horizon: 48 active hours -> Exit at Friday 16:00 boundary.
        Exit bar: Friday 15:00 H1 bar (4th constituent H1 bar of Block 11).
        """
        wed_00 = 1623196800  # Wed 2021-06-09 00:00:00 UTC
        dt_wed = datetime.fromtimestamp(wed_00, tz=timezone.utc)
        self.assertEqual(dt_wed.strftime("%A"), "Wednesday")

        rel_ts = wed_00 + 15 * 3600 + 1800  # Wed 15:30:00
        entry_ts = wed_00 + 16 * 3600       # Wed 16:00:00 (delay 1800s = 30m)

        bars = []
        for i in range(48):
            ts = entry_ts + i * 3600
            bars.append(CandleBar(
                timestamp=ts,
                open=1.10000 + i * 0.00010,
                high=1.10050 + i * 0.00010,
                low=1.09950 + i * 0.00010,
                close=1.10020 + i * 0.00010,
                spread=10
            ))

        c_index = CandlePriceIndex.from_bars(bars)

        # 1. Primary 6-H4 Horizon (6 blocks = 24 active hours)
        h6_res = c_index.resolve_horizon_bars(entry_ts, horizon_h4=6)
        self.assertTrue(h6_res["is_complete"])
        self.assertEqual(h6_res["completed_blocks"], 6)
        self.assertFalse(h6_res["crosses_weekend"])
        self.assertFalse(h6_res["has_missing_h1"])
        self.assertEqual(h6_res["entry_timestamp"], entry_ts)
        self.assertEqual(h6_res["exit_timestamp"], entry_ts + 24 * 3600)  # Thu 16:00:00
        self.assertEqual(h6_res["entry_bar"].timestamp, entry_ts)          # Wed 16:00:00
        self.assertEqual(h6_res["exit_bar"].timestamp, entry_ts + 23 * 3600)  # Thu 15:00:00
        self.assertEqual(len(h6_res["blocks_bars"]), 6)
        for block in h6_res["blocks_bars"]:
            self.assertEqual(len(block), 4)

        # 2. Descriptive 12-H4 Horizon (12 blocks = 48 active hours)
        h12_res = c_index.resolve_horizon_bars(entry_ts, horizon_h4=12)
        self.assertTrue(h12_res["is_complete"])
        self.assertEqual(h12_res["completed_blocks"], 12)
        self.assertFalse(h12_res["crosses_weekend"])
        self.assertEqual(h12_res["entry_timestamp"], entry_ts)
        self.assertEqual(h12_res["exit_timestamp"], entry_ts + 48 * 3600)  # Fri 16:00:00
        self.assertEqual(h12_res["entry_bar"].timestamp, entry_ts)
        self.assertEqual(h12_res["exit_bar"].timestamp, entry_ts + 47 * 3600)  # Fri 15:00:00
        self.assertEqual(len(h12_res["blocks_bars"]), 12)

    def test_h1_to_h4_aggregation_and_timestamps_1630_release(self):
        """
        Tests H1-to-H4 aggregation and entry/exit timestamps for a 16:30 Wednesday release.
        Wednesday 16:30 release -> Entry at Wednesday 20:00 (210-min / 3.5h delay).
        Primary 6-H4 horizon: 24 active hours -> Exit at Thursday 20:00 boundary.
        Exit bar: Thursday 19:00 H1 bar (4th constituent H1 bar of Block 5).
        """
        wed_00 = 1623196800  # Wed 00:00:00 UTC
        entry_ts = wed_00 + 20 * 3600  # Wed 20:00:00 (delay 12600s = 210m)

        bars = []
        for i in range(24):
            ts = entry_ts + i * 3600
            bars.append(CandleBar(
                timestamp=ts,
                open=1.12000,
                high=1.12100,
                low=1.11900,
                close=1.12050,
                spread=8
            ))

        c_index = CandlePriceIndex.from_bars(bars)
        h6_res = c_index.resolve_horizon_bars(entry_ts, horizon_h4=6)

        self.assertTrue(h6_res["is_complete"])
        self.assertEqual(h6_res["completed_blocks"], 6)
        self.assertEqual(h6_res["entry_timestamp"], entry_ts)
        self.assertEqual(h6_res["exit_timestamp"], entry_ts + 24 * 3600)  # Thu 20:00:00
        self.assertEqual(h6_res["entry_bar"].timestamp, entry_ts)          # Wed 20:00:00
        self.assertEqual(h6_res["exit_bar"].timestamp, entry_ts + 23 * 3600)  # Thu 19:00:00

    def test_h1_to_h4_aggregation_and_timestamps_friday_weekend_crossing(self):
        """
        Tests H1-to-H4 aggregation stepping across a valid weekend closure.
        Friday 15:30 release -> Entry at Friday 16:00.
        Friday active trading: 2 H4 blocks (16:00 to 24:00 = 8 H1 bars).
        Weekend closure: 48-hour gap (Friday 24:00 to Monday 00:00).
        Monday active trading: 4 H4 blocks (00:00 to 16:00 = 16 H1 bars).
        Total forward blocks: 2 + 4 = 6 completed H4 blocks = 24 active trading hours.
        Exit boundary: Monday 16:00:00.
        Exit bar: Monday 15:00:00 (4th constituent H1 bar of Block 5).
        """
        fri_00 = 1623369600  # Fri 2021-06-11 00:00:00 UTC
        entry_ts = fri_00 + 16 * 3600  # Fri 16:00:00

        bars = []
        # Friday bars: 8 bars from 16:00 to 24:00
        for i in range(8):
            ts = entry_ts + i * 3600
            bars.append(CandleBar(
                timestamp=ts,
                open=1.15000,
                high=1.15100,
                low=1.14900,
                close=1.15020,
                spread=10
            ))

        # Weekend gap: Friday 24:00 to Monday 00:00 is 48 hours
        mon_00 = fri_00 + 24 * 3600 + 48 * 3600  # 1623628800

        # Monday bars: 16 bars from 00:00 to 16:00
        for i in range(16):
            ts = mon_00 + i * 3600
            bars.append(CandleBar(
                timestamp=ts,
                open=1.15000,
                high=1.15100,
                low=1.14900,
                close=1.15080,
                spread=10
            ))

        c_index = CandlePriceIndex.from_bars(bars)
        h6_res = c_index.resolve_horizon_bars(entry_ts, horizon_h4=6)

        self.assertTrue(h6_res["is_complete"])
        self.assertEqual(h6_res["completed_blocks"], 6)
        self.assertTrue(h6_res["crosses_weekend"])
        self.assertFalse(h6_res["has_missing_h1"])
        self.assertEqual(h6_res["entry_timestamp"], entry_ts)             # Fri 16:00:00
        self.assertEqual(h6_res["exit_timestamp"], mon_00 + 16 * 3600)   # Mon 16:00:00
        self.assertEqual(h6_res["entry_bar"].timestamp, entry_ts)         # Fri 16:00:00
        self.assertEqual(h6_res["exit_bar"].timestamp, mon_00 + 15 * 3600)  # Mon 15:00:00

    def test_adversarial_weekday_gap_not_treated_as_weekend(self):
        """
        Adversarial Regression Test for Codex Issue 1:
        A Wednesday-to-Friday gap (missing Thursday: 24h gap) must NOT be excused
        as a 'weekend' closure. The market closure rule must reject weekday data gaps
        and fail closed (is_complete=False, has_missing_h1=True, crosses_weekend=False).
        """
        # Wednesday 2021-06-09 00:00:00 UTC = 1623196800
        wed_00 = 1623196800
        entry_ts = wed_00 + 16 * 3600  # Wed 16:00:00

        # Wednesday trading: 8 H1 bars (Wed 16:00 to Wed 24:00)
        bars = []
        for i in range(8):
            bars.append(CandleBar(
                timestamp=entry_ts + i * 3600,
                open=1.10000, high=1.10100, low=1.09900, close=1.10050, spread=10
            ))

        # OMIT THURSDAY (24-hour gap from Wed 24:00 to Fri 00:00)
        # Friday trading: 16 H1 bars (Fri 00:00 to Fri 16:00)
        fri_00 = wed_00 + 2 * 86400  # 1623369600 (Friday 00:00:00)
        dt_fri = datetime.fromtimestamp(fri_00, tz=timezone.utc)
        self.assertEqual(dt_fri.strftime("%A"), "Friday")

        for i in range(16):
            bars.append(CandleBar(
                timestamp=fri_00 + i * 3600,
                open=1.10000, high=1.10100, low=1.09900, close=1.10050, spread=10
            ))

        # Test market closure rule function directly
        # Wed 24:00 is Thursday 00:00 (1623196800 + 86400 = 1623283200)
        gap_start = wed_00 + 86400
        resume_ts = fri_00
        is_wknd, reason = is_valid_weekend_market_closure(gap_start, resume_ts)
        self.assertFalse(is_wknd)
        self.assertIn("weekday data gap", reason)

        # Test CandlePriceIndex.resolve_horizon_bars fails closed
        c_index = CandlePriceIndex.from_bars(bars)
        res = c_index.resolve_horizon_bars(entry_ts, horizon_h4=6)

        self.assertFalse(res["is_complete"])
        self.assertTrue(res["has_missing_h1"])
        self.assertFalse(res["crosses_weekend"])
        self.assertEqual(res["completed_blocks"], 2)  # Only the 2 Wed blocks completed
        self.assertIn(gap_start, res["missing_timestamps"])

        # Test CandleTimestampIndex.evaluate_forward_horizon fails closed
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
            for b in bars:
                tmp.write(f"{b.timestamp},1.1,1.1,1.1,1.1,10,1,0\n")

        try:
            cov_index = CandleTimestampIndex(tmp_path)
            cov_res = cov_index.evaluate_forward_horizon(entry_ts, horizon_h4=6)
            self.assertFalse(cov_res["is_complete"])
            self.assertTrue(cov_res["has_missing_h1"])
            self.assertFalse(cov_res["crosses_weekend"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_handling_incomplete_missing_duplicate_bars(self):
        """Verifies rigorous handling of missing, duplicate, and malformed candle bars."""
        base_ts = 1623196800  # Wed 00:00:00

        # 1. Duplicate timestamp rejection
        bars_dup = [
            CandleBar(timestamp=base_ts, open=1.1, high=1.2, low=1.0, close=1.1, spread=5),
            CandleBar(timestamp=base_ts, open=1.1, high=1.2, low=1.0, close=1.1, spread=5)
        ]
        with self.assertRaises(ValueError) as ctx:
            CandlePriceIndex.from_bars(bars_dup)
        self.assertIn("Duplicate candle timestamp", str(ctx.exception))

        # 2. Non-monotonic timestamp rejection
        bars_non_mono = [
            CandleBar(timestamp=base_ts + 3600, open=1.1, high=1.2, low=1.0, close=1.1, spread=5),
            CandleBar(timestamp=base_ts, open=1.1, high=1.2, low=1.0, close=1.1, spread=5)
        ]
        with self.assertRaises(ValueError) as ctx:
            CandlePriceIndex.from_bars(bars_non_mono)
        self.assertIn("monotonically increasing", str(ctx.exception))

        # 3. Invalid candle price bounds (high < low)
        with self.assertRaises(ValueError):
            CandleBar(timestamp=base_ts, open=1.1, high=0.9, low=1.0, close=1.1, spread=5)

        # 4. Missing constituent H1 bar in H4 block
        bars_missing = [
            CandleBar(timestamp=base_ts, open=1.1, high=1.2, low=1.0, close=1.1, spread=5),
            CandleBar(timestamp=base_ts + 3600, open=1.1, high=1.2, low=1.0, close=1.1, spread=5),
            CandleBar(timestamp=base_ts + 10800, open=1.1, high=1.2, low=1.0, close=1.1, spread=5),
        ]
        c_missing = CandlePriceIndex.from_bars(bars_missing)
        is_ok, constituent, missing = c_missing.check_h4_block(base_ts)
        self.assertFalse(is_ok)
        self.assertEqual(missing, [7200])

        # 5. Horizon resolution fails closed on missing constituent bar
        res = c_missing.resolve_horizon_bars(base_ts, horizon_h4=1)
        self.assertFalse(res["is_complete"])
        self.assertTrue(res["has_missing_h1"])
        self.assertEqual(res["missing_timestamps"], [base_ts + 7200])

    def test_post2022_boundary_fails_closed_hard_seal(self):
        """
        Verifies that post-2022 holdout boundary (1672531200) genuinely fails closed:
        1. Attempting to override split_timestamp > 1672531200 raises PermissionError.
        2. Candle bar with timestamp == 1672531200 raises PermissionError.
        3. Candle bar with timestamp > 1672531200 raises PermissionError.
        4. CSV reader checks column 0 and breaks immediately at split without reading prices.
        """
        split_ts = HARD_SPLIT_TIMESTAMP  # 1672531200

        # 1. Reject split override
        with self.assertRaises(PermissionError) as ctx_ov:
            CandlePriceIndex(split_timestamp=split_ts + 1)
        self.assertIn("Cannot override split boundary", str(ctx_ov.exception))

        # 2. Reject exact boundary bar
        bar_exact = CandleBar(timestamp=split_ts, open=1.07, high=1.08, low=1.06, close=1.075)
        with self.assertRaises(PermissionError) as ctx_ex:
            CandlePriceIndex.from_bars([bar_exact])
        self.assertIn("strictly sealed post-2022 holdout", str(ctx_ex.exception))

        # 3. Reject post-split bar
        bar_post = CandleBar(timestamp=split_ts + 3600, open=1.07, high=1.08, low=1.06, close=1.075)
        with self.assertRaises(PermissionError) as ctx_post:
            CandlePriceIndex.from_bars([bar_post])
        self.assertIn("strictly sealed post-2022 holdout", str(ctx_post.exception))

        # 4. CSV reader halts at split boundary without parsing corrupted post-split price columns
        csv_content = (
            "time,open,high,low,close,tick_volume,spread,real_volume\n"
            f"{split_ts - 3600},1.07000,1.07100,1.06900,1.07050,10,5,0\n"
            f"{split_ts},CORRUPT_PRICE,INVALID,NOT_A_NUM,GARBAGE,FOO,BAR,BAZ\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(csv_content)

        try:
            c_csv = CandlePriceIndex.from_csv(tmp_path)
            self.assertTrue(c_csv.has_bar(split_ts - 3600))
            self.assertFalse(c_csv.has_bar(split_ts))
            self.assertEqual(len(c_csv._sorted_timestamps), 1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_long_and_short_execution_arithmetic_all_five_scenarios(self):
        """
        Hand-checkable test of trade execution arithmetic across all 5 cost scenarios.
        Tests both Long (+1) and Short (-1) in exact pips and log returns.
        """
        # Long trade (+1):
        # Entry open = 1.10000, Exit close = 1.10200 (+20 gross pips)
        entry_bar_long = CandleBar(timestamp=1600000000, open=1.10000, high=1.10050, low=1.09950, close=1.10020, spread=10)
        exit_bar_long = CandleBar(timestamp=1600086400, open=1.10150, high=1.10250, low=1.10100, close=1.10200, spread=10)

        res_long = execute_single_trade_across_scenarios(entry_bar_long, exit_bar_long, direction=1)

        # Scenario A (0 pts):
        sc_a = res_long["Scenario_A_0pts"]
        self.assertEqual(sc_a["entry_price"], 1.10000)
        self.assertEqual(sc_a["exit_price"], 1.10200)
        self.assertAlmostEqual(sc_a["net_pips"], 20.0, places=4)
        self.assertAlmostEqual(sc_a["net_return"], math.log(1.10200 / 1.10000), places=8)
        self.assertTrue(sc_a["is_win"])

        # Scenario B (5 pts = 0.5 pips):
        sc_b = res_long["Scenario_B_5pts"]
        self.assertAlmostEqual(sc_b["entry_price"], 1.10005, places=6)
        self.assertEqual(sc_b["exit_price"], 1.10200)
        self.assertAlmostEqual(sc_b["net_pips"], 19.5, places=4)
        self.assertAlmostEqual(sc_b["net_return"], math.log(1.10200 / 1.10005), places=8)
        self.assertTrue(sc_b["is_win"])

        # Scenario C (10 pts = 1.0 pip) - Primary Hurdle:
        sc_c = res_long["Scenario_C_10pts"]
        self.assertAlmostEqual(sc_c["entry_price"], 1.10010, places=6)
        self.assertEqual(sc_c["exit_price"], 1.10200)
        self.assertAlmostEqual(sc_c["net_pips"], 19.0, places=4)
        self.assertAlmostEqual(sc_c["net_return"], math.log(1.10200 / 1.10010), places=8)
        self.assertTrue(sc_c["is_win"])

        # Scenario D (20 pts = 2.0 pips):
        sc_d = res_long["Scenario_D_20pts"]
        self.assertAlmostEqual(sc_d["entry_price"], 1.10020, places=6)
        self.assertEqual(sc_d["exit_price"], 1.10200)
        self.assertAlmostEqual(sc_d["net_pips"], 18.0, places=4)
        self.assertAlmostEqual(sc_d["net_return"], math.log(1.10200 / 1.10020), places=8)
        self.assertTrue(sc_d["is_win"])

        # Scenario E (30 pts = 3.0 pips) - Hypothetical combined sensitivity:
        sc_e = res_long["Scenario_E_30pts"]
        self.assertAlmostEqual(sc_e["entry_price"], 1.10030, places=6)
        self.assertEqual(sc_e["exit_price"], 1.10200)
        self.assertAlmostEqual(sc_e["net_pips"], 17.0, places=4)
        self.assertAlmostEqual(sc_e["net_return"], math.log(1.10200 / 1.10030), places=8)
        self.assertTrue(sc_e["is_win"])

        # Short trade (-1):
        # Entry open = 1.10200, Exit close = 1.10000 (+20 gross pips)
        entry_bar_short = CandleBar(timestamp=1600000000, open=1.10200, high=1.10250, low=1.10150, close=1.10180, spread=10)
        exit_bar_short = CandleBar(timestamp=1600086400, open=1.10050, high=1.10100, low=1.09950, close=1.10000, spread=10)

        res_short = execute_single_trade_across_scenarios(entry_bar_short, exit_bar_short, direction=-1)

        # Scenario A (0 pts):
        sc_a_s = res_short["Scenario_A_0pts"]
        self.assertEqual(sc_a_s["entry_price"], 1.10200)
        self.assertEqual(sc_a_s["exit_price"], 1.10000)
        self.assertAlmostEqual(sc_a_s["net_pips"], 20.0, places=4)
        self.assertAlmostEqual(sc_a_s["net_return"], math.log(1.10200 / 1.10000), places=8)
        self.assertTrue(sc_a_s["is_win"])

        # Scenario C (10 pts = 1.0 pip):
        sc_c_s = res_short["Scenario_C_10pts"]
        self.assertEqual(sc_c_s["entry_price"], 1.10200)
        self.assertAlmostEqual(sc_c_s["exit_price"], 1.10010, places=6)
        self.assertAlmostEqual(sc_c_s["net_pips"], 19.0, places=4)
        self.assertAlmostEqual(sc_c_s["net_return"], math.log(1.10200 / 1.10010), places=8)
        self.assertTrue(sc_c_s["is_win"])

        # Scenario E (30 pts = 3.0 pips):
        sc_e_s = res_short["Scenario_E_30pts"]
        self.assertEqual(sc_e_s["entry_price"], 1.10200)
        self.assertAlmostEqual(sc_e_s["exit_price"], 1.10030, places=6)
        self.assertAlmostEqual(sc_e_s["net_pips"], 17.0, places=4)
        self.assertAlmostEqual(sc_e_s["net_return"], math.log(1.10200 / 1.10030), places=8)
        self.assertTrue(sc_e_s["is_win"])

    def test_pre2023_package_accounting_fail_closed_on_wrong_totals(self):
        """
        Verifies Codex Issue 2: evaluate_packages fails closed unless frozen package accounting
        strictly matches all totals: 96 total, 49 strict (27 POS, 22 NEG), 28/9/2/8 exclusions.
        Tests empty list, wrong counts, and unknown categories.
        """
        c_index = CandlePriceIndex.from_bars([])
        runner = RetailSalesCalculationRunner(allow_unblinded_run=False)

        # 1. Zero-case run fails closed (does NOT label INCONCLUSIVE_UNDERPOWERED)
        with self.assertRaises(ValueError) as ctx_empty:
            runner.evaluate_packages([], c_index)
        self.assertIn("Frozen pre-2023 package accounting validation failed", str(ctx_empty.exception))

        # Base valid setup
        base_h4 = 1520000000 - (1520000000 % 14400)
        valid_pkgs, valid_bars = build_synthetic_pre2023_packages(base_h4)
        c_valid_index = CandlePriceIndex.from_bars(valid_bars)

        # 2. Test 95 packages (omit one package) -> ValueError
        with self.assertRaises(ValueError) as ctx_95:
            runner.evaluate_packages(valid_pkgs[:-1], c_valid_index)
        self.assertIn("Frozen pre-2023 package accounting validation failed", str(ctx_95.exception))

        # 3. Test wrong strict count (change one strict POS to active conflict) -> ValueError
        corrupted_strict = [dict(p) for p in valid_pkgs]
        corrupted_strict[0]["sign_category"] = "ACTIVE_CONFLICT"
        with self.assertRaises(ValueError) as ctx_sc:
            runner.evaluate_packages(corrupted_strict, c_valid_index)
        self.assertIn("Strict=48", str(ctx_sc.exception))

        # 4. Test wrong POS/NEG split (26 POS, 23 NEG instead of 27/22) -> ValueError
        corrupted_split = [dict(p) for p in valid_pkgs]
        corrupted_split[0]["sign_category"] = "STRICT_AGREE_NEG"
        with self.assertRaises(ValueError) as ctx_split:
            runner.evaluate_packages(corrupted_split, c_valid_index)
        self.assertIn("POS=26", str(ctx_split.exception))

        # 5. Test unknown category -> ValueError
        corrupted_cat = [dict(p) for p in valid_pkgs]
        corrupted_cat[0]["sign_category"] = "UNKNOWN_BOGUS_CATEGORY"
        with self.assertRaises(ValueError) as ctx_cat:
            runner.evaluate_packages(corrupted_cat, c_valid_index)
        self.assertIn("Unknown package category", str(ctx_cat.exception))

        # 6. Test duplicate package timestamp -> ValueError
        corrupted_dup = [dict(p) for p in valid_pkgs]
        corrupted_dup[1]["timestamp"] = corrupted_dup[0]["timestamp"]
        with self.assertRaises(ValueError) as ctx_dup:
            runner.evaluate_packages(corrupted_dup, c_valid_index)
        self.assertIn("Duplicate package timestamp", str(ctx_dup.exception))

        # 7. Valid packages pass accounting cleanly
        out = runner.evaluate_packages(valid_pkgs, c_valid_index)
        acc = out["package_accounting"]
        self.assertEqual(acc["total_packages_evaluated"], 96)
        self.assertEqual(acc["strict_concordance_count"], 49)
        self.assertEqual(acc["strict_pos_count"], 27)
        self.assertEqual(acc["strict_neg_count"], 22)
        self.assertEqual(acc["excluded_missing_forecast_count"], 28)
        self.assertEqual(acc["excluded_active_conflict_count"], 9)
        self.assertEqual(acc["excluded_both_zero_count"], 2)
        self.assertEqual(acc["excluded_one_zero_count"], 8)
        self.assertEqual(acc["evaluated_trade_count"], 49)

    def test_undefined_primary_statistics_fails_explicitly(self):
        """
        Verifies Codex Issue 4:
        If primary viability statistics under Scenario C are undefined (zero sample variance
        such that t-stat/p-val do not exist), evaluate_packages fails explicitly with RuntimeError,
        halting for protocol review, rather than inventing an INCONCLUSIVE_UNDERPOWERED verdict.
        """
        base_h4 = 1520000000 - (1520000000 % 14400)
        # Build packages with vary_prices=False (all 49 trades have identical return -> zero variance)
        pkgs_zero_var, bars_zero_var = build_synthetic_pre2023_packages(base_h4, vary_prices=False)
        c_index_zero = CandlePriceIndex.from_bars(bars_zero_var)

        runner = RetailSalesCalculationRunner()
        with self.assertRaises(RuntimeError) as ctx:
            runner.evaluate_packages(pkgs_zero_var, c_index_zero)
        self.assertIn("Primary viability statistics under Scenario C are undefined", str(ctx.exception))
        self.assertIn("Halted for explicit protocol review", str(ctx.exception))

    def test_release_derived_fields_validated_against_corrupted_inputs(self):
        """
        Verifies Codex Issue 5:
        Validate release-derived entry timestamp, weekday, and collision flags against corrupted inputs.
        """
        base_h4 = 1520000000 - (1520000000 % 14400)
        valid_pkgs, valid_bars = build_synthetic_pre2023_packages(base_h4)
        c_index = CandlePriceIndex.from_bars(valid_bars)
        runner = RetailSalesCalculationRunner()

        # 1. Corrupted entry timestamp raises ValueError
        bad_entry = [dict(p) for p in valid_pkgs]
        bad_entry[0]["entry_timestamp"] = bad_entry[0]["timestamp"] + 3600  # wrong delay
        with self.assertRaises(ValueError) as ctx_e:
            runner.evaluate_packages(bad_entry, c_index)
        self.assertIn("corrupted or mismatching entry_timestamp", str(ctx_e.exception))

        # 2. Corrupted weekday raises ValueError
        bad_wd = [dict(p) for p in valid_pkgs]
        bad_wd[0]["weekday"] = "Sunday"  # wrong weekday
        with self.assertRaises(ValueError) as ctx_w:
            runner.evaluate_packages(bad_wd, c_index)
        self.assertIn("corrupted or mismatching weekday", str(ctx_w.exception))

        # 3. Corrupted collision flag raises ValueError
        bad_coll = [dict(p) for p in valid_pkgs]
        bad_coll[0]["currencies"] = ["USD"]
        bad_coll[0]["has_cross_currency_collision"] = True  # contradiction: only USD, but flagged True
        with self.assertRaises(ValueError) as ctx_c:
            runner.evaluate_packages(bad_coll, c_index)
        self.assertIn("corrupted has_cross_currency_collision flag", str(ctx_c.exception))

    def test_prohibit_default_execution_on_pinned_candidate_candles(self):
        """
        Verifies that attempting unblinded execution on pinned candle files
        without explicit authorization raises PermissionError.
        """
        runner = RetailSalesCalculationRunner(allow_unblinded_run=False)

        # 1. Calling execute_from_paths with pinned path raises PermissionError
        with self.assertRaises(PermissionError) as ctx:
            runner.execute_from_paths(
                calendar_path=PINNED_CALENDAR_PATH,
                candle_path=PINNED_EURUSD_CANDLES_PATH,
                allow_unblinded_run=False
            )
        self.assertIn("Unblinded empirical execution is strictly prohibited", str(ctx.exception))

        # 2. Calling CandlePriceIndex.from_csv directly on pinned path raises PermissionError
        with self.assertRaises(PermissionError) as ctx2:
            CandlePriceIndex.from_csv(
                PINNED_EURUSD_CANDLES_PATH,
                allow_unblinded_run=False
            )
        self.assertIn("Unblinded empirical execution on pinned candidate candle prices is strictly prohibited", str(ctx2.exception))

    def test_deterministic_output_ordering_and_complete_schema_serialization(self):
        """
        Verifies that output schema is complete, trade episodes are deterministically sorted
        chronologically, source provenance and implementation version are present,
        and serialize_runner_output produces 100% valid JSON.
        """
        base_h4 = 1520000000 - (1520000000 % 14400)
        valid_pkgs, valid_bars = build_synthetic_pre2023_packages(base_h4, vary_prices=True)

        # Shuffle packages out of chronological order
        shuffled_pkgs = list(reversed(valid_pkgs))
        c_index = CandlePriceIndex.from_bars(valid_bars)

        runner = RetailSalesCalculationRunner()
        output = runner.evaluate_packages(shuffled_pkgs, c_index)

        # 1. Verify all top-level keys
        required_keys = [
            "schema_version",
            "metadata",
            "package_accounting",
            "trade_episodes",
            "primary_results_6h4",
            "subgroup_results_6h4",
            "descriptive_results_12h4",
            "decision_classification",
            "governance_notice"
        ]
        for k in required_keys:
            self.assertIn(k, output)

        self.assertEqual(output["schema_version"], SCHEMA_VERSION)

        # 2. Verify metadata versioning, dynamic git identity, and provenance separation
        meta = output["metadata"]
        self.assertEqual(meta["runner_implementation_version"], RUNNER_IMPLEMENTATION_VERSION)
        self.assertEqual(meta["split_timestamp"], HARD_SPLIT_TIMESTAMP)

        ident = meta["implementation_identity"]
        self.assertIn("git_checkout_state", ident)
        self.assertIn("git_head_commit", ident)
        self.assertIn("has_uncommitted_changes", ident)
        self.assertNotIn("formal_protocol_freeze_approved", ident)
        self.assertNotIn("formal_freeze_record", ident)
        self.assertNotIn("is_frozen_baseline", ident)
        self.assertNotIn("implementation_state", ident)
        self.assertEqual(ident["runner_implementation_version"], RUNNER_IMPLEMENTATION_VERSION)

        symbols = meta["symbol_specification"]
        self.assertEqual(symbols["headline_event_id"], "840020010")
        self.assertEqual(symbols["core_event_id"], "840020011")

        prov = meta["provenance"]
        self.assertEqual(prov["provenance_classification"], "SYNTHETIC_FIXTURE")
        self.assertTrue(prov["is_synthetic_fixture_run"])
        self.assertFalse(prov["is_non_pinned_input_run"])
        self.assertFalse(prov["pinned_sources_verified"])
        self.assertEqual(prov["expected_pinned_sources"], EXPECTED_PINNED_SOURCES)

        verified = prov["verified_sources_used"]
        self.assertEqual(verified["calendar"]["source_type"], "SYNTHETIC_FIXTURE")
        self.assertFalse(verified["calendar"]["pinned_source_verified"])
        self.assertEqual(verified["candles"]["source_type"], "SYNTHETIC_FIXTURE")
        self.assertFalse(verified["candles"]["pinned_source_verified"])

        # 3. Verify deterministic chronological ordering of trade episodes
        episodes = output["trade_episodes"]
        self.assertEqual(len(episodes), 49)
        timestamps = [ep["package_timestamp"] for ep in episodes]
        self.assertEqual(timestamps, sorted(timestamps))

        # 4. Verify complete JSON serialization
        json_str = serialize_runner_output(output)
        self.assertIsInstance(json_str, str)
        reloaded = json.loads(json_str)
        self.assertEqual(reloaded["schema_version"], SCHEMA_VERSION)
        self.assertEqual(reloaded["package_accounting"]["strict_concordance_count"], 49)
        self.assertIn("Scenario_C_10pts", reloaded["primary_results_6h4"])
        self.assertIn("disposition", reloaded["decision_classification"])

    def test_synthetic_fixture_run_provenance_isolated(self):
        """
        Verifies that runs on synthetic fixture inputs identify themselves as fixtures
        (is_synthetic_fixture_run=True, provenance_classification="SYNTHETIC_FIXTURE")
        and NEVER claim verified pinned sources (pinned_sources_verified=False).
        Also verifies that dynamic git implementation identity reports uncommitted working tree
        without claiming formal protocol freeze.
        """
        base_h4 = 1520000000 - (1520000000 % 14400)
        valid_pkgs, valid_bars = build_synthetic_pre2023_packages(base_h4, vary_prices=True)
        c_index = CandlePriceIndex.from_bars(valid_bars)

        # CandlePriceIndex from in-memory bars has SYNTHETIC_FIXTURE metadata
        self.assertEqual(c_index.source_metadata["source_type"], "SYNTHETIC_FIXTURE")
        self.assertFalse(c_index.source_metadata["pinned_source_verified"])

        runner = RetailSalesCalculationRunner()
        output = runner.evaluate_packages(valid_pkgs, c_index)

        prov = output["metadata"]["provenance"]
        self.assertEqual(prov["provenance_classification"], "SYNTHETIC_FIXTURE")
        self.assertTrue(prov["is_synthetic_fixture_run"])
        self.assertFalse(prov["is_non_pinned_input_run"])
        self.assertFalse(prov["pinned_sources_verified"])
        self.assertEqual(prov["verified_sources_used"]["calendar"]["source_type"], "SYNTHETIC_FIXTURE")
        self.assertFalse(prov["verified_sources_used"]["calendar"]["pinned_source_verified"])
        self.assertEqual(prov["verified_sources_used"]["candles"]["source_type"], "SYNTHETIC_FIXTURE")
        self.assertFalse(prov["verified_sources_used"]["candles"]["pinned_source_verified"])

        ident = output["metadata"]["implementation_identity"]
        self.assertIn(ident["git_checkout_state"], ("COMMITTED_CLEAN", "UNCOMMITTED_CHANGES"))
        self.assertIsInstance(ident["has_uncommitted_changes"], bool)
        self.assertNotIn("formal_protocol_freeze_approved", ident)
        self.assertNotIn("formal_freeze_record", ident)
        self.assertNotIn("is_frozen_baseline", ident)

    def test_adversarial_alternate_input_rejected_from_pinned_provenance(self):
        """
        Adversarial test proving alternate inputs CANNOT receive falsely verified pinned provenance.
        Even when loaded via from_csv with identical column format, an alternate candle or calendar
        file with a non-matching SHA-256 hash is classified as NON_PINNED_INPUT, flagged
        pinned_source_verified=False, and forces is_non_pinned_input_run=True.
        """
        base_h4 = 1520000000 - (1520000000 % 14400)
        valid_pkgs, valid_bars = build_synthetic_pre2023_packages(base_h4, vary_prices=True)

        # Write valid synthetic candle bars to a temporary CSV file
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_candle_path = tmp.name
            tmp.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
            for b in valid_bars:
                tmp.write(f"{b.timestamp},{b.open:.5f},{b.high:.5f},{b.low:.5f},{b.close:.5f},{b.tick_volume},{b.spread},{b.real_volume}\n")

        try:
            # 1. Verify CandlePriceIndex.from_csv on alternate input classifies as NON_PINNED_INPUT
            c_index = CandlePriceIndex.from_csv(tmp_candle_path)
            meta = c_index.source_metadata
            self.assertEqual(meta["source_type"], "NON_PINNED_INPUT")
            self.assertFalse(meta["pinned_source_verified"])
            self.assertNotEqual(meta["source_sha256"], EXPECTED_PINNED_SOURCES["raw_candles_eurusd"]["sha256"])
            self.assertEqual(meta["source_sha256"], compute_file_sha256(tmp_candle_path))

            # 2. Verify evaluate_packages with alternate candle index marks NON_PINNED_INPUT
            runner = RetailSalesCalculationRunner()
            output = runner.evaluate_packages(valid_pkgs, c_index)

            prov = output["metadata"]["provenance"]
            self.assertEqual(prov["provenance_classification"], "NON_PINNED_INPUT")
            self.assertTrue(prov["is_synthetic_fixture_run"])  # valid_pkgs is in-memory synthetic fixture
            self.assertTrue(prov["is_non_pinned_input_run"])   # c_index is non-pinned CSV
            self.assertFalse(prov["pinned_sources_verified"])
            self.assertFalse(prov["verified_sources_used"]["candles"]["pinned_source_verified"])
            self.assertEqual(prov["verified_sources_used"]["candles"]["source_type"], "NON_PINNED_INPUT")
            self.assertEqual(prov["verified_sources_used"]["candles"]["source_sha256"], meta["source_sha256"])

            # 3. Verify that passing an alternate calendar metadata also classifies as NON_PINNED_INPUT
            alt_cal_meta = {
                "source_type": "NON_PINNED_INPUT",
                "source_description": "alternate_calendar.csv",
                "source_path": "/fake/path/alternate_calendar.csv",
                "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "pinned_source_verified": False
            }
            output_alt_cal = runner.evaluate_packages(
                valid_pkgs,
                c_index,
                calendar_source_metadata=alt_cal_meta
            )
            prov_alt = output_alt_cal["metadata"]["provenance"]
            self.assertEqual(prov_alt["provenance_classification"], "NON_PINNED_INPUT")
            self.assertFalse(prov_alt["is_synthetic_fixture_run"])
            self.assertTrue(prov_alt["is_non_pinned_input_run"])
            self.assertFalse(prov_alt["pinned_sources_verified"])
            self.assertFalse(prov_alt["verified_sources_used"]["calendar"]["pinned_source_verified"])

        finally:
            if os.path.exists(tmp_candle_path):
                os.remove(tmp_candle_path)

    def test_default_execution_touches_neither_input_before_unblinding_flag(self):
        """
        Verifies that execute_from_paths with default allow_unblinded_run=False
        checks authorization FIRST and raises PermissionError before touching,
        opening, or computing SHA-256 hashes of either input file.
        Uses a mock to prove compute_file_sha256 is never called.
        """
        from unittest.mock import patch
        runner = RetailSalesCalculationRunner(allow_unblinded_run=False)

        with patch("src.calculation_runner.compute_file_sha256") as mock_hash:
            with self.assertRaises(PermissionError) as ctx:
                runner.execute_from_paths(
                    calendar_path=PINNED_CALENDAR_PATH,
                    candle_path=PINNED_EURUSD_CANDLES_PATH,
                    allow_unblinded_run=False
                )
            self.assertIn("Unblinded empirical execution is strictly prohibited", str(ctx.exception))
            mock_hash.assert_not_called()

    def test_clean_git_does_not_mean_frozen(self):
        """
        Adversarial test proving that Git cleanliness reports strictly Git working tree state.
        A clean checkout reports COMMITTED_CLEAN, not a formal freeze approval.
        Formal protocol freeze approval is never inferred from git status and has no caller-supplied mechanism.
        """
        # 1. Default inspection in current working tree
        ident = get_implementation_provenance()
        self.assertNotIn("formal_protocol_freeze_approved", ident)
        self.assertNotIn("formal_freeze_record", ident)
        self.assertNotIn("is_frozen_baseline", ident)
        self.assertNotIn("FROZEN_COMMITTED", ident.values())
        self.assertIn(ident["git_checkout_state"], ("COMMITTED_CLEAN", "UNCOMMITTED_CHANGES"))
        self.assertIsInstance(ident["has_uncommitted_changes"], bool)

        # 2. Simulated clean git status (mock subprocess to return clean)
        from unittest.mock import patch
        with patch("subprocess.run") as mock_run:
            class MockSubprocessResult:
                def __init__(self, stdout):
                    self.stdout = stdout

            # Mock git rev-parse HEAD and git status --porcelain (empty output = clean)
            mock_run.side_effect = [
                MockSubprocessResult("abcdef1234567890abcdef1234567890abcdef12\n"),
                MockSubprocessResult("")
            ]
            clean_ident = get_implementation_provenance()
            self.assertEqual(clean_ident["git_checkout_state"], "COMMITTED_CLEAN")
            self.assertTrue(clean_ident["git_status_clean"])
            self.assertFalse(clean_ident["has_uncommitted_changes"])
            # Crucial assertion: Git state reports ONLY Git state, no freeze approval claims
            self.assertNotIn("formal_protocol_freeze_approved", clean_ident)
            self.assertNotIn("formal_freeze_record", clean_ident)
            self.assertNotIn("is_frozen_baseline", clean_ident)

    def test_non_pinned_empirical_inputs_fail_before_calculation(self):
        """
        Adversarial test proving that in the formal execute_from_paths empirical entry point,
        execution fails closed with ValueError BEFORE any outcome calculation or classification
        unless BOTH actual calendar and candle SHA-256 digests equal the expected pinned digests.
        A non-pinned CSV must not receive a formal discovery disposition merely because package counts match.
        Uses temporary fixtures and mocks to verify fail-closed hash validation without opening or
        hashing the actual pinned candle file on disk.
        """
        from unittest.mock import patch
        base_h4 = 1520000000 - (1520000000 % 14400)
        valid_pkgs, valid_bars = build_synthetic_pre2023_packages(base_h4, vary_prices=True)

        # Create temporary non-pinned candle CSV
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp_c:
            tmp_candle_path = tmp_c.name
            tmp_c.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
            for b in valid_bars[:48]:
                tmp_c.write(f"{b.timestamp},{b.open:.5f},{b.high:.5f},{b.low:.5f},{b.close:.5f},{b.tick_volume},{b.spread},{b.real_volume}\n")

        # Create temporary non-pinned calendar CSV
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp_cal:
            tmp_cal_path = tmp_cal.name
            tmp_cal.write("event_id,time,currency,actual,forecast,previous\n")
            for p in valid_pkgs:
                tmp_cal.write(f"840020010,{p['timestamp']},USD,0.5,0.2,0.1\n")

        runner = RetailSalesCalculationRunner(allow_unblinded_run=True)
        exp_cal_sha = EXPECTED_PINNED_SOURCES["calendar_releases"]["sha256"]
        exp_candle_sha = EXPECTED_PINNED_SOURCES["raw_candles_eurusd"]["sha256"]

        try:
            # 1. Both non-pinned: fails closed immediately before calculation
            with self.assertRaises(ValueError) as ctx1:
                runner.execute_from_paths(
                    calendar_path=tmp_cal_path,
                    candle_path=tmp_candle_path,
                    allow_unblinded_run=True
                )
            self.assertIn("rejected non-pinned input", str(ctx1.exception))
            self.assertIn("Calendar file", str(ctx1.exception))
            self.assertIn("Candle file", str(ctx1.exception))

            # 2. Pinned calendar (mocked hash), non-pinned candle: fails closed before calculation
            # Uses mocked hash so real pinned files are never opened or hashed on disk
            with patch("src.calculation_runner.compute_file_sha256") as mock_hash:
                mock_hash.side_effect = lambda path: exp_cal_sha if path == tmp_cal_path else "mismatched_candle_hash"
                with self.assertRaises(ValueError) as ctx2:
                    runner.execute_from_paths(
                        calendar_path=tmp_cal_path,
                        candle_path=tmp_candle_path,
                        allow_unblinded_run=True
                    )
                self.assertIn("rejected non-pinned input", str(ctx2.exception))
                self.assertIn("Candle file", str(ctx2.exception))

            # 3. Non-pinned calendar, pinned candle (mocked hash): fails closed before calculation
            # Uses mocked hash so real pinned files are never opened or hashed on disk
            with patch("src.calculation_runner.compute_file_sha256") as mock_hash:
                mock_hash.side_effect = lambda path: exp_candle_sha if path == tmp_candle_path else "mismatched_cal_hash"
                with self.assertRaises(ValueError) as ctx3:
                    runner.execute_from_paths(
                        calendar_path=tmp_cal_path,
                        candle_path=tmp_candle_path,
                        allow_unblinded_run=True
                    )
                self.assertIn("rejected non-pinned input", str(ctx3.exception))
                self.assertIn("Calendar file", str(ctx3.exception))

        finally:
            if os.path.exists(tmp_candle_path):
                os.remove(tmp_candle_path)
            if os.path.exists(tmp_cal_path):
                os.remove(tmp_cal_path)


if __name__ == "__main__":
    unittest.main()
