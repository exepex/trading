# Protocol v4: item E option 2, crash cuts measured (`tools/v4_crash_cut.py`)

## Cost: real rolling 2019-26 windows removed

Judgeable = at least 5 2% days (revision 8: every member).

| question | n | cut | removed | judgeable before | judgeable after | removed windows start |
|---|---|---|---|---|---|---|
| v1_rv_next_session | 125 | vix_above_25 | 7.6% | 50% | 42% | 2019-10-23 to 2020-05-12 |
| v1_rv_next_session | 125 | big_share_above_10pct | 12.6% | 50% | 37% | 2019-09-16 to 2022-02-15 |
| v1_rv_next_session | 250 | vix_above_25 | 8.9% | 79% | 70% | 2019-08-30 to 2020-04-08 |
| v1_rv_next_session | 250 | big_share_above_10pct | 15.6% | 79% | 63% | 2019-03-25 to 2020-04-17 |
| v2_rv_next_5_sessions | 125 | vix_above_25 | 7.6% | 50% | 42% | 2019-10-23 to 2020-05-12 |
| v2_rv_next_5_sessions | 125 | big_share_above_10pct | 12.6% | 50% | 37% | 2019-09-16 to 2022-02-15 |
| v2_rv_next_5_sessions | 250 | vix_above_25 | 8.9% | 78% | 70% | 2019-08-30 to 2020-04-08 |
| v2_rv_next_5_sessions | 250 | big_share_above_10pct | 15.6% | 78% | 63% | 2019-03-25 to 2020-04-17 |
| v6_abs_move_2pct_next_session | 125 | vix_above_25 | 7.6% | 50% | 42% | 2019-10-23 to 2020-05-12 |
| v6_abs_move_2pct_next_session | 125 | big_share_above_10pct | 12.6% | 50% | 37% | 2019-09-16 to 2022-02-15 |
| v6_abs_move_2pct_next_session | 250 | vix_above_25 | 8.9% | 78% | 70% | 2019-08-30 to 2020-04-08 |
| v6_abs_move_2pct_next_session | 250 | big_share_above_10pct | 15.6% | 78% | 63% | 2019-03-25 to 2020-04-17 |
| v6_abs_move_2pct_within_5_sessions | 125 | vix_above_25 | 7.6% | 50% | 43% | 2019-10-23 to 2020-05-12 |
| v6_abs_move_2pct_within_5_sessions | 125 | big_share_above_10pct | 12.7% | 50% | 37% | 2019-09-16 to 2022-02-15 |
| v6_abs_move_2pct_within_5_sessions | 250 | vix_above_25 | 8.9% | 78% | 69% | 2019-08-30 to 2020-04-08 |
| v6_abs_move_2pct_within_5_sessions | 250 | big_share_above_10pct | 15.7% | 78% | 63% | 2019-03-25 to 2020-04-17 |

## Re-measured on each judged set's own truth (paired draws with `v4_regime_stress.md`)

Rates among the judged series that each cut keeps (5+ 2% days and not cut), next to the same draws with no cut. **set** = that judged set's own pooled true improvement: a "no" is false only where set >= the minimum effect, a claim only where set <= 0. **Bold**: false and above nominal + 2 Monte Carlo SE of the judged count; *italic*: above it but that set's truth. A set with almost nothing judged says little.

