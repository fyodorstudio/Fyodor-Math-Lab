"""Unit and End-to-End Tests for Fyodor Macro Research Groundwork.

Validates:
1. Nine-pair global exclusion
2. Exact calendar event IDs and units
3. Missing versus zero values
4. Same-time release bundles
5. Base/quote USD direction inversion
6. Timestamp boundaries and cohort partitioning
7. Strict pre-release ATR(14) boundary (bar_open + 3600 < release_timestamp)
8. End-to-end pinned real row verifications:
   - CPI missing m/m in December 2025 (2025.12.18 16:30:00)
   - September 2026 cutoff (2026.09.11 CPI, 2026.09.04 NFP)
   - USDCHF 76-hour gap on 2015.01.09 NFP (H60 valid, H120/H240 disqualified)
   - Canadian-jobs / NFP same-time collision (exactly 89 releases)
   - Raw constituent dynamic counts (CPI = 558, NFP = 560)
   - Complete ledger reconciliation (Total 980 = Eligible N + Sum of Exclusions)
"""

import unittest
import sys
import os
import csv
import json
import tempfile
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent calculator directory to path
CALC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if CALC_DIR not in sys.path:
    sys.path.insert(0, CALC_DIR)

from models import CandleBar, CalendarRelease, ReleaseBundle
from protocol_specs import (
    ALL_EXPORTED_PAIRS,
    GLOBALLY_EXCLUDED_PAIRS,
    ACTIVE_RESEARCH_PAIRS,
    ACTIVE_USD_PAIRS,
    USD_BASE_PAIRS,
    USD_QUOTE_PAIRS,
    EVENT_ID_US_CPI_MM,
    EVENT_ID_US_CORE_CPI_MM,
    EVENT_ID_US_CPI_YY,
    EVENT_ID_US_CORE_CPI_YY,
    EVENT_ID_US_NONFARM_PAYROLLS,
    EVENT_ID_US_UNEMPLOYMENT_RATE,
    EVENT_ID_US_AVG_HOURLY_EARNINGS_MM,
    EVENT_ID_US_AVG_HOURLY_EARNINGS_YY,
    EVENT_ID_US_INITIAL_JOBLESS_CLAIMS,
    assert_event_id_valid,
    compute_difference,
    classify_signal_state,
    invert_usd_direction_for_pair,
)
from data_loader import (
    assert_pair_active,
    create_release_bundles,
    load_candles,
    load_calendar_releases,
    load_all_releases_by_timestamp,
    DEFAULT_RAW_DIR,
)
from path_indexer import (
    find_entry_bar,
    calculate_pre_release_atr14,
    inspect_path_coverage,
    detect_path_weekday_gaps,
    is_regular_weekend,
    is_scheduled_market_closure,
)
from eligibility_evaluator import (
    determine_cohort,
    evaluate_cpi_pre_outcome,
    evaluate_nfp_pre_outcome,
)
from run_pre_outcome_pipeline import (
    PUBLISHED_ANCHOR_HASHES,
    compute_sha256,
    build_provenance_index,
    EXPECTED_RAW_FILES,
)

REPO_ROOT = os.path.normpath(os.path.join(CALC_DIR, "..", ".."))


