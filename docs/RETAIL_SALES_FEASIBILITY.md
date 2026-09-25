# Price-Blind Feasibility Investigation: US Retail Sales m/m Package on EURUSD

**Document Status**: RESEARCH DELIVERABLE (AUDITED & RECONCILED FEASIBILITY REPORT)  
**Research Stance**: Strict Non-Discovery, Zero Price Inspection, Zero Backtest  
**Chronological Split Boundary**: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`)  
**Investigated Series**:
- Primary Headline: `USD:US:840020010:r0` (Retail Sales m/m)
- Co-Released Core: `USD:US:840020011:r0` (Core Retail Sales m/m)  
**Evaluated Currency Pair**: `EURUSD` (PERIOD_H1 trade-server timestamps)  

---

## 1. Executive Summary & Forensic Audit Verdict

This document presents the reconciled, price-blind feasibility investigation of US Retail Sales m/m and Core Retail Sales m/m on EURUSD across the pre-2023 discovery window (`2015-01-01` to `2022-12-31`).

### Forensic Verdict: **FEASIBLE WITH SEVERE DOWNSTREAM ATTRIBUTION HAZARDS**
1. **Physical Forward Path Completeness**: **100.0% FORWARD PATH COMPLETENESS**. Across all **68 complete Actual/Forecast/Previous (A/F/P) packages** (May 2017 to December 2022), exactly **68 of 68 forward paths** are complete without missing H1 bars on EURUSD for **both 6 H4 (24 active hours) and 12 H4 (48 active hours)**.
2. **Resolution of the 65 vs 68 Discrepancy**: The previously reported count of 65 clean paths was caused by inheriting a separate **14-H4 pre-entry lookback filter** from the legacy `evidence/inventory/fms_episodes.jsonl` ledger. For a fixed-horizon directional return study, pre-entry volatility lookback is unnecessary. Pure forward-path outcome coverage is **68 / 68 (100.0%)**.
3. **Joint Package Integrity**: **100% CO-RELEASED**. Headline and Core Retail Sales are co-released at the identical timestamp in 100% of observations (96 of 96 pre-2023 packages). Zero orphaned or desynchronized releases exist.
4. **Surprise Sign Concordance ($N = 68$)**:
   - **Strict Agreement ($N = 49$)**: Headline and Core surprise signs agree in 49 of 68 complete packages (72.1% concordance: 27 POS/POS, 22 NEG/NEG).
   - **Active Conflict ($N = 9$)**: In 9 packages (13.2%), Headline and Core actively contradict each other (5 POS/NEG, 4 NEG/POS).
   - **Neutral / Zero Surprise ($N = 10$)**: 8 packages have one zero and one non-zero surprise; 2 packages have both zero.
5. **Physical Execution Delays**: Releases occur at either `15:30:00` or `16:30:00` trade-server time. Entry at the **Open of the next active H4 bar** immediately following announcement bar completion enforces:
   - **30-minute delay** for 15:30 releases (47 of 68 AFP packages, entering at 16:00:00).
   - **210-minute (3.5-hour) delay** for 16:30 releases (21 of 68 AFP packages, entering at 20:00:00).
6. **Severe Downstream Attribution Hazards (Major Caveats)**:
   - **Cross-Currency Collisions**: **57.4%** of complete AFP packages (39 of 68) coincide with simultaneous Canadian macroeconomic releases (37 with CAD, 6 with EUR; 4 coincide with both).
   - **Massive Same-Timestamp Release Bundles**: Retail Sales is never released in isolation. Packages bundle a Mean of **12.2 distinct economic indicators** (Min 5, Max 21) at the exact same second.
   - **Weekend Gap Exposure**: **32.4%** of 6 H4 paths (22 of 68) and **51.5%** of 12 H4 paths (35 of 68) span the Friday–Sunday market closure, extending wall-clock exposure from 24/48 hours to 72/96 hours.
   - **Later-Release Compounding**: During a 6 H4 window, trades encounter a Median of **10 subsequent macro packages** (5 USD, 5 EUR). During 12 H4, trades encounter a Median of **18 subsequent macro packages**.

---

## 2. Independent Series Identity & Metadata Reconciliation

All metadata fields were independently verified against `calendar_events.csv` and `calendar_releases.csv` in the pinned v3.1 export:

| Field | Primary Headline Series | Co-Released Core Series | Verification Status |
|---|---|---|---|
| **Series Key** | `USD:US:840020010:r0` | `USD:US:840020011:r0` | **Exact Match** |
| **MetaQuotes event_id** | `840020010` | `840020011` | **Exact Match** |
| **Event Name** | `Retail Sales m/m` | `Core Retail Sales m/m` | **Exact Match** |
| **Event Code** | `retail-sales-mm` | `retail-sales-ex-autos-mm` | **Exact Match** |
| **Currency / Country** | `USD` / `US` (840) | `USD` / `US` (840) | **Exact Match** |
| **Sector** | `CALENDAR_SECTOR_CONSUMER` (9) | `CALENDAR_SECTOR_CONSUMER` (9) | **Exact Match** |
| **Frequency** | `CALENDAR_FREQUENCY_MONTH` (2) | `CALENDAR_FREQUENCY_MONTH` (2) | **Exact Match** |
| **Time Mode** | `CALENDAR_TIMEMODE_DATETIME` (0) | `CALENDAR_TIMEMODE_DATETIME` (0) | **Exact Match** |
| **Unit** | `CALENDAR_UNIT_PERCENT` (1) | `CALENDAR_UNIT_PERCENT` (1) | **Exact Match** |
| **Multiplier** | `CALENDAR_MULTIPLIER_NONE` (0) | `CALENDAR_MULTIPLIER_NONE` (0) | **Exact Match** |
| **Digits** | `1` | `1` | **Exact Match** |
| **Importance** | `high` / `CALENDAR_IMPORTANCE_HIGH` (3) | `high` / `CALENDAR_IMPORTANCE_HIGH` (3) | **Exact Match** |
| **Source URL** | `https://census.gov` | `https://census.gov` | **Exact Match** |
| **Revision Stage** | `0` (100% of rows) | `0` (100% of rows) | **Zero Revisions != 0** |

