# FMS Read-Only Timestamp Eligibility & Provenance Inventory

**Document Status**: COMPLETED FIRST RESEARCH MILESTONE  
**Milestone Scope**: Read-Only, Timestamp-Only Eligibility & Provenance Ledger  
**Research Stance**: Strict Non-Discovery, Zero Optimization, Zero Strategy Backtest  
**Baseline Boundary**: Chronological split at `2023-01-01 00:00:00` (`timestamp = 1672531200`)  
**Generated At**: `2026-09-24T16:43:44.239Z`  

---

## 1. Executive Summary & Forensic Verification

This milestone implements strictly the **first FMS research milestone** defined in `research note.md`: an episode-level, read-only, timestamp-only eligibility and provenance inventory. In accordance with the protocol:
- **Zero Strategy Discovery**: No recipe was tested, ranked, or revived from old FMS 51 setups.
- **Timestamp-Only Candle Inspection**: Candle files were parsed **exclusively for column 0 (timestamp)**. No OHLC prices, tick volumes, spreads, or real volumes were read, parsed, stored, or analyzed.
- **Zero Return or Outcome Computation**: No price returns, directional classifications, MFE/MAE, TP/SL paths, R-multiples, or performance metrics were calculated.
- **Strict Pre-2023 Sealing**: Releases on or after `2023-01-01 00:00:00` are strictly excluded and sealed. Any candidate holding path crossing `2023-01-01 00:00:00` is excluded under the boundary rule.
- **Fail-Closed Methodology**: Gaps, missing bars, and uncertain boundaries are explicitly recorded and disqualified rather than guessed or smoothed.

