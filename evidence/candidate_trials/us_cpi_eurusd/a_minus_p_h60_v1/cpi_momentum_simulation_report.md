# Forensic Exploratory Historical Simulation Report: US CPI on EURUSD
## Candidate Variant: A−P Momentum with H60 Expiry (`a_minus_p_h60_v1`)
**Status**: UNDER AUDIT — POST-HOC EXPLORATORY SPECIFICATION (NO REGISTERED SETUP)  
**Target Asset**: EURUSD  
**Date**: 2026-09-27  
**Governance Scope**: Post-Hoc Exploratory Specification (Isolated Parameter Inspection; Zero Forward/Live/Demo Claims)

---

## 1. Cryptographic Provenance & Input Data Integrity
All calculations are grounded in the byte-verified pinned export files:

| Input File | Absolute Path | SHA-256 Digest | Status |
|---|---|---|---|
| **Calendar Releases** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv` | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` | Byte-verified |
| **EURUSD H1 Candles** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv` | `893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5` | Byte-verified |

### Static Data Sanity Audit
- **Duplicate Initial-Release Records**: 0 duplicates detected.
- **Raw-Scaled vs Displayed Consistency**: 0 mismatches across headline and core CPI release records (`actual_raw_scaled_1e6 / 1e6 == actual`).
- **Unit and Multiplier Uniformity**: 100% of US headline and core CPI records conform to `CALENDAR_UNIT_PERCENT` and `CALENDAR_MULTIPLIER_NONE`.
- **Zero Synthetic Data**: Zero synthetic observations, mock arrays, or seed generators were utilized.

---

## 2. Complete 277-Episode Decision Ledger Reconciliation
Counts establish the complete universe of 277 US_INFLATION episodes from the pinned calendar:

```text
Total Pinned Calendar Data Rows:                                  123,054 (123,055 lines with header)
  |-- Revision 0 Initial Releases:                                104,068
  |-- Non-zero Revisions / Historical Corrections:                 18,986
Total Distinct Timestamps across Full Calendar:                    40,202
  |
  +-- Total US_INFLATION Family Episodes:                             277
        |
        +-- Less: Core PCE Only Releases (840010001):                -138 (PCE_ONLY)
        +-- Less: Shared Collisions with Retail Sales:                -12 (SHARED_COLLISION)
        +-- Less: Missing Actual or Previous (A/P):                   -0 (MISSING_AP)
        |
        = Eligible Unshared CPI Episodes:                             127
              |
              +-- Concordant Positive (A - P > 0, Both Accelerating):   26  --> EURUSD SHORT (CANDIDATE_TRADE)
              +-- Concordant Negative (A - P < 0, Both Decelerating):   29  --> EURUSD LONG (CANDIDATE_TRADE)
              +-- Discordant / Mixed / Equal Momentum:                 72  --> NO TRADE (MIXED_OR_EQUAL)
              |
              = Total Directional Candidate Trades:                    55  (26 Short / 29 Long)
