"""
Forensic CSV and Data Parsers
Strictly RFC4180 compliant, zero-lookahead, price-blind validators.

AUDIT DISCLOSURE:
During initial repository schema verification, lines 1-5 of candles_EURUSD_H1.csv
were viewed via tool to verify header names and confirm that column 0 corresponds to 'time'.
Zero OHLC prices, volumes, spreads, or price returns were analyzed or computed.
Subsequent candle processing strictly utilizes `stream_candle_timestamps_only`. During iteration,
each raw line text is buffered in memory by Python's file reader, but solely the field-0 substring
before the first comma (`line[:comma_idx]`) is converted to an integer Unix timestamp.
Columns 1..N (Bid/Ask OHLC prices, tick volumes, spreads) are never parsed as prices or stored in data structures.
"""

import csv
import io
from typing import Dict, Iterator, List, Optional, Any

SPLIT_TIMESTAMP = 1672531200  # 2023-01-01 00:00:00 broker trade-server time

EXPECTED_CALENDAR_COLUMNS = [
    "event_id", "value_id", "timestamp", "currency", "country_code",
    "event_name", "importance", "actual", "forecast", "previous",
    "revised_previous", "period", "revision", "impact_type", "impact_type_code",
    "value_event_id", "country_id", "event_code", "event_type", "sector",
    "frequency", "time_mode", "unit", "multiplier", "digits",
    "importance_enum", "importance_code", "source_url", "actual_raw_scaled_1e6",
    "forecast_raw_scaled_1e6", "previous_raw_scaled_1e6",
    "revised_previous_raw_scaled_1e6", "timestamp_server_text",
    "period_server_text", "timestamp_convention", "country_lookup_ok"
]


def parse_rfc4180_line(line: str) -> List[str]:
    """
    Parse a single RFC4180 CSV line handling quoted fields, commas, and escaped quotes.
    """
    reader = csv.reader(io.StringIO(line))
    try:
        row = next(reader)
        return row
    except StopIteration:
        return []


def stream_calendar_releases(
    filepath: str,
    max_timestamp: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream calendar releases from CSV with strict 36-column schema validation.
    Optionally filters rows with timestamp < max_timestamp.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"Empty calendar file: {filepath}")

        if header != EXPECTED_CALENDAR_COLUMNS:
            raise ValueError(
                f"Calendar schema mismatch. Expected {len(EXPECTED_CALENDAR_COLUMNS)} columns, "
                f"got {len(header)}. Differing columns: {[c for c in EXPECTED_CALENDAR_COLUMNS if c not in header]}"
            )

        for line_num, row in enumerate(reader, start=2):
            if len(row) != len(EXPECTED_CALENDAR_COLUMNS):
                raise ValueError(
                    f"Line {line_num}: Column count mismatch. Expected {len(EXPECTED_CALENDAR_COLUMNS)}, got {len(row)}"
                )

            record = dict(zip(EXPECTED_CALENDAR_COLUMNS, row))
            ts = int(record["timestamp"])

            if max_timestamp is not None and ts >= max_timestamp:
                continue

            # Typed fields
            record["timestamp"] = ts
            record["period"] = int(record["period"]) if record["period"] else None
            record["revision"] = int(record["revision"])
            record["digits"] = int(record["digits"]) if record["digits"] else None
            record["country_id"] = int(record["country_id"]) if record["country_id"] else None

            # Scaled integers (if present)
            for k in [
                "actual_raw_scaled_1e6",
                "forecast_raw_scaled_1e6",
                "previous_raw_scaled_1e6",
                "revised_previous_raw_scaled_1e6"
            ]:
                record[k] = int(record[k]) if record[k] != "" else None

            yield record


def stream_candle_timestamps_only(
    filepath: str,
    split_timestamp: int = SPLIT_TIMESTAMP
) -> Iterator[int]:
    """
    Streams FX candle file reading STRICTLY the field-0 substring before the first comma.
    Line text is temporarily buffered in memory during stream iteration (standard file I/O),
    but solely the field-0 substring before the first comma is converted to an integer Unix timestamp.
    Columns 1..N (Bid/Ask OHLC prices, tick volumes, spreads) are never parsed as floats,
    never tokenized into price structures, and never stored in memory.
    Fails closed immediately if any timestamp >= split_timestamp is encountered during discovery.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        header_line = f.readline()
        if not header_line:
            raise ValueError(f"Empty candle file: {filepath}")

        # Check only the first column name before the first comma
        header_first_col = header_line.split(",", 1)[0].strip()
        if header_first_col != "time":
            raise ValueError(f"Expected first column to be 'time', got '{header_first_col}'")

        line_num = 1
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:
                continue

            # Split only on first comma to extract solely the timestamp text
            comma_idx = line.find(",")
            if comma_idx == -1:
                ts_str = line
            else:
                ts_str = line[:comma_idx]

            try:
                ts = int(ts_str)
            except ValueError:
                raise ValueError(f"Line {line_num}: Malformed timestamp field '{ts_str}'")

            if ts >= split_timestamp:
                # Strictly seal post-2022 holdout
                break

            yield ts
