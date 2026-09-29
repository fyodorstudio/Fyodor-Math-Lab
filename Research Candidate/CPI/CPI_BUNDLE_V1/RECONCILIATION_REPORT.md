# USD CPI Same-Time Bundle V1: Count Reconciliation Report

> [!IMPORTANT]
> **PRE-OUTCOME RECONCILIATION AUDIT:** This report reconciles the exact counts derived directly from the pinned MT5 economic calendar export for the US CPI same-time bundle. It covers constituent presence, sign distributions, joint headline/core agreement, external collisions, and candidate eligibility waterfalls across the 7 active USD pairs. It contains **zero price returns, zero gross R, zero barrier touches, and zero candidate rankings**.

---

## 1. Rigorous Count Separation & Inventory Boundaries

The inventory is partitioned into strictly defined, non-overlapping count tiers:

1. **Total Pinned Calendar Inventory ($N = 140$ Bundles, $980$ Pair-Observations):**
   - All unique CPI release timestamps exported by MT5 in `calendar_releases.csv`.
   - Total Raw Constituent Rows: $558 = 139 + 139 + 140 + 140$.
   - Inventory Pair-Observations: $140 \text{ bundles} \times 7 \text{ active USD pairs} = \mathbf{980}$.

2. **In-Scope Research Cohort through August 2026 ($N = 139$ Bundles, $973$ Pair-Observations):**
   - Core full years 2015–2025: $\mathbf{131}$ bundles ($917$ pair-observations).
   - Partial year January–August 2026: $\mathbf{8}$ bundles ($56$ pair-observations).
   - Post-cutoff release: $\mathbf{1}$ bundle (`2026.09.11 15:30:00`, $7$ pair-observations), excluded solely by the predeclared August 31, 2026 research cutoff date.

3. **In-Scope Cohort with m/m Anchors Present ($N = 138$ Bundles, $966$ Pair-Observations):**
   - In-scope releases with Headline m/m and Core m/m anchors present: $139 - 1 = \mathbf{138}$ bundles.
   - Absent Anchor Release: `2025.12.18 16:30:00` lacks both m/m anchors in the MT5 export ($7$ pair-observations excluded).

4. **Initial Jobless Claims Collision Subsets (`840140001`):**
   - Total coincident Claims timestamps in full inventory: $\mathbf{33}$ timestamps.
   - Coincident Claims timestamps with Headline m/m present: $\mathbf{32}$ timestamps.
   - Coincident Claims timestamps on absent-anchor release (`2025.12.18`): $\mathbf{1}$ timestamp.
   - Clean in-scope bundles with m/m anchors present: $138 - 32 = \mathbf{106}$ bundles ($106 \times 7 = \mathbf{742}$ pair-observations).

5. **Candidate-Specific Pre-Outcome H60-Eligible Pair Observations:**
   - Pre-outcome eligible observation counts are **strictly smaller** than inventory N (980) and in-cutoff N (973/966) due to signal definitions, zero-momentum abstentions, and physical execution filters (these observations verify pre-release ATR warmup and gap-free path coverage, but contain zero exit prices or returns):
     - **Candidate 1 (Headline m/m Benchmark):** $\mathbf{859}$ pre-outcome H60-eligible pair observations (861 non-zero minus 2 entry-delay exclusions).
     - **Candidate 2 (Core m/m Led):** $\mathbf{656}$ pre-outcome H60-eligible pair observations (658 non-zero minus 2 entry-delay exclusions).
     - **Candidate 3 (Concordant Only):** $\mathbf{411}$ pre-outcome H60-eligible pair observations (413 concordant minus 2 entry-delay exclusions).
     - **Candidate 4 (Conflict-Filtered Headline):** $\mathbf{663}$ pre-outcome H60-eligible pair observations (665 pair-observations [95 active releases × 7] minus 2 entry-delay exclusions = 663).
     - **Conflict-Only Descriptive Sub-study:** $\mathbf{196}$ pre-outcome H60-eligible pair observations (196 conflict pair-observations across 28 releases; 0 entry-delay exclusions).
   - **Audited Entry-Delay Exclusions (Derived Directly from Ledger Rows):**
     - `2015.01.16 16:30:00` — `USDCHF` — delay 199,800s (`delay_seconds > 3600`, observed delay exceeding 3600s threshold; missing timely entry candle).
     - `2017.05.12 15:30:00` — `NZDUSD` — delay 235,800s (`delay_seconds > 3600`, observed delay exceeding 3600s threshold; missing timely entry candle).
     Both releases are concordant (`CONCORDANT_NEG` and `CONCORDANT_POS`), thus each excludes exactly 1 pair observation from Candidates 1, 2, 3, and 4 (2 pair observations total across each candidate), and 0 from the Conflict Sub-study.

