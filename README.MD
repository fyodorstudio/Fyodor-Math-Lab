# Expanded Macro Research

An isolated workspace for researching economic-release reactions across a fixed FX universe. It now has **verified local CPI and NFP V2 exploratory results** and a standalone [HTML evidence viewer](HTML%20Viewer/table_viewer.html). No trading setup is registered or shown to be profitable after costs. Start with [the local results index](Research%20Candidate/README.md), [the expansion plan](Docs/CONTRACT%20AND%20PLANNING/MAJOR%20EXPANSION%20PLAN.MD), and [the calculation contract](Docs/CONTRACT%20AND%20PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md).

## Working layout

```text
Expanded Macro Research/
├── README.MD                         tracked navigation and 28-pair whitelist
├── Docs/
│   ├── CONTRACT AND PLANNING/        research design and calculation contract
│   ├── MT5_EXPORTER_SCRIPT/          old V3 reference and new V4 exporter
│   └── SYMBOL_PLACEHOLDER_FOLDER/    local, Git-ignored symbol wish list
├── HTML Viewer/
│   ├── table_viewer.html             standalone CPI/NFP evidence snapshot
│   └── Python Calculator/           Python calculation/build source only
├── Research Candidate/              versioned evidence, grouped by family/trial
│   ├── README.md                    tracked folder purpose and evidence boundary
│   ├── CPI/                         local, ignored V2 exploration packages
│   └── NFP/                         local, ignored V2 exploration packages
└── raw_data/                        local, Git-ignored MT5 exports
    └── FyodorResearchExport_v4_20260928_021936_79538281_server/
```

The V4 export and large V2 output packages are local and ignored by Git; see the [results index](Research%20Candidate/README.md) before opening a package. The full-year release core is 2015–2025, with January–August 2026 shown separately; candle data extends beyond those release dates to evaluate H240.

The Python code sits under `HTML Viewer/Python Calculator/`, but its **calculation output is evidence in `Research Candidate/`**, not numbers typed into HTML. The viewer is generated from the pinned final CPI/NFP V2 release paths and summary grids by `python "HTML Viewer/Python Calculator/build_viewer.py"`; `--check` confirms it matches those packages. The generated HTML opens locally without a web server and includes both source digests and an explicit no-registration warning. It does not embed the 200 MB trial ledgers; use the local packages for deeper audits. No old viewer, calculations, or CPI/NFP ledgers have been imported from the previous repository.

## Allowed FX universe

The V4 exporter requested **all 28 listed FX pairs**—seven USD majors and 21 extended crosses. This is the exported whitelist, **not** the active research set or a claim that every event affects every pair.

| Seven USD majors | 21 extended FX crosses |
| --- | --- |
| AUDUSD, EURUSD, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY | AUDCAD, AUDCHF, AUDJPY, AUDNZD, CADCHF, CADJPY, CHFJPY, EURAUD, EURCAD, EURCHF, EURGBP, EURJPY, EURNZD, GBPAUD, GBPCAD, GBPCHF, GBPJPY, GBPNZD, NZDCAD, NZDCHF, NZDJPY |

**Active research set: 19 pairs.** The following nine exported pairs are **explicitly excluded from all first-pass research, including their available 2026 rows**: `CADCHF`, `CADJPY`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPNZD`, `NZDCAD`, `NZDCHF`, `NZDJPY`. Their H1 files begin only on 25–26 November 2025; the Director confirmed the MT5/broker history bottleneck and chose not to pursue another broker. Preserve the raw files but do not select these pairs, count them as losses, or silently admit their shorter-period observations. Restoring any pair requires a new, explicit scope version.

For an event associated with one of AUD, CAD, CHF, EUR, GBP, JPY, NZD or USD, the **primary** comparison uses active pairs containing that currency as base or quote. Thus the initial **US CPI and US NFP studies each have seven relevant pairs**: `AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`. The other 12 active crosses belong to future non-USD family studies, not indirect USD spillover tests. Even active pairs require per-event path checks: `EURCHF` has a known 437-hour gap from 31 December 2014 to 19 January 2015. Indirect effects on pairs without the event currency are a separate, explicitly named question. Crypto, energy and metals in the local wish list are out of scope for this pass.

## Data and time rules

- **H1 only** for the first export, entry, price path and H60/H120/H240 holding horizons. No M15, M30, M1 or tick history in this pass.
- The simulated entry is the first H1 bar open **strictly after** the release. Its delay from the announcement is recorded; it is not an at-release fill.
- Compare full calendar years 2015–2025; show January–August 2026 in a separate partial-year panel. The conservative 2026 release cutoff is **31 August**, subject to complete observed candle paths. Do not cut candle data at the release cutoff.
- Export all broker-available data, record exact coverage and SHA-256 hashes, and exclude missing or incomplete event/pair/horizon cases with reasons. Never synthesize missing prices or calendar values.
- The V4 exporter has been compiled and run. Its first snapshot is identified above; see the [export audit and usage note](Docs/MT5_EXPORTER_SCRIPT/new/README.md). `candles_completed=true` means the run finished, **not** that all pairs have full history.

Raw data, local exploration packages, and the symbol-placeholder tree are ignored by Git. The exported whitelist and active/excluded decision are repeated here deliberately so a GitHub clone preserves the research boundary. CPI and NFP V2 have calculated gross OHLC outcomes, but no rule has been selected or registered for forward testing.

The publishable `EXPANDED` branch is a clean snapshot based on the existing remote branch. The original local sequence of research commits, including invalidated V1 output blobs and the historical commit IDs cited by the local V2 manifests, is preserved on `archive/EXPANDED-before-size-cleanup` **only on this computer**. That archive branch cannot be pushed to ordinary GitHub Git because of the V1 file-size limit. Keep it and the Git-ignored final V2 packages for exact provenance.

## Git handoff

The local work is prepared on branch `EXPANDED` for the existing [Fyodor-Math-Lab GitHub repository](https://github.com/fyodorstudio/Fyodor-Math-Lab). That remote's `main` branch contains the older project; `EXPANDED` is an independent new-repository history and should **not** be force-pushed over `main`. After verifying the local commit and remote, the user can publish this branch with `git push -u origin EXPANDED`.
