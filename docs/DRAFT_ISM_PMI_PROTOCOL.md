# DRAFT RESEARCH PROTOCOL: US ISM MANUFACTURING PMI ON EURUSD

> [!CAUTION]
> **PROTOCOL STATUS: DRAFT PROPOSAL PENDING CODEX & OWNER REVIEW (DO NOT EXECUTE)**
> This document is a **draft pre-price research specification**.
> All trade mechanics, cost scenarios, statistical decision gates, directional mappings, and friction models are **PROPOSALS FOR REVIEW**, not approved or frozen facts.
> **Strict Halt**: No candidate candle prices, returns, winning trades, or directional paths may be read, parsed, or computed under this protocol until formally audited, reconciled, and frozen by Codex and authorized by the Project Director.
> Chronological Split Boundary: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).
> All post-2022 price observations and calendar surprises remain strictly sealed.

---

## 1. Candidate Research Question & Scope

### 1.1 Sole Primary Question: Strategy Viability
> *For the 66 pre-2023 actionable releases of US ISM Manufacturing PMI on EURUSD, is the sample mean 24-active-H1 directional Scenario C net pip return strictly positive at one-sided alpha 0.05 AFTER deducting exactly 1.0 assumed pip of execution friction?*

**Explicit Scope Limitation**:
- This is an empirical **directional-strategy screening test** under prespecified assumed friction.
- More precisely, Scenario C tests a **hypothetical one-pip-friction screening rule**, not verified all-in broker profitability: historical commission, slippage, financing, and point-in-time calendar availability remain unmeasured. Any passing result is a candidate for further validation, not evidence that a broker could have filled historical trades at those prices.
- It is **NOT** an estimate of the causal macroeconomic effect of US ISM Manufacturing PMI on exchange rates.
- It is **NOT** a measure of "excess return versus matched controls."
- Any observed post-announcement price movement reflects the joint market absorption of the headline PMI, co-released Construction Spending, unobserved order flow, liquidity conditions, and subsequent macroeconomic announcements.

### 1.2 Descriptive 48-Active-H1 Horizon (Secondary Diagnostic Only)
- The 48-active-H1 horizon (2 full trading days / 48 active hours) is evaluated strictly as an **exploratory and descriptive persistence diagnostic**.
- There is **no separate setup-registration claim**, no secondary hypothesis gate, and no family-wise error adjustment on 48-H1.
- Performance on 48-H1 will be reported descriptively alongside 24-H1 to observe whether return drift persists, reverses, or attenuates over a two-day holding period.
- **Strict Non-Optimization Rule**: If 24-H1 fails its primary hurdle, a positive return on 48-H1 cannot rescue the candidate or be post-hoc promoted into a primary rule.

### 1.3 Prior Trials & Researcher Degrees of Freedom Registration
In accordance with forensic research integrity standards, this protocol explicitly registers prior trial history:
1. **US Retail Sales Discovery Run**: Closed as **`DISCONFIRMED_ADVERSE`** at commit `2e2f3ff` (Scenario C mean return $-2.62857$ pips, win rate $25/49 = 51.02\%$, one-sided $p = 0.65132$).
2. **Phase 1 Trials**: Formal empirical trials on US CPI and NFP post-announcement drift.
3. **German Ifo Pilot Trial**: Evaluated German Ifo Business Climate on EURUSD ($N = 40$ actionable episodes; permutation $p = 0.9575$, concluding State 3: No Convincing Evidence).
4. **Multi-Candidate Screening**: The prior inventory screened 21 macroeconomic series across 51 currency pairs.
*Limitation on Nominal Significance*: Investigating US ISM Manufacturing PMI is step $K > 1$ in an ongoing sequential screening program. Prior family screening means that any nominal p-value reported from this protocol is not an unadjusted, program-wide false-positive guarantee.

---

## 2. Exact Series Identification & Data Provenance

### 2.1 Pinned Identifiers (Verified Facts)
- **Primary Headline Series**:
  - Key: `USD:US:840040001:r0`
  - Name: `ISM Manufacturing PMI` (`event_id = 840040001`, `revision = 0`, Institute for Supply Management)
  - Sector: `CALENDAR_SECTOR_BUSINESS` (`sector_code = 8`)
  - Unit: `CALENDAR_UNIT_NONE` (`unit_code = 0`)
  - Importance: `high` (`importance_code = 3`)
