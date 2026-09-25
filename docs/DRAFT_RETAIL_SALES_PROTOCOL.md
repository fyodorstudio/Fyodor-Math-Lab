
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
- This is an empirical **directional-strategy screening test** under prespecified assumed friction.
- More precisely, Scenario C tests a **hypothetical one-pip-friction screening rule**, not verified all-in broker profitability: historical commission, slippage, financing, and point-in-time calendar availability remain unmeasured. Any passing result is a candidate for further validation, not evidence that a broker could have filled the historical trades at those prices.
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
$$S_H = \text{Actual}_H - \text{Forecast}_H$$
$$S_C = \text{Actual}_C - \text{Forecast}_C$$

### 3.2 Predeclared Sample: Strict Concordance ($N = 49$)
The primary candidate sample is strictly restricted to packages exhibiting unequivocal sign agreement:
$$\text{sign}(S_H) \times \text{sign}(S_C) > 0$$
- **Positive Consensus Surprise (Short EURUSD, $d = -1$)**: Exactly **27 packages**.
- **Negative Consensus Surprise (Long EURUSD, $d = +1$)**: Exactly **22 packages**.
- **Total Actionable Sample**: Exactly **$N = 49$ packages** (100% forward path completeness on EURUSD for both 6 H4 and 12 H4).

### 3.3 Excluded Categories (Pre-2023 Baseline)
1. **Active Sign Conflict ($\text{sign}(S_H) \times \text{sign}(S_C) < 0$)**: Exactly **9 packages** (5 POS/NEG, 4 NEG/POS). Excluded due to contradictory economic transmission signals.
2. **Missing Consensus Forecast**: Exactly **28 packages** (all 24 packages in 2015–2016, plus 4 in Jan–Apr 2017 before MetaQuotes populated forecasts).
3. **Double Zero Surprise ($S_H = 0 \land S_C = 0$)**: Exactly **2 packages**.
4. **Single Zero Surprise ($S_H = 0 \lor S_C = 0$)**: Exactly **8 packages**.

---

## 4. Execution Timing, Bid–Ask Arithmetic & Assumed Cost Sensitivity Scenarios

### 4.1 Temporal Entry Rule
Entry occurs at the **Open of the next active H4 bar** immediately following completion of the announcement bar window:
- `15:30:00` release: Announcement H4 window (`12:00:00`–`16:00:00`) completes at `16:00:00`.
  - Entry occurs at the **Open of the 16:00:00 H4 bar** ($T_{\text{entry}} = \mathbf{16:00:00}$, **30-minute delay**; 35 of 49 strict packages).
- `16:30:00` release: Announcement H4 window (`16:00:00`–`20:00:00`) completes at `20:00:00`.
  - Entry occurs at the **Open of the 20:00:00 H4 bar** ($T_{\text{entry}} = \mathbf{20:00:00}$, **210-minute / 3.5-hour delay**; 14 of 49 strict packages).

### 4.2 Holding Horizon & Exit Pricing
- **Primary 6-H4 Horizon**: 6 completed active H4 blocks ($B_0, \dots, B_5$, 24 active hours).
- **Exit Timestamp**: $T_{\text{exit}} = T_{\text{entry}} + 6 \times 14400\text{ seconds}$ (in continuous trading) or stepped across the weekend closure.
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
     $$P_{\text{entry, Ask}} = \text{Open}_{\text{Bid}}(T_{\text{entry}}) + (\text{Spread}_{\text{entry}} \times \text{Point})$$
   - **Exit**: Executes at the **Bid** price:
     $$P_{\text{exit, Bid}} = \text{Close}_{\text{Bid}}(T_{\text{exit}})$$
   - **Directional Net Log Return**:
     $$R_{\text{net, Long}} = \ln\left(\frac{P_{\text{exit, Bid}}}{P_{\text{entry, Ask}}}\right) = \ln\left(\frac{\text{Close}_{\text{Bid}}}{\text{Open}_{\text{Bid}} + (\text{Spread}_{\text{entry}} \times \text{Point})}\right)$$
   - **Directional Net Pip Return**:
     $$\text{Net Pips}_{\text{Long}} = \frac{\text{Close}_{\text{Bid}} - (\text{Open}_{\text{Bid}} + \text{Spread}_{\text{entry}} \times \text{Point})}{10 \times \text{Point}}$$

