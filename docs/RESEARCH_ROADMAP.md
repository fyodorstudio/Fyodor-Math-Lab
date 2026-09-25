# Macro Research Roadmap & Decision Sequence

> [!IMPORTANT]
> **GOVERNANCE STATUS: RESEARCH IN PROGRESS (ZERO PROFITABILITY EVIDENCE)**  
> **No registered setup, profitable edge, or executable trading recommendation exists in this repository.**  
> Prior trials (Phase 1 CPI/NFP and the German Ifo pilot trial with $p = 0.9575$) yielded no actionable trading setups.  
> The current candidate investigation (US Retail Sales on EURUSD) is strictly in pre-price feasibility and protocol audit. Candidate prices, win rates, and post-2022 holdout outcomes remain completely uninspected and sealed.

---

## 1. Current Research Sequence

The repository executes a strictly staged, unidirectional research pipeline:

```text
[1] Pinned Source Data & Inventory Audit                      [COMPLETE]
    - MT5 v3.1 export (76062b8f..., 893aa193...)
    - 30,015 pre-2023 packages, 1,172 series, 51 pairs
                      |
                      v
[2] US Retail Sales Price-Blind Feasibility                   [COMPLETE]
    - Co-release coherence: Headline (840020010) + Core (840020011)
    - 68/68 forward H4 path completeness verified on EURUSD
    - 49 strict-concordance packages (sign(S_H) * sign(S_C) > 0)
    - Confounder audits: 30/49 collisions, 15/49 Fridays, 65.3% control contamination
                      |
                      v
[3] Pre-Price Protocol Audit & Freeze                         [PENDING REVIEW]
    - Primary question: directional strategy viability under Scenario C (10 pts / 1.0 pip)
    - 1-sample Student's t-test (p < 0.05, win rate >= 53%, Friday/non-Friday positive)
    - Decision truth table and classify_discovery_outcome() 100% equivalent
    - Predeclared post-2022 holdout decision gates in classify_holdout_outcome()
                      |
                      v
[4] Pre-2023 Directional Strategy Viability Discovery         [AWAITING FREEZE]
    - Run unblinded calculation on N = 49 pre-2023 strict packages ONLY
    - If adverse (mean <= 0) -> DISCONFIRMED_ADVERSE; investigation terminated
    - If underpowered/fragile -> INCONCLUSIVE; investigation terminated
    - If meets all hurdles -> PROMISING_DISCOVERY_CANDIDATE (NOT a registered setup)
                      |
                      v
[5] Conditional Post-2022 Historical Holdout Validation       [SEALED]
    - Evaluated ONLY if Step 4 yields PROMISING_DISCOVERY_CANDIDATE
    - N_holdout < 15 -> HOLDOUT_SAMPLE_DEFICIENT (first branch; descriptive only)
    - N_holdout >= 15 & mean <= 0 -> HOLDOUT_FAIL (candidate permanently terminated)
    - N_holdout >= 15 & (p >= 0.05 | W < 50% | sign mismatch) -> HOLDOUT_INCONCLUSIVE
    - N_holdout >= 15 & p < 0.05 & W >= 50% & matching sign -> HOLDOUT_PASS_ELIGIBLE_FOR_DEMO
                      |
                      v
[6] Prospective Demo Ledger (Forward Execution Tracking)      [PROSPECTIVE ONLY]
    - First-seen live demo-account forward observation
    - Real-time timestamped capture of calendar values, spreads, slippage, and swaps
    - Evaluates forward viability on genuinely unseen market regimes
                      |
                      v
[7] Later Canvas Integration (C:\dev\NO-AI\canvas)            [FUTURE MILESTONE]
    - Terminal frontend integration permitted ONLY after substantial demo track record
    - Research lab remains strictly isolated from production terminal
```

---

## 2. Historical Holdout Independence vs. Genuine Prospective Testing

A rigorous epistemological boundary separates historical holdouts from forward observation:

1. **The 2023+ Historical Holdout (`timestamp >= 1672531200`)**:
   - The post-2022 dataset is a **retrospective chronological partition**, NOT a genuinely prospective forward trial.
   - Because the MT5 export spans 2015–2026, the 2023–2026 data were already present on disk during legacy laboratory operations. The independence of this partition from prior human inspection and exploratory trial exposure requires continuous forensic audit.
   - Clearing the holdout hurdle grants **eligibility for demo forward validation ONLY**. It does not prove that an anomaly is executable, profitable, or immune to historical data leakage.

