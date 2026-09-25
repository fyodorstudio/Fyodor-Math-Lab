/**
 * EURUSD H1 to H4 Candle Aggregator and Path Price Resolver.
 * Governed strictly by docs/FMS_PILOT_IFO_PROTOCOL.md (Sections 5.1 & 5.4).
 *
 * Enforces:
 * 1. H4 bars aggregated strictly from all four constituent H1 candles [T, T+3600, T+7200, T+10800].
 * 2. Next-H4 Bid-bar Open proxy for entry: P_entry = Open(T_entry).
 * 3. Bid-bar Close proxy of Nth completed active bar for exit: P_exit = Close(B_{N-1}).
 * 4. Fails closed on missing interior candles, incomplete blocks, or any timestamp >= 1672531200.
 * 5. Explicitly notes that Bid OHLC values are reproducible proxies, not guaranteed execution fills.
 */

import fs from 'fs';
import readline from 'readline';
import crypto from 'crypto';
import { CandleH1, CandleH4, Pre2023CandlesManifest } from './ifoPilotAnalysisTypes.js';
import { SPLIT_TIMESTAMP } from './fmsInventoryTypes.js';
import { parseCSVLine } from '../data/csvReader.js';

export interface LoadedPre2023Candles {
  candleMap: Map<number, CandleH1>;
  manifest: Pre2023CandlesManifest;
}

/**
 * Aggregates a single completed H4 bar from 4 consecutive H1 candles in the provided map.
 * Fails closed if any of the 4 H1 candles is missing or invalid.
 */
export function aggregateH4Bar(
  h1Map: Map<number, CandleH1>,
  blockStartTs: number,
  splitTimestamp: number = SPLIT_TIMESTAMP
): CandleH4 {
  if (blockStartTs % 14400 !== 0) {
    throw new Error(`Block start timestamp ${blockStartTs} is not on an H4 boundary (mod 14400 != 0)`);
  }

  const h1Offsets = [0, 3600, 7200, 10800];
  const candles: CandleH1[] = [];

  for (const offset of h1Offsets) {
    const ts = blockStartTs + offset;
    if (ts >= splitTimestamp) {
      throw new Error(
        `Pre-2023 violation: H1 candle timestamp ${ts} is at or beyond the split boundary ${splitTimestamp}`
      );
    }
    const c = h1Map.get(ts);
    if (!c) {
      throw new Error(
        `Incomplete H4 block: missing constituent H1 candle at ${ts} for block starting at ${blockStartTs}`
      );
    }
    if (
      !Number.isFinite(c.open) ||
      !Number.isFinite(c.high) ||
      !Number.isFinite(c.low) ||
      !Number.isFinite(c.close) ||
      c.open <= 0 ||
      c.high <= 0 ||
      c.low <= 0 ||
      c.close <= 0 ||
      c.low > c.high ||
      c.open > c.high ||
      c.open < c.low ||
      c.close > c.high ||
      c.close < c.low
    ) {
      throw new Error(
        `Contradictory or corrupt candle prices at timestamp ${ts}: O=${c.open}, H=${c.high}, L=${c.low}, C=${c.close}`
      );
    }
    candles.push(c);
  }

  const open = candles[0].open;
  const high = Math.max(candles[0].high, candles[1].high, candles[2].high, candles[3].high);
  const low = Math.min(candles[0].low, candles[1].low, candles[2].low, candles[3].low);
  const close = candles[3].close;

  return {
    timestamp: blockStartTs,
    open,
    high,
    low,
    close,
  };
}

/**
 * Resolves all H4 candles along a validated sequence of completed active bar start timestamps.
 */
export function resolveH4Sequence(
  h1Map: Map<number, CandleH1>,
  barTimestamps: number[],
  splitTimestamp: number = SPLIT_TIMESTAMP
): CandleH4[] {
  return barTimestamps.map(barTs => aggregateH4Bar(h1Map, barTs, splitTimestamp));
}

/**
 * Loads EURUSD H1 candles from a CSV file strictly up to splitTimestamp.
 * Fails closed if any candle on or after splitTimestamp is read.
 */
