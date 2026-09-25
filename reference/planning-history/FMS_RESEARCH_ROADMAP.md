# Historical Snapshot: FMS Research Roadmap & Decision Record (Legacy GEMINI Archive)

> [!CAUTION]
> **HISTORICAL ARCHIVE SNAPSHOT (PRESERVED FOR AUDIT REFERENCE ONLY)**:
> This document is an immutable historical snapshot copied from the legacy repository (GEMINI/docs/FMS_RESEARCH_ROADMAP.md, dated 2026-09-24).
> It reflects an earlier planning phase when German Ifo was being considered as a pilot prior to its empirical failure ( = 0.9575$, State 3: No Convincing Evidence).
> Paths, statuses, and trial states described herein are historical artifacts, NOT current policy or instructions to revive old code.
> For the current active research sequence, see [docs/RESEARCH_ROADMAP.md](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RESEARCH_ROADMAP.md).

---

# FMS research roadmap and decision record

Status: planning document, 2026-09-24. It is **not** a frozen setup, a trading recommendation, or authorization to open the 2023+ Phase 1 confirmation outcomes. The goal is a defensible, versioned candidate for **demo-account forward testing** in the separate `C:\dev\NO-AI` `canvas` terminal. Historical profitability, let alone a living from trading, has not been established.

## Where we stand