### Source Verification & File Checksums
| Source Property | Recorded / Pinned Protocol Value | Forensic Verification Status |
|---|---|---|
| **Export Root** | `FyodorResearchExport_v3_20260923_234930_server` | Verified on disk |
| **Manifest File** | `manifest.csv` | Verified (records export configuration metadata) |
| **Schema Version** | `fyodor-mt5-research-export/3.1.0` | **EXACT MATCH** |
| **Exporter Version** | `3.1.0` | Build 6182 export |
| **Broker / Server** | `Elev8 Markets Ltd.` / `Elev8-Demo2` | Trade-server time (+03:00 snapshot offset) |
| **Calendar SHA-256** | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` | **VERIFIED MATCH** (`76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e`) |
| **Candle Symbols Exported** | `51` pairs | **51/51 SHA-256 hashes computed & recorded** |
| **Total Calendar Rows** | `123054` | Ingested: 82813 pre-2023, 40241 sealed |

*Clarification on Checksum Provenance*: `manifest.csv` records export configuration metadata (terminal build, account server, symbol list, and row counts). File SHA-256 hashes are verified against pinned protocol expected values (calendar SHA-256 matches `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` bit-for-bit).

---

## 2. Macro Packages & Immutable Deduplication

A critical quantitative failure in unprincipled news research is multiplying sample counts by treating multiple releases at the same timestamp (e.g. Nonfarm Payrolls + Unemployment Rate + Hourly Earnings), or responses across multiple FX pairs, as separate independent observations rather than distinct timestamp packages.

Under this inventory:
- **Total Pre-2023 Calendar Releases**: **82,813** raw rows.
- **Distinct Timestamp Packages**: **30,015** distinct timestamps.
- **Deduplication Ratio**: On average, each distinct timestamp package bundles **2.76** calendar releases.
- **Same-Time Cross-Currency Collisions**: **2,501** packages (8.33%) contain simultaneous releases across multiple sovereign currencies (e.g. simultaneous US and Canadian employment data at 15:30 broker time).

### Macro Package Currency Distribution
| Currency | Raw Pre-2023 Releases | Approximate Share |
|---|---:|---:|
| **USD** | 27,619 | 33.35% |
| **EUR** | 23,282 | 28.11% |
| **JPY** | 9,047 | 10.92% |
| **GBP** | 8,049 | 9.72% |
| **AUD** | 4,692 | 5.67% |
| **CAD** | 4,462 | 5.39% |
| **NZD** | 3,473 | 4.19% |
| **CHF** | 2,189 | 2.64% |

---

## 3. Exact Calendar Series & Non-Claiming Macro-Family Taxonomy

Releases are identified by their exact source series key: `currency:country:event_id:revision`. Event names are preserved solely as descriptive presentation labels. Parsed with RFC4180 quote awareness and strict 36-column type validation.

Across the pre-2023 dataset, **1,172** exact series are present.

### Non-Claiming Macro-Family Distribution
| Macro Family | Exact Series Count | Total Pre-2023 Releases | Economic Rationale / Scope |
|---|---:|---:|---|
| **Unclassified** | 491 | 34,722 | Ambiguous, non-standard, or unmapped events |
| **Inflation** | 190 | 13,848 | CPI, HICP, PPI, PCE deflator, price indices |
| **Business Surveys / PMI** | 120 | 8,830 | S&P Global/Markit, ISM, IFO, ZEW, regional Fed surveys |
| **Labor / Employment** | 89 | 6,140 | Payrolls, unemployment, claims, wages, workforce |
| **International Trade** | 53 | 4,732 | Trade balance, current account, import/export flows |
| **Consumer / Retail** | 46 | 3,634 | Retail sales, consumer confidence, spending indices |
| **Production / Activity** | 37 | 3,194 | Industrial output, factory orders, capacity utilization |
| **Housing / Construction** | 34 | 2,848 | Building permits, home sales, mortgage applications |
| **Central Bank / Rates** | 43 | 2,532 | Benchmark policy rates, official target rates |
| **National Accounts / Growth** | 65 | 1,966 | GDP, GNP, gross value added |
| **Government / Fiscal** | 4 | 367 | Budget balances, treasury statements |

### Input Completeness: Top Documented Exact Series ($N \ge 20$, Complete A/F/P $\ge 80\%$)
Only **41** exact series across the entire calendar satisfy basic input completeness ($\ge 20$ pre-2023 releases with $\ge 80\%$ complete Actual, Forecast, and Previous fields).

| Series Key | Label | Family | Pre-2023 N | Years | A% | F% | P% | AFP% |
|---|---|---|---:|---|---:|---:|---:|---:|
| `USD:US:840020015:r0` | Housing Starts m/m | Housing / Construction | 84 | 2016–2022 | 100% | 81% | 99% | **81.0%** |
| `USD:US:840020016:r0` | Building Permits m/m | Housing / Construction | 84 | 2016–2022 | 100% | 81% | 99% | **81.0%** |
| `GBP:GB:826020017:r0` | BoE M4 Money Supply m/m | Unclassified | 72 | 2017–2022 | 100% | 90% | 100% | **90.3%** |
| `GBP:GB:826020018:r0` | BoE Mortgage Approvals | Housing / Construction | 72 | 2017–2022 | 100% | 90% | 100% | **90.3%** |
| `USD:US:840020006:r1` | Wholesale Inventories m/m | Unclassified | 66 | 2017–2022 | 94% | 92% | 100% | **92.4%** |
| `USD:US:840020006:r3` | Wholesale Inventories m/m | Unclassified | 64 | 2017–2022 | 100% | 100% | 100% | **100.0%** |
| `USD:US:840030031:r0` | Import Price Index excl. Petrole | Inflation | 60 | 2018–2022 | 100% | 83% | 98% | **83.3%** |
| `EUR:DE:276010005:r0` | Export Price Index m/m | Inflation | 59 | 2018–2022 | 100% | 85% | 98% | **84.7%** |
| `EUR:DE:276010006:r0` | Export Price Index y/y | Inflation | 59 | 2018–2022 | 100% | 85% | 98% | **84.7%** |
| `USD:US:840020022:r1` | Nondefense Capital Goods Shipmen | Unclassified | 59 | 2018–2022 | 100% | 85% | 100% | **84.7%** |
| `USD:US:840020022:r3` | Nondefense Capital Goods Shipmen | Unclassified | 59 | 2018–2022 | 100% | 85% | 98% | **84.7%** |
| `EUR:FR:250010002:r1` | CPI y/y | Inflation | 57 | 2018–2022 | 100% | 86% | 98% | **86.0%** |
| `EUR:FR:250010002:r3` | CPI y/y | Inflation | 57 | 2018–2022 | 100% | 86% | 100% | **86.0%** |
| `EUR:ES:724010001:r1` | CPI m/m | Inflation | 53 | 2018–2022 | 100% | 91% | 100% | **90.6%** |
| `EUR:ES:724010002:r1` | CPI y/y | Inflation | 53 | 2018–2022 | 100% | 91% | 100% | **90.6%** |
| `EUR:ES:724010003:r1` | HICP m/m | Inflation | 53 | 2018–2022 | 100% | 91% | 100% | **90.6%** |
| `AUD:AU:36500001:r1` | S&P Global Manufacturing PMI | Business Surveys / PMI | 49 | 2018–2022 | 100% | 84% | 98% | **83.7%** |
| `AUD:AU:36500001:r3` | S&P Global Manufacturing PMI | Business Surveys / PMI | 49 | 2019–2022 | 100% | 84% | 100% | **83.7%** |
| `AUD:AU:36500002:r1` | S&P Global Services PMI | Business Surveys / PMI | 49 | 2018–2022 | 100% | 84% | 98% | **83.7%** |
| `AUD:AU:36500002:r3` | S&P Global Services PMI | Business Surveys / PMI | 48 | 2019–2022 | 100% | 83% | 100% | **83.3%** |
| `EUR:ES:724500001:r0` | S&P Global Manufacturing PMI | Business Surveys / PMI | 46 | 2019–2022 | 100% | 100% | 100% | **100.0%** |
| `EUR:ES:724500002:r0` | S&P Global Services PMI | Business Surveys / PMI | 46 | 2019–2022 | 100% | 100% | 100% | **100.0%** |
| `EUR:IT:380500001:r0` | S&P Global Manufacturing PMI | Business Surveys / PMI | 46 | 2019–2022 | 100% | 100% | 100% | **100.0%** |
| `EUR:IT:380500002:r0` | S&P Global Services PMI | Business Surveys / PMI | 46 | 2019–2022 | 100% | 100% | 100% | **100.0%** |
| `JPY:JP:392500002:r1` | au Jibun Bank Services PMI | Business Surveys / PMI | 42 | 2019–2022 | 100% | 100% | 100% | **100.0%** |

---

## 4. Instrument History Availability & H1-Derived H4 Coverage Proxy

> [!IMPORTANT]
> **METHODOLOGICAL CLASSIFICATION: H1-DERIVED COVERAGE PROXY**  
> This inventory evaluates whether four correctly aligned H1 candle timestamps exist for each candidate H4 period. It does **not** assert native H4 prices, order book fills, or a validated execution contract.

### Instrument History Availability in Export
Physical candle records on disk fall into three empirical categories:
- **19 Pairs with Full 2015–2022 Span**: Possess 49,468 to 49,761 pre-2023 H1 bars starting in January 2015 and continuing through December 30, 2022. Each possesses 377–385 pure weekend closures and 42–53 weekday/mixed gaps (chiefly holiday market closures such as Christmas/New Year and DST transitions; maximum gap duration 82–106 hours):
  `AUDCAD`, `AUDCHF`, `AUDJPY`, `AUDNZD`, `AUDUSD`, `CHFJPY`, `EURAUD`, `EURCAD`, `EURCHF`, `EURGBP`, `EURJPY`, `EURNZD`, `EURUSD`, `GBPCHF`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`.