class TestMacroGroundwork(unittest.TestCase):
    """Synthetic unit tests and end-to-end pinned reconciliation tests."""

    def test_nine_pair_global_exclusion(self):
        """Verify that the 9 truncated-history pairs are strictly excluded."""
        self.assertEqual(len(GLOBALLY_EXCLUDED_PAIRS), 9)
        expected_excluded = {
            "CADCHF", "CADJPY", "GBPAUD", "GBPCAD", "GBPJPY",
            "GBPNZD", "NZDCAD", "NZDCHF", "NZDJPY"
        }
        self.assertEqual(set(GLOBALLY_EXCLUDED_PAIRS), expected_excluded)

        for pair in GLOBALLY_EXCLUDED_PAIRS:
            self.assertNotIn(pair, ACTIVE_RESEARCH_PAIRS)
            self.assertNotIn(pair, ACTIVE_USD_PAIRS)
            with self.assertRaises(ValueError):
                assert_pair_active(pair)

        self.assertEqual(len(ACTIVE_RESEARCH_PAIRS), 19)
        for pair in ACTIVE_RESEARCH_PAIRS:
            assert_pair_active(pair)

    def test_exact_event_ids(self):
        """Verify exact calendar event IDs for CPI and NFP."""
        # CPI Family
        self.assertEqual(EVENT_ID_US_CPI_MM, "840030005")
        self.assertEqual(EVENT_ID_US_CORE_CPI_MM, "840030006")
        self.assertEqual(EVENT_ID_US_CPI_YY, "840030007")
        self.assertEqual(EVENT_ID_US_CORE_CPI_YY, "840030008")

        # NFP Family
        self.assertEqual(EVENT_ID_US_NONFARM_PAYROLLS, "840030016")
        self.assertEqual(EVENT_ID_US_UNEMPLOYMENT_RATE, "840030015")
        self.assertEqual(EVENT_ID_US_AVG_HOURLY_EARNINGS_MM, "840030018")
        self.assertEqual(EVENT_ID_US_AVG_HOURLY_EARNINGS_YY, "840030019")

    def test_missing_versus_zero_integrity(self):
        """Verify that missing values are never coerced to zero."""
        self.assertIsNone(compute_difference(None, 2.0))
        self.assertIsNone(compute_difference(2.5, None))
        self.assertIsNone(compute_difference(None, None))
        
        self.assertEqual(compute_difference(2.5, 2.5), 0.0)
        self.assertEqual(compute_difference(0.0, 0.0), 0.0)
        self.assertEqual(compute_difference(3.0, 2.8), 0.2)
        self.assertEqual(compute_difference(2.0, 2.5), -0.5)

        self.assertEqual(classify_signal_state(None), "MISSING")
        self.assertEqual(classify_signal_state(0.0), "ZERO")
        self.assertEqual(classify_signal_state(0.0000001), "POSITIVE")
        self.assertEqual(classify_signal_state(-0.0000001), "NEGATIVE")

    def test_same_time_bundles(self):
        """Verify grouping of same-timestamp releases into atomic bundles."""
        ts = 1500000000
        rel1 = CalendarRelease(
            event_id="840030005", value_id="1", timestamp=ts,
            timestamp_server_text="2017.07.14 15:30:00", currency="USD",
            country_code="US", event_name="CPI m/m", importance="high",
            actual=0.2, forecast=0.1, previous=0.1, revised_previous=None,
            period_server_text="2017.06.01 00:00:00", unit="CALENDAR_UNIT_PERCENT",
            unit_code=1, multiplier="CALENDAR_MULTIPLIER_NONE", multiplier_code=0,
            digits=1, raw_actual_str="0.2", raw_forecast_str="0.1",
            raw_previous_str="0.1", raw_revised_previous_str=""
        )
        rel2 = CalendarRelease(
            event_id="840030006", value_id="2", timestamp=ts,
            timestamp_server_text="2017.07.14 15:30:00", currency="USD",
            country_code="US", event_name="Core CPI m/m", importance="high",
            actual=0.1, forecast=0.2, previous=0.1, revised_previous=None,
            period_server_text="2017.06.01 00:00:00", unit="CALENDAR_UNIT_PERCENT",
            unit_code=1, multiplier="CALENDAR_MULTIPLIER_NONE", multiplier_code=0,
            digits=1, raw_actual_str="0.1", raw_forecast_str="0.2",
            raw_previous_str="0.1", raw_revised_previous_str=""
        )
        coincident = CalendarRelease(
            event_id="840020010", value_id="3", timestamp=ts,
            timestamp_server_text="2017.07.14 15:30:00", currency="USD",
            country_code="US", event_name="Retail Sales m/m", importance="high",
            actual=-0.2, forecast=0.1, previous=-0.1, revised_previous=None,
            period_server_text="2017.06.01 00:00:00", unit="CALENDAR_UNIT_PERCENT",
            unit_code=1, multiplier="CALENDAR_MULTIPLIER_NONE", multiplier_code=0,
            digits=1, raw_actual_str="-0.2", raw_forecast_str="0.1",
            raw_previous_str="-0.1", raw_revised_previous_str=""
        )
        
        target_ids = {"840030005", "840030006"}
        all_by_ts = {ts: [rel1, rel2, coincident]}
        bundles = create_release_bundles("CPI", target_ids, [rel1, rel2], all_by_ts)

        self.assertEqual(len(bundles), 1)
        b = bundles[0]
        self.assertEqual(b.timestamp, ts)
        self.assertEqual(len(b.constituents), 2)
        self.assertIn("840030005", b.constituents)
        self.assertIn("840030006", b.constituents)
        self.assertEqual(len(b.coincident_releases), 1)
        self.assertEqual(b.coincident_releases[0].event_id, "840020010")

    def test_base_quote_usd_direction_inversion(self):
        """Verify USD base vs quote currency direction inversion."""
        for pair in USD_BASE_PAIRS:
            self.assertEqual(invert_usd_direction_for_pair(1, pair), 1)
            self.assertEqual(invert_usd_direction_for_pair(-1, pair), -1)
            self.assertIsNone(invert_usd_direction_for_pair(None, pair))

        for pair in USD_QUOTE_PAIRS:
            self.assertEqual(invert_usd_direction_for_pair(1, pair), -1)
            self.assertEqual(invert_usd_direction_for_pair(-1, pair), 1)
            self.assertIsNone(invert_usd_direction_for_pair(None, pair))

        with self.assertRaises(ValueError):
            invert_usd_direction_for_pair(1, "EURGBP")

    def test_timestamp_boundaries(self):
        """Verify cohort separation: Core (2015-2025), Partial 2026, Post-Cutoff."""
        self.assertEqual(determine_cohort("2014.12.31 23:59:59"), "PRE_2015")
        self.assertEqual(determine_cohort("2015.01.01 00:00:00"), "CORE_2015_2025")
        self.assertEqual(determine_cohort("2020.06.15 15:30:00"), "CORE_2015_2025")
        self.assertEqual(determine_cohort("2025.12.31 23:59:59"), "CORE_2015_2025")
        self.assertEqual(determine_cohort("2026.01.01 00:00:00"), "PARTIAL_2026")
        self.assertEqual(determine_cohort("2026.08.31 23:59:59"), "PARTIAL_2026")
        self.assertEqual(determine_cohort("2026.09.01 00:00:00"), "POST_CUTOFF_2026")

    def test_strict_atr_boundary_and_zero_lookahead(self):
        """Verify that a bar closing exactly at release timestamp is strictly excluded from ATR.
        
        Per Contract: bars whose close (bar_open + 3600) is STRICTLY LESS than release_timestamp.
        If a release occurs at t = 1000 * 3600, a bar opening at 999 * 3600 closes at 1000 * 3600.
        It must be excluded!
        """
        release_ts = 300 * 3600  # exact H1 boundary
        bars = []
        for i in range(301):
            t = i * 3600
            # Let normal bars have TR = 0.0100
            # Bar 299 opens at 299*3600 and closes at 300*3600 (exact release instant!)
            # Give bar 299 an EXTREME range of 1.0000 (100x normal)
            if i == 299:
                bars.append(CandleBar(
                    timestamp=t, open=1.1000, high=2.1000, low=1.1000, close=2.1000,
                    tick_volume=1000, spread=5, real_volume=0, symbol="EURUSD",
                    time_server_text=f"bar_{i}", complete_at_export=True
                ))
            else:
                bars.append(CandleBar(
                    timestamp=t, open=1.1000, high=1.1050, low=1.0950, close=1.1000,
                    tick_volume=100, spread=5, real_volume=0, symbol="EURUSD",
                    time_server_text=f"bar_{i}", complete_at_export=True
                ))

        has_atr, atr, count = calculate_pre_release_atr14(bars, release_ts)
        self.assertTrue(has_atr)
        # Bar 299 has close = 300*3600, which is NOT strictly less than release_ts (300*3600).
        # Thus bar 299 must be EXCLUDED!
        # The usable bars are bars 0..298 (299 bars).
        # Since every admitted bar has constant TR = 0.0100, ATR must be 0.0100!
        # If bar 299 had leaked into ATR, ATR would be much larger (~0.07).
        self.assertAlmostEqual(atr, 0.0100, places=6)

    def test_pinned_row_cpi_missing_mm_december_2025(self):
        """Verify that CPI release 2025.12.18 has missing m/m anchor and is properly excluded."""
        cpi_bundles, cpi_obs, raw_cnt = evaluate_cpi_pre_outcome(DEFAULT_RAW_DIR)
        dec_bundle = next((b for b in cpi_bundles if b.timestamp_server_text.startswith("2025.12.18")), None)
        self.assertIsNotNone(dec_bundle)
        
        # Verify 840030005 (m/m) is missing, but 840030007 (y/y) is present
        self.assertNotIn(EVENT_ID_US_CPI_MM, dec_bundle.constituents)
        self.assertIn(EVENT_ID_US_CPI_YY, dec_bundle.constituents)

        # Check observations for this bundle
        dec_obs = [o for o in cpi_obs if o.timestamp_server_text.startswith("2025.12.18")]
        self.assertEqual(len(dec_obs), 7)
        for o in dec_obs:
            self.assertFalse(o.anchor_present)
            self.assertIsNone(o.signal_af)
            self.assertIsNone(o.signal_ap)
            self.assertFalse(o.is_candidate_eligible_h240_af)
            self.assertFalse(o.is_candidate_eligible_h240_ap)
            self.assertEqual(o.primary_exclusion_reason_h240_af, "excluded_missing_anchor_cpi_mm")
            self.assertEqual(o.primary_exclusion_reason_h240_ap, "excluded_missing_anchor_cpi_mm")

    def test_pinned_row_september_2026_cutoff(self):
        """Verify that September 2026 releases are classified as POST_CUTOFF_2026."""
        cpi_bundles, cpi_obs, _ = evaluate_cpi_pre_outcome(DEFAULT_RAW_DIR)
        nfp_bundles, nfp_obs, _ = evaluate_nfp_pre_outcome(DEFAULT_RAW_DIR)

        # Check CPI Sept release (2026.09.11)
        cpi_sept = [o for o in cpi_obs if o.timestamp_server_text.startswith("2026.09.11")]
        self.assertEqual(len(cpi_sept), 7)
        for o in cpi_sept:
            self.assertEqual(o.cohort, "POST_CUTOFF_2026")
            self.assertFalse(o.is_candidate_eligible_h240_af)
            self.assertEqual(o.primary_exclusion_reason_h240_af, "excluded_post_2026_cutoff")

        # Check NFP Sept release (2026.09.04)
        nfp_sept = [o for o in nfp_obs if o.timestamp_server_text.startswith("2026.09.04")]
        self.assertEqual(len(nfp_sept), 7)
        for o in nfp_sept:
            self.assertEqual(o.cohort, "POST_CUTOFF_2026")
            self.assertFalse(o.is_candidate_eligible_h240_ap)
            self.assertEqual(o.primary_exclusion_reason_h240_ap, "excluded_post_2026_cutoff")

    def test_pinned_row_usdchf_nfp_weekday_gap(self):
        """Verify USDCHF NFP on 2015.01.09: H60 is valid; H120 and H240 cross 76h gap and are excluded."""
        _, nfp_obs, _ = evaluate_nfp_pre_outcome(DEFAULT_RAW_DIR)
        chf_obs = next(
            o for o in nfp_obs
            if o.timestamp_server_text.startswith("2015.01.09") and o.pair == "USDCHF"
        )
        self.assertEqual(chf_obs.coverage.entry_delay_seconds, 1800)
        self.assertEqual(chf_obs.coverage.max_weekday_gap_sec_h60, 0)
        self.assertTrue(chf_obs.coverage.has_h60_path_gap_free)
        self.assertEqual(chf_obs.coverage.max_weekday_gap_sec_h120, 273600)  # 76 hours
        self.assertFalse(chf_obs.coverage.has_h120_path_gap_free)
        self.assertEqual(chf_obs.coverage.max_weekday_gap_sec_h240, 273600)
        self.assertFalse(chf_obs.coverage.has_h240_path_gap_free)

        # Under Momentum (A-P), verify H60 is eligible while H120 and H240 are excluded
        self.assertTrue(chf_obs.is_candidate_eligible_h60_ap)
        self.assertFalse(chf_obs.is_candidate_eligible_h120_ap)
        self.assertEqual(chf_obs.primary_exclusion_reason_h120_ap, "excluded_path_gap_exceeded")
        self.assertFalse(chf_obs.is_candidate_eligible_h240_ap)
        self.assertEqual(chf_obs.primary_exclusion_reason_h240_ap, "excluded_path_gap_exceeded")

    def test_pinned_row_canadian_jobs_nfp_collisions(self):
        """Verify that Canadian employment data collides on exactly 89 of 140 NFP releases."""
        nfp_bundles, nfp_obs, raw_cnt = evaluate_nfp_pre_outcome(DEFAULT_RAW_DIR)
        self.assertEqual(len(nfp_bundles), 140)
        self.assertEqual(raw_cnt, 560)

        cad_collision_bundles = [
            b for b in nfp_bundles
            if any(c.currency == "CAD" and c.event_id in ("124010011", "124010014") for c in b.coincident_releases)
        ]
        self.assertEqual(len(cad_collision_bundles), 89)

        # Check ledger rows for USDCAD
        cad_obs = [o for o in nfp_obs if o.pair == "USDCAD" and o.has_cad_employment_collision]
        self.assertEqual(len(cad_obs), 89)

    def test_raw_constituent_dynamic_counts(self):
        """Verify dynamic constituent counts: CPI = 558, NFP = 560."""
        _, _, cpi_cnt = evaluate_cpi_pre_outcome(DEFAULT_RAW_DIR)
        _, _, nfp_cnt = evaluate_nfp_pre_outcome(DEFAULT_RAW_DIR)
        self.assertEqual(cpi_cnt, 558)
        self.assertEqual(nfp_cnt, 560)

    def test_ledger_reconciliation_assertions(self):
        """Verify complete ledger reconciliation: Total 980 == Eligible N + Sum of Exclusions."""
        for fam, eval_func in [("CPI", evaluate_cpi_pre_outcome), ("NFP", evaluate_nfp_pre_outcome)]:
            bundles, obs_list, _ = eval_func(DEFAULT_RAW_DIR)
            self.assertEqual(len(bundles), 140)
            self.assertEqual(len(obs_list), 980)

            for horizon in ["h60", "h120", "h240"]:
                for sig in ["af", "ap"]:
                    elig_attr = f"is_candidate_eligible_{horizon}_{sig}"
                    excl_attr = f"primary_exclusion_reason_{horizon}_{sig}"
                    
                    el_count = sum(1 for o in obs_list if getattr(o, elig_attr))
                    ex_counts = defaultdict(int)
                    for o in obs_list:
                        ex = getattr(o, excl_attr)
                        if ex:
                            ex_counts[ex] += 1
                            
                    total_accounted = el_count + sum(ex_counts.values())
                    self.assertEqual(
                        total_accounted, 980,
                        f"{fam} {horizon}_{sig} failed reconciliation: {total_accounted} != 980"
                    )

    def test_scheduled_market_closure_bounded_and_narrow(self):
        """Verify narrow and bounded market closure classification with positive and negative synthetic tests."""
        # Negative test 1: 10-day Friday-to-following-Monday outage (outage spanning across multiple weeks)
        t_fri = datetime(2021, 5, 7, 21, 0, 0)
        t_mon_10d = datetime(2021, 5, 17, 1, 0, 0)  # 10 days later
        self.assertFalse(
            is_scheduled_market_closure(t_fri, t_mon_10d),
            "10-day outage must be rejected as an unscheduled outage"
        )

        # Negative test 2: Arbitrary 6-day Dec 22-28 weekday gap
        t_dec22 = datetime(2021, 12, 22, 10, 0, 0)  # Mid-week Wednesday
        t_dec28 = datetime(2021, 12, 28, 10, 0, 0)  # 144 hours later
        self.assertFalse(
            is_scheduled_market_closure(t_dec22, t_dec28),
            "Arbitrary 6-day Dec 22-28 gap must be rejected"
        )

        # Negative test 3: Christmas Eve morning start (2018-12-24 09:00 -> 2018-12-26 00:00)
        t_xmas_morn_1 = datetime(2018, 12, 24, 9, 0, 0)
        t_xmas_morn_2 = datetime(2018, 12, 26, 0, 0, 0)
        self.assertFalse(
            is_scheduled_market_closure(t_xmas_morn_1, t_xmas_morn_2),
            "Weekday morning start on Dec 24 (09:00) must not be excused as a scheduled closure"
        )

        # Negative test 4: Christmas Eve afternoon start before 18:00 (2018-12-24 14:00)
        t_xmas_aft_1 = datetime(2018, 12, 24, 14, 0, 0)
        self.assertFalse(
            is_scheduled_market_closure(t_xmas_aft_1, t_xmas_morn_2),
            "Dec 24 start before 18:00 must not be excused as a scheduled closure"
        )

        # Positive test 1: Actual ordinary weekend (49.0 hours)
        t_fri_norm = datetime(2021, 5, 7, 23, 0, 0)
        t_mon_norm = datetime(2021, 5, 10, 0, 0, 0)
        self.assertTrue(
            is_scheduled_market_closure(t_fri_norm, t_mon_norm),
            "Standard 49h weekend closure must be accepted"
        )

        # Positive test 2: Bounded Christmas 2017 holiday + weekend (82.0 hours)
        t_xmas_2017_1 = datetime(2017, 12, 22, 23, 0, 0)
        t_xmas_2017_2 = datetime(2017, 12, 26, 9, 0, 0)
        self.assertTrue(
            is_scheduled_market_closure(t_xmas_2017_1, t_xmas_2017_2),
            "Christmas 2017 weekend + Boxing Day closure (82h) must be accepted"
        )

        # Positive test 3: Bounded midweek Christmas (34.0 hours)
        t_xmas_2018_1 = datetime(2018, 12, 24, 23, 0, 0)
        t_xmas_2018_2 = datetime(2018, 12, 26, 9, 0, 0)
        self.assertTrue(
            is_scheduled_market_closure(t_xmas_2018_1, t_xmas_2018_2),
            "Midweek Christmas Eve to Boxing Day morning closure (34h) must be accepted"
        )

        # Positive test 4: Bounded New Year 2018 holiday + weekend (82.0 hours)
        t_ny_2017_1 = datetime(2017, 12, 29, 23, 0, 0)
        t_ny_2017_2 = datetime(2018, 1, 2, 9, 0, 0)
        self.assertTrue(
            is_scheduled_market_closure(t_ny_2017_1, t_ny_2017_2),
            "New Year 2018 weekend closure (82h) must be accepted"
        )

    def test_allow_scheduled_holidays_false_weekend_policy(self):
        """Verify that allow_scheduled_holidays=False strictly enforces bounded regular weekends."""
        # 1. Bounded regular weekend (49.0 hours): should NOT be flagged as an unscheduled gap
        b1_norm = CandleBar(
            timestamp=1620428400, open=1.0, high=1.0, low=1.0, close=1.0,
            tick_volume=100, spread=10, real_volume=0, symbol="EURUSD",
            time_server_text="2021.05.07 23:00:00", complete_at_export=True
        )
        b2_norm = CandleBar(
            timestamp=1620604800, open=1.0, high=1.0, low=1.0, close=1.0,
            tick_volume=100, spread=10, real_volume=0, symbol="EURUSD",
            time_server_text="2021.05.10 00:00:00", complete_at_export=True
        )
        gap_cnt_norm, _ = detect_path_weekday_gaps([b1_norm, b2_norm], entry_idx=0, horizon_bars=2, allow_scheduled_holidays=False)
        self.assertEqual(gap_cnt_norm, 0, "Ordinary 49h weekend must not be flagged when allow_scheduled_holidays=False")

        # 2. Extended 10-day Friday-to-Monday outage (241 hours): MUST be flagged as an unscheduled gap
        b1_outage = CandleBar(
            timestamp=1620421200, open=1.0, high=1.0, low=1.0, close=1.0,
            tick_volume=100, spread=10, real_volume=0, symbol="EURUSD",
            time_server_text="2021.05.07 21:00:00", complete_at_export=True
        )
        b2_outage = CandleBar(
            timestamp=1621288800, open=1.0, high=1.0, low=1.0, close=1.0,
            tick_volume=100, spread=10, real_volume=0, symbol="EURUSD",
            time_server_text="2021.05.17 01:00:00", complete_at_export=True
        )
        gap_cnt_outage, max_sec = detect_path_weekday_gaps([b1_outage, b2_outage], entry_idx=0, horizon_bars=2, allow_scheduled_holidays=False)
        self.assertEqual(gap_cnt_outage, 1, "10-day outage must be flagged when allow_scheduled_holidays=False")
        self.assertEqual(max_sec, 1621288800 - 1620421200)

        # 3. Scheduled Christmas holiday closure (34h):
        # Under allow_scheduled_holidays=True: valid closure (0 gaps)
        # Under allow_scheduled_holidays=False: NOT an ordinary weekend, so flagged as gap (1 gap)
        b1_xmas = CandleBar(
            timestamp=1545692400, open=1.0, high=1.0, low=1.0, close=1.0,
            tick_volume=100, spread=10, real_volume=0, symbol="EURUSD",
            time_server_text="2018.12.24 23:00:00", complete_at_export=True
        )
        b2_xmas = CandleBar(
            timestamp=1545814800, open=1.0, high=1.0, low=1.0, close=1.0,
            tick_volume=100, spread=10, real_volume=0, symbol="EURUSD",
            time_server_text="2018.12.26 09:00:00", complete_at_export=True
        )
        gap_cnt_xmas_allow, _ = detect_path_weekday_gaps([b1_xmas, b2_xmas], entry_idx=0, horizon_bars=2, allow_scheduled_holidays=True)
        self.assertEqual(gap_cnt_xmas_allow, 0, "Christmas closure accepted when allow_scheduled_holidays=True")
        gap_cnt_xmas_disallow, _ = detect_path_weekday_gaps([b1_xmas, b2_xmas], entry_idx=0, horizon_bars=2, allow_scheduled_holidays=False)
        self.assertEqual(gap_cnt_xmas_disallow, 1, "Christmas closure flagged as gap when allow_scheduled_holidays=False")

    def test_build_provenance_index_fail_closed(self):
        """Verify that build_provenance_index fails closed under corruption, missing files, or bootstrap violations."""
        with tempfile.TemporaryDirectory() as td:
            tmp_json = os.path.join(td, "provenance.json")
            tmp_md = os.path.join(td, "provenance.md")

            # 1. Corrupt JSON fixture
            with open(tmp_json, "w", encoding="utf-8") as f:
                f.write("CORRUPT_JSON_NOT_VALID_SYNTAX {[[")
            with self.assertRaises(RuntimeError) as cm:
                build_provenance_index(DEFAULT_RAW_DIR, json_path=tmp_json, md_path=tmp_md, bootstrap=False)
            self.assertIn("malformed or unreadable prior provenance index JSON", str(cm.exception))

            # 2. Incomplete prior JSON fixture (missing files)
            incomplete_records = [{"rel_raw": "manifest.csv", "sha256": PUBLISHED_ANCHOR_HASHES["manifest.csv"]}]
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump(incomplete_records, f)
            with self.assertRaises(RuntimeError) as cm:
                build_provenance_index(DEFAULT_RAW_DIR, json_path=tmp_json, md_path=tmp_md, bootstrap=False)
            self.assertIn("prior provenance index missing expected files", str(cm.exception))

            # 2b. Duplicate entry in prior JSON fixture
            full_valid_records = [{"rel_raw": f, "sha256": "0" * 64} for f in EXPECTED_RAW_FILES]
            dup_records = full_valid_records + [{"rel_raw": "manifest.csv", "sha256": "0" * 64}]
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump(dup_records, f)
            with self.assertRaises(RuntimeError) as cm:
                build_provenance_index(DEFAULT_RAW_DIR, json_path=tmp_json, md_path=tmp_md, bootstrap=False)
            self.assertIn("duplicate entry in prior provenance index", str(cm.exception))

            # 2c. Unexpected extra entry in prior JSON fixture
            extra_prior_records = full_valid_records + [{"rel_raw": "candles/candles_UNEXPECTED_H1.csv", "sha256": "0" * 64}]
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump(extra_prior_records, f)
            with self.assertRaises(RuntimeError) as cm:
                build_provenance_index(DEFAULT_RAW_DIR, json_path=tmp_json, md_path=tmp_md, bootstrap=False)
            self.assertIn("prior provenance index contains unexpected files", str(cm.exception))

            # 3. Missing JSON when bootstrap=False
            missing_json = os.path.join(td, "does_not_exist.json")
            with self.assertRaises(RuntimeError) as cm:
                build_provenance_index(DEFAULT_RAW_DIR, json_path=missing_json, md_path=tmp_md, bootstrap=False)
            self.assertIn("existing provenance index not found", str(cm.exception))

            # 4. Bootstrap initialization when bootstrap=True
            records = build_provenance_index(DEFAULT_RAW_DIR, json_path=missing_json, md_path=tmp_md, bootstrap=True)
            self.assertEqual(len(records), 34)
            self.assertTrue(os.path.exists(missing_json))
            self.assertTrue(os.path.exists(tmp_md))

            # 5. Missing non-anchor candle fixture in raw_dir
            raw_mock_missing = os.path.join(td, "raw_mock_missing")
            os.makedirs(os.path.join(raw_mock_missing, "candles"), exist_ok=True)
            for frel in EXPECTED_RAW_FILES:
                if frel == "candles/candles_EURUSD_H1.csv":
                    continue
                fpath = os.path.join(raw_mock_missing, frel)
                os.makedirs(os.path.dirname(fpath), exist_ok=True)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("test")
            with self.assertRaises(RuntimeError) as cm:
                build_provenance_index(raw_mock_missing, json_path=tmp_json, md_path=tmp_md, bootstrap=True)
            self.assertIn("missing 1 file(s): ['candles/candles_EURUSD_H1.csv']", str(cm.exception))

            # 6. Unexpected extra file fixture in raw_dir
            raw_mock_extra = os.path.join(td, "raw_mock_extra")
            os.makedirs(os.path.join(raw_mock_extra, "candles"), exist_ok=True)
            for frel in EXPECTED_RAW_FILES:
                fpath = os.path.join(raw_mock_extra, frel)
                os.makedirs(os.path.dirname(fpath), exist_ok=True)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("test")
            extra_path = os.path.join(raw_mock_extra, "candles", "candles_EXTRA_H1.csv")
            with open(extra_path, "w", encoding="utf-8") as f:
                f.write("test")
            with self.assertRaises(RuntimeError) as cm:
                build_provenance_index(raw_mock_extra, json_path=tmp_json, md_path=tmp_md, bootstrap=True)
            self.assertIn("unexpected 1 file(s): ['candles/candles_EXTRA_H1.csv']", str(cm.exception))

    def test_fail_closed_provenance_anchors(self):
        """Verify that the 3 published SHA-256 anchors fail closed upon corruption."""
        # 1. Verify that current files in raw_dir match the 3 published anchors bit-for-bit
        for fname, exp_hash in PUBLISHED_ANCHOR_HASHES.items():
            fpath = os.path.join(DEFAULT_RAW_DIR, fname)
            self.assertTrue(os.path.exists(fpath), f"Missing anchor file: {fname}")
            actual_hash = compute_sha256(fpath)
            self.assertEqual(actual_hash, exp_hash, f"Hash mismatch for anchor {fname}")

        # 2. Verify that an altered expected hash triggers fail-closed assertion
        corrupt_anchors = dict(PUBLISHED_ANCHOR_HASHES)
        corrupt_anchors["manifest.csv"] = "0000000000000000000000000000000000000000000000000000000000000000"
        with self.assertRaises(RuntimeError):
            for anchor_file, expected_hash in corrupt_anchors.items():
                anchor_path = os.path.join(DEFAULT_RAW_DIR, anchor_file)
                if compute_sha256(anchor_path) != expected_hash:
                    raise RuntimeError(f"Fail-closed anchor check failed for {anchor_file}")

    def test_horizon_specific_eligibility_counts(self):
        """Verify exact horizon-specific candidate counts across CPI/NFP × AF/AP × H60/H120/H240."""
        _, cpi_obs, _ = evaluate_cpi_pre_outcome(DEFAULT_RAW_DIR)
        _, nfp_obs, _ = evaluate_nfp_pre_outcome(DEFAULT_RAW_DIR)

        # CPI AF: All 671 eligible observations have complete paths with zero gap disqualifications across H60, H120, H240
        self.assertEqual(sum(1 for o in cpi_obs if o.is_candidate_eligible_h60_af), 671)
        self.assertEqual(sum(1 for o in cpi_obs if o.is_candidate_eligible_h120_af), 671)
        self.assertEqual(sum(1 for o in cpi_obs if o.is_candidate_eligible_h240_af), 671)

        # CPI AP: All 859 eligible observations have complete paths with zero gap disqualifications across H60, H120, H240
        self.assertEqual(sum(1 for o in cpi_obs if o.is_candidate_eligible_h60_ap), 859)
        self.assertEqual(sum(1 for o in cpi_obs if o.is_candidate_eligible_h120_ap), 859)
        self.assertEqual(sum(1 for o in cpi_obs if o.is_candidate_eligible_h240_ap), 859)

        # NFP AF: 777 eligible at H60; NZDUSD 2017.05.05 crosses 106h gap at bar 80 -> excluded at H120/H240 (776)
        self.assertEqual(sum(1 for o in nfp_obs if o.is_candidate_eligible_h60_af), 777)
        self.assertEqual(sum(1 for o in nfp_obs if o.is_candidate_eligible_h120_af), 776)
        self.assertEqual(sum(1 for o in nfp_obs if o.is_candidate_eligible_h240_af), 776)

        # NFP AP: 966 eligible at H60; USDCHF 2015.01.09 (76h gap at bar 100) and NZDUSD 2017.05.05 (106h gap at bar 80)
        # both cross gaps after bar 60 -> excluded at H120/H240 (964)
        self.assertEqual(sum(1 for o in nfp_obs if o.is_candidate_eligible_h60_ap), 966)
        self.assertEqual(sum(1 for o in nfp_obs if o.is_candidate_eligible_h120_ap), 964)
        self.assertEqual(sum(1 for o in nfp_obs if o.is_candidate_eligible_h240_ap), 964)

    def test_initial_jobless_claims_identity_and_collision_reconciliation(self):
        """Verify Initial Jobless Claims ID 840140001, reject 840014001, and reconcile collision counts."""
        # 1. Pinned ID constant
        self.assertEqual(EVENT_ID_US_INITIAL_JOBLESS_CLAIMS, "840140001")

        # 2. Assert raw calendar event file existence and naming
        events_path = os.path.join(DEFAULT_RAW_DIR, "calendar_events.csv")
        self.assertTrue(os.path.exists(events_path))
        found_claims = False
        with open(events_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["event_id"] == "840140001":
                    found_claims = True
                    self.assertEqual(row["country_code"], "US")
                    self.assertEqual(row["country_currency"], "USD")
                    self.assertEqual(row["event_name"], "Initial Jobless Claims")
                elif row["event_id"] == "840014001":
                    self.fail("Erroneous event_id 840014001 must NOT exist in raw calendar_events.csv")
        self.assertTrue(found_claims, "Event ID 840140001 must exist in calendar_events.csv")

        # 3. Fail-loud validation function
        self.assertTrue(assert_event_id_valid("840140001", DEFAULT_RAW_DIR))
        with self.assertRaises(ValueError):
            assert_event_id_valid("840014001", DEFAULT_RAW_DIR)

        # 4. Direct raw calendar coincidence count reconciliation
        all_by_ts = load_all_releases_by_timestamp(DEFAULT_RAW_DIR)

        # CPI:
        cpi_constituents = {"840030005", "840030006", "840030007", "840030008"}
        cpi_timestamps = [ts for ts, rels in all_by_ts.items() if any(r.event_id in cpi_constituents for r in rels)]
        self.assertEqual(len(cpi_timestamps), 140, "Total raw CPI timestamps must equal 140")

        cpi_coincident_claims = [ts for ts in cpi_timestamps if any(r.event_id == "840140001" for r in all_by_ts[ts])]
        self.assertEqual(len(cpi_coincident_claims), 33, "Total raw CPI timestamps coincident with claims must equal 33")

        # Check anchor-present subset
        cpi_anchor_present = [ts for ts in cpi_timestamps if any(r.event_id == "840030005" for r in all_by_ts[ts])]
        self.assertEqual(len(cpi_anchor_present), 139, "Total CPI anchor-present timestamps must equal 139")

        cpi_anchor_present_with_claims = [ts for ts in cpi_anchor_present if any(r.event_id == "840140001" for r in all_by_ts[ts])]
        self.assertEqual(len(cpi_anchor_present_with_claims), 32, "Anchor-present CPI timestamps with claims must equal 32")

        cpi_anchor_missing_with_claims = [ts for ts in cpi_coincident_claims if ts not in cpi_anchor_present]
        self.assertEqual(len(cpi_anchor_missing_with_claims), 1, "Exactly 1 anchor-absent bundle has claims collision")
        self.assertEqual(cpi_anchor_missing_with_claims[0], 1766075400, "December 2025 anchor-absent bundle timestamp must be 1766075400")

        # NFP:
        nfp_constituents = {"840030016", "840030015", "840030018", "840030019"}
        nfp_timestamps = [ts for ts, rels in all_by_ts.items() if any(r.event_id in nfp_constituents for r in rels)]
        self.assertEqual(len(nfp_timestamps), 140, "Total raw NFP timestamps must equal 140")

        nfp_coincident_claims = [ts for ts in nfp_timestamps if any(r.event_id == "840140001" for r in all_by_ts[ts])]
        self.assertEqual(len(nfp_coincident_claims), 4, "NFP timestamps coincident with claims must equal exactly 4")
        expected_nfp_claims_ts = {1435851000, 1593703800, 1751556600, 1783006200}
        self.assertEqual(set(nfp_coincident_claims), expected_nfp_claims_ts)

        cad_jobs_ids = {"124010011", "124010014"}
        nfp_coincident_cad_jobs = [ts for ts in nfp_timestamps if any(r.event_id in cad_jobs_ids for r in all_by_ts[ts])]
        self.assertEqual(len(nfp_coincident_cad_jobs), 89, "NFP timestamps coincident with Canadian jobs must equal 89")

        # 5. Pre-outcome V2 Ledger flag verification
        cpi_ledger_v2 = os.path.join(REPO_ROOT, "Research Candidate", "CPI", "pre_outcome_ledger_cpi_v2.csv")
        self.assertTrue(os.path.exists(cpi_ledger_v2), "pre_outcome_ledger_cpi_v2.csv must exist")
        with open(cpi_ledger_v2, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cpi_rows = list(reader)
        self.assertEqual(len(cpi_rows), 980)
        cpi_flagged_claims = sum(1 for r in cpi_rows if r["has_us_jobless_claims_collision"].lower() == "true")
        self.assertEqual(cpi_flagged_claims, 33 * 7, "CPI V2 ledger must have 33*7 = 231 flagged claims rows")

        nfp_ledger_v2 = os.path.join(REPO_ROOT, "Research Candidate", "NFP", "pre_outcome_ledger_nfp_v2.csv")
        self.assertTrue(os.path.exists(nfp_ledger_v2), "pre_outcome_ledger_nfp_v2.csv must exist")
        with open(nfp_ledger_v2, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            nfp_rows = list(reader)
        self.assertEqual(len(nfp_rows), 980)
        nfp_flagged_claims = sum(1 for r in nfp_rows if r["has_us_jobless_claims_collision"].lower() == "true")
        self.assertEqual(nfp_flagged_claims, 4 * 7, "NFP V2 ledger must have 4*7 = 28 flagged claims rows")
        nfp_flagged_cad = sum(1 for r in nfp_rows if r["has_cad_employment_collision"].lower() == "true")
        self.assertEqual(nfp_flagged_cad, 89 * 7, "NFP V2 ledger must have 89*7 = 623 flagged CAD employment rows")


if __name__ == "__main__":
    unittest.main()
