# Expanded Macro Research

An isolated workspace for researching economic-release reactions across a fixed FX universe. This repository currently contains **plans, a calculation contract, and a pending-state research viewer**, not a verified dataset, profitable result, or registered trading setup. Start with [the expansion plan](Docs/CONTRACT%20AND%20PLANNING/MAJOR%20EXPANSION%20PLAN.MD), then [the calculation and candidate contract](Docs/CONTRACT%20AND%20PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md). The exploratory ATR grid and H60/H120/H240 expiries are specified there; family signals and eligibility rules remain open.

## Working layout

```text
Expanded Macro Research/
├── README.MD                         tracked navigation and 28-pair whitelist
├── Docs/
│   ├── CONTRACT AND PLANNING/        research design and calculation contract
│   ├── MT5_EXPORTER_SCRIPT/          old V3 reference and new V4 exporter
│   └── SYMBOL_PLACEHOLDER_FOLDER/    local, Git-ignored symbol wish list
├── HTML Viewer/
│   ├── table_viewer.html             standalone viewer with pending-state grids
│   └── Python Calculator/           Python calculation/build source only
├── Research Candidate/              versioned evidence, grouped by family/trial
│   ├── README.md                    tracked folder purpose and evidence boundary
│   ├── CPI/                         empty until an audited CPI study exists
│   └── NFP/                         empty until an audited NFP study exists
└── raw_data/                        local, Git-ignored MT5 exports
    ├── raw_candle_data/H1/
    └── raw_economic_calendar_data_2015-2025/  current local placeholder name
```

Empty folders are local placeholders and may not appear in a Git clone until they contain tracked files. The tracked `Research Candidate/README.md` makes that parent folder visible, but empty `CPI/` and `NFP/` still will not appear. The calendar folder's `2015-2025` name is **not** the research cutoff: the planned full-year release core is 2015–2025, with January–August 2026 shown separately, and candle data must extend beyond those release dates to evaluate H240. A year-neutral raw calendar folder should be used when the actual export is established.

The Python code may sit under `HTML Viewer/Python Calculator/` for tidy local organization, but its **calculation output is evidence in `Research Candidate/`**, not numbers typed into HTML. The HTML file only displays audited evidence. It opens locally without a web server. No old viewer, calculations, or CPI/NFP ledgers have been imported from the previous repository.

## Allowed FX universe

The first export and research pass cover **all 28 listed FX pairs**—seven USD majors and 21 extended crosses. This is the boundary of permissible pair candidates, not a claim that every event affects every pair.

| Seven USD majors | 21 extended FX crosses |
| --- | --- |
| AUDUSD, EURUSD, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY | AUDCAD, AUDCHF, AUDJPY, AUDNZD, CADCHF, CADJPY, CHFJPY, EURAUD, EURCAD, EURCHF, EURGBP, EURJPY, EURNZD, GBPAUD, GBPCAD, GBPCHF, GBPJPY, GBPNZD, NZDCAD, NZDCHF, NZDJPY |

For an event associated with one of AUD, CAD, CHF, EUR, GBP, JPY, NZD or USD, the **primary** comparison uses whitelist pairs containing that currency as base or quote. A family is calculated across all such pairs in one versioned pass. Indirect effects on pairs without the event currency are a separate, explicitly named question. Crypto, energy and metals in the local wish list are out of scope for this pass.

## Data and time rules

- **H1 only** for the first export, entry, price path and H60/H120/H240 holding horizons. No M15, M30, M1 or tick history in this pass.
- The simulated entry is the first H1 bar open **strictly after** the release. Its delay from the announcement is recorded; it is not an at-release fill.
- Compare full calendar years 2015–2025; show January–August 2026 in a separate partial-year panel. The conservative 2026 release cutoff is **31 August**, subject to complete observed candle paths. Do not cut candle data at the release cutoff.
- Export all broker-available data, record exact coverage and SHA-256 hashes, and exclude missing or incomplete event/pair/horizon cases with reasons. Never synthesize missing prices or calendar values.
- A generic MT5 exporter should accept configured broker symbols rather than hard-code these 28. The exporter has **not yet been written or frozen** in this repo.

Raw data and the local symbol-placeholder tree are ignored by Git. The 28-pair whitelist is repeated here deliberately so a GitHub clone preserves the approved research boundary. The expansion plan and future exporter are intended to be tracked.

## Git handoff

The local work is prepared on branch `EXPANDED` for the existing [Fyodor-Math-Lab GitHub repository](https://github.com/fyodorstudio/Fyodor-Math-Lab). That remote's `main` branch contains the older project; `EXPANDED` is an independent new-repository history and should **not** be force-pushed over `main`. After verifying the local commit and remote, the user can publish this branch with `git push -u origin EXPANDED`.