2. **Genuinely Prospective Demo Testing**:
   - **Only future, first-seen live releases executed in a demo environment are truly out-of-sample.**
   - In prospective testing, calendar values and candle paths do not exist on disk prior to event arrival. An append-only forward capture engine records exact arrival timestamps, broker quote latency, effective entry/exit spreads, and financing costs.

---

## 3. Parked Future Research Question: Recurring Macro "State Signatures" ($S = A - F$, $M = A - P$)

> [!NOTE]
> **PARKED RESEARCH QUESTION (NOT AN ACTIVE EXPERIMENT)**:
> The following inquiry is formally cataloged for future investigation under a separate, independently frozen protocol.
> It does **NOT** modify the US Retail Sales protocol, does **NOT** introduce momentum ($M$) as an exploratory filter, and must **NOT** be executed at this time.

### 3.1 Conceptual Formulation
The Project Director has proposed exploring whether macroeconomic releases exhibit recurring **"state signatures"** based on the joint configuration of consensus surprise and macro momentum:
- **Consensus Surprise ($S$)**: Deviation from market expectations:
  $$S = \text{Actual} - \text{Forecast} = A - F$$
- **Macro Momentum ($M$)**: Directional trajectory relative to the prior period:
  $$M = \text{Actual} - \text{Previous} = A - P$$

### 3.2 Candidate Hypothesis
For releases within the **same exact macroeconomic series or co-released family**, do episodes exhibiting prospectively defined, similar relative $(S, M)$ state signatures produce higher win rates or positive mean directional net trade returns compared to dissimilar states or unconditional baselines?

- **Expectancy Over Perfection**: The hypothesis does **not** demand or assume a 100% win rate. It tests whether specific macro states offer positive net trade expectancy after deducting realistic bid–ask spread, slippage, and overnight financing friction.

### 3.3 Mandatory Methodological Guardrails
To prevent data mining and retrospective selection bias, any future trial investigating state signatures must adhere to these non-negotiable standards:
1. **Prior-Only Binning**: State similarity bins (e.g. quintiles, sign quadrants, or standardized $z$-score thresholds) must be specified **prospectively using prior-only historical data** (rolling lookback) before inspecting subsequent price outcomes.
2. **Exhaustive Denominator Accounting**: The study must explicitly report all qualifying and non-qualifying episodes across the entire historical series. Filtering out adverse outcomes by post-hoc tightening similarity criteria is strictly prohibited.
3. **No Retrospective Cluster Cherry-Picking**: An investigator cannot inspect the historical scatter plot, identify a favorable 2- or 3-case cluster of past winning trades, and retroactively declare it a "recurring signature."
4. **Independent Protocol & Holdout**: If pursued, this inquiry requires an independent protocol charter, a separate multiplicity adjustment ($K$-trial penalty), and validation on genuinely untouched data.
5. **Zero Interaction with Current Retail Sales Study**: Momentum ($M = A - P$) is strictly barred from being injected into the current Retail Sales pre-price design as a post-hoc filter.

---

## 4. Prior Trial History & Archive Links

This repository maintains an unbroken forensic record of all prior candidate trials:

| Trial / Milestone | Subject | Status / Outcome | Documentation Link |
|---|---|---|---|
| **Phase 1 Exploration** | USD CPI & NFP on EURUSD / USDJPY | Completed; no reliable delayed drift found | [`evidence/trials/phase1/PHASE1_EXPLORATION.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/phase1/PHASE1_EXPLORATION.md) |
| **Ifo Pilot Trial** | German Ifo Business Climate on EURUSD | Completed; **State 3: No Convincing Evidence** ($p = 0.9575$) | [`evidence/trials/ifo/ifo_pre2023_exploration_report.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/ifo_pre2023_exploration_report.md) |
| **Retail Sales Feasibility** | US Retail Sales m/m + Core on EURUSD | Completed; 49 strict-concordance packages, 68/68 paths clean | [`docs/RETAIL_SALES_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FEASIBILITY.md) |
| **Retail Sales Protocol** | Directional Strategy Viability on EURUSD | Pre-price design v0.5 pending Codex freeze review | [`docs/DRAFT_RETAIL_SALES_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/DRAFT_RETAIL_SALES_PROTOCOL.md) |
| **Historical Planning Archive** | Legacy FMS Roadmap (2026-09-24) | Archived reference snapshot | [`reference/planning-history/FMS_RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/planning-history/FMS_RESEARCH_ROADMAP.md) |
