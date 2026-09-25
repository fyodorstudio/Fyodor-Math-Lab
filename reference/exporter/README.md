# Fyodor MT5 Research Exporter v3.1

The source/compiled exporter live here alongside two **ignored, large, timestamped data snapshots**. Keep the validated `FyodorResearchExport_v3_20260923_234930_server` snapshot in its current location: the research code and frozen protocols pin that path. The earlier `233418` snapshot is malformed, but is retained for provenance; never select it for research. Do not move or delete either as a documentation cleanup. See the [repository research roadmap](../../docs/FMS_RESEARCH_ROADMAP.md).

`FyodorResearchExporterV3.mq5` creates a new timestamped export folder on every run. It does not modify an earlier dataset. Version 3.1 uses quoted UTF-8 CSV text fields and defaults to exporting only symbols whose MT5 calculation mode is Forex.

## Before running

1. In MT5, open **Tools → Options → Charts** and set **Max bars in chart** high enough to cover the requested H1 history. Restart MT5 if you change it.
2. Put every FX instrument you want exported in Market Watch. With the default `ExportOnlyForexSymbols = true`, stocks, crypto, commodities, and other non-FX calculation modes are recorded as skipped and no candle file is produced for them.
3. Open the script in MetaEditor and compile it. Treat the `.mq5` source as authoritative; do not reuse an older `.ex5`.
4. Confirm MT5 is connected to the intended broker and trade server.

## Run

1. Attach the compiled script to any chart.
2. Keep `CandleTimeframe = PERIOD_H1` for the current research lab.
3. Leave both `...ToDate` inputs at `0` to freeze the run at its recorded trade-server snapshot time.
4. Keep `ExcludeIncompleteBar = true`.
5. Review the Experts log for failed calendar queries, failed symbols, or truncated history warnings.

By default, output is written beneath:

`Terminal/Common/Files/FyodorResearchExport_v3_<timestamp>_server/`

The exact folder name is printed and displayed when the run finishes.

## Return this evidence

Copy or zip the **entire timestamped folder** without opening and resaving any CSV. It should contain:

- `manifest.csv`
- `calendar_events.csv`
- `calendar_releases.csv`
- `candle_symbols.csv`
- `candles/`

Do not rename files or merge this export into an older `raw_data` dataset. Once copied into the research repository, calculate SHA-256 hashes before any ingestion or transformation.

The exporter intentionally omits the account login and client name. Broker company, server, terminal build, snapshot times, exporter/schema versions, query failures, and coverage diagnostics are retained for reproducibility.
