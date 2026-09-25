"""
Synthetic Unit Tests for ISM Reconciliation Engine
Tests headline surprise classification, multi-component contingency matrix,
S&P Global 900-second lead detection, collision filtering, and active H1 path logic.
"""

import unittest
from src.ism_reconciliation import (
    audit_ism_headline,
    audit_headline_prices_paid_matrix,
    audit_sp_global,
    audit_foreign_currency_collisions,
    audit_candle_paths_from_timestamps,
    SECONDS_IN_H1,
)


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

    def test_audit_candle_paths_active_bars_and_weekend_gap(self):
        # Create synthetic candle timestamps:
        # Start at 0, generate consecutive 1-hour timestamps
        # Insert a weekend gap at bar 10 (gap of 48 hours)
        # Total bars: 60 bars
        t0 = 100000
        candle_ts = []
        curr = t0
        for i in range(60):
            candle_ts.append(curr)
            if i == 10:
                # Weekend gap: add 48 hours instead of 1 hour
                curr += 48 * SECONDS_IN_H1
            else:
                curr += SECONDS_IN_H1

        # Release at t0 - 3600 -> entry at t0 (bar 0)
        release_ts = t0 - 3600
        path_res = audit_candle_paths_from_timestamps(candle_ts, [release_ts])

        self.assertEqual(path_res["evaluated_packages"], 1)
        self.assertEqual(path_res["paths_24_complete"], 1)
        self.assertEqual(path_res["weekend_cross_24"], 1)  # Crosses the gap at bar 10
        self.assertEqual(path_res["paths_48_complete"], 1)
        self.assertEqual(path_res["weekend_cross_48"], 1)

        details = path_res["details"][0]
        self.assertEqual(details["entry_ts"], t0)
        self.assertTrue(details["crosses_weekend_24"])
        # Final active bar for 24-bar horizon is bar index 23
        self.assertEqual(details["final_bar_open_24"], candle_ts[23])


if __name__ == "__main__":
    unittest.main()