- **17 Pairs with Truncated Pre-2023 Span**: Possess 4,401 to 14,010 pre-2023 H1 bars with history ending prematurely or containing multi-year gaps:
  - `USDHKD` has 14,010 pre-2023 bars, ending 2022-10-14 (full export extends to 2026-09-23), featuring a **48,329-hour multi-year gap** between 2017-03-24 and 2022-09-28.
  - `USDSEK` and `USDSGD` possess 10,511 and 10,516 pre-2023 bars, ending 2022-10-14, featuring a **53,423-hour multi-year gap** between 2016-08-24 and 2022-09-28.
  - `EURHKD` has 8,489 bars ending 2017-03-15, with a **6,109-hour gap** between 2015-02-27 and 2015-11-09.
  - 13 other truncated pairs (`EURHUF`, `EURNOK`, `EURPLN`, `EURSEK`, `EURTRY`, `SGDJPY`, `USDCNH`, `USDCZK`, `USDDKK`, `USDHUF`, `USDNOK`, `USDPLN`, `USDTRY`) end in August/September 2016.
- **15 Pairs with ZERO Pre-2023 Bars**: Possess zero bars prior to late 2025:
  `CADCHF`, `CADJPY`, `EURMXN`, `EURZAR`, `GBPAUD`, `GBPCAD`, `GBPJPY`, `GBPMXN`, `GBPNZD`, `GBPZAR`, `NZDCAD`, `NZDCHF`, `NZDJPY`, `USDMXN`, `USDZAR`.

*Methodological Declaration*: Descriptive bar counts, gap counts, and spans are reported as verified physical data observations on disk. They do not constitute an arbitrary viability filter or strategy rule.

