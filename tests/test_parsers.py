"""
Synthetic Unit Tests for Parsers
Tests RFC4180 parsing, column validation, and price-blind timestamp readers with hand-checkable fixtures.
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
        line1 = "123,USD,US,Retail Sales,0.5"
        self.assertEqual(parse_rfc4180_line(line1), ["123", "USD", "US", "Retail Sales", "0.5"])

        line2 = '123,"USD,EUR",US,"Retail Sales m/m",0.5'
        self.assertEqual(parse_rfc4180_line(line2), ["123", "USD,EUR", "US", "Retail Sales m/m", "0.5"])

        line3 = '123,"US ""Core"" Retail",0.5'
        self.assertEqual(parse_rfc4180_line(line3), ["123", 'US "Core" Retail', "0.5"])

    def test_calendar_schema_validation(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write("col1,col2,col3\n1,2,3\n")

        try:
            with self.assertRaises(ValueError) as ctx:
                list(stream_calendar_releases(tmp_path))
            self.assertIn("Calendar schema mismatch", str(ctx.exception))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_calendar_valid_streaming(self):
        row = [""] * 36
        row[0] = "840020010"
        row[1] = "100"
        row[2] = "1500000000"
        row[3] = "USD"
        row[4] = "US"
        row[5] = "Retail Sales m/m"
        row[6] = "high"
        row[7] = "0.4"
        row[8] = "0.2"
        row[9] = "-0.1"
        row[11] = "1497139200"
        row[12] = "0"
        row[16] = "840"
        row[24] = "1"
        row[28] = "400000"
        row[29] = "200000"
        row[30] = "-100000"

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
        # Synthetic candle CSV where remaining columns contain invalid price garbage.
        # A genuine timestamp-only reader should only inspect the first field and not error.
        content = (
            "time,open,high,low,close,tick_volume,spread,real_volume\n"
            "1672524000,INVALID_PRICE,CORRUPT,999,NaN,FOO,BAR,BAZ\n"
            "1672527600,ANOTHER_GARBAGE,CORRUPT,999,NaN,FOO,BAR,BAZ\n"
            "1672531200,SPLIT_BOUNDARY,CORRUPT,999,NaN,FOO,BAR,BAZ\n"
            "1672534800,POST_SPLIT,CORRUPT,999,NaN,FOO,BAR,BAZ\n"
        )

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            timestamps = list(stream_candle_timestamps_only(tmp_path, split_timestamp=SPLIT_TIMESTAMP))
            self.assertEqual(timestamps, [1672524000, 1672527600])
            self.assertNotIn(1672531200, timestamps)
            self.assertNotIn(1672534800, timestamps)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_candle_timestamp_reader_malformed_timestamp(self):
        content = (
            "time,open,high,low,close\n"
            "NOT_A_TIMESTAMP,1.0,1.1,0.9,1.0\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            with self.assertRaises(ValueError) as ctx:
                list(stream_candle_timestamps_only(tmp_path, split_timestamp=SPLIT_TIMESTAMP))
            self.assertIn("Malformed timestamp field", str(ctx.exception))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
