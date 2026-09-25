import fs from 'fs';
import path from 'path';
import readline from 'readline';
import { parseCSVLine } from '../data/csvReader.js';
import { loadCandleTimestampsOnly, classifyGap } from './fmsInventoryEngine.js';
import { SPLIT_TIMESTAMP } from './fmsInventoryTypes.js';
import { IfoPackageRecord } from './ifoPilotLedgerTypes.js';

export type ControlCandidateChoice = 'D_MINUS_7' | 'D_PLUS_7' | 'D_MINUS_14' | 'D_PLUS_14';

export interface IfoControlRecord {
  eventIndex: number;
  eventTimestamp: number;
  eventBrokerDateTime: string;
  eventEntryTimestamp: number;
  eventDirection: 'LONG' | 'SHORT';
  status: 'PAIRED' | 'CONTROL_UNAVAILABLE';
  controlCandidateChoice: ControlCandidateChoice | null;
  controlEntryTimestamp: number | null;
  controlExitTimestamp: number | null;
  rejectionReasons: Record<ControlCandidateChoice, string | null>;
}

export interface IfoControlAuditResult {
  totalEventEpisodes: number;
  horizonBars: number;
  pairedCount: number;
  unavailableCount: number;
  duplicateControlCount: number;
  fallbackDistribution: {
    dMinus7: number;
    dPlus7: number;
    dMinus14: number;
    dPlus14: number;
    unavailable: number;
  };
  records: IfoControlRecord[];
}

export interface AuditIfoControlsOptions {
  repoRoot?: string;
  actionableRows: IfoPackageRecord[];
  horizonBars?: 6 | 12;
  disallowDuplicates?: boolean;
}

/**
 * Verifies that a path of `numBars` H4 blocks starting at `entryTs` is physically valid:
 * 1. entryTs must be on an H4 boundary (entryTs % 14400 === 0).
 * 2. Every completed H4 block must contain all four consecutive H1 candles:
 *    [blockStart, blockStart + 3600, blockStart + 7200, blockStart + 10800].
 * 3. Skipped blocks are permitted ONLY when every missing hour between blocks is a
 *    Saturday/Sunday broker-clock hour (PURE_WEEKEND closure).
 * 4. Fails closed on any partial block, missing interior H1 candle, or weekday gap.
 * 5. Returns the exit timestamp (close of the final completed H4 bar) and list of bar starts.
 */
export function verifyH4Path(
  entryTs: number,
  numBars: number,
  h1Set: Set<number>,
  splitTimestamp: number = SPLIT_TIMESTAMP
): { complete: boolean; exitTs: number; reason: string | null; bars: number[] } {
  if (entryTs % 14400 !== 0) {
    return { complete: false, exitTs: 0, reason: `Entry timestamp ${entryTs} not on H4 boundary`, bars: [] };
  }

  // Verify first block (block 0) has all 4 H1 candles
  for (let offset = 0; offset < 14400; offset += 3600) {
    if (!h1Set.has(entryTs + offset)) {
      return {
        complete: false,
        exitTs: 0,
        reason: `Missing H1 candle at ${entryTs + offset} in initial H4 block starting at ${entryTs}`,
        bars: [],
      };
    }
  }

  const selectedBars: number[] = [entryTs];
  let currBlockStart = entryTs;

  while (selectedBars.length < numBars) {
    const prevBlockEnd = currBlockStart + 14400; // Close of previous H4 block
    const nextCandidate = prevBlockEnd;

    // Count how many H1 candles of the candidate contiguous block are present
    const presentCount = [0, 3600, 7200, 10800].filter(off => h1Set.has(nextCandidate + off)).length;

    if (presentCount === 4) {
      selectedBars.push(nextCandidate);
      currBlockStart = nextCandidate;
    } else if (presentCount > 0) {
      // Partially present block (e.g. 1, 2, or 3 candles present, missing interior candles)
      return {
        complete: false,
        exitTs: 0,
        reason: `Partial block: missing interior H1 candle in H4 block starting at ${nextCandidate} (${presentCount}/4 candles present)`,
        bars: [],
      };
    } else {
      // presentCount === 0: Entire 4-hour block was skipped; search forward for resumed active trading
      let nextActiveH1: number | null = null;
      for (let t = prevBlockEnd; t < prevBlockEnd + 80 * 3600; t += 3600) {
        if (h1Set.has(t)) {
          nextActiveH1 = t;
          break;
        }
      }

      if (!nextActiveH1) {
        return {
          complete: false,
          exitTs: 0,
          reason: `No subsequent active H1 candles found after H4 block at ${currBlockStart}`,
          bars: [],
        };
      }

      // Next active block must begin on a clean H4 boundary
      if (nextActiveH1 % 14400 !== 0) {
        return {
          complete: false,
          exitTs: 0,
          reason: `Next active H1 candle at ${nextActiveH1} does not align with H4 boundary`,
          bars: [],
        };
      }

      // Classify the gap between the last H1 candle of the previous block and nextActiveH1
      const lastH1OfPrev = currBlockStart + 10800;
      const gapInfo = classifyGap(lastH1OfPrev, nextActiveH1);
      if (gapInfo.classification !== 'PURE_WEEKEND') {
        return {
          complete: false,
          exitTs: 0,
          reason: `Weekday gap of ${gapInfo.missingHours}h detected between ${lastH1OfPrev} and ${nextActiveH1}`,
          bars: [],
        };
      }

      // Verify nextActiveH1 block has all four H1 candles
      const hasAll4Resumed = [0, 3600, 7200, 10800].every(off => h1Set.has(nextActiveH1! + off));
      if (!hasAll4Resumed) {
        return {
          complete: false,
          exitTs: 0,
          reason: `Partial block: missing interior H1 candle in resumed H4 block at ${nextActiveH1}`,
          bars: [],
        };
      }

      selectedBars.push(nextActiveH1);
      currBlockStart = nextActiveH1;
    }
  }

  const lastBar = selectedBars[numBars - 1];
  const exitTs = lastBar + 14400; // Close of the numBars-th completed active H4 bar

  if (exitTs > splitTimestamp) {
    return {
      complete: false,
      exitTs: 0,
      reason: `Exit timestamp ${exitTs} exceeds pre-2023 split boundary (${splitTimestamp})`,
      bars: [],
    };
  }

  return { complete: true, exitTs, reason: null, bars: selectedBars };
}

