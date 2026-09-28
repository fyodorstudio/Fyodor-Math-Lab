# Fyodor Research Export V4 — Provenance and Integrity Index

**Snapshot Identifier:** `FyodorResearchExport_v4_20260928_021936_79538281_server`
**Source Broker / Server:** Elev8 Markets Ltd. / Elev8-Demo2
**Terminal:** MetaTrader 5 (Build 6230) by MetaQuotes Ltd.
**Exporter Version:** 4.0.0 (`fyodor-mt5-research-export/4.0.0`)
**Export ID:** `20260928_021936_79538281`
**Snapshot Trade Server Time:** `1790561976` (`2026.09.28 02:19:36`)
**Snapshot GMT Time:** `1790551176` (`2026.09.27 23:19:36`)
**Trade Server Minus GMT Offset (Snapshot):** `+3 hours` (`10800s`)
**Timestamp Convention:** `trade_server_time` (original trade-server time preserved, no constant DST assumption)

---

## 1. Executive Summary & Verification Boundary

This tracked document indexes all **34 immutable raw data files** exported by MT5 on 2026-09-28 and placed into `raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/`.

- **Total Files:** 34 (6 root catalog/calendar files + 28 H1 candle files in `candles/`).
- **Total Exported H1 Bars:** 1,452,398 (exact match to `manifest.csv` `candle_bars_exported`).
- **Total Calendar Events:** 1,051 (exact match to `manifest.csv` `calendar_events_exported`).
- **Total Calendar Releases:** 123,256 (exact match to `manifest.csv` `calendar_releases_exported`).
- **Export Completeness Status:** `calendar_completed=true`, `candles_completed=true`.
- **Universe Scope:** 28 exported pairs. **19 pairs active for first-pass research; 9 pairs globally excluded** due to truncated broker history starting only 25–26 November 2025.

### Independently Anchored Hashes (3 Files)

The three anchor files published in `Docs/MT5_EXPORTER_SCRIPT/new/README.md` are verified fail-closed bit-for-bit before pipeline execution:

| Anchor File | Published Anchor SHA-256 | Verified Local SHA-256 | Status |
| --- | --- | --- | --- |
| `calendar_releases.csv` | `FCB68E1C2A6269D98287F4BEDBEE1F3BCB5A8C99379502782359EDFD20E83D6F` | `FCB68E1C2A6269D98287F4BEDBEE1F3BCB5A8C99379502782359EDFD20E83D6F` | **EXACT MATCH** |
| `candle_symbols.csv` | `876495CC3FCD0B4E88CB1412E6DF154CF8813B5DF7CC5EC57A8F74C57BD7475D` | `876495CC3FCD0B4E88CB1412E6DF154CF8813B5DF7CC5EC57A8F74C57BD7475D` | **EXACT MATCH** |
| `manifest.csv` | `1E7C8A5047BDEDAF0F66DE23F5E6CC382C29EA839B9E07A911789BBFFC548A6F` | `1E7C8A5047BDEDAF0F66DE23F5E6CC382C29EA839B9E07A911789BBFFC548A6F` | **EXACT MATCH** |

### Computed and Registered Snapshot Files (31 Files)

The remaining 31 files (28 H1 candle files, `calendar_currencies.csv`, `calendar_events.csv`, and `run_started.csv`) were computed directly from disk and registered into this tracked index.

---

## 2. Complete Inventory of All 34 Raw Files

### Root Metadata and Calendar Files (6 files)

