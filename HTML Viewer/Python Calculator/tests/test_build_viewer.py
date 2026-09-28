"""Regression checks for the standalone final-evidence viewer snapshot."""

import importlib.util
import json
from pathlib import Path
import unittest


CALC_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_viewer", CALC_DIR / "build_viewer.py")
build_viewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_viewer)


@unittest.skipUnless(
    (build_viewer.ROOT / "Research Candidate" / "CPI" / "CPI_EXPLORATION_V2" /
     build_viewer.RUN_ID / "manifest.json").exists(),
    "Local ignored final CPI/NFP packages are not present",
)
class FinalViewerSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rendered, cls.payload = build_viewer.build_html()

    def test_snapshot_is_current_and_standalone(self):
        self.assertEqual(self.rendered, build_viewer.HTML.read_text(encoding="utf-8"))
        self.assertIn('id="viewer-data"', self.rendered)
        self.assertNotIn('src="http', self.rendered)

    def test_complete_family_counts_and_paths(self):
        for name, count in (("CPI", 9984), ("NFP", 11232)):
            family = self.payload["families"][name]
            self.assertEqual(len(family["episodes"]), 980)
            self.assertEqual(len(family["summaries"]), count)
            self.assertTrue(all(len(row[10]) == 240 for row in family["episodes"]))

    def test_representative_eurusd_cells_match_ledger_reconciled_summary(self):
        examples = (
            ("CPI", "JOBLESS_CLAIMS_CLEAN", ("73", "36", "37", "-0.013699", "4/9")),
            ("NFP", "PRIMARY_PANEL", ("111", "62", "49", "0.117117", "9/9")),
        )
        for family_name, panel, expected in examples:
            rows = [row for row in self.payload["families"][family_name]["summaries"]
                    if row[:5] == [panel, "EURUSD", "af", "ALL_ELIGIBLE", "60"]
                    and row[5:7] == ["2", "2"]]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual((row[8], row[9], row[10], row[13], row[19]), expected)

    def test_embedded_json_matches_loaded_evidence(self):
        start = self.rendered.index('<script type="application/json" id="viewer-data">')
        start = self.rendered.index(">", start) + 1
        end = self.rendered.index("</script>", start)
        self.assertEqual(json.loads(self.rendered[start:end]), self.payload)


if __name__ == "__main__":
    unittest.main()
