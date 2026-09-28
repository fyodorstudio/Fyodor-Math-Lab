# Pre-Outcome Inventory & Eligibility Report: US CPI

> [!IMPORTANT]
> **PRE-OUTCOME AUDIT BOUNDARY:** This report assesses calendar constituent completeness, same-time collisions, timestamp-only entry and horizon path continuity, pre-release Wilder ATR(14) warmup, and candidate eligibility across the seven active USD pairs. It contains **zero event-linked price returns, zero ATR-barrier hits, zero backtests, and zero claims of trading profitability**.

---

## 1. Release Inventory & Audit Identity

- **Event Family:** US CPI  
- **Primary Anchor Indicator:** `CPI m/m` (Event ID: `840030005`)  
- **Raw Constituent Releases (N):** 558 across the 4 tracked series (dynamically verified from calendar).  
- **Unique Same-Time Bundles (N):** 140 release timestamps.  
- **Active USD Pair Denominator:** 140 bundles × 7 pairs = **980 pair-observations**.  
- **Globally Excluded Universe:** 9 pairs (`CADCHF, CADJPY, GBPAUD, GBPCAD, GBPJPY, GBPNZD, NZDCAD, NZDCHF, NZDJPY`) strictly excluded from all denominators (reason: `excluded_truncated_history`).  

### Annual Release Breakdown

| Year | Cohort Classification | Unique Bundles | Total Pair Observations | Anchor Present | Forecast Present | Previous Present | Revised Previous |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | CORE_2015_2025 | 12 | 84 | 12/12 | 0/12 | 12/12 | 0/12 |
| 2016 | CORE_2015_2025 | 12 | 84 | 12/12 | 0/12 | 12/12 | 0/12 |
| 2017 | CORE_2015_2025 | 12 | 84 | 12/12 | 8/12 | 12/12 | 7/12 |
| 2018 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 1/12 |
| 2019 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 1/12 |
| 2020 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 0/12 |
| 2021 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 1/12 |
| 2022 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 1/12 |
| 2023 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 1/12 |
| 2024 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 1/12 |
| 2025 | CORE_2015_2025 | 11 | 77 | 10/11 | 9/11 | 10/11 | 2/11 |
| 2026 | PARTIAL (8) + POST-CUTOFF (1) | 9 | 63 | 9/9 | 8/9 | 9/9 | 0/9 |

### Consensus Forecast Availability Audit

- **Anchor Indicator:** CPI m/m (`840030005`) strictly. (On `2025.12.18 16:30:00`, m/m anchor is absent from MT5 calendar records).
- **Missing Forecast Bundles:** Exactly **30 release bundles** where the m/m anchor is present have unpopulated forecasts in MT5.
  - **Pre-May-2017 Missingness:** 28 bundles from `2015.01.16` through `2017.04.14` (MT5 economic calendar consensus forecast coverage begins on `2017.05.12`).
  - **Post-May-2017 Missingness:** 2 subsequent bundles have unpopulated forecasts on `2025.10.24` and `2026.01.13`.
- **Integrity Note:** Post-May-2017 consensus forecast coverage is **not uninterrupted**. These unpopulated releases are explicitly excluded with `excluded_missing_forecast`.

### Same-Time Macroeconomic Collision Audit

- **US Initial Jobless Claims (`840140001`):** Exactly **33 release bundles** (32 where anchor `CPI m/m` is present) coincide at the exact same release timestamp on Thursday shifts.
  - **Clean vs Collision Breakdown:** Exactly 107 bundles have zero claims collision. For anchor-present releases, exactly 107 releases (107 bundles, 749 pair-obs) are completely claims-clean.
  - **Absent Anchor Coincidence:** The release on `2025.12.18 16:30:00 UTC` coincides with Jobless Claims, but CPI m/m is missing from MT5.
- **Canadian Employment Collisions:** Exactly 0 CPI releases collide with Statistics Canada Labour Force Survey releases.
- **US Trade Balance Collisions:** Exactly 0 CPI releases collide with US Trade Balance releases.

---

## 2. Path Coverage & Trading Session Gap Policy (All 7 Active USD Pairs)