### Release Count Reconciliation
- **Total Exported Releases (2015–2026)**: **141** Headline, **141** Core.
- **Pre-2023 Releases (`timestamp < 1672531200`)**: **96** Headline, **96** Core.
- **Post-2022 Sealed Releases (`timestamp >= 1672531200`)**: **45** Headline, **45** Core (Sealed Holdout).
- **Pre-2023 Complete A/F/P Records**: **68** Headline, **68** Core.
- **Pre-2023 Incomplete (Missing Forecast)**: **28** Headline, **28** Core.
  - The 28 missing forecasts span 2015 through April 2017. MetaQuotes began populating forecast values on `2017.05.12 15:30:00`.
  - Effective sample span is **5.67 years** (`2017-05-12` through `2022-12-15`).

---

## 3. Package-Level Joint Surprise-Sign Contingency Table

Surprise is defined strictly as $S = \text{Actual} - \text{Forecast}$ using raw scaled integers (`1e6` scale):
- Positive Surprise: $S > 0$
- Negative Surprise: $S < 0$
- Zero Surprise: $S = 0$
- Missing: Forecast is empty (`""` / `null`)

### Full Sign-Pair Contingency Matrix (All 96 Pre-2023 Packages)

| Headline ($S_H$) \ Core ($S_C$) | Core POS ($S_C > 0$) | Core NEG ($S_C < 0$) | Core ZERO ($S_C = 0$) | Core MISSING | Total Headline |
|---|---:|---:|---:|---:|---:|
| **Headline POS ($S_H > 0$)** | **27** | **5** | **2** | 0 | **34** |
| **Headline NEG ($S_H < 0$)** | **4** | **22** | **3** | 0 | **29** |
| **Headline ZERO ($S_H = 0$)** | **3** | **0** | **2** | 0 | **5** |
| **Headline MISSING** | 0 | 0 | 0 | **28** | **28** |
| **Total Core** | **34** | **27** | **7** | **28** | **96** |

