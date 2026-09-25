# US Retail Sales EURUSD Research Protocol (Draft Proposal v0.4 - Freeze-Ready Pre-Price Design)

> [!CAUTION]
> **PROTOCOL STATUS: UNFROZEN PROPOSAL REQUIRING CODEX REVIEW & APPROVAL (DO NOT EXECUTE)**  
> This document is a **draft pre-price research specification**.  
> All trade mechanics, cost scenarios, statistical decision gates, directional mappings, and friction models are **PROPOSALS FOR REVIEW**, not approved or frozen facts.  
> **Strict Halt**: No candidate candle prices, returns, winning trades, or directional paths may be read, parsed, or computed under this protocol until formally audited, reconciled, and frozen by Codex.  
> Chronological Split Boundary: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).  
> All post-2022 price observations remain strictly sealed.

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
*Limitation on Nominal Significance*: Investigating US Retail Sales is step $K > 1$ in an ongoing research program. Any nominal p-value reported from this protocol is conditioned on prior candidate screening and must not be interpreted as an unadjusted, single-trial test.

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

## 4. Execution Timing, Bid–Ask Arithmetic & Cost-Sensitivity Scenarios

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

### 4.5 Bar-Level Spread Limitation & Frozen Cost-Sensitivity Scenarios
> [!WARNING]
> **BAR-LEVEL SPREAD CAVEAT**:
> The `spread` column in the pinned H1 candle file records a historical bar attribute (point snapshot). **It does NOT guarantee an executable entry or exit Ask price.** At bar transitions (16:00:00 / 20:00:00) and following macroeconomic releases, executable order-book depth and live spreads fluctuate.
> Fixed claims of "typical 1.0 pip spread" or "a 2-pip hurdle guarantees profit" are unsupported and rejected.

To ensure rigorous evaluation without assuming unverified execution costs, the protocol predeclares **four frozen cost-sensitivity scenarios**:

| Scenario ID | Scenario Name | Broker Points | EURUSD Pips | Price Deduction ($\Delta P$) | Purpose & Operational Context |
|---|---|---:|---:|---:|---|
| **Scenario 0** | **Gross / Frictionless** | 0 pts | 0.0 pips | 0.00000 | Theoretical baseline: measures gross informational drift. |
| **Scenario 1** | **Prime Institutional** | 5 pts | 0.5 pips | 0.00005 | Best-case ECN / prime institutional execution. |
| **Scenario 2** | **Standard Retail (Primary Gate)** | 10 pts | 1.0 pip | 0.00010 | Standard retail / median execution friction during normal hours. |
| **Scenario 3** | **Stressed / Conservative** | 20 pts | 2.0 pips | 0.00020 | Stressed execution (wider post-announcement spread and adverse fill). |

**Reporting Mandate**: All experimental outputs must report mean returns, pips, t-statistics, and win rates across **all four scenarios simultaneously**. To be considered viable, a strategy must clear **Scenario 2 (Standard Retail, 10 points / 1.0 pip)** with a strictly positive net return.

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

### 5.3 Uncertainty Interval
- **Primary Confidence Interval**: 95% two-sided Student's t confidence interval:
  $$\left[\bar{R}_{\text{net}}(c) - t_{0.975, 48} \cdot \text{SE}(c), \quad \bar{R}_{\text{net}}(c) + t_{0.975, 48} \cdot \text{SE}(c)\right]$$
  where $t_{0.975, 48} \approx 2.0106$.
- **Descriptive Bootstrap Interval**: Reported alongside the parametric interval as a descriptive check using a 100,000-iteration percentile bootstrap.

### 5.4 Test Assumptions & Explicit Scientific Honesty
1. **Independence Assumption**: Trade episodes occur approximately once per month (~30 days apart). Temporal autocorrelation between consecutive monthly episodes is assumed negligible.
2. **Central Limit Theorem for Sample Mean**: While individual FX returns exhibit excess kurtosis (fat tails), the sample mean $\bar{R}_{\text{net}}$ across $N = 49$ independent episodes is approximately normally distributed under the Central Limit Theorem.
3. **Prohibition on Misleading Statistical Terminology**:
   - Directional assignments ($d_i \in \{-1, +1\}$) are **NOT randomized by nature**; they are deterministic functions of macroeconomic releases.
   - The 1-sample t-test is **NOT a paired t-test** (there is no paired control trade in the primary test).
   - Non-parametric tests such as the Wilcoxon signed-rank test are **NOT assumption-free**; they assume that the underlying distribution of differences is continuous and symmetric around its pseudo-median.

### 5.5 Descriptive Robustness Checks (Secondary Diagnostics)
To verify that parametric significance is not driven by a single extreme outlier:
1. **Wilcoxon Signed-Rank Test**: Evaluates median directional shift against zero under the assumption of distributional symmetry.
2. **Sign-Test / Sign-Flip Permutation**: Evaluates whether the number of positive trades exceeds chance, assuming reflection symmetry under $H_0$.
3. **Outlier Jackknife**: Leave-one-out recomputation of $\bar{R}_{\text{net}}$ and $t$ to verify that significance does not collapse upon removal of any single episode.

---

## 6. Predeclared Research Boundaries & Confounder Diagnostics

