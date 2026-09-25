# Next-Family Price-Blind Shortlist: US GDP vs. US ISM Manufacturing PMI

> [!IMPORTANT]
> **GOVERNANCE STATUS: PRICE-BLIND CANDIDATE SCREENING (NOT AN EXECUTABLE PROTOCOL)**  
> **No price data was parsed, no returns were calculated, and no trading setups are registered.**  
> This shortlist evaluates **DATA SUITABILITY ONLY**, not predicted profitability.  
> Candlestick files were accessed strictly to verify Unix timestamp continuity (`time` column 0). Zero Open, High, Low, Close, or Spread fields were inspected.  
> The US Retail Sales study remains completely unaffected and unaltered by this screening. No new runner or live/demo code has been generated.

---

## 1. Candidate Screening Purpose & Governance Constraints

Following the completion of the US Retail Sales pre-price runner, this screening establishes a price-blind candidate queue for future macro event families.

### Mandatory Methodological Guardrails:
1. **Zero Price Inspection**: Candidate evaluation relies strictly on pre-2023 economic calendar fields and EURUSD H1 candle timestamps.
2. **Strict Non-Pooling Mandate**: Advance, Second, and Third GDP revision stages must **NOT** be pooled merely to inflate sample size. S&P Global (Markit) and ISM PMI providers must **NOT** be pooled.
3. **Researcher History & Multiplicity Context**: Any candidate advancing from this queue enters as step $K \ge 3$ in an unbroken institutional research history following:
   - **Phase 1 Historical Exploration**: Narrow exploratory tests on USD CPI and NFP post-announcement drift (`evidence/trials/phase1/PHASE1_EXPLORATION.md`).
   - **German Ifo Pilot Trial**: Directional EURUSD pilot ($N = 40$) resulting in **State 3: No Convincing Evidence** ($p = 0.9575$, $\Delta \bar{R} = -21.31\text{ bps}$; `evidence/trials/ifo/ifo_pre2023_exploration_report.md`).
   - **US Retail Sales Pilot**: Current frozen protocol pending Codex review ($N = 49$).
   *Consequence*: Nominal p-values for any future candidate must reflect multi-candidate screening history.

---

## 2. Forensic Candidate Audit: US GDP Releases (`840010007`)

### 2.1 Pinned Metadata & Release Stage Architecture
- **MT5 Event ID**: `840010007` (`event_name = "GDP q/q"`)
- **Series Sector / Frequency**: `CALENDAR_SECTOR_GDP` / `CALENDAR_FREQUENCY_QUARTER`
- **Official Source**: U.S. Bureau of Economic Analysis (BEA)
- **Unit / Digits**: `CALENDAR_UNIT_PERCENT` / 1 decimal place
- **MT5 Release Stage Structure**:
  The BEA reports quarterly GDP across three sequential monthly releases. In MT5, these are indexed under `revision`:
  - **Revision 1 (Advance Estimate)**: First public estimate of GDP for the prior quarter, released ~30 days after quarter close (late Jan, Apr, Jul, Oct).
  - **Revision 2 (Second Estimate)**: Incorporates revised source data, released ~60 days after quarter close (late Feb, May, Aug, Nov).
  - **Revision 3 (Third / Final Estimate)**: Further refined estimate, released ~90 days after quarter close (late Mar, Jun, Sep, Dec).

### 2.2 Independent Episode Counts & A/F/P Completeness (Pre-2023)
Between `2015-01-01` and `2022-12-31` (`timestamp < 1672531200`), there are 95 total GDP release rows:

| Stage / Revision | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | Total Pre-2023 | Complete A/F/P | Completeness % |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Advance (Rev 1)** | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **32** | **22** | 68.8% |
| **Second (Rev 2)** | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 | **31** | **22** | 71.0% |
| **Third (Rev 3)** | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **32** | **23** | 71.9% |
| *Pooled (Prohibited)* | *12* | *12* | *12* | *12* | *11* | *12* | *12* | *12* | *95* | *67* | *70.5%* |

