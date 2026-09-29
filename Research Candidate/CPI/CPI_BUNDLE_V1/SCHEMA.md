# USD CPI Same-Time Bundle V1: Ledger Schema & Data Dictionary

**Document Status:** TRACKED PRE-OUTCOME REPOSITORY ASSET  
**Study Identifier:** `USD_CPI_BUNDLE_V1`  
**Governing Contract:** [Calculation Contract](../../Docs/CONTRACT%20AND%20PLANNING/CALCULATION_AND_CANDIDATE_CONTRACT.md)  
**Location of Local Run Artifacts:** `Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_pre_outcome/` (Git-ignored)

---

## 1. Primary Bundle Ledger: `cpi_bundle_ledger.csv`

One row per unique CPI release timestamp in the raw calendar inventory ($N = 140$).

| Column | Type | Nullable | Description & Domain |
| --- | --- | --- | --- |
| `bundle_id` | String | No | Stable atomic identifier: `USD_CPI_BUNDLE_{timestamp}`. |
| `timestamp` | Integer | No | Trade server epoch seconds. |
| `timestamp_server_text` | String | No | Formatted server timestamp (`YYYY.MM.DD HH:MM:SS`). |
| `bundle_period_server_text` | String | No | Reference period string from broker calendar (e.g. `2026.04.01 00:00:00`). |
| `year` | Integer | No | Calendar release year ($2015..2026$). |
| `cohort` | String | No | `CORE_2015_2025`, `PARTIAL_2026`, or `POST_CUTOFF_2026`. |
| `is_bundle_complete` | Boolean | No | `True` if all 4 tracked constituents present; `False` if any missing. |
| `present_constituent_ids` | String | No | Comma-separated list of present event IDs in bundle. |
| `missing_constituent_ids` | String | Yes | Comma-separated list of absent event IDs (e.g. `840030005,840030006`). |
| `headline_mm_present` | Boolean | No | Presence of Headline CPI m/m (`840030005`). |
| `headline_mm_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `headline_mm_value_id` | String | Yes | MT5 internal value ID. |
| `headline_mm_unit` | String | Yes | Unit string (`CALENDAR_UNIT_PERCENT`). |
| `headline_mm_digits` | Integer | Yes | Precision digits (typically 1). |
| `headline_mm_actual` | Float | Yes | Exported actual value $A$. |
| `headline_mm_previous` | Float | Yes | Exported reported previous value $P$. |
| `headline_mm_revised_previous` | Float | Yes | Exported revised previous (if supplied by broker). |
| `headline_mm_period_server_text` | String | Yes | Constituent reference period text. |
| `headline_mm_delta` | Float | Yes | $\Delta = A - P$, rounded to 6 decimal places. |
| `headline_mm_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `core_mm_present` | Boolean | No | Presence of Core CPI m/m (`840030006`). |
| `core_mm_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `core_mm_value_id` | String | Yes | MT5 internal value ID. |
| `core_mm_unit` | String | Yes | Unit string. |
| `core_mm_digits` | Integer | Yes | Precision digits. |
| `core_mm_actual` | Float | Yes | Exported actual value $A$. |
| `core_mm_previous` | Float | Yes | Exported reported previous value $P$. |
| `core_mm_revised_previous` | Float | Yes | Exported revised previous. |
| `core_mm_period_server_text` | String | Yes | Constituent reference period text. |
| `core_mm_delta` | Float | Yes | $\Delta = A - P$. |
| `core_mm_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `headline_yy_present` | Boolean | No | Presence of Headline CPI y/y (`840030007`). |
| `headline_yy_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `headline_yy_value_id` | String | Yes | MT5 internal value ID. |
| `headline_yy_unit` | String | Yes | Unit string. |
| `headline_yy_digits` | Integer | Yes | Precision digits. |
| `headline_yy_actual` | Float | Yes | Exported actual value $A$. |
| `headline_yy_previous` | Float | Yes | Exported reported previous value $P$. |
| `headline_yy_revised_previous` | Float | Yes | Exported revised previous. |
| `headline_yy_period_server_text` | String | Yes | Constituent reference period text. |
| `headline_yy_delta` | Float | Yes | $\Delta = A - P$. |
| `headline_yy_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `core_yy_present` | Boolean | No | Presence of Core CPI y/y (`840030008`). |
| `core_yy_source_row` | Integer | Yes | 1-indexed row number in raw `calendar_releases.csv`. |
| `core_yy_value_id` | String | Yes | MT5 internal value ID. |
| `core_yy_unit` | String | Yes | Unit string. |
| `core_yy_digits` | Integer | Yes | Precision digits. |
| `core_yy_actual` | Float | Yes | Exported actual value $A$. |
| `core_yy_previous` | Float | Yes | Exported reported previous value $P$. |
| `core_yy_revised_previous` | Float | Yes | Exported revised previous. |
| `core_yy_period_server_text` | String | Yes | Constituent reference period text. |
| `core_yy_delta` | Float | Yes | $\Delta = A - P$. |
| `core_yy_sign` | String | No | `POSITIVE`, `NEGATIVE`, `ZERO`, or `MISSING`. |
| `mm_concordance_state` | String | No | Categorical relation: `CONCORDANT_POS`, `CONCORDANT_NEG`, `CONFLICT_HEAD_POS_CORE_NEG`, `CONFLICT_HEAD_NEG_CORE_POS`, `HEAD_POS_CORE_ZERO`, `HEAD_NEG_CORE_ZERO`, `HEAD_ZERO_CORE_POS`, `HEAD_ZERO_CORE_NEG`, `BOTH_ZERO`, or `MISSING_ANCHOR`. |
| `is_conflict_episode` | Boolean | No | `True` if `CONFLICT_HEAD_POS_CORE_NEG` or `CONFLICT_HEAD_NEG_CORE_POS` ($N=28$). |
| `coincident_claims_collision` | Boolean | No | `True` if US Initial Jobless Claims (`840140001`) coincides at release minute ($N=33$). |
| `coincident_claims_value_id` | String | Yes | MT5 value ID for coincident Jobless Claims record. |
| `coincident_claims_actual` | String | Yes | Actual claims reading. |
| `coincident_claims_previous` | String | Yes | Previous claims reading. |
| `coincident_non_cpi_count` | Integer | No | Count of external non-CPI events at identical timestamp. |
| `coincident_non_cpi_event_ids` | String | Yes | Pipe-separated list of `currency_event_id:event_name`. |

