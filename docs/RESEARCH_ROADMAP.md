# Macro Research Roadmap & Decision Sequence

> [!IMPORTANT]
> **GOVERNANCE STATUS: RESEARCH IN PROGRESS (NO VERIFIED PROFITABLE SETUP)**
> **No registered setup, profitable edge, or executable trading recommendation exists in this repository.**
> Prior trials (Phase 1 CPI/NFP, German Ifo pilot trial with $p = 0.9575$, and US Retail Sales discovery trial with mean -2.63 pips and $p = 0.6513$) yielded no actionable trading setups.
> The active candidate investigation is advancing to US ISM Manufacturing PMI (`USD:US:840040001:r0`) in price-blind feasibility. Candidate prices, spreads, and holdout outcomes remain completely uninspected and sealed.

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
    - 49 strict-concordance packages (sign(S_H) * sign(S_C) > 0)
    - Confounder audits: 30/49 collisions, 15/49 Fridays
                      |
                      v
[3] Pre-Price Protocol Audit & Freeze                         [COMPLETE]
    - Protocol v0.5 frozen byte-for-byte; schema 1.1.0 authorized
    - 43 synthetic unit tests passing; source hashes verified
                      |
                      v
[4] Pre-2023 Retail Sales Discovery Execution                 [COMPLETE: DISCONFIRMED]
    - Unblinded run on N = 49 pre-2023 strict packages (commit 2e2f3ff)
    - Scenario C mean net return = -2.63 pips (-2.45 bps), p = 0.6513, 25/49 wins
    - Frictionless Scenario A mean net return = -1.63 pips (-1.57 bps)
    - Disposition: DISCONFIRMED_ADVERSE; investigation terminated
                      |
                      v
[5] Conditional Post-2022 Historical Holdout Validation       [PERMANENTLY SEALED]
    - Terminated without unsealing due to adverse discovery point estimate
    - Post-2022 partition (timestamp >= 1672531200) remains untouched
                      |
                      v
[6] Next Candidate: US ISM Manufacturing PMI Feasibility      [ACTIVE SCREENING]
    - Price-blind feasibility pass on USD:US:840040001:r0
    - Calendar fields and candle timestamps only; zero OHLC/returns parsed
