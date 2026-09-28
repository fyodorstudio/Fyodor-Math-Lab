# Research Protocol: US CPI Historical Exploration (V2)

**Protocol Identifier:** `CPI_EXPLORATION_V2`
**Supersedes:** `CPI_EXPLORATION_V1` (Frozen 2026-09-28, Commit `5a11760`)
**Status:** FROZEN EXPLORATORY PROTOCOL (NO SETUP REGISTRATION)
**Contract Baseline:** `Docs/CONTRACT AND PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md` (Amended `selection_policy = NONE`)
**Pre-Outcome Groundwork:** V4 Snapshot (`raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server`)
**Pre-Outcome Ledger Path:** `Research Candidate/CPI/pre_outcome_ledger_cpi_v2.csv`
**Pre-Outcome Ledger SHA-256:** `29AC66F511736121A0A588221DF2A5D8C816722D9C79F9E72FF99C9FE28F0B66`
**Candidate Package Target:** `Research Candidate/CPI/CPI_EXPLORATION_V2/run_20260928_v2/`

---

## 1. Explicit Invalidation of Exploration V1

The V1 exploratory artifacts (`Research Candidate/CPI/CPI_EXPLORATION_V1/`) are preserved locally on the pre-publication archive branch, but excluded from the publishable Git branch because of their large ledgers. They are formally **INVALIDATED** for decision-making due to four audited forensic defects:

1. **Typographical Collision Event ID:** V1 implemented US Initial Jobless Claims as `840014001` instead of the verified MT5 calendar event ID `840140001`. Consequently, the V1 collision evaluator identified zero claims collisions, and the "clean" panel in V1 was identical to the full panel.
2. **False Narrative Collision Counts:** The V1 narrative reported "20 CPI release bundles collide", whereas the raw calendar contains exactly 33 coincident timestamps (32 where the CPI m/m anchor is present, 1 on `2025.12.18` where the anchor is absent).
3. **Erroneous LOYO Specification:** V1 incorrectly reported the median yearly return as "LOYO", rather than recomputing the full aggregate across leave-one-year-out sample folds.
4. **Aggregated Exit Distributions:** V1 pooled all exits together rather than separating Take-Profit (TP) and Stop-Loss (SL) exit timing distributions.

---

## 2. Pinned Universe, Anchor Series, and Raw Calendar Groundwork

- **Active USD Universe (7 Pairs):** `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`.
- **Strictly Excluded Pairs (9 Pairs):** `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY` (truncated broker history; denominator strictly 0).
- **Primary Anchor Series:** `CPI m/m` (Event ID `840030005`, Sector: Prices, Digits: 1, Unit: Percent).
  - **Zero Silent Fallback:** If m/m is missing (e.g. `2025.12.18 16:30:00 UTC`), the observation is strictly excluded (`excluded_missing_anchor`). Zero fallback to y/y (`840030007`).
- **Coincident Initial Jobless Claims:** `840140001` (verified in `calendar_events.csv`).
  - Total raw CPI bundle timestamps: **140**.
  - Timestamps coinciding with `840140001`: Exactly **33** timestamps.
  - Timestamps coinciding with `840140001` where CPI m/m anchor is present: Exactly **32** timestamps.
  - Coincident release on `2025.12.18 16:30:00 UTC` coincides with `840140001`, but CPI m/m is absent from MT5.
  - Clean bundles where CPI m/m anchor is present: $139 - 32 = \mathbf{107}$ clean bundles ($107 \times 7 = 749$ clean pair-observations).
- **Total Pair-Observation Denominator:** Exactly $140 \text{ bundles} \times 7 \text{ pairs} = \mathbf{980}$ pair-observations.

---

## 3. Direction Hypotheses & Signal States

- **Surprise Signal ($S = A - F$):** Actual minus Consensus Forecast.
  - $S > 0 \implies$ USD Strength ($+1$).
  - $S < 0 \implies$ USD Weakness ($-1$).
  - $S = 0 \implies$ Zero Surprise (Abstain, `excluded_zero_or_neutral_signal`).
  - $F \text{ is None} \implies$ Missing Forecast (`excluded_missing_forecast`).
    - *Forecasting Missingness Audit:* Exactly 30 bundles with m/m anchor present lack forecasts: 28 pre-May-2017 (`2015.01.16` to `2017.04.14`), plus 2 post-May-2017 anomalies (`2025.10.24` and `2026.01.13`).
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
  - Strict zero lookahead: $\text{bar\_open} + 3600 < T_{\text{release}}$. Release candle, entry candle, and candle closing at release are strictly excluded.
- **Physical Expiry Horizons:**
  - H60: 60 completed H1 bars ($60 \text{ hours of observed market trading}$).
  - H120: 120 completed H1 bars.
  - H240: 240 completed H1 bars.
- **Trading Session Gap Policy:**
  - Ordinary weekends ($\le 54\text{ hours}$) and recognized holiday closures are permitted.
  - Unscheduled weekday halts $> 4\text{ hours}$ (14,400s) disqualify path (`excluded_path_gap_exceeded`).

---

## 5. 52-Cell Exploratory Grid

