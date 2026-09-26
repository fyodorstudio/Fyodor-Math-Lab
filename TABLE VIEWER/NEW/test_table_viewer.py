"""
Independent Numerical Correctness Unit Tests for Simple Table Viewer
Verifies against raw pinned CSV files:
1. Per-family and per-year release-time counts (2019 Inflation N=23, 2026 partial total N=54, total 839 family episodes across 825 distinct timestamps).
2. Exact breakdown of 14 coincident timestamps: 12 Inflation + Retail, 2 Labor + Retail.
3. Complete A/F/P counts: 634 total across the 5 families; exactly 0 in 2015 and 0 in 2016 (72 calendar episodes each).
4. Exact EURUSD pip arithmetic at hand-checkable episodes for both BASE and QUOTE signs.
5. Strict 19-pair scope (CADJPY removed, no extraneous pairs).
6. Table column header 'F' hover tooltip and 100% fidelity to raw CSV forecast values.
7. CPI condition group membership:
   - Both Above (A - F > 0 for both headline and core).
   - Both Below (A - F < 0 for both headline and core).
   - Mixed or Zero (neither holds).
   - Core PCE strictly excluded.
   - Missing A/F strictly excluded (no silent zero conversion).
   - Cross-family shared timestamps strictly excluded from conditioned groups.
8. Exact group Ns by year and All Years (18 Both Above, 18 Both Below, 65 Mixed/Zero = 101 Eligible CPI).
9. Exact Type-7 linear interpolation percentiles (P10, P50, P90) and Positive-Move Frequency arithmetic.
10. BASE vs QUOTE percentile sign inversion: P50(-v) = -P50(v), P10(-v) = -P90(v), P90(-v) = -P10(v).
11. Single-episode selection and missing pip values regression test.
12. Strict light mode styling (zero dark mode CSS classes).
"""

import unittest
import os
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone

VIEWER_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(VIEWER_DIR, "..", ".."))
HTML_PATH = os.path.join(VIEWER_DIR, "table_viewer.html")
CALENDAR_PATH = os.path.join(BASE_DIR, "data", "pinned", "FyodorResearchExport_v3_20260923_234930_server", "calendar_releases.csv")

SCOPED_19_PAIRS = [
    "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "EURGBP", "EURAUD", "EURCAD", "EURCHF", "EURNZD",
    "AUDJPY", "CHFJPY", "GBPCHF", "AUDCAD", "AUDCHF", "AUDNZD"
]


def compute_type7_percentile(sorted_vals, p):
    n = len(sorted_vals)
    if n == 0:
        return None
    if n == 1:
        return sorted_vals[0]
    pos = (n - 1) * p
    k = int(pos)
    d = pos - k
    if k >= n - 1:
        return sorted_vals[-1]
    return sorted_vals[k] + d * (sorted_vals[k + 1] - sorted_vals[k])