- **Tradable Instrument**: **`EURUSD`** (PERIOD_H1 trade-server time).

### 2.2 Directional Mapping (Predeclared Specification)
Because EURUSD is quoted as EUR (Base Currency) / USD (Quote Currency):
- **Hawkish US Shock (Strong Manufacturing Demand)**:
  - Headline POS ($S_H > 0$) $\implies$ **Short EURUSD** ($d_i = -1$).
- **Dovish US Shock (Weak Manufacturing Demand)**:
  - Headline NEG ($S_H < 0$) $\implies$ **Long EURUSD** ($d_i = +1$).
- **Neutral Shock (Exact Consensus Match)**:
  - Headline ZERO ($S_H = 0.0$) $\implies$ **Excluded / Not Actionable** ($d_i = 0$).

### 2.3 Cryptographic Source Provenance Hashes (Verified Facts)
- Raw Calendar: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv`
  `SHA-256: 76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e`
- Calendar Events Metadata: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_events.csv`
  `SHA-256: e08d2df96e83fdefa1c56d33316ee09178fe75aff1f3325d6f4ec4c80a4b7f13`
- Candle Symbols Metadata: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candle_symbols.csv`
  `SHA-256: 3b067061adbb6e941be26006f9451e853a91cd622479e78387b32102a43755b1`
- Candle Data: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv`
  `SHA-256: 893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5`

---

## 3. Coherence Rule & Sample Boundaries

### 3.1 Consensus Surprise Definition
Using raw unrounded scaled integers (`1e6` scale):
$$S_H = \text{Actual}_H - \text{Forecast}_H = A_H - F_H$$

### 3.2 Pre-2023 Sample Accounting (Verified Facts)
1. **Total Pre-2023 Headline Releases**: Exactly **96 releases** across the 8-year discovery period (`2015-01-01` to `2022-12-31`).
2. **Missing Consensus Forecasts (Excluded)**: Exactly **29 releases** (all 24 in 2015–2016, plus 5 in Jan–May 2017 before MetaQuotes began populating forecasts).
3. **Complete A/F/P Packages**: Exactly **67 releases** (June 2017 through December 2022).
4. **Surprise Breakdown Across All 67 Complete Releases**:
   - **Positive Surprises ($S_H > 0$, Short EURUSD)**: Exactly **28 packages** (41.8% of complete packages).
   - **Negative Surprises ($S_H < 0$, Long EURUSD)**: Exactly **38 packages** (56.7% of complete packages).
   - **Zero Surprise ($S_H = 0.0$)**: Exactly **1 package** (`2018-03-01 18:00:00`, timestamp `1519927200`, Actual = 60.8, Forecast = 60.8). Excluded due to lack of directional impulse.
5. **Actionable Primary Discovery Sample**: Exactly **$N = 66$ packages** ($28 + 38$).
   - 100% EURUSD H1 forward path completeness exists across all 66 actionable packages for both 24-H1 and 48-H1 horizons.

### 3.3 Explicit Pre-Declared Rejection of Multi-Component Filtering
Component series are formally **REJECTED as trade entry filters** and preserved strictly as post-unblinding attribution diagnostics:
1. **Prices Paid (`USD:US:840040002:r0`)**:
   - Measures input inflation, not output activity. In stagflation regimes, manufacturing activity falls while input costs rise ($S_H < 0 \land S_P > 0$).
   - Concordance is only 55.2% ($37 / 67$). Forcing concordance drops 29 of 66 actionable releases (43.9% sample loss).