---

## 2. Annual Release Distribution

| Year | Cohort Classification | Pinned Bundles | Pair Obs | Headline m/m | Core m/m | Headline y/y | Core y/y | Claims Coincidence (`840140001`) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2015 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 3 |
| 2016 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 4 |
| 2017 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 1 |
| 2018 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 4 |
| 2019 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 3 |
| 2020 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 3 |
| 2021 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 2 |
| 2022 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 4 |
| 2023 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 3 |
| 2024 | CORE_2015_2025 | 12 | 84 | 12/12 | 12/12 | 12/12 | 12/12 | 3 |
| 2025 | CORE_2015_2025 | 11 | 77 | 11/11 | 11/11 | 11/11 | 11/11 | 3 |
| 2026 | PARTIAL (8) + POST-CUTOFF (1) | 9 | 63 | 9/9 | 9/9 | 9/9 | 9/9 | 0 |

---

## 3. Constituent Presence & Sign Breakdown

| Series Name | Event ID | Present | Missing | Positive (A > P) | Negative (A < P) | Zero (A = P) | Total Deltas | Revised P Populated |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Headline CPI m/m | `840030005` | 139 | 1 | 61 | 63 | 15 | 139 | 15 |
| Core CPI m/m | `840030006` | 139 | 1 | 48 | 47 | 44 | 139 | 12 |
| Headline CPI y/y | `840030007` | 140 | 0 | 68 | 59 | 13 | 140 | 1 |
| Core CPI y/y | `840030008` | 140 | 0 | 47 | 56 | 37 | 140 | 1 |

> [!NOTE]
> **Core m/m Zero Inertia:** Core CPI m/m exhibits **44 zero deltas** (31.7% of its releases). Because core CPI m/m is reported to one decimal place, month-to-month changes frequently reproduce the preceding month's rate. A strategy requiring non-zero core momentum abstains on roughly one-third of releases.

---

## 4. Headline m/m vs Core m/m Joint Sign Matrix

Categorization of all 140 CPI release timestamps across the two month-on-month measures:

| Category | State Identifier | Total Bundles | Core (2015–2025) | Partial (2026) | Post-Cutoff (2026) | Pair Obs (×7) | Tradable Direction Proposal |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| **Concordant Bullish** | `CONCORDANT_POS` | 28 | 26 | 1 | 1 | 196 | USD Long (+1) |
| **Concordant Bearish** | `CONCORDANT_NEG` | 32 | 30 | 2 | 0 | 224 | USD Short (-1) |
| **Conflict: Head+ / Core-** | `CONFLICT_HEAD_POS_CORE_NEG` | 13 | 12 | 1 | 0 | 91 | Conflict Sub-study |
| **Conflict: Head- / Core+** | `CONFLICT_HEAD_NEG_CORE_POS` | 15 | 13 | 2 | 0 | 105 | Conflict Sub-study |
| **Head+ / Core Zero** | `HEAD_POS_CORE_ZERO` | 20 | 19 | 1 | 0 | 140 | Headline-led vs Abstain |
| **Head- / Core Zero** | `HEAD_NEG_CORE_ZERO` | 16 | 16 | 0 | 0 | 112 | Headline-led vs Abstain |
| **Head Zero / Core+** | `HEAD_ZERO_CORE_POS` | 5 | 5 | 0 | 0 | 35 | Core-led vs Abstain |
| **Head Zero / Core-** | `HEAD_ZERO_CORE_NEG` | 2 | 2 | 0 | 0 | 14 | Core-led vs Abstain |
| **Both Zero** | `BOTH_ZERO` | 8 | 7 | 1 | 0 | 56 | Strict Abstain (0) |
| **Missing Anchors** | `MISSING_ANCHOR` | 1 | 1 | 0 | 0 | 7 | Strict Exclusion (`2025.12.18`) |
| **TOTAL** | — | **140** | **131** | **8** | **1** | **980** | — |

