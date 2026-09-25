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
> *For the 66 pre-2023 actionable releases of US ISM Manufacturing PMI on EURUSD, is the sample mean 24-active-H1 directional trade return strictly positive AFTER deducting a prespecified 1.0-pip execution friction (Scenario C)?*

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
*Limitation on Nominal Significance*: Investigating US ISM Manufacturing PMI is step $K > 1$ in an ongoing sequential screening program. Any nominal p-value reported from this protocol is conditioned on prior candidate screening and must not be interpreted as an unadjusted, discovery-wide false-positive guarantee.

---

## 2. Exact Series Identification & Data Provenance

### 2.1 Pinned Identifiers (Verified Facts)
- **Primary Headline Series**:
  - Key: `USD:US:840040001:r0`
  - Name: `ISM Manufacturing PMI` (`event_id = 840040001`, `revision = 0`, Institute for Supply Management)
  - Sector: `CALENDAR_SECTOR_BUSINESS` (`sector_code = 2`)
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
4. **Surprise Breakdown**:
   - **Positive Surprises ($S_H > 0$, Short EURUSD)**: Exactly **28 packages** (41.8% of complete packages).
   - **Negative Surprises ($S_H < 0$, Long EURUSD)**: Exactly **38 packages** (56.7% of complete packages).
   - **Zero Surprise ($S_H = 0.0$)**: Exactly **1 package** (`2018-03-01 18:00:00`, timestamp `1519927200`, Actual = 60.8, Forecast = 60.8). Excluded due to lack of directional impulse.
5. **Actionable Primary Discovery Sample**: Exactly **$N = 66$ packages** ($28 + 38$).
   - 100% EURUSD H1 forward path completeness exists across all 66 packages for both 24-H1 and 48-H1 horizons.

### 3.3 Explicit Pre-Declared Rejection of Multi-Component Filtering
Component series are formally **REJECTED as trade entry filters** and preserved strictly as post-unblinding attribution diagnostics:
1. **Prices Paid (`USD:US:840040002:r0`)**:
   - Measures input inflation, not output activity. In stagflation regimes, manufacturing activity falls while input costs rise ($S_H < 0 \land S_P > 0$).
   - Concordance is only 55.2% ($37 / 67$). Forcing concordance drops 29 of 66 actionable releases (43.9% sample loss).
2. **Employment (`USD:US:840040004:r0`) & New Orders (`USD:US:840040006:r0`)**:
   - Lack consensus forecasts prior to September 2017 in MetaQuotes data (32 missing forecasts).
   - Across the 63 complete component releases ($S_H \neq 0$):
     - Headline + Employment + New Orders: 23 concordant (12 pos, 11 neg) and 40 non-concordant (38 opposite sign, 2 neutral component). Imposing this drops sample to $N = 23$ (65.2% sample loss).
     - Headline + Prices Paid + Employment: 20 concordant (9 pos, 11 neg) and 43 non-concordant (43 opposite sign, 0 neutral).
     - All Four Components: 10 concordant (6 pos, 4 neg) and 53 non-concordant (51 opposite sign, 2 neutral). Imposing full concordance drops sample to $N = 10$ (84.8% sample loss).
   - Conditioning trade entry on component concordance collapses statistical test power to negligible levels. The primary test remains strictly on Headline PMI ($N = 66$).

---

## 4. Execution Timing, Pricing Arithmetic & Friction Model

### 4.1 Temporal Entry Rule: Uniform 60-Minute H1 Absorption Delay
Entry occurs at the **Open of the next active H1 candle** immediately following the announcement candle:
$$T_{\text{entry}} = T_{\text{release}} + 3600$$
- **Summer Schedule (EDT, UTC-4)**: Release at `17:00:00` server open $\implies$ Enter at **`18:00:00`** server open (60-minute delay; 43 of 66 actionable packages).
- **Winter Schedule (EST, UTC-5)**: Release at `18:00:00` server open $\implies$ Enter at **`19:00:00`** server open (60-minute delay; 23 of 66 actionable packages).