2. **Short EURUSD Trade ($d_i = -1$, Hawkish Shock)**:
   - **Entry**: Executes at the **Bid** price:
     $$P_{\text{entry, Bid}} = \text{Open}_{\text{Bid}}(T_{\text{entry}})$$
   - **Exit**: Executes at the **Ask** price:
     $$P_{\text{exit, Ask}} = \text{Close}_{\text{Bid}}(T_{\text{exit}}) + (\text{Spread}_{\text{exit}} \times \text{Point})$$
   - **Directional Net Log Return**:
     $$R_{\text{net, Short}} = \ln\left(\frac{P_{\text{entry, Bid}}}{P_{\text{exit, Ask}}}\right) = \ln\left(\frac{\text{Open}_{\text{Bid}}}{\text{Close}_{\text{Bid}} + (\text{Spread}_{\text{exit}} \times \text{Point})}\right)$$
   - **Directional Net Pip Return**:
     $$\text{Net Pips}_{\text{Short}} = \frac{\text{Open}_{\text{Bid}} - (\text{Close}_{\text{Bid}} + \text{Spread}_{\text{exit}} \times \text{Point})}{10 \times \text{Point}}$$

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
> **Protocol Policy**: The protocol does **NOT** assume these unmeasured costs are zero. Instead, the protocol predeclares an explicit hypothetical combined-cost sensitivity scenario (Scenario E) to stress-test whether drift survives when spread is compounded by assumed commission, slippage, and overnight carry drag (acknowledging that historical broker commission, slippage, and swap tables are not recorded in the pinned data).

### 4.6 Assumed Spread-Friction Sensitivity Scenarios
The protocol establishes **five frozen, assumed sensitivity scenarios** (0, 5, 10, 20, and 30 broker points). These are predeclared sensitivity hurdles, **NOT empirically established broker tiers**:

| Scenario ID | Points Hurdle | Pips Hurdle | Price Cost ($\Delta P$) | Specific Analytical Coverage |
|---|---:|---:|---:|---|
| **Scenario A** | 0 pts | 0.0 pips | 0.00000 | Frictionless theoretical baseline: evaluates gross post-announcement directional drift. |
| **Scenario B** | 5 pts | 0.5 pips | 0.00005 | Assumed minimal spread-only deduction: best-case frictionless environment. |
| **Scenario C** | 10 pts | 1.0 pip | 0.00010 | **Primary Screening Hurdle**: Assumed moderate spread deduction (1.0 pip). Strategy must clear this hurdle to be considered viable. |
| **Scenario D** | 20 pts | 2.0 pips | 0.00020 | Assumed conservative spread deduction: wider post-announcement spread conditions. |
| **Scenario E** | 30 pts | 3.0 pips | 0.00030 | **Hypothetical Combined-Cost Sensitivity Hurdle**: Combines moderate spread (10–15 pts) + assumed commission buffer (5 pts) + slippage & swap carry buffer (10 pts). NOT an empirically established all-in broker fee. |

**Reporting Mandate**: All experimental outputs must report mean returns, pips, t-statistics, and win rates across **all five scenarios simultaneously**. Viability requires strictly positive net return under **Scenario C (10 points / 1.0 pip)**, with Scenarios D and E providing explicit sensitivity boundaries.

---

## 5. Statistical Framework & Primary Hypothesis Test