### Full Instrument Candle Inventory (All 51 Pairs)
| Pair | Pre-2023 Bars | Total Bars | Earliest Date | Latest Pre-2023 Date | Full Export End | Pure Weekend Gaps | Weekday/Mixed Gaps | Max Pre-2023 Gap | Category Span |
|---|---:|---:|---|---|---|---:|---:|---|---|
| **AUDCAD** | 49,761 | 72,967 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 380 | 48 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **AUDCHF** | 49,750 | 72,970 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 381 | 47 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **AUDJPY** | 49,755 | 72,974 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 381 | 50 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **AUDNZD** | 49,760 | 72,980 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 380 | 48 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **AUDUSD** | 49,760 | 72,979 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 381 | 48 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **CADCHF** | 0 | 5,140 | 2025-11-25 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **CADJPY** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **CHFJPY** | 49,747 | 72,966 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 380 | 48 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURAUD** | 49,758 | 72,977 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 381 | 48 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURCAD** | 49,759 | 72,979 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 380 | 49 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURCHF** | 49,468 | 72,688 | 2015-01-19 | 2022-12-30 | 2026-09-23 | 377 | 51 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURGBP** | 49,760 | 72,979 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 382 | 47 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURHKD** | 8,489 | 8,489 | 2015-01-02 | 2017-03-15 | 2017-03-15 | 53 | 35 | 6,109h (2015-02-27 → 2015-11-09) | truncated pre-2023 span |
| **EURHUF** | 10,088 | 10,088 | 2015-01-02 | 2016-08-24 | 2016-08-24 | 31 | 123 | 77h (2015-12-31 → 2016-01-04) | truncated pre-2023 span |
| **EURJPY** | 49,759 | 72,978 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 382 | 47 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURMXN** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **EURNOK** | 10,160 | 10,160 | 2015-01-01 | 2016-08-24 | 2016-08-24 | 31 | 62 | 77h (2015-12-31 → 2016-01-04) | truncated pre-2023 span |
| **EURNZD** | 49,741 | 72,961 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 380 | 53 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURPLN** | 10,152 | 10,152 | 2015-01-01 | 2016-08-24 | 2016-08-24 | 31 | 72 | 77h (2015-12-31 → 2016-01-04) | truncated pre-2023 span |
| **EURSEK** | 10,221 | 10,221 | 2015-01-01 | 2016-08-24 | 2016-08-24 | 31 | 58 | 77h (2015-12-31 → 2016-01-04) | truncated pre-2023 span |
| **EURTRY** | 9,924 | 9,924 | 2015-01-02 | 2016-08-24 | 2016-08-24 | 73 | 17 | 331h (2015-06-05 → 2015-06-19) | truncated pre-2023 span |
| **EURUSD** | 49,761 | 72,967 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 385 | 47 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **EURZAR** | 0 | 4,279 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **GBPAUD** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **GBPCAD** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **GBPCHF** | 49,749 | 72,969 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 382 | 47 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **GBPJPY** | 0 | 5,097 | 2025-11-25 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **GBPMXN** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **GBPNZD** | 0 | 5,133 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **GBPUSD** | 49,740 | 72,959 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 383 | 48 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **GBPZAR** | 0 | 4,279 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **NZDCAD** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **NZDCHF** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **NZDJPY** | 0 | 5,134 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **NZDUSD** | 49,699 | 72,916 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 380 | 50 | 106h (2017-05-10 → 2017-05-15) | 2015–2022 span |
| **SGDJPY** | 10,214 | 10,214 | 2015-01-02 | 2016-08-24 | 2016-08-24 | 77 | 12 | 78h (2015-12-24 → 2015-12-28) | truncated pre-2023 span |
| **USDCAD** | 49,760 | 72,979 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 381 | 48 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **USDCHF** | 49,734 | 72,953 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 381 | 42 | 82h (2017-12-22 → 2017-12-26) | 2015–2022 span |
| **USDCNH** | 4,401 | 4,401 | 2015-11-17 | 2016-09-19 | 2016-09-19 | 12 | 132 | 411h (2016-08-30 → 2016-09-16) | truncated pre-2023 span |
| **USDCZK** | 10,167 | 10,167 | 2015-01-02 | 2016-08-24 | 2016-08-24 | 19 | 71 | 76h (2015-12-24 → 2015-12-27) | truncated pre-2023 span |
| **USDDKK** | 10,218 | 10,218 | 2015-01-02 | 2016-08-24 | 2016-08-24 | 78 | 8 | 78h (2015-12-24 → 2015-12-28) | truncated pre-2023 span |
| **USDHKD** | 14,010 | 32,797 | 2015-01-02 | 2022-10-14 | 2026-09-23 | 65 | 78 | 48,329h (2017-03-24 → 2022-09-28) | truncated pre-2023 span |
| **USDHUF** | 10,179 | 10,179 | 2015-01-01 | 2016-08-24 | 2016-08-24 | 31 | 59 | 77h (2015-12-31 → 2016-01-04) | truncated pre-2023 span |
| **USDJPY** | 49,761 | 72,900 | 2015-01-02 | 2022-12-30 | 2026-09-23 | 382 | 47 | 82h (2017-12-29 → 2018-01-02) | 2015–2022 span |
| **USDMXN** | 0 | 5,125 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |
| **USDNOK** | 10,218 | 10,218 | 2015-01-02 | 2016-08-24 | 2016-08-24 | 78 | 8 | 78h (2015-12-24 → 2015-12-28) | truncated pre-2023 span |
| **USDPLN** | 10,169 | 10,169 | 2015-01-01 | 2016-08-24 | 2016-08-24 | 31 | 60 | 77h (2015-12-31 → 2016-01-04) | truncated pre-2023 span |
| **USDSEK** | 10,511 | 29,298 | 2015-01-02 | 2022-10-14 | 2026-09-23 | 78 | 13 | 53,423h (2016-08-24 → 2022-09-28) | truncated pre-2023 span |
| **USDSGD** | 10,516 | 29,303 | 2015-01-02 | 2022-10-14 | 2026-09-23 | 80 | 9 | 53,422h (2016-08-24 → 2022-09-28) | truncated pre-2023 span |
| **USDTRY** | 10,174 | 10,174 | 2015-01-02 | 2016-08-24 | 2016-08-24 | 77 | 12 | 91h (2015-05-08 → 2015-05-12) | truncated pre-2023 span |
| **USDZAR** | 0 | 4,279 | 2025-11-26 | none | 2026-09-23 | 0 | 0 | none | zero pre-2023 H1 bars |

### Major Pair Timestamp Coverage Summary (Mutually Exclusive Partition)
For each distinct timestamp package relevant to the pair:
1. **Entry Boundary Status**: Mutually exclusive categorization at $T_{\text{entry}}$ into `OPEN_MARKET`, `WEEKEND_BLOCKED`, `WEEKDAY_GAP`, or `MISSING_HISTORY`.
2. **Pre-Entry 14 History**: Mutually exclusive breakdown for open market entries into `CLEAN_14`, `MISSING_HISTORY`, `WEEKDAY_GAP`, or `MISSING_H1_BARS`.
3. **Candidate Holding Horizons**: 6, 12, 30, 42, and 60 H4 periods evaluated strictly for `CLEAN_14` episodes.