*Derivation & Observations*:
1. **Forecast Omission**: MetaQuotes did not record consensus forecasts for GDP releases in 2015 and 2016 (0/24 populated). Forecasts began populating mid-2017.
2. **2019 Q4 2018 BEA Shutdown Anomaly**: In 2019, Revision 2 contains only 3 releases instead of 4. Due to the 35-day U.S. Federal Government shutdown (Dec 22, 2018 – Jan 25, 2019), the BEA delayed the Q4 2018 Advance release into late February 2019, skipped the Second estimate entirely, and proceeded directly to the Third estimate in March.
3. **Severe Sample Deficiency (Under Non-Pooling)**: For the economically primary Advance estimate (Rev 1), exactly **$N = 22$ complete packages** exist in the entire 8-year pre-2023 record.

### 2.3 Simultaneous Co-Releases & Cross-Currency Collisions (Advance Estimate)
- **Mean Bundled Same-Second Releases**: **9.9 events** (range: 5 to 22).
- **Clean USD-Only Releases**: **18 / 32 (56.2%)**.
- **Cross-Currency Collisions**: **14 / 32 (43.8%)** — Collides with Canadian (CAD) data in 12 releases, Eurozone (EUR) data in 2 releases.
- **Constant Same-Second US Bundling**:
  - `GDP Price Index q/q` (`840010008`): 32/32 (100.0%)
  - `Core PCE Price Index q/q` (`840010009`): 32/32 (100.0%)
  - `PCE Price Index q/q` (`840010010`): 32/32 (100.0%)
  - `Real PCE q/q` (`840010016`): 32/32 (100.0%)
  - `Initial Jobless Claims` (`840140001`): 15/32 (46.9%) — Whenever GDP falls on a Thursday.

### 2.4 EURUSD Candle Timestamp-Path Coverage (Advance Estimate, $N=22$ Complete A/F/P)
- **6-H4 Horizon (24 active hours)**: **22 / 22 (100.0%) complete**. (8 packages cross the weekend).
- **12-H4 Horizon (48 active hours)**: **19 / 22 (86.4%) complete**. (3 incomplete; 19 packages cross the weekend).
- *Quirk*: The 3 incomplete 12-H4 episodes occurred on late October releases (2020-10-29, 2021-10-28, 2022-10-27). Q3 Advance GDP consistently coincides with the European Daylight Saving Time changeover weekend, introducing weekend boundary gaps that disrupt 48-hour path continuity.

---

## 3. Forensic Candidate Audit: US ISM Manufacturing PMI (`840040001`)

### 3.1 Pinned Metadata & Architecture
- **MT5 Event ID**: `840040001` (`event_name = "ISM Manufacturing PMI"`)
- **Series Sector / Frequency**: `CALENDAR_SECTOR_BUSINESS` / `CALENDAR_FREQUENCY_MONTH`
- **Official Source**: Institute for Supply Management (ISM)
- **Unit / Digits**: `CALENDAR_UNIT_NONE` (diffusion index centered at 50) / 1 decimal place
- **MT5 Release Stage Structure**: Single revision (`revision = 0`). No preliminary/final stages; ISM releases a single monthly report on the first business day of each month.

### 3.2 Independent Episode Counts & A/F/P Completeness (Pre-2023)
Between `2015-01-01` and `2022-12-31`, exactly 96 monthly releases exist (12 per year):

| Year | Total Releases | Actual Populated | Forecast Populated | Previous Populated | Complete A/F/P Packages |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **2015** | 12 | 12 | 0 | 12 | **0** |
| **2016** | 12 | 12 | 0 | 12 | **0** |
| **2017** | 12 | 12 | 7 | 12 | **7** |
| **2018** | 12 | 12 | 12 | 12 | **12** |
| **2019** | 12 | 12 | 12 | 12 | **12** |
| **2020** | 12 | 12 | 12 | 12 | **12** |
| **2021** | 12 | 12 | 12 | 12 | **12** |
| **2022** | 12 | 12 | 12 | 12 | **12** |
| **Total** | **96** | **96** | **67** | **96** | **67** |

