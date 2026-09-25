/**
 * German Ifo Pre-2023 Exploration & Statistical Evaluation Engine.
 * Governed strictly by docs/FMS_PILOT_IFO_PROTOCOL.md (v1.2 FROZEN).
 *
 * Implements pure evaluation functions:
 * 1. Event and control return/drift calculations.
 * 2. Paired differences and win indicators.
 * 3. Seeded Mulberry32 permutation p-values, Wilcoxon, paired t-test.
 * 4. Cost sensitivity analysis (0 to 2 pips).
 * 5. Ordered decision rules (States 1, 2, 3).
 *
 * Decoupled from file I/O for 100% testability on synthetic fixtures.
 */

import {
  CandleH4,
  IfoEvaluatedEpisode,
  IfoEvaluatedControl,
  IfoPairedObservation,
  IfoCostSensitivityRow,
  IfoHorizonSummary,
  IfoDecisionEvaluation,
  IfoSubgroupStats,
  IfoPilotExplorationReportData,
  TradeDirection,
} from './ifoPilotAnalysisTypes.js';
import {
  runPairedSignFlipTest,
  computeWilcoxonSignedRank,
  computePairedTTest,
  computeHolmAdjustedPValues,
} from './ifoPermutationEngine.js';

export const PIP_SIZE = 0.0001; // Standard EURUSD pip

/**
 * Computes gross directional log return: d_i * ln(P_exit / P_entry).
 */
export function calculateLogReturn(direction: TradeDirection, entryPrice: number, exitPrice: number): number {
  if (entryPrice <= 0 || exitPrice <= 0) {
    throw new Error(`Invalid prices: entry=${entryPrice}, exit=${exitPrice}`);
  }
  const sign = direction === 'LONG' ? 1.0 : -1.0;
  return sign * Math.log(exitPrice / entryPrice);
}

/**
 * Computes gross directional pip drift: d_i * (P_exit - P_entry) / 0.0001.
 */
export function calculatePipDrift(direction: TradeDirection, entryPrice: number, exitPrice: number): number {
  if (entryPrice <= 0 || exitPrice <= 0) {
    throw new Error(`Invalid prices: entry=${entryPrice}, exit=${exitPrice}`);
  }
  const sign = direction === 'LONG' ? 1.0 : -1.0;
  return sign * ((exitPrice - entryPrice) / PIP_SIZE);
}

/**
 * Evaluates an event episode across 6-H4 and 12-H4 horizons from aggregated H4 candle paths.
 */
export function evaluateEvent(
  meta: {
    packageIndex: number;
    actionableIndex: number;
    releaseTimestamp: number;
    brokerDateTime: string;
    direction: TradeDirection;
    entryTimestamp: number;
    hasCrossCurrencyCollision: boolean;
    collidingCurrencies: string[];
    hasUs1530MorningRelease: boolean;
  },
  candles6: CandleH4[],
  candles12: CandleH4[]
): IfoEvaluatedEpisode {
  if (candles6.length !== 6) {
    throw new Error(`Expected exactly 6 H4 candles for episode ${meta.actionableIndex}, got ${candles6.length}`);
  }
  if (candles12.length !== 12) {
    throw new Error(`Expected exactly 12 H4 candles for episode ${meta.actionableIndex}, got ${candles12.length}`);
  }

  const entryPrice = candles6[0].open;
  const exitPrice6 = candles6[5].close;
  const exitTimestamp6 = candles6[5].timestamp + 14400;

  const exitPrice12 = candles12[11].close;
  const exitTimestamp12 = candles12[11].timestamp + 14400;

  const logReturn6 = calculateLogReturn(meta.direction, entryPrice, exitPrice6);
  const pipDrift6 = calculatePipDrift(meta.direction, entryPrice, exitPrice6);

  const logReturn12 = calculateLogReturn(meta.direction, entryPrice, exitPrice12);
  const pipDrift12 = calculatePipDrift(meta.direction, entryPrice, exitPrice12);

  return {
    packageIndex: meta.packageIndex,
    actionableIndex: meta.actionableIndex,
    releaseTimestamp: meta.releaseTimestamp,
    brokerDateTime: meta.brokerDateTime,
    direction: meta.direction,
    entryTimestamp: meta.entryTimestamp,
    entryPrice,
    exitTimestamp6,
    exitPrice6,
    logReturn6,
    pipDrift6,
    bars6: candles6.map(c => c.timestamp),
    exitTimestamp12,
    exitPrice12,
    logReturn12,
    pipDrift12,
    bars12: candles12.map(c => c.timestamp),
    hasCrossCurrencyCollision: meta.hasCrossCurrencyCollision,
    collidingCurrencies: meta.collidingCurrencies,
    hasUs1530MorningRelease: meta.hasUs1530MorningRelease,
  };
}

/**
 * Evaluates a matched control path.
 */
