# US CPI Exploration V1 Protocol (Historical Exploration)

**Protocol Identifier:** `CPI_EXPLORATION_V1`  
**Status:** FROZEN EXPLORATION PROTOCOL (Historical Exploration Only; NOT Setup Registration)  
**Parent Contract:** [`Docs/CONTRACT AND PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md`](CALCULATION_AND_CANDIDATE_CONTRACT.md) (as amended 2026-09-28)  
**Pre-Outcome Baseline Commit:** `12de3315d82e3be57cbf3f3ad18671fbd70aa1a2`  
**Execution Context:** Pinned V4 Snapshot (`raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server`)  

---

## 1. Executive Summary & Protocol Authority

This protocol freezes all parameters, signal definitions, directional hypotheses, execution proxies, and attribution strata for the **historical exploration** of US Consumer Price Index (CPI) releases. 

> [!IMPORTANT]
> **EXPLORATION ONLY — ZERO SETUP REGISTRATION:**
> In accordance with the calculation contract amendment of 2026-09-28, the selection policy for this run is explicitly set to **`selection_policy = NONE`**. All approved grid cells (52 stop/target cells across 3 horizons = 156 combinations per signal/pair) will be computed and reported in full, including all losing and stagnant cells. No single "optimal" or "winning" setup is selected, registered, or claimed to possess an edge. The strict multi-year selection and stability gates remain reserved for any future setup registration protocol.

---

## 2. Event Anchor Series & Constituents

- **Primary Anchor Series:** **US CPI m/m** (Headline, Seasonally Adjusted)
  - **MetaTrader 5 Event ID:** `840030005`
  - **Event Name:** `CPI m/m`
  - **Currency:** `USD` | **Country:** `US`
  - **Unit:** `CALENDAR_UNIT_PERCENT` (Multiplier: `CALENDAR_MULTIPLIER_NONE`, Digits: 1)
- **Constituent Co-Releases (Same-Time Bundle Members):**
  - Core CPI m/m (`840030006`, Percent)
  - CPI y/y (`840030007`, Percent)
  - Core CPI y/y (`840030008`, Percent)
- **Integrity Invariant:** Anchor series is strictly `840030005`. **Zero silent fallback** to CPI y/y (`840030007`) or Core CPI is permitted. If `840030005` is absent from a release bundle (e.g., `2025.12.18 16:30:00`), that release is excluded with `excluded_missing_anchor_series`.
- **Constituent Count:** Exactly 558 raw constituent rows across 140 unique bundle timestamps.

---

## 3. Pair Universe & Independence Boundary

- **Active USD Research Universe (7 Pairs):**
  - **USD Base Pairs:** `USDCAD`, `USDCHF`, `USDJPY`
  - **USD Quote Pairs:** `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`
- **Globally Excluded Universe (9 Pairs):**
  - `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY`
  - Reason: Truncated history starting Nov 2025 (`excluded_truncated_history`). Strictly excluded from all candidate and trade denominators.
- **Cross-Sectional Independence Warning:** Seven pairs responding to a single CPI release are cross-sectionally correlated expressions of USD revaluation. They are **never** pooled or treated as seven statistically independent macro events.

---

## 4. Signal Definitions & Missingness Handling

Two primary signals are evaluated independently:

1. **Surprise Signal ($S = A - F$):**
   - $S = \text{Actual} - \text{Forecast}$ on Anchor `840030005`.
   - **Missing Forecast Rule:** If $F$ is unpopulated (`None`), the observation is excluded with `excluded_missing_forecast`. (30 bundles total: 28 pre-May-2017 plus `2025.10.24` and `2026.01.13`).
   - **Zero Difference Rule:** If $S == 0.0$, the observation is excluded from trade execution with `excluded_zero_signal` (abstain).
2. **Reported Momentum Signal ($M = A - P$):**
   - $M = \text{Actual} - \text{Previous}$ on Anchor `840030005`.
   - **Revision Invariant:** $P$ is the raw exported `previous` value. The field `revised_previous` is **never** used.
   - **Point-in-Time Caveat:** The point-in-time vintage of `previous` in MT5 historical records is unverified.
   - **Missing Previous Rule:** If $P$ is unpopulated, excluded with `excluded_missing_previous`.
   - **Zero Difference Rule:** If $M == 0.0$, excluded with `excluded_zero_signal` (abstain).

---

## 5. Predeclared Directional Hypothesis

- **Hypothesis (Under Test, Not an Asserted Fact):**
  - Higher-than-expected inflation ($S > 0$) or accelerating monthly inflation ($M > 0$) increases market expectations of tighter Federal Reserve monetary policy, predicting USD appreciation ($D_{\text{USD}} = +1$).
  - Lower-than-expected inflation ($S < 0$) or decelerating monthly inflation ($M < 0$) predicts USD depreciation ($D_{\text{USD}} = -1$).
