# US Retail Sales EURUSD Research Freeze Packet

> [!CAUTION]
> **GOVERNANCE STATUS: PENDING CODEX / PROJECT DIRECTOR APPROVAL**
> **CURRENT STATE: FROZEN SPECIFICATION PENDING AUDIT (NOT APPROVED, NOT EXECUTED)**
> This document is a formal pre-price research freeze record.
> **Strict Operational Boundary**: This freeze packet does **NOT** authorize an empirical price run, does **NOT** authorize parsing candle prices or calculating trade returns, and does **NOT** authorize opening or unsealing the post-2022 historical holdout partition (`timestamp >= 1672531200`). Live or demo order dispatch is strictly prohibited.
> The protocol parameters and decision rules herein are frozen byte-for-byte; they must **NOT** be altered or retrofitted to improve expected results.

---

## 1. Frozen Baseline Commit & Protocol Anchors

- **Repository Baseline Commit SHA**: [`b32fb8c14f2cf383d0358bbbc6b7df13bb891f03`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research)
- **Governing Protocol Document**: [`docs/DRAFT_RETAIL_SALES_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/DRAFT_RETAIL_SALES_PROTOCOL.md) (Pre-Price Design v0.5)
- **Feasibility Investigation**: [`docs/RETAIL_SALES_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FEASIBILITY.md)
- **Executable Calculation Runner**: [`src/calculation_runner.py`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/calculation_runner.py)
- **Unit Test Suite Status**: **43 / 43 tests passing** (`python -m unittest discover -s tests` executed in 7.84s clean)

---

## 2. Pinned Cryptographic Source Provenance Hashes

Every input data file is pinned to an immutable SHA-256 digest:

| Artifact Description | Disk Location | SHA-256 Hash |
|---|---|---|
| **Raw Economic Calendar** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv` | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` |
| **EURUSD H1 Candle Data** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv` | `893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5` |
| **Pre-2023 Episode Ledger** | `evidence/inventory/fms_episodes.jsonl` | `37df7880a2bc36dbbce06b4a6ba39f7bd962a4c1c92eb2ce64cb71a886de55d2` |
| **Symbol Specification** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candle_symbols.csv` | `3b067061adbb6e941be26006f9451e853a91cd622479e78387b32102a43755b1` |

*Verified Symbol Specification*: EURUSD 5 digits (`symbol_digits = 5`), point = `0.00001`, 1 standard pip = 10 broker points (`0.00010`).

---

## 3. Primary Trading Rule & Candidate Sample Specification

### 3.1 Primary Horizon & Execution Mechanics (6-H4 Rule)
- **Tradable Instrument**: `EURUSD` (PERIOD_H1 broker trade-server time).
- **Temporal Entry**: Open of the next active H4 bar immediately following release window completion:
  - `15:30:00` release $\implies$ Entry at **16:00:00 H4 Open** (30-minute delay; 35 of 49 packages).
  - `16:30:00` release $\implies$ Entry at **20:00:00 H4 Open** (210-minute / 3.5-hour delay; 14 of 49 packages).
- **Holding Period**: Exactly **6 completed active H4 blocks** ($B_0, \dots, B_5$, 24 active trading hours).
- **Exit Pricing**: Bid price for Long trades, Ask price for Short trades, evaluated at the Close of H4 block $B_5$.
- **Directional Shock Mapping**:
  - **Hawkish Shock** ($S_H > 0 \land S_C > 0$): **Short EURUSD** ($d_i = -1$).
  - **Dovish Shock** ($S_H < 0 \land S_C < 0$): **Long EURUSD** ($d_i = +1$).
- **Exploratory Diagnostic**: 12-H4 (48 active hours) evaluated strictly as a descriptive persistence check; no secondary hypothesis gate or separate setup claim.

### 3.2 Actionable Sample: Strict Concordance ($N = 49$)
The primary test sample is restricted strictly to pre-2023 packages where Headline (`USD:US:840020010:r0`) and Core (`USD:US:840020011:r0`) agree in surprise sign:
$$\text{sign}(S_H) \times \text{sign}(S_C) > 0$$
- **Hawkish Packages (Short EURUSD, $d = -1$)**: Exactly **27 packages**.
- **Dovish Packages (Long EURUSD, $d = +1$)**: Exactly **22 packages**.
- **Total Actionable Discovery Sample**: Exactly **$N = 49$ packages**.
- **EURUSD Timestamp Path Coverage**: **49 / 49 (100.0%)** complete paths for both 6 H4 and 12 H4.
- **Excluded Pre-2023 Packages (Exhaustive Accounting)**:
  - Active sign conflicts ($\text{sign}(S_H) \times \text{sign}(S_C) < 0$): **9 packages** (5 POS/NEG, 4 NEG/POS).
  - Missing consensus forecast: **28 packages** (24 in 2015–2016, 4 in Jan–Apr 2017).
  - Double zero surprise ($S_H = 0 \land S_C = 0$): **2 packages**.
  - Single zero surprise ($S_H = 0 \lor S_C = 0$): **8 packages**.
  - Total non-actionable packages: $9 + 28 + 2 + 8 = \mathbf{47\text{ packages}}$ ($49 + 47 = 96$ total releases).

---

## 4. Primary Screening Friction: Scenario C (Assumed 1.0 Pip)

Viability is evaluated across five predeclared sensitivity tiers, anchored to **Scenario C**:

