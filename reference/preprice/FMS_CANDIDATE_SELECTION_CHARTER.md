# FMS Candidate-Selection Charter: Data Eligibility & Economic Reasoning

**Document Status**: RESEARCH PLANNING DELIVERABLE (MILESTONE 2 - CODEX CONTINGENCY AUDIT REVISED)  
**Deliverable Type**: Candidate-Selection Charter (Pre-Price, Pre-Backtest, Timestamp & Economic Governance)  
**Research Stance**: Strict Non-Discovery, Zero Return Calculation, Zero Recipe Ranking, Zero Strategy Backtest  
**Research Director & Auditor**: Codex  
**Implementation & Analysis Workhorse**: Antigravity  
**Chronological Split Boundary**: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`)  
**Data Provenance**: Verified against `lab/research/fms_eligibility_inventory.json`, `fms_episodes.jsonl`, and pinned export `tools/mt5/FyodorResearchExport_v3_20260923_234930_server`  

---

## 1. Executive Mandate & Charter Purpose

This document fulfills the second milestone of the FMS research roadmap ([`docs/FMS_RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/GEMINI/docs/FMS_RESEARCH_ROADMAP.md)). It establishes a candidate-selection charter based exclusively on:
1. **Physical data eligibility** and provenance established in the pre-2023 timestamp-only inventory ([`lab/research/FMS_ELIGIBILITY_INVENTORY.md`](file:///c:/dev/Fyodor%20Math%20Lab/GEMINI/lab/research/FMS_ELIGIBILITY_INVENTORY.md)).
2. **First-principles economic transmission mechanisms** across foreign exchange spot markets.
3. **Execution feasibility and calendar collision realities** on trade-server time.

### Operational Boundaries
- **Zero Candidate Price Outcomes**: No candle OHLC, tick volumes, spreads, price returns, directional drift, MFE/MAE, stops/targets, or win rates were read, parsed, or computed for any candidate setup. The repository test suite includes existing legacy candle-data tests (e.g., verifying timestamp gap diagnostics, CSV reader regressions, and Phase 1 test fixtures), but candidate price series remained strictly uninspected for research outcomes.
- **Pre-2023 Sealing**: All releases and candidate price paths on or after `2023-01-01 00:00:00` remain strictly sealed.
- **Zero Historical Return Ranking**: Candidates are proposed based on data completeness and economic plausibility, never on historical return curves or deprecated FMS v1 backtest performance.
- **Candidate Questions, Not Winning Setups**: This charter defines falsifiable empirical *questions* to be formally pre-registered in Milestone 3, not optimized recipes.

---

## 2. Proposed Research Candidates

We propose **three genuinely distinct candidate research questions**. They span different macroeconomic families (Housing/Construction leading indicators, Forward-looking Business Surveys, and Labor/Wage inflation), different currency regimes (USD, EUR, GBP), and different post-announcement holding horizons.

---

### Candidate 1: Real-Economy Interest-Rate Transmission (US Housing Construction: Building Permits & Housing Starts on EURUSD)

#### 1. Core Research Question
> *Does a consensus surprise in US residential construction demand (Building Permits / Housing Starts) produce persistent directional drift on EURUSD across the first and second trading days (6 H4 / 12 H4), or does immediate market repricing absorb the shock within the announcement bar?*

#### 2. Series Identification & Predeclared Co-Release Rule
- **Exact Primary Series**:
  - `USD:US:840020005:r0` — Building Permits (Monthly, US Census Bureau, `event_id = 840020005`, `revision = 0`).
- **Exact Co-Released Series**:
  - `USD:US:840020004:r0` — Housing Starts (Monthly, US Census Bureau, `event_id = 840020004`, `revision = 0`).
- **Economic Hierarchy & Conflict Handling**:
  - Building Permits are the upstream regulatory authorization that legally precedes construction activity; Housing Starts represent physical groundbreaking.
  - *Chosen Coherence Rule*: **Primary + Non-Conflicting Confirmation**. Building Permits surprise ($S_P = A - F$) determines the trade direction. Housing Starts surprise ($S_S = A - F$) must not contradict Permits direction ($\text{sign}(S_P) \times \text{sign}(S_S) \ge 0$). Episodes where Starts actively contradict Permits direction ($\text{sign}(S_P) \times \text{sign}(S_S) < 0$) are filtered out prior to price evaluation.
  - *Cross-Currency Collisions*: 69 of the 96 packages (71.9%) coincide with simultaneous Canadian macroeconomic releases (e.g., Canadian manufacturing sales co-released at 08:30 ET). Collisions are tracked as an explicit interaction covariate.

#### 3. Full Sign-Pair Contingency Table (Before Exclusions)
Joined directly from `calendar_releases.csv` against all clean EURUSD holding episodes in `fms_episodes.jsonl`:

**Primary Horizon: 6 H4 (Clean Paths = 93, Unfiltered Upper Bound = 66)**

| Permits ($S_P$) \ Starts ($S_S$) | Starts POS | Starts NEG | Starts ZERO | Starts MISSING | Total |
|---|---|---|---|---|---|
| **Permits POS** | 21 | 14 | 0 | 0 | **35** |
| **Permits NEG** | 9 | 22 | 0 | 0 | **31** |
| **Permits ZERO** | 0 | 0 | 0 | 0 | **0** |
| **Permits MISSING** | 0 | 0 | 0 | 27 | **27** |
| **Total** | **30** | **36** | **0** | **27** | **93** |

- **Unfiltered Upper Bound** (Primary Complete AFP on Clean 6 H4): **66 episodes** (35 POS + 31 NEG).
- **Actionable Non-Conflicting Count**: **43 episodes** (21 POS/POS + 22 NEG/NEG). Note: Because Starts ZERO = 0, Strict Agreement and Non-Conflicting Confirmation yield the exact same 43 episodes.
- **Conflicting Count**: **23 episodes** (14 POS/NEG + 9 NEG/POS).
- **Neutral Primary Cases** ($S_P = 0$): **0 episodes**.
- **Missing Consensus**: **27 episodes** (both series lack consensus forecasts in 2015–2016 MT5 calendar).

#### 4. Recomputed Counts Across All Evaluated Horizons

| Horizon | Total Clean Paths | Unfiltered Upper Bound | Actionable Non-Conflicting ($N$) | Conflicting Excluded | Permits Zero | Missing Forecast |
|---|---|---|---|---|---|---|
| **6 H4 (1st Trading Day)** | 93 | **66** | **43** (21 POS, 22 NEG) | 23 | 0 | 27 |
| **12 H4 (2nd Trading Day)** | 91 | **65** | **43** (21 POS, 22 NEG) | 22 | 0 | 26 |
| **30 H4 (5 Trading Days)** | 84 | **60** | **41** (20 POS, 21 NEG) | 19 | 0 | 24 |
| **42 H4 (7 Trading Days)** | 80 | **57** | **39** (18 POS, 21 NEG) | 18 | 0 | 23 |
| **60 H4 (10 Trading Days)** | 76 | **54** | **36** (18 POS, 18 NEG) | 18 | 0 | 22 |

#### 5. Physical Execution Timing & Session Realities
- **Release Clock Times**: 64 packages released at `15:30:00` broker time $\to T_{\text{entry}} = \mathbf{16:00:00}$ (30-minute delay); 32 packages released at `16:30:00` broker time (due to US/EU Daylight Saving Time shifts) $\to T_{\text{entry}} = \mathbf{20:00:00}$ (210-minute / 3.5-hour delay).
- **Weekday & Session Duration**: Tuesday (35), Wednesday (28), Thursday (20), Friday (13). Entries on Tuesday at 16:00 close 6 H4 at Wednesday 16:00 (24 wall-clock hours). The 13 Friday entries span the weekend closure, closing on Monday at 16:00/20:00 (**72 wall-clock hours**).
- **Matched Control Rule**: Dynamic session-matching to the exact entry broker hour (16:00 or 20:00), day of week, and market session state on non-announcement weeks.

#### 6. Later-Release Overlap & Attribution Concern
- Across the $N = 66$ clean 6 H4 episodes, paths encounter a Median of **21 release rows** [IQR: 14–30] across Median = **7 packages** [IQR: 5–9].
- At 60 H4 ($N = 54$), paths encounter a Median of **264 release rows** across Median = **97 packages**.
- *Attribution Governance*: Exposure to compounding subsequent macro packages is retained as an architectural concern and open question for protocol pre-registration (see Section 4).

#### 7. Revision Provenance Disclosure
- In MT5 `calendar_releases.csv`, `revision = 0` identifies a provider revision-stage field relative to the reporting period, **not a cryptographically verified point-in-time first-seen snapshot**. The retrospective export cannot prove live consensus availability at the release millisecond.

#### 8. Prior Exploration Disclosure
- *Phase 1 Overlap*: Zero overlap (Phase 1 evaluated USD CPI, NFP, Core PCE).
- *Historical FMS v1 Overlap*: Present (`s41`, `s42` on 60 H4). Must be treated as reused historical data requiring prospective validation.

---

### Candidate 2: Forward-Looking Business Sentiment & Capital Allocation (German Ifo Business Climate on EURUSD)

#### 1. Core Research Question
> *Does a consensus surprise in German business sentiment (Ifo Business Expectations / Business Climate) generate persistent multi-session trend continuation on EURUSD over the first trading day (6 H4), reflecting institutional equity and fixed-income capital rebalancing?*

#### 2. Series Identification & Predeclared Co-Release Rule Choice
- **Exact Primary Series**:
  - `EUR:DE:276030003:r0` — Ifo Business Climate (Monthly, Ifo Institute, `event_id = 276030003`, `revision = 0`).
- **Exact Co-Released Series**:
  - `EUR:DE:276030001:r0` — Ifo Business Expectations (`event_id = 276030001`, `revision = 0`).
  - `EUR:DE:276030002:r0` — Ifo Current Assessment (`event_id = 276030002`, `revision = 0`).
- **Co-Release Rule Decision & Justification**:
  - *Candidate Rule 1 (Strict Agreement)*: Requires same-sign nonzero surprises ($\text{sign}(S_C) \times \text{sign}(S_E) > 0$).
  - *Candidate Rule 2 (Non-Conflicting Confirmation)*: Requires $\text{sign}(S_C) \ne 0$ and $\text{sign}(S_E) \in \{\text{sign}(S_C), 0\}$.
  - **Chosen Rule**: **Strict Directional Agreement ($N = 40$)**.
  - *Explicit Justification*: When Business Expectations surprise is zero ($S_E = 0$), forward expectations provide zero confirmation of the headline print, leaving open whether the shock is driven by backward-looking current conditions. Requiring strict sign concordance ensures that both the headline benchmark and its forward-looking component confirm the macroeconomic shift in the same direction. (We explicitly document the single $S_E = 0$ case below).

#### 3. Full Sign-Pair Contingency Table (Before Exclusions)
Joined directly from `calendar_releases.csv` against all clean EURUSD holding episodes in `fms_episodes.jsonl`:

**Primary Horizon: 6 H4 (Clean Paths = 89, Unfiltered Upper Bound = 46)**

| Climate ($S_C$) \ Expectations ($S_E$) | Expect POS | Expect NEG | Expect ZERO | Expect MISSING | Total |
|---|---|---|---|---|---|
| **Climate POS** | 18 | 2 | 1 | 0 | **21** |
| **Climate NEG** | 1 | 22 | 0 | 0 | **23** |
| **Climate ZERO** | 0 | 2 | 0 | 0 | **2** |
| **Climate MISSING** | 0 | 0 | 0 | 43 | **43** |
| **Total** | **19** | **26** | **1** | **43** | **89** |

- **Unfiltered Upper Bound** (Primary Complete AFP on Clean 6 H4): **46 episodes** (21 POS + 23 NEG + 2 ZERO).
- **Strict Directional Agreement Count (Chosen Rule)**: **40 episodes** (18 POS/POS + 22 NEG/NEG).
- **Non-Conflicting Count**: **41 episodes** (includes 1 Climate POS / Expect ZERO pair from 2021-08-25: Climate +0.2, Expect 0.0).
- **Conflicting Count**: **3 episodes** (2 Climate POS / Expect NEG; 1 Climate NEG / Expect POS).
- **Neutral Primary Cases** ($S_C = 0$): **2 episodes** (both Climate ZERO / Expect NEG).
- **Missing Consensus**: **43 episodes** (pre-November 2018 releases lack consensus forecasts in MT5 calendar).

#### 4. Recomputed Counts Across All Evaluated Horizons

| Horizon | Total Clean Paths | Unfiltered Upper Bound | Strict Agreement ($N$, Chosen) | Non-Conflicting ($N$) | Conflicting | Climate Zero | Missing Forecast |
|---|---|---|---|---|---|---|---|
| **6 H4 (1st Trading Day)** | 89 | **46** | **40** (18 POS, 22 NEG) | 41 | 3 | 2 | 43 |
| **12 H4 (2nd Trading Day)** | 88 | **46** | **40** (18 POS, 22 NEG) | 41 | 3 | 2 | 42 |
| **30 H4 (5 Trading Days)** | 79 | **40** | **35** (17 POS, 18 NEG) | 36 | 2 | 2 | 39 |
| **42 H4 (7 Trading Days)** | 77 | **39** | **34** (16 POS, 18 NEG) | 35 | 2 | 2 | 38 |
| **60 H4 (10 Trading Days)** | 74 | **38** | **33** (15 POS, 18 NEG) | 34 | 2 | 2 | 36 |

#### 5. Ifo April 2018 Methodology Change & Structural Sample Break
- In April 2018, the CESifo Group rebased the index (2005=100 $\to$ 2015=100) and integrated the German services sector.
- **Empirical Grounding in Export**: All 50 complete AFP packages (and all 46 clean 6 H4 episodes) occur exclusively post-overhaul (from November 2018 onwards). The complete-input sample is internally homogeneous under the modern methodology, but effective pre-2023 sample size is compressed to $N = 40$ actionable episodes.

#### 6. Physical Execution Timing & Session Realities
- **Release Clock Times**: 11:00 (28 pkgs), 11:30 (27 pkgs) $\to T_{\text{entry}} = \mathbf{12:00:00}$; 12:00 (18 pkgs), 12:30 (23 pkgs) $\to T_{\text{entry}} = \mathbf{16:00:00}$. (55 episodes enter at 12:00; 41 episodes enter at 16:00).
- **Matched Control Rule**: Dynamic session-matching to the exact entry broker hour (12:00 or 16:00), day of week (Mon: 36, Tue: 17, Wed: 13, Thu: 14, Fri: 16), and session state on non-announcement weeks.

#### 7. Later-Release Overlap & Attribution Concern
- At 6 H4 ($N = 46$), paths encounter Median = **18 release rows** [IQR: 14–25] across Median = **8 packages** [IQR: 6–10].
- At 60 H4 ($N = 38$), paths encounter Median = **303 release rows** across Median = **112 packages**.
- *Attribution Governance*: Retained as an architectural concern and open question.

#### 8. Revision Provenance Disclosure
- `revision = 0` identifies a provider revision-stage field relative to the reporting period, not a first-seen snapshot.

#### 9. Prior Exploration Disclosure
- *Phase 1 Overlap*: Zero overlap.
- *Historical FMS v1 Overlap*: Present (`s33` on 60 H4). Must be treated as reused historical data.

---

### Candidate 3: Policy-Repricing Wage Growth Shock (UK Average Weekly Earnings on GBPUSD)

#### 1. Core Research Question
> *Do wage growth surprises in UK labor releases (Average Weekly Earnings y/y) generate persistent policy-repricing drift on GBPUSD across the second trading day (12 H4), driven by Bank of England monetary policy repricing?*

#### 2. Series Identification & Predeclared Co-Release Rule Choice
- **Exact Primary Series**:
  - `GBP:GB:826010001:r0` — Average Weekly Earnings, Regular Pay y/y (Monthly, UK Office for National Statistics, `event_id = 826010001`, `revision = 0`).
- **Exact Co-Released Series**:
  - `GBP:GB:826010003:r0` — Unemployment Rate (`event_id = 826010003`, `revision = 0`).
- **Economic Transmission & Co-Release Rule Choice**:
  - Regular Pay y/y reflects underlying domestic wage pressure. Unemployment Rate reflects labor market slack.
  - *Chosen Rule*: **Actionable Non-Conflicting Non-Zero Wage ($N = 32$)**.
  - *Policy Direction Definition*:
    - **Hawkish Wage Impulse**: $S_{\text{Wage}} > 0$ accompanied by non-opposing labor slack ($S_{\text{Unemp}} \le 0$, i.e. Unemployment NEG or ZERO) $\to$ Long GBP.
    - **Dovish Wage Impulse**: $S_{\text{Wage}} < 0$ accompanied by non-opposing labor slack ($S_{\text{Unemp}} \ge 0$, i.e. Unemployment POS or ZERO) $\to$ Short GBP.
    - **Neutral Primary Exclusion**: Episodes where $S_{\text{Wage}} = 0$ exhibit no primary wage impulse and are excluded from directional trading.
    - **Conflicting Exclusion**: Episodes where wage inflation opposes unemployment slack ($S_{\text{Wage}} > 0 \land S_{\text{Unemp}} > 0$ or $S_{\text{Wage}} < 0 \land S_{\text{Unemp}} < 0$) are excluded.

#### 3. Full Sign-Pair Contingency Table (Before Exclusions)
Joined directly from `calendar_releases.csv` against all clean GBPUSD holding episodes in `fms_episodes.jsonl`:

**Primary Horizon: 12 H4 (Clean Paths = 92, Unfiltered Upper Bound = 62)**

| Wage ($S_W$) \ Unemployment ($S_U$) | Unemp POS | Unemp NEG | Unemp ZERO | Unemp MISSING | Total |
|---|---|---|---|---|---|
| **Wage POS** | 16 | 7 | 8 | 0 | **31** |
| **Wage NEG** | 6 | 6 | 11 | 0 | **23** |
| **Wage ZERO** | 2 | 3 | 3 | 0 | **8** |
| **Wage MISSING** | 0 | 0 | 0 | 30 | **30** |
| **Total** | **24** | **16** | **22** | **30** | **92** |

- **Unfiltered Upper Bound** (Primary Complete AFP on Clean 12 H4): **62 episodes** (31 POS + 23 NEG + 8 ZERO).
- **Actionable Non-Conflicting Count (Chosen Rule)**: **32 episodes**
  - Hawkish Impulse (Wage POS & Unemp NEG/ZERO): 7 + 8 = **15 episodes**.
  - Dovish Impulse (Wage NEG & Unemp POS/ZERO): 6 + 11 = **17 episodes**.
- **Explicit Accounting of the Eight Neutral Primary Cases** ($S_{\text{Wage}} = 0$):
  - Wage ZERO & Unemp POS = **2 episodes**
  - Wage ZERO & Unemp NEG = **3 episodes**
  - Wage ZERO & Unemp ZERO = **3 episodes**
  - *Total Neutral Primary*: **8 episodes**. In these 8 cases, headline wage growth matched consensus exactly ($A = F$). Because the primary indicator experienced zero surprise shock, there was no wage impulse to initiate directional positioning.
- **Conflicting Count**: **22 episodes** (16 Wage POS / Unemp POS; 6 Wage NEG / Unemp NEG).
- **Missing Consensus**: **30 episodes** (2015–2016 releases lack consensus forecasts in MT5 calendar).

#### 4. Recomputed Counts Across All Evaluated Horizons

| Horizon | Total Clean Paths | Unfiltered Upper Bound | Actionable Non-Conflicting ($N$) | Conflicting | Neutral Primary ($S_W = 0$) | Missing Forecast |
|---|---|---|---|---|---|---|
| **6 H4 (Diagnostic)** | 92 | **62** | **32** (15 Hawk, 17 Dove) | 22 | 8 | 30 |
| **12 H4 (Primary Horizon)** | 92 | **62** | **32** (15 Hawk, 17 Dove) | 22 | 8 | 30 |
| **30 H4 (5 Trading Days)** | 88 | **61** | **32** (15 Hawk, 17 Dove) | 21 | 8 | 27 |
| **42 H4 (7 Trading Days)** | 85 | **60** | **31** (15 Hawk, 16 Dove) | 21 | 8 | 25 |
| **60 H4 (10 Trading Days)** | 81 | **56** | **29** (13 Hawk, 16 Dove) | 20 | 7 | 25 |

#### 5. Physical Execution Timing & Session Realities
- **Release Clock Times**: 09:00 (21 pkgs), 10:00 (12 pkgs), 11:30 (35 pkgs) $\to T_{\text{entry}} = \mathbf{12:00:00}$; 12:30 (28 pkgs) $\to T_{\text{entry}} = \mathbf{16:00:00}$. (68 enter at 12:00; 28 enter at 16:00).
- **Weekday Distribution**: Tuesday (55), Wednesday (38), Thursday (2), Friday (1).
- **Matched Control Rule**: Dynamic session-matching to entry broker hour (12:00 or 16:00), day of week, and session state on non-announcement weeks.

#### 6. Later-Release Overlap & Attribution Concern
- At 12 H4 ($N = 62$), paths encounter Median = **47 release rows** [IQR: 33–54] across Median = **11 packages** [IQR: 10–13].
- At 60 H4 ($N = 56$), paths encounter Median = **179 release rows** across Median = **53 packages**.
- *Attribution Governance*: Retained as an architectural concern and open question.

#### 7. Revision Provenance Disclosure
- `revision = 0` identifies a provider revision-stage field relative to the reporting period, not a first-seen snapshot. Quoted-comma parsing regression was verified on disk (`"Average Weekly Earnings, Regular Pay y/y"` retains intact columns).

#### 8. Prior Exploration Disclosure
- *Phase 1 Overlap*: Zero overlap.
- *Historical FMS v1 Overlap*: Present (`s11`, `s12` on 60 H4). Must be treated as reused historical data.

---

## 3. Candidate Comparison Matrix

The table below contrasts the empirical data suitability, release distributions, and research properties of the three proposed candidates:

| Candidate Property | Candidate 1: US Housing Construction | Candidate 2: German Business Sentiment | Candidate 3: UK Labor & Wage Growth |
|---|---|---|---|
| **Macroeconomic Family** | Housing / Construction | Business Surveys / PMI | Labor / Employment |
| **Primary Series Key** | `USD:US:840020005:r0` (Permits) | `EUR:DE:276030003:r0` (Ifo Climate) | `GBP:GB:826010001:r0` (Avg Earnings) |
| **Co-Released Series** | `USD:US:840020004:r0` (Starts) | `EUR:DE:276030001:r0` (Expectations) | `GBP:GB:826010003:r0` (Unemployment) |
| **Trading Currency / Pair** | `USD` / **`EURUSD`** | `EUR` / **`EURUSD`** | `GBP` / **`GBPUSD`** |
| **Primary Proposed Horizon** | **6 H4 (1st Trading Day)** | **6 H4 (1st Trading Day)** | **12 H4 (2nd Trading Day)** |
| **Secondary Comparative Horizon** | 12 H4 (2nd Trading Day) | 12 H4 (2nd Trading Day) | 6 H4 (1st Trading Day) |
| **Pre-2023 Total Packages** | 96 (Monthly 2015–2022) | 96 (Monthly 2015–2022) | 96 (Monthly 2015–2022) |
| **Complete Inputs ($A/F/P$)** | 68 (70.8%) | 50 (52.1%, all post-Nov 2018) | 66 (68.8%) |
| **Release Broker Clock Times** | 15:30 (64 pkgs), 16:30 (32 pkgs) | 11:00 (28), 11:30 (27), 12:00 (18), 12:30 (23) | 09:00 (21), 10:00 (12), 11:30 (35), 12:30 (28) |
| **Derived $T_{\text{entry}}$ Hours** | 16:00 (64 pkgs), 20:00 (32 pkgs) | 12:00 (55 pkgs), 16:00 (41 pkgs) | 12:00 (68 pkgs), 16:00 (28 pkgs) |
| **Weekday Distribution** | Tue: 35, Wed: 28, Thu: 20, Fri: 13 | Mon: 36, Tue: 17, Wed: 13, Thu: 14, Fri: 16 | Tue: 55, Wed: 38, Thu: 2, Fri: 1 |
| **Unfiltered Joint Clean 6 H4** | **66 episodes** (Upper Bound) | **46 episodes** (Upper Bound) | **62 episodes** (Diagnostic) |
| **Unfiltered Joint Clean 12 H4** | **65 episodes** (Upper Bound) | **46 episodes** (Upper Bound) | **62 episodes** (Upper Bound) |
| **Unfiltered Joint Clean 60 H4** | 54 episodes | 38 episodes | 56 episodes |
| **Chosen Coherence Rule** | Primary + Non-Conflicting Starts | Strict Agreement ($S_C \times S_E > 0$) | Actionable Non-Conflicting Non-Zero |
| **Actionable Primary Horizon ($N$)** | **43 episodes** (6 H4) | **40 episodes** (6 H4) | **32 episodes** (12 H4) |
| **Actionable 12 H4 Count ($N$)** | 43 episodes | 40 episodes | **32 episodes** |
| **Actionable 60 H4 Count ($N$)** | 36 episodes | 33 episodes | 29 episodes |
| **Neutral Primary Cases** | 0 episodes | 2 episodes | **8 episodes** (explicitly accounted) |
| **Conflicting Direction Cases** | 23 episodes (6 H4) | 3 episodes (6 H4) | 22 episodes (12 H4) |
| **Later Overlap Rows (6 H4)** | Median = 21 [IQR: 14–30] | Median = 18 [IQR: 14–25] | Median = 26 [IQR: 16–32] |
| **Later Overlap Pkgs (6 H4)** | Median = 7 [IQR: 5–9] | Median = 8 [IQR: 6–10] | Median = 5 [IQR: 4–7] |
| **Later Overlap Rows (12 H4)** | Median = 41 [IQR: 35–50] | Median = 42 [IQR: 34–50] | Median = 47 [IQR: 33–54] |
| **Later Overlap Pkgs (12 H4)** | Median = 15 [IQR: 13–19] | Median = 17 [IQR: 14–21] | Median = 11 [IQR: 10–13] |
| **Later Overlap Rows (60 H4)** | Median = 264 [IQR: 242–283] | Median = 303 [IQR: 293–321] | Median = 179 [IQR: 167–192] |
| **Later Overlap Pkgs (60 H4)** | Median = 97 [IQR: 87–110] | Median = 112 [IQR: 101–119] | Median = 53 [IQR: 50–57] |
| **Cross-Currency Collision Rate** | 69 pkgs (71.9%, CAD co-releases) | 10 pkgs (10.4%) | 13 pkgs (13.5%) |
| **Historical FMS v1 Overlap** | Yes (`s41`, `s42` on 60 H4) | Yes (`s33` on 60 H4) | Yes (`s11`, `s12` on 60 H4) |

---

## 4. Accounting of Considered and Rejected Candidates

To ensure research selection is fully auditable and free from post-hoc selection bias, the table below documents candidate indicators, asset classes, and design choices evaluated and formally rejected:

| Considered Option / Design Choice | Evaluation Status & Grounds |
|---|---|
| **US Nonfarm Payrolls (`USD:US:840030016:r0`) & Headline CPI (`USD:US:840030005:r0`)** | **Formally Rejected**: Evaluated in Phase 1 across EURUSD and USDJPY for $H_1$ to $H_{24}$ delayed horizons. Permutation testing yielded no convincing directional drift ($p = 0.87$ on NFP, $p = 0.30$ on CPI). Note: `USD:US:840010001:r0` is Core PCE Price Index m/m; headline CPI is correctly identified as `840030005:r0`. Re-proposing NFP/CPI on major pairs without an entirely new mechanism would constitute unprincipled data reselling. |
| **Weekly US Petroleum Inventories (`USD:US:840200001:r0` – `840200009:r0`)** | **Rejected on Transmission Suitability**: Although possessing high package counts ($N = 416$), oil and gas stocks transmit primarily into energy futures and petrocurrencies (USDCAD, CADJPY). Impact on EURUSD or GBPUSD is highly diluted, and weekly releases suffer from continuous compounding overlap (a new release occurs every 7 calendar days). |
| **Eurozone / National GDP Releases (`EUR:EU:999030016:r1` – `r3`, `EUR:DE:276010001`)** | **Rejected on Sample Sparsity & Revision Cadence**: Quarterly GDP produces only 32 calendar packages over 8 years. Complete consensus inputs exist for only 21–23 packages. Multiple revision stages (preliminary, revised, final) further fragment statistical power. |
| **Minor / Exotics FX Pairs (`USDHKD`, `USDSEK`, `USDSGD`, `EURHKD`)** | **Rejected on Severe Physical Data Gaps**: As proven in our physical diagnostic, USDHKD has a 48,329-hour multi-year gap (2017 to 2022); USDSEK has a 53,423-hour gap; EURHKD ends in 2017. Furthermore, historical retail execution spreads and liquidity for exotics are unmanifested. |
| **Zero-History Pairs (`CADJPY`, `GBPJPY`, `USDMXN`, etc.)** | **Rejected on Non-Existence**: Exactly 15 pairs in the export have zero pre-2023 H1 bars. |
| **Long Horizons (30 H4, 42 H4, 60 H4: ~5–10 Trading Days)** | **Retained as an Open Design Question (Architectural Concern)**: Long-horizon paths encounter substantial compounding macro exposure (e.g., median 53 to 112 subsequent packages at 60 H4). This raises legitimate causal attribution decay concerns regarding whether price returns can be attributed to the initiating announcement. Rather than arbitrarily disqualifying long horizons without a counted tier-1 event filter, we retain long horizons as an explicit open question for Project Director steering and Milestone 3 pre-registration. |
| **Pooling Multiple Countries or Indicator Stages** | **Rejected on Methodological Integrity**: Pooling preliminary French CPI with final German CPI to inflate $N$ introduces severe heterogeneity in information content and timing. |

---

## 5. Epistemic Separation: Facts, Conjectures, and Unresolved Choices

In accordance with Chief of Staff guidelines, we strictly partition verified data facts, economic theories, and steering decisions:

### A. Verified Inventory Facts (Empirical Grounding)
1. **Sample Bounds**: Each monthly series possesses exactly **96 distinct timestamp packages** across the 2015–2022 pre-discovery period.
2. **True Joint Intersections (Upper Bounds)**: Complete inputs ($A/F/P$) and clean instrument paths on the SAME package yield **66 episodes for Housing Permits (6 H4)**, **46 episodes for German Ifo (6 H4)**, and **62 episodes for UK Wages (12 H4)**.
3. **Actionable Filtered Bounds (Contingency Table Verified)**:
   - US Housing: **43 episodes** (21 POS, 22 NEG). Zero neutral cases. 23 conflicting excluded.
   - German Ifo: **40 episodes** under Strict Agreement (18 POS, 22 NEG). 1 neutral expectation case ($N = 41$ under non-conflicting). 2 neutral primary cases. 3 conflicting excluded.
   - UK Wages: **32 episodes** (15 Hawkish, 17 Dovish). **8 neutral primary cases explicitly accounted for**. 22 conflicting excluded.
4. **Physical Entry Timing**: Entry at `calculateNextH4Boundary(ts)` introduces variable delays (30m to 240m) due to Daylight Saving Time shifts and sub-session release schedules.
5. **Session vs. Wall-Clock Duration**: Friday entries (13 for US Housing, 16 for German Ifo, 1 for UK Wages) cross the weekend broker closure, resulting in 72 wall-clock hours for 6 completed H4 bars and 96 wall-clock hours for 12 completed H4 bars.
6. **Ifo Methodology Break**: All 50 complete AFP packages for German Ifo occur post-April 2018 (November 2018 to December 2022), corresponding 100% to the CESifo 2015=100 services-inclusive methodology. Pre-2018 is unrepresented due to missing forecast coverage in MT5.
7. **Revision Field Provenance**: `revision = 0` identifies a provider revision-stage field relative to the reporting period, not a first-seen snapshot.
8. **No Touched Confirmation Data**: All 2023+ candle bars and calendar releases remain sealed.

### B. Economic Conjectures (Theories to be Tested, Not Assumed Facts)
1. **Delayed Institutional Rebalancing (Conjecture)**: We hypothesize that corporate hedging and portfolio realignments after real-economy demand surprises (Permits/Starts) and business surveys (Ifo) require several market sessions (6 to 12 H4) to fully clear.
2. **Policy Repricing Persistence (Conjecture)**: We hypothesize that wage growth surprises in the post-Brexit UK economy trigger multi-day gilt yield and currency drift via Bank of England policy expectations.
3. **First-Bar Information Absorption (Conjecture)**: We hypothesize that the close of the first complete H4 bar ($T_{\text{entry}}$) allows immediate announcement spread widening and microstructural noise to dissipate while preserving institutional flow.

### C. Unresolved Choices (Pending Project Director Steering & Codex Review)
1. **Candidate Priority**: Which of the three candidates (US Housing Demand [$N=43$], German Ifo Business Climate [$N=40$], or UK Labor Wage Growth [$N=32$]) should be selected as the primary candidate for Milestone 3 protocol pre-registration?
2. **Holding Horizon Selection**: Should the pre-registered protocol evaluate short holding horizons (6 H4 / 12 H4) exclusively, or formally retain multi-day holding horizons (30 H4, 42 H4, 60 H4) as secondary comparative branches?
3. **Surprise Metric Formulation**: Should surprise be evaluated as:
   - Raw difference: $S = A - F$?
   - Scaled z-score: $z = \frac{A - F}{\sigma_{\text{historical}}}$ (strictly rolling / expanding window)?
   - Quantile / percentile rank: $Q(A - F)$?
4. **Execution Spread Policy**: What fixed or time-of-day Bid/Ask spread penalty must be enforced at $T_{\text{entry}}$ during Milestone 4 exploration?

---

## 6. Before / After Correction Audit Table

The table below documents every remediation requested across both Codex audits, the exact read-only fields and filters applied, and the verified empirical state:

| Audit Item | Pre-Audit Draft State | Post-Audit Remediated State | Exact Read-Only Fields & Filters Used |
|---|---|---|---|
| **1. Sign-Pair Contingency Tables & Filtered Counts** | Filtered counts (43, 40, 40) did not reproduce from written rules. Missing full contingency matrices. | Published full sign-pair contingency tables (POS/NEG/ZERO/MISSING) for all candidates and horizons before exclusions. Reconciled exact actionable counts: Housing = **43**, Ifo = **40** (under Strict Agreement; 41 under non-conflicting), Wages = **32**. | Joined `calendar_releases.csv` (`actual`, `forecast`, `revision == 0`) with `fms_episodes.jsonl` clean paths by horizon. |
| **2. Explicit Accounting of Neutral Wage Cases** | Reported 40 for UK Wages, which inadvertently included 8 zero-wage episodes. | Explicitly decomposed all 62 upper-bound episodes: **32 actionable non-conflicting** (15 Hawkish, 17 Dovish), **8 neutral primary cases** ($S_{\text{Wage}} = 0$: 2 POS, 3 NEG, 3 ZERO in unemp), and **22 conflicting**. | `calendar_releases.csv`: `eventId == 826010001` vs `826010003`, evaluated for $S = A - F$. |
| **3. Ifo Rule Choice & Zero Expectations Case** | Ambiguity between written non-conflicting ($N=41$) and strict agreement ($N=40$). | Declared **Strict Directional Agreement ($N=40$)** before outcomes. Documented the single nonzero Climate / zero Expectations episode (2021-08-25: +0.2 / 0.0) and 2 Climate ZERO cases. | `calendar_releases.csv`: `eventId == 276030003` vs `276030001`. |
| **4. Revision = 0 Field Provenance** | Claimed `revision = 0` guarantees a point-in-time initial release value. | Corrected: `revision = 0` identifies a provider revision-stage field relative to the reporting period, not a first-seen snapshot. Noted that retrospective export cannot prove real-time consensus visibility at announcement. | `calendar_releases.csv` schema documentation: `revision` column semantics. |
| **5. Later-Release Exposure & Long Horizons** | Categorically rejected 42–60 H4 based on later releases without counting tier-1 events. | Reframed long-horizon exposure as an architectural concern (causal attribution decay). Retained long horizons (30, 42, 60 H4) as an open design question for Director steering and Milestone 3 pre-registration. | Recomputed overlap medians and IQRs; preserved long horizons in open questions. |
| **6. Exact Read-Only Disciplines & Zero Prices** | Risk of premature return ranking. | Zero candidate OHLC prices, returns, MFE/MAE, or backtests were read or computed. Candidate price outcomes remained strictly sealed. Repository test suite continues to run legacy candle validation tests (verifying timestamp gaps and parser regressions). | Pinned export `tools/mt5/FyodorResearchExport_v3_20260923_234930_server`. |

---

## 7. Audit Stop Gate

> [!CAUTION]
> **DIRECTOR & AUDITOR REVIEW STOP GATE**  
> In strict compliance with the research roadmap:
> - No recipe has been frozen.
> - No strategy backtest has been performed.
> - Candidate price series remain strictly sealed (zero candidate OHLC prices, returns, or rankings computed).
> - 2023+ confirmation data remains untouched.
> 
> **STOPPED HERE.** The Project Director is requested to submit this revised charter to Codex for review and steering approval before proceeding to Milestone 3 (Protocol Pre-Registration).
