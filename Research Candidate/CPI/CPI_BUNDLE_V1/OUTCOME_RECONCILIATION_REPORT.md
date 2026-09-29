# USD CPI Same-Time Bundle V1: Outcome Reconciliation Report

**Protocol Identifier:** `USD_CPI_BUNDLE_V1`  
**Active Run Target:** `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes_v3/` (Local / Git-ignored)  
**Date Generated:** 2026-09-29T21:41:01.711227+00:00  
**Baseline Git Commit:** `1bc93052cf59b1a37589bd528725d07414b69af0`  
**Code Status:** `UNCOMMITTED (working tree on baseline 1bc93052cf59b1a37589bd528725d07414b69af0)`  
**Selection Policy:** `NONE` (Zero setup registration; full grid reported; HTML viewer and Trading Terminal untouched)  

> [!IMPORTANT]
> **AUDIT BOUNDARY & SELECTION INTEGRITY:**  
> This document records the complete, unoptimized outcome evaluation of the USD CPI same-time bundle across all four proposed candidate interpretations, plus the two directions of the Conflict-Only descriptive sub-study. No winning rule is selected, no setup is registered in the terminal, and no HTML viewer modifications have been made.

---

## 1. Provenance & Dependency Hashes

### Pinned Raw Inputs & Pre-Outcome Ledgers (Verified Fail-Closed)
- `manifest.csv`: `1E7C8A5047BDEDAF0F66DE23F5E6CC382C29EA839B9E07A911789BBFFC548A6F`
- `calendar_releases.csv`: `FCB68E1C2A6269D98287F4BEDBEE1F3BCB5A8C99379502782359EDFD20E83D6F`
- `cpi_bundle_ledger.csv`: `55F28DA8D1205693F147E47EC4BEF7D1132A510627B96E5006FA059173FC15BE`
- `cpi_pair_expanded_ledger.csv` (V2 Full-Precision ATR): `3A5ECA2CED0131EC923C790D43E4BCDB883E91DDB10B6EDD592FCAC3E83263F9`
- Active 7-Pair H1 Candle Exports: All 7 SHA-256 checksums verified bit-for-bit.

### Calculation Dependencies (Uncommitted Working Tree Hashes)
| Dependency File | Size (Bytes) | SHA-256 Checksum | Role |
| --- | ---: | --- | --- |
| `run_cpi_bundle_outcomes.py` | 69,881 | `37DED8DBF8350531D151298F189365076248B76573A27F28AF4E7CF95C4977AB` | Calculation dependency |
| `outcome_engine.py` | 41,423 | `319E337E85524E6ED8508C3974C31EE7B91735E4A3244D4506AC847A0CDDBEAF` | Calculation dependency |
| `audit_raw_csv_ohlc.py` | 22,659 | `AA4D380DB26C7B953796FE4BD70028F0C06A4BB0505ED089E3829506350D20C2` | Calculation dependency |
| `data_loader.py` | 10,859 | `A130AB2B052222BFBD584759446DF2FD5FFCA814920813588C4BB89D73BACC9B` | Calculation dependency |
| `path_indexer.py` | 8,597 | `FFA074FE7B7723D5ADC68A2129E628A62F1689BD40E5703D3E7C8AFF1F1BBD68` | Calculation dependency |
| `protocol_specs.py` | 6,475 | `DF044F631A6D9AF0706341221DC068826408BCB01641E29B012884021FB50955` | Calculation dependency |
| `models.py` | 5,592 | `E292679339EA045F2ED226C8C3EC4634C0261CE2710AC9B99E7E3221A647E255` | Calculation dependency |
| `generate_cpi_bundle_inventory.py` | 64,686 | `216FC2BE0EDCA461DD0562A84D534B295034D15FE694E06611843FF9A7876374` | Calculation dependency |