| Pair | Evaluated Packages | Open Entry | Weekend Blocked | Weekday Gap Blocked | Missing History | 14 H4 Clean Pre-Entry | 6 H4 Clean | 12 H4 Clean | 30 H4 Clean | 42 H4 Clean | 60 H4 Clean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **EURUSD** | 19,033 | 17,892 | 1,068 | 72 | 1 | 17,014 | 16,774 | 16,319 | 15,706 | 15,289 | 14,737 |
| **USDJPY** | 12,298 | 11,249 | 973 | 75 | 1 | 10,678 | 10,511 | 10,198 | 9,797 | 9,511 | 9,157 |
| **GBPUSD** | 11,551 | 10,504 | 968 | 78 | 1 | 9,986 | 9,844 | 9,531 | 9,138 | 8,858 | 8,508 |
| **AUDUSD** | 11,261 | 10,236 | 956 | 68 | 1 | 9,678 | 9,555 | 9,258 | 8,879 | 8,614 | 8,259 |
| **USDCAD** | 9,913 | 8,873 | 960 | 79 | 1 | 8,423 | 8,314 | 8,053 | 7,717 | 7,478 | 7,184 |
| **USDCHF** | 10,157 | 9,124 | 959 | 73 | 1 | 8,689 | 8,578 | 8,279 | 7,910 | 7,647 | 7,329 |
| **NZDUSD** | 10,651 | 9,600 | 965 | 85 | 1 | 9,077 | 8,956 | 8,662 | 8,274 | 8,007 | 7,653 |

### Boundary & Gap Disqualifications Across Holding Horizons (EURUSD Partition)
Holding horizon outcomes sum strictly to `eligiblePreEntry14` (17,014 episodes):

| Metric (EURUSD, Eligible Pre-Entry 14 = 17,014) | 6 H4 | 12 H4 | 30 H4 | 42 H4 | 60 H4 |
|---|---:|---:|---:|---:|---:|
| **Clean Complete Paths** | 16,774 | 16,319 | 15,706 | 15,289 | 14,737 |
| **2023 Boundary Exclusions** | 3 | 10 | 19 | 33 | 50 |
| **Weekday Gap Disqualifications** | 17 | 62 | 103 | 141 | 191 |
| **Missing H1 Bar Disqualifications** | 220 | 623 | 1,186 | 1,551 | 2,036 |
| **Sum (Invariant Verification)** | 17,014 | 17,014 | 17,014 | 17,014 | 17,014 |

---

## 5. Exact-Series × Pair Eligibility Matrix (Marginal vs. Joint Intersections)

To prevent sample count multiplication and spurious setup counts, eligibility is reported at the individual **exact-series × currency-relevant pair** intersection. Each cell captures:
- **Distinct Pkgs**: Total distinct timestamp packages containing the exact series evaluated on the pair.
- **Marginal Inputs**: Packages where the series has complete Actual, Forecast, and Previous values ($A \ne \emptyset, F \ne \emptyset, P \ne \emptyset$).
- **Marginal Clean 6H4**: Packages where the instrument path is clean across 6 H4 periods, regardless of input completeness.
- **Joint Complete & Clean Pre-14**: Packages where the series has complete inputs **AND** the pair has clean 14 pre-entry periods on the **SAME** package.
- **Joint Complete & Clean Paths (6 to 60 H4)**: Packages where the series has complete inputs **AND** the pair has contiguous completed H4 holding blocks on the **SAME** package.

### Candidate Exact Series × Benchmark Pair Eligibility Matrix
The table below presents candidate series satisfying input completeness ($N \ge 20$, Complete A/F/P $\ge 80\%$) as well as benchmark indicators across macroeconomic families, audited against their primary FX benchmark pairs.

