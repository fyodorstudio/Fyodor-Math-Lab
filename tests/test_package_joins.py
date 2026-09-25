"""
Synthetic Unit Tests for Package Joins & Denominator Reconciliation
Tests co-release grouping, surprise computations, sign concordances, and denominator reconciliations.
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
    row[12] = "0"
    row[28] = str(actual_raw)
    row[29] = str(forecast_raw)
    row[30] = str(previous_raw)
    row[32] = "2020.01.15 15:30:00"
    row[33] = "2019.12.01 00:00:00"
    return ",".join(row)


class TestPackageJoins(unittest.TestCase):

    def test_hand_checkable_denominator_reconciliation(self):
        # Hand-checkable fixture with exactly 4 retail packages:
        # Pkg 1: Strict POS/POS with CAD collision (A=0.5, F=0.2 -> +0.3; Core A=0.4, F=0.1 -> +0.3)
        # Pkg 2: Active conflict POS/NEG (A=0.3, F=0.1 -> +0.2; Core A=-0.1, F=0.2 -> -0.3)
        # Pkg 3: One-zero (A=0.2, F=0.2 -> 0.0; Core A=0.5, F=0.1 -> +0.4)
        # Pkg 4: Missing forecast (A=0.2, F="", P=0.1; Core A=0.1, F="", P=0.0)
        # Extra: 1 non-retail package (event_id 840010001) that should not be counted as retail
        ts1 = 1500000000
        ts2 = 1510000000
        ts3 = 1520000000
        ts4 = 1530000000
        ts5 = 1540000000  # non-retail

        lines = [",".join(EXPECTED_CALENDAR_COLUMNS)]

        # Pkg 1
        lines.append(make_synthetic_calendar_row("840020010", ts1, "USD", "Retail Sales m/m", "0.5", "0.2", "0.1", "500000", "200000", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts1, "USD", "Core Retail Sales m/m", "0.4", "0.1", "0.1", "400000", "100000", "100000"))
        lines.append(make_synthetic_calendar_row("124010001", ts1, "CAD", "Manufacturing Sales m/m", "1.0", "0.5", "0.2", "1000000", "500000", "200000"))

        # Pkg 2
        lines.append(make_synthetic_calendar_row("840020010", ts2, "USD", "Retail Sales m/m", "0.3", "0.1", "0.1", "300000", "100000", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts2, "USD", "Core Retail Sales m/m", "-0.1", "0.2", "0.1", "-100000", "200000", "100000"))

        # Pkg 3
        lines.append(make_synthetic_calendar_row("840020010", ts3, "USD", "Retail Sales m/m", "0.2", "0.2", "0.1", "200000", "200000", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts3, "USD", "Core Retail Sales m/m", "0.5", "0.1", "0.1", "500000", "100000", "100000"))

        # Pkg 4
        lines.append(make_synthetic_calendar_row("840020010", ts4, "USD", "Retail Sales m/m", "0.2", "", "0.1", "200000", "", "100000"))
        lines.append(make_synthetic_calendar_row("840020011", ts4, "USD", "Core Retail Sales m/m", "0.1", "", "0.0", "100000", "", "0"))

        # Non-retail package
        lines.append(make_synthetic_calendar_row("840010001", ts5, "USD", "Core PCE Price Index m/m", "0.2", "0.2", "0.1", "200000", "200000", "100000"))

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write("\n".join(lines) + "\n")

        try:
            ledger = build_retail_sales_package_ledger(tmp_path, candle_csv_path=None)

            # Reconcile counts
            self.assertEqual(ledger["total_packages"], 4)
            self.assertEqual(ledger["complete_joint_afp_packages"], 3)

            # Denominator reconciliation:
            # 1. Against total packages (N = 4):
            self.assertEqual(ledger["cross_currency_collisions"]["all_pre2023"]["count"], 1)
            self.assertEqual(ledger["cross_currency_collisions"]["all_pre2023"]["pct"], 1 / 4)

            # 2. Against complete AFP packages (N = 3):
            self.assertEqual(ledger["cross_currency_collisions"]["complete_afp"]["count"], 1)
            self.assertEqual(ledger["cross_currency_collisions"]["complete_afp"]["pct"], 1 / 3)

            # Sign distributions
            signs = ledger["sign_distribution"]
            self.assertEqual(signs["STRICT_AGREE_POS"], 1)
            self.assertEqual(signs["ACTIVE_CONFLICT"], 1)
            self.assertEqual(signs["ONE_ZERO"], 1)
            self.assertEqual(signs["MISSING_FORECAST"], 1)

            # Sum of categories equals total packages
            self.assertEqual(sum(signs.values()), 4)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