- **Instrument Mapping ($D_{\text{pair}}$):**
  - **Base USD Pairs** (`USDCAD`, `USDCHF`, `USDJPY`): $D_{\text{pair}} = D_{\text{USD}}$ (+1 = Long, -1 = Short).
  - **Quote USD Pairs** (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`): $D_{\text{pair}} = -D_{\text{USD}}$ (+1 = Short, -1 = Long).

---

## 6. Execution Rules, Horology, & Barrier Grid

- **Entry Timestamp & Price:** Open price of the first complete H1 candle strictly following release timestamp:
  $$t_{\text{bar\_open}} > t_{\text{release}}$$
  The entry candle is indexed as **Bar H1** of the observed price path.
- **Entry Delay Cap:** Maximum permitted entry delay is **3600 seconds** (1 hour). Any observation with delay $> 3600$s is disqualified (`excluded_entry_delay_exceeded`).
  - *Empirical Impact:* Excludes `USDCHF 2015.01.16` (55.5h) and `NZDUSD 2017.05.12` (65.5h). The other 978 observations enter within 1800s.
- **Pre-Release Reference Volatility:**
  - H1 ATR(14) with Wilder smoothing, calculated strictly on bars whose close is earlier than release instant:
    $$t_{\text{bar\_close}} = t_{\text{bar\_open}} + 3600 < t_{\text{release}}$$
  - Minimum 251 pre-release bars (250 True Ranges) required. Zero lookahead.
- **Exploratory Expiry Horizons:**
  - **H60:** 60 observed H1 market bars (approx. 2.5 trading days).
  - **H120:** 120 observed H1 market bars (approx. 5 trading days).
  - **H240:** 240 observed H1 market bars (approx. 10 trading days).
- **Approved Exploratory ATR Grid (52 Cells):**
  - **Stop Widths ($s$):** $\{1, 2, 3, 4\}$ ATR. Stop distance $B = s \times \text{ATR}$.
  - **Target Widths ($p$):** $\{1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00\}$ ATR. Target distance $T = p \times \text{ATR}$.
  - Total combinations per signal/pair: $4 \times 13 = 52$ cells $\times 3$ horizons = $156$ trials.
  - *Grid Semantics:* Notation `s:p` represents absolute ATR multipliers (e.g., `4:4` means 4 ATR stop and 4 ATR target, giving reward-to-risk ratio $p/s = 1.00$).

---

## 7. OHLC Barrier Touch Semantics & Arithmetic

- **Barrier Levels:**
  - For Long ($D = +1$): $\text{Stop} = E - B$, $\text{Target} = E + T$.
  - For Short ($D = -1$): $\text{Stop} = E + B$, $\text{Target} = E - T$.
- **Intrabar Touch Proxy:**
  - Long: Stop touched if $\text{Low} \le \text{Stop}$; Target touched if $\text{High} \ge \text{Target}$.
  - Short: Stop touched if $\text{High} \ge \text{Stop}$; Target touched if $\text{Low} \le \text{Target}$.
- **Dual-Touch Ambiguity Handling:**
  - **Primary Bound (Conservative):** If both Stop and Target are touched in the same H1 candle, resolve as **STOP-FIRST** (Loss). Record `dual_touch = True`.
  - **Sensitivity Bound:** Re-evaluate as **TARGET-FIRST** (Win) and report the delta.
- **Opening Gaps:**
  - If a bar opens beyond the stop level, exit at open price:
    $$\text{Gross R} = -\frac{|E - \text{open}|}{B}$$
  - If a bar opens beyond the target level, exit at open price:
    $$\text{Gross R} = +\frac{|\text{open} - E|}{B}$$
- **Timeout Exit:**
  - If neither barrier is touched through the close of Bar $H_{\text{max}}$, exit at Bar $H_{\text{max}}$ close price.
  - $\text{Gross R} = D \times \frac{\text{close}_{H_{\text{max}}} - E}{B}$.
  - $\text{Signed Pips} = D \times \frac{\text{close}_{H_{\text{max}}} - E}{\text{pip\_size}}$.
- **Excursion Tracking (MFE / MAE):**
  - Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE) recorded in pips and ATR units.
  - Exit-bar excursion ambiguity handled by reporting guaranteed pre-exit lower bound and OHLC upper bound.
- **Cost Independence:** All metrics represent **gross OHLC arithmetic**. Zero spread, slippage, or financing costs are deducted. Never described as "net profit".

---

## 8. Attribution Strata & Collision Panels

- **Primary Attribution Panel:** Full eligible panel (139 valid bundles, 973 candidate observations per horizon).
- **Secondary Collision Sensitivity (US Jobless Claims):**
  - Exactly 20 CPI release bundles collide with weekly US Initial Jobless Claims (`840014001`) on Thursday release shifts.
  - Sensitivity panel evaluates the 119 collision-clean bundles separately.
- **Descriptive Sub-Strata (Not Automated Selection Filters):**
  - **Core Agreement:** Anchor Headline m/m and Core m/m have same sign.
  - **Sign Quadrants:** Joint signs of $(S, M) \in \{(+,+), (+,-), (-,+), (-,-)\}$.

---

## 9. Cohort Partitioning & Reporting Standard

- **Core Sample:** Full calendar years 2015–2025, reported year by year.
- **Partial Cohort:** January 1, 2026 through August 31, 2026. Reported separately; never pooled into annual stability claims.
- **Post-Cutoff Releases:** September 2026 releases (`2026.09.11`) excluded (`excluded_post_cutoff_2026`).
- **Common-Complete Cohort:** Reported across H60, H120, and H240 for like-for-like horizon comparisons.
