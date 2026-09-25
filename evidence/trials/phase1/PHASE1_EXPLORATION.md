# Phase 1 Exploration Research Report: Macroeconomic Release Drift Analysis

- **Document Version**: 1.2.0 (Automated Read-Only Serialization & Forensic Verification)
- **Generated At**: 2026-09-24T01:15:26.872Z
- **Baseline Commit**: `7ba2530`
- **Data Source**: `tools/mt5/FyodorResearchExport_v3_20260923_234930_server`
- **Calendar SHA-256**: `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` (Verified match across 123,054 records)
- **Candle Verification Status**: Calendar hash was cryptographically verified; candle CSV contents were discovered and loaded from the exported candles directory, not hash-pinned at run time.
- **Chronological Split Boundary**: `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`)
- **Exploration Window**: Complete history up to `2022-12-31 23:59:59`
- **Confirmation Status**: **SEALED**. Zero post-2022 event releases were evaluated, and zero Confirmation returns or performance metrics were calculated or inspected.

---

## 1. Executive Summary & Epistemic Finding

### Core Research Question
> *Do scheduled macroeconomic releases show repeatable directional FX behavior over subsequent complete H1 bars, beyond the immediate announcement response?*

### Exploration Finding: **Fail to Reject the Null Hypothesis (No Convincing Signal Detected in This Sample)**
Under the pre-registered protocol, empirical analysis of macroeconomic releases in the Exploration period yields **no convincing signal detected in this sample** to support repeatable post-announcement directional drift on either EURUSD or USDJPY.

1. **Predeclared Exploration Primary Contrasts at $H_{12}$ Delayed Response (EURUSD)**:
   - **USD CPI m/m** ($N_{+3}=11, N_{-3}=7$): The observed mean difference is **negative** (-12.3\text{ bps}, with USD showing lower delayed returns following positive surprises relative to negative surprises). The exact combinatorial permutation test p-value across all 31,824 partitions is **$p = 0.3009$**, and the Mann-Whitney U rank-sum test p-value is **$p = 0.2771$**. Multiplicity-adjusted Holm p-values are **$p = 1.0000$** (full $K=4$ family) and **$p = 0.6018$** (evaluated $K=2$ subset).
   - **USD Nonfarm Payrolls** ($N_{+3}=20, N_{-3}=7$): The observed mean difference is **-2.0\text{ bps}** (median difference +8.8\text{ bps}). The seeded Monte Carlo permutation test (100,000 trials, seed `42840030`) p-value is **$p = 0.8734$**, and the Mann-Whitney U test p-value is **$p = 0.6381$**. Multiplicity-adjusted Holm p-values are **$p = 1.0000$** ($K=4$) and **$p = 0.8734$** ($K=2$).
   - **USD Core CPI m/m** ($N_{+3}=4 < 5, N_{-3}=11$): **Formally Underpowered**. Omitted from inferential hypothesis testing per pre-registered rule ($\min(N_+, N_-) < 5$). Descriptively, the mean difference is -2.8\text{ bps}, and chronological stability analysis revealed that the sign of the difference inverted between early (-18.2\text{ bps}) and late (+36.8\text{ bps}) halves.
   - **USD Core PCE m/m** ($N_{+3}=6, N_{-3}=2 < 5$): **Formally Underpowered**. Omitted from inferential hypothesis testing.
2. **Predefined Secondary Horizons**:
   - Neither $H_4$ delayed (short-range post-shock absorption) nor $H_{24}$ delayed (daily cycle) reached significance on EURUSD (all raw permutation $p \in [0.2020, 0.5304]$).
   - Cumulative returns ($P_0 \to H_1$ and $P_0 \to H_{12}$) similarly failed to reject the null hypothesis (raw $p \in [0.2261, 0.7872]$).
3. **Exploratory 5×5 Interaction Matrix**:
   - Evaluating the Cartesian product of Surprise ($\pm 3, \pm 2, \pm 1$) and Momentum ($\pm 3, \pm 2, \pm 1$) shows substantial sample sparsity (10 of 25 cells for CPI and 13 of 25 cells for NFP contain zero observations) and no monotonic trend reinforcement.
4. **Epistemic Synthesis**:
   - In quantitative research, recording no convincing signal detected in this sample is an informative and successful outcome. The Exploration data indicates that the conjecture of post-announcement directional drift cannot be supported empirically on these major currency pairs.