---

## 2. Pair-Expanded Pre-Outcome Ledger: `cpi_pair_expanded_ledger.csv`

One row per active pair and bundle ($N = 140 \times 7 = 980$). Price-blind coverage and pre-outcome candidate eligibility only.

| Column | Type | Nullable | Description & Domain |
| --- | --- | --- | --- |
| `bundle_id` | String | No | Foreign key matching `cpi_bundle_ledger.csv`. |
| `pair` | String | No | Approved 7 active USD pairs (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, `USDCHF`, `USDJPY`). |
| `usd_role` | String | No | `BASE` (`USDCAD`, `USDCHF`, `USDJPY`) or `QUOTE` (`AUDUSD`, `EURUSD`, `GBPUSD`, `NZDUSD`). |
| `timestamp` | Integer | No | Release timestamp. |
| `timestamp_server_text` | String | No | Release timestamp text. |
| `year` | Integer | No | Calendar year. |
| `cohort` | String | No | Chronological cohort (`CORE_2015_2025`, `PARTIAL_2026`, `POST_CUTOFF_2026`). |
| `is_bundle_complete` | Boolean | No | Bundle completeness flag. |
| `headline_mm_sign` | String | No | Headline m/m sign. |
| `core_mm_sign` | String | No | Core m/m sign. |
| `headline_yy_sign` | String | No | Headline y/y sign. |
| `core_yy_sign` | String | No | Core y/y sign. |
| `mm_concordance_state` | String | No | Joint m/m categorical relationship. |
| `is_conflict_episode` | Boolean | No | Flag indicating headline/core m/m sign conflict. |
| `coincident_claims_collision` | Boolean | No | Initial claims coincidence flag. |
| `has_entry_candle` | Boolean | No | Earliest complete H1 bar with `bar_open > release_timestamp` exists. |
| `entry_bar_timestamp` | Integer | Yes | Timestamp of simulated entry bar. |
| `entry_bar_server_text` | String | Yes | Text representation of entry bar open time. |
| `entry_delay_seconds` | Integer | Yes | Elapsed seconds from release to entry bar open. |
| `is_entry_delay_valid` | Boolean | No | `True` if `entry_delay_seconds <= 3600`. |
| `has_atr_warmup` | Boolean | No | 251 pre-release H1 bars strictly prior to release exist for Wilder ATR(14). |
| `pre_release_atr` | Float | Yes | Computed pre-release ATR(14) in price units. Serialized with round-trip IEEE 754 double precision (repr). |
| `has_h60_bars` | Boolean | No | 60 continuous H1 bars available after entry. |
| `has_h60_gap_free` | Boolean | No | H60 path free of weekday gaps > 4 hours. |
| `has_h120_bars` | Boolean | No | 120 continuous H1 bars available after entry. |
| `has_h120_gap_free` | Boolean | No | H120 path free of weekday gaps > 4 hours. |
| `has_h240_bars` | Boolean | No | 240 continuous H1 bars available after entry. |
| `has_h240_gap_free` | Boolean | No | H240 path free of weekday gaps > 4 hours. |
| `eligible_candidate_1_headline_mm_h60` | Boolean | No | Candidate 1 (Benchmark Headline m/m) H60 eligibility. |
| `exclusion_candidate_1_headline_mm_h60` | String | Yes | Exclusion reason for Candidate 1 if ineligible. |
| `eligible_candidate_2_core_mm_led_h60` | Boolean | No | Candidate 2 (Core m/m Led) H60 eligibility. |
| `exclusion_candidate_2_core_mm_led_h60` | String | Yes | Exclusion reason for Candidate 2 if ineligible. |
| `eligible_candidate_3_concordant_mm_h60` | Boolean | No | Candidate 3 (Concordant Only) H60 eligibility. |
| `exclusion_candidate_3_concordant_mm_h60` | String | Yes | Exclusion reason for Candidate 3 if ineligible. |
| `eligible_candidate_4_conflict_filtered_headline_h60` | Boolean | No | Candidate 4 (Conflict-Filtered Headline) H60 eligibility. |
| `exclusion_candidate_4_conflict_filtered_headline_h60` | String | Yes | Exclusion reason for Candidate 4 if ineligible. |
| `eligible_conflict_substudy_h60` | Boolean | No | Conflict-Only Descriptive Sub-study H60 eligibility. |
| `exclusion_conflict_substudy_h60` | String | Yes | Exclusion reason for Conflict Sub-study if ineligible. |
