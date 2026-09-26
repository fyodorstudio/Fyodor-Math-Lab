# EURUSD H1 Macro-Event Price & Release Atlas (2015–2026)

## 1. Owner's Scope Decision & Governance Notice

This directory contains a self-contained, offline HTML macroeconomic event viewer and interactive candlestick atlas displaying EURUSD H1 trajectories ($H_1$ through $H_{60}$) following scheduled macroeconomic releases, paired with an event-level macroeconomic release ledger across 2015–2026.

### Owner's Scope Decision (Full-History Exploration)
- **Deliberate Unblinded History**: The Project Director authorized full exploratory inspection across the entire pinned dataset (2015 through the export snapshot of 2026-09-23). Artificial 2023–2026 price concealment has been removed from **THIS VIEWER**.
- **Holdout Forfeiture Warning**: *Once these prices are inspected, 2023–2026 cannot later be claimed as an untouched historical holdout for rules selected with this tool.* Genuinely unblinded forward testing will require future demo terminal data.
- **Descriptive Exploration Only**: Cell values reflect **gross directional price displacement (%)**. This is **NOT** a win rate, TP-before-SL probability, net profit, or executable trading strategy. Zero spreads, commissions, or slippage are deducted.
- **US ISM Manufacturing PMI**: Evaluated strictly as descriptive exploration, **NOT** as an approved trading rule.
- **Static Export Snapshot (2026 is Partial)**: The data export is a static server snapshot dated `2026-09-23`. Year 2026 contains partial observations up to September 2026 and does not imply live updating.

### Deferred Idea: Cross-Symbol Research
This atlas strictly utilizes the pinned EURUSD H1 candle file (`candles_EURUSD_H1.csv`). The other 50 FX currency pairs, 279 tradable broker symbols, commodities, and cryptocurrencies exported in the repository remain out of scope for this tool. Cross-symbol macro spillover and multi-asset response modeling are explicitly deferred for future research.

---

## 2. Accounting Integrity: Distinct Event Episodes vs. Calendar Rows

Earlier iterations suffered from an accounting discrepancy where component indicator rows in `calendar_releases.csv` were conflated with distinct event trading episodes.

### Key Distinctions:
1. **Raw Calendar Row**: One single indicator component row in `calendar_releases.csv` (e.g. 1,260 total rows across the 5 target families).
2. **Distinct Event Episode**: A unique macroeconomic release event on a single date and time. When an institution releases multiple indicators simultaneously as a package, they constitute **ONE distinct event episode** and contribute exactly **ONE price path** to sample size and statistics.
3. **Distinct Release Timestamps**: The unique broker-server release timestamps.

### Co-Release Reconciliation:
- **German Ifo**: Releases Business Climate (`EUR:DE:276030003:r0`) and Business Expectations (`EUR:DE:276030001:r0`) concurrently. The pre-2023 archive contains **40 actionable Ifo episodes** (18 Long, 22 Short), not 80 duplicated trades.
- **US Retail Sales**: Releases Retail Sales m/m (`USD:US:840020010:r0`) and Core Retail Sales m/m (`USD:US:840020011:r0`) concurrently. The pre-2023 archive contains **49 trade episodes** (27 Short, 22 Long), not 98 duplicated trades.
- **US Inflation (CPI & Core CPI)**: Co-released concurrently at 15:30 or 16:30 server time. On exactly 8 release dates between 2020 and 2022, both Headline CPI and Core CPI qualified concurrently with $\pm 3$ surprise scores.
- **157 Memberships vs. 149 Timestamps**: Across Phase 1 (68 memberships), German Ifo (40 actionable episodes), and US Retail Sales (49 trade episodes), there are exactly **157 pre-2023 cohort memberships** spanning exactly **149 distinct release timestamps** ($157 - 8 = 149$).

---

## 3. Pinned Data Lineage & Cryptographic Hashes