**Methodological Rationale**:
- Guarantees **100% seasonal symmetry**: identical 60-minute absorption delay year-round.
- Avoids the 120- vs 180-minute distortion introduced by H4 bar structures.
- Allows release-time spread widening to subside while entering ahead of secondary session liquidity.

### 4.2 Holding Horizon & Exit Pricing
- **Primary 24-Active-H1 Horizon**: Trade enters at the Open of the H1 candle at $T_{\text{entry}}$ (bar 0) and is held for exactly **24 consecutive active H1 bars** (bars $0, \dots, 23$).
- **Exit Definition**: **Exit occurs at the Close of the 24th active H1 bar** (bar 23).
- **Active Bar Stepping Across Weekend Closures**:
  - When holding spans a Friday 23:00 to Sunday 23:00 market closure, bar indexing steps over the closed period and resumes on Sunday/Monday open.
  - Exactly **11 of 66 actionable paths (16.7%)** cross a weekend boundary under 24-H1.
  - Exactly **22 of 66 actionable paths (33.3%)** cross a weekend boundary under 48-H1.
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

### 4.4 Exact Pricing & Return Formulas
From `candle_symbols.csv`:
- Symbol Digits: `5`
- Broker Point Size: $\text{Point} = 0.00001$ ($10^{-5}$)
- Standard Pip: $1\text{ pip} = 0.00010 = 10\text{ broker points}$
- Spread Field: The `spread` column in `candles_EURUSD_H1.csv` records the broker spread in integer points (`spread_points`).

Historical candle files record Bid prices (`open`, `high`, `low`, `close`). Execution accounts for the spread at entry and exit:

1. **Long EURUSD Trade ($d_i = +1$, Dovish USD Shock, $S_H < 0$)**:
   - Entry at Ask price:
     $$P_{\text{entry, Ask}} = \text{Open}_{\text{Bid}}(T_{\text{entry}}) + (\text{Spread}_{\text{entry}} \times \text{Point})$$
   - Exit at Bid price:
     $$P_{\text{exit, Bid}} = \text{Close}_{\text{Bid}}(T_{\text{exit\_bar}})$$
   - Directional Net Log Return:
     $$R_{\text{net, Long}} = \ln\left(\frac{P_{\text{exit, Bid}}}{P_{\text{entry, Ask}}}\right) = \ln\left(\frac{\text{Close}_{\text{Bid}}}{\text{Open}_{\text{Bid}} + (\text{Spread}_{\text{entry}} \times \text{Point})}\right)$$
   - Directional Net Pip Return:
     $$\text{Net Pips}_{\text{Long}} = \frac{\text{Close}_{\text{Bid}} - (\text{Open}_{\text{Bid}} + \text{Spread}_{\text{entry}} \times \text{Point})}{10 \times \text{Point}}$$

2. **Short EURUSD Trade ($d_i = -1$, Hawkish USD Shock, $S_H > 0$)**:
   - Entry at Bid price:
     $$P_{\text{entry, Bid}} = \text{Open}_{\text{Bid}}(T_{\text{entry}})$$
   - Exit at Ask price:
     $$P_{\text{exit, Ask}} = \text{Close}_{\text{Bid}}(T_{\text{exit\_bar}}) + (\text{Spread}_{\text{exit}} \times \text{Point})$$
   - Directional Net Log Return:
     $$R_{\text{net, Short}} = \ln\left(\frac{P_{\text{entry, Bid}}}{P_{\text{exit, Ask}}}\right) = \ln\left(\frac{\text{Open}_{\text{Bid}}}{\text{Close}_{\text{Bid}} + (\text{Spread}_{\text{exit}} \times \text{Point})}\right)$$
   - Directional Net Pip Return:
     $$\text{Net Pips}_{\text{Short}} = \frac{\text{Open}_{\text{Bid}} - (\text{Close}_{\text{Bid}} + \text{Spread}_{\text{exit}} \times \text{Point})}{10 \times \text{Point}}$$

