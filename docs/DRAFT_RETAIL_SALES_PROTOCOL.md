# US Retail Sales EURUSD Research Protocol (Draft Proposal v0.5 - Freeze-Ready Pre-Price Design)

> [!CAUTION]
> **PROTOCOL STATUS: UNFROZEN PROPOSAL REQUIRING CODEX REVIEW & APPROVAL (DO NOT EXECUTE)**  
> This document is a **draft pre-price research specification**.  
> All trade mechanics, cost scenarios, statistical decision gates, directional mappings, and friction models are **PROPOSALS FOR REVIEW**, not approved or frozen facts.  
> **Strict Halt**: No candidate candle prices, returns, winning trades, or directional paths may be read, parsed, or computed under this protocol until formally audited, reconciled, and frozen by Codex.  
> Chronological Split Boundary: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).  
> All post-2022 price observations and calendar surprises remain strictly sealed.

---

## 1. Candidate Research Question & Hypothesis

### 1.1 Sole Primary Question: Strategy Viability
> *For the 49 pre-2023 strict-concordance US Retail Sales packages on EURUSD, is the sample mean 6-H4 directional trade return strictly positive AFTER deducting a prespecified execution cost assumption?*

**Explicit Scope Limitation**:
- This is strictly an empirical test of **directional trading strategy viability** under executable friction.
- It is **NOT** an estimate of the causal macroeconomic effect of US Retail Sales on exchange rates.
- It is **NOT** a measure of "excess return versus matched controls."
- Any observed post-announcement price movement reflects the joint market absorption of the co-released Retail Sales package, bundled same-second indicators, cross-currency collisions, liquidity conditions, and subsequent macroeconomic announcements.

### 1.2 Exploratory 12-H4 Horizon (Descriptive Only)
- The 12-H4 horizon (48 active trading hours) is evaluated strictly as an **exploratory and descriptive persistence diagnostic**.
- There is **no separate setup-registration claim**, no secondary hypothesis gate, and no family-wise error adjustment on 12-H4.
- Performance on 12-H4 will be reported descriptively alongside 6-H4 to observe whether return drift persists, reverses, or attenuates over a two-day holding period.

### 1.3 Prior Trials & Researcher Degrees of Freedom Registration
In accordance with forensic research integrity standards, this protocol explicitly registers prior trial history:
1. **Phase 1 Trials**: Formal empirical trials on US CPI and NFP post-announcement drift.
2. **German Ifo Pilot Trial**: Evaluated German Ifo Business Climate + Expectations on EURUSD ($N = 40$ actionable episodes). Permutation test yielded $p = 0.9575$, concluding **State 3: No Convincing Evidence** (`evidence/trials/ifo/FMS_PILOT_IFO_PROTOCOL.md`).
3. **Multi-Candidate Screening**: The prior inventory (`evidence/inventory/fms_episodes.jsonl`) screened 21 macroeconomic series across 51 currency pairs.
*Limitation on Nominal Significance*: Investigating US Retail Sales is step $K > 1$ in an ongoing research program. Any nominal p-value reported from this protocol is conditioned on prior candidate screening and must not be interpreted as an unadjusted, discovery-wide false-positive guarantee.

---

## 2. Exact Series Identification & Data Provenance

### 2.1 Pinned Identifiers (Verified Facts)
- **Primary Headline Series**:
  - Key: `USD:US:840020010:r0`
  - Name: `Retail Sales m/m` (`event_id = 840020010`, `revision = 0`, Census Bureau)
- **Co-Released Core Series**:
  - Key: `USD:US:840020011:r0`
  - Name: `Core Retail Sales m/m` (`event_id = 840020011`, `revision = 0`, Census Bureau)
- **Tradable Instrument**: **`EURUSD`** (PERIOD_H1 trade-server time).

### 2.2 Directional Mapping (Predeclared Specification)
Because EURUSD is quoted as EUR (Base Currency) / USD (Quote Currency):
- **Hawkish US Shock (Strong Consumer Demand)**:
  - Headline POS ($S_H > 0$) & Core POS ($S_C > 0$) $\implies$ **Short EURUSD** ($d_i = -1$).
