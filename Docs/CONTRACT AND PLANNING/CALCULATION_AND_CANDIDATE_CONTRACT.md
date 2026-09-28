# Calculation and Research Candidate Contract

**Status: draft implementation contract v0.2 for Director review, not a frozen trading strategy.** It proposes how new evidence must be produced. The exploratory stop/target grid and three expiry horizons are specified below; signal directions and family-specific inclusion rules remain open until a versioned protocol is approved. No agent should run candidate price outcomes merely because this document exists. Old-repository findings are not evidence under this contract.

| Defined here for review | Still requires a family protocol or Director decision |
| --- | --- |
| H1 first-open-after-release entry; H1 through H240 indexing; pre-release ATR(14) formula; exploratory stop/target grid and three horizons; pip and gross-R arithmetic; OHLC ambiguity; MFE/MAE bounds; ledgers and tests | Which release series and pairs to try; signal-to-currency direction; bundle/collision policy; entry-delay and gap caps; candidate selection; future-event censor set |

## Authority and versions

This document governs the calculator and evidence. The [expansion plan](MAJOR%20EXPANSION%20PLAN.MD) explains the research programme; a family protocol supplies decisions left open here. A conflict requires an explicit contract amendment before calculation. Never silently alter a formula after viewing results.

Every run identifies contract version, family-protocol version, code commit/hash, exporter version, broker/server, input hashes, timestamp convention, complete parameters and run time. Corrections create a new package, preserving the old one. Exploration, candidate registration and prospective demo observations are separate states.

## Inputs and atomic observations

- The V4 snapshot exported H1 candles for all 28 FX pairs in the root README and calendar releases for AUD, CAD, CHF, EUR, GBP, JPY, NZD and USD. **Only 19 pairs are active for first-pass research.** Globally exclude `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY` because their files start only on 25–26 November 2025. This applies even to their available 2026 bars; do not quietly switch to a shorter sample for them. The Director confirmed an MT5/broker history bottleneck and chose not to repair it with another broker. Reinstatement requires a newly versioned scope decision. The primary analysis of a currency X uses only **active** pairs containing X. US CPI and US NFP each have exactly seven relevant active pairs: `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`. Other instruments or spillovers need separate protocols.
- Full-year releases: 2015-01-01 through 2025-12-31. Show 2026-01-01 through 2026-08-31 separately as **partial**. Candles must extend beyond the release cutoff to resolve H240. These historically inspected years are not an untouched holdout.
- Calendar row minimum: stable event/value IDs, original release timestamp, currency, indicator, units and scale, actual A, forecast F, exported previous P, revised previous if supplied, and source-row reference. Missing is not zero. P and revised previous are distinct; a historical snapshot does not establish what revision was known at release time.
- H1 row minimum: broker symbol, original bar-open timestamp, open/high/low/close and source-row reference. Prices must be finite and satisfy `low <= min(open,close) <= max(open,close) <= high`. Reject duplicate/out-of-order bars and incomplete current bars.
- The input manifest records per-file SHA-256, schema, row count, first/last time, gaps, missingness, exporter version and errors. Raw inputs remain immutable under ignored `raw_data/`; never synthesize a value or candle.

Calendar and candle times must share one **documented trade-server clock**, with original strings and normalized comparable values preserved. Do not interpret a server-clock string as UTC or use workstation timezone implicitly. Broker historical offset/DST changes require evidence, not a guessed constant. MT5's calendar APIs use trade-server time, and `CopyRates` timestamps are bar opens ([calendar documentation](https://www.mql5.com/en/docs/calendar), [CopyRates documentation](https://www.mql5.com/en/docs/series/copyrates)). Unresolved clock mapping stops the calculation.

The atomic observation is `(same-time release bundle, pair)`, not one indicator row. Preserve every same-timestamp constituent and its A/F/P completeness, even when a candidate uses only one. A family protocol names its anchor IDs and collision treatment. Use stable observation IDs derived from dataset version, bundle IDs/time and symbol. Correlated pair observations from one bundle are not independent macro releases.

## Price-blind eligibility and N

