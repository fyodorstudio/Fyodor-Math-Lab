/**
 * Deterministic PRNG and Seeded Monte Carlo Paired Sign-Flip Permutation Engine.
 * Pinned by docs/FMS_PILOT_IFO_PROTOCOL.md (Section 9.2).
 *
 * Algorithm: Mulberry32
 * Default Seed: 20260925
 * Default Draws: 100,000
 */

export interface PermutationTestResult {
  observedMean: number;
  pValue: number;
  draws: number;
  seed: number;
  exceedanceCount: number;
  nPairs: number;
}

export interface ExhaustivePermutationResult {
  observedMean: number;
  pValue: number;
  totalPermutations: number;
  exceedanceCount: number;
  nPairs: number;
}

export interface WilcoxonResult {
  sumPositiveRanks: number;
  sumNegativeRanks: number;
  expectedW: number;
  varianceW: number;
  zStatistic: number;
  pValueOneSided: number;
  effectiveN: number;
  zeroCount: number;
  tieCorrection: number;
}

export interface TTestResult {
  mean: number;
  std: number;
  tStatistic: number;
  degreesOfFreedom: number;
  pValueOneSided: number;
}

/**
 * Creates a deterministic 32-bit Mulberry32 PRNG.
 * Produces pseudo-random floating point values in [0, 1).
 */