1. **EURUSD H1 Candle File**:
   - Path: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv`
   - SHA-256 Digest: `893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5`
   - Total Candles: 72,967 active H1 bars (`1420189200` to `1790200800`, spanning 2015-01-02 to 2026-09-23).
2. **Calendar Releases File**:
   - Path: `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv`
   - SHA-256 Digest: `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e`
   - Total Target Component Rows: 1,260 (collapsed into 840 distinct event episodes).
3. **Archived Evidence References**:
   - Phase 1 Discovery: `evidence/trials/phase1/phase1_exploration.json`
   - German Ifo Pilot: `evidence/trials/ifo/ifo_pilot_ledger.json` & `ifo_pre2023_exploration_report.json`
   - US Retail Sales Discovery: `evidence/trials/retail_sales/retail_sales_pre2023_discovery.json`

---

## 4. Target Series Metadata & Identifiers

| Family | Series Name | Exact Identifier | Event ID | Base Direction |
| :--- | :--- | :--- | :---: | :---: |
| **US inflation** | USD CPI m/m | `USD:US:840030005:r0` | `840030005` | SHORT (+3) / LONG (-3) |
| **US inflation** | USD Core CPI m/m | `USD:US:840030006:r0` | `840030006` | SHORT (+3) / LONG (-3) |
| **US inflation** | USD Core PCE m/m | `USD:US:840010001:r0` | `840010001` | SHORT (+3) / LONG (-3) |
| **US labor** | USD Nonfarm Payrolls | `USD:US:840030016:r0` | `840030016` | SHORT (+3) / LONG (-3) |
| **German Ifo** | Ifo Business Climate | `EUR:DE:276030003:r0` | `276030003` | LONG (Agree Pos) / SHORT (Agree Neg) |
| **German Ifo** | Ifo Business Expectations | `EUR:DE:276030001:r0` | `276030001` | LONG (Agree Pos) / SHORT (Agree Neg) |
| **US Retail Sales** | Retail Sales m/m | `USD:US:840020010:r0` | `840020010` | SHORT (Agree Pos) / LONG (Agree Neg) |
| **US Retail Sales** | Core Retail Sales m/m | `USD:US:840020011:r0` | `840020011` | SHORT (Agree Pos) / LONG (Agree Neg) |
| **US ISM PMI** | ISM Manufacturing PMI | `USD:US:840040001:r0` | `840040001` | SHORT (Surprise > 0) / LONG (Surprise < 0) |

*Retail Sales Identifier Audit*: Verified against `docs/DRAFT_RETAIL_SALES_PROTOCOL.md` and `src/package_ledger.py`. Deprecated test IDs `840030001` and `840030002` are strictly excluded.

---

## 5. Annual Accounting Breakdown (2015–2026 Snapshot)

| Year | Distinct Episodes | Raw Calendar Rows | Eligible Episodes | Research Status |
| :---: | :---: | :---: | :---: | :--- |
| **2015** | 72 | 108 | 0 | Pre-2023 Historical Period (Early history accumulating; forecasts missing) |
| **2016** | 72 | 108 | 0 | Pre-2023 Historical Period (Early history accumulating; forecasts missing) |
| **2017** | 72 | 108 | 13 | Pre-2023 Historical Period (Retail Sales start: 6, ISM: 7) |
| **2018** | 72 | 108 | 22 | Pre-2023 Historical Period (Retail Sales: 9, Ifo: 2, ISM: 11) |
| **2019** | 72 | 108 | 37 | Pre-2023 Historical Period (Phase 1 series qualify, Ifo: 10, RS: 8, ISM: 12) |
| **2020** | 72 | 108 | 49 | Pre-2023 Historical Period (NFP, CPI, PCE, Ifo: 8, RS: 8, ISM: 12) |
| **2021** | 72 | 108 | 51 | Pre-2023 Historical Period (Ifo: 10, RS: 10, ISM: 12, Phase 1) |
| **2022** | 72 | 108 | 43 | Pre-2023 Historical Period (Ifo: 10, RS: 8, ISM: 12, Phase 1) |
| **2023** | 72 | 108 | 34 | Unblinded Exploratory Period |
| **2024** | 72 | 108 | 26 | Unblinded Exploratory Period |
| **2025** | 66 | 99 | 29 | Unblinded Exploratory Period |
| **2026** | 54 | 81 | 19 | Partial Snapshot (to 2026-09-23) |
| **TOTAL** | **840** | **1,260** | **323** | **Full Pinned History** |

---

## 6. Interactive Candlestick Chart Conventions

For any selected episode, the chart renders an HTML5 canvas candlestick visualizer:
1. **Pre-Event Context**: 12 active H1 candles prior to release bar.
2. **Release Bar Highlight**: Light blue background fill, vertical cyan line, and top banner `"Release Bar"`. Tooltip clarifies: *"Release occurred within this H1 bar (exact execution tick unknown)"*.
3. **Entry Bar ($H_1$)**: Light green highlight with `"H1"` banner.
4. **Entry Open Reference**: Horizontal dashed cyan line across the chart at $P_{\text{entry\_open}}$ labeled `"Entry Open: 1.XXXXX"`.
5. **Post-Entry Active Trajectory**: Up to 60 consecutive active H1 bars ($H_1$ through $H_{60}$) with standard candlestick bodies and wicks (green bullish, red bearish).
6. **Weekend Closure Indicators**: Vertical dashed gray lines mark weekend gaps where adjacent candles have timestamps differing by more than 3,600 seconds.
7. **Interactive Crosshair & Hover Tooltip**: Hovering over any bar shows horizon label (`Pre-X`, `Release`, `Rel+X`, `H1`...`H60`), server timestamp (`YYYY.MM.DD HH:mm:ss`), OHLC prices to 5 decimals, and gross directional displacement (%):
   $$\text{Directional \%} = d \times \frac{P_{\text{close}} - P_{\text{entry\_open}}}{P_{\text{entry\_open}}} \times 100\%$$

---

## 7. Dynamic H1–H60 Response Profile Table

- **Dynamic Pooling**: When filtering by family, year, or cohort, the medians across $H_1$ through $H_{60}$ are recalculated dynamically from the individual episode return arrays of the selected subset.
- **No Averaged Medians**: Summary medians are **never** calculated by averaging precomputed medians.
- **Available $N$ Tracking**: Tooltip on every cell reports exact available sample count $N_{\text{avail}} / N_{\text{total}}$, handling recent 2026 episodes where fewer than 60 post-entry bars exist prior to the export cutoff.

---

## 8. Verification & Execution Commands

### Regenerate the Atlas:
```powershell
python "TABLE VIEWER/generate_table.py"
```

### Run Synthetic Unit Tests:
```powershell
python -B "TABLE VIEWER/test_table_viewer.py"
```

### View Offline in Browser:
```powershell
Start-Process "TABLE VIEWER\table_viewer.html"
```
Or open `file:///C:/dev/Fyodor%20Math%20Lab/Macro%20Research/TABLE%20VIEWER/table_viewer.html`.