- **Dovish US Shock (Weak Consumer Demand)**:
  - Headline NEG ($S_H < 0$) & Core NEG ($S_C < 0$) $\implies$ **Long EURUSD** ($d_i = +1$).

### 2.3 Cryptographic Source Provenance Hashes (Verified Facts)
- Raw Calendar: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv`  
  `SHA-256: 76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e`
- Candle Data: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv`  
  `SHA-256: 893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5`
- Prior Episode Ledger: `evidence/inventory/fms_episodes.jsonl`  
  `SHA-256: 37df7880a2bc36dbbce06b4a6ba39f7bd962a4c1c92eb2ce64cb71a886de55d2`

---

## 3. Co-Release Coherence Rule & Sample Boundaries

### 3.1 Surprise Definition
Using raw scaled integers (`1e6` scale):
$$S_H = 	ext{Actual}_H - 	ext{Forecast}_H$$
$$S_C = 	ext{Actual}_C - 	ext{Forecast}_C$$

### 3.2 Predeclared Sample: Strict Concordance ($N = 49$)
The primary candidate sample is strictly restricted to packages exhibiting unequivocal sign agreement:
$$	ext{sign}(S_H) 	imes 	ext{sign}(S_C) > 0$$
- **Positive Consensus Surprise (Short EURUSD, $d = -1$)**: Exactly **27 packages**.
- **Negative Consensus Surprise (Long EURUSD, $d = +1$)**: Exactly **22 packages**.
- **Total Actionable Sample**: Exactly **$N = 49$ packages** (100% forward path completeness on EURUSD for both 6 H4 and 12 H4).

### 3.3 Excluded Categories (Pre-2023 Baseline)
1. **Active Sign Conflict ($	ext{sign}(S_H) 	imes 	ext{sign}(S_C) < 0$)**: Exactly **9 packages** (5 POS/NEG, 4 NEG/POS). Excluded due to contradictory economic transmission signals.
2. **Missing Consensus Forecast**: Exactly **28 packages** (all 24 packages in 2015–2016, plus 4 in Jan–Apr 2017 before MetaQuotes populated forecasts).
3. **Double Zero Surprise ($S_H = 0 \land S_C = 0$)**: Exactly **2 packages**.
4. **Single Zero Surprise ($S_H = 0 \lor S_C = 0$)**: Exactly **8 packages**.

---

## 4. Execution Timing, Bid–Ask Arithmetic & Assumed Cost Sensitivity Scenarios

### 4.1 Temporal Entry Rule
Entry occurs at the **Open of the next active H4 bar** immediately following completion of the announcement bar window:
- `15:30:00` release: Announcement H4 window (`12:00:00`–`16:00:00`) completes at `16:00:00`.
  - Entry occurs at the **Open of the 16:00:00 H4 bar** ($T_{	ext{entry}} = \mathbf{16:00:00}$, **30-minute delay**; 35 of 49 strict packages).
- `16:30:00` release: Announcement H4 window (`16:00:00`–`20:00:00`) completes at `20:00:00`.
  - Entry occurs at the **Open of the 20:00:00 H4 bar** ($T_{	ext{entry}} = \mathbf{20:00:00}$, **210-minute / 3.5-hour delay**; 14 of 49 strict packages).

### 4.2 Holding Horizon & Exit Pricing
- **Primary 6-H4 Horizon**: 6 completed active H4 blocks ($B_0, \dots, B_5$, 24 active hours).
- **Exit Timestamp**: $T_{	ext{exit}} = T_{	ext{entry}} + 6 	imes 14400	ext{ seconds}$ (in continuous trading) or stepped across the weekend closure.
- **Exit Bar**: Close of H4 block $B_5$ (which corresponds to the Close of the 6th active H4 bar).

