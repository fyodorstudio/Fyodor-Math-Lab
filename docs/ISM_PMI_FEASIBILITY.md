# Price-Blind Feasibility Investigation: US ISM Manufacturing PMI on EURUSD

**Document Status**: RESEARCH DELIVERABLE (AUDITED PRICE-BLIND FEASIBILITY & PRE-PRICE DESIGN REPORT)
**Research Stance**: Strict Non-Discovery, Zero Price Inspection, Zero Backtest, Zero OHLC Reading
**Chronological Split Boundary**: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`)
**Investigated Series**:
- Primary Candidate: `USD:US:840040001:r0` (ISM Manufacturing PMI)
- Evaluated Co-Released Components:
  - `USD:US:840040002:r0` (ISM Manufacturing Prices Paid)
  - `USD:US:840040004:r0` (ISM Manufacturing Employment)
  - `USD:US:840040006:r0` (ISM Manufacturing New Orders)
- Evaluated Preceding Confounder:
  - `USD:US:840500001:r3` (S&P Global Manufacturing PMI, Revision 3, released 15 minutes prior)
  - `USD:US:840500001:r1` (S&P Global Manufacturing PMI, Revision 1 Flash, tracked separately)
**Evaluated Currency Pair**: `EURUSD` (PERIOD_H1 trade-server timestamps)
**Reconciliation Module**: [`src/ism_reconciliation.py`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/ism_reconciliation.py) (CLI runnable; verified by [`tests/test_ism_reconciliation.py`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/tests/test_ism_reconciliation.py))

---

## 1. Executive Summary & Forensic Audit Verdict

Following the disconfirmation and permanent closure of the US Retail Sales directional trial on 2026-09-26, this investigation conducts the price-blind feasibility screening and pre-price architecture design for **US ISM Manufacturing PMI** on EURUSD. All counts and findings are derived directly from the pinned MT5 v3.1 export and reproducible via `python -m src.ism_reconciliation`.

### Forensic Feasibility Verdict: **FEASIBLE FOR CANDIDATE PROTOCOL DESIGN (WITH EXPLICIT CONFOUNDER AUDIT)**

1. **Physical Forward Path Completeness: 100.0% Complete**:
   Across all **67 complete Actual/Forecast/Previous (A/F/P) pre-2023 packages** (June 2017 to December 2022), exactly **67 of 67 forward candle paths** on EURUSD are 100% complete without missing bars for both **24 active H1 hours** (1 trading day) and **48 active H1 hours** (2 trading days).
2. **Actionable Pre-2023 Sample Size: Exactly $N = 66$ Packages**:
   - Total pre-2023 releases: **96 monthly releases** (January 2015 to December 2022).
   - Incomplete packages (missing forecasts): **29 releases** (all 24 in 2015–2016, plus 5 in Jan–May 2017). MetaQuotes began recording consensus forecasts in June 2017.
   - Complete A/F/P packages: **67 releases** (June 2017 to December 2022).
   - Zero-surprise release: Exactly **1 release** (`2018-03-01 18:00:00`, timestamp `1519927200`, Actual = 60.8, Forecast = 60.8, $S_H = 0.0$), excluded as non-directional.
   - Actionable pre-2023 directional episodes: **$N = 66$ packages** (28 Hawkish / Short EURUSD, 38 Dovish / Long EURUSD).
3. **Execution Timing & Broker Trade-Server Synchronization**:
   - Releases occur at **10:00:00 AM New York time** on the first business day of the month.
   - In broker trade-server time (Elev8 / MetaQuotes UTC+3 fixed summer convention):
     - Summer (EDT, UTC-4): 10:00 AM NY = 14:00 UTC = **17:00:00 server time** (62 of 96 releases).
     - Winter (EST, UTC-5): 10:00 AM NY = 15:00 UTC = **18:00:00 server time** (34 of 96 releases).
   - Every release lands **exactly on an H1 candle boundary** (`timestamp % 3600 == 0`).
   - Entering at the next H4 bar open (20:00 server time) causes an asymmetrical delay (120 min winter vs 180 min summer). The pre-price design specifies entry at the **Open of the next active H1 bar** ($T_{\text{release}} + 3600$), enforcing a **uniform 60-minute post-announcement absorption delay** across all seasons.
   - *Execution Caveat*: A 60-minute delay substantially reduces immediate release-time spread widening and slippage exposure, but does not guarantee the total absence of execution slippage or spread spikes.
4. **Clean Currency Isolation (Low Cross-Currency Collision)**:
   Unlike US Retail Sales (which suffered a 57.4% collision rate primarily with Canadian releases), ISM Manufacturing PMI exhibits a **96.9% clean USD isolation rate** (93 of 96 pre-2023 releases are completely free of same-timestamp foreign releases). Exactly 3 release dates exhibit foreign-currency collisions, of which only **1 belongs to the 66 actionable releases** (2022-06-01 CAD BoC rate decision/statement).
5. **Preceding Informational Confounder: S&P Global 15-Minute Lead**:
   S&P Global Manufacturing PMI (`840500001`, Revision 3) releases **15 minutes earlier** (9:45 AM NY / 900 seconds prior) on **91 of 96 release dates (94.8%)** and on **61 of the 66 actionable releases with populated forecasts**. We audit this relationship and pre-declare its role as a diagnostic partition rather than an exploratory post-hoc filter.
6. **Pre-Declared Primary Rule & Explicit Rejection of Concordance**:
   The primary rule is pre-declared on **Headline ISM Manufacturing PMI alone** ($S_H = A - F$). Multi-component concordance (forcing agreement between Headline and Prices Paid) is **explicitly rejected** prior to price inspection, preventing researcher degrees of freedom that would discard 43.3% of the dataset.

---

## 2. Pinned Series Identity & Component Inventory

All metadata fields were independently audited and verified against `calendar_events.csv` and `calendar_releases.csv` in the pinned MT5 v3.1 export:

| Metadata Field | Headline ISM PMI | Prices Paid Component | Employment Component | New Orders Component |
|---|---|---|---|---|
| **Series Key** | `USD:US:840040001:r0` | `USD:US:840040002:r0` | `USD:US:840040004:r0` | `USD:US:840040006:r0` |
| **MetaQuotes event_id** | `840040001` | `840040002` | `840040004` | `840040006` |
| **Event Name** | `ISM Manufacturing PMI` | `ISM Manufacturing Prices Paid` | `ISM Manufacturing Employment` | `ISM Manufacturing New Orders` |
| **Event Code** | `ism-manufacturing-pmi` | `ism-prices-paid` | `ism-manufacturing-employment` | `ism-manufacturing-new-orders` |
| **Currency / Country** | `USD` / `US` (840) | `USD` / `US` (840) | `USD` / `US` (840) | `USD` / `US` (840) |
| **Sector** | `CALENDAR_SECTOR_BUSINESS` (8) | `CALENDAR_SECTOR_BUSINESS` (8) | `CALENDAR_SECTOR_BUSINESS` (8) | `CALENDAR_SECTOR_BUSINESS` (8) |
| **Frequency** | `MONTH` (2) | `MONTH` (2) | `MONTH` (2) | `MONTH` (2) |
| **Time Mode** | `DATETIME` (0) | `DATETIME` (0) | `DATETIME` (0) | `DATETIME` (0) |
| **Unit** | `CALENDAR_UNIT_NONE` (0) | `CALENDAR_UNIT_NONE` (0) | `CALENDAR_UNIT_NONE` (0) | `CALENDAR_UNIT_NONE` (0) |
| **Multiplier** | `NONE` (0) | `NONE` (0) | `NONE` (0) | `NONE` (0) |
| **Digits** | `1` | `1` | `1` | `1` |
| **Importance** | `high` (3) | `high` (3) | `medium` (2) | `low` (1) |
| **Source URL** | `https://ismworld.org` | `https://ismworld.org` | `https://ismworld.org` | `https://ismworld.org` |

