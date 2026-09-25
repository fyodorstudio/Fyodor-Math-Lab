# Price-Blind Feasibility Investigation: US Retail Sales m/m Package on EURUSD

**Document Status**: RESEARCH DELIVERABLE (PRICE-BLIND FEASIBILITY AUDIT)  
**Research Stance**: Strict Non-Discovery, Zero Price Inspection, Zero Backtest  
**Chronological Split Boundary**: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`)  
**Investigated Series**:
- Primary Headline: `USD:US:840020010:r0` (Retail Sales m/m)
- Co-Released Core: `USD:US:840020011:r0` (Core Retail Sales m/m)  
**Evaluated Currency Pair**: `EURUSD` (PERIOD_H1 trade-server timestamps)  

---

## 1. Executive Summary & Forensic Verdict

This document presents the independent, price-blind feasibility investigation of US Retail Sales m/m and Core Retail Sales m/m on EURUSD across the pre-2023 historical discovery window (`2015-01-01` to `2022-12-31`).

### Forensic Verdict: **FEASIBLE WITH SEVERE DOWNSTREAM ATTRIBUTION HAZARDS**
1. **Physical Data Completeness**: **PASSABLE BUT CONSTRAINED**. Across 8 full calendar years (96 monthly releases), exactly **68 releases** (May 2017 to December 2022) contain complete Actual, Forecast, and Previous (A/F/P) records. The 2015 to early-2017 period (28 releases) completely lacks consensus forecast data in the MT5 provider calendar and cannot be used for surprise-driven research.
2. **Joint Package Integrity**: **100% CO-RELEASED**. Headline and Core Retail Sales are co-released at the exact same timestamp in 100% of observations (96 of 96 packages). Zero orphaned or desynchronized releases exist.
3. **Surprise Sign Concordance**:
   - **Strict Agreement ($N = 49$)**: Headline and Core surprise signs agree in 49 of 68 complete packages (72.1% concordance: 27 POS/POS, 22 NEG/NEG).
   - **Active Conflict ($N = 9$)**: In 9 packages (13.2%), Headline and Core actively contradict each other (5 POS/NEG, 4 NEG/POS).
   - **Neutral / Zero Surprise ($N = 10$)**: 8 packages have one zero and one non-zero surprise; 2 packages have both zero.
4. **Physical Execution Delays**: Releases occur at either `15:30:00` or `16:30:00` trade-server time due to US/EU Daylight Saving Time shifts. Next-completed H4 entry enforces a **30-minute delay** for 15:30 releases (47 of 68 AFP packages) and a **210-minute (3.5-hour) delay** for 16:30 releases (21 of 68 AFP packages).
5. **Downstream Attribution Hazards (Major Caveats)**:
   - **Cross-Currency Collisions**: **57.4%** of complete AFP packages (39 of 68) coincide with simultaneous Canadian macroeconomic releases (37 with CAD, 6 with EUR).
   - **Same-Timestamp Release Bundles**: Retail Sales is never released in isolation. Packages bundle a Mean of **12.2 distinct economic indicators** (Min 5, Max 21) at the exact same second (including Retail Control, Import/Export Price Indices, and Empire State Manufacturing).
   - **Weekend Gap Exposure**: **33.8%** of 6 H4 paths (22 of 65) and **53.8%** of 12 H4 paths (35 of 65) span the Friday–Sunday market closure, extending wall-clock exposure from 24/48 hours to 72/96 hours.
   - **Later-Release Compounding**: During a 6 H4 holding window, trades encounter a Median of **10 subsequent macro packages** (5 USD, 5 EUR). During 12 H4, trades encounter a Median of **18 subsequent macro packages**.

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
- **Post-2022 Sealed Releases (`timestamp >= 1672531200`)**: **45** Headline, **45** Core (Holdout).
- **Pre-2023 Complete A/F/P Records**: **68** Headline, **68** Core.
- **Pre-2023 Incomplete (Missing Forecast)**: **28** Headline, **28** Core.

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
1. **Strict Concordance (Both Same Sign)**: **49 packages** (72.1%)
   - Both Positive (POS/POS): **27 packages** (39.7%)
   - Both Negative (NEG/NEG): **22 packages** (32.4%)
2. **Active Conflict (Opposing Signs)**: **9 packages** (13.2%)
   - Headline POS, Core NEG: **5 packages**
   - Headline NEG, Core POS: **4 packages**
3. **One Neutral / One Directional**: **8 packages** (11.8%)
   - Headline POS, Core ZERO: **2 packages**
   - Headline ZERO, Core POS: **3 packages**
   - Headline NEG, Core ZERO: **3 packages**
   - Headline ZERO, Core NEG: **0 packages**
4. **Double Neutral (Both Zero)**: **2 packages** (2.9%)
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

*Key Takeaway*: Effective research sample is limited to **5.67 years** (`2017-05-12` through `2022-12-15`).

### Weekday Distribution of Releases

| Day of Week | All 96 Releases | 68 Complete AFP Releases | Share of AFP | Physical Entry Implications |
|---|---:|---:|---:|---|
| **Monday** | 5 | 5 | 7.4% | Max 4 completed H4 bars in current week lookback. |
| **Tuesday** | 17 | 11 | 16.2% | Max 10 completed H4 bars in current week lookback. |
| **Wednesday** | 24 | 17 | 25.0% | Mid-week, exits Thursday 16:00/20:00 (no weekend). |
| **Thursday** | 18 | 13 | 19.1% | 6 H4 exits Friday; 12 H4 crosses weekend to Monday. |
| **Friday** | 32 | 22 | **32.4%** | **Must cross weekend closure** (72h / 96h wall clock). |
| **Total** | **96** | **68** | **100.0%** | — |

---

## 5. Physical Execution Timing & Session Realities

### Release Clock Times & Enforced Entry Delays
- **15:30:00 Trade-Server Time**: 47 of 68 AFP packages (69.1%).
  - Next H4 boundary is `16:00:00`.
  - **Enforced Entry Delay**: **30 minutes** (0.5 hours).
- **16:30:00 Trade-Server Time**: 21 of 68 AFP packages (30.9%).
  - Next H4 boundary is `20:00:00`.
  - **Enforced Entry Delay**: **210 minutes** (3.5 hours).

### Candle Timestamp Coverage on EURUSD
Across the 68 complete AFP packages:
- **Clean 6 H4 Paths (24 active hours)**: **65 packages** (95.6%).
  - 3 packages fail pre-entry 14-bar lookback without weekend crossings (`1554132600` on Monday, `1584459000` on Tuesday, `1615908600` on Tuesday).
  - All 65 clean paths have 24 continuous active H1 bars without missing data.
  - **22 clean paths (33.8%) cross the weekend closure**.
- **Clean 12 H4 Paths (48 active hours)**: **65 packages** (95.6%).
  - **35 clean paths (53.8%) cross the weekend closure**.

### Sign Contingency Under Strict 14-Bar Lookback ($N = 65$)
The 3 disqualified episodes all belong to the `NEG/NEG` cell:
- **Strict Agreement POS/POS**: **27 packages**
- **Strict Agreement NEG/NEG**: **19 packages** (down from 22)
- **Total Strict Concordance**: **46 packages**
- **Active Conflict**: **9 packages** (5 POS/NEG, 4 NEG/POS)
- **Neutral / Zero**: **10 packages**

---

## 6. Downstream Hazards & Attribution Confounders

### 1. Cross-Currency Collisions (57.4%)
- **39 out of 68 complete AFP packages** collide with simultaneous non-USD releases at the exact same timestamp.
- **Canadian Dollar (CAD)**: 37 collisions. The US and Canada frequently synchronize 08:30 ET releases (e.g. Canadian Manufacturing Sales, Wholesale Trade, Merchandise Trade).
- **Euro (EUR)**: 6 collisions (Eurozone Trade Balance, Industrial Production).
- *Hazard*: EURUSD price action following 08:30 ET is influenced by North American trade and CAD cross-flows, not solely US consumer demand.

### 2. Massive Simultaneous Release Bundling
US Retail Sales is not released alone. The Census Bureau and Bureau of Labor Statistics simultaneously publish:
- `USD:US:840020011:r0` (Core Retail Sales m/m)
- `USD:US:840020012:r0` (Retail Control m/m)
- `USD:US:840020021:r0` (Retail Sales excl. Autos and Gas m/m)
- `USD:US:840020025:r0` (Retail Sales y/y)
- `USD:US:840030026:r0` (Import Price Index m/m)
- `USD:US:840030028:r0` (Export Price Index m/m)
- NY Empire State Manufacturing Index (mid-month releases)
- Across our 68 complete packages, each release bundles an average of **12.2 distinct economic series** (Min 5, Max 21).
- *Hazard*: Disentangling whether price drift is caused by retail sales or simultaneous import price inflation is physically impossible from timestamp analysis alone.

### 3. Compounding Later-Release Exposure
- **During 6 H4 (24 hours)**: A trade encounters a Median of **5 subsequent USD packages** and **5 subsequent EUR packages** (Total Median = 10 later macro events).
- **During 12 H4 (48 hours)**: A trade encounters a Median of **9 subsequent USD packages** and **9 subsequent EUR packages** (Total Median = 18 later macro events).
- *Hazard*: Attributing a 24-hour or 48-hour return to the initial retail sales shock rather than subsequent FOMC speeches, initial jobless claims, or ECB commentary requires severe heroic assumptions.

---

## 7. Strategic Impact & Comparative Summary

| Feature / Metric | Building Permits (Candidate 1) | German Ifo (Failed Pilot) | US Retail Sales (Candidate Question) |
|---|---|---|---|
| **Pre-2023 Complete AFP Sample** | $N = 66$ (clean 6 H4) | $N = 40$ (clean 6 H4) | **$N = 65$ (clean 6 H4)** |
| **Strict Sign Agreement Sample** | $N = 43$ (65.2%) | N/A (single series) | **$N = 46$ (70.8%)** |
| **Active Conflict Share** | 23 / 66 (34.8%) | N/A | **9 / 65 (13.8%)** |
| **Cross-Currency Collisions** | 71.9% (CAD) | 0.0% | **57.4% (CAD, EUR)** |
| **Same-Timestamp Releases** | Mean 3.2 | Mean 1.0 (isolated) | **Mean 12.2 (extreme bundling)** |
| **Weekend Crossing Rate (6 H4)** | 19.7% (13/66) | 0.0% (Wednesday releases) | **33.8% (22/65)** |
| **Enforced Entry Delays** | 30 min / 210 min | 60 min (10:00 $\to$ 11:00) | **30 min / 210 min** |
| **Later Packages Overlap (6 H4)** | Median 7 | Median 14 | **Median 10** |
