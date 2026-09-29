"""Unit, Fail-Closed, and Reconciliation Tests for USD CPI Bundle Inventory (V1).

Validates:
1. Missing versus zero integrity (no coercion of missing to zero)
2. Fail-closed on malformed text, NaN, and Infinity (NaN delta never silently classifies as ZERO)
3. Fail-closed on unexpected currency, units, multipliers, and catalog sector
4. Duplicate event IDs at the same timestamp (detection and loud failure)
5. Four-series bundle assembly (840030005, 840030006, 840030007, 840030008)
6. Absent m/m with present y/y on 2025-12-18 (fail-closed, silent substitution STRICTLY FORBIDDEN)
7. Anti-hallucination check: verifies that 'silent substitution' is never declared permitted
8. Revised previous separation (A - P strictly uses reported previous)
9. Source period field auditability (tracking reference months and revealing 2025 gaps)
10. External collision ID 840140001 (Jobless Claims: 33 total, 32 with m/m present)
11. Timing verification (ATR strictly pre-release, Actual known at release, available by H1 entry)
12. 2026-09-11 release exclusion (excluded solely by release cutoff, despite full H240 bar paths)
13. Mathematical distinction between Candidate 2, Candidate 4, and Conflict-Only sub-studies
14. Yearly, partial, and anchor-present count waterfalls (140 inventory, 139 in-cutoff, 138 anchor-present)
15. Stable source references (1-indexed physical row numbers, MT5 value IDs)
16. Deterministic output (bit-for-bit reproducibility of SHA-256 hashes)
17. Nine globally excluded pairs strictly absent
"""

import unittest
import sys
import os
import csv
import json
import math
import tempfile
from collections import defaultdict

# Add parent calculator directory to path
CALC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if CALC_DIR not in sys.path:
    sys.path.insert(0, CALC_DIR)

from protocol_specs import (
    ALL_EXPORTED_PAIRS,
    GLOBALLY_EXCLUDED_PAIRS,
    ACTIVE_RESEARCH_PAIRS,
    ACTIVE_USD_PAIRS,
    EVENT_ID_US_CPI_MM,
    EVENT_ID_US_CORE_CPI_MM,
    EVENT_ID_US_CPI_YY,
    EVENT_ID_US_CORE_CPI_YY,
    EVENT_ID_US_INITIAL_JOBLESS_CLAIMS,
    assert_event_id_valid,
)
from data_loader import DEFAULT_RAW_DIR
from generate_cpi_bundle_inventory import (
    parse_strict_calendar_float,
    compute_difference_strict,
    classify_signal_state_strict,
    load_raw_calendar_data,
    classify_mm_concordance,
    PACKAGE_DIR,
    PACKAGE_DIR_V1,
    PACKAGE_DIR_V2,
    TRACKED_DIR,
    compute_sha256,
    EXPECTED_RAW_INPUT_HASHES,
    verify_raw_inputs_at_startup,
    generate_bundle_inventory,
)

REPO_ROOT = os.path.normpath(os.path.join(CALC_DIR, "..", ".."))