### Pre-2023 Inventory & Missing Forecast Analysis

Across the 8-year pre-2023 historical span (96 monthly calendar slots from 2015-01-01 to 2022-12-31):

| Series Key | Event Name | Total Pre-2023 Rows | Actuals Present | Forecasts Present | Complete A/F/P Packages | Incomplete / Missing F |
|---|---|---:|---:|---:|---:|---:|
| `840040001` | **Headline ISM PMI** | **96** | **96** | **67** | **67** | **29** (2015–May 2017) |
| `840040002` | Prices Paid | 96 | 96 | 67 | 67 | 29 (2015–May 2017) |
| `840040004` | Employment | 96 | 96 | 64 | 64 | 32 (2015–Aug 2017) |
| `840040006` | New Orders | 96 | 96 | 64 | 64 | 32 (2015–Aug 2017) |

- **Observation Period**: Complete A/F/P records for Headline ISM PMI span from `2017-06-01 17:00:00` through `2022-12-01 17:00:00` (5.58 continuous calendar years).
- **Missing Forecast Period**: MetaQuotes did not populate consensus forecasts for ISM series prior to June 2017. All 96 releases have recorded Actual and Previous values, but the first 29 releases lack consensus expectations. Under strict non-improvisation rules, missing historical forecasts are not backfilled or approximated.

