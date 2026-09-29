# Grand Objective and Research Direction

**Maintained planning note — 29 September 2026.** This is the durable handoff for the Project Director, Codex, and future implementation agents. It records decisions and reasoning, but it is **not** a frozen trading protocol, a result ledger, or permission to register a setup. When a calculation needs an exact rule, the versioned [calculation contract](../CONTRACT%20AND%20PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md) and a new family-specific protocol must supply it. Preserve older protocols and outputs; never silently reinterpret them under this note.

## The objective

Find at least one **precisely specified, historically plausible, auditable macro-event setup** that the Director can freeze for **demo-account forward testing** in Fyodor Trading Terminal. The setup should state which releases and pair it applies to, how its direction is formed, when it enters, its ATR-based stop and target, its maximum holding period, and what happens when another major event arrives. It must be supported by an event-level ledger, sample counts, year-by-year behavior, failure cases, and an explicit record of how it was selected. Demo results then belong to a prospective, no-retuning phase.

The wider personal aspiration is eventually to trade profitably, potentially as a source of income. **Neither a positive historical gross result nor a visually convincing chart establishes that outcome.** This project does not require a guaranteed win rate. It seeks repeatable positive expectancy and sensible risk/reward, while honestly reporting uncertainty and failure. Historical calculations intentionally omit spread, slippage, financing, and other trading costs at the Director's request; they must therefore always be labelled **gross OHLC proxies**, not net or executable profit. The Director will handle practical cost assessment separately before any live-money decision.

The intended strategy is not necessarily a first-minute news trade. The Director's chart-reading hypothesis is that useful macro effects may persist into later H1 bars and subsequent days. Keep the existing first-H1-open-after-release entry and study H60, H120, and H240 observed-bar horizons. Minute or tick data is **not a prerequisite for this phase**. Do not claim that H1 bars reconstruct the announcement's first minutes or the intrabar order of stop/target touches.

## Where the project stands

```text
Pinned MT5 V4 calendar + H1 candles
        |
        v
Audited CPI V2 and NFP V2 exploratory packages + standalone HTML viewer
        |  completed locally; gross, historical; no winner selected
        v
NEW: USD CPI same-time bundle, A-P only, context and later-event analysis
        |  planned here; NOT yet implemented or tested
        v
Small, disclosed candidate shortlist and independent review
        |  future; no registered setup today
        v
Versioned Criterion chart snapshot + Director's episode audit notes
        |  only after a candidate is reviewed and approved
        v
Frozen demo forward test, with no retrospective retuning
```