---

## 2. Integrity & Boundary Verification

Prior to return calculations, data integrity and chronological boundaries were audited:

| Audit Item | Verified Property | Status |
| :--- | :--- | :--- |
| **Calendar SHA-256** | `76062b8f6747d38b530d086780f2dfcf0b0bde59690bfdf4458c7519d4e6be2e` | **MATCH** |
| **Export Schema** | `fyodor-mt5-research-export/3.1.0` | **MATCH** |
| **Total Export Records** | 123,054 calendar rows; 51 H1 candle files | **VERIFIED** |
| **Candle Hash-Pinning Caveat** | Calendar hash was verified; candle CSV contents were not hash-pinned at run time | **DOCUMENTED** |
| **Split Boundary** | `2023-01-01 00:00:00` broker trade-server time (`timestamp = 1672531200`) | **FROZEN** |
| **EURUSD $H_{42}$ Crossings** | Exploration releases whose 42-hour close reached into Confirmation | **0 violations** |
| **USDJPY $H_{42}$ Crossings** | Exploration releases whose 42-hour close reached into Confirmation | **0 violations** |
| **Pair-Specific Boundary Filter** | Split filtering executed separately per pair prior to return calculation | **ENFORCED** |
| **Confirmation Data** | Post-2022 release outcomes and return series | **SEALED (Uncalculated)** |

---

## 3. Predeclared Exploration Primary Contrasts ($H_{12}$ Delayed on EURUSD)

The primary predeclared inferential family tests whether Large Positive Surprises ($+3$) produce higher delayed event-currency returns than Large Negative Surprises ($-3$) on EURUSD from the close of the first complete post-release hour ($H_1$) to the close of hour 12 ($H_{12}$).

### Primary Hypothesis Test Summary Table

| Series Name | Series Key | Eligible $N$ | $+3$ $N$ | $-3$ $N$ | Mean Diff | Median Diff | Permutation $p$ | Method | Rank-Sum $p$ | Holm $p$ ($K=4$) | BH FDR $p$ ($K=4$) | Power Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **USD CPI m/m** | `USD:US:840030005:r0` | 47 | 11 | 7 | **-12.3\text{ bps}** | -11.0\text{ bps} | **0.3009** | Exact (31,824) | **0.2771** | **1.0000** | **1.0000** | **ADEQUATE (Fail to reject null)** |
| **USD Nonfarm Payrolls** | `USD:US:840030016:r0` | 48 | 20 | 7 | **-2.0\text{ bps}** | +8.8\text{ bps} | **0.8734** | Monte Carlo (100k) | **0.6381** | **1.0000** | **1.0000** | **ADEQUATE (Fail to reject null)** |
| **USD Core CPI m/m** | `USD:US:840030006:r0` | 35 | 4 | 11 | **-2.8\text{ bps}** | -8.1\text{ bps} | *null* | Omitted (N+ < 5) | *null* | *null* | *null* | **UNDERPOWERED (Descriptive only)** |
| **USD Core PCE m/m** | `USD:US:840010001:r0` | 32 | 6 | 2 | **-66.8\text{ bps}** | -73.2\text{ bps} | *null* | Omitted (N- < 5) | *null* | *null* | *null* | **UNDERPOWERED (Descriptive only)** |

*Multiplicity Note*:
- Evaluated Subset ($K=2$): USD CPI Holm $p = 0.6018$, Benjamini-Hochberg FDR $p = 0.6018$; USD NFP Holm $p = 0.8734$, Benjamini-Hochberg FDR $p = 0.8734$.
- Full Family ($K=4$) Penalty: Because the two underpowered series consume error budget, both Holm-Bonferroni and Benjamini-Hochberg adjusted p-values are capped at 1.0000.

---

### Detailed Series Distributional Breakdown

#### USD CPI m/m (`USD:US:840030005:r0`)
- **Large Positive Surprise ($+3$, $N=11$)**:
  - Mean: +0.001004 (+10.0\text{ bps})
  - Median: +0.000718 (+7.2\text{ bps})
  - Standard Deviation: +0.002731
  - Range: [-0.003069, +0.005058]
  - Percentiles: P10 = -0.002134, P25 = -0.001057, P50 = +0.000718, P75 = +0.003025, P90 = +0.004360