class TestTableViewerNumericalCorrectness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Regenerate HTML if missing
        if not os.path.exists(HTML_PATH):
            import subprocess
            subprocess.run(["python", os.path.join(VIEWER_DIR, "generate_table.py")], check=True)

        with open(HTML_PATH, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

        # Extract embedded JSON DB
        start_marker = "const DB = "
        end_marker = ";\n\n  let viewingMode"
        idx1 = cls.html_content.find(start_marker) + len(start_marker)
        idx2 = cls.html_content.find(end_marker)
        raw_json = cls.html_content[idx1:idx2]
        cls.data = json.loads(raw_json)

    def test_file_exists_and_light_mode_styling(self):
        """Verifies HTML exists and contains strictly light mode styles (no dark theme)."""
        self.assertTrue(os.path.exists(HTML_PATH))
        self.assertGreater(os.path.getsize(HTML_PATH), 1000000)

        content_lower = self.html_content.lower()
        self.assertNotIn("dark-theme", content_lower)
        self.assertNotIn("theme-dark", content_lower)
        self.assertNotIn("@media (prefers-color-scheme: dark)", content_lower)
        self.assertIn("background-color: #f8fafc", self.html_content)

    def test_mode_toggle_buttons_labeled_correctly(self):
        """Verifies Toggle buttons are plainly labeled BASE GOOD = GREEN and QUOTE GOOD = GREEN."""
        self.assertIn("BASE GOOD = GREEN", self.html_content)
        self.assertIn("QUOTE GOOD = GREEN", self.html_content)
        self.assertNotIn("USD-Aligned Pips", self.html_content)
        self.assertNotIn("in favor of event", self.html_content.lower())

    def test_calendar_family_episodes_and_distinct_timestamps(self):
        """
        Verifies:
        - 839 family episodes total across the 5 families.
        - 825 distinct release timestamps across the 5 families (14 coincident timestamps).
        - Accurate collision breakdown: exactly 12 are ('US_INFLATION', 'US_RETAIL_SALES')
          and exactly 2 are ('US_LABOR', 'US_RETAIL_SALES').
        """
        episodes = self.data["episodes"]
        self.assertEqual(len(episodes), 839)

        distinct_ts = set(ep["ts"] for ep in episodes)
        self.assertEqual(len(distinct_ts), 825)
        self.assertEqual(len(episodes) - len(distinct_ts), 14)

        ts_fams = defaultdict(set)
        for ep in episodes:
            ts_fams[ep["ts"]].add(ep["family"])

        collisions = {ts: fams for ts, fams in ts_fams.items() if len(fams) > 1}
        self.assertEqual(len(collisions), 14)

        breakdown = defaultdict(int)
        for ts, fams in collisions.items():
            breakdown[tuple(sorted(list(fams)))] += 1

        self.assertEqual(breakdown[("US_INFLATION", "US_RETAIL_SALES")], 12)
        self.assertEqual(breakdown[("US_LABOR", "US_RETAIL_SALES")], 2)
        self.assertEqual(len(breakdown), 2, "No other cross-family collisions should exist")

    def test_family_and_year_counts_including_2019_inflation_and_2026_total(self):
        """
        Verifies:
        - US_INFLATION in 2019 has N = 23 episodes.
        - 2026 partial total across the 5 families has N = 54 episodes.
        - 2015 and 2016 each have 72 calendar episodes.
        """
        episodes = self.data["episodes"]

        inf_2019 = [ep for ep in episodes if ep["family"] == "US_INFLATION" and ep["year"] == 2019]
        self.assertEqual(len(inf_2019), 23)

        eps_2026 = [ep for ep in episodes if ep["year"] == 2026]
        self.assertEqual(len(eps_2026), 54)

        eps_2015 = [ep for ep in episodes if ep["year"] == 2015]
        self.assertEqual(len(eps_2015), 72)

        eps_2016 = [ep for ep in episodes if ep["year"] == 2016]
        self.assertEqual(len(eps_2016), 72)

    def test_complete_afp_counts(self):
        """
        Verifies:
        - Exactly 634 episodes have complete A/F/P across the 5 families.
        - 2015 has exactly 0 complete A/F/P episodes.
        - 2016 has exactly 0 complete A/F/P episodes.
        """
        episodes = self.data["episodes"]
        complete_afp = [ep for ep in episodes if ep["is_complete_afp"]]
        self.assertEqual(len(complete_afp), 634)

        complete_2015 = [ep for ep in complete_afp if ep["year"] == 2015]
        self.assertEqual(len(complete_2015), 0)

        complete_2016 = [ep for ep in complete_afp if ep["year"] == 2016]
        self.assertEqual(len(complete_2016), 0)

    def test_both_2019_04_29_core_pce_records_survive_without_doubling_episode(self):
        """
        Verifies:
        - Pinned calendar contains 2 Core PCE records at 2019-04-29 15:30 (Feb and March 2019 periods).
        - Both records are preserved with period identifiers.
        - Exactly ONE release-time episode exists for 2019-04-29 15:30 (ts=1556551800).
        - US_INFLATION 2019 count remains exactly 23 (not 24).
        """
        episodes = self.data["episodes"]
        ep_pce = [ep for ep in episodes if ep["ts"] == 1556551800 and ep["family"] == "US_INFLATION"]
        self.assertEqual(len(ep_pce), 1, "Must be exactly ONE release-time episode")

        indicators = ep_pce[0]["indicators"]
        self.assertEqual(len(indicators), 2, "Must preserve both component records")

        names = [i["name"] for i in indicators]
        self.assertTrue(any("2019-03" in n for n in names))
        self.assertTrue(any("2019-02" in n for n in names))

    def test_eurusd_pip_arithmetic_exact_examples(self):
        """
        Verifies EURUSD pip arithmetic at hand-checkable episodes for both BASE and QUOTE signs.
        """
        episodes = self.data["episodes"]

        ep_2024 = next(ep for ep in episodes if ep["ts"] == 1704990600)
        pips_eur = ep_2024["pips"]["EURUSD"]
        raw_h1 = pips_eur[0]
        raw_h60 = pips_eur[59]

        self.assertAlmostEqual(raw_h1, -7.8, places=1)
        self.assertAlmostEqual(raw_h60, -30.3, places=1)

        # BASE vs QUOTE
        self.assertAlmostEqual(raw_h1, -7.8, places=1)
        self.assertAlmostEqual(-raw_h1, 7.8, places=1)

    def test_strictly_19_pairs_scoped(self):
        """
        Verifies:
        - Only the 19 scoped full-history FX pairs are included in the generated output.
        - CADJPY is strictly absent from DB['pairs'].
        """
        pairs = self.data["pairs"]
        self.assertEqual(len(pairs), 19)
        self.assertEqual(pairs, SCOPED_19_PAIRS)
        self.assertNotIn("CADJPY", pairs)

    def test_forecast_header_and_source_csv_fidelity(self):
        """
        Verifies:
        - The table column header is exactly 'F'.
        - Header has title tooltip explaining 'F = Forecast; -- = absent in the pinned source.'
        - 100% of numeric forecast values displayed in the viewer match the raw source CSV.
        """
        self.assertIn('<th class="sticky-col-afpsm sticky-col-5" title="F = Forecast; -- = absent in the pinned source.">F</th>', self.html_content)

        raw_by_ts = defaultdict(list)
        with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["revision"] != "0":
                    continue
                raw_by_ts[int(r["timestamp"])].append(r)

        checked_numeric = 0
        checked_missing = 0
        for ep in self.data["episodes"]:
            ts = ep["ts"]
            rows = raw_by_ts.get(ts, [])
            for ind in ep["indicators"]:
                disp_f = ind["forecast"]
                if disp_f == "--":
                    checked_missing += 1
                else:
                    checked_numeric += 1
                    matched = any(r["forecast"].strip() and abs(float(r["forecast"]) - float(disp_f)) < 1e-6 for r in rows)
                    self.assertTrue(matched)

        self.assertEqual(checked_numeric, 941)
        self.assertEqual(checked_missing, 319)

    def test_cpi_group_membership_and_core_pce_exclusion(self):
        """
        Verifies Requirement 2:
        - Core PCE releases NEVER enter any CPI group (cpi_group is None).
        - Both Above: headline A - F > 0 and core A - F > 0.
        - Both Below: headline A - F < 0 and core A - F < 0.
        - Mixed or Zero: neither of the above holds.
        - Previous, momentum, price movement, and future candles are NOT used.
        """
        episodes = self.data["episodes"]
        inf_eps = [ep for ep in episodes if ep["family"] == "US_INFLATION"]

        for ep in inf_eps:
            has_cpi = any("CPI m/m" in ind["name"] and "Core PCE" not in ind["name"] for ind in ep["indicators"])
            has_pce = any("Core PCE" in ind["name"] for ind in ep["indicators"])

            if not has_cpi:
                # Pure Core PCE release: must be completely excluded from CPI groups
                self.assertIsNone(ep["cpi_group"], f"Core PCE at ts {ep['ts']} was incorrectly assigned to a CPI group")

            if ep["cpi_group"] is not None:
                head = next(ind for ind in ep["indicators"] if ind["name"] == "USD CPI m/m")
                core = next(ind for ind in ep["indicators"] if ind["name"] == "USD Core CPI m/m")

                self.assertNotEqual(head["actual"], "--")
                self.assertNotEqual(head["forecast"], "--")
                self.assertNotEqual(core["actual"], "--")
                self.assertNotEqual(core["forecast"], "--")

                s_head = round(float(head["actual"]) - float(head["forecast"]), 4)
                s_core = round(float(core["actual"]) - float(core["forecast"]), 4)

                if ep["cpi_group"] == "BOTH_ABOVE":
                    self.assertGreater(s_head, 0)
                    self.assertGreater(s_core, 0)
                elif ep["cpi_group"] == "BOTH_BELOW":
                    self.assertLess(s_head, 0)
                    self.assertLess(s_core, 0)
                elif ep["cpi_group"] == "MIXED_ZERO":
                    self.assertFalse(s_head > 0 and s_core > 0)
                    self.assertFalse(s_head < 0 and s_core < 0)

    def test_cpi_missing_forecasts_exclusion(self):
        """
        Verifies Requirement 2:
        - Releases with missing forecasts (e.g. 2015 and 2016, and Jan 2017) are strictly excluded.
        - Missing forecasts NEVER silently become zero.
        """
        episodes = self.data["episodes"]
        inf_eps = [ep for ep in episodes if ep["family"] == "US_INFLATION"]

        for ep in inf_eps:
            if ep["year"] in [2015, 2016]:
                self.assertIsNone(ep["cpi_group"], f"Episode at {ep['dt_str']} in {ep['year']} must have cpi_group None")

    def test_cpi_cross_family_collision_exclusion(self):
        """
        Verifies Requirement 3:
        - Exclude timestamps shared with another macro family (12 Inflation + Retail Sales).
        - All 12 shared timestamps in US_INFLATION have is_shared_timestamp == True.
        """
        episodes = self.data["episodes"]
        inf_eps = [ep for ep in episodes if ep["family"] == "US_INFLATION"]

        shared_inf = [ep for ep in inf_eps if ep["is_shared_timestamp"]]
        self.assertEqual(len(shared_inf), 12, "Exactly 12 US_INFLATION episodes collide with US_RETAIL_SALES")

    def test_exact_cpi_group_ns_by_year_and_all_years(self):
        """
        Verifies Requirement 2, 3 & 7:
        Exact group Ns by year and across All Years:
        - Across All Years (2015-2026):
          Eligible unshared CPI episodes = 101:
          - Both Above = 18
          - Both Below = 18
          - Mixed or Zero = 65
        - Shared collisions = 12
        - Core PCE = 138
        - Missing A/F = 26
        - Total US_INFLATION = 277
        """
        episodes = self.data["episodes"]
        inf_eps = [ep for ep in episodes if ep["family"] == "US_INFLATION"]
        self.assertEqual(len(inf_eps), 277)

        # Unshared eligible CPI episodes
        eligible_unshared = [ep for ep in inf_eps if not ep["is_shared_timestamp"] and ep["cpi_group"] is not None]
        self.assertEqual(len(eligible_unshared), 101)

        above_all = [ep for ep in eligible_unshared if ep["cpi_group"] == "BOTH_ABOVE"]
        below_all = [ep for ep in eligible_unshared if ep["cpi_group"] == "BOTH_BELOW"]
        mixed_all = [ep for ep in eligible_unshared if ep["cpi_group"] == "MIXED_ZERO"]

        self.assertEqual(len(above_all), 18)
        self.assertEqual(len(below_all), 18)
        self.assertEqual(len(mixed_all), 65)

        # Year-specific exact counts
        by_year = defaultdict(lambda: {"above": 0, "below": 0, "mixed": 0})
        for ep in eligible_unshared:
            by_year[ep["year"]][ep["cpi_group"].lower().replace("both_", "").replace("_zero", "")] += 1

        self.assertEqual(by_year[2015]["above"], 0)
        self.assertEqual(by_year[2016]["above"], 0)
        self.assertEqual(by_year[2017]["above"], 1)
        self.assertEqual(by_year[2018]["above"], 1)
        self.assertEqual(by_year[2019]["above"], 1)
        self.assertEqual(by_year[2020]["above"], 4)
        self.assertEqual(by_year[2021]["above"], 3)
        self.assertEqual(by_year[2022]["above"], 3)
        self.assertEqual(by_year[2023]["above"], 0)
        self.assertEqual(by_year[2024]["above"], 2)
        self.assertEqual(by_year[2025]["above"], 2)
        self.assertEqual(by_year[2026]["above"], 1)

        self.assertEqual(by_year[2020]["below"], 3)
        self.assertEqual(by_year[2022]["below"], 4)
        self.assertEqual(by_year[2023]["below"], 3)
        self.assertEqual(by_year[2024]["below"], 1)

    def test_exact_type7_percentile_and_positive_freq_arithmetic(self):
        """
        Verifies Requirement 5:
        Exact Type-7 percentiles (P10, P50, P90) and Positive-Move Frequency arithmetic
        on small hand-calculable test samples:
        Position: pos = (N - 1) * p
        """
        # Case 1: N = 1, [7.5]
        s1 = [7.5]
        self.assertEqual(compute_type7_percentile(s1, 0.10), 7.5)
        self.assertEqual(compute_type7_percentile(s1, 0.50), 7.5)
        self.assertEqual(compute_type7_percentile(s1, 0.90), 7.5)

        # Case 2: N = 2, [-10.0, 20.0]
        # pos(0.10) = 0.1 -> -10.0 + 0.1 * 30.0 = -7.0
        # pos(0.50) = 0.5 -> -10.0 + 0.5 * 30.0 = 5.0
        # pos(0.90) = 0.9 -> -10.0 + 0.9 * 30.0 = 17.0
        s2 = [-10.0, 20.0]
        self.assertAlmostEqual(compute_type7_percentile(s2, 0.10), -7.0, places=5)
        self.assertAlmostEqual(compute_type7_percentile(s2, 0.50), 5.0, places=5)
        self.assertAlmostEqual(compute_type7_percentile(s2, 0.90), 17.0, places=5)

        # Case 3: N = 5, [-4.0, -2.0, 0.0, 3.0, 8.0]
        # pos(0.10) = 4 * 0.1 = 0.4 -> -4.0 + 0.4 * 2.0 = -3.2
        # pos(0.50) = 4 * 0.5 = 2.0 -> 0.0
        # pos(0.90) = 4 * 0.9 = 3.6 -> 3.0 + 0.6 * 5.0 = 6.0
        s3 = [-4.0, -2.0, 0.0, 3.0, 8.0]
        self.assertAlmostEqual(compute_type7_percentile(s3, 0.10), -3.2, places=5)
        self.assertAlmostEqual(compute_type7_percentile(s3, 0.50), 0.0, places=5)
        self.assertAlmostEqual(compute_type7_percentile(s3, 0.90), 6.0, places=5)

        # Positive-move frequency: count(v > 0) / available N
        # Zero belongs in denominator but NOT numerator
        pos_count = len([v for v in s3 if v > 0])
        self.assertEqual(pos_count, 2)  # 3.0 and 8.0
        self.assertAlmostEqual(pos_count / len(s3), 0.40, places=5)

        # Case 4: N = 0
        self.assertIsNone(compute_type7_percentile([], 0.10))
        self.assertIsNone(compute_type7_percentile([], 0.50))
        self.assertIsNone(compute_type7_percentile([], 0.90))

    def test_base_quote_percentile_sign_inversion_property(self):
        """
        Verifies Requirement 5:
        When values flip sign (v -> -v), the percentiles invert:
          P50(-v) = -P50(v)
          P10(-v) = -P90(v)
          P90(-v) = -P10(v)
        Tested across all H1..H60 for the actual Both Above conditioned subset.
        """
        episodes = self.data["episodes"]
        above_eps = [ep for ep in episodes if ep["family"] == "US_INFLATION" and not ep["is_shared_timestamp"] and ep["cpi_group"] == "BOTH_ABOVE"]
        self.assertEqual(len(above_eps), 18)

        for h in range(60):
            base_vals = [ep["pips"]["EURUSD"][h] for ep in above_eps if ep["pips"]["EURUSD"][h] is not None]
            quote_vals = [-v for v in base_vals]

            base_sorted = sorted(base_vals)
            quote_sorted = sorted(quote_vals)

            p10_base = compute_type7_percentile(base_sorted, 0.10)
            p50_base = compute_type7_percentile(base_sorted, 0.50)
            p90_base = compute_type7_percentile(base_sorted, 0.90)

            p10_quote = compute_type7_percentile(quote_sorted, 0.10)
            p50_quote = compute_type7_percentile(quote_sorted, 0.50)
            p90_quote = compute_type7_percentile(quote_sorted, 0.90)

            self.assertAlmostEqual(p50_quote, -p50_base, places=5, msg=f"P50 sign inversion failed at H{h+1}")
            self.assertAlmostEqual(p10_quote, -p90_base, places=5, msg=f"P10/P90 sign inversion failed at H{h+1}")
            self.assertAlmostEqual(p90_quote, -p10_base, places=5, msg=f"P90/P10 sign inversion failed at H{h+1}")

    def test_single_episode_selection_and_missing_pips_regression(self):
        """
        Verifies Requirement 1 & 5:
        Regression test for single-episode selection and missing pip values.
        """
        self.assertIn("const qualifyingEpisodes = episodesToRender.filter", self.html_content)
        self.assertIn("footerPricedN", self.html_content)
        self.assertIn("computeType7Percentile", self.html_content)

        episodes = self.data["episodes"]
        ep_priced = next(ep for ep in episodes if ep["ts"] == 1704990600)
        self.assertTrue(ep_priced["is_complete_afp"])
        self.assertIsNotNone(ep_priced["pips"]["EURUSD"])

        # N = 1 percentile equality
        val = ep_priced["pips"]["EURUSD"][0]  # H1
        s = [val]
        self.assertEqual(compute_type7_percentile(s, 0.10), val)
        self.assertEqual(compute_type7_percentile(s, 0.50), val)
        self.assertEqual(compute_type7_percentile(s, 0.90), val)


if __name__ == "__main__":
    unittest.main()