| Scenario ID | Points Hurdle | Pips Hurdle | Price Deduction ($\Delta P$) | Role in Frozen Protocol |
|---|---:|---:|---:|---|
| **Scenario A** | 0 pts | 0.0 pips | 0.00000 | Frictionless theoretical baseline. |
| **Scenario B** | 5 pts | 0.5 pips | 0.00005 | Assumed minimal spread-only deduction. |
| **Scenario C** | **10 pts** | **1.0 pip** | **0.00010** | **Sole Primary Viability Hurdle**: Must yield $\bar{R}_{\text{net}} > 0$. |
| **Scenario D** | 20 pts | 2.0 pips | 0.00020 | Assumed conservative spread deduction. |
| **Scenario E** | 30 pts | 3.0 pips | 0.00030 | Hypothetical combined-cost sensitivity buffer (spread + commission + slippage/swap). |

---

## 5. Fixed Decision Gates

The software classification engine ([`src/strategy_viability.py`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/strategy_viability.py)) and written rules are 100% mathematically aligned:

### 5.1 Pre-2023 Discovery Decision Gates (Scenario C)
1. **`DISCONFIRMED_ADVERSE`**: $\bar{R}_{\text{net}} \le 0.0 \implies$ Adverse point estimate; investigation terminated; post-2022 holdout permanently sealed.
2. **`INCONCLUSIVE_UNDERPOWERED`**: $\bar{R}_{\text{net}} > 0.0$ and $p_{\text{1-sided}} \ge 0.10 \implies$ Statistically indistinguishable from noise; investigation terminated.
3. **`INCONCLUSIVE_FRAGILE`**: $\bar{R}_{\text{net}} > 0.0$ and either:
   - $0.05 \le p_{\text{1-sided}} < 0.10$, OR
   - Win Rate $W < 53\%$, OR
   - Friday subgroup mean $\bar{R}_{\text{Fri}} \le 0.0$, OR
   - Non-Friday subgroup mean $\bar{R}_{\text{NonFri}} \le 0.0$.
   $\implies$ Lacks consistency across market regimes; investigation terminated.
4. **`PROMISING_DISCOVERY_CANDIDATE`**: $\bar{R}_{\text{net}} > 0.0$ AND $p_{\text{1-sided}} < 0.05$ AND $W \ge 53\%$ AND $\bar{R}_{\text{Fri}} > 0.0$ AND $\bar{R}_{\text{NonFri}} > 0.0$.
   $\implies$ Promising candidate (**NOT A REGISTERED SETUP**); unlocks permission for Codex to review holdout unsealing.

### 5.2 Predeclared Post-2022 Holdout Gates (Sealed Partition: $t \ge 1672531200$)
1. **`HOLDOUT_SAMPLE_DEFICIENT`**: $N_{\text{holdout}} < 15$ packages $\implies$ Descriptive metrics only; no inference; candidate terminated.
2. **`HOLDOUT_FAIL`**: $N_{\text{holdout}} \ge 15$ and $\bar{R}_{\text{holdout, net}} \le 0.0 \implies$ Fails out-of-sample replication; candidate permanently terminated.
3. **`HOLDOUT_INCONCLUSIVE`**: $N_{\text{holdout}} \ge 15$ and $\bar{R}_{\text{holdout, net}} > 0.0$, but $p_{\text{holdout}} \ge 0.05$ OR $W < 50\% \implies$ Statistically weak; candidate terminated.
4. **`HOLDOUT_PASS_ELIGIBLE_FOR_DEMO`**: $N_{\text{holdout}} \ge 15$ AND $\bar{R}_{\text{holdout, net}} > 0.0$ AND $p_{\text{holdout}} < 0.05$ AND $W \ge 50\%$.
   $\implies$ Grants eligibility for forward demo-account tracking ONLY (**NOT PROOF OF PROFITABILITY**).

---

## 6. Known Forensic Limitations & Disclosures

1. **Unmeasured All-In Execution Costs**:
   - The pinned candle export records Bid prices and bar spread only.
   - Historical round-turn commissions ($3–$7/lot), entry/exit fill slippage (1–5 points), and overnight financing swaps (especially on 15 Friday releases crossing the 72-hour weekend gap) are unmeasured on disk.
   - Scenario E (30 broker points / 3.0 pips) provides an assumed combined stress-test, but live forward execution may face different slippage and swap regimes.
2. **Retrospective Calendar Vintages**:
   - The MT5 economic calendar export is a retrospective historical dataset, not an auditable live ticker feed recorded at announcement time.
   - "Previous" figures in historical calendar exports may reflect subsequent revisions rather than the exact value displayed on trader terminals at release seconds.
3. **Historical Holdout Exposure**:
   - The 2023+ partition (`timestamp >= 1672531200`) was present in the local filesystem during earlier lab operations. True independence from prior human inspection cannot be mathematically guaranteed.
   - Consequently, clearing the holdout grants eligibility for **prospective forward demo validation only**, not an immediate claim of genuine out-of-sample confirmation.
4. **Multiplicity and Prior Trials**:
   - Retail Sales is candidate step $K > 1$ in an iterative search sequence following Phase 1 (CPI/NFP) and German Ifo ($p = 0.9575$). Nominal p-values are conditioned on prior exploratory screening.

---

## 7. Explicit Reviewer Sign-Off & Freeze Status

| Review Dimension | Requirement | Audit Status |
|---|---|---|
| **Git Baseline** | Commit `b32fb8c14f2cf383d0358bbbc6b7df13bb891f03` verified clean | **VERIFIED** |
| **Unit Test Coverage** | 43 / 43 tests passing | **VERIFIED** |
| **Price Blindness** | Zero candle prices parsed; zero returns computed | **VERIFIED** |
| **Holdout Boundary** | `timestamp >= 1672531200` completely sealed | **VERIFIED** |
| **Codex / Director Approval** | Formal sign-off to proceed to pre-2023 price execution | **PENDING AUDIT & SIGN-OFF** |

> [!IMPORTANT]
> **NEXT ACTION**: Stop and await Codex Quant Director audit and Project Director steering decision.