- **Large Negative Surprise ($-3$, $N=7$)**:
  - Mean: +0.002233 (+22.3\text{ bps})
  - Median: +0.001815 (+18.2\text{ bps})
  - Standard Deviation: +0.001670
  - Range: [+0.000732, +0.005392]
  - Percentiles: P10 = +0.000773, P25 = +0.001086, P50 = +0.001815, P75 = +0.002761, P90 = +0.004232
- **Contrast**:
  - Difference in Means ($\bar{r}_{+3} - \bar{r}_{-3}$): -0.001230 (-12.3\text{ bps})
  - Difference in Medians ($\tilde{r}_{+3} - \tilde{r}_{-3}$): -0.001097 (-11.0\text{ bps})
  - Permutation Test (Exact combinatorial permutation test across all 31,824 partitions): $p = 0.3009$ (raw: 0.30090498)
  - Mann-Whitney U Test: $p = 0.2771$ (raw: 0.27712520)
  - **Verdict**: Fail to reject null hypothesis. No convincing signal detected in this sample.

#### USD Nonfarm Payrolls (`USD:US:840030016:r0`)
- **Large Positive Surprise ($+3$, $N=20$)**:
  - Mean: -0.000229 (-2.3\text{ bps})
  - Median: -0.000198 (-2.0\text{ bps})
  - Standard Deviation: +0.002798
  - Range: [-0.007660, +0.006759]
  - Percentiles: P10 = -0.002751, P25 = -0.001241, P50 = -0.000198, P75 = +0.001110, P90 = +0.002133
- **Large Negative Surprise ($-3$, $N=7$)**:
  - Mean: -0.000028 (-0.3\text{ bps})
  - Median: -0.001075 (-10.7\text{ bps})
  - Standard Deviation: +0.002934
  - Range: [-0.002330, +0.006183]
  - Percentiles: P10 = -0.002033, P25 = -0.001821, P50 = -0.001075, P75 = +0.000335, P90 = +0.002697
- **Contrast**:
  - Difference in Means ($\bar{r}_{+3} - \bar{r}_{-3}$): -0.000202 (-2.0\text{ bps})
  - Difference in Medians ($\tilde{r}_{+3} - \tilde{r}_{-3}$): +0.000876 (+8.8\text{ bps})
  - Permutation Test (Seeded Monte Carlo permutation test with 100,000 iterations (seed: 42840030) across 888,030 theoretical combinations): $p = 0.8734$ (raw: 0.87337127)
  - Mann-Whitney U Test: $p = 0.6381$ (raw: 0.63814726)
  - **Verdict**: Fail to reject null hypothesis. No convincing signal detected in this sample.

#### USD Core CPI m/m (`USD:US:840030006:r0`)
- **Large Positive Surprise ($+3$, $N=4$)**:
  - Mean: +0.000311 (+3.1\text{ bps})
  - Median: -0.000225 (-2.3\text{ bps})
  - Standard Deviation: +0.002917
  - Range: [-0.002134, +0.003830]
  - Percentiles: P10 = -0.002106, P25 = -0.002064, P50 = -0.000225, P75 = +0.002149, P90 = +0.003158
- **Large Negative Surprise ($-3$, $N=11$)**:
  - Mean: +0.000588 (+5.9\text{ bps})
  - Median: +0.000584 (+5.8\text{ bps})
  - Standard Deviation: +0.001089
  - Range: [-0.001870, +0.002064]
  - Percentiles: P10 = -0.000554, P25 = +0.000410, P50 = +0.000584, P75 = +0.001136, P90 = +0.001815
- **Contrast**:
  - Difference in Means ($\bar{r}_{+3} - \bar{r}_{-3}$): -0.000277 (-2.8\text{ bps})
  - Difference in Medians ($\tilde{r}_{+3} - \tilde{r}_{-3}$): -0.000810 (-8.1\text{ bps})
  - **Power Classification**: **UNDERPOWERED** (Underpowered for formal hypothesis testing: min(N+, N-) = min(4, 11) < 5. Reported descriptively only.)
  - Chronological Stability: Sign of mean difference flipped between earlier and later Exploration periods (chronologically unstable).

#### USD Core PCE m/m (`USD:US:840010001:r0`)
- **Large Positive Surprise ($+3$, $N=6$)**:
  - Mean: -0.000174 (-1.7\text{ bps})
  - Median: -0.000817 (-8.2\text{ bps})
  - Standard Deviation: +0.002431
  - Range: [-0.002435, +0.003424]
  - Percentiles: P10 = -0.002333, P25 = -0.002152, P50 = -0.000817, P75 = +0.001443, P90 = +0.002627