2. **Employment (`USD:US:840040004:r0`) & New Orders (`USD:US:840040006:r0`)**:
   - Lack consensus forecasts prior to September 2017 in MetaQuotes data (32 missing forecasts across pre-2023 releases; Prices Paid has 29 missing).
   - Across the 63 pre-2023 releases where all component series have complete A/F/P packages and non-zero headline surprise ($S_H \neq 0$):
     - **Headline + Employment + New Orders**: Exactly **23 concordant packages** (12 all positive, 11 all negative) and **40 non-concordant packages** (**38 opposite-sign**, **2 neutral-component** where New Orders surprise was zero: `1536080400` and `1583172000`). Restricting entry to this combination collapses the sample from $N = 66$ to $N = 23$ (65.2% sample loss).
     - **Headline + Prices Paid + Employment**: Exactly **20 concordant packages** (9 all positive, 11 all negative) and **43 non-concordant packages** (all **43 opposite-sign**, 0 neutral-component).
     - **All Four Components**: Exactly **10 concordant packages** (6 all positive, 4 all negative) and **53 non-concordant packages** (**51 opposite-sign**, **2 neutral-component**). Restricting entry to all four components collapses the sample from $N = 66$ to $N = 10$ (84.8% sample loss).
   - Conditioning trade entry on multi-component concordance collapses available sample size to negligible levels ($N=10$ or $N=23$). Statistical power cannot be asserted without an assumed effect size and variance, but severe sample truncation severely undermines estimation precision. The primary test remains strictly on Headline PMI ($N = 66$).

---

## 4. Execution Timing, Pricing Arithmetic & Friction Model

### 4.1 Temporal Entry Rule: Uniform 60-Minute H1 Absorption Delay
Entry occurs at the **Open of the next active H1 candle** immediately following the announcement candle:
$$T_{\text{entry}} = T_{\text{release}} + 3600$$
Among the **66 actionable releases**:
- **Summer Schedule (EDT, UTC-4)**: Release at `17:00:00` server open $\implies$ Enter at **`18:00:00`** server open (60-minute delay; exactly **45 of 66 actionable packages**).
- **Winter Schedule (EST, UTC-5)**: Release at `18:00:00` server open $\implies$ Enter at **`19:00:00`** server open (60-minute delay; exactly **21 of 66 actionable packages**).

*(Note on complete inventory: Across all 67 complete A/F/P releases including the single zero-surprise package, 45 occurred at 17:00 and 22 at 18:00 server open).*

**Methodological Rationale & Execution Hypothesis**:
- Guarantees **100% seasonal symmetry**: identical 60-minute absorption delay year-round.
- Avoids the 120- vs 180-minute distortion introduced by H4 bar structures.
- **Execution Hypothesis**: The 60-minute entry delay is based on the execution hypothesis that release-time spread widening and initial order-book noise subside within the first hour while entering ahead of secondary session liquidity. This is an operational hypothesis, not an empirically observed fact in the exported dataset (which lacks sub-hourly tick spreads and order book depth).

### 4.2 Holding Horizon & Exit Pricing
- **Primary 24-Active-H1 Horizon**: Trade enters at the Open of the H1 candle at $T_{\text{entry}}$ (bar 0) and is held for exactly **24 consecutive active H1 bars** (bars $0, \dots, 23$).
- **Exit Definition**: **Exit occurs at the Close of the 24th active H1 bar** (bar 23).
- **Active Bar Stepping Across Weekend Closures**:
  - When holding spans a Friday 23:00 to Sunday 23:00 market closure, bar indexing steps over the closed period and resumes on Sunday/Monday open.
  - **24-H1 Horizon**: Exactly **11 of 66 actionable paths (16.7%)** cross a weekend boundary (all 11 are Friday releases).
  - **48-H1 Horizon**: Exactly **21 of 66 actionable paths (31.8%)** cross a weekend boundary (11 Friday releases + 10 Thursday releases).
  *(Note on complete inventory: Across all 67 complete packages, 11/67 cross weekends at 24-H1 and 22/67 cross weekends at 48-H1, because the single zero-surprise Thursday release crossed a weekend at 48-H1).*
  - Exit timestamp is computed dynamically from active candle bars, not by naive wall-clock multiplication ($T_{\text{entry}} + 24 \times 3600$).

