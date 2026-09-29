# Research Protocol: USD CPI Same-Time Bundle Study (V1)

**Protocol Identifier:** `USD_CPI_BUNDLE_V1`  
**Status:** OUTCOMES EVALUATED / SELECTION POLICY NONE / NOT REGISTERED  
**Date:** 30 September 2026  
**Contract Baseline:** [Calculation Contract](CALCULATION_AND_CANDIDATE_CONTRACT.md)  
**Maintained Context:** [Grand Objective](../Maintained%20Planning/Grand%20Objective.md)  
**Local Run Targets:**  
- Pre-Outcome Target (Version 2 - Current Audited): `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_pre_outcome_v2/`  
- Pre-Outcome Target (Version 1 - Preserved): `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_pre_outcome/`  
- Outcome Run Target (Version 3 - Current Audited): `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes_v3/`  
- Preserved Historical Run (Version 2): `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes_v2/`  
- Preserved Historical Run (Version 1): `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes/`  
**Tracked Schema & Reconciliation:**  
- Schema: [Ledger Schema](../../Research%20Candidate/CPI/CPI_BUNDLE_V1/SCHEMA.md)  
- Pre-Outcome Reconciliation: [Count Reconciliation Report](../../Research%20Candidate/CPI/CPI_BUNDLE_V1/RECONCILIATION_REPORT.md)  
- Outcome Reconciliation: [Outcome Reconciliation Report](../../Research%20Candidate/CPI/CPI_BUNDLE_V1/OUTCOME_RECONCILIATION_REPORT.md)  

> [!IMPORTANT]
> **OUTCOME AUDIT BOUNDARY (SELECTION POLICY NONE):**  
> This protocol specifies the research design, calendar constituent architecture, price-blind inventory, and finite candidate comparison rules for a NEW, versioned study of the same-time USD Consumer Price Index (CPI) release bundle. Outcomes across all 52 ATR barrier cells and 3 horizons have been simulated strictly under `selection_policy = NONE`. It contains **zero candidate ranking, zero winner selection, and zero setup registration**. The HTML viewer and Trading Terminal remain untouched.

---

## 1. Input Hashes & Raw Data Provenance

All calculations in this study derive strictly and immutably from the pinned V4 broker/terminal export located at:  
`raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/`

### Root Raw Calendar and Configuration Hashes (Fail-Closed Check)

| Raw File | Size (Bytes) | SHA-256 Checksum | Provenance Tier |
| --- | --- | --- | --- |
| `manifest.csv` | 3,515 | `1E7C8A5047BDEDAF0F66DE23F5E6CC382C29EA839B9E07A911789BBFFC548A6F` | Independently Anchored |
| `calendar_releases.csv` | 55,514,491 | `FCB68E1C2A6269D98287F4BEDBEE1F3BCB5A8C99379502782359EDFD20E83D6F` | Independently Anchored |
| `calendar_events.csv` | 359,636 | `E08D2DF96E83FDEFA1C56D33316EE09178FE75AFF1F3325D6F4EC4C80A4B7F13` | Computed and Registered |
| `calendar_currencies.csv` | 224 | `ADB8C1A4DB5041067CDEF06852C29D5EFA4BCF8E56B7F978AD9AB84CA9C3F809` | Computed and Registered |
| `candle_symbols.csv` | 6,660 | `876495CC3FCD0B4E88CB1412E6DF154CF8813B5DF7CC5EC57A8F74C57BD7475D` | Independently Anchored |
| `run_started.csv` | 105 | `0F9944FDE37206826EADF9CBE8675B4381E15F9F524478EB7F76E6A8D9A8DA10` | Computed and Registered |

### Seven Active USD Pair H1 Candle Exports (ATR Warmup & Path Verification)

| Candle File | Size (Bytes) | SHA-256 Checksum | Active Pair Role |
| --- | --- | --- | --- |
| `candles/candles_AUDUSD_H1.csv` | 7,892,321 | `804FF41B922BD02A7EDE6705D2BD9861A7AF5B45D7D9DD841E10AEEE81FA7181` | Quote USD Pair |
| `candles/candles_EURUSD_H1.csv` | 7,859,948 | `96A51AA29BBC3F3E9CB07633328F154AC6967D8BF40B7A5211934ACB0DEFF45E` | Quote USD Pair |
| `candles/candles_GBPUSD_H1.csv` | 7,900,601 | `77438C3DF042FA379533144A830FEDFBEC8AC12A47E53647C8653C7090F45512` | Quote USD Pair |
| `candles/candles_NZDUSD_H1.csv` | 7,889,012 | `DFAD73063A3313175ED7F111F8FD38AC0C1D5D1E62FD0D037A2DB396972B755E` | Quote USD Pair |
| `candles/candles_USDCAD_H1.csv` | 7,899,102 | `D854DDB5494E3CD62D9F80E2A22F9F65FAAA886643572602D638722C1DC72D44` | Base USD Pair |
| `candles/candles_USDCHF_H1.csv` | 7,906,778 | `134A250D6FE0F3259A6B0D842872866B481A9A7FE9D7567E7892DCB23B63897E` | Base USD Pair |
| `candles/candles_USDJPY_H1.csv` | 7,900,249 | `3DCE78FE38019275F288E71E4F9134E4BEA1FD02A09E1CEE2873025A3961468C` | Base USD Pair |

