"""
Synthetic & Empirical Unit Tests for Count Reconciliation
Verifies exact counts, completeness numbers, joint package identities,
and forward-path coverage against pinned data.
"""

import unittest
import os
from src.calendar_reconciliation import reconcile_retail_sales_series
from src.package_ledger import (
    build_retail_sales_package_ledger,
    audit_strict_agreement_subsamples,
    audit_ifo_benchmark,
    audit_control_availability
)
from src.candle_coverage import CandleTimestampIndex

PINNED_CALENDAR_PATH = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv"
PINNED_EURUSD_PATH = "data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv"
PINNED_IFO_PATH = "evidence/trials/ifo/ifo_pilot_ledger.json"


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

    def test_package_ledger_forward_coverage_and_collisions(self):
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

        # Collision counts and denominators
        colls = ledger["cross_currency_collisions"]
        self.assertEqual(colls["all_pre2023"]["count"], 45)
        self.assertAlmostEqual(colls["all_pre2023"]["pct"], 45 / 96, places=4)
        self.assertEqual(colls["complete_afp"]["count"], 39)
        self.assertAlmostEqual(colls["complete_afp"]["pct"], 39 / 68, places=4)

        # Forward path coverage on complete AFP: 100% complete for both horizons!
        if os.path.exists(PINNED_EURUSD_PATH):
            fwd = ledger["forward_coverage_complete_afp"]
            self.assertEqual(fwd["h6_clean_count"], 68)
            self.assertEqual(fwd["h6_clean_pct"], 1.0)
            self.assertEqual(fwd["h6_weekend_crossings"], 22)
            self.assertAlmostEqual(fwd["h6_weekend_pct"], 22 / 68, places=4)

            self.assertEqual(fwd["h12_clean_count"], 68)
            self.assertEqual(fwd["h12_clean_pct"], 1.0)
            self.assertEqual(fwd["h12_weekend_crossings"], 35)
            self.assertAlmostEqual(fwd["h12_weekend_pct"], 35 / 68, places=4)

            # Audit pre-entry lookback attrition: 16 releases occur on Mon/Tue and fail intra-week 14 lookback
            mon_tue_count = sum(1 for p in ledger["packages"] if p["joint_afp_complete"] and p["weekday"] in ("Monday", "Tuesday"))
            self.assertEqual(mon_tue_count, 16)  # 5 Monday + 11 Tuesday

    def test_strict_agreement_subsamples(self):
        ledger = build_retail_sales_package_ledger(
            PINNED_CALENDAR_PATH,
            PINNED_EURUSD_PATH if os.path.exists(PINNED_EURUSD_PATH) else None
        )
        sub = audit_strict_agreement_subsamples(ledger)

        self.assertEqual(sub["total_strict_agreement"], 49)
        self.assertEqual(sub["strict_pos"], 27)
        self.assertEqual(sub["strict_neg"], 22)

        # 1. Friday Filter (leaves 34)
        ff = sub["friday_filter"]
        self.assertEqual(ff["fridays_count"], 15)
        self.assertEqual(ff["remaining_non_fridays_count"], 34)

        # 2. Strict Same-Week 14-H4 Lookback Filter (leaves 37)
        lf = sub["lookback_filter"]
        self.assertEqual(lf["failures_count"], 12)
        self.assertEqual(lf["remaining_passes_count"], 37)

        # 3. Cross-Currency Collision Filter (leaves 19)
        cf = sub["collision_filter"]
        self.assertEqual(cf["collisions_count"], 30)
        self.assertEqual(cf["remaining_collision_free_count"], 19)

        # 4. Combined clean intersection (leaves 6)
        self.assertEqual(sub["combined_clean_intersection_count"], 6)

    def test_ifo_benchmark_reconciliation(self):
        if not os.path.exists(PINNED_IFO_PATH) or not os.path.exists(PINNED_EURUSD_PATH):
            raise unittest.SkipTest("Ifo ledger or EURUSD candles not found")

        candle_index = CandleTimestampIndex(PINNED_EURUSD_PATH)
        ifo_audit = audit_ifo_benchmark(PINNED_IFO_PATH, candle_index)

        self.assertEqual(ifo_audit["total_actionable"], 40)
        self.assertEqual(ifo_audit["friday_episodes_count"], 6)
        self.assertEqual(ifo_audit["h6_weekend_crossings_count"], 6)
        self.assertAlmostEqual(ifo_audit["h6_weekend_crossings_pct"], 6 / 40, places=4)

        # Bundled series verification
        series_eids = [s["event_id"] for s in ifo_audit["ifo_bundled_series"]]
        self.assertIn("276030001", series_eids)  # Expectations
        self.assertIn("276030002", series_eids)  # Current Business Situation
        self.assertIn("276030003", series_eids)  # Climate

    def test_control_availability_reconciliation(self):
        ledger = build_retail_sales_package_ledger(
            PINNED_CALENDAR_PATH,
            PINNED_EURUSD_PATH if os.path.exists(PINNED_EURUSD_PATH) else None
        )
        ctrl = audit_control_availability(ledger["packages"], PINNED_CALENDAR_PATH)

        self.assertEqual(ctrl["total_evaluated_packages"], 49)
        self.assertEqual(ctrl["clean_7d_count"], 14)
        self.assertAlmostEqual(ctrl["clean_7d_pct"], 14 / 49, places=4)
        self.assertEqual(ctrl["clean_14d_count"], 5)
        self.assertAlmostEqual(ctrl["clean_14d_pct"], 5 / 49, places=4)
        self.assertEqual(ctrl["clean_either_count"], 17)
        self.assertAlmostEqual(ctrl["clean_either_pct"], 17 / 49, places=4)
        self.assertEqual(ctrl["contaminated_both_count"], 32)
        self.assertAlmostEqual(ctrl["contaminated_both_pct"], 32 / 49, places=4)


if __name__ == "__main__":
    unittest.main()