### 4.3 Split-Boundary Exit Close Convention & Holdout Seal
- **Boundary Condition**: Under the laboratory's strict holdout seal, trade evaluations must not extend into or sample prices from the post-2022 holdout window (`timestamp >= 1672531200`).
- Because an H1 candle opening at timestamp $T_{\text{bar}}$ spans $[T_{\text{bar}}, T_{\text{bar}} + 3600)$, its close timestamp is $T_{\text{exit\_close}} = \text{bar}_{H-1} + 3600$.
- In an H1 candle series, all bar timestamps align to exact hour boundaries (`timestamp % 3600 == 0`), where `SPLIT_TIMESTAMP = 1672531200` represents `2023-01-01 00:00:00`.
- If an unrigorous engine only checked whether the trade *entry* opened before 2023 ($T_{\text{entry}} < 1672531200$), a trade entering on `2022-12-31 01:00:00` (`1672448400`, which is `SPLIT_TIMESTAMP - 23 * 3600`) would have its 24th active holding bar opening at `2023-01-01 00:00:00` (`1672531200`) and closing at `2023-01-01 01:00:00` (`1672534800`)—leaking directly into holdout data.
- Under the exit-close convention, the final active H1 bar must satisfy:
  $$T_{\text{exit\_close}} = \text{bar}_{H-1} + 3600 \le 1672531200$$
  which means on the H1 grid, the latest valid pre-2023 bar must open at or before `1672527600` (`2022-12-31 23:00:00`, closing at `1672531200`). Any bar opening at `1672531200` or later has its close strictly exceeding `1672531200` and is rejected.
- **Preflight Verification**: The latest pre-2023 release occurred on `2022-12-01 17:00:00` server open (`timestamp = 1669914000`). Its 24-H1 holding horizon exits at `2022-12-02 18:00:00` (bar close) and its 48-H1 holding horizon exits at `2022-12-05 18:00:00` (bar close, `timestamp = 1670263200`), over 26 days before `1672531200`. Exactly **66 of 66 actionable paths (100.0%)** strictly satisfy the exit-close split-boundary constraint.

### 4.4 Mathematically Singular Primary Outcome & Return Formulas

To eliminate any ambiguity between reconstructed bid/ask spreads and fixed cost scenarios, the primary outcome is defined **mathematically singularly in pips**:

1. **Gross Directional Pip Return**:
   For each eligible trade episode $i \in \{1, \dots, N\}$ (where $N = 66$):
   $$\text{Gross Pips}_i = d_i \times \frac{\text{Close}(T_{\text{exit\_bar}}) - \text{Open}(T_{\text{entry\_bar}})}{0.00010}$$
   where:
   - $d_i = -1$ if $S_H > 0$ (Short EURUSD, Hawkish USD shock)
   - $d_i = +1$ if $S_H < 0$ (Long EURUSD, Dovish USD shock)
   - $\text{Open}(T_{\text{entry\_bar}})$ is the Open price of the exported H1 bar at $T_{\text{entry}} = T_{\text{release}} + 3600$.
   - $\text{Close}(T_{\text{exit\_bar}})$ is the Close price of the 24th active exported H1 bar ($B_{23}$).
   - $0.00010$ is the standard EURUSD pip scale ($10 \times \text{Point}$, where $\text{Point} = 0.00001$ from `candle_symbols.csv`).

2. **Scenario C Net Pip Return (Primary Estimand)**:
   $$\text{Net Pips}_i(C) = \text{Gross Pips}_i - 1.0$$
   Scenario C deducts **exactly 1.0 assumed pip (10 broker points)** of friction.

3. **Standard 5 Assumed-Cost Sensitivity Scenarios**:
   Each cost scenario substitutes its respective fixed assumed friction cost $C_c$ **ONCE**, directly subtracting from gross directional pips:
   $$\text{Net Pips}_i(c) = \text{Gross Pips}_i - C_c$$

| Scenario ID | Assumed Friction ($C_c$) | Point Equivalent | Specific Analytical Coverage |
|---|---:|---:|---|
| **Scenario A** | 0.0 pips | 0 pts | Frictionless baseline: evaluates gross post-announcement directional drift. |
| **Scenario B** | 0.5 pips | 5 pts | Assumed minimal spread-only deduction: best-case institutional execution. |
| **Scenario C** | **1.0 pip** | **10 pts** | **Primary Screening Hurdle**: Assumed standard retail/ECN spread deduction (1.0 pip). |
| **Scenario D** | 2.0 pips | 20 pts | Assumed conservative spread deduction: wider post-announcement spread conditions. |
| **Scenario E** | 3.0 pips | 30 pts | **Hypothetical Combined-Cost Sensitivity Hurdle**: Combines moderate spread + commission + slippage buffer. NOT an empirically verified all-in fee. |