| Series Key | Indicator Label | Family | Pair | Distinct Pkgs | Marginal Inputs | Marginal Clean 6H4 | Joint Pre-14 | Joint 6H4 | Joint 12H4 | Joint 30H4 | Joint 42H4 | Joint 60H4 | Years | Collisions (%) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `USD:US:840200003:r0` | EIA Crude Oil Imports Chan | International Trade | **EURUSD** | 363 | 280 (77%) | 357 | 278 | 278 | 273 | 248 | 246 | 233 | 2016–2022 | 16 (4%) |
| `USD:US:840020015:r0` | Housing Starts m/m | Housing / Construction | **EURUSD** | 84 | 68 (81%) | 82 | 67 | 66 | 65 | 60 | 57 | 54 | 2016–2022 | 57 (68%) |
| `USD:US:840020016:r0` | Building Permits m/m | Housing / Construction | **EURUSD** | 84 | 68 (81%) | 82 | 67 | 66 | 65 | 60 | 57 | 54 | 2016–2022 | 61 (73%) |
| `USD:US:840020006:r3` | Wholesale Inventories m/m | Unclassified | **EURUSD** | 64 | 64 (100%) | 63 | 63 | 63 | 63 | 61 | 59 | 59 | 2017–2022 | 11 (17%) |
| `USD:US:840020006:r1` | Wholesale Inventories m/m | Unclassified | **EURUSD** | 66 | 61 (92%) | 63 | 60 | 59 | 55 | 50 | 49 | 48 | 2017–2022 | 25 (38%) |
| `USD:US:840150001:r0` | Federal Budget Balance | Government / Fiscal | **EURUSD** | 96 | 68 (71%) | 78 | 56 | 56 | 54 | 52 | 52 | 48 | 2015–2022 | 2 (2%) |
| `GBP:GB:826020017:r0` | BoE M4 Money Supply m/m | Unclassified | **GBPUSD** | 72 | 65 (90%) | 60 | 57 | 54 | 53 | 50 | 50 | 47 | 2017–2022 | 1 (1%) |
| `GBP:GB:826020018:r0` | BoE Mortgage Approvals | Housing / Construction | **GBPUSD** | 72 | 65 (90%) | 60 | 57 | 54 | 53 | 50 | 50 | 47 | 2017–2022 | 1 (1%) |
| `USD:US:840030031:r0` | Import Price Index excl. P | Inflation | **EURUSD** | 60 | 50 (83%) | 58 | 49 | 48 | 47 | 46 | 45 | 42 | 2018–2022 | 37 (62%) |
| `USD:US:840020022:r1` | Nondefense Capital Goods S | Unclassified | **EURUSD** | 59 | 50 (85%) | 56 | 48 | 48 | 43 | 39 | 37 | 37 | 2018–2022 | 24 (41%) |
| `USD:US:840020022:r3` | Nondefense Capital Goods S | Unclassified | **EURUSD** | 59 | 50 (85%) | 56 | 47 | 47 | 46 | 45 | 42 | 42 | 2018–2022 | 9 (15%) |
| `EUR:FR:250010002:r3` | CPI y/y | Inflation | **EURUSD** | 57 | 49 (86%) | 54 | 47 | 46 | 45 | 45 | 44 | 41 | 2018–2022 | 0 (0%) |
| `EUR:DE:276010005:r0` | Export Price Index m/m | Inflation | **EURUSD** | 59 | 50 (85%) | 53 | 46 | 45 | 42 | 39 | 39 | 39 | 2018–2022 | 14 (24%) |
| `EUR:DE:276010006:r0` | Export Price Index y/y | Inflation | **EURUSD** | 59 | 50 (85%) | 53 | 46 | 45 | 42 | 39 | 39 | 39 | 2018–2022 | 14 (24%) |
| `EUR:ES:724500002:r0` | S&P Global Services PMI | Business Surveys / PMI | **EURUSD** | 46 | 46 (100%) | 45 | 46 | 45 | 44 | 44 | 43 | 40 | 2019–2022 | 0 (0%) |
| `EUR:IT:380500002:r0` | S&P Global Services PMI | Business Surveys / PMI | **EURUSD** | 46 | 46 (100%) | 45 | 46 | 45 | 44 | 44 | 43 | 40 | 2019–2022 | 2 (4%) |
| `EUR:ES:724010001:r1` | CPI m/m | Inflation | **EURUSD** | 53 | 48 (91%) | 48 | 46 | 44 | 39 | 38 | 38 | 37 | 2018–2022 | 26 (49%) |
| `EUR:ES:724010002:r1` | CPI y/y | Inflation | **EURUSD** | 53 | 48 (91%) | 48 | 46 | 44 | 39 | 38 | 38 | 37 | 2018–2022 | 27 (51%) |
| `EUR:ES:724010003:r1` | HICP m/m | Inflation | **EURUSD** | 53 | 48 (91%) | 48 | 46 | 44 | 39 | 38 | 38 | 37 | 2018–2022 | 26 (49%) |
| `EUR:FR:250010002:r1` | CPI y/y | Inflation | **EURUSD** | 57 | 49 (86%) | 50 | 46 | 42 | 41 | 41 | 41 | 41 | 2018–2022 | 0 (0%) |
| `EUR:ES:724500001:r0` | S&P Global Manufacturing P | Business Surveys / PMI | **EURUSD** | 46 | 46 (100%) | 40 | 40 | 40 | 40 | 39 | 39 | 36 | 2019–2022 | 1 (2%) |
| `EUR:IT:380500001:r0` | S&P Global Manufacturing P | Business Surveys / PMI | **EURUSD** | 46 | 46 (100%) | 40 | 40 | 40 | 40 | 39 | 39 | 36 | 2019–2022 | 0 (0%) |
| `USD:US:840050026:r0` | Fed Industrial Production  | Production / Activity | **EURUSD** | 58 | 42 (72%) | 54 | 40 | 40 | 39 | 39 | 37 | 34 | 2018–2022 | 1 (2%) |
| `JPY:JP:392500002:r1` | au Jibun Bank Services PMI | Business Surveys / PMI | **USDJPY** | 42 | 42 (100%) | 39 | 40 | 39 | 38 | 37 | 34 | 33 | 2019–2022 | 5 (12%) |
| `AUD:AU:36500001:r1` | S&P Global Manufacturing P | Business Surveys / PMI | **AUDUSD** | 49 | 41 (84%) | 45 | 39 | 38 | 37 | 36 | 33 | 32 | 2018–2022 | 0 (0%) |
| `AUD:AU:36500002:r1` | S&P Global Services PMI | Business Surveys / PMI | **AUDUSD** | 49 | 41 (84%) | 45 | 39 | 38 | 37 | 36 | 33 | 32 | 2018–2022 | 0 (0%) |
| `JPY:JP:392500002:r3` | au Jibun Bank Services PMI | Business Surveys / PMI | **USDJPY** | 41 | 41 (100%) | 38 | 39 | 38 | 37 | 37 | 36 | 34 | 2019–2022 | 19 (46%) |
| `GBP:GB:826010039:r0` | GDP m/m | National Accounts / Growth | **GBPUSD** | 39 | 39 (100%) | 37 | 39 | 37 | 37 | 36 | 36 | 36 | 2019–2022 | 20 (51%) |
| `EUR:EU:999030010:r3` | Core CPI m/m | Inflation | **EURUSD** | 37 | 37 (100%) | 37 | 37 | 37 | 36 | 33 | 31 | 29 | 2019–2022 | 2 (5%) |
| `EUR:EU:999030011:r3` | CPI m/m | Inflation | **EURUSD** | 37 | 37 (100%) | 37 | 37 | 37 | 36 | 33 | 31 | 29 | 2019–2022 | 2 (5%) |
| `EUR:EU:999030024:r3` | CPI excl. Energy and Unpro | Inflation | **EURUSD** | 37 | 37 (100%) | 37 | 37 | 37 | 36 | 33 | 31 | 29 | 2019–2022 | 2 (5%) |
| `GBP:GB:826500002:r3` | S&P Global/CIPS Services P | Business Surveys / PMI | **GBPUSD** | 37 | 37 (100%) | 37 | 37 | 37 | 36 | 35 | 34 | 32 | 2019–2022 | 6 (16%) |
| `GBP:GB:826500001:r1` | S&P Global/CIPS Manufactur | Business Surveys / PMI | **GBPUSD** | 38 | 38 (100%) | 36 | 37 | 36 | 35 | 33 | 30 | 30 | 2019–2022 | 1 (3%) |
| `GBP:GB:826500002:r1` | S&P Global/CIPS Services P | Business Surveys / PMI | **GBPUSD** | 38 | 38 (100%) | 36 | 37 | 36 | 35 | 33 | 30 | 30 | 2019–2022 | 1 (3%) |
| `AUD:AU:36500002:r3` | S&P Global Services PMI | Business Surveys / PMI | **AUDUSD** | 48 | 40 (83%) | 41 | 35 | 35 | 34 | 33 | 32 | 30 | 2019–2022 | 4 (8%) |
| `AUD:AU:36500001:r3` | S&P Global Manufacturing P | Business Surveys / PMI | **AUDUSD** | 48 | 40 (83%) | 39 | 34 | 33 | 33 | 32 | 32 | 29 | 2019–2022 | 0 (0%) |
| `EUR:EU:999030010:r1` | Core CPI m/m | Inflation | **EURUSD** | 37 | 37 (100%) | 33 | 35 | 33 | 33 | 33 | 33 | 30 | 2019–2022 | 1 (3%) |
| `EUR:EU:999030011:r1` | CPI m/m | Inflation | **EURUSD** | 37 | 37 (100%) | 33 | 35 | 33 | 33 | 33 | 33 | 30 | 2019–2022 | 1 (3%) |
| `EUR:EU:999030024:r1` | CPI excl. Energy and Unpro | Inflation | **EURUSD** | 37 | 37 (100%) | 33 | 35 | 33 | 33 | 33 | 33 | 30 | 2019–2022 | 1 (3%) |
| `GBP:GB:826500001:r3` | S&P Global/CIPS Manufactur | Business Surveys / PMI | **GBPUSD** | 37 | 37 (100%) | 32 | 32 | 32 | 32 | 32 | 32 | 29 | 2019–2022 | 0 (0%) |
| `EUR:EU:999030016:r2` | GDP q/q | National Accounts / Growth | **EURUSD** | 27 | 23 (85%) | 27 | 23 | 23 | 23 | 23 | 23 | 23 | 2016–2022 | 4 (15%) |
| `EUR:EU:999030017:r2` | GDP y/y | National Accounts / Growth | **EURUSD** | 27 | 23 (85%) | 27 | 23 | 23 | 23 | 23 | 23 | 23 | 2016–2022 | 4 (15%) |
| `AUD:AU:36010012:r3` | Retail Sales m/m | Consumer / Retail | **AUDUSD** | 26 | 25 (96%) | 23 | 23 | 22 | 22 | 22 | 21 | 20 | 2020–2022 | 3 (12%) |
| `EUR:EU:999030009:r0` | Labour Cost Index | Labor / Employment | **EURUSD** | 32 | 23 (72%) | 26 | 21 | 19 | 18 | 17 | 14 | 13 | 2015–2022 | 1 (3%) |
| `EUR:FR:250010006:r3` | GDP y/y | National Accounts / Growth | **EURUSD** | 20 | 17 (85%) | 18 | 16 | 16 | 15 | 15 | 15 | 15 | 2018–2022 | 1 (5%) |
| `GBP:GB:826020009:r0` | BoE Interest Rate Decision | Central Bank / Rates | **GBPUSD** | 73 | 5 (7%) | 72 | 5 | 5 | 4 | 4 | 3 | 3 | 2015–2022 | 6 (8%) |

