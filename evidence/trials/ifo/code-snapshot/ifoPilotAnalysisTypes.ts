/**
 * Type definitions for German Ifo Pilot Pre-2023 Exploration & Outcome Analysis (Milestone 4).
 * Governed strictly by the frozen protocol in docs/FMS_PILOT_IFO_PROTOCOL.md (v1.2 FROZEN).
 */

import { TradeDirection } from './ifoPilotLedgerTypes.js';
import { ControlCandidateChoice } from './ifoControlAudit.js';

export { TradeDirection, ControlCandidateChoice };

export interface CandleH1 {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface CandleH4 {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface IfoEvaluatedEpisode {
  packageIndex: number; // 1..96 from allPackages
  actionableIndex: number; // 1..40 from actionableRows
  releaseTimestamp: number;
  brokerDateTime: string;
  direction: TradeDirection;
  entryTimestamp: number;
  entryPrice: number; // Bid-bar Open proxy at T_entry
  exitTimestamp6: number;
  exitPrice6: number; // Bid-bar Close proxy of 6th completed active H4 bar
  logReturn6: number; // d_i * ln(P_exit / P_entry)
  pipDrift6: number; // d_i * (P_exit - P_entry) / 0.0001
  bars6: number[];
  exitTimestamp12: number;
  exitPrice12: number; // Bid-bar Close proxy of 12th completed active H4 bar
  logReturn12: number;
  pipDrift12: number;
  bars12: number[];
  hasCrossCurrencyCollision: boolean;
  collidingCurrencies: string[];
  hasUs1530MorningRelease: boolean;
}

export interface IfoEvaluatedControl {
  actionableIndex: number;
  horizon: 6 | 12;
  status: 'PAIRED' | 'CONTROL_UNAVAILABLE';
  controlChoice: ControlCandidateChoice | null;
  exclusionReason?: string;
  direction: TradeDirection;
  controlEntryTimestamp: number | null;
  controlEntryPrice: number | null;
  controlExitTimestamp: number | null;
  controlExitPrice: number | null;
  logReturn: number | null;
  pipDrift: number | null;
  bars: number[];
}

export interface IfoPairedObservation {
  actionableIndex: number;
  horizon: 6 | 12;
  direction: TradeDirection;
  eventTimestamp: number;
  controlTimestamp: number;
  controlChoice: ControlCandidateChoice;
  eventEntryPrice: number;
  controlEntryPrice: number;
  eventReturn: number;
  controlReturn: number;
  deltaReturn: number; // eventReturn - controlReturn
  eventPipDrift: number;
  controlPipDrift: number;
  deltaPipDrift: number; // eventPipDrift - controlPipDrift
  isEventWin: boolean; // deltaReturn > 0
}

export interface IfoCostSensitivityRow {
  costPips: number; // 0.0, 0.5, 1.0, 1.5, 2.0
  grossMeanEventPips: number;
  netMeanEventPips: number; // grossMeanEventPips - costPips

  // Scenario A: Paired Executable Trades (Equal Cost c on Both Trades)
  // Equal cost c cancels out in the paired difference: (event - c) - (control - c) = event - control
  scenarioA_EqualCostDeltaPips: number;
  scenarioA_EqualCostDeltaReturn: number;
  scenarioA_WinRate: number;

  // Scenario B: Event Trade Net of Cost vs. Frictionless Benchmark Control
  // Difference reduced by c: (event - c) - control = delta - c
  scenarioB_EventOnlyNetDeltaPips: number;
  scenarioB_EventOnlyNetDeltaReturn: number;
  scenarioB_WinRate: number;