**Reporting Mandate**:
- Fixed cost is deducted **ONCE**, NOT on top of reconstructed bar spread.
- The primary sample mean ($\bar{P}_{\text{net}}$), sample standard deviation ($s$), standard error ($\text{SE}$), t-statistic ($t$), one-sided p-value ($p$), confidence interval, and win count ($N_{\text{win}}$ where $\text{Net Pips}_i(C) > 0$) must **ALL use Scenario C net PIPS consistently**.
- **Labeling Mandate**: This outcome is labeled strictly as an **assumed-cost, bar-based screening return**, NOT verified executable broker P&L.

### 4.5 OHLC & Spread Provenance
- **Exported Bar Prices**: Historical candle rows record exported bar prices, not independently verified Bid prices, because `SYMBOL_CHART_MODE` was not exported in the research manifest.
- **Spread Snapshot Uncertainty**: The `spread` column in `candles_EURUSD_H1.csv` records an integer snapshot of the broker point spread at the time the bar was recorded (`rates[b].spread`). Its timing relative to actual order fills is uncertain and cannot establish the exact tick-level spread or Ask price at trade entry or exit.
- **Assumed Friction Standard**: Any analysis utilizing the candle bar spread column is strictly descriptive and exploratory. The primary evaluation relies on fixed assumed friction (Scenario C: 1.0 pip), never an exact historical cost.

### 4.6 Real-World Execution Limitations & Omitted Costs
> [!WARNING]
> **ASSUMED-COST ARITHMETIC IS NOT FULLY EXECUTABLE BROKER PROFIT**:
> The pinned repository contains historical H1 candle data and calendar releases. It does **NOT** contain tick-level order book depth, historical execution fill logs, broker commission statements, or historical overnight swap schedules.
> A physical trade incurs three real-world friction components that are not captured in candle-based testing:
> 1. **Broker Commissions**: Incurred per trade on physical execution; commission schedules are account- and broker-dependent and not recorded in the pinned dataset.
> 2. **Execution Slippage**: Market orders at bar boundaries can experience adverse fill slippage during post-announcement volatility; tick-level order book depth and actual fill prices are not recorded in the pinned dataset.
> 3. **Overnight Financing / Swaps**: Holding across 00:00 server rollover incurs overnight carry or financing charges. Historical swap schedules, rates, and rollover conventions are account- and broker-specific, not exported in the dataset, and remain unmeasured. No assumption is made about specific swap ranges or triple rollover incidence.
>
> These unmeasured costs are **NOT** assumed to be zero. Scenario E provides an assumed sensitivity stress-test, but does not represent verified broker fees.

---

## 5. Statistical Framework & Primary Decision Rule

### 5.1 Estimand & Test Statistic (Consistently in Pips)
Let $P_{\text{net}, i}(C) = \text{Net Pips}_i(C)$ be the Scenario C net pip return of trade episode $i \in \{1, \dots, N\}$ (where $N = 66$).
- **Sample Estimand (Mean Scenario C Net Pips)**:
  $$\bar{P}_{\text{net}}(C) = \frac{1}{N} \sum_{i=1}^N P_{\text{net}, i}(C)$$
- **Sample Standard Deviation** ($s$, with $N - 1 = 65$ degrees of freedom):
  $$s(C) = \sqrt{\frac{1}{N - 1} \sum_{i=1}^N \left(P_{\text{net}, i}(C) - \bar{P}_{\text{net}}(C)\right)^2}$$
- **Standard Error of the Mean**:
  $$\text{SE}(C) = \frac{s(C)}{\sqrt{N}}$$

### 5.2 Hypothesis Formulation & Single Primary Test
- **Null Hypothesis ($H_0$)**: Expected Scenario C net pip return is non-positive:
  $$H_0: \mu_{\text{net}}(C) \le 0.0\text{ pips}$$
- **Alternative Hypothesis ($H_1$)**: Expected Scenario C net pip return is strictly positive:
  $$H_1: \mu_{\text{net}}(C) > 0.0\text{ pips}$$
