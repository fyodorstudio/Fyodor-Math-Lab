# Expanded Macro Research — working plan

**Status:** planning contract for a new, isolated repository. It is not a frozen trading rule, backtest result, or authorization to trade. The old Macro Research repository remains historical reference; none of its results or code are silently imported into this one.

## 1. Decisions fixed for this repository

| Topic | Current contract |
| --- | --- |
| Asset universe | The **28 FX pairs** in the seven “Forex Major” and 21 “Forex Extended” local placeholders. Their eight currencies are AUD, CAD, CHF, EUR, GBP, JPY, NZD and USD. Crypto, energy and metals are future wishes, **not** in this pass. |
| Pair relevance | For a release associated with currency X, the primary study includes listed FX pairs with X as base or quote. Test all relevant pairs in **one family-level calculation pass**, not by repeatedly redesigning the event study for each pair. Indirect spillovers to pairs without X require a separate named study. |
| Price resolution | **H1 candles only.** No M15, M30, M1 or tick export in this pass. Entry is the open of the first H1 bar **strictly after** the release timestamp; record the actual wait. Do not call this an at-release fill. |
| Holding horizons | H60, H120 and H240 mean 60, 120 and 240 **observed H1 market bars after entry**. They are not fixed calendar-day durations. |
| Exporter | One configurable MT5 exporter must eventually accept arbitrary available broker symbols. Its **first configured run** requests the 28 FX pairs above, H1 candles, and economic-calendar records for the eight currencies. The script is not yet present or frozen. |
| Data completeness | Export whatever the broker truly supplies, with per-symbol/calendar coverage, missing intervals, errors and hashes. Never invent bars or backfill missing A/F/P values. A case lacking the data required by its declared rule is excluded with a reason, not counted as a loss. |
| Evidence and presentation | Python source lives in `HTML Viewer/Python Calculator/`; calculated, versioned ledgers/reports live in `Research Candidate/`; `HTML Viewer/table_viewer.html` is a standalone local presentation artifact. The viewer never supplies or changes research numbers. |

The pair whitelist is preserved in the root README because ignored empty placeholder directories do not survive a Git clone. A listed pair is an **allowed candidate**, not a claim that a particular announcement moved its price.

## 2. Time boundary, especially partial 2026

- **Full-year comparison core:** releases dated **2015-01-01 through 2025-12-31**, subject to actual A/F/P and price coverage. Do not call every year equally complete: older calendar forecasts may be absent.
- **Separate partial-year panel:** releases dated **2026-01-01 through 2026-08-31**. This August cutoff is a conservative *release-date* boundary for comparing H60/H120/H240 against a price snapshot extending at least into late September 2026. It is not proof that each August event has H240 coverage; verify each path.
- The raw **candle** export must extend beyond the release-date cutoff: December 2025 releases may need January 2026 candles, and August 2026 releases need September candles. Record the actual latest complete candle timestamp in the dataset manifest. Do not truncate prices at 2025-12-31 or 2026-08-31.
- September–December 2026 are **not** part of this first common-H240 comparison. A later snapshot may add them under a new version. Never score an incomplete H240 path as a stop, timeout or zero return.
- Alongside horizon-specific eligible Ns, show a **common-complete cohort** with all three horizons available, so changes between H60/H120/H240 are not caused by changing the event sample.
- The 2015–2026 historical paths in the old project have already been viewed; neither the core nor the partial panel is an untouched holdout. Prospective observations after a rule is registered are the meaningful new-data test.

## 3. Questions to research, not answers to assume

