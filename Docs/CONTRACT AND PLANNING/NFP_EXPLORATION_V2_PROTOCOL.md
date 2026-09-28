# Research Protocol: US NFP Historical Exploration (V2)

**Protocol Identifier:** `NFP_EXPLORATION_V2`
**Supersedes:** `NFP_EXPLORATION_V1` (Frozen 2026-09-28, Commit `5a11760`)
**Status:** FROZEN EXPLORATORY PROTOCOL (NO SETUP REGISTRATION)
**Contract Baseline:** `Docs/CONTRACT AND PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md` (Amended `selection_policy = NONE`)
**Pre-Outcome Groundwork:** V4 Snapshot (`raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server`)
**Pre-Outcome Ledger Path:** `Research Candidate/NFP/pre_outcome_ledger_nfp_v2.csv`
**Pre-Outcome Ledger SHA-256:** `157970C1788CE7CDD47291BCC9E94898E33559FD73FC7503BD7ED821483007CB`
**Candidate Package Target:** `Research Candidate/NFP/NFP_EXPLORATION_V2/run_20260928_v2/`

---

## 1. Explicit Invalidation of Exploration V1

The V1 exploratory artifacts (`Research Candidate/NFP/NFP_EXPLORATION_V1/`) are preserved locally on the pre-publication archive branch, but excluded from the publishable Git branch because of their large ledgers. They are formally **INVALIDATED** for decision-making due to four audited forensic defects:

1. **Failure to Enforce USDCAD Primary Policy:** The contract stipulated that CAD-employment-clean USDCAD must serve as the primary panel for USDCAD, and the primary all-pairs panel must include only CAD-clean USDCAD. V1 pooled unconditioned USDCAD into its primary tables, obscuring massive CAD macro variance.
2. **Narrative Inconsistencies:** The V1 narrative manually claimed that USDCAD CAD-clean had a gross mean R of $+0.1429$, whereas the actual computed ledger value was $-0.071429$ (13 wins out of 42 trades, $-3$ gross R).
3. **Typographical Claims Event ID:** V1 implemented US Initial Jobless Claims as `840014001` instead of `840140001`, failing to properly identify the 4 Thursday NFP claims collisions (`2015.07.02`, `2020.07.02`, `2025.07.03`, `2026.07.02`).
4. **Erroneous LOYO & Pooled Distributions:** V1 used median yearly return rather than true leave-one-year-out aggregate recomputation, and pooled win/loss exit bars into a single distribution.

---

## 2. Pinned Universe, Anchor Series, and Raw Calendar Groundwork

- **Active USD Universe (7 Pairs):** `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`.
- **Strictly Excluded Pairs (9 Pairs):** `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY` (truncated broker history; denominator strictly 0).
- **Primary Anchor Series:** `Nonfarm Payrolls` (Event ID `840030016`, Sector: Jobs, Multiplier: Thousands, Unit: Jobs).
  - All 140 NFP releases contain the anchor series. Forecast coverage in MT5 begins on `2017.05.05` and is uninterrupted thereafter (28 releases pre-May-2017 lack forecasts).
- **Coincident Collision Audit:**
  - **Canadian Employment (`124010011` / `124010014`):** Exactly **89 of 140 releases** collide with Statistics Canada Labour Force Survey releases at the exact same release minute.
  - **US Initial Jobless Claims (`840140001`):** Exactly **4 releases** coincide on Thursday holiday shifts (`2015.07.02`, `2020.07.02`, `2025.07.03`, `2026.07.02`).
  - **US Trade Balance (`840020001`):** Exactly **26 releases** coincide.
- **Total Pair-Observation Denominator:** Exactly $140 \text{ bundles} \times 7 \text{ pairs} = \mathbf{980}$ pair-observations.

---

## 3. Direction Hypotheses & Signal States

- **Surprise Signal ($S = A - F$):** Actual minus Consensus Forecast.
  - $S > 0 \implies$ USD Strength ($+1$).
  - $S < 0 \implies$ USD Weakness ($-1$).
  - $S = 0 \implies$ Zero Surprise (Abstain, `excluded_zero_or_neutral_signal`).
  - $F \text{ is None} \implies$ Missing Forecast (`excluded_missing_forecast`). Exactly 28 releases lack forecasts.
