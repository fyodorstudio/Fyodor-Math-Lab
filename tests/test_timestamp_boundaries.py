"""
Synthetic Unit Tests for Timestamp Boundaries & Coverage
Tests chronological split enforcement, H4 block boundaries, entry delay rules,
forward-path eligibility versus pre-entry lookback, and weekend gap handling.
"""

import unittest
import tempfile
import os
from src.package_ledger import compute_entry_timestamp
from src.candle_coverage import CandleTimestampIndex, SECONDS_IN_H1, SECONDS_IN_H4
from src.parsers import SPLIT_TIMESTAMP


class TestTimestampBoundaries(unittest.TestCase):

    def test_entry_timestamp_computation(self):
        base = 1500006400 - (1500006400 % 14400)

        # 15:30 release -> Open of next H4 bar is 16:00 (30 min delay)
        rel_1530 = base + 12600
        entry_1530 = compute_entry_timestamp(rel_1530)
        self.assertEqual(entry_1530, base + 14400)
        self.assertEqual((entry_1530 - rel_1530) // 60, 30)

        # 16:30 release -> Open of next H4 bar is 20:00 (210 min / 3.5h delay)
        rel_1630 = base + 1800
        entry_1630 = compute_entry_timestamp(rel_1630)
        self.assertEqual(entry_1630, base + 14400)
        self.assertEqual((entry_1630 - rel_1630) // 60, 210)

    def test_h4_block_integrity(self):
        base_h4 = 1600003200
        base_h4 = (base_h4 // 14400) * 14400

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

    def test_forward_weekend_crossing(self):
        # Small hand-checkable fixture:
        # Friday entry at 16:00:
        # Friday trading: 2 H4 blocks (16:00 to 24:00 = 8 H1 bars)
        # Weekend gap: 48 hours (Friday 24:00 to Monday 00:00)
        # Monday trading: 4 H4 blocks (00:00 to 16:00 = 16 H1 bars)
        # Total forward blocks: 2 + 4 = 6 completed H4 blocks = 24 active hours
        # Friday 2020-09-18 16:00:00 UTC = 1600444800
        base_friday_entry = 1600444800

        bars = []
        for i in range(8):
            bars.append(base_friday_entry + i * SECONDS_IN_H1)

        monday_open = base_friday_entry + 8 * SECONDS_IN_H1 + 48 * SECONDS_IN_H1
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
            cov = idx.evaluate_forward_horizon(base_friday_entry, horizon_h4=6)

            self.assertTrue(cov["is_complete"])
            self.assertEqual(cov["completed_blocks"], 6)
            self.assertTrue(cov["crosses_weekend"])
            self.assertFalse(cov["has_missing_h1"])
            self.assertEqual(cov["exit_timestamp"], monday_open + 16 * SECONDS_IN_H1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_forward_eligibility_versus_lookback_eligibility(self):
        # Small hand-checkable fixture:
        # Monday 16:00 entry:
        # Preceding Sunday/Monday has ONLY 4 completed H4 blocks (16 hours = 00:00 to 16:00).
        # Before Monday 00:00 is a 48h weekend gap.
        # Forward Monday 16:00 has 6 continuous H4 blocks (24 hours = Monday 16:00 to Tuesday 16:00).
        monday_entry = 1600003200
        monday_entry = (monday_entry // 14400) * 14400
        monday_open = monday_entry - 4 * SECONDS_IN_H4

        bars = []
        # Monday pre-entry: 16 hours = 4 H4 blocks
        for i in range(16):
            bars.append(monday_open + i * SECONDS_IN_H1)

        # Forward holding: 24 hours = 6 H4 blocks
        for i in range(24):
            bars.append(monday_entry + i * SECONDS_IN_H1)

        content = "time,open,high,low,close,tick_volume,spread,real_volume\n"
        for b in sorted(list(set(bars))):
            content += f"{b},1.0,1.1,0.9,1.0,10,1,0\n"

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            idx = CandleTimestampIndex(tmp_path, split_timestamp=SPLIT_TIMESTAMP)

            # 1. Forward path evaluation for 6 H4: fully clean!
            fwd_cov = idx.evaluate_forward_horizon(monday_entry, horizon_h4=6)
            self.assertTrue(fwd_cov["is_complete"])
            self.assertEqual(fwd_cov["completed_blocks"], 6)
            self.assertFalse(fwd_cov["crosses_weekend"])

            # 2. Pre-entry lookback audit: only 4 blocks completed this week!
            lb_audit = idx.audit_pre_entry_lookback(monday_entry, target_h4_blocks=14)
            self.assertEqual(lb_audit["intra_week_completed_blocks"], 4)
            self.assertFalse(lb_audit["has_14_intra_week"])
            self.assertTrue(lb_audit["hit_weekend_or_gap_backwards"])

            # This proves: forward eligibility is 100% complete, while intra-week lookback fails!
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