### 4.5 Standard 5 Cost Sensitivity Scenarios
Performance must be evaluated across the identical five standardized friction scenarios established in the laboratory:

| Scenario ID | Points Hurdle | Pips Hurdle | Price Cost ($\Delta P$) | Specific Analytical Coverage |
|---|---:|---:|---:|---|
| **Scenario A** | 0 pts | 0.0 pips | 0.00000 | Frictionless baseline: evaluates gross post-announcement directional drift. |
| **Scenario B** | 5 pts | 0.5 pips | 0.00005 | Assumed minimal spread-only deduction: best-case institutional execution. |
| **Scenario C** | 10 pts | 1.0 pip | 0.00010 | **Primary Screening Hurdle**: Assumed standard retail/ECN spread deduction (1.0 pip). |
| **Scenario D** | 20 pts | 2.0 pips | 0.00020 | Assumed conservative spread deduction: wider post-announcement spread conditions. |
| **Scenario E** | 30 pts | 3.0 pips | 0.00030 | **Hypothetical Combined-Cost Sensitivity Hurdle**: Combines moderate spread (10–15 pts) + assumed commission buffer (5 pts) + slippage & swap carry buffer (10 pts). NOT an empirically verified all-in fee. |

### 4.6 Omitted Cost Warnings
> [!WARNING]
> **SPREAD-ONLY ARITHMETIC DOES NOT EQUAL VERIFIED NET BROKER PROFIT**:
> The pinned repository does not contain historical tick-level order book depth, execution slippage logs, broker commission statements, or historical overnight swap tables.
> A physical trade incurs three real-world friction components not captured by candle spreads:
> 1. **Broker Commissions**: Typically $3–$7 per round-turn standard lot (~0.3 to 0.7 pips).
> 2. **Execution Slippage**: Post-announcement volatility can cause adverse fill slippage (1 to 5 broker points).
> 3. **Overnight Swaps**: Holding for 24 active hours spans broker 00:00 trade-server rollover. The 11 weekend-crossing trades incur triple weekend financing.
> These unmeasured costs are **NOT** assumed to be zero. Scenario E provides a stress-test buffer.

---

## 5. Statistical Framework & Primary Decision Rule

### 5.1 Estimand & Test Statistic
Let $R_{\text{net}, i}(c)$ be the directional net log return of trade episode $i \in \{1, \dots, N\}$ under cost scenario $c$.
- **Sample Estimand**: The sample mean net directional return:
  $$\bar{R}_{\text{net}}(c) = \frac{1}{N} \sum_{i=1}^N R_{\text{net}, i}(c)$$
- **Sample Standard Deviation** ($s$, with $N - 1$ degrees of freedom):
  $$s(c) = \sqrt{\frac{1}{N - 1} \sum_{i=1}^N \left(R_{\text{net}, i}(c) - \bar{R}_{\text{net}}(c)\right)^2}$$
- **Standard Error of the Mean**:
  $$\text{SE}(c) = \frac{s(c)}{\sqrt{N}}$$

### 5.2 Hypothesis Formulation & Decision Gate
- **Null Hypothesis ($H_0$)**: Expected net directional return is non-positive:
  $$H_0: \mu_{\text{net}}(c_2) \le 0$$
- **Alternative Hypothesis ($H_1$)**: Expected net directional return is strictly positive:
  $$H_1: \mu_{\text{net}}(c_2) > 0$$
- **Primary Statistical Test**: **1-Sample Student's t-Test** (1-sided test against zero):
  $$t(c_2) = \frac{\bar{R}_{\text{net}}(c_2)}{\text{SE}(c_2)}$$
  $$p(c_2) = 1 - F_{t_{N-1}}(t(c_2))$$
  where $F_{t_{N-1}}$ is the cumulative distribution function of the Student's t distribution with $N - 1 = 65$ degrees of freedom.