- **Momentum Signal ($M = A - P$):** Actual minus Unrevised Previous.
  - $M > 0 \implies$ USD Strength ($+1$).
  - $M < 0 \implies$ USD Weakness ($-1$).
  - $M = 0 \implies$ Zero Momentum (Abstain, `excluded_zero_or_neutral_signal`).
- **Pair Direction Mapping:**
  - Base USD Pairs (`USDCAD`, `USDCHF`, `USDJPY`): Pair Direction = USD Direction.
  - Quote USD Pairs (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`): Pair Direction = $-1 \times \text{USD Direction}$.

---

## 4. Physical Path & Execution Constraints

- **Entry Bar Selection:** First completed H1 candle strictly following release timestamp: $\text{bar\_open} > T_{\text{release}}$.
- **Entry Delay Cap:** Entry bar open must occur within $\le 3600\text{s}$ of release. Releases with delay $> 3600\text{s}$ excluded (`excluded_abnormal_entry_delay`).
- **Pre-Release ATR(14) Warmup:**
  - Calculated from 250 true ranges across 251 completed H1 bars prior to release.
  - Strict zero lookahead: $\text{bar\_open} + 3600 < T_{\text{release}}$.
- **Physical Expiry Horizons:**
  - H60: 60 completed H1 bars ($60 \text{ hours of observed market trading}$).
  - H120: 120 completed H1 bars.
  - H240: 240 completed H1 bars.
- **Physical Gap Policy:**
  - Unscheduled weekday halts $> 4\text{ hours}$ (14,400s) disqualify path (`excluded_path_gap_exceeded`).
  - *Pinned Row:* `USDCHF` on `2015.01.09` is eligible at H60, but crosses a 76-hour unscheduled broker gap (`2015.01.12 17:00` to `2015.01.15 21:00`), disqualifying it from H120 and H240.

---

## 5. Primary Attribution Panels & Canadian Employment Policy

To eliminate cross-currency contamination:

1. **USDCAD Standalone Reporting:**
   - **Primary Panel:** **CAD-Employment-Clean USDCAD** ($N=51$ bundles, 42 candidate-eligible trades at H60).
   - **Sensitivity Panel:** **Full USDCAD** ($N=140$ bundles, 111 candidate-eligible trades at H60).
2. **All Pairs Combined Reporting:**
   - **Primary Panel:** 6 Other Eligible Pairs (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCHF`, `USDJPY`) + **CAD-Clean USDCAD** ($N=708$ trades at H60 for A−F).
   - **Sensitivity Panel:** Full 7-Pair Panel including all USDCAD observations ($N=777$ trades at H60 for A−F).
3. **Macro Independence Representation:**
   - Summary tables report both pair-observation counts ($N_{\text{trades}}$) and unique macroeconomic release counts ($N_{\text{releases}}$). Cross-sectional pair observations are explicitly documented as correlated expressions of a single USD shock, not independent statistical events.

---

## 6. 52-Cell Exploratory Grid & Barrier Arithmetic

- **Stop ATR Multiples:** $S \in \{1.0, 2.0, 3.0, 4.0\}$.
- **Target ATR Multiples:** $T \in \{1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00\}$.
- **Total Grid Cells:** Exactly 52 cells per horizon (156 cell-horizon combinations per signal).
- **Intrabar Resolution:**
  - **Primary Bound:** `STOP_FIRST`.
  - **Sensitivity Bound:** `TARGET_FIRST`.
- **Cost Independence:** Pure gross OHLC arithmetic. Zero spread, slippage, or financing deducted. Never called "net profit".

---

## 7. Upgraded Statistical Summary & Attribution Specifications

1. **True Leave-One-Year-Out (LOYO):**
   - 11 folds evaluated per cell, each excluding one full calendar year $Y \in [2015, 2025]$.
   - Metric outputs: `loyo_positive_years`, `loyo_min_mean_r`, `loyo_max_mean_r`, `loyo_min_sum_r`, `loyo_max_sum_r`.
   - Partial year 2026 strictly excluded from LOYO and reported separately.
2. **Year-by-Year Annual Ledger:**
   - Complete annual accounting for years 2015..2025 and partial 2026.