### Breakdown by Economic Decision Category (68 Complete Packages)
1. **Strict Concordance (Both Same Sign)**: **49 packages** (72.1% of complete AFP)
   - Both Positive (POS/POS): **27 packages** (39.7%)
   - Both Negative (NEG/NEG): **22 packages** (32.4%)
2. **Active Conflict (Opposing Signs)**: **9 packages** (13.2% of complete AFP)
   - Headline POS, Core NEG: **5 packages**
   - Headline NEG, Core POS: **4 packages**
3. **One Neutral / One Directional**: **8 packages** (11.8% of complete AFP)
   - Headline POS, Core ZERO: **2 packages**
   - Headline ZERO, Core POS: **3 packages**
   - Headline NEG, Core ZERO: **3 packages**
   - Headline ZERO, Core NEG: **0 packages**
4. **Double Neutral (Both Zero)**: **2 packages** (2.9% of complete AFP)
5. **Missing Forecast**: **28 packages** (100% concentrated in 2015 to April 2017)

---

## 4. Chronological & Weekday Distribution

### Year-by-Year Completeness Table

| Year | Total Releases | Complete A/F/P | Missing Forecast | Strict Agree (POS/POS) | Strict Agree (NEG/NEG) | Conflict (POS/NEG) | Conflict (NEG/POS) | Neutral (Any Zero) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **2015** | 12 | 0 | **12** | 0 | 0 | 0 | 0 | 0 |
| **2016** | 12 | 0 | **12** | 0 | 0 | 0 | 0 | 0 |
| **2017** | 12 | 8 | **4** | 3 | 3 | 0 | 0 | 2 |
| **2018** | 12 | 12 | 0 | 6 | 4 | 0 | 1 | 1 |
| **2019** | 12 | 12 | 0 | 5 | 5 | 1 | 0 | 1 |
| **2020** | 12 | 12 | 0 | 4 | 5 | 1 | 1 | 1 |
| **2021** | 12 | 12 | 0 | 4 | 3 | 2 | 1 | 2 |
| **2022** | 12 | 12 | 0 | 5 | 2 | 1 | 1 | 3 |
| **Total** | **96** | **68** | **28** | **27** | **22** | **5** | **4** | **10** |

### Weekday Distribution of Releases

| Day of Week | All 96 Releases | 68 Complete AFP Releases | Share of AFP | Forward Path Weekend Crossing (6 H4) | Forward Path Weekend Crossing (12 H4) |
|---|---:|---:|---:|---|---|
| **Monday** | 5 | 5 | 7.4% | 0 (completes Tuesday) | 0 (completes Wednesday) |
| **Tuesday** | 17 | 11 | 16.2% | 0 (completes Wednesday) | 0 (completes Thursday) |
| **Wednesday** | 24 | 17 | 25.0% | 0 (completes Thursday) | 0 (completes Friday) |
| **Thursday** | 18 | 13 | 19.1% | 0 (completes Friday) | **13 (crosses weekend to Monday)** |
| **Friday** | 32 | 22 | **32.4%** | **22 (crosses weekend to Monday)** | **22 (crosses weekend to Tuesday)** |
| **Total** | **96** | **68** | **100.0%** | **22 / 68 (32.4%)** | **35 / 68 (51.5%)** |

---

## 5. Physical Execution Timing & Forward Path Audit

### A. Temporal Entry Definitions
- `15:30:00` release: Announcement H4 window (`12:00:00`–`16:00:00`) completes at `16:00:00`.
  - Entry occurs at the **Open of the next active H4 bar** ($T_{\text{entry}} = \mathbf{16:00:00}$, **30-minute delay**; 47 of 68 AFP packages).
- `16:30:00` release: Announcement H4 window (`16:00:00`–`20:00:00`) completes at `20:00:00`.
  - Entry occurs at the **Open of the next active H4 bar** ($T_{\text{entry}} = \mathbf{20:00:00}$, **210-minute / 3.5-hour delay**; 21 of 68 AFP packages).