### Generated Local Outcome Artifacts (`run_20260930_outcomes_v3/`)
| Artifact File | Size (Bytes) | SHA-256 Checksum | Description |
| --- | ---: | --- | --- |
| `trial_ledger.csv` | 252,623,985 | `3C468999F7F876B1DC9ED01E278B389990A73E41F28141F0815C7E504F83273F` | Generated output |
| `summary_grid_results.csv` | 13,452,063 | `0F28962DF6A717264AB8194B88416CCD739BF55299187E7571313902DB669777` | Generated output |
| `annual_breakdown.csv` | 44,700,610 | `3DAC97108850021396A15E823B7E5CE3FC8D81E122C20B1D3097938FCF3E3DC1` | Generated output |
| `loyo_folds.csv` | 37,051,471 | `816EA0171452B030839AD243CD79691602B76D964A8E34265F558AE540AE3B86` | Generated output |
| `v2_to_v3_comparison.json` | 952 | `176C65A3D1D62FC50CD2BDCF3769E0C49A4D8C08EC2C54711AF39A214227BEC9` | Generated output |

---

## 1.1 Machine-Readable V2-to-V3 Run Comparison (Full-Precision Round-Trip ATR Audit)

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
| **Changed Summary Cell Outcome Counts** | **1856** | Summary cells reflecting the 246 trial classification shifts |
| **Summary Cells with Float Precision Shift** | 5,642 | Max abs delta in Gross Mean R: `0.0427360000R`; Max abs delta in Gross Sum R: `3.02750000R` |

---

## 2. Denominator Accounting & Cohort Invariant

- **Total Raw CPI Inventory:** 140 release timestamps (980 pair-observations).
- **In-Cutoff Releases (through 2026.08.31):** 139 release timestamps (973 pair-observations).
- **In-Cutoff with m/m Anchor Present:** 138 release timestamps (966 pair-observations). Excludes `2025.12.18` (missing m/m anchor; zero silent substitution with y/y).
- **Physical Entry-Delay Exclusions:** Exactly 2 in-cutoff observations exceeded 3600s delaycap (missing timely entry candle):
  - `2015.01.16 16:30:00` — `USDCHF` — delay 199,800s (`CONCORDANT_NEG`).
  - `2017.05.12 15:30:00` — `NZDUSD` — delay 235,800s (`CONCORDANT_POS`).

> [!NOTE]
> **ALL_ELIGIBLE vs COMMON_H240 COHORT EQUIVALENCE:**  
> In this dataset, every in-cutoff pair observation has complete, gap-free 240-hour paths (zero missing bars, zero weekday gaps > 4 hours). Therefore, `ALL_ELIGIBLE` and `COMMON_H240` contain the **identical set of observations** across all pairs and candidates. Reporting both cohorts preserves schema conformity with V2 exploratory benchmarks, but does **not** constitute independent corroboration.

| Comparison Identifier | Full Panel Bundles (N) | Full Panel Trades (N) | Claims-Clean Bundles (N) | Claims-Clean Trades (N) | Core Mechanism |
| --- | ---: | ---: | ---: | ---: | --- |
| **Candidate 1 (Headline m/m Benchmark)** | 123 | **859** | 96 | **670** | $D_{\text{USD}} = \text{sign}(\Delta_{\text{head}})$; zero/missing abstains |
| **Candidate 2 (Core m/m Led)** | 94 | **656** | 74 | **516** | $D_{\text{USD}} = \text{sign}(\Delta_{\text{core}})$; zero/missing abstains |
| **Candidate 3 (Concordant Only)** | 59 | **411** | 51 | **355** | Trades only on mutual agreement; abstains on conflict or zero |
| **Candidate 4 (Conflict-Filtered Headline)** | 95 | **663** | 77 | **537** | Trades concordant + core-zero headline; strictly abstains on conflict |
| **Conflict Sub-study A (Headline Dominant)** | 28 | **196** | 19 | **133** | On 28 conflict releases: $D_{\text{USD}} = \text{sign}(\Delta_{\text{head}})$; abstains elsewhere |
| **Conflict Sub-study B (Core Dominant)** | 28 | **196** | 19 | **133** | On 28 conflict releases: $D_{\text{USD}} = \text{sign}(\Delta_{\text{core}})$; abstains elsewhere |

---

## 3. Benchmark ATR Barrier Grid Outcomes (H60 Primary)

In all tables below, **Gross Mean R (R per trade)** is rigorously separated from **Gross Sum R (Total cumulative R)**. Target-First sensitivity is explicitly reported.

