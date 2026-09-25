"""
Synthetic Unit Tests for Package Joins & Sign Classifications
Tests co-release grouping, surprise computations, sign concordances, and cross-currency collision detection.
"""

import unittest
import tempfile
import os
from src.package_ledger import build_retail_sales_package_ledger
from src.parsers import EXPECTED_CALENDAR_COLUMNS


def make_synthetic_calendar_row(
    event_id: str,
    ts: int,
    curr: str,
    event_name: str,
    actual: str,
    forecast: str,
    previous: str,
    actual_raw: str = "",
    forecast_raw: str = "",
    previous_raw: str = ""
) -> str:
    row = [""] * 36
    row[0] = str(event_id)
    row[1] = "1"
    row[2] = str(ts)
    row[3] = curr
    row[4] = "US" if curr == "USD" else "CA"
    row[5] = event_name
    row[6] = "high"
    row[7] = str(actual)
    row[8] = str(forecast)
    row[9] = str(previous)
    row[12] = "0"  # revision
    row[28] = str(actual_raw)
    row[29] = str(forecast_raw)
    row[30] = str(previous_raw)
    row[32] = "2020.01.15 15:30:00"
    row[33] = "2019.12.01 00:00:00"
    return ",".join(row)


class TestPackageJoins(unittest.TestCase):

    def test_package_classification_and_collisions(self):
        # 1. Package 1: Strict POS/POS with CAD collision
        # Headline: A=0.5, F=0.2 (+0.3) -> POS
        # Core:     A=0.4, F=0.1 (+0.3) -> POS
        # CAD:      Manufacturing Sales at same timestamp
        ts1 = 1500000000

        # 2. Package 2: Active Conflict POS/NEG
        # Headline: A=0.3, F=0.1 (+0.2) -> POS
        # Core:     A=-0.1, F=0.2 (-0.3) -> NEG
        ts2 = 1510000000

        # 3. Package 3: One Zero
        # Headline: A=0.2, F=0.2 (0.0) -> ZERO
        # Core:     A=0.5, F=0.1 (+0.4) -> POS
        ts3 = 1520000000

        # 4. Package 4: Missing Forecast
        # Headline: A=0.2, F="", P=0.1
        # Core:     A=0.1, F="", P=0.0
        ts4 = 1530000000

        lines = [",".join(EXPECTED_CALENDAR_COLUMNS)]

        # Add rows for pkg 1
        lines.append(make_synthetic_calendar_row("840020010", ts1, "USD", "Retail Sales m/m", "0.5", "0.2", "0.1", "500000", "200000", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts1, "USD", "Core Retail Sales m/m", "0.4", "0.1", "0.1", "400000", "100000", "100000"))
        lines.append(make_synthetic_calendar_row("124010001", ts1, "CAD", "Manufacturing Sales m/m", "1.0", "0.5", "0.2", "1000000", "500000", "200000"))

        # Add rows for pkg 2
        lines.append(make_synthetic_calendar_row("840020010", ts2, "USD", "Retail Sales m/m", "0.3", "0.1", "0.1", "300000", "100000", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts2, "USD", "Core Retail Sales m/m", "-0.1", "0.2", "0.1", "-100000", "200000", "100000"))

        # Add rows for pkg 3
        lines.append(make_synthetic_calendar_row("840020010", ts3, "USD", "Retail Sales m/m", "0.2", "0.2", "0.1", "200000", "200000", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts3, "USD", "Core Retail Sales m/m", "0.5", "0.1", "0.1", "500000", "100000", "100000"))

        # Add rows for pkg 4
        lines.append(make_synthetic_calendar_row("840020010", ts4, "USD", "Retail Sales m/m", "0.2", "", "0.1", "200000", "", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts4, "USD", "Core Retail Sales m/m", "0.1", "", "0.0", "100000", "", "0"))

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write("\n".join(lines) + "\n")

        try:
            ledger = build_retail_sales_package_ledger(tmp_path, candle_csv_path=None)

            self.assertEqual(ledger["total_packages"], 4)
            self.assertEqual(ledger["complete_joint_afp_packages"], 3)

            pkgs = {p["timestamp"]: p for p in ledger["packages"]}

            # Check Pkg 1
            p1 = pkgs[ts1]
            self.assertEqual(p1["sign_category"], "STRICT_AGREE_POS")
            self.assertTrue(p1["has_cross_currency_collision"])
            self.assertEqual(p1["colliding_currencies"], ["CAD"])
            self.assertEqual(p1["co_released_events_count"], 3)
            self.assertEqual(p1["headline_diff_scaled"], 300000)
            self.assertEqual(p1["core_diff_scaled"], 300000)

            # Check Pkg 2
            p2 = pkgs[ts2]
            self.assertEqual(p2["sign_category"], "ACTIVE_CONFLICT")
            self.assertFalse(p2["has_cross_currency_collision"])
            self.assertEqual(p2["headline_diff_scaled"], 200000)
            self.assertEqual(p2["core_diff_scaled"], -300000)

            # Check Pkg 3
            p3 = pkgs[ts3]
            self.assertEqual(p3["sign_category"], "ONE_ZERO")
            self.assertEqual(p3["headline_diff_scaled"], 0)
            self.assertEqual(p3["core_diff_scaled"], 400000)

            # Check Pkg 4
            p4 = pkgs[ts4]
            self.assertEqual(p4["sign_category"], "MISSING_FORECAST")
            self.assertFalse(p4["joint_afp_complete"])

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