---

## 3. Package Structure & Surprise Distribution

### 3.1 Surprise Definition
Consensus surprise is measured strictly as the difference between Actual and Forecast using raw unrounded scaled integers (`1e6` scale):
$$S_H = \text{Actual} - \text{Forecast} = A_H - F_H$$

Economic interpretation for USD:
- $S_H > 0$: **Positive Shock (Hawkish)**. US manufacturing expansion exceeds expectations, indicating stronger aggregate demand and upward interest rate pressure $\implies$ Expected USD appreciation $\implies$ **Short EURUSD**.
- $S_H < 0$: **Negative Shock (Dovish)**. US manufacturing activity falls short of expectations, indicating economic contraction or slowdown $\implies$ Expected USD depreciation $\implies$ **Long EURUSD**.
- $S_H = 0.0$: **Neutral Surprise**. Release exactly matches consensus $\implies$ **No directional signal (Excluded)**.

### 3.2 Pre-2023 Headline Surprise Distribution ($N = 67$)

Across the 67 complete A/F/P releases:
- **Positive Surprises ($S_H > 0$)**: **28 packages** (41.8% of complete packages)
- **Negative Surprises ($S_H < 0$)**: **38 packages** (56.7% of complete packages)
- **Zero Surprises ($S_H = 0.0$)**: Exactly **1 package** (1.5% of complete packages)
  - Date: `2018-03-01 18:00:00` (timestamp `1519927200`, Actual = 60.8, Forecast = 60.8)
- **Net Actionable Discovery Sample**: **$N = 66$ packages** ($28 + 38$).

### 3.3 Multi-Component Relationship: Headline vs. Prices Paid Contingency

To evaluate whether component concordance is viable, we compute the joint contingency matrix between Headline PMI ($S_H$) and Prices Paid ($S_P$) using raw scaled integers (`actual_raw_scaled_1e6 - forecast_raw_scaled_1e6`):

| Headline ($S_H$) \ Prices Paid ($S_P$) | Prices Paid POS ($S_P > 0$) | Prices Paid NEG ($S_P < 0$) | Prices Paid ZERO ($S_P = 0$) | Total Headline |
|---|---:|---:|---:|---:|
| **Headline POS ($S_H > 0$)** | **16** | **12** | 0 | **28** |
| **Headline NEG ($S_H < 0$)** | **17** | **21** | 0 | **38** |
| **Headline ZERO ($S_H = 0$)** | **1** | 0 | 0 | **1** |
| **Total Prices Paid** | **34** | **33** | **0** | **67** |

#### Critical Methodological Finding: Concordance Rate is Low (55.2%)
- **Concordant Packages (Both POS or Both NEG)**: **37 packages** ($16 + 21$, 55.2% of complete packages).
- **Discordant Packages (Opposite Signs)**: **29 packages** ($12 + 17$, 43.3% of complete packages).
- **Neutral Package (Headline ZERO, Prices POS)**: **1 package** (`2018-03-01`, 1.5%).
- **Substantive Economic Rationale**:
  - Unlike Retail Sales (where Headline and Core measure the same consumer basket with/without autos, yielding 72.1% concordance), ISM Prices Paid measures **input cost inflation**, whereas Headline PMI measures **manufacturing volume/activity**.
  - In stagflationary or supply-shock environments (e.g. supply chain bottlenecks in 2021–2022), manufacturing activity slows while input costs surge. Thus, $S_H < 0$ and $S_P > 0$ is a frequent, economically coherent macro state.
  - Imposing strict concordance between Headline and Prices Paid would **discard 29 of 66 actionable releases (43.9% of sample)**, collapsing the sample size from $N = 66$ to $N = 37$.
  - **Pre-Price Decision**: Multi-component concordance is **REJECTED** as an entry filter for ISM Manufacturing. The primary hypothesis is tested solely on Headline PMI. Prices Paid and Employment are preserved strictly as post-unblinding attribution diagnostics.

