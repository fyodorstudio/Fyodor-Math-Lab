# US Retail Sales EURUSD Research Protocol (Draft Proposal v0.2)

> [!CAUTION]
> **PROTOCOL STATUS: UNFROZEN PROPOSAL REQUIRING CODEX REVIEW & APPROVAL (DO NOT EXECUTE)**  
> This document is a **draft pre-price research specification**.  
> All control matching algorithms, exclusion rules, statistical decision gates, directional mappings, and cost proxies are **PROPOSALS FOR REVIEW**, not approved or frozen facts.  
> **Strict Halt**: No candidate candle prices, returns, winning trades, or directional paths may be read, parsed, or computed under this protocol until formally audited, reconciled, and frozen by Codex.  
> Chronological Split Boundary: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).  
> All post-2022 observations remain sealed.

---

## 1. Candidate Research Question & Hypothesis (Proposed)

> *Does an unexpected consensus surprise in US consumer retail demand (Retail Sales m/m + Core Retail Sales m/m) produce statistically significant, persistent post-announcement drift on EURUSD across the first (6 H4 / 24 active hours) or second (12 H4 / 48 active hours) trading day, or is the macroeconomic information immediately absorbed during the announcement bar?*

### Economic Transmission Rationale (Proposed)
- **Consumer Demand & Monetary Policy**: Personal consumption accounts for ~70% of US GDP. US Retail Sales is the earliest monthly hard data on goods consumption. A positive retail sales surprise indicates robust consumer demand, upward pressure on terminal interest rates, and higher Treasury yields, implying USD appreciation (**Short EURUSD**, $d = -1$).
- **Delayed Drift Hypothesis**: If institutional portfolio rebalancing and systematic fixed-income duration adjustments take multiple trading sessions to clear, EURUSD may experience multi-session post-announcement drift.
- **Null Hypothesis ($H_0$)**: Post-announcement excess log return $\Delta R = 0$. Immediate repricing within the announcement bar absorbs all informational content; delayed drift does not exceed matched non-announcement drift.

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

### 3.3 Excluded Categories
1. **Active Sign Conflict ($\text{sign}(S_H) \times \text{sign}(S_C) < 0$)**: Exactly **9 packages** (5 POS/NEG, 4 NEG/POS).
2. **Missing Consensus Forecast**: Exactly **28 packages** (2015 to April 2017).
3. **Double Zero Surprise ($S_H = 0 \land S_C = 0$)**: Exactly **2 packages**.

---

## 4. Execution Timing & Horizon Definitions

### 4.1 Temporal Entry Rule (Proposed Specification)
Entry occurs at the **Open of the next active H4 bar** immediately following completion of the announcement bar window:
- `15:30:00` release: Announcement H4 window (`12:00:00`–`16:00:00`) completes at `16:00:00`.
  - Entry occurs at the **Open of the 16:00:00 H4 bar** ($T_{\text{entry}} = \mathbf{16:00:00}$, **30-minute delay**; 47 of 68 AFP packages).
- `16:30:00` release: Announcement H4 window (`16:00:00`–`20:00:00`) completes at `20:00:00`.
  - Entry occurs at the **Open of the 20:00:00 H4 bar** ($T_{\text{entry}} = \mathbf{20:00:00}$, **210-minute / 3.5-hour delay**; 21 of 68 AFP packages).
- Entry Price Proxy: $P_{\text{entry}} = \text{Open}_{\text{Bid}}(T_{\text{entry}})$.

### 4.2 Primary & Secondary Holding Horizons (Proposed Specification)
- **Primary Horizon**: **6 completed active H4 blocks (24 active hours / 1st trading day)**.
  - Blocks: $B_0, B_1, B_2, B_3, B_4, B_5$.
  - Exit Price Proxy: $P_{\text{exit}} = \text{Close}_{\text{Bid}}(B_5)$.
- **Secondary Horizon**: **12 completed active H4 blocks (48 active hours / 2nd trading day)**.
  - Blocks: $B_0, \dots, B_{11}$.
  - Exit Price Proxy: $P_{\text{exit}} = \text{Close}_{\text{Bid}}(B_{11})$.

### 4.3 Weekend Handling & Exposure (Unresolved Design Decision)
- Friday releases (22 complete AFP packages) cross the weekend market closure:
  - 6 H4 horizon spans **72 wall-clock hours** (exits Monday 16:00/20:00).
  - 12 H4 horizon spans **96 wall-clock hours** (exits Tuesday 16:00/20:00).
- Thursday releases (13 complete AFP packages):
  - 6 H4 exits Friday afternoon (no weekend).
  - 12 H4 spans **96 wall-clock hours** (crosses weekend to Monday).