### Pinned Pre-Outcome Ledger Artifacts

#### Version 2: `run_20260930_pre_outcome_v2` (Current Audited - Full Precision ATR `repr`)
| Generated Ledger | Scope | Row Count | SHA-256 Checksum |
| --- | --- | --- | --- |
| `cpi_bundle_ledger.csv` | Unique CPI Release Bundles | 140 (141 lines) | `55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE` |
| `cpi_pair_expanded_ledger.csv` | 7 Active USD Pairs × 140 Bundles | 980 (981 lines) | `3A5ECA2CED0131EC923C790D43E4BCDB883E91DDB10B6EDD592FCAC3E83263F9` |
| `manifest.json` | Pre-Outcome Package Manifest | 168 lines | `F4C0561D8CC95B3882A21962495735009C7E25D2D310AA35D0547BFF0F75399D` |

#### Version 1: `run_20260930_pre_outcome` (Preserved Historical Baseline - `.6f` rounded ATR)
| Generated Ledger | Scope | Row Count | SHA-256 Checksum |
| --- | --- | --- | --- |
| `cpi_bundle_ledger.csv` | Unique CPI Release Bundles | 140 (141 lines) | `55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE` |
| `cpi_pair_expanded_ledger.csv` | 7 Active USD Pairs × 140 Bundles | 980 (981 lines) | `3B8A75B853A07F7F1BBE0CC1D30CCA269311C6E700EE61843B1521D5E8C4ECBB` |
| `manifest.json` | Pre-Outcome Package Manifest | 108 lines | `3B4B27CE3A4105B925BA05DF569DC11DE470081C4F2BD40BEA128B47BF94E27D` |

### Calculation Dependencies (Uncommitted Working Tree Hashes on Baseline `1bc93052cf59b1a37589bd528725d07414b69af0`)

| Dependency Script | Size (Bytes) | SHA-256 Checksum | Role |
| --- | ---: | --- | --- |
| `run_cpi_bundle_outcomes.py` | 69,881 | `37DED8DBF8350531D151298F189365076248B76573A27F28AF4E7CF95C4977AB` | Master outcome runner & report generator |
| `outcome_engine.py` | 41,423 | `319E337E85524E6ED8508C3974C31EE7B91735E4A3244D4506AC847A0CDDBEAF` | Pure outcome simulation engine & metrics |
| `audit_raw_csv_ohlc.py` | 22,659 | `AA4D380DB26C7B953796FE4BD70028F0C06A4BB0505ED089E3829506350D20C2` | Genuinely standalone raw-CSV OHLC audit |
| `data_loader.py` | 10,859 | `A130AB2B052222BFBD584759446DF2FD5FFCA814920813588C4BB89D73BACC9B` | Pinned candle/calendar CSV ingestion |
| `path_indexer.py` | 8,597 | `FFA074FE7B7723D5ADC68A2129E628A62F1689BD40E5703D3E7C8AFF1F1BBD68` | 240-bar path coverage & gap validator |
| `protocol_specs.py` | 6,475 | `DF044F631A6D9AF0706341221DC068826408BCB01641E29B012884021FB50955` | Static FX pairs, pips, and event metadata |
| `models.py` | 5,592 | `E292679339EA045F2ED226C8C3EC4634C0261CE2710AC9B99E7E3221A647E255` | Typed dataclasses for calendar rows |
| `generate_cpi_bundle_inventory.py` | 64,686 | `216FC2BE0EDCA461DD0562A84D534B295034D15FE694E06611843FF9A7876374` | Pre-outcome inventory & ledger generator |

### Generated Outcome Artifacts (Version 3: `run_20260930_outcomes_v3` - Active Audited)

| Generated Artifact | Size (Bytes) | SHA-256 Checksum | Description |
| --- | ---: | --- | --- |
| `trial_ledger.csv` | 252,623,985 | `3C468999F7F876B1DC9ED01E278B389990A73E41F28141F0815C7E504F83273F` | 465,036 simulated trials (unrounded ATR, full float R aggregation) |
| `summary_grid_results.csv` | 13,452,063 | `0F28962DF6A717264AB8194B88416CCD739BF55299187E7571313902DB669777` | 29,952 aggregated grid rows with full Target-First sensitivity columns |
| `annual_breakdown.csv` | 44,700,610 | `3DAC97108850021396A15E823B7E5CE3FC8D81E122C20B1D3097938FCF3E3DC1` | 344,448 annual performance rows (2015..2025 Core vs 2026 Partial) |
| `loyo_folds.csv` | 37,051,471 | `816EA0171452B030839AD243CD79691602B76D964A8E34265F558AE540AE3B86` | 314,496 Leave-One-Year-Out year-removal stability check fold rows |
| `v2_to_v3_comparison.json` | 952 | `176C65A3D1D62FC50CD2BDCF3769E0C49A4D8C08EC2C54711AF39A214227BEC9` | Machine-readable V2-to-V3 ledger and summary comparison metrics |
| `manifest.json` | 14,840 | `2B135F4A7783243F05F2127240ED96E2E53EBBC066E701FA25225B8F997331B7` | Run parameters, dependency hashes, raw audit, and comparison records |