### B. Horizon Exit Indexing
- **Primary Horizon (6 H4)**: 6 completed active H4 blocks ($B_0, B_1, B_2, B_3, B_4, B_5$). Exit price proxy is $\text{Close}_{\text{Bid}}(B_5)$. In continuous trading, duration is 24 active hours.
- **Secondary Horizon (12 H4)**: 12 completed active H4 blocks ($B_0, \dots, B_{11}$). Exit price proxy is $\text{Close}_{\text{Bid}}(B_{11})$. In continuous trading, duration is 48 active hours.

### C. Forward Path Completion vs Pre-Entry Lookback Audit
- **Forward Path Outcome Coverage**:
  - **6 H4 Horizon**: **68 / 68 (100.0%)** paths are complete without missing constituent H1 bars.
    - 22 paths cross the weekend closure (32.4%, all Friday releases).
    - 46 paths complete within the same week (67.6%).
  - **12 H4 Horizon**: **68 / 68 (100.0%)** paths are complete without missing constituent H1 bars.
    - 35 paths cross the weekend closure (51.5%: 22 Friday + 13 Thursday releases).
    - 33 paths complete within the same week (48.5%).
- **Pre-Entry History Lookback Audit (Decoupled Diagnostic)**:
  - *Where the 14-H4 lookback originated*: In legacy FMS v1 research, a 14-H4 lookback was used to calculate pre-entry Average True Range (ATR) for volatility stop and target placement.
  - *Why it is unnecessary here*: The current candidate research question evaluates fixed-horizon excess log returns ($R = d \cdot \ln(P_{\text{exit}} / P_{\text{entry}})$) and does not utilize ATR-scaled stops or targets.
  - *Actual Attrition if Intra-Week 14-H4 Lookback Were Imposed*:
    - 14 H4 blocks require 56 hours of continuous trading history.
    - Monday releases (entry at 16:00) accumulate at most **4 completed H4 blocks** in the current week.
    - Tuesday releases (entry at 16:00) accumulate at most **10 completed H4 blocks** in the current week.
    - Therefore, a strict same-week lookback disqualifies **all 5 Monday and all 11 Tuesday releases** (16 of 68 = 23.5%), reducing the sample to $N = 52$ (NOT 65).
    - The legacy count of 65 in `fms_episodes.jsonl` was an artifact of attempting to bridge across the weekend and failing on 3 specific Friday 23:00 / Sunday 23:00 broker session misalignments (`1554132600`, `1584459000`, `1615908600`).
  - *Conclusion*: Forward outcome paths are **100% complete ($N = 68$)**. Pre-entry lookback is not imposed on this return-only question.

---

## 6. Downstream Hazards & Attribution Confounders

### 1. Cross-Currency Collisions (57.4% on Complete AFP)
- Across all 96 pre-2023 packages: **45 / 96 (46.9%)** collide with other sovereign currencies.
- Across the 68 complete AFP packages: **39 / 68 (57.4%)** collide with simultaneous non-USD releases at the exact same timestamp:
  - **Canadian Dollar (CAD)**: 37 collisions (Canadian Manufacturing Sales, Wholesale Trade, Merchandise Trade at 08:30 ET).
  - **Euro (EUR)**: 6 collisions (Eurozone Trade Balance, Industrial Production).
  - (4 packages collide with both CAD and EUR: $37 + 6 - 4 = 39$).
- *Hazard*: EURUSD post-release price action reflects broader North American cross-border portfolio rebalancing rather than pure US consumer retail demand.

### 2. Massive Simultaneous Release Bundling (Mean 12.2 Series per Release)
US Retail Sales is never released in isolation. Packages bundle an average of **12.2 distinct economic series** (Min 5, Max 21) at the exact same second:
- `USD:US:840020011:r0` (Core Retail Sales m/m)
- `USD:US:840020012:r0` (Retail Control m/m)
- `USD:US:840020021:r0` (Retail Sales excl. Autos and Gas m/m)
- `USD:US:840020025:r0` (Retail Sales y/y)
- `USD:US:840030026:r0` (Import Price Index m/m)
- `USD:US:840030028:r0` (Export Price Index m/m)
- NY Empire State Manufacturing Index (mid-month releases)
- *Hazard*: Mathematically isolating the price drift of EURUSD to retail goods demand rather than simultaneous import inflation is impossible from timestamp analysis alone.

