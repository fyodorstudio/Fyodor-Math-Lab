# Forensic Exploratory Historical Simulation Report: US CPI on EURUSD
**Status**: UNDER AUDIT — NO REGISTERED SETUP  
**Target Asset**: EURUSD  
**Generated Date**: 2026-09-27  
**Governance Scope**: Research Exploratory Baseline (No Executable Claim)

---

## 1. Cryptographic Data Provenance & Verification
All simulation inputs were ingested directly from byte-verified pinned export files:

| Input File | Absolute Path | SHA-256 Digest | Status |
|---|---|---|---|
| **Calendar Releases** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv` | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` | Byte-verified |
| **EURUSD H1 Candles** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv` | `893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5` | Byte-verified |

*Notice*: Zero synthetic fixtures, mock arrays, or lookahead peeking were utilized.

---

## 2. Complete Filter Reconciliation & Decision Ledger (277 Inflation Episodes)
Counts establish the complete universe of 277 US_INFLATION episodes from the pinned calendar:

```text
Total Pinned Calendar Data Rows:                                  123,054 (123,055 lines with header)
  |-- Revision 0 Initial Releases:                                104,068
  |-- Non-zero Revisions / Historical Corrections:                 18,986
Total Distinct Timestamps across Full Calendar:                    40,202
Total Distinct Timestamps across the 5 Studied Families:               825 (14 cross-family collisions)
  |
  +-- Total US_INFLATION Family Episodes:                             277
        |
        +-- Less: Core PCE Only Releases (840010001):                -138 (PCE_ONLY)
        +-- Less: Shared Collisions with Retail Sales:                -12 (SHARED_COLLISION)
        +-- Less: CPI Missing A or F (2015-2016 unforecasted, Jan 2017): -26 (MISSING_AF)
        |
        = Eligible Unshared CPI Episodes:                             101
              |
              +-- Concordant Positive (A - F > 0, Both Above):         18  --> EURUSD SHORT (CANDIDATE_TRADE)
              +-- Concordant Negative (A - F < 0, Both Below):         18  --> EURUSD LONG (CANDIDATE_TRADE)
              +-- Discordant / Mixed / Zero Surprise:                  65  --> NO TRADE (MIXED_ZERO)
              |
              = Total Directional Candidate Trades:                    36  (18 Short / 18 Long)