### Primary Full Panel (All 7 Active USD Pairs Combined, H60, ALL_ELIGIBLE)

| Comparison | N (Trades) | Cell 1:1 (Mean R / Sum R) | Cell 1:2 (Mean R / Sum R) | Cell 2:2 (Mean R / Sum R) | Cell 2:4 (Mean R / Sum R) | Cell 3:3 (Mean R / Sum R) |
| --- | ---: | --- | --- | --- | --- | --- |
| **Candidate 1 (Headline Benchmark)** | 859 | Mean: `-0.0873R` / Sum: `-75.0R` (WR 45.6%, TF Mean: `+0.0640R`) | Mean: `-0.0291R` / Sum: `-25.0R` (WR 32.4%, TF Mean: `+0.0338R`) | Mean: `-0.0058R` / Sum: `-5.0R` (WR 49.7%, TF Mean: `+0.0058R`) | Mean: `+0.0546R` / Sum: `+46.9R` (WR 33.0%, TF Mean: `+0.0581R`) | Mean: `-0.0044R` / Sum: `-3.8R` (WR 47.7%, TF Mean: `+0.0003R`) |
| **Candidate 2 (Core Led)** | 656 | Mean: `-0.1341R` / Sum: `-88.0R` (WR 43.3%, TF Mean: `+0.0366R`) | Mean: `-0.0854R` / Sum: `-56.0R` (WR 30.5%, TF Mean: `-0.0122R`) | Mean: `-0.0610R` / Sum: `-40.0R` (WR 47.0%, TF Mean: `-0.0488R`) | Mean: `-0.0050R` / Sum: `-3.3R` (WR 30.5%, TF Mean: `-0.0004R`) | Mean: `-0.0522R` / Sum: `-34.2R` (WR 45.0%, TF Mean: `-0.0492R`) |
| **Candidate 3 (Concordant Only)** | 411 | Mean: `-0.2214R` / Sum: `-91.0R` (WR 38.9%, TF Mean: `-0.0122R`) | Mean: `-0.1679R` / Sum: `-69.0R` (WR 27.7%, TF Mean: `-0.0657R`) | Mean: `-0.0657R` / Sum: `-27.0R` (WR 46.7%, TF Mean: `-0.0511R`) | Mean: `-0.0306R` / Sum: `-12.6R` (WR 30.4%, TF Mean: `-0.0233R`) | Mean: `-0.0658R` / Sum: `-27.0R` (WR 45.7%, TF Mean: `-0.0609R`) |
| **Candidate 4 (Conflict-Filtered)** | 663 | Mean: `-0.0980R` / Sum: `-65.0R` (WR 45.1%, TF Mean: `+0.0769R`) | Mean: `-0.0588R` / Sum: `-39.0R` (WR 31.4%, TF Mean: `+0.0181R`) | Mean: `-0.0317R` / Sum: `-21.0R` (WR 48.4%, TF Mean: `-0.0196R`) | Mean: `+0.0042R` / Sum: `+2.8R` (WR 31.7%, TF Mean: `+0.0088R`) | Mean: `-0.0289R` / Sum: `-19.1R` (WR 47.1%, TF Mean: `-0.0228R`) |
| **Conflict Sub-study A (Headline)** | 196 | Mean: `-0.0510R` / Sum: `-10.0R` (WR 47.4%, TF Mean: `+0.0204R`) | Mean: `+0.0714R` / Sum: `+14.0R` (WR 35.7%, TF Mean: `+0.0867R`) | Mean: `+0.0816R` / Sum: `+16.0R` (WR 54.1%, TF Mean: `+0.0918R`) | Mean: `+0.2250R` / Sum: `+44.1R` (WR 37.2%, TF Mean: `+0.2250R`) | Mean: `+0.0784R` / Sum: `+15.4R` (WR 50.0%, TF Mean: `+0.0784R`) |
| **Conflict Sub-study B (Core)** | 196 | Mean: `-0.0204R` / Sum: `-4.0R` (WR 49.0%, TF Mean: `+0.0510R`) | Mean: `-0.0051R` / Sum: `-1.0R` (WR 33.2%, TF Mean: `+0.0255R`) | Mean: `-0.0918R` / Sum: `-18.0R` (WR 45.4%, TF Mean: `-0.0816R`) | Mean: `+0.0621R` / Sum: `+12.2R` (WR 31.6%, TF Mean: `+0.0621R`) | Mean: `-0.0784R` / Sum: `-15.4R` (WR 40.8%, TF Mean: `-0.0784R`) |