### Preserved Historical Outcome Artifacts (Version 2: `run_20260930_outcomes_v2` - Preserved Unchanged)

| Generated Artifact | Size (Bytes) | SHA-256 Checksum | Description |
| --- | ---: | --- | --- |
| `trial_ledger.csv` | 247,763,535 | `4CB9388DEC29F8F267DFEDF69C5B14A048EC28B96393D8D4F9B49320550DCC2B` | Historical V2 ledger (rounded .6f ATR) |
| `summary_grid_results.csv` | 13,452,301 | `C295654FEA0B506D499CCE2057AA5FA593A533B08ADA44C5CC5480BF50AEB4D5` | Historical V2 summary |
| `annual_breakdown.csv` | 44,700,668 | `FC9786FC19395D6EA12A0274DDBD1FA8CEEC432F4F9DD75EA25BEA2F77F67F0C` | Historical V2 annual breakdown |
| `loyo_folds.csv` | 37,051,823 | `A1A47E7E48E5C1EBEEB8B3265089632956839B37D1668853F13C2AC82554B790` | Historical V2 LOYO folds |
| `manifest.json` | 6,567 | `F7C3F60F7AEFD66D1C4F375D689A3ED9CEA5DDD467D8DA4F4404D28265B3F439` | Historical V2 manifest |

### Preserved Historical Outcome Artifacts (Version 1: `run_20260930_outcomes` - Preserved Unchanged)

| Generated Artifact | Size (Bytes) | SHA-256 Checksum | Status |
| --- | ---: | --- | --- |
| `trial_ledger.csv` | 247,763,535 | `4CB9388DEC29F8F267DFEDF69C5B14A048EC28B96393D8D4F9B49320550DCC2B` | Historical V1 ledger |
| `summary_grid_results.csv` | 11,578,911 | `424F4712FDB33D6D5D6DAC2BD7FE9D45E8EB30760E0F8E9F9046414E451B79C2` | Historical V1 summary (pre-target-first columns) |
| `annual_breakdown.csv` | 44,700,668 | `FC9786FC19395D6EA12A0274DDBD1FA8CEEC432F4F9DD75EA25BEA2F77F67F0C` | Historical V1 annual breakdown |
| `loyo_folds.csv` | 37,051,823 | `A1A47E7E48E5C1EBEEB8B3265089632956839B37D1668853F13C2AC82554B790` | Historical V1 LOYO folds |
| `manifest.json` | 3,754 | `0C15B550A189213A24E5A2CBCC634F12F3C6101D0965C6411947671C3406939D` | Historical V1 manifest |

### 1.1 Machine-Readable V2-to-V3 Run Comparison (Full-Precision Round-Trip ATR Audit)

This comparison evaluates the exact differences between `run_20260930_outcomes_v2` and `run_20260930_outcomes_v3`. All metrics are derived directly from the trial ledgers and summary grids on disk:

| Comparison Metric | Observed Value | Audit Interpretation & Invariant Status |
| --- | ---: | --- |
| **Total Simulated Trials Evaluated** | 465,036 | Exhaustive grid: 6 comparisons × 3 horizons × 52 cells |
| **Changed ATR Inputs** | 465,036 | Pre-release ATR updated to unrounded IEEE 754 precision (`repr`) across all trials |
| **Changed Stop/Target Classifications** | **246** | Borderline barrier touches shifted between win/loss/timeout (0.053% of trials) |
| **Changed Exit Bars** | **858** | Exit-bar timing shifts on borderline barrier touches (0.184% of trials) |
| **Changed Stop-First R Values (Nominal Win/Loss)** | **0** | Nominal ±1R stop/target payouts are invariant to float precision |
| **Changed Stop-First R Values (Timeout Precision)** | 5,008 | Sub-1e-7 floating-point precision adjustment on timeout trades |
| **Changed Target-First R Values (Timeout Precision)** | 5,038 | Sub-1e-7 floating-point precision adjustment on timeout trades |
| **Total Summary Grid Cells Evaluated** | 29,952 | 2 panels × 8 pairs × 6 comparisons × 2 cohorts × 3 horizons × 52 cells |
| **Changed Summary Cell Trade Counts** | **0** | Trade counts N are 100% invariant across all 29,952 cells |
| **Changed Summary Cell Outcome Counts** | **1,856** | Summary cells reflecting the 246 trial classification shifts |
| **Summary Cells with Float Precision Shift** | 5,642 | Max abs delta in Gross Mean R: `0.0427360000R`; Max abs delta in Gross Sum R: `3.02750000R` |

### Absolute Data Integrity Prohibitions
1. **Zero Synthetic / Mock Data:** No random numbers, pseudo-random generators, or fabricated series.
2. **Zero Outcome Faking:** No assumed outcomes, modulo toggles, or hardcoded win/loss sequences.
3. **Strict Information Timing (Zero Lookahead):**
   - **Pre-Release ATR(14):** Inputs must strictly precede release ($t_{\text{close}} < t_{\text{release}}$). Zero release bar or post-release candle affects volatility.
   - **Signal Availability & Timing:** The Actual CPI reading ($A$) becomes known **AT release** ($t = t_{\text{release}}$). The simulated trade enters at the open of the first completed H1 bar strictly after release ($t_{\text{entry}} > t_{\text{release}}$, typically 30 minutes after release). While $A$ is assumed available for entry by the end of the release bar / start of the H1 entry bar, a static historical economic calendar export cannot prove live network latency or order-routing transmission times, nor can it establish whether any Previous revision was visible to market participants prior to or only upon the release timestamp. The signal is not claimed to be known prior to release.