- **Primary Statistical Test**: **1-Sample Student's t-Test** (1-sided test against zero):
  $$t(C) = \frac{\bar{P}_{\text{net}}(C)}{\text{SE}(C)}$$
  $$p(C) = 1 - F_{t_{N-1}}(t(C))$$
  where $F_{t_{N-1}}$ is the cumulative distribution function of the Student's t distribution with $N - 1 = 65$ degrees of freedom.

### 5.3 Primary Decision Hurdle
The candidate clears the prespecified primary discovery hurdle if and only if:
$$\bar{P}_{\text{net}}(C) > 0.0\text{ pips} \quad \text{AND} \quad p(C) < 0.05 \quad (t > t_{0.95, 65} \approx 1.6686)$$

**Status of a Passing Result & Temporal Sequence**:
- Protocol approval and freeze precede any discovery execution on candidate prices.
- A passing discovery result is **ONLY A CANDIDATE, NEVER A REGISTERED SETUP**.
- A passing pre-2023 discovery outcome earns **only separate holdout review**, not retroactive protocol freezing.
- Prior family screening means the nominal p-value is not a program-wide false-positive guarantee.

### 5.4 Diagnostic Reporting (Not Automatic Pass/Fail Gates)
To provide complete visibility without introducing arbitrary secondary hurdle dependencies, the following metrics are reported **strictly as descriptive diagnostics**:
1. **Win Count & Win Rate**:
   - $N_{\text{win}} = \sum_{i=1}^{66} \mathbb{I}(P_{\text{net}, i}(C) > 0.0)$
   - $W = \frac{N_{\text{win}}}{66}$
   - Reported descriptively to evaluate whether mean return is broadly distributed across episodes or concentrated in a few outliers.
2. **Subgroup Performance (Friday vs Non-Friday)**:
   - Friday releases ($N = 11$): all cross weekend market closures.
   - Non-Friday releases ($N = 55$): intra-week continuous trading.
   - Reported descriptively to observe weekend-gap sensitivity. Absent an a priori theoretical rationale for structural divergence, subgroup differences do not act as automatic pass/fail gates.
3. **Descriptive Robustness Diagnostics**:
   - Wilcoxon signed-rank test on net pips.
   - Sign permutation test.
   - Leave-one-out jackknife mean and t-statistic.

### 5.5 Fail-Closed Boundary Handling
To guarantee system stability, audit integrity, and prevent false discoveries:
- **Zero Variance ($s = 0$)**: If the sample standard deviation of Scenario C net pips is zero ($s(C) = 0.0$), the t-statistic and p-value are mathematically undefined. The evaluation must fail closed (raise an explicit exception or output an explicit fail-closed disposition). Under NO circumstances may a degenerate zero-variance series be classified as `PROMISING_DISCOVERY_CANDIDATE`.
- **Non-Finite Returns**: If any return calculation produces `NaN`, positive infinity ($+\infty$), or negative infinity ($-\infty$), execution must immediately fail closed.
- **Undefined Statistics**: If standard error is non-finite, degrees of freedom are degenerate ($N \le 1$), or p-value cannot be computed, the result must be flagged as fail-closed.
- **Sample Count Mismatch**: If the actionable pre-2023 sample size deviates from $N = 66$, execution must halt and fail closed unless explicitly authorized.

---

## 6. Predeclared Confounder Diagnostics (Descriptive Only)

### 6.1 S&P Global (Markit) 15-Minute Preceding Lead Diagnostic
- **Physical Reality**: S&P Global US Manufacturing PMI (`USD:US:840500001:r3`) releases at 9:45 AM NY—exactly 15 minutes (900 seconds) prior to ISM in **61 of 66 actionable releases (92.4%)** with populated consensus forecasts.
- **Diagnostic Partition**:
  - Concordant S&P Releases: Releases where S&P surprise sign matches ISM surprise sign.
  - Discordant S&P Releases: Releases where S&P surprise sign contradicts ISM surprise sign.
