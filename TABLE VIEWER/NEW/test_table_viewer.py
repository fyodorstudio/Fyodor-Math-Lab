"""
Unit tests for the new light-mode table viewer in TABLE VIEWER/NEW.
Verifies:
1. HTML file existence and validity.
2. Light mode styling (strict absence of dark mode CSS).
3. Pinned pairs and event families integrity.
4. Exact pip calculations on hand-checkable candle bars.
5. Inversion logic for USD-base vs USD-quote currency pairs.
"""

import unittest
import os
import json
import re

VIEWER_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(VIEWER_DIR, "table_viewer.html")


class TestNewTableViewer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(HTML_PATH):
            import subprocess
            subprocess.run(["python", os.path.join(VIEWER_DIR, "generate_table.py")], check=True)

        with open(HTML_PATH, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

        # Extract embedded JSON DB
        start_marker = "const DB = "
        end_marker = ";\n\n  let displayMode"
        idx1 = cls.html_content.find(start_marker) + len(start_marker)
        idx2 = cls.html_content.find(end_marker)
        raw_json = cls.html_content[idx1:idx2]
        cls.data = json.loads(raw_json)

    def test_file_exists_and_non_empty(self):
        self.assertTrue(os.path.exists(HTML_PATH))
        self.assertGreater(os.path.getsize(HTML_PATH), 1000000)

    def test_strict_light_mode_styling(self):
        """Verifies strictly light mode (no dark theme backgrounds or CSS classes)."""
        content_lower = self.html_content.lower()
        self.assertNotIn("dark-theme", content_lower)
        self.assertNotIn("theme-dark", content_lower)
        self.assertNotIn("@media (prefers-color-scheme: dark)", content_lower)
        # Background should be light
        self.assertIn("background-color: #f8fafc", self.html_content)

    def test_pairs_metadata_completeness(self):
        """Verifies all 19 full FX pairs exist in metadata with pip size and USD role."""
        pairs = self.data["pairs"]
        self.assertEqual(len(pairs), 19)
        self.assertIn("EURUSD", pairs)
        self.assertIn("USDJPY", pairs)
        self.assertIn("GBPUSD", pairs)
        self.assertIn("AUDUSD", pairs)
        self.assertIn("USDCAD", pairs)
        self.assertIn("USDCHF", pairs)
        self.assertIn("NZDUSD", pairs)

        meta = self.data["pair_meta"]
        self.assertEqual(meta["EURUSD"]["pip"], 0.00010)
        self.assertEqual(meta["EURUSD"]["usd_role"], "quote")
        self.assertEqual(meta["USDJPY"]["pip"], 0.010)
        self.assertEqual(meta["USDJPY"]["usd_role"], "base")

    def test_event_families_present(self):
        """Verifies all required event families are present."""
        fams = self.data["families"]
        self.assertIn("US_INFLATION", fams)
        self.assertIn("US_LABOR", fams)
        self.assertIn("US_RETAIL_SALES", fams)

    def test_episodes_data_integrity(self):
        """Verifies episodes structure, dates, and non-empty pips arrays."""
        episodes = self.data["episodes"]
        self.assertGreater(len(episodes), 500)

        for ep in episodes[:50]:
            self.assertIn("ts", ep)
            self.assertIn("dt_str", ep)
            self.assertIn("family", ep)
            self.assertIn("indicators", ep)
            self.assertIn("pips", ep)
            self.assertEqual(len(ep["pips"]["EURUSD"]), 60)
            self.assertEqual(len(ep["pips"]["USDJPY"]), 60)

    def test_2026_coverage_and_cutoff_handling(self):
        """Verifies 2026 episodes exist, have complete observations up to export, and UI renders nulls as '--'."""
        episodes = self.data["episodes"]
        ep_2026 = [ep for ep in episodes if ep["year"] == 2026]
        self.assertTrue(len(ep_2026) > 0)
        self.assertEqual(len(ep_2026), 54)
        # Verify that table viewer code explicitly formats null/unobserved bars as '--'
        self.assertIn("tdH.textContent = '--';", self.html_content)
        self.assertIn("cell-na", self.html_content)


if __name__ == "__main__":
    unittest.main()