### Claims-Clean Sensitivity Panel (All 7 Active USD Pairs Combined, H60, ALL_ELIGIBLE)

| Comparison | N (Trades) | Cell 1:1 (Mean R / Sum R) | Cell 1:2 (Mean R / Sum R) | Cell 2:2 (Mean R / Sum R) | Cell 2:4 (Mean R / Sum R) | Cell 3:3 (Mean R / Sum R) |
| --- | ---: | --- | --- | --- | --- | --- |
| **Candidate 1 (Headline Benchmark)** | 670 | Mean: `-0.1104R` / Sum: `-74.0R` (WR 44.5%, TF Mean: `+0.0358R`) | Mean: `-0.0642R` / Sum: `-43.0R` (WR 31.2%, TF Mean: `-0.0060R`) | Mean: `+0.0030R` / Sum: `+2.0R` (WR 50.1%, TF Mean: `+0.0090R`) | Mean: `+0.0606R` / Sum: `+40.6R` (WR 33.9%, TF Mean: `+0.0606R`) | Mean: `-0.0020R` / Sum: `-1.3R` (WR 48.5%, TF Mean: `+0.0010R`) |
| **Candidate 2 (Core Led)** | 516 | Mean: `-0.1783R` / Sum: `-92.0R` (WR 41.1%, TF Mean: `-0.0039R`) | Mean: `-0.1512R` / Sum: `-78.0R` (WR 28.3%, TF Mean: `-0.0756R`) | Mean: `-0.0814R` / Sum: `-42.0R` (WR 45.9%, TF Mean: `-0.0736R`) | Mean: `-0.0317R` / Sum: `-16.4R` (WR 30.6%, TF Mean: `-0.0317R`) | Mean: `-0.0816R` / Sum: `-42.1R` (WR 44.2%, TF Mean: `-0.0816R`) |
| **Candidate 3 (Concordant Only)** | 355 | Mean: `-0.2676R` / Sum: `-95.0R` (WR 36.6%, TF Mean: `-0.0761R`) | Mean: `-0.2394R` / Sum: `-85.0R` (WR 25.4%, TF Mean: `-0.1465R`) | Mean: `-0.0873R` / Sum: `-31.0R` (WR 45.6%, TF Mean: `-0.0817R`) | Mean: `-0.0892R` / Sum: `-31.7R` (WR 28.5%, TF Mean: `-0.0892R`) | Mean: `-0.0931R` / Sum: `-33.0R` (WR 44.2%, TF Mean: `-0.0931R`) |
| **Candidate 4 (Conflict-Filtered)** | 537 | Mean: `-0.1099R` / Sum: `-59.0R` (WR 44.5%, TF Mean: `+0.0503R`) | Mean: `-0.0782R` / Sum: `-42.0R` (WR 30.7%, TF Mean: `-0.0112R`) | Mean: `-0.0056R` / Sum: `-3.0R` (WR 49.7%, TF Mean: `-0.0019R`) | Mean: `+0.0076R` / Sum: `+4.1R` (WR 31.8%, TF Mean: `+0.0076R`) | Mean: `-0.0141R` / Sum: `-7.6R` (WR 48.0%, TF Mean: `-0.0103R`) |
| **Conflict Sub-study A (Headline)** | 133 | Mean: `-0.1128R` / Sum: `-15.0R` (WR 44.4%, TF Mean: `-0.0226R`) | Mean: `-0.0075R` / Sum: `-1.0R` (WR 33.1%, TF Mean: `+0.0150R`) | Mean: `+0.0376R` / Sum: `+5.0R` (WR 51.9%, TF Mean: `+0.0526R`) | Mean: `+0.2748R` / Sum: `+36.5R` (WR 42.1%, TF Mean: `+0.2748R`) | Mean: `+0.0469R` / Sum: `+6.2R` (WR 50.4%, TF Mean: `+0.0469R`) |
| **Conflict Sub-study B (Core)** | 133 | Mean: `+0.0226R` / Sum: `+3.0R` (WR 51.1%, TF Mean: `+0.1128R`) | Mean: `+0.0827R` / Sum: `+11.0R` (WR 36.1%, TF Mean: `+0.1278R`) | Mean: `-0.0526R` / Sum: `-7.0R` (WR 47.4%, TF Mean: `-0.0376R`) | Mean: `+0.1818R` / Sum: `+24.2R` (WR 38.3%, TF Mean: `+0.1818R`) | Mean: `-0.0469R` / Sum: `-6.2R` (WR 45.1%, TF Mean: `-0.0469R`) |