### 5.1 Primary Test Statistic & Estimand
Let $R_{\text{net}, i}(c)$ be the directional net log return of trade episode $i \in \{1, \dots, N\}$ under cost scenario $c$.
- **Sample Estimand**: The sample mean net directional return:
  $$\bar{R}_{\text{net}}(c) = \frac{1}{N} \sum_{i=1}^N R_{\text{net}, i}(c)$$
- **Sample Standard Deviation** ($s$, with $N - 1$ degrees of freedom):
  $$s(c) = \sqrt{\frac{1}{N - 1} \sum_{i=1}^N \left(R_{\text{net}, i}(c) - \bar{R}_{\text{net}}(c)\right)^2}$$
- **Standard Error of the Mean**:
  $$\text{SE}(c) = \frac{s(c)}{\sqrt{N}}$$

### 5.2 Hypothesis Formulation & Test Method
- **Null Hypothesis ($H_0$)**: Expected net directional return is non-positive:
  $$H_0: \mu_{\text{net}}(c) \le 0$$
- **Alternative Hypothesis ($H_1$)**: Expected net directional return is strictly positive:
  $$H_1: \mu_{\text{net}}(c) > 0$$
- **Primary Statistical Test**: **1-Sample Student's t-Test** (1-sided test against zero):
  $$t(c) = \frac{\bar{R}_{\text{net}}(c)}{\text{SE}(c)}$$
  $$p(c) = 1 - F_{t_{N-1}}(t(c))$$
  where $F_{t_{N-1}}$ is the cumulative distribution function of the Student's t distribution with $N - 1 = 48$ degrees of freedom.

### 5.3 Mathematical Reconciliation: One-Sided Test vs Two-Sided Confidence Interval
> [!NOTE]
> **CONFIDENCE BOUND RECONCILIATION**:
> The primary decision hurdle is a **one-sided test at $\alpha = 0.05$** ($t > t_{0.95, 48} \approx 1.6772$).
> The matching one-sided 95% lower confidence bound is:
> $$\text{LB}_{95\%} = \bar{R}_{\text{net}}(c) - 1.6772 \cdot \text{SE}(c)$$
> This one-sided lower bound is **strictly positive if and only if $p_{\text{1-sided}} < 0.05$**.
>
> When a standard **two-sided 95% confidence interval** is reported:
> $$\left[\bar{R}_{\text{net}}(c) - 2.0106 \cdot \text{SE}(c), \quad \bar{R}_{\text{net}}(c) + 2.0106 \cdot \text{SE}(c)\right]$$
> its lower bound covers $2.5\%$ in each tail rather than $5\%$ in one tail. Consequently, whenever $0.025 \le p_{\text{1-sided}} < 0.05$, the one-sided test PASSES ($p < 0.05$), but the lower bound of the two-sided 95% confidence interval includes zero ($\text{CI}_{\text{lower}} \le 0$).
> This is a standard mathematical consequence of differing tail coverages and does **NOT** indicate that the primary one-sided test failed. Both bounds are reported explicitly to prevent misinterpretation.

### 5.4 Test Assumptions & Input Validation Safeguards
1. **Independence Assumption**: Trade episodes occur approximately once per month (~30 days apart). Temporal autocorrelation between consecutive monthly episodes is assumed negligible.
2. **Approximation, Not Guarantee**: The one-sample t-test relies on an adequate sampling approximation. $N = 49$ alone does not establish approximate normality of the sample mean under fat tails, outliers, or dependence; inspect the predeclared diagnostics and report any sensitivity without changing the primary rule after outcomes are known.
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
3. **Outlier Jackknife**: Leave-one-out recomputation of $\bar{R}_{\text{net}}$ and $t$ to verify that significance does not collapse upon removal of any single episode.

---

## 6. Predeclared Research Boundaries & Confounder Diagnostics