- **Strict Governance Rule**: This partition is evaluated **strictly as an informational attribution diagnostic**.
- **PROHIBITION AGAINST POST-HOC FILTER PROMOTION**: Researchers are strictly forbidden from promoting the "Concordant S&P" subgroup into an optimized strategy rule after observing prices. If the primary $N=66$ sample fails, the hypothesis is disconfirmed.

### 6.2 Construction Spending Co-Release Diagnostic
- US Construction Spending m/m (`USD:US:840020002:r0`) co-releases at 10:00 AM NY in **62 of 66 actionable releases (93.9%)**.
- *(Across all 67 complete A/F/P releases: 63/67 co-released; across all 96 pre-2023 releases: 92/96 co-released).*
- Attribution limitation: Any observed drift reflects the combined arrival of ISM and Construction Spending.

### 6.3 Cross-Currency Collision Diagnostic
- Across all 66 actionable dates, exactly **1 release** experiences a foreign central bank collision:
  - `2022-06-01 17:00:00`: CAD Bank of Canada Interest Rate Decision (`124040006`) and Rate Statement (`124040007`).
- The remaining **65 of 66 actionable releases (98.5%)** enjoy pure USD isolation.

### 6.4 Multi-Component Attribution Diagnostic
- Descriptive reporting of returns partitioned by component concordance:
  - Headline + Employment + New Orders ($N = 23$ concordant, $N = 38$ opposite, $N = 2$ neutral).
  - Headline + Prices Paid + Employment ($N = 20$ concordant, $N = 43$ opposite, $N = 0$ neutral).
  - All Four Components ($N = 10$ concordant, $N = 51$ opposite, $N = 2$ neutral).
- Labeled diagnostic only; non-promotable.

---

## 7. Mutually Exclusive Decision Truth Table & Failure Labels

All evaluations use **Scenario C (Assumed 1.0-pip friction)** on the primary 24-active-H1 horizon ($N = 66$). Every possible numerical outcome maps to **exactly one mutually exclusive case**:

| Case ID | Primary Statistical Conditions | Exact Decision Disposition | Scientific Verdict & Downstream Action |
|---|---|---|---|
| **Case 1** | $\bar{P}_{\text{gross}} \le 0.0\text{ pips}$ | **`DISCONFIRMED_ADVERSE`** | **Adverse Point Estimate**: Gross post-announcement drift is non-positive even before transaction friction. Primary hypothesis disconfirmed. Post-2022 holdout remains SEALED. Investigation concluded. |
| **Case 2** | $\bar{P}_{\text{gross}} > 0.0\text{ pips} \land \bar{P}_{\text{net}}(C) \le 0.0\text{ pips}$ | **`INCONCLUSIVE_FRICTION_DECAY`** | **Friction Decay**: Gross drift is positive, but net drift is eliminated after standard 1.0-pip friction. Candidate lacks commercial viability. Post-2022 holdout remains SEALED. Investigation concluded. |
| **Case 3** | $\bar{P}_{\text{net}}(C) > 0.0\text{ pips} \land p(C) \ge 0.10$ | **`INCONCLUSIVE_INSUFFICIENT_EVIDENCE`** | **Insufficient Evidence**: Positive point estimate, but indistinguishable from random noise ($p(C) \ge 0.10$); insufficient evidence to reject the null hypothesis. Post-2022 holdout remains SEALED. Investigation concluded. |
| **Case 4** | $\bar{P}_{\text{net}}(C) > 0.0\text{ pips} \land 0.05 \le p(C) < 0.10$ | **`INCONCLUSIVE_FRAGILE`** | **Marginally Significant**: Positive point estimate, but fails standard $p < 0.05$ threshold. Post-2022 holdout remains SEALED. |
| **Case 5** | $\bar{P}_{\text{net}}(C) > 0.0\text{ pips} \land p(C) < 0.05$ | **`PROMISING_DISCOVERY_CANDIDATE`** | **Promising Discovery Candidate**: Statistically significant positive Scenario C net pips. **NOT A REGISTERED SETUP.** Earns the right to post-2022 holdout review. |
| **Fail-Closed** | $s(C) = 0.0 \lor \text{non-finite stats} \lor N \neq 66$ | **`FAIL_CLOSED_INVALID`** | **Execution or Data Failure**: Degenerate variance, non-finite return, or malformed sample. Fails closed. Post-2022 holdout remains SEALED. |