export async function loadPre2023H1Candles(
  csvPath: string,
  splitTimestamp: number = SPLIT_TIMESTAMP
): Promise<LoadedPre2023Candles> {
  if (!fs.existsSync(csvPath)) {
    throw new Error(`Candle file missing at ${csvPath}`);
  }

  const candleMap = new Map<number, CandleH1>();
  const fileStream = fs.createReadStream(csvPath);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let headerSeen = false;
  let tsIdx = -1;
  let oIdx = -1;
  let hIdx = -1;
  let lIdx = -1;
  let cIdx = -1;
  let completeIdx = -1;
  let lastTimestamp: number | null = null;
  let lineNumber = 0;

  let rowCount = 0;
  let firstTimestamp: number | null = null;
  let lastTimestampConsumed: number | null = null;
  const dataHash = crypto.createHash('sha256');
  const streamHash = crypto.createHash('sha256');

  try {
    for await (const line of rl) {
      lineNumber++;
      const trimmed = line.trim();
      if (!trimmed) continue;
      const parts = parseCSVLine(trimmed);

      if (!headerSeen) {
        headerSeen = true;
        streamHash.update(trimmed + '\n');
        // Pinned MT5 schema has time in column 0; fail closed if header violates expected schema
        tsIdx = parts.indexOf('time');
        if (tsIdx === -1) {
          tsIdx = parts.indexOf('timestamp');
        }
        if (tsIdx !== 0) {
          throw new Error(
            `Invalid candle CSV header format at ${csvPath}: expected timestamp column ('time') at index 0, got ${tsIdx}`
          );
        }
        oIdx = parts.indexOf('open');
        hIdx = parts.indexOf('high');
        lIdx = parts.indexOf('low');
        cIdx = parts.indexOf('close');
        completeIdx = parts.indexOf('complete_at_export');

        if (oIdx === -1 || hIdx === -1 || lIdx === -1 || cIdx === -1) {
          throw new Error(
            `Invalid candle CSV header format at ${csvPath}: missing required OHLC column`
          );
        }
        continue;
      }

      // 1. Extract and validate timestamp from column 0 before checking OHLC columns or parsing prices
      const tsRaw = parts[tsIdx]?.trim();
      if (!tsRaw || !/^\d+$/.test(tsRaw)) {
        throw new Error(`Malformed timestamp '${tsRaw}' at line ${lineNumber} in ${csvPath}`);
      }

      const ts = Number(tsRaw);
      if (!Number.isSafeInteger(ts) || ts <= 0) {
        throw new Error(`Invalid non-positive or non-integer timestamp ${ts} at line ${lineNumber} in ${csvPath}`);
      }

      // 2. Monotonicity and duplicate detection
      if (lastTimestamp !== null) {
        if (ts === lastTimestamp) {
          throw new Error(`Duplicate candle timestamp detected at ${ts} (line ${lineNumber} in ${csvPath})`);
        }
        if (ts < lastTimestamp) {
          throw new Error(
            `Non-monotone candle timestamp sequence: ${ts} followed prior timestamp ${lastTimestamp} (line ${lineNumber} in ${csvPath})`
          );
        }
      }
      lastTimestamp = ts;

      // 3. Strict fail-closed split check: halt immediately at or after split boundary.
      // Crucially: OHLC price columns are NOT checked, parsed, converted, or hashed for boundary or post-split rows.
      if (ts >= splitTimestamp) {
        break;
      }

      // 4. PRE-split row validation: validate required OHLC column count
      const minCols = Math.max(tsIdx, oIdx, hIdx, lIdx, cIdx, completeIdx) + 1;
      if (parts.length < minCols) {
        throw new Error(
          `Malformed CSV row at line ${lineNumber} in ${csvPath}: expected at least ${minCols} columns, got ${parts.length}`
        );
      }

      // Incomplete candle check (if complete_at_export column exists in schema)
      if (completeIdx !== -1) {
        const compVal = parts[completeIdx]?.trim().toLowerCase();
        if (compVal !== 'true') {
          throw new Error(
            `Incomplete candle at export at timestamp ${ts} (line ${lineNumber}): complete_at_export='${parts[completeIdx]}'`
          );
        }
      }

      // Parse and validate OHLC prices
      const oRaw = parts[oIdx]?.trim();
      const hRaw = parts[hIdx]?.trim();
      const lRaw = parts[lIdx]?.trim();
      const cRaw = parts[cIdx]?.trim();

      if (!oRaw || !hRaw || !lRaw || !cRaw) {
        throw new Error(`Missing price value at timestamp ${ts} (line ${lineNumber} in ${csvPath})`);
      }

      const open = Number(oRaw);
      const high = Number(hRaw);
      const low = Number(lRaw);
      const close = Number(cRaw);

      if (
        !Number.isFinite(open) ||
        !Number.isFinite(high) ||
        !Number.isFinite(low) ||
        !Number.isFinite(close)
      ) {
        throw new Error(
          `Non-finite price detected at timestamp ${ts} (line ${lineNumber}): O=${open}, H=${high}, L=${low}, C=${close}`
        );
      }

      if (open <= 0 || high <= 0 || low <= 0 || close <= 0) {
        throw new Error(
          `Non-positive price detected at timestamp ${ts} (line ${lineNumber}): O=${open}, H=${high}, L=${low}, C=${close}`
        );
      }

      // Contradictory OHLC (open or close outside high-low, or low > high)
      if (high < low || open > high || open < low || close > high || close < low) {
        throw new Error(
          `Contradictory OHLC prices at timestamp ${ts} (line ${lineNumber}): open=${open}, high=${high}, low=${low}, close=${close}`
        );
      }

      if (candleMap.has(ts)) {
        throw new Error(`Duplicate candle timestamp detected in map at ${ts}`);
      }

      candleMap.set(ts, { timestamp: ts, open, high, low, close });

      rowCount++;
      if (firstTimestamp === null) {
        firstTimestamp = ts;
      }
      lastTimestampConsumed = ts;
      dataHash.update(trimmed + '\n');
      streamHash.update(trimmed + '\n');
    }
  } finally {
    rl.close();
    fileStream.destroy();
    if (!fileStream.closed) {
      await new Promise<void>(resolve => fileStream.once('close', () => resolve()));
    }
  }

  const manifest: Pre2023CandlesManifest = {
    rowCount,
    firstTimestamp,
    lastTimestamp: lastTimestampConsumed,
    sha256: dataHash.digest('hex'),
    sha256WithHeader: streamHash.digest('hex'),
  };

  return { candleMap, manifest };
}
