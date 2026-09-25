# US Retail Sales EURUSD Research Protocol (Draft Proposal v0.3)

> [!CAUTION]
> **PROTOCOL STATUS: UNFROZEN PROPOSAL REQUIRING CODEX REVIEW & APPROVAL (DO NOT EXECUTE)**  
> This document is a **draft pre-price research specification**.  
> All control matching algorithms, exclusion rules, statistical decision gates, directional mappings, and cost proxies are **PROPOSALS FOR REVIEW**, not approved or frozen facts.  
> **Strict Halt**: No candidate candle prices, returns, winning trades, or directional paths may be read, parsed, or computed under this protocol until formally audited, reconciled, and frozen by Codex.  
> Chronological Split Boundary: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).  
> All post-2022 price observations remain strictly sealed.

---

## 1. Candidate Research Question & Hypothesis (Proposed)

> *Does an unexpected consensus surprise in US consumer retail demand (Retail Sales m/m + Core Retail Sales m/m) produce statistically significant, persistent post-announcement drift on EURUSD across the primary trading day (6 completed H4 blocks / 24 active hours), or is the macroeconomic information immediately absorbed during the announcement bar?*

### 1.1 Declared Primary Horizon & Exploratory Horizon
To avoid multi-horizon data dredging and preserve statistical power:
- **Primary Horizon**: **6 completed active H4 blocks (24 active hours / 1st trading day)**. All primary hypothesis tests, decision gates, and sample-size evaluations are pegged strictly to 6 H4.
- **Secondary / Exploratory Horizon**: **12 completed active H4 blocks (48 active hours / 2nd trading day)**. Evaluated strictly as an exploratory persistence check under Holm-Bonferroni family-wise error rate control ($\alpha_{\text{primary}} = 0.025$, $\alpha_{\text{exploratory}} = 0.05$).

### 1.2 Prior Trials & Researcher Degrees of Freedom Registration
In accordance with forensic anti-hallucination and research integrity standards, this protocol explicitly registers prior trial history:
1. **Phase 1 Trials**: Formal empirical trials on US CPI and NFP post-announcement drift.
2. **German Ifo Pilot Trial**: Evaluated German Ifo Business Climate + Expectations on EURUSD ($N = 40$ actionable episodes). Yielded permutation $p = 0.9575$, concluding **State 3: No Convincing Evidence** (`evidence/trials/ifo/FMS_PILOT_IFO_PROTOCOL.md`).
3. **Multi-Candidate Screening**: The prior inventory (`evidence/inventory/fms_episodes.jsonl`) screened 21 macro series.
*Governance Mandate*: Investigating US Retail Sales is step $K > 1$ in an ongoing research program. Any reported p-value must be interpreted within this sequential context rather than presented as an unconditioned single trial.

### 1.3 Economic Transmission Rationale
- **Consumer Demand & Monetary Policy**: Personal consumption accounts for ~70% of US GDP. US Retail Sales is the earliest monthly hard data on goods consumption. A positive retail sales surprise indicates robust consumer demand, upward pressure on terminal interest rates, and higher Treasury yields, implying USD appreciation (**Short EURUSD**, $d = -1$).
- **Delayed Drift Hypothesis**: If institutional portfolio rebalancing and systematic fixed-income duration adjustments take multiple trading sessions to clear, EURUSD may experience multi-session post-announcement drift.
- **Null Hypothesis ($H_0$)**: Post-announcement excess log return $\mathbb{E}[\Delta R] \le 0$. Immediate repricing within the announcement bar absorbs all informational content; delayed post-announcement drift does not exceed baseline market drift.

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

### 2.2 Directional Mapping (Proposal Requiring Review)
Because EURUSD is quoted as EUR (Base) / USD (Quote):
- **Bullish US Economy (Hawkish Shock)**:
  - Headline POS ($S_H > 0$) & Core POS ($S_C > 0$) $\implies$ **Short EURUSD** ($d_i = -1$).
- **Bearish US Economy (Dovish Shock)**:
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

### 3.2 Actionable Co-Release Rule (Unresolved Design Decision)
- **Option A (Strict Sign Agreement - Recommended Proposal)**:
  $$\text{sign}(S_H) \times \text{sign}(S_C) > 0$$
  Requires both headline and core to surprise in the identical direction.
  - POS/POS (Short EURUSD): **27 packages**
  - NEG/NEG (Long EURUSD): **22 packages**
  - Actionable Sample: **$N = 49$** (100% forward path completeness on EURUSD).
- **Option B (Primary + Non-Conflicting Confirmation)**:
  $$\text{sign}(S_H) \ne 0 \quad \land \quad \text{sign}(S_H) \times \text{sign}(S_C) \ge 0$$
  Admits cases where Core surprise is zero ($S_C = 0$) but Headline is directional.
  - Adds 2 packages (Headline POS / Core ZERO).
  - Actionable Sample: **$N = 51$**.
