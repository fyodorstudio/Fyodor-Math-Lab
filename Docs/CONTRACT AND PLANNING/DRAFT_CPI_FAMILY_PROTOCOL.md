# DRAFT US CPI Family Research Protocol

**Status:** Draft Protocol v0.1 for Project Director & Codex Review (PRE-OUTCOME PASS).  
**Notice:** This document contains research specifications and proposed decisions. It is **not** a frozen trading rule, backtest claim, or authorization to trade. Outcome prices and simulated returns remain strictly uncalculated.

---

## 1. Protocol Identification & Anchor Event IDs

| Field | Verified Value from Snapshot `FyodorResearchExport_v4_...` | Notes / Audit Verification |
| --- | --- | --- |
| **Family Name** | US Consumer Price Index (CPI) | Sector: `CALENDAR_SECTOR_PRICES` |
| **Source Authority** | U.S. Bureau of Labor Statistics (BLS) | URL: `https://www.bls.gov` |
| **Primary Currency** | USD | Relevant Active Universe: 7 active USD pairs |
| **Anchor Headline CPI m/m** | Event ID: `840030005` | Unit: `CALENDAR_UNIT_PERCENT` (1), Digits: 1, Mult: 0, Importance: High |
| **Anchor Core CPI m/m** | Event ID: `840030006` | Unit: `CALENDAR_UNIT_PERCENT` (1), Digits: 1, Mult: 0, Importance: High |
| **Distinct Series: CPI y/y** | Event ID: `840030007` | Unit: `CALENDAR_UNIT_PERCENT` (1), Digits: 1, Mult: 0, Importance: High. **Separate series; NEVER used as a silent fallback for missing m/m.** |
| **Distinct Series: Core CPI y/y**| Event ID: `840030008` | Unit: `CALENDAR_UNIT_PERCENT` (1), Digits: 1, Mult: 0, Importance: Medium |
| **Non-Percentage Indices** | `840030009` (CPI n.s.a.), `840030010` (Core CPI n.s.a.) | **EXCLUDED** as signal anchors due to incompatible index-level units (~250–310). |

---

## 2. Active Pair Universe & Exclusion Boundary

- **Active Universe (7 USD Pairs):** `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`.
- **Global Exclusion (9 Pairs):** `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY` are **strictly excluded** from all candidate and trade denominators due to truncated history starting only November 2025.
- **Other 12 Active Crosses:** Reserved for non-USD family research; not indirect spillovers.

---

## 3. Signal Formulation & Missing / Zero Policy

Let $A$ = Actual, $F$ = Forecast, $P$ = Reported Previous.

### A. Strict Anchor Integrity (Zero Silent Fallback)
- The CPI m/m protocol anchors strictly on `840030005` (CPI m/m).
- If CPI m/m is missing from a bundle (specifically on `2025.12.18 16:30:00`), the observation has a missing signal and is explicitly excluded with `excluded_missing_anchor_cpi_mm`.
- It is **strictly forbidden** to quietly substitute CPI y/y (`840030007`) when m/m is absent. A y/y study requires its own independent family protocol.

### B. Surprise ($S = A - F$)
- Measures the surprise component relative to consensus expectations.
- **Forensic Finding on Forecast Completeness:** In the MT5 export, $F$ has **30 unpopulated bundles** where the m/m anchor is present: 28 occurrences prior to the first populated forecast on `2017.05.12` (`2015.01.16` through `2017.04.14`), plus 2 subsequent occurrences on `2025.10.24` and `2026.01.13` (in addition to `2025.12.18` where the m/m anchor itself was missing). Post-May-2017 forecast coverage is **not uninterrupted**.
- **Zero vs. Missing Rule:** If $F$ is missing (empty string/null), $S$ is strictly `None` (uncalculated). It is **NEVER** coerced to $A - 0.0$.
- *Proposed Decision 1:* $S = A - F$ research excludes all releases with unpopulated forecasts using reason `excluded_missing_forecast` (210 pair-observations across the 30 bundles).

### C. Reported-Previous Momentum ($M = A - P$)
- Measures the direction of acceleration from the previous published month.
- **Forensic Finding on Previous Completeness:** $A$ and $P$ are **100% complete** across all available CPI m/m releases.
- **Zero vs. Missing Rule:** If $A - P = 0.0$, this is classified as `ZERO` (a neutral stratum), distinct from missing.
- *Proposed Decision 2:* $M = A - P$ can be evaluated across the entire 2015–2025 core and 2026 partial cohorts where the m/m anchor is present.

