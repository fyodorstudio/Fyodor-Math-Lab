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
    audit_sp_global,
    audit_foreign_currency_collisions,
    audit_calendar_metadata,
    validate_h1_path_transitions,
    audit_candle_paths_from_timestamps,
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


if __name__ == "__main__":
    unittest.main()