### 4.3 Provenance Verification of Broker Points, Pips, and Spread
From `candle_symbols.csv` and `FyodorResearchExporterV3.mq5`:
- **Symbol Digits**: `symbol_digits = 5` (5 decimal places, e.g., 1.10000).
- **Broker Point Size**: `point = 0.00001` ($10^{-5}$).
- **EURUSD Standard Pip**: 1 pip = `0.00010` = **10 broker points**.
- **Spread Column Meaning**: In `candles_EURUSD_H1.csv`, the `spread` field contains the integer count of broker points recorded by MT5 for that bar (`IntegerToString(rates[b].spread)`).

### 4.4 Bid–Ask Trade Execution Arithmetic
The historical candle file records Bid prices (`open`, `high`, `low`, `close`). Physical execution incurs the Bid–Ask spread at both entry and exit:

1. **Long EURUSD Trade ($d_i = +1$, Dovish Shock)**:
   - **Entry**: Executes at the **Ask** price:
     $$P_{	ext{entry, Ask}} = 	ext{Open}_{	ext{Bid}}(T_{	ext{entry}}) + (	ext{Spread}_{	ext{entry}} 	imes 	ext{Point})$$
   - **Exit**: Executes at the **Bid** price:
     $$P_{	ext{exit, Bid}} = 	ext{Close}_{	ext{Bid}}(T_{	ext{exit}})$$
   - **Directional Net Log Return**:
     $$R_{	ext{net, Long}} = \ln\left(rac{P_{	ext{exit, Bid}}}{P_{	ext{entry, Ask}}}ight) = \ln\left(rac{	ext{Close}_{	ext{Bid}}}{	ext{Open}_{	ext{Bid}} + (	ext{Spread}_{	ext{entry}} 	imes 	ext{Point})}ight)$$
   - **Directional Net Pip Return**:
     $$	ext{Net Pips}_{	ext{Long}} = rac{	ext{Close}_{	ext{Bid}} - (	ext{Open}_{	ext{Bid}} + 	ext{Spread}_{	ext{entry}} 	imes 	ext{Point})}{10 	imes 	ext{Point}}$$

2. **Short EURUSD Trade ($d_i = -1$, Hawkish Shock)**:
   - **Entry**: Executes at the **Bid** price:
     $$P_{	ext{entry, Bid}} = 	ext{Open}_{	ext{Bid}}(T_{	ext{entry}})$$
   - **Exit**: Executes at the **Ask** price:
     $$P_{	ext{exit, Ask}} = 	ext{Close}_{	ext{Bid}}(T_{	ext{exit}}) + (	ext{Spread}_{	ext{exit}} 	imes 	ext{Point})$$
   - **Directional Net Log Return**:
     $$R_{	ext{net, Short}} = \ln\left(rac{P_{	ext{entry, Bid}}}{P_{	ext{exit, Ask}}}ight) = \ln\left(rac{	ext{Open}_{	ext{Bid}}}{	ext{Close}_{	ext{Bid}} + (	ext{Spread}_{	ext{exit}} 	imes 	ext{Point})}ight)$$
   - **Directional Net Pip Return**:
     $$	ext{Net Pips}_{	ext{Short}} = rac{	ext{Open}_{	ext{Bid}} - (	ext{Close}_{	ext{Bid}} + 	ext{Spread}_{	ext{exit}} 	imes 	ext{Point})}{10 	imes 	ext{Point}}$$

### 4.5 Execution Friction Limitations & Omitted Costs
> [!WARNING]
> **SPREAD-ONLY ARITHMETIC IS NOT FULLY EXECUTABLE NET PROFIT**:
> The pinned repository contains historical H1 candle data and calendar releases. It does **NOT** contain tick-level order book depth, historical commission ledgers, or historical overnight swap tables.
> A physical trade incurs three additional real-world friction components that are not captured by candle spread alone:
> 1. **Broker Commissions**: Institutional and retail ECN accounts typically charge $3–$7 per round-turn standard lot (equivalent to approximately 0.3 to 0.7 pips, or 3 to 7 broker points).
> 2. **Execution Slippage**: Submitting market or aggressive limit orders at bar boundaries (16:00:00 / 20:00:00) during post-macro volatility frequently experiences adverse fill slippage (1 to 5 broker points).
> 3. **Direction- and Day-Dependent Overnight Swaps**:
>    - Holding for 24 active hours (6 H4) spans the broker's 00:00 trade-server rollover, incurring overnight financing (swap).
>    - All **15 Friday releases** cross the Friday 23:00 to Sunday 23:00 market closure, incurring weekend rollover financing (or Wednesday triple swap depending on broker schedule).
>    - Swaps depend strictly on position direction (Long EUR vs Short EUR) and prevailing central bank policy rate differentials (Fed Funds vs ECB deposit rate).
>
> **Protocol Policy**: The protocol does **NOT** assume these unmeasured costs are zero. Instead, the protocol predeclares an explicit all-in cost sensitivity scenario (Scenario E) to stress-test whether drift survives when spread is compounded by commission, slippage, and overnight carry drag.