/**
 * Conducts a strictly PRICE-BLIND matched-control availability audit for the
 * 40 actionable German Ifo EURUSD episodes.
 *
 * Checks physical H4 candle timestamp availability (all 4 H1 candles per block)
 * and calendar release disqualifications WITHOUT reading, parsing, or loading OHLC prices or returns.
 */
export async function auditIfoControls(
  options: AuditIfoControlsOptions
): Promise<IfoControlAuditResult> {
  const root = options.repoRoot || path.resolve(__dirname, '../../../');
  const horizonBars = options.horizonBars || 6;
  const disallowDuplicates = options.disallowDuplicates || false;

  const candlePath = path.join(
    root,
    'tools/mt5/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv'
  );
  const calPath = path.join(
    root,
    'tools/mt5/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv'
  );

  if (!fs.existsSync(candlePath)) {
    throw new Error(`Candle file missing at ${candlePath}`);
  }
  if (!fs.existsSync(calPath)) {
    throw new Error(`Calendar file missing at ${calPath}`);
  }

  // 1. Load EURUSD H1 timestamps ONLY
  const h1Times = await loadCandleTimestampsOnly(candlePath);
  const h1Set = new Set(h1Times.filter(ts => ts < SPLIT_TIMESTAMP));

  // 2. Load Calendar releases
  interface CalRelease {
    eventId: string;
    timestamp: number;
    currency: string;
    countryCode: string;
    eventName: string;
    importance: string;
  }
  const releases: CalRelease[] = [];
  const calStream = fs.createReadStream(calPath, { encoding: 'utf-8' });
  const rlCal = readline.createInterface({ input: calStream, crlfDelay: Infinity });
  let lineIdx = 0;
  for await (const line of rlCal) {
    lineIdx++;
    if (lineIdx === 1 || !line.trim()) continue;
    const parts = parseCSVLine(line);
    const ts = parseInt(parts[2]?.trim(), 10);
    if (ts >= SPLIT_TIMESTAMP) continue;
    releases.push({
      eventId: parts[0]?.trim() || '',
      timestamp: ts,
      currency: parts[3]?.trim() || '',
      countryCode: parts[4]?.trim() || '',
      eventName: parts[5]?.trim() || '',
      importance: parts[6]?.trim().toLowerCase() || '',
    });
  }

  const records: IfoControlRecord[] = [];
  const usedControlTimestamps = new Set<number>();
  let duplicateCount = 0;

  const fallbackDistribution = {
    dMinus7: 0,
    dPlus7: 0,
    dMinus14: 0,
    dPlus14: 0,
    unavailable: 0,
  };

  const candidateDefs: Array<{ choice: ControlCandidateChoice; dayOffset: number }> = [
    { choice: 'D_MINUS_7', dayOffset: -7 },
    { choice: 'D_PLUS_7', dayOffset: 7 },
    { choice: 'D_MINUS_14', dayOffset: -14 },
    { choice: 'D_PLUS_14', dayOffset: 14 },
  ];

  for (let i = 0; i < options.actionableRows.length; i++) {
    const act = options.actionableRows[i];
    const eventEntryTs = act.pairCoverage.entryTimestamp!;
    const eventRelTs = act.timestamp;

    let chosenChoice: ControlCandidateChoice | null = null;
    let chosenEntryTs: number | null = null;
    let chosenExitTs: number | null = null;
    const rejectionReasons: Record<ControlCandidateChoice, string | null> = {
      D_MINUS_7: null,
      D_PLUS_7: null,
      D_MINUS_14: null,
      D_PLUS_14: null,
    };

    for (const cand of candidateDefs) {
      const candEntryTs = eventEntryTs + cand.dayOffset * 86400;
      const candRelTs = eventRelTs + cand.dayOffset * 86400;

      // Duplicate check if duplicates are disallowed
      if (disallowDuplicates && usedControlTimestamps.has(candEntryTs)) {
        rejectionReasons[cand.choice] = `Control timestamp ${candEntryTs} already claimed by an earlier episode`;
        continue;
      }

      // 1. Physical path check across all horizonBars (requires all 4 H1 candles per H4 block)
      const pathInfo = verifyH4Path(candEntryTs, horizonBars, h1Set);
      if (!pathInfo.complete) {
        rejectionReasons[cand.choice] = pathInfo.reason;
        continue;
      }

      // 2. Calendar disqualification check across [candRelTs, pathInfo.exitTs]:
      // Disqualify if any High-Importance EUR release occurs in the holding window
      const conflicts = releases.filter(r => {
        if (r.timestamp < candRelTs || r.timestamp > pathInfo.exitTs) return false;
        return (
          r.currency === 'EUR' &&
          (r.importance === 'high' || r.eventId === '276030003' || r.eventId === '276030001')
        );
      });

      if (conflicts.length > 0) {
        rejectionReasons[cand.choice] = `High-importance EUR release conflict: ${conflicts
          .map(c => `${c.eventName}@${c.timestamp}`)
          .join(', ')}`;
        continue;
      }

      // Candidate is valid
      chosenChoice = cand.choice;
      chosenEntryTs = candEntryTs;
      chosenExitTs = pathInfo.exitTs;
      break;
    }

    if (chosenChoice && chosenEntryTs) {
      if (chosenChoice === 'D_MINUS_7') fallbackDistribution.dMinus7++;
      else if (chosenChoice === 'D_PLUS_7') fallbackDistribution.dPlus7++;
      else if (chosenChoice === 'D_MINUS_14') fallbackDistribution.dMinus14++;
      else if (chosenChoice === 'D_PLUS_14') fallbackDistribution.dPlus14++;

      if (usedControlTimestamps.has(chosenEntryTs)) {
        duplicateCount++;
      }
      usedControlTimestamps.add(chosenEntryTs);

      records.push({
        eventIndex: i + 1,
        eventTimestamp: act.timestamp,
        eventBrokerDateTime: act.brokerDateTime,
        eventEntryTimestamp: eventEntryTs,
        eventDirection: act.actionableDirection!,
        status: 'PAIRED',
        controlCandidateChoice: chosenChoice,
        controlEntryTimestamp: chosenEntryTs,
        controlExitTimestamp: chosenExitTs,
        rejectionReasons,
      });
    } else {
      fallbackDistribution.unavailable++;
      records.push({
        eventIndex: i + 1,
        eventTimestamp: act.timestamp,
        eventBrokerDateTime: act.brokerDateTime,
        eventEntryTimestamp: eventEntryTs,
        eventDirection: act.actionableDirection!,
        status: 'CONTROL_UNAVAILABLE',
        controlCandidateChoice: null,
        controlEntryTimestamp: null,
        controlExitTimestamp: null,
        rejectionReasons,
      });
    }
  }

  const pairedCount = records.filter(r => r.status === 'PAIRED').length;
  const unavailableCount = records.filter(r => r.status === 'CONTROL_UNAVAILABLE').length;

  return {
    totalEventEpisodes: options.actionableRows.length,
    horizonBars,
    pairedCount,
    unavailableCount,
    duplicateControlCount: duplicateCount,
    fallbackDistribution,
    records,
  };
}