| Active USD Pair | Role | Releases | Entry Found | Delay ≤ 3600s | Delay > 3600s | Pre-Release ATR(14) | H60 Path Gap-Free | H120 Path Gap-Free | H240 Path Gap-Free |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AUDUSD` | QUOTE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `EURUSD` | QUOTE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `GBPUSD` | QUOTE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `NZDUSD` | QUOTE | 140 | 140/140 | 139/140 | 1 | 140/140 | 140/140 | 140/140 | 140/140 |
| `USDCAD` | BASE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |
| `USDCHF` | BASE | 140 | 140/140 | 139/140 | 1 | 140/140 | 140/140 | 140/140 | 140/140 |
| `USDJPY` | BASE | 140 | 140/140 | 140/140 | 0 | 140/140 | 140/140 | 140/140 | 140/140 |

### Documented Trading Session & Gap Policy Findings

1. **Bounded Regular Weekend:** Friday evening (>= 20:00) to Sunday (>= 21:00) or Monday (<= 03:00), strictly bounded between 45.0 and 55.0 elapsed hours. Rejects extended outages (e.g. 10-day outage).
2. **Bounded Annual Holidays:** Christmas (Dec 22-25 to Dec 25-28, max 84.0h) and New Year (Dec 29-31 to Jan 1-4, max 84.0h). Rejects arbitrary weekday gaps (e.g. 6-day Dec 22-28 gap).
3. **Unscheduled Weekday Gaps:** Any unscheduled weekday gap > 4 hours (14,400s) during regular market hours disqualifies that horizon path.

#### Full-History Raw Candle Gaps vs. Event-Path Exclusions Audit (2014–2026)

A dynamic scan of all 7 active USD pairs across the loaded candle series using the tested market closure classifier identifies exactly 4 non-exempt raw gaps > 4 hours:

1. `GBPUSD`: `2019.09.30 23:00:00` -> `2019.10.02 00:00:00` (25.0h elapsed, 90,000s). 0 CPI event-path intersections.
2. `NZDUSD`: `2017.05.10 23:00:00` -> `2017.05.15 09:00:00` (106.0h elapsed, 381,600s). 0 CPI event-path intersections.
3. `USDCHF`: `2014.11.28 23:00:00` -> `2014.12.02 00:00:00` (73.0h elapsed, 262,800s). 0 CPI event-path intersections.
4. `USDCHF`: `2015.01.15 20:00:00` -> `2015.01.19 00:00:00` (76.0h elapsed, 273,600s). 0 CPI event-path intersections.

- **Event-Path Intersection Audit:**
  - **CPI Family:** Exactly **0** CPI event path(s) intersect any of these 4 gaps across all horizons (H60, H120, H240).
    All 980 CPI pair-observations with valid entry have 100% gap-free paths.

#### Entry Delay Findings (Derived from Ledger Rows)

- `NZDUSD` on `2017.05.12 15:30:00`: Next-H1 entry is `2017.05.15 09:00:00` (delay = 235,800s / 65.5h). The candle records show no bars between release and entry. Exceeds the 3600s cap.
- `USDCHF` on `2015.01.16 16:30:00`: Next-H1 entry is `2015.01.19 00:00:00` (delay = 199,800s / 55.5h). The candle records show no bars between release and entry. Exceeds the 3600s cap.
- *Summary:* All other 978 pair-observations have next-H1 entry delay ≤ 3600 seconds (typically 1800s).

#### Horizon Path Gap Exclusions (Derived from Observed Candle Paths)

- **Zero Path Gap Exclusions:** 100% of observations with valid entries have complete, gap-free paths across H60, H120, and H240.

---

## 3. Reconciled Primary Exclusions Table (Horizon H240)

Every pair-observation receives exactly one non-overlapping primary exclusion reason. Verified by strict assertion:
$$\text{Total Observations } (980) = \text{Eligible Candidate N} + \sum \text{Primary Exclusions}$$

### A − F Surprise Signal Exclusions (H240)

| Primary Exclusion Reason | Description | Core (2015–2025) | Partial (2026) | Post-Cutoff (2026) | Total Excluded |
| --- | --- | --- | --- | --- | --- |
| `excluded_entry_delay_exceeded` | Primary filter failure | 1 | 0 | 0 | **1** |
| `excluded_missing_anchor_cpi_mm` | Primary filter failure | 7 | 0 | 0 | **7** |
| `excluded_missing_forecast` | Primary filter failure | 203 | 7 | 0 | **210** |
| `excluded_post_2026_cutoff` | Primary filter failure | 0 | 0 | 7 | **7** |
| `excluded_zero_signal` | Primary filter failure | 63 | 21 | 0 | **84** |

### A − P Momentum Signal Exclusions (H240)

| Primary Exclusion Reason | Description | Core (2015–2025) | Partial (2026) | Post-Cutoff (2026) | Total Excluded |
| --- | --- | --- | --- | --- | --- |
| `excluded_entry_delay_exceeded` | Primary filter failure | 2 | 0 | 0 | **2** |
| `excluded_missing_anchor_cpi_mm` | Primary filter failure | 7 | 0 | 0 | **7** |
| `excluded_post_2026_cutoff` | Primary filter failure | 0 | 0 | 7 | **7** |
| `excluded_zero_signal` | Primary filter failure | 98 | 7 | 0 | **105** |

---

## 4. Reconciled Count Waterfall

Separating **Calendar N**, **Pair-Observation Denominator**, **Physical Path Coverage**, and **Eligible Candidate N**:

### Surprise Waterfall (A − F)

| Level | Waterfall Stage | Core 2015–2025 | Partial 2026 | Post-Cutoff 2026 | Total Full Dataset |
| --- | --- | --- | --- | --- | --- |
| 1. Raw Calendar Constituent Releases (N) | 522 | 32 | 4 | **558** |
| 2. Unique Same-Time Bundles (N) | 131 | 8 | 1 | **140** |
| 3. Signal-Complete Bundles (Anchor & Input Present) | 101 | 7 | 1 | **109** |
| 4. Fixed Pair-Observation Denominator (Bundles × 7) | 917 | 56 | 7 | **980** |
| 5. Non-Zero Signal Pair-Observations | 644 | 28 | 7 | **679** |
| 6. Valid Entry Observations (Delay ≤ 3600s) | 643 | 28 | 7 | **678** |
| 7. Pre-Release ATR(14) Warmup Complete (bar_close < t) | 643 | 28 | 7 | **678** |
| 8. Eligible Candidate Cohort: H60 (Gap Policy Enforced) | 643 | 28 | 0 | **671** |
| 9. Eligible Candidate Cohort: H120 (Gap Policy Enforced) | 643 | 28 | 0 | **671** |
| 10. Eligible Candidate Cohort: H240 (Gap Policy Enforced) | 643 | 28 | 0 | **671** |

### Momentum Waterfall (A − P)

| Level | Waterfall Stage | Core 2015–2025 | Partial 2026 | Post-Cutoff 2026 | Total Full Dataset |
| --- | --- | --- | --- | --- | --- |
| 1. Raw Calendar Constituent Releases (N) | 522 | 32 | 4 | **558** |
| 2. Unique Same-Time Bundles (N) | 131 | 8 | 1 | **140** |
| 3. Signal-Complete Bundles (Anchor & Input Present) | 130 | 8 | 1 | **139** |
| 4. Fixed Pair-Observation Denominator (Bundles × 7) | 917 | 56 | 7 | **980** |
| 5. Non-Zero Signal Pair-Observations | 812 | 49 | 7 | **868** |
| 6. Valid Entry Observations (Delay ≤ 3600s) | 810 | 49 | 7 | **866** |
| 7. Pre-Release ATR(14) Warmup Complete (bar_close < t) | 810 | 49 | 7 | **866** |
| 8. Eligible Candidate Cohort: H60 (Gap Policy Enforced) | 810 | 49 | 0 | **859** |
| 9. Eligible Candidate Cohort: H120 (Gap Policy Enforced) | 810 | 49 | 0 | **859** |
| 10. Eligible Candidate Cohort: H240 (Gap Policy Enforced) | 810 | 49 | 0 | **859** |

---

## 5. Summary of Verified Groundwork & Stop Point

1. **Zero Outcome Leaks:** No event-linked returns, barrier collisions, or simulated PnL were computed.
2. **Data Integrity Certifications:**
   - 9 excluded pairs strictly rejected and zero observations admitted.
   - Raw constituent releases: 558 dynamically verified.
   - All 140 bundles and 980 pair-observations accounted for bit-for-bit.
   - Documented session gap policy separates clean paths from contaminated weekday halts.
3. **Audit Status:** GROUNDWORK READY FOR CODEX REVIEW. Awaiting Project Director authorization on protocol decisions before executing any price trial.
