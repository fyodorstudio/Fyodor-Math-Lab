# Fyodor Math Lab: Macro Research

A clean, reproducible, research-only environment for empirical macroeconomic event studies on foreign exchange spot markets.

---

## 1. Project Identity & Purpose

This repository investigates macro-event patterns in H1 FX prices. Its practical objective is a precisely defined entry, stop, target, and expiry whose historical target-before-stop frequency and reward-to-risk justify a frozen demo-account forward test. A historical pattern is not a guarantee of future profit.

- **No Web Application**: Legacy H1 web applications, interactive dashboards, and UI servers are deliberately excluded.
- **Price-Blind Feasibility First**: Check source integrity, calendar definitions, and H1 coverage before inspecting a candidate's prices.
- **Discovery Is Allowed**: Explore entry times, stop/target zones, and other patterns on designated discovery data. Record the full search, then freeze a selected rule before assessing later data. Discovery performance is not independent validation.
- **Gross Price-Path Focus**: Historical target-before-stop odds, reward-to-risk, and price-path geometry are the research target. Broker spread, slippage, commissions, and financing are outside the primary historical screen; the owner will assess those separately before any real-money decision. Do not label gross results executable net profit.
- **Maintained Research Roadmap**: The active staged sequence, holdout audit policies, and parked research hypotheses are maintained in [`docs/RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RESEARCH_ROADMAP.md). Zero registered setups or profitability evidence currently exist.

---

## 2. Governance & Research Directives

1. **Strict Chronological Boundary (`1672531200`)**:
   - The historical discovery period ends strictly at `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).
   - All observations on or after `1672531200` remain strictly sealed as a future holdout. Candle timestamps on or after this boundary are never evaluated during discovery.
2. **Candle Inspection Policy & Audit Disclosure**:
   - **Prior Inspection Disclosure**: During initial schema verification, lines 1–5 of `candles_EURUSD_H1.csv` were inspected via tool to verify column headers and confirm that column 0 corresponds to `time`.
   - **Candidate-Specific Boundary**: Archived Phase 1, Ifo, and Retail Sales trials did calculate historical price outcomes. The active ISM candidate has not yet had its price outcomes calculated; its pre-price inventory uses timestamps only. Full-file integrity hashing reads opaque bytes, not interpreted returns.
   - A designated discovery search may inspect pre-2023 H1 OHLC after its scope and output accounting are recorded. The post-2022 holdout remains separate until a selected rule is locked and authorized for validation.
3. **Data Integrity Covenant**:
   - Zero synthetic, mock, or pseudo-random data is used for empirical analysis.
   - Every metric, count, and sign is deterministically computed from verified raw source files on disk.
4. **Disclosure of Prior Trials**:
   - **Phase 1 Exploration**: Narrow exploratory tests on USD CPI and NFP (`evidence/trials/phase1/`).
   - **German Ifo Pilot**: Conducted on EURUSD under protocol v1.2 (`evidence/trials/ifo/`). Concluded with **State 3: No Convincing Evidence** ($p = 0.9575$, $\Delta \bar{R} = -21.31\text{ bps}$). The pilot is archived as immutable evidence; pre-2023 history cannot be treated as an independent confirmation sample.
5. **No Presumption of Tradability**:
   - A high-impact macro release does not imply a tradable post-announcement drift. Immediate asset repricing often absorbs macro shocks within the announcement bar.

---

## 3. Directory Roles & Classification

| Directory | Classification | Role & Retention Policy |
|---|---|---|
| `docs/` | **Active Guidance** | Current maintained documentation, research roadmap ([`docs/RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RESEARCH_ROADMAP.md)), protocol drafts, and feasibility ledgers. |
| `src/` | **Active Guidance** | Clean Python research modules for parsing, reconciliation, and audit. |
| `tests/` | **Active Guidance** | Synthetic unit tests for parsers, joins, boundaries, and reconciliation. |
| `data/pinned/` | **Pinned Data** | Immutable MT5 v3.1 export (`fyodor-mt5-research-export/3.1.0`). Ignored by Git. |
| `evidence/` | **Immutable Evidence** | Cryptographically verified records: prior inventory, Phase 1, and German Ifo pilot records. Treated as read-only audit reference. Large ledger (`fms_episodes.jsonl`) is ignored by Git. |
| `reference/` | **Historical Reference** | Historical planning notes, candidate selection charter, exporter MQL5 source, and quantitative audit notes. Contains historical paths; does not represent active policy. |
| `scratch/` | **Disposable Scratch** | Transient calculation scripts and temporary artifacts. Ignored by Git. |

---

## 4. Cryptographic Provenance & Verification Hashes

All source inputs are verified against byte-for-byte SHA-256 digests:

| File / Component | Path | SHA-256 Hash |
|---|---|---|
| **Raw Calendar Releases** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv` | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` |
| **Raw Calendar Events** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_events.csv` | `e08d2df96e83fdefa1c56d33316ee09178fe75aff1f3325d6f4ec4c80a4b7f13` |
| **Export Manifest** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/manifest.csv` | `8815cb64cbc5d8efe5c552adcb27b7059e7b33f6a2094eceb287b7a29d013d66` |
| **Candle Symbols List** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candle_symbols.csv` | `3b067061adbb6e941be26006f9451e853a91cd622479e78387b32102a43755b1` |
| **EURUSD H1 Candles** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv` | `893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5` |
| **FMS Episode Ledger** | `evidence/inventory/fms_episodes.jsonl` | `37df7880a2bc36dbbce06b4a6ba39f7bd962a4c1c92eb2ce64cb71a886de55d2` |
| **Ifo Pilot Ledger JSON** | `evidence/trials/ifo/ifo_pilot_ledger.json` | `324b99a1f2ac9ebe73b5102d35208cc32a7e2eb7eb9cc69480b3feae710ff658` |
| **Ifo Pilot Ledger MD** | `evidence/trials/ifo/ifo_pilot_ledger.md` | `e2e3a6c19bbfadfd1bef151861bcba3a3e5066836e3dfc28835e28a616ef72c8` |
| **Ifo Report JSON** | `evidence/trials/ifo/ifo_pre2023_exploration_report.json` | `651799af78db111f7cc65e7fff7894877a9ea58a36a889cce649f5f848aede16` |
| **Ifo Report MD** | `evidence/trials/ifo/ifo_pre2023_exploration_report.md` | `2bad548e181b5ba8cf0df4c60e16d0904947aa2de41f2cb45008a6b10d963c79` |

---

## 5. Running the Research Suite & Tests

To execute the test suite:

```bash
python -m unittest discover tests
```

To run the independent reconciliation and package ledger generation:

```bash
python -m src.package_ledger
```