### 6.1 Predeclared Inclusions and Retentions
1. **Strict Concordance Sample ($N = 49$)**: All primary testing is pegged to the 49 packages with $S_H \times S_C > 0$.
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

## 7. Formal Pre-Price Decision Gate Hierarchy

The empirical evaluation of the primary 6-H4 horizon across the 49 pre-2023 packages will result in exactly one of the following three mutually exclusive dispositions:

```
                                  [ Pre-2023 Evaluation: N = 49 Packages ]
                                                     |
                     +-------------------------------+-------------------------------+
                     |                                                               |
        Mean Net Return <= 0 OR                                            Mean Net Return > 0 AND
           1-Sided p >= 0.10                                                  1-Sided p < 0.10
                     |                                                               |
                     v                                               +---------------+---------------+
        [ DISCONFIRMED / NEGATIVE ]                                  |                               |
       (State 3: No Convincing Evid.)                       0.05 <= p < 0.10 OR             p < 0.05 AND Win Rate >= 53%
             * HARD STOP *                                 Win Rate < 50% OR               AND Positive under Scenario 2
       Post-2022 remains SEALED                            Fails Scenario 2                          |
                                                                     |                               v
                                                                     v                   [ PROMISING DISCOVERY CANDIDATE ]
                                                           [ INCONCLUSIVE / FRAGILE ]      (Candidate for Holdout Check)
                                                                 * HARD STOP *               * NOT A REGISTERED SETUP *
                                                           Post-2022 remains SEALED         Holdout Protocol Freeze Required
```

### Complete Pre-Price Decision Matrix

| Empirical Disposition | Quantitative Criteria (Scenario 2: Standard Retail 1.0 Pip) | Scientific Verdict & Downstream Action | Post-2022 Holdout Action |
|---|---|---|---|
| **1. Negative / Disconfirmed (State 3)** | $\bar{R}_{\text{net}}(c_2) \le 0$ **OR** 1-sided $p(c_2) \ge 0.10$ | **No Convincing Evidence**: Directional retail drift is absent or absorbed by retail execution friction. Candidate rejected. Closed as negative empirical result. | **STRICTLY SEALED**. Zero inspection permitted. Investigation concludes. |
| **2. Inconclusive / Economically Fragile** | $\bar{R}_{\text{net}}(c_2) > 0$ **AND** ($0.05 \le p(c_2) < 0.10$ **OR** win rate $< 50\%$ **OR** positive under Scenario 0/1 but negative under Scenario 2) | **Fragile / Statistically Insufficient**: Drift fails standard significance hurdles or cannot reliably clear standard retail transaction friction. | **STRICTLY SEALED**. Candidate is not robust enough to risk consuming holdout data. No setup registered. |
| **3. Promising Discovery Result** | $\bar{R}_{\text{net}}(c_2) > 0$ **AND** 1-sided $p(c_2) < 0.05$ **AND** win rate $\ge 53\%$ **AND** $\bar{R}_{\text{net}} > 0$ in both Friday and Non-Friday partitions | **Candidate for Holdout Verification**: Evidence of post-announcement drift surviving standard retail friction. **NOT A REGISTERED SETUP.** | **ELIGIBLE FOR FORMAL HOLDOUT FREEZE**. Candidate earns the right to a formal, frozen holdout verification audit on post-2022 data. |

### Governance Rules for a Promising Discovery Result
1. **NOT A REGISTERED SETUP**:
   A promising discovery result in pre-2023 data does **NOT** constitute a production trading strategy, an approved signal, or a registered setup.
2. **Untouched Post-2022 Holdout Verification**:
   The candidate must be tested against the untouched post-2022 holdout ($N = 45$ sealed packages, `2023-01-01` to `2026-09-23`) under the **exact, unchanged, frozen rule** (6 H4 horizon, entry at next active H4 bar, strict concordance, Scenario 2 friction).
3. **Demo Forward Testing**:
   If and only if the candidate survives the post-2022 holdout with positive net return and non-degraded win rate, it may be drafted into live forward paper/demo execution.

---

## 8. Audit Checklist & Mandatory Stop

- [x] Pinned raw calendar hash verified (`76062b8f...`)
- [x] Pinned EURUSD H1 candle hash verified (`893aa193...`)
- [x] Provenance verified: EURUSD 5 digits, point = 0.00001, pip = 10 broker points (`candle_symbols.csv`)
- [x] Long/Short Bid–Ask execution arithmetic defined and synthetically unit-tested (`tests/test_strategy_viability_arithmetic.py`)
- [x] 1-sample Student's t viability statistic and confidence interval defined and synthetically unit-tested
- [x] Frozen cost-sensitivity scenarios specified (0, 5, 10, 20 points)
- [x] Matched calendar controls removed from primary test; diagnostic availability ledger documented (65.3% contamination)
- [x] 12-H4 horizon designated strictly exploratory/descriptive; inconsistent fixed Holm thresholds removed
- [x] Prior candidate searches ($K=21$, CPI/NFP Phase 1, German Ifo failure) registered as nominal p-value limitation
- [x] Complete decision table provided with explicit distinction between discovery candidate and registered setup
- [x] Price blindness strictly preserved (zero price reads, zero backtests run, holdout strictly sealed)
- [ ] Codex Quant Director audit & formal protocol freeze
