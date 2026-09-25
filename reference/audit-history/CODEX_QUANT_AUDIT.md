# Adversarial Quantitative Audit

Audit date: 2026-09-24  
Audited commit: `a83a39f4180d698fb285368daebea5ea0c76e555`  
Selected calendar SHA-256: `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e`  
Selected export tree SHA-256: `83eba32af0e1acd2e0c65ee983c11023591f55fd140ee4cd4fe2a0ec39832ffe`  
Selected export: `FyodorResearchExport_v3_20260923_234930_server` (`fyodor-mt5-research-export/3.1.0`)  
Machine evidence: [`lab/audit_exports/codex_quant_audit.json`](../lab/audit_exports/codex_quant_audit.json)

Reproduction command: `cd lab && npm run audit:quant`

## 1. Executive summary

### v3.1 migration status (supersedes the original provenance caveats below)

The validated v3.1 export resolves the previous exporter, manifest, broker-identity, scaling-metadata, and PMI-stage identification blockers. It identifies Elev8 Markets Ltd. / Elev8-Demo2; preserves MetaQuotes period, revision, unit, multiplier, digits, event metadata, source URL, and raw scaled integers; and explicitly records trade-server time with a +03:00 snapshot offset. The lab now selects only a complete `fyodor-mt5-research-export/3.1.0` dataset and groups research populations by `currency:country:event_id:revision`.

Remaining limitations are narrower: the manifest cannot reconstruct historical broker timezone/DST rules, cannot prove that provider fields are immutable first-vintage observations, and does not turn descriptive event studies into a costed strategy backtest. The large export directory is not currently Git-tracked. Any older statement below saying the exporter or revision metadata is absent describes the received legacy dataset and is superseded by this migration status.

The laboratory was not scientifically trustworthy as received for unrestricted “exact event” research. A high-severity identity defect pooled different countries under identical EUR PMI display names. Several additional defects affected filtered matrices, minimum-history enforcement for exact-zero observations, weekend diagnostics, timestamp labels, and audit exports. Those implementation defects are repaired and covered by tests.

The repaired core engine is mathematically trustworthy for descriptive event-response calculations within a selected MetaQuotes `event_id + revision` series when the researcher accepts the broker snapshot as given. Walk-forward mode now satisfies the narrow claim that percentile thresholds, ranks, and ties use only observations with `timestamp < current.timestamp`, including same-timestamp batch isolation and minimum-history suppression.

It is not yet trustworthy for serious strategy or backtest conclusions. The remaining constraints are provider-vintage uncertainty, historical timezone policy, candle gaps, simultaneous-release attribution, multiple testing, the lack of an untouched confirmation sample, and the absence of a cost/execution model. These are research-design and data-vintage problems, not code-style concerns.

Confidence labels used below:

- **VERIFIED FACT**: directly demonstrated from source, raw rows, deterministic recomputation, or primary documentation.
- **LIKELY**: best explanation supported by multiple observations, but required provenance is absent.
- **POSSIBLE**: plausible failure mode without sufficient evidence.
- **UNKNOWN**: repository evidence cannot resolve the question.

## 2. Critical findings

No repository-wide **CRITICAL** defect remains after remediation. The PMI identity defect was **HIGH** for affected populations, not proof that every series was invalid.

## 3. High findings

### HIGH-1 — Display-name grouping contaminated EUR PMI populations — fixed at revision-series level

**VERIFIED FACT.** The old key was `currency + eventName`. For EUR `S&P Global Manufacturing PMI`, that pooled 1,127 rows across five distinct MetaQuotes event IDs:

| Country | event_id | Rows | Active months | Complete A/F/P |
|---|---:|---:|---:|---:|
| France | 250500001 | 281 | 142 | 181 |
| Germany | 276500001 | 282 | 142 | 182 |
| Italy | 380500001 | 142 | 142 | 91 |
| Spain | 724500001 | 141 | 141 | 90 |
| Eurozone | 999500001 | 281 | 142 | 219 |

The prior audit's 708-observation nonzero Surprise population was therefore not an exact Eurozone series. Queries are now keyed by `event_id`; ambiguous name-only queries fail closed. UI selectors show country code and event ID. For audited Eurozone value `118422`, the retrospective nonzero Surprise N changes from the old pooled 708 to 193, and P75 changes to 1.0.