```

### Decision Ledger Funnel Accounting
Every single one of the 277 inflation episodes is recorded in [`cpi_momentum_decision_ledger.csv`](cpi_momentum_decision_ledger.csv):
- `PCE_ONLY`: 138
- `SHARED_COLLISION`: 12
- `MISSING_AP`: 0
- `MIXED_OR_EQUAL`: 72
- `CANDIDATE_TRADE`: 55
- Price / ATR / Path Exclusions: 0 (all 55 candidates had valid entry bars, 60 observed forward bars, and pre-release ATR14 windows).
- **Sum**: 277 / 277 (100% closed accounting).

---

## 3. Revised Previous Audit & Point-in-Time Limitations
MT5 calendar exposes `previous`, `revised_previous`, and `revision` as separate fields.
- **Presence**: In 9 of the 127 eligible CPI episodes (7.1%), a non-empty `revised_previous` value exists.
- **Directional Disagreement**: In **3 episodes**, substituting `revised_previous` for `previous` would alter the directional signal:
  1. `2021.02.10 16:30:00`: Original A−P gave **LONG** (Head: 0.3 vs 0.4 = -0.1; Core: 0.0 vs 0.1 = -0.1). Substituting revised previous (Head: 0.3 vs 0.2 = +0.1; Core: 0.0 vs 0.0 = 0.0) yields mixed momentum -> **NO TRADE**.
  2. `2023.02.14 16:30:00`: Original A−P gave **SHORT** (Head: 0.5 vs -0.1 = +0.6; Core: 0.4 vs 0.3 = +0.1). Substituting revised previous (Head: 0.5 vs 0.1 = +0.4; Core: 0.4 vs 0.4 = 0.0) yields mixed momentum -> **NO TRADE**.
  3. `2024.02.13 16:30:00`: Original A−P gave **NO TRADE** (Head: 0.3 vs 0.3 = 0.0; Core: 0.4 vs 0.3 = +0.1). Substituting revised previous (Head: 0.3 vs 0.2 = +0.1; Core: 0.4 vs 0.3 = +0.1) yields concordant positive -> **SHORT**.

> [!WARNING]
> **POINT-IN-TIME GOVERNANCE DIRECTIVE**:
> Historical point-in-time availability of `revised_previous` is **unproven** by this static snapshot. We cannot prove from this export whether `revised_previous` arrived simultaneously with the revision-0 release or was retroactively back-filled during a subsequent benchmark revision. In accordance with this post-hoc exploratory specification, `revised_previous` is recorded for audit purposes only and is **NEVER** substituted into the primary trading rule.

---

## 4. Execution Mechanics & Path Continuity (Observed Bars vs Clock Hours)
- **Entry Execution**: Exact OPEN price of the intended next-hour H1 candle (`((ts // 3600) + 1) * 3600`). For a 15:30 release, entry is strictly at 16:00:00. Zero forward search across gaps was permitted.
- **Pre-Release ATR(14)**: Calculated as arithmetic mean of 14 completed H1 True Ranges ending **strictly before** release timestamp (`candle_time + 3600 < release_ts`). Release-containing candle is strictly excluded. Requires 15 strictly consecutive completed bars with zero gaps.
- **Protective Stop Loss**: $1.0 \times \text{ATR14}$ nominal. Fills at worse open if bar opens beyond stop.
- **Profit Target**: $1.5 \times \text{ATR14}$ nominal (primary trial). Favorable target gaps capped at nominal target.
- **Expiry Horizon (H60)**: Exits at close of the 60th **observed market candle** (`TIMEOUT_H60`).
- **Path Continuity Audit**:
  - Across all 55 candidates, **37 standard weekend market closures** (Friday close to Sunday/Monday open) were observed based on strict server-date weekdays and transition endpoints.
  - **Zero unexpected missing-data gaps** occurred in the forward 60-bar paths.
  - Zero trades experienced adverse stop gap fills or favorable target gap capping on their exit bars.

---

## 5. Primary Trial Performance Summary (1.5x ATR Target)

| Metric | Primary Trial (Conservative: Stop First) | Optimistic Sensitivity (Target First) |
|---|---|---|
| **Total Candidate Trades (N)** | **55** (26 Short, 29 Long) | **55** (26 Short, 29 Long) |
| **Wins / Losses / Timeouts** | **23 / 32 / 0** | **27 / 28 / 0** |
| **Win Rate** | **41.8%** | **49.1%** |
| **Gross Profit Factor** | **1.08** | **1.45** |
| **Cumulative Gross Return** | **+2.50 R** | **+12.50 R** |
| **Mean Return per Trade** | **+0.05 R** | **+0.23 R** |
| **Cumulative Gross P&L** | **+40.9 pips** | **+144.0 pips** |
| **Actual Mean Risk Distance** | **12.20 pips** | **12.20 pips** |
| **Actual Mean Gross P&L** | **+0.74 pips** | **+2.62 pips** |
| **Maximum Drawdown** | **7.00 R** | **6.00 R** |
| **Ambiguous Intrabar Touches** | **4 episodes (7.3%)** | **4 episodes (7.3%)** |
| **Return Without Best Trade** | **+1.00 R** | **+11.00 R** |

*Notice*: Actual trade-level means are computed directly from the ledger (12.20 risk pips and +0.74 gross P&L pips). Mean R is not multiplied by mean risk distance.

### Holding Time Distribution (Observed H1 Market Candles)
`Bar 1: 43, Bar 2: 8, Bar 5: 2, Bar 18: 1, Bar 23: 1`  
- **Bar 1**: 43 trades (78.2%)
- **Bar 2**: 8 trades (14.5%)
- **Bar 5**: 2 trades (3.6%)
- **Bar 18**: 1 trades (1.8%)
- **Bar 23**: 1 trades (1.8%)
- **H60 Timeouts**: 0 trades (0.0%)
- **Latest Exit**: Bar 23 (2021.02.10 16:30:00 release, target hit at Bar 23). Extending expiry from H24 to H60 changed zero exit outcomes for the 1.5x primary trial because all trades resolved within 23 observed bars.

---

## 6. Annual Breakdown & Directional Splits

### Annual Performance Breakdown

| Year | Trades | Longs | Shorts | Wins | Losses | Gross R | Gross Pips |
|---|---|---|---|---|---|---|---|
| 2015 | 2 | 2 | 0 | 0 | 2 | -2.00 R | -35.7 |
| 2016 | 5 | 2 | 3 | 1 | 4 | -2.50 R | -54.1 |
| 2017 | 1 | 0 | 1 | 1 | 0 | +1.50 R | +20.4 |
| 2018 | 2 | 1 | 1 | 1 | 1 | +0.50 R | +7.1 |
| 2019 | 2 | 1 | 1 | 1 | 1 | +0.50 R | -0.3 |
| 2020 | 9 | 6 | 3 | 4 | 5 | +1.00 R | +31.5 |
| 2021 | 11 | 5 | 6 | 4 | 7 | -1.00 R | +9.5 |
| 2022 | 4 | 2 | 2 | 1 | 3 | -1.50 R | -29.1 |
| 2023 | 5 | 2 | 3 | 3 | 2 | +2.50 R | +22.1 |
| 2024 | 3 | 2 | 1 | 0 | 3 | -3.00 R | -20.6 |
| 2025 | 7 | 4 | 3 | 4 | 3 | +3.00 R | +61.1 |
| 2026 | 4 | 2 | 2 | 3 | 1 | +3.50 R | +29.2 |

### Long vs. Short Directional Performance
- **Longs (Both Decelerating, A < P)**: N = 29, Gross R = **-1.50 R** (+0.8 pips)
- **Shorts (Both Accelerating, A > P)**: N = 26, Gross R = **+4.00 R** (+40.1 pips)

### Co-Release Split: Initial Jobless Claims (`840140001`)
- **8 Candidate Timestamps with Initial Jobless Claims**: Sum Gross R = **+4.50 R**
- **47 Candidate Timestamps without Initial Jobless Claims**: Sum Gross R = **-2.00 R**

---

## 7. Comparative Overlap Analysis: A−P Momentum (55 Trades) vs Baseline A−F (36 Trades)
The baseline trial evaluated announcement surprise ($A - F$) over H24; this candidate evaluates historical momentum ($A - P$) over H60.

| Overlap Metric | Count | Accounting Rationale |
|---|---|---|
| **Baseline A−F Candidate Trades** | 36 | Requires valid forecast and concordant $A - F$ surprise |
| **New A−P Momentum Trades** | 55 | Requires valid previous and concordant $A - P$ momentum |
| **Overlapping Timestamps** | 25 | Release satisfied both surprise and momentum criteria |
| **A−F Baseline Only Timestamps** | 11 | Concordant surprise ($A - F$), but mixed/equal momentum ($A - P$) |
| **A−P Candidate Only Timestamps** | 30 | 8 unforecasted episodes (2015-2016, 2025) + 22 mixed-surprise episodes |
| **Directional Agreement on Overlap** | 24 | Same direction signaled by both rules |
| **Directional Disagreement on Overlap** | 1 | `2018.03.13 15:30:00`: A−F = SHORT (+1.50 R); A−P = LONG (-1.00 R) |

### Detailed Disagreement Episode: 2018.03.13 15:30:00
- **Headline CPI**: Actual = 0.2%, Forecast = 0.1%, Previous = 0.5%  
  $A - F = +0.1%$ (Bullish USD Surprise) vs $A - P = -0.3%$ (Decelerating Inflation)
- **Core CPI**: Actual = 0.2%, Forecast = 0.1%, Previous = 0.3%  
  $A - F = +0.1%$ (Bullish USD Surprise) vs $A - P = -0.1%$ (Decelerating Inflation)
- **Market Reaction**: EURUSD dropped immediately on release, hitting the A−F SHORT target (+1.50 R) while stopping out the A−P LONG position (-1.00 R). This demonstrates the fundamental divergence between announcement surprise and trend momentum.

---

## 8. Sensitivity Analysis across Target Multiples & Intrabar Precedence

| Target Multiple | Intrabar Precedence | Trades | Win Rate | Gross R | Mean R | Profit Factor | Max DD | Ambiguous Bars | Latest Exit |
|---|---|---|---|---|---|---|---|---|---|
| **1.0x ATR** (1:1 R:R) | Conservative (Stop First) | 55 | 43.6% | -7.00 R | -0.13 R | 0.77 | 11.00 R | 5 | Bar 5 |
| **1.0x ATR** (1:1 R:R) | Optimistic (Target First) | 55 | 52.7% | +3.00 R | +0.05 R | 1.12 | 5.00 R | 5 | Bar 5 |
| **1.5x ATR** (Primary) | Conservative (Stop First) | 55 | 41.8% | +2.50 R | +0.05 R | 1.08 | 7.00 R | 4 | Bar 23 |
| **1.5x ATR** (Primary) | Optimistic (Target First) | 55 | 49.1% | +12.50 R | +0.23 R | 1.45 | 6.00 R | 4 | Bar 23 |
| **2.0x ATR** (1:2 R:R) | Conservative (Stop First) | 55 | 36.4% | +5.00 R | +0.09 R | 1.14 | 7.00 R | 3 | Bar 23 |
| **2.0x ATR** (1:2 R:R) | Optimistic (Target First) | 55 | 41.8% | +14.00 R | +0.25 R | 1.44 | 7.00 R | 3 | Bar 23 |

### Ambiguous Intrabar Collisions (1.5x Target)
Four episodes touched both SL (1.0x) and TP (1.5x) in the same H1 candle:
1. `2021.05.12 15:30:00` (SHORT): Bar 1 touched both SL and TP.
2. `2023.02.14 16:30:00` (SHORT): Bar 1 touched both SL and TP.
3. `2024.06.12 15:30:00` (LONG): Bar 1 touched both SL and TP.
4. `2024.07.11 15:30:00` (LONG): Bar 1 touched both SL and TP.

*Impact*: Resolving these 4 ambiguous bars in favor of Target changes cumulative return from **+2.50 R** to **+12.50 R** (+400% swing). This proves extreme sensitivity to microsecond execution order, which cannot be resolved on hourly OHLC bars.

---

## 9. Real-World Execution Limitations & Governance Boundary
1. **Post-Hoc Exploratory Specification**: Historical prices, trade paths, and multiple target variants (1.0x, 1.5x, 2.0x) were inspected prior to drafting the trial protocol. This candidate is a post-hoc exploratory specification, NOT a pre-price-frozen hypothesis test.
2. **Parameter Variations Disclosure**: The 1.0x and 2.0x target sensitivities are post-hoc descriptive inspections on the identical historical sample. They are NOT independently validated parameter choices and must not be interpreted as forward-tested optimizations.
3. **Registration Status**: This trial is NOT a registered setup and must not be traded on live or demo accounts. Zero setups are registered or approved for forward trading. It is an isolated exploratory research pass under audit and does not replace the baseline.
4. **Gross OHLC Limitation**: Gross mid/bid prices only. Zero spread, slippage, commission, or overnight swap is modeled.
5. **Horizon Irrelevance at Current Targets**: In this sample, 100% of trades resolved by Bar 23. Extending expiry from H24 to H60 produced zero timeouts across all evaluated target multiples.