**A** is released actual, **F** is forecast, **P** is the exported previous value. **S = A−F** measures announcement surprise; **M = A−P** measures movement from the reported previous reading. S and M are derived from A/F/P, not independent data sources. Keep `previous` distinct from `revised_previous`; a static historical calendar snapshot does not establish precisely which revision was visible at each release. See the [St. Louis Fed's real-time-vintage explanation](https://alfred.stlouisfed.org/help).

Start with CPI and NFP as **separate** family protocols, then extend to other macro families under versioned definitions. For CPI, evaluate headline/core sign agreement and the four S/M sign quadrants (`+/+`, `+/−`, `−/+`, `−/−`) plus zero, mixed and missing cases. For NFP, distinguish headline payrolls, unemployment and wages; their economic signs and units are not interchangeable. NFP A−P requires its own defensible previous/revision rule before any price trial. Same-time releases are bundles; never label an NFP report “isolated” simply because its headline is the primary signal.

The older project's CPI A−F/H24 and CPI A−P/H60 findings are **legacy exploratory observations**, not evidence generated by this repository and not registered setups. They may guide questions but must not be copied into new results as validation. NFP A−F price results were not established in this repository, and NFP A−P is unresearched.

For each event family, write one event-and-pair eligibility ledger before making performance claims. The ledger must expose timestamp, pair, A/F/P completeness, direction rule, coincident releases, entry bar, ATR input window, candle coverage, exclusion reason and data version. A pair's direction must account for whether the event currency is the **base** or **quote**. Preserve per-event records for manual audit in the viewer.

## 4. Price-path questions and guarded search

**Fixed-horizon analysis is primary.** For each rule and pair, compare identical entries and barriers at H60, H120 and H240. Also test a separately labelled **event-isolation sensitivity**: the earliest of TP, SL, Hmax or the next *predeclared* contaminating event. Freeze the contaminating event IDs and the H1 exit convention before calculating it. An announcement inside an H1 bar cannot be exited at that bar's post-announcement close and called pre-event censoring; use the last fully completed bar strictly before it or mark the case unresolved. Same-time releases belong to the initial bundle, not the future-event censor.

The proposed ATR stop/target grid is **not frozen yet**. The notation `1:4` is ambiguous once the stop is 2–4 ATR: it might mean a target four ATR away or four times the stop distance. Keep that choice open for the Director's separate Q&A pass. Until then, do not implement or run a grid, nominate a winning cell, or treat values in the old draft as an approved parameter search. Once settled, publish the complete grid, its trial count and selection statistic before results are viewed. The historical search's best-looking cell is a discovery, not an independently validated edge; see [White's data-snooping reality check](https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00152).

For each approved cell and pair report raw **N**, target/stop/timeout/censored counts, gross R and pips, ambiguity count, year and direction splits, and the number still unresolved at selected H1 milestones. A timeout is not a target hit. Report bars-to-exit median, 75th percentile, 90th percentile and maximum, with TP-only and SL-only distributions and their own Ns. Record MFE/MAE in pips and ATR units both to simulated exit and across the full observation path; the latter is counterfactual after an earlier exit. A dual-touch H1 bar has unknown intrabar order: use stop-first for the primary bound and show target-first only as a sensitivity. No exact execution-price claim follows from OHLC alone.

Stability matters more than a precise-looking summary from a small monthly sample. Show each calendar year (2026 separately partial), leave-one-year-out results, whether one year supplies most of total R, and adjacent stop/target-cell behaviour rather than only the single maximum. A direction-permutation check should retain the same release dates, market paths and eligible N; if selecting the best grid cell, repeat the **whole selection** for each shuffle rather than assigning a p-value to the already selected winner. Record seed, strata, statistic and limitations before running. These are exploratory robustness checks, not a substitute for forward testing.

## 5. Delivery order and evidence boundary

1. **Repository and data contract:** commit this plan and README as the navigational baseline; keep raw exports and local symbol-placeholder folders out of Git. Build and version the generic H1/calendar exporter, then document exact per-file schema, broker/server identity, export date range, timestamp convention, row counts, gaps and SHA-256 hashes. Stop on unresolved timestamp or data-integrity errors.
2. **Auditable calculator:** implement a shared Python engine for the 28-pair universe, with family-specific event rules supplied as explicit configuration rather than duplicated simulators. Unit-test base/quote sign, missing forecasts/previous values, exact next-H1 entry, ATR lookahead, weekend gaps, full H240 coverage, ambiguous TP/SL touches, and calendar collisions. Do not run price outcomes until the corresponding rule and grid are frozen.
3. **Evidence, then viewer:** write versioned per-event and per-trial evidence under `Research Candidate/`; independently reconcile representative cases from raw inputs. Generate the standalone HTML only from validated evidence. Its selector may show pending families/pairs, but must never invent N or results.
4. **Candidate registration:** after inspecting the disclosed search and stability checks, write at most a small number of simple, exact demo rules. A registration card must name event IDs, pair/direction, data fields and point-in-time caveats, entry, ATR, stop/target, expiry, collision/censor policy, ambiguity assumption, full historical N and failures, hashes, protocol/code versions, and a prospective no-retuning evaluation schedule. If nothing survives, record that negative result and move to the next family rather than widening the search until something wins.

**No current registered setup and no claim of historical or future net profitability.** The user will handle costs separately; gross OHLC outcomes should remain explicitly labelled as such.
