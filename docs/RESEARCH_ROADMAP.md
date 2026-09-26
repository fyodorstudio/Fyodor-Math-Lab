# Macro Research Roadmap & Decision Sequence

> [!IMPORTANT]
> **GOVERNANCE STATUS: RESEARCH IN PROGRESS (NO VERIFIED PROFITABLE SETUP)**
> **No registered setup, profitable edge, or executable trading recommendation exists in this repository.**
> Prior trials (Phase 1 CPI/NFP, German Ifo pilot trial with $p = 0.9575$, and US Retail Sales discovery trial with mean -2.63 pips and $p = 0.6513$) yielded no actionable trading setups.
> The active candidate investigation is US ISM Manufacturing PMI (`USD:US:840040001:r0`). ISM price outcomes have not been calculated; the post-2022 holdout remains sealed.

## Research Objective and What Counts as Progress

The owner's target is **not** a guarantee or a 100% win rate. It is an H1 macro-event setup with an observable entry rule, stop zone, target zone, maximum holding time, historical probability of **target before stop**, and quoted reward-to-risk (target distance divided by stop distance). Gross H1 price-path behavior is the primary research question. The owner will evaluate spread, slippage, commissions, and financing separately; research must not relabel gross results as executable net profit.

Searching historical discovery data for a promising pattern is legitimate. A favorable pattern found during that search is a **discovery**, including if luck helped produce it. It becomes stronger evidence only when the exact selected rule and all selection choices are recorded, and the rule then survives data not used to choose it. Three similar examples are an interesting lead, not a measured target-before-stop probability. No setup is registered for demo testing until its entry/stop/target/expiry rule and later validation are documented.

The existing ISM draft protocol asks a **narrower** question: whether entering one hour after a release and exiting after 24 active H1 bars has positive mean directional return under an assumed one-pip deduction. It does **not** test stop/target ordering, entry-time selection, zone width, or reward-to-risk. Its result cannot alone answer the owner's setup question; a separate H1 price-path discovery and frozen validation design is needed. Do not silently rewrite completed trials or call a fixed-exit result a target/stop setup.

### Event-family progress (broad grouping)

| Family | Rule actually examined or prepared | Current result | Target-before-stop and R:R? |
|---|---|---|---|
| US inflation (headline/core CPI and core PCE) | Large positive versus large negative forecast surprises; compare delayed H1 response after the first bar, chiefly through H12 | CPI contrast not convincing; core CPI/PCE comparisons underpowered | Not tested |
| US labor (Nonfarm Payrolls) | Same large-surprise delayed-H1 contrast | No convincing delayed effect | Not tested |
| German Ifo | Business Climate and Expectations surprises same nonzero sign; trade EURUSD in that direction from the next H4 open to the sixth active H4 close | Pilot found no convincing evidence | Not tested |
| US Retail Sales | Headline and core surprises same nonzero sign; trade EURUSD in that direction from the next H4 open to the sixth active H4 close | Pre-2023 discovery adverse; closed under its predeclared fixed-exit rule | Not tested |
| US ISM Manufacturing PMI | Headline forecast-surprise sign sets EURUSD direction; entry one active H1 after release; proposed fixed exit after 24 active H1 bars (48 H1 descriptive) | Pre-price feasibility and runner ready for review; **no ISM price outcome yet** | Not tested |

Thus **four broad families have some historical price analysis; a fifth, ISM, is prepared but has no price result. Zero families have completed the requested target-before-stop/R:R setup test.** US GDP was screened for data suitability only, not tested on prices. These counts describe this repository's audited work, not all work the owner ever attempted.

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
    - Post-2022 historical outcomes were not evaluated and remain sealed (full-file hashing and calendar scanning occurred)
                      |
                      v
[6] Next Candidate: US ISM Manufacturing PMI                  [PRE-PRICE READY]
    - Price-blind feasibility on USD:US:840040001:r0 complete
    - Draft fixed-exit test exists; zero ISM OHLC outcomes calculated
                      |
                      v
[7] H1 Entry / Stop / Target Discovery                         [NOT STARTED]
    - Separate, explicit search on discovery-period paths
    - Freeze one candidate; then validate on later history
    - Registration, if warranted, means demo-forward eligibility only
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
For releases within the **same exact macroeconomic series or co-released family**, do episodes with similar relative $(S, M)$ state signatures show different gross H1 target-before-stop frequencies or reward-to-risk from other states? A signature selected during discovery must be defined exactly before later validation.