### 6.1 Predeclared Inclusions and Retentions
1. **Strict Concordance Sample ($N = 49$)**: All primary testing is pegged strictly to the 49 packages with $S_H \times S_C > 0$.
2. **Omission of ATR Lookback**: Pure fixed-horizon return study; no 14-H4 pre-entry volatility lookback is applied.
3. **Friday Releases Retained ($N = 15$)**: All 15 Friday releases are retained in the primary sample. However, results **must be reported separately for Friday ($N = 15$) vs Non-Friday ($N = 34$)** to diagnose the empirical effect of 72-hour weekend gap exposure.

### 6.2 Predeclared Limitations (Not Used to Post-Hoc Optimize)
1. **Simultaneous Cross-Currency Collisions (30 of 49 packages)**:
   - 25 packages collide with Canadian releases (CAD), 2 with Eurozone releases (EUR), and 3 with both CAD and EUR.
   - *Governance Rule*: Collisions are retained in the primary test. Results will be partitioned by $I_{\text{collision}} \in \{0, 1\}$ (19 clean vs 30 colliding) as an attribution limitation, **NOT used to optimize or post-hoc filter the primary rule**.
2. **Same-Timestamp Macroeconomic Bundling (Mean 12.2 series)**:
   - Retail Sales is released simultaneously with Import Price Index, Export Price Index, and regional manufacturing surveys. Sole causal attribution to retail sales is strictly prohibited.
3. **Subsequent Macro Event Exposure (Median 10 later events)**:
   - Trades absorb subsequent economic releases during the 24-hour holding period. Reported as an empirical market reality.

### 6.3 Diagnostic Calendar Control Availability Audit (Labeled Diagnostic Only)
The calendar control audit evaluated whether non-announcement matching ($T - 7\text{d}$ or $T - 14\text{d}$) was feasible:
- $T - 7\text{d}$ clean of high-impact USD/EUR releases: **14 / 49 (28.6%)**.
- $T - 14\text{d}$ clean of high-impact USD/EUR releases: **5 / 49 (10.2%)**.
- At least one clean: **17 / 49 (34.7%)**.
- Contaminated in BOTH windows: **32 / 49 (65.3%)**.
> [!NOTE]
> **REMOVAL FROM PRIMARY TEST**:
> Matched calendar controls are **REMOVED from the primary hypothesis test**. The "17 clean" screening only checked calendar event tags; it did not verify matched candle-path continuity or execution spread feasibility. Furthermore, subtracting a control window that is contaminated 65.3% of the time by NFP, CPI, or FOMC decisions injects severe exogenous noise. The control availability ledger is retained strictly as an informational diagnostic.

---

## 7. Exact Pre-Price Decision Truth Table

The written decision logic and the software classification engine [`classify_discovery_outcome()`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/strategy_viability.py) are **100% mathematically equivalent**. All evaluations use **Scenario C (Assumed 10-point / 1.0-pip friction)** as the primary viability hurdle:

