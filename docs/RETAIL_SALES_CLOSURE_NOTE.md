# US Retail Sales EURUSD Discovery Trial: Forensic Audit & Closure Note

> [!NOTE]
> **TRIAL STATUS: CLOSED (DISCONFIRMED_ADVERSE)**
> **FINAL DISCOVERY DISPOSITION**: **`DISCONFIRMED_ADVERSE`**
> **EXECUTION COMMIT**: [`2e2f3ffb0af0c3a2b19568a387b0db930fd1d0f5`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research)
> **RAW EVIDENCE ARTIFACT**: [`evidence/trials/retail_sales/retail_sales_pre2023_discovery.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/retail_sales/retail_sales_pre2023_discovery.json)
> `SHA-256 = 125aa3cf4b3160f6e8a3442186f69655e9a0303ff3421b5c85e4eafe19bf2481`
> **GOVERNANCE ACTION**: Investigation permanently terminated. The post-2022 historical holdout partition (`timestamp >= 1672531200`) was NOT evaluated and remains strictly sealed. Zero registered setups or live/demo trading recommendations exist.

---

## 1. Executive Summary & Verdict

Following formal authorization from the Project Director and Codex on 2026-09-26, the pre-2023 unblinded discovery calculation for US Retail Sales m/m (`USD:US:840020010:r0`) and Core Retail Sales m/m (`USD:US:840020011:r0`) on EURUSD was executed across the frozen $N = 49$ strict-concordance package sample.

The empirical point estimate is negative under the primary Scenario C friction hurdle (10 broker points / 1.0 pip) as well as under frictionless Scenario A (0.0 pips). In accordance with Condition #1 of the predeclared protocol decision truth table ([`docs/DRAFT_RETAIL_SALES_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/DRAFT_RETAIL_SALES_PROTOCOL.md)), the hypothesis is **disconfirmed**. The candidate is permanently terminated and closed.

---

## 2. Frozen Empirical Discovery Metrics (Pre-2023, $N = 49$)

### 2.1 Primary Screening Hurdle: Scenario C (Assumed 1.0 Pip Friction)
- **Actionable Sample Size**: Exactly **49 packages** (100% path completeness).
- **Winning Trades**: **25 / 49 wins** (51.02% win rate; required $\ge 53\% \implies$ **FAIL**).
- **Sample Mean Net Pips**: **-2.62857 pips** (loss of 2.63 pips per trade; required $> 0 \implies$ **FAIL**).
- **Sample Mean Net Log Return**: **-0.00024532** (-2.45 bps).
- **1-Sample Student's $t$-Test**: $t = -0.3912$, $p_{\text{1-sided}} = \mathbf{0.651320}$ (required $p < 0.05 \implies$ **FAIL**).
- **Confidence Bounds**:
  - 95% 1-Sided Lower Bound: **-0.00129702** (-12.97 bps).
  - 95% 2-Sided Confidence Interval: `[-0.00150609, +0.00101545]`.

### 2.2 Frictionless Baseline: Scenario A (0.0 Pips Friction)
- **Sample Mean Net Pips**: **-1.62857 pips**.
- **Sample Mean Net Log Return**: **-0.00015741** (-1.57 bps).
- **Statistical Significance**: $t = -0.2510$, $p_{\text{1-sided}} = 0.598572$.
- **Finding**: The directional drift is negative even in the absence of transaction costs. Transaction friction does not cause the strategy failure; the gross post-announcement drift itself does not favor the economic surprise direction.

### 2.3 Sensitivity Summary Across All 5 Cost Scenarios (6-H4)
| Scenario | Deduction | Mean Return ($\bar{R}_{\text{net}}$) | Mean Net Pips | $t$-Stat | $p$-Value (1-Sided) | Win Rate |
|---|---:|---:|---:|---:|---:|:---:|
| **Scenario A** | 0.0 pips | -0.00015741 (-1.57 bps) | -1.63 pips | -0.2510 | 0.5986 | 51.02% (25/49) |
| **Scenario B** | 0.5 pips | -0.00020137 (-2.01 bps) | -2.13 pips | -0.3211 | 0.6252 | 51.02% (25/49) |
| **Scenario C (Primary)** | **1.0 pip** | **-0.00024532 (-2.45 bps)** | **-2.63 pips** | **-0.3912** | **0.6513** | **51.02% (25/49)** |
| **Scenario D** | 2.0 pips | -0.00033322 (-3.33 bps) | -3.63 pips | -0.5314 | 0.7012 | 51.02% (25/49) |
| **Scenario E** | 3.0 pips | -0.00042112 (-4.21 bps) | -4.63 pips | -0.6715 | 0.7475 | 51.02% (25/49) |