export function evaluateControl(
  meta: {
    actionableIndex: number;
    horizon: 6 | 12;
    direction: TradeDirection;
    controlChoice: 'D_MINUS_7' | 'D_PLUS_7' | 'D_MINUS_14' | 'D_PLUS_14' | null;
    status: 'PAIRED' | 'CONTROL_UNAVAILABLE';
    exclusionReason?: string;
  },
  candles: CandleH4[] | null
): IfoEvaluatedControl {
  if (meta.status === 'CONTROL_UNAVAILABLE' || !candles || candles.length === 0) {
    return {
      actionableIndex: meta.actionableIndex,
      horizon: meta.horizon,
      status: 'CONTROL_UNAVAILABLE',
      controlChoice: null,
      exclusionReason: meta.exclusionReason,
      direction: meta.direction,
      controlEntryTimestamp: null,
      controlEntryPrice: null,
      controlExitTimestamp: null,
      controlExitPrice: null,
      logReturn: null,
      pipDrift: null,
      bars: [],
    };
  }

  const expectedLength = meta.horizon;
  if (candles.length !== expectedLength) {
    throw new Error(
      `Control for actionable index ${meta.actionableIndex} has ${candles.length} candles, expected ${expectedLength}`
    );
  }

  const controlEntryTimestamp = candles[0].timestamp;
  const controlEntryPrice = candles[0].open;
  const controlExitPrice = candles[expectedLength - 1].close;
  const controlExitTimestamp = candles[expectedLength - 1].timestamp + 14400;

  const logReturn = calculateLogReturn(meta.direction, controlEntryPrice, controlExitPrice);
  const pipDrift = calculatePipDrift(meta.direction, controlEntryPrice, controlExitPrice);

  return {
    actionableIndex: meta.actionableIndex,
    horizon: meta.horizon,
    status: 'PAIRED',
    controlChoice: meta.controlChoice,
    direction: meta.direction,
    controlEntryTimestamp,
    controlEntryPrice,
    controlExitTimestamp,
    controlExitPrice,
    logReturn,
    pipDrift,
    bars: candles.map(c => c.timestamp),
  };
}

/**
 * Pairs an event episode with its matched control observation.
 */
export function pairObservations(
  event: IfoEvaluatedEpisode,
  control: IfoEvaluatedControl,
  horizon: 6 | 12
): IfoPairedObservation {
  if (event.actionableIndex !== control.actionableIndex) {
    throw new Error(
      `Mismatched actionable index: event=${event.actionableIndex}, control=${control.actionableIndex}`
    );
  }
  if (control.status !== 'PAIRED' || control.logReturn === null || control.pipDrift === null) {
    throw new Error(`Cannot pair unavailable control for episode ${event.actionableIndex}`);
  }

  const eventReturn = horizon === 6 ? event.logReturn6 : event.logReturn12;
  const eventPipDrift = horizon === 6 ? event.pipDrift6 : event.pipDrift12;
  const controlReturn = control.logReturn;
  const controlPipDrift = control.pipDrift;

  const deltaReturn = eventReturn - controlReturn;
  const deltaPipDrift = eventPipDrift - controlPipDrift;
  const isEventWin = deltaReturn > 0;

  return {
    actionableIndex: event.actionableIndex,
    horizon,
    direction: event.direction,
    eventTimestamp: event.releaseTimestamp,
    controlTimestamp: control.controlEntryTimestamp!,
    controlChoice: control.controlChoice!,
    eventEntryPrice: event.entryPrice,
    controlEntryPrice: control.controlEntryPrice!,
    eventReturn,
    controlReturn,
    deltaReturn,
    eventPipDrift,
    controlPipDrift,
    deltaPipDrift,
    isEventWin,
  };
}

/**
 * Computes cost sensitivity analysis across hypothetical friction levels c \in {0.0, 0.5, 1.0, 1.5, 2.0} pips.
 * Evaluates both:
 * Scenario A: Paired Executable Trades (equal cost c on both trades cancels in the paired difference)
 * Scenario B: Event Trade Net of Cost vs. Frictionless Benchmark Control (difference reduced by c)
 */
export function computeCostSensitivity(
  pairs: IfoPairedObservation[],
  events: IfoEvaluatedEpisode[],
  horizon: 6 | 12
): IfoCostSensitivityRow[] {
  const frictionLevels = [0.0, 0.5, 1.0, 1.5, 2.0];
  const nPairs = pairs.length;
  const nEvents = events.length;

  const eventPips = events.map(e => (horizon === 6 ? e.pipDrift6 : e.pipDrift12));
  const grossMeanEventPips = eventPips.reduce((a, b) => a + b, 0) / nEvents;

  const deltaPips = pairs.map(p => p.deltaPipDrift);
  const grossMeanDeltaPips = deltaPips.reduce((a, b) => a + b, 0) / nPairs;

  const deltaReturns = pairs.map(p => p.deltaReturn);
  const grossMeanDeltaReturn = deltaReturns.reduce((a, b) => a + b, 0) / nPairs;

  return frictionLevels.map(costPips => {
    const netMeanEventPips = grossMeanEventPips - costPips;

    // -------------------------------------------------------------------------
    // Scenario A: Paired Executable Trades (Equal Cost c in Pips on Both Trades)
    // -------------------------------------------------------------------------
    // 1. Pips: Equal cost c cancels identically: (event - c) - (control - c) = event - control
    const scenarioA_EqualCostDeltaPips = grossMeanDeltaPips;

    // 2. Log Return: Each leg incurs friction relative to its distinct entry price:
    //    R_{event, net} = R_{event} - (c * 1e-4) / P_{entry, event}
    //    R_{control, net} = R_{control} - (c * 1e-4) / P_{entry, control}
    //    Delta_R_{net} = R_{event, net} - R_{control, net}
    let sumDeltaReturnA = 0;
    let winsA = 0;
    for (const p of pairs) {
      const penaltyEvent = (costPips * PIP_SIZE) / p.eventEntryPrice;
      const penaltyControl = (costPips * PIP_SIZE) / p.controlEntryPrice;
      const netEventReturn = p.eventReturn - penaltyEvent;
      const netControlReturn = p.controlReturn - penaltyControl;
      const netDeltaReturn = netEventReturn - netControlReturn;
      sumDeltaReturnA += netDeltaReturn;
      if (netDeltaReturn > 0) winsA++;
    }
    const scenarioA_EqualCostDeltaReturn = sumDeltaReturnA / nPairs;
    const scenarioA_WinRate = winsA / nPairs;

    // -------------------------------------------------------------------------
    // Scenario B: Event Trade Net of Cost vs. Frictionless Benchmark Control
    // -------------------------------------------------------------------------
    // 1. Pips: (event - c) - control = delta - c
    const scenarioB_EventOnlyNetDeltaPips = grossMeanDeltaPips - costPips;

    // 2. Log Return: Only event leg incurs friction:
    //    R_{event, net} = R_{event} - (c * 1e-4) / P_{entry, event}
    //    Delta_R_{net} = R_{event, net} - R_{control}
    let sumDeltaReturnB = 0;
    let winsB = 0;
    for (const p of pairs) {
      const penaltyEvent = (costPips * PIP_SIZE) / p.eventEntryPrice;
      const netEventReturn = p.eventReturn - penaltyEvent;
      const netDeltaReturn = netEventReturn - p.controlReturn;
      sumDeltaReturnB += netDeltaReturn;
      if (netDeltaReturn > 0) winsB++;
    }
    const scenarioB_EventOnlyNetDeltaReturn = sumDeltaReturnB / nPairs;
    const scenarioB_WinRate = winsB / nPairs;

    return {
      costPips,
      grossMeanEventPips,
      netMeanEventPips,
      scenarioA_EqualCostDeltaPips,
      scenarioA_EqualCostDeltaReturn,
      scenarioA_WinRate,
      scenarioB_EventOnlyNetDeltaPips,
      scenarioB_EventOnlyNetDeltaReturn,
      scenarioB_WinRate,
      grossMeanDeltaPips,
      netMeanDeltaPips: scenarioB_EventOnlyNetDeltaPips,
      grossMeanDeltaReturn,
      netMeanDeltaReturn: scenarioB_EventOnlyNetDeltaReturn,
      winRateNet: scenarioB_WinRate,
    };
  });
}

