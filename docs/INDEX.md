# Documentation Index & Artifact Classification

This repository maintains a strict classification between active guidance, immutable historical evidence, historical reference, pinned raw data, and disposable scratch artifacts.

---

## 1. Active Guidance (Current Policy & Draft Protocols)

These documents define current research boundaries, protocols under active review, and active implementation code.

- [`README.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/README.md): Repository entrance, governance rules, directory classification, and provenance manifest.
- [`docs/INDEX.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/INDEX.md): This classification index.
- [`docs/RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RESEARCH_ROADMAP.md): Active maintained macro research roadmap, decision sequence, and parked state-signature and price-zone questions.
- [`docs/ISM_PMI_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/ISM_PMI_FEASIBILITY.md): Comprehensive price-blind feasibility investigation and pre-price architecture design for US ISM Manufacturing PMI (`USD:US:840040001:r0`) on EURUSD.
- [`docs/NEXT_FAMILY_PRICE_BLIND_SHORTLIST.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/NEXT_FAMILY_PRICE_BLIND_SHORTLIST.md): Price-blind data suitability evaluation of US GDP vs US ISM Manufacturing PMI; ranks ISM conditionally suitable ($N=67$) and parks GDP due to unpooled sample deficiency ($N=22$).
- [`docs/RETAIL_SALES_FEASIBILITY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FEASIBILITY.md): Historical price-blind feasibility investigation of US Retail Sales m/m (`USD:US:840020010:r0`) and Core Retail Sales m/m (`USD:US:840020011:r0`) on EURUSD.
- [`docs/DRAFT_RETAIL_SALES_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/DRAFT_RETAIL_SALES_PROTOCOL.md): Pre-price design protocol v0.5 for US Retail Sales (executed and concluded).
- [`docs/RETAIL_SALES_FREEZE_PACKET.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_FREEZE_PACKET.md): Pre-price research freeze record anchoring the 6-H4 rule, 49 strict packages, and decision gates (authorized for pre-2023 discovery only).
- [`src/`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/src/): Core Python research modules (parsers, calendar reconciliation, candle coverage, package ledger, calculation runner).
- [`tests/`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/tests/): Focused synthetic unit tests covering parser edge cases, timestamp boundary enforcement, package joins, and count reconciliation.

---

## 2. Immutable Evidence (Frozen Audits & Previous Trials)

These files are preserved byte-for-byte from previous research phases. They serve as audit trails and negative evidence; they are never rewritten, revived, or executed as live code.

### A. Pre-Price Eligibility Inventory
- [`evidence/inventory/FMS_ELIGIBILITY_INVENTORY.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/inventory/FMS_ELIGIBILITY_INVENTORY.md): Executive summary of the initial timestamp-only eligibility inventory across all 1,172 series.
- [`evidence/inventory/fms_series_pair_eligibility.csv`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/inventory/fms_series_pair_eligibility.csv): Tabular series-pair eligibility metrics across 51 forex pairs.
- [`evidence/inventory/fms_eligibility_inventory.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/inventory/fms_eligibility_inventory.json): Machine-readable inventory summary.
- [`evidence/inventory/fms_episodes.jsonl`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/inventory/fms_episodes.jsonl): 844 MB episode-level ledger containing all 30,015 pre-2023 macro packages and pair coverage (Git-ignored).

### B. German Ifo EURUSD Pilot (Failed Trial)
- [`evidence/trials/ifo/FMS_PILOT_IFO_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/FMS_PILOT_IFO_PROTOCOL.md): Protocol v1.2 under which the pilot was executed.
- [`evidence/trials/ifo/ifo_pre2023_exploration_report.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/ifo_pre2023_exploration_report.md): Formal exploration report confirming **State 3: No Convincing Evidence** ($p = 0.9575$, $\Delta \bar{R} = -21.31\text{ bps}$).
- [`evidence/trials/ifo/ifo_pre2023_exploration_report.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/ifo_pre2023_exploration_report.json): Machine-readable Ifo outcome report.
- [`evidence/trials/ifo/ifo_pilot_ledger.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/ifo_pilot_ledger.md) & [`.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/ifo_pilot_ledger.json): Episode-level event and control ledger for the Ifo pilot.
- [`evidence/trials/ifo/code-snapshot/`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/ifo/code-snapshot/): Code snapshot of the Ifo exploration runner and aggregator, retained strictly for audit reproducibility.

### C. Phase 1 Historical Exploration
- [`evidence/trials/phase1/PHASE1_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/phase1/PHASE1_PROTOCOL.md): Protocol governing initial exploratory tests.
- [`evidence/trials/phase1/PHASE1_EXPLORATION.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/phase1/PHASE1_EXPLORATION.md): Outcome record of narrow exploratory tests on USD CPI and NFP.
- [`evidence/trials/phase1/phase1_exploration.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/phase1/phase1_exploration.json) & [`phase1_preflight.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/phase1/phase1_preflight.json): Machine-readable Phase 1 artifacts.

### D. US Retail Sales EURUSD Discovery Trial (Disconfirmed / Closed)
- [`docs/RETAIL_SALES_CLOSURE_NOTE.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/docs/RETAIL_SALES_CLOSURE_NOTE.md): Formal forensic audit and closure note recording trial disconfirmation, negative zero-cost mean, primary 6-H4 subgroup reconciliation, and permanent sealing of the 2023+ holdout.
- [`evidence/trials/retail_sales/retail_sales_pre2023_discovery.json`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/evidence/trials/retail_sales/retail_sales_pre2023_discovery.json): Complete, immutable raw JSON execution record of the pre-2023 unblinded discovery calculation across 49 strict-concordance packages (`SHA-256 = 125aa3cf...`).


---

## 3. Historical Reference (Non-Active Context)

These documents contain historical research notes, exporter source code, and early audits. They reference legacy paths and older file structures; they do not dictate current policy.

- [`reference/audit-history/CODEX_QUANT_AUDIT.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/audit-history/CODEX_QUANT_AUDIT.md): Quantitative audit of the legacy laboratory and MT5 v3.1 migration verification.
- [`reference/exporter/FyodorResearchExporterV3.mq5`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/exporter/FyodorResearchExporterV3.mq5) & [`README.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/exporter/README.md): MQL5 source script that generated the pinned export.
- [`reference/planning-history/research note.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/planning-history/research%20note.md): Initial roadmap formulation and milestone planning notes.
- [`reference/planning-history/FMS_RESEARCH_ROADMAP.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/planning-history/FMS_RESEARCH_ROADMAP.md): Historical planning snapshot and decision record preserved from legacy GEMINI archive.
- [`reference/preprice/FMS_CANDIDATE_SELECTION_CHARTER.md`](file:///c:/dev/Fyodor%20Math%20Lab/Macro%20Research/reference/preprice/FMS_CANDIDATE_SELECTION_CHARTER.md): Preliminary candidate-selection charter covering Building Permits and German Ifo.

---

## 4. Pinned Data (Source Data Repository)

Located at `data/pinned/FyodorResearchExport_v3_20260923_234930_server/`.
- Schema Version: `fyodor-mt5-research-export/3.1.0`
- Exporter Version: `3.1.0`
- Trade-Server Time: Elev8 Markets Ltd. / Elev8-Demo2
- Pinned Hash: `calendar_releases.csv` SHA-256 = `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e`.
- Contains 123,054 calendar release rows and 51 H1 candle CSVs across 8 sovereign currencies.
- Kept out of Git history due to file size.

---

## 5. Disposable Scratch

Located at `scratch/` (and local app data scratch).
- Contains temporary calculation scripts and intermediate JSON dumps used during forensic verification.
- Never committed to Git history.