---

## 3. Subgroup Reconciliation & Forensic Prose Correction

### 3.1 Formal Correction of Prior Prose Reporting
In the initial unblinding briefing, the figures cited for the cross-currency collision and clean subgroups were inadvertently copied from the descriptive 12-H4 diagnostic block rather than the primary 6-H4 horizon block. The verified primary 6-H4 metrics from the raw evidence JSON are recorded below:

- **PRIMARY 6-H4 Cross-Currency Collision Subgroup ($N = 30$, CAD/EUR co-releases)**:
  - **Wins**: **16 / 30 wins** (**53.33%** win rate). *(Prior prose incorrectly cited 17/30 from 12-H4)*.
  - **Mean Net Pips**: **+1.12000 pips** (+1.12 pips). *(Prior prose incorrectly cited -7.86 pips from 12-H4)*.
  - **Mean Net Return**: **+0.00008011** (+0.80 bps).
  - $t = +0.1050$, $p_{\text{1-sided}} = 0.4586$.
- **PRIMARY 6-H4 Clean USD Subgroup ($N = 19$, uncollided releases)**:
  - **Wins**: **9 / 19 wins** (**47.37%** win rate). *(Prior prose incorrectly cited 11/19 from 12-H4)*.
  - **Mean Net Pips**: **-8.54737 pips** (-8.55 pips). *(Prior prose incorrectly cited -1.84 pips from 12-H4)*.
  - **Mean Net Return**: **-0.00075915** (-7.59 bps).
  - $t = -0.6934$, $p_{\text{1-sided}} = 0.7515$.

### 3.2 Friday vs. Non-Friday Regimes (Scenario C)
- **Friday Subgroup ($N = 15$, 72-hour weekend gap crossing)**:
  - Mean Net Return: **-0.00110346** (-11.03 bps); Mean Net Pips: **-12.51 pips**; Win Rate: **46.67%** (7/15).
- **Non-Friday Subgroup ($N = 34$, continuous intra-week trading)**:
  - Mean Net Return: **+0.00013327** (+1.33 bps); Mean Net Pips: **+1.73 pips**; Win Rate: **52.94%** (18/34).

### 3.3 Strict Governance Rule: Zero Subgroup Cherry-Picking
Under protocol rules, subgroup analyses exist strictly as **attribution diagnostics and fragility hurdles**, NOT as mining pools to rescue a disconfirmed hypothesis. It is strictly prohibited to promote the intra-week ($N = 34$) or collision ($N = 30$) subgroups into an ad-hoc setup. The primary candidate fails because the total strict sample point estimate is adverse ($\bar{R}_{\text{net}} \le 0$).

---

## 4. Descriptive 12-H4 Persistence Diagnostic (48 Active Hours)

As predeclared, 12-H4 performance is reported strictly as a descriptive persistence check:
- **Sample Size**: 49 packages (100% path coverage).
- **Scenario C Mean Net Return**: **-0.00045805** (-4.58 bps).
- **Scenario C Mean Net Pips**: **-5.53 pips**.
- **Scenario C Win Rate**: **57.14%** (28 wins / 49).
- **Finding**: Drift remains negative over the two-day holding period; holding longer doubles the mean pip loss (-5.53 pips vs -2.63 pips).

---

## 5. Holdout Partition Status & Technical Disclosures

1. **Post-2022 Holdout Remains Sealed**:
   - The post-2022 historical holdout partition (`timestamp >= 1672531200`) was **NOT evaluated or calculated**.
   - Zero post-2022 candle prices or returns were parsed or computed.
   - Because the discovery run resulted in `DISCONFIRMED_ADVERSE`, the holdout partition is **permanently closed** without ever being unsealed.
2. **File Boundary Disclosures**:
   - Full-file cryptographic hashing (SHA-256) read all binary bytes of `calendar_releases.csv` and `candles_EURUSD_H1.csv` to verify data integrity before calculation, as disclosed in [`src/calculation_runner.py`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/calculation_runner.py).
   - In-memory CSV streaming read the timestamp column of all calendar release rows to reconcile total series counts, but candle prices post-split were never parsed into memory.

---

## 6. Archival Status

The Retail Sales directional pilot is formally concluded and archived. The complete raw execution record is preserved for immutable forensic audit at [`evidence/trials/retail_sales/retail_sales_pre2023_discovery.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/retail_sales/retail_sales_pre2023_discovery.json).