The [root README](../../README.MD) defines the exported 28-pair FX whitelist and the **19-pair active research subset**. Nine truncated-history pairs are excluded even where they have recent bars. US CPI and US NFP currently use only the seven active pairs containing USD: `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, and `USDJPY`. Seven pair outcomes from one release are correlated expressions of **one macro episode**, not seven independent releases. Cross-symbol spillovers, commodities, and crypto are future, separately scoped questions.

The V4 broker/MT5 export is pinned locally under `raw_data/` and is Git-ignored. Full release years **2015–2025** are analyzed together; **January–August 2026** is a separate partial release cohort. Later candles may resolve those releases' H240 paths. These historical years have already been inspected; **none may now be described as an untouched holdout for a newly selected CPI-bundle rule**. Future genuine out-of-sample evidence must come from a separately declared untouched source/time interval or prospective demo observations.

The [research evidence index](../../Research%20Candidate/README.md) points to the final local packages `CPI_EXPLORATION_V2/run_20260929_v2_final` and `NFP_EXPLORATION_V2/run_20260929_v2_final`. Their package reconciliation passed, and four representative cases per family were independently recalculated from raw candles. That is **not** an independent raw-price recalculation of every trade or a proof of trading profitability. The reports contain 238,680 CPI and 271,596 NFP **trial rows**, largely repetitions of the same releases over pairs, signals, stops, targets, and horizons; these numbers are **not** independent trade opportunities. The published viewer is a generated, locally opening HTML evidence snapshot; its numbers come from the packages, not hand-entered HTML. Both V2 studies used `selection_policy = NONE`: the full 52-cell stop/target grid and H60/H120/H240 were displayed, **no candidate was selected and no setup registered**. Invalidated or superseded V1/intermediate packages must not be promoted because a number looks attractive.

**Worktree caution at the time this note was created:** the viewer builder, its tests, the generated HTML, and `Research Candidate/README.md` already had uncommitted changes made outside this documentation pass. Preserve and review those changes separately; this note neither validates nor replaces them.

Fyodor Trading Terminal currently provides the Director with a **versioned historical Criterion snapshot**, EURUSD CPI/NFP episode arrows, nominal entry/SL/TP chart lines, an Arrow Result panel, and persistent personal audit notes. That terminal is the later **manual chart-audit and forward-test surface**, not the place to develop or silently recalculate the next rule. Its existing published exploratory report is not automatically updated by this planning note or by new research outputs.

## Decisions made in the current discussion

1. **Next research is in this Expanded Macro Research repository, not a frontend/matrix rebuild.** Calculate and audit the bundle study here, then present comprehensible evidence in this repository's standalone HTML viewer. Mount only a reviewed, versioned shortlist/evidence snapshot in Terminal Criterion later. Do not rebuild the old interactive economic matrix in the terminal now.
2. **The new USD CPI-bundle research is A−P only.** Let `M = Actual − reported Previous`, within each indicator's own units. The Director deliberately drops forecast (`A−F`) from this *new* research because historical consensus feeds disagree and are incomplete. This also permits study of releases with no forecast. Keep existing A−F packages intact as historical baselines, but do not use forecast to form, rank, or filter the new CPI-bundle candidates. This choice sacrifices a direct measure of market surprise; **A−P is a change in a reading, not necessarily news to the market**. Never call the new rule a forecast-surprise strategy.
3. **Conflict is not automatically “no trade.”** When headline and core readings point in different directions, retain a named conflict category. Investigate whether headline, core, or relative magnitude appears more informative; a no-trade response can be one *tested alternative*, not the presumed correct answer. The May 2026 episode prompted this question and therefore is a **post-hoc discovery example**, not independent confirmation that any proposed remedy works.
4. **Do not assume four CPI readings carry four equal votes.** Headline includes core, and year-on-year readings overlap many months of data. Core may better reflect persistent inflation, yet headline shocks can matter, and the Federal Reserve formally targets headline **PCE**, not core CPI. The role of each CPI reading for this H1-entry EURUSD study remains an empirical question, not a hard-coded 25/25/25/25 weighting.
5. **A 90-day, pair-aware EUR/USD economic timeline is a useful inspection aid, not a 90-day optimization feature dump.** The Director's former matrix displayed EUR and USD releases grouped by Policy, Inflation, Economy, and Other, with release-time grouping and a selectable chart range. Preserve that *concept* for later compact evidence display if useful, without reading or importing the old repository. The research rule itself may use only a small, declared set of timestamped facts known by entry.
6. **Separate the initial release from information arriving during the trade.** Show both fixed H60/H120/H240 outcomes and a separately specified event-isolation sensitivity. Future releases' *schedules* may be known at entry; their *actual results* are not. Never use later results as entry features. Any future-event censor set and exact exit-bar policy require a new frozen protocol before calculation.
7. **Do the math and audits centrally, then let the Director inspect a shortlist.** The Director need not hand-score every release in a matrix. The HTML should disclose enough source values, counts, exceptions, and individual episodes to make the calculation challengeable. A visually attractive top cell alone cannot be called a registered setup; searching many cells and interpretations increases the chance of finding a lucky historical winner. Preserve every attempted comparison and negative result.

These decisions **do not retroactively change** the CPI/NFP V2 protocols, their results, or the general calculation contract. The next CPI-bundle run requires its **own versioned protocol and package**. Where the older contract describes A−F as permitted, the new study simply elects not to use it; if a contract requirement conflicts with the new decision, amend it explicitly rather than silently bypassing it.

## Why the USD CPI bundle is the next study

The old CPI V2 trade direction came **only** from US headline CPI month-on-month, event ID `840030005`. Yet the same release timestamp normally contains four tracked CPI series:

| Same-time CPI constituent | MT5 event ID | Proposed role in the new study |
| --- | --- | --- |
| Headline CPI m/m | `840030005` | Recent headline change; preserve as the existing benchmark direction. |
| Core CPI m/m | `840030006` | Recent underlying-price change; compare with headline, including disagreements. |
| Headline CPI y/y | `840030007` | Annual inflation context; analyze separately, not as an extra independent vote. |
| Core CPI y/y | `840030008` | Annual underlying-inflation context; analyze separately. |

The pinned calendar contains **140 CPI bundle timestamps** across the study scope and **139 with the headline m/m anchor**. One timestamp, `2025-12-18`, lacks both tracked m/m anchors in the MT5 export; do not synthesize them or silently substitute y/y. The four tracked series total **558 constituent rows**, rather than a complete 560. A co-timestamped *other family*, such as Initial Jobless Claims, is a separate collision/sensitivity flag. Core CPI is **part of the CPI bundle**, not an “external collision” to remove. Existing CPI V2's clean panel excluded eligible Jobless Claims coincidences; that filtering must remain explicit when comparing against V2.

### Concrete motivating case: 12 May 2026, EURUSD

The terminal showed a `15:30` **trade-server-clock** CPI release, a `16:00` research entry, and a long EURUSD direction from headline `A−P`. The pinned MT5 calendar values at that timestamp are:

| Series | A | P | A−P, in percentage points | Interpretation of this one comparison |
| --- | ---: | ---: | ---: | --- |
| Headline m/m | 0.6 | 0.9 | −0.3 | Monthly headline pace cooled. |
| Core m/m | 0.4 | 0.2 | +0.2 | Monthly core pace heated. |
| Headline y/y | 3.8 | 3.3 | +0.5 | Annual headline rate rose. |
| Core y/y | 2.8 | 2.6 | +0.2 | Annual core rate rose. |

The [official BLS release](https://www.bls.gov/news.release/archives/cpi_05122026.htm) corroborates the published actual and prior rates. Rising y/y alongside cooling m/m is possible partly because a y/y change depends on the comparison month a year earlier; it is not four independent contradictory announcements ([BLS explanation](https://www.bls.gov/blog/2023/understanding-the-math-behind-recent-inflation-trends.htm)). [CME's same-day commentary](https://www.cmegroup.com/videos/2026/05/12/euro-futures-fell-to-range-midpoint-amid-hot-cpi-and-dollar-bid-.html) described a dollar bid and euro reversal. Those observations support a **plausible mixed-bundle explanation**, not proof of the unique cause of EURUSD's move.

Forecast discrepancy motivates the new boundary but is **not** itself the new signal: MT5 stored headline/core m/m forecasts of `0.7/0.1` for this release; [ING's pre-release note](https://think.ing.com/downloads/pdf/article/fx-daily-impact-of-us-cpi-mostly-depends-on-equities) described `0.6/0.3` consensus. Neither observation, alone, proves a particular vendor was wrong. The Director chooses not to spend this phase reconciling surveys.

The chart ran far beyond release day. [US PPI arrived on 13 May](https://www.bls.gov/news.release/archives/ppi_05132026.htm), and [US retail sales arrived on 14 May](https://www.census.gov/retail/marts/www/adv2604_layout_preview.pdf). The full path through late May must **not** be attributed solely to the 12 May CPI bundle. Unscheduled developments, oil, risk sentiment, and policy expectations may also matter and are not automatically captured by the broker calendar. This example is a *research question and audit case*, not evidence that a core-led trade would have won in general.

## Proposed CPI-bundle research sequence — not yet a frozen rule

### A. Establish a clean, point-in-time descriptive ledger

Use one atomic episode per CPI timestamp and pair. Attach the four constituent IDs, their units, A/P values, missing/zero flags, source rows, and any exported revision fields. Keep the original trade-server clock and input hashes. Confirm which `previous` value was actually available at release time; a later historical export does not establish its publication vintage. A−P results depending on unresolved vintage must be flagged, not quietly declared live-reproducible. Inventory bundle completeness and co-timestamped non-CPI releases **before** comparing outcomes. Report independent release N separately from pair-observation N and trial-cell N, by full year and 2026 partial cohort.

For each CPI series `i`, calculate `delta_i = A_i − P_i`, with **positive, negative, zero, and missing** separate. Preserve the raw percentage-point difference. A−P on a y/y rate is a change in the annual rate and has base-effect complications; do not label it identical to month-on-month acceleration. Compare series within their own definitions and never sum raw percentage-point changes as if they had equal meaning.

### B. Describe disagreement and possible magnitude, without inventing weights

Start with headline-versus-core **m/m** sign states: `(+,+)`, `(+,-)`, `(-,+)`, `(-,-)`, plus explicit zero/missing states. Display both y/y signs as an additional trend axis rather than crossing all four binaries into an unmanageably sparse 16-cell trading grid. Show every state's unique release N by year, not merely its pooled trade count. Preserve conflict episodes; do not automatically trade, reverse, or exclude them.

A **proposed, not frozen** comparison is the *within-series historical rank* of each `|A−P|`: how unusual was this change relative to **earlier releases of the same indicator**, with its sign stored separately? Any percentile or robust normalization must use only observations available before the episode; document the trailing window, minimum history, ties, zero-heavy data, revisions, and missingness **before** looking at outcomes. Ninety days contains only about three monthly CPI releases and is a viewer context window, **not** a sufficient percentile reference. A 90th-percentile core change versus a 55th-percentile headline change means the former is more unusual *within its own history*; it does **not** establish a 90:55 market-impact weight or a direction automatically. Avoid post-hoc numerical weights fitted to the May 2026 loss.

### C. Compare a deliberately small set of interpretations

First report descriptive paths and outcomes for the already known headline-only A−P benchmark and clearly separated candidate interpretations such as **core-led**, **headline/core concordance**, and **conflict stratified by predeclared relative magnitude**. These are suggestions for a future protocol, **not yet authorized or fully specified trade rules**. If a category predicts a direction, zero or abstention, define it before its price result is calculated. Assess what each interpretation keeps, removes, or changes by year; how many unique CPI releases remain; and what happens to gross R, TP/SL/timeout, MFE/MAE, ambiguous same-bar touches, and time-to-exit. Core-only is not assumed correct; “conflict = no trade” is not assumed correct either.

Compare signal interpretations on **the same episode set, H1 entry, ATR, and initially fixed exit settings**. Do not simultaneously select the best of 52 ATR cells × three horizons × every new interpretation and report that winner as if it were a single prespecified test. The old full grid remains a descriptive benchmark and can be run for all disclosed candidates later, with the full number of searched combinations visible. The exact initial comparison cell(s), candidate definitions, selection statistic, and validation schedule must be frozen in the new protocol; this note does not choose them by looking at existing outcomes.

### D. Add context and later-event attribution without lookahead

Separate three clocks in every episode:

1. **Before release / known by entry:** a compact, timestamped EUR-and-USD context view. A proposed 90-day timeline may group available releases by Policy, Inflation, Economy, and Other, and may also sort by release time. The UI may show many facts for forensic reading. Only a small, separately declared subset with proven availability may influence an executable rule. Missing or stale prior events remain missing/stale, not implicitly neutral.
2. **At release:** all simultaneous CPI members form **one bundle**; other same-time families are flagged. Use only values published by the H1 entry. Keep source and timestamp distinctions explicit.
3. **After entry:** mark later major releases and other known updates. Their occurrence may explain subsequent price, but their actual values **cannot** be fed back into the initial signal. Compare the fixed-H60/H120/H240 result with a separately labelled “exit/censor at next predefined major event” sensitivity. Predeclare the event set and exact bar boundary. Do not censor every tiny calendar item just because it is available, and do not call a censored exit TP, SL, or ordinary expiry.

The existing H1 export resolves the **post-entry H1 research question**. It cannot identify the precise first-minute response or the order of two barriers touched within the same H1 candle. The first limitation is accepted for this phase; retain the contract's stop-first primary bound and target-first sensitivity for the second. No current task requires fetching ticks or rebuilding the exporter.

### E. Make results inspectable, then consider registration

In this repo, extend the generated HTML only after the calculator and ledger pass independent checks. A minimal CPI-bundle inspection should expose: four A/P/delta values and their signs, a clearly sourced percentile if adopted, same-time other events, unique release N, per-year results, comparison with headline-only, fixed-horizon versus next-event outcomes, and drill-down to each underlying episode. A compact *Before / At / During* explanation is preferable to duplicating the former full matrix UI. The HTML must consume validated, immutable package data; it must not contain manually typed “winning” numbers or hide losing subsets.

Before a setup is nominated for demo: show complete candidate-search history, year/episode independence, annual and leave-one-year-out stability, adjacent-cell behavior, execution ambiguity, source and revision limitations, and a transparent counterfactual such as the old headline-only rule. Where feasible, use a properly declared direction-permutation or later genuinely prospective observations. **This historically inspected sample cannot turn into a fresh holdout merely because the new interpretation is written down today.** A shortlist may still justify chart audit and demo observation, but its evidence tier must be labelled honestly.

After review, publish a **versioned Criterion snapshot** with only the approved candidate's identification, frozen rule, eligible episodes, and audit links. The terminal's chart arrows and persistent notes are for Director/Codex manual assessment, not proof that the exploratory winner will repeat. Future demo results must stay separate from the historical package.

## Future expansion, after CPI-bundle understanding

The same **bundle → known context → later-event timeline → fixed outcomes → audit** architecture can be reused for other families. NFP's existing dataset contains payrolls plus same-time unemployment and wage measures; it likewise must not be treated as payrolls alone without disclosing the bundle. PPI, policy decisions, retail sales, GDP, PMIs, other currencies and eventually other instruments are possible subsequent studies **only with their own series definitions, sign conventions, point-in-time data checks, and independent episode counts**. Do not turn all released fields and every pair into one opaque score merely because the calendar makes that technically possible. Expand family by family, reusing tested infrastructure rather than copying the CPI interpretation indiscriminately.

## What the next implementation pass must settle explicitly

- New CPI-bundle protocol identifier, baseline input hashes, date cohorts, and preservation of V2 outputs.
- Four series' availability, A/P/revision-vintage caveats, zero/missing handling, and the exact use (or descriptive-only role) of y/y.
- The finite list of candidate direction/abstention rules and **a priori** comparison settings; whether a rolling percentile is included, its history window, and its handling of ties/warmup.
- Same-time non-CPI collision policy, later contaminating-event set, and first/last eligible H1 bar at a future event.
- Fixed benchmark exits before any renewed stop/target search, with all attempted alternatives disclosed.
- Audit tests, per-year and independent-bundle counts, verification of the HTML against the package, and a clear outcome label that does not claim net profitability or registration.

This list is a **design checklist**, not a claim that those decisions were already made. The immediate next deliverable should be a **versioned, auditable USD CPI-bundle research protocol and input-only bundle inventory** in Expanded Macro Research, followed by outcome calculation and HTML presentation only after its definitions are reviewed. Do not modify the Terminal frontend first, infer instructions from deprecated repositories, or treat this maintained note as an instruction to overwrite the current report.