*Complete Tabular Matrix*: The full 14,684 series × pair universe has been emitted to `lab/research/fms_series_pair_eligibility.csv` and preserved in `lab/research/fms_eligibility_inventory.json`.

---

## 6. Dynamic Overlap with Later Scheduled Releases

Holding an FX position across multi-day H4 horizons inevitably exposes the position to subsequent scheduled macroeconomic releases in the pair's base and quote currencies. All statistics below are **empirically derived from the generated ledger** with explicit denominators (clean complete holding episodes) and units:

### Later Release Exposure across Clean Complete Paths (EURUSD)
Base Currency: **EUR** | Quote Currency: **USD**

| Horizon | Denominator (Clean Episodes) | Episodes with Base Overlap | Episodes with Quote Overlap | Episodes with Pair Overlap (%) | Later Release Rows Median [IQR] | Later Timestamp Packages Median [IQR] |
|---|---:|---:|---:|---:|---|---|
| **6 H4** | 16,774 | 16,627 (99.1%) | 16,414 (97.9%) | **16,772 (100.0%)** | 24 [17–32] | 9 [7–11] |
| **12 H4** | 16,319 | 16,318 (100.0%) | 16,269 (99.7%) | **16,319 (100.0%)** | 49 [38–61] | 18 [15–22] |
| **30 H4** | 15,706 | 15,706 (100.0%) | 15,706 (100.0%) | **15,706 (100.0%)** | 122 [104–140] | 46 [40–53] |
| **42 H4** | 15,289 | 15,289 (100.0%) | 15,289 (100.0%) | **15,289 (100.0%)** | 172 [149–193] | 65 [56–73] |
| **60 H4** | 14,737 | 14,737 (100.0%) | 14,737 (100.0%) | **14,737 (100.0%)** | 246 [221–271] | 92 [82–102] |

