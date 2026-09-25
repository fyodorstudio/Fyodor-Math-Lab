# US Retail Sales EURUSD Research Protocol (Draft Protocol v0.1)

> [!CAUTION]
> **PROTOCOL STATUS: DRAFT FOR REVIEW (DO NOT EXECUTE)**  
> This protocol is a **pre-price research design proposal** submitted for Codex review.  
> **Strict Halt**: No candidate candle prices, returns, winning trades, or directional paths may be read, parsed, or computed under this protocol until formally reviewed and frozen by Codex.  
> Chronological Split Boundary: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).  
> All observations on or after `1672531200` remain sealed.

---

## 1. Candidate Research Question & Hypothesis

> *Does an unexpected consensus surprise in US consumer retail demand (Retail Sales m/m + Core Retail Sales m/m) produce statistically significant, persistent post-announcement drift on EURUSD across the first (6 H4 / 24 active hours) or second (12 H4 / 48 active hours) trading day, or is the macroeconomic information immediately absorbed during the announcement bar?*

### Economic Transmission Rationale
- **Consumer Demand & Monetary Policy**: Personal consumption accounts for ~70% of US GDP. US Retail Sales is the earliest monthly hard data on goods consumption. A positive retail sales surprise indicates robust consumer demand, upward pressure on terminal interest rates, and higher Treasury yields, implying USD appreciation (**Short EURUSD**, $d = -1$).
- **Delayed Drift Hypothesis**: If institutional portfolio rebalancing and systematic fixed-income duration adjustments take multiple trading sessions to clear, EURUSD may experience multi-session post-announcement drift.
- **Null Hypothesis ($H_0$)**: Post-announcement excess log return $\Delta R = 0$. Immediate repricing within the announcement bar absorbs all informational content; delayed drift does not exceed matched non-announcement drift.

---

## 2. Exact Series Identification & Data Provenance

### 2.1 Pinned Identifiers
- **Primary Headline Series**:
  - Key: `USD:US:840020010:r0`
  - Name: `Retail Sales m/m` (`event_id = 840020010`, `revision = 0`, Census Bureau)
- **Co-Released Core Series**:
  - Key: `USD:US:840020011:r0`
  - Name: `Core Retail Sales m/m` (`event_id = 840020011`, `revision = 0`, Census Bureau)
- **Tradable Instrument**: **`EURUSD`** (PERIOD_H1 trade-server time).

### 2.2 Directional Mapping
Because EURUSD is quoted as EUR (Base) / USD (Quote):
- **Bullish US Economy (Hawkish Shock)**:
  - Headline POS ($S_H > 0$) & Core POS ($S_C > 0$) $\implies$ **Short EURUSD** ($d_i = -1$).
- **Bearish US Economy (Dovish Shock)**:
  - Headline NEG ($S_H < 0$) & Core NEG ($S_C < 0$) $\implies$ **Long EURUSD** ($d_i = +1$).

### 2.3 Cryptographic Source Provenance Hashes
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

### 3.2 Actionable Co-Release Rule Options (Open Design Decision)
- **Policy Option A (Strict Sign Agreement - Recommended)**:
  $$\text{sign}(S_H) \times \text{sign}(S_C) > 0$$
  Requires both headline and core to surprise in the identical direction.
  - POS/POS (Short EURUSD): **27 packages**
  - NEG/NEG (Long EURUSD): **22 packages** (or 19 if strict intra-week pre-lookback enforced)
  - Actionable Sample: **$N = 49$** (or $N = 46$).
- **Policy Option B (Primary + Non-Conflicting Confirmation)**:
  $$\text{sign}(S_H) \ne 0 \quad \land \quad \text{sign}(S_H) \times \text{sign}(S_C) \ge 0$$
  Admits cases where Core surprise is zero ($S_C = 0$) but Headline is directional.
  - Adds 2 packages (Headline POS / Core ZERO).
  - Actionable Sample: **$N = 51$** (or $N = 48$).

### 3.3 Excluded Categories
1. **Active Sign Conflict ($\text{sign}(S_H) \times \text{sign}(S_C) < 0$)**: Exactly **9 packages** (5 POS/NEG, 4 NEG/POS). Excluded due to internally conflicting macroeconomic signals.
2. **Missing Consensus Forecast**: Exactly **28 packages** (2015 to April 2017). Excluded because market expectation cannot be computed from MT5 provider data.
3. **Double Zero Surprise ($S_H = 0 \land S_C = 0$)**: Exactly **2 packages**. Excluded due to absence of economic shock.

