# Pre-Outcome Inventory & Eligibility Report: US NFP

> [!IMPORTANT]
> **PRE-OUTCOME AUDIT BOUNDARY:** This report assesses calendar constituent completeness, same-time collisions, timestamp-only entry and horizon path continuity, pre-release Wilder ATR(14) warmup, and candidate eligibility across the seven active USD pairs. It contains **zero event-linked price returns, zero ATR-barrier hits, zero backtests, and zero claims of trading profitability**.

---

## 1. Release Inventory & Audit Identity

- **Event Family:** US NFP  
- **Primary Anchor Indicator:** `Nonfarm Payrolls` (Event ID: `840030016`)  
- **Raw Constituent Releases (N):** 560 across the 4 tracked series (dynamically verified from calendar).  
- **Unique Same-Time Bundles (N):** 140 release timestamps.  
- **Active USD Pair Denominator:** 140 bundles × 7 pairs = **980 pair-observations**.  
- **Globally Excluded Universe:** 9 pairs (`CADCHF, CADJPY, GBPAUD, GBPCAD, GBPJPY, GBPNZD, NZDCAD, NZDCHF, NZDJPY`) strictly excluded from all denominators (reason: `excluded_truncated_history`).  

### Annual Release Breakdown

| Year | Cohort Classification | Unique Bundles | Total Pair Observations | Anchor Present | Forecast Present | Previous Present | Revised Previous |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | CORE_2015_2025 | 12 | 84 | 12/12 | 0/12 | 12/12 | 12/12 |
| 2016 | CORE_2015_2025 | 12 | 84 | 12/12 | 0/12 | 12/12 | 12/12 |
| 2017 | CORE_2015_2025 | 12 | 84 | 12/12 | 8/12 | 12/12 | 12/12 |
| 2018 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 |
| 2019 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 |
| 2020 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 |
| 2021 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 |
| 2022 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 11/12 |
| 2023 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 11/12 |
| 2024 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 |
| 2025 | CORE_2015_2025 | 11 | 77 | 11/11 | 11/11 | 11/11 | 11/11 |
| 2026 | PARTIAL (8) + POST-CUTOFF (1) | 9 | 63 | 9/9 | 9/9 | 9/9 | 9/9 |

### Consensus Forecast Availability Audit

- **Anchor Indicator:** Nonfarm Payrolls (`840030016`) strictly (all 140 release bundles present).
- **Missing Forecast Bundles:** Exactly **28 release bundles** where the payrolls anchor is present have unpopulated forecasts in MT5.
  - **Pre-May-2017 Missingness:** All 28 occurrences run from `2015.01.09` through `2017.04.07`.
- **Integrity Note:** From the first populated forecast on `2017.05.05` through August 2026, Nonfarm Payrolls forecast coverage in MT5 is uninterrupted.

### Same-Time Macroeconomic Collision Audit

- **Canadian Employment (`124010011` / `124010014`):** Exactly **89 of 140 release bundles** coincide with Statistics Canada Labour Force Survey releases at the exact same release minute.
  - *USDCAD Impact:* For USDCAD, exactly 51 releases (51 bundles, 357 pair-obs) are CAD-employment clean.
- **US Initial Jobless Claims (`840140001`):** Exactly **4 release bundles** coincide on Thursday holiday shifts ahead of July 4th Independence Day (`2015.07.02`, `2020.07.02`, `2025.07.03`, `2026.07.02`).
- **US Trade Balance (`840020001`):** Exactly **26 release bundles** coincide with US Trade Balance releases.

---

## 2. Path Coverage & Trading Session Gap Policy (All 7 Active USD Pairs)