---

## 4. Timing, Broker Trade-Server Mapping, and Physical Execution

### 4.1 Release Time vs. Broker Bar Alignment
Releases occur at 10:00:00 AM New York time on the first business day of each month:
- **Summer Schedule (EDT, UTC-4)**:
  - 10:00 AM NY = 14:00 UTC = **17:00:00 broker trade-server time** (62 of 96 pre-2023 releases).
- **Winter Schedule (EST, UTC-5)**:
  - 10:00 AM NY = 15:00 UTC = **18:00:00 broker trade-server time** (34 of 96 pre-2023 releases).

All releases land exactly on an H1 candle boundary (`timestamp % 3600 == 0`).

### 4.2 The H4 vs. H1 Bar Alignment Dilemma
Under the standard Elev8 / MetaQuotes 4-hour bar structure, H4 candles open at `00:00, 04:00, 08:00, 12:00, 16:00, 20:00`.
- In summer, a release at `17:00:00` lands inside the `16:00–20:00` H4 bar. Waiting for the next H4 bar requires waiting until `20:00:00` (**180-minute delay**).
- In winter, a release at `18:00:00` also lands inside the `16:00–20:00` H4 bar. Waiting for the next H4 bar requires waiting until `20:00:00` (**120-minute delay**).

This introduces two severe technical defects:
1. **Asymmetrical Execution Latency**: Winter trades enter 2 hours after release; summer trades enter 3 hours after release.
2. **Excessive Market Absorption Time**: By 120–180 minutes post-release, high-frequency liquidity providers and algorithmic participants have completely re-priced the macro surprise, potentially extinguishing any post-announcement drift.

### 4.3 Proposed Execution Solution: Uniform 60-Minute H1 Entry
To resolve this defect, the pre-price design specifies entry at the **Open of the next active H1 candle**:
$$T_{\text{entry}} = T_{\text{release}} + 3600$$
- Summer releases (`17:00:00`) enter at the Open of the `18:00:00` H1 candle (**60-minute delay**).
- Winter releases (`18:00:00`) enter at the Open of the `19:00:00` H1 candle (**60-minute delay**).

This guarantees:
- **100% Seasonal Symmetry**: Exactly 60 minutes of post-announcement absorption delay in both summer and winter.
- **Physical Feasibility**: Substantially reduces release-time spread widening and slippage exposure, though execution slippage and spread widening cannot be guaranteed to be zero.
- **Pure H1 Granularity**: The holding period is parameterized in active H1 trading hours.

---

## 5. Forward Path Completeness & Continuity Audit

EURUSD H1 candle coverage was evaluated across all 67 complete A/F/P packages in the pre-2023 discovery window:

### 5.1 Candle Path Completeness

| Holding Horizon | Active H1 Bars Required | Total Packages Evaluated | 100% Complete Paths | Missing / Truncated Paths | Path Completeness Rate |
|---|---:|---:|---:|---:|---:|
| **Primary: 24 H1 Bars (1 Day)** | 24 active bars | 67 | 67 | 0 | **100.0%** |
| **Descriptive: 48 H1 Bars (2 Days)** | 48 active bars | 67 | 67 | 0 | **100.0%** |

Zero missing bars, holes, or abnormal gaps exist in the EURUSD H1 candle series across any of the 67 forward trade paths.

### 5.2 Weekend Gap Crossings
Releases occur on the first business day of the month:
- **24-H1 Horizon**: Exactly **11 of 67 paths (16.4%)** cross a Friday–Sunday weekend boundary (where the release occurs on a Thursday or Friday).
- **48-H1 Horizon**: Exactly **22 of 67 paths (32.8%)** cross a weekend boundary.
- Relative to Retail Sales (where 32.4% crossed weekends for 24 hours), ISM has **half the weekend gap exposure** because first-of-month releases cluster earlier in the trading week.

---

## 6. Confounder Audit: S&P Global (Markit) 15-Minute Preceding Release

### 6.1 The 15-Minute Lead Phenomenon (Revision 3 vs. Revision 1)
The S&P Global (formerly Markit) US Manufacturing PMI (`USD:US:840500001`) is released at **9:45:00 AM New York time**—exactly **15 minutes (900 seconds) prior** to the ISM Manufacturing PMI release at 10:00:00 AM NY.