- **Large Negative Surprise ($-3$, $N=2$)**:
  - Mean: +0.006506 (+65.1\text{ bps})
  - Median: +0.006506 (+65.1\text{ bps})
  - Standard Deviation: +0.009456
  - Range: [-0.000180, +0.013192]
  - Percentiles: P10 = +0.001157, P25 = +0.003163, P50 = +0.006506, P75 = +0.009849, P90 = +0.011855
- **Contrast**:
  - Difference in Means ($\bar{r}_{+3} - \bar{r}_{-3}$): -0.006681 (-66.8\text{ bps})
  - Difference in Medians ($\tilde{r}_{+3} - \tilde{r}_{-3}$): -0.007323 (-73.2\text{ bps})
  - **Power Classification**: **UNDERPOWERED** (Underpowered for formal hypothesis testing: min(N+, N-) = min(6, 2) < 5. Reported descriptively only.)
  - Chronological Stability: Insufficient sample to determine stability sign agreement.

---

## 4. Predefined Secondary Contrasts & Horizon Trajectories

To test whether price adjustments occur across alternative time horizons, four secondary contrasts were pre-registered and evaluated across EURUSD:

### Secondary Contrast Results on EURUSD

| Series Name | Contrast Horizon | Type | Group $+3$ Mean | Group $-3$ Mean | Mean Difference | Permutation $p$ | Permutation Method |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **USD CPI** | $H4$ | Delayed | +0.000080 | +0.001619 | -0.001539 (-15.4\text{ bps}) | **0.2020** | Exact (31,824) |
| **USD CPI** | $H24$ | Delayed | +0.000813 | +0.002253 | -0.001440 (-14.4\text{ bps}) | **0.5304** | Exact (31,824) |
| **USD CPI** | $H1$ | Cumulative | +0.000662 | -0.000148 | +0.000810 (+8.1\text{ bps}) | **0.3857** | Exact (31,824) |
| **USD CPI** | $H12$ | Cumulative | +0.001668 | +0.002084 | -0.000416 (-4.2\text{ bps}) | **0.7872** | Exact (31,824) |
| **USD NFP** | $H4$ | Delayed | -0.000300 | +0.000361 | -0.000662 (-6.6\text{ bps}) | **0.4301** | Monte Carlo (100k) |
| **USD NFP** | $H24$ | Delayed | -0.000520 | +0.000650 | -0.001170 (-11.7\text{ bps}) | **0.4958** | Monte Carlo (100k) |
| **USD NFP** | $H1$ | Cumulative | -0.000338 | +0.000632 | -0.000970 (-9.7\text{ bps}) | **0.2261** | Monte Carlo (100k) |
| **USD NFP** | $H12$ | Cumulative | -0.000569 | +0.000603 | -0.001172 (-11.7\text{ bps}) | **0.3395** | Monte Carlo (100k) |

### Key Observations:
1. **Compounding Identity and Price Isolation**:
   - In USD CPI, the initial $H_1$ cumulative reaction showed a nominal mean difference of +8.1\text{ bps}, while at $H_{12}$ cumulative the difference was -4.2\text{ bps}.
   - Isolating post-$H_1$ price movement through delayed returns demonstrates that from hour 1 close to hour 12 close, USD delayed returns following positive surprises were -12.3\text{ bps} relative to negative surprises.
2. **Short-Range vs. Daily Absorption**:
   - Neither the 4-hour window ($H_4$) nor the 24-hour cycle ($H_{24}$) yielded evidence of directional persistence.
   - At no secondary horizon did any contrast reach statistical significance ($p < 0.05$).

---

## 5. Exploratory 25-Cell Interaction Matrices ($H_{12}$ Delayed)

To explore non-linear interactions between announcement shock (Surprise) and prevailing baseline context (Momentum), the full $5 \times 5$ matrix ($\{+3,+2,+1,-2,-3\} \times \{+3,+2,+1,-2,-3\}$) was computed at $H_{12}$ delayed response on EURUSD.

### USD CPI m/m (`840030005:r0`) Complete 25-Cell Matrix