### 5.3 Primary Decision Hurdle (Scenario C, 1.0-Pip Friction)
A candidate passes the primary discovery hurdle if and only if **ALL FOUR** criteria are satisfied simultaneously:
1. **Positive Point Estimate**: $\bar{R}_{\text{net}}(c_2) > 0.0$ pips.
2. **Parametric Significance**: One-sided p-value $p(c_2) < 0.05$ ($t > t_{0.95, 65} \approx 1.6686$).
3. **Win Rate Consistency**: $W = \frac{N_{\text{win}}}{N} \ge 50.0\%$ (at least 33 of 66 trades profitable).
4. **Subgroup Stability**: Both Friday ($N = 11$) and Non-Friday ($N = 55$) subgroups must exhibit positive mean returns ($\bar{R}_{\text{Fri}} > 0 \land \bar{R}_{\text{NonFri}} > 0$).

### 5.4 Descriptive Robustness Checks (Secondary Diagnostics)
To verify that parametric significance is not an artifact of a single extreme outlier:
1. **Wilcoxon Signed-Rank Test**: Evaluates median directional shift against zero under distributional symmetry.
2. **Sign-Test / Permutation**: Evaluates whether positive trades exceed chance under reflection symmetry.
3. **Leave-One-Out Jackknife**: Recomputes $\bar{R}_{\text{net}}$ and $t$ iteratively across all $N=66$ subsets to confirm no single episode drives the result.

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
- US Construction Spending m/m (`USD:US:840020002:r0`) co-releases at 10:00 AM NY in **63 of 66 actionable releases (95.5%)**.
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

## 7. Standard Failure Labels & Decision Truth Table

All evaluations use **Scenario C (Assumed 1.0-pip / 10-point friction)** on the primary 24-active-H1 horizon:

| Condition # | Mean Net Return ($\bar{R}_{\text{net}}$) | 1-Sided p-Value ($p_{\text{1-sided}}$) | Win Rate ($W$) | Friday Subgroup ($\bar{R}_{\text{Fri}}$) | Non-Friday Subgroup ($\bar{R}_{\text{NonFri}}$) | Exact Decision Disposition | Scientific Verdict & Downstream Action |
|---|---|---|---|---|---|---|---|
| **1** | $\le 0.0$ | Any value | Any value | Any value | Any value | **`DISCONFIRMED_ADVERSE`** | **Adverse Point Estimate**: Strategy produces flat or negative drift under standard friction. Hypothesis disconfirmed. Post-2022 holdout remains SEALED. Investigation concluded. |
| **2** | $> 0.0$ (Scen A) $\land \le 0.0$ (Scen C) | Any value | Any value | Any value | Any value | **`INCONCLUSIVE_FRICTION_DECAY`** | **Friction Decay**: Positive gross drift destroyed by 1-pip bid-ask spread. Candidate not commercially viable. Post-2022 holdout remains SEALED. |
| **3** | $> 0.0$ | $\ge 0.10$ | Any value | Any value | Any value | **`INCONCLUSIVE_UNDERPOWERED`** | **Statistically Underpowered**: Positive point estimate, but indistinguishable from random noise ($p \ge 0.10$). Post-2022 holdout remains SEALED. |
| **4** | $> 0.0$ | $0.05 \le p < 0.10$ | Any value | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Marginally Significant**: Fails the standard $p < 0.05$ threshold. Post-2022 holdout remains SEALED. |
| **5** | $> 0.0$ | $< 0.05$ | $< 0.50$ | Any value | Any value | **`INCONCLUSIVE_FRAGILE`** | **Directionally Inconsistent**: Fewer than half of trades are profitable; return is driven by a minority of outlier bars. Post-2022 holdout remains SEALED. |
| **6** | $> 0.0$ | $< 0.05$ | $\ge 0.50$ | $\le 0.0$ | Any value | **`INCONCLUSIVE_FRAGILE`** | **Friday Subgroup Failure**: Fails on Friday/weekend-crossing trades ($\bar{R}_{\text{Fri}} \le 0$). Cannot claim general viability. Post-2022 holdout remains SEALED. |
| **7** | $> 0.0$ | $< 0.05$ | $\ge 0.50$ | Any value | $\le 0.0$ | **`INCONCLUSIVE_FRAGILE`** | **Non-Friday Subgroup Failure**: Fails on intra-week trades ($\bar{R}_{\text{NonFri}} \le 0$). Post-2022 holdout remains SEALED. |
| **8** | $> 0.0$ | $< 0.05$ | $\ge 0.50$ | $> 0.0$ | $> 0.0$ | **`PROMISING_DISCOVERY_CANDIDATE`** | **Promising Discovery Candidate**: Satisfies all discovery hurdles. **NOT A REGISTERED SETUP.** Earns the right to post-2022 holdout verification under a frozen protocol. |

