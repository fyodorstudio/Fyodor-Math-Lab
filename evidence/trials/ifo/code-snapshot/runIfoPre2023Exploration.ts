/**
 * German Ifo Pre-2023 Outcome Analysis Runner (Milestone 4 Exploration).
 * Governed strictly by docs/FMS_PILOT_IFO_PROTOCOL.md (v1.2 FROZEN).
 *
 * DO NOT RUN WITHOUT EXPLICIT CODEX AUDIT AUTHORIZATION.
 *
 * Enforces:
 * 1. Cryptographic hash verification of all inputs via streaming SHA-256.
 * 2. Strictly reads EURUSD H1 candles up to splitTimestamp (1672531200 = 2023-01-01 00:00:00).
 * 3. Fails closed on any candle >= 1672531200, missing interior candles, or incomplete blocks.
 * 4. Uses fixed 40 actionable events, 39 primary 6-H4 pairs, and strict 34 secondary 12-H4 pairs.
 * 5. Uses seeded Mulberry32 (seed 20260925, B=100,000 draws) for one-sided paired sign-flip test.
 * 6. Generates auditable JSON and Markdown exploration reports.
 * 7. Guarded CLI requiring explicit execution confirmation flag.
 */

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import readline from 'readline';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { loadPre2023H1Candles, resolveH4Sequence } from './ifoCandleAggregator.js';
import { auditIfoControls, verifyH4Path } from './ifoControlAudit.js';
import {
  evaluateEvent,
  evaluateControl,
  pairObservations,
  summarizeHorizon,
  evaluateDecisionRules,
  generateIfoExplorationMarkdownReport,
} from './ifoExplorationEngine.js';
import { computeHolmAdjustedPValues } from './ifoPermutationEngine.js';
import {
  IfoEvaluatedEpisode,
  IfoEvaluatedControl,
  IfoPairedObservation,
  IfoPilotExplorationReportData,
  ImplementationManifest,
} from './ifoPilotAnalysisTypes.js';
import { IfoPilotLedgerArtifact } from './ifoPilotLedgerTypes.js';
import { SPLIT_TIMESTAMP } from './fmsInventoryTypes.js';
import { parseCSVLine } from '../data/csvReader.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Pinned hashes from protocol v1.2 FROZEN
export const PINNED_HASHES = {
  rawCalendar: '76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e',
  episodesJsonl: '37df7880a2bc36dbbce06b4a6ba39f7bd962a4c1c92eb2ce64cb71a886de55d2',
  pilotLedgerJson: '324b99a1f2ac9ebe73b5102d35208cc32a7e2eb7eb9cc69480b3feae710ff658',
  pilotLedgerMd: 'e2e3a6c19bbfadfd1bef151861bcba3a3e5066836e3dfc28835e28a616ef72c8',
};

/**
 * Computes SHA-256 hash of a file via asynchronous streaming to avoid large heap allocations.
 */
export async function computeFileSha256(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(filePath)) {
      return reject(new Error(`File not found for hash calculation: ${filePath}`));
    }
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath);
    stream.on('data', chunk => hash.update(chunk));
    stream.on('end', () => resolve(hash.digest('hex')));
    stream.on('error', err => reject(err));
  });
}

/**
 * Loads calendar USD release timestamps to evaluate 15:30 morning release exposure.
 * Strictly restricts to timestamps before splitTimestamp (1672531200).
 */
export async function loadUsdReleaseTimestamps(
  calendarCsvPath: string,
  splitTimestamp: number = SPLIT_TIMESTAMP
): Promise<Set<number>> {
  const usdTimestamps = new Set<number>();
  const stream = fs.createReadStream(calendarCsvPath, { encoding: 'utf8' });
  const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });

  let lineCount = 0;
  for await (const line of rl) {
    lineCount++;
    if (lineCount === 1 || !line.trim()) continue;
    const parts = parseCSVLine(line);
    // Currency is in column index 3, timestamp in column index 2
    if (parts[3]?.trim() === 'USD') {
      const ts = parseInt(parts[2]?.trim(), 10);
      if (!isNaN(ts) && ts > 0 && ts < splitTimestamp) {
        usdTimestamps.add(ts);
      }
    }
  }

  return usdTimestamps;
}

