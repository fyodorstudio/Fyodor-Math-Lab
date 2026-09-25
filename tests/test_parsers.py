"""
Synthetic Unit Tests for Parsers
Tests RFC4180 parsing, column validation, and price-blind timestamp readers.
"""

import unittest
import tempfile
import os
from src.parsers import (
    parse_rfc4180_line,
    stream_calendar_releases,
    stream_candle_timestamps_only,
    EXPECTED_CALENDAR_COLUMNS,
    SPLIT_TIMESTAMP,
)


class TestParsers(unittest.TestCase):

    def test_rfc4180_parsing(self):
        # Standard unquoted line
        line1 = "123,USD,US,Retail Sales,0.5"
        self.assertEqual(parse_rfc4180_line(line1), ["123", "USD", "US", "Retail Sales", "0.5"])

        # Quoted field with comma
        line2 = '123,"USD,EUR",US,"Retail Sales m/m",0.5'
        self.assertEqual(parse_rfc4180_line(line2), ["123", "USD,EUR", "US", "Retail Sales m/m", "0.5"])

        # Quoted field with escaped quote
        line3 = '123,"US ""Core"" Retail",0.5'
        self.assertEqual(parse_rfc4180_line(line3), ["123", 'US "Core" Retail', "0.5"])

    def test_calendar_schema_validation(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            # Write invalid header
            tmp.write("col1,col2,col3\n1,2,3\n")

        try:
            with self.assertRaises(ValueError) as ctx:
                list(stream_calendar_releases(tmp_path))
            self.assertIn("Calendar schema mismatch", str(ctx.exception))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_calendar_valid_streaming(self):
        # Create a valid synthetic 36-column row
        row = [""] * 36
        row[0] = "840020010"  # event_id
        row[1] = "100"        # value_id
        row[2] = "1500000000" # timestamp
        row[3] = "USD"
        row[4] = "US"
        row[5] = "Retail Sales m/m"
        row[6] = "high"
        row[7] = "0.4"        # actual
        row[8] = "0.2"        # forecast
        row[9] = "-0.1"       # previous
        row[11] = "1497139200"# period
        row[12] = "0"         # revision
        row[16] = "840"       # country_id
        row[24] = "1"         # digits
        row[28] = "400000"    # actual_raw_scaled_1e6
        row[29] = "200000"    # forecast_raw_scaled_1e6
        row[30] = "-100000"   # previous_raw_scaled_1e6

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(",".join(EXPECTED_CALENDAR_COLUMNS) + "\n")
            tmp.write(",".join(row) + "\n")

        try:
            records = list(stream_calendar_releases(tmp_path))
            self.assertEqual(len(records), 1)
            rec = records[0]
            self.assertEqual(rec["event_id"], "840020010")
            self.assertEqual(rec["timestamp"], 1500000000)
            self.assertEqual(rec["actual_raw_scaled_1e6"], 400000)
            self.assertEqual(rec["forecast_raw_scaled_1e6"], 200000)
            self.assertEqual(rec["previous_raw_scaled_1e6"], -100000)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_candle_timestamp_reader_price_blindness_and_split(self):
        # Synthetic candle CSV with time and dummy price columns
        content = (
            "time,open,high,low,close,tick_volume,spread,real_volume\n"
            "1672524000,1.0700,1.0710,1.0690,1.0705,100,5,0\n"  # 2 hours before split
            "1672527600,1.0705,1.0720,1.0700,1.0715,110,5,0\n"  # 1 hour before split
            "1672531200,1.0715,1.0730,1.0710,1.0725,120,5,0\n"  # exact split boundary
            "1672534800,1.0725,1.0740,1.0720,1.0735,130,5,0\n"  # 1 hour after split
        )

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            # Stream timestamps only up to SPLIT_TIMESTAMP (1672531200)
            timestamps = list(stream_candle_timestamps_only(tmp_path, split_timestamp=SPLIT_TIMESTAMP))
            # Must return ONLY pre-split timestamps
            self.assertEqual(timestamps, [1672524000, 1672527600])
            self.assertNotIn(1672531200, timestamps)
            self.assertNotIn(1672534800, timestamps)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
