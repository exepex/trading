# Protocol v4: item E option 2, crash cuts measured (`tools/v4_crash_cut.py`)

## Cost: real rolling 2019-26 windows removed

| question | n | cut | removed | judgeable before | judgeable after | removed windows start |
|---|---|---|---|---|---|---|
| v1_rv_next_session | 125 | vix_above_25 | 7.6% | 100% | 92% | 2019-10-23 to 2020-05-12 |
| v1_rv_next_session | 125 | big_share_above_10pct | 12.6% | 100% | 87% | 2019-09-16 to 2022-02-15 |
| v1_rv_next_session | 250 | vix_above_25 | 8.9% | 100% | 91% | 2019-08-30 to 2020-04-08 |
| v1_rv_next_session | 250 | big_share_above_10pct | 15.6% | 100% | 84% | 2019-03-25 to 2020-04-17 |
| v2_rv_next_5_sessions | 125 | vix_above_25 | 7.6% | 100% | 92% | 2019-10-23 to 2020-05-12 |
| v2_rv_next_5_sessions | 125 | big_share_above_10pct | 12.6% | 100% | 87% | 2019-09-16 to 2022-02-15 |
| v2_rv_next_5_sessions | 250 | vix_above_25 | 8.9% | 100% | 91% | 2019-08-30 to 2020-04-08 |
| v2_rv_next_5_sessions | 250 | big_share_above_10pct | 15.6% | 100% | 84% | 2019-03-25 to 2020-04-17 |
| v6_abs_move_2pct_next_session | 125 | vix_above_25 | 7.6% | 50% | 42% | 2019-10-23 to 2020-05-12 |
| v6_abs_move_2pct_next_session | 125 | big_share_above_10pct | 12.6% | 50% | 37% | 2019-09-16 to 2022-02-15 |
| v6_abs_move_2pct_next_session | 250 | vix_above_25 | 8.9% | 78% | 70% | 2019-08-30 to 2020-04-08 |
| v6_abs_move_2pct_next_session | 250 | big_share_above_10pct | 15.6% | 78% | 63% | 2019-03-25 to 2020-04-17 |
| v6_abs_move_2pct_within_5_sessions | 125 | vix_above_25 | 7.6% | 50% | 43% | 2019-10-23 to 2020-05-12 |
| v6_abs_move_2pct_within_5_sessions | 125 | big_share_above_10pct | 12.7% | 50% | 37% | 2019-09-16 to 2022-02-15 |
| v6_abs_move_2pct_within_5_sessions | 250 | vix_above_25 | 8.9% | 78% | 69% | 2019-08-30 to 2020-04-08 |
| v6_abs_move_2pct_within_5_sessions | 250 | big_share_above_10pct | 15.7% | 78% | 63% | 2019-03-25 to 2020-04-17 |

## Re-measured: rates among kept series (paired with `v4_regime_stress.md`)

Marks as in `v4_regime_stress.md`: **bold** false verdict above nominal + 2 Monte Carlo SE of the kept count, *italic* above it but the regime's truth (local = the whole stretch's true improvement). The kept median estimate is the median measured improvement of the kept series: below the minimum effect, a "no" there agrees with what the kept (calmer) windows show. A stretch with almost nothing kept says little.