### Later Release Exposure across Clean Complete Paths (USDJPY)
Base Currency: **USD** | Quote Currency: **JPY**

| Horizon | Denominator (Clean Episodes) | Episodes with Base Overlap | Episodes with Quote Overlap | Episodes with Pair Overlap (%) | Later Release Rows Median [IQR] | Later Timestamp Packages Median [IQR] |
|---|---:|---:|---:|---:|---|---|
| **6 H4** | 10,511 | 10,306 (98.0%) | 9,481 (90.2%) | **10,487 (99.8%)** | 17 [12–23] | 6 [4–7] |
| **12 H4** | 10,198 | 10,171 (99.7%) | 10,083 (98.9%) | **10,198 (100.0%)** | 36 [28–44] | 12 [10–14] |
| **30 H4** | 9,797 | 9,797 (100.0%) | 9,797 (100.0%) | **9,797 (100.0%)** | 89 [77–100] | 29 [26–33] |
| **42 H4** | 9,511 | 9,511 (100.0%) | 9,511 (100.0%) | **9,511 (100.0%)** | 126 [111–140] | 41 [37–46] |
| **60 H4** | 9,157 | 9,157 (100.0%) | 9,157 (100.0%) | **9,157 (100.0%)** | 178 [161–192] | 58 [54–64] |

*Forensic Conclusion*: At **6 H4** (~24 hours), 100.0% of EURUSD clean holding episodes encounter subsequent scheduled releases in EUR or USD. At **42–60 H4** (~7–10 trading days), **100.0–100.0% of episodes** encounter multiple subsequent releases (median of 172–246 subsequent release rows across 65–92 distinct release timestamp packages). Long-horizon post-release price movement cannot be attributed purely to the initial announcement shock.

---

## 7. What Was Verified vs. What Remains Uncertain

### Verified Facts
1. **Source Integrity**: Export `FyodorResearchExport_v3_20260923_234930_server` verified against manifest `manifest.csv`; calendar SHA-256 matches pinned protocol hash `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` bit-for-bit.
2. **Candle Checksums**: All 51 candle CSV files independently hashed; 19 pairs possess full 2015–2022 span; 17 pairs possess truncated pre-2023 history; 15 pairs have zero pre-2023 H1 bars.
3. **Temporal Partitioning**: Split strictly enforced at `2023-01-01 00:00:00` (`1672531200`). No 2023+ price, return, or event was computed.
4. **Episode Deduplication**: 82,813 pre-2023 releases collapse into 30,015 distinct timestamp packages.
5. **Exact Series Isolation**: Primary keys `currency:country:event_id:revision` prevent pooling across countries or revision stages.
6. **Joint Series × Pair Eligibility**: Evaluated strictly on the SAME package, asserting joint $le$ marginal bounds and horizon monotonicity across all 14,684 combinations.
7. **Aggregate Invariants**: Entry statuses, pre-entry histories, and holding horizon outcomes satisfy strict sum-to-parent invariants across all 51 pairs.

### Persistent Uncertainties
1. **Historical Broker DST & Timezone**: Snapshot offset is +03:00, but historical daylight saving transitions are unmanifested.
2. **Calendar Vintage & Point-in-Time Availability**: Retrospective export does not prove whether consensus forecasts or preliminary revisions were visible to market participants at the announcement timestamp.
3. **Execution Realism**: H1-derived H4 coverage proves candle timestamp presence only; it does not establish Bid/Ask spreads, announcement slippage, or intrabar price path ordering.

---

## 8. Audit Stop Gate

> [!CAUTION]
> **DIRECTOR AUDIT STOP GATE**  
> In strict compliance with the protocol and Chief of Staff mandate:
> - No recipe has been chosen.
> - No strategy backtest has been performed.
> - No historical performance metric has been computed or used as a tie-breaker.
> 
> **STOP HERE.** The Project Director is requested to inspect this inventory and bring it back to Codex for quant audit before any setup or recipe is selected.