export function createMulberry32(seed: number): () => number {
  let s = seed >>> 0;
  return function (): number {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Executes the frozen seeded Monte Carlo paired sign-flip test.
 *
 * Under H_0: E[R_event - R_control] <= 0 (no directional excess return).
 * Tests directional alternative H_1: E[R_event - R_control] > 0.
 *
 * p = (1 + sum(I(Delta_R^(b) >= Delta_R_obs))) / (B + 1)
 */
export function runPairedSignFlipTest(
  differences: number[],
  options: { draws?: number; seed?: number } = {}
): PermutationTestResult {
  const n = differences.length;
  if (n === 0) {
    throw new Error('Cannot run paired sign-flip test on empty differences array');
  }

  const draws = options.draws ?? 100000;
  const seed = options.seed ?? 20260925;
  const prng = createMulberry32(seed);

  let sumObs = 0;
  for (let i = 0; i < n; i++) {
    sumObs += differences[i];
  }
  const observedMean = sumObs / n;

  // Floating point precision epsilon for comparisons
  const EPSILON = 1e-14;

  let exceedanceCount = 0;

  for (let b = 0; b < draws; b++) {
    let permSum = 0;
    for (let i = 0; i < n; i++) {
      // Sign flip: +1 or -1 with probability 0.5
      const sign = prng() < 0.5 ? 1 : -1;
      permSum += sign * differences[i];
    }
    const permMean = permSum / n;

    if (permMean >= observedMean - EPSILON) {
      exceedanceCount++;
    }
  }

  const pValue = (1 + exceedanceCount) / (draws + 1);

  return {
    observedMean,
    pValue,
    draws,
    seed,
    exceedanceCount,
    nPairs: n,
  };
}

/**
 * Runs an exhaustive enumeration of all 2^N paired sign flips for small N (N <= 16).
 * Used for synthetic tests to benchmark Monte Carlo accuracy against the exact permutation distribution.
 */
export function runExhaustivePairedSignFlipTest(
  differences: number[]
): ExhaustivePermutationResult {
  const n = differences.length;
  if (n === 0) {
    throw new Error('Cannot run exhaustive test on empty array');
  }
  if (n > 20) {
    throw new Error(`Exhaustive enumeration for N=${n} exceeds practical limits (2^${n})`);
  }

  let sumObs = 0;
  for (let i = 0; i < n; i++) {
    sumObs += differences[i];
  }
  const observedMean = sumObs / n;

  const totalPermutations = 1 << n; // 2^n
  const EPSILON = 1e-14;
  let exceedanceCount = 0;

  for (let mask = 0; mask < totalPermutations; mask++) {
    let permSum = 0;
    for (let i = 0; i < n; i++) {
      const sign = (mask & (1 << i)) !== 0 ? 1 : -1;
      permSum += sign * differences[i];
    }
    const permMean = permSum / n;
    if (permMean >= observedMean - EPSILON) {
      exceedanceCount++;
    }
  }

  const pValue = exceedanceCount / totalPermutations;

  return {
    observedMean,
    pValue,
    totalPermutations,
    exceedanceCount,
    nPairs: n,
  };
}

/**
 * Standard Normal Cumulative Distribution Function (error function approximation).
 */
export function normalCdf(z: number): number {
  const b1 = 0.319381530;
  const b2 = -0.356563782;
  const b3 = 1.781477937;
  const b4 = -1.821255978;
  const b5 = 1.330274429;
  const p = 0.2316419;
  const c = 0.3989422804014327; // 1 / sqrt(2 * pi)

  if (z >= 0) {
    const t = 1.0 / (1.0 + p * z);
    return 1.0 - c * Math.exp(-0.5 * z * z) * t * (t * (t * (t * (t * b5 + b4) + b3) + b2) + b1);
  } else {
    const t = 1.0 / (1.0 - p * z);
    return c * Math.exp(-0.5 * z * z) * t * (t * (t * (t * (t * b5 + b4) + b3) + b2) + b1);
  }
}

/**
 * Computes natural logarithm of the Gamma function ln(Gamma(z)) via Lanczos approximation.
 * High precision approximation (g=7, n=9), error < 1e-14 for all z > 0.
 */
export function logGamma(z: number): number {
  const p = [
    676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059,
    12.507343278686905, -0.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7,
  ];
  if (z < 0.5) {
    return Math.log(Math.PI / Math.sin(Math.PI * z)) - logGamma(1.0 - z);
  }
  z -= 1.0;
  let x = 0.99999999999980993;
  for (let i = 0; i < p.length; i++) {
    x += p[i] / (z + (i + 1));
  }
  const t = z + p.length - 0.5;
  return 0.5 * Math.log(2.0 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

/**
 * Evaluates the continued fraction for the incomplete beta function (Numerical Recipes betacf).
 */
export function betacf(a: number, b: number, x: number): number {
  const MAXIT = 200;
  const EPS = 1e-14;
  const FPMIN = 1e-30;

  const qab = a + b;
  const qap = a + 1.0;
  const qam = a - 1.0;

  let c = 1.0;
  let d = 1.0 - (qab * x) / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1.0 / d;
  let h = d;

  for (let m = 1; m <= MAXIT; m++) {
    const m2 = 2 * m;
    const aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1.0 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1.0 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1.0 / d;
    h *= d * c;

    const bb = -((a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1.0 + bb * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1.0 + bb / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1.0 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1.0) < EPS) break;
  }
  return h;
}

/**
 * Regularized incomplete beta function I_x(a, b) = B(x; a, b) / B(a, b).
 */
export function regularizedIncompleteBeta(a: number, b: number, x: number): number {
  if (x <= 0) return 0.0;
  if (x >= 1) return 1.0;

  const lbeta = logGamma(a) + logGamma(b) - logGamma(a + b);
  const bt = Math.exp(a * Math.log(x) + b * Math.log(1.0 - x) - lbeta);

  if (x < (a + 1.0) / (a + b + 2.0)) {
    return (bt * betacf(a, b, x)) / a;
  } else {
    return 1.0 - (bt * betacf(b, a, 1.0 - x)) / b;
  }
}

/**
 * Computes the exact one-sided upper-tail p-value P(T >= t) for Student's t distribution
 * with df degrees of freedom, evaluated via the regularized incomplete beta function.
 */
export function studentTUpperTail(t: number, df: number): number {
  if (df <= 0) {
    throw new Error(`Degrees of freedom must be positive, got ${df}`);
  }
  if (!Number.isFinite(t)) {
    return t > 0 ? 0.0 : 1.0;
  }
  if (t === 0) {
    return 0.5;
  }

  const x = df / (df + t * t);
  const ibeta = regularizedIncompleteBeta(df / 2.0, 0.5, x);

  if (t > 0) {
    return 0.5 * ibeta;
  } else {
    return 1.0 - 0.5 * ibeta;
  }
}

/**
 * Computes the Wilcoxon signed-rank test for paired differences (diagnostic).
 * One-sided test of H_1: median(differences) > 0.
 *
 * Implements standard Wilcoxon convention:
 * 1. Exact zeros (|d_i| <= 1e-15) are dropped (effectiveN = n - n_0).
 * 2. Average ranks assigned to tied absolute differences.
 * 3. Exact tie correction subtracted from variance: sum(t_j^3 - t_j) / 48.
 * 4. Continuity correction (+/- 0.5) applied to test statistic.
 */
export function computeWilcoxonSignedRank(differences: number[]): WilcoxonResult {
  const nonZero = differences.filter(d => Math.abs(d) > 1e-15);
  const zeroCount = differences.length - nonZero.length;
  const n = nonZero.length;

  if (n === 0) {
    return {
      sumPositiveRanks: 0,
      sumNegativeRanks: 0,
      expectedW: 0,
      varianceW: 0,
      zStatistic: 0,
      pValueOneSided: 1.0,
      effectiveN: 0,
      zeroCount,
      tieCorrection: 0,
    };
  }

  // Create absolute values and track signs
  const items = nonZero.map(d => ({ absVal: Math.abs(d), sign: d > 0 ? 1 : -1, rank: 0 }));
  items.sort((a, b) => a.absVal - b.absVal);

  // Assign ranks with average ranks for ties, and calculate tie correction sum
  let tieCorrectionSum = 0;
  let i = 0;
  while (i < n) {
    let j = i;
    while (j < n - 1 && Math.abs(items[j + 1].absVal - items[j].absVal) < 1e-15) {
      j++;
    }
    const tieCount = j - i + 1;
    if (tieCount > 1) {
      tieCorrectionSum += (tieCount * tieCount * tieCount - tieCount);
    }
    const avgRank = (i + 1 + j + 1) / 2.0;
    for (let k = i; k <= j; k++) {
      items[k].rank = avgRank;
    }
    i = j + 1;
  }

  let sumPos = 0;
  let sumNeg = 0;
  for (const item of items) {
    if (item.sign > 0) {
      sumPos += item.rank;
    } else {
      sumNeg += item.rank;
    }
  }

  // Large-sample normal approximation with tie-corrected variance
  const expectedW = (n * (n + 1)) / 4.0;
  const rawVarianceW = (n * (n + 1) * (2 * n + 1)) / 24.0;
  const tieCorrection = tieCorrectionSum / 48.0;
  const varianceW = Math.max(rawVarianceW - tieCorrection, 1e-15);
  const stdW = Math.sqrt(varianceW);

  // One-sided: testing if sumPos is greater than expectedW with continuity correction
  let z = 0;
  if (stdW > 0) {
    if (sumPos > expectedW) {
      z = (sumPos - expectedW - 0.5) / stdW;
    } else if (sumPos < expectedW) {
      z = (sumPos - expectedW + 0.5) / stdW;
    } else {
      z = 0;
    }
  }
  const pValueOneSided = 1.0 - normalCdf(z);

  return {
    sumPositiveRanks: sumPos,
    sumNegativeRanks: sumNeg,
    expectedW,
    varianceW,
    zStatistic: z,
    pValueOneSided,
    effectiveN: n,
    zeroCount,
    tieCorrection,
  };
}

/**
 * Computes paired Student's t-test (diagnostic).
 * One-sided test of H_1: mean(differences) > 0.
 *
 * Evaluates exact Student's t distribution tail using degrees of freedom df = n - 1.
 */
export function computePairedTTest(differences: number[]): TTestResult {
  const n = differences.length;
  if (n < 2) {
    throw new Error('Paired t-test requires at least 2 pairs');
  }

  let sum = 0;
  for (let i = 0; i < n; i++) sum += differences[i];
  const mean = sum / n;

  let sumSqDiff = 0;
  for (let i = 0; i < n; i++) {
    const diff = differences[i] - mean;
    sumSqDiff += diff * diff;
  }
  const variance = sumSqDiff / (n - 1);
  const std = Math.sqrt(variance);
  const se = std / Math.sqrt(n);
  const t = se > 0 ? mean / se : 0;
  const df = n - 1;

  // Exact Student's t distribution one-sided upper tail with df degrees of freedom
  const pValueOneSided = studentTUpperTail(t, df);

  return {
    mean,
    std,
    tStatistic: t,
    degreesOfFreedom: df,
    pValueOneSided,
  };
}

/**
 * Computes Holm-Bonferroni step-down adjusted p-values for a family of hypotheses.
 * Preserves the original input order of the p-values.
 */
export function computeHolmAdjustedPValues(pValues: number[]): number[] {
  const m = pValues.length;
  if (m === 0) return [];
  if (m === 1) return [...pValues];

  // Create indexed items and sort ascending by p-value
  const indexed = pValues.map((p, idx) => ({ p, idx, adj: 0 }));
  indexed.sort((a, b) => a.p - b.p);

  // Apply step-down adjustment: adj_{(i)} = min(1, (m - i) * p_{(i)})
  let maxSoFar = 0;
  for (let i = 0; i < m; i++) {
    const multiplier = m - i;
    const rawAdj = Math.min(1.0, multiplier * indexed[i].p);
    maxSoFar = Math.max(maxSoFar, rawAdj);
    indexed[i].adj = maxSoFar;
  }

  // Restore original ordering
  indexed.sort((a, b) => a.idx - b.idx);
  return indexed.map(item => item.adj);
}