| question | stretch | n | orientation | cut | kept | claim | futility | local (futility null) | kept median estimate (futility null) |
|---|---|---|---|---|---|---|---|---|---|
| v1_rv_next_session | full | 125 | as measured | vix_above_25 | 98.8% | 0.04% | 0.00% | +0.030 | +0.129 |
| v1_rv_next_session | full | 125 | as measured | big_share_above_10pct | 89.2% | 0.05% | 0.00% | +0.030 | +0.124 |
| v1_rv_next_session | full | 125 | flipped | vix_above_25 | 98.7% | 0.00% | 1.50% | +0.030 | -0.068 |
| v1_rv_next_session | full | 125 | flipped | big_share_above_10pct | 89.2% | 0.00% | 1.58% | +0.030 | -0.062 |
| v1_rv_next_session | full | 250 | as measured | vix_above_25 | 99.9% | 0.05% | 0.00% | +0.030 | +0.090 |
| v1_rv_next_session | full | 250 | as measured | big_share_above_10pct | 93.9% | 0.05% | 0.00% | +0.030 | +0.088 |
| v1_rv_next_session | full | 250 | flipped | vix_above_25 | 99.9% | 0.00% | 2.25% | +0.030 | -0.029 |
| v1_rv_next_session | full | 250 | flipped | big_share_above_10pct | 94.0% | 0.00% | 2.29% | +0.030 | -0.026 |
| v1_rv_next_session | busy 125 | 125 | as measured | vix_above_25 | 18.8% | 0.00% | 0.00% | +0.235 | +0.184 |
| v1_rv_next_session | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.00% | 0.00% | +0.235 | +0.143 |
| v1_rv_next_session | busy 125 | 125 | flipped | vix_above_25 | 18.7% | 0.00% | 0.01% | -0.182 | -0.121 |
| v1_rv_next_session | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | 0.00% | 0.00% | -0.182 | -0.071 |
| v1_rv_next_session | busy 125 | 250 | as measured | vix_above_25 | 9.9% | 0.00% | 0.00% | +0.235 | +0.191 |
| v1_rv_next_session | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 0.00% | +0.235 | +0.138 |
| v1_rv_next_session | busy 125 | 250 | flipped | vix_above_25 | 9.7% | 0.00% | 0.04% | -0.182 | -0.128 |
| v1_rv_next_session | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | 0.00% | -0.182 | -0.067 |
| v1_rv_next_session | busy 250 | 125 | as measured | vix_above_25 | 32.7% | 0.00% | 0.00% | +0.155 | +0.105 |
| v1_rv_next_session | busy 250 | 125 | as measured | big_share_above_10pct | 19.5% | 0.00% | 0.00% | +0.155 | +0.085 |
| v1_rv_next_session | busy 250 | 125 | flipped | vix_above_25 | 32.7% | 0.00% | 0.06% | -0.099 | -0.046 |
| v1_rv_next_session | busy 250 | 125 | flipped | big_share_above_10pct | 19.7% | 0.00% | 0.17% | -0.099 | -0.019 |
| v1_rv_next_session | busy 250 | 250 | as measured | vix_above_25 | 22.5% | 0.00% | 0.00% | +0.155 | +0.111 |
| v1_rv_next_session | busy 250 | 250 | as measured | big_share_above_10pct | 9.9% | 0.00% | 0.00% | +0.155 | +0.087 |
| v1_rv_next_session | busy 250 | 250 | flipped | vix_above_25 | 22.6% | 0.00% | 0.07% | -0.099 | -0.052 |
| v1_rv_next_session | busy 250 | 250 | flipped | big_share_above_10pct | 10.0% | 0.00% | 0.19% | -0.099 | -0.025 |
| v2_rv_next_5_sessions | full | 125 | as measured | vix_above_25 | 98.8% | 0.02% | 0.00% | +0.030 | +0.271 |
| v2_rv_next_5_sessions | full | 125 | as measured | big_share_above_10pct | 89.2% | 0.02% | 0.00% | +0.030 | +0.258 |
| v2_rv_next_5_sessions | full | 125 | flipped | vix_above_25 | 98.7% | 0.00% | 0.79% | +0.030 | -0.216 |
| v2_rv_next_5_sessions | full | 125 | flipped | big_share_above_10pct | 89.2% | 0.00% | 0.84% | +0.030 | -0.199 |
| v2_rv_next_5_sessions | full | 250 | as measured | vix_above_25 | 99.9% | 0.02% | 0.00% | +0.030 | +0.137 |
| v2_rv_next_5_sessions | full | 250 | as measured | big_share_above_10pct | 94.0% | 0.02% | 0.00% | +0.030 | +0.125 |
| v2_rv_next_5_sessions | full | 250 | flipped | vix_above_25 | 99.9% | 0.00% | 0.49% | +0.030 | -0.078 |
| v2_rv_next_5_sessions | full | 250 | flipped | big_share_above_10pct | 94.0% | 0.00% | 0.51% | +0.030 | -0.066 |
| v2_rv_next_5_sessions | busy 125 | 125 | as measured | vix_above_25 | 18.7% | 0.01% | 0.00% | +0.528 | +0.453 |
| v2_rv_next_5_sessions | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.00% | 0.00% | +0.528 | +0.472 |
| v2_rv_next_5_sessions | busy 125 | 125 | flipped | vix_above_25 | 18.8% | 0.00% | 0.16% | -0.500 | -0.419 |
| v2_rv_next_5_sessions | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | 0.00% | 0.64% | -0.500 | -0.428 |
| v2_rv_next_5_sessions | busy 125 | 250 | as measured | vix_above_25 | 9.8% | 0.00% | 0.00% | +0.528 | +0.461 |
| v2_rv_next_5_sessions | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 0.00% | +0.528 | +0.445 |
| v2_rv_next_5_sessions | busy 125 | 250 | flipped | vix_above_25 | 9.8% | 0.00% | 0.07% | -0.500 | -0.426 |
| v2_rv_next_5_sessions | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | 1.59% | -0.500 | -0.422 |
| v2_rv_next_5_sessions | busy 250 | 125 | as measured | vix_above_25 | 32.8% | 0.01% | 0.00% | +0.453 | +0.355 |
| v2_rv_next_5_sessions | busy 250 | 125 | as measured | big_share_above_10pct | 19.7% | 0.03% | 0.00% | +0.453 | +0.381 |
| v2_rv_next_5_sessions | busy 250 | 125 | flipped | vix_above_25 | 32.8% | 0.00% | 0.09% | -0.414 | -0.311 |
| v2_rv_next_5_sessions | busy 250 | 125 | flipped | big_share_above_10pct | 19.7% | 0.00% | 0.30% | -0.414 | -0.327 |
| v2_rv_next_5_sessions | busy 250 | 250 | as measured | vix_above_25 | 22.7% | 0.00% | 0.00% | +0.453 | +0.360 |
| v2_rv_next_5_sessions | busy 250 | 250 | as measured | big_share_above_10pct | 9.9% | 0.00% | 0.00% | +0.453 | +0.358 |
| v2_rv_next_5_sessions | busy 250 | 250 | flipped | vix_above_25 | 22.3% | 0.00% | 0.00% | -0.414 | -0.314 |
| v2_rv_next_5_sessions | busy 250 | 250 | flipped | big_share_above_10pct | 9.8% | 0.00% | 0.03% | -0.414 | -0.295 |
| v6_abs_move_2pct_next_session | full | 125 | as measured | vix_above_25 | 98.8% | 0.00% | 1.14% | +0.020 | -0.154 |
| v6_abs_move_2pct_next_session | full | 125 | as measured | big_share_above_10pct | 89.2% | 0.00% | 1.12% | +0.020 | -0.174 |
| v6_abs_move_2pct_next_session | full | 125 | flipped | vix_above_25 | 98.7% | 0.05% | 0.02% | +0.020 | +0.208 |
| v6_abs_move_2pct_next_session | full | 125 | flipped | big_share_above_10pct | 89.2% | 0.04% | 0.00% | +0.020 | +0.233 |
| v6_abs_move_2pct_next_session | full | 250 | as measured | vix_above_25 | 99.9% | 0.00% | 2.16% | +0.020 | -0.121 |
| v6_abs_move_2pct_next_session | full | 250 | as measured | big_share_above_10pct | 93.9% | 0.00% | 2.30% | +0.020 | -0.130 |
| v6_abs_move_2pct_next_session | full | 250 | flipped | vix_above_25 | 99.9% | 0.08% | 0.00% | +0.020 | +0.167 |
| v6_abs_move_2pct_next_session | full | 250 | flipped | big_share_above_10pct | 94.0% | 0.09% | 0.00% | +0.020 | +0.179 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | as measured | vix_above_25 | 18.8% | 0.00% | 1.12% | +0.340 | +0.095 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.00% | **5.70%** | +0.340 | -0.067 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | flipped | vix_above_25 | 18.7% | **0.37%** | 0.60% | -0.333 | -0.082 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | **3.41%** | 0.00% | -0.333 | +0.090 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | as measured | vix_above_25 | 9.9% | 0.00% | 0.02% | +0.340 | +0.180 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 2.56% | +0.340 | -0.034 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | flipped | vix_above_25 | 9.7% | 0.00% | 0.00% | -0.333 | -0.169 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | 0.00% | -0.333 | +0.073 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | as measured | vix_above_25 | 32.7% | 0.00% | **7.57%** | +0.236 | -0.071 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | as measured | big_share_above_10pct | 19.5% | 0.00% | 1.64% | +0.236 | -0.146 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | flipped | vix_above_25 | 32.7% | **0.30%** | 0.00% | -0.225 | +0.091 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | flipped | big_share_above_10pct | 19.7% | 0.02% | 0.00% | -0.225 | +0.177 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | as measured | vix_above_25 | 22.5% | 0.00% | 2.02% | +0.236 | -0.014 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | as measured | big_share_above_10pct | 9.9% | 0.00% | **4.36%** | +0.236 | -0.100 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | flipped | vix_above_25 | 22.6% | 0.02% | 0.00% | -0.225 | +0.032 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | flipped | big_share_above_10pct | 10.0% | 0.05% | 0.00% | -0.225 | +0.125 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | as measured | vix_above_25 | 98.7% | 0.00% | 1.03% | +0.020 | -0.077 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | as measured | big_share_above_10pct | 89.1% | 0.00% | 1.14% | +0.020 | -0.112 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | flipped | vix_above_25 | 98.7% | 0.05% | 0.21% | +0.020 | +0.129 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | flipped | big_share_above_10pct | 89.1% | 0.06% | 0.10% | +0.020 | +0.163 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | as measured | vix_above_25 | 99.9% | 0.00% | 2.01% | +0.020 | -0.032 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | as measured | big_share_above_10pct | 94.0% | 0.00% | 2.13% | +0.020 | -0.052 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | flipped | vix_above_25 | 99.9% | 0.09% | 0.96% | +0.020 | +0.076 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | flipped | big_share_above_10pct | 93.9% | 0.10% | 0.29% | +0.020 | +0.097 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | as measured | vix_above_25 | 18.7% | *2.30%* | 0.14% | +0.649 | +0.466 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.17% | 2.07% | +0.649 | +0.350 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | flipped | vix_above_25 | 18.8% | 0.03% | *39.54%* | -0.638 | -0.452 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | **0.42%** | *9.19%* | -0.638 | -0.330 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | as measured | vix_above_25 | 9.8% | *35.93%* | 0.00% | +0.649 | +0.493 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 0.00% | +0.649 | +0.356 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | flipped | vix_above_25 | 9.8% | 0.00% | *98.82%* | -0.638 | -0.481 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | *58.73%* | -0.638 | -0.324 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | as measured | vix_above_25 | 32.8% | 0.00% | **10.41%** | +0.305 | -0.008 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | as measured | big_share_above_10pct | 19.7% | 0.00% | **16.00%** | +0.305 | -0.186 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | flipped | vix_above_25 | 32.8% | **1.31%** | 0.46% | -0.289 | +0.031 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | flipped | big_share_above_10pct | 19.7% | **2.10%** | 0.01% | -0.289 | +0.216 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | as measured | vix_above_25 | 22.7% | 0.00% | **5.14%** | +0.305 | +0.064 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | as measured | big_share_above_10pct | 9.9% | 0.00% | **11.38%** | +0.305 | -0.084 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | flipped | vix_above_25 | 22.3% | **0.91%** | 2.38% | -0.289 | -0.040 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | flipped | big_share_above_10pct | 9.8% | **2.05%** | 0.03% | -0.289 | +0.109 |