| Relative Path | Size (Bytes) | Row Count | Provenance Tier | SHA-256 Checksum | Schema / Header |
| --- | --- | --- | --- | --- | --- |
| `raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/calendar_currencies.csv` | 224 | 8 | COMPUTED_AND_REGISTERED | `ADB8C1A4DB5041067CDEF06852C29D5EFA4BCF8E56B7F978AD9AB84CA9C3F809` | `currency,event_definitions,releases,query_error,status` |
| `raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/calendar_events.csv` | 359,636 | 1,051 | COMPUTED_AND_REGISTERED | `E08D2DF96E83FDEFA1C56D33316EE09178FE75AFF1F3325D6F4EC4C80A4B7F13` | `event_id,requested_currency,country_id,country_code,country_name,country_currency,country_currency_symbol,country_url_name,event_name,event_code,event_type,event_type_code,sector,sector_code,frequency,frequency_code,time_mode,time_mode_code,unit,unit_code,importance,importance_enum,importance_code,multiplier,multiplier_code,digits,source_url,country_lookup_ok` |
| `raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/calendar_releases.csv` | 55,514,491 | 123,256 | INDEPENDENTLY_ANCHORED | `FCB68E1C2A6269D98287F4BEDBEE1F3BCB5A8C99379502782359EDFD20E83D6F` | `event_id,value_id,timestamp,currency,country_code,event_name,importance,actual,forecast,previous,revised_previous,period,revision,impact_type,impact_type_code,value_event_id,country_id,event_code,event_type,sector,frequency,time_mode,unit,multiplier,digits,importance_enum,importance_code,source_url,actual_raw_scaled_1e6,forecast_raw_scaled_1e6,previous_raw_scaled_1e6,revised_previous_raw_scaled_1e6,timestamp_server_text,period_server_text,timestamp_convention,country_lookup_ok` |
| `raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/candle_symbols.csv` | 6,660 | 28 | INDEPENDENTLY_ANCHORED | `876495CC3FCD0B4E88CB1412E6DF154CF8813B5DF7CC5EC57A8F74C57BD7475D` | `source_symbol,canonical_symbol,output_file,timeframe,calculation_mode,calculation_mode_code,symbol_digits,point,currency_base,currency_profit,bars_copied,bars_written,earliest_bar_timestamp,latest_bar_timestamp,earliest_bar_server_text,latest_bar_server_text,requested_from,requested_to,coverage_starts_after_requested,coverage_ends_before_available_terminal_history,excluded_incomplete_bars,copy_error,status,chart_price_basis` |
| `raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/manifest.csv` | 3,515 | 61 | INDEPENDENTLY_ANCHORED | `1E7C8A5047BDEDAF0F66DE23F5E6CC382C29EA839B9E07A911789BBFFC548A6F` | `key,value,note` |
| `raw_data/FyodorResearchExport_v4_20260928_021936_79538281_server/run_started.csv` | 105 | 1 | COMPUTED_AND_REGISTERED | `0F9944FDE37206826EADF9CBE8675B4381E15F9F524478EB7F76E6A8D9A8DA10` | `export_id,snapshot_trade_server_timestamp,exporter_version` |

### H1 Candle Files (28 pairs)