### 4.6 Assumed Spread-Friction Sensitivity Scenarios
The protocol establishes **five frozen, assumed sensitivity scenarios** (0, 5, 10, 20, and 30 broker points). These are predeclared sensitivity hurdles, **NOT empirically established broker tiers**:

| Scenario ID | Points Hurdle | Pips Hurdle | Price Cost ($\Delta P$) | Specific Analytical Coverage |
|---|---:|---:|---:|---|
| **Scenario A** | 0 pts | 0.0 pips | 0.00000 | Frictionless theoretical baseline: evaluates gross post-announcement directional drift. |
| **Scenario B** | 5 pts | 0.5 pips | 0.00005 | Assumed minimal spread-only deduction: best-case frictionless environment. |
| **Scenario C** | 10 pts | 1.0 pip | 0.00010 | **Primary Screening Hurdle**: Assumed moderate spread deduction (1.0 pip). Strategy must clear this hurdle to be considered viable. |
| **Scenario D** | 20 pts | 2.0 pips | 0.00020 | Assumed conservative spread deduction: wider post-announcement spread conditions. |
| **Scenario E** | 30 pts | 3.0 pips | 0.00030 | **All-In Conservative Sensitivity Hurdle**: Combines moderate spread (10–15 pts) + commission buffer (5 pts) + slippage & swap carry buffer (10 pts). |

**Reporting Mandate**: All experimental outputs must report mean returns, pips, t-statistics, and win rates across **all five scenarios simultaneously**. Viability requires strictly positive net return under **Scenario C (10 points / 1.0 pip)**, with Scenarios D and E providing explicit sensitivity boundaries.

---

## 5. Statistical Framework & Primary Hypothesis Test

### 5.1 Primary Test Statistic & Estimand
Let $R_{	ext{net}, i}(c)$ be the directional net log return of trade episode $i \in \{1, \dots, N\}$ under cost scenario $c$.
- **Sample Estimand**: The sample mean net directional return:
  $$ar{R}_{	ext{net}}(c) = rac{1}{N} \sum_{i=1}^N R_{	ext{net}, i}(c)$$
- **Sample Standard Deviation** ($s$, with $N - 1$ degrees of freedom):
  $$s(c) = \sqrt{rac{1}{N - 1} \sum_{i=1}^N \left(R_{	ext{net}, i}(c) - ar{R}_{	ext{net}}(c)ight)^2}$$
- **Standard Error of the Mean**:
  $$	ext{SE}(c) = rac{s(c)}{\sqrt{N}}$$

### 5.2 Hypothesis Formulation & Test Method
- **Null Hypothesis ($H_0$)**: Expected net directional return is non-positive:
  $$H_0: \mu_{	ext{net}}(c) \le 0$$
- **Alternative Hypothesis ($H_1$)**: Expected net directional return is strictly positive:
  $$H_1: \mu_{	ext{net}}(c) > 0$$
- **Primary Statistical Test**: **1-Sample Student's t-Test** (1-sided test against zero):
  $$t(c) = rac{ar{R}_{	ext{net}}(c)}{	ext{SE}(c)}$$
  $$p(c) = 1 - F_{t_{N-1}}(t(c))$$
  where $F_{t_{N-1}}$ is the cumulative distribution function of the Student's t distribution with $N - 1 = 48$ degrees of freedom.

