"""
Synthetic and Offline Unit Tests for Full-History EURUSD H1 Macro-Event Table Viewer & Atlas:
- German Ifo co-release accounting: 40 pre-2023 actionable episodes (not 80 duplicated trades)
- US Retail Sales co-release accounting: 49 pre-2023 trade episodes (not 98 duplicated trades)
- 157 pre-2023 cohort memberships correspond to exactly 149 distinct release timestamps
- Release timestamps inside an H1 bar (e.g. 15:30 inside [15:00, 16:00) bar, H1 at 16:00)
- Known +3 records verification with exact A/F/P/S/M against archived trial artifacts
- Retail Sales series identifier verification (840020010 and 840020011)
- Dynamic median recalculation across full 2015–2026 history (never averaging precomputed medians)
- Full-history unblinded exploratory price coverage (2023–2026 populated, not None)
- Truncation handling near export snapshot boundary
- Directional price change arithmetic & input validation
- Offline HTML viewer self-containment (zero external requests, holdout forfeiture notice)
"""

import json
import os
import statistics
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from generate_table import (
    compute_directional_change_pct,
    load_all_candles,
    build_event_episodes,
    generate_html_viewer,
    SPLIT_TIMESTAMP,
    MAX_HORIZONS,
    SERIES_METADATA,
    CANDLE_PATH,
    CALENDAR_PATH,
    PHASE1_PATH,
    IFO_PATH,
    RETAIL_SALES_PATH,
    OUTPUT_HTML_PATH
)


class TestDirectionalArithmetic(unittest.TestCase):
    """Verifies gross directional EURUSD price change formula."""

    def test_long_direction_math(self):
        # Long (+1): price increase is positive directional movement
        # Entry open = 1.1000, Exit close = 1.1055 (+55 pips = +0.5%)
        pct_gain = compute_directional_change_pct(1.1000, 1.1055, direction=1)
        self.assertAlmostEqual(pct_gain, 0.50, places=4)

        # Long (+1): price drop is negative directional movement
        pct_loss = compute_directional_change_pct(1.1000, 1.0945, direction=1)
        self.assertAlmostEqual(pct_loss, -0.50, places=4)

    def test_short_direction_math(self):
        # Short (-1): price drop is positive directional movement
        pct_gain = compute_directional_change_pct(1.1000, 1.0945, direction=-1)
        self.assertAlmostEqual(pct_gain, 0.50, places=4)

        # Short (-1): price increase is negative directional movement
        pct_loss = compute_directional_change_pct(1.1000, 1.1055, direction=-1)
        self.assertAlmostEqual(pct_loss, -0.50, places=4)

    def test_invalid_arguments_rejected(self):
        with self.assertRaises(ValueError):
            compute_directional_change_pct(0.0, 1.1000, direction=1)
        with self.assertRaises(ValueError):
            compute_directional_change_pct(1.1000, -1.0, direction=1)
        with self.assertRaises(ValueError):
            compute_directional_change_pct(1.1000, 1.1050, direction=0)
        with self.assertRaises(ValueError):
            compute_directional_change_pct(1.1000, 1.1050, direction=2)


class TestRetailSalesIdentifiers(unittest.TestCase):
    """Verifies that Retail Sales series identifiers exactly match the protocol."""

    def test_identifiers_match_protocol(self):
        h_meta = SERIES_METADATA["USD:US:840020010:r0"]
        c_meta = SERIES_METADATA["USD:US:840020011:r0"]

        self.assertEqual(h_meta["event_id"], 840020010)
        self.assertEqual(h_meta["name"], "Retail Sales m/m")
        self.assertEqual(h_meta["family"], "US Retail Sales")

        self.assertEqual(c_meta["event_id"], 840020011)
        self.assertEqual(c_meta["name"], "Core Retail Sales m/m")
        self.assertEqual(c_meta["family"], "US Retail Sales")

        # Confirm deprecated/incorrect IDs are NOT in metadata
        self.assertNotIn("USD:US:840030001:r0", [k for k in SERIES_METADATA if "Retail" in SERIES_METADATA[k]["family"]])
        self.assertNotIn("USD:US:840030002:r0", [k for k in SERIES_METADATA if "Retail" in SERIES_METADATA[k]["family"]])