---

## 8. Strict Conditions Required Before Any 2023+ Holdout Examination

> [!CAUTION]
> **ABSOLUTE GOVERNANCE BARRIER: THE POST-2022 HOLDOUT IS STRICTLY SEALED**
> Under no circumstances may any post-2022 candle price (`timestamp >= 1672531200`), spread, return, or holdout trade outcome be computed or inspected unless ALL of the following sequential conditions are fulfilled:

1. **Protocol Approval**:
   - This draft protocol must be formally audited, reviewed, and signed off by Codex and the Project Director.
2. **Runner Implementation & Synthetic Verification**:
   - A dedicated calculation runner must be implemented and tested strictly on synthetic bars before execution.
   - Codex audits the committed runner implementation and synthetic unit test suite.
3. **Committed Freeze Packet**:
   - A dedicated `ISM_PMI_FREEZE_PACKET.md` is committed to git, pinning the approved protocol, exact input hashes, runner commit SHA, and immutable decision rules.
4. **Pre-2023 Discovery Execution**:
   - Only after the freeze packet is committed may pre-2023 candidate prices be read.
   - The pre-2023 discovery run must be executed on the clean committed state.
5. **Discovery Hurdle Clearance & Review**:
   - The pre-2023 discovery outcome must achieve **`PROMISING_DISCOVERY_CANDIDATE`** (Case 5).
   - A passing discovery result earns **only separate holdout review**, not retroactive protocol freezing.
   - **Hard Stop on Disconfirmation**: If the discovery run produces `DISCONFIRMED_ADVERSE` (Case 1), `INCONCLUSIVE_FRICTION_DECAY` (Case 2), `INCONCLUSIVE_INSUFFICIENT_EVIDENCE` (Case 3), `INCONCLUSIVE_FRAGILE` (Case 4), or any fail-closed status, the investigation is **TERMINATED IMMEDIATELY**. The post-2022 holdout partition is **NEVER UNSEALED**.
6. **Separate Owner & Codex Authorization for Holdout Unsealing**:
   - Even if pre-2023 succeeds, holdout unsealing requires a separate, explicit pass of Codex audit and Project Director authorization.
7. **Holdout Sample Floor ($N_{\text{holdout}} \ge 15$)**:
   - The export manifest contains 45 post-2022 calendar rows for ISM Manufacturing PMI.
   - Eligible holdout packages ($N_{\text{holdout}}$) must be determined strictly by the identical inclusion criteria (complete A/F/P, $S_H \neq 0$).
   - The $N_{\text{holdout}} \ge 15$ threshold is a **prespecified minimum-count decision floor**, not proof of adequate power.
   - If $N_{\text{holdout}} < 15$, the sample fails the minimum-count decision floor and is classified as `HOLDOUT_SAMPLE_DEFICIENT` (descriptive only; no inference permitted).
8. **Holdout Decision Gates**:
   - If $N_{\text{holdout}} \ge 15$:
     - $\bar{P}_{\text{holdout, net}}(C) \le 0.0\text{ pips} \implies$ **`HOLDOUT_FAIL`** (Disconfirmed on holdout).
     - $\bar{P}_{\text{holdout, net}}(C) > 0.0\text{ pips} \land p_{\text{holdout}} \ge 0.05 \implies$ **`HOLDOUT_INCONCLUSIVE`**.
     - $\bar{P}_{\text{holdout, net}}(C) > 0.0\text{ pips} \land p_{\text{holdout}} < 0.05 \implies$ **`HOLDOUT_PASS_ELIGIBLE_FOR_DEMO`**.
   - A holdout pass does NOT prove profitability; it grants solely eligibility for forward demo-account forward validation.

---

## 9. Next Immediate Actions

1. Review and commit this draft protocol specification.
2. Implement pre-2023 calculation runner (`src/ism_runner.py`) and unit tests (`tests/test_ism_runner.py`) with injected synthetic candle fixtures.
3. Verify synthetic test suite and commit runner and tests without reading candidate OHLC data.
4. Prepare and commit freeze packet pinning protocol, input hashes, runner commit, and decision rules.
5. Await Project Director authorization before executing pre-2023 unblinded price run.