### D. Previous vs. Revised Previous
- In `calendar_releases.csv`, `revised_previous` is present in only 15 of 139 releases for CPI m/m, and 1 of 140 for CPI y/y.
- *Proposed Decision 3:* Baseline signals strictly use exported `previous`. A static calendar snapshot does not verify what revision vintage was known at release time. `revised_previous` is not mixed into baseline momentum.

### E. Headline vs. Core Coherence
- A release contains both Headline CPI m/m (`840030005`) and Core CPI m/m (`840030006`).
- *Proposed Decision 4:* Define explicit coherence strata:
  - **Coherent Bullish:** $S_{\text{headline}} > 0$ AND $S_{\text{core}} > 0$.
  - **Coherent Bearish:** $S_{\text{headline}} < 0$ AND $S_{\text{core}} < 0$.
  - **Conflicting:** $S_{\text{headline}} \times S_{\text{core}} < 0$.
  - **Neutral / Zero:** Either signal is zero.
  - **Missing:** Either signal is missing.

---

## 4. Same-Time Bundles & Collision Policy

- **Constituents:** Across the 4 tracked CPI series (`840030005`, `840030006`, `840030007`, `840030008`), there are **558 raw release rows** across 140 unique bundle timestamps (not 560, because m/m and Core m/m are absent on `2025.12.18`). Coincident `840030030` (Real Earnings m/m) is present on 133 timestamps.
- **Forensic Finding — Incomplete Bundle:** On `2025.12.18 16:30:00`, CPI y/y (`840030007`) and Core CPI y/y (`840030008`) exist, but CPI m/m (`840030005`) and Core CPI m/m (`840030006`) are absent from the MT5 calendar.
  - *Proposed Decision 5:* All 7 active pairs on `2025.12.18` are excluded with primary reason `excluded_missing_anchor_cpi_mm`.
- **External Collisions:**
  - Initial Jobless Claims (`840030001`): Collides on **20 releases** when CPI falls on a Thursday.
  - Canadian releases (Foreign Securities, CPI, Employment): Collides on 1–6 releases.
  - *Proposed Decision 6:* Primary candidate pass evaluates the full unconstrained release panel. A secondary disclosed collision-sensitivity cohort excludes the 20 Thursday Jobless Claims collision releases.

---

## 5. Explicit USD Direction Hypotheses

- **Economic Mechanism:** Higher-than-expected CPI ($S > 0$) or accelerating CPI ($M > 0$) indicates persistent inflation, prompting market expectations of higher policy rates by the Federal Reserve, thereby causing USD appreciation.
- **Hypothesized Direction ($D_{\text{USD}}$):**
  - Positive surprise/momentum: $D_{\text{USD}} = +1$ (USD Strength)
  - Negative surprise/momentum: $D_{\text{USD}} = -1$ (USD Weakness)
  - Zero surprise/momentum: $D_{\text{USD}} = 0$ (Abstain)