*Derivation & Observations*:
1. **Forecast Availability**: Forecasts are missing throughout 2015–2016 and Jan–May 2017. They are 100% complete from June 2017 through December 2022.
2. **Actionable Sample Size**: Exactly **$N = 67$ complete A/F/P packages** exist pre-2023 without pooling disparate providers or revision stages.

### 3.3 Simultaneous Co-Releases & Cross-Currency Collisions
- **Mean Bundled Same-Second Releases**: **5.4 events** (range: 4 to 12).
- **Clean USD-Only Releases**: **93 / 96 (96.9%)**.
- **Cross-Currency Collisions**: ONLY **3 / 96 (3.1%)** (2 CAD, 1 EUR).
  - *Comparison*: Far superior currency isolation compared to US Retail Sales (which suffered 61.2% collisions) and US GDP (43.8% collisions).
- **Same-Second Co-Releases (Internal ISM Sub-Indices)**:
  - `ISM Manufacturing Prices Paid` (`840040002`): 96/96 (100.0%)
  - `ISM Manufacturing Employment` (`840040004`): 96/96 (100.0%)
  - `ISM Manufacturing New Orders` (`840040006`): 96/96 (100.0%)
  - `Construction Spending m/m` (`840020002`): 92/96 (95.8%)

### 3.4 EURUSD Candle Timestamp-Path Coverage ($N=67$ Complete A/F/P)
- **6-H4 Horizon (24 active hours)**: **66 / 67 (98.5%) complete**. (10 packages cross the weekend).
- **12-H4 Horizon (48 active hours)**: **66 / 67 (98.5%) complete**. (21 packages cross the weekend).
- *Single Path Failure*: TS 1572627600 (Friday 2019-11-01 17:00 UTC). Europe shifted out of DST on Oct 27, while the US did not shift until Nov 3; the broker trade-server closed at 22:00 UTC, leaving the 20:00 H4 block with only 3 constituent H1 bars before weekend shutdown.

### 3.5 Critical Family Quirks
1. **15-Minute Preemption by S&P Global (Markit) PMI**:
   - On 91 of 96 release dates, `S&P Global Manufacturing PMI` (`840500001`, revision 3) was released **exactly 15 minutes earlier** (at 9:45 AM ET / 17:45 or 16:45 server time).
   - *Epistemological Risk*: Because S&P Global reports on the identical underlying economic sector 15 minutes ahead of ISM, initial market repricing often occurs on the S&P release, partially absorbing the shock before ISM prints. A protocol cannot assume ISM enters an untouched market.
2. **Multi-Component Internal Conflict**:
   - Headline PMI can diverge from Prices Paid (inflation) or New Orders (forward demand). E.g., a strong headline PMI accompanied by an unexpected spike in Prices Paid creates conflicting policy and growth signals.

---

## 4. Head-to-Head Data Suitability Comparison