---

## 4. Execution Timing & Horizon Definitions

### 4.1 Entry Rule
- Entry occurs at the **Open of the first completed H4 bar following release**:
  - `15:30:00` release $\to T_{\text{entry}} = \mathbf{16:00:00}$ (30-minute delay).
  - `16:30:00` release $\to T_{\text{entry}} = \mathbf{20:00:00}$ (210-minute / 3.5-hour delay).
- Entry Price Proxy: $P_{\text{entry}} = \text{Open}_{\text{Bid}}(T_{\text{entry}})$.

### 4.2 Primary & Secondary Holding Horizons
- **Primary Horizon**: **6 H4 blocks (24 active trading hours / 1st trading day)**.
  - Exit Price Proxy: $P_{\text{exit}} = \text{Close}_{\text{Bid}}(B_5)$.
- **Secondary Horizon**: **12 H4 blocks (48 active trading hours / 2nd trading day)**.
  - Exit Price Proxy: $P_{\text{exit}} = \text{Close}_{\text{Bid}}(B_{11})$.

### 4.3 Weekend Handling
- FX market closes Friday 24:00 (or broker close) and reopens Sunday 00:00 (approx 48h gap).
- Friday releases (22 complete AFP packages) cross the weekend closure:
  - 6 H4 horizon spans **72 wall-clock hours** (exits Monday 16:00/20:00).
  - 12 H4 horizon spans **96 wall-clock hours** (exits Tuesday 16:00/20:00).
- Non-announcement matched controls must replicate the exact weekend duration and entry session.

---

## 5. Statistical Framework & Multiplicity Control

### 5.1 Matched Control Architecture
For each event episode $i$, an unconfounded price-blind control episode is selected:
- **Session Matching**: Identical broker entry hour (16:00 or 20:00) and day of week.
- **Calendar Offset**: Prior non-announcement week ($T_{\text{entry}} - 7\text{ days}$ or $T_{\text{entry}} - 14\text{ days}$).
- **Exclusion**: Control window must not contain major high-impact USD or EUR releases.

### 5.2 Test Statistic & Permutation Scheme
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
- **Family-Wise Error Rate Control**: Holm-Bonferroni step-down adjustment across the 2 testing horizons (6 H4 and 12 H4) at family $\alpha = 0.05$.

### 5.3 Formal Decision Gate Hierarchy
- **Step 1 (Inconclusive / Negative Drift)**: If permutation $p \ge 0.10$ OR $\Delta \bar{R} \le 0$, immediately declare **State 3: No Convincing Evidence**. Hard stop.
- **Step 2 (Borderline / Economically Fragile)**: If $p \ge 0.05$ OR event mean gross drift $\bar{\Delta}_{\text{pips}} < 1.0\text{ pip}$ OR win rate $< 55\%$, conclude fragile anomaly.
- **Step 3 (Plausible Anomaly)**: Requires Holm-Bonferroni adjusted $p < 0.05$, $\bar{\Delta}_{\text{pips}} \ge 1.0$, and win rate $\ge 55\%$.

---

## 6. Pre-Declared Attribution & Confounder Covariates

To address the severe downstream hazards documented in [`docs/RETAIL_SALES_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FEASIBILITY.md), the following interaction covariates are pre-registered:
1. **Canadian Macro Collision Indicator ($I_{\text{CAD}} \in \{0, 1\}$)**:
   - 57.4% of packages collide with Canadian 08:30 ET releases. Sub-group analysis must report performance partitioned by $I_{\text{CAD}}$.
2. **Subsequent Macro Event Overlap Count ($K_{\text{later}}$)**:
   - Evaluates whether drift attenuates or compounds in episodes with high vs low subsequent event counts.

---

## 7. Audit Checklist & Mandatory Stop

- [x] Pinned raw calendar hash verified (`76062b8f...`)
- [x] Pinned EURUSD H1 candle hash verified (`893aa193...`)
- [x] Package deduplication and sign contingency verified ($N=96, N_{\text{AFP}}=68$)
- [x] Price blindness strictly preserved (zero price reads)
- [ ] Codex Quant Director audit & approval
- [ ] Formal protocol freeze before price exploration