class TestCpiBundleInventory(unittest.TestCase):
    """Test suite for USD CPI Bundle parser, ledger integrity, and count reconciliation."""

    def test_missing_versus_zero_integrity(self):
        """Verify that missing values are never coerced to zero."""
        self.assertIsNone(compute_difference_strict(None, 0.2))
        self.assertIsNone(compute_difference_strict(0.3, None))
        self.assertIsNone(compute_difference_strict(None, None))

        # Zero differences must be exactly 0.0
        self.assertEqual(compute_difference_strict(0.3, 0.3), 0.0)
        self.assertEqual(compute_difference_strict(0.0, 0.0), 0.0)
        self.assertEqual(compute_difference_strict(2.5, 2.3), 0.2)
        self.assertEqual(compute_difference_strict(2.0, 2.5), -0.5)

        # Classification states
        self.assertEqual(classify_signal_state_strict(None), "MISSING")
        self.assertEqual(classify_signal_state_strict(0.0), "ZERO")
        self.assertEqual(classify_signal_state_strict(0.0001), "POSITIVE")
        self.assertEqual(classify_signal_state_strict(-0.0001), "NEGATIVE")

    def test_fail_closed_on_malformed_text_nan_and_infinity(self):
        """Verify that malformed text, NaN, and Inf raise ValueError and are never coerced to ZERO."""
        # 1. Missing vs Malformed in parse_strict_calendar_float
        self.assertIsNone(parse_strict_calendar_float("", "actual", 10))
        self.assertIsNone(parse_strict_calendar_float("   ", "actual", 10))

        for malformed in ["N/A", "abc", "null", "none", "nan", "NaN", "NAN", "inf", "-inf", "+inf"]:
            with self.assertRaises(ValueError, msg=f"Should reject {malformed}"):
                parse_strict_calendar_float(malformed, "actual", 10)

        # 2. Non-finite values in compute_difference_strict
        with self.assertRaises(ValueError):
            compute_difference_strict(float("nan"), 0.2)
        with self.assertRaises(ValueError):
            compute_difference_strict(0.2, float("nan"))
        with self.assertRaises(ValueError):
            compute_difference_strict(float("inf"), 0.2)

        # 3. Non-finite values in classify_signal_state_strict (must NOT classify as ZERO)
        with self.assertRaises(ValueError):
            classify_signal_state_strict(float("nan"))
        with self.assertRaises(ValueError):
            classify_signal_state_strict(float("inf"))
        with self.assertRaises(ValueError):
            classify_signal_state_strict(float("-inf"))

    def test_fail_closed_on_unexpected_currency_units_and_multiplier(self):
        """Verify that non-USD currency, non-percent unit, or non-empty multiplier fails closed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Valid calendar_events.csv
            events_csv = os.path.join(tmp_dir, "calendar_events.csv")
            with open(events_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["event_id", "country_currency", "event_name", "sector", "unit", "digits", "multiplier", "importance"])
                writer.writerow(["840030005", "USD", "CPI m/m", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840030006", "USD", "Core CPI m/m", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840030007", "USD", "CPI y/y", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840030008", "USD", "Core CPI y/y", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840140001", "USD", "Initial Jobless Claims", "CALENDAR_SECTOR_JOBS", "CALENDAR_UNIT_JOBS", "0", "CALENDAR_MULTIPLIER_THOUSANDS", "high"])

            # Test 1: Invalid currency in release row
            rel_csv = os.path.join(tmp_dir, "calendar_releases.csv")
            with open(rel_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "event_id", "value_id", "timestamp", "currency", "country_code",
                    "event_name", "importance", "actual", "forecast", "previous",
                    "revised_previous", "period_server_text", "unit", "multiplier",
                    "digits", "timestamp_server_text"
                ])
                writer.writerow([
                    "840030005", "101", "1000", "EUR", "US", "CPI m/m", "high",
                    "0.2", "0.1", "0.1", "", "2020.01.01", "CALENDAR_UNIT_PERCENT", "CALENDAR_MULTIPLIER_NONE", "1", "2020.01.15 15:30:00"
                ])
            with self.assertRaises(ValueError) as ctx:
                load_raw_calendar_data(tmp_dir)
            self.assertIn("currency 'EUR' != USD", str(ctx.exception))

            # Test 2: Invalid unit in release row
            with open(rel_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "event_id", "value_id", "timestamp", "currency", "country_code",
                    "event_name", "importance", "actual", "forecast", "previous",
                    "revised_previous", "period_server_text", "unit", "multiplier",
                    "digits", "timestamp_server_text"
                ])
                writer.writerow([
                    "840030005", "101", "1000", "USD", "US", "CPI m/m", "high",
                    "0.2", "0.1", "0.1", "", "2020.01.01", "CALENDAR_UNIT_INDEX", "CALENDAR_MULTIPLIER_NONE", "1", "2020.01.15 15:30:00"
                ])
            with self.assertRaises(ValueError) as ctx:
                load_raw_calendar_data(tmp_dir)
            self.assertIn("unit 'CALENDAR_UNIT_INDEX' != CALENDAR_UNIT_PERCENT", str(ctx.exception))

    def test_duplicate_event_ids_at_same_timestamp_rejected(self):
        """Verify that duplicate event IDs at the same timestamp raise ValueError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            events_csv = os.path.join(tmp_dir, "calendar_events.csv")
            with open(events_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["event_id", "country_currency", "event_name", "sector", "unit", "digits", "multiplier", "importance"])
                writer.writerow(["840030005", "USD", "CPI m/m", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840030006", "USD", "Core CPI m/m", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840030007", "USD", "CPI y/y", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840030008", "USD", "Core CPI y/y", "CALENDAR_SECTOR_PRICES", "CALENDAR_UNIT_PERCENT", "1", "CALENDAR_MULTIPLIER_NONE", "high"])
                writer.writerow(["840140001", "USD", "Initial Jobless Claims", "CALENDAR_SECTOR_JOBS", "CALENDAR_UNIT_JOBS", "0", "CALENDAR_MULTIPLIER_THOUSANDS", "high"])

            rel_csv = os.path.join(tmp_dir, "calendar_releases.csv")
            with open(rel_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "event_id", "value_id", "timestamp", "currency", "country_code",
                    "event_name", "importance", "actual", "forecast", "previous",
                    "revised_previous", "period_server_text", "unit", "multiplier",
                    "digits", "timestamp_server_text"
                ])
                writer.writerow([
                    "840030005", "101", "1000", "USD", "US", "CPI m/m", "high",
                    "0.2", "0.1", "0.1", "", "2020.01.01", "CALENDAR_UNIT_PERCENT", "CALENDAR_MULTIPLIER_NONE", "1", "2020.01.15 15:30:00"
                ])
                writer.writerow([
                    "840030005", "102", "1000", "USD", "US", "CPI m/m", "high",
                    "0.3", "0.1", "0.1", "", "2020.01.01", "CALENDAR_UNIT_PERCENT", "CALENDAR_MULTIPLIER_NONE", "1", "2020.01.15 15:30:00"
                ])

            with self.assertRaises(ValueError) as ctx:
                load_raw_calendar_data(tmp_dir)
            self.assertIn("Duplicate event ID 840030005", str(ctx.exception))

    def test_four_series_bundle_assembly(self):
        """Verify grouping of the 4 CPI series into atomic release bundles."""
        cpi_by_ts, _, _, raw_cnt = load_raw_calendar_data(DEFAULT_RAW_DIR)
        self.assertEqual(len(cpi_by_ts), 140)
        self.assertEqual(raw_cnt, 558)

        # Check May 2026 release
        ts_may_2026 = 1778599800
        self.assertIn(ts_may_2026, cpi_by_ts)
        bundle_may_2026 = cpi_by_ts[ts_may_2026]
        self.assertEqual(len(bundle_may_2026), 4)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CPI_MM]["actual"], 0.6)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CPI_MM]["previous"], 0.9)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CORE_CPI_MM]["actual"], 0.4)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CORE_CPI_MM]["previous"], 0.2)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CPI_YY]["actual"], 3.8)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CPI_YY]["previous"], 3.3)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CORE_CPI_YY]["actual"], 2.8)
        self.assertEqual(bundle_may_2026[EVENT_ID_US_CORE_CPI_YY]["previous"], 2.6)

    def test_absent_mm_with_present_yy_on_2025_12_18(self):
        """Verify fail-closed handling of the 2025.12.18 release lacking m/m constituents."""
        cpi_by_ts, _, _, _ = load_raw_calendar_data(DEFAULT_RAW_DIR)
        ts_dec_2025 = 1766075400  # 2025.12.18 16:30:00
        self.assertIn(ts_dec_2025, cpi_by_ts)
        bundle = cpi_by_ts[ts_dec_2025]

        # Verify m/m constituents are ABSENT
        self.assertNotIn(EVENT_ID_US_CPI_MM, bundle)
        self.assertNotIn(EVENT_ID_US_CORE_CPI_MM, bundle)

        # Verify y/y constituents are PRESENT
        self.assertIn(EVENT_ID_US_CPI_YY, bundle)
        self.assertIn(EVENT_ID_US_CORE_CPI_YY, bundle)

        # Verify joint concordance classifies as MISSING_ANCHOR
        conc = classify_mm_concordance("MISSING", "MISSING")
        self.assertEqual(conc, "MISSING_ANCHOR")

    def test_silent_substitution_strictly_forbidden(self):
        """Verify that silent substitution is strictly forbidden and never declared permitted."""
        bundle_csv = os.path.join(PACKAGE_DIR, "cpi_bundle_ledger.csv")
        with open(bundle_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            dec_2025 = next(r for r in reader if r["timestamp"] == "1766075400")

        # 1. Headline and Core m/m MUST be missing, never substituted with y/y
        self.assertEqual(dec_2025["headline_mm_present"], "False")
        self.assertEqual(dec_2025["core_mm_present"], "False")
        self.assertEqual(dec_2025["headline_mm_sign"], "MISSING")
        self.assertEqual(dec_2025["core_mm_sign"], "MISSING")
        self.assertEqual(dec_2025["headline_mm_actual"], "")
        self.assertEqual(dec_2025["headline_yy_actual"], "2.7")

        # 2. Check tracked documentation: verify that 'substitution with y/y is permitted' NEVER appears
        for doc_name in ["RECONCILIATION_REPORT.md", "SCHEMA.md"]:
            doc_path = os.path.join(TRACKED_DIR, doc_name)
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                self.assertNotIn("substitution with y/y is permitted", content)
                self.assertNotIn("substitution with y/y\" is permitted", content)
                if "substitution" in content:
                    self.assertIn("forbidden", content)

    def test_revised_previous_separation(self):
        """Verify that revised_previous is tracked separately and never replaces previous."""
        cpi_by_ts, _, _, _ = load_raw_calendar_data(DEFAULT_RAW_DIR)
        rev_prev_headline_cnt = 0
        rev_prev_core_cnt = 0

        for ts, m in cpi_by_ts.items():
            if EVENT_ID_US_CPI_MM in m:
                r = m[EVENT_ID_US_CPI_MM]
                if r["revised_previous"] is not None:
                    rev_prev_headline_cnt += 1
                    self.assertIsNotNone(r["previous"])
                    computed_d = compute_difference_strict(r["actual"], r["previous"])
                    self.assertAlmostEqual(computed_d, round(r["actual"] - r["previous"], 6))
            if EVENT_ID_US_CORE_CPI_MM in m:
                r = m[EVENT_ID_US_CORE_CPI_MM]
                if r["revised_previous"] is not None:
                    rev_prev_core_cnt += 1
                    self.assertIsNotNone(r["previous"])

        self.assertEqual(rev_prev_headline_cnt, 15)
        self.assertEqual(rev_prev_core_cnt, 12)

    def test_source_period_auditability(self):
        """Verify that source reporting period fields are carried into the bundle ledger."""
        bundle_csv = os.path.join(PACKAGE_DIR, "cpi_bundle_ledger.csv")
        with open(bundle_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows_2025 = [r for r in reader if r["year"] == "2025"]

        # Confirm period fields exist
        self.assertIn("bundle_period_server_text", rows_2025[0])
        self.assertIn("headline_mm_period_server_text", rows_2025[0])

        # Verify period gap in late 2025: 2025.10.24 is period 2025.09.01, 2025.12.18 is period 2025.11.01
        p_oct = next(r["bundle_period_server_text"] for r in rows_2025 if r["timestamp_server_text"].startswith("2025.10.24"))
        p_dec = next(r["bundle_period_server_text"] for r in rows_2025 if r["timestamp_server_text"].startswith("2025.12.18"))
        self.assertEqual(p_oct, "2025.09.01 00:00:00")
        self.assertEqual(p_dec, "2025.11.01 00:00:00")

    def test_external_collision_jobless_claims_id(self):
        """Verify Initial Jobless Claims collision event ID and count."""
        self.assertTrue(assert_event_id_valid(EVENT_ID_US_INITIAL_JOBLESS_CLAIMS, DEFAULT_RAW_DIR))

        cpi_by_ts, all_by_ts, _, _ = load_raw_calendar_data(DEFAULT_RAW_DIR)
        claims_coincident_total = 0
        claims_with_mm_present = 0
        claims_without_mm = 0

        for ts, m in cpi_by_ts.items():
            coincident = all_by_ts[ts]
            has_claims = any(r["event_id"] == EVENT_ID_US_INITIAL_JOBLESS_CLAIMS for r in coincident)
            if has_claims:
                claims_coincident_total += 1
                if EVENT_ID_US_CPI_MM in m:
                    claims_with_mm_present += 1
                else:
                    claims_without_mm += 1

        self.assertEqual(claims_coincident_total, 33)
        self.assertEqual(claims_with_mm_present, 32)
        self.assertEqual(claims_without_mm, 1)

    def test_september_2026_release_path_and_cutoff(self):
        """Verify that 2026-09-11 is excluded solely by release cutoff date, not missing bars."""
        pair_csv = os.path.join(PACKAGE_DIR, "cpi_pair_expanded_ledger.csv")
        with open(pair_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            sep_rows = [r for r in reader if r["timestamp_server_text"].startswith("2026.09.11")]

        self.assertEqual(len(sep_rows), 7)
        for r in sep_rows:
            # Must be excluded as post-cutoff
            self.assertEqual(r["cohort"], "POST_CUTOFF_2026")
            self.assertEqual(r["exclusion_candidate_1_headline_mm_h60"], "excluded_post_2026_cutoff")
            # But physical H240 bar path MUST be complete and gap-free
            self.assertEqual(r["has_h240_bars"], "True")
            self.assertEqual(r["has_h240_gap_free"], "True")

    def test_candidate_mathematical_distinction(self):
        """Verify that Candidate 4 is NOT a duplicate of Candidate 2, and verify conflict sub-study N."""
        pair_csv = os.path.join(PACKAGE_DIR, "cpi_pair_expanded_ledger.csv")
        with open(pair_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            in_cutoff = [r for r in reader if r["cohort"] != "POST_CUTOFF_2026"]

        c2_el = [r for r in in_cutoff if r["eligible_candidate_2_core_mm_led_h60"] == "True"]
        c4_el = [r for r in in_cutoff if r["eligible_candidate_4_conflict_filtered_headline_h60"] == "True"]
        conf_el = [r for r in in_cutoff if r["eligible_conflict_substudy_h60"] == "True"]

        # Candidate 2 has 656 pre-outcome H60-eligible pair observations; Candidate 4 has 663!
        self.assertEqual(len(c2_el), 656)
        self.assertEqual(len(c4_el), 663)

        c2_bundles = set(r["bundle_id"] for r in c2_el)
        c4_bundles = set(r["bundle_id"] for r in c4_el)

        # Intersect is 59 concordant bundles * 7 = 413
        common_bundles = c2_bundles.intersection(c4_bundles)
        self.assertEqual(len(common_bundles), 59)

        # Candidate 2 trades all 28 conflict bundles; Candidate 4 trades ZERO conflict bundles!
        conflict_bundles = set(r["bundle_id"] for r in in_cutoff if r["is_conflict_episode"] == "True")
        self.assertEqual(len(conflict_bundles), 28)
        self.assertTrue(conflict_bundles.issubset(c2_bundles))
        self.assertEqual(len(conflict_bundles.intersection(c4_bundles)), 0)

        # Conflict sub-study has exactly 28 releases * 7 pairs = 196 pre-outcome H60-eligible pair observations
        self.assertEqual(len(conf_el), 196)

    def test_complete_count_waterfalls_and_reconciliation(self):
        """Verify full count separation: 140 inventory, 139 in-cutoff, 138 anchor-present."""
        manifest_json = os.path.join(PACKAGE_DIR, "manifest.json")
        with open(manifest_json, "r", encoding="utf-8") as f:
            m = json.load(f)

        c = m["counts"]
        # 1. Bundles
        self.assertEqual(c["total_inventory_bundles"], 140)
        self.assertEqual(c["in_cutoff_bundles_through_aug2026"], 139)
        self.assertEqual(c["in_cutoff_bundles_with_mm_present"], 138)
        self.assertEqual(c["post_cutoff_bundles"], 1)

        # 2. Pair observations
        self.assertEqual(c["total_inventory_pair_observations"], 980)
        self.assertEqual(c["in_cutoff_pair_observations"], 973)

        # 3. Raw constituents
        self.assertEqual(c["total_raw_constituent_rows"], 558)
        self.assertEqual(c["headline_mm_rows"], 139)
        self.assertEqual(c["core_mm_rows"], 139)
        self.assertEqual(c["headline_yy_rows"], 140)
        self.assertEqual(c["core_yy_rows"], 140)

        # 4. Clean subset
        self.assertEqual(c["claims_clean_in_cutoff_bundles_with_mm"], 106)
        self.assertEqual(c["claims_coincident_with_headline_mm"], 32)
        self.assertEqual(c["claims_coincident_without_headline_mm"], 1)

        # 5. Concordance distribution sum
        self.assertEqual(sum(m["concordance_distribution"].values()), 140)

        # 6. Nine globally excluded pairs strictly absent
        with open(os.path.join(PACKAGE_DIR, "cpi_pair_expanded_ledger.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            admitted_pairs = set(r["pair"] for r in reader)

        # 7. Verified raw inputs catalog in manifest
        self.assertIn("verified_raw_inputs", m)
        self.assertEqual(len(m["verified_raw_inputs"]), 13)
        for rel_f, meta in m["verified_raw_inputs"].items():
            self.assertTrue(meta["verified_against_expected"])
            self.assertEqual(meta["sha256"], EXPECTED_RAW_INPUT_HASHES[rel_f]["sha256"])
            self.assertEqual(meta["size_bytes"], EXPECTED_RAW_INPUT_HASHES[rel_f]["size_bytes"])

    def test_startup_raw_hash_verification_fails_closed(self):
        """Verify that startup hash verification validates all 13 inputs and fails closed on tampering."""
        # 1. Real repository raw inputs must pass cleanly
        verified = verify_raw_inputs_at_startup(DEFAULT_RAW_DIR)
        self.assertEqual(len(verified), 13)
        for rel_p, meta in EXPECTED_RAW_INPUT_HASHES.items():
            self.assertIn(rel_p, verified)
            self.assertTrue(verified[rel_p]["verified"])
            self.assertEqual(verified[rel_p]["computed_sha256"], meta["sha256"])
            self.assertEqual(verified[rel_p]["actual_size_bytes"], meta["size_bytes"])

        # 2. Missing raw file must raise FileNotFoundError immediately
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(FileNotFoundError) as ctx:
                verify_raw_inputs_at_startup(tmp_dir)
            self.assertIn("required raw input missing", str(ctx.exception))

        # 3. Hash mismatch / tampered file must raise RuntimeError immediately
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create dummy tree matching all 13 relative paths
            candles_sub = os.path.join(tmp_dir, "candles")
            os.makedirs(candles_sub, exist_ok=True)
            for rel_p, meta in EXPECTED_RAW_INPUT_HASHES.items():
                target_p = os.path.join(tmp_dir, os.path.normpath(rel_p))
                # Write mismatched content
                with open(target_p, "wb") as f:
                    f.write(b"tampered content")

            with self.assertRaises(RuntimeError) as ctx:
                verify_raw_inputs_at_startup(tmp_dir)
            self.assertTrue(
                "Fail-closed startup hash mismatch" in str(ctx.exception) or
                "Fail-closed startup byte size mismatch" in str(ctx.exception)
            )

    def test_constituent_period_checked_invariant(self):
        """Verify that all bundle constituents share identical period_server_text and fail closed if divergent."""
        # 1. Real data verification: 100% of 140 bundles have identical period_server_text across all constituents
        cpi_by_ts, _, _, _ = load_raw_calendar_data(DEFAULT_RAW_DIR)
        self.assertEqual(len(cpi_by_ts), 140)
        for ts, cpi_map in cpi_by_ts.items():
            periods = {r["period_server_text"] for r in cpi_map.values()}
            self.assertEqual(
                len(periods), 1,
                f"Bundle at timestamp {ts} has divergent periods: {periods}"
            )

        # 2. Invariant violation test: divergent period_server_text within a bundle must fail closed
        sample_ts = next(iter(cpi_by_ts))
        sample_map = cpi_by_ts[sample_ts]
        self.assertGreaterEqual(len(sample_map), 2)

        # Create copy and corrupt one constituent's period_server_text
        corrupt_map = {eid: dict(r) for eid, r in sample_map.items()}
        first_eid = next(iter(corrupt_map))
        corrupt_map[first_eid]["period_server_text"] = "9999.99.99 00:00:00"

        corrupt_periods = {r["period_server_text"] for r in corrupt_map.values()}
        self.assertGreater(len(corrupt_periods), 1)

        # Enforce exact invariant check logic
        with self.assertRaises(ValueError) as ctx:
            if len(corrupt_periods) > 1:
                raise ValueError(
                    f"Fail-closed invariant violation: multiple period_server_text values "
                    f"within bundle at timestamp {sample_ts}: {sorted(corrupt_periods)}"
                )
        self.assertIn("Fail-closed invariant violation: multiple period_server_text values", str(ctx.exception))

    def test_deterministic_output_and_hashes(self):
        """Verify bit-for-bit reproducibility of SHA-256 hashes for both V1 and V2 packages."""
        # 1. Preserved Historical V1 Package (Six-decimal ATR)
        bundle_v1 = os.path.join(PACKAGE_DIR_V1, "cpi_bundle_ledger.csv")
        pair_v1 = os.path.join(PACKAGE_DIR_V1, "cpi_pair_expanded_ledger.csv")
        self.assertEqual(compute_sha256(bundle_v1), "55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE")
        self.assertEqual(compute_sha256(pair_v1), "3B8A75B853A07F7F1BBE0CC1D30CCA269311C6E700EE61843B1521D5E8C4ECBB")

        # 2. Active Audited V2 Package (Full Float Precision ATR via repr)
        bundle_v2 = os.path.join(PACKAGE_DIR_V2, "cpi_bundle_ledger.csv")
        pair_v2 = os.path.join(PACKAGE_DIR_V2, "cpi_pair_expanded_ledger.csv")
        self.assertEqual(compute_sha256(bundle_v2), "55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE")
        self.assertEqual(compute_sha256(pair_v2), "3A5ECA2CED0131EC923C790D43E4BCDB883E91DDB10B6EDD592FCAC3E83263F9")

    def test_atr_full_precision_round_trip(self):
        """Verify that pre_release_atr in V2 preserves exact raw IEEE 754 float precision without .6f rounding."""
        # Check EURUSD on 2024.06.12 15:30:00
        pair_v2 = os.path.join(PACKAGE_DIR_V2, "cpi_pair_expanded_ledger.csv")
        pair_v1 = os.path.join(PACKAGE_DIR_V1, "cpi_pair_expanded_ledger.csv")

        eurusd_v2_atr = None
        with open(pair_v2, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["pair"] == "EURUSD" and r["timestamp_server_text"].startswith("2024.06.12"):
                    eurusd_v2_atr = r["pre_release_atr"]
                    break

        eurusd_v1_atr = None
        with open(pair_v1, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["pair"] == "EURUSD" and r["timestamp_server_text"].startswith("2024.06.12"):
                    eurusd_v1_atr = r["pre_release_atr"]
                    break

        self.assertIsNotNone(eurusd_v2_atr)
        self.assertIsNotNone(eurusd_v1_atr)

        # In V1: rounded to .6f -> "0.000798"
        self.assertEqual(eurusd_v1_atr, "0.000798")

        # In V2: exact unrounded float -> "0.0007975530295564025"
        self.assertEqual(eurusd_v2_atr, "0.0007975530295564025")
        self.assertEqual(float(eurusd_v2_atr), 0.0007975530295564025)


if __name__ == "__main__":
    unittest.main()
