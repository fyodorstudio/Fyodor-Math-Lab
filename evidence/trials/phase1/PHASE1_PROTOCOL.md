# Phase 1 Exploration Protocol: Macroeconomic Releases and Post-Release FX H1 Directionality

**Document Status**: FROZEN BEFORE RETURN COMPUTATION  
**Protocol Version**: 1.1.0  
**Baseline Git Commit**: `7ba2530`  
**Execution Environment**: `C:\dev\Fyodor Math Lab\GEMINI`  
**Author / Systems Guardian**: Antigravity Quantitative Research Engine  

---

## 1. Research Question & Scientific Stance

### Core Research Question
> *Do scheduled macroeconomic releases show repeatable directional FX behavior over subsequent complete H1 bars, beyond the immediate announcement response?*

### Epistemic Stance
This inquiry is treated as a conjecture to test and potentially falsify. A negative or inconclusive result is considered a successful, trustworthy research outcome. Under the laboratory covenant:
- No outcome will be optimized to manufacture an attractive curve.
- No trading strategy will be proposed, backtested with costs, or claimed to be profitable in Phase 1.
- Positive direction rate is descriptive and will **never** be labeled a "win rate."
- The practical baseline/null is: median return $\approx 0$, positive direction rate $\approx 50\%$, and no persistent directional continuation after the initial complete H1 repricing bar.

---

## 2. Verified Data Source & Lineage

The data source for this study is strictly pinned to the validated MetaTrader 5 export:
- **Export Root**: `tools/mt5/FyodorResearchExport_v3_20260923_234930_server`
- **Manifest Schema Version**: `fyodor-mt5-research-export/3.1.0`
- **Terminal & Server**: MetaTrader 5 Build 6182, Elev8 Markets Ltd. / Elev8-Demo2
- **Calendar Releases Exported**: 123,054 records
- **Forex Candle Instruments**: 51 symbols (1,686,617 completed H1 bars)
- **Calendar File SHA-256 Hash**:
  `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e`

### Fallback & Malformed Source Prohibitions
- The earlier `233418` export is malformed and must **never** be used.
- The legacy repaired calendar in `raw_data/` must **never** be silently substituted.
- Any mismatch in hash, schema, or record counts triggers an immediate hard stop.

---

## 3. Chronological Boundary & Sealed Confirmation Holdout