function computeSubgroupStats(pairs: IfoPairedObservation[]): IfoSubgroupStats {
  const n = pairs.length;
  if (n === 0) {
    return { count: 0, meanDeltaReturn: 0, meanDeltaPips: 0, winRate: 0 };
  }
  let sumR = 0;
  let sumPips = 0;
  let wins = 0;
  for (const p of pairs) {
    sumR += p.deltaReturn;
    sumPips += p.deltaPipDrift;
    if (p.isEventWin) wins++;
  }
  return {
    count: n,
    meanDeltaReturn: sumR / n,
    meanDeltaPips: sumPips / n,
    winRate: wins / n,
  };
}

/**
 * Computes complete horizon statistical summary.
 */
export function summarizeHorizon(
  horizon: 6 | 12,
  horizonLabel: string,
  events: IfoEvaluatedEpisode[],
  pairs: IfoPairedObservation[],
  unavailableCount: number,
  options: { seed?: number; draws?: number } = {}
): IfoHorizonSummary {
  const nActionable = events.length; // 40
  const nPaired = pairs.length;

  const eventReturns = pairs.map(p => p.eventReturn);
  const controlReturns = pairs.map(p => p.controlReturn);
  const deltaReturns = pairs.map(p => p.deltaReturn);
  const deltaPips = pairs.map(p => p.deltaPipDrift);

  const meanEventReturn = eventReturns.reduce((a, b) => a + b, 0) / nPaired;
  const meanControlReturn = controlReturns.reduce((a, b) => a + b, 0) / nPaired;
  const meanDeltaReturn = deltaReturns.reduce((a, b) => a + b, 0) / nPaired;

  // Median delta return
  const sortedDelta = [...deltaReturns].sort((a, b) => a - b);
  const mid = Math.floor(nPaired / 2);
  const medianDeltaReturn = nPaired % 2 !== 0 ? sortedDelta[mid] : (sortedDelta[mid - 1] + sortedDelta[mid]) / 2;

  // Standard deviation
  let sumSq = 0;
  for (const d of deltaReturns) sumSq += (d - meanDeltaReturn) * (d - meanDeltaReturn);
  const stdDeltaReturn = Math.sqrt(sumSq / (nPaired - 1));

  // Event drift over all 40 actionable episodes
  const allEventPips = events.map(e => (horizon === 6 ? e.pipDrift6 : e.pipDrift12));
  const meanEventPipDrift = allEventPips.reduce((a, b) => a + b, 0) / nActionable;

  const meanControlPipDrift = pairs.map(p => p.controlPipDrift).reduce((a, b) => a + b, 0) / nPaired;
  const meanDeltaPipDrift = deltaPips.reduce((a, b) => a + b, 0) / nPaired;

  // Win rate
  const pairedWins = pairs.filter(p => p.isEventWin).length;
  const pairedWinRate = pairedWins / nPaired;

  // Statistical tests
  const permResult = runPairedSignFlipTest(deltaReturns, {
    draws: options.draws ?? 100000,
    seed: options.seed ?? 20260925,
  });
  const wilcoxonResult = computeWilcoxonSignedRank(deltaReturns);
  const tTestResult = computePairedTTest(deltaReturns);

  // Cost sensitivity
  const costSensitivity = computeCostSensitivity(pairs, events, horizon);

  // Subgroups by year
  const yearDistribution: Record<string, IfoSubgroupStats> = {};
  for (const year of ['2018', '2019', '2020', '2021', '2022']) {
    const yearPairs = pairs.filter(p => {
      const ev = events.find(e => e.actionableIndex === p.actionableIndex)!;
      return ev.brokerDateTime.startsWith(year);
    });
    yearDistribution[year] = computeSubgroupStats(yearPairs);
  }

  // Cross-currency collision partition
  const collisionPairs = pairs.filter(p => {
    const ev = events.find(e => e.actionableIndex === p.actionableIndex)!;
    return ev.hasCrossCurrencyCollision;
  });
  const nonCollisionPairs = pairs.filter(p => {
    const ev = events.find(e => e.actionableIndex === p.actionableIndex)!;
    return !ev.hasCrossCurrencyCollision;
  });
  const collisionPartition = {
    collision: computeSubgroupStats(collisionPairs),
    nonCollision: computeSubgroupStats(nonCollisionPairs),
  };

  // US Morning release overlap partition
  const withUsPairs = pairs.filter(p => {
    const ev = events.find(e => e.actionableIndex === p.actionableIndex)!;
    return ev.hasUs1530MorningRelease;
  });
  const withoutUsPairs = pairs.filter(p => {
    const ev = events.find(e => e.actionableIndex === p.actionableIndex)!;
    return !ev.hasUs1530MorningRelease;
  });
  const usMorningOverlapPartition = {
    with1530Release: computeSubgroupStats(withUsPairs),
    without1530Release: computeSubgroupStats(withoutUsPairs),
  };

  // Outliers: absolute paired delta return > 2 * std
  const outliers: Array<{
    actionableIndex: number;
    eventTimestamp: number;
    brokerDateTime: string;
    direction: TradeDirection;
    deltaReturn: number;
    deltaPips: number;
  }> = [];
  for (const p of pairs) {
    if (Math.abs(p.deltaReturn - meanDeltaReturn) > 2.0 * stdDeltaReturn) {
      const ev = events.find(e => e.actionableIndex === p.actionableIndex)!;
      outliers.push({
        actionableIndex: p.actionableIndex,
        eventTimestamp: p.eventTimestamp,
        brokerDateTime: ev.brokerDateTime,
        direction: p.direction,
        deltaReturn: p.deltaReturn,
        deltaPips: p.deltaPipDrift,
      });
    }
  }

  return {
    horizonBars: horizon,
    horizonLabel,
    totalActionable: nActionable,
    pairedCount: nPaired,
    unavailableCount,
    meanEventReturn,
    meanControlReturn,
    meanDeltaReturn,
    medianDeltaReturn,
    stdDeltaReturn,
    meanEventPipDrift,
    meanControlPipDrift,
    meanDeltaPipDrift,
    pairedWins,
    pairedWinRate,
    pValuePermutation: permResult.pValue,
    pValueWilcoxon: wilcoxonResult.pValueOneSided,
    wilcoxonZeroCount: wilcoxonResult.zeroCount,
    wilcoxonTieCorrection: wilcoxonResult.tieCorrection,
    pValueTTest: tTestResult.pValueOneSided,
    tTestDegreesOfFreedom: tTestResult.degreesOfFreedom,
    costSensitivity,
    yearDistribution,
    collisionPartition,
    usMorningOverlapPartition,
    tier1UsInteractionNote:
      'Descriptive Tier-1 US release interaction (NFP, CPI, FOMC) requires frozen protocol specification addendum defining MT5 series identities and exact exposure windows prior to execution.',
    outliers,
  };
}