---

## 5. Audit Clarifications & Anti-Hallucination Guardrails

1. **Silent Substitution Policy:**
   - **Silent substitution with y/y is STRICTLY FORBIDDEN.**
   - When Headline m/m (`840030005`) or Core m/m (`840030006`) is missing from a bundle (specifically on `2025.12.18 16:30:00`), m/m candidate evaluations strictly assign `excluded_missing_anchor`.
   - Zero silent substitution with y/y is performed or tolerated.

2. **Timing of Information & Signals:**
   - **Pre-Release Volatility:** Wilder ATR(14) inputs must strictly precede release ($t_{\text{close}} < t_{\text{release}}$). Zero release bar or post-release candle affects volatility.
   - **Signal Availability & Timing:** Actual ($A$) is known at the release timestamp ($t = t_{\text{release}}$) and is assumed available for entry by the end of the release bar / start of the H1 entry bar ($t_{\text{entry}} > t_{\text{release}}$, typically 30 minutes after release). However, a static historical economic calendar export cannot prove live network latency or order-routing transmission times, nor can it establish whether any Previous revision was visible to market participants prior to or only upon the release timestamp. The signal is not claimed to be known prior to release.

3. **Exclusion of the September 2026 Release (`2026.09.11`):**
   - The release on `2026.09.11 15:30:00` has complete H240 bar coverage and gap-free paths in the raw V4 export.
   - It is excluded from the research cohort **solely by the predeclared August 31, 2026 release cutoff date** (`excluded_post_2026_cutoff`).

---

## 6. Ledger Verification Hashes

The active pre-outcome run files under `run_20260930_pre_outcome_v2/` (and preserved historical run `run_20260930_pre_outcome/`) are indexed with fail-closed SHA-256 hashes:

### Active Pre-Outcome Artifacts (Version 2 - Full Float Precision ATR)
| Filename | Row Count | SHA-256 Checksum | Storage Tier |
| --- | --- | --- | --- |
| `cpi_bundle_ledger.csv` | 140 (141 lines) | `55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE` | Local run directory (Git-ignored) |
| `cpi_pair_expanded_ledger.csv` | 980 (981 lines) | `3A5ECA2CED0131EC923C790D43E4BCDB883E91DDB10B6EDD592FCAC3E83263F9` | Local run directory (Git-ignored) |
| `manifest.json` | — | (in package) | Local run directory (Git-ignored) |
| `SCHEMA.md` | — | (tracked) | Tracked in Git |
| `RECONCILIATION_REPORT.md` | — | (tracked) | Tracked in Git |

### Preserved Historical Pre-Outcome Artifacts (Version 1 - Six-Decimal ATR)
| Filename | Row Count | SHA-256 Checksum | Description |
| --- | --- | --- | --- |
| `cpi_bundle_ledger.csv` | 140 (141 lines) | `55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE` | Preserved historical V1 bundle ledger |
| `cpi_pair_expanded_ledger.csv` | 980 (981 lines) | `3B8A75B853A07F7F1BBE0CC1D30CCA269311C6E700EE61843B1521D5E8C4ECBB` | Preserved historical V1 pair ledger (.6f ATR) |

---

## 7. Audit Conclusion & Stop Point

Pre-outcome inventory and reconciliation for `USD_CPI_BUNDLE_V1` is complete and verified directly against the raw export on disk. **Zero price outcomes, gross R metrics, barrier touches, or trade simulations have been performed.** This groundwork is submitted for Director and Codex review.