### The Split Rule
To protect against researcher degrees of freedom and retrospective overfitting, historical time is partitioned into two mutually exclusive periods:
- **Chronological Boundary**: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`).
- **Exploration Sample**: Releases strictly before `2023-01-01 00:00:00` (`timestamp < 1672531200`).
- **Confirmation Sample**: Releases on or after `2023-01-01 00:00:00` (`timestamp >= 1672531200`).

### Sealed Confirmation Guarantee
The Confirmation sample is **strictly sealed** throughout Phase 1. No code in this session will calculate, summarize, print, chart, or inspect Confirmation FX returns. This rule is enforced programmatically in `lab/src/research/boundaryGuard.ts` (`assertStrictlyExploration`), which aborts execution if Confirmation timestamps are touched.

### Pair-Specific H42 Boundary Exclusion Rule
To prevent post-split price data from contaminating the pre-split Exploration study, each currency pair's observation path must complete its entire 42-hour observation window before the boundary:
- Let $P_0$ be the first complete H1 candle at or after the release on that pair.
- The 42nd candle ($H_{42}$) has start timestamp $T_{42} = \text{candleTimes}[p_0 + 41]$ and closing timestamp $T_{\text{close}, H42} = T_{42} + 3600$.
- **Boundary Condition (evaluated independently per pair)**:
  - $T_{\text{close}, H42} \le 1672531200 \implies$ **Eligible**: All 42 candles close at or before 2023-01-01 00:00:00 for that pair.
  - $T_{\text{close}, H42} > 1672531200 \implies$ **Excluded**: The path extends into 2023. Excluded from that pair's Exploration dataset *before* return computation.
  - Pair-specific boundary mismatches (e.g. where an event completes H42 in time on EURUSD but extends beyond the boundary on USDJPY due to holiday/missing bars) are evaluated independently; neither pair's boundary state leaks into or affects the other.

---

## 4. Target Series & Currency Pairs

### Series Identities (Exact MT5 `event_id + revision`)
1. **USD CPI m/m**: `USD:US:840030005:r0` (Headline monthly inflation)
2. **USD Core CPI m/m**: `USD:US:840030006:r0` (Core monthly inflation ex food/energy)
3. **USD Core PCE m/m**: `USD:US:840010001:r0` (Core personal consumption expenditures price index)
4. **USD Nonfarm Payrolls**: `USD:US:840030016:r0` (Net monthly employment change)

### Pair Representations & Observational Unit
- **Primary Pair**: `EURUSD` (USD in quote position, $Q = -1$).
- **Pair-Robustness Diagnostic**: `USDJPY` (USD in base position, $Q = +1$).
- **Strict Independence Principle**: One macroeconomic release observed on two currency pairs remains **one single event**. EURUSD and USDJPY observations will be reported in separate tables and never pooled into an artificial $2N$ pseudo-sample.

---

## 5. Frozen Analytical Defaults

1. **Scoring Mode**: Walk-Forward scoring only.
2. **Percentile Threshold**: 75th percentile ($P_{75}$) of absolute nonzero deltas using Hyndman–Fan type 7 linear interpolation: index $(N-1) \times 0.75$.
3. **Minimum Prior History**: Strictly prior nonzero observations within the exact series must be $\ge 20$ (`minHistory = 20`). Same-timestamp releases are evaluated before any member of the batch enters history.
4. **Deltas**:
   - Surprise: $\Delta_S = A - F$
   - Momentum: $\Delta_M = A - P$
5. **Exact-Zero Scoring Rule**:
   - If $|\Delta| \le 10^{-6}$ and prior nonzero history $N \ge 20 \implies$ Score $= +1$ (Inline / Equal).
   - If $|\Delta| \le 10^{-6}$ and prior nonzero history $N < 20 \implies$ Score $= \text{null}$.
6. **Nonzero Score Classification**:
   - Delta $> 0$ and $|\Delta| > P_{75} \implies +3$ (Large Positive)
   - Delta $> 0$ and $|\Delta| \le P_{75} \implies +2$ (Moderate Positive)
   - Delta $< 0$ and $|\Delta| \le P_{75} \implies -2$ (Moderate Negative)
   - Delta $< 0$ and $|\Delta| > P_{75} \implies -3$ (Large Negative)
   - Note: $|\Delta| = P_{75}$ remains magnitude 2; magnitude 3 requires strictly exceeding the threshold.
7. **Missing Values**:
   - $A, F,$ and $P$ must all be valid finite numbers. If any value is missing, both Surprise and Momentum scores are null. Zero is a valid number, distinct from missing.
8. **Entry Anchor ($P_0$)**:
   - The open of the first complete H1 candle beginning at or after the release timestamp:
     - 15:30 release $\implies P_0 = 16:00$ candle open.
     - 15:00 release $\implies P_0 = 15:00$ candle open.
9. **Horizons ($H_1$ to $H_{42}$)**:
   - Count available trading bars. Weekend gaps are skipped. Trailing unavailable horizons remain null.

---

## 6. Precise Definition of Cumulative vs. Delayed Response

### Outcome 1: Existing Cumulative Response ($P_0 \to H_h$)
Measures total event-currency price movement from entry anchor $P_0$ to the close of horizon $H_h$ ($h \in [1, 42]$):
- Base currency (e.g. USD in USDJPY):
  $$r_{\text{cum}, h} = \frac{P_h}{P_0} - 1$$
- Quote currency (e.g. USD in EURUSD):
  $$r_{\text{cum}, h} = \frac{P_0}{P_h} - 1$$
- Normalized log return: $Q \ln(P_h / P_0)$.

### Outcome 2: Delayed Response ($H_1 \text{ close} \to H_h \text{ close}$)
Measures whether event-currency price movement **continues or reverses** after the initial complete H1 bar has already closed ($h \in [2, 42]$):
- Base currency:
  $$r_{\text{delayed}, h} = \frac{P_h}{P_1} - 1$$
- Quote currency:
  $$r_{\text{delayed}, h} = \frac{P_1}{P_h} - 1$$
- Normalized log return: $Q \ln(P_h / P_1)$.
- For $h=1$: delayed response is undefined ($\text{null}$).

### Mathematical Compounding Identity
For both base and quote positions, the definitions satisfy exact multiplicative compounding:
$$(1 + r_{\text{cum}, 1}) \times (1 + r_{\text{delayed}, h}) = 1 + r_{\text{cum}, h}$$
*Proof for quote currency*:
$$\left(1 + \frac{P_0}{P_1} - 1\right) \times \left(1 + \frac{P_1}{P_h} - 1\right) = \frac{P_0}{P_1} \times \frac{P_1}{P_h} = \frac{P_0}{P_h} = 1 + r_{\text{cum}, h}.$$

### Methodological Distinction & Horizon Interpretation
- Cumulative return $r_{\text{cum}, h}$ mechanically embeds the $H_1$ repricing move for all subsequent horizons $h \ge 2$. If $H_1$ jumped $+50\text{ bps}$ and price remains flat thereafter, cumulative returns at $H_{12}$ and $H_{24}$ will both record $+50\text{ bps}$, creating the illusion of a persistent multi-hour trend when no further price movement occurred.
- Delayed return $r_{\text{delayed}, h}$ isolates post-$H_1$ price displacement. It tests genuine persistence: does order flow continue in the direction of the surprise after the first complete hour?
- **Intrahour Timing Disparity**: Releases partway through an hour (e.g. 15:30) have their initial 30 minutes contained within the prior candle; $P_0$ begins at 16:00, so $H_1$ measures minutes 30–90 post-release. Releases on the hour (e.g. 15:00) have $P_0$ at 15:00, so $H_1$ measures minutes 0–60 post-release.

---

## 7. Primary Exploratory Hypotheses & Contrasts

### Primary Contrast (Predeclared)
- **Horizon**: $H_{12}$ Delayed Response ($H_1 \text{ close} \to H_{12} \text{ close}$) on **EURUSD**.
- **Comparison**: Large Positive Surprise ($+3$) vs. Large Negative Surprise ($-3$) within each exact series.
- **Metrics Reported**:
  - Signed distributions of $+3$ and $-3$ groups: N, mean, median, std dev, min, max, P10, P25, P50, P75, P90.
  - Group differences: $\Delta_{\text{mean}} = \bar{r}_{+3} - \bar{r}_{-3}$ and $\Delta_{\text{median}} = \tilde{r}_{+3} - \tilde{r}_{-3}$.
  - Permutation test p-value:
    - Computed via **exact combinatorial enumeration** across all $\binom{N_1+N_2}{N_1}$ partitions when combinations $\le 50,000$ (e.g. USD CPI with $N_1=11, N_2=7$, $\binom{18}{7} = 31,824$ partitions).
    - Computed via **seeded Monte Carlo** (100,000 iterations, seed `42840030`) when combinations $> 50,000$, and explicitly labeled as such.
  - Mann-Whitney U test p-value.

### Predefined Secondary Horizons
- $H_4$ Delayed Response (short-range post-shock absorption).
- $H_{24}$ Delayed Response (full 24-hour daily cycle).
- $H_1$ Cumulative Response (initial complete bar benchmark).
- $H_{12}$ Cumulative Response (for direct comparison against $H_{12}$ delayed).
- The full $H_1$–$H_{42}$ curve is presented as descriptive trajectory context, **not** as 42 independent opportunities to discover an effect.

### Exploratory State Interactions: Complete 25-Cell 5×5 Matrix
- The complete Cartesian product $\{+3, +2, +1, -2, -3\} \times \{+3, +2, +1, -2, -3\}$ will be evaluated at $H_{12}$ delayed response.
- All 25 cells will be explicitly output, including cells with $N=0$. No sparse cell will be elevated to an inferential finding.

### Co-Release Pairwise Directional Coherence Analysis
- To prevent spurious aggregation across heterogeneous macroeconomic data, directional coherence is evaluated **strictly as pairwise labels between predefined partner indicators**, NOT as proof that an entire multi-release bundle agrees. Generic same-sign "coherence" across unrelated indicators is explicitly rejected.
- Predefined indicator pairings:
  - **Headline CPI (`840030005`) vs. Core CPI (`840030006`)**: Same surprise delta sign is `COHERENT` (both indicate higher/lower inflation); opposing surprise sign is `CONFLICTING`.
  - **Nonfarm Payrolls (`840030016`) vs. Unemployment Rate (`840030015`)**: Opposing surprise delta signs are `COHERENT` (e.g. NFP beat $+50\text{k}$ and Unemployment drop $-0.1\%$ both indicate stronger labor market); same surprise sign is `CONFLICTING`.
- Classification taxonomy:
  - `COHERENT`: Explicit predefined partner has aligned economic surprise sign.
  - `CONFLICTING`: Explicit predefined partner has contradicting economic surprise sign.
  - `ISOLATED`: Release occurred with no other concurrent releases at the same currency and timestamp.
  - `NEUTRAL`: Target release has an exact-zero or null surprise delta (distinct from unclassified).
  - `UNCLASSIFIED`: Simultaneous releases that do not match the explicit pairs above (e.g. Core PCE with Personal Spending, or CPI with Jobless Claims), or where the predefined partner had zero/null surprise.
- Group metrics will be reported across these categories to evaluate pairwise interaction.

### Individual-Event Trajectories
- All eligible historical observations will have their full input values, assigned scores, $P_0$, $H_1$ close, cumulative $H_1$–$H_{42}$ paths, delayed $H_2$–$H_{42}$ paths, and flag metadata preserved in `phase1_exploration.json` for independent forensic review.

---

## 8. Power Threshold & Multiple-Testing Policy

### Sample Power & Cell Reporting Threshold
- **Predeclared Reporting Gate**: $\min(N_{+3}, N_{-3}) \ge 5$ required to perform formal two-sample hypothesis tests.
- Cells with $\min(N_{+3}, N_{-3}) < 5$ are formally designated **Underpowered / Omitted from Inferential Hypothesis Testing**. They are reported strictly descriptively ($N$, distribution, individual event paths).
- **Epistemic Note**: $N=5$ is strictly an exploratory noise gate, **not** proof of statistical power. Small samples ($N < 20$) possess wide confidence intervals, which will be disclosed prominently.

### Multiple-Testing Family ($K=4$)
The primary confirmatory family consists of the 4 planned series contrasts at $H_{12}$ delayed response on EURUSD. To prevent researcher degrees of freedom or post-hoc threshold manipulation:
1. **Full Family ($K=4$) Penalty**: Underpowered/omitted series do not reduce the multiplicity penalty; they consume error budget.
   - Bonferroni family threshold: $\alpha / 4 = 0.0125$.
   - Holm-Bonferroni step-down: starts with base $m = 4$.
2. **Evaluated Subset ($K=2$)**: Holm-Bonferroni and Benjamini-Hochberg FDR across the evaluated series reported side-by-side for complete transparency.
3. All other horizon, matrix, and pair analyses form an unadjusted exploratory atlas.

---

## 9. Simultaneous Releases & Causal Attribution Policy

- Co-releases sharing currency and timestamp will be identified using the audited `detectSimultaneousReleases` algorithm.
- Pairwise directional coherence (aligned vs conflicting deltas between explicitly defined indicator pairs) will be recorded. Arbitrary multi-release combinations remain `UNCLASSIFIED`.
- **Strict Attribution Boundary**: When multiple releases occur simultaneously, observed FX moves reflect the bundled information shock. The study **prohibits** attributing price behavior exclusively to a single indicator headline, and pairwise coherence labels must not be cited as proof that an entire multi-release bundle agrees.

---

## 10. Prior Historical Outcome Disclosures

The audit report [`CODEX_QUANT_AUDIT.md`](file:///c:/dev/Fyodor%20Math%20Lab/GEMINI/docs/CODEX_QUANT_AUDIT.md) previously exposed seven historical observations. Their split status:
- Value ID `229745` (USD CPI, 2025-08-12): **Confirmation** (Sealed)
- Value ID `229744` (USD CPI, 2025-07-15): **Confirmation** (Sealed)
- Value ID `229741` (USD CPI, 2025-04-10): **Confirmation** (Sealed)
- Value ID `229757` (USD Core CPI, 2025-08-12): **Confirmation** (Sealed)
- Value ID `115719` (USD Core PCE, 2020-10-01): **Exploration** (Known prior exposure; disclosed sensitivity item)
- Value ID `118422` (Eurozone PMI, 2020-09-23): **Exploration** (EUR series outside primary USD family)
- Value ID `277623` (USD NFP, 2026-09-04): **Confirmation** (Sealed)

All Confirmation prior-exposure records will be excluded from the primary Confirmation evaluation and retained only as disclosed sensitivity checks.