---

## 8. Strict Conditions Required Before Any 2023+ Holdout Examination

> [!CAUTION]
> **ABSOLUTE GOVERNANCE BARRIER: THE POST-2022 HOLDOUT IS STRICTLY SEALED**
> Under no circumstances may any post-2022 candle price (`timestamp >= 1672531200`), spread, return, or holdout trade outcome be computed or inspected unless ALL of the following sequential conditions are fulfilled:

1. **Protocol Freeze Approval**:
   - This draft protocol must be formally audited, reviewed, and signed off by Codex.
   - The Project Director must grant explicit written authorization to freeze the protocol.
2. **Committed Freeze Packet**:
   - A dedicated `ISM_PMI_FREEZE_PACKET.md` must be committed to git, pinning exact file hashes, git commit SHA, runner version, and decision gates.
3. **Calculation Runner Construction & Verification**:
   - A dedicated, price-blind calculation runner must be built, verified by unit tests, and committed to git BEFORE reading any candidate prices.
   - The runner must be strictly locked to pre-2023 discovery execution only.
4. **Pre-2023 Discovery Execution**:
   - The pre-2023 discovery run must be executed on the clean committed state.
5. **Discovery Hurdle Clearance**:
   - The pre-2023 discovery outcome must achieve **`PROMISING_DISCOVERY_CANDIDATE`**.
   - **Hard Stop on Disconfirmation**: If the discovery run produces `DISCONFIRMED_ADVERSE`, `INCONCLUSIVE_FRICTION_DECAY`, `INCONCLUSIVE_UNDERPOWERED`, or `INCONCLUSIVE_FRAGILE`, the investigation is **TERMINATED IMMEDIATELY**. The post-2022 holdout partition is **NEVER UNSEALED**.
6. **Separate Owner & Codex Authorization for Holdout Unsealing**:
   - Even if pre-2023 succeeds, holdout unsealing requires a separate, explicit pass of Codex audit and Project Director authorization.
7. **Holdout Sample Adequacy ($N_{\text{holdout}} \ge 15$)**:
   - The export manifest contains 45 post-2022 calendar rows for ISM Manufacturing PMI.
   - Eligible holdout packages ($N_{\text{holdout}}$) must be determined strictly by the identical inclusion criteria (complete A/F/P, $S_H \neq 0$).
   - If $N_{\text{holdout}} < 15$, the sample fails minimum statistical power and is classified as `HOLDOUT_SAMPLE_DEFICIENT` (descriptive only; no inference permitted).

---

## 9. Next Immediate Actions

1. Halt all code and price execution.
2. Submit this draft protocol to Codex and the Project Director for architectural review.
3. Do not create a calculation runner, read candle prices, or evaluate trade returns.