An audit of all 96 pre-2023 calendar rows in `calendar_releases.csv` reveals:
- **Revision 3 (Final Release)**:
  - Exactly **96 pre-2023 rows**, with **67 populated consensus forecasts**.
  - **Same-Day 15-Minute Lead**: In **91 of 96 releases (94.8%)**, Revision 3 released exactly 900 seconds prior to ISM on the same day.
  - **Actionable Releases**: In **61 of the 66 actionable ISM releases (92.4%)**, Revision 3 released exactly 900 seconds prior with a populated consensus forecast.
- **Revision 1 (Flash Release)**:
  - Tracked separately; has **96 pre-2023 rows** and **68 populated forecasts**. Flash releases occur earlier in the month (approximately mid-month) and do not collide with ISM.
- **Early January Discrepancy (5 releases)**: In 5 instances (`2018-01-03`, `2019-01-03`, `2020-01-03`, `2021-01-05`, `2022-01-04`), S&P Global released its final PMI on January 2nd, while ISM released 1 to 2 business days later due to holiday scheduling conventions.

### 6.2 Epistemological & Attribution Risk
Does the market react to S&P Global at 9:45 AM, partially pricing in the manufacturing environment before ISM is published at 10:00 AM?
- **Hypothesis A (Market Preemption)**: If S&P Global pre-empts ISM, post-10:00 AM drift might be muted, erratic, or reversed if ISM merely confirms what S&P already showed.
- **Hypothesis B (ISM Primacy)**: Institutional fixed income and currency markets historically treat ISM Manufacturing as the premier benchmark, treating S&P Global's US survey as secondary. If so, ISM retains independent market-moving power.

### 6.3 Pre-Price Governance Policy on S&P Global
Because candidate price returns remain **strictly uninspected**, we cannot know whether S&P Global pre-empts ISM. To maintain forensic integrity:
1. **Zero Exploratory Filtering**: We **do not** filter out ISM trades based on S&P Global surprises. The primary sample remains all $N = 66$ ISM releases.
2. **Pre-Declared Diagnostic Partition**: In post-unblinding analysis, releases where S&P Global and ISM had concordant vs. discordant surprises will be reported strictly as an informational diagnostic, not as a parameter optimization.

### 6.4 Other Co-Releases & Currency Collisions at 10:00 AM NY
Unlike Retail Sales (which bundled up to 21 indicators), ISM releases in a relatively focused window:
- **US Construction Spending m/m (`USD:US:840020002:r0`)**: Co-released at 10:00 AM NY in **92 of 96 releases (95.8%)**. Rated `medium` (importance 2). *(Note: event `840030005` is CPI m/m, which does not co-release at 10:00 AM)*.
- **Foreign-Currency Collisions at ISM Timestamps**:
  Across all 96 pre-2023 dates, exactly **3 dates** coincide with simultaneous foreign releases:
  1. `2016-05-02 17:00:00`: EUR ECB President Draghi Speech (`999010004`) — Inactive (2016 missing forecast).
  2. `2017-03-01 18:00:00`: CAD BoC Interest Rate Decision (`124040006`) & Statement (`124040007`) — Inactive (March 2017 missing forecast).
  3. `2022-06-01 17:00:00`: CAD BoC Interest Rate Decision (`124040006`) & Statement (`124040007`) — **Actionable** (belongs to the 66 actionable releases).
- **Collision Summary**: Only **1 of the 66 actionable releases (1.5%)** suffers a cross-currency collision. ISM offers a **98.5% clean USD isolation rate** on actionable trades.

---

## 7. Pre-Declared Primary Economic Rule & Trade Specifications

To prevent p-hacking and researcher degrees of freedom, the complete trade parameterization is declared prior to inspecting candle prices:

### 7.1 Actionable Universe
- **Target Instrument**: `EURUSD`
- **Candidate Series**: `USD:US:840040001:r0` (Headline ISM Manufacturing PMI)
- **Pre-2023 Sample Window**: `2015-01-01 00:00:00` to `2022-12-31 23:59:59`
- **Inclusion Criteria**:
  1. Complete Actual, Forecast, and Previous fields present.
  2. Non-zero headline surprise: $S_H \neq 0$.
- **Pre-2023 Actionable Sample**: Exactly **$N = 66$ packages**.

### 7.2 Directional Mapping
$$\text{Direction} = \begin{cases} \text{SHORT EURUSD} & \text{if } S_H > 0 \quad (\text{Hawkish USD shock}) \\ \text{LONG EURUSD} & \text{if } S_H < 0 \quad (\text{Dovish USD shock}) \end{cases}$$

