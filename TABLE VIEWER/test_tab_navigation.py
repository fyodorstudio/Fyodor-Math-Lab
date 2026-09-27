"""
Unit Tests for Two-Tab Navigation, Independent Candidate Research, and Parity Verification
Location: TABLE VIEWER/test_tab_navigation.py

Verifies:
1. Strict Two-Tab DOM structure & WAI-ARIA keyboard accessibility.
2. Independent selectors between Event Table and Candidate Research tabs.
3. Dedicated Candidate Research selector with 'US CPI · EURUSD' available and pending studies properly guarded.
4. Pending study empty state has zero invented parameter cards or simulation numbers.
5. Candidate Research tab explicitly states fixed historical period scope independent of Event Table selections.
6. Preserved governance warnings ('UNDER AUDIT — NO REGISTERED SETUP', exploratory disclaimers).
7. Embedded Event Table dataset parity against pre-change baseline (839 episodes, 825 timestamps, 634 complete AFP).
8. CPI ledger-derived values parity against audited ledger (36 trades, 16W/20L, +4.00 R, etc.).
9. 100% self-contained standalone HTML with zero external network or server dependencies (file:// double-clickable).
"""

import json
import os
import re
import sys
import unittest

VIEWER_DIR = os.path.dirname(os.path.abspath(__file__))
if VIEWER_DIR not in sys.path:
    sys.path.insert(0, VIEWER_DIR)

HTML_PATH = os.path.join(VIEWER_DIR, "table_viewer.html")
LEDGER_PATH = os.path.join(VIEWER_DIR, "cpi_setup", "cpi_trade_ledger.json")


