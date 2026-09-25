# German Ifo EURUSD Pilot Pre-2023 Exploration Report (Milestone 4)

> [!IMPORTANT]
> **GOVERNANCE STATUS: EXPLORATION REPORT (v1.2 FROZEN FROZEN PROTOCOL)**  
> Evaluated strictly under `docs/FMS_PILOT_IFO_PROTOCOL.md`.  
> Chronological Split Boundary: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).  
> Evaluation Timestamp: `2026-09-24T23:58:54.515Z`.  
> Post-2022 historical holdout (`timestamp >= 1672531200`) remains strictly sealed and uninspected.

---

## 1. Cryptographic Provenance Hashes & Manifests (Verified)

| Input / Manifest Component | Verified Identifier / SHA-256 Hash | Status / Details |
|---|---|---|
| `calendar_releases.csv` | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` | Match Pinned |
| `fms_episodes.jsonl` | `37df7880a2bc36dbbce06b4a6ba39f7bd962a4c1c92eb2ce64cb71a886de55d2` | Match Pinned |
| `ifo_pilot_ledger.json` | `324b99a1f2ac9ebe73b5102d35208cc32a7e2eb7eb9cc69480b3feae710ff658` | Match Pinned |
| `ifo_pilot_ledger.md` | `e2e3a6c19bbfadfd1bef151861bcba3a3e5066836e3dfc28835e28a616ef72c8` | Match Pinned |
| **Consumed Pre-2023 H1 Rows** | `b8607ca37f04279f6be1f318d08be557dc7292e3faf38169abff1942bef5be4d` | 49761 rows (1420189200 → 1672441200) |
| Consumed Pre-2023 H1 (w/ Header) | `b5bd256c7394f64b75967d7b8d8870f5bc50405eff5fda75f01824ab0b9ce00e` | Header included |
| **Analysis Git Commit** | `63a6d74546aedeb9e9861e1ba57ec46a579e737c` | Immutable Implementation ID |

---

## 2. Decision State & Governance Evaluation

### **State 3: No Convincing Evidence in this Sample**

- **Decision State Code**: `STATE_3_NO_CONVINCING_EVIDENCE`
- **Operational Mandate**: Conclude that there is no convincing evidence in this sample of delayed post-announcement drift for German Ifo on EURUSD. Archive pilot with complete negative report. Zero parameter tweaking, indicator substitution, or horizon hunting is permitted.

### Step-by-Step Gate Evaluation:
- **Step 1 (Inconclusive / Negative Signal: $p \ge 0.10$ OR $\Delta \bar{R} \le 0$)**: **FAILED** (Permutation p-value (0.9575) >= 0.10 and sample mean paired difference Delta_R (-0.00213) <= 0.0)
- **Step 2 (Borderline / Economically Fragile: $p \ge 0.05$ OR $\bar{\Delta}_{pips} < 1.0$ OR WinRate $< 55%$)**: PASSED
- **Step 3 (Plausible In-Sample Anomaly)**: NOT MET

---

## 3. Primary Testing Horizon: 6 H4 (First Trading Day / 24 Active Hours)

| Metric | Value | Protocol Threshold / Hurdle | Disposition |
|---|---|---|---|
| Actionable Event Episodes ($N$) | **40** | 40 | Complete Sample |
| Price-Blind Paired Controls ($N_{\text{paired}}$) | **39** | 39 resolved (1 unavailable) | Clean Pairs |
| Sample Mean Paired Excess Log Return ($\Delta \bar{R}$) | **-21.31 bps** (-0.002131) | $> 0.0$ | Non-Positive |
| Event Mean Gross Pip Drift ($\bar{\Delta}_{\text{pips}}$) | **-12.85 pips** | $\ge 1.0\text{ pip}$ | Below Hurdle |
| Paired Win Rate ($R_{\text{event}} > R_{\text{ctrl}}$) | **48.7%** (19/39) | $\ge 55.0\%$ | Below Hurdle |
| Seeded Mulberry32 Permutation $p$-value (raw) | **0.95745** | $\alpha = 0.05$ (1-sided) | Not Significant |
| Holm-Bonferroni Step-Down Multiplicity Gate | **Rank 2 of 2 | Raw: 0.95745 (cutoff $\le 0.050$) | Adjusted: 1.00000 (vs $\alpha = 0.05$)** | Step-down family threshold | Ineligible (Rank 2: Step 1 failed) |
| Student's $t$-test $p$-value ($df = 38$) | **0.95828** | Diagnostic ($df = 38$) | Student-$t$ Tail |
| Wilcoxon Signed-Rank $p$-value | **0.90162** | Diagnostic (Zeros dropped, Tie-corrected) | Non-parametric |

---

## 4. Secondary Testing Horizon: 12 H4 (Second Trading Day / 48 Active Hours)

### A. Frozen Strict Audit ($N_{\text{paired}} = 34$, 0 Duplicates, 6 Unavailable)

| Metric | Strict 12 H4 Value | Permissive 12 H4 Diagnostic ($N=35$) |
|---|---|---|
| Paired Observations | **34** | **35** |
| Mean Paired Excess Log Return ($\Delta \bar{R}$) | **-25.65 bps** | **-29.43 bps** |
| Event Mean Pip Drift | **-13.51 pips** | **-13.51 pips** |
| Paired Win Rate | **41.2%** (14/34) | **40.0%** (14/35) |
| Seeded Permutation $p$-value (raw) | **0.92025** | **0.94691** |
| Holm-Bonferroni Multiplicity Gate | **Rank 1 of 2 | Raw: 0.92025 (cutoff $\le 0.025$) | Adjusted: 1.00000 (vs $\alpha = 0.05$)** | Failed Step 1 (Rank 1: raw p > 0.025) |
| Student's $t$-test $p$-value | **0.92090** | **0.94761** |
| Wilcoxon Signed-Rank $p$-value | **0.85150** | **0.89785** |

---

## 5. Cost Sensitivity Analysis (Dimension: Pips & Log Return)

> [!NOTE]
> **Explicit Distinct Friction Scenarios**:
> 1. **Scenario A (Paired Executable Trades)**: If both the event trade and matched control trade are treated as executable trades each bearing round-turn friction penalty $c_{\text{pips}}$:
>    - **In pips**: Equal cost $c$ cancels identically in the paired difference: $(\Delta_{\text{event}} - c) - (\Delta_{\text{control}} - c) = \Delta_{\text{gross paired}}$.
>    - **In log return**: Because event and control trades enter at distinct price levels ($P_{\text{entry}, e} \ne P_{\text{entry}, c}$), their log-return penalties differ: $R_{e, \text{net}} = R_e - (c \cdot 10^{-4}) / P_{\text{entry}, e}$ and $R_{c, \text{net}} = R_c - (c \cdot 10^{-4}) / P_{\text{entry}, c}$. Paired net return difference and win rate are evaluated from these respective penalties.
> 2. **Scenario B (Event Friction vs. Frictionless Benchmark Control)**: If the matched control represents an unexecutable, frictionless macroeconomic baseline:
>    - **In pips**: $(\Delta_{\text{event}} - c) - \Delta_{\text{control}} = \Delta_{\text{gross paired}} - c$.
>    - **In log return**: $R_{e, \text{net}} - R_c = \Delta R_{\text{gross}} - (c \cdot 10^{-4}) / P_{\text{entry}, e}$.
> *Neither scenario alters the frozen gross primary statistic.*

| Friction Penalty ($c_{\text{pips}}$) | Gross Event Pips | Net Event Pips | Scenario A Net $\Delta$ Pips (Cost Cancels) | Scenario A Net $\Delta$ Return (bps) | Scenario A Win Rate | Scenario B Net $\Delta$ Pips (Event Friction Only) | Scenario B Net $\Delta$ Return (bps) | Scenario B Win Rate |
|---|---|---|---|---|---|---|---|---|
| **0.0 pips** | -12.85 | -12.85 | -22.49 | -21.31 | 48.7% | -22.49 | -21.31 | 48.7% |
| **0.5 pips** | -12.85 | -13.35 | -22.49 | -21.31 | 48.7% | -22.99 | -21.76 | 46.2% |
| **1.0 pips** | -12.85 | -13.85 | -22.49 | -21.31 | 48.7% | -23.49 | -22.21 | 46.2% |
| **1.5 pips** | -12.85 | -14.35 | -22.49 | -21.31 | 48.7% | -23.99 | -22.66 | 46.2% |
| **2.0 pips** | -12.85 | -14.85 | -22.49 | -21.32 | 48.7% | -24.49 | -23.10 | 46.2% |

---

## 6. Subgroups & Descriptive Diagnostics

### A. Yearly Performance Breakdown (6 H4)

| Year | Pairs ($N$) | Mean $\Delta \bar{R}$ (bps) | Mean $\Delta$ Pips | Win Rate |
|---|---|---|---|---|
| **2018** | 2 | -3.68 | -4.30 | 50.0% |
| **2019** | 10 | -23.03 | -25.82 | 30.0% |
| **2020** | 8 | -50.40 | -55.94 | 37.5% |
| **2021** | 9 | 16.56 | 19.47 | 77.8% |
| **2022** | 10 | -33.93 | -33.80 | 50.0% |

### B. Same-Time Cross-Currency Collision Partition

| Partition | Pairs ($N$) | Mean $\Delta \bar{R}$ (bps) | Mean $\Delta$ Pips | Win Rate |
|---|---|---|---|---|
| **Collision Sessions (GBP)** | 4 | -24.72 | -28.03 | 50.0% |
| **Collision-Free Sessions** | 35 | -20.92 | -21.86 | 48.6% |

### C. US 15:30 Morning Release Overlap Partition

| Partition | Pairs ($N$) | Mean $\Delta \bar{R}$ (bps) | Mean $\Delta$ Pips | Win Rate |
|---|---|---|---|---|
| **With 15:30 USD Release in Entry Bar** | 16 | -0.35 | -0.79 | 50.0% |
| **Without 15:30 USD Release in Entry Bar** | 23 | -35.89 | -37.58 | 47.8% |

### D. US Tier-1 Macro Interaction (NFP / CPI / FOMC)

> [!NOTE]
> **Diagnostic Status: NOT_EVALUATED (Pending Independent Pre-Outcome Addendum Review)**  
> Forensic catalog reconciliation of raw `calendar_releases.csv` identifies:
> - US Headline CPI m/m: `840030005` (139 releases, importance: high)
> - US Nonfarm Payrolls (NFP): `840030016` (140 releases, importance: high)
> - Federal Reserve Monetary Policy (FOMC): spans multiple distinct series (`840050014` Rate Decision [95 releases], `840050002` Statement [91 releases], `840050018` Press Conference [74 releases], `840050004` Minutes [94 releases], `840050003` Economic Projections [46 releases]).
>
> Due to standard calendar scheduling (NFP early month, CPI mid month, Ifo late month), neither NFP nor headline CPI falls within the 6-H4 holding window for any of the 40 Ifo episodes. Only FOMC Minutes (`840050004`) overlaps with a single episode (#29, 2021-11-24).
> Because FOMC encompasses multiple distinct release types and exact boundaries were not frozen in v1.2, this diagnostic is marked **NOT_EVALUATED** to prevent ad-hoc specification drift prior to Codex audit clearance.

### E. Outlier Sessions ($|\Delta R - \Delta \bar{R}| > 2\sigma$)

| Episode # | Broker Date/Time | Direction | $\Delta R$ (bps) | $\Delta$ Pips |
|---|---|---|---|---|
| #14 | `2020-03-25 12:30:00` | **SHORT** | -208.36 | -226.90 |
| #38 | `2022-10-25 11:30:00` | **SHORT** | -211.20 | -210.00 |
| #39 | `2022-11-24 12:30:00` | **LONG** | -233.77 | -239.70 |

---

## 7. Event-by-Event Ledger & Paired Observations (6 H4 - All 40 Actionable Episodes)

| # | Broker Date/Time | Dir | Entry Price | Exit Price | Event Pips | Ctrl Choice | Ctrl Pips | $\Delta$ Pips | Status / Disposition |
|---|---|---|---|---|---|---|---|---|---|
| #1 | `2018-11-26 12:30:00` | **SHORT** | 1.13647 | 1.13198 | 44.90 | `D_MINUS_7` | 21.30 | **23.60** | WIN |
| #2 | `2018-12-18 12:30:00` | **SHORT** | 1.13786 | 1.14010 | -22.40 | `D_MINUS_7` | 9.80 | **-32.20** | LOSS |
| #3 | `2019-01-25 12:30:00` | **SHORT** | 1.13568 | 1.14169 | -60.10 | `D_MINUS_7` | 36.50 | **-96.60** | LOSS |
| #4 | `2019-02-22 12:30:00` | **SHORT** | 1.13359 | 1.13543 | -18.40 | `D_MINUS_7` | -69.20 | **50.80** | WIN |
| #5 | `2019-04-24 11:30:00` | **LONG** | 1.12179 | 1.11470 | -70.90 | `D_PLUS_7` | -19.70 | **-51.20** | LOSS |
| #6 | `2019-05-23 11:30:00` | **SHORT** | 1.11393 | 1.11842 | -44.90 | `D_PLUS_7` | -14.10 | **-30.80** | LOSS |
| #7 | `2019-06-24 11:30:00` | **SHORT** | 1.13855 | 1.13849 | 0.60 | `D_PLUS_7` | 37.30 | **-36.70** | LOSS |
| #8 | `2019-07-25 11:30:00` | **SHORT** | 1.11288 | 1.11354 | -6.60 | `D_MINUS_7` | -11.70 | **5.10** | WIN |
| #9 | `2019-08-26 11:30:00` | **SHORT** | 1.11143 | 1.11128 | 1.50 | `D_PLUS_7` | 23.70 | **-22.20** | LOSS |
| #10 | `2019-10-25 11:30:00` | **LONG** | 1.11205 | 1.10911 | -29.40 | `D_MINUS_7` | 39.10 | **-68.50** | LOSS |
| #11 | `2019-11-25 12:30:00` | **LONG** | 1.10161 | 1.10169 | 0.80 | `D_MINUS_7` | 21.00 | **-20.20** | LOSS |
| #12 | `2019-12-18 12:30:00` | **LONG** | 1.11169 | 1.11146 | -2.30 | `D_MINUS_14` | -14.40 | **12.10** | WIN |
| #13 | `2020-02-24 12:30:00` | **LONG** | 1.08143 | 1.08406 | 26.30 | `D_MINUS_7` | -33.80 | **60.10** | WIN |
| #14 | `2020-03-25 12:30:00` | **SHORT** | 1.07980 | 1.09744 | -176.40 | `D_PLUS_7` | 50.50 | **-226.90** | LOSS |
| #15 | `2020-04-24 11:30:00` | **SHORT** | 1.07554 | 1.08494 | -94.00 | `D_PLUS_7` | 31.20 | **-125.20** | LOSS |
| #16 | `2020-06-24 11:30:00` | **LONG** | 1.13008 | 1.12291 | -71.70 | `D_MINUS_14` | 20.40 | **-92.10** | LOSS |
| #17 | `2020-07-27 11:30:00` | **LONG** | 1.16949 | 1.17205 | 25.60 | `D_PLUS_7` | 13.60 | **12.00** | WIN |
| #18 | `2020-08-25 11:30:00` | **LONG** | 1.18235 | 1.18141 | -9.40 | `D_MINUS_14` | -24.60 | **15.20** | WIN |
| #19 | `2020-09-24 11:30:00` | **LONG** | 1.16568 | 1.16556 | -1.20 | `D_PLUS_14` | 41.30 | **-42.50** | LOSS |
| #20 | `2020-11-24 12:30:00` | **SHORT** | 1.18537 | 1.19040 | -50.30 | `D_PLUS_14` | -2.20 | **-48.10** | LOSS |
| #21 | `2021-01-25 12:30:00` | **SHORT** | 1.21466 | 1.21564 | -9.80 | `D_MINUS_7` | -70.00 | **60.20** | WIN |
| #22 | `2021-02-22 12:30:00` | **LONG** | 1.21470 | 1.21489 | 1.90 | `D_MINUS_7` | -18.50 | **20.40** | WIN |
| #23 | `2021-04-26 11:30:00` | **LONG** | 1.20995 | 1.20579 | -41.60 | `D_MINUS_7` | 43.50 | **-85.10** | LOSS |
| #24 | `2021-05-25 11:30:00` | **LONG** | 1.22586 | 1.22406 | -18.00 | `D_MINUS_14` | -28.20 | **10.20** | WIN |
| #25 | `2021-06-24 11:30:00` | **LONG** | 1.19233 | 1.19413 | 18.00 | `D_PLUS_7` | -16.90 | **34.90** | WIN |
| #26 | `2021-08-25 11:30:00` | **SHORT** | 1.17510 | 1.17586 | -7.60 | `D_PLUS_7` | -31.80 | **24.20** | WIN |
| #27 | `2021-09-24 11:30:00` | **SHORT** | 1.17357 | 1.16891 | 46.60 | `CONTROL_UNAVAILABLE` | N/A | N/A | EXCLUDED (D_MINUS_7 rejected: High-importance EUR release conflict: CPI y/y@1631880000; D_PLUS_7 rejected: High-importance EUR release conflict: CPI y/y@1633089600; D_MINUS_14 rejected: High-importance EUR release conflict: ECB President Lagarde Speech@1631277000; D_PLUS_14 rejected: High-importance EUR release conflict: ECB President Lagarde Speech@1633705800) |
| #28 | `2021-10-25 11:30:00` | **SHORT** | 1.16494 | 1.16083 | 41.10 | `D_MINUS_7` | -79.60 | **120.70** | WIN |
| #29 | `2021-11-24 12:30:00` | **SHORT** | 1.12065 | 1.12185 | -12.00 | `D_PLUS_7` | 3.20 | **-15.20** | LOSS |
| #30 | `2021-12-17 12:30:00` | **SHORT** | 1.13072 | 1.12930 | 14.20 | `D_MINUS_7` | 9.30 | **4.90** | WIN |
| #31 | `2022-01-25 12:30:00` | **LONG** | 1.12754 | 1.12821 | 6.70 | `D_MINUS_7` | -34.10 | **40.80** | WIN |
| #32 | `2022-02-22 12:30:00` | **LONG** | 1.13403 | 1.13511 | 10.80 | `D_MINUS_7` | 7.10 | **3.70** | WIN |
| #33 | `2022-04-25 11:30:00` | **SHORT** | 1.07447 | 1.06808 | 63.90 | `D_MINUS_7` | -19.00 | **82.90** | WIN |
| #34 | `2022-05-23 11:30:00` | **LONG** | 1.06456 | 1.07043 | 58.70 | `D_MINUS_7` | 57.30 | **1.40** | WIN |
| #35 | `2022-07-25 11:30:00` | **SHORT** | 1.02220 | 1.02075 | 14.50 | `D_PLUS_7` | 15.20 | **-0.70** | LOSS |
| #36 | `2022-08-25 11:30:00` | **SHORT** | 1.00069 | 0.99886 | 18.30 | `D_PLUS_7` | 63.90 | **-45.60** | LOSS |
| #37 | `2022-09-26 11:30:00` | **SHORT** | 0.96847 | 0.96239 | 60.80 | `D_MINUS_7` | -34.10 | **94.90** | WIN |
| #38 | `2022-10-25 11:30:00` | **SHORT** | 0.98568 | 1.00380 | -181.20 | `D_PLUS_7` | 28.80 | **-210.00** | LOSS |
| #39 | `2022-11-24 12:30:00` | **LONG** | 1.04223 | 1.03720 | -50.30 | `D_MINUS_14` | 189.40 | **-239.70** | LOSS |
| #40 | `2022-12-19 12:30:00` | **LONG** | 1.06060 | 1.06153 | 9.30 | `D_MINUS_7` | 75.00 | **-65.70** | LOSS |
