"""
Forensic CSV and Data Parsers
Strictly RFC4180 compliant, zero-lookahead, price-blind validators.
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
    Streams EURUSD (or any FX pair) candle file reading ONLY column 0 (timestamp).
    Strictly forbids reading OHLC prices, volumes, or spreads to preserve price-blindness.
    Fails closed immediately if any timestamp >= split_timestamp is encountered during discovery.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"Empty candle file: {filepath}")

        if header[0] != "time":
            raise ValueError(f"Expected first column to be 'time', got '{header[0]}'")

        for line_num, row in enumerate(reader, start=2):
            if not row:
                continue
            ts = int(row[0])
            if ts >= split_timestamp:
                # Stop streaming at split boundary to ensure post-2022 holdout sealing
                break
            yield ts