- **Stop ATR Multiples:** $S \in \{1.0, 2.0, 3.0, 4.0\}$.
- **Target ATR Multiples:** $T \in \{1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00\}$.
- **Total Grid Cells:** Exactly 52 cells per horizon.
- **Total Evaluations per Pair/Signal:** 52 cells $\times$ 3 horizons = 156 evaluations.
- **Barrier Arithmetic:**
  - Barrier distance: $B_{\text{stop}} = S \times \text{ATR}$, $B_{\text{target}} = T \times \text{ATR}$.
  - Long: $\text{Stop} = E - B_{\text{stop}}$, $\text{Target} = E + B_{\text{target}}$.
  - Short: $\text{Stop} = E + B_{\text{stop}}$, $\text{Target} = E - B_{\text{target}}$.
- **Intrabar Touch Resolution & Dual-Touch Bound:**
  - **Primary Bound:** `STOP_FIRST`. If both high $\ge \text{Target}$ and low $\le \text{Stop}$ within the same bar, the trade is booked as a loss.
  - **Sensitivity Bound:** `TARGET_FIRST`. Evaluated and reported to measure intrabar ambiguity.
- **Timeout Exit:** If neither barrier is touched through the close of Bar $H$, exit at Bar $H$ close price:
  $$\text{Gross R} = D \times \frac{\text{close}_H - E}{B_{\text{stop}}}$$
- **Opening Gap Exit:** If a candle opens beyond a barrier, nominal proxy credits threshold touch, while actual open price and gap-executable R are stored for slippage sensitivity.
- **Cost Independence:** Pure gross OHLC arithmetic. Zero spread, slippage, or financing deducted. Never called "net profit".

---

## 6. Upgraded Statistical Summary & Attribution Specifications

To eliminate V1 defects, summary aggregation adheres to the following strict standards:

1. **True Leave-One-Year-Out (LOYO):**
   - For every cell, evaluate 11 separate folds, each excluding one complete calendar year $Y \in [2015, 2025]$.
   - For each fold: calculate remaining trades $N$, wins, losses, timeouts, win rate, gross sum R, and gross mean R.
   - Record: `loyo_positive_years` (count of folds with gross sum R $> 0$), `loyo_min_mean_r`, `loyo_max_mean_r`, `loyo_min_sum_r`, `loyo_max_sum_r`.
   - Partial year 2026 is strictly excluded from LOYO folds and reported as a separate partial cohort. Empty years never generate zero-result folds.
2. **Year-by-Year Annual Ledger:**
   - Full annual accounting for each year 2015..2025 and partial 2026: trades $N$, wins, losses, timeouts, win rate, gross sum R, gross mean R.
3. **Separate TP-Only and SL-Only Duration Distributions (Trading Bars and Wall-Clock Time):**
   - For Wins (TP hits): report $N_{\text{wins}}$, median bars, 75th percentile, 90th percentile, and maximum bars; and wall-clock proxy seconds (`tp_bar_close_proxy_seconds_median`, `p75`, `p90`, `max`).
   - For Losses (SL hits): report $N_{\text{losses}}$, median bars, 75th percentile, 90th percentile, and maximum bars; and wall-clock proxy seconds (`sl_bar_close_proxy_seconds_median`, `p75`, `p90`, `max`).
   - For Timeouts: report $N_{\text{timeouts}}$, bars ($H$).
   - **Wall-Clock Duration Accounting:** Trading bars count only observed broker sessions. Across weekends and scheduled closures, actual elapsed wall-clock time is measured from entry bar open ($T_{\text{entry}}$) to exit bar open and close:
     - For **opening-gap exits** (`TARGET_GAP`, `STOP_GAP`), execution is at the bar open (the gap price is observable at open): both `clock_seconds_to_bar_open` and `clock_seconds_bar_close_proxy` are set to $T_{\text{bar\_open}} - T_{\text{entry}}$ (exact, not a proxy).
     - For **intrabar touch exits** (`TARGET`, `STOP`), the exact sub-hour touch timestamp is unknown: `clock_seconds_to_bar_open` is the lower bound ($T_{\text{bar\_open}} - T_{\text{entry}}$) and `clock_seconds_bar_close_proxy` is the upper-bound proxy ($T_{\text{bar\_close}} - T_{\text{entry}}$).
     - For **timeout exit** at close of Bar $H_{\text{max}}$, the exit duration is exact: $T_{\text{exit\_bar\_close}} - T_{\text{entry}}$.
4. **Attribution Panels:**
   - **Full Panel:** All eligible candidate trades ($N=671$ for A−F).
   - **Jobless Claims Clean Panel:** The subset of releases with zero coincidence with `840140001` ($N=510$ for A−F).
5. **Common H240-Complete Cohort:**
   - Identical set of trades having valid, gap-free paths through Bar 240, reported across H60, H120, and H240 for unbiased horizon comparisons.
6. **Programmatic Report Verification:**
   - Every numerical value presented in `EXPLORATION_SUMMARY_REPORT.md` must be derived dynamically from `summary_grid_results.csv` and `manifest.json`. Zero hardcoded narrative figures.

---

## 7. Versioned Artifact Layout & Storage

Target package layout:
```
Research Candidate/CPI/CPI_EXPLORATION_V2/run_20260928_v2/
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
- **Fail-Closed Immutability & Independent Verification:** Output directory will not be overwritten if it exists (`check_package_immutability`). Independent read-only verification is supported via CLI (`python run_exploration_pipeline.py --verify-only --family CPI --run-id <run_id>`), which recomputes and reconciles 100% of summary grid results, annual breakdowns, and LOYO folds from the trial ledger with zero writes to disk.