/**
 * Evaluates ordered decision rules (Section 11 of frozen protocol).
 */
export function evaluateDecisionRules(
  summary6: IfoHorizonSummary
): IfoDecisionEvaluation {
  const pVal = summary6.pValuePermutation;
  const deltaRMean = summary6.meanDeltaReturn;
  const barDeltaPips = summary6.meanEventPipDrift;
  const winRate = summary6.pairedWinRate;

  // Step 1: Check Inconclusive / Negative Signal
  if (pVal >= 0.10 || deltaRMean <= 0.0) {
    let reason = '';
    if (pVal >= 0.10 && deltaRMean <= 0.0) {
      reason = `Permutation p-value (${pVal.toFixed(4)}) >= 0.10 and sample mean paired difference Delta_R (${deltaRMean.toFixed(5)}) <= 0.0`;
    } else if (pVal >= 0.10) {
      reason = `Permutation p-value (${pVal.toFixed(4)}) >= 0.10`;
    } else {
      reason = `Sample mean paired difference Delta_R (${deltaRMean.toFixed(5)}) <= 0.0`;
    }

    return {
      decisionState: 'STATE_3_NO_CONVINCING_EVIDENCE',
      stateTitle: 'State 3: No Convincing Evidence in this Sample',
      operationalMandate:
        'Conclude that there is no convincing evidence in this sample of delayed post-announcement drift for German Ifo on EURUSD. Archive pilot with complete negative report. Zero parameter tweaking, indicator substitution, or horizon hunting is permitted.',
      criteria: {
        step1Failed: true,
        step1Reason: reason,
        step2Fragile: false,
        state1Plausible: false,
      },
    };
  }

  // Step 2: Check Borderline / Economically Fragile Signal
  if (pVal >= 0.05 || barDeltaPips < 1.0 || winRate < 0.55) {
    let subCase: '2A_MARGINAL_SIGNIFICANCE' | '2B_COMMERCIALLY_INSIGNIFICANT' | '2C_OUTLIER_DOMINATED';
    let reason = '';

    if (pVal >= 0.05) {
      subCase = '2A_MARGINAL_SIGNIFICANCE';
      reason = `Marginal statistical significance: p-value (${pVal.toFixed(4)}) is between 0.05 and 0.10`;
    } else if (barDeltaPips < 1.0) {
      subCase = '2B_COMMERCIALLY_INSIGNIFICANT';
      reason = `Commercially insignificant: event-trade gross pip drift (${barDeltaPips.toFixed(2)} pips) fails to clear the 1.0 pip economic hurdle`;
    } else {
      subCase = '2C_OUTLIER_DOMINATED';
      reason = `Outlier-dominated / inconsistent: paired win rate (${(winRate * 100).toFixed(1)}%) < 55%`;
    }

    return {
      decisionState: 'STATE_2_INCONCLUSIVE_FRAGILE_EVIDENCE',
      stateTitle: 'State 2: Inconclusive / Economically Fragile Evidence',
      operationalMandate:
        'Document findings in post-mortem report; archive pilot as inconclusive; prohibit promotion to demo trading or canvas integration.',
      criteria: {
        step1Failed: false,
        step2Fragile: true,
        step2SubCase: subCase,
        step2Reason: reason,
        state1Plausible: false,
      },
    };
  }

  // Step 3: State 1 Plausible In-Sample Anomaly
  return {
    decisionState: 'STATE_1_PLAUSIBLE_IN_SAMPLE_ANOMALY',
    stateTitle: 'State 1: Plausible In-Sample Anomaly Warranting Out-of-Sample Audit',
    operationalMandate:
      'The exploratory sample demonstrates evidence of directional drift exceeding matched controls and basic friction floors. Advance to Milestone 5 for out-of-sample audit on the presently uninspected post-2022 historical holdout.',
    criteria: {
      step1Failed: false,
      step2Fragile: false,
      state1Plausible: true,
    },
  };
}