---

## 4. Conflict-Only Descriptive Sub-Study & Regime Fragility

### Direct Counterfactual Comparison on Identical 28 Conflicting Releases (N=196 Trades)

| Evaluation Cell & Horizon | Sub-study A: Headline Dominant | Sub-study B: Core Dominant | Win Rate (Head vs Core) | Delta Mean R (Head - Core) | Delta Sum R (Head - Core) |
| --- | --- | --- | ---: | ---: | ---: |
| H60 Cell 1:1 | Mean: `-0.0510R` (Sum: `-10.0R`) | Mean: `-0.0204R` (Sum: `-4.0R`) | 47.4% vs 49.0% | **`-0.0306R`** | **`-6.0R`** |
| H60 Cell 1:2 | Mean: `+0.0714R` (Sum: `+14.0R`) | Mean: `-0.0051R` (Sum: `-1.0R`) | 35.7% vs 33.2% | **`+0.0765R`** | **`+15.0R`** |
| H60 Cell 2:2 | Mean: `+0.0816R` (Sum: `+16.0R`) | Mean: `-0.0918R` (Sum: `-18.0R`) | 54.1% vs 45.4% | **`+0.1735R`** | **`+34.0R`** |
| H60 Cell 2:4 | Mean: `+0.2250R` (Sum: `+44.1R`) | Mean: `+0.0621R` (Sum: `+12.2R`) | 37.2% vs 31.6% | **`+0.1629R`** | **`+31.9R`** |
| H60 Cell 3:3 | Mean: `+0.0784R` (Sum: `+15.4R`) | Mean: `-0.0784R` (Sum: `-15.4R`) | 50.0% vs 40.8% | **`+0.1567R`** | **`+30.7R`** |
| H120 Cell 1:1 | Mean: `-0.0510R` (Sum: `-10.0R`) | Mean: `-0.0204R` (Sum: `-4.0R`) | 47.4% vs 49.0% | **`-0.0306R`** | **`-6.0R`** |
| H120 Cell 1:2 | Mean: `+0.0714R` (Sum: `+14.0R`) | Mean: `-0.0051R` (Sum: `-1.0R`) | 35.7% vs 33.2% | **`+0.0765R`** | **`+15.0R`** |
| H120 Cell 2:2 | Mean: `+0.0816R` (Sum: `+16.0R`) | Mean: `-0.0918R` (Sum: `-18.0R`) | 54.1% vs 45.4% | **`+0.1735R`** | **`+34.0R`** |
| H120 Cell 2:4 | Mean: `+0.2051R` (Sum: `+40.2R`) | Mean: `+0.0738R` (Sum: `+14.5R`) | 39.8% vs 35.7% | **`+0.1313R`** | **`+25.7R`** |
| H120 Cell 3:3 | Mean: `+0.0903R` (Sum: `+17.7R`) | Mean: `-0.0903R` (Sum: `-17.7R`) | 53.6% vs 44.9% | **`+0.1807R`** | **`+35.4R`** |
| H240 Cell 1:1 | Mean: `-0.0510R` (Sum: `-10.0R`) | Mean: `-0.0204R` (Sum: `-4.0R`) | 47.4% vs 49.0% | **`-0.0306R`** | **`-6.0R`** |
| H240 Cell 1:2 | Mean: `+0.0714R` (Sum: `+14.0R`) | Mean: `-0.0051R` (Sum: `-1.0R`) | 35.7% vs 33.2% | **`+0.0765R`** | **`+15.0R`** |
| H240 Cell 2:2 | Mean: `+0.0816R` (Sum: `+16.0R`) | Mean: `-0.0918R` (Sum: `-18.0R`) | 54.1% vs 45.4% | **`+0.1735R`** | **`+34.0R`** |
| H240 Cell 2:4 | Mean: `+0.2054R` (Sum: `+40.2R`) | Mean: `+0.0714R` (Sum: `+14.0R`) | 39.8% vs 35.7% | **`+0.1339R`** | **`+26.2R`** |
| H240 Cell 3:3 | Mean: `+0.0987R` (Sum: `+19.4R`) | Mean: `-0.0987R` (Sum: `-19.4R`) | 54.6% vs 44.9% | **`+0.1975R`** | **`+38.7R`** |