- **Option C (Unfiltered Headline)**:
  Trade Headline direction regardless of Core surprise ($N = 63$).

### 3.3 Excluded Categories (Pre-2023 Baseline)
1. **Active Sign Conflict ($\text{sign}(S_H) \times \text{sign}(S_C) < 0$)**: Exactly **9 packages** (5 POS/NEG, 4 NEG/POS).
2. **Missing Consensus Forecast**: Exactly **28 packages** (2015 to April 2017).
3. **Double Zero Surprise ($S_H = 0 \land S_C = 0$)**: Exactly **2 packages**.

---

## 4. Execution Timing, Horizon Definitions & Friction Modeling

### 4.1 Temporal Entry Rule (Proposed Specification)
Entry occurs at the **Open of the next active H4 bar** immediately following completion of the announcement bar window:
- `15:30:00` release: Announcement H4 window (`12:00:00`–`16:00:00`) completes at `16:00:00`.
  - Entry occurs at the **Open of the 16:00:00 H4 bar** ($T_{\text{entry}} = \mathbf{16:00:00}$, **30-minute delay**; 35 of 49 strict packages).
- `16:30:00` release: Announcement H4 window (`16:00:00`–`20:00:00`) completes at `20:00:00`.
  - Entry occurs at the **Open of the 20:00:00 H4 bar** ($T_{\text{entry}} = \mathbf{20:00:00}$, **210-minute / 3.5-hour delay**; 14 of 49 strict packages).

### 4.2 Primary & Secondary Holding Horizons
- **Primary Horizon (6 H4)**: 6 completed active H4 blocks ($B_0, \dots, B_5$, 24 active hours). Theoretical exit proxy is $\text{Close}_{\text{Bid}}(B_5)$.
- **Secondary Horizon (12 H4)**: 12 completed active H4 blocks ($B_0, \dots, B_{11}$, 48 active hours). Theoretical exit proxy is $\text{Close}_{\text{Bid}}(B_{11})$.

### 4.3 Executable Pricing & Real-World Transaction Friction
A model measuring $\text{Open}_{\text{Bid}} \to \text{Close}_{\text{Bid}}$ represents a theoretical, friction-free mid/bid benchmark. In physical execution:
- **Long EURUSD Trade ($d_i = +1$)**:
  - Enters at **Ask**: $P_{\text{entry, exec}} = \text{Open}_{\text{Bid}} + \text{Spread}_{\text{entry}}$
  - Exits at **Bid**: $P_{\text{exit, exec}} = \text{Close}_{\text{Bid}}$
  - Return: $\ln(P_{\text{exit, exec}} / P_{\text{entry, exec}}) \approx \ln(\text{Close}_{\text{Bid}} / \text{Open}_{\text{Bid}}) - \frac{\text{Spread}_{\text{entry}}}{P}$
- **Short EURUSD Trade ($d_i = -1$)**:
  - Enters at **Bid**: $P_{\text{entry, exec}} = \text{Open}_{\text{Bid}}$
  - Exits at **Ask**: $P_{\text{exit, exec}} = \text{Close}_{\text{Bid}} + \text{Spread}_{\text{exit}}$
  - Return: $-\ln(P_{\text{exit, exec}} / P_{\text{entry, exec}}) \approx -\ln(\text{Close}_{\text{Bid}} / \text{Open}_{\text{Bid}}) - \frac{\text{Spread}_{\text{exit}}}{P}$

**Execution Friction Mandate**:
- On EURUSD, typical retail/institutional spreads range from **0.5 to 1.5 pips**.
- A nominal gross drift hurdle of **1.0 pip is completely wiped out by spread drag**.
- *Protocol Rule*: Gross drift $\bar{\Delta}_{\text{pips}} \ge 1.0\text{ pip}$ is **REJECTED** as evidence of net profitability. The candidate must demonstrate net executable return after modeling realistic spread friction (or satisfy an unadjusted gross drift hurdle of at least $\bar{\Delta}_{\text{pips}} \ge 2.0\text{ pips}$).

### 4.4 Weekend Handling & Reconciled Sample Attrition
Among the **49 strict-agreement packages**:
- Exactly **15 packages (30.6%) are Friday releases**.
- For 6 H4, all 15 Friday packages cross the Friday 23:00 to Sunday 23:00 market closure, spanning **72 wall-clock hours** (exiting Monday).
- **Option A (Retain with Matched Weekend Exposure - Recommended)**: Preserves the full $N = 49$ sample.
- **Option B (Exclude Friday Releases)**: Eliminates weekend gap risk, but removes 15 packages, reducing the sample to **$N = 34$ packages** ($49 - 15 = 34$).