### 3. Compounding Later-Release Exposure
- **During 6 H4 (24 active hours)**: Paths encounter a Median of **5 subsequent USD packages** and **5 subsequent EUR packages** (Total Median = 10 later macro events).
- **During 12 H4 (48 active hours)**: Paths encounter a Median of **9 subsequent USD packages** and **9 subsequent EUR packages** (Total Median = 18 later macro events).
- *Hazard*: Post-announcement drift cannot be cleanly attributed to the initial retail surprise when trades absorb multiple subsequent FOMC speeches, initial claims, and ECB commentary.

---

## 7. Comparative Benchmark: Verified German Ifo vs US Retail Sales

Every cell below is verified directly against immutable project evidence (`evidence/trials/ifo/FMS_PILOT_IFO_PROTOCOL.md` and `ifo_pilot_ledger.json`):

| Operational Dimension | German Ifo Pilot (Verified Evidence) | US Retail Sales (Audited Candidate) |
|---|---|---|
| **Co-Released Indicators** | **2 Series**: Ifo Climate (`276030003`) + Expectations (`276030001`) | **2 Series**: Headline (`840020010`) + Core (`840020011`) |
| **Total Pre-2023 Packages** | 96 packages | 96 packages |
| **Missing Forecast Exclusions** | 43 packages (pre-Nov 2018 lacked MT5 forecasts) | 28 packages (pre-May 2017 lacked MT5 forecasts) |
| **Complete AFP Sample** | $N = 45$ complete forecast packages | **$N = 68$ complete forecast packages** |
| **Actionable Strict Agreement** | **$N = 40$** (18 Long, 22 Short EURUSD) | **$N = 49$** (27 Short, 22 Long EURUSD) |
| **Active Conflict Exclusions** | 3 packages (6.7% of complete forecasts) | 9 packages (13.2% of complete forecasts) |
| **Cross-Currency Collisions** | **4 of 40 (10.0%)** have same-time GBP collisions (`Yes (GBP)`) | **39 of 68 (57.4%)** have same-time CAD / EUR collisions |
| **Weekday Distribution (Actionable)** | Mon (15), Tue (7), Fri (**6 = 15.0%**), Wed (6), Thu (6) | Mon (5), Tue (11), Wed (17), Thu (13), Fri (**22 = 32.4%**) |
| **Enforced Entry Delays** | **30 min** (11:30 $\to$ 12:00, 23 rows) / **210 min** (12:30 $\to$ 16:00, 17 rows) | **30 min** (15:30 $\to$ 16:00, 47 rows) / **210 min** (16:30 $\to$ 20:00, 21 rows) |
| **Forward Path Completeness (6 H4)** | 40 / 40 (100.0% of actionable) | **68 / 68 (100.0% of complete AFP)** |
| **Forward Weekend Crossings (6 H4)** | 0 of 40 (Friday entries had no weekend gap in test) | **22 of 68 (32.4%)** cross Friday–Monday closure |
| **Trial Disposition / Status** | **STATE 3: NO CONVINCING EVIDENCE** ($p = 0.9575$) | **Candidate Question (Price-Blind Audit)** |

---

## 8. Forensic Data Integrity & Prior Inspection Disclosure

1. **Disclosure of Prior Schema Inspection**: During initial schema verification, lines 1–5 of `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv` were inspected via tool to verify column headers and confirm that column 0 corresponds to `time`.
2. **Zero Price-Outcome Computation**: No price returns, directional drift, win rates, MFE/MAE, or backtest metrics have ever been calculated for this candidate.
3. **Genuine Field-0 Timestamp-Only Streaming**: Subsequent candle processing is performed strictly via `stream_candle_timestamps_only`, which extracts only the field-0 substring before the first comma (`line.split(',', 1)[0]`), ensuring that columns 1..N (OHLC prices, spreads, volumes) are never tokenized or processed.
4. **Pre-2023 Boundary Sealing**: All timestamps $\ge 1672531200$ remain strictly sealed.