Before reading outcome prices, write an eligibility ledger containing every considered active bundle/pair, input completeness, timestamp, pair relevance, entry candidate, ATR availability, coverage and all exclusion flags. Keep the nine globally excluded symbols in a separate source-inventory/exclusion list with reason `excluded_truncated_history`; **never** include their episodes in the candidate or trade denominator. For active pairs, one primary exclusion reason is required. Distinguish missing A/F/P, incompatible units, duplicate calendar records, collision, unmapped time, insufficient ATR warmup, unexplained candle gap and insufficient horizon. The 437-hour EURCHF gap from 31 December 2014 to 19 January 2015 is a known internal hole, not proof that the other 19 histories are fully gap-free. Exclusion is neither loss nor timeout nor zero return.

Publish the count waterfall: calendar rows, unique bundles, signal-complete bundles, relevant pair-bundles, entry-eligible observations and priced observations for each horizon. The **common-complete cohort** has valid paths through H240 and is used for like-for-like H60/H120/H240 comparisons. If the family protocol has not yet specified entry-delay and gap limits, produce only a provisional coverage ledger, not a final trade N.

## H1 entry, ATR and horizons

For release time `t`, entry is the `open` price `E` of the earliest **complete** H1 candle with `bar_open > t`. Record entry time and delay in seconds, including market closures. Entry is not a fill at release. The protocol must set any maximum allowed delay before outcome inspection.

The entry candle is path bar **H1**. Scan barriers starting in H1. H60/H120/H240 mean 60/120/240 observed H1 market bars starting with that entry candle; an unhit trade exits at the **close** of bar Hmax. Weekends create clock delay but not numbered bars. Unexplained missing weekday/session bars must be flagged and handled by a predeclared broker-session/gap policy, never silently skipped. A horizon without a full valid path is missing, not a timeout.

### Approved exploratory expiry horizons

| Expiry | Approximate intuition | Exact calculation |
| --- | --- | --- |
| **H60** | About 2.5 days of continuous H1 trading, or half a five-day trading week | Expire at the close of the 60th eligible H1 market bar, counting the entry bar as H1. |
| **H120** | About five trading days, or one trading week | Expire at the close of the 120th eligible H1 market bar. |
| **H240** | About ten trading days, or two trading weeks | Expire at the close of the 240th eligible H1 market bar. |

The exact bar counts govern. These are **not** promises of 2.5, 5 or 10 elapsed calendar days; weekends, holidays and session closures can extend elapsed time. The Director's phrase “24 H1 for two weeks” is interpreted here as **240 H1**, since 24 H1 bars represent about one day of trading, not two weeks. If that interpretation is wrong, amend this contract before calculation.

The reference volatility is **H1 ATR(14), Wilder smoothing, entirely pre-release**. Select the last 250 true ranges from fully completed H1 bars whose close (`bar_open + 1 hour`) is **strictly earlier** than `t`; this requires the preceding close and thus at least 251 usable bars. For each bar, `TR = max(high-low, abs(high-previous_close), abs(low-previous_close))`. Seed ATR with the arithmetic mean of the first 14 TR values; thereafter `ATR_new = (13*ATR_old + TR)/14`. Use the final finite positive value. Record the warmup bar IDs, last eligible bar and ATR in price units. No release bar, entry bar or future bar may affect ATR. Missing warmup excludes ATR-based trials, though a clearly labelled price-only descriptive row may remain. This finite warmup keeps ATR stable when older exports are added; it is an explicit research definition, not a claim of bit-for-bit equality with MT5 `iATR`.

For the approved FX universe, one pip is `0.01` when JPY is the **quote** currency, otherwise `0.0001`. Preserve unrounded raw prices/ATR for calculations. Symbol suffixes and broker point size do not redefine this pip; exceptions require an explicit tested mapping.

### Approved exploratory ATR stop/target grid

Use stop widths `s ∈ {1, 2, 3, 4}` ATR. **Independently**, for every stop width, use target widths `p ∈ {1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00}` ATR. Thus `SL distance = s × ATR` and `TP distance = p × ATR`. The notation **s:p is absolute ATR multiples, not a target-to-stop ratio**: `1:4` means SL=1 ATR and TP=4 ATR, while `4:4` means SL=4 ATR and TP=4 ATR. A 4:4 cell **never** has a 16-ATR target. For each cell, calculate its actual reward-to-risk number as `p/s` (4:4 gives 1.00; 2:1 gives 0.50).