| question | stretch | n | orientation | cut | judged | claim | futility | set claim / futility null |
|---|---|---|---|---|---|---|---|---|
| v1_rv_next_session | full | 125 | as measured | no cut | 53.3% | 0.02% | 0.00% | -0.013 / +0.013 |
| v1_rv_next_session | full | 125 | as measured | vix_above_25 | 52.0% | 0.02% | 0.00% | -0.016 / +0.010 |
| v1_rv_next_session | full | 125 | as measured | big_share_above_10pct | 42.3% | 0.02% | 0.00% | -0.032 / -0.003 |
| v1_rv_next_session | full | 125 | flipped | no cut | 53.0% | 0.00% | 1.06% | +0.013 / +0.043 |
| v1_rv_next_session | full | 125 | flipped | vix_above_25 | 51.7% | 0.00% | 1.06% | +0.015 / +0.047 |
| v1_rv_next_session | full | 125 | flipped | big_share_above_10pct | 42.1% | 0.00% | 1.13% | +0.031 / +0.063 |
| v1_rv_next_session | full | 250 | as measured | no cut | 90.2% | 0.04% | 0.00% | -0.001 / +0.028 |
| v1_rv_next_session | full | 250 | as measured | vix_above_25 | 90.1% | 0.04% | 0.00% | -0.001 / +0.027 |
| v1_rv_next_session | full | 250 | as measured | big_share_above_10pct | 84.3% | 0.04% | 0.00% | -0.004 / +0.025 |
| v1_rv_next_session | full | 250 | flipped | no cut | 90.1% | 0.00% | 2.09% | +0.001 / +0.031 |
| v1_rv_next_session | full | 250 | flipped | vix_above_25 | 90.0% | 0.00% | 2.09% | +0.002 / +0.032 |
| v1_rv_next_session | full | 250 | flipped | big_share_above_10pct | 84.1% | 0.00% | 2.12% | +0.004 / +0.035 |
| v1_rv_next_session | busy 125 | 125 | as measured | no cut | 100.0% | 0.00% | 0.00% | +0.208 / +0.234 |
| v1_rv_next_session | busy 125 | 125 | as measured | vix_above_25 | 18.7% | 0.00% | 0.00% | +0.153 / +0.183 |
| v1_rv_next_session | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.00% | 0.00% | +0.100 / +0.139 |
| v1_rv_next_session | busy 125 | 125 | flipped | no cut | 100.0% | 0.00% | 0.01% | -0.208 / -0.182 |
| v1_rv_next_session | busy 125 | 125 | flipped | vix_above_25 | 18.7% | 0.00% | 0.01% | -0.154 / -0.124 |
| v1_rv_next_session | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | 0.00% | 0.00% | -0.107 / -0.070 |
| v1_rv_next_session | busy 125 | 250 | as measured | no cut | 100.0% | 0.00% | 0.00% | +0.208 / +0.235 |
| v1_rv_next_session | busy 125 | 250 | as measured | vix_above_25 | 9.8% | 0.00% | 0.00% | +0.161 / +0.190 |
| v1_rv_next_session | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 0.00% | +0.103 / +0.133 |
| v1_rv_next_session | busy 125 | 250 | flipped | no cut | 100.0% | 0.00% | 0.46% | -0.209 / -0.182 |
| v1_rv_next_session | busy 125 | 250 | flipped | vix_above_25 | 9.7% | 0.00% | 0.04% | -0.160 / -0.130 |
| v1_rv_next_session | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | 0.00% | -0.101 / -0.062 |
| v1_rv_next_session | busy 250 | 125 | as measured | no cut | 98.5% | 0.00% | 0.00% | +0.127 / +0.155 |
| v1_rv_next_session | busy 250 | 125 | as measured | vix_above_25 | 31.4% | 0.00% | 0.00% | +0.072 / +0.101 |
| v1_rv_next_session | busy 250 | 125 | as measured | big_share_above_10pct | 18.1% | 0.00% | 0.00% | +0.045 / +0.077 |
| v1_rv_next_session | busy 250 | 125 | flipped | no cut | 98.5% | 0.00% | 0.04% | -0.127 / -0.100 |
| v1_rv_next_session | busy 250 | 125 | flipped | vix_above_25 | 31.3% | 0.00% | 0.03% | -0.074 / -0.044 |
| v1_rv_next_session | busy 250 | 125 | flipped | big_share_above_10pct | 18.1% | 0.00% | 0.09% | -0.046 / -0.013 |
| v1_rv_next_session | busy 250 | 250 | as measured | no cut | 100.0% | 0.00% | 0.00% | +0.127 / +0.154 |
| v1_rv_next_session | busy 250 | 250 | as measured | vix_above_25 | 22.9% | 0.00% | 0.00% | +0.081 / +0.109 |
| v1_rv_next_session | busy 250 | 250 | as measured | big_share_above_10pct | 10.0% | 0.00% | 0.00% | +0.053 / +0.084 |
| v1_rv_next_session | busy 250 | 250 | flipped | no cut | 100.0% | 0.00% | 0.21% | -0.126 / -0.099 |
| v1_rv_next_session | busy 250 | 250 | flipped | vix_above_25 | 22.7% | 0.00% | 0.07% | -0.080 / -0.051 |
| v1_rv_next_session | busy 250 | 250 | flipped | big_share_above_10pct | 9.9% | 0.00% | 0.19% | -0.055 / -0.022 |
| v2_rv_next_5_sessions | full | 125 | as measured | no cut | 53.3% | 0.01% | 0.00% | -0.010 / +0.011 |
| v2_rv_next_5_sessions | full | 125 | as measured | vix_above_25 | 52.0% | 0.01% | 0.00% | -0.022 / +0.001 |
| v2_rv_next_5_sessions | full | 125 | as measured | big_share_above_10pct | 42.4% | 0.01% | 0.00% | -0.096 / -0.068 |
| v2_rv_next_5_sessions | full | 125 | flipped | no cut | 53.4% | 0.00% | 0.54% | +0.013 / +0.035 |
| v2_rv_next_5_sessions | full | 125 | flipped | vix_above_25 | 52.1% | 0.00% | 0.55% | +0.024 / +0.047 |
| v2_rv_next_5_sessions | full | 125 | flipped | big_share_above_10pct | 42.5% | 0.00% | 0.61% | +0.096 / +0.122 |
| v2_rv_next_5_sessions | full | 250 | as measured | no cut | 90.1% | 0.01% | 0.00% | -0.005 / +0.024 |
| v2_rv_next_5_sessions | full | 250 | as measured | vix_above_25 | 90.0% | 0.01% | 0.00% | -0.006 / +0.023 |
| v2_rv_next_5_sessions | full | 250 | as measured | big_share_above_10pct | 84.1% | 0.01% | 0.00% | -0.023 / +0.006 |
| v2_rv_next_5_sessions | full | 250 | flipped | no cut | 90.1% | 0.00% | 0.39% | +0.008 / +0.034 |
| v2_rv_next_5_sessions | full | 250 | flipped | vix_above_25 | 90.0% | 0.00% | 0.39% | +0.008 / +0.035 |
| v2_rv_next_5_sessions | full | 250 | flipped | big_share_above_10pct | 83.9% | 0.00% | 0.41% | +0.025 / +0.054 |
| v2_rv_next_5_sessions | busy 125 | 125 | as measured | no cut | 100.0% | 0.00% | 0.00% | +0.515 / +0.529 |
| v2_rv_next_5_sessions | busy 125 | 125 | as measured | vix_above_25 | 18.5% | 0.01% | 0.00% | +0.429 / +0.444 |
| v2_rv_next_5_sessions | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.00% | 0.00% | +0.435 / +0.462 |
| v2_rv_next_5_sessions | busy 125 | 125 | flipped | no cut | 100.0% | 0.00% | 0.07% | -0.515 / -0.500 |
| v2_rv_next_5_sessions | busy 125 | 125 | flipped | vix_above_25 | 18.7% | 0.00% | 0.16% | -0.427 / -0.411 |
| v2_rv_next_5_sessions | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | 0.00% | 0.65% | -0.436 / -0.415 |
| v2_rv_next_5_sessions | busy 125 | 250 | as measured | no cut | 100.0% | 0.00% | 0.00% | +0.515 / +0.529 |
| v2_rv_next_5_sessions | busy 125 | 250 | as measured | vix_above_25 | 9.8% | 0.00% | 0.00% | +0.440 / +0.456 |
| v2_rv_next_5_sessions | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 0.00% | +0.427 / +0.449 |
| v2_rv_next_5_sessions | busy 125 | 250 | flipped | no cut | 100.0% | 0.00% | 0.01% | -0.515 / -0.500 |
| v2_rv_next_5_sessions | busy 125 | 250 | flipped | vix_above_25 | 9.8% | 0.00% | 0.07% | -0.439 / -0.423 |
| v2_rv_next_5_sessions | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | 1.59% | -0.424 / -0.410 |
| v2_rv_next_5_sessions | busy 250 | 125 | as measured | no cut | 98.5% | 0.01% | 0.00% | +0.433 / +0.454 |
| v2_rv_next_5_sessions | busy 250 | 125 | as measured | vix_above_25 | 31.3% | 0.00% | 0.00% | +0.302 / +0.327 |
| v2_rv_next_5_sessions | busy 250 | 125 | as measured | big_share_above_10pct | 18.2% | 0.02% | 0.00% | +0.295 / +0.331 |
| v2_rv_next_5_sessions | busy 250 | 125 | flipped | no cut | 98.5% | 0.00% | 0.08% | -0.435 / -0.416 |
| v2_rv_next_5_sessions | busy 250 | 125 | flipped | vix_above_25 | 31.3% | 0.00% | 0.04% | -0.304 / -0.283 |
| v2_rv_next_5_sessions | busy 250 | 125 | flipped | big_share_above_10pct | 18.3% | 0.00% | 0.22% | -0.301 / -0.271 |
| v2_rv_next_5_sessions | busy 250 | 250 | as measured | no cut | 100.0% | 0.00% | 0.00% | +0.434 / +0.453 |
| v2_rv_next_5_sessions | busy 250 | 250 | as measured | vix_above_25 | 22.6% | 0.00% | 0.00% | +0.326 / +0.349 |
| v2_rv_next_5_sessions | busy 250 | 250 | as measured | big_share_above_10pct | 9.9% | 0.00% | 0.00% | +0.307 / +0.340 |
| v2_rv_next_5_sessions | busy 250 | 250 | flipped | no cut | 100.0% | 0.00% | 0.00% | -0.433 / -0.414 |
| v2_rv_next_5_sessions | busy 250 | 250 | flipped | vix_above_25 | 22.5% | 0.00% | 0.00% | -0.326 / -0.302 |
| v2_rv_next_5_sessions | busy 250 | 250 | flipped | big_share_above_10pct | 9.9% | 0.00% | 0.03% | -0.312 / -0.281 |
| v6_abs_move_2pct_next_session | full | 125 | as measured | no cut | 53.2% | 0.00% | 2.11% | +0.081 / +0.095 |
| v6_abs_move_2pct_next_session | full | 125 | as measured | vix_above_25 | 51.9% | 0.00% | 2.16% | +0.059 / +0.073 |
| v6_abs_move_2pct_next_session | full | 125 | as measured | big_share_above_10pct | 42.2% | 0.00% | 2.37% | -0.073 / -0.060 |
| v6_abs_move_2pct_next_session | full | 125 | flipped | no cut | 53.0% | 0.09% | 0.43% | -0.082 / -0.068 |
| v6_abs_move_2pct_next_session | full | 125 | flipped | vix_above_25 | 51.7% | 0.09% | 0.04% | -0.059 / -0.045 |
| v6_abs_move_2pct_next_session | full | 125 | flipped | big_share_above_10pct | 42.1% | 0.09% | 0.00% | +0.075 / +0.093 |
| v6_abs_move_2pct_next_session | full | 250 | as measured | no cut | 90.2% | 0.00% | 2.39% | +0.015 / +0.032 |
| v6_abs_move_2pct_next_session | full | 250 | as measured | vix_above_25 | 90.1% | 0.00% | 2.40% | +0.013 / +0.030 |
| v6_abs_move_2pct_next_session | full | 250 | as measured | big_share_above_10pct | 84.3% | 0.00% | 2.56% | -0.038 / -0.018 |
| v6_abs_move_2pct_next_session | full | 250 | flipped | no cut | 90.1% | 0.09% | 0.00% | -0.014 / +0.006 |
| v6_abs_move_2pct_next_session | full | 250 | flipped | vix_above_25 | 90.0% | 0.09% | 0.00% | -0.013 / +0.008 |
| v6_abs_move_2pct_next_session | full | 250 | flipped | big_share_above_10pct | 84.1% | 0.10% | 0.00% | +0.038 / +0.061 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | as measured | no cut | 100.0% | *0.21%* | 0.21% | +0.336 / +0.340 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | as measured | vix_above_25 | 18.7% | 0.00% | 1.12% | +0.142 / +0.147 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.00% | *5.78%* | -0.067 / -0.051 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | flipped | no cut | 100.0% | 0.07% | *35.97%* | -0.336 / -0.333 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | flipped | vix_above_25 | 18.7% | **0.37%** | 0.60% | -0.141 / -0.135 |
| v6_abs_move_2pct_next_session | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | *3.45%* | 0.00% | +0.066 / +0.074 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | as measured | no cut | 100.0% | 0.00% | 0.00% | +0.337 / +0.341 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | as measured | vix_above_25 | 9.8% | 0.00% | 0.02% | +0.179 / +0.185 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 2.56% | -0.045 / -0.026 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | flipped | no cut | 100.0% | 0.00% | 0.17% | -0.337 / -0.333 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | flipped | vix_above_25 | 9.7% | 0.00% | 0.00% | -0.178 / -0.173 |
| v6_abs_move_2pct_next_session | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | 0.00% | +0.040 / +0.072 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | as measured | no cut | 98.5% | 0.01% | **2.73%** | +0.232 / +0.238 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | as measured | vix_above_25 | 31.4% | 0.00% | *7.93%* | -0.027 / -0.017 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | as measured | big_share_above_10pct | 18.1% | 0.00% | 1.77% | -0.138 / -0.123 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | flipped | no cut | 98.5% | 0.10% | *10.43%* | -0.232 / -0.226 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | flipped | vix_above_25 | 31.3% | *0.32%* | 0.00% | +0.026 / +0.037 |
| v6_abs_move_2pct_next_session | busy 250 | 125 | flipped | big_share_above_10pct | 18.1% | 0.02% | 0.00% | +0.137 / +0.152 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | as measured | no cut | 100.0% | 0.00% | 0.46% | +0.231 / +0.236 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | as measured | vix_above_25 | 22.9% | 0.00% | 2.02% | +0.024 / +0.033 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | as measured | big_share_above_10pct | 10.0% | 0.00% | *4.37%* | -0.087 / -0.073 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | flipped | no cut | 100.0% | 0.01% | 0.00% | -0.230 / -0.224 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | flipped | vix_above_25 | 22.7% | 0.02% | 0.00% | -0.023 / -0.015 |
| v6_abs_move_2pct_next_session | busy 250 | 250 | flipped | big_share_above_10pct | 9.9% | 0.05% | 0.00% | +0.089 / +0.099 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | as measured | no cut | 53.4% | 0.01% | 1.90% | +0.113 / +0.127 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | as measured | vix_above_25 | 52.1% | 0.00% | 1.94% | +0.096 / +0.110 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | as measured | big_share_above_10pct | 42.5% | 0.00% | 2.38% | +0.009 / +0.022 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | flipped | no cut | 53.4% | 0.10% | 0.62% | -0.110 / -0.095 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | flipped | vix_above_25 | 52.2% | 0.10% | 0.39% | -0.094 / -0.079 |
| v6_abs_move_2pct_within_5_sessions | full | 125 | flipped | big_share_above_10pct | 42.6% | 0.13% | 0.20% | -0.006 / +0.011 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | as measured | no cut | 90.3% | 0.00% | 2.22% | +0.016 / +0.036 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | as measured | vix_above_25 | 90.1% | 0.00% | 2.22% | +0.014 / +0.035 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | as measured | big_share_above_10pct | 84.1% | 0.00% | 2.38% | -0.020 / +0.001 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | flipped | no cut | 90.2% | 0.10% | 1.13% | -0.015 / +0.001 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | flipped | vix_above_25 | 90.1% | 0.10% | 1.06% | -0.014 / +0.003 |
| v6_abs_move_2pct_within_5_sessions | full | 250 | flipped | big_share_above_10pct | 84.0% | 0.11% | 0.32% | +0.021 / +0.038 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | as measured | no cut | 100.0% | *43.22%* | 0.03% | +0.644 / +0.649 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | as measured | vix_above_25 | 18.5% | *2.30%* | 0.14% | +0.454 / +0.460 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | as measured | big_share_above_10pct | 1.2% | 0.17% | 2.10% | +0.343 / +0.345 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | flipped | no cut | 100.0% | 0.01% | *84.87%* | -0.644 / -0.639 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | flipped | vix_above_25 | 18.7% | 0.03% | *39.57%* | -0.453 / -0.447 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 125 | flipped | big_share_above_10pct | 1.2% | **0.42%** | *9.27%* | -0.342 / -0.327 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | as measured | no cut | 100.0% | *90.81%* | 0.00% | +0.644 / +0.649 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | as measured | vix_above_25 | 9.8% | *35.93%* | 0.00% | +0.484 / +0.491 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | as measured | big_share_above_10pct | 0.1% | 0.00% | 0.00% | +0.359 / +0.355 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | flipped | no cut | 100.0% | 0.00% | *99.88%* | -0.643 / -0.638 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | flipped | vix_above_25 | 9.8% | 0.00% | *98.82%* | -0.484 / -0.477 |
| v6_abs_move_2pct_within_5_sessions | busy 125 | 250 | flipped | big_share_above_10pct | 0.1% | 0.00% | *58.73%* | -0.357 / -0.338 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | as measured | no cut | 98.5% | *1.85%* | **3.48%** | +0.302 / +0.310 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | as measured | vix_above_25 | 31.3% | 0.00% | *10.90%* | -0.003 / +0.008 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | as measured | big_share_above_10pct | 18.2% | 0.00% | *17.32%* | -0.176 / -0.158 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | flipped | no cut | 98.5% | **0.44%** | *12.84%* | -0.303 / -0.294 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | flipped | vix_above_25 | 31.3% | *1.37%* | 0.48% | +0.001 / +0.012 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 125 | flipped | big_share_above_10pct | 18.3% | *2.27%* | 0.01% | +0.174 / +0.187 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | as measured | no cut | 100.0% | *3.14%* | 1.17% | +0.296 / +0.305 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | as measured | vix_above_25 | 22.6% | 0.00% | **5.14%** | +0.047 / +0.058 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | as measured | big_share_above_10pct | 9.9% | 0.00% | *11.39%* | -0.105 / -0.091 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | flipped | no cut | 100.0% | **0.20%** | *31.64%* | -0.298 / -0.289 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | flipped | vix_above_25 | 22.5% | **0.91%** | 2.38% | -0.047 / -0.036 |
| v6_abs_move_2pct_within_5_sessions | busy 250 | 250 | flipped | big_share_above_10pct | 9.9% | *2.05%* | 0.03% | +0.106 / +0.116 |
