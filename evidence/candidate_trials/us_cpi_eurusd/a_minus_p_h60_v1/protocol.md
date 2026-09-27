# Post-Hoc Exploratory Specification: US CPI on EURUSD (A−P Momentum, H60 Expiry)

**Identifier**: `us_cpi_eurusd_a_minus_p_h60_v1`  
**Date**: 2026-09-27  
**Governance State**: Post-Hoc Exploratory Specification (Under Audit — No Registered Setup)  
**Target Pair**: EURUSD (Gross Mid/Bid OHLC)  

> [!IMPORTANT]
> **POST-HOC DISCLOSURE & GOVERNANCE BOUNDARY**:
> Historical EURUSD H1 candle prices, candidate trade paths, holding distributions, and multiple target multiples (1.0x, 1.5x, 2.0x) were inspected prior to drafting this protocol document. This document formalizes a **post-hoc exploratory specification** to ensure forensic auditability and exact numerical reproducibility; it is **NOT** a pre-price-frozen hypothesis test.
> The 1.0x and 2.0x target sensitivities are descriptive post-hoc parameter variations evaluated on the identical historical sample. They must **NOT** be portrayed as independently validated choices or forward-tested edges.
> This trial is **NOT** a registered setup and must not be traded on live or demo accounts.
> Zero setups are registered or approved for live or demo forward trading.

---

## 1. Research Question & Rationale
The maintained baseline evaluates announcement surprise ($A - F$: Actual minus Forecast) with an H24 holding horizon. This trial evaluates a distinct economic hypothesis:
- Does monthly macroeconomic acceleration/deceleration ($A - P$: Actual minus Previous) on US headline and core CPI provide a tradeable directional displacement signal on EURUSD?
- Does an extended holding window of 60 observed H1 candles (H60) capture prolonged post-release drift, or do trades resolve well before 60 bars?

This pass is strictly exploratory. It does not replace the $A - F$ baseline, modify the HTML viewer, or register an executable rule for forward testing.

---

## 2. Cryptographic Provenance & Input Data
The trial ingests exclusively byte-verified local pinned data exports:

| Resource | Path | Expected SHA-256 |
|---|---|---|
| **Calendar Releases** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/calendar_releases.csv` | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` |
| **EURUSD H1 Candles** | `data/pinned/FyodorResearchExport_v3_20260923_234930_server/candles/candles_EURUSD_H1.csv` | `893aa1934ef93dce57101e1eec85d08c0055112123e2b4846f2c70ceb234ade5` |

The runner computes and verifies both input SHA-256 digests before execution and fails closed on any discrepancy. Zero mock data, pseudo-random generators, seed fixtures, or forward lookahead are permitted.

---

## 3. Signal Specification

### Release Pairing & Filtering
1. **Event Pairing**:
   - US CPI m/m (`840030005`, Headline)
   - US Core CPI m/m (`840030006`, Core)
   - Releases must share the identical release timestamp (`timestamp`).
2. **Revision Filter**:
   - `revision == "0"` strictly enforced. Non-zero revisions and subsequent historical corrections are excluded from entry triggers.
3. **Collision Filter**:
   - Pinned timestamps coincident with US Retail Sales releases (`840020010` Advance Retail Sales m/m, `840020011` Retail Sales Ex Auto m/m) are excluded from trade execution (`SHARED_COLLISION`). Other coincident releases (e.g., Initial Jobless Claims) are recorded for context but not filtered out.
4. **Directional Logic ($A - P$)**:
   - Headline Momentum: $\Delta_{\text{head}} = \text{round}(\text{Actual}_{\text{head}} - \text{Previous}_{\text{head}}, 4)$
   - Core Momentum: $\Delta_{\text{core}} = \text{round}(\text{Actual}_{\text{core}} - \text{Previous}_{\text{core}}, 4)$
   - Signal rules:
     * **SHORT EURUSD**: $\Delta_{\text{head}} > 0$ **and** $\Delta_{\text{core}} > 0$ (both accelerating => USD Bullish).
     * **LONG EURUSD**: $\Delta_{\text{head}} < 0$ **and** $\Delta_{\text{core}} < 0$ (both decelerating => USD Bearish).
     * **NO TRADE**: Mixed signs ($\Delta_{\text{head}} \times \Delta_{\text{core}} < 0$), either equal to zero ($\Delta = 0$), or missing numeric value. Zero is a valid numeric value, not missing.