| Metric / Evaluation Dimension | US GDP Releases (`840010007`) | US ISM Manufacturing PMI (`840040001`) |
|---|---|---|
| **Primary MT5 Series ID** | `USD:US:840010007:r1` (Advance) | `USD:US:840040001:r0` |
| **Reporting Frequency** | Quarterly (4/year) | Monthly (12/year) |
| **Total Pre-2023 Releases** | 32 (Advance) / 95 (All Stages) | 96 |
| **Complete A/F/P Sample ($N$)** | **$N = 22$** (Advance, Unpooled) | **$N = 67$** (Unpooled) |
| **Statistical Viability Power** | **Severely Deficient** ($N = 22$ fails robust discovery) | **Adequate** ($N = 67$ provides solid power) |
| **Clean USD Currency Isolation** | 56.2% Clean (43.8% CAD/EUR collisions) | **96.9% Clean** (3.1% CAD/EUR collisions) |
| **Confounding Co-Releases** | Pervasive: Core PCE (100%), Jobless Claims (46.9%) | Moderate: Construction Spending (95.8%), ISM Sub-indices |
| **6-H4 Candle Path Coverage** | 100.0% (22/22 complete) | 98.5% (66/67 complete) |
| **12-H4 Candle Path Coverage** | 86.4% (19/22; late-Oct DST gaps) | 98.5% (66/67 complete) |
| **External Preemption Quirk** | None | **S&P Global PMI prints 15m earlier** |
| **Post-2022 Holdout Size** | $N_{\text{holdout}} = 14$ (Advance) $\implies$ Likely sample-deficient | $N_{\text{holdout}} = 45 \implies$ Substantial holdout |

---

## 5. Formal Data Suitability Ranking & Recommendation

### Rank 1: US ISM Manufacturing PMI (`USD:US:840040001:r0`)
- **Suitability Classification**: **CONDITIONALLY SUITABLE FOR FUTURE PROTOCOL DESIGN**
- **Justification**:
  - Sample size ($N = 67$ complete pre-2023 packages) is well above the empirical discovery threshold ($N \ge 30–50$) needed to distinguish systematic drift from variance.
  - Near-zero cross-currency contamination (96.9% clean USD releases).
  - Excellent candle path completeness (98.5%).
  - Post-2022 holdout ($N = 45$) exceeds the $N \ge 15$ sample-adequacy requirement.
- **Mandatory Preconditions Before Protocol Formulation**:
  1. Audit whether the 15-minute preceding S&P Global PMI release dampens or alters EURUSD volatility.
  2. Define an explicit coherence rule across ISM sub-components (Headline vs Prices Paid).
  3. Predeclare entry timing (10:00 AM ET is 16:00 or 17:00 broker time, landing on H1/H4 boundaries).

### Rank 2: US GDP Releases (`USD:US:840010007`)
- **Suitability Classification**: **UNSUITABLE FOR STANDALONE STRATEGY VIABILITY PILOT**
- **Justification**:
  - **Fatal Sample Deficiency**: Under the non-pooling constraint, Advance GDP offers only $N = 22$ complete packages in 8 years. A sample of 22 has negligible statistical power to survive a 1.0-pip friction hurdle without extreme outlier distortion.
  - Even if all stages were improperly pooled ($N = 67$), combining Advance, Second, and Third estimates mixes preliminary first-look shocks with minor accounting revisions that do not elicit comparable market mechanisms.
  - Heavy cross-currency collision rate (43.8% CAD/EUR contamination) and chronic bundling with Initial Jobless Claims and Core PCE prevent clean attribution.
  - The post-2022 holdout ($N_{\text{holdout}} = 14$ for Advance) already falls below the prespecified $N \ge 15$ adequacy threshold.
- **Action**: **PARK US GDP**. Do not build a research runner or draft a trading protocol for US GDP at this time.

---

## 6. Audit & Status Boundary

- [x] Pre-2023 calendar releases analyzed with zero OHLC candle price reads
- [x] Exact MT5 series IDs and release stages identified
- [x] Independent episode counts derived by year
- [x] Simultaneous co-releases and cross-currency collisions audited
- [x] EURUSD H1 timestamp coverage resolved for 24h and 48h horizons
- [x] S&P Global lead-in and BEA revision quirks documented
- [x] Prior research history (CPI/NFP Phase 1, Ifo pilot failure, Retail Sales) explicitly registered
- [ ] Codex Quant Director audit & formal review

> [!IMPORTANT]
> **STOP**: Candidate screening is complete. No executable code has been modified or created. Awaiting Codex audit.
