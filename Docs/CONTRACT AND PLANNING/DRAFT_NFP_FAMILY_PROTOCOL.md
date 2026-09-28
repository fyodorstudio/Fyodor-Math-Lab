# DRAFT US NFP Family Research Protocol

**Status:** Draft Protocol v0.1 for Project Director & Codex Review (PRE-OUTCOME PASS).  
**Notice:** This document contains research specifications and proposed decisions. It is **not** a frozen trading rule, backtest claim, or authorization to trade. Outcome prices and simulated returns remain strictly uncalculated.

---

## 1. Protocol Identification & Anchor Event IDs

| Field | Verified Value from Snapshot `FyodorResearchExport_v4_...` | Notes / Audit Verification |
| --- | --- | --- |
| **Family Name** | US Employment Situation (Nonfarm Payrolls / Jobs Report) | Sector: `CALENDAR_SECTOR_JOBS` |
| **Source Authority** | U.S. Bureau of Labor Statistics (BLS) | URL: `https://www.bls.gov` |
| **Primary Currency** | USD | Relevant Active Universe: 7 active USD pairs |
| **Anchor Nonfarm Payrolls** | Event ID: `840030016` | Unit: `CALENDAR_UNIT_JOB` (4), Mult: `CALENDAR_MULTIPLIER_THOUSANDS` (1), Digits: 0, Importance: High |
| **Constituent Unemployment Rate** | Event ID: `840030015` | Unit: `CALENDAR_UNIT_PERCENT` (1), Mult: `CALENDAR_MULTIPLIER_NONE` (0), Digits: 1, Importance: High |
| **Constituent Hourly Earnings m/m** | Event ID: `840030018` | Unit: `CALENDAR_UNIT_PERCENT` (1), Mult: `CALENDAR_MULTIPLIER_NONE` (0), Digits: 1, Importance: High |
| **Constituent Hourly Earnings y/y** | Event ID: `840030019` | Unit: `CALENDAR_UNIT_PERCENT` (1), Mult: `CALENDAR_MULTIPLIER_NONE` (0), Digits: 1, Importance: Medium |
| **Other Same-Time BLS Events** | `840030017` (Participation), `840030020` (Weekly Hours), `840030022` (Govt Payrolls), `840030023` (Private Payrolls), `840030024` (U6), `840030032` (Mfg Payrolls) | All 10 BLS series release simultaneously on 140 of 140 timestamps. |

---

## 2. Active Pair Universe & Exclusion Boundary

- **Active Universe (7 USD Pairs):** `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`.
- **Global Exclusion (9 Pairs):** `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY` are **strictly excluded** from all candidate and trade denominators due to truncated history starting only November 2025.
- **Other 12 Active Crosses:** Reserved for non-USD family research; not indirect spillovers.

---

## 3. Multi-Indicator Distinction & Coherence Logic

The monthly BLS release is a multi-dimensional macro bundle with differing units and economic mechanisms:

1. **Nonfarm Payrolls (`840030016`):**
   - Units: Net job additions in thousands (e.g., $+150$ means $+150,000$ jobs).
   - Higher payrolls surprise ($S > 0$) implies strong labor demand $\rightarrow$ **USD Bullish (+1)**.
2. **Unemployment Rate (`840030015`):**
   - Units: Percentage of civilian labor force (digits = 1).
   - Lower unemployment surprise ($S < 0$) implies labor market tightening $\rightarrow$ **USD Bullish (+1)**.
   - *Inverted economic sign:* $\text{Direction}_{\text{UR}} = -1 \times \text{sign}(S_{\text{UR}})$.
3. **Average Hourly Earnings m/m (`840030018`):**
   - Units: Percentage change in wages (digits = 1).
   - Higher wage growth surprise ($S > 0$) implies wage-push inflation pressure $\rightarrow$ **USD Bullish (+1)**.

### Coherence Strata Formulation
*Proposed Decision 1:* Candidate rules must not evaluate Nonfarm Payrolls in isolation without disclosing multi-indicator coherence:
- **Strong Coherent Bullish:** $S_{\text{NFP}} > 0$ AND $S_{\text{UR}} \le 0$ AND $S_{\text{AHE}} \ge 0$.
- **Strong Coherent Bearish:** $S_{\text{NFP}} < 0$ AND $S_{\text{UR}} \ge 0$ AND $S_{\text{AHE}} \le 0$.
- **Conflicted / Divided:** Signals diverge (e.g., strong payrolls but higher unemployment or falling wages).
- **Neutral / Zero:** Primary signal is zero.
- **Missing:** Any constituent forecast is missing.

---

## 4. Signal Formulation & Missing / Zero Policy