### 7.3 Entry & Exit Specifications
- **Execution Bar**: Entry at the **Open of the H1 candle immediately following the announcement candle**:
  $$T_{\text{entry}} = T_{\text{release}} + 3600$$
  - Summer (17:00 release): Enter at `18:00:00` server open (60-minute absorption delay).
  - Winter (18:00 release): Enter at `19:00:00` server open (60-minute absorption delay).
- **Holding Horizon & Exit Definition**:
  - The trade enters at the Open of the H1 bar at $T_{\text{entry}}$.
  - The trade is held for $H$ consecutive active H1 trading bars (bars $0$ to $H-1$).
  - **Exit occurs at the Close of the final active H1 bar** (bar $H-1$).
  - *Active Bar Stepping*: When holding spans a Friday–Sunday weekend market closure, bar indexing steps over the closed period and resumes on Sunday/Monday open. Wall-clock holding time extends past $H \times 3600$, and the exit timestamp is **not** a universal $T_{\text{entry}} + H \times 3600$.
  - **Primary Horizon ($H = 24$)**: Close at the close of the 24th active H1 bar (1 full trading day).
  - **Descriptive Horizon ($H = 48$)**: Close at the close of the 48th active H1 bar (2 full trading days).

### 7.4 Transaction Friction Model (Identical to Retail Sales)
Performance must be evaluated across the identical 5 standardized friction scenarios:
- **Scenario A**: 0.0 pips (Gross frictionless baseline)
- **Scenario B**: 0.5 pips (5 broker points)
- **Scenario C (Primary Screening Hurdle)**: **1.0 pip (10 broker points)**
- **Scenario D**: 2.0 pips (20 broker points)
- **Scenario E**: 3.0 pips (30 broker points)

---

## 8. Explicitly Pre-Declared Rejection of Methodological Alternatives

To eliminate hindsight bias, we formally record why alternative design choices were considered and rejected before unblinding:

1. **Rejection of Multi-Component Concordance (Headline + Prices Paid)**:
   - *Rationale*: As demonstrated in Section 3.3, Prices Paid is an inflation survey, not a growth survey. Concordance is only 55.2%. Forcing agreement would drop 29 of 66 actionable releases, slashing power and misrepresenting economic reality during stagflationary regimes. Prices Paid is relegated to diagnostic attribution.
2. **Rejection of Multi-Component Concordance (Headline + Employment / New Orders)**:
   - *Rationale*: Employment and New Orders lack consensus forecasts prior to September 2017 in MetaQuotes data (32 missing forecasts). Restricting to 3-way concordance further erodes sample size to $N \approx 35$.
3. **Rejection of Delayed H4 Entry (20:00 Server Open)**:
   - *Rationale*: Creates seasonal distortion (180 min wait in summer vs 120 min in winter) and allows 2 to 3 hours of market absorption, defeating the purpose of measuring systematic post-announcement drift.
4. **Rejection of S&P Global PMI Pooling**:
   - *Rationale*: S&P Global uses different panel methodology and weights. Pooling distinct series violates the laboratory's non-pooling mandate.
5. **Rejection of S&P Global Directional Pre-Filtering**:
   - *Rationale*: Conditioning trade entry on S&P Global agreement would reduce sample size and introduce an unnecessary researcher degree of freedom before primary testing.

---

## 9. Current Status & Governance Boundaries

> [!CAUTION]
> **GOVERNANCE DIRECTIVE: NO RUNNER, NO UNBLINDING, NO TRADE SETUP**
> 1. This document completes the **audited price-blind feasibility screening** of US ISM Manufacturing PMI.
> 2. **NO PROTOCOL IS FROZEN**: A formal protocol and freeze packet must be drafted, reviewed, and approved before any calculation runner is constructed.
> 3. **NO PRICES INSPECTED**: Zero OHLC prices, spreads, or returns for EURUSD around ISM dates have been read or computed.
> 4. **HOLDOUT SEALED**: Historical outcomes in the post-2022 holdout partition (`timestamp >= 1672531200`) were not evaluated and remain strictly sealed. Full-file SHA-256 hashing and in-memory calendar-row scanning occurred for schema reconciliation.
> 5. **STOP & WAIT**: Work halts here for Codex audit and Project Director steering.