| Condition # | Mean Net Return ($\bar{R}_{\text{net}}$) | 1-Sided p-Value ($p_{\text{1-sided}}$) | Win Rate ($W$) | Friday Subgroup ($\bar{R}_{\text{Fri}}$) | Non-Friday Subgroup ($\bar{R}_{\text{NonFri}}$) | Exact Decision Disposition | Scientific Verdict & Downstream Action |
|---|---|---|---|---|---|---|---|
| **1** | $\le 0.0$ | Any value | Any value | Any value | Any value | **`DISCONFIRMED_ADVERSE`** | **Adverse Point Estimate**: Strategy produces negative or flat drift under standard friction. Hypothesis disconfirmed. Post-2022 holdout remains SEALED. Investigation concluded. |
| **2** | $> 0.0$ | $\ge 0.10$ | Any value | Any value | Any value | **`INCONCLUSIVE_UNDERPOWERED`** | **Statistically Underpowered**: Positive point estimate, but indistinguishable from random drift ($p \ge 0.10$). Insufficient evidence. Post-2022 holdout remains SEALED. |
| **3** | $> 0.0$ | $0.05 \le p < 0.10$ | Any value | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Marginally Significant**: Positive point estimate, but fails standard $p < 0.05$ hurdle. Post-2022 holdout remains SEALED. |
| **4** | $> 0.0$ | $< 0.05$ | $< 0.50$ | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Directionally Inconsistent**: Fewer than half of trades are profitable; return is driven by a minority of extreme outlier bars. Post-2022 holdout remains SEALED. |
| **5** | $> 0.0$ | $< 0.05$ | $0.50 \le W < 0.53$ | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Sub-Hurdle Win Rate**: Profitable on mean, but fails the predeclared 53% win rate consistency hurdle. Post-2022 holdout remains SEALED. |
| **6** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | $\le 0.0$ | Any value | **`INCONCLUSIVE_FRAGILE`** | **Friday Subgroup Failure**: Anomaly fails on Friday / weekend-crossing trades ($\bar{R}_{\text{Fri}} \le 0$). Cannot claim general viability. Post-2022 holdout remains SEALED. |
| **7** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | Any value | $\le 0.0$ | **`INCONCLUSIVE_FRAGILE`** | **Non-Friday Subgroup Failure**: Anomaly fails on intra-week trades ($\bar{R}_{\text{NonFri}} \le 0$). Cannot claim general viability. Post-2022 holdout remains SEALED. |
| **8** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | Unverified / `None` | Unverified / `None` | **`INCONCLUSIVE_FRAGILE`** | **Missing Subgroup Verification**: Subgroup means not provided. Cannot verify stability across Friday vs Non-Friday regimes. Post-2022 holdout remains SEALED. |
| **9** | $> 0.0$ | $< 0.05$ | $\ge 0.53$ | $> 0.0$ | $> 0.0$ | **`PROMISING_DISCOVERY_CANDIDATE`** | **Promising Discovery Candidate**: Satisfies all discovery hurdles. **NOT A REGISTERED SETUP.** Earns the right to post-2022 holdout verification under the frozen rule. |

---

## 8. Predeclared Post-2022 Holdout Protocol (Predeclared while Sealed)

> [!IMPORTANT]
> **GOVERNANCE DIRECTIVE FOR POST-2022 HOLDOUT**:
> A promising pre-2023 discovery result is **NOT A REGISTERED SETUP**. It is merely an empirical finding that earns the right to be tested against the untouched post-2022 holdout.
> The rules governing the holdout test are **proposed for freeze before outcomes are opened**, prior to any holdout inspection or unsealing.

### 8.1 Holdout Scope & Eligible-Release Handling
1. **Holdout Window**: `2023-01-01 00:00:00` to `2026-09-23 22:00:00` broker trade-server time (`timestamp >= 1672531200`).
2. **Eligible Sample Size ($N_{\text{holdout}}$)**:
   - The export manifest contains 45 calendar rows for Retail Sales m/m.
   - **$N_{\text{holdout}}$ is NOT assumed to be 45.** It will be determined strictly by applying the identical pre-2023 eligibility criteria:
     - Both Headline (`USD:US:840020010:r0`) and Core (`USD:US:840020011:r0`) must be co-released at the identical timestamp with non-empty Actual, Forecast, and Previous values.
     - Strict concordance required: $\text{sign}(S_H) \times \text{sign}(S_C) > 0$.
     - Missing forecasts, active sign conflicts, and zero surprises are excluded under the identical logic.
3. **Sample Adequacy Requirement**:
   - If $N_{\text{holdout}} < 15$ packages, the sample fails this protocol's **prespecified minimum** and cannot earn a holdout pass. This cutoff is a decision rule, not a theorem that all inference with fewer than 15 observations is invalid. The report must state the limitation and report descriptive metrics only under this protocol.