| Pair | Research Scope | Row Count | First Bar (Server Time) | Last Bar (Server Time) | Provenance Tier | SHA-256 Checksum |
| --- | --- | --- | --- | --- | --- | --- |
| `candles_AUDCAD` | Active (19-pair universe) | 74,007 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `492ECDD81A864D97A7002FF3666CBF55B0030F53303E03519A24AE79CB682F71` |
| `candles_AUDCHF` | Active (19-pair universe) | 74,010 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `B5AB971CECF15E8530A23D349DFC2048FE777E7CE7D27300EA62C4C10E79282B` |
| `candles_AUDJPY` | Active (19-pair universe) | 74,014 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `19E0DBB591147A5DBF24C4B5A70630B3AC072F19AA8994CFF19EB842F7C9D38C` |
| `candles_AUDNZD` | Active (19-pair universe) | 74,020 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `ADED3805D8FD0815FE6FA654AB8D0B75097BE4FE20E578902DD8ABDF3CC39D0F` |
| `candles_AUDUSD` | Active (19-pair universe) | 74,018 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `804FF41B922BD02A7EDE6705D2BD9861A7AF5B45D7D9DD841E10AEEE81FA7181` |
| `candles_CADCHF` | Active (19-pair universe) | 5,191 | `2025.11.25 19:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `61CD00E38F66FE12E9FF1D5CC30991AF4C2E642D1736DB490BA8DA9BA512082F` |
| `candles_CADJPY` | Active (19-pair universe) | 5,185 | `2025.11.26 01:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `2BF8B722BD207301FDB3988BDDC5658D4412FFDCC82B95C7C67F67355E4C088E` |
| `candles_CHFJPY` | Active (19-pair universe) | 74,005 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `5F7E5E8AC36D8236AA092438DB2B01F6FED9A3F883076AF51944D21ABFD3190A` |
| `candles_EURAUD` | Active (19-pair universe) | 74,017 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `7F462079C6480BFABA9E7300A64F470D2D095374C4DBD83C77D91A2AF7584EC8` |
| `candles_EURCAD` | Active (19-pair universe) | 74,019 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `37D3B8D1ABE2B4506D1BDBDF18A762851743385D8B99886D49BE2716A62A2042` |
| `candles_EURCHF` | Active (19-pair universe) | 73,727 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `03DDBDE28C8267841B822AE1BE03C687FFCD93C0AFE3D2DB62823FEF1A3EC5D1` |
| `candles_EURGBP` | Active (19-pair universe) | 74,018 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `30BBF17F085410889BED36499C8ABFF54F802B341E620042360842BC45440194` |
| `candles_EURJPY` | Active (19-pair universe) | 74,017 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `450DB955EAB38351FB5523FD64BF6C6156F86FD86E65CE572909C77BEC5644D6` |
| `candles_EURNZD` | Active (19-pair universe) | 74,000 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `2208C8E040ACD1E9ED7B67E6760A140FFBCDB5F7B09D28E29CC8BF9807D435EB` |
| `candles_EURUSD` | Active (19-pair universe) | 74,006 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `96A51AA29BBC3F3E9CB07633328F154AC6967D8BF40B7A5211934ACB0DEFF45E` |
| `candles_GBPAUD` | Active (19-pair universe) | 5,185 | `2025.11.26 01:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `CE0463F095EBF15A3771B5EA76A3E5062EC37EBFB20EDAB1B0C564EE920EAFC0` |
| `candles_GBPCAD` | Active (19-pair universe) | 5,185 | `2025.11.26 01:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `7F0C73A170F798AE407E7CC73F2FCFE841638F32FBF707B167E96831A0887B88` |
| `candles_GBPCHF` | Active (19-pair universe) | 74,009 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `C5A7F593F8A7DE1285F2688970799A9AF1B638B467F881CE310A3E0714DE3FC4` |
| `candles_GBPJPY` | Active (19-pair universe) | 5,147 | `2025.11.25 19:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `E35B26F95646FCCB6C1330A362338459B1019A0C8F1B7767BC407482BE31C63E` |
| `candles_GBPNZD` | Active (19-pair universe) | 5,184 | `2025.11.26 01:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `32EFEEC4F392D8894DE7AB6734326279FA8377D53BA25FBC5E7CFCB796D95A9A` |
| `candles_GBPUSD` | Active (19-pair universe) | 73,999 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `77438C3DF042FA379533144A830FEDFBEC8AC12A47E53647C8653C7090F45512` |
| `candles_NZDCAD` | Active (19-pair universe) | 5,185 | `2025.11.26 01:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `30A3CFDD24FEF029C41A5023FFE42BF66AC47472822F339D687081B859299E80` |
| `candles_NZDCHF` | Active (19-pair universe) | 5,185 | `2025.11.26 01:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `54986956BC6A1A4693DBBB22520F78B3F0E1E23E4D04788CB99B6ED559FF876B` |
| `candles_NZDJPY` | Active (19-pair universe) | 5,185 | `2025.11.26 01:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `1003713E1C4C16347DA0799DF008D8EEDD9533263250610EF8A519373CB0BF87` |
| `candles_NZDUSD` | Active (19-pair universe) | 73,955 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `DFAD73063A3313175ED7F111F8FD38AC0C1D5D1E62FD0D037A2DB396972B755E` |
| `candles_USDCAD` | Active (19-pair universe) | 74,019 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `D854DDB5494E3CD62D9F80E2A22F9F65FAAA886643572602D638722C1DC72D44` |
| `candles_USDCHF` | Active (19-pair universe) | 73,968 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `134A250D6FE0F3259A6B0D842872866B481A9A7FE9D7567E7892DCB23B63897E` |
| `candles_USDJPY` | Active (19-pair universe) | 73,938 | `2014.11.03 00:00:00` | `2026.09.28 01:00:00` | COMPUTED_AND_REGISTERED | `3DCE78FE38019275F288E71E4F9134E4BEA1FD02A09E1CEE2873025A3961468C` |

---

## 3. Pinned Pre-Outcome Ledger Baselines (V2 Freeze)

The pre-outcome candidate eligibility ledgers for US CPI and US NFP were generated and verified fail-closed on 2026-09-28 (Commit `3c3d108`). These files establish the immutable pre-simulation denominator and candidate eligibility classifications:

| Relative File Path | Event Family | Row Count | Total Observations | Eligible H60 (A-F / A-P) | Eligible H240 (A-F / A-P) | Verified SHA-256 Checksum |
| --- | --- | --- | --- | --- | --- | --- |
| `Research Candidate/CPI/pre_outcome_ledger_cpi_v2.csv` | US CPI | 980 | 980 | 671 / 859 | 671 / 859 | `29AC66F511736121A0A588221DF2A5D8C816722D9C79F9E72FF99C9FE28F0B66` |
| `Research Candidate/NFP/pre_outcome_ledger_nfp_v2.csv` | US NFP | 980 | 980 | 777 / 965 | 776 / 964 | `157970C1788CE7CDD47291BCC9E94898E33559FD73FC7503BD7ED821483007CB` |