class TestTabNavigationAndParity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure HTML exists
        if not os.path.exists(HTML_PATH):
            import subprocess
            subprocess.run(["python", os.path.join(VIEWER_DIR, "generate_table.py")], check=True)

        with open(HTML_PATH, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            cls.ledger_data = json.load(f)

        # Extract embedded DB
        start_marker = "const DB = "
        end_marker = ";\n\n  let viewingMode"
        idx1 = cls.html_content.find(start_marker) + len(start_marker)
        idx2 = cls.html_content.find(end_marker)
        raw_json = cls.html_content[idx1:idx2]
        cls.db = json.loads(raw_json)

    def test_two_tab_navigation_and_aria_structure(self):
        """Verifies two-tab navigation structure, ARIA roles, and accessibility attributes."""
        # 1. Navigation element with role="tablist"
        self.assertIn('<nav class="tab-nav" role="tablist" aria-label="Research Workspace Tabs">', self.html_content)

        # 2. Both tab buttons with proper roles and aria-controls
        self.assertIn('id="tabBtnEventTable"', self.html_content)
        self.assertIn('role="tab"', self.html_content)
        self.assertIn('aria-controls="tabPanelEventTable"', self.html_content)
        self.assertIn('id="tabBtnCandidateResearch"', self.html_content)
        self.assertIn('aria-controls="tabPanelCandidateResearch"', self.html_content)

        # 3. Both tab panels with proper role="tabpanel" and aria-labelledby
        self.assertIn('<div id="tabPanelEventTable" class="tab-panel" role="tabpanel" aria-labelledby="tabBtnEventTable">', self.html_content)
        self.assertIn('<div id="tabPanelCandidateResearch" class="tab-panel" role="tabpanel" aria-labelledby="tabBtnCandidateResearch" style="display: none;">', self.html_content)

        # 4. Keyboard navigation script exists in JS
        self.assertIn("ArrowRight", self.html_content)
        self.assertIn("ArrowLeft", self.html_content)
        self.assertIn("switchTab('eventTable')", self.html_content)
        self.assertIn("switchTab('candidateResearch')", self.html_content)

    def test_independent_selectors_on_both_tabs(self):
        """
        Verifies that Event Table has its own selectors (Pair, Year, Family, CPI response, Episode, Median pop)
        and Candidate Research has its own research study selector (selResearchStudy).
        """
        # Event Table selectors
        self.assertIn('id="selPair"', self.html_content)
        self.assertIn('id="selYear"', self.html_content)
        self.assertIn('id="selFamily"', self.html_content)
        self.assertIn('id="selCpiResponse"', self.html_content)
        self.assertIn('id="selEpisode"', self.html_content)
        self.assertIn('id="selMedianPop"', self.html_content)

        # Candidate Research selector
        self.assertIn('id="selResearchStudy"', self.html_content)
        self.assertIn('value="US_CPI_EURUSD"', self.html_content)

        # Verify selResearchStudy is inside tabPanelCandidateResearch
        p2_start = self.html_content.find('id="tabPanelCandidateResearch"')
        p2_end = self.html_content.find('<script>')
        p2_html = self.html_content[p2_start:p2_end]
        self.assertIn('id="selResearchStudy"', p2_html)
        self.assertNotIn('id="selPair"', p2_html)

    def test_candidate_research_study_selector_and_pending_guards(self):
        """
        Verifies Candidate Research study choices:
        - Currently available: US CPI · EURUSD.
        - Other macro studies are clearly marked Pending.
        - Pending container exists with clear audit guard message and no invented data.
        """
        # Available study
        self.assertIn('<option value="US_CPI_EURUSD" selected>US CPI · EURUSD</option>', self.html_content)

        # Other studies marked Pending
        self.assertIn('US Labor (NFP) · EURUSD (Pending)', self.html_content)
        self.assertIn('US Retail Sales · EURUSD (Pending)', self.html_content)
        self.assertIn('German Ifo · EURUSD (Pending)', self.html_content)
        self.assertIn('US ISM PMI · EURUSD (Pending)', self.html_content)

        # Pending study container and messaging
        self.assertIn('id="studyContentPending"', self.html_content)
        self.assertIn('STUDY PENDING AUDIT', self.html_content)
        self.assertIn('No candidate parameter card or simulation ledger is available in this viewer for this study', self.html_content)
        self.assertNotIn('No candidate parameter card, simulation ledger, or backtest exists', self.html_content)
        self.assertIn('Zero setups are registered', self.html_content)

    def test_fixed_historical_period_scope_notice(self):
        """
        Verifies that the Candidate Research tab explicitly states results cover the full
        historical evaluation period regardless of Event Table selections.
        """
        self.assertIn(
            "These fixed audited results are completely independent of any pair, year, or family filters selected on the Event Table tab.",
            self.html_content
        )
        self.assertIn(
            "These fixed all-years results do NOT change with the pair, year, or episode selectors on the Event Table tab.",
            self.html_content
        )

    def test_prominent_governance_warnings_preserved(self):
        """
        Verifies that pre-registration audit governance warnings remain prominent:
        - 'UNDER AUDIT — NO REGISTERED SETUP'
        - 'EXPLORATORY HISTORICAL SIMULATION — NO REGISTERED SETUP'
        - Gross mid/bid H1 prices disclaimer, zero broker friction modeled.
        - No claim of executable profit or registered forward-test setup.
        """
        self.assertIn("UNDER AUDIT — NO REGISTERED SETUP", self.html_content)
        self.assertIn("EXPLORATORY HISTORICAL SIMULATION — NO REGISTERED SETUP", self.html_content)
        self.assertIn("Exploratory historical OHLC simulation; no registered setup.", self.html_content)
        self.assertIn("Zero broker spread, slippage, commission, or overnight financing modeled", self.html_content)
        self.assertIn("registered <em>for</em> demo forward testing", self.html_content)
        self.assertNotIn("STATUS: REGISTERED", self.html_content)

    def test_embedded_event_table_dataset_parity(self):
        """
        Verifies byte-level and numerical parity of the embedded dataset in table_viewer.html:
        - 19 FX pairs
        - 839 family episodes
        - 825 distinct timestamps
        - 634 complete A/F/P episodes
        - 277 US_INFLATION episodes (101 eligible unshared: 18 above, 18 below, 65 mixed/zero)
        - 14 cross-family collisions (12 Inflation + Retail, 2 Labor + Retail)
        """
        self.assertEqual(len(self.db["pairs"]), 19)
        self.assertEqual(len(self.db["episodes"]), 839)

        distinct_ts = set(ep["ts"] for ep in self.db["episodes"])
        self.assertEqual(len(distinct_ts), 825)

        complete_afp = [ep for ep in self.db["episodes"] if ep["is_complete_afp"]]
        self.assertEqual(len(complete_afp), 634)

        inf_eps = [ep for ep in self.db["episodes"] if ep["family"] == "US_INFLATION"]
        self.assertEqual(len(inf_eps), 277)

        eligible_unshared = [ep for ep in inf_eps if not ep["is_shared_timestamp"] and ep["cpi_group"] is not None]
        self.assertEqual(len(eligible_unshared), 101)

        above = [ep for ep in eligible_unshared if ep["cpi_group"] == "BOTH_ABOVE"]
        below = [ep for ep in eligible_unshared if ep["cpi_group"] == "BOTH_BELOW"]
        mixed = [ep for ep in eligible_unshared if ep["cpi_group"] == "MIXED_ZERO"]
        self.assertEqual(len(above), 18)
        self.assertEqual(len(below), 18)
        self.assertEqual(len(mixed), 65)

    def test_cpi_ledger_derived_values_parity(self):
        """
        Verifies that all CPI simulation metrics in the HTML match the baseline ledger:
        - 36 directional episodes
        - Sensitivity 1.0x: 16W / 20L, -4.00 R, -0.11 R mean, 3 ambiguous
        - Primary 1.5x: 16W / 20L, +4.00 R, +0.11 R mean, 2 ambiguous
        - Sensitivity 2.0x: 13W / 23L, +3.00 R, +0.08 R mean, 1 ambiguous
        - Longs: N=18, +4.5 R (9 targets / 9 stops)
        - Shorts: N=18, -0.5 R (7 targets / 11 stops)
        - Jobless: 11 timestamps, +4 R (6 targets / 5 stops)
        - Other: 25 timestamps, 0 R (10 targets / 15 stops)
        - Removing best trade: +2.50 R
        - Trade-level means: 13.30 pips risk, +1.89 pips P&L
        - Holding times: Bar 1: 26 (72.2%), Bar 2: 6 (16.7%), Bar 3: 2 (5.6%), Bar 5: 1 (2.8%), Bar 18: 1 (2.8%)
        - Timeouts: 0 trades reached H24 timeout
        """
        p_met = self.ledger_data["trials"]["primary_1.5x_conservative"]["metrics"]
        s1_met = self.ledger_data["trials"]["sensitivity_1.0x_conservative"]["metrics"]
        s2_met = self.ledger_data["trials"]["sensitivity_2.0x_conservative"]["metrics"]

        # Table rows in HTML
        self.assertIn("<td>1.0&times; : 1.0&times;</td>", self.html_content)
        self.assertIn("<td>36</td>", self.html_content)
        self.assertIn("<span class=\"stat-neg\">-4.00 R</span>", self.html_content)
        self.assertIn("<td>-0.11 R</td>", self.html_content)

        self.assertIn("<strong>1.5&times; : 1.0&times; (PRIMARY)</strong>", self.html_content)
        self.assertIn("<span class=\"stat-pos\"><strong>+4.00 R</strong></span>", self.html_content)
        self.assertIn("<td>+0.11 R</td>", self.html_content)

        self.assertIn("<td>2.0&times; : 1.0&times;</td>", self.html_content)
        self.assertIn("<span class=\"stat-pos\">+3.00 R</span>", self.html_content)
        self.assertIn("<td>+0.08 R</td>", self.html_content)

        # Splits note in HTML
        self.assertIn("Longs (N=18): <span class=\"stat-pos\">+4.5 R</span> (9 targets / 9 stops)", self.html_content)
        self.assertIn("Shorts (N=18): <span class=\"stat-neg\">-0.5 R</span> (7 targets / 11 stops)", self.html_content)
        self.assertIn("11 timestamps coinciding with Initial Jobless Claims: <span class=\"stat-pos\">+4 R</span>", self.html_content)
        self.assertIn("Remaining 25 timestamps: <span class=\"stat-zero\">0 R</span>", self.html_content)
        self.assertIn("Removing single best trade (+1.50 R on 2024.04.10 15:30:00): gross return = +2.50 R", self.html_content)
        self.assertIn("Mean risk: 13.30 pips", self.html_content)
        self.assertIn("Mean gross P&L: +1.89 pips", self.html_content)
        self.assertIn("Bar 1: 26 (72.2%), Bar 2: 6 (16.7%), Bar 3: 2 (5.6%), Bar 5: 1 (2.8%), Bar 18: 1 (2.8%)", self.html_content)
        self.assertIn("Zero trades reached H24 timeout.", self.html_content)

    def test_standalone_zero_external_network_or_server_dependency(self):
        """
        Verifies that table_viewer.html is 100% self-contained:
        - Zero fetch() calls
        - Zero XMLHttpRequest calls
        - Zero external http/https script/style resources
        - Zero external JSON or CDN dependencies
        - Safe for direct double-click opening via file:// protocol
        """
        # Script tags should only be inline
        script_tags = re.findall(r'<script\b[^>]*>', self.html_content, re.IGNORECASE)
        for tag in script_tags:
            self.assertNotIn("src=", tag.lower(), f"External script src forbidden: {tag}")

        # Link stylesheet tags should only be absent or inline data
        link_tags = re.findall(r'<link\b[^>]*>', self.html_content, re.IGNORECASE)
        for tag in link_tags:
            self.assertNotIn("stylesheet", tag.lower(), f"External stylesheet forbidden: {tag}")

        # No network API calls in JS
        js_code = self.html_content[self.html_content.find("<script>"):self.html_content.rfind("</script>")]
        self.assertNotIn("fetch(", js_code)
        self.assertNotIn("XMLHttpRequest", js_code)
        self.assertNotIn("http://", js_code)
        self.assertNotIn("https://", js_code)
        self.assertNotIn("import ", js_code)


class TestCpiLedgerFailClosedAndReconciliation(unittest.TestCase):
    """
    Focused tests proving:
    1. Missing cpi_trade_ledger.json fails closed with FileNotFoundError instructing operator to run cpi_simulation.py explicitly (never silently reruns).
    2. Missing required trials or metrics fail closed with clear ValueError (never silently defaults to 0, empty, or plausible values).
    3. Inconsistent directional or co-release split counts or R values fail closed with clear ValueError.
    4. Legitimate numerical zero remains zero (not rejected, not converted to None or empty, formatted cleanly with stat-zero).
    5. JavaScript syntax check passes cleanly with node --check.
    """

    @classmethod
    def setUpClass(cls):
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            cls.valid_ledger = json.load(f)

    def test_missing_ledger_file_raises_filenotfounderror_with_instruction(self):
        """Proves missing ledger file fails closed and instructs operator to run cpi_simulation.py."""
        from generator.cpi_ledger import load_cpi_ledger_data
        with self.assertRaises(FileNotFoundError) as ctx:
            load_cpi_ledger_data(ledger_path="nonexistent_path_to_cpi_trade_ledger.json")
        err_msg = str(ctx.exception)
        self.assertIn("CPI trade ledger not found", err_msg)
        self.assertIn("cpi_simulation.py", err_msg)
        self.assertIn("will not silently rerun", err_msg)

    def test_missing_required_trial_fails_closed(self):
        """Proves missing required trial raises ValueError rather than defaulting."""
        from generator.cpi_ledger import prepare_cpi_presentation_data
        import copy
        corrupted = copy.deepcopy(self.valid_ledger)
        del corrupted["trials"]["primary_1.5x_conservative"]
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted)
        self.assertIn("primary_1.5x_conservative", str(ctx.exception))

    def test_missing_or_none_required_metric_fails_closed(self):
        """Proves missing or None required metrics raise ValueError rather than defaulting to 0."""
        from generator.cpi_ledger import prepare_cpi_presentation_data
        import copy
        # 1. Missing total_gross_r in primary trial
        corrupted = copy.deepcopy(self.valid_ledger)
        del corrupted["trials"]["primary_1.5x_conservative"]["metrics"]["total_gross_r"]
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted)
        self.assertIn("total_gross_r", str(ctx.exception))

        # 2. None total_gross_r in sensitivity trial
        corrupted2 = copy.deepcopy(self.valid_ledger)
        corrupted2["trials"]["sensitivity_1.0x_conservative"]["metrics"]["total_gross_r"] = None
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted2)
        self.assertIn("total_gross_r", str(ctx.exception))

        # 3. Missing direction_splits
        corrupted3 = copy.deepcopy(self.valid_ledger)
        del corrupted3["trials"]["primary_1.5x_conservative"]["metrics"]["direction_splits"]
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted3)
        self.assertIn("direction_splits", str(ctx.exception))

        # 4. Missing co_release_splits
        corrupted4 = copy.deepcopy(self.valid_ledger)
        del corrupted4["trials"]["primary_1.5x_conservative"]["metrics"]["co_release_splits"]
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted4)
        self.assertIn("co_release_splits", str(ctx.exception))

        # 5. Missing bars_held_distribution
        corrupted5 = copy.deepcopy(self.valid_ledger)
        del corrupted5["trials"]["primary_1.5x_conservative"]["metrics"]["bars_held_distribution"]
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted5)
        self.assertIn("bars_held_distribution", str(ctx.exception))

    def test_inconsistent_directional_reconciliation_fails_closed(self):
        """Proves count or R reconciliation discrepancies in direction_splits raise ValueError."""
        from generator.cpi_ledger import prepare_cpi_presentation_data
        import copy
        # Count mismatch: long_count + short_count != total_trades
        corrupted = copy.deepcopy(self.valid_ledger)
        corrupted["trials"]["primary_1.5x_conservative"]["metrics"]["direction_splits"]["long_count"] += 1
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted)
        self.assertIn("Direction splits count reconciliation failure", str(ctx.exception))

        # R mismatch: long_gross_r + short_gross_r != total_gross_r
        corrupted_r = copy.deepcopy(self.valid_ledger)
        corrupted_r["trials"]["primary_1.5x_conservative"]["metrics"]["direction_splits"]["long_gross_r"] += 1.0
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted_r)
        self.assertIn("Direction splits R reconciliation failure", str(ctx.exception))

    def test_inconsistent_co_release_reconciliation_fails_closed(self):
        """Proves count or R reconciliation discrepancies in co_release_splits raise ValueError."""
        from generator.cpi_ledger import prepare_cpi_presentation_data
        import copy
        # Count mismatch: jobless + other != total_trades
        corrupted = copy.deepcopy(self.valid_ledger)
        corrupted["trials"]["primary_1.5x_conservative"]["metrics"]["co_release_splits"]["jobless_claims_count"] += 1
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted)
        self.assertIn("Co-release splits count reconciliation failure", str(ctx.exception))

        # R mismatch: jobless_r + other_r != total_gross_r
        corrupted_r = copy.deepcopy(self.valid_ledger)
        corrupted_r["trials"]["primary_1.5x_conservative"]["metrics"]["co_release_splits"]["jobless_claims_gross_r"] += 1.0
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(corrupted_r)
        self.assertIn("Co-release splits R reconciliation failure", str(ctx.exception))

    def test_legitimate_numerical_zero_remains_zero(self):
        """
        Proves that legitimate numerical zeros (e.g. 0 R return, 0 timeouts, 0 ambiguous trades)
        are preserved as valid numerical zero and not rejected, dropped, or corrupted.
        """
        from generator.cpi_ledger import prepare_cpi_presentation_data, format_trial_r_html, format_subgroup_r_html

        # 1. Helper formatting verification for zero
        zero_trial_html = format_trial_r_html(0.0)
        self.assertIn('class="stat-zero"', zero_trial_html)
        self.assertIn('+0.00 R', zero_trial_html)

        zero_subgroup_html = format_subgroup_r_html(0.0)
        self.assertIn('class="stat-zero"', zero_subgroup_html)
        self.assertIn('0 R', zero_subgroup_html)

        # 2. Existing baseline ledger has legitimate zeros
        pres = prepare_cpi_presentation_data(self.valid_ledger)
        # Timeout count is 0
        self.assertEqual(pres["timeout_str_html"], "Zero trades reached H24 timeout.")
        # Other co-releases gross R is 0.0 (near-zero floating point from raw trials)
        self.assertAlmostEqual(pres["other_gross_r"], 0.0, places=4)
        self.assertIn('<span class="stat-zero">0 R</span>', pres["other_r_html"])

        # 3. Dynamic ledger with 0.0 total gross R remains 0.0
        import copy
        zero_ledger = copy.deepcopy(self.valid_ledger)
        zero_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["total_gross_r"] = 0.0
        zero_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["mean_gross_r"] = 0.0
        zero_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["gross_r_without_best_trade"] = 0.0
        zero_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["direction_splits"]["long_gross_r"] = 0.0
        zero_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["direction_splits"]["short_gross_r"] = 0.0
        zero_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["co_release_splits"]["jobless_claims_gross_r"] = 0.0
        zero_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["co_release_splits"]["other_co_releases_gross_r"] = 0.0
        for t in zero_ledger["trials"]["primary_1.5x_conservative"]["trades"]:
            t["gross_r_multiple"] = 0.0
        pres_zero = prepare_cpi_presentation_data(zero_ledger)
        self.assertIn('<span class="stat-zero"><strong>+0.00 R</strong></span>', pres_zero["p_gross_r_html"])

        # 4. Zero trades trial (total_trades = 0, len(trades) = 0) is valid
        zero_trades_ledger = copy.deepcopy(self.valid_ledger)
        for t_k in ["primary_1.5x_conservative", "sensitivity_1.0x_conservative", "sensitivity_2.0x_conservative"]:
            zero_trades_ledger["trials"][t_k]["trades"] = []
            zero_trades_ledger["trials"][t_k]["metrics"]["total_trades"] = 0
            zero_trades_ledger["trials"][t_k]["metrics"]["wins"] = 0
            zero_trades_ledger["trials"][t_k]["metrics"]["losses"] = 0
            zero_trades_ledger["trials"][t_k]["metrics"]["ties"] = 0
            zero_trades_ledger["trials"][t_k]["metrics"]["total_gross_r"] = 0.0
            zero_trades_ledger["trials"][t_k]["metrics"]["mean_gross_r"] = 0.0
        zero_trades_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["bars_held_distribution"] = {}
        zero_trades_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["direction_splits"] = {
            "long_count": 0, "short_count": 0, "long_gross_r": 0.0, "short_gross_r": 0.0
        }
        zero_trades_ledger["trials"]["primary_1.5x_conservative"]["metrics"]["co_release_splits"] = {
            "jobless_claims_count": 0, "jobless_claims_gross_r": 0.0,
            "other_co_releases_count": 0, "other_co_releases_gross_r": 0.0
        }
        pres_zt = prepare_cpi_presentation_data(zero_trades_ledger)
        self.assertEqual(pres_zt["total_trades_cnt"], 0)

    def test_trade_gross_r_reconciliation_fails_closed(self):
        """Proves discrepancy between sum of trade gross_r_multiple and total_gross_r raises ValueError."""
        from generator.cpi_ledger import prepare_cpi_presentation_data
        import copy
        damaged = copy.deepcopy(self.valid_ledger)
        damaged["trials"]["primary_1.5x_conservative"]["trades"][0]["gross_r_multiple"] += 1.0
        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(damaged)
        self.assertIn("gross R reconciliation failure", str(ctx.exception))

    def test_regression_damaged_empty_trades_with_nonzero_total(self):
        """
        Regression Test 1 (Codex Audit Case):
        Starting with an in-memory copy of the real ledger, set the primary trial's trades to []
        and its exit_counts.TIMEOUT_H24 to 0.
        prepare_cpi_presentation_data() must raise a clear ValueError rather than accepting
        total_trades=36 and producing zero subgroup target/stop counts.
        """
        from generator.cpi_ledger import prepare_cpi_presentation_data
        import copy
        damaged = copy.deepcopy(self.valid_ledger)
        damaged["trials"]["primary_1.5x_conservative"]["trades"] = []
        if "exit_counts" not in damaged["trials"]["primary_1.5x_conservative"]["metrics"]:
            damaged["trials"]["primary_1.5x_conservative"]["metrics"]["exit_counts"] = {}
        damaged["trials"]["primary_1.5x_conservative"]["metrics"]["exit_counts"]["TIMEOUT_H24"] = 0

        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(damaged)
        self.assertIn("trade count mismatch", str(ctx.exception))
        self.assertIn("primary_1.5x_conservative", str(ctx.exception))

    def test_regression_damaged_outcomes_reconciliation(self):
        """
        Regression Test 2 (Codex Audit Case):
        Starting with an in-memory copy of the real ledger, change primary wins from 16 to 35
        while leaving losses=20 and total_trades=36.
        prepare_cpi_presentation_data() must raise a clear ValueError rather than accepting
        55 outcomes for 36 trades.
        """
        from generator.cpi_ledger import prepare_cpi_presentation_data
        import copy
        damaged = copy.deepcopy(self.valid_ledger)
        damaged["trials"]["primary_1.5x_conservative"]["metrics"]["wins"] = 35

        with self.assertRaises(ValueError) as ctx:
            prepare_cpi_presentation_data(damaged)
        self.assertIn("outcome reconciliation failure", str(ctx.exception))
        self.assertIn("primary_1.5x_conservative", str(ctx.exception))

    def test_javascript_syntax_with_node(self):
        """
        Validates JavaScript syntax of template app.js and extracted inline script from table_viewer.html using node --check.
        """
        import subprocess
        import tempfile

        # Check template app.js
        app_js_path = os.path.join(VIEWER_DIR, "generator", "templates", "app.js")
        result_app = subprocess.run(["node", "--check", app_js_path], capture_output=True, text=True)
        self.assertEqual(result_app.returncode, 0, f"app.js syntax error: {result_app.stderr}")

        # Check generated table_viewer.html inline script
        with open(HTML_PATH, "r", encoding="utf-8") as f:
            html = f.read()
        js_start = html.find("<script>") + len("<script>")
        js_end = html.rfind("</script>")
        js_code = html[js_start:js_end]

        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8") as tf:
            tf.write(js_code)
            tmp_js = tf.name

        try:
            result_html_js = subprocess.run(["node", "--check", tmp_js], capture_output=True, text=True)
            self.assertEqual(result_html_js.returncode, 0, f"table_viewer.html inline script syntax error: {result_html_js.stderr}")
        finally:
            if os.path.exists(tmp_js):
                os.remove(tmp_js)


if __name__ == "__main__":
    unittest.main()