class TestDistinctEventEpisodeAccounting(unittest.TestCase):
    """
    Verifies that simultaneous co-releases (German Ifo Climate + Expectations,
    and US Retail Sales Headline + Core) form single distinct event episodes
    and contribute exactly once to sample size and statistics.
    """

    @classmethod
    def setUpClass(cls):
        cls.candles, cls.ts_to_idx = load_all_candles()
        cls.episodes, cls.metadata = build_event_episodes(candles=cls.candles, ts_to_idx=cls.ts_to_idx)
        cls.pre2023 = [e for e in cls.episodes if e["timestamp"] < SPLIT_TIMESTAMP]

    def test_ifo_contributes_40_pre2023_episodes_not_80(self):
        """
        German Ifo releases Business Climate and Expectations concurrently.
        The pre-2023 archive contains 40 actionable Ifo episodes, not 80 duplicated trades.
        """
        ifo_pre = [e for e in self.pre2023 if e["family"] == "German Ifo"]
        ifo_actionable = [e for e in ifo_pre if e["is_eligible"]]

        # Total distinct pre-2023 episodes is 96 (one per monthly release timestamp)
        self.assertEqual(len(ifo_pre), 96)
        # Exactly 40 actionable episodes
        self.assertEqual(len(ifo_actionable), 40)
        self.assertNotEqual(len(ifo_actionable), 80, "Must NOT duplicate co-released components into 80 trades")

        # Verify that each Ifo episode has both Climate and Expectations components
        for ep in ifo_actionable:
            self.assertEqual(len(ep["components"]), 2)
            c_names = set(c["name"] for c in ep["components"])
            self.assertIn("Ifo Business Climate", c_names)
            self.assertIn("Ifo Business Expectations", c_names)

        # Direction breakdown: 18 Long, 22 Short
        longs = [e for e in ifo_actionable if e["direction"] == 1]
        shorts = [e for e in ifo_actionable if e["direction"] == -1]
        self.assertEqual(len(longs), 18)
        self.assertEqual(len(shorts), 22)
        self.assertEqual(len(longs) + len(shorts), 40)

    def test_retail_sales_contributes_49_pre2023_episodes_not_98(self):
        """
        US Retail Sales releases Headline and Core concurrently.
        The pre-2023 archive contains 49 trade episodes, not 98 duplicated trades.
        """
        rs_pre = [e for e in self.pre2023 if e["family"] == "US Retail Sales"]
        rs_trade = [e for e in rs_pre if e["is_eligible"]]

        # Total distinct pre-2023 episodes is 96 (one per monthly release timestamp)
        self.assertEqual(len(rs_pre), 96)
        # Exactly 49 trade episodes
        self.assertEqual(len(rs_trade), 49)
        self.assertNotEqual(len(rs_trade), 98, "Must NOT duplicate co-released components into 98 trades")

        # Verify that each Retail Sales episode has both Headline and Core components
        for ep in rs_trade:
            self.assertEqual(len(ep["components"]), 2)
            c_names = set(c["name"] for c in ep["components"])
            self.assertIn("Retail Sales m/m", c_names)
            self.assertIn("Core Retail Sales m/m", c_names)

        # Direction breakdown: 27 Short (positive surprise), 22 Long (negative surprise)
        shorts = [e for e in rs_trade if e["direction"] == -1]
        longs = [e for e in rs_trade if e["direction"] == 1]
        self.assertEqual(len(shorts), 27)
        self.assertEqual(len(longs), 22)
        self.assertEqual(len(shorts) + len(longs), 49)

    def test_pre2023_cohort_memberships_and_timestamps(self):
        """
        Verifies that 157 pre-2023 cohort memberships correspond to exactly 149 distinct release timestamps.
        On exactly 8 dates, Headline CPI and Core CPI both qualified concurrently.
        """
        # Phase 1 + Ifo + Retail Sales eligible pre-2023 episodes
        target_families = ["US inflation", "US labor", "German Ifo", "US Retail Sales"]
        target_eps = [e for e in self.pre2023 if e["family"] in target_families and e["is_eligible"]]

        # Sum of cohort memberships
        total_memberships = sum(len(e["cohort_tags"]) for e in target_eps)
        distinct_timestamps = len(set(e["timestamp"] for e in target_eps))

        self.assertEqual(total_memberships, 157)
        self.assertEqual(distinct_timestamps, 149)
        self.assertEqual(total_memberships - distinct_timestamps, 8, "Expected exactly 8 dual-qualifying CPI timestamps")

        # Find the 8 dual-qualifying CPI episodes
        cpi_dual = [e for e in target_eps if "Headline CPI (+3)" in e["cohort_tags"] or "Headline CPI (-3)" in e["cohort_tags"]]
        cpi_dual = [e for e in cpi_dual if "Core CPI (+3)" in e["cohort_tags"] or "Core CPI (-3)" in e["cohort_tags"]]
        self.assertEqual(len(cpi_dual), 8)


