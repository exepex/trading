# Protocol v4: every member's rules inside one regime (`tools/v4_regime_stress.py`)

100,000 series per cell; operative thresholds unchanged. Claims: look 1, null centred over 2019-26 (nominal 0.133%; a claim also needs the point estimate at the minimum effect). Futility: null shifted to a full-period true improvement of exactly the minimum effect (target 2.5%). **local** = the true relative improvement inside the stretch: a futility "no" is false only where local >= the minimum effect, a claim only where local <= 0. **Bold**: a false verdict above nominal + 2 Monte Carlo SE; *italic*: above it, but the regime's truth. Exposed data; Brier members judged only with 5+ 2% days.

| question | stretch | n | orientation | claim | local (claim null) | futility | local (futility null) | judged |
|---|---|---|---|---|---|---|---|---|
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | as measured | 0.04% | +0.000 | 0.00% | +0.030 | 100% |
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | flipped | 0.00% | -0.000 | 1.49% | +0.030 | 100% |
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | as measured | 0.05% | +0.000 | 0.00% | +0.030 | 100% |
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | flipped | 0.00% | -0.000 | 2.25% | +0.030 | 100% |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | 0.00% | +0.208 | 0.00% | +0.235 | 100% |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 0.00% | -0.208 | 0.01% | -0.182 | 100% |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | 0.00% | +0.208 | 0.00% | +0.235 | 100% |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 0.00% | -0.208 | 0.46% | -0.182 | 100% |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | **0.85%** | -0.175 | 0.00% | -0.143 | 100% |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0.00% | +0.175 | **6.81%** | +0.208 | 100% |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | **0.66%** | -0.175 | 0.00% | -0.143 | 100% |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0.00% | +0.175 | **2.93%** | +0.208 | 100% |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | 0.00% | +0.127 | 0.00% | +0.155 | 100% |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | 0.00% | -0.127 | 0.05% | -0.099 | 100% |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | 0.00% | +0.127 | 0.00% | +0.155 | 100% |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | 0.00% | -0.127 | 0.21% | -0.099 | 100% |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | *0.19%* | +0.170 | 0.00% | +0.207 | 100% |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0.00% | -0.170 | *4.51%* | -0.134 | 100% |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | *0.47%* | +0.170 | 0.00% | +0.207 | 100% |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0.00% | -0.170 | *11.44%* | -0.134 | 100% |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | as measured | 0.01% | +0.000 | 0.00% | +0.030 | 100% |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | flipped | 0.00% | -0.000 | 0.78% | +0.030 | 100% |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | as measured | 0.02% | +0.000 | 0.00% | +0.030 | 100% |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | flipped | 0.00% | -0.000 | 0.49% | +0.030 | 100% |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | 0.00% | +0.514 | 0.00% | +0.528 | 100% |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 0.00% | -0.514 | 0.07% | -0.500 | 100% |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | 0.00% | +0.514 | 0.00% | +0.528 | 100% |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 0.00% | -0.514 | 0.01% | -0.500 | 100% |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | 0.02% | -1.214 | 0.00% | -1.167 | 100% |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0.00% | +1.214 | 1.96% | +1.261 | 100% |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | 0.05% | -1.214 | 0.00% | -1.167 | 100% |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0.00% | +1.214 | 0.65% | +1.261 | 100% |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | 0.01% | +0.434 | 0.00% | +0.453 | 100% |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | 0.00% | -0.434 | 0.10% | -0.414 | 100% |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | 0.00% | +0.434 | 0.00% | +0.453 | 100% |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | 0.00% | -0.434 | 0.00% | -0.414 | 100% |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | *0.70%* | +1.332 | 0.00% | +1.393 | 100% |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0.00% | -1.332 | *13.71%* | -1.272 | 100% |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | *6.61%* | +1.332 | 0.00% | +1.393 | 100% |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0.00% | -1.332 | *41.42%* | -1.272 | 100% |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | as measured | 0.00% | -0.000 | 1.12% | +0.020 | 53% |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | flipped | 0.05% | -0.000 | 0.23% | +0.020 | 53% |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | as measured | 0.00% | -0.000 | 2.16% | +0.020 | 90% |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | flipped | 0.08% | -0.000 | 0.00% | +0.020 | 90% |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | *0.21%* | +0.337 | 0.21% | +0.340 | 100% |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 0.07% | -0.337 | *35.97%* | -0.333 | 100% |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | 0.00% | +0.337 | 0.00% | +0.340 | 100% |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 0.00% | -0.337 | 0.17% | -0.333 | 100% |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | 0.00% | -0.555 | 0.00% | -0.407 | 0% |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0.00% | +0.555 | 0.00% | +0.704 | 0% |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | 0.00% | -0.555 | 0.00% | -0.407 | 0% |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0.00% | +0.555 | 0.00% | +0.704 | 0% |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | 0.01% | +0.231 | **2.69%** | +0.236 | 99% |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | 0.10% | -0.231 | *10.27%* | -0.225 | 98% |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | 0.00% | +0.231 | 0.46% | +0.236 | 100% |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | 0.01% | -0.231 | 0.00% | -0.225 | 100% |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | 0.00% | -0.399 | 0.00% | -0.211 | 0% |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0.00% | +0.399 | 0.00% | +0.586 | 0% |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | 0.00% | -0.399 | 0.00% | -0.211 | 0% |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0.00% | +0.399 | 0.00% | +0.586 | 0% |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | as measured | 0.01% | -0.000 | 1.01% | +0.020 | 53% |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | flipped | 0.05% | -0.000 | 0.33% | +0.020 | 53% |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | as measured | 0.00% | -0.000 | 2.00% | +0.020 | 90% |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | flipped | 0.09% | -0.000 | 1.02% | +0.020 | 90% |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | *43.21%* | +0.643 | 0.03% | +0.649 | 100% |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 0.01% | -0.643 | *84.86%* | -0.638 | 100% |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | *90.81%* | +0.643 | 0.00% | +0.649 | 100% |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 0.00% | -0.643 | *99.88%* | -0.638 | 100% |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | 0.00% | -0.209 | 0.00% | -0.157 | 0% |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0.00% | +0.209 | 0.00% | +0.261 | 0% |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | 0.00% | -0.209 | 0.00% | -0.157 | 0% |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0.00% | +0.209 | 0.00% | +0.261 | 0% |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | *1.82%* | +0.297 | **3.43%** | +0.305 | 99% |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | **0.43%** | -0.297 | *12.65%* | -0.289 | 99% |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | *3.14%* | +0.297 | 1.17% | +0.305 | 100% |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | **0.20%** | -0.297 | *31.63%* | -0.289 | 100% |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | 0.00% | +0.575 | 0.00% | +0.628 | 0% |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0.00% | -0.575 | 0.00% | -0.522 | 0% |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | 0.00% | +0.575 | 0.00% | +0.628 | 0% |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0.00% | -0.575 | 0.00% | -0.522 | 0% |