This is **4 × 13 = 52** stop/target cells and **52 × 3 = 156** cell–expiry combinations per signal/pair cohort, before any direction, context, collision, pair or family variants. Enumerate all approved cells in the protocol and report all results, including failures; do not quietly narrow the grid after inspection. The grid is for systematic *exploration*, not a claim that its best cell is independently validated. No setup is registered merely because one of 156 combinations looks good.

## Candidate-rule vocabulary

The engine accepts typed, versioned configurations, not arbitrary code hidden inside a candidate row. Before any price trial, a family protocol must enumerate the complete finite candidate set and selection statistic. Each rule specifies:

| Field | Required meaning |
| --- | --- |
| Event identity | Exact family, anchor series IDs, accepted bundle members and collision policy. |
| Signal | Required A/F/P/revised-P fields, units, sign/zero/missing handling and any context fields available by entry. |
| Currency prediction | `+1`, `-1` or abstain for event-currency strength; a positive release surprise does **not** automatically imply appreciation. |
| Pair prediction | Same direction if event currency is base, inverted if it is quote. |
| Entry/ATR | Entry-delay cap, fixed H1 entry and pre-release ATR definitions above. |
| Exit | Explicit stop distance, target interpretation/distance, Hmax and collision/censor policy. |

Permitted first comparisons are `S = A-F` (surprise) and `M = A-P` (reported-previous momentum) **within the same indicator and compatible units**, with negative/zero/positive/missing states. CPI headline/core agreement and NFP payroll/unemployment/wages coherence are separate family-specific definitions; do not mix unlike units or silently substitute revised P. A context variable needs a predeclared source, availability time, bins and missing policy. Unrecorded discretionary chart judgement is not a candidate condition.

If a family protocol elects to examine joint S/M signs, the four nonzero cells are `(+,+)`, `(+,-)`, `(-,+)`, and `(-,-)`; zero and missing values are separate named strata, never forced into a quadrant. These are **descriptive subsets**, not four automatically profitable rules. Each subset needs an explicit predicted direction or abstention before its price outcome is inspected. The engine may support a subset without that subset being approved for the current search.

The **grid geometry and absolute-ATR interpretation above are specified**, but a family trial is still not authorized until its signal, direction mapping, entry-delay cap, bundle/collision policy, gap policy, full candidate count and selection statistic are frozen in its own protocol. Every added pair, quadrant, coherence stratum or context filter is another disclosed comparison. A larger stop does not automatically imply a better or safer setup.

## OHLC outcome semantics

For an approved rule, let `D=+1` for long pair and `D=-1` for short pair. Let `B=stop_ATR_multiplier*ATR` and `T=target_price_distance` from the frozen protocol. Stop=`E-D*B`; target=`E+D*T`. For long: stop touched if `low<=stop`, target if `high>=target`. For short: stop touched if `high>=stop`, target if `low<=target`. The first touched level resolves the trade. If both touch within one H1 candle, order is unknown: use **stop-first as the primary bound**, target-first as a separately labelled sensitivity, and record `dual_touch=true`.

Flag an opening gap beyond either barrier. The primary **threshold-touch proxy** credits nominal stop/target levels, not actual executable fills; retain the gap-open price for sensitivity. An untouched trade exits at Hmax close as `TIMEOUT`. An approved future-event isolation analysis exits at the last fully completed bar strictly before the next **predeclared** contaminating event, or is unresolved if none exists after entry. Its outcome is `CENSORED`, not TP/SL/timeout. Initial same-time bundle members are not future censors.

Gross signed pips=`D*(exit_proxy-E)/pip_size`; gross R=`D*(exit_proxy-E)/B`. Nominal stop is `-1R`, target is `T/B R`, timeout can have either sign. Counts of TP, SL, timeout, censored and unresolved must reconcile to eligible N. These are OHLC/barrier **gross proxies**, not net profit or a reliable broker-fill simulation; spread, slippage and financing remain outside this user's chosen calculation scope.