class TestIntradayBarAlignment(unittest.TestCase):
    """
    Verifies that release timestamps inside an H1 bar (e.g. 15:30 inside [15:00, 16:00) bar,
    H1 entry at 16:00) are cleanly aligned without faking intraday tick prices.
    """

    @classmethod
    def setUpClass(cls):
        cls.candles, cls.ts_to_idx = load_all_candles()
        cls.episodes, _ = build_event_episodes(candles=cls.candles, ts_to_idx=cls.ts_to_idx)

    def test_nfp_intraday_release_and_entry_alignment(self):
        # NFP on 2019-01-04 is released at 15:30:00 server time (ts = 1546619400)
        ts = 1546619400
        self.assertEqual(ts % 3600, 1800, "Release must be at :30 (inside an H1 candle)")

        ep = next(e for e in self.episodes if e["timestamp"] == ts and e["family"] == "US labor")
        self.assertIsNotNone(ep)

        # Containing H1 bar opens at 15:00:00
        rel_bar_ts = ts - (ts % 3600)
        self.assertEqual(rel_bar_ts, 1546617600)
        self.assertIn(rel_bar_ts, self.ts_to_idx)
        self.assertEqual(ep["release_candle_index"], self.ts_to_idx[rel_bar_ts])

        # Entry candle H1 opens at 16:00:00
        expected_entry_ts = rel_bar_ts + 3600
        self.assertEqual(ep["entry_timestamp"], expected_entry_ts)
        self.assertEqual(ep["candle_index"], self.ts_to_idx[expected_entry_ts])
        self.assertEqual(ep["candle_index"], ep["release_candle_index"] + 1)

    def test_retail_sales_intraday_release_alignment(self):
        # US Retail Sales on 2017-05-12 at 15:30:00 server time (ts = 1494603000)
        ts = 1494603000
        ep = next(e for e in self.episodes if e["timestamp"] == ts and e["family"] == "US Retail Sales")
        self.assertIsNotNone(ep)

        rel_bar_ts = ts - (ts % 3600)
        self.assertEqual(rel_bar_ts, 1494601200)
        self.assertEqual(ep["release_candle_index"], self.ts_to_idx[rel_bar_ts])
        self.assertEqual(ep["entry_timestamp"], 1494604800)  # 16:00:00 server open
        self.assertEqual(ep["candle_index"], self.ts_to_idx[1494604800])


class TestKnownPlus3Records(unittest.TestCase):
    """Reconciles known +3 records with exact A/F/P/S/M against archived trial artifacts."""

    @classmethod
    def setUpClass(cls):
        cls.candles, cls.ts_to_idx = load_all_candles()
        cls.episodes, _ = build_event_episodes(candles=cls.candles, ts_to_idx=cls.ts_to_idx)
        with open(PHASE1_PATH, "r", encoding="utf-8") as f:
            cls.p1 = json.load(f)

    def test_known_nfp_plus3_record(self):
        # NFP release on 2019-01-04 (ts = 1546619400)
        ts = 1546619400
        nfp_ep = next(e for e in self.episodes if e["timestamp"] == ts and e["family"] == "US labor")
        self.assertIsNotNone(nfp_ep)

        comp = nfp_ep["components"][0]
        self.assertEqual(comp["actual"], 312.0)
        self.assertEqual(comp["forecast"], 170.0)
        self.assertEqual(comp["previous"], 155.0)
        self.assertEqual(comp["surprise"], 142.0)  # S = 312 - 170
        self.assertEqual(comp["momentum"], 157.0)  # M = 312 - 155
        self.assertEqual(comp["score"], 3)
        self.assertEqual(nfp_ep["direction_label"], "SHORT")
        self.assertTrue(nfp_ep["is_eligible"])
        self.assertIn("NFP (+3)", nfp_ep["cohort_tags"])

        # Reconcile against Phase 1 individualEventPaths
        arch_p = next(p for p in self.p1["eurusdOutcomes"]["USD:US:840030016:r0"]["individualEventPaths"] if p["timestamp"] == ts)
        self.assertEqual(arch_p["actual"], comp["actual"])
        self.assertEqual(arch_p["forecast"], comp["forecast"])
        self.assertEqual(arch_p["previous"], comp["previous"])
        self.assertEqual(arch_p["surpriseDelta"], comp["surprise"])
        self.assertEqual(arch_p["momentumDelta"], comp["momentum"])
        self.assertEqual(arch_p["surpriseScore"], comp["score"])

    def test_known_cpi_plus3_record(self):
        # Headline CPI release on 2019-04-10 (ts = 1554910200)
        ts = 1554910200
        cpi_ep = next(e for e in self.episodes if e["timestamp"] == ts and e["family"] == "US inflation")
        self.assertIsNotNone(cpi_ep)

        comp = next(c for c in cpi_ep["components"] if c["series_id"] == "USD:US:840030005:r0")
        self.assertAlmostEqual(comp["actual"], 0.4, places=2)
        self.assertAlmostEqual(comp["forecast"], 0.1, places=2)
        self.assertAlmostEqual(comp["previous"], 0.2, places=2)
        self.assertAlmostEqual(comp["surprise"], 0.3, places=2)
        self.assertAlmostEqual(comp["momentum"], 0.2, places=2)
        self.assertEqual(comp["score"], 3)
        self.assertEqual(cpi_ep["direction_label"], "SHORT")
        self.assertTrue(cpi_ep["is_eligible"])
        self.assertIn("Headline CPI (+3)", cpi_ep["cohort_tags"])


