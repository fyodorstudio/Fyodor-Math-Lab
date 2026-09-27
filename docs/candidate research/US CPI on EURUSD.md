# Candidate Research

This is the maintained, human-readable map of our current candidate and the questions we will investigate next. Detailed calculations and per-episode records live in the linked ledgers; this page does not replace them.

> **Status: exploratory baseline, not a registered setup.** No rule has been approved for demo forward testing. The pinned data end on **23 September 2026**, so 2026 is a partial year. The full 2015–2026 history has already been inspected; it is not an untouched holdout.

## Current focus: US CPI on EURUSD

We are asking whether a clear headline-and-core CPI surprise has a repeatable, tradeable EURUSD reaction. The existing trial tests one specific rule; it does not claim to have found the best rule.

| Baseline rule | Fixed choice |
| --- | --- |
| Release | US headline CPI m/m **and** core CPI m/m at the same timestamp |
| Direction | Both actuals above forecasts: short EURUSD. Both below: long EURUSD. Mixed or zero surprise: no trade. |
| Collision treatment | Exclude timestamps shared with Retail Sales; other same-time releases are recorded, not universally excluded. |
| Entry | Open of the exact next H1 candle |
| Stop / target | 1.0 × pre-release H1 ATR(14) stop; 1.5 × ATR(14) target |
| Exit | Stop or target first; otherwise close at H24. If both are touched within one H1 bar, count the stop first. |

The signal is **A − F** (actual minus forecast), not **A − P** (actual minus previous). Here, A − F measures the announcement surprise; A − P describes the change from the previous reported reading. Neither should be silently substituted for the other.

### What the pinned data currently show

| Accounting | Episodes |
| --- | ---: |
| All US-inflation-family episodes | 277 |
| Core PCE-only, without the CPI pair | 138 |
| CPI timestamps shared with Retail Sales | 12 |
| Remaining CPI episodes missing a required actual or forecast | 26 |
| Complete, unshared CPI episodes | 101 |
| Headline and core both above forecast | 18 |
| Headline and core both below forecast | 18 |
| Mixed or zero surprise | 65 |

The equal **18 / 18** split is an observed count, not a balancing rule. It is not evidence by itself of a profitable or suspicious pattern.

| Historical trial result | Conservative baseline |
| --- | ---: |
| Candidate trades | 36: 18 short, 18 long |
| Target first / stop first | 16 / 20 |
| Win rate | 44.4% |
| Total gross return | +4.00 R |
| H24 timeouts | 0 |
| Latest stop/target exit | H18 |

These are exploratory, in-sample, OHLC-based results. Two trades touched both stop and target within one H1 candle; the baseline assigns them a stop. Gross results do not establish a forward-tested edge.

The numerical source of truth is the [simulation report](../../TABLE%20VIEWER/cpi_setup/cpi_simulation_report.md), [277-episode decision ledger](../../TABLE%20VIEWER/cpi_setup/cpi_decision_ledger.csv), and [trade ledger](../../TABLE%20VIEWER/cpi_setup/cpi_trade_ledger.csv). Preserve this baseline unchanged when evaluating new variants.

## Separate exploratory variant: A−P momentum, H60

This post-hoc trial preserves the CPI pairing, EURUSD, Retail Sales collision exclusion, exact next-H1 entry, pre-release ATR(14), 1.0 × ATR stop, 1.5 × ATR target, and conservative stop-first intrabar rule. Its signal is **actual minus exported previous** for both headline and core; both positive means short EURUSD, both negative means long, and mixed/equal/missing means no trade. Forecast is context, not an eligibility requirement. `revised_previous` is diagnostic only; its historical point-in-time availability is unproven. See the [MQL5 calendar structure reference](https://www.mql5.com/en/docs/constants/structures/mqlcalendar).

| A−P/H60 result from pinned 2015–September 2026 data | Conservative trial |
| --- | ---: |
| Inflation-family episodes / eligible unshared CPI episodes | 277 / 127 |
| Directional trades: short / long | 55: 26 / 29 |
| Target first / stop first | 23 / 32 |
| Win rate | 41.8% |
| Total gross return | +2.50 R; +40.9 pips |
| Same-H1-bar stop-and-target ambiguity | 4 trades, counted as stops |
| H60 timeouts / latest stop-or-target exit | 0 / H23 |

The trial inspected historical prices and several target multiples **before** its protocol was written. The +2.50 R margin is thin: one target becoming a stop removes 2.50 R. The 8 trades coinciding with Initial Jobless Claims contribute +4.50 R; the remaining 47 **without Initial Jobless Claims** contribute −2.00 R, but they are not solitary CPI releases. This subgroup contrast was discovered after viewing outcomes and is not an approved filter. No trade reached H24, so lengthening this particular stop/target rule from H24 to H60 would not have changed its recorded exits.

The [A−P trial protocol](../../evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/protocol.md), [277-episode decision ledger](../../evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/cpi_momentum_decision_ledger.csv), [55-trade ledger](../../evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/cpi_momentum_trade_ledger.csv), and [simulation report](../../evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/cpi_momentum_simulation_report.md) are separate from the byte-preserved A−F baseline. These historical gross figures are for manual audit, **not** a registered setup or independently validated profit claim.

## Next investigations — separate from the baseline

| Question | What we know now | What to examine next |
| --- | --- | --- |
| **Retail Sales collision** | Of the 12 excluded shared timestamps, four lack a required forecast, seven have mixed/zero CPI surprises, and **one** has both CPI surprises above forecast. Removing only the collision filter would therefore add **one eligible signal**, not 12. Its trade outcome has not been evaluated here. | Display all 12 as a separate co-release cohort, including the Retail Sales values and whether their surprise agrees or conflicts with CPI. Audit that one additional candidate without folding it into the 36-trade baseline. |
| **A versus P** | The original A−F rule gave 36 trades and +4.00 gross R; the separate A−P/H60 rule gave 55 trades and +2.50 gross R. Neither is independently validated, and they select different episodes. | Inspect where A−F and A−P agree or conflict, including both headline and core and any same-time releases. Any combined rule is a new named trial, not a retrofit. |
| **H60 horizon** | The Event Table shows H1–H60 displacement. Baseline trades exited by H18; all 55 A−P trades exited by H23. | Use H1–H60 paths to study longer behavior, but changing the expiry alone cannot alter the current stop/target results. Any new entry or exit rule needs its own trial. |

Keep cohort sizes, individual episodes, and gross outcomes visible. Do not promote whichever subset looks best after seeing its returns into the original baseline. If a new variant looks promising, name and specify it before any subsequent prospective demo evaluation.

## Viewer boundary

The [research viewer](../../TABLE%20VIEWER/table_viewer.html) is a **generated, self-contained HTML artifact** so it remains fast and opens by double-click. Its ~1,600 lines and ~6.8 MB are mostly the result of embedding data, styles, and scripts—not a requirement to maintain one giant source file. Maintain the smaller sources in `TABLE VIEWER/generator/` and regenerate the HTML; do not hand-edit the generated output. If future data makes the viewer sluggish, measure load/render time first and then consider smaller embedded payloads or on-demand data loading. Neither a framework rewrite nor a local server is required by the current three investigations.
