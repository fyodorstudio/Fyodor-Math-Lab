import { describe, it, expect, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';
import crypto from 'crypto';
import {
  createMulberry32,
  runPairedSignFlipTest,
  runExhaustivePairedSignFlipTest,
  computeWilcoxonSignedRank,
  computePairedTTest,
  studentTUpperTail,
  computeHolmAdjustedPValues,
} from '../src/research/ifoPermutationEngine.js';
import {
  aggregateH4Bar,
  resolveH4Sequence,
  loadPre2023H1Candles,
} from '../src/research/ifoCandleAggregator.js';
import {
  calculateLogReturn,
  calculatePipDrift,
  evaluateEvent,
  evaluateControl,
  pairObservations,
  computeCostSensitivity,
  evaluateDecisionRules,
  evaluateHolmFamily,
  generateIfoExplorationMarkdownReport,
} from '../src/research/ifoExplorationEngine.js';
import {
  runIfoPre2023Exploration,
  computeFileSha256,
  loadUsdReleaseTimestamps,
  getImplementationManifest,
  PINNED_HASHES,
} from '../src/research/runIfoPre2023Exploration.js';
import { verifyH4Path } from '../src/research/ifoControlAudit.js';
import {
  CandleH1,
  CandleH4,
  IfoEvaluatedEpisode,
  IfoEvaluatedControl,
  IfoHorizonSummary,
  IfoPilotExplorationReportData,
  Pre2023CandlesManifest,
  ImplementationManifest,
} from '../src/research/ifoPilotAnalysisTypes.js';
import { SPLIT_TIMESTAMP } from '../src/research/fmsInventoryTypes.js';

describe('German Ifo Pre-2023 Exploration & Testing Engine (Milestone 4)', () => {
  function createMockSummary(pVal: number, deltaR: number, eventPips: number, winRate: number): IfoHorizonSummary {
    return {
      horizonBars: 6,
      horizonLabel: 'Test',
      totalActionable: 40,
      pairedCount: 39,
      unavailableCount: 1,
      meanEventReturn: 0.001,
      meanControlReturn: 0.0,
      meanDeltaReturn: deltaR,
      medianDeltaReturn: deltaR,
      stdDeltaReturn: 0.005,
      meanEventPipDrift: eventPips,
      meanControlPipDrift: 0.0,
      meanDeltaPipDrift: eventPips,
      pairedWins: Math.round(winRate * 39),
      pairedWinRate: winRate,
      pValuePermutation: pVal,
      pValueWilcoxon: pVal,
      pValueTTest: pVal,
      costSensitivity: [],
      yearDistribution: {},
      collisionPartition: {
        collision: { count: 0, meanDeltaReturn: 0, meanDeltaPips: 0, winRate: 0 },
        nonCollision: { count: 0, meanDeltaReturn: 0, meanDeltaPips: 0, winRate: 0 },
      },
      usMorningOverlapPartition: {
        with1530Release: { count: 0, meanDeltaReturn: 0, meanDeltaPips: 0, winRate: 0 },
        without1530Release: { count: 0, meanDeltaReturn: 0, meanDeltaPips: 0, winRate: 0 },
      },
      outliers: [],
    };
  }

  // 1. Fixed Externally Calculated PRNG Expected Values (Non-Self-Referential)
  describe('Mulberry32 PRNG Algorithm & Fixed Expected Values', () => {
    it('produces fixed externally verified reference values from pinned seed 20260925', () => {
      const prng = createMulberry32(20260925);
      // Fixed sequence calculated independently from the 32-bit integer arithmetic specification:
      expect(prng()).toBeCloseTo(0.475283432751894, 12);
      expect(prng()).toBeCloseTo(0.34156298893503845, 12);
      expect(prng()).toBeCloseTo(0.7733166066464037, 12);
      expect(prng()).toBeCloseTo(0.9350769815500826, 12);
      expect(prng()).toBeCloseTo(0.8965572987217456, 12);
    });

    it('demonstrates stable bit-identical results across repeated permutation runs on identical inputs', () => {
      const diffs = [0.001, -0.0005, 0.002, 0.0008, -0.0003, 0.0015, 0.0002, -0.0004];
      const res1 = runPairedSignFlipTest(diffs, { seed: 20260925, draws: 10000 });
      const res2 = runPairedSignFlipTest(diffs, { seed: 20260925, draws: 10000 });

      expect(res1.pValue).toBe(res2.pValue);
      expect(res1.exceedanceCount).toBe(res2.exceedanceCount);
      expect(res1.observedMean).toBe(res2.observedMean);
    });
  });

  // 2. Exact Student-t Tail & Paired t-Test (Degrees of Freedom)
  describe('Student-t Tail Distribution & Paired t-Test Audit', () => {
    it('matches exact mathematical values across various degrees of freedom', () => {
      // df=1, t=1.0: Cauchy distribution tail is exactly 0.25
      expect(studentTUpperTail(1.0, 1)).toBeCloseTo(0.25, 12);

      // df=2, t=sqrt(2): analytical value is 0.5 * (1 - 1/sqrt(2)) = 0.1464466094...
      const expectedDf2 = 0.5 * (1.0 - 1.0 / Math.SQRT2);
      expect(studentTUpperTail(Math.SQRT2, 2)).toBeCloseTo(expectedDf2, 10);

      // df=10, t=1.812461: standard textbook critical value for alpha = 0.05
      expect(studentTUpperTail(1.812461, 10)).toBeCloseTo(0.05, 5);

      // df=38 (N=39 paired pilot), t=1.685954: critical value for alpha = 0.05
      expect(studentTUpperTail(1.685954, 38)).toBeCloseTo(0.05, 5);

      // df=38, t=2.024394: critical value for alpha = 0.025
      expect(studentTUpperTail(2.024394, 38)).toBeCloseTo(0.025, 5);

      // Symmetry check: P(T >= -t) = 1 - P(T >= t)
      expect(studentTUpperTail(-1.685954, 38)).toBeCloseTo(1.0 - 0.05, 5);

      // Edge cases
      expect(studentTUpperTail(0, 38)).toBe(0.5);
      expect(studentTUpperTail(100, 38)).toBeCloseTo(0.0, 10);
      expect(studentTUpperTail(-100, 38)).toBeCloseTo(1.0, 10);
    });

    it('evaluates paired t-test using Student-t distribution rather than normal CDF', () => {
      // Differences with sample size N = 5 (df = 4)
      const diffs = [0.002, 0.003, 0.001, 0.004, 0.002];
      const res = computePairedTTest(diffs);

      expect(res.degreesOfFreedom).toBe(4);
      expect(res.mean).toBeCloseTo(0.0024, 6);
      expect(res.tStatistic).toBeGreaterThan(0);

      // Verify that the p-value matches the Student-t tail with df = 4
      const expectedP = studentTUpperTail(res.tStatistic, 4);
      expect(res.pValueOneSided).toBeCloseTo(expectedP, 10);
    });
  });

  // 3. Wilcoxon Signed-Rank with Ties and Zero Handling Audit
  describe('Wilcoxon Signed-Rank Audit (Ties & Zero Handling)', () => {
    it('matches textbook reference case without ties or zeros', () => {
      // D = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] (all positive, no ties)
      // W+ = 55, Exp = 27.5, Var = 96.25, z = 2.75209, p = 0.00296
      const diffs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      const res = computeWilcoxonSignedRank(diffs);

      expect(res.effectiveN).toBe(10);
      expect(res.zeroCount).toBe(0);
      expect(res.sumPositiveRanks).toBe(55);
      expect(res.sumNegativeRanks).toBe(0);
      expect(res.expectedW).toBe(27.5);
      expect(res.varianceW).toBeCloseTo(96.25, 4);
      expect(res.tieCorrection).toBe(0);
      expect(res.zStatistic).toBeCloseTo(2.75209, 4);
      expect(res.pValueOneSided).toBeCloseTo(0.00296, 4);
    });

    it('correctly drops zeros and applies tie correction on tied differences', () => {
      // D = [0, -2, 2, 3, -3, 3, 5, -5]
      // 1 zero dropped -> effectiveN = 7
      // Tied absolute groups: {2: 2, 3: 3, 5: 2} -> tieCorrection = ((8-2)+(27-3)+(8-2))/48 = 36/48 = 0.75
      // W+ = 16, Exp = 14, Var = 35 - 0.75 = 34.25, z = (16 - 14 - 0.5) / sqrt(34.25) = 0.25631, p = 0.39886
      const diffs = [0, -2, 2, 3, -3, 3, 5, -5];
      const res = computeWilcoxonSignedRank(diffs);

      expect(res.effectiveN).toBe(7);
      expect(res.zeroCount).toBe(1);
      expect(res.tieCorrection).toBe(0.75);
      expect(res.expectedW).toBe(14);
      expect(res.varianceW).toBe(34.25);
      expect(res.sumPositiveRanks).toBe(16);
      expect(res.zStatistic).toBeCloseTo(0.25631, 4);
      expect(res.pValueOneSided).toBeCloseTo(0.39886, 4);
    });
  });

  // 4. Holm-Bonferroni Multiplicity Adjustment
  describe('Holm-Bonferroni Multiplicity Adjustment', () => {
    it('applies step-down Holm adjustment across a family of p-values', () => {
      // Family of 2 hypotheses (6 H4 and 12 H4)
      const pVals1 = [0.01, 0.04];
      const adj1 = computeHolmAdjustedPValues(pVals1);
      // Sorted: 0.01 (x2 = 0.02), 0.04 (x1 = 0.04)
      expect(adj1[0]).toBeCloseTo(0.02, 6);
      expect(adj1[1]).toBeCloseTo(0.04, 6);

      // Preserves original index order
      const pVals2 = [0.04, 0.01];
      const adj2 = computeHolmAdjustedPValues(pVals2);
      expect(adj2[0]).toBeCloseTo(0.04, 6);
      expect(adj2[1]).toBeCloseTo(0.02, 6);

      // Enforces monotonicity
      const pVals3 = [0.04, 0.05];
      const adj3 = computeHolmAdjustedPValues(pVals3);
      // 0.04 * 2 = 0.08, 0.05 * 1 = 0.05 -> max so far is 0.08
      expect(adj3[0]).toBeCloseTo(0.08, 6);
      expect(adj3[1]).toBeCloseTo(0.08, 6);
    });

    it('sorts raw p-values before assigning cutoffs and evaluates rankings and decisions when p12 < p6', () => {
      const rawP6 = 0.04;
      const rawP12 = 0.01;
      const [adjP6, adjP12] = computeHolmAdjustedPValues([rawP6, rawP12]);
      // Sorted order: 0.01 (x2 = 0.02), 0.04 (x1 = 0.04)
      expect(adjP12).toBeCloseTo(0.02, 6);
      expect(adjP6).toBeCloseTo(0.04, 6);

      const family = evaluateHolmFamily(rawP6, rawP12, adjP6, adjP12);

      // Secondary 12 H4 is smaller -> Rank 1, cutoff 0.025
      expect(family.secondary12.rank).toBe(1);
      expect(family.secondary12.cutoff).toBe(0.025);
      expect(family.secondary12.cleared).toBe(true);
      expect(family.secondary12.disposition).toContain('Cleared Step 1');

      // Primary 6 H4 is larger -> Rank 2, cutoff 0.050
      expect(family.primary6.rank).toBe(2);
      expect(family.primary6.cutoff).toBe(0.050);
      expect(family.primary6.cleared).toBe(true);
      expect(family.primary6.disposition).toContain('Cleared Step 2');

      // Verify that the frozen fixed-sequence primary decision evaluates strictly on Primary 6 H4 stats
      const mockSummary6 = createMockSummary(rawP6, 0.0015, 2.5, 0.60);
      const decision = evaluateDecisionRules(mockSummary6);
      // p6 = 0.04 (< 0.05), event pips = 2.5 (>= 1.0), win rate = 0.60 (>= 0.55) -> State 1
      expect(decision.decisionState).toBe('STATE_1_PLAUSIBLE_IN_SAMPLE_ANOMALY');

      // If p6 had been 0.07 (while p12 was 0.01), p6 would trigger State 2 even though p12 cleared Step 1
      const mockSummary6Fragile = createMockSummary(0.07, 0.0015, 2.5, 0.60);
      const decisionFragile = evaluateDecisionRules(mockSummary6Fragile);
      expect(decisionFragile.decisionState).toBe('STATE_2_INCONCLUSIVE_FRAGILE_EVIDENCE');

      // Verify Markdown generation displays both ranked horizons accurately
      const mockSummary12 = createMockSummary(rawP12, 0.0020, 3.0, 0.65);
      mockSummary6.pValueHolmAdjusted = adjP6;
      mockSummary12.pValueHolmAdjusted = adjP12;

      const mockReportData: IfoPilotExplorationReportData = {
        protocolVersion: '1.2 FROZEN',
        protocolDate: '2026-09-25',
        splitTimestamp: SPLIT_TIMESTAMP,
        evaluatedAt: new Date().toISOString(),
        implementation: {
          gitCommit: 'mock-commit-sha',
          sourceFilesSha256: { 'file1.ts': 'mockhash1' },
        },
        manifest: {
          consumedPre2023H1Candles: {
            rowCount: 100,
            firstTimestamp: 1600000000,
            lastTimestamp: 1600360000,
            sha256: 'mockcandlehsh',
            sha256WithHeader: 'mockcandlewithheader',
          },
          implementation: {
            gitCommit: 'mock-commit-sha',
            sourceFilesSha256: { 'file1.ts': 'mockhash1' },
          },
        },
        provenanceHashes: {
          rawCalendarSha256: 'a',
          episodesJsonlSha256: 'b',
          pilotLedgerJsonSha256: 'c',
          pilotLedgerMdSha256: 'd',
          consumedPre2023H1CandlesSha256: 'mockcandlehsh',
        },
        events: [],
        primary6H4: { summary: mockSummary6, pairs: [], controls: [] },
        secondary12H4Strict: { summary: mockSummary12, pairs: [], controls: [] },
        secondary12H4Permissive: { summary: mockSummary12, pairs: [], controls: [] },
        decision,
      };

      const md = generateIfoExplorationMarkdownReport(mockReportData);
      // Section 3 (Primary 6 H4) must show Rank 2 of 2 and cutoff 0.050
      expect(md).toContain('Rank 2 of 2 | Raw: 0.04000 (cutoff $\\le 0.050$) | Adjusted: 0.04000');
      expect(md).toContain('Cleared Step 2 (Rank 2: raw p <= 0.050)');

      // Section 4 (Secondary 12 H4) must show Rank 1 of 2 and cutoff 0.025
      expect(md).toContain('Rank 1 of 2 | Raw: 0.01000 (cutoff $\\le 0.025$) | Adjusted: 0.02000');
      expect(md).toContain('Cleared Step 1 (Rank 1: raw p <= 0.025)');

      // Section 2 must show State 1 decision from Primary 6 H4
      expect(md).toContain('State 1: Plausible In-Sample Anomaly');
    });
  });

  // 5. Small-N Exhaustive Comparison vs Monte Carlo
  describe('Small-N Exhaustive Paired Sign-Flip Benchmark', () => {
    it('converges to the exact combinatorial distribution on synthetic differences', () => {
      const diffs = [0.0015, 0.0008, -0.0002, 0.0021, 0.0005, -0.0006, 0.0011, 0.0003];
      const exact = runExhaustivePairedSignFlipTest(diffs);
      expect(exact.totalPermutations).toBe(256);
      expect(exact.nPairs).toBe(8);

      const mc = runPairedSignFlipTest(diffs, { seed: 20260925, draws: 50000 });
      expect(Math.abs(mc.pValue - exact.pValue)).toBeLessThan(0.005);
    });
  });

  // 6. Directional Sign Arithmetic
  describe('Directional Sign Arithmetic (Long vs Short)', () => {
    const pEntry = 1.1000;
    const pUp = 1.1050; // +50 pips
    const pDown = 1.0950; // -50 pips

    it('computes correct positive and negative returns for LONG direction', () => {
      const retUp = calculateLogReturn('LONG', pEntry, pUp);
      const retDown = calculateLogReturn('LONG', pEntry, pDown);

      expect(retUp).toBeGreaterThan(0);
      expect(retDown).toBeLessThan(0);
      expect(retUp).toBeCloseTo(Math.log(1.1050 / 1.1000), 8);
      expect(retDown).toBeCloseTo(Math.log(1.0950 / 1.1000), 8);

      const pipsUp = calculatePipDrift('LONG', pEntry, pUp);
      const pipsDown = calculatePipDrift('LONG', pEntry, pDown);
      expect(pipsUp).toBeCloseTo(50.0, 4);
      expect(pipsDown).toBeCloseTo(-50.0, 4);
    });

    it('computes correct inverted returns for SHORT direction', () => {
      const retUp = calculateLogReturn('SHORT', pEntry, pUp);
      const retDown = calculateLogReturn('SHORT', pEntry, pDown);

      expect(retUp).toBeLessThan(0);
      expect(retDown).toBeGreaterThan(0);
      expect(retUp).toBeCloseTo(-Math.log(1.1050 / 1.1000), 8);
      expect(retDown).toBeCloseTo(-Math.log(1.0950 / 1.1000), 8);

      const pipsUp = calculatePipDrift('SHORT', pEntry, pUp);
      const pipsDown = calculatePipDrift('SHORT', pEntry, pDown);
      expect(pipsUp).toBeCloseTo(-50.0, 4);
      expect(pipsDown).toBeCloseTo(50.0, 4);
    });
  });

  // 7. Exact MT5 Export Schema & Fail-Closed Candle Loader
  describe('Exact MT5 Schema & Fail-Closed Guarded Candle Loader', () => {
    it('successfully loads synthetic CSV with the exact MT5 export header', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-schema-'));
      const csvPath = path.join(tempDir, 'candles_synthetic.csv');

      const header = 'time,open,high,low,close,tick_volume,spread,real_volume,source_symbol,time_server_text,timestamp_convention,complete_at_export';
      const rows = [
        header,
        '1600000000,1.1000,1.1020,1.0990,1.1010,100,10,0,"EURUSD",2020.09.13 12:00:00,trade_server_time,true',
        '1600003600,1.1010,1.1030,1.1000,1.1025,120,10,0,"EURUSD",2020.09.13 13:00:00,trade_server_time,true',
      ];
      fs.writeFileSync(csvPath, rows.join('\n'), 'utf8');

      const { candleMap: map, manifest } = await loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP);
      expect(map.size).toBe(2);
      expect(map.get(1600000000)?.open).toBe(1.1000);
      expect(map.get(1600003600)?.close).toBe(1.1025);
      expect(manifest.rowCount).toBe(2);
      expect(manifest.firstTimestamp).toBe(1600000000);
      expect(manifest.lastTimestamp).toBe(1600003600);
      expect(typeof manifest.sha256).toBe('string');
      expect(manifest.sha256.length).toBe(64);

      fs.rmSync(tempDir, { recursive: true, force: true });
    });

    it('fails closed on malformed non-integer timestamp', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-malformed-ts-'));
      const csvPath = path.join(tempDir, 'candles.csv');
      const content = [
        'time,open,high,low,close,complete_at_export',
        'invalid_ts,1.1000,1.1020,1.0990,1.1010,true',
      ].join('\n');
      fs.writeFileSync(csvPath, content, 'utf8');

      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(/Malformed timestamp/);
      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    });

    it('fails closed on non-monotone timestamp sequence', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-non-monotone-'));
      const csvPath = path.join(tempDir, 'candles.csv');
      const content = [
        'time,open,high,low,close,complete_at_export',
        '1600003600,1.1000,1.1020,1.0990,1.1010,true',
        '1600000000,1.1010,1.1030,1.1000,1.1025,true', // Retrograde timestamp
      ].join('\n');
      fs.writeFileSync(csvPath, content, 'utf8');

      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(/Non-monotone candle timestamp/);
      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    });

    it('fails closed on duplicate candle timestamps', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-dup-ts-'));
      const csvPath = path.join(tempDir, 'candles.csv');
      const content = [
        'time,open,high,low,close,complete_at_export',
        '1600000000,1.1000,1.1020,1.0990,1.1010,true',
        '1600000000,1.1000,1.1020,1.0990,1.1010,true', // Duplicate
      ].join('\n');
      fs.writeFileSync(csvPath, content, 'utf8');

      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(/Duplicate candle timestamp/);
      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    });

    it('fails closed on incomplete candle (complete_at_export = false)', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-incomplete-'));
      const csvPath = path.join(tempDir, 'candles.csv');
      const content = [
        'time,open,high,low,close,complete_at_export',
        '1600000000,1.1000,1.1020,1.0990,1.1010,false', // Incomplete!
      ].join('\n');
      fs.writeFileSync(csvPath, content, 'utf8');

      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(/Incomplete candle at export/);
      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    });

    it('fails closed on contradictory OHLC (open/close outside high-low)', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-contradictory-'));
      const csvPath = path.join(tempDir, 'candles.csv');

      // Case A: Open > High
      fs.writeFileSync(
        csvPath,
        ['time,open,high,low,close,complete_at_export', '1600000000,1.1050,1.1020,1.0990,1.1010,true'].join('\n'),
        'utf8'
      );
      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(/Contradictory OHLC prices/);

      // Case B: Close < Low
      fs.writeFileSync(
        csvPath,
        ['time,open,high,low,close,complete_at_export', '1600000000,1.1000,1.1020,1.0990,1.0980,true'].join('\n'),
        'utf8'
      );
      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(/Contradictory OHLC prices/);

      // Case C: Low > High
      fs.writeFileSync(
        csvPath,
        ['time,open,high,low,close,complete_at_export', '1600000000,1.1000,1.0980,1.1020,1.1000,true'].join('\n'),
        'utf8'
      );
      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(/Contradictory OHLC prices/);

      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    });

    it('proves reader stops at pre-2023 boundary without parsing 2023+ price values', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-split-isolation-'));
      const csvPath = path.join(tempDir, 'candles.csv');

      // Last pre-split candle at 1672527600 (2022-12-31 23:00)
      // First boundary candle at SPLIT_TIMESTAMP (1672531200 = 2023-01-01 00:00) has CORRUPT price strings
      const content = [
        'time,open,high,low,close,complete_at_export',
        '1672527600,1.0700,1.0710,1.0690,1.0705,true',
        `${SPLIT_TIMESTAMP},CORRUPT_NON_NUMERIC,CORRUPT,CORRUPT,CORRUPT,true`,
      ].join('\n');
      fs.writeFileSync(csvPath, content, 'utf8');

      // If the reader parsed 2023+ OHLC values, it would throw on CORRUPT_NON_NUMERIC.
      // Because it halts at boundary without parsing prices, it succeeds with 1 candle:
      const { candleMap: map, manifest } = await loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP);
      expect(map.size).toBe(1);
      expect(map.has(1672527600)).toBe(true);
      expect(map.has(SPLIT_TIMESTAMP)).toBe(false);
      expect(manifest.rowCount).toBe(1);
      expect(manifest.firstTimestamp).toBe(1672527600);
      expect(manifest.lastTimestamp).toBe(1672527600);

      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    });

    it('fails closed if header violates expected schema (time not in column 0)', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-header-col0-'));
      const csvPath = path.join(tempDir, 'candles.csv');
      // time is in column 1 instead of column 0
      const content = [
        'source_symbol,time,open,high,low,close,complete_at_export',
        '"EURUSD",1600000000,1.1000,1.1020,1.0990,1.1010,true',
      ].join('\n');
      fs.writeFileSync(csvPath, content, 'utf8');

      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(
        /expected timestamp column \('time'\) at index 0/
      );
      fs.rmSync(tempDir, { recursive: true, force: true });
    });

    it('succeeds when first post-split row contains only a valid timestamp and no price columns, preserving identical pre-split count and hash', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-timestamp-only-post-split-'));
      const csvPathBaseline = path.join(tempDir, 'candles_baseline.csv');
      const csvPathTimestampOnly = path.join(tempDir, 'candles_ts_only.csv');

      const header = 'time,open,high,low,close,complete_at_export';
      const preSplitRows = [
        '1600000000,1.1000,1.1020,1.0990,1.1010,true',
        '1600003600,1.1010,1.1030,1.1000,1.1025,true',
      ];

      // Baseline file has standard full post-split rows
      const baselinePostSplit = [
        `${SPLIT_TIMESTAMP},1.0700,1.0720,1.0690,1.0710,true`,
        `${SPLIT_TIMESTAMP + 3600},1.0710,1.0730,1.0700,1.0720,true`,
      ];

      // Target file has post-split row containing ONLY a valid timestamp and no price columns
      const tsOnlyPostSplit = [
        `${SPLIT_TIMESTAMP}`, // ONLY a timestamp, zero commas, zero price columns!
      ];

      fs.writeFileSync(csvPathBaseline, [header, ...preSplitRows, ...baselinePostSplit].join('\n'), 'utf8');
      fs.writeFileSync(csvPathTimestampOnly, [header, ...preSplitRows, ...tsOnlyPostSplit].join('\n'), 'utf8');

      const resBaseline = await loadPre2023H1Candles(csvPathBaseline, SPLIT_TIMESTAMP);
      const resTsOnly = await loadPre2023H1Candles(csvPathTimestampOnly, SPLIT_TIMESTAMP);

      // Loading succeeds
      expect(resTsOnly.candleMap.size).toBe(2);
      expect(resTsOnly.candleMap.has(SPLIT_TIMESTAMP)).toBe(false);

      // Pre-split count must remain strictly identical
      expect(resTsOnly.manifest.rowCount).toBe(resBaseline.manifest.rowCount);
      expect(resTsOnly.manifest.rowCount).toBe(2);
      expect(resTsOnly.manifest.firstTimestamp).toBe(resBaseline.manifest.firstTimestamp);
      expect(resTsOnly.manifest.lastTimestamp).toBe(resBaseline.manifest.lastTimestamp);

      // Pre-split SHA-256 hash must remain strictly identical
      expect(resTsOnly.manifest.sha256).toBe(resBaseline.manifest.sha256);
      expect(resTsOnly.manifest.sha256WithHeader).toBe(resBaseline.manifest.sha256WithHeader);

      await new Promise(resolve => setTimeout(resolve, 50));
      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
    });

    it('fails closed when a PRE-split row contains only a timestamp without required OHLC columns', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-malformed-presplit-'));
      const csvPath = path.join(tempDir, 'candles.csv');
      const content = [
        'time,open,high,low,close,complete_at_export',
        '1600000000,1.1000,1.1020,1.0990,1.1010,true',
        '1600003600', // PRE-split row with only timestamp and no price columns
      ].join('\n');
      fs.writeFileSync(csvPath, content, 'utf8');

      await expect(loadPre2023H1Candles(csvPath, SPLIT_TIMESTAMP)).rejects.toThrow(
        /Malformed CSV row at line 3/
      );
      fs.rmSync(tempDir, { recursive: true, force: true });
    });

    it('computes pre-2023 candle manifest (SHA-256, row count, first/last ts) without hashing 2023+ rows, and verifies repeatability', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-manifest-'));
      const csvPathA = path.join(tempDir, 'candles_A.csv');
      const csvPathB = path.join(tempDir, 'candles_B.csv');

      const header = 'time,open,high,low,close,complete_at_export';
      const preSplitRows = [
        '1600000000,1.1000,1.1020,1.0990,1.1010,true',
        '1600003600,1.1010,1.1030,1.1000,1.1025,true',
        '1600007200,1.1025,1.1040,1.1015,1.1035,true',
      ];

      // File A has post-split rows with one set of post-split values
      const postSplitA = [
        `${SPLIT_TIMESTAMP},1.0700,1.0720,1.0690,1.0710,true`,
        `${SPLIT_TIMESTAMP + 3600},1.0710,1.0730,1.0700,1.0720,true`,
      ];

      // File B has post-split rows with completely DIFFERENT post-split values
      const postSplitB = [
        `${SPLIT_TIMESTAMP},9.9999,9.9999,9.9999,9.9999,true`,
        `${SPLIT_TIMESTAMP + 3600},8.8888,8.8888,8.8888,8.8888,true`,
      ];

      fs.writeFileSync(csvPathA, [header, ...preSplitRows, ...postSplitA].join('\n'), 'utf8');
      fs.writeFileSync(csvPathB, [header, ...preSplitRows, ...postSplitB].join('\n'), 'utf8');

      const resA1 = await loadPre2023H1Candles(csvPathA, SPLIT_TIMESTAMP);
      const resA2 = await loadPre2023H1Candles(csvPathA, SPLIT_TIMESTAMP);
      const resB = await loadPre2023H1Candles(csvPathB, SPLIT_TIMESTAMP);

      // 1. Row count, first and last timestamps match pre-split data exactly
      expect(resA1.manifest.rowCount).toBe(3);
      expect(resA1.manifest.firstTimestamp).toBe(1600000000);
      expect(resA1.manifest.lastTimestamp).toBe(1600007200);

      // 2. Repeatability: repeated run on same file yields bit-for-bit identical SHA-256
      expect(resA1.manifest.sha256).toBe(resA2.manifest.sha256);
      expect(resA1.manifest.sha256WithHeader).toBe(resA2.manifest.sha256WithHeader);

      // 3. Post-split isolation: completely different post-split data produces identical SHA-256
      // Proves that post-split rows are NEVER hashed or analyzed
      expect(resB.manifest.rowCount).toBe(3);
      expect(resB.manifest.sha256).toBe(resA1.manifest.sha256);
      expect(resB.manifest.sha256WithHeader).toBe(resA1.manifest.sha256WithHeader);

      // 4. Verify sha256 matches independent computation of exact pre-split rows
      const manualHash = crypto.createHash('sha256');
      for (const row of preSplitRows) {
        manualHash.update(row + '\n');
      }
      expect(resA1.manifest.sha256).toBe(manualHash.digest('hex'));

      await new Promise(resolve => setTimeout(resolve, 50));
      fs.rmSync(tempDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
    });
  });

  // 8. Streaming Cryptographic Hash Engine & Manifest Verification
  describe('Streaming Cryptographic SHA-256 Hash Engine & Manifests', () => {
    it('computes accurate hash via streaming and detects deliberate corruption', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-hash-'));
      const filePath = path.join(tempDir, 'sample.txt');
      fs.writeFileSync(filePath, 'Exact Deterministic Payload for Hash Verification', 'utf8');

      const expectedHash = crypto.createHash('sha256').update('Exact Deterministic Payload for Hash Verification').digest('hex');
      const streamedHash = await computeFileSha256(filePath);
      expect(streamedHash).toBe(expectedHash);

      // Deliberate corruption: 1 byte modified
      fs.writeFileSync(filePath, 'Exact Deterministic Payload for Hash Verification!', 'utf8');
      const corruptedHash = await computeFileSha256(filePath);
      expect(corruptedHash).not.toBe(expectedHash);

      fs.rmSync(tempDir, { recursive: true, force: true });
    });

    it('restricts USD release timestamps strictly to pre-split releases and excludes post-split releases', async () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-test-usd-'));
      const calCsvPath = path.join(tempDir, 'calendar.csv');

      const calLines = [
        'eventId,valueId,timestamp,currency,countryCode,eventName,actualStr,forecastStr,previousStr,revisionStr,timestampServerText',
        '1001,1,1600000000,USD,US,Pre-Split Release,1.0,1.0,1.0,,2020.09.13 12:00:00',
        '1002,2,1650000000,USD,US,Pre-Split Release 2,2.0,2.0,2.0,,2022.04.15 12:00:00',
        '1003,3,1600000000,EUR,DE,EUR Release (Ignored),1.0,1.0,1.0,,2020.09.13 12:00:00',
        `1004,4,${SPLIT_TIMESTAMP},USD,US,Split Boundary Release (Excluded),3.0,3.0,3.0,,2023.01.01 00:00:00`,
        '1005,5,1680000000,USD,US,Post-Split Release (Excluded),4.0,4.0,4.0,,2023.03.28 12:00:00',
      ];
      fs.writeFileSync(calCsvPath, calLines.join('\n'), 'utf8');

      const usdSet = await loadUsdReleaseTimestamps(calCsvPath, SPLIT_TIMESTAMP);

      // Pre-split USD releases must be present
      expect(usdSet.has(1600000000)).toBe(true);
      expect(usdSet.has(1650000000)).toBe(true);

      // EUR release must be excluded
      expect(usdSet.size).toBe(2);

      // Split boundary (>= SPLIT_TIMESTAMP) must be excluded
      expect(usdSet.has(SPLIT_TIMESTAMP)).toBe(false);

      // Post-split USD release (1680000000 >= SPLIT_TIMESTAMP) must be excluded
      expect(usdSet.has(1680000000)).toBe(false);

      fs.rmSync(tempDir, { recursive: true, force: true });
    });

    it('computes immutable implementation manifest with source file hashes and git commit', () => {
      const repoRoot = path.resolve(__dirname, '../../');
      const manifest = getImplementationManifest(repoRoot);

      expect(typeof manifest.sourceFilesSha256).toBe('object');
      const keys = Object.keys(manifest.sourceFilesSha256);
      expect(keys.length).toBeGreaterThanOrEqual(6);

      for (const [filePath, hash] of Object.entries(manifest.sourceFilesSha256)) {
        expect(hash).toMatch(/^[a-f0-9]{64}$/);
        expect(fs.existsSync(path.join(repoRoot, filePath))).toBe(true);
      }

      // gitCommit is either a 40-character hex string or null
      if (manifest.gitCommit !== null) {
        expect(manifest.gitCommit).toMatch(/^[a-f0-9]{40}$/);
      }
    });
  });

  // 9. Dual Cost Sensitivity Scenarios (Scenario A vs Scenario B)
  describe('Dual Cost Sensitivity Scenarios (Paired vs Frictionless Benchmark)', () => {
    it('evaluates both Scenario A (equal friction cancels) and Scenario B (event friction only)', () => {
      const mockEvent: IfoEvaluatedEpisode = {
        packageIndex: 1,
        actionableIndex: 1,
        releaseTimestamp: 1600000000,
        brokerDateTime: '2020-09-15 12:00:00',
        direction: 'LONG',
        entryTimestamp: 1600000000,
        entryPrice: 1.1000,
        exitTimestamp6: 1600086400,
        exitPrice6: 1.1020, // +20 pips
        logReturn6: 0.001817,
        pipDrift6: 20.0,
        bars6: [],
        exitTimestamp12: 1600172800,
        exitPrice12: 1.1030,
        logReturn12: 0.002723,
        pipDrift12: 30.0,
        bars12: [],
        hasCrossCurrencyCollision: false,
        collidingCurrencies: [],
        hasUs1530MorningRelease: false,
      };

      const mockControl: IfoEvaluatedControl = {
        actionableIndex: 1,
        horizon: 6,
        status: 'PAIRED',
        controlChoice: 'D_MINUS_7',
        direction: 'LONG',
        controlEntryTimestamp: 1599395200,
        controlEntryPrice: 1.1000,
        controlExitTimestamp: 1599481600,
        controlExitPrice: 1.1010, // +10 pips
        logReturn: 0.000909,
        pipDrift: 10.0,
        bars: [],
      };

      const pair = pairObservations(mockEvent, mockControl, 6);
      const rows = computeCostSensitivity([pair], [mockEvent], 6);

      expect(rows.length).toBe(5);

      // Baseline at c = 0.0
      expect(rows[0].costPips).toBe(0.0);
      expect(rows[0].grossMeanEventPips).toBeCloseTo(20.0, 4);
      expect(rows[0].netMeanEventPips).toBeCloseTo(20.0, 4);
      expect(rows[0].scenarioA_EqualCostDeltaPips).toBeCloseTo(10.0, 4);
      expect(rows[0].scenarioB_EventOnlyNetDeltaPips).toBeCloseTo(10.0, 4);
      expect(rows[0].scenarioA_WinRate).toBe(1.0);
      expect(rows[0].scenarioB_WinRate).toBe(1.0);

      // At c = 1.0 pip:
      // Event trade net pips = 20 - 1 = 19 pips
      expect(rows[2].costPips).toBe(1.0);
      expect(rows[2].netMeanEventPips).toBeCloseTo(19.0, 4);
      // Scenario A: equal friction c cancels out in paired difference: (20 - 1) - (10 - 1) = 10 pips
      expect(rows[2].scenarioA_EqualCostDeltaPips).toBeCloseTo(10.0, 4);
      expect(rows[2].scenarioA_WinRate).toBe(1.0);
      // Scenario B: difference reduced by c: (20 - 1) - 10 = 9 pips
      expect(rows[2].scenarioB_EventOnlyNetDeltaPips).toBeCloseTo(9.0, 4);
      expect(rows[2].scenarioB_WinRate).toBe(1.0);

      // At c = 2.0 pips:
      expect(rows[4].costPips).toBe(2.0);
      expect(rows[4].netMeanEventPips).toBeCloseTo(18.0, 4);
      expect(rows[4].scenarioA_EqualCostDeltaPips).toBeCloseTo(10.0, 4);
      expect(rows[4].scenarioB_EventOnlyNetDeltaPips).toBeCloseTo(8.0, 4);
    });

    it('evaluates Scenario A log-return penalties when event and control have distinct entry prices', () => {
      // Event: LONG at entry = 1.1000, exit = 1.1020 (+20 pips)
      const mockEvent: IfoEvaluatedEpisode = {
        packageIndex: 1,
        actionableIndex: 1,
        releaseTimestamp: 1600000000,
        brokerDateTime: '2020-09-15 12:00:00',
        direction: 'LONG',
        entryTimestamp: 1600000000,
        entryPrice: 1.1000,
        exitTimestamp6: 1600086400,
        exitPrice6: 1.1020,
        logReturn6: Math.log(1.1020 / 1.1000),
        pipDrift6: 20.0,
        bars6: [],
        exitTimestamp12: 1600172800,
        exitPrice12: 1.1030,
        logReturn12: Math.log(1.1030 / 1.1000),
        pipDrift12: 30.0,
        bars12: [],
        hasCrossCurrencyCollision: false,
        collidingCurrencies: [],
        hasUs1530MorningRelease: false,
      };

      // Control: LONG at distinct entry = 1.2000, exit = 1.2010 (+10 pips)
      const mockControl: IfoEvaluatedControl = {
        actionableIndex: 1,
        horizon: 6,
        status: 'PAIRED',
        controlChoice: 'D_MINUS_7',
        direction: 'LONG',
        controlEntryTimestamp: 1599395200,
        controlEntryPrice: 1.2000,
        controlExitTimestamp: 1599481600,
        controlExitPrice: 1.2010,
        logReturn: Math.log(1.2010 / 1.2000),
        pipDrift: 10.0,
        bars: [],
      };

      const pair = pairObservations(mockEvent, mockControl, 6);
      expect(pair.eventEntryPrice).toBe(1.1000);
      expect(pair.controlEntryPrice).toBe(1.2000);

      const rows = computeCostSensitivity([pair], [mockEvent], 6);

      // In pips: equal cost cancels identically: delta pips is strictly 10.0 across all cost levels
      expect(rows[0].scenarioA_EqualCostDeltaPips).toBeCloseTo(10.0, 6);
      expect(rows[2].scenarioA_EqualCostDeltaPips).toBeCloseTo(10.0, 6); // at c=1.0 pip
      expect(rows[4].scenarioA_EqualCostDeltaPips).toBeCloseTo(10.0, 6); // at c=2.0 pips

      // In log return: at c = 1.0 pip (0.0001):
      // penaltyEvent = 0.0001 / 1.1000
      // penaltyControl = 0.0001 / 1.2000
      // expectedDeltaReturn = grossDeltaReturn - (0.0001 / 1.1000 - 0.0001 / 1.2000)
      const grossDeltaReturn = pair.deltaReturn;
      const expectedDeltaReturn1Pip =
        grossDeltaReturn - (0.0001 / 1.1000 - 0.0001 / 1.2000);
      expect(rows[2].scenarioA_EqualCostDeltaReturn).toBeCloseTo(expectedDeltaReturn1Pip, 8);
      expect(rows[2].scenarioA_EqualCostDeltaReturn).not.toBeCloseTo(grossDeltaReturn, 8);
    });

    it('proves grossMeanDeltaReturn is identical at every cost level while scenarioA_EqualCostDeltaReturn varies with entry prices', () => {
      // Pair with distinct entry prices: Pe = 1.1000, Pc = 1.2500
      const mockEvent: IfoEvaluatedEpisode = {
        packageIndex: 1,
        actionableIndex: 1,
        releaseTimestamp: 1600000000,
        brokerDateTime: '2020-09-15 12:00:00',
        direction: 'LONG',
        entryTimestamp: 1600000000,
        entryPrice: 1.1000,
        exitTimestamp6: 1600086400,
        exitPrice6: 1.1020,
        logReturn6: Math.log(1.1020 / 1.1000),
        pipDrift6: 20.0,
        bars6: [],
        exitTimestamp12: 1600172800,
        exitPrice12: 1.1030,
        logReturn12: Math.log(1.1030 / 1.1000),
        pipDrift12: 30.0,
        bars12: [],
        hasCrossCurrencyCollision: false,
        collidingCurrencies: [],
        hasUs1530MorningRelease: false,
      };

      const mockControl: IfoEvaluatedControl = {
        actionableIndex: 1,
        horizon: 6,
        status: 'PAIRED',
        controlChoice: 'D_MINUS_7',
        direction: 'LONG',
        controlEntryTimestamp: 1599395200,
        controlEntryPrice: 1.2500,
        controlExitTimestamp: 1599481600,
        controlExitPrice: 1.2510,
        logReturn: Math.log(1.2510 / 1.2500),
        pipDrift: 10.0,
        bars: [],
      };

      const pair = pairObservations(mockEvent, mockControl, 6);
      const rows = computeCostSensitivity([pair], [mockEvent], 6);

      const baselineGrossReturn = rows[0].grossMeanDeltaReturn;

      for (const row of rows) {
        // 1. grossMeanDeltaReturn is strictly identical at every cost level
        expect(row.grossMeanDeltaReturn).toBe(baselineGrossReturn);
        // 2. grossMeanDeltaPips is strictly identical at every cost level
        expect(row.grossMeanDeltaPips).toBe(10.0);
      }

      // Scenario A net log-return at c = 0.0 matches gross return
      expect(rows[0].scenarioA_EqualCostDeltaReturn).toBeCloseTo(baselineGrossReturn, 10);

      // Scenario A net log-return at c = 1.0 differs from gross return because 1/1.1000 !== 1/1.2500
      expect(rows[2].scenarioA_EqualCostDeltaReturn).not.toBeCloseTo(baselineGrossReturn, 10);
      expect(rows[2].scenarioA_EqualCostDeltaReturn).toBeLessThan(baselineGrossReturn);

      // At c = 2.0 pips, it differs even more
      expect(rows[4].scenarioA_EqualCostDeltaReturn).toBeLessThan(rows[2].scenarioA_EqualCostDeltaReturn);
    });
  });

  // 10. Ordered Decision Rules
  describe('Ordered Decision Rules (States 1, 2, 3)', () => {

    it('triggers State 3 when p >= 0.10 or mean delta return <= 0', () => {
      const s1 = createMockSummary(0.12, 0.0010, 2.5, 0.60);
      expect(evaluateDecisionRules(s1).decisionState).toBe('STATE_3_NO_CONVINCING_EVIDENCE');

      const s2 = createMockSummary(0.04, -0.0002, 2.5, 0.60);
      expect(evaluateDecisionRules(s2).decisionState).toBe('STATE_3_NO_CONVINCING_EVIDENCE');
    });

    it('triggers State 2 when borderline or economically fragile', () => {
      const s1 = createMockSummary(0.07, 0.0015, 2.5, 0.60);
      expect(evaluateDecisionRules(s1).decisionState).toBe('STATE_2_INCONCLUSIVE_FRAGILE_EVIDENCE');

      const s2 = createMockSummary(0.03, 0.0008, 0.7, 0.60);
      expect(evaluateDecisionRules(s2).decisionState).toBe('STATE_2_INCONCLUSIVE_FRAGILE_EVIDENCE');

      const s3 = createMockSummary(0.03, 0.0015, 2.5, 0.50);
      expect(evaluateDecisionRules(s3).decisionState).toBe('STATE_2_INCONCLUSIVE_FRAGILE_EVIDENCE');
    });

    it('triggers State 1 only when all four hurdle criteria are met', () => {
      const s = createMockSummary(0.02, 0.0020, 2.5, 0.62);
      expect(evaluateDecisionRules(s).decisionState).toBe('STATE_1_PLAUSIBLE_IN_SAMPLE_ANOMALY');
    });
  });

  // 11. Synthetic End-to-End Exploration Invocation & Price Seal Isolation
  describe('Synthetic End-to-End Invocation & Price Seal Isolation', () => {
    it('executes the full pipeline on synthetic test fixtures, verifying 40/39/34 accounting and JSON/MD report outputs', async () => {
      const repoRoot = path.resolve(__dirname, '../../');
      const realCandlePath = path.join(
        repoRoot,
        'tools/mt5/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv'
      );

      // Instrument forensic spies to prove the test NEVER opens the real candle file
      const readFileSyncSpy = vi.spyOn(fs, 'readFileSync');
      const createReadStreamSpy = vi.spyOn(fs, 'createReadStream');

      // Create isolated temporary workspace
      const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ifo-synthetic-e2e-'));
      const toolsDir = path.join(tempRoot, 'tools/mt5/FyodorResearchExport_v3_20260923_234930_server');
      const candlesDir = path.join(toolsDir, 'candles');
      const labResearchDir = path.join(tempRoot, 'lab/research');

      fs.mkdirSync(candlesDir, { recursive: true });
      fs.mkdirSync(labResearchDir, { recursive: true });

      // Copy the pinned artifacts so their hashes match PINNED_HASHES
      fs.copyFileSync(
        path.join(repoRoot, 'tools/mt5/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv'),
        path.join(toolsDir, 'calendar_releases.csv')
      );
      fs.copyFileSync(
        path.join(repoRoot, 'lab/research/fms_episodes.jsonl'),
        path.join(labResearchDir, 'fms_episodes.jsonl')
      );
      fs.copyFileSync(
        path.join(repoRoot, 'lab/research/ifo_pilot_ledger.json'),
        path.join(labResearchDir, 'ifo_pilot_ledger.json')
      );
      fs.copyFileSync(
        path.join(repoRoot, 'lab/research/ifo_pilot_ledger.md'),
        path.join(labResearchDir, 'ifo_pilot_ledger.md')
      );

      // Load ONLY timestamps from pure timestamp fixture (no OHLC, no volume, no spread)
      const timestampFixturePath = path.join(repoRoot, 'lab/tests/fixtures/pre2023_h1_timestamps.json');
      expect(fs.existsSync(timestampFixturePath)).toBe(true);
      const timestamps: number[] = JSON.parse(fs.readFileSync(timestampFixturePath, 'utf8'));
      expect(timestamps.length).toBeGreaterThan(0);

      // Create a SYNTHETIC candles_EURUSD_H1.csv in tempRoot with synthetic prices
      const syntheticCandleLines = [
        'time,open,high,low,close,tick_volume,spread,real_volume,source_symbol,time_server_text,timestamp_convention,complete_at_export',
      ];

      for (const ts of timestamps) {
        if (ts >= SPLIT_TIMESTAMP) break;

        // Generate synthetic prices strictly within realistic bounds: 1.1000 to 1.1500
        // Real candidate EURUSD OHLC values are NEVER opened or used
        const synthOpen = 1.1000 + (ts % 1000) * 0.00005;
        const synthHigh = synthOpen + 0.0020;
        const synthLow = synthOpen - 0.0020;
        const synthClose = synthOpen + 0.0005;

        syntheticCandleLines.push(
          `${ts},${synthOpen.toFixed(5)},${synthHigh.toFixed(5)},${synthLow.toFixed(5)},${synthClose.toFixed(5)},100,10,0,"EURUSD",2020.01.01 00:00:00,trade_server_time,true`
        );
      }

      const synthCandlePath = path.join(candlesDir, 'candles_EURUSD_H1.csv');
      fs.writeFileSync(synthCandlePath, syntheticCandleLines.join('\n'), 'utf8');

      // Define explicit output paths in temp directory
      const outJsonPath = path.join(tempRoot, 'output_report.json');
      const outMdPath = path.join(tempRoot, 'output_report.md');

      // Execute full runner against the synthetic fixture directory
      const report = await runIfoPre2023Exploration({
        repoRoot: tempRoot,
        outputPathJson: outJsonPath,
        outputPathMd: outMdPath,
      });

      // FORENSIC AUDIT PROOF: Verify that real candidate candle CSV was NEVER opened
      for (const call of readFileSyncSpy.mock.calls) {
        expect(path.resolve(String(call[0]))).not.toBe(path.resolve(realCandlePath));
      }
      for (const call of createReadStreamSpy.mock.calls) {
        expect(path.resolve(String(call[0]))).not.toBe(path.resolve(realCandlePath));
      }

      // Restore spies
      readFileSyncSpy.mockRestore();
      createReadStreamSpy.mockRestore();

      // 1. Verify 40 actionable events
      expect(report.events.length).toBe(40);
      expect(report.primary6H4.summary.totalActionable).toBe(40);

      // 2. Verify Primary 6-H4 accounting (39 paired, 1 unavailable)
      expect(report.primary6H4.summary.pairedCount).toBe(39);
      expect(report.primary6H4.summary.unavailableCount).toBe(1);
      expect(report.primary6H4.pairs.length).toBe(39);
      expect(report.primary6H4.controls.length).toBe(40);

      // Verify Episode #27 control is explicitly recorded as CONTROL_UNAVAILABLE with reason
      const unavailControl = report.primary6H4.controls.find(c => c.actionableIndex === 27);
      expect(unavailControl).toBeDefined();
      expect(unavailControl!.status).toBe('CONTROL_UNAVAILABLE');
      expect(unavailControl!.exclusionReason).toBeDefined();

      // 3. Verify Secondary 12-H4 strict accounting (34 paired, 6 unavailable)
      expect(report.secondary12H4Strict.summary.pairedCount).toBe(34);
      expect(report.secondary12H4Strict.summary.unavailableCount).toBe(6);
      expect(report.secondary12H4Strict.pairs.length).toBe(34);
      expect(report.secondary12H4Strict.controls.length).toBe(40);

      // 4. Verify Secondary 12-H4 permissive accounting (35 paired, 5 unavailable)
      expect(report.secondary12H4Permissive.summary.pairedCount).toBe(35);
      expect(report.secondary12H4Permissive.summary.unavailableCount).toBe(5);
      expect(report.secondary12H4Permissive.pairs.length).toBe(35);
      expect(report.secondary12H4Permissive.controls.length).toBe(40);

      // 5. Verify 15:30 US morning overlap accounting: exactly 16 with and 7 without for 12:00 entries
      const noonEvents = report.events.filter(e => e.actionableIndex && [5,6,7,8,9,10,15,16,17,18,19,23,24,25,26,27,28,33,34,35,36,37,38].includes(e.actionableIndex));
      expect(noonEvents.length).toBe(23);
      const with1530 = noonEvents.filter(e => e.hasUs1530MorningRelease);
      const without1530 = noonEvents.filter(e => !e.hasUs1530MorningRelease);
      expect(with1530.length).toBe(16);
      expect(without1530.length).toBe(7);

      // 6. Verify Holm-Bonferroni adjusted p-values are computed
      expect(report.primary6H4.summary.pValueHolmAdjusted).toBeDefined();
      expect(report.secondary12H4Strict.summary.pValueHolmAdjusted).toBeDefined();

      // 7. Verify JSON and Markdown reports were written to disk
      expect(fs.existsSync(outJsonPath)).toBe(true);
      expect(fs.existsSync(outMdPath)).toBe(true);

      const jsonParsed = JSON.parse(fs.readFileSync(outJsonPath, 'utf8'));
      expect(jsonParsed.protocolVersion).toBe('1.2 FROZEN');
      expect(jsonParsed.decision).toBeDefined();
      expect(jsonParsed.primary6H4.controls.length).toBe(40);

      const mdContent = fs.readFileSync(outMdPath, 'utf8');
      expect(mdContent).toContain('German Ifo EURUSD Pilot Pre-2023 Exploration Report');
      expect(mdContent).toContain('39 resolved (1 unavailable)');
      expect(mdContent).toContain('34');

      // 8. Verify Holm-Bonferroni thresholds and labels in Markdown
      expect(mdContent).toContain('Holm-Bonferroni Step-Down Multiplicity Gate');
      expect(mdContent).toContain('cutoff $\\le 0.025$');
      expect(mdContent).toContain('vs $\\alpha = 0.05$');
      expect(mdContent).toContain('cutoff $\\le 0.050$');

      // 9. Verify Dual Cost Sensitivity Scenarios in Markdown
      expect(mdContent).toContain('Scenario A (Paired Executable Trades)');
      expect(mdContent).toContain('Scenario B (Event Friction vs. Frictionless Benchmark Control)');
      expect(mdContent).toContain('Scenario A Net $\\Delta$ Pips (Cost Cancels)');
      expect(mdContent).toContain('Scenario A Net $\\Delta$ Return (bps)');
      expect(mdContent).toContain('Scenario B Net $\\Delta$ Pips (Event Friction Only)');

      // 10. Verify Section 7 Table contains all 40 actionable episodes
      for (let i = 1; i <= 40; i++) {
        expect(mdContent).toContain(`| #${i} |`);
      }
      // Verify Episode #27 is explicitly presented as CONTROL_UNAVAILABLE with its exclusion reason
      expect(mdContent).toContain('| #27 |');
      expect(mdContent).toContain('`CONTROL_UNAVAILABLE`');
      expect(mdContent).toContain('EXCLUDED (');

      // Verify Episode #27 synthetic price drift and literal report row
      const ev27 = report.events.find(e => e.actionableIndex === 27);
      expect(ev27).toBeDefined();
      expect(ev27!.entryTimestamp).toBe(1632484800);
      expect(ev27!.entryPrice).toBe(1.14000);
      expect(ev27!.bars6.length).toBe(6);
      expect(ev27!.bars6[5]).toBe(1632729600); // 6th active H4 bar start (Mon 08:00 broker)
      expect(ev27!.bars6[5] + 3 * 3600).toBe(1632740400); // 4th H1 candle in 6th bar (Mon 11:00 broker)
      expect(ev27!.exitTimestamp6).toBe(1632744000); // bar end (Mon 12:00 broker)
      expect(ev27!.exitPrice6).toBe(1.12050);
      expect(ev27!.pipDrift6).toBeCloseTo(195.00, 5);

      const expectedRow27 =
        '| #27 | `2021-09-24 11:30:00` | **SHORT** | 1.14000 | 1.12050 | 195.00 | `CONTROL_UNAVAILABLE` | N/A | N/A | EXCLUDED (D_MINUS_7 rejected: High-importance EUR release conflict: CPI y/y@1631880000; D_PLUS_7 rejected: High-importance EUR release conflict: CPI y/y@1633089600; D_MINUS_14 rejected: High-importance EUR release conflict: ECB President Lagarde Speech@1631277000; D_PLUS_14 rejected: High-importance EUR release conflict: ECB President Lagarde Speech@1633705800) |';
      expect(mdContent).toContain(expectedRow27);

      // 11. Verify Manifest Fields in JSON and Markdown outputs
      expect(report.manifest).toBeDefined();
      expect(report.manifest.consumedPre2023H1Candles).toBeDefined();
      const expectedPre2023Count = timestamps.filter(ts => ts < SPLIT_TIMESTAMP).length;
      expect(report.manifest.consumedPre2023H1Candles.rowCount).toBe(expectedPre2023Count);
      expect(report.manifest.consumedPre2023H1Candles.sha256).toMatch(/^[a-f0-9]{64}$/);
      expect(report.manifest.consumedPre2023H1Candles.sha256WithHeader).toMatch(/^[a-f0-9]{64}$/);
      expect(report.implementation.sourceFilesSha256).toBeDefined();
      expect(Object.keys(report.implementation.sourceFilesSha256).length).toBeGreaterThanOrEqual(6);

      expect(jsonParsed.manifest).toBeDefined();
      expect(jsonParsed.manifest.consumedPre2023H1Candles.rowCount).toBe(expectedPre2023Count);
      expect(jsonParsed.implementation).toBeDefined();

      expect(mdContent).toContain('Consumed Pre-2023 H1 Rows');
      expect(mdContent).toContain('Analysis Git Commit');

      // Clean up temp directory
      fs.rmSync(tempRoot, { recursive: true, force: true });
    }, 30000);
  });
});