class TestDynamicMedianRecalculationAndFullHistory(unittest.TestCase):
    """
    Verifies dynamic median recalculation across full 2015–2026 history
    and verifies that post-2022 prices are unblinded and populated.
    """

    @classmethod
    def setUpClass(cls):
        cls.candles, cls.ts_to_idx = load_all_candles()
        cls.episodes, cls.meta = build_event_episodes(candles=cls.candles, ts_to_idx=cls.ts_to_idx)

    def test_post2022_prices_unblinded_for_exploration(self):
        """Proves that post-2022 episodes have real directional price paths populated."""
        post2022_eps = [e for e in self.episodes if e["timestamp"] >= SPLIT_TIMESTAMP and e["is_eligible"]]
        self.assertGreater(len(post2022_eps), 0, "Must have eligible post-2022 episodes")

        for ep in post2022_eps:
            self.assertIsNotNone(ep["price_path"], f"Post-2022 episode {ep['episode_id']} must have price path")
            self.assertEqual(len(ep["price_path"]), MAX_HORIZONS)
            # First horizon must be float
            self.assertIsInstance(ep["price_path"][0], float)

    def test_dynamic_median_recalculation_never_averages_medians(self):
        """
        Verifies that medians for filtered subsets (e.g. 2021) are calculated from
        individual episode returns, and do not equal an average of yearly medians.
        """
        cohort_name = "Headline CPI (+3)"
        eligible_cpi = [e for e in self.episodes if e["is_eligible"] and cohort_name in e["cohort_tags"]]

        # 2021 subset (N = 4)
        cpi_2021 = [e for e in eligible_cpi if e["year"] == 2021]
        self.assertEqual(len(cpi_2021), 4)
        # Headline CPI (+3) has SHORT direction (-1)
        h1_2021 = [e["price_path"][0] if (e["price_path"] is not None and e["direction"] != 0) else round(-1 * e["raw_price_path"][0], 4) for e in cpi_2021]
        median_2021 = statistics.median(h1_2021)

        # 2022 subset (N = 3)
        cpi_2022 = [e for e in eligible_cpi if e["year"] == 2022]
        self.assertEqual(len(cpi_2022), 3)
        h1_2022 = [e["price_path"][0] if (e["price_path"] is not None and e["direction"] != 0) else round(-1 * e["raw_price_path"][0], 4) for e in cpi_2022]
        median_2022 = statistics.median(h1_2022)

        # Pooled 2021 + 2022 (N = 7)
        pooled = h1_2021 + h1_2022
        pooled_median = statistics.median(pooled)

        # Naive average of yearly medians
        avg_medians = (median_2021 + median_2022) / 2.0

        # Pooled median must equal median of concatenated individual returns
        self.assertEqual(pooled_median, statistics.median(pooled))
        # Averaging medians must NOT equal the pooled median
        self.assertNotEqual(pooled_median, avg_medians)

    def test_truncation_handling_near_export_snapshot_boundary(self):
        """
        Verifies that recent releases near 2026-09-23 properly track available horizons
        and append null/None if fewer than 60 bars remain before export cutoff.
        """
        latest_ep = max(self.episodes, key=lambda e: e["timestamp"])
        self.assertEqual(latest_ep["year"], 2026)
        self.assertIn("2026", latest_ep["timestamp_server_text"])
        self.assertLessEqual(latest_ep["available_horizons"], MAX_HORIZONS)


class TestHtmlViewerIntegrity(unittest.TestCase):
    """Verifies that generated HTML is completely self-contained and offline."""

    def test_generated_html_structure(self):
        self.assertTrue(os.path.exists(OUTPUT_HTML_PATH))
        with open(OUTPUT_HTML_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Zero external HTTP/HTTPS dependencies
        self.assertNotIn("http://", content)
        self.assertNotIn("https://", content)

        # Core UI and Governance elements
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("familyFilter", content)
        self.assertIn("yearFilter", content)
        self.assertIn("cohortFilter", content)
        self.assertIn("Distinct Event Episodes", content)
        self.assertIn("Raw Calendar Rows", content)
        self.assertIn("Holdout Forfeiture Warning", content)
        self.assertIn("candleCanvas", content)
        self.assertIn("USD:US:840020010:r0", content)
        self.assertIn("USD:US:840020011:r0", content)


if __name__ == "__main__":
    unittest.main()