### A. Surprise ($S = A - F$)
- **Forensic Finding on Forecast Completeness:** In the MT5 snapshot, $F$ is **100% missing for all of 2015, all of 2016, and Jan–Apr 2017** (28 consecutive releases) across all four NFP series.
- **Zero vs. Missing Rule:** If $F$ is missing, $S$ is strictly `None`. It is **NEVER** coerced to $A - 0.0$.
- *Proposed Decision 2:* NFP $S = A - F$ research is restricted to May 2017 through August 2026. Pre-May 2017 releases are excluded with reason `excluded_missing_forecast`.

### B. Reported-Previous Momentum ($M = A - P$)
- **Forensic Finding on Previous Completeness:** $A$ and $P$ are **100% complete** across all 140 releases (2015–2026).
- **The Nonfarm Revision Trap:** Nonfarm payrolls are notoriously revised by large magnitudes in subsequent months. In `calendar_releases.csv`, `revised_previous` is present in **138 of 140 releases**.
- **Point-in-Time Warning:** Static historical snapshots contain revised previous values that may reflect subsequent benchmark revisions rather than what was known on release day.
- *Proposed Decision 3:* Baseline momentum uses reported `previous` ($A - P$). `revised_previous` is reserved for an explicit secondary vintage sensitivity pass and must not be quietly substituted into the baseline.

---

## 5. Same-Time Bundles & Cross-Currency Collisions

### Canadian Labour Force Survey Collision (Critical for USDCAD)
- **Forensic Finding:** Statistics Canada releases its Labour Force Survey (Employment Change `124010011`, Unemployment Rate `124010014`, etc.) at the **exact same timestamp** as US NFP on **89 of the 140 releases** (63.6% of episodes).
- **Market Impact:** On those 89 releases, `USDCAD` is simultaneously subjected to major CAD domestic employment shocks and US USD employment shocks.
- *Proposed Decision 4:* For `USDCAD`, candidate eligibility must distinguish:
  - **Full Panel:** All 140 releases (with CAD collision disclosed).
  - **CAD-Clean Panel:** The 51 releases where Canada did NOT release employment data simultaneously.
  - Candidate metrics for `USDCAD` must be presented for both panels to isolate domestic CAD confounding.

### Other External Collisions
- US Trade Balance (`840020001`): Collides on **26 releases**.
- US Initial Jobless Claims (`840014001`): Collides on **4 releases** (Thursday NFP shifts).
- Major central bank speeches (Fed, ECB, BoE): Collides on 1–2 releases each.
- *Proposed Decision 5:* Primary candidate pass evaluates the full unconstrained release panel; secondary sensitivity isolates trade balance collisions.

---

## 6. Explicit USD Direction Hypotheses

- **Economic Mechanism:** Strong payroll growth, declining unemployment, and rising wage inflation strengthen Federal Reserve hawkish expectations, driving USD appreciation.
- **Hypothesized Direction ($D_{\text{USD}}$):**
  - Strong Bullish labor signal: $D_{\text{USD}} = +1$ (USD Strength)
  - Strong Bearish labor signal: $D_{\text{USD}} = -1$ (USD Weakness)
  - Neutral / Zero: $D_{\text{USD}} = 0$ (Abstain)
