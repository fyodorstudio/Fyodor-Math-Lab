"""
Synthetic Unit Tests for Timestamp Boundaries & Coverage
Tests chronological split enforcement, H4 block boundaries, entry delay rules, and weekend gap handling.
"""

import unittest
import tempfile
import os
from src.package_ledger import compute_entry_timestamp
from src.candle_coverage import CandleTimestampIndex, SECONDS_IN_H1, SECONDS_IN_H4
from src.parsers import SPLIT_TIMESTAMP


class TestTimestampBoundaries(unittest.TestCase):

    def test_entry_timestamp_computation(self):
        # Base H4 timestamp: e.g. 1500000000 % 14400
        # Let base = 1500000000 - (1500000000 % 14400) (aligned to 00:00, 04:00, 08:00, 12:00, 16:00, or 20:00)
        base = 1500006400 - (1500006400 % 14400)  # aligned H4

        # 15:30 is 12:00 + 3.5h = 12:00 + 12600s
        # 12:00 is aligned to H4. Next H4 is 16:00 (+14400s).
        rel_1530 = base + 12600
        entry_1530 = compute_entry_timestamp(rel_1530)
        self.assertEqual(entry_1530, base + 14400)
        self.assertEqual((entry_1530 - rel_1530) // 60, 30)  # exactly 30 min delay

        # 16:30 is 16:00 + 0.5h = 16:00 + 1800s
        # 16:00 is aligned to H4. Next H4 is 20:00 (+14400s).
        rel_1630 = base + 1800
        entry_1630 = compute_entry_timestamp(rel_1630)
        self.assertEqual(entry_1630, base + 14400)
        self.assertEqual((entry_1630 - rel_1630) // 60, 210)  # exactly 210 min (3.5 hours) delay

    def test_h4_block_integrity(self):
        base_h4 = 1600003200  # must be divisible by 14400
        base_h4 = (base_h4 // 14400) * 14400

        # Construct candle CSV with 4 consecutive H1 bars for this block
        bars = [base_h4, base_h4 + 3600, base_h4 + 7200, base_h4 + 10800]
        content = "time,open,high,low,close,tick_volume,spread,real_volume\n"
        for b in bars:
            content += f"{b},1.0,1.1,0.9,1.0,10,1,0\n"

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            idx = CandleTimestampIndex(tmp_path, split_timestamp=SPLIT_TIMESTAMP)
            is_ok, missing = idx.check_h4_block(base_h4)
            self.assertTrue(is_ok)
            self.assertEqual(missing, [])

            # Test missing constituent bar
            # Remove bar at offset 7200
            content_missing = "time,open,high,low,close,tick_volume,spread,real_volume\n"
            for b in [base_h4, base_h4 + 3600, base_h4 + 10800]:
                content_missing += f"{b},1.0,1.1,0.9,1.0,10,1,0\n"

            with open(tmp_path, "w") as f2:
                f2.write(content_missing)

            idx_missing = CandleTimestampIndex(tmp_path, split_timestamp=SPLIT_TIMESTAMP)
            is_ok_m, missing_m = idx_missing.check_h4_block(base_h4)
            self.assertFalse(is_ok_m)
            self.assertEqual(missing_m, [7200])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_holding_horizon_weekend_crossing(self):
        # Create continuous Friday bars (8 hours = 2 H4 blocks), then 48h weekend gap, then Monday bars (16 hours = 4 H4 blocks)
        base_friday_entry = 1600003200
        base_friday_entry = (base_friday_entry // 14400) * 14400

        bars = []
        # Friday: 2 H4 blocks = 8 H1 bars
        for i in range(8):
            bars.append(base_friday_entry + i * SECONDS_IN_H1)

        # Weekend jump: Friday 24:00 to Monday 00:00 (48 hours = 48 * 3600 gap)
        monday_open = base_friday_entry + 8 * SECONDS_IN_H1 + 48 * SECONDS_IN_H1
        # Monday: 4 H4 blocks = 16 H1 bars
        for i in range(16):
            bars.append(monday_open + i * SECONDS_IN_H1)

        content = "time,open,high,low,close,tick_volume,spread,real_volume\n"
        for b in bars:
            content += f"{b},1.0,1.1,0.9,1.0,10,1,0\n"

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            idx = CandleTimestampIndex(tmp_path, split_timestamp=SPLIT_TIMESTAMP)
            cov = idx.evaluate_holding_horizon(base_friday_entry, horizon_h4=6)

            self.assertTrue(cov["is_complete"])
            self.assertEqual(cov["completed_blocks"], 6)
            self.assertTrue(cov["crosses_weekend"])
            self.assertFalse(cov["has_missing_h1"])
            self.assertFalse(cov["crosses_split"])
            # Exit timestamp should be monday_open + 16 * 3600
            self.assertEqual(cov["exit_timestamp"], monday_open + 16 * SECONDS_IN_H1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_holding_horizon_split_boundary_rejection(self):
        # Test an episode right before the split boundary 1672531200
        # If entry is 12 hours before split, a 24-hour horizon crosses the split and must fail closed
        near_split_entry = SPLIT_TIMESTAMP - 12 * SECONDS_IN_H1
        near_split_entry = (near_split_entry // 14400) * 14400

        bars = []
        for i in range(24):
            b = near_split_entry + i * SECONDS_IN_H1
            bars.append(b)

        content = "time,open,high,low,close,tick_volume,spread,real_volume\n"
        for b in bars:
            content += f"{b},1.0,1.1,0.9,1.0,10,1,0\n"

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            idx = CandleTimestampIndex(tmp_path, split_timestamp=SPLIT_TIMESTAMP)
            cov = idx.evaluate_holding_horizon(near_split_entry, horizon_h4=6)

            self.assertFalse(cov["is_complete"])
            self.assertTrue(cov["crosses_split"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