```

### Complete Decision Ledger Funnel Closure
Every single one of the 277 inflation episodes is recorded in [`cpi_decision_ledger.csv`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/TABLE%20VIEWER/NEW/cpi_setup/cpi_decision_ledger.csv):
- `PCE_ONLY`: 138
- `SHARED_COLLISION`: 12
- `MISSING_AF`: 26
- `MIXED_ZERO`: 65
- `CANDIDATE_TRADE`: 36
- New Price / ATR Exclusions: 0 (all 36 candidates possessed valid intended entry bars, complete H24 paths, and valid pre-release ATR windows).
- **Sum**: 277 / 277 (100% closed accounting).

---

## 3. Specification of the Fixed Rule Bundle & Audit Corrections
- **Entry Execution**: Exact OPEN price of the intended next-hour H1 candle (`((ts // 3600) + 1) * 3600`). For a 15:30 server time release, entry occurs strictly at the 16:00:00 candle open. The runner requires the exact intended entry bar and does not search forward across gaps.
- **Volatility Scaling (ATR14)**: Calculated as the arithmetic mean of 14 completed H1 True Ranges ending **strictly before** the release timestamp (`candle_time + 3600 < release_ts`). Any candle ending at or after the release timestamp is strictly excluded.
- **Protective Stop Loss**: $1.0 \times \text{ATR14}$ nominal from entry price. Fills at worse open if a bar opens beyond the stop.
- **Profit Target**: $1.5 \times \text{ATR14}$ nominal from entry price (primary trial). Sensitivities evaluated at $1.0 \times \text{ATR14}$ and $2.0 \times \text{ATR14}$. If a bar opens beyond the target level, fill is capped at the nominal target price.
- **Maximum Holding Expiry**: 24 observed H1 candles (H24 close). Requires a complete 24-bar path; exits at Bar 24 close if neither Stop nor Target is triggered.
- **Intrabar Ambiguity Precedence**: If a bar touches both Stop and Target levels within the same hour, the trade is flagged `ambiguous_flag = True`. Conservative governance assumes **Stop Hit First** (`STOP_FIRST`). An optimistic sensitivity (`TARGET_FIRST`) is also reported.

### Real Outcome Invariance Check
The mathematical corrections (strictly-before ATR lookback, exact intended entry bar requirement, complete H24 path requirement, and favorable target gap capping) **alter zero of the 36 real trade outcomes**. All 36 historical releases occurred at :30 (where `< release_ts` and `<= release_ts` identify identical ATR windows), all 36 intended entry bars were present on disk, all 36 forward paths had at least 24 bars, and zero trades experienced favorable gap openings beyond target.

---

## 4. Performance Summary Table (Primary Trial: 1.5x ATR Target)

| Metric | Primary Trial (Conservative: Stop First) | Optimistic Sensitivity (Target First) |
|---|---|---|
| **Total Candidate Trades** | 36 (18 Short, 18 Long) | 36 (18 Short, 18 Long) |
| **Wins / Losses / Ties** | 16 / 20 / 0 | 18 / 18 / 0 |
| **Win Rate** | **44.4%** | **50.0%** |
| **Gross Profit Factor** | **1.20** | **1.50** |
| **Cumulative Gross Return** | **+4.00 R** | **+9.00 R** |
| **Mean Return per Trade** | **+0.11 R** | **+0.25 R** |
| **Actual Mean Risk Distance** | **13.30 pips** | **13.30 pips** |
| **Actual Mean Gross P&L** | **+1.89 pips** | — |
| **Maximum Drawdown** | **6.00 R** | **6.00 R** |
| **Ambiguous Bar Touches** | 2 episodes (5.6%) | 2 episodes (5.6%) |
| **Return Without Best Trade** | **+2.50 R** | — |

*Notice*: Actual trade-level means are computed directly from the ledger (13.30 risk pips and +1.89 gross P&L pips). Mean R is not multiplied by mean risk.

### Holding Time Distribution (Observed H1 Candles)
`Bar 1: 26, Bar 2: 6, Bar 3: 2, Bar 5: 1, Bar 18: 1`  
- **Bar 1**: 26 trades (72.2%)
- **Bar 2**: 6 trades (16.7%)
- **Bar 3**: 2 trades (5.6%)
- **Bar 5**: 1 trade (2.8%)
- **Bar 18**: 1 trade (2.8%)
- **H24 Timeout**: 0 trades (0.0%)

---

## 5. Annual Breakdown & Directional Splits

### Annual Performance Breakdown

| Year | Trades | Longs | Shorts | Wins | Losses | Gross R |
|---|---|---|---|---|---|---|
| 2015 | 0 | 0 | 0 | 0 | 0 | +0.00 R |
| 2016 | 0 | 0 | 0 | 0 | 0 | +0.00 R |
| 2017 | 1 | 0 | 1 | 1 | 0 | +1.50 R |
| 2018 | 2 | 1 | 1 | 1 | 1 | +0.50 R |
| 2019 | 3 | 2 | 1 | 1 | 2 | -0.50 R |
| 2020 | 7 | 3 | 4 | 4 | 3 | +3.00 R |
| 2021 | 4 | 1 | 3 | 1 | 3 | -1.50 R |
| 2022 | 7 | 4 | 3 | 1 | 6 | -4.50 R |
| 2023 | 3 | 3 | 0 | 3 | 0 | +4.50 R |
| 2024 | 3 | 1 | 2 | 1 | 2 | -0.50 R |
| 2025 | 4 | 2 | 2 | 2 | 2 | +1.00 R |
| 2026 | 2 | 1 | 1 | 1 | 1 | +0.50 R |

### Long vs. Short Directional Performance
- **Longs (Both Below)**: N = 18, Gross R = **+4.50 R**
- **Shorts (Both Above)**: N = 18, Gross R = **-0.50 R**

### Co-Release Split: Initial Jobless Claims (Post-Hoc Analysis)
- **11 Candidate Timestamps with Initial Jobless Claims (`840140001`)**: Sum Gross R = **+4.00 R**
- **25 Candidate Timestamps without Initial Jobless Claims**: Sum Gross R = **+0.00 R**

> [!CAUTION]
> **GOVERNANCE NOTICE ON DESCRIPTIVE SPLITS**:
> The observed co-release split (+4.00 R on Thursday Jobless Claims releases vs 0.00 R on other days) and directional asymmetry (+4.50 R on Longs vs -0.50 R on Shorts) are post-hoc historical observations across small subsets ($N=11$ and $N=18$). They do not represent causal attribution or independent statistical validation. They must **NOT** be used to create cherry-picked sub-filters post-hoc.

---

## 6. Sensitivity Analysis across Target Multiples & Intrabar Precedence

| Target Multiple | Intrabar Precedence | Trades | Win Rate | Gross R | Mean R | Profit Factor | Max DD | Ambiguous |
|---|---|---|---|---|---|---|---|---|
| **1.0x ATR** (1:1 R:R) | Conservative (Stop First) | 36 | 44.4% | -4.00 R | -0.11 R | 0.80 | 8.00 R | 3 |
| **1.0x ATR** (1:1 R:R) | Optimistic (Target First) | 36 | 52.8% | +2.00 R | +0.06 R | 1.12 | 6.00 R | 3 |
| **1.5x ATR** (Primary) | Conservative (Stop First) | 36 | 44.4% | +4.00 R | +0.11 R | 1.20 | 6.00 R | 2 |
| **1.5x ATR** (Primary) | Optimistic (Target First) | 36 | 50.0% | +9.00 R | +0.25 R | 1.50 | 6.00 R | 2 |
| **2.0x ATR** (1:2 R:R) | Conservative (Stop First) | 36 | 36.1% | +3.00 R | +0.08 R | 1.13 | 6.00 R | 2 |
| **2.0x ATR** (1:2 R:R) | Optimistic (Target First) | 36 | 41.7% | +9.00 R | +0.25 R | 1.43 | 6.00 R | 2 |

### Ambiguous Intrabar Collisions
Two episodes touched both the 1.0x Stop and the 1.5x Target during Bar 1:
1. **2021-05-12 15:30:00 (SHORT)**: Entry 1.21295, ATR14 10.5 pips. Bar 16:00:00 Low reached 1.21137 (TP) while High reached 1.21400 (SL).
2. **2024-07-11 15:30:00 (LONG)**: Entry 1.08864, ATR14 6.1 pips. Bar 16:00:00 Low reached 1.08803 (SL) while High reached 1.08956 (TP).

*Impact*: Resolving these 2 ambiguous bars in favor of Target changes the cumulative outcome from **+4.00 R** to **+9.00 R** (+125% increase). This demonstrates significant sensitivity to sub-hourly microstructural pathing.

---

## 7. Real-World Execution Limitations & Governance Boundary
1. **Gross-Only Limitation**: This simulation models gross mid/bid H1 candle prices. Zero broker spread, slippage, commission, or overnight financing is modeled. The owner assesses broker friction and execution costs separately before any live trading decision.
2. **Sub-Hourly Precedence**: 2 trades touched both SL and TP in the same hour. Backtesting on H1 OHLC cannot resolve intra-hour sequence. Forward demo testing with real tick capture is required.
3. **Data Exposure Disclosure**: The full 2015–2026 dataset has been visualized and inspected during exploratory analysis. Therefore, post-2022 observations cannot be claimed as an untouched, pristine holdout for this setup.
4. **Registration Governance**: A setup is registered **FOR** demo forward testing upon explicit approval by the Project Director / Codex before execution begins, not only after demo testing is complete. This candidate remains strictly UNDER AUDIT with ZERO registered claims.