---

## 5. Statistical Framework & Control Availability Ledger

### 5.1 Price-Blind Control Availability Ledger (Verified Audit)
The matched calendar control architecture ($T_{\text{entry}} - 7\text{ days}$ or $T_{\text{entry}} - 14\text{ days}$) was audited against the pinned calendar releases for high-impact USD and EUR macroeconomic releases:

| Control Window | Clean of High-Impact USD/EUR Releases | Contaminated by High-Impact Releases | Contamination Share |
|---|---:|---:|---:|
| **$T - 7\text{ days}$ Control** | **14 / 49** | 35 / 49 | **71.4% Contaminated** |
| **$T - 14\text{ days}$ Control** | **5 / 49** | 44 / 49 | **89.8% Contaminated** |
| **At Least One Clean ($T - 7\text{d} \lor T - 14\text{d}$)** | **17 / 49** | 32 / 49 | **65.3% Contaminated in BOTH** |

**Forensic Finding**:
In **32 of the 49 strict-agreement packages (65.3%)**, BOTH the $T - 7\text{d}$ and $T - 14\text{d}$ control windows are contaminated by major high-impact macro releases (including NFP, CPI, PPI, ISM PMI, Fed Interest Rate Decisions, and ECB press conferences).
- *Downstream Trap*: Subtracting a contaminated control return $R_{\text{ctrl}, i}$ injects exogenous macro shocks from unrelated events into the excess return $\Delta R_i = R_{\text{event}, i} - R_{\text{ctrl}, i}$.
- *Architectural Decision for Director*:
  - **Control Choice A (Direct Event Return Permutation - Recommended)**: Test $H_0: \mathbb{E}[R_{\text{event}}] \le 0$ directly using directional sign-flip permutations ($d_i \in \{-1, +1\}$), avoiding synthetic control contamination entirely ($N = 49$).
  - **Control Choice B (Contaminated Calendar Controls)**: Use $T - 7\text{d}$ / $T - 14\text{d}$ excess returns, accepting that the control absorbs non-announcement macro variance.
  - **Control Choice C (Strict Clean Control Filtering)**: Enforce clean controls, causing catastrophic sample collapse to **$N = 17$ packages**.

### 5.2 Test Statistic & Permutation Scheme
- Directional Event Return:
  $$R_{\text{event}, i} = d_i \cdot \ln\left(\frac{P_{\text{exit}, i}}{P_{\text{entry}, i}}\right)$$
- If paired control is used:
  $$\Delta R_i = R_{\text{event}, i} - R_{\text{ctrl}, i}$$
- Sample Mean:
  $$\bar{R} = \frac{1}{N} \sum_{i=1}^N R_i$$

### 5.3 Paired Sign-Flip Assumptions & Robustness Fallbacks
A paired sign-flip permutation test permutes the directional assignments under $H_0$:
$$R_i^* = \epsilon_i \cdot R_i, \quad \epsilon_i \in \{-1, +1\} \text{ with equal probability } 0.5$$
- **Underlying Theoretical Assumptions**:
  1. **Exchangeability under $H_0$**: Under the null hypothesis of no announcement effect, the sign of the return is exchangeable ($\mathbb{P}(R_i) = \mathbb{P}(-R_i)$).
  2. **Distribution Symmetry**: Returns are assumed symmetric around zero under $H_0$.
- **Downstream Hazards**: Financial returns exhibit fat tails, volatility clustering, and macroeconomic drift skew that can violate strict symmetry.
- **Mandatory Fallback Diagnostics**:
  1. **Wilcoxon Signed-Rank Test**: Non-parametric test evaluating median directional shift without normality assumptions.
  2. **Student's Paired t-Test**: Standard parametric test for benchmark comparison.
  3. **Stationary Block Bootstrap**: Preserves temporal autocorrelation and heteroskedasticity structure.
  *Failure Rule*: If the sign-flip permutation rejects $H_0$ but fallback tests fail ($p \ge 0.05$), the candidate must be declared **distributionally fragile**.

### 5.4 Decision Gate Hierarchy (Primary 6 H4 Horizon)
- **Step 1 (Inconclusive / Negative Drift)**: If permutation $p \ge 0.10$ OR $\bar{R} \le 0$, immediately declare **State 3: No Convincing Evidence**. Hard stop.
- **Step 2 (Borderline / Economically Fragile)**: If $p \ge 0.05$ OR event mean gross drift $\bar{\Delta}_{\text{pips}} < 2.0\text{ pips}$ (insufficient to clear spread friction) OR win rate $< 55\%$, conclude fragile anomaly.
- **Step 3 (Plausible Anomaly)**: Requires Holm-Bonferroni adjusted $p < 0.025$, $\bar{\Delta}_{\text{pips}} \ge 2.0\text{ pips}$ gross, positive net return after spread deduction, and win rate $\ge 55\%$.