- **Expectancy Over Perfection**: The hypothesis does **not** demand or assume a 100% win rate. A future gross-price-path study may ask whether a state improves target-before-stop frequency and reward-to-risk. Execution costs are a separate owner-managed assessment, not silently included in historical gross results.

### 3.3 Mandatory Methodological Guardrails
To make discovery interpretable and later validation meaningful, a future state-signature study must:
1. **Discovery Then Locking**: State-similarity bins (e.g. quintiles, sign quadrants, or standardized $z$-score thresholds) may be explored on discovery data, but the selected exact definition must be locked before later validation. Any rolling threshold used at trade time must depend on prior-only history.
2. **Exhaustive Denominator Accounting**: Report all qualifying and non-qualifying episodes across the discovery series. Exploratory tightening is allowed, but every tested definition and its unfavorable outcomes must remain visible.
3. **Discovery Versus Validation**: Investigators may inspect and select favorable historical clusters in designated discovery data, provided the whole search and denominator are recorded. A selected 2- or 3-case cluster is a hypothesis, not an independently validated recurring signature.
4. **Independent Protocol & Holdout**: Record how many definitions were explored; do not present a best-of-many discovery result as if it were a single prespecified test. Lock the chosen rule before a separate validation period.
5. **Preserve Closed Trials**: Do not revise the completed Retail Sales trial by adding momentum as though it had been part of that original rule. A new Retail Sales signature would be a new exploratory study.

### 3.4 Questions to Resolve Before a Separate State-Signature Protocol
- Define the exact series, units, calendar vintage, and whether `Previous` means the value visible at release time or a later revised value. A retrospective calendar export alone does not establish point-in-time availability.
- Define a small, fixed set of scale-aware states within each series; an equal numeric difference across unlike indicators or changed units is not necessarily a similar economic surprise. State membership must use only information available before the trade.
- Before validation, lock trade direction, entry, stop, target, expiry, comparator, and a minimum independent-episode count. Three matching outcomes are a lead, not a registration threshold; relevant evidence includes the full target-first/stop-first distribution and its uncertainty. Cost assessment is separate.
- Record every attempted family, state definition, horizon, and pair before testing. A future trial needs an explicit selection/multiplicity policy and genuinely new validation evidence; do not recycle the current Retail Sales outcomes into a second confirmation claim.

---

## 4. Priority Next Design: Price Zones and Post-Release Response Paths

The owner previously used support/resistance-aware stop-loss and take-profit levels and tracked event responses over 1, 2, 3, ... 60 or more candles. **H1 is the preferred granularity for any new response-path investigation; H4 describes the old implementation, not a current requirement.** These are now priority **unvalidated research ideas**, separate from the existing ISM fixed-exit draft. A support or resistance level is conceived as a **zone with width**, where price may reverse or break through; neither outcome is assumed to have a demonstrated probability here.

For each candidate, define zones using only completed **pre-entry H1 bars**: the lookback, swing/level algorithm, zone width, touch/break rule, and invalidation. Stop, target, and expiry must use information available at entry. Discovery may compare multiple documented entry delays, zone widths, stops, and targets; record every combination and outcome, then lock one rule before later validation. Report target-first, stop-first, neither-hit-by-expiry, and same-bar ambiguous counts separately. H1 OHLC cannot reveal whether stop or target was hit first within the same bar; use a prespecified conservative rule or mark those episodes unresolved. Report gross target/stop distances, reward-to-risk, observed win frequency, uncertainty, and realized R-multiple where determinable. Execution costs remain outside this price-path screen.

The multi-horizon response curve may be reported descriptively (directional return, absolute move, maximum favorable/adverse excursion, and time to excursion). Scanning horizons and selecting the best is legitimate **discovery**, not independent confirmation; disclose the search and validate the selected exact rule later. Do not relabel the already failed Retail Sales fixed-exit trial as a successful stop/target test. A genuinely different Retail Sales zone hypothesis would require a new, clearly exploratory study rather than retroactive alteration of its closed record.

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
| **ISM Manufacturing Feasibility** | US ISM Manufacturing PMI on EURUSD | Price-blind feasibility complete ($N=66$ actionable packages); zero ISM price outcomes calculated | [`docs/ISM_PMI_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/ISM_PMI_FEASIBILITY.md) |
| **Historical Planning Archive** | Legacy FMS Roadmap (2026-09-24) | Archived reference snapshot | [`reference/planning-history/FMS_RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/planning-history/FMS_RESEARCH_ROADMAP.md) |