### 8.2 Fixed Execution & Cost Specifications
- **Identical Entry Rule**: Open of the next active H4 bar ($T_{\text{entry}} = 16:00$ for 15:30 releases; $20:00$ for 16:30 releases).
- **Identical Holding Horizon**: 6 completed active H4 blocks ($B_0, \dots, B_5$, 24 active hours).
- **Identical Directional Mapping**: $S_H > 0 \land S_C > 0 \implies \text{Short EURUSD}$ ($d = -1$); $S_H < 0 \land S_C < 0 \implies \text{Long EURUSD}$ ($d = +1$).
- **Identical Cost Hurdle**: Primary evaluation under **Scenario C (Assumed 10-point / 1.0-pip friction)**. Zero re-tuning of friction parameters.

### 8.3 Exact Holdout Decision Gates

The post-2022 holdout classification is implemented in [`classify_holdout_outcome()`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/strategy_viability.py) with four mutually exclusive branches:

```
                              [ Post-2022 Holdout Sample Size: N_holdout ]
                                                   |
                     +-----------------------------+-----------------------------+
                     |                                                           |
             N_holdout < 15                                               N_holdout >= 15
                     |                                                           |
                     v                                           +---------------+---------------+
         [ HOLDOUT SAMPLE DEFICIENT ]                            |                               |
       (Underpowered / N < 15 Packages)                 Holdout Mean Net <= 0           Holdout Mean Net > 0
           Descriptive Metrics Only                              |                               |
                * HARD STOP *                                    v               +---------------+---------------+
            No Inference Permitted                        [ HOLDOUT FAIL ]       |                               |
                                                    (Disconfirmed Point Est.) p_holdout >= 0.05 OR    p_holdout < 0.05 AND
                                                          * HARD STOP *       Win Rate < 50% OR       Win Rate >= 50% AND
                                                       Candidate Terminated   Sign Mismatch           Sign Matches Discovery
                                                                                 |                               |
                                                                                 v                               v
                                                                      [ HOLDOUT INCONCLUSIVE ]   [ HOLDOUT PASS ELIGIBLE FOR DEMO ]
                                                                       (Statistically Weak)      (Eligible for Demo Forward Validation)
                                                                           * HARD STOP *                 * NOT PROVEN PROFITABLE *
                                                                       No Setup Registration         Grants Demo Forward Validation
```

1. **Branch 1: HOLDOUT SAMPLE DEFICIENT (Underpowered Sample Size)**:
   - **Hurdle**: Sample size $N_{\text{holdout}} < 15$ packages (evaluated FIRST, before requiring statistical metrics).
   - **Downstream Action**: The holdout sample fails the prespecified minimum for a pass. If $N_{\text{holdout}} = 0$ (no eligible releases), sample mean, p-value, and win rate do not exist; `classify_holdout_outcome(0, None, None, None)` returns `HOLDOUT_SAMPLE_DEFICIENT` without invented placeholder numbers. For $N_{\text{holdout}} \ge 15$, valid finite statistics are strictly required. The report documents descriptive metrics only under this protocol. Zero forward demo trading or setup registration is permitted.
2. **Branch 2: HOLDOUT FAIL (Disconfirmed / Non-Replicating Discovery)**:
   - **Hurdle**: Sample size $N_{\text{holdout}} \ge 15$ AND sample mean net return under Scenario C $\bar{R}_{\text{holdout, net}}(c_2) \le 0.0$.
   - **Downstream Action**: The historical holdout point estimate is flat or negative. This candidate is rejected **under this frozen rule** and must not be rescued by parameter re-tuning on the same data. A negative estimate does not prove the discovery was an overfit or that the true expected return is non-positive.
3. **Branch 3: HOLDOUT INCONCLUSIVE (Statistically Insufficient or Inconsistent)**:
   - **Hurdle**: Sample size $N_{\text{holdout}} \ge 15$ AND $\bar{R}_{\text{holdout, net}}(c_2) > 0.0$, BUT fails any secondary hurdle:
     - 1-sided Student's t-test on holdout: $p_{\text{holdout}} \ge 0.05$ (data cannot distinguish positive drift from random noise).
     - Win rate $< 50\%$ (fewer than half of holdout trades are profitable).
     - Directional sign flip: $\text{sign}(\bar{R}_{\text{holdout}}) \ne \text{sign}(\bar{R}_{\text{discovery}})$.
   - **Downstream Action**: Positive drift is observed, but evidence is statistically insufficient or directionally inconsistent. The candidate **CANNOT be registered as a setup** and CANNOT advance to demo trading. It remains an unverified historical anomaly.