**Legacy finding.** In the repaired legacy CSV, France, Germany, and Eurozone IDs averaged about 1.98 releases per active month and could not be separated without a heuristic.

**V3.1 RESOLUTION.** The new export preserves `period` and `revision`. For German event `276500001`, revision 1 and revision 3 each contain 140 monthly observations (plus one isolated revision-0 row); each revision series averages exactly one release per active month. The API and all UI selectors now carry the complete `eventSeriesKey`, so revision populations cannot be silently pooled. The audited Eurozone value `118422` belongs to `EUR:EU:999500001:r1`; its revised retrospective Surprise population is N=104 with P75=1.4.

### HIGH-2 — Calendar provenance and repair lineage were absent — resolved by v3.1 export

**VERIFIED FACT.** The CSV preserves `event_id`, `value_id`, timestamp, currency, country code, display name, importance, Actual, Forecast, Previous, and Revised Previous. Its schema and known IDs strongly support MetaQuotes/MT5 origin.

**VERIFIED FACT.** No exporter or repair source exists in the repository. No manifest describes what “repaired” means. The source omits `period`, `revision`, frequency, unit, multiplier, digits, source URL, and event code. MetaQuotes documents all of those fields in its calendar structures and documents raw numeric storage at a 10^6 scale plus separate event multipliers: [MQL5 calendar structures](https://www.mql5.com/en/docs/constants/structures/mqlcalendar).

**LEGACY FACT.** `raw_data/` is ignored by Git, so the original repaired file is not recoverable from the recorded commit. The selected v3.1 export is likewise kept outside Git in this workspace; its SHA-256 is recorded above and in the machine evidence.

**Consequence.** Point-in-time versus reconstructed values, multiplier handling, later revisions, and repair transformations are **UNKNOWN**. Raw values were not rewritten during this audit.

**V3.1 RESOLUTION.** `FyodorResearchExporterV3.mq5` and its compiled EX5 are present. The selected manifest reports schema/exporter 3.1.0, terminal build 6182, Elev8 Markets Ltd. / Elev8-Demo2, 123,054 calendar releases, 51 Forex symbols, 1,686,617 completed H1 bars, and zero calendar/candle query failures. The calendar stores accessor-derived decimals and the original 1e6-scaled integer fields side by side. The lab does not apply a repair transform to this source.

### HIGH-3 — Forecast provenance is unresolved

For USD CPI m/m value `229745` (broker-server timestamp `2025-08-12 15:30`), the raw row is A=0.2, F=0.6, P=0.3. Official BLS data verify Actual=0.2 and Previous=0.3: [BLS July 2025 CPI](https://www.bls.gov/news.release/archives/cpi_08122025.htm). A Reuters economist poll reported a 0.2 consensus, not 0.6: [Reuters report](https://www.investing.com/news/economy/us-inflation-rises-in-july-in-line-with-expectations-4185127).

Classification: **PERSISTENT PROVIDER FORECAST DISCREPANCY**. The direct v3.1 broker export also reports F=0.6, so the legacy repair step is not needed to explain this value. Forecasts are provider-specific, and the available snapshot does not prove what consensus was visible before release. Replacing it with a third-party value would be methodologically unjustified and was not done.

An independent official-actual cross-check passed for Core PCE value `115719`: raw Actual=0.3 matches the BEA's August 2020 core PCE price-index change: [BEA release](https://www.bea.gov/news/2020/personal-income-and-outlays-august-2020).

## 4. Medium findings

### MEDIUM-1 — Score matrices ignored active filters — fixed

`getPattern()` calculated horizon statistics from filtered observations but score matrices from all observations. Date, score, importance, simultaneous, and weekend filters could therefore produce a visually inconsistent matrix. Matrices now use `filteredObservations`. A real-data test asserts matrix H1 N equals filtered H1 N.

### MEDIUM-2 — Walk-forward exact zeros bypassed minimum history — fixed

An exact A=F or A=P observation received +1 even when prior nonzero N was below `minHistory`. The stated methodology requires all scores to be null when prior N is insufficient. Exact zeros now receive +1 only after the history requirement is met; otherwise score, threshold, and rank are null.

### MEDIUM-3 — Null thresholds silently produced magnitude 2 — fixed

The scoring utility treated a missing threshold as infinity, assigning any nonzero delta magnitude 2. It now returns null for a nonzero delta without a valid threshold.

### MEDIUM-4 — Distribution and scoring populations could differ — fixed

The distribution endpoint admitted dimension-valid A/F or A/P rows even when the scoring engine required complete A/F/P. Displayed P75 could therefore differ from the threshold used to score the same observation. Distribution tables now use the same complete-A/F/P, nonzero eligibility rule as scoring.

### MEDIUM-5 — Any candle gap was labeled a weekend — fixed

The prior code set `crossesWeekend=true` for every gap greater than one hour, including missing weekday bars. Weekend detection now checks whether the missing interval actually includes Saturday or Sunday in broker-server wall-clock coordinates. A separate `crossesNonWeekendGap` flag and warning preserve missing-candle diagnostics.

Across all 51 v3.1 FX files and 1,686,617 rows:

- duplicate timestamps: 0
- out-of-order timestamps: 0
- non-hour-aligned timestamps: 0
- invalid OHLC relationships: 0
- weekend gaps: 14,202
- non-weekend gaps: 1,288

Available bars are still counted rather than fabricated. A path crossing a non-weekend gap therefore has a longer wall-clock duration than its H-number and is now disclosed.

### MEDIUM-6 — Timestamp labels asserted UTC without evidence — fixed

MetaQuotes states that economic-calendar functions and `MqlCalendarValue.time` use trade-server time, not local time or necessarily UTC: [CalendarValueHistory documentation](https://www.mql5.com/en/docs/calendar/calendarvaluehistory). The UI and types previously labeled these values UTC.

The labels now say broker server time. V3.1 identifies Elev8 Markets Ltd. / Elev8-Demo2 and records a +03:00 offset at the export snapshot. Historical offset/DST rules remain unavailable, so no UTC conversion is applied.

### MEDIUM-7 — Audit CSV omitted required evidence — fixed

Observation CSV exports omitted event/value IDs, source file, revised previous, thresholds, reference N, tie metrics, raw pair returns, and log returns. Those fields are now exported alongside exact event-currency simple returns.

## 5. Minor findings

### LOW-1 — Rank diagnostics were rounded before storage — fixed

Strict-lower ranks and tie rates were rounded to one decimal inside the math utilities. They are now retained to eight canonical decimals; the UI may still format them for display.

### LOW-2 — Documentation contradicted the implementation — fixed

The root README described weak arithmetic sign inversion, a contaminated P0 anchor, and a non-strict percentile rank. Both READMEs now state exact quote inversion, the complete-bar P0 rule, strict-lower rank, type-7 quantiles, and timestamp uncertainty.

### LOW-3 — Pattern Explorer mode controls did not trigger recalculation — fixed

`scoringMode` and `minHistory` were omitted from the React effect dependency list. The request builder contained them, but changing the controls did not automatically issue a new request. They now propagate immediately.

## 6. Verified-correct components

The following were independently checked and are **VERIFIED CORRECT** after remediation:

- raw strings and parsed A/F/P/revised-P are preserved in observations;
- signed deltas are A−F and A−P, with separate absolute magnitudes;
- exact zero maps to +1, subject to walk-forward minimum history;
- magnitude 3 requires strictly greater than the threshold; equality remains magnitude 2;
- percentile populations exclude exact zeros;
- strict-lower rank is `count(v < x) / N × 100`;
- tie count, lower rank, upper rank, and tie rate use the same population as threshold/rank;
- quantiles use deterministic Hyndman–Fan type 7 interpolation;
- same-timestamp walk-forward observations are evaluated before any member of the batch enters history;
- base simple return is `Pt/P0−1`;
- quote simple return is `P0/Pt−1`, not the negated pair return;
- normalized log return is `Q ln(Pt/P0)`;
- H1–H42 statistics use exact event-currency simple returns;
- positive/negative direction rates use valid non-null returns and are not labeled win rates;
- P0 is the open of the first available H1 candle whose start is at or after the release timestamp;
- horizons count available bars; unavailable trailing horizons remain null;
- pair candles are indexed and binary-searched rather than rescanned per event;
- simultaneous groups use same currency and exact timestamp and now preserve other release IDs.

## 7. Raw-data provenance

Provider classification: **VERIFIED manifested MetaQuotes/MT5 broker export**. The v3.1 manifest and exporter record terminal, account company/server, schema, extraction window, completion status, query-failure counts, and source conventions.

The new calendar preserves human-scale accessor values and raw 10^6 integers together, plus event unit, multiplier, and digits. This makes the scaling operation auditable without rewriting either representation.

The parser continues to support legacy suffixes such as K/M/B. V3.1 source units are preserved and exposed, while cross-series raw deltas remain strictly isolated.

## 8. Timestamp findings

**VERIFIED FACT.** Raw calendar and H1 integers occupy the same apparent wall-clock coordinate system: a 15:30 calendar event sits inside the 15:00 candle and anchors to the 16:00 candle. Relative alignment is therefore internally coherent.

**VERIFIED BY MANIFEST.** The calendar and candles were emitted together by the same exporter and retain MT5 trade-server timestamps without UTC conversion.

**PARTIALLY RESOLVED.** The broker/server are Elev8 Markets Ltd. / Elev8-Demo2 and the snapshot server-minus-GMT offset is +10,800 seconds. The export correctly warns that this is a snapshot, not a historical DST map. External comparisons remain consistent with a +02/+03 broker clock.

No historical UTC conversion is justified until the server's historical timezone/DST rules are obtained.

## 9. Event identity findings

Primary grouping is now `currency:country_code:event_id:revision`, exposed as `eventSeriesKey`. Display names remain presentation fields.

The source also preserves event code, period, frequency, unit, multiplier, digits, and source URL. Revision is the source-declared stage discriminator; the lab does not guess human labels such as “flash” or “final.” Family classification remains descriptive and is never used as an exact-event percentile population.

Central-bank headline rate series remain econometrically incomplete because A−F does not encode statements, projected paths, press conferences, or information shocks.

## 10. Statistical methodology findings

### Quantile definition

For sorted values `v[0] ... v[N−1]` and percentile fraction `p`:

1. `i = (N−1)p`
2. `lower = floor(i)`, `upper = ceil(i)`
3. `Q(p) = v[lower] + (i−lower)(v[upper]−v[lower])`

This is Hyndman–Fan type 7, the common default in R and NumPy's linear method.

Real reconstructable example: Core PCE value `115719`, walk-forward Surprise population N=24. For P75, `i=(24−1)×0.75=17.25`; `v[17]=0.1`, `v[18]=0.2`; therefore `P75=0.1+0.25×(0.2−0.1)=0.125`. The engine and independent audit both return 0.125.

### Floating-point policy

Deltas and population values are canonicalized to eight decimal places. Epsilon is 1e−9, below the smallest retained decimal step. Threshold comparisons, rank, and ties therefore agree on values such as `0.20000000000000004` versus `0.20`.

### Researcher degrees of freedom

The UI exposes many filters and thresholds. It does not rank “best” patterns or label profitability, which is appropriate. It still enables extensive exploratory slicing, so any candidate effect must be frozen before confirmation. Current outputs have no multiple-testing adjustment and no untouched holdout designation.

## 11. FX normalization verification

USD CPI value `229745` on EURUSD is a quote-currency case:

- P0=1.16420 at broker-server 16:00
- H1 close=1.16520
- raw EURUSD return=`1.16520/1.16420−1=+0.0008589589`
- exact USD return=`1.16420/1.16520−1=−0.0008582218`
- USD log return=`−ln(1.16520/1.16420)=−0.0008585902`

USD CPI value `229744` on USDJPY is a base-currency case:

- P0=147.885
- H1 close=148.573
- exact USD return=`148.573/147.885−1=+0.0046522636`
- normalized log return=`ln(148.573/147.885)=+0.0046414753`

Independent calculations equal engine outputs at H1, H2, H4, H12, H24, and H42 for all seven real-data cases.

## 12. H1 alignment verification

For CPI value `229745`, release timestamp is broker-server 15:30. The contaminated 15:00 bar is not used as P0. P0 is the 16:00 open, 1.16420. H1 is the close of that same complete 16:00–17:00 bar; H4 is the fourth available bar close. All horizons are cumulative from the same P0.

For Eurozone PMI value `118422`, the release is exactly 12:00 and P0 is the 12:00 open, consistent with the stated boundary convention.

Friday NFP value `277623` crosses the weekend within H42 and remains included with `crossesWeekend=true`; it is not automatically discarded.

## 13. Walk-forward verification

Walk-forward scoring is grouped by exact source event ID and revision, sorted ascending, then processed in timestamp batches. Tests demonstrate both members of a synthetic same-event same-timestamp batch see prior N=20, not 20 and 21.

For CPI value `229745`:

- prior Surprise N=90, all timestamps strictly earlier;
- P75=0.4;
- strict-lower count=66, rank=73.33333333%;
- tie count=8, tie rate=8.88888889%;
- |A−F|=0.4 equals the threshold, so score is −2, not −3.

For Core CPI value `229757`, A=F and sufficient prior N=67, so Surprise score is +1 and rank is N/A. A deterministic test also verifies the same exact-zero observation becomes null when `minHistory=21` and only 20 prior nonzero observations exist.

Conclusion: **VERIFIED** for absence of future percentile leakage within the selected source-series definition. This is not a claim of full backtest safety.

## 14. Audit-artifact consistency

The legacy audit artifacts were generated from the old display-name grouping and UTC labeling. Their EUR PMI N=708 and related thresholds are invalid for an exact Eurozone revision series. They are currently absent from the working tree and were not restored by this migration.

Spot checks did not reproduce the allegation that the old Markdown and JSON disagreed on the selected CPI/PMI case fields; rather, both shared the same upstream identity error. They are superseded by [`lab/audit_exports/codex_quant_audit.json`](../lab/audit_exports/codex_quant_audit.json), which contains independent recomputation and engine comparisons against v3.1.

The machine artifact records the raw file hash, PMI before/after counts, all 51 candle integrity summaries, external cross-check classifications, and seven real observations.

## 15. Remaining uncertainties

- **UNKNOWN:** whether forecasts are original point-in-time broker values or later reconstructed values.
- **UNKNOWN:** whether Actual/Previous fields reflect first-release vintages or later database revisions.
- **UNKNOWN:** historical broker UTC-offset/DST transition rules (the snapshot offset is +03:00).
- **KNOWN:** PMI populations are separated by source revision; revision codes are not relabeled heuristically as flash/final.
- **KNOWN LIMITATION:** 1,288 non-weekend candle gaps across discovered v3.1 FX data.
- **KNOWN LIMITATION:** simultaneous releases prevent clean causal attribution to a single headline.
- **KNOWN LIMITATION:** central-bank scalar deltas omit guidance/information shocks.
- **KNOWN LIMITATION:** no exploration/confirmation split, multiple-testing correction, regime validation, costs, or execution model.

## 16. Changes made

- replaced display-name statistical grouping with MetaQuotes `event_id + revision` grouping;
- added deterministic v3.1 source discovery with explicit override and legacy fallback;
- preserved and exposed period, revision, event metadata, units/scaling, source URL, and raw scaled integers;
- added stable `eventSeriesKey`, source file, and simultaneous-release identities;
- made ambiguous name-only requests fail closed;
- exposed PMI cadence/stage warnings;
- fixed filtered score matrices;
- enforced walk-forward minimum N for exact zero;
- made nonzero scoring return null without a threshold;
- aligned distribution eligibility with scoring eligibility;
- preserved unrounded rank/tie diagnostics to eight decimals;
- separated weekend from non-weekend candle gaps;
- corrected UTC labels to broker server time;
- expanded CSV audit exports;
- fixed frontend series-ID and scoring-mode propagation;
- corrected contradictory README formulas and claims;
- added a reproducible real-data audit generator.

No `raw_data/` files were modified. The user's already-missing legacy audit files were not restored or altered. No profitability optimization was added.

## 17. Tests added

The suite now has 12 files and 70 passing tests. New coverage includes:

- same-name event-ID separation and ambiguous-query rejection;
- source filename/series preservation;
- displayed threshold equals scoring threshold population;
- filtered matrix N propagation;
- synthetic same-timestamp batch isolation;
- exact-zero insufficient-history suppression;
- null-threshold score suppression;
- weekday-gap versus weekend-gap detection.
- v3.1 RFC4180 parsing, metadata preservation, and revision-series ambiguity rejection.

Existing tests cover signed generic percentiles, strict-lower ranks, ties, exact zero, floating equality, type-7 interpolation, retrospective and walk-forward modes, exact base/quote/log returns, exact-hour and between-hour anchors, weekend sequences, missing trailing horizons, simultaneous releases, statistics, and real API service calls.

Validation completed:

- `npm test`: 70/70 passed
- `npm run build`: server TypeScript and web production build passed
- `npm run ingest`: 123,054 calendar rows and 1,686,617 FX H1 bars indexed from the selected v3.1 source
- `npm run audit:quant`: seven real cases plus all-pair candle integrity evidence generated

## 18. Manual real-data calculations

| Value ID | Series | Pair/position | A/F/P | Surprise | Retro N / P75 / rank / score | WF N / P75 / score | P0 | H1 event-currency return | Flags |
|---|---|---|---|---:|---|---|---:|---:|---|
| 229745 | USD CPI m/m | EURUSD quote | 0.2 / 0.6 / 0.3 | −0.4 | 97 / 0.4 / 71.1340 / −2 | 90 / 0.4 / −2 | 1.16420 | −0.085822% | 11 simultaneous |
| 229744 | USD CPI m/m | USDJPY base | 0.3 / −0.3 / 0.1 | +0.6 | 97 / 0.4 / 89.6907 / +3 | 89 / 0.4 / +3 | 147.885 | +0.465226% | non-weekend gap in H42 path |
| 229741 | USD CPI m/m | EURUSD quote | −0.1 / 0.4 / 0.2 | −0.5 | 97 / 0.4 / 81.4433 / −3 | 86 / 0.3 / −3 | 1.10972 | −0.266024% | weekend; 14 simultaneous |
| 229757 | USD Core CPI m/m | EURUSD quote | 0.3 / 0.3 / 0.2 | 0 | 71 / 0.2 / N/A / +1 | 67 / 0.2 / +1 | 1.16420 | −0.085822% | exact match; 11 simultaneous |
| 115719 | USD Core PCE m/m | EURUSD quote | 0.3 / 0.1 / 0.3 | +0.2 | 76 / 0.2 / 60.5263 / +2 | 24 / 0.125 / +3 | 1.17546 | +0.142274% | revised P=0.4; weekend |
| 118422 | Eurozone Manufacturing PMI r1 | EURUSD base | 47.8 / 45.1 / 46.3 | +2.7 | 104 / 1.4 / 90.3846 / +3 | 32 / 1.2 / +3 | 1.10354 | +0.015405% | revision-isolated; 4 simultaneous |
| 277623 | USD Nonfarm Payrolls | EURUSD quote | 162 / 41 / −23 | +121 | 112 / 303.5 / 50.0000 / +2 | 111 / 314 / +2 | 1.16012 | −0.073215% | Friday/weekend; 10 simultaneous |

The full JSON includes surrounding prices, H1/H2/H4/H12/H24/H42 raw pair returns, exact simple returns, log returns, tie bands, simultaneous identities, and equality comparisons against the engine.

## 19. Recommended next research step

The single next milestone should be a **frozen, versioned research snapshot and preregistered walk-forward validation protocol**. Record the v3.1 tree hash, keep the exporter/source version with it, choose discovery and untouched confirmation windows, define multiple-testing control, and specify spread/slippage/holding-cost assumptions before examining strategy performance.

The current export already contains the requested identity and scaling fields. What remains is governance against data drift and researcher degrees of freedom, plus a separate historical-timezone policy if UTC joins are introduced.

## Direct answers

1. **Definitely correct:** core delta math, type-7 thresholds, strict-lower/tie math, base/quote/log return normalization, complete-bar H1 anchoring, available-bar sequencing, and timestamp-batched walk-forward classification after the fixes.
2. **Definitely wrong:** old same-name PMI grouping, filtered matrices, zero/min-history behavior, null-threshold defaulting, generic-gap weekend labels, UTC labels, incomplete CSV evidence, and stale documentation.
3. **Fixed:** all definite implementation defects listed above; raw values were preserved.
4. **Uncertain:** forecast/actual vintage immutability and historical broker timezone/DST rules; unit and revision metadata are now preserved.
5. **Descriptive trust:** yes within a selected `event_id + revision` series, subject to simultaneous-release and data-vintage caveats.
6. **Walk-forward percentile leakage:** yes, the mode is trustworthy for its narrow no-future-percentile claim within the chosen source-series identity.
7. **Serious strategy blockers:** point-in-time vintage uncertainty, historical timezone policy, missing candle gaps, simultaneous attribution, multiple testing, no holdout/regime validation, and no cost/execution model.
8. **Single next milestone:** freeze this validated v3.1 snapshot and preregister a costed walk-forward confirmation protocol.
