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

## Next candidate: A−P momentum, H60 (specified, not calculated)

This is a separate exploratory pass, not a correction to the A−F baseline above. Keep the same US headline and core CPI m/m release pairing, EURUSD, Retail Sales collision exclusion, exact next-H1 entry, pre-release ATR(14), 1.0 × ATR stop, 1.5 × ATR target, and conservative stop-first intrabar rule. Change only the signal and expiry:

- For **both** headline and core, `actual > previous` means short EURUSD; `actual < previous` means long EURUSD. Mixed, equal, or missing values produce no signal. Forecast is recorded for context but is not required for eligibility.
- Expire at the close of the 60th **observed H1 candle** only if neither stop nor target has been hit. Require the exact entry candle and enough forward bars; audit missing-data gaps separately from normal market closures instead of hiding either in the bar count.
- Use the exported `previous` field for the primary A−P signal. Retain `revised_previous` in the audit ledger and report its presence and any sign disagreement; do not silently substitute it, and do not discard an episode merely because it exists. Check historical point-in-time availability before describing the result as live-replicable. MT5 exposes `previous`, `revised_previous`, and the release's own `revision` as distinct fields; they are not interchangeable. See the [MQL5 calendar structure reference](https://www.mql5.com/en/docs/constants/structures/mqlcalendar).

Recount the entire CPI episode funnel and write this variant's own ledgers and report. The 36 A−F trades and their H18 latest exit do **not** imply the A−P candidate has the same N or that H60 is irrelevant to it. No A−P H60 price result exists yet.

## Next investigations — separate from the baseline

| Question | What we know now | What to examine next |
| --- | --- | --- |
| **Retail Sales collision** | Of the 12 excluded shared timestamps, four lack a required forecast, seven have mixed/zero CPI surprises, and **one** has both CPI surprises above forecast. Removing only the collision filter would therefore add **one eligible signal**, not 12. Its trade outcome has not been evaluated here. | Display all 12 as a separate co-release cohort, including the Retail Sales values and whether their surprise agrees or conflicts with CPI. Audit that one additional candidate without folding it into the 36-trade baseline. |
| **A versus P** | The current entry rule does not use previous readings. The raw calendar has a `previous` field, but its availability and point-in-time meaning must be checked before treating it as live-usable context. | For headline and core separately, show A − P alongside A − F, missingness, and direction agreement. First describe the existing 36 trades and non-trades; any A − P gate becomes a **new, explicitly named variant**, not a retrofit. |
| **H60 horizon** | The Event Table can show H1–H60 displacement. All 36 baseline trades already hit stop or target by H18, so extending **only** the H24 expiry to H60 would change none of their outcomes. | Inspect the H1–H60 paths as price behavior. A 60-bar stop/target simulation matters only if the entry, stop, target, or exit rule changes; report that as a separate variant with full path coverage checks. |

Keep cohort sizes, individual episodes, and gross outcomes visible. Do not promote whichever subset looks best after seeing its returns into the original baseline. If a new variant looks promising, name and specify it before any subsequent prospective demo evaluation.

## Viewer boundary

The [research viewer](../../TABLE%20VIEWER/table_viewer.html) is a **generated, self-contained HTML artifact** so it remains fast and opens by double-click. Its ~1,600 lines and ~6.8 MB are mostly the result of embedding data, styles, and scripts—not a requirement to maintain one giant source file. Maintain the smaller sources in `TABLE VIEWER/generator/` and regenerate the HTML; do not hand-edit the generated output. If future data makes the viewer sluggish, measure load/render time first and then consider smaller embedded payloads or on-demand data loading. Neither a framework rewrite nor a local server is required by the current three investigations.