- **Pair Direction Mapping ($D_{\text{pair}}$):**
  - **Base USD Pairs** (`USDCAD`, `USDCHF`, `USDJPY`): $D_{\text{pair}} = D_{\text{USD}}$ (+1 = Long, -1 = Short).
  - **Quote USD Pairs** (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`): $D_{\text{pair}} = -D_{\text{USD}}$ (+1 = Short, -1 = Long).

---

## 7. Execution Rules & Quality Guardrails (Proposed Decisions)

- **Entry Timing:** Open of the first complete H1 candle strictly after release timestamp ($t_{\text{entry}} > t_{\text{release}}$).
- **Entry Delay Cap:**
  - Forensic Finding: 100% of NFP releases (140 of 140) across all 7 pairs have an entry delay of **exactly 1800 seconds (30 minutes)**. There are zero abnormal weekend or gap entries at release time.
  - *Proposed Decision 6:* Enforce a **maximum entry delay of 3600 seconds (1 hour)**. Zero NFP observations are excluded by this cap.
- **Pre-Release Volatility (ATR-14):**
  - Computed on strictly completed H1 bars prior to release ($t_{\text{close}} = \text{bar\_open} + 3600 < t_{\text{release}}$, strictly earlier than release instant).
  - Minimum 251 pre-release bars (250 TRs) required for Wilder smoothing warmup. Zero lookahead.
  - *Verification:* 100% of the 140 releases across all 7 pairs have > 1,500 pre-release bars, ensuring 100% ATR warmup coverage.
- **Path Horizons & Trading Session Gap Policy:**
  - Standard horizons: H60, H120, H240 observed market bars.
  - Bounded regular weekend closures (Friday >= 20:00 to Sunday >= 21:00 or Monday <= 03:00, 45.0 to 55.0 elapsed hours) and scheduled Christmas/New Year closures (bounded <= 84.0 hours) are recognized market closures.
  - *Proposed Decision 7:* Any unscheduled weekday gap $> 4\text{ hours}$ (14,400s) during regular market hours disqualifies that horizon path.
  - *Full-History Raw Candle Gaps vs. Event-Path Exclusions Audit (2014–2026):* An audit of all 7 active USD pairs across the entire 2014–2026 raw candle dataset identifies exactly five non-exempt raw gaps > 4 hours:
    1. `USDCHF`: `2014.11.28 23:00:00` -> `2014.12.02 00:00:00` (73.0h elapsed, Friday night to Tuesday midnight; pre-sample warmup, 0 release intersections).
    2. `USDCHF`: `2015.01.15 20:00:00` -> `2015.01.19 00:00:00` (76.0h elapsed, Thursday night to Monday midnight; intersects `2015.01.09` NFP at Bar 100, 0 CPI intersections).
    3. `NZDUSD`: `2017.05.10 23:00:00` -> `2017.05.15 09:00:00` (106.0h elapsed, Wednesday night to Monday morning; intersects `2017.05.05` NFP at Bar 80, 0 CPI intersections).
    4. `GBPUSD`: `2019.09.30 23:00:00` -> `2019.10.02 00:00:00` (25.0h elapsed, Monday night to Wednesday midnight; between monthly release windows, 0 release intersections).
    5. `GBPUSD`: `2021.01.01 00:00:00` -> `2021.01.04 00:00:00` (72.0h elapsed, Friday midnight Jan 1 to Monday midnight Jan 4; between monthly release windows, 0 release intersections).
  - *Specific Historical Gap Exclusions Detected (Exactly 2 Event-Path Intersections):*
    1. `USDCHF` on `2015.01.09`: Entry is Bar 1 (`2015.01.09 17:00:00`). At Bar 100, the candle records exhibit the 76.0-hour weekday gap above between `2015.01.15 20:00:00` and `2015.01.19 00:00:00`.
       - H60 Path: Bar 1 to 60 completes on 2015.01.14 (0 gaps). **Eligible.**
       - H120 Path: Crosses the 76h gap. **Disqualified** (`excluded_path_gap_exceeded`).
       - H240 Path: Crosses the 76h gap. **Disqualified** (`excluded_path_gap_exceeded`).
    2. `NZDUSD` on `2017.05.05`: Entry is Bar 1 (`2017.05.05 16:00:00`). At Bar 80, the candle records exhibit the 106.0-hour weekday gap above between `2017.05.10 23:00:00` and `2017.05.15 09:00:00`.
       - H60 Path: Bar 1 to 60 completes on 2017.05.10 03:00 (0 gaps). **Eligible.**
       - H120 Path: Crosses the 106h gap. **Disqualified** (`excluded_path_gap_exceeded`).
       - H240 Path: Crosses the 106h gap. **Disqualified** (`excluded_path_gap_exceeded`).
    - *Summary:* Exactly 2 of the 5 full-history gaps intersect NFP event paths. The other 3 raw candle gaps fall entirely outside all NFP observation paths.
    - *Causal Attribution Guardrail:* The candle records establish the existence and duration of these gaps, not their external causes. No unsourced historical events are assumed.
- **Candidate Selection Rule (Draft Proposal for Codex/Director Review):**
  - *Proposed Decision 8:* Selection policy remains an open draft decision. A potential criterion under review is highest median gross R across leave-one-year-out partitions requiring $N \ge 10$ trades/year, adjacent-cell stability within $\pm 0.25$ ATR, and positive performance in $\ge 80\%$ of years. **This is NOT an established profit criterion or registered rule.** No strategy is validated merely because a backtest metric is high.

---

## 8. Open Decisions for Project Director Steering

The following items are explicitly marked as **UNRESOLVED JUDGMENTS** requiring Director steering before any price outcome is calculated:

1. **USDCAD Canada Jobs Collision:** Should `USDCAD` NFP trials exclude the 89 Canadian jobs collision releases by default, or evaluate all 140 releases with a collision flag?
2. **NFP A-P Revision Policy:** Should Nonfarm Payrolls momentum trials use exported `previous` or test `revised_previous`, given that MT5 does not verify point-in-time publication dates for revisions?
3. **Multi-Indicator Coherence Requirement:** Should trading eligibility require triple agreement (Payrolls + Unemployment + Wages), or should Payrolls alone serve as the primary trigger with coherence reported as a descriptive filter?
4. **Pre-2017 Forecast Truncation:** For $S = A - F$, should pre-May-2017 releases be omitted, or should an audited external consensus dataset be considered under a future version?
5. **Session Gap Policy Threshold:** Should the unscheduled weekday gap threshold be frozen at 4 hours (14,400s) or 2 hours (7,200s)?
