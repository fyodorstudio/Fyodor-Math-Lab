# Research Candidate evidence

This tracked file makes the folder visible in Git. **No setup is registered for forward testing.** The CPI and NFP V2 exploratory packages below are local, immutable outputs from the seven active USD pairs; the nine truncated-history pairs are globally excluded.

| Family | Final local report | Result status |
| --- | --- | --- |
| CPI | [V2 exploration report](CPI/CPI_EXPLORATION_V2/run_20260929_v2_final/EXPLORATION_SUMMARY_REPORT.md) | Full trial-ledger/summary reconciliation passed |
| NFP | [V2 exploration report](NFP/NFP_EXPLORATION_V2/run_20260929_v2_final/EXPLORATION_SUMMARY_REPORT.md) | Full trial-ledger/summary reconciliation passed |

Both final manifests identify calculation commit `ce5392155cacafd6ca6a934176c515c774c474d6`. The final packages contain 238,680 CPI and 271,596 NFP trial rows. Each family passed four independent raw-candle sample cases; this is a sample price audit, not an independent recalculation of every trade. The `run_20260928_v2` CPI package failed verification and is **rejected**. The `run_20260929_v2_reconciled` packages passed numerical verification but have superseded report wording. Use only `run_20260929_v2_final` for inspection.

**Publication boundary:** The historical commit IDs recorded in the local V2 manifests and protocols refer to `archive/EXPANDED-before-size-cleanup` on the original computer. The publishable `EXPANDED` branch is a clean snapshot without the oversized V1 blobs; those old commit IDs are not reachable in a fresh GitHub clone. Preserve the local archive branch and evidence packages if exact historical commit provenance is needed.

These large packages are Git-ignored and remain on this computer; the report links will not resolve in a fresh GitHub clone until the packages are transferred separately. The tracked [standalone HTML viewer](../HTML%20Viewer/table_viewer.html) embeds the pinned final CPI/NFP V2 release paths and summary-grid metrics for inspection. It does not contain the full trade ledgers, and it does not designate a winning or registered rule. Rebuild from the local final packages with `python "HTML Viewer/Python Calculator/build_viewer.py"`, or use `--check` to detect a stale snapshot.

The [calculation and candidate contract](../Docs/CONTRACT%20AND%20PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md) defines versioned packages, ledgers, and audit requirements. Do not import old-repository results as though they were calculated under this contract.