export interface HolmEvaluation {
  rank: 1 | 2;
  rawP: number;
  cutoff: number; // 0.025 or 0.050
  adjustedP: number;
  cleared: boolean;
  disposition: string;
}

/**
 * Dynamically evaluates Holm step-down family by sorting raw p-values before assigning
 * step-down cutoffs (0.025 for Rank 1, 0.050 for Rank 2).
 */
export function evaluateHolmFamily(
  rawP6: number,
  rawP12: number,
  adjustedP6: number,
  adjustedP12: number
): {
  primary6: HolmEvaluation;
  secondary12: HolmEvaluation;
} {
  const p6IsRank1 = rawP6 <= rawP12;

  // Rank 1 evaluation: cutoff alpha / 2 = 0.025
  const rank1Raw = p6IsRank1 ? rawP6 : rawP12;
  const rank1Cleared = rank1Raw <= 0.025;

  // Rank 2 evaluation: cutoff alpha / 1 = 0.050, eligible only if Rank 1 cleared
  const rank2Raw = p6IsRank1 ? rawP12 : rawP6;
  const rank2Cleared = rank1Cleared && rank2Raw <= 0.050;

  const eval6: HolmEvaluation = p6IsRank1
    ? {
        rank: 1,
        rawP: rawP6,
        cutoff: 0.025,
        adjustedP: adjustedP6,
        cleared: rank1Cleared,
        disposition: rank1Cleared
          ? 'Cleared Step 1 (Rank 1: raw p <= 0.025)'
          : 'Failed Step 1 (Rank 1: raw p > 0.025)',
      }
    : {
        rank: 2,
        rawP: rawP6,
        cutoff: 0.050,
        adjustedP: adjustedP6,
        cleared: rank2Cleared,
        disposition: !rank1Cleared
          ? 'Ineligible (Rank 2: Step 1 failed)'
          : rank2Cleared
          ? 'Cleared Step 2 (Rank 2: raw p <= 0.050)'
          : 'Failed Step 2 (Rank 2: raw p > 0.050)',
      };

  const eval12: HolmEvaluation = !p6IsRank1
    ? {
        rank: 1,
        rawP: rawP12,
        cutoff: 0.025,
        adjustedP: adjustedP12,
        cleared: rank1Cleared,
        disposition: rank1Cleared
          ? 'Cleared Step 1 (Rank 1: raw p <= 0.025)'
          : 'Failed Step 1 (Rank 1: raw p > 0.025)',
      }
    : {
        rank: 2,
        rawP: rawP12,
        cutoff: 0.050,
        adjustedP: adjustedP12,
        cleared: rank2Cleared,
        disposition: !rank1Cleared
          ? 'Ineligible (Rank 2: Step 1 failed)'
          : rank2Cleared
          ? 'Cleared Step 2 (Rank 2: raw p <= 0.050)'
          : 'Failed Step 2 (Rank 2: raw p > 0.050)',
      };

  return { primary6: eval6, secondary12: eval12 };
}

/**
 * Generates an auditable, comprehensive Markdown exploration report.
 */