5. **Role of Forecast**:
   - Forecast values (`forecast`) are recorded in ledgers for analytical context, but are **NOT** required for candidate eligibility and do **NOT** govern signal direction.
6. **Role of Revised Previous**:
   - MT5 exports `previous`, `revised_previous`, and `revision` as separate fields.
   - `revised_previous` is preserved in all audit outputs and audited for presence and potential sign change.
   - `revised_previous` is **NEVER** substituted into the primary trading rule, and an episode is never excluded merely because it exists.
   - Point-in-time caveat: Static snapshot data does not establish whether `revised_previous` was available at the moment of release or updated retrospectively.

---

## 4. Execution Mechanics

1. **Entry Price & Timing**:
   - Exact OPEN price of the intended next-hour H1 candle:
     $$\text{entry\_ts} = \left(\lfloor \text{ts} / 3600 \rfloor + 1\right) \times 3600$$
   - The simulator requires the exact intended entry candle to exist on disk. Forward search across missing bars is strictly prohibited.
2. **Volatility Measure (Pre-Release ATR14)**:
   - Arithmetic mean of 14 completed H1 True Ranges ending **strictly before** the release timestamp:
     $$\text{candle\_time} + 3600 < \text{release\_ts}$$
   - Any bar containing or touching the release timestamp is strictly excluded.
   - Requires exactly 15 strictly consecutive completed H1 bars (each exactly 3600 seconds apart) ending before the release timestamp. Fails closed if any bar is missing.
3. **Protective Stop Loss**:
   - Entry $\pm 1.0 \times \text{ATR14}$ nominal.
   - Adverse gap handling: if a bar opens beyond the stop level, it fills at the worse open price.
4. **Profit Target**:
   - Entry $\mp 1.5 \times \text{ATR14}$ nominal (primary trial).
   - Sensitivities evaluated at $1.0 \times \text{ATR14}$ and $2.0 \times \text{ATR14}$ as descriptive parameter variations.
   - Favorable gap handling: if a bar opens beyond the target level, fill is capped at the nominal target price.
5. **Expiry Horizon (H60)**:
   - Evaluates up to 60 **observed market H1 candles** from entry.
   - If neither Stop nor Target is triggered within 60 observed bars, trade exits at the close of Bar 60 with label `TIMEOUT_H60`.
   - Requires at least 60 forward bars in the candle series.
   - Observed market candles are distinguished from elapsed clock hours. Weekend market closures are classified strictly by server-date weekdays (Friday close to Sunday/Monday open) and audited separately from unexpected missing-data gaps.
6. **Intrabar Ambiguity Precedence**:
   - If a single H1 candle touches both Stop Loss and Profit Target levels:
     * Trade is flagged `ambiguous_flag = True`.
     * Conservative rule (`STOP_FIRST`): Stop is assumed hit first.
     * Optimistic sensitivity (`TARGET_FIRST`): Target is assumed hit first.
7. **Friction Model**:
   - Gross OHLC prices only. Zero spread, slippage, commission, or swap is modeled.

---

## 5. Ledger & Accounting Integrity
1. **Decision Ledger Funnel Closure**:
   - All 277 US_INFLATION family episodes must be accounted for with mutually exclusive dispositions:
     * `PCE_ONLY`: Core PCE only release (event 840010001).
     * `SHARED_COLLISION`: Timestamps shared with US Retail Sales (events 840020010/840020011).
     * `MISSING_AP`: Missing headline/core release record or non-numeric actual/previous.
     * `MIXED_OR_EQUAL`: Discordant momentum signs or zero momentum.
     * `CANDIDATE_TRADE`: Concordant momentum triggering execution.
   - $\sum \text{Dispositions} \equiv 277$.
2. **Artifact Isolation**:
   - All output files are written strictly to `evidence/candidate_trials/us_cpi_eurusd/a_minus_p_h60_v1/`.
   - Baseline setup files in `TABLE VIEWER/cpi_setup/` remain untouched and byte-identical.