export const IMPLEMENTATION_SOURCE_FILES = [
  'lab/src/research/ifoCandleAggregator.ts',
  'lab/src/research/ifoControlAudit.ts',
  'lab/src/research/ifoExplorationEngine.ts',
  'lab/src/research/ifoPermutationEngine.ts',
  'lab/src/research/ifoPilotAnalysisTypes.ts',
  'lab/src/research/runIfoPre2023Exploration.ts',
];

/**
 * Computes an immutable implementation identifier containing git commit ID
 * (if available in git repo) and SHA-256 hashes of all relevant research engine source files.
 */
export function getImplementationManifest(repoRoot?: string): ImplementationManifest {
  const root =
    repoRoot && fs.existsSync(path.join(repoRoot, 'lab/src/research'))
      ? repoRoot
      : path.resolve(__dirname, '../../../');

  const sourceFilesSha256: Record<string, string> = {};
  for (const relPath of IMPLEMENTATION_SOURCE_FILES) {
    const fullPath = path.join(root, relPath);
    if (fs.existsSync(fullPath)) {
      const content = fs.readFileSync(fullPath);
      sourceFilesSha256[relPath] = crypto.createHash('sha256').update(content).digest('hex');
    }
  }

  let gitCommit: string | null = null;
  try {
    gitCommit = execSync('git rev-parse HEAD', { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString()
      .trim();
  } catch {
    gitCommit = null;
  }

  return {
    gitCommit,
    sourceFilesSha256,
  };
}

export async function runIfoPre2023Exploration(options: {
  repoRoot?: string;
  outputPathJson?: string;
  outputPathMd?: string;
} = {}): Promise<IfoPilotExplorationReportData> {
  const root = options.repoRoot || path.resolve(__dirname, '../../../');

  const calPath = path.join(
    root,
    'tools/mt5/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv'
  );
  const epsPath = path.join(root, 'lab/research/fms_episodes.jsonl');
  const ledgerJsonPath = path.join(root, 'lab/research/ifo_pilot_ledger.json');
  const ledgerMdPath = path.join(root, 'lab/research/ifo_pilot_ledger.md');
  const candlesH1Path = path.join(
    root,
    'tools/mt5/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv'
  );

  // 1. Verify provenance hashes of pinned artifacts via streaming BEFORE any price load
  const calHash = await computeFileSha256(calPath);
  if (calHash !== PINNED_HASHES.rawCalendar) {
    throw new Error(`Calendar SHA-256 mismatch: got ${calHash}, expected ${PINNED_HASHES.rawCalendar}`);
  }
  const epsHash = await computeFileSha256(epsPath);
  if (epsHash !== PINNED_HASHES.episodesJsonl) {
    throw new Error(`Episodes JSONL SHA-256 mismatch: got ${epsHash}, expected ${PINNED_HASHES.episodesJsonl}`);
  }
  const ledgerJsonHash = await computeFileSha256(ledgerJsonPath);
  if (ledgerJsonHash !== PINNED_HASHES.pilotLedgerJson) {
    throw new Error(`Ledger JSON SHA-256 mismatch: got ${ledgerJsonHash}, expected ${PINNED_HASHES.pilotLedgerJson}`);
  }
  const ledgerMdHash = await computeFileSha256(ledgerMdPath);
  if (ledgerMdHash !== PINNED_HASHES.pilotLedgerMd) {
    throw new Error(`Ledger MD SHA-256 mismatch: got ${ledgerMdHash}, expected ${PINNED_HASHES.pilotLedgerMd}`);
  }

  // 2. Load pinned pre-price ledger
  const ledgerArtifact: IfoPilotLedgerArtifact = JSON.parse(fs.readFileSync(ledgerJsonPath, 'utf8'));
  const actionableRows = ledgerArtifact.actionableRows;
  if (actionableRows.length !== 40) {
    throw new Error(`Expected exactly 40 actionable rows, got ${actionableRows.length}`);
  }

  // 3. Load calendar USD release timestamps for verified 15:30 morning overlap calculation (< SPLIT_TIMESTAMP)
  const usdTimestamps = await loadUsdReleaseTimestamps(calPath, SPLIT_TIMESTAMP);

  // 4. Load EURUSD H1 candles strictly up to SPLIT_TIMESTAMP (fail-closed on >= 1672531200)
  const { candleMap: h1Map, manifest: candleManifest } = await loadPre2023H1Candles(
    candlesH1Path,
    SPLIT_TIMESTAMP
  );
  const h1Timestamps = new Set(h1Map.keys());

  // 5. Run price-blind control audits
  // Primary 6-H4 audit (39 paired, 1 unavailable)
  const audit6 = await auditIfoControls({
    repoRoot: root,
    actionableRows,
    horizonBars: 6,
    disallowDuplicates: false,
  });
  if (audit6.pairedCount !== 39 || audit6.unavailableCount !== 1) {
    throw new Error(`Audit 6-H4 mismatch: paired=${audit6.pairedCount}, unavailable=${audit6.unavailableCount}`);
  }

  // Secondary 12-H4 strict audit (34 paired, 6 unavailable, disallowDuplicates: true)
  const audit12Strict = await auditIfoControls({
    repoRoot: root,
    actionableRows,
    horizonBars: 12,
    disallowDuplicates: true,
  });
  if (audit12Strict.pairedCount !== 34 || audit12Strict.unavailableCount !== 6) {
    throw new Error(
      `Audit 12-H4 strict mismatch: paired=${audit12Strict.pairedCount}, unavailable=${audit12Strict.unavailableCount}`
    );
  }

  // Secondary 12-H4 permissive audit (35 paired, 5 unavailable, disallowDuplicates: false)
  const audit12Permissive = await auditIfoControls({
    repoRoot: root,
    actionableRows,
    horizonBars: 12,
    disallowDuplicates: false,
  });
  if (audit12Permissive.pairedCount !== 35 || audit12Permissive.unavailableCount !== 5) {
    throw new Error(
      `Audit 12-H4 permissive mismatch: paired=${audit12Permissive.pairedCount}, unavailable=${audit12Permissive.unavailableCount}`
    );
  }

  // 6. Evaluate all 40 actionable event episodes
  const evaluatedEvents: IfoEvaluatedEpisode[] = [];
  for (let i = 0; i < actionableRows.length; i++) {
    const row = actionableRows[i];
    const entryTs = row.pairCoverage.entryTimestamp!;

    // Resolve 6 H4 path
    const path6 = verifyH4Path(entryTs, 6, h1Timestamps, SPLIT_TIMESTAMP);
    if (!path6.complete) {
      throw new Error(`Actionable event ${i + 1} failed 6-H4 path verification: ${path6.reason}`);
    }
    const candles6 = resolveH4Sequence(h1Map, path6.bars, SPLIT_TIMESTAMP);

    // Resolve 12 H4 path
    const path12 = verifyH4Path(entryTs, 12, h1Timestamps, SPLIT_TIMESTAMP);
    if (!path12.complete) {
      throw new Error(`Actionable event ${i + 1} failed 12-H4 path verification: ${path12.reason}`);
    }
    const candles12 = resolveH4Sequence(h1Map, path12.bars, SPLIT_TIMESTAMP);

    // Compute calendar-only 15:30 USD morning release exposure:
    // 11:30 releases enter at 12:00 (delay=30m), initial bar is 12:00-16:00. 15:30 falls inside entry bar.
    // 12:30 releases enter at 16:00 (delay=210m), 15:30 occurred prior to entry.
    let hasUs1530 = false;
    if (row.pairCoverage.entryDelayMinutes === 30) {
      const target1530 = entryTs + 12600; // 12:00 + 3.5h = 15:30
      hasUs1530 = usdTimestamps.has(target1530);
    }

    const evaluated = evaluateEvent(
      {
        packageIndex: row.packageIndex,
        actionableIndex: i + 1,
        releaseTimestamp: row.timestamp,
        brokerDateTime: row.brokerDateTime,
        direction: row.actionableDirection!,
        entryTimestamp: entryTs,
        hasCrossCurrencyCollision: row.collision.hasCrossCurrencyCollision,
        collidingCurrencies: row.collision.collidingCurrencies,
        hasUs1530MorningRelease: hasUs1530,
      },
      candles6,
      candles12
    );
    evaluatedEvents.push(evaluated);
  }

  // 7. Evaluate matched controls and create pairs for Primary 6 H4
  const pairs6: IfoPairedObservation[] = [];
  const controls6: IfoEvaluatedControl[] = [];
  for (let i = 0; i < audit6.records.length; i++) {
    const rec = audit6.records[i];
    const event = evaluatedEvents[i];

    if (rec.status === 'PAIRED') {
      const ctrlBars = verifyH4Path(rec.controlEntryTimestamp!, 6, h1Timestamps, SPLIT_TIMESTAMP);
      if (!ctrlBars.complete) {
        throw new Error(`Control 6-H4 for episode ${i + 1} failed path verification: ${ctrlBars.reason}`);
      }
      const ctrlCandles = resolveH4Sequence(h1Map, ctrlBars.bars, SPLIT_TIMESTAMP);
      const evaluatedCtrl = evaluateControl(
        {
          actionableIndex: i + 1,
          horizon: 6,
          direction: event.direction,
          controlChoice: rec.controlCandidateChoice,
          status: 'PAIRED',
        },
        ctrlCandles
      );
      controls6.push(evaluatedCtrl);
      const pair = pairObservations(event, evaluatedCtrl, 6);
      pairs6.push(pair);
    } else {
      const rejectionEntries = Object.entries(rec.rejectionReasons).filter(([_, r]) => r !== null);
      const exclusionReason =
        rejectionEntries.length > 0
          ? rejectionEntries.map(([k, r]) => `${k} rejected: ${r}`).join('; ')
          : 'All 4 candidate dates collided or failed path verification';
      const evaluatedCtrl = evaluateControl(
        {
          actionableIndex: i + 1,
          horizon: 6,
          direction: event.direction,
          controlChoice: null,
          status: 'CONTROL_UNAVAILABLE',
          exclusionReason,
        },
        null
      );
      controls6.push(evaluatedCtrl);
    }
  }

  // 8. Evaluate matched controls and create pairs for Secondary 12 H4 (Strict)
  const pairs12Strict: IfoPairedObservation[] = [];
  const controls12Strict: IfoEvaluatedControl[] = [];
  for (let i = 0; i < audit12Strict.records.length; i++) {
    const rec = audit12Strict.records[i];
    const event = evaluatedEvents[i];

    if (rec.status === 'PAIRED') {
      const ctrlBars = verifyH4Path(rec.controlEntryTimestamp!, 12, h1Timestamps, SPLIT_TIMESTAMP);
      if (!ctrlBars.complete) {
        throw new Error(`Control 12-H4 strict for episode ${i + 1} failed path verification: ${ctrlBars.reason}`);
      }
      const ctrlCandles = resolveH4Sequence(h1Map, ctrlBars.bars, SPLIT_TIMESTAMP);
      const evaluatedCtrl = evaluateControl(
        {
          actionableIndex: i + 1,
          horizon: 12,
          direction: event.direction,
          controlChoice: rec.controlCandidateChoice,
          status: 'PAIRED',
        },
        ctrlCandles
      );
      controls12Strict.push(evaluatedCtrl);
      const pair = pairObservations(event, evaluatedCtrl, 12);
      pairs12Strict.push(pair);
    } else {
      const rejectionEntries = Object.entries(rec.rejectionReasons).filter(([_, r]) => r !== null);
      const exclusionReason =
        rejectionEntries.length > 0
          ? rejectionEntries.map(([k, r]) => `${k} rejected: ${r}`).join('; ')
          : 'All 4 candidate dates collided or failed path verification';
      const evaluatedCtrl = evaluateControl(
        {
          actionableIndex: i + 1,
          horizon: 12,
          direction: event.direction,
          controlChoice: null,
          status: 'CONTROL_UNAVAILABLE',
          exclusionReason,
        },
        null
      );
      controls12Strict.push(evaluatedCtrl);
    }
  }

  // 9. Evaluate matched controls and create pairs for Secondary 12 H4 (Permissive)
  const pairs12Permissive: IfoPairedObservation[] = [];
  const controls12Permissive: IfoEvaluatedControl[] = [];
  for (let i = 0; i < audit12Permissive.records.length; i++) {
    const rec = audit12Permissive.records[i];
    const event = evaluatedEvents[i];

    if (rec.status === 'PAIRED') {
      const ctrlBars = verifyH4Path(rec.controlEntryTimestamp!, 12, h1Timestamps, SPLIT_TIMESTAMP);
      if (!ctrlBars.complete) {
        throw new Error(`Control 12-H4 permissive for episode ${i + 1} failed path verification: ${ctrlBars.reason}`);
      }
      const ctrlCandles = resolveH4Sequence(h1Map, ctrlBars.bars, SPLIT_TIMESTAMP);
      const evaluatedCtrl = evaluateControl(
        {
          actionableIndex: i + 1,
          horizon: 12,
          direction: event.direction,
          controlChoice: rec.controlCandidateChoice,
          status: 'PAIRED',
        },
        ctrlCandles
      );
      controls12Permissive.push(evaluatedCtrl);
      const pair = pairObservations(event, evaluatedCtrl, 12);
      pairs12Permissive.push(pair);
    } else {
      const rejectionEntries = Object.entries(rec.rejectionReasons).filter(([_, r]) => r !== null);
      const exclusionReason =
        rejectionEntries.length > 0
          ? rejectionEntries.map(([k, r]) => `${k} rejected: ${r}`).join('; ')
          : 'All 4 candidate dates collided or failed path verification';
      const evaluatedCtrl = evaluateControl(
        {
          actionableIndex: i + 1,
          horizon: 12,
          direction: event.direction,
          controlChoice: null,
          status: 'CONTROL_UNAVAILABLE',
          exclusionReason,
        },
        null
      );
      controls12Permissive.push(evaluatedCtrl);
    }
  }

  // 10. Summarize Horizons
  const summary6 = summarizeHorizon(6, 'Primary 6 H4 Horizon (First Trading Day)', evaluatedEvents, pairs6, 1);
  const summary12Strict = summarizeHorizon(
    12,
    'Secondary 12 H4 Horizon (Strict No-Duplicate Controls)',
    evaluatedEvents,
    pairs12Strict,
    6
  );
  const summary12Permissive = summarizeHorizon(
    12,
    'Secondary 12 H4 Horizon (Permissive Controls Sensitivity)',
    evaluatedEvents,
    pairs12Permissive,
    5
  );

  // Compute Holm-Bonferroni step-down adjusted p-values across primary and secondary horizons
  const [holmP6, holmP12Strict] = computeHolmAdjustedPValues([
    summary6.pValuePermutation,
    summary12Strict.pValuePermutation,
  ]);
  summary6.pValueHolmAdjusted = holmP6;
  summary12Strict.pValueHolmAdjusted = holmP12Strict;

  // 11. Evaluate Ordered Decision Rules
  const decision = evaluateDecisionRules(summary6);

  const implementation = getImplementationManifest(root);

  const reportData: IfoPilotExplorationReportData = {
    protocolVersion: '1.2 FROZEN',
    protocolDate: '2026-09-25',
    splitTimestamp: SPLIT_TIMESTAMP,
    evaluatedAt: new Date().toISOString(),
    implementation,
    manifest: {
      consumedPre2023H1Candles: candleManifest,
      implementation,
    },
    provenanceHashes: {
      rawCalendarSha256: calHash,
      episodesJsonlSha256: epsHash,
      pilotLedgerJsonSha256: ledgerJsonHash,
      pilotLedgerMdSha256: ledgerMdHash,
      consumedPre2023H1CandlesSha256: candleManifest.sha256,
    },
    events: evaluatedEvents,
    primary6H4: {
      summary: summary6,
      pairs: pairs6,
      controls: controls6,
    },
    secondary12H4Strict: {
      summary: summary12Strict,
      pairs: pairs12Strict,
      controls: controls12Strict,
    },
    secondary12H4Permissive: {
      summary: summary12Permissive,
      pairs: pairs12Permissive,
      controls: controls12Permissive,
    },
    decision,
  };

  // 12. Write outputs if paths provided
  if (options.outputPathJson) {
    const dir = path.dirname(path.resolve(options.outputPathJson));
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(options.outputPathJson, JSON.stringify(reportData, null, 2), 'utf8');
  }

  if (options.outputPathMd) {
    const dir = path.dirname(path.resolve(options.outputPathMd));
    fs.mkdirSync(dir, { recursive: true });
    const md = generateIfoExplorationMarkdownReport(reportData);
    fs.writeFileSync(options.outputPathMd, md, 'utf8');
  }

  return reportData;
}

// ---------------------------------------------------------------------------
// Guarded CLI Entry Point
// ---------------------------------------------------------------------------
const isMain =
  process.argv[1] &&
  path.resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase();

if (isMain) {
  const args = process.argv.slice(2);
  let repoRoot: string | undefined;
  let outputPathJson: string | undefined;
  let outputPathMd: string | undefined;
  let executeRealRun = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--execute-real-run') {
      executeRealRun = true;
    } else if (arg === '--repoRoot' || arg === '--repo-root') {
      repoRoot = args[++i];
    } else if (arg === '--outputPathJson' || arg === '--out-json') {
      outputPathJson = args[++i];
    } else if (arg === '--outputPathMd' || arg === '--out-md') {
      outputPathMd = args[++i];
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Usage: npx tsx lab/src/research/runIfoPre2023Exploration.ts [options]

Options:
  --execute-real-run       Explicit pre-execution authorization flag to run against real EURUSD prices
  --repoRoot <dir>         Repository root directory (default: current working directory)
  --outputPathJson <path>  Target output path for structured JSON report
  --outputPathMd <path>    Target output path for Markdown exploration report
  --help, -h               Show this help message
`);
      process.exit(0);
    }
  }

  if (!executeRealRun) {
    console.error(`
================================================================================
[PRE-EXECUTION AUDIT GUARD]: Real Candidate Price Exploration Locked
Protocol: docs/FMS_PILOT_IFO_PROTOCOL.md (v1.2 FROZEN)
Status: Awaiting Independent Pre-Execution Audit by Codex.

Execution against real candidate EURUSD OHLC prices is strictly forbidden until
Codex reviews and authorizes Milestone 4 exploration.

To execute upon formal audit clearance:
  npx tsx lab/src/research/runIfoPre2023Exploration.ts \\
    --execute-real-run \\
    --outputPathJson lab/research/ifo_pre2023_exploration_report.json \\
    --outputPathMd lab/research/ifo_pre2023_exploration_report.md
================================================================================
`);
    process.exit(1);
  }

  const resolvedRoot = repoRoot || process.cwd();
  const defaultJson = path.join(resolvedRoot, 'lab/research/ifo_pre2023_exploration_report.json');
  const defaultMd = path.join(resolvedRoot, 'lab/research/ifo_pre2023_exploration_report.md');

  runIfoPre2023Exploration({
    repoRoot: resolvedRoot,
    outputPathJson: outputPathJson || defaultJson,
    outputPathMd: outputPathMd || defaultMd,
  })
    .then(report => {
      console.log(`Exploration complete. Decision: ${report.decision.stateTitle}`);
      console.log(`JSON report written to: ${outputPathJson || defaultJson}`);
      console.log(`Markdown report written to: ${outputPathMd || defaultMd}`);
    })
    .catch(err => {
      console.error('Exploration execution failed:', err);
      process.exit(1);
    });
}