  // Backwards-compatible aliases:
  grossMeanDeltaPips: number;
  netMeanDeltaPips: number; // maps to scenarioB
  grossMeanDeltaReturn: number;
  netMeanDeltaReturn: number; // maps to scenarioB
  winRateNet: number; // maps to scenarioB
}

export interface IfoSubgroupStats {
  count: number;
  meanDeltaReturn: number;
  meanDeltaPips: number;
  winRate: number;
}

export interface IfoHorizonSummary {
  horizonBars: 6 | 12;
  horizonLabel: string;
  totalActionable: number; // 40
  pairedCount: number; // 39 for 6H4, 34 for 12H4 strict
  unavailableCount: number; // 1 for 6H4, 6 for 12H4 strict
  meanEventReturn: number;
  meanControlReturn: number;
  meanDeltaReturn: number; // \Delta\bar{R}
  medianDeltaReturn: number;
  stdDeltaReturn: number;
  meanEventPipDrift: number; // \bar{\Delta}_{pips}
  meanControlPipDrift: number;
  meanDeltaPipDrift: number;
  pairedWins: number;
  pairedWinRate: number; // fraction
  pValuePermutation: number; // Seeded Mulberry32 paired sign-flip
  pValueWilcoxon: number;
  pValueTTest: number;
  pValueHolmAdjusted?: number;
  wilcoxonZeroCount?: number;
  wilcoxonTieCorrection?: number;
  tTestDegreesOfFreedom?: number;
  costSensitivity: IfoCostSensitivityRow[];
  yearDistribution: Record<string, IfoSubgroupStats>;
  collisionPartition: {
    collision: IfoSubgroupStats;
    nonCollision: IfoSubgroupStats;
  };
  usMorningOverlapPartition: {
    with1530Release: IfoSubgroupStats;
    without1530Release: IfoSubgroupStats;
  };
  tier1UsInteractionNote?: string;
  outliers: Array<{
    actionableIndex: number;
    eventTimestamp: number;
    brokerDateTime: string;
    direction: TradeDirection;
    deltaReturn: number;
    deltaPips: number;
  }>;
}

export type IfoDecisionState =
  | 'STATE_1_PLAUSIBLE_IN_SAMPLE_ANOMALY'
  | 'STATE_2_INCONCLUSIVE_FRAGILE_EVIDENCE'
  | 'STATE_3_NO_CONVINCING_EVIDENCE';

export interface IfoDecisionEvaluation {
  decisionState: IfoDecisionState;
  stateTitle: string;
  operationalMandate: string;
  criteria: {
    step1Failed: boolean;
    step1Reason?: string;
    step2Fragile: boolean;
    step2SubCase?: '2A_MARGINAL_SIGNIFICANCE' | '2B_COMMERCIALLY_INSIGNIFICANT' | '2C_OUTLIER_DOMINATED';
    step2Reason?: string;
    state1Plausible: boolean;
  };
}

export interface Pre2023CandlesManifest {
  rowCount: number;
  firstTimestamp: number | null;
  lastTimestamp: number | null;
  sha256: string;
  sha256WithHeader: string;
}

export interface ImplementationManifest {
  gitCommit: string | null;
  sourceFilesSha256: Record<string, string>;
}

export interface IfoExplorationManifest {
  consumedPre2023H1Candles: Pre2023CandlesManifest;
  implementation: ImplementationManifest;
}

export interface IfoPilotExplorationReportData {
  protocolVersion: string;
  protocolDate: string;
  splitTimestamp: number;
  evaluatedAt: string;
  implementation: ImplementationManifest;
  manifest: IfoExplorationManifest;
  provenanceHashes: {
    rawCalendarSha256: string;
    episodesJsonlSha256: string;
    pilotLedgerJsonSha256: string;
    pilotLedgerMdSha256: string;
    consumedPre2023H1CandlesSha256?: string;
  };
  events: IfoEvaluatedEpisode[];
  primary6H4: {
    summary: IfoHorizonSummary;
    pairs: IfoPairedObservation[];
    controls: IfoEvaluatedControl[];
  };
  secondary12H4Strict: {
    summary: IfoHorizonSummary;
    pairs: IfoPairedObservation[];
    controls: IfoEvaluatedControl[];
  };
  secondary12H4Permissive: {
    summary: IfoHorizonSummary;
    pairs: IfoPairedObservation[];
    controls: IfoEvaluatedControl[];
  };
  decision: IfoDecisionEvaluation;
}
