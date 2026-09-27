# Macro Research

Repository for macroeconomic release displacement analysis and candidate setup evaluation.

## Where to look

| Location | Role |
| --- | --- |
| [US CPI on EURUSD](docs/candidate%20research/US%20CPI%20on%20EURUSD.md) | Maintained study narrative: baseline, separately named candidate variants, results, and open questions. This is the human-readable research record. |
| [Director's notes](docs/director's%20note/notes.md) | Ideas and possible later work; not an approved trading rule or evidence ledger. |
| [`TABLE VIEWER/cpi_setup/`](TABLE%20VIEWER/cpi_setup/) | Original A−F/H24 CPI baseline ledgers and report. Preserve these unchanged. |
| [A−P/H60 trial evidence](evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/) | Separate post-hoc CPI momentum decision/trade ledgers, report, and protocol. |
| [Research viewer](TABLE%20VIEWER/table_viewer.html) | Generated inspection screen for episodes and candidate results; not a second manually maintained research document. |

The pinned MT5 export lives under `data/pinned/` locally and is Git-ignored. Edit the source files under `TABLE VIEWER/generator/`, then regenerate the standalone HTML rather than editing its embedded data by hand.

## Research Table Viewer

The approved research viewer is a self-contained, light-mode HTML artifact located at:
`TABLE VIEWER/table_viewer.html`

It opens directly in any modern browser via double-clicking (`file://` protocol) with zero server, CDN, network, or external runtime dependencies.

### Workspace Tabs
1. **Event Table**: 19-pair FX macroeconomic displacement analysis (H1–H60 pips from defined H1 entry open) across 5 event families (US Inflation, US Labor, US Retail Sales, German Ifo, US ISM PMI), with exact N accounting and Type-7 percentiles.
2. **Candidate Research**: Separate selector entries show the original **US CPI · EURUSD · A−F surprise · H24** baseline (36 trades) and the **A−P momentum · H60** post-hoc trial (55 trades). Both use the pinned 2015–September 23, 2026 snapshot; 2026 is partial. Neither is a registered or validated setup. Other macro studies remain pending, with no invented results.

### Regeneration
To regenerate the standalone HTML viewer:
```bash
python "TABLE VIEWER/generate_table.py"
```

To run the full CPI simulation suite and refresh audit ledgers:
```bash
python "TABLE VIEWER/cpi_simulation.py"
```

To regenerate the separate A−P/H60 exploratory ledgers and report:
```bash
python "TABLE VIEWER/cpi_momentum_simulation.py"
```

### Verification Suite
To execute all numerical correctness, audit reconciliation, and tab navigation tests:
```bash
python -m unittest discover -s "TABLE VIEWER" -p "test_*.py"
```

### Governance Notice
Exploratory historical OHLC simulation; no registered setup. Zero setups are currently registered for demo forward testing. Gross mid/bid prices only; zero broker friction modeled.