### 5.3 Mathematical Reconciliation: One-Sided Test vs Two-Sided Confidence Interval
> [!NOTE]
> **CONFIDENCE BOUND RECONCILIATION**:
> The primary decision hurdle is a **one-sided test at $lpha = 0.05$** ($t > t_{0.95, 48} pprox 1.6772$).
> The matching one-sided 95% lower confidence bound is:
> $$	ext{LB}_{95\%} = ar{R}_{	ext{net}}(c) - 1.6772 \cdot 	ext{SE}(c)$$
> This one-sided lower bound is **strictly positive if and only if $p_{	ext{1-sided}} < 0.05$**.
>
> When a standard **two-sided 95% confidence interval** is reported:
> $$\left[ar{R}_{	ext{net}}(c) - 2.0106 \cdot 	ext{SE}(c), \quad ar{R}_{	ext{net}}(c) + 2.0106 \cdot 	ext{SE}(c)ight]$$
> its lower bound covers $2.5\%$ in each tail rather than $5\%$ in one tail. Consequently, whenever $0.025 \le p_{	ext{1-sided}} < 0.05$, the one-sided test PASSES ($p < 0.05$), but the lower bound of the two-sided 95% confidence interval includes zero ($	ext{CI}_{	ext{lower}} \le 0$).
> This is a standard mathematical consequence of differing tail coverages and does **NOT** indicate that the primary one-sided test failed. Both bounds are reported explicitly to prevent misinterpretation.

### 5.4 Test Assumptions & Input Validation Safeguards
1. **Independence Assumption**: Trade episodes occur approximately once per month (~30 days apart). Temporal autocorrelation between consecutive monthly episodes is assumed negligible.
2. **Central Limit Theorem for Sample Mean**: While individual FX returns exhibit excess kurtosis (fat tails), the sample mean $ar{R}_{	ext{net}}$ across $N = 49$ independent episodes is approximately normally distributed under the Central Limit Theorem.
3. **Statistical Integrity Prohibitions**:
   - Directional assignments ($d_i \in \{-1, +1\}$) are **NOT randomized by nature**; they are deterministic functions of macroeconomic releases.
   - The 1-sample test is **NOT a paired t-test** (there is no paired control trade in the primary test).
   - Non-parametric tests such as the Wilcoxon signed-rank test are **NOT assumption-free**; they assume that the underlying distribution of differences is continuous and symmetric around its pseudo-median.
4. **Input Validation & Zero-Variance Boundary Handling**:
   - If input returns contain `NaN`, `Inf`, or non-numeric values, the function raises `ValueError`.
   - If sample variance is zero ($s = 0$, all return values identical), the t-statistic and p-value are undefined. The statistical function raises `ValueError` rather than silently manufacturing a p-value of 0.5.

### 5.5 Descriptive Robustness Checks (Secondary Diagnostics)
To verify that parametric significance is not driven by a single extreme outlier:
1. **Wilcoxon Signed-Rank Test**: Evaluates median directional shift against zero under the assumption of distributional symmetry.
2. **Sign-Test / Sign-Flip Permutation**: Evaluates whether the number of positive trades exceeds chance, assuming reflection symmetry under $H_0$.
3. **Outlier Jackknife**: Leave-one-out recomputation of $ar{R}_{	ext{net}}$ and $t$ to verify that significance does not collapse upon removal of any single episode.

---

## 6. Predeclared Research Boundaries & Confounder Diagnostics

### 6.1 Predeclared Inclusions and Retentions
1. **Strict Concordance Sample ($N = 49$)**: All primary testing is pegged strictly to the 49 packages with $S_H 	imes S_C > 0$.
2. **Omission of ATR Lookback**: Pure fixed-horizon return study; no 14-H4 pre-entry volatility lookback is applied.
3. **Friday Releases Retained ($N = 15$)**: All 15 Friday releases are retained in the primary sample. However, results **must be reported separately for Friday ($N = 15$) vs Non-Friday ($N = 34$)** to diagnose the empirical effect of 72-hour weekend gap exposure.