### Severe Regime Concentration: 2022 Shock in Conflict Sub-study A (H60 Cell 2:4)

While Conflict Sub-study A appears profitable overall at H60 Cell 2:4 (**Gross Mean R = +0.225030R**, **Gross Sum R = +44.1058R**, N=196 trades across 28 release bundles), inspection of its annual breakdown reveals **extreme concentration in calendar year 2022**:

| Calendar Year | Cohort | Bundles (N) | Trades (N) | Wins | Losses | Timeouts | Win Rate | Gross Sum R | Gross Mean R (R per trade) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2015 | CORE_2015_2025 | 5 | 35 | 5 | 25 | 5 | 14.3% | `-8.2039R` | `-0.2344R` |
| 2016 | CORE_2015_2025 | 3 | 21 | 2 | 16 | 3 | 9.5% | `-11.9965R` | `-0.5713R` |
| 2017 | CORE_2015_2025 | 3 | 21 | 6 | 15 | 0 | 28.6% | `-3.0000R` | `-0.1429R` |
| 2018 | CORE_2015_2025 | 2 | 14 | 7 | 6 | 1 | 50.0% | `+9.7333R` | `+0.6952R` |
| 2019 | CORE_2015_2025 | 1 | 7 | 3 | 4 | 0 | 42.9% | `+2.0000R` | `+0.2857R` |
| 2020 | CORE_2015_2025 | 1 | 7 | 0 | 7 | 0 | 0.0% | `-7.0000R` | `-1.0000R` |
| 2021 | CORE_2015_2025 | 1 | 7 | 2 | 5 | 0 | 28.6% | `-1.0000R` | `-0.1429R` |
| **2022** | **CORE_2015_2025** | **4** | **28** | **22** | **5** | **1** | **78.6%** | **`+40.0300R`** | **`+1.4296R`** |
| 2023 | CORE_2015_2025 | 3 | 21 | 8 | 13 | 0 | 38.1% | `+3.0000R` | `+0.1429R` |
| 2025 | CORE_2015_2025 | 2 | 14 | 10 | 4 | 0 | 71.4% | `+16.0000R` | `+1.1429R` |
| 2026 | PARTIAL_2026 | 3 | 21 | 8 | 12 | 1 | 38.1% | `+4.5428R` | `+0.2163R` |
| **TOTAL** | — | **28** | **196** | **73** | **107** | **16** | **37.2%** | **`+44.1058R`** | **`+0.225030R`** |

> [!WARNING]
> **LEAVE-ONE-YEAR-OUT (LOYO) YEAR-REMOVAL STABILITY CHECK:**  
> Year 2022 accounts for **+40.0300R of the total +44.1058R (90.8% of cumulative gross return across all 196 trades)**.  
> - **Full Sample Excluding 2022 (2015–2026, 24 release bundles, N=168 trades):** Gross Sum R = **+4.0758R** (Gross Mean R = `+0.024261R`, about +4.08R).  
> - **Core Cohort LOYO Fold Excluding 2022 (2015–2025 closed years, 21 release bundles, N=147 trades):** Gross Sum R = **-0.4671R** (Gross Mean R = `-0.003177R`), flipping the closed-year baseline negative.  
> 
> LOYO is strictly a **year-removal stability check** measuring historical regime sensitivity, not independent out-of-sample validation. Headline dominance on conflicting releases is highly regime-dependent, driven almost entirely by the unprecedented post-pandemic inflation shock of 2022.