1. The v3.1 MT5 export `tools/mt5/FyodorResearchExport_v3_20260923_234930_server` is the pinned input. The earlier `233418` export is malformed and must not be used; neither export should be casually moved or deleted. See [the quant audit](CODEX_QUANT_AUDIT.md) and [the Phase 1 protocol](../lab/research/PHASE1_PROTOCOL.md).
2. Phase 1 explored four USD release series on EURUSD/USDJPY before 2023. It found no convincing delayed directional H1 signal in that **particular** test; this is not a universal null result. Its 2023+ outcomes remain sealed under that protocol. See [the exploration report](../lab/research/PHASE1_EXPLORATION.md).
3. The FMS [eligibility inventory](../lab/research/FMS_ELIGIBILITY_INVENTORY.md) is the completed first milestone: pre-2023, timestamp-only, no OHLC prices or returns read. It identifies 82,813 calendar rows, 30,015 timestamp packages, 51 pairs, and H1-derived H4 *coverage proxies*. Nineteen pairs span 2015–2022; 17 have truncated historical coverage; 15 have no pre-2023 H1 bars. These are coverage facts, **not** profitable-trade counts.
4. Package and pair observations are correlated. A simultaneous release package is one macro episode even if several series or FX pairs are represented. Of 30,015 packages, 2,501 have same-time cross-currency collisions. Complete inputs and a clean pair path must be evaluated jointly, not multiplied from marginal totals.
5. Later releases are normal, not exceptional. In the inventory, essentially every clean EURUSD 6-H4 path has a later EUR/USD calendar release; multi-day paths contain many. Thus a long-horizon predictive setup may be testable, but its whole return cannot be causally credited to the initiating announcement.
6. The [candidate-selection charter](FMS_CANDIDATE_SELECTION_CHARTER.md) is complete. German Ifo Business Climate + Expectations on EURUSD is the single current pilot; its pre-outcome protocol is being frozen. No Ifo candidate price outcomes or 2023+ confirmation outcomes have been opened for this pilot. The [contingency queue](../research%20note.md#if-the-german-ifo-pilot-fails-a-bounded-investigation-queue) records *possible new questions* if Ifo fails, not additional authorized trials.

## The sequence

```text
Pinned export + audit trail
          |
          v
[1] Timestamp-only episode/pair eligibility inventory     COMPLETE
          |
          v
[2] Candidate-selection charter, no price outcomes         COMPLETE
    Few exact packages/series + pair + economic rationale
    Consider first/second-day AND longer holds; count trials
          |
          v
[3] Freeze Ifo pilot analysis plan                          IN PROGRESS
    Signal availability, entry, exits, costs, missing paths,
    calendar collisions, competing releases, null comparator
          |
          v
[4] Pre-2023 historical exploration on prices
    No credible edge -> archive with full negative result
    Plausible edge -> independent validation
          |
          v
[5] Validate net of costs, uncertainty, and selection
    Failure -> archive; survival -> version and register
          |
          v
[6] Separate canvas integration + prospective demo ledger
    Immutable first-seen inputs, no-trades, decisions, fills
          |
          v
[7] Review a substantial forward record before live risk
```

Passing one gate does not imply passing the next. There is no promised timeline, number of candidate trials, or guaranteed setup. A failed thesis stays recorded rather than being silently optimized into a new winner.

## Candidate-selection charter: completed planning basis

Use only pre-2023 inventory fields and independently stated economics to propose **at most a few** candidate *questions*, not winning recipes. Rank data suitability and feasibility, **not returns**. For each candidate: exact MT5 series identities and simultaneous package rule; country/currency and pair; release orientation and how conflicting co-releases are handled; calendar-input completeness on the same eligible episode; independent package count, year distribution, and joint pair coverage for candidate horizons; known historical-vintage and broker-clock limitations; overlap with later releases; rationale for why a delayed continuation, reversal, or volatility effect could persist. Identify which choices were influenced by earlier FMS/Phase 1 inspection.

The owner's holding horizon is **not fixed to 42–60 H4 bars**. Include an explicitly defined first/second-trading-day window alongside longer horizons **only if justified before reading outcomes**. Do not confuse 42–60 H4 bars (roughly 7–10 trading days) with 42–60 hours. Avoid treating 6, 12, 30, 42, and 60 H4 as five free shots to select the best curve; choose a primary horizon or a tightly controlled comparison before testing. Release-time immediate moves and candle-close delayed moves are different hypotheses. A first/second-day setup must say exactly when information is available and when an executable entry first occurs.

If exact candidate packages are too sparse, the charter should say so and propose a principled family-level definition *before* seeing returns. Do not pool unlike countries, revisions, or announcement stages merely to enlarge N. Candidate selection alone does not authorize price-based discovery, opening confirmation outcomes, or code implementation.

## Gates that the later frozen protocol must resolve

- **Point-in-time information:** the retrospective MT5 calendar does not prove historical first-seen Actual/Forecast/Previous/revisions or broker DST alignment. Sensitivity analysis may bound historical claims; prospective append-only capture is needed for first-seen proof.
- **Outcome and execution:** H1-derived H4 coverage is not native H4 OHLC or a fill. Validate bar aggregation/alignment and use an explicit Bid/Ask spread, slippage, swap, weekend-gap, and same-bar stop/target ambiguity policy. Acquire targeted M1/tick evidence only if a candidate's execution claim requires it. [MT5 distinguishes generated OHLC ticks from real ticks](https://www.metatrader5.com/en/terminal/help/algotrading/tick_generation).
- **Statistical independence:** one package may generate several candidate pair outcomes; adjacent multi-day trades can overlap. Show episode and calendar-time dependence, year-by-year stability, uncertainty, all excluded cases, and the complete trial ledger. Multiple tried recipes require a selection penalty; a conventional unadjusted p-value is not enough. [Backtest-overfitting research](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253).
- **Comparison:** choose a realistic matched non-release or no-signal baseline before outcomes, not a zero-return straw man. Distinguish predictive profitability from causal attribution to one announcement. FX can react rapidly to macro news, so a delayed edge is an empirical question, not a given. [Federal Reserve event-study evidence](https://www.federalreserve.gov/pubs/ifdp/2004/823/ifdp823.htm).
- **Holdout honesty:** Phase 1's 2023+ partition is sealed for that study, but prior FMS work and human inspection may have contaminated independent validation for related families. Do not call reused history an untouched holdout. A new study needs its own frozen protocol and explicit holdout-use decision. If none is credible, rely more heavily on prospective demo observation.
- **Registration:** only a reviewed recipe with fixed inputs, direction, entry, risk/exit rules, costs, activation boundary, and version/hash may be called a *registered demo candidate*. Registration is not proof of positive expectancy. Frontend integration is a separate reviewed step; this lab must not modify the canvas branch implicitly.

## Repository boundaries

- `raw_data/`: legacy read-only fallback/reference, not the pinned v3.1 source.
- `tools/mt5/FyodorResearchExporterV3.mq5`: exporter source; `*.ex5`: compiled artifact. The two `FyodorResearchExport_v3_*` directories are ignored, large source snapshots. The valid `234930` snapshot is referenced by code and historical protocols; leave both snapshot paths untouched until a migration is explicitly planned and verified.
- `lab/research/`: generated evidence and frozen Phase 1 artifacts. The ~805 MB episode JSONL is ignored; do not regenerate, move, or delete it for documentation tidiness.
- `docs/DEPRECATED/`: quarantined notes about old FMS v1. They are historical leads, not instructions or validated present-day setups. Do not open or import the old trading-terminal repository.
- `C:\dev\NO-AI` `canvas`: functioning separate frontend/bridge; no research code is to be integrated there before a reviewed candidate passes its gates.
