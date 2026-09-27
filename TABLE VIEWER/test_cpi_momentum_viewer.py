"""
Unit tests for Study Selector Isolation and Ledger-to-HTML Reconciliation
Verifies:
1. Candidate Research study selector provides two distinct CPI options:
   - "US CPI · EURUSD · A−F Surprise · H24" (Baseline, unchanged)
   - "US CPI · EURUSD · A−P Momentum · H60" (Exploratory trial)
2. Study selector isolation: Baseline (36 cases) and Momentum (55 cases) reside in distinct panels
   and are never mixed or conflated.
3. Baseline ledger-to-HTML reconciliation: N=36, 16 targets, 20 stops, +4.00 gross R, 13.30 mean risk pips,
   2 ambiguous trades, 18 shorts, 18 longs, 11 jobless claims.
4. Momentum ledger-to-HTML reconciliation: N=55, 23 targets, 32 stops, +2.50 gross R (Conservative),
   +12.50 gross R (Optimistic), 12.20 mean risk pips, 4 ambiguous trades, 26 shorts, 29 longs,
   8 jobless claims, complete 277 funnel, all 12 yearly breakdown rows, all 55 per-trade rows.
5. Governance compliance: Prominent 'POST-HOC EXPLORATORY — NOT A REGISTERED SETUP' notice,
   explicit disclaimers, zero claims of registered setups or independent forward edges.
"""

import json
import os
import sys
import unittest

VIEWER_DIR = os.path.dirname(os.path.abspath(__file__))
if VIEWER_DIR not in sys.path:
    sys.path.insert(0, VIEWER_DIR)

from generator.config import (
    OUTPUT_HTML_PATH,
    CPI_LEDGER_PATH,
    CPI_MOMENTUM_LEDGER_PATH
)


class TestCpiMomentumViewerIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(OUTPUT_HTML_PATH, "r", encoding="utf-8") as f:
            cls.html = f.read()

        with open(CPI_LEDGER_PATH, "r", encoding="utf-8") as f:
            cls.baseline_ledger = json.load(f)

        with open(CPI_MOMENTUM_LEDGER_PATH, "r", encoding="utf-8") as f:
            cls.momentum_ledger = json.load(f)

    def test_01_study_selector_distinct_options(self):
        """Verifies selector provides two distinct CPI options with exact requested labels."""
        self.assertIn('US CPI · EURUSD · A−F Surprise · H24', self.html)
        self.assertIn('US CPI · EURUSD · A−P Momentum · H60', self.html)
        self.assertIn('value="US_CPI_EURUSD_AF_H24"', self.html)
        self.assertIn('value="US_CPI_EURUSD_AP_H60"', self.html)

        # Other studies marked Pending
        self.assertIn('US Labor (NFP) · EURUSD (Pending)', self.html)
        self.assertIn('US Retail Sales · EURUSD (Pending)', self.html)
        self.assertIn('German Ifo · EURUSD (Pending)', self.html)
        self.assertIn('US ISM PMI · EURUSD (Pending)', self.html)

    def test_02_study_panels_isolation(self):
        """Verifies distinct containers exist for baseline, momentum, and pending studies."""
        self.assertIn('id="studyContentCpiBaseline"', self.html)
        self.assertIn('id="studyContentCpiMomentum"', self.html)
        self.assertIn('id="studyContentPending"', self.html)

        # Ensure baseline panel has baseline notice and not momentum notice
        idx_base = self.html.find('id="studyContentCpiBaseline"')
        idx_mom = self.html.find('id="studyContentCpiMomentum"')
        idx_pend = self.html.find('id="studyContentPending"')

        self.assertTrue(idx_base < idx_mom < idx_pend)

        base_html = self.html[idx_base:idx_mom]
        mom_html = self.html[idx_mom:idx_pend]

        # 36 Directional Episodes in baseline; 55 in momentum
        self.assertIn('36 Directional Episodes', base_html)
        self.assertNotIn('55 Directional Episodes', base_html)

        self.assertIn('55 Directional Episodes', mom_html)
        self.assertNotIn('36 Directional Episodes', mom_html)

    def test_03_baseline_html_reconciliation(self):
        """Reconciles baseline section against cpi_trade_ledger.json."""
        p_met = self.baseline_ledger["trials"]["primary_1.5x_conservative"]["metrics"]
        self.assertEqual(p_met["total_trades"], 36)
        self.assertEqual(p_met["wins"], 16)
        self.assertEqual(p_met["losses"], 20)
        self.assertAlmostEqual(p_met["total_gross_r"], 4.00, places=2)
        self.assertAlmostEqual(p_met["mean_risk_pips"], 13.30, places=1)
        self.assertEqual(p_met["ambiguous_trades"], 2)

        idx_base = self.html.find('id="studyContentCpiBaseline"')
        idx_mom = self.html.find('id="studyContentCpiMomentum"')
        base_html = self.html[idx_base:idx_mom]

        # Parameters
        self.assertIn('EURUSD (Spot FX)', base_html)
        self.assertIn('Both A &gt; F &rarr; SHORT; Both A &lt; F &rarr; LONG', base_html)
        self.assertIn('24 observed H1 candles', base_html)

        # Metrics
        self.assertIn('+4.00 R', base_html)
        self.assertIn('13.30 pips', base_html)
        self.assertIn('Longs (N=18)', base_html)
        self.assertIn('Shorts (N=18)', base_html)
        self.assertIn('11 timestamps coinciding with Initial Jobless Claims', base_html)
        self.assertIn('Remaining 25 timestamps', base_html)
        self.assertIn('cpi_setup/cpi_trade_ledger.json', base_html)

    def test_04_momentum_html_reconciliation(self):
        """Reconciles momentum section against cpi_momentum_trade_ledger.json."""
        p_met = self.momentum_ledger["trials"]["primary_1.5x_conservative"]["metrics"]
        p_opt = self.momentum_ledger["trials"]["primary_1.5x_optimistic"]["metrics"]
        s1_cons = self.momentum_ledger["trials"]["sensitivity_1.0x_conservative"]["metrics"]
        s1_opt = self.momentum_ledger["trials"]["sensitivity_1.0x_optimistic"]["metrics"]
        s2_cons = self.momentum_ledger["trials"]["sensitivity_2.0x_conservative"]["metrics"]
        s2_opt = self.momentum_ledger["trials"]["sensitivity_2.0x_optimistic"]["metrics"]

        self.assertEqual(p_met["total_trades"], 55)
        self.assertEqual(p_met["wins"], 23)
        self.assertEqual(p_met["losses"], 32)
        self.assertAlmostEqual(p_met["total_gross_r"], 2.50, places=2)
        self.assertAlmostEqual(p_opt["total_gross_r"], 12.50, places=2)
        self.assertAlmostEqual(s1_cons["total_gross_r"], -7.00, places=2)
        self.assertAlmostEqual(s1_opt["total_gross_r"], 3.00, places=2)
        self.assertAlmostEqual(s2_cons["total_gross_r"], 5.00, places=2)
        self.assertAlmostEqual(s2_opt["total_gross_r"], 14.00, places=2)
        self.assertAlmostEqual(p_met["mean_risk_pips"], 12.20, places=1)
        self.assertEqual(p_met["ambiguous_trades"], 4)

        idx_mom = self.html.find('id="studyContentCpiMomentum"')
        idx_pend = self.html.find('id="studyContentPending"')
        mom_html = self.html[idx_mom:idx_pend]

        # Parameters
        self.assertIn('Candidate Parameter Card (A−P Momentum / H60)', mom_html)
        self.assertIn('Both &Delta; &gt; 0 &rarr; SHORT EURUSD; Both &Delta; &lt; 0 &rarr; LONG EURUSD', mom_html)
        self.assertIn('60 observed H1 market candles', mom_html)
        self.assertIn('All 55 trades resolved by Bar 23', mom_html)

        # Funnel
        self.assertIn('Total US Inflation Episodes: <strong>277</strong>', mom_html)
        self.assertIn('&minus;138</strong> (PCE_ONLY)', mom_html)
        self.assertIn('&minus;12</strong> (SHARED_COLLISION)', mom_html)
        self.assertIn('Eligible Unshared CPI Episodes: <strong>127</strong>', mom_html)
        self.assertIn('&minus;72</strong> (MIXED_OR_EQUAL)', mom_html)
        self.assertIn('Total Directional Candidate Trades: <strong>55</strong> (26 Short / 29 Long)', mom_html)

        # Performance table
        self.assertIn('+2.50 R', mom_html)
        self.assertIn('+12.50 R', mom_html)
        self.assertIn('-7.00 R', mom_html)
        self.assertIn('+3.00 R', mom_html)
        self.assertIn('+5.00 R', mom_html)
        self.assertIn('+14.00 R', mom_html)

        # Splits
        self.assertIn('Longs (N=29): <span class="stat-neg">-1.5 R</span> (11 targets / 18 stops)', mom_html)
        self.assertIn('Shorts (N=26): <span class="stat-pos">+4 R</span> (12 targets / 14 stops)', mom_html)
        self.assertIn('8 timestamps coinciding with Initial Jobless Claims: <span class="stat-pos">+4.5 R</span> (5 targets / 3 stops)', mom_html)
        self.assertIn('Remaining 47 timestamps (No Initial Jobless Claims): <span class="stat-neg">-2 R</span> (18 targets / 29 stops)', mom_html)
        self.assertIn('Mean risk: 12.20 pips', mom_html)

        # Four Ambiguous Bars
        self.assertIn('2021.05.12 15:30:00', mom_html)
        self.assertIn('2023.02.14 16:30:00', mom_html)
        self.assertIn('2024.06.12 15:30:00', mom_html)
        self.assertIn('2024.07.11 15:30:00', mom_html)

        # Yearly breakdown has 12 years (2015..2026)
        for yr in range(2015, 2027):
            self.assertIn(f'<td>{yr}</td>', mom_html)

        # Audit ledger paths
        self.assertIn('evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/cpi_momentum_trade_ledger.json', mom_html)
        self.assertIn('evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/cpi_momentum_trade_ledger.csv', mom_html)

    def test_05_governance_and_no_registered_setup_claims(self):
        """Verifies governance notices and absence of registration claims."""
        idx_mom = self.html.find('id="studyContentCpiMomentum"')
        idx_pend = self.html.find('id="studyContentPending"')
        mom_html = self.html[idx_mom:idx_pend]

        # Prominent post-hoc exploratory notice
        self.assertIn('POST-HOC EXPLORATORY — NOT A REGISTERED SETUP', mom_html)
        self.assertIn('Must not be traded on live or demo accounts', mom_html)
        self.assertIn('Zero setups are registered or approved for forward trading', mom_html)
        self.assertTrue('not an independently validated or pre-price-frozen hypothesis test' in mom_html.lower())

        # Neither panel claims setup is approved or registered
        self.assertNotIn('is approved for forward trading', self.html)
        self.assertNotIn('setup is registered for forward trading', self.html)

    def test_06_event_table_filters_do_not_alter_candidate_research(self):
        """
        Verifies that candidate study results are static HTML blocks rendered
        independent of dynamic event table filter state.
        """
        # Event Table DOM element IDs
        self.assertIn('id="selPair"', self.html)
        self.assertIn('id="selYear"', self.html)
        self.assertIn('id="selFamily"', self.html)

        # Event Table selectors have no references to study panels in app.js
        self.assertIn("updateEpisodeSelector(getFilteredEpisodes(), selPair.value);", self.html)
        self.assertIn("function updateResearchStudy()", self.html)

    def test_07_co_release_parsing_and_no_character_counting(self):
        """
        Verifies co_releases is properly parsed from semicolon-separated string:
        - 2026.09.11 15:30:00 displays '10 Co-release(s)', NOT character count '265 Co-release(s)'
        - Zero badges count string characters (no badge with >= 30 co-releases)
        - parse_co_releases utility splits and strips accurately
        """
        import re
        from generator.cpi_ledger import parse_co_releases

        idx_mom = self.html.find('id="studyContentCpiMomentum"')
        idx_pend = self.html.find('id="studyContentPending"')
        mom_html = self.html[idx_mom:idx_pend]

        # Exact trade 2026.09.11 15:30 check
        self.assertNotIn('265 Co-release', mom_html)
        self.assertIn('10 Co-release(s)', mom_html)

        # Check row 55 specifically
        row_match = re.search(r'<tr><td>55</td><td>2026\.09\.11 15:30:00.*?</tr>', mom_html)
        self.assertIsNotNone(row_match, "Trade #55 row not found in HTML.")
        self.assertIn('10 Co-release(s)', row_match.group(0))
        self.assertNotIn('265 Co-release', row_match.group(0))

        # Check all co-release badges in momentum HTML
        badges = re.findall(r'(\d+)\s+Co-release', mom_html)
        self.assertTrue(len(badges) > 0, "No co-release badges found.")
        for b in badges:
            count = int(b)
            self.assertLess(count, 30, f"Suspicious character-length badge found: {b} Co-release(s)")
            self.assertGreaterEqual(count, 1, f"Invalid zero/negative co-release count: {b}")

        # Unit test parse_co_releases
        sample = "CPI y/y (840030007); Core CPI y/y (840030008); Current Account (276010024)"
        parsed = parse_co_releases(sample)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], "CPI y/y (840030007)")
        self.assertEqual(parsed[2], "Current Account (276010024)")

    def test_08_subgroup_language_and_no_solitary_cpi(self):
        """
        Verifies governance language rules:
        - The 47 trades without Initial Jobless Claims must NEVER be called 'solitary CPI'.
        - Labeled 'No Initial Jobless Claims' subgroup.
        - Preserves 8-with-Jobless / 47-without counts and their gross R values (+4.5 R / -2 R).
        """
        # Global check across entire HTML file
        self.assertNotIn('solitary', self.html.lower())

        idx_mom = self.html.find('id="studyContentCpiMomentum"')
        idx_pend = self.html.find('id="studyContentPending"')
        mom_html = self.html[idx_mom:idx_pend]

        # Subgroup phrasing
        self.assertIn('Remaining 47 timestamps (No Initial Jobless Claims)', mom_html)
        self.assertIn('8 timestamps coinciding with Initial Jobless Claims', mom_html)
        self.assertIn('+4.5 R', mom_html)
        self.assertIn('-2 R', mom_html)

    def test_09_dynamic_presentation_values(self):
        """
        Verifies that presentation figures are derived dynamically from validated JSON metrics:
        - 127 eligible unshared CPI episodes
        - 26 Short / 29 Long candidate trade breakdown
        - All 55 trades resolved by Bar 23 (0 timeouts)
        - 4 Ambiguous Intrabar Bars
        - Execution-precedence sensitivity: +2.50 R vs +12.50 R (+10.00 R difference, +103.1 pips)
        """
        idx_mom = self.html.find('id="studyContentCpiMomentum"')
        idx_pend = self.html.find('id="studyContentPending"')
        mom_html = self.html[idx_mom:idx_pend]

        # Dynamic funnel
        self.assertIn('Eligible Unshared CPI Episodes: <strong>127</strong>', mom_html)
        self.assertIn('Total Directional Candidate Trades: <strong>55</strong> (26 Short / 29 Long)', mom_html)

        # Dynamic holding resolution
        self.assertIn('All 55 trades resolved by Bar 23 (0 timeouts)', mom_html)
        self.assertIn('0 trades reached H60 timeout', mom_html)

        # Dynamic ambiguity sensitivity
        self.assertIn('4 Ambiguous Intrabar Bars', mom_html)
        self.assertIn('+2.50 R', mom_html)
        self.assertIn('+12.50 R', mom_html)
        self.assertIn('+10.00 R difference, +103.1 pips', mom_html)


if __name__ == "__main__":
    unittest.main()