4. **Preservation of Exploratory Baselines:** The completed V2 studies (`CPI_EXPLORATION_V2` and `NFP_EXPLORATION_V2`) are preserved as immutable historical baselines. This study does not overwrite or alter them.

---

## 2. Contract Relationship & Authority

1. **Hierarchy:** The [Calculation and Candidate Contract](CALCULATION_AND_CANDIDATE_CONTRACT.md) governs bar indexing, Wilder ATR(14) formulas, barrier geometry, pip sizes, OHLC touch resolution, and ledger auditability. This document defines the family-specific bundle assembly, indicator definitions, signal derivation, finite candidate comparisons, and collision handling.
2. **Prior Draft Invalidation:** This protocol formally supersedes the exploratory notes in `DRAFT_CPI_FAMILY_PROTOCOL.md`. Specifically:
   - Initial Jobless Claims event ID is verified as `840140001` (NOT the older draft's erroneous `840030001`).
   - The verified count of coincident Claims timestamps is exactly **33** (32 with Headline m/m anchor present, 1 on `2025.12.18` where m/m is absent), rather than the older narrative's "20 releases".
3. **Decision Boundary:** The new study is **A−P only**. Forecasts ($F$) and consensus surprise ($A - F$) are **excluded** from candidate formation, ranking, and filtering.

---

## 3. FX Universe Scope & Exclusion Boundary

- **Active USD Universe (7 Pairs):**  
  `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`.
  - Base USD Pairs (USD Strength $\implies$ Long Pair): `USDCAD`, `USDCHF`, `USDJPY`.
  - Quote USD Pairs (USD Strength $\implies$ Short Pair): `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`.
- **Strictly Excluded Pairs (9 Pairs):**  
  `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY`.  
  Globally excluded due to broker history starting only 25–26 November 2025. Denominator in all candidate and trade calculations is strictly 0.
- **Extended Crosses (12 Pairs):**  
  Reserved for non-USD family research; zero indirect spillover evaluation in this study.
- **Single Macro Episode Identity:** Seven pair outcomes from a single release timestamp represent seven correlated expressions of **one macroeconomic event**, not seven independent trade opportunities.

---

## 4. Chronological Cohort Definitions & Inspection History Warning

1. **Core Cohort (2015–2025 Full Years):**  
   - Interval: `2015.01.01 00:00:00` to `2025.12.31 23:59:59`.  
   - Bundles: **131 unique release timestamps** (12 releases per year for 2015–2024, 11 releases in 2025).  
   - Pair observations: $131 \times 7 = \mathbf{917}$ pair-observations.
2. **Partial Cohort (January–August 2026):**  
   - Interval: `2026.01.01 00:00:00` to `2026.08.31 23:59:59`.  
   - Bundles: **8 unique release timestamps**.  
   - Pair observations: $8 \times 7 = \mathbf{56}$ pair-observations.
3. **Post-Cutoff Release (September 2026):**  
   - Release: `2026.09.11 15:30:00` (1 bundle, 7 pair-observations).  
   - **Exclusion Rationale:** Excluded from historical research cohorts (`excluded_post_2026_cutoff`) **solely by the predeclared August 31, 2026 study release cutoff date**. The raw V4 candle export extends through September 28, 2026 and contains complete, gap-free H240 bar paths for all seven pairs for this release. It remains visible in the raw inventory ledger but outside outcome cohorts.
4. **Rigorous Count Separation:**
   - **140 Bundles (980 Pair-Observations):** Total raw calendar inventory on disk.
   - **139 Bundles (973 Pair-Observations):** In-cutoff research cohort through the August 31, 2026 cutoff date ($131 + 8$).
   - **138 Bundles (966 Pair-Observations):** In-cutoff m/m-anchor-present cohort ($139 - 1 = 138$, excluding `2025.12.18`).
   - **106 Bundles (742 Pair-Observations):** In-cutoff Claims-clean subset with m/m anchors present ($138 - 32 = 106$, with 742 pair-observations).
   - **Candidate-Specific Pre-Outcome H60-Eligible Pair Observations:** Strictly smaller than in-cutoff denominators due to zero-momentum abstentions, physical entry delay caps, and collision filters (Candidate 1: 859, Candidate 2: 656, Candidate 3: 411, Candidate 4: 663, Conflict Sub-study: 196). Never label the 140-bundle inventory as in-cutoff, never call N=138/966 'all eligible candidate releases', and never cite 'N=139' where the absent-anchor release has already been excluded.

> [!WARNING]
> **INSPECTION WARNING — NO UNTOUCHED HISTORICAL HOLDOUT:**  
> The 2015–2026 data has already been inspected during exploratory phases V1 and V2. **None of these historical years may be treated as a fresh or untouched out-of-sample holdout.** Any candidate rule specified today is informed by prior inspection of these exact episodes. True out-of-sample evidence can only come from future prospective demo forward-testing.

---

## 5. CPI Same-Time Bundle Definition & Constituent Architecture

A US CPI release timestamp represents a multi-series statistical release by the U.S. Bureau of Labor Statistics (BLS). Four specific percentage-change series are tracked as constituents of the unified bundle:

| Constituent Name | MT5 Event ID | Frequency / Horizon | Units / Scale | Stored Digits | Bundle Role |
| --- | --- | --- | --- | --- | --- |
| **Headline CPI m/m** | `840030005` | Monthly pace | Percent | 1 | Anchor for benchmark momentum |
| **Core CPI m/m** | `840030006` | Monthly underlying pace | Percent | 1 | Primary comparison & conflict evaluation |
| **Headline CPI y/y** | `840030007` | Annual pace | Percent | 1 | Descriptive annual context (NOT equal vote) |
| **Core CPI y/y** | `840030008` | Annual underlying pace | Percent | 1 | Descriptive annual context (NOT equal vote) |

### Non-Percentage Index Rows Excluded
Index-level rows (e.g. `840030009` CPI n.s.a. ~310.0, `840030010` Core CPI ~320.0) are index-level figures with non-percentage scales (~250–320). They are **excluded** from momentum calculations to prevent unit distortion.

### Core CPI is a Bundle Member, Not an External Collision
Core CPI is released simultaneously by the BLS as part of the CPI report. It is an **internal bundle member**, not an external collision.

### Strict Anchor Integrity & The Missing m/m Event of 2025-12-18
- **Empirical Observation:** On `2025.12.18 16:30:00`, Headline m/m (`840030005`) and Core m/m (`840030006`) are **absent from the MT5 export**. Both y/y series (`840030007`, `840030008`) exist at that timestamp.
- **Strict Prohibition on Fallback:** **Silent substitution with y/y is STRICTLY FORBIDDEN.** When evaluating an m/m candidate, `2025.12.18` is recorded with `headline_mm_sign = MISSING` and excluded via `excluded_missing_anchor`. Zero silent substitution with y/y is performed or tolerated.

---

## 6. Signal Formulation: A−P Only, Zero/Missing Integrity, and Publication Vintage

### Arithmetic Definition & Fail-Closed Validation
For each constituent series $i \in \{\text{Headline m/m}, \text{Core m/m}, \text{Headline y/y}, \text{Core y/y}\}$:
$$\Delta_i = A_i - P_i$$
where:
- $A_i$ = Exported Actual reading.
- $P_i$ = Exported reported Previous reading.

The parsing engine enforces strict fail-closed validation:
- Any unexpected currency (non-USD), non-percent unit, or non-empty multiplier raises `ValueError`.
- Malformed numeric strings, `"nan"`, `"inf"`, or non-numeric representations raise `ValueError`.
- Missing fields (empty string) are represented strictly as `None` / `MISSING`. Missing is strictly distinct from malformed text.
- A non-finite or `NaN` delta raises `ValueError` and is never silently classified as `ZERO`.

### Non-Overlapping Sign States
- **POSITIVE:** $\Delta_i > +10^{-9}$ (Pace accelerated / heated relative to prior month's reading).
- **NEGATIVE:** $\Delta_i < -10^{-9}$ (Pace cooled relative to prior month's reading).
- **ZERO:** $|\Delta_i| \le 10^{-9}$ (Pace unchanged from prior month's reading).
- **MISSING:** $A_i$ or $P_i$ is `None` / absent from calendar.

### Empirical Missingness & Zero Findings
1. **100% Completeness when Present:** For all 139 present occurrences of Headline m/m and Core m/m, and all 140 occurrences of Headline y/y and Core y/y, both $A$ and $P$ are 100% populated with valid finite floats.
2. **Core m/m Zero Inertia:** Core CPI m/m displays **44 zero deltas** out of 139 releases (31.7%). Because Core CPI is rounded to 1 decimal place, monthly increments frequently reproduce the prior month's reported rate.
3. **Zero is Distinct from Missing:** Zero momentum is a neutral factual observation ($\Delta = 0.0$), never coerced to positive or negative, and never conflated with missing data.

### Unresolved Publication-Vintage Limitation
> [!IMPORTANT]
> **FORENSIC PUBLICATION-VINTAGE RISK:**  
> A static historical economic calendar export captures the `previous` value stored in the broker database at the time of export. It does **not** establish what previous reading was visible to market participants at the exact release second, nor does it document whether `previous` was subsequently adjusted for seasonal revisions.  
> In the raw calendar:
> - `revised_previous` is populated in **15 of 139 releases** for Headline m/m.
> - `revised_previous` is populated in **12 of 139 releases** for Core m/m.
> - `revised_previous` is populated in **1 of 140 releases** for Headline y/y and Core y/y.
> Baseline research strictly uses the exported `previous`. Any strategy evaluated on historical $A - P$ cannot be certified as live-reproducible from a historical database snapshot alone without real-time tick-audit verification.

---

## 7. Joint Headline / Core m/m Sign Matrix

Rather than crossing all 4 series into an unmanageably sparse 52-state grid (which fragments 140 releases into N=1 or N=2 bins), the primary structural taxonomy categorizes releases by the joint signs of **Headline m/m** and **Core m/m**:

| Category Name | State Code | 2015–2025 Core | 2026 Partial | 2026 Post | Total Releases | Pair Obs (×7) | Economic Description |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| **Concordant Bullish** | `CONCORDANT_POS` | 26 | 1 | 1 | **28** | 196 | Both headline and core monthly pace accelerated. |
| **Concordant Bearish** | `CONCORDANT_NEG` | 30 | 2 | 0 | **32** | 224 | Both headline and core monthly pace cooled. |
| **Conflict: Head+ / Core-** | `CONFLICT_HEAD_POS_CORE_NEG` | 12 | 1 | 0 | **13** | 91 | Headline heated (energy/food shock), but core cooled. |
| **Conflict: Head- / Core+** | `CONFLICT_HEAD_NEG_CORE_POS` | 13 | 2 | 0 | **15** | 105 | Headline cooled (energy drop), but core inflation accelerated. |
| **Headline+ / Core Zero** | `HEAD_POS_CORE_ZERO` | 19 | 1 | 0 | **20** | 140 | Headline accelerated while core was unchanged. |
| **Headline- / Core Zero** | `HEAD_NEG_CORE_ZERO` | 16 | 0 | 0 | **16** | 112 | Headline cooled while core was unchanged. |
| **Headline Zero / Core+** | `HEAD_ZERO_CORE_POS` | 5 | 0 | 0 | **5** | 35 | Headline unchanged while core accelerated. |
| **Headline Zero / Core-** | `HEAD_ZERO_CORE_NEG` | 2 | 0 | 0 | **2** | 14 | Headline unchanged while core cooled. |
| **Both Zero** | `BOTH_ZERO` | 7 | 1 | 0 | **8** | 56 | Both headline and core monthly rates unchanged. |
| **Missing Anchor** | `MISSING_ANCHOR` | 1 | 0 | 0 | **1** | 7 | Release `2025.12.18` lacking m/m constituents. |
| **TOTAL** | — | **131** | **8** | **1** | **140** | **980** | Complete, closed accounting. |

---

## 8. Finite Proposed Next-Stage Comparison Plan (UNFROZEN)

### Mathematical Proof of Previous Candidate 4 Redundancy
In an earlier draft, Candidate 4 was described as trading concordant releases on mutual agreement and conflicting releases on core direction. Formally:
Let $S_{\text{head}} = \text{sign}(\Delta_{\text{headline\_mm}})$ and $S_{\text{core}} = \text{sign}(\Delta_{\text{core\_mm}})$.
Candidate 2 (Core-m/m-Led):
$$D_2 = \begin{cases} +1 & \text{if } S_{\text{core}} = \text{POSITIVE} \\ -1 & \text{if } S_{\text{core}} = \text{NEGATIVE} \\ 0 & \text{if } S_{\text{core}} \in \{\text{ZERO}, \text{MISSING}\} \end{cases}$$
The previous Candidate 4 was defined as:
$$D_4 = \begin{cases} 
+1 & \text{if } (S_{\text{head}}, S_{\text{core}}) \in \{(\text{POS}, \text{POS}), (\text{NEG}, \text{POS}), (\text{ZERO}, \text{POS})\} \\
-1 & \text{if } (S_{\text{head}}, S_{\text{core}}) \in \{(\text{NEG}, \text{NEG}), (\text{POS}, \text{NEG}), (\text{ZERO}, \text{NEG})\} \\
0 & \text{if } S_{\text{core}} \in \{\text{ZERO}, \text{MISSING}\}
\end{cases}$$
Because $\{S_{\text{head}} \in \{\text{POS}, \text{NEG}, \text{ZERO}\}\} \times \{S_{\text{core}} = \text{POS}\} \equiv \{S_{\text{core}} = \text{POS}\}$, and similarly for $\text{NEG}$, $D_4(\omega) \equiv D_2(\omega)$ across all releases $\omega$. That draft definition was a literal duplicate of Candidate 2.

### Four Genuinely Distinct Tradable Candidates (UNFROZEN)

To evaluate multi-series interaction without redundancy, the protocol proposes four distinct tradable candidate rules across in-scope releases:

| Candidate ID | Rule Name | Core Direction Mechanism | In-Cutoff Active Releases ($N$) | In-Cutoff Abstentions ($N$) | Pre-Outcome H60-Eligible Pair Observations ($N$) |
| --- | --- | --- | ---: | ---: | ---: |
| **Candidate 1** | **Headline m/m Benchmark** | $D_{\text{USD}} = \text{sign}(\Delta_{\text{headline\_mm}})$; zero/missing abstains | 123 | 16 | **859** |
| **Candidate 2** | **Core m/m Led** | $D_{\text{USD}} = \text{sign}(\Delta_{\text{core\_mm}})$; zero/missing abstains | 94 | 45 | **656** |
| **Candidate 3** | **Concordant Only** | Trades only when Headline and Core agree in sign; abstains on conflict or zero | 59 | 80 | **411** |
| **Candidate 4** | **Conflict-Filtered Headline** | Trades Concordant direction; trades Headline direction when Core is Zero; strictly abstains on Conflict | 95 | 44 | **663** |

*Note on Candidate 4 vs Candidate 2:*
- Candidate 2 trades all 28 conflicting releases (where Core is non-zero) and abstains on all 44 in-cutoff Core-Zero releases ($44 \times 7 = 308$ pair-observations).
- Candidate 4 trades all 36 in-cutoff Core-Zero releases where Headline is active ($36 \times 7 = 252$ pair-observations, $252 - 0 = 252$ pre-outcome H60-eligible observations), and strictly abstains on all 28 conflicting releases ($28 \times 7 = 196$ pair-observations).
- Their common releases are strictly the 59 in-cutoff concordant releases ($59 \times 7 = 413$ pair-observations, minus 2 entry-delay exclusions = **411** pre-outcome H60-eligible observations).
- Candidate 4 arithmetic: $95 \text{ active releases} \times 7 \text{ pairs} = 665 \text{ pair-observations} - 2 \text{ entry-delay exclusions} = \mathbf{663}$ pre-outcome H60-eligible pair observations.
- **Audited Entry-Delay Exclusions (Derived Directly from Ledger Rows):**
  - `2015.01.16 16:30:00` — `USDCHF` — delay 199,800s (`delay_seconds > 3600`, observed delay exceeding 3600s threshold; missing timely entry candle).
  - `2017.05.12 15:30:00` — `NZDUSD` — delay 235,800s (`delay_seconds > 3600`, observed delay exceeding 3600s threshold; missing timely entry candle).
  Both releases are concordant (`CONCORDANT_NEG` and `CONCORDANT_POS`), thus each excludes exactly 1 pair observation from Candidates 1, 2, 3, and 4 (2 pair observations total across each candidate), and 0 from the Conflict Sub-study.

### Dedicated Conflict-Only Descriptive Comparison Panel (UNFROZEN)

To directly evaluate the Director's inquiry into headline versus core priority on conflicting releases without presuming a winner or defaulting to "conflict = no trade", a dedicated **Conflict-Only Descriptive Sub-study** is evaluated strictly across the **28 conflicting release timestamps** (25 Core 2015–2025, 3 Partial 2026; exactly 196 pair-observations):

- **Conflict Sub-study A (Headline Dominant on Conflict):**  
  - On the 28 conflicting releases: $D_{\text{USD}} = \text{sign}(\Delta_{\text{headline\_mm}})$.
  - On the remaining 111 in-cutoff releases through August 2026 (110 non-conflicting + 1 absent-anchor `2025.12.18`): $D_{\text{USD}} = 0$ (Abstain).
  - Evaluates whether broad headline momentum dictates the price response despite core divergence.
- **Conflict Sub-study B (Core Dominant on Conflict):**  
  - On the 28 conflicting releases: $D_{\text{USD}} = \text{sign}(\Delta_{\text{core\_mm}})$.
  - On the remaining 111 in-cutoff releases through August 2026 (110 non-conflicting + 1 absent-anchor `2025.12.18`): $D_{\text{USD}} = 0$ (Abstain).
  - Evaluates whether underlying core momentum dictates the price response when headline is distorted by food/energy shocks.

This produces a direct, like-for-like counterfactual comparison across the identical 28 episodes ($N = 196$ pre-outcome H60-eligible pair observations), isolating the exact transmission of opposing signals on the May 2026 episode and all historical equivalents.

### Descriptive Role of Annual Rates (Headline & Core y/y)
- **Non-Equal Voting:** Year-on-year rates reflect 12-month base effects and cannot be treated as independent monthly momentum votes equivalent to m/m.
- **Initial Protocol Role:** Year-on-year signs (`Hy`, `Cy`) will initially be reported as **descriptive trend strata** alongside trade outcomes, rather than active direction gates.

### Within-Series Historical Percentile Rank (Proposed Design & Limitations)
If relative magnitude is investigated to resolve conflicts:
1. **Past-Only Window:** The percentile rank of $|\Delta_i|$ must be computed strictly over trailing historical releases of the same indicator prior to release ($t_{\text{historical}} < t_{\text{release}}$).
2. **Warmup Requirement:** Minimum trailing sample of 24 monthly releases. Releases prior to 2017 cannot have valid percentiles under a 24-month warmup.
3. **Rejection of 90-Day Context Window:** A 90-day window contains only ~3 monthly CPI releases, which is mathematically insufficient to estimate a percentile rank.
4. **Tie and Zero Policy:** Because Core m/m has 31.7% zero deltas, rank ties at zero must use fractional mid-ranks or explicit zero truncation.
5. **Percentile Rank $\ne$ Market Impact Weight:** A 90th percentile core change versus a 50th percentile headline change indicates statistical rarity within their respective series; it **does NOT prove** market participants weigh the core move with an 90:50 ratio.

---

## 9. Physical Path, Execution, and Gap Policy

- **Simulated Entry:** Earliest complete H1 bar with `bar_open > release_timestamp`. Delay from release must satisfy `delay_seconds <= 3600`.
- **Pre-Release ATR(14):** Wilder smoothed true range across 250 bars from 251 completed H1 candles strictly closing prior to release ($t_{\text{close}} < t_{\text{release}}$). Zero lookahead.
- **Holding Horizons:** H60 (60 H1 bars), H120 (120 H1 bars), H240 (240 H1 bars).
- **Session Gap Policy:** Weekday halts > 4 hours (14,400s) disqualify path (`excluded_path_gap_exceeded`).
- **ALL_ELIGIBLE vs COMMON_H240 Cohort Equivalence:** In the pinned V4 dataset, every in-cutoff pair observation has complete, gap-free 240-hour paths (zero missing bars, zero weekday gaps > 4 hours). Therefore, `ALL_ELIGIBLE` and `COMMON_H240` contain the **identical set of observations** across all pairs and candidates. Reporting both cohorts preserves schema conformity with V2 exploratory benchmarks, but does **not** constitute independent corroboration.

---

## 10. External Same-Time Collisions

Across the 140 CPI timestamps:
- **US Initial Jobless Claims (`840140001`):** Coincides on **33 timestamps** (32 where Headline m/m is present; 1 on `2025.12.18` where m/m is absent).
- **Real Earnings m/m (`840030030`):** Coincides on 138 timestamps.
- **Retail Sales (`840020010`):** Coincides on 12 timestamps.
- **Foreign Collisions:** Canadian releases (Building Permits, Manufacturing Sales, etc.) coincide on 2–16 timestamps.

### Primary vs Collision-Clean Sensitivity Panels
All candidate interpretations must be evaluated across:
1. **Full Panel:** In-cutoff m/m-anchor-present cohort ($N = 138$ bundles, 966 pair-observations).
2. **Claims-Clean Panel:** The subset of in-cutoff releases with zero coincidence with Initial Jobless Claims ($N = 106$ bundles with m/m present, 742 pair-observations).

---

## 11. Frozen Steering Decisions & Execution Governance

The following design decisions were explicitly **FROZEN** by Director steering prior to outcome execution:

1. **Selection Policy & Evaluation Scope:**  
   Option C frozen: The full 52-cell descriptive grid is evaluated across H60, H120, and H240 with `selection_policy = NONE`. Zero winning setup is selected, registered, or promoted to production.
2. **Evaluated Candidate & Sub-Study Universe:**  
   Candidates 1–4 evaluated exactly as specified, plus both directions of the Conflict-Only descriptive comparison (Sub-study A: Headline dominant vs Sub-study B: Core dominant) on the identical 28 conflicting releases.
3. **Primary Panel vs Collision Sensitivity:**  
   The primary evaluation basis is the Full In-Cutoff Panel ($N = 138$ bundles, 966 pair-observations). The Claims-Clean Panel ($N = 106$ bundles, 742 pair-observations) is evaluated in parallel as a separately labeled sensitivity panel.
4. **Later-Event Censoring:**  
   Deferred entirely to a subsequent dedicated study. Zero unapproved later-event censoring is applied to this run.
5. **Trial Space Accounting:**  
   All 465,036 simulated trials across the 6 comparisons, 3 horizons, and 52 cells are recorded in `trial_ledger.csv`, and full parameters are anchored in `manifest.json`.

---

## 12. Verification & Audit Checkpoint

- **Check 1 (Input Provenance):** All 15 input file hashes verified bit-for-bit against published raw index and pre-outcome hashes.
- **Check 2 (Constituent Reconciliation):** 140 unique bundle timestamps reconciled with exact constituent counts (558 total).
- **Check 3 (Anchor Integrity):** Missing m/m on `2025.12.18` cleanly excluded via `excluded_missing_anchor`. Zero silent substitution with y/y performed.
- **Check 4 (Universe Exclusions):** 9 globally excluded pairs strictly rejected with zero admitted trades.
- **Check 5 (Sample Audit):** Five representative sample cases independently recomputed from raw candles via `audit_raw_csv_ohlc.py` (zero outcome_engine dependencies):
  - Base-USD Pair (`2024.06.12 USDCAD` cell 1:2 H60): STOP on Bar 1 (`gross_r = -1.0000R`, `dual_touch = False`). **PASSED**
  - Quote-USD Pair (`2024.06.12 EURUSD` cell 1:2 H60): Dual touch on Bar 2 (High 1.08492 & Low 1.08172 touch both barriers). STOP-FIRST yields STOP (`gross_r = -1.0000R`), TARGET-FIRST yields TARGET (`gross_r = +2.0000R`), `dual_touch = True`. **PASSED**
  - Conflict Episode (`2026.05.12 EURUSD` cell 2:2 H60): Bar 1 touches lower barrier. Headline-led STOP (`-1.0R`) vs Core-led TARGET (`+1.0R`), `dual_touch = False`. **PASSED**
  - Timeout Episode (`2015.01.16 AUDUSD` cell 4:4 H60): TIMEOUT on Bar 60 (`gross_r = +0.1895R`, `dual_touch = False`). **PASSED**
  - Dual-Touch Ambiguity (`2015.12.15 EURUSD` cell 3:1 H60): Bar 29 dual-touch. STOP-FIRST `-1.0000R` vs TARGET-FIRST `+0.3333R`, `dual_touch = True`. **PASSED**
- **Check 6 (Automated Test Suite):** 17 pre-outcome tests (`test_cpi_bundle_inventory.py`) and 11 outcome tests (`test_cpi_bundle_outcomes.py`) pass 100%, reconciling all 29,952 summary rows and verifying target-first identities.
- **STOP DIRECTIVE:** Outcome simulation complete. Awaiting Project Director and Codex audit. Zero changes to HTML viewer or Terminal. Zero Git commits.