| Cell Key | Surprise Score | Momentum Score | Cell $N$ | Mean Return | Mean Return (bps) | Median Return | Positive Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `S+3_M+3` | 3 | 3 | **4** | +0.002028 | +20.3\text{ bps} | +0.002539 | 75.0% |
| `S+3_M+2` | 3 | 2 | **6** | +0.000844 | +8.4\text{ bps} | +0.001087 | 66.7% |
| `S+3_M+1` | 3 | 1 | **1** | -0.002134 | -21.3\text{ bps} | -0.002134 | 0.0% |
| `S+3_M-2` | 3 | -2 | **0** | *null* | *null* | *null* | *null* |
| `S+3_M-3` | 3 | -3 | **0** | *null* | *null* | *null* | *null* |
| `S+2_M+3` | 2 | 3 | **2** | +0.001047 | +10.5\text{ bps} | +0.001047 | 50.0% |
| `S+2_M+2` | 2 | 2 | **5** | +0.000226 | +2.3\text{ bps} | -0.001426 | 40.0% |
| `S+2_M+1` | 2 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S+2_M-2` | 2 | -2 | **5** | -0.000479 | -4.8\text{ bps} | +0.000540 | 80.0% |
| `S+2_M-3` | 2 | -3 | **1** | -0.000554 | -5.5\text{ bps} | -0.000554 | 0.0% |
| `S+1_M+3` | 1 | 3 | **0** | *null* | *null* | *null* | *null* |
| `S+1_M+2` | 1 | 2 | **2** | -0.002841 | -28.4\text{ bps} | -0.002841 | 0.0% |
| `S+1_M+1` | 1 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S+1_M-2` | 1 | -2 | **2** | -0.001621 | -16.2\text{ bps} | -0.001621 | 0.0% |
| `S+1_M-3` | 1 | -3 | **0** | *null* | *null* | *null* | *null* |
| `S-2_M+3` | -2 | 3 | **0** | *null* | *null* | *null* | *null* |
| `S-2_M+2` | -2 | 2 | **1** | -0.007556 | -75.6\text{ bps} | -0.007556 | 0.0% |
| `S-2_M+1` | -2 | 1 | **3** | -0.000844 | -8.4\text{ bps} | -0.001104 | 0.0% |
| `S-2_M-2` | -2 | -2 | **7** | +0.000779 | +7.8\text{ bps} | +0.001089 | 85.7% |
| `S-2_M-3` | -2 | -3 | **0** | *null* | *null* | *null* | *null* |
| `S-3_M+3` | -3 | 3 | **0** | *null* | *null* | *null* | *null* |
| `S-3_M+2` | -3 | 2 | **1** | +0.005392 | +53.9\text{ bps} | +0.005392 | 100.0% |
| `S-3_M+1` | -3 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S-3_M-2` | -3 | -2 | **2** | +0.000766 | +7.7\text{ bps} | +0.000766 | 100.0% |
| `S-3_M-3` | -3 | -3 | **4** | +0.002177 | +21.8\text{ bps} | +0.001939 | 100.0% |

### USD Nonfarm Payrolls (`840030016:r0`) Complete 25-Cell Matrix

| Cell Key | Surprise Score | Momentum Score | Cell $N$ | Mean Return | Mean Return (bps) | Median Return | Positive Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `S+3_M+3` | 3 | 3 | **7** | -0.000084 | -0.8\text{ bps} | -0.000062 | 42.9% |
| `S+3_M+2` | 3 | 2 | **9** | +0.000051 | +0.5\text{ bps} | +0.000866 | 55.6% |
| `S+3_M+1` | 3 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S+3_M-2` | 3 | -2 | **3** | -0.000441 | -4.4\text{ bps} | -0.001152 | 33.3% |
| `S+3_M-3` | 3 | -3 | **1** | -0.003135 | -31.3\text{ bps} | -0.003135 | 0.0% |
| `S+2_M+3` | 2 | 3 | **2** | +0.000276 | +2.8\text{ bps} | +0.000276 | 50.0% |
| `S+2_M+2` | 2 | 2 | **2** | -0.004141 | -41.4\text{ bps} | -0.004141 | 50.0% |
| `S+2_M+1` | 2 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S+2_M-2` | 2 | -2 | **7** | +0.002143 | +21.4\text{ bps} | +0.001130 | 57.1% |
| `S+2_M-3` | 2 | -3 | **2** | -0.001278 | -12.8\text{ bps} | -0.001278 | 50.0% |
| `S+1_M+3` | 1 | 3 | **0** | *null* | *null* | *null* | *null* |
| `S+1_M+2` | 1 | 2 | **0** | *null* | *null* | *null* | *null* |
| `S+1_M+1` | 1 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S+1_M-2` | 1 | -2 | **0** | *null* | *null* | *null* | *null* |
| `S+1_M-3` | 1 | -3 | **0** | *null* | *null* | *null* | *null* |
| `S-2_M+3` | -2 | 3 | **0** | *null* | *null* | *null* | *null* |
| `S-2_M+2` | -2 | 2 | **1** | -0.001638 | -16.4\text{ bps} | -0.001638 | 0.0% |
| `S-2_M+1` | -2 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S-2_M-2` | -2 | -2 | **5** | -0.000066 | -0.7\text{ bps} | -0.000519 | 40.0% |
| `S-2_M-3` | -2 | -3 | **2** | -0.000430 | -4.3\text{ bps} | -0.000430 | 50.0% |
| `S-3_M+3` | -3 | 3 | **0** | *null* | *null* | *null* | *null* |
| `S-3_M+2` | -3 | 2 | **0** | *null* | *null* | *null* | *null* |
| `S-3_M+1` | -3 | 1 | **0** | *null* | *null* | *null* | *null* |
| `S-3_M-2` | -3 | -2 | **0** | *null* | *null* | *null* | *null* |
| `S-3_M-3` | -3 | -3 | **7** | -0.000028 | -0.3\text{ bps} | -0.001075 | 42.9% |

### Analytical Synthesis of 5×5 Matrices:
1. **Severe Empirical Sparsity**: 10 of 25 cells for CPI and 13 of 25 cells for NFP contain zero historical observations. Specific sub-cell intersections represent small samples ($N \le 4$).
2. **Absence of Monotonic Gradient**: In CPI, extreme negative surprise with negative momentum (`S-3_M-3`) exhibited an average delayed USD return of +21.8\text{ bps} ($N=4$), comparable to extreme positive surprise with positive momentum (`S+3_M+3`, +20.3\text{ bps}, $N=4$). In NFP, both extreme diagonal cells clustered near zero (-0.8\text{ bps} and -0.3\text{ bps}).

---

## 6. Co-Release Pairwise Coherence & Simultaneous Attribution

Evaluating simultaneous releases sharing currency and timestamp across the complete loaded calendar:

### Complete Co-Release Coherence Reconciliation Table ($H_{12}$ Delayed on EURUSD)

Every eligible historical observation is explicitly accounted for across the classification categories:

| Series Name | Eligible $N$ | Pairwise Coherent | Pairwise Conflicting | Isolated Releases | Unclassified Simultaneous | Neutral Target Surprise | Complete Sum Check | Coherence Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **USD CPI m/m** | **47** | $N=21$ (+9.7\text{ bps}) | $N=12$ (+6.7\text{ bps}) | $N=0$ (*null*) | $N=10$ (-4.8\text{ bps}) | $N=4$ (-22.3\text{ bps}) | 21 + 12 + 0 + 10 + 4 = **47** | Coherent and conflicting pairwise subsets show small nominal difference (+3.0 bps). |
| **USD Core CPI m/m** | **35** | $N=18$ (+9.1\text{ bps}) | $N=8$ (+14.2\text{ bps}) | $N=0$ (*null*) | $N=1$ (-27.3\text{ bps}) | $N=8$ (-5.5\text{ bps}) | 18 + 8 + 0 + 1 + 8 = **35** | Conflicting pairwise observations showed higher average USD return than coherent observations (+14.2 vs +9.1 bps). |
| **USD Core PCE m/m** | **32** | $N=0$ (*null*) | $N=0$ (*null*) | $N=0$ (*null*) | $N=28$ (+6.6\text{ bps}) | $N=4$ (+10.4\text{ bps}) | 0 + 0 + 0 + 28 + 4 = **32** | No modeled pairwise partner indicator. All simultaneous releases remain unclassified. |
| **USD Nonfarm Payrolls** | **48** | $N=24$ (+1.9\text{ bps}) | $N=14$ (+1.1\text{ bps}) | $N=0$ (*null*) | $N=10$ (-8.9\text{ bps}) | $N=0$ (*null*) | 24 + 14 + 0 + 10 + 0 = **48** | Pairwise coherent and conflicting subsets show negligible difference (+0.8 bps). |

### Causal Attribution Constraints:
- **Pairwise Definitions**: Coherence labels apply strictly to predefined economic pairings (Headline CPI vs. Core CPI; NFP vs. Unemployment Rate) and do not represent proof that an entire multi-release release bundle agreed. Generic same-sign coherence across unrelated indicators was explicitly excluded.
- **NEUTRAL Category**: Accounts for observations where the target indicator surprise delta was exact-zero or null, distinguishing them from unclassified simultaneous releases.
- **Absence of Isolated Events**: In the Exploration dataset, **zero releases of USD CPI or USD NFP occurred in isolation**. Every release was accompanied by at least one concurrent economic indicator. Observed market behavior reflects the bundled announcement shock rather than the isolated influence of a single headline.

---

## 7. Cross-Pair Examination: USDJPY

To evaluate whether EURUSD outcomes reflected pair-specific idiosyncrasies, the identical protocol was executed on USDJPY ($H_{12}$ delayed, base currency USD):

| Series Name | Eligible $N$ | $+3$ $N$ | $-3$ $N$ | Mean Diff | Median Diff | Permutation $p$ | Method | Rank-Sum $p$ | Power Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| **USD CPI m/m** | 47 | 11 | 7 | +17.4\text{ bps} | +31.4\text{ bps} | **0.0757** | Exact (31,824) | **0.1236** | **ADEQUATE (Fails to reach alpha=0.05)** |
| **USD Nonfarm Payrolls** | 48 | 20 | 7 | -29.2\text{ bps} | -27.5\text{ bps} | **0.2370** | Monte Carlo (100k) | **0.2132** | **ADEQUATE (Fails to reject null)** |
| **USD Core CPI m/m** | 35 | 4 | 11 | +4.9\text{ bps} | +18.8\text{ bps} | *null* | Omitted (N+ < 5) | *null* | **UNDERPOWERED (Descriptive only)** |
| **USD Core PCE m/m** | 32 | 6 | 2 | -71.5\text{ bps} | -72.9\text{ bps} | *null* | Omitted (N- < 5) | *null* | **UNDERPOWERED (Descriptive only)** |

### Synthesis:
- On USDJPY, USD CPI yielded an unadjusted permutation p-value of $p = 0.0757$ (rank-sum $p = 0.1236$), failing to reach statistical significance.
- USD NFP on USDJPY showed a sample mean difference of -29.2\text{ bps} with $p = 0.2370$.
- Cross-pair results show no coherent directional drift.

---

## 8. Forensic Artifacts Preserved

1. **Exploration Data File**: [`lab/research/phase1_exploration.json`](file:///c:/dev/Fyodor%20Math%20Lab/GEMINI/lab/research/phase1_exploration.json) (2.36 MB). Preserves complete series outcomes, 25-cell matrices, and all individual observation records including raw input values, assigned scores, $P_0$, $H_1$ close, cumulative paths ($H_1$–$H_{42}$), delayed paths ($H_2$–$H_{42}$), and gap flags.
2. **Preflight Manifest**: [`lab/research/phase1_preflight.json`](file:///c:/dev/Fyodor%20Math%20Lab/GEMINI/lab/research/phase1_preflight.json).
3. **Protocol Specification**: [`lab/research/PHASE1_PROTOCOL.md`](file:///c:/dev/Fyodor%20Math%20Lab/GEMINI/lab/research/PHASE1_PROTOCOL.md) (v1.1.0).

---

## 9. Methodological Considerations & Research Integrity

1. **Sample Size Constraints and Noise**:
   With only 11 positive CPI surprises and 7 negative CPI surprises across historical data, statistical power is inherently constrained. Subdividing samples into multi-variable interaction cells rapidly leads to small sample sizes ($N \le 4$), where observed return variations reflect idiosyncratic noise rather than structural market phenomena.
2. **Practical Implementation Considerations**:
   In live market conditions, spreads, intrahour volatility, execution latency, and financing costs present substantial practical hurdles that would further attenuate small nominal returns, even had statistical significance been observed.
3. **Preservation of the Confirmation Dataset**:
   The Confirmation dataset (`2023-01-01` to `2026-09-23`) remains uninspected and sealed. Because the Exploration analysis failed to reject the null hypothesis across primary and secondary specifications, there is no validated pattern to confirm. Opening Confirmation under these circumstances would constitute post-hoc data dredging rather than independent validation.