### 6.2 Predeclared Limitations (Not Used to Post-Hoc Optimize)
1. **Simultaneous Cross-Currency Collisions (30 of 49 packages)**:
   - 25 packages collide with Canadian releases (CAD), 2 with Eurozone releases (EUR), and 3 with both CAD and EUR.
   - *Governance Rule*: Collisions are retained in the primary test. Results will be partitioned by $I_{	ext{collision}} \in \{0, 1\}$ (19 clean vs 30 colliding) as an attribution limitation, **NOT used to optimize or post-hoc filter the primary rule**.
2. **Same-Timestamp Macroeconomic Bundling (Mean 12.2 series)**:
   - Retail Sales is released simultaneously with Import Price Index, Export Price Index, and regional manufacturing surveys. Sole causal attribution to retail sales is strictly prohibited.
3. **Subsequent Macro Event Exposure (Median 10 later events)**:
   - Trades absorb subsequent economic releases during the 24-hour holding period. Reported as an empirical market reality.

### 6.3 Diagnostic Calendar Control Availability Audit (Labeled Diagnostic Only)
The calendar control audit evaluated whether non-announcement matching ($T - 7	ext{d}$ or $T - 14	ext{d}$) was feasible:
- $T - 7	ext{d}$ clean of high-impact USD/EUR releases: **14 / 49 (28.6%)**.
- $T - 14	ext{d}$ clean of high-impact USD/EUR releases: **5 / 49 (10.2%)**.
- At least one clean: **17 / 49 (34.7%)**.
- Contaminated in BOTH windows: **32 / 49 (65.3%)**.
> [!NOTE]
> **REMOVAL FROM PRIMARY TEST**:
> Matched calendar controls are **REMOVED from the primary hypothesis test**. The "17 clean" screening only checked calendar event tags; it did not verify matched candle-path continuity or execution spread feasibility. Furthermore, subtracting a control window that is contaminated 65.3% of the time by NFP, CPI, or FOMC decisions injects severe exogenous noise. The control availability ledger is retained strictly as an informational diagnostic.

---

## 7. Exact Pre-Price Decision Truth Table

The written decision logic and the software classification engine [`classify_discovery_outcome()`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/strategy_viability.py) are **100% mathematically equivalent**. All evaluations use **Scenario C (Assumed 10-point / 1.0-pip friction)** as the primary viability hurdle:

| Condition # | Mean Net Return ($ar{R}_{	ext{net}}$) | 1-Sided p-Value ($p_{	ext{1-sided}}$) | Win Rate ($W$) | Friday Subgroup ($ar{R}_{	ext{Fri}}$) | Non-Friday Subgroup ($ar{R}_{	ext{NonFri}}$) | Exact Decision Disposition | Scientific Verdict & Downstream Action |
|---|---|---|---|---|---|---|---|
| **1** | $\le 0.0$ | Any value | Any value | Any value | Any value | **`DISCONFIRMED_ADVERSE`** | **Adverse Point Estimate**: Strategy produces negative or flat drift under standard friction. Hypothesis disconfirmed. Post-2022 holdout remains SEALED. Investigation concluded. |
| **2** | $> 0.0$ | $\ge 0.10$ | Any value | Any value | Any value | **`INCONCLUSIVE_UNDERPOWERED`** | **Statistically Underpowered**: Positive point estimate, but indistinguishable from random drift ($p \ge 0.10$). Insufficient evidence. Post-2022 holdout remains SEALED. |
| **3** | $> 0.0$ | $0.05 \le p < 0.10$ | Any value | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Marginally Significant**: Positive point estimate, but fails standard $p < 0.05$ hurdle. Post-2022 holdout remains SEALED. |
| **4** | $> 0.0$ | $< 0.05$ | $< 0.50$ | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Directionally Inconsistent**: Fewer than half of trades are profitable; return is driven by a minority of extreme outlier bars. Post-2022 holdout remains SEALED. |
| **5** | $> 0.0$ | $< 0.05$ | $0.50 \le W < 0.53$ | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Sub-Hurdle Win Rate**: Profitable on mean, but fails the predeclared 53% win rate consistency hurdle. Post-2022 holdout remains SEALED. |
| **6** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | $\le 0.0$ | Any value | **`INCONCLUSIVE_FRAGILE`** | **Friday Subgroup Failure**: Anomaly fails on Friday / weekend-crossing trades ($ar{R}_{	ext{Fri}} \le 0$). Cannot claim general viability. Post-2022 holdout remains SEALED. |
| **7** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | Any value | $\le 0.0$ | **`INCONCLUSIVE_FRAGILE`** | **Non-Friday Subgroup Failure**: Anomaly fails on intra-week trades ($ar{R}_{	ext{NonFri}} \le 0$). Cannot claim general viability. Post-2022 holdout remains SEALED. |
| **8** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | Unverified / `None` | Unverified / `None` | **`INCONCLUSIVE_FRAGILE`** | **Missing Subgroup Verification**: Subgroup means not provided. Cannot verify stability across Friday vs Non-Friday regimes. Post-2022 holdout remains SEALED. |
| **9** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | $> 0.0$ | $> 0.0$ | **`PROMISING_DISCOVERY_CANDIDATE`** | **Promising Discovery Candidate**: Satisfies all discovery hurdles. **NOT A REGISTERED SETUP.** Earns the right to post-2022 holdout verification under the frozen rule. |