## Paths, timing and excursions

Keep an event-level H1..H240 path with bar OHLC, raw-pair pips and event-currency-aligned pips. At each horizon show N, median, p75, p90 and positive-move count/N; missing values are excluded from a statistic with the used denominator shown. A zero move is neither positive nor missing. The path is descriptive and does not imply one could enter at each past bar.

For long, MFE uses `high-E` and MAE uses `E-low`; for short, MFE uses `E-low` and MAE uses `high-E`, each floored at zero. Record pips and ATR units for the **full observed horizon** (counterfactual after an earlier exit) separately from the **through-exit** path. For a barrier exit, the exit bar's opposite extreme may have occurred *after* the barrier: exact pre-exit MFE/MAE is unknown. Store a guaranteed lower bound from prior complete bars plus the touched threshold, and an OHLC upper bound; never label the entire exit-bar range as exact pre-exit excursion. Timeout at bar close may use the entire bar.

Bars-to-exit starts at H1=1. Report median, p75, p90, maximum and elapsed clock time for all exits, TP-only and SL-only, each with its own N. Even-N median averages the middle two; p75/p90 use nearest-rank `ceil(p*N)`. Empty distributions show missing, not zero.

## Evidence package, viewer and registration

Each immutable package under `Research Candidate/<family>/<protocol_id>/<run_id>/` contains a machine-readable `manifest`, price-blind `event_eligibility` ledger, event/pair/rule/horizon `trial_ledger`, complete `summary`, documented schema, and `audit/` samples independently recalculated from raw source rows. Ledgers include IDs, timestamps, source references, input completeness, signals, entry/ATR/barriers, path/exit, ambiguity, pips/R, exclusions and data version. Summary includes all attempted candidates and failed cells, yearly and direction Ns, 2026 partial separately, leave-one-year-out results, adjacent-cell stability and common-complete cohort.

If a direction permutation is used, preserve release dates, market paths and eligible observations; predeclare seed, shuffling strata and statistic. When judging a selected winner, repeat the **entire candidate-selection process** in each shuffle. Small, dependent samples and selected results cannot be called proven profitability on the strength of one p-value.

`HTML Viewer/table_viewer.html` displays only validated package evidence; it does not recalculate ATR, eligibility or trade outcomes and contains no hand-entered winning numbers. Pending studies display **PENDING**. A possible demo-registration card states exact event IDs, fields and point-in-time limits, pair/direction, all parameters, historical N and failures, ambiguity/censor policy, stability/selection record, source/code hashes and a prospective **no-retuning** schedule. No result is registered merely for looking good historically.

## Minimum acceptance tests

Synthetic cases must cover: explicit nine-pair global rejection; release exactly on an H1 open and inside a bar; weekend entry; base/quote sign inversion; zero versus missing A/F/P; revised P separation; same-time release bundles; pre-release ATR despite extreme release candle; insufficient warmup; duplicate/out-of-order/missing candles; H60/H120/H240 boundaries; stop-only, target-only, timeout, opening gap, dual touch under both bounds, censor before/after entry; short gross R; MFE/MAE exit-bar bounds; even-N median and nearest-rank quantiles; and count reconciliation. Then independently hand-recompute representative real rows from hashed inputs. Passing tests alone does not validate broker data or establish an edge.

---

## Amendment 2026-09-28: Exploratory Research Exemption (selection_policy = NONE)

For descriptive historical exploration passes (specifically `CPI_EXPLORATION_V1` and `NFP_EXPLORATION_V1`):
1. **Explicit Setting:** `selection_policy = NONE`.
2. **Descriptive Scope:** All 52 grid cells across the 3 horizons (156 cell-horizon evaluations) are fully reported across all active USD pairs and signals, including all losing, stagnant, and empty cells.
3. **Zero Winner Selection or Registration:** Zero candidate ranking, zero optimization metric, and zero winner selection or setup registration are permitted under this exploration mode.
4. **Preservation of Registration Standards:** Any future setup registration or live demo deployment remains strictly bound by the formal multi-year candidate selection criteria and out-of-sample validation rules specified in this contract.