---

## 5. Dual-Touch Distribution & Concordance Reality Check

### Empirical Dual-Touch Rates Across the ATR Grid (Candidate 1 H60 Full Panel)
The assumption of a blanket '5–10%' dual-touch frequency is empirically false. Dual-touch frequency is strictly a function of barrier geometry:
- **Tight Stops & Targets (e.g. 1:1):** 65 / 859 trades (**7.57%** dual touch).
- **Asymmetric Targets (e.g. 1:2):** 18 / 859 trades (**2.10%** dual touch).
- **Moderate Stops (e.g. 2:2):** 5 / 859 trades (**0.58%** dual touch).
- **Wide Stops (e.g. 3:3):** 2 / 859 trades (**0.23%** dual touch).
- **Wide Stops (e.g. 4:4):** Exactly 0 / 859 trades (**0.00%** dual touch).

### Concordance Reality Check: Candidate 3 vs Candidate 1
Filtering for headline/core concordance does **NOT** eliminate losses or improve risk-adjusted returns:
- **Cell 1:1:** Candidate 3 Mean R = `-0.2214R` (Sum `-91.0R`, WR 38.9%) vs Candidate 1 Mean R = `-0.0873R` (Sum `-75.0R`, WR 45.6%).
- **Cell 1:2:** Candidate 3 Mean R = `-0.1679R` (Sum `-69.0R`, WR 27.7%) vs Candidate 1 Mean R = `-0.0291R` (Sum `-25.0R`, WR 32.4%).
- **Cell 2:2:** Candidate 3 Mean R = `-0.0657R` (Sum `-27.0R`, WR 46.7%) vs Candidate 1 Mean R = `-0.0058R` (Sum `-5.0R`, WR 49.7%).
- **Cell 2:4:** Candidate 3 Mean R = `-0.0306R` (Sum `-12.6R`, WR 30.4%) vs Candidate 1 Mean R = `+0.0546R` (Sum `+46.9R`, WR 33.0%).

**Why Concordance Fails:** Because Core m/m exhibits 31.7% zero deltas (due to 1-decimal rounding inertia), requiring concordant confirmation forces abstention on 36 valid, strongly-trending releases where headline accelerated or cooled while core was unchanged.

---

## 6. Genuinely Independent Raw-CSV OHLC Audit & Production-Ledger Verification

The five showcased episodes below were computed by `audit_raw_csv_ohlc.py`, a genuinely standalone raw-CSV parser that does **not** import `outcome_engine.py` or call `simulate_single_trade`:

| Case ID | Pair & Release Timestamp | Barrier Cell | Signal Direction | Observed Candle Execution | First Touched Bar | Dual Touch? | STOP-FIRST Outcome | TARGET-FIRST Sensitivity | Status |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| **1. Base-USD Pair** | `USDCAD` 2024.06.12 15:30:00 | 1:2 (H60) | Short USD $\implies$ Short USDCAD | Bar 1 High 1.36989 touches Stop 1.36978 | Bar 1 | **No** | `STOP` (`-1.0000R`) | `STOP` (`-1.0000R`) | **PASSED** |
| **2. Quote-USD Pair** | `EURUSD` 2024.06.12 15:30:00 | 1:2 (H60) | Short USD $\implies$ Long EURUSD | Bar 2 High 1.08492 & Low 1.08172 touch both | Bar 2 | **YES** | `STOP` (`-1.0000R`) | `TARGET` (`+2.0000R`) | **PASSED** |
| **3. Conflict Episode** | `EURUSD` 2026.05.12 15:30:00 | 2:2 (H60) | Head Long vs Core Short | Bar 1 Low 1.17264 touches Lower Barrier 1.17277 | Bar 1 | **No** | Head: `STOP` (`-1.0R`)<br>Core: `TARGET` (`+1.0R`) | Head: `STOP` (`-1.0R`)<br>Core: `TARGET` (`+1.0R`) | **PASSED** |
| **4. Timeout Episode** | `AUDUSD` 2015.01.16 16:30:00 | 4:4 (H60) | Long AUDUSD | 60 bars complete without touch; Close=0.81921 | Bar 60 | **No** | `TIMEOUT` (`+0.1895R`) | `TIMEOUT` (`+0.1895R`) | **PASSED** |
| **5. Dual-Touch Ambiguity** | `EURUSD` 2015.12.15 16:30:00 | 3:1 (H60) | Long EURUSD | Bar 29 High 1.10116 & Low 1.08878 touch both | Bar 29 | **YES** | `STOP` (`-1.0000R`) | `TARGET` (`+0.3333R`) | **PASSED** |