---

## 8. Predeclared Post-2022 Holdout Protocol (Predeclared while Sealed)

> [!IMPORTANT]
> **GOVERNANCE DIRECTIVE FOR POST-2022 HOLDOUT**:
> A promising pre-2023 discovery result is **NOT A REGISTERED SETUP**. It is merely an empirical finding that earns the right to be tested against the untouched post-2022 holdout.
> The rules governing the holdout test are **frozen now**, prior to any holdout inspection or unsealing.

### 8.1 Holdout Scope & Eligible-Release Handling
1. **Holdout Window**: `2023-01-01 00:00:00` to `2026-09-23 22:00:00` broker trade-server time (`timestamp >= 1672531200`).
2. **Eligible Sample Size ($N_{	ext{holdout}}$)**:
   - The export manifest contains 45 calendar rows for Retail Sales m/m.
   - **$N_{	ext{holdout}}$ is NOT assumed to be 45.** It will be determined strictly by applying the identical pre-2023 eligibility criteria:
     - Both Headline (`USD:US:840020010:r0`) and Core (`USD:US:840020011:r0`) must be co-released at the identical timestamp with non-empty Actual, Forecast, and Previous values.
     - Strict concordance required: $	ext{sign}(S_H) 	imes 	ext{sign}(S_C) > 0$.
     - Missing forecasts, active sign conflicts, and zero surprises are excluded under the identical logic.
3. **Sample Adequacy Requirement**:
   - If $N_{	ext{holdout}} < 15$ packages, the holdout sample is formally declared **sample-deficient / underpowered** for independent asymptotic hypothesis testing. The report must state this limitation and report descriptive metrics only.

### 8.2 Fixed Execution & Cost Specifications
- **Identical Entry Rule**: Open of the next active H4 bar ($T_{	ext{entry}} = 16:00$ for 15:30 releases; $20:00$ for 16:30 releases).
- **Identical Holding Horizon**: 6 completed active H4 blocks ($B_0, \dots, B_5$, 24 active hours).
- **Identical Directional Mapping**: $S_H > 0 \land S_C > 0 \implies 	ext{Short EURUSD}$ ($d = -1$); $S_H < 0 \land S_C < 0 \implies 	ext{Long EURUSD}$ ($d = +1$).
- **Identical Cost Hurdle**: Primary evaluation under **Scenario C (Assumed 10-point / 1.0-pip friction)**. Zero re-tuning of friction parameters.

### 8.3 Exact Holdout Decision Gates