export function generateIfoExplorationMarkdownReport(
  data: IfoPilotExplorationReportData
): string {
  const p6 = data.primary6H4.summary;
  const p12Strict = data.secondary12H4Strict.summary;
  const p12Perm = data.secondary12H4Permissive.summary;
  const dec = data.decision;

  const adjP6 = p6.pValueHolmAdjusted ?? p6.pValuePermutation;
  const adjP12 = p12Strict.pValueHolmAdjusted ?? p12Strict.pValuePermutation;
  const holm = evaluateHolmFamily(
    p6.pValuePermutation,
    p12Strict.pValuePermutation,
    adjP6,
    adjP12
  );
  const h6 = holm.primary6;
  const h12 = holm.secondary12;

  const lines: string[] = [
    '# German Ifo EURUSD Pilot Pre-2023 Exploration Report (Milestone 4)',
    '',
    '> [!IMPORTANT]',
    `> **GOVERNANCE STATUS: EXPLORATION REPORT (v${data.protocolVersion} FROZEN PROTOCOL)**  `,
    `> Evaluated strictly under \`docs/FMS_PILOT_IFO_PROTOCOL.md\`.  `,
    `> Chronological Split Boundary: \`2023-01-01 00:00:00\` broker trade-server time (\`timestamp = ${data.splitTimestamp}\`).  `,
    `> Evaluation Timestamp: \`${data.evaluatedAt}\`.  `,
    `> Post-2022 historical holdout (\`timestamp >= 1672531200\`) remains strictly sealed and uninspected.`,
    '',
    '---',
    '',
    '## 1. Cryptographic Provenance Hashes & Manifests (Verified)',
    '',
    '| Input / Manifest Component | Verified Identifier / SHA-256 Hash | Status / Details |',
    '|---|---|---|',
    `| \`calendar_releases.csv\` | \`${data.provenanceHashes.rawCalendarSha256}\` | Match Pinned |`,
    `| \`fms_episodes.jsonl\` | \`${data.provenanceHashes.episodesJsonlSha256}\` | Match Pinned |`,
    `| \`ifo_pilot_ledger.json\` | \`${data.provenanceHashes.pilotLedgerJsonSha256}\` | Match Pinned |`,
    `| \`ifo_pilot_ledger.md\` | \`${data.provenanceHashes.pilotLedgerMdSha256}\` | Match Pinned |`,
    ...(data.manifest?.consumedPre2023H1Candles
      ? [
          `| **Consumed Pre-2023 H1 Rows** | \`${data.manifest.consumedPre2023H1Candles.sha256}\` | ${data.manifest.consumedPre2023H1Candles.rowCount} rows (${data.manifest.consumedPre2023H1Candles.firstTimestamp} → ${data.manifest.consumedPre2023H1Candles.lastTimestamp}) |`,
          `| Consumed Pre-2023 H1 (w/ Header) | \`${data.manifest.consumedPre2023H1Candles.sha256WithHeader}\` | Header included |`,
        ]
      : []),
    ...(data.implementation
      ? [
          `| **Analysis Git Commit** | \`${data.implementation.gitCommit ?? 'UNCOMMITTED'}\` | Immutable Implementation ID |`,
        ]
      : []),
    '',
    '---',
    '',
    '## 2. Decision State & Governance Evaluation',
    '',
    `### **${dec.stateTitle}**`,
    '',
    `- **Decision State Code**: \`${dec.decisionState}\``,
    `- **Operational Mandate**: ${dec.operationalMandate}`,
    '',
    '### Step-by-Step Gate Evaluation:',
    `- **Step 1 (Inconclusive / Negative Signal: $p \\ge 0.10$ OR $\\Delta \\bar{R} \\le 0$)**: ${dec.criteria.step1Failed ? `**FAILED** (${dec.criteria.step1Reason})` : 'PASSED'}`,
    `- **Step 2 (Borderline / Economically Fragile: $p \\ge 0.05$ OR $\\bar{\\Delta}_{pips} < 1.0$ OR WinRate $< 55\%$)**: ${dec.criteria.step2Fragile ? `**TRIGGERED** (${dec.criteria.step2Reason})` : 'PASSED'}`,
    `- **Step 3 (Plausible In-Sample Anomaly)**: ${dec.criteria.state1Plausible ? '**CONFIRMED**' : 'NOT MET'}`,
    '',
    '---',
    '',
    '## 3. Primary Testing Horizon: 6 H4 (First Trading Day / 24 Active Hours)',
    '',
    '| Metric | Value | Protocol Threshold / Hurdle | Disposition |',
    '|---|---|---|---|',
    `| Actionable Event Episodes ($N$) | **${p6.totalActionable}** | 40 | Complete Sample |`,
    `| Price-Blind Paired Controls ($N_{\\text{paired}}$) | **${p6.pairedCount}** | 39 resolved (1 unavailable) | Clean Pairs |`,
    `| Sample Mean Paired Excess Log Return ($\\Delta \\bar{R}$) | **${(p6.meanDeltaReturn * 10000).toFixed(2)} bps** (${p6.meanDeltaReturn.toFixed(6)}) | $> 0.0$ | ${p6.meanDeltaReturn > 0 ? 'Positive' : 'Non-Positive'} |`,
    `| Event Mean Gross Pip Drift ($\\bar{\\Delta}_{\\text{pips}}$) | **${p6.meanEventPipDrift.toFixed(2)} pips** | $\\ge 1.0\\text{ pip}$ | ${p6.meanEventPipDrift >= 1.0 ? 'Hurdle Cleared' : 'Below Hurdle'} |`,
    `| Paired Win Rate ($R_{\\text{event}} > R_{\\text{ctrl}}$) | **${(p6.pairedWinRate * 100).toFixed(1)}%** (${p6.pairedWins}/${p6.pairedCount}) | $\\ge 55.0\\%$ | ${p6.pairedWinRate >= 0.55 ? 'Hurdle Cleared' : 'Below Hurdle'} |`,
    `| Seeded Mulberry32 Permutation $p$-value (raw) | **${p6.pValuePermutation.toFixed(5)}** | $\\alpha = 0.05$ (1-sided) | ${p6.pValuePermutation < 0.05 ? 'Significant ($p < 0.05$)' : 'Not Significant'} |`,
    `| Holm-Bonferroni Step-Down Multiplicity Gate | **Rank ${h6.rank} of 2 | Raw: ${p6.pValuePermutation.toFixed(5)} (cutoff $\\le ${h6.cutoff.toFixed(3)}$) | Adjusted: ${h6.adjustedP.toFixed(5)} (vs $\\alpha = 0.05$)** | Step-down family threshold | ${h6.disposition} |`,
    `| Student's $t$-test $p$-value ($df = ${p6.tTestDegreesOfFreedom ?? 38}$) | **${p6.pValueTTest.toFixed(5)}** | Diagnostic ($df = 38$) | Student-$t$ Tail |`,
    `| Wilcoxon Signed-Rank $p$-value | **${p6.pValueWilcoxon.toFixed(5)}** | Diagnostic (Zeros dropped, Tie-corrected) | Non-parametric |`,
    '',
    '---',
    '',
    '## 4. Secondary Testing Horizon: 12 H4 (Second Trading Day / 48 Active Hours)',
    '',
    '### A. Frozen Strict Audit ($N_{\\text{paired}} = 34$, 0 Duplicates, 6 Unavailable)',
    '',
    '| Metric | Strict 12 H4 Value | Permissive 12 H4 Diagnostic ($N=35$) |',
    '|---|---|---|',
    `| Paired Observations | **${p12Strict.pairedCount}** | **${p12Perm.pairedCount}** |`,
    `| Mean Paired Excess Log Return ($\\Delta \\bar{R}$) | **${(p12Strict.meanDeltaReturn * 10000).toFixed(2)} bps** | **${(p12Perm.meanDeltaReturn * 10000).toFixed(2)} bps** |`,
    `| Event Mean Pip Drift | **${p12Strict.meanEventPipDrift.toFixed(2)} pips** | **${p12Perm.meanEventPipDrift.toFixed(2)} pips** |`,
    `| Paired Win Rate | **${(p12Strict.pairedWinRate * 100).toFixed(1)}%** (${p12Strict.pairedWins}/${p12Strict.pairedCount}) | **${(p12Perm.pairedWinRate * 100).toFixed(1)}%** (${p12Perm.pairedWins}/${p12Perm.pairedCount}) |`,
    `| Seeded Permutation $p$-value (raw) | **${p12Strict.pValuePermutation.toFixed(5)}** | **${p12Perm.pValuePermutation.toFixed(5)}** |`,
    `| Holm-Bonferroni Multiplicity Gate | **Rank ${h12.rank} of 2 | Raw: ${p12Strict.pValuePermutation.toFixed(5)} (cutoff $\\le ${h12.cutoff.toFixed(3)}$) | Adjusted: ${h12.adjustedP.toFixed(5)} (vs $\\alpha = 0.05$)** | ${h12.disposition} |`,
    `| Student's $t$-test $p$-value | **${p12Strict.pValueTTest.toFixed(5)}** | **${p12Perm.pValueTTest.toFixed(5)}** |`,
    `| Wilcoxon Signed-Rank $p$-value | **${p12Strict.pValueWilcoxon.toFixed(5)}** | **${p12Perm.pValueWilcoxon.toFixed(5)}** |`,
    '',
    '---',
    '',
    '## 5. Cost Sensitivity Analysis (Dimension: Pips & Log Return)',
    '',
    '> [!NOTE]',
    '> **Explicit Distinct Friction Scenarios**:',
    '> 1. **Scenario A (Paired Executable Trades)**: If both the event trade and matched control trade are treated as executable trades each bearing round-turn friction penalty $c_{\\text{pips}}$:',
    '>    - **In pips**: Equal cost $c$ cancels identically in the paired difference: $(\\Delta_{\\text{event}} - c) - (\\Delta_{\\text{control}} - c) = \\Delta_{\\text{gross paired}}$.',
    '>    - **In log return**: Because event and control trades enter at distinct price levels ($P_{\\text{entry}, e} \\ne P_{\\text{entry}, c}$), their log-return penalties differ: $R_{e, \\text{net}} = R_e - (c \\cdot 10^{-4}) / P_{\\text{entry}, e}$ and $R_{c, \\text{net}} = R_c - (c \\cdot 10^{-4}) / P_{\\text{entry}, c}$. Paired net return difference and win rate are evaluated from these respective penalties.',
    '> 2. **Scenario B (Event Friction vs. Frictionless Benchmark Control)**: If the matched control represents an unexecutable, frictionless macroeconomic baseline:',
    '>    - **In pips**: $(\\Delta_{\\text{event}} - c) - \\Delta_{\\text{control}} = \\Delta_{\\text{gross paired}} - c$.',
    '>    - **In log return**: $R_{e, \\text{net}} - R_c = \\Delta R_{\\text{gross}} - (c \\cdot 10^{-4}) / P_{\\text{entry}, e}$.',
    '> *Neither scenario alters the frozen gross primary statistic.*',
    '',
    '| Friction Penalty ($c_{\\text{pips}}$) | Gross Event Pips | Net Event Pips | Scenario A Net $\\Delta$ Pips (Cost Cancels) | Scenario A Net $\\Delta$ Return (bps) | Scenario A Win Rate | Scenario B Net $\\Delta$ Pips (Event Friction Only) | Scenario B Net $\\Delta$ Return (bps) | Scenario B Win Rate |',
    '|---|---|---|---|---|---|---|---|---|',
  ];

  for (const row of p6.costSensitivity) {
    lines.push(
      `| **${row.costPips.toFixed(1)} pips** | ${row.grossMeanEventPips.toFixed(2)} | ${row.netMeanEventPips.toFixed(2)} | ${row.scenarioA_EqualCostDeltaPips.toFixed(2)} | ${(row.scenarioA_EqualCostDeltaReturn * 10000).toFixed(2)} | ${(row.scenarioA_WinRate * 100).toFixed(1)}% | ${row.scenarioB_EventOnlyNetDeltaPips.toFixed(2)} | ${(row.scenarioB_EventOnlyNetDeltaReturn * 10000).toFixed(2)} | ${(row.scenarioB_WinRate * 100).toFixed(1)}% |`
    );
  }

  lines.push(
    '',
    '---',
    '',
    '## 6. Subgroups & Descriptive Diagnostics',
    '',
    '### A. Yearly Performance Breakdown (6 H4)',
    '',
    '| Year | Pairs ($N$) | Mean $\\Delta \\bar{R}$ (bps) | Mean $\\Delta$ Pips | Win Rate |',
    '|---|---|---|---|---|'
  );

  for (const [year, stats] of Object.entries(p6.yearDistribution)) {
    lines.push(
      `| **${year}** | ${stats.count} | ${(stats.meanDeltaReturn * 10000).toFixed(2)} | ${stats.meanDeltaPips.toFixed(2)} | ${(stats.winRate * 100).toFixed(1)}% |`
    );
  }

  lines.push(
    '',
    '### B. Same-Time Cross-Currency Collision Partition',
    '',
    '| Partition | Pairs ($N$) | Mean $\\Delta \\bar{R}$ (bps) | Mean $\\Delta$ Pips | Win Rate |',
    '|---|---|---|---|---|',
    `| **Collision Sessions (GBP)** | ${p6.collisionPartition.collision.count} | ${(p6.collisionPartition.collision.meanDeltaReturn * 10000).toFixed(2)} | ${p6.collisionPartition.collision.meanDeltaPips.toFixed(2)} | ${(p6.collisionPartition.collision.winRate * 100).toFixed(1)}% |`,
    `| **Collision-Free Sessions** | ${p6.collisionPartition.nonCollision.count} | ${(p6.collisionPartition.nonCollision.meanDeltaReturn * 10000).toFixed(2)} | ${p6.collisionPartition.nonCollision.meanDeltaPips.toFixed(2)} | ${(p6.collisionPartition.nonCollision.winRate * 100).toFixed(1)}% |`,
    '',
    '### C. US 15:30 Morning Release Overlap Partition',
    '',
    '| Partition | Pairs ($N$) | Mean $\\Delta \\bar{R}$ (bps) | Mean $\\Delta$ Pips | Win Rate |',
    '|---|---|---|---|---|',
    `| **With 15:30 USD Release in Entry Bar** | ${p6.usMorningOverlapPartition.with1530Release.count} | ${(p6.usMorningOverlapPartition.with1530Release.meanDeltaReturn * 10000).toFixed(2)} | ${p6.usMorningOverlapPartition.with1530Release.meanDeltaPips.toFixed(2)} | ${(p6.usMorningOverlapPartition.with1530Release.winRate * 100).toFixed(1)}% |`,
    `| **Without 15:30 USD Release in Entry Bar** | ${p6.usMorningOverlapPartition.without1530Release.count} | ${(p6.usMorningOverlapPartition.without1530Release.meanDeltaReturn * 10000).toFixed(2)} | ${p6.usMorningOverlapPartition.without1530Release.meanDeltaPips.toFixed(2)} | ${(p6.usMorningOverlapPartition.without1530Release.winRate * 100).toFixed(1)}% |`,
    '',
    '### D. US Tier-1 Macro Interaction (NFP / CPI / FOMC)',
    '',
    '> [!NOTE]',
    '> **Diagnostic Status: NOT_EVALUATED (Pending Independent Pre-Outcome Addendum Review)**  ',
    '> Forensic catalog reconciliation of raw `calendar_releases.csv` identifies:',
    '> - US Headline CPI m/m: `840030005` (139 releases, importance: high)',
    '> - US Nonfarm Payrolls (NFP): `840030016` (140 releases, importance: high)',
    '> - Federal Reserve Monetary Policy (FOMC): spans multiple distinct series (`840050014` Rate Decision [95 releases], `840050002` Statement [91 releases], `840050018` Press Conference [74 releases], `840050004` Minutes [94 releases], `840050003` Economic Projections [46 releases]).',
    '>',
    '> Due to standard calendar scheduling (NFP early month, CPI mid month, Ifo late month), neither NFP nor headline CPI falls within the 6-H4 holding window for any of the 40 Ifo episodes. Only FOMC Minutes (`840050004`) overlaps with a single episode (#29, 2021-11-24).',
    '> Because FOMC encompasses multiple distinct release types and exact boundaries were not frozen in v1.2, this diagnostic is marked **NOT_EVALUATED** to prevent ad-hoc specification drift prior to Codex audit clearance.',
    '',
    '### E. Outlier Sessions ($|\\Delta R - \\Delta \\bar{R}| > 2\\sigma$)',
    '',
    p6.outliers.length === 0
      ? '*No statistical outlier sessions observed beyond 2 standard deviations.*'
      : [
          '| Episode # | Broker Date/Time | Direction | $\\Delta R$ (bps) | $\\Delta$ Pips |',
          '|---|---|---|---|---|',
          ...p6.outliers.map(
            o =>
              `| #${o.actionableIndex} | \`${o.brokerDateTime}\` | **${o.direction}** | ${(o.deltaReturn * 10000).toFixed(2)} | ${o.deltaPips.toFixed(2)} |`
          ),
        ].join('\n'),
    '',
    '---',
    '',
    '## 7. Event-by-Event Ledger & Paired Observations (6 H4 - All 40 Actionable Episodes)',
    '',
    '| # | Broker Date/Time | Dir | Entry Price | Exit Price | Event Pips | Ctrl Choice | Ctrl Pips | $\\Delta$ Pips | Status / Disposition |',
    '|---|---|---|---|---|---|---|---|---|---|'
  );

  for (const ev of data.events) {
    const pair = data.primary6H4.pairs.find(p => p.actionableIndex === ev.actionableIndex);
    if (pair) {
      lines.push(
        `| #${ev.actionableIndex} | \`${ev.brokerDateTime}\` | **${pair.direction}** | ${ev.entryPrice.toFixed(5)} | ${ev.exitPrice6.toFixed(5)} | ${pair.eventPipDrift.toFixed(2)} | \`${pair.controlChoice}\` | ${pair.controlPipDrift.toFixed(2)} | **${pair.deltaPipDrift.toFixed(2)}** | ${pair.isEventWin ? 'WIN' : 'LOSS'} |`
      );
    } else {
      const ctrl = data.primary6H4.controls.find(c => c.actionableIndex === ev.actionableIndex);
      const reason = ctrl?.exclusionReason || 'All 4 candidate dates (D-7, D+7, D-14, D+14) collided with high-importance EUR releases';
      lines.push(
        `| #${ev.actionableIndex} | \`${ev.brokerDateTime}\` | **${ev.direction}** | ${ev.entryPrice.toFixed(5)} | ${ev.exitPrice6.toFixed(5)} | ${ev.pipDrift6.toFixed(2)} | \`CONTROL_UNAVAILABLE\` | N/A | N/A | EXCLUDED (${reason}) |`
      );
    }
  }

  lines.push('');
  return lines.join('\n');
}