4. **Branch 4: HOLDOUT PASS (Eligible for Demo Forward Validation)**:
   - **Hurdles (All Must Be Satisfied Simultaneously)**:
     - Sample size $N_{\text{holdout}} \ge 15$.
     - Sample mean net return strictly positive under Scenario C: $\bar{R}_{\text{holdout, net}}(c_2) > 0$.
     - Directional consistency: $\text{sign}(\bar{R}_{\text{holdout}}) == \text{sign}(\bar{R}_{\text{discovery}})$.
     - 1-sided Student's t-test on holdout: $p_{\text{holdout}} < 0.05$.
     - Win rate $\ge 50\%$.
   - **Downstream Action**: The candidate successfully replicates out-of-sample under the predeclared hurdle. This grants **eligibility for demo forward validation** in a live forward paper/demo execution environment. It does **NOT** constitute proof of executable profitability or an immutable trading setup.

**Logical simplification for this candidate:** Discovery can advance only with a strictly positive Scenario C mean. The holdout `mean <= 0` branch is tested before the sign check. Consequently, any holdout with `mean > 0` already has a matching sign; the written "sign mismatch" condition and the code's `discovery_mean_sign` comparison are redundant for this positive-drift protocol, not an independent validation hurdle. Do not count them as separate evidence.

---

## 9. Audit Checklist & Mandatory Stop

- [x] Pinned raw calendar hash verified (`76062b8f...`)
- [x] Pinned EURUSD H1 candle hash verified (`893aa193...`)
- [x] Provenance verified: EURUSD 5 digits, point = 0.00001, pip = 10 broker points (`candle_symbols.csv`)
- [x] Long/Short Bid–Ask execution arithmetic defined and synthetically unit-tested (`tests/test_strategy_viability_arithmetic.py`)
- [x] 1-sample Student's t viability statistic and confidence interval defined and synthetically unit-tested
- [x] Boundary input validation implemented: rejects NaN, Inf, and zero variance without manufacturing p-values
- [x] Mathematical reconciliation between 1-sided p < 0.05 test and 2-sided 95% confidence interval documented
- [x] Assumed cost-sensitivity scenarios specified (0, 5, 10, 20, 30 points) with Scenario E explicitly labeled as hypothetical combined-cost sensitivity, disclosing unmeasured historical commission, slippage, and overnight swap drag
- [x] Matched calendar controls removed from primary test; diagnostic availability ledger documented (65.3% contamination)
- [x] 12-H4 horizon designated strictly exploratory/descriptive; inconsistent fixed Holm thresholds removed
- [x] Complete decision truth table defined and proven 100% equivalent to `classify_discovery_outcome()`
- [x] Prior candidate searches ($K=21$, CPI/NFP Phase 1, German Ifo failure) registered as nominal p-value limitation
- [x] Exact, non-optimizable post-2022 holdout pass/fail rule predeclared while holdout outcomes remain sealed
- [x] Price blindness strictly preserved (zero price reads, zero backtests run, holdout strictly sealed)
- [ ] Codex Quant Director audit & formal protocol freeze

**Freeze-review scope:** A freeze would authorize only the prespecified *historical screening calculation* on pre-2023 prices. It would not validate historical fills, establish first-seen calendar vintages, or authorize use of the 2023+ partition or live/demo orders. Before opening candidate prices, record the exact implementation commit and output schema, verify the H1-to-H4 entry/exit mapping against hand-worked synthetic cases (including a weekend), and retain the executable calculation as an auditable artifact. These are review items, not permission to retune the hypothesis after seeing returns.