---

## 6. Pre-Declared Attribution & Confounder Covariates

To address the severe downstream hazards documented in [`docs/RETAIL_SALES_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FEASIBILITY.md), the following interaction covariates are pre-registered:
1. **Canadian Macro Collision Indicator ($I_{\text{CAD}} \in \{0, 1\}$)**:
   - 61.2% of strict packages (30 of 49) collide with simultaneous Canadian releases. Sub-group analysis must report performance partitioned by $I_{\text{CAD}}$.
2. **Same-Timestamp Bundle Size ($N_{\text{bundle}}$)**:
   - Mean of 12.2 series released simultaneously (including Import Price Index, Export Price Index, NY Empire State Manufacturing).
3. **Subsequent Macro Event Overlap Count ($K_{\text{later}}$)**:
   - Evaluates whether drift attenuates or compounds in episodes with high vs low subsequent event counts (Median 10 events over 6 H4).
*Attribution Mandate*: The research deliverable must report all bundled and subsequent covariates. The team is strictly forbidden from claiming sole causality of EURUSD price movements to retail sales.

---

## 7. Reconciled Open Design Decisions for Codex Steering

All sample-size cells below are reconciled directly from the package ledger against the **$N = 49$ strict-agreement packages**:

| Decision | Option A (Preserve Sample) | Option B (Filter / Exclude) | Option C (Alternative) | Strategic Trade-Off & Reconciled Impact |
|---|---|---|---|---|
| **1. Co-Release Rule** | **Strict Concordance ($N = 49$)**<br>(27 POS / 22 NEG) | Non-Conflicting ($N = 51$)<br>(adds 2 Headline POS/Core ZERO) | Unfiltered Headline ($N = 63$)<br>(ignores Core surprise) | Signal cleanliness vs sample size.<br>Strict agreement is cleanest transmission test. |
| **2. Weekend Exposure** | **Retain Full Sample ($N = 49$)**<br>(includes 15 Friday releases, 72h exposure) | Discard Friday Releases (**$N = 34$**)<br>(leaves $49 - 15 = 34$ packages) | — | Power vs weekend gap carry risk.<br>Discarding Fridays removes 30.6% of data. |
| **3. Pre-Entry Lookback** | **Omit Lookback ($N = 49$)**<br>(pure forward return question) | Strict Same-Week Lookback (**$N = 37$**)<br>(fails 12 Mon/Tue releases; $49 - 12 = 37$) | — | Unnecessary 14-H4 lookback penalizes Monday/Tuesday releases for prior weekend gap. |
| **4. CAD Collisions** | **Stratify as Covariate ($N = 49$)**<br>(report $I_{\text{CAD}} = 0$ vs $1$) | Exclude Collisions (**$N = 19$**)<br>(removes 30 collisions; $49 - 30 = 19$) | — | Attribution purity vs severe sample collapse.<br>Excluding CAD leaves only 19 trades. |
| **5. Control Architecture** | **Direct Event Return ($N = 49$)**<br>(test $H_0: \mathbb{E}[R_{\text{event}}] \le 0$) | Contaminated Calendar Control ($N = 49$)<br>($T-7\text{d}$ / $T-14\text{d}$, 65.3% contaminated) | Clean Calendar Control Only (**$N = 17$**)<br>(drops 32 contaminated controls) | Avoiding control contamination vs paired excess return benchmark. |
| **6. Combined Strict Filter** | — | **Impose All Exclusions ($N = 6$)**<br>(Non-Fri + Lookback + Zero Collision) | — | **Sample Destruction**: Imposing all filters destroys the sample ($N = 6$). |

---

## 8. Audit Checklist & Mandatory Stop

- [x] Pinned raw calendar hash verified (`76062b8f...`)
- [x] Pinned EURUSD H1 candle hash verified (`893aa193...`)
- [x] Package deduplication and sign contingency verified ($N=96, N_{\text{AFP}}=68, N_{\text{strict}}=49$)
- [x] Strict subsample attrition cells verified ($49 \to 34$ Friday, $49 \to 37$ lookback, $49 \to 19$ collision, $N = 6$ combined)
- [x] German Ifo benchmark reconciled (6/40 weekend crossings, CESifo 3-series bundle)
- [x] Control window availability audited (65.3% contaminated in both 7d/14d)
- [x] Price blindness strictly preserved (zero price reads, field-0 substring extraction only)
- [ ] Codex Quant Director audit & approval of unresolved design choices
- [ ] Formal protocol freeze before price exploration
