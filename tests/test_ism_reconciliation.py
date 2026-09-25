"""
Synthetic Unit Tests for ISM Reconciliation Engine
Tests headline surprise classification, multi-component contingency matrix,
S&P Global 900-second lead detection, collision filtering, transition validation,
and strict price-blind timestamp reader constraints.
"""

import unittest
import tempfile
import os
from src.ism_reconciliation import (
    audit_ism_headline,
    audit_headline_prices_paid_matrix,
    audit_multi_component_concordance,
    audit_sp_global,
    audit_foreign_currency_collisions,
    audit_calendar_metadata,
    validate_h1_path_transitions,
    audit_candle_paths_from_timestamps,
    load_pre2023_releases,
    DEFAULT_DATA_DIR,
    SECONDS_IN_H1,
    SPLIT_TIMESTAMP,
)
from src.parsers import stream_candle_timestamps_only


class TestIsmReconciliation(unittest.TestCase):

    def test_audit_ism_headline_classification(self):
        # Synthetic releases: 1 positive, 1 negative, 1 zero, 1 incomplete
        by_event = {
            "840040001": [
                {
                    "timestamp": "1500000000",
                    "actual_raw_scaled_1e6": "55000000",
                    "forecast_raw_scaled_1e6": "52000000",
                    "previous_raw_scaled_1e6": "50000000",
                },
                {
                    "timestamp": "1503000000",
                    "actual_raw_scaled_1e6": "48000000",
                    "forecast_raw_scaled_1e6": "50000000",
                    "previous_raw_scaled_1e6": "51000000",
                },
                {
                    "timestamp": "1506000000",
                    "actual_raw_scaled_1e6": "50000000",
                    "forecast_raw_scaled_1e6": "50000000",
                    "previous_raw_scaled_1e6": "50000000",
                },
                {
                    "timestamp": "1509000000",
                    "actual_raw_scaled_1e6": "52000000",
                    "forecast_raw_scaled_1e6": "",
                    "previous_raw_scaled_1e6": "50000000",
                },
            ]
        }

        result = audit_ism_headline(by_event)
        self.assertEqual(result["total_pre2023"], 4)
        self.assertEqual(result["complete_afp_count"], 3)
        self.assertEqual(result["incomplete_count"], 1)
        self.assertEqual(result["positive_count"], 1)
        self.assertEqual(result["negative_count"], 1)
        self.assertEqual(result["zero_count"], 1)
        self.assertEqual(result["actionable_count"], 2)
        self.assertIn(1500000000, result["actionable_timestamps"])
        self.assertIn(1503000000, result["actionable_timestamps"])
        self.assertNotIn(1506000000, result["actionable_timestamps"])

    def test_audit_headline_prices_paid_matrix(self):
        complete_afp = [
            {"timestamp": "100", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "50"},  # Headline POS (+10)
            {"timestamp": "200", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "50"},  # Headline POS (+10)
            {"timestamp": "300", "actual_raw_scaled_1e6": "40", "forecast_raw_scaled_1e6": "50"},  # Headline NEG (-10)
            {"timestamp": "400", "actual_raw_scaled_1e6": "40", "forecast_raw_scaled_1e6": "50"},  # Headline NEG (-10)
            {"timestamp": "500", "actual_raw_scaled_1e6": "50", "forecast_raw_scaled_1e6": "50"},  # Headline ZERO
        ]
        by_event = {
            "840040002": [
                {"timestamp": "100", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60"},  # PP POS (+10) -> POS/POS
                {"timestamp": "200", "actual_raw_scaled_1e6": "50", "forecast_raw_scaled_1e6": "60"},  # PP NEG (-10) -> POS/NEG
                {"timestamp": "300", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60"},  # PP POS (+10) -> NEG/POS
                {"timestamp": "400", "actual_raw_scaled_1e6": "50", "forecast_raw_scaled_1e6": "60"},  # PP NEG (-10) -> NEG/NEG
                {"timestamp": "500", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60"},  # PP POS (+10) -> ZERO/POS
            ]
        }

        matrix = audit_headline_prices_paid_matrix(by_event, complete_afp)
        self.assertEqual(matrix["POS/POS"], 1)
        self.assertEqual(matrix["POS/NEG"], 1)
        self.assertEqual(matrix["NEG/POS"], 1)
        self.assertEqual(matrix["NEG/NEG"], 1)
        self.assertEqual(matrix["ZERO/POS"], 1)
        self.assertEqual(matrix["POS/ZERO"], 0)

    def test_audit_multi_component_concordance(self):
        # Synthetic releases across:
        # 840040001: Headline
        # 840040002: Prices Paid
        # 840040004: Employment
        # 840040006: New Orders
        #
        # Cases:
        # 1000: All 4 POS (HEN pos, HPE pos, C4 pos)
        # 2000: All 4 NEG (HEN neg, HPE neg, C4 neg)
        # 3000: PP is NEG, others POS (HEN pos, HPE disc, C4 disc)
        # 4000: NO is POS, others NEG (HEN disc, HPE neg, C4 disc)
        # 5000: Emp is NEG, others POS (HEN disc, HPE disc, C4 disc)
        # 6000: NO missing forecast, others POS (HEN incomp, HPE pos, C4 incomp)
        # 7000: Headline surprise == 0 (not in actionable_timestamps, excluded from all)
        by_event = {
            "840040001": [
                {"timestamp": "1000", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "2000", "actual_raw_scaled_1e6": "40", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "3000", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "4000", "actual_raw_scaled_1e6": "40", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "5000", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "6000", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "7000", "actual_raw_scaled_1e6": "50", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "8000", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
            ],
            "840040002": [
                {"timestamp": "1000", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "2000", "actual_raw_scaled_1e6": "50", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "3000", "actual_raw_scaled_1e6": "50", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "4000", "actual_raw_scaled_1e6": "50", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "5000", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "6000", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "7000", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "8000", "actual_raw_scaled_1e6": "70", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
            ],
            "840040004": [
                {"timestamp": "1000", "actual_raw_scaled_1e6": "55", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "2000", "actual_raw_scaled_1e6": "45", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "3000", "actual_raw_scaled_1e6": "55", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "4000", "actual_raw_scaled_1e6": "45", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "5000", "actual_raw_scaled_1e6": "45", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "6000", "actual_raw_scaled_1e6": "55", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "7000", "actual_raw_scaled_1e6": "55", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
                {"timestamp": "8000", "actual_raw_scaled_1e6": "55", "forecast_raw_scaled_1e6": "50", "previous_raw_scaled_1e6": "50"},
            ],
            "840040006": [
                {"timestamp": "1000", "actual_raw_scaled_1e6": "65", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "2000", "actual_raw_scaled_1e6": "55", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "3000", "actual_raw_scaled_1e6": "65", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "4000", "actual_raw_scaled_1e6": "65", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "5000", "actual_raw_scaled_1e6": "65", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "6000", "actual_raw_scaled_1e6": "65", "forecast_raw_scaled_1e6": "", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "7000", "actual_raw_scaled_1e6": "65", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
                {"timestamp": "8000", "actual_raw_scaled_1e6": "60", "forecast_raw_scaled_1e6": "60", "previous_raw_scaled_1e6": "60"},
            ],
        }
        ism_audit = {
            "actionable_timestamps": {1000, 2000, 3000, 4000, 5000, 6000, 8000}
        }

        mc = audit_multi_component_concordance(by_event, ism_audit)

        # 1. Headline + Employment + New Orders
        hen = mc["headline_emp_neworders"]
        self.assertEqual(hen["complete_packages"], 6)
        self.assertEqual(hen["concordant_total"], 3)
        self.assertEqual(hen["concordant_positive"], 2)
        self.assertEqual(hen["concordant_negative"], 1)
        self.assertEqual(hen["discordant_total"], 3)
        self.assertEqual(hen["opposite_sign_total"], 2)
        self.assertEqual(hen["neutral_component_total"], 1)

        # 2. Headline + Prices Paid + Employment
        hpe = mc["headline_prices_paid_emp"]
        self.assertEqual(hpe["complete_packages"], 7)
        self.assertEqual(hpe["concordant_total"], 5)
        self.assertEqual(hpe["concordant_positive"], 3)
        self.assertEqual(hpe["concordant_negative"], 2)
        self.assertEqual(hpe["discordant_total"], 2)
        self.assertEqual(hpe["opposite_sign_total"], 2)
        self.assertEqual(hpe["neutral_component_total"], 0)

        # 3. All Four Components
        c4 = mc["all_four_components"]
        self.assertEqual(c4["complete_packages"], 6)
        self.assertEqual(c4["concordant_total"], 2)
        self.assertEqual(c4["concordant_positive"], 1)
        self.assertEqual(c4["concordant_negative"], 1)
        self.assertEqual(c4["discordant_total"], 4)
        self.assertEqual(c4["opposite_sign_total"], 3)
        self.assertEqual(c4["neutral_component_total"], 1)

    def test_audit_sp_global_timing(self):
        ism_releases = [
            {"timestamp": "1000"},  # target S&P = 100
            {"timestamp": "2000"},  # target S&P = 1100
        ]
        actionable_ts = {1000}
        by_event = {
            "840500001": [
                {"timestamp": "100", "revision": "3", "forecast_raw_scaled_1e6": "50000000"},
                {"timestamp": "1050", "revision": "3", "forecast_raw_scaled_1e6": "50000000"},  # not 1100
                {"timestamp": "100", "revision": "1", "forecast_raw_scaled_1e6": "50000000"},
            ]
        }

        sp_res = audit_sp_global(by_event, ism_releases, actionable_ts)
        self.assertEqual(sp_res["rev3_total"], 2)
        self.assertEqual(sp_res["rev1_total"], 1)
        self.assertEqual(sp_res["rev3_exact_900s_all"], 1)
        self.assertEqual(sp_res["rev3_exact_900s_with_fc_all"], 1)
        self.assertEqual(sp_res["rev3_exact_900s_actionable"], 1)
        self.assertEqual(sp_res["rev3_exact_900s_with_fc_actionable"], 1)
        self.assertEqual(len(sp_res["dates_not_900s"]), 1)
        self.assertEqual(sp_res["dates_not_900s"][0]["ism_timestamp"], 2000)

    def test_audit_foreign_currency_collisions(self):
        all_releases = [
            {"timestamp": "1000", "currency": "USD", "event_id": "840040001", "event_name": "ISM PMI"},
            {"timestamp": "1000", "currency": "CAD", "event_id": "124040006", "event_name": "BoC Rate"},
            {"timestamp": "2000", "currency": "USD", "event_id": "840040001", "event_name": "ISM PMI"},
            {"timestamp": "2000", "currency": "USD", "event_id": "840020002", "event_name": "Construction Spending"},
        ]
        ism_releases = [
            {"timestamp": "1000"},
            {"timestamp": "2000"},
        ]
        actionable_ts = {1000}

        collisions = audit_foreign_currency_collisions(all_releases, ism_releases, actionable_ts)
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0]["currency"], "CAD")
        self.assertEqual(collisions[0]["event_id"], "124040006")
        self.assertTrue(collisions[0]["is_actionable"])

    def test_path_with_missing_weekday(self):
        # Wednesday 2020-09-16 12:00 UTC = 1600257600
        # Create a 24-bar sequence with a missing 24-hour gap between bar 5 and bar 6 (Wednesday to Thursday)
        t0 = 1600257600
        bars = []
        curr = t0
        for i in range(24):
            bars.append(curr)
            if i == 5:
                # Arbitrary weekday gap of 24h
                curr += 24 * SECONDS_IN_H1
            else:
                curr += SECONDS_IN_H1

        is_valid, crosses_weekend, reason = validate_h1_path_transitions(bars, split_timestamp=SPLIT_TIMESTAMP)
        self.assertFalse(is_valid)
        self.assertIn("weekday data gap", reason)

        # In full path audit, package must be marked incomplete
        res = audit_candle_paths_from_timestamps(bars, [t0 - SECONDS_IN_H1], split_timestamp=SPLIT_TIMESTAMP)
        self.assertEqual(res["paths_24_complete"], 0)

    def test_path_with_valid_weekend_closure(self):
        # Friday 2020-09-18 20:00 UTC = 1600459200
        # 4 bars on Friday (20:00, 21:00, 22:00, 23:00)
        # Gap from Friday 23:00 to Sunday 23:00 (48h)
        # 20 bars on Sunday/Monday
        t0 = 1600459200
        bars = []
        curr = t0
        for i in range(24):
            bars.append(curr)
            if i == 3:
                # Weekend gap: Friday 23:00 to Sunday 23:00 (48 hours)
                curr += 48 * SECONDS_IN_H1
            else:
                curr += SECONDS_IN_H1

        is_valid, crosses_weekend, reason = validate_h1_path_transitions(bars, split_timestamp=SPLIT_TIMESTAMP)
        self.assertTrue(is_valid)
        self.assertTrue(crosses_weekend)
        self.assertEqual(reason, "Valid path")

        res = audit_candle_paths_from_timestamps(bars, [t0 - SECONDS_IN_H1], split_timestamp=SPLIT_TIMESTAMP)
        self.assertEqual(res["paths_24_complete"], 1)
        self.assertEqual(res["weekend_cross_24"], 1)

    def test_path_crossing_split(self):
        # SPLIT_TIMESTAMP = 1672531200
        # Bar sequence starting 10 hours before split, extending past split
        t_start = SPLIT_TIMESTAMP - 10 * SECONDS_IN_H1
        bars = [t_start + i * SECONDS_IN_H1 for i in range(24)]

        is_valid, _, reason = validate_h1_path_transitions(bars, split_timestamp=SPLIT_TIMESTAMP)
        self.assertFalse(is_valid)
        self.assertIn("at or beyond split", reason)

    def test_split_boundary_exit_close(self):
        # Case 1: Valid 24-bar H1 path where all bars are H1-aligned (ts % 3600 == 0).
        # Final bar opens at SPLIT_TIMESTAMP - 3600 (1672527600, 2022-12-31 23:00:00).
        # Its close is (SPLIT_TIMESTAMP - 3600) + 3600 = SPLIT_TIMESTAMP (1672531200).
        # Under exit_close_ts <= SPLIT_TIMESTAMP, this strictly satisfies the holdout seal.
        t_start_valid = SPLIT_TIMESTAMP - 24 * SECONDS_IN_H1
        bars_valid = [t_start_valid + i * SECONDS_IN_H1 for i in range(24)]
        self.assertTrue(all(ts % SECONDS_IN_H1 == 0 for ts in bars_valid))
        self.assertEqual(bars_valid[-1], SPLIT_TIMESTAMP - SECONDS_IN_H1)
        is_valid, _, reason = validate_h1_path_transitions(bars_valid, split_timestamp=SPLIT_TIMESTAMP)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "Valid path")

        # Case 2: H1-aligned 24-bar path starting 1 hour later (at SPLIT_TIMESTAMP - 23 * 3600).
        # Bar 0 opens before the split (1672448400 < SPLIT_TIMESTAMP).
        # All bars are exact multiples of 3600.
        # But final bar (bar 23) opens at SPLIT_TIMESTAMP (1672531200) and closes at
        # SPLIT_TIMESTAMP + 3600 (1672534800, 2023-01-01 01:00:00).
        # validate_h1_path_transitions must reject this path.
        t_start_cross = SPLIT_TIMESTAMP - 23 * SECONDS_IN_H1
        bars_cross = [t_start_cross + i * SECONDS_IN_H1 for i in range(24)]
        self.assertTrue(all(ts % SECONDS_IN_H1 == 0 for ts in bars_cross))
        self.assertLess(bars_cross[0], SPLIT_TIMESTAMP)
        self.assertEqual(bars_cross[-1], SPLIT_TIMESTAMP)
        is_valid_cross, _, reason_cross = validate_h1_path_transitions(bars_cross, split_timestamp=SPLIT_TIMESTAMP)
        self.assertFalse(is_valid_cross)
        self.assertIn("at or beyond split", reason_cross)

        # Case 3: Single H1-aligned bar opening at SPLIT_TIMESTAMP (1672531200).
        # Exact multiple of 3600; closes at SPLIT_TIMESTAMP + 3600 (1672534800).
        bars_at_split = [SPLIT_TIMESTAMP]
        self.assertEqual(bars_at_split[0] % SECONDS_IN_H1, 0)
        is_valid_single, _, reason_single = validate_h1_path_transitions(
            bars_at_split, split_timestamp=SPLIT_TIMESTAMP
        )
        self.assertFalse(is_valid_single)
        self.assertIn("at or beyond split", reason_single)

    def test_duplicate_or_unsorted_timestamps(self):
        t0 = 1600000000
        # Duplicate bar
        bars_dup = [t0, t0 + 3600, t0 + 3600, t0 + 7200]
        valid_dup, _, reason_dup = validate_h1_path_transitions(bars_dup, split_timestamp=SPLIT_TIMESTAMP)
        self.assertFalse(valid_dup)
        self.assertIn("Duplicate or unsorted", reason_dup)

        # Unsorted bar (t1 > t2)
        bars_unsorted = [t0 + 3600, t0, t0 + 7200]
        valid_unsorted, _, reason_unsorted = validate_h1_path_transitions(bars_unsorted, split_timestamp=SPLIT_TIMESTAMP)
        self.assertFalse(valid_unsorted)
        self.assertIn("Duplicate or unsorted", reason_unsorted)

        # Global audit rejects unsorted candle list
        with self.assertRaises(ValueError) as ctx:
            audit_candle_paths_from_timestamps(bars_dup, [t0 - 3600], split_timestamp=SPLIT_TIMESTAMP)
        self.assertIn("Duplicate or unsorted", str(ctx.exception))

    def test_malformed_non_time_candle_fields(self):
        # Tests that stream_candle_timestamps_only genuinely reads only column 0
        # and does not crash or tokenize invalid price/spread garbage
        content = (
            "time,open,high,low,close,tick_volume,spread,real_volume\n"
            "1600000000,INVALID_OPEN,CORRUPT_HIGH,NaN,INF,BAD_VOL,#DIV/0,NULL\n"
            "1600003600,GARBAGE,GARBAGE,GARBAGE,GARBAGE,GARBAGE,GARBAGE,GARBAGE\n"
            f"{SPLIT_TIMESTAMP},SPLIT_ROW,CORRUPT,NaN,NaN,0,0,0\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            ts = list(stream_candle_timestamps_only(tmp_path, split_timestamp=SPLIT_TIMESTAMP))
            self.assertEqual(ts, [1600000000, 1600003600])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_metadata_missing_fields_raises(self):
        # When a required field like sector_code is missing or empty,
        # audit_calendar_metadata must raise ValueError and NOT substitute defaults
        content = (
            "event_id,event_name,event_code,sector,sector_code,unit,unit_code,importance,importance_code\n"
            "840040001,ISM Manufacturing PMI,ism-manufacturing-pmi,CALENDAR_SECTOR_BUSINESS,,CALENDAR_UNIT_NONE,0,high,3\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            with self.assertRaises(ValueError) as ctx:
                audit_calendar_metadata(tmp_path)
            self.assertIn("Missing or empty required metadata field 'sector_code'", str(ctx.exception))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_pinned_calendar_multi_component_reconciliation(self):
        cal_path = os.path.join(DEFAULT_DATA_DIR, "calendar_releases.csv")
        if not os.path.exists(cal_path):
            self.skipTest(f"Pinned calendar not found at {cal_path}")

        _, by_event = load_pre2023_releases(cal_path)
        ism_audit = audit_ism_headline(by_event)
        mc = audit_multi_component_concordance(by_event, ism_audit)

        # 1. Headline + Employment + New Orders
        hen = mc["headline_emp_neworders"]
        self.assertEqual(hen["complete_packages"], 63)
        self.assertEqual(hen["concordant_total"], 23)
        self.assertEqual(hen["concordant_positive"], 12)
        self.assertEqual(hen["concordant_negative"], 11)
        self.assertEqual(hen["discordant_total"], 40)
        self.assertEqual(hen["opposite_sign_total"], 38)
        self.assertEqual(hen["neutral_component_total"], 2)

        # 2. Headline + Prices Paid + Employment
        hpe = mc["headline_prices_paid_emp"]
        self.assertEqual(hpe["complete_packages"], 63)
        self.assertEqual(hpe["concordant_total"], 20)
        self.assertEqual(hpe["concordant_positive"], 9)
        self.assertEqual(hpe["concordant_negative"], 11)
        self.assertEqual(hpe["discordant_total"], 43)
        self.assertEqual(hpe["opposite_sign_total"], 43)
        self.assertEqual(hpe["neutral_component_total"], 0)

        # 3. All Four Components (Headline + Prices Paid + Employment + New Orders)
        c4 = mc["all_four_components"]
        self.assertEqual(c4["complete_packages"], 63)
        self.assertEqual(c4["concordant_total"], 10)
        self.assertEqual(c4["concordant_positive"], 6)
        self.assertEqual(c4["concordant_negative"], 4)
        self.assertEqual(c4["discordant_total"], 53)
        self.assertEqual(c4["opposite_sign_total"], 51)
        self.assertEqual(c4["neutral_component_total"], 2)


if __name__ == "__main__":
    unittest.main()