```

---

## 2. Historical Holdout Independence vs. Genuine Prospective Testing

A rigorous epistemological boundary separates historical holdouts from forward observation:

1. **The 2023+ Historical Holdout (`timestamp >= 1672531200`)**:
   - The post-2022 dataset is a **retrospective chronological partition**, NOT a genuinely prospective forward trial.
   - Because the MT5 export spans 2015–2026, the 2023–2026 data were already present on disk during legacy laboratory operations. The independence of this partition from prior human inspection and exploratory trial exposure requires continuous forensic audit.
   - Clearing the holdout hurdle grants **eligibility for demo forward validation ONLY**. It does not prove that an anomaly is executable, profitable, or immune to historical data leakage.

2. **Genuinely Prospective Demo Testing**:
   - Future, first-seen releases recorded under a fixed demo protocol offer genuinely prospective evidence. A historical holdout can be out-of-sample relative to a fixed model, but must not be described as prospectively observed, and its independence from earlier researcher exposure is uncertain here.
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

### 3.4 Questions to Resolve Before a Separate State-Signature Protocol
- Define the exact series, units, calendar vintage, and whether `Previous` means the value visible at release time or a later revised value. A retrospective calendar export alone does not establish point-in-time availability.
- Define a small, fixed set of scale-aware states within each series; an equal numeric difference across unlike indicators or changed units is not necessarily a similar economic surprise. State membership must use only information available before the trade.
- Predefine trade direction, entry, exit, friction, comparator, and the minimum number of independent episodes. Three matching outcomes are a lead, not a registration threshold; the relevant evidence is the complete conditional return distribution and uncertainty after costs.
- Record every attempted family, state definition, horizon, and pair before testing. A future trial needs an explicit selection/multiplicity policy and genuinely new validation evidence; do not recycle the current Retail Sales outcomes into a second confirmation claim.

---

## 4. Parked Idea: Price Zones and Post-Release Response Paths

The owner previously used support/resistance-aware stop-loss and take-profit levels and tracked event responses over 1, 2, 3, ... 60 or more H4 candles. Preserve these as **unvalidated research ideas**, separate from the active ISM price-blind design. A support or resistance level is conceived as a **zone with width**, where price may reverse or break through; neither outcome is assumed to have a demonstrated probability or positive expectancy here.

Any future test must define zones using only completed **pre-entry** H1/H4 bars: the lookback, swing/level algorithm, zone width, touch/break rule, and invalidation must be frozen before evaluating subsequent returns. Stop, target, and expiry must be set from information available at entry. H1 OHLC cannot always reveal whether a stop or target was hit first within the same bar; use a prespecified conservative resolution or obtain finer point-in-time data. Spread, slippage, gaps, and financing remain execution limitations.

The multi-horizon response curve may be reported descriptively (directional return, absolute move, maximum favorable/adverse excursion, and time to excursion), but scanning dozens of horizons and selecting the best one is a new multiple-testing exercise, **not** one prespecified setup. A tradable hypothesis needs one primary horizon or a predeclared correction scheme, an explicit comparator, and fresh validation. Do not retrofit zones, stops, targets, or horizons onto the already failed Retail Sales discovery as a rescue attempt.

---

## 5. Prior Trial History & Archive Links

This repository maintains an unbroken forensic record of all prior candidate trials:

| Trial / Milestone | Subject | Status / Outcome | Documentation Link |
|---|---|---|---|
| **Phase 1 Exploration** | USD CPI & NFP on EURUSD / USDJPY | Completed; no reliable delayed drift found | [`evidence/trials/phase1/PHASE1_EXPLORATION.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/phase1/PHASE1_EXPLORATION.md) |
| **Ifo Pilot Trial** | German Ifo Business Climate on EURUSD | Completed; **State 3: No Convincing Evidence** ($p = 0.9575$) | [`evidence/trials/ifo/ifo_pre2023_exploration_report.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/ifo_pre2023_exploration_report.md) |
| **Retail Sales Feasibility** | US Retail Sales m/m + Core on EURUSD | Completed; 49 strict-concordance packages, 68/68 paths clean | [`docs/RETAIL_SALES_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FEASIBILITY.md) |
| **Retail Sales Protocol & Freeze Packet** | Directional Strategy Viability on EURUSD | Frozen at commit `b674a0c`; authorized for pre-2023 discovery only | [`docs/DRAFT_RETAIL_SALES_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/DRAFT_RETAIL_SALES_PROTOCOL.md) & [`docs/RETAIL_SALES_FREEZE_PACKET.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FREEZE_PACKET.md) |
| **Retail Sales Discovery Trial** | Pre-2023 Discovery Execution on EURUSD | **DISCONFIRMED_ADVERSE** (Scenario C mean -2.63 pips, $p=0.6513$, 25/49 wins). Closed; holdout sealed. | [`docs/RETAIL_SALES_CLOSURE_NOTE.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_CLOSURE_NOTE.md) & [`evidence/trials/retail_sales/retail_sales_pre2023_discovery.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/retail_sales/retail_sales_pre2023_discovery.json) |
| **ISM Manufacturing Feasibility** | US ISM Manufacturing PMI on EURUSD | Active price-blind feasibility screening ($N=66$ actionable packages); zero prices read | [`docs/ISM_PMI_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/ISM_PMI_FEASIBILITY.md) |
| **Historical Planning Archive** | Legacy FMS Roadmap (2026-09-24) | Archived reference snapshot | [`reference/planning-history/FMS_RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/planning-history/FMS_RESEARCH_ROADMAP.md) |