- **Option A (Retain with Matched Weekend Controls - Recommended)**: Preserve full sample ($N = 49$), matching Friday releases against non-announcement Friday control sessions with identical 72-hour exposure.
- **Option B (Exclude Friday Releases)**: Eliminate weekend carry risk, but discard 22 packages, reducing actionable sample to **$N \le 27$** (statistically underpowered).

---

## 5. Statistical Framework & Multiplicity Control (Proposed)

### 5.1 Matched Control Architecture (Proposal Requiring Review)
For each event episode $i$, an unconfounded price-blind control episode is selected:
- **Session Matching**: Identical broker entry hour (16:00 or 20:00) and day of week.
- **Calendar Offset**: Prior non-announcement week ($T_{\text{entry}} - 7\text{ days}$ or $T_{\text{entry}} - 14\text{ days}$).
- **Exclusion**: Control window must not contain major high-impact USD or EUR releases.

### 5.2 Test Statistic & Permutation Scheme (Proposal Requiring Review)
- Directional Log Return:
  $$R_{\text{event}, i} = d_i \cdot \ln\left(\frac{P_{\text{exit}, i}}{P_{\text{entry}, i}}\right)$$
  $$R_{\text{ctrl}, i} = d_i \cdot \ln\left(\frac{P_{\text{exit, ctrl}, i}}{P_{\text{entry, ctrl}, i}}\right)$$
- Paired Excess Log Return:
  $$\Delta R_i = R_{\text{event}, i} - R_{\text{ctrl}, i}$$
- Sample Mean Paired Excess Return:
  $$\Delta \bar{R} = \frac{1}{N} \sum_{i=1}^N \Delta R_i$$
- **Hypothesis Test**: 1-sided paired permutation test:
  $$H_0: \mathbb{E}[\Delta R] \le 0 \quad \text{vs} \quad H_1: \mathbb{E}[\Delta R] > 0$$
- **Permutation Engine**: Seeded Mulberry32 PRNG (seed pinned to `20260925`), $B = 100,000$ paired sign-flip permutations.
- **Multiplicity Control**: Holm-Bonferroni step-down adjustment across the 2 testing horizons (6 H4 and 12 H4) at family $\alpha = 0.05$.

### 5.3 Formal Decision Gate Hierarchy (Proposal Requiring Review)
- **Step 1 (Inconclusive / Negative Drift)**: If permutation $p \ge 0.10$ OR $\Delta \bar{R} \le 0$, immediately declare **State 3: No Convincing Evidence**. Hard stop.
- **Step 2 (Borderline / Economically Fragile)**: If $p \ge 0.05$ OR event mean gross drift $\bar{\Delta}_{\text{pips}} < 1.0\text{ pip}$ OR win rate $< 55\%$, conclude fragile anomaly.
- **Step 3 (Plausible Anomaly)**: Requires Holm-Bonferroni adjusted $p < 0.05$, $\bar{\Delta}_{\text{pips}} \ge 1.0$, and win rate $\ge 55\%$.

---

## 6. Pre-Declared Attribution & Confounder Covariates (Proposed)

To address the severe downstream hazards documented in [`docs/RETAIL_SALES_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FEASIBILITY.md), the following interaction covariates are proposed for pre-registration:
1. **Canadian Macro Collision Indicator ($I_{\text{CAD}} \in \{0, 1\}$)**:
   - 57.4% of packages collide with Canadian 08:30 ET releases. Sub-group analysis must report performance partitioned by $I_{\text{CAD}}$.
2. **Subsequent Macro Event Overlap Count ($K_{\text{later}}$)**:
   - Evaluates whether drift attenuates or compounds in episodes with high vs low subsequent event counts.

---

## 7. Open Design Decisions for Codex Steering

| Decision | Option A | Option B | Option C | Strategic Trade-Off |
|---|---|---|---|---|
| **1. Co-Release Rule** | Strict Concordance ($N=49$) | Non-Conflicting ($N=51$) | Unfiltered Headline ($N=63$) | Signal cleanliness vs sample size |
| **2. Weekend Exposure** | Retain with 72h controls ($N=49$) | Discard Friday releases ($N=27$) | — | Power vs weekend carry risk |
| **3. Pre-Entry Lookback** | Omit (return-only, $N=49$) | Bridge weekend ($N=46$) | Strict same-week ($N=33$) | Unnecessary lookback cuts Mon/Tue |
| **4. CAD Collisions** | Covariate stratification ($N=49$) | Exclude CAD collisions ($N=20$) | — | Attribution control vs sample viability |

---

## 8. Audit Checklist & Mandatory Stop

- [x] Pinned raw calendar hash verified (`76062b8f...`)
- [x] Pinned EURUSD H1 candle hash verified (`893aa193...`)
- [x] Package deduplication and sign contingency verified ($N=96, N_{\text{AFP}}=68$)
- [x] Price blindness strictly preserved (zero price reads)
- [ ] Codex Quant Director audit & approval of unresolved design choices
- [ ] Formal protocol freeze before price exploration