- **Pair Direction Mapping ($D_{\text{pair}}$):**
  - **Base USD Pairs** (`USDCAD`, `USDCHF`, `USDJPY`): $D_{\text{pair}} = D_{\text{USD}}$ (+1 = Long, -1 = Short).
  - **Quote USD Pairs** (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`): $D_{\text{pair}} = -D_{\text{USD}}$ (+1 = Short, -1 = Long).

---

## 6. Execution Rules & Quality Guardrails (Proposed Decisions)

- **Entry Timing:** Open of the first complete H1 candle strictly after release timestamp ($t_{\text{entry}} > t_{\text{release}}$).
- **Entry Delay Cap:**
  - Normal delay: 1800s (30 minutes) when release is at HH:30.
  - *Proposed Decision 7:* Enforce a **maximum entry delay of 3600 seconds (1 hour)**. Any observation exceeding 3600s is excluded with `excluded_entry_delay_exceeded`.
  - *Impact:* Excludes `USDCHF` on `2015.01.16` (next-H1 entry `2015.01.19 00:00:00`, delay 199,800s / ~55.5 hours; candle records show no bars between Friday 16:00 and Monday 00:00) and `NZDUSD` on `2017.05.12` (next-H1 entry `2017.05.15 09:00:00`, delay 235,800s / ~65.5 hours; candle records show no bars between Friday 15:00 and Monday 09:00). All other 978 pair-observations have normal 1800s delay.
- **Pre-Release Volatility (ATR-14):**
  - Computed on strictly completed H1 bars prior to release ($t_{\text{close}} = \text{bar\_open} + 3600 < t_{\text{release}}$, strictly earlier than release instant).
  - Minimum 251 pre-release bars (250 TRs) required for Wilder smoothing warmup. Zero lookahead.
  - *Verification:* 100% of the 140 releases across all 7 pairs have > 1,500 pre-release bars, ensuring 100% ATR warmup coverage.
- **Trading Session & Gap Policy:**
  - Bounded regular weekend closures (Friday >= 20:00 to Sunday >= 21:00 or Monday <= 03:00, 45.0 to 55.0 elapsed hours) and scheduled Christmas/New Year closures (bounded <= 84.0 hours) are recognized market closures.
  - *Proposed Decision 8:* Any unscheduled weekday gap $> 4\text{ hours}$ (14,400s) during regular market hours disqualifies that horizon path.
  - *Full-History Raw Candle Gaps vs. Event-Path Exclusions Audit (2014–2026):* An audit of all 7 active USD pairs across the entire 2014–2026 raw candle dataset identifies exactly five non-exempt raw gaps > 4 hours:
    1. `USDCHF`: `2014.11.28 23:00:00` -> `2014.12.02 00:00:00` (73.0h elapsed, Friday night to Tuesday midnight; pre-sample warmup, 0 release intersections).
    2. `USDCHF`: `2015.01.15 20:00:00` -> `2015.01.19 00:00:00` (76.0h elapsed, Thursday night to Monday midnight; intersects `2015.01.09` NFP at Bar 100, 0 CPI intersections).
    3. `NZDUSD`: `2017.05.10 23:00:00` -> `2017.05.15 09:00:00` (106.0h elapsed, Wednesday night to Monday morning; intersects `2017.05.05` NFP at Bar 80, 0 CPI intersections).
    4. `GBPUSD`: `2019.09.30 23:00:00` -> `2019.10.02 00:00:00` (25.0h elapsed, Monday night to Wednesday midnight; between monthly release windows, 0 release intersections).
    5. `GBPUSD`: `2021.01.01 00:00:00` -> `2021.01.04 00:00:00` (72.0h elapsed, Friday midnight Jan 1 to Monday midnight Jan 4; between monthly release windows, 0 release intersections).
  - *CPI Verification:* Exactly **0** event paths intersect any of these five gaps across all horizons (H60, H120, H240). 100% of the 980 CPI pair-observations with valid entry have complete, gap-free paths.
- **Candidate Selection Rule (Draft Proposal for Codex/Director Review):**
  - *Proposed Decision 9:* Selection policy remains an open draft decision. A potential criterion under review is highest median gross R across leave-one-year-out partitions requiring $N \ge 10$ trades/year, adjacent-cell stability within $\pm 0.25$ ATR, and positive performance in $\ge 80\%$ of years. **This is NOT an established profit criterion or registered rule.** No strategy is validated merely because a backtest metric is high.

---

## 7. Open Decisions for Project Director Steering

The following items are explicitly marked as **UNRESOLVED JUDGMENTS** requiring Director steering before any price outcome is calculated:

1. **Primary Anchor Selection:** Should the primary CPI study anchor on **CPI m/m** (`840030005`, 139 releases) or **CPI y/y** (`840030007`, 140 releases)?
2. **Pre-2017 Forecast Truncation:** For $S = A - F$, should pre-May-2017 releases be omitted, or should an audited external consensus dataset be considered under a future version?
3. **Collision Treatment:** Should Thursday releases colliding with US Jobless Claims (20 releases) be excluded globally, or retained with a flagged collision sensitivity?
4. **Coherence Filter:** Should the primary signal require Core CPI agreement, or should Headline alone serve as primary with Core agreement reported as a sub-cohort?
5. **Session Gap Policy Threshold:** Should the unscheduled weekday gap threshold be frozen at 4 hours (14,400s) or 2 hours (7,200s)?