3. **Separate TP-Only and SL-Only Duration Distributions (Trading Bars and Wall-Clock Time):**
   - For Wins (TP hits): $N_{\text{wins}}$, median bars, 75th percentile, 90th percentile, maximum bars; and wall-clock proxy seconds (`tp_bar_close_proxy_seconds_median`, `p75`, `p90`, `max`).
   - For Losses (SL hits): $N_{\text{losses}}$, median bars, 75th percentile, 90th percentile, maximum bars; and wall-clock proxy seconds (`sl_bar_close_proxy_seconds_median`, `p75`, `p90`, `max`).
   - For Timeouts: $N_{\text{timeouts}}$, bars ($H$).
   - **Wall-Clock Duration Accounting:** Trading bars count only observed broker sessions. Across weekends and scheduled closures, actual elapsed wall-clock time is measured from entry bar open ($T_{\text{entry}}$) to exit bar open and close:
     - For **opening-gap exits** (`TARGET_GAP`, `STOP_GAP`), execution is at the bar open (the gap price is observable at open): both `clock_seconds_to_bar_open` and `clock_seconds_bar_close_proxy` are set to $T_{\text{bar\_open}} - T_{\text{entry}}$ (exact, not a proxy).
     - For **intrabar touch exits** (`TARGET`, `STOP`), the exact sub-hour touch timestamp is unknown: `clock_seconds_to_bar_open` is the lower bound ($T_{\text{bar\_open}} - T_{\text{entry}}$) and `clock_seconds_bar_close_proxy` is the upper-bound proxy ($T_{\text{bar\_close}} - T_{\text{entry}}$).
     - For **timeout exit** at close of Bar $H_{\text{max}}$, the exit duration is exact: $T_{\text{exit\_bar\_close}} - T_{\text{entry}}$.
4. **Common H240-Complete Cohort:**
   - Evaluated across H60, H120, H240 on the subset of trades with complete, gap-free paths through Bar 240.
5. **Programmatic Report Verification:**
   - All figures in `EXPLORATION_SUMMARY_REPORT.md` must be dynamically verified against `summary_grid_results.csv`. Zero hardcoded narrative text.

---

## 8. Versioned Artifact Layout & Storage

Target package layout:
```
Research Candidate/NFP/NFP_EXPLORATION_V2/run_20260928_v2/
  manifest.json
  release_paths.csv
  trial_ledger.csv
  summary_grid_results.csv
  annual_breakdown.csv
  loyo_folds.csv
  EXPLORATION_SUMMARY_REPORT.md
```
- **High-Precision Bounded Serialization:** Numerical fields are serialized with high-precision bounded representations: 8 decimals for ATR and Gross R (`.8f`), 4 decimals for Pips (`.4f`), 6 decimals for Prices (`.6f`), and integer seconds for clock timestamps. Never described as "unrounded" fixed-point.
- **Reproducible Aggregate Basis (audit amendment after rejected first run):** Barrier outcomes use unrounded source prices and ATR. All published aggregate R metrics and categorical LOYO positive-fold counts are then calculated from the same eight-decimal trade R values written to `trial_ledger.csv`. This prevents an effectively zero fold from changing sign only because the verifier reads the published ledger. The rejected first-run package is preserved and must not be treated as validated evidence.
- **Serialization-Aware Verification Bounds:** The verifier compares trial-ledger-derived values against the published aggregates with *no relative tolerance*. A field printed to `d` decimal places has at most $0.5\times10^{-d}$ output-rounding error. An aggregate of $N$ trade-R values also allows at most $N\times0.5\times10^{-8}$ input-rounding error because trial R is stored to eight decimals; a $10^{-10}$ floating-point margin is added. Thus four-decimal R sums and summary-grid LOYO extrema permit $0.00005+N\times0.000000005+10^{-10}$ for sums (one input-rounding unit for means); six-decimal gross R means/medians and LOYO-fold means permit $0.0000005+0.000000005+10^{-10}$; four-decimal rates permit $0.00005+10^{-10}$; one-decimal bar statistics permit $0.05+10^{-10}$; whole-second clock statistics permit $0.5+10^{-10}$. These bounds reflect serialization, not market uncertainty or an acceptable change in the underlying result.
- **Fail-Closed Immutability & Independent Verification:** Output directory cannot be overwritten (`check_package_immutability`). Independent read-only verification is supported via CLI (`python run_exploration_pipeline.py --verify-only --family NFP --run-id <run_id>`), which recomputes and reconciles 100% of summary grid results, annual breakdowns, and LOYO folds from the trial ledger with zero writes to disk.