| Active USD Pair | Role | Releases | Entry Found | Delay ≤ 3600s | Delay > 3600s | Pre-Release ATR(14) | H60 Path Gap-Free | H120 Path Gap-Free | H240 Path Gap-Free |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AUDUSD` | QUOTE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `EURUSD` | QUOTE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `GBPUSD` | QUOTE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `NZDUSD` | QUOTE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 139/140 | 139/140 |
| `USDCAD` | BASE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `USDCHF` | BASE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 139/140 | 139/140 |
| `USDJPY` | BASE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |

### Documented Trading Session & Gap Policy Findings

1. **Bounded Regular Weekend:** Friday evening (>= 20:00) to Sunday (>= 21:00) or Monday (<= 03:00), strictly bounded between 45.0 and 55.0 elapsed hours. Rejects extended outages (e.g. 10-day outage).
2. **Bounded Annual Holidays:** Christmas (Dec 22-25 to Dec 25-28, max 84.0h) and New Year (Dec 29-31 to Jan 1-4, max 84.0h). Rejects arbitrary weekday gaps (e.g. 6-day Dec 22-28 gap).
3. **Unscheduled Weekday Gaps:** Any unscheduled weekday gap > 4 hours (14,400s) during regular market hours disqualifies that horizon path.

#### Full-History Raw Candle Gaps vs. Event-Path Exclusions Audit (2014–2026)

A dynamic scan of all 7 active USD pairs across the loaded candle series using the tested market closure classifier identifies exactly 4 non-exempt raw gaps > 4 hours:

1. `GBPUSD`: `2019.09.30 23:00:00` -> `2019.10.02 00:00:00` (25.0h elapsed, 90,000s). 0 NFP event-path intersections.
2. `NZDUSD`: `2017.05.10 23:00:00` -> `2017.05.15 09:00:00` (106.0h elapsed, 381,600s). Intersects NFP release(s) `2017.05.05 15:30:00` (disqualifying H120/H240 paths).
3. `USDCHF`: `2014.11.28 23:00:00` -> `2014.12.02 00:00:00` (73.0h elapsed, 262,800s). 0 NFP event-path intersections.
4. `USDCHF`: `2015.01.15 20:00:00` -> `2015.01.19 00:00:00` (76.0h elapsed, 273,600s). Intersects NFP release(s) `2015.01.09 16:30:00` (disqualifying H120/H240 paths).

- **Event-Path Intersection Audit:**
  - **NFP Family:** Exactly **2** NFP event path(s) intersect any of these 4 gaps across all horizons (H60, H120, H240).
    Disqualifies H120 and H240 paths for the affected observation(s). The remaining 2 raw candle gaps fall entirely outside all NFP observation paths.

#### Entry Delay Findings (Derived from Ledger Rows)

- **Zero Abnormal Delays:** All 980 pair-observations across all 7 pairs have next-H1 entry delay ≤ 3600 seconds (typically 1800s).

#### Horizon Path Gap Exclusions (Derived from Observed Candle Paths)

- `NFP / NZDUSD` on `2017.05.05 15:30:00`:
  - *H60 Path:* Eligible.
  - *H120 Path:* Disqualified (`excluded_path_gap_exceeded`).
  - *H240 Path:* Disqualified (`excluded_path_gap_exceeded`).
- `NFP / USDCHF` on `2015.01.09 16:30:00`:
  - *H60 Path:* Eligible.
  - *H120 Path:* Disqualified (`excluded_path_gap_exceeded`).
  - *H240 Path:* Disqualified (`excluded_path_gap_exceeded`).
- *Causal Attribution Guardrail:* The candle records establish the existence and duration of these gaps, not their external causes. No unsourced historical events are assumed.

---

## 3. Reconciled Primary Exclusions Table (Horizon H240)

Every pair-observation receives exactly one non-overlapping primary exclusion reason. Verified by strict assertion:
$$\text{Total Observations } (980) = \text{Eligible Candidate N} + \sum \text{Primary Exclusions}$$

### A − F Surprise Signal Exclusions (H240)

| Primary Exclusion Reason | Description | Core (2015–2025) | Partial (2026) | Post-Cutoff (2026) | Total Excluded |
| --- | --- | --- | --- | --- | --- |
| `excluded_missing_forecast` | Primary filter failure | 196 | 0 | 0 | **196** |
| `excluded_path_gap_exceeded` | Primary filter failure | 1 | 0 | 0 | **1** |
| `excluded_post_2026_cutoff` | Primary filter failure | 0 | 0 | 7 | **7** |

### A − P Momentum Signal Exclusions (H240)

| Primary Exclusion Reason | Description | Core (2015–2025) | Partial (2026) | Post-Cutoff (2026) | Total Excluded |
| --- | --- | --- | --- | --- | --- |
| `excluded_path_gap_exceeded` | Primary filter failure | 2 | 0 | 0 | **2** |
| `excluded_post_2026_cutoff` | Primary filter failure | 0 | 0 | 7 | **7** |
| `excluded_zero_signal` | Primary filter failure | 7 | 0 | 0 | **7** |

---

## 4. Reconciled Count Waterfall

Separating **Calendar N**, **Pair-Observation Denominator**, **Physical Path Coverage**, and **Eligible Candidate N**:

### Surprise Waterfall (A − F)

| Level | Waterfall Stage | Core 2015–2025 | Partial 2026 | Post-Cutoff 2026 | Total Full Dataset |
| --- | --- | --- | --- | --- | --- |
| 1. Raw Calendar Constituent Releases (N) | 524 | 32 | 4 | **560** |
| 2. Unique Same-Time Bundles (N) | 131 | 8 | 1 | **140** |
| 3. Signal-Complete Bundles (Anchor & Input Present) | 103 | 8 | 1 | **112** |
| 4. Fixed Pair-Observation Denominator (Bundles × 7) | 917 | 56 | 7 | **980** |
| 5. Non-Zero Signal Pair-Observations | 721 | 56 | 7 | **784** |
| 6. Valid Entry Observations (Delay ≤ 3600s) | 721 | 56 | 7 | **784** |
| 7. Pre-Release ATR(14) Warmup Complete (bar_close < t) | 721 | 56 | 7 | **784** |
| 8. Eligible Candidate Cohort: H60 (Gap Policy Enforced) | 721 | 56 | 0 | **777** |
| 9. Eligible Candidate Cohort: H120 (Gap Policy Enforced) | 720 | 56 | 0 | **776** |
| 10. Eligible Candidate Cohort: H240 (Gap Policy Enforced) | 720 | 56 | 0 | **776** |

### Momentum Waterfall (A − P)

| Level | Waterfall Stage | Core 2015–2025 | Partial 2026 | Post-Cutoff 2026 | Total Full Dataset |
| --- | --- | --- | --- | --- | --- |
| 1. Raw Calendar Constituent Releases (N) | 524 | 32 | 4 | **560** |
| 2. Unique Same-Time Bundles (N) | 131 | 8 | 1 | **140** |
| 3. Signal-Complete Bundles (Anchor & Input Present) | 131 | 8 | 1 | **140** |
| 4. Fixed Pair-Observation Denominator (Bundles × 7) | 917 | 56 | 7 | **980** |
| 5. Non-Zero Signal Pair-Observations | 910 | 56 | 7 | **973** |
| 6. Valid Entry Observations (Delay ≤ 3600s) | 910 | 56 | 7 | **973** |
| 7. Pre-Release ATR(14) Warmup Complete (bar_close < t) | 910 | 56 | 7 | **973** |
| 8. Eligible Candidate Cohort: H60 (Gap Policy Enforced) | 910 | 56 | 0 | **966** |
| 9. Eligible Candidate Cohort: H120 (Gap Policy Enforced) | 908 | 56 | 0 | **964** |
| 10. Eligible Candidate Cohort: H240 (Gap Policy Enforced) | 908 | 56 | 0 | **964** |

---

## 5. Summary of Verified Groundwork & Stop Point

1. **Zero Outcome Leaks:** No event-linked returns, barrier collisions, or simulated PnL were computed.
2. **Data Integrity Certifications:**
   - 9 excluded pairs strictly rejected and zero observations admitted.
   - Raw constituent releases: 560 dynamically verified.
   - All 140 bundles and 980 pair-observations accounted for bit-for-bit.
   - Documented session gap policy separates clean paths from contaminated weekday halts.
3. **Audit Status:** GROUNDWORK READY FOR CODEX REVIEW. Awaiting Project Director authorization on protocol decisions before executing any price trial.
