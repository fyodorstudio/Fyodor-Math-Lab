# Fyodor Research Exporter V4 — usage and first-export audit

`FyodorResearchExporterV4.mq5` is the source for the expanded H1/28-pair data export. It was built from the V3 reference in `../old/`, which is preserved unchanged. MetaEditor compiled V4 locally with **0 errors, 0 warnings** on 2026-09-28. Compilation does **not** verify that this broker supplies the requested history.

## Before attaching it in MT5

1. Copy the `.mq5` source into your MT5 terminal's `MQL5/Scripts` directory and compile it in that terminal's MetaEditor. Attach the compiled script to a chart; the chart's symbol and timeframe do not set export scope.
2. In MT5 options, set **Max. bars in chart** high enough for the full requested H1 history. MT5 can reject history requests that exceed `TERMINAL_MAXBARS` ([CopyRates reference](https://www.mql5.com/en/docs/series/copyrates)). The script records the actual setting in `manifest.csv`.
3. Leave `CandleTimeframe=PERIOD_H1`, `RequireExact28PairSet=true`, `ExcludeIncompleteBar=true`, `ExportCalendar=true`, `ExportRequestedBars=true`, and `StopOnCalendarError=true` for the first research run.
4. `RequestedBrokerSymbols` defaults to the 28 plain pair names. If your broker uses suffixes, replace entries with the **exact broker symbol names**, preserving exactly one symbol for each canonical pair in the root README. The script selects those names in Market Watch, verifies base/quote currencies, and refuses to certify a missing or duplicate canonical pair.
5. Leave `CandleFromDate=2014.11.01` unless there is a documented reason to change it; the earlier start supplies pre-release ATR warmup for 2015. This does not force the broker to provide those bars. Calendar rows start in 2015; both exports run through the trade-server snapshot unless you set an earlier end.

## After the run

Copy the **entire newly named export folder** unchanged into `raw_data/`. Do not merge it with an older folder. Before treating it as research input, inspect:

- `manifest.csv`: `calendar_completed`, `candles_completed`, `missing_required_pairs_count`, and `partial_coverage_symbols`.
- `calendar_currencies.csv`: all eight requested currencies and any query failures or zero-event warnings.
- `candle_symbols.csv`: exactly 28 successfully exported canonical pairs, their actual broker symbols, first/last H1 timestamps, bar counts, `chart_price_basis`, and any coverage warnings.
- Every candle file's ordering and gaps, and the calendar/candle time convention. Calculate SHA-256 hashes on the copied files. The exporter does not compute hashes inside MT5.

The script retries `CopyRates` when a positive response still appears short of the requested boundaries, because MT5 can return available bars while older history continues downloading. After bounded retries it may export the best observed partial history **with warnings**; it never fabricates missing bars. A clean compile or an output file alone is **not** evidence of complete 2015–2026 coverage. Per-event H60/H120/H240 and ATR eligibility are decided later by the independent calculator.

For the first handoff, bring back the export-folder path and the four summary fields above. Do not run the research calculator yet.

## First export: 28 September 2026

Snapshot `FyodorResearchExport_v4_20260928_021936_79538281_server` was copied **unchanged** into ignored `raw_data/`. All 34 copied files matched their MT5 originals by SHA-256. The run reported 28 exported pairs, zero missing requested pairs, 1,452,398 H1 bars, eight successful calendar-currency queries, 1,051 calendar event definitions and 123,256 release rows. Independent streaming checks found no out-of-order candle timestamps or invalid OHLC rows and reconciled file row counts to the manifest. This is a structural audit, **not** a claim that all release inputs or H240 paths are complete.

The nine truncated-history pairs are `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY`. They begin on 25–26 November 2025. The Director checked MT5 and attributed the bottleneck to MT5/broker data rather than exporter code, then chose to **exclude these nine from all first-pass research** rather than pursue another broker. Their raw files remain preserved. The 19 remaining pairs still need per-event coverage checks; `EURCHF` has a known 437-hour gap from 31 December 2014 to 19 January 2015.

Three anchor file hashes for identifying this local snapshot (SHA-256):

| File | SHA-256 |
| --- | --- |
| `manifest.csv` | `1E7C8A5047BDEDAF0F66DE23F5E6CC382C29EA839B9E07A911789BBFFC548A6F` |
| `calendar_releases.csv` | `FCB68E1C2A6269D98287F4BEDBEE1F3BCB5A8C99379502782359EDFD20E83D6F` |
| `candle_symbols.csv` | `876495CC3FCD0B4E88CB1412E6DF154CF8813B5DF7CC5EC57A8F74C57BD7475D` |

The calculator's tracked provenance index must compute and retain hashes for **all 34 raw files** before producing trial outcomes. Do not interpret `candles_completed=true` as complete historical coverage.
