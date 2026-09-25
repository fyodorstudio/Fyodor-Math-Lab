"""
Synthetic & Empirical Unit Tests for Count Reconciliation
Verifies exact counts, completeness numbers, and joint package identities against pinned data.
"""

import unittest
import os
from src.calendar_reconciliation import reconcile_retail_sales_series
from src.package_ledger import build_retail_sales_package_ledger

PINNED_CALENDAR_PATH = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv"
PINNED_EURUSD_PATH = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv"


class TestCountReconciliation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(PINNED_CALENDAR_PATH):
            raise unittest.SkipTest(f"Pinned calendar not found at {PINNED_CALENDAR_PATH}")

    def test_reconcile_retail_sales_counts(self):
        rec = reconcile_retail_sales_series(PINNED_CALENDAR_PATH)

        h = rec["headline"]
        c = rec["core"]
        j = rec["joint_package"]

        # Exact identities
        self.assertEqual(h["series_key"], "USD:US:840020010:r0")
        self.assertEqual(h["event_id"], "840020010")
        self.assertEqual(h["event_name"], "Retail Sales m/m")
        self.assertEqual(h["event_code"], "retail-sales-mm")
        self.assertEqual(h["unit"], "CALENDAR_UNIT_PERCENT")
        self.assertEqual(h["revisions_seen"], [0])

        self.assertEqual(c["series_key"], "USD:US:840020011:r0")
        self.assertEqual(c["event_id"], "840020011")
        self.assertEqual(c["event_name"], "Core Retail Sales m/m")
        self.assertEqual(c["event_code"], "retail-sales-ex-autos-mm")
        self.assertEqual(c["unit"], "CALENDAR_UNIT_PERCENT")
        self.assertEqual(c["revisions_seen"], [0])

        # Release counts
        self.assertEqual(h["total_releases"], 141)
        self.assertEqual(h["pre2023_releases"], 96)
        self.assertEqual(h["post2022_sealed_releases"], 45)
        self.assertEqual(h["complete_afp_pre2023"], 68)
        self.assertEqual(h["missing_forecast_pre2023"], 28)

        self.assertEqual(c["total_releases"], 141)
        self.assertEqual(c["pre2023_releases"], 96)
        self.assertEqual(c["post2022_sealed_releases"], 45)
        self.assertEqual(c["complete_afp_pre2023"], 68)
        self.assertEqual(c["missing_forecast_pre2023"], 28)

        # Joint package verification
        self.assertEqual(j["total_distinct_timestamps"], 96)
        self.assertEqual(j["co_released_timestamps"], 96)
        self.assertEqual(j["headline_only_timestamps"], 0)
        self.assertEqual(j["core_only_timestamps"], 0)
        self.assertEqual(j["joint_complete_afp"], 68)
        self.assertEqual(j["joint_missing_forecast"], 28)

    def test_package_ledger_concordance_and_collisions(self):
        ledger = build_retail_sales_package_ledger(
            PINNED_CALENDAR_PATH,
            PINNED_EURUSD_PATH if os.path.exists(PINNED_EURUSD_PATH) else None
        )

        self.assertEqual(ledger["total_packages"], 96)
        self.assertEqual(ledger["complete_joint_afp_packages"], 68)

        signs = ledger["sign_distribution"]
        self.assertEqual(signs.get("STRICT_AGREE_POS"), 27)
        self.assertEqual(signs.get("STRICT_AGREE_NEG"), 22)
        self.assertEqual(signs.get("ACTIVE_CONFLICT"), 9)
        self.assertEqual(signs.get("ONE_ZERO"), 8)
        self.assertEqual(signs.get("BOTH_ZERO"), 2)
        self.assertEqual(signs.get("MISSING_FORECAST"), 28)

        # Total complete AFP = 27 + 22 + 9 + 8 + 2 = 68
        total_complete = sum(signs[k] for k in ["STRICT_AGREE_POS", "STRICT_AGREE_NEG", "ACTIVE_CONFLICT", "ONE_ZERO", "BOTH_ZERO"])
        self.assertEqual(total_complete, 68)

        # Collision counts
        colls = ledger["cross_currency_collisions"]
        self.assertEqual(colls["all_pre2023"]["count"], 45)
        self.assertAlmostEqual(colls["all_pre2023"]["pct"], 45 / 96, places=4)
        self.assertEqual(colls["complete_afp"]["count"], 39)
        self.assertAlmostEqual(colls["complete_afp"]["pct"], 39 / 68, places=4)


if __name__ == "__main__":
    unittest.main()
