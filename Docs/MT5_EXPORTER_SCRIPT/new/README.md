# Fyodor Research Exporter V4 — pre-export checklist

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