```
                                  [ Post-2022 Holdout Evaluation: N_holdout ]
                                                     |
                     +-------------------------------+-------------------------------+
                     |                                                               |
            Holdout Mean Net <= 0                                           Holdout Mean Net > 0
                     |                                                               |
                     v                                               +---------------+---------------+
             [ HOLDOUT FAIL ]                                        |                               |
       (Non-Replicating Discovery)                          p_holdout >= 0.05 OR             p_holdout < 0.05 AND
             * HARD STOP *                                   N_holdout < 15 OR               Win Rate >= 50% AND
         Candidate Terminated                                 Win Rate < 50%                   N_holdout >= 15
                                                                     |                               |
                                                                     v                               v
                                                          [ HOLDOUT INCONCLUSIVE ]            [ HOLDOUT PASS ]
                                                           (Unverified Anomaly)          (Confirmed Valid Anomaly)
                                                               * HARD STOP *                         |
                                                          No Setup Registration                      v
                                                                                       [ ELIGIBLE FOR DEMO TRADING ]
```

1. **HOLDOUT PASS (Confirmed Out-of-Sample Anomaly)**:
   - Criteria:
     - Sample size $N_{	ext{holdout}} \ge 15$.
     - Sample mean net return strictly positive under Scenario C: $ar{R}_{	ext{holdout, net}}(c_2) > 0$.
     - Directional consistency: $	ext{sign}(ar{R}_{	ext{holdout}}) == 	ext{sign}(ar{R}_{	ext{discovery}})$.
     - 1-sided Student's t-test on holdout: $p_{	ext{holdout}} < 0.05$.
     - Win rate $\ge 50\%$.
   - **Downstream Action**: The anomaly has successfully replicated out-of-sample. The candidate is approved to advance to **live demo/forward paper trading**.
2. **HOLDOUT FAIL (Disconfirmed / Non-Replicating Discovery)**:
   - Criteria: $ar{R}_{	ext{holdout, net}}(c_2) \le 0.0$.
   - **Downstream Action**: The anomaly failed to replicate out-of-sample. The candidate is **permanently rejected** and cataloged as an in-sample discovery artifact / data-mining overfit. The inquiry is terminated; zero parameter re-tuning is permitted.
3. **HOLDOUT INCONCLUSIVE (Statistically Insufficient)**:
   - Criteria: $ar{R}_{	ext{holdout, net}}(c_2) > 0.0$, but $p_{	ext{holdout}} \ge 0.05$, OR $N_{	ext{holdout}} < 15$, OR win rate $< 50\%$.
   - **Downstream Action**: Positive drift is observed, but evidence is statistically insufficient to distinguish from random chance. The candidate **CANNOT be registered as a setup** and CANNOT advance to demo trading. It remains an unverified historical anomaly.

---

## 9. Audit Checklist & Mandatory Stop

- [x] Pinned raw calendar hash verified (`76062b8f...`)
- [x] Pinned EURUSD H1 candle hash verified (`893aa193...`)
- [x] Provenance verified: EURUSD 5 digits, point = 0.00001, pip = 10 broker points (`candle_symbols.csv`)
- [x] Long/Short Bid–Ask execution arithmetic defined and synthetically unit-tested (`tests/test_strategy_viability_arithmetic.py`)
- [x] 1-sample Student's t viability statistic and confidence interval defined and synthetically unit-tested
- [x] Boundary input validation implemented: rejects NaN, Inf, and zero variance without manufacturing p-values
- [x] Mathematical reconciliation between 1-sided p < 0.05 test and 2-sided 95% confidence interval documented
- [x] Frozen cost-sensitivity scenarios specified (0, 5, 10, 20, 30 points) with explicit disclosure of unmeasured commission, slippage, and overnight swap drag
- [x] Matched calendar controls removed from primary test; diagnostic availability ledger documented (65.3% contamination)
- [x] 12-H4 horizon designated strictly exploratory/descriptive; inconsistent fixed Holm thresholds removed
- [x] Complete decision truth table defined and proven 100% equivalent to `classify_discovery_outcome()`
- [x] Prior candidate searches ($K=21$, CPI/NFP Phase 1, German Ifo failure) registered as nominal p-value limitation
- [x] Exact, non-optimizable post-2022 holdout pass/fail rule predeclared while holdout outcomes remain sealed
- [x] Price blindness strictly preserved (zero price reads, zero backtests run, holdout strictly sealed)
- [ ] Codex Quant Director audit & formal protocol freeze