### Direct Source-to-Ledger Row Verification (`verify_audit_against_trial_ledger`)

To ensure absolute calculation integrity without circular validation, `verify_audit_against_trial_ledger` reads the production `trial_ledger.csv` and cross-verifies all 10 independent raw-CSV fields directly against production output:

| Case Label | Production Trial ID | Entry Open | Raw ATR(14) | Nominal Stop | Nominal Target | Exit Bar | Dual Touch? | SF Outcome (R) | TF Outcome (R) | Match Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| **1_BASE_USD_PAIR** | `CANDIDATE_1_HEADLINE_MM_USD_CPI_BUNDLE_1718206200_USDCAD_60_1:2` | `1.36900` | `0.000784` | `1.36978` | `1.36743` | Bar 1 | **False** | `STOP` (`-1.0000R`) | `STOP` (`-1.0000R`) | **SOURCE_TO_LEDGER_MATCH_VERIFIED** |
| **2_QUOTE_USD_PAIR** | `CANDIDATE_1_HEADLINE_MM_USD_CPI_BUNDLE_1718206200_EURUSD_60_1:2` | `1.08262` | `0.000798` | `1.08182` | `1.08422` | Bar 2 | **True** | `STOP` (`-1.0000R`) | `TARGET` (`+2.0000R`) | **SOURCE_TO_LEDGER_MATCH_VERIFIED** |
| **3_CONFLICT_HEADLINE** | `CONFLICT_SUBSTUDY_A_HEADLINE_USD_CPI_BUNDLE_1778599800_EURUSD_60_2:2` | `1.17471` | `0.000972` | `1.17277` | `1.17665` | Bar 1 | **False** | `STOP` (`-1.0000R`) | `STOP` (`-1.0000R`) | **SOURCE_TO_LEDGER_MATCH_VERIFIED** |
| **3_CONFLICT_CORE** | `CONFLICT_SUBSTUDY_B_CORE_USD_CPI_BUNDLE_1778599800_EURUSD_60_2:2` | `1.17471` | `0.000972` | `1.17665` | `1.17277` | Bar 1 | **False** | `TARGET` (`+1.0000R`) | `TARGET` (`+1.0000R`) | **SOURCE_TO_LEDGER_MATCH_VERIFIED** |
| **4_TIMEOUT_EPISODE** | `CANDIDATE_1_HEADLINE_MM_USD_CPI_BUNDLE_1421425800_AUDUSD_60_4:4` | `0.81768` | `0.002018` | `0.80961` | `0.82575` | Bar 60 | **False** | `TIMEOUT` (`+0.1895R`) | `TIMEOUT` (`+0.1895R`) | **SOURCE_TO_LEDGER_MATCH_VERIFIED** |
| **5_DUAL_TOUCH_EPISODE** | `CANDIDATE_1_HEADLINE_MM_USD_CPI_BUNDLE_1450197000_EURUSD_60_3:1` | `1.09575` | `0.002090` | `1.08948` | `1.09784` | Bar 29 | **True** | `STOP` (`-1.0000R`) | `TARGET` (`+0.3333R`) | **SOURCE_TO_LEDGER_MATCH_VERIFIED** |
---

## 7. Audit Summary & Explicit Stop Directive

1. **Full Grid Evaluated:** All 52 cells across H60, H120, and H240 are evaluated with both Stop-First and Target-First metrics recorded in `summary_grid_results.csv` (29,952 rows).
2. **Selection Policy `NONE`:** No winner selected, no setup registered, and no HTML viewer modified.
3. **Code Status:** Uncommitted working tree on baseline commit `1bc93052cf59b1a37589bd528725d07414b69af0`.

```
STATUS: PASS — AWAITING CODEX AND PROJECT DIRECTOR STEERING AUDIT
```
