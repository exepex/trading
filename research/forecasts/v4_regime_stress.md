# Protocol v4: every member's rules inside one regime (`tools/v4_regime_stress.py`)

100,000 series per cell; operative thresholds unchanged; revision 8: **every member** is judged only with 5 or more
2% days in the scored window. Claims: look 1, null centred over 2019-26 (nominal 0.133%; a claim also needs the point
estimate at the minimum effect). Futility: null shifted to a full-period true improvement of exactly the minimum effect
(target 2.5%). "all" = rate among every series (unjudged = no verdict); "judged" = rate among judged series. **local**
= the stretch's true relative improvement; **set** = the judged series' own pooled true improvement (what "beat the
baseline over the scored window" means for them). Each rate is marked against its own truth: a "no" is false only
where truth >= the minimum effect, a claim only where truth <= 0. **Bold**: false and above nominal + 2 Monte Carlo SE
of its count; *italic*: above it but that set's truth. Exposed data.

| question | stretch | n | orientation | judged | claim all | claim judged | futility all | futility judged | local claim / futility null | set claim / futility null |
|---|---|---|---|---|---|---|---|---|---|---|
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | as measured | 53% | 0.01% | 0.02% | 0.00% | 0.00% | +0.000 / +0.030 | -0.013 / +0.013 |
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | flipped | 53% | 0.00% | 0.00% | 0.56% | 1.06% | -0.000 / +0.030 | +0.013 / +0.043 |
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | as measured | 90% | 0.04% | 0.04% | 0.00% | 0.00% | +0.000 / +0.030 | -0.001 / +0.028 |
| v1_rv_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | flipped | 90% | 0.00% | 0.00% | 1.88% | 2.09% | -0.000 / +0.030 | +0.001 / +0.031 |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | 100% | 0.00% | 0.00% | 0.00% | 0.00% | +0.208 / +0.235 | +0.208 / +0.234 |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 100% | 0.00% | 0.00% | 0.01% | 0.01% | -0.208 / -0.182 | -0.208 / -0.182 |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | 100% | 0.00% | 0.00% | 0.00% | 0.00% | +0.208 / +0.235 | +0.208 / +0.235 |
| v1_rv_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 100% | 0.00% | 0.00% | 0.46% | 0.46% | -0.208 / -0.182 | -0.209 / -0.182 |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.175 / -0.143 | none / none |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.175 / +0.208 | none / none |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.175 / -0.143 | none / none |
| v1_rv_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.175 / +0.208 | none / none |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | 99% | 0.00% | 0.00% | 0.00% | 0.00% | +0.127 / +0.155 | +0.127 / +0.155 |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | 98% | 0.00% | 0.00% | 0.04% | 0.04% | -0.127 / -0.099 | -0.127 / -0.100 |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | 100% | 0.00% | 0.00% | 0.00% | 0.00% | +0.127 / +0.155 | +0.127 / +0.154 |
| v1_rv_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | 100% | 0.00% | 0.00% | 0.21% | 0.21% | -0.127 / -0.099 | -0.126 / -0.099 |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.170 / +0.207 | none / none |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.170 / -0.134 | none / none |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.170 / +0.207 | none / none |
| v1_rv_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.170 / -0.134 | none / none |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | as measured | 53% | 0.00% | 0.01% | 0.00% | 0.00% | +0.000 / +0.030 | -0.010 / +0.011 |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | flipped | 53% | 0.00% | 0.00% | 0.29% | 0.54% | -0.000 / +0.030 | +0.013 / +0.035 |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | as measured | 90% | 0.01% | 0.01% | 0.00% | 0.00% | +0.000 / +0.030 | -0.005 / +0.024 |
| v2_rv_next_5_sessions | full (2019-01-15 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | flipped | 90% | 0.00% | 0.00% | 0.35% | 0.39% | -0.000 / +0.030 | +0.008 / +0.034 |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | 100% | 0.00% | 0.00% | 0.00% | 0.00% | +0.514 / +0.528 | +0.515 / +0.529 |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 100% | 0.00% | 0.00% | 0.07% | 0.07% | -0.514 / -0.500 | -0.515 / -0.500 |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | 100% | 0.00% | 0.00% | 0.00% | 0.00% | +0.514 / +0.528 | +0.515 / +0.529 |
| v2_rv_next_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 100% | 0.00% | 0.00% | 0.01% | 0.01% | -0.514 / -0.500 | -0.515 / -0.500 |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -1.214 / -1.167 | none / none |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +1.214 / +1.261 | none / none |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -1.214 / -1.167 | none / none |
| v2_rv_next_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +1.214 / +1.261 | none / none |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | 99% | 0.01% | 0.01% | 0.00% | 0.00% | +0.434 / +0.453 | +0.433 / +0.454 |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | 99% | 0.00% | 0.00% | 0.08% | 0.08% | -0.434 / -0.414 | -0.435 / -0.416 |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | 100% | 0.00% | 0.00% | 0.00% | 0.00% | +0.434 / +0.453 | +0.434 / +0.453 |
| v2_rv_next_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | 100% | 0.00% | 0.00% | 0.00% | 0.00% | -0.434 / -0.414 | -0.433 / -0.414 |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +1.332 / +1.393 | none / none |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -1.332 / -1.272 | none / none |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +1.332 / +1.393 | none / none |
| v2_rv_next_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -1.332 / -1.272 | none / none |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | as measured | 53% | 0.00% | 0.00% | 1.12% | 2.11% | -0.000 / +0.020 | +0.081 / +0.095 |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 125 | flipped | 53% | 0.05% | 0.09% | 0.23% | 0.43% | -0.000 / +0.020 | -0.082 / -0.068 |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | as measured | 90% | 0.00% | 0.00% | 2.16% | 2.39% | -0.000 / +0.020 | +0.015 / +0.032 |
| v6_abs_move_2pct_next_session | full (2019-01-15 to 2026-10-14; 94 2% days, VIX 17.1) | 250 | flipped | 90% | 0.08% | 0.09% | 0.00% | 0.00% | -0.000 / +0.020 | -0.014 / +0.006 |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | 100% | *0.21%* | *0.21%* | 0.21% | 0.21% | +0.337 / +0.340 | +0.336 / +0.340 |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 100% | 0.07% | 0.07% | *35.97%* | *35.97%* | -0.337 / -0.333 | -0.336 / -0.333 |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | 100% | 0.00% | 0.00% | 0.00% | 0.00% | +0.337 / +0.340 | +0.337 / +0.341 |
| v6_abs_move_2pct_next_session | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 100% | 0.00% | 0.00% | 0.17% | 0.17% | -0.337 / -0.333 | -0.337 / -0.333 |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.555 / -0.407 | none / none |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.555 / +0.704 | none / none |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.555 / -0.407 | none / none |
| v6_abs_move_2pct_next_session | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.555 / +0.704 | none / none |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | 99% | 0.01% | 0.01% | **2.69%** | **2.73%** | +0.231 / +0.236 | +0.232 / +0.238 |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | 98% | 0.10% | 0.10% | *10.27%* | *10.43%* | -0.231 / -0.225 | -0.232 / -0.226 |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | 100% | 0.00% | 0.00% | 0.46% | 0.46% | +0.231 / +0.236 | +0.231 / +0.236 |
| v6_abs_move_2pct_next_session | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | 100% | 0.01% | 0.01% | 0.00% | 0.00% | -0.231 / -0.225 | -0.230 / -0.224 |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.399 / -0.211 | none / none |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.399 / +0.586 | none / none |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.399 / -0.211 | none / none |
| v6_abs_move_2pct_next_session | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.399 / +0.586 | none / none |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | as measured | 53% | 0.01% | 0.01% | 1.01% | 1.90% | -0.000 / +0.020 | +0.113 / +0.127 |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 125 | flipped | 53% | 0.05% | 0.10% | 0.33% | 0.62% | -0.000 / +0.020 | -0.110 / -0.095 |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | as measured | 90% | 0.00% | 0.00% | 2.00% | 2.22% | -0.000 / +0.020 | +0.016 / +0.036 |
| v6_abs_move_2pct_within_5_sessions | full (2019-01-21 to 2026-10-08; 94 2% days, VIX 17.1) | 250 | flipped | 90% | 0.09% | 0.10% | 1.02% | 1.13% | -0.000 / +0.020 | -0.015 / +0.001 |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | as measured | 100% | *43.21%* | *43.22%* | 0.03% | 0.03% | +0.643 / +0.649 | +0.644 / +0.649 |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 125 | flipped | 100% | 0.01% | 0.01% | *84.86%* | *84.87%* | -0.643 / -0.638 | -0.644 / -0.639 |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | as measured | 100% | *90.81%* | *90.81%* | 0.00% | 0.00% | +0.643 / +0.649 | +0.644 / +0.649 |
| v6_abs_move_2pct_within_5_sessions | busy 125 (2019-12-16 to 2020-06-18; 36 2% days, VIX 30.6) | 250 | flipped | 100% | 0.00% | 0.00% | *99.88%* | *99.88%* | -0.643 / -0.638 | -0.643 / -0.638 |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.209 / -0.157 | none / none |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.209 / +0.261 | none / none |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.209 / -0.157 | none / none |
| v6_abs_move_2pct_within_5_sessions | calm 125 (2021-04-13 to 2021-10-12; 0 2% days, VIX 16.0) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.209 / +0.261 | none / none |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | as measured | 99% | *1.82%* | *1.85%* | **3.43%** | **3.48%** | +0.297 / +0.305 | +0.302 / +0.310 |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 125 | flipped | 99% | **0.43%** | **0.44%** | *12.65%* | *12.84%* | -0.297 / -0.289 | -0.303 / -0.294 |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | as measured | 100% | *3.14%* | *3.14%* | 1.17% | 1.17% | +0.297 / +0.305 | +0.296 / +0.305 |
| v6_abs_move_2pct_within_5_sessions | busy 250 (2020-01-31 to 2021-02-02; 44 2% days, VIX 27.5) | 250 | flipped | 100% | **0.20%** | **0.20%** | *31.63%* | *31.64%* | -0.297 / -0.289 | -0.298 / -0.289 |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.575 / +0.628 | none / none |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 125 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.575 / -0.522 | none / none |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | as measured | 0% | 0.00% | 0.00% | 0.00% | 0.00% | +0.575 / +0.628 | none / none |
| v6_abs_move_2pct_within_5_sessions | calm 250 (2022-10-06 to 2023-10-10; 0 2% days, VIX 13.2) | 250 | flipped | 0% | 0.00% | 0.00% | 0.00% | 0.00% | -0.575 / -0.522 | none / none |

## Full period by 2%-day band (the banding test)

Rates among the band's series, thresholds as above; **bold** above nominal + 2 Monte Carlo SE of the band's count (revision 5's test, against the full-period null); truth = the band's pooled true improvement.

| question | n | orientation | band | series | claim | futility | truth claim / futility null |
|---|---|---|---|---|---|---|---|
| v1_rv_next_session | 125 | as measured | 5-7 | 24,815 | 0.03% | 0.00% | -0.016 / +0.013 |
| v1_rv_next_session | 125 | as measured | 8-12 | 17,475 | 0.01% | 0.00% | -0.053 / -0.025 |
| v1_rv_next_session | 125 | as measured | 13+ | 10,786 | 0.00% | 0.00% | +0.053 / +0.072 |
| v1_rv_next_session | 125 | flipped | 5-7 | 24,738 | 0.00% | 1.32% | +0.017 / +0.050 |
| v1_rv_next_session | 125 | flipped | 8-12 | 17,544 | 0.00% | 0.86% | +0.050 / +0.080 |
| v1_rv_next_session | 125 | flipped | 13+ | 10,840 | 0.00% | 0.78% | -0.053 / -0.025 |
| v1_rv_next_session | 250 | as measured | 5-7 | 18,362 | 0.06% | 0.00% | +0.012 / +0.042 |
| v1_rv_next_session | 250 | as measured | 8-12 | 31,838 | 0.06% | 0.00% | -0.008 / +0.022 |
| v1_rv_next_session | 250 | as measured | 13+ | 40,042 | 0.01% | 0.00% | -0.001 / +0.026 |
| v1_rv_next_session | 250 | flipped | 5-7 | 18,431 | 0.00% | **2.75%** | -0.012 / +0.017 |
| v1_rv_next_session | 250 | flipped | 8-12 | 31,836 | 0.00% | 2.15% | +0.009 / +0.038 |
| v1_rv_next_session | 250 | flipped | 13+ | 39,902 | 0.00% | 1.73% | +0.002 / +0.032 |
| v2_rv_next_5_sessions | 125 | as measured | 5-7 | 24,858 | 0.01% | 0.00% | -0.087 / -0.056 |
| v2_rv_next_5_sessions | 125 | as measured | 8-12 | 17,566 | 0.01% | 0.00% | -0.106 / -0.084 |
| v2_rv_next_5_sessions | 125 | as measured | 13+ | 10,793 | 0.00% | 0.00% | +0.226 / +0.228 |
| v2_rv_next_5_sessions | 125 | flipped | 5-7 | 24,860 | 0.00% | 0.75% | +0.087 / +0.121 |
| v2_rv_next_5_sessions | 125 | flipped | 8-12 | 17,485 | 0.00% | 0.40% | +0.106 / +0.124 |
| v2_rv_next_5_sessions | 125 | flipped | 13+ | 10,768 | 0.00% | 0.29% | -0.217 / -0.205 |
| v2_rv_next_5_sessions | 250 | as measured | 5-7 | 18,525 | 0.04% | 0.00% | -0.009 / +0.021 |
| v2_rv_next_5_sessions | 250 | as measured | 8-12 | 31,805 | 0.01% | 0.00% | -0.055 / -0.026 |
| v2_rv_next_5_sessions | 250 | as measured | 13+ | 39,941 | 0.00% | 0.00% | +0.028 / +0.057 |
| v2_rv_next_5_sessions | 250 | flipped | 5-7 | 18,163 | 0.00% | 0.62% | +0.003 / +0.052 |
| v2_rv_next_5_sessions | 250 | flipped | 8-12 | 32,213 | 0.00% | 0.46% | +0.064 / +0.090 |
| v2_rv_next_5_sessions | 250 | flipped | 13+ | 39,721 | 0.00% | 0.22% | -0.027 / -0.008 |
| v6_abs_move_2pct_next_session | 125 | as measured | 5-7 | 24,759 | 0.00% | 2.45% | -0.131 / -0.111 |
| v6_abs_move_2pct_next_session | 125 | as measured | 8-12 | 17,479 | 0.00% | 2.25% | -0.021 / -0.014 |
| v6_abs_move_2pct_next_session | 125 | as measured | 13+ | 10,765 | 0.00% | 1.13% | +0.336 / +0.346 |
| v6_abs_move_2pct_next_session | 125 | flipped | 5-7 | 24,813 | 0.11% | 0.00% | +0.132 / +0.152 |
| v6_abs_move_2pct_next_session | 125 | flipped | 8-12 | 17,508 | 0.06% | 0.00% | +0.024 / +0.039 |
| v6_abs_move_2pct_next_session | 125 | flipped | 13+ | 10,842 | 0.08% | 2.11% | -0.340 / -0.330 |
| v6_abs_move_2pct_next_session | 250 | as measured | 5-7 | 18,340 | 0.00% | 2.34% | -0.270 / -0.231 |
| v6_abs_move_2pct_next_session | 250 | as measured | 8-12 | 31,829 | 0.00% | 2.34% | -0.155 / -0.130 |
| v6_abs_move_2pct_next_session | 250 | as measured | 13+ | 40,017 | 0.00% | 2.45% | +0.129 / +0.141 |
| v6_abs_move_2pct_next_session | 250 | flipped | 5-7 | 18,334 | 0.08% | 0.00% | +0.271 / +0.309 |
| v6_abs_move_2pct_next_session | 250 | flipped | 8-12 | 32,005 | 0.11% | 0.00% | +0.155 / +0.179 |
| v6_abs_move_2pct_next_session | 250 | flipped | 13+ | 39,761 | 0.08% | 0.00% | -0.130 / -0.114 |
| v6_abs_move_2pct_within_5_sessions | 125 | as measured | 5-7 | 24,908 | 0.00% | 2.36% | -0.089 / -0.068 |
| v6_abs_move_2pct_within_5_sessions | 125 | as measured | 8-12 | 17,610 | 0.00% | 2.41% | +0.110 / +0.118 |
| v6_abs_move_2pct_within_5_sessions | 125 | as measured | 13+ | 10,892 | 0.06% | 0.02% | +0.381 / +0.393 |
| v6_abs_move_2pct_within_5_sessions | 125 | flipped | 5-7 | 24,541 | 0.13% | 0.01% | +0.091 / +0.108 |
| v6_abs_move_2pct_within_5_sessions | 125 | flipped | 8-12 | 17,624 | 0.13% | 0.48% | -0.105 / -0.091 |
| v6_abs_move_2pct_within_5_sessions | 125 | flipped | 13+ | 10,859 | 0.00% | 2.27% | -0.380 / -0.369 |
| v6_abs_move_2pct_within_5_sessions | 250 | as measured | 5-7 | 18,307 | 0.00% | 2.13% | -0.231 / -0.205 |
| v6_abs_move_2pct_within_5_sessions | 250 | as measured | 8-12 | 32,089 | 0.00% | 2.51% | -0.103 / -0.082 |
| v6_abs_move_2pct_within_5_sessions | 250 | as measured | 13+ | 39,928 | 0.00% | 2.03% | +0.144 / +0.161 |
| v6_abs_move_2pct_within_5_sessions | 250 | flipped | 5-7 | 18,167 | 0.06% | 0.00% | +0.233 / +0.259 |
| v6_abs_move_2pct_within_5_sessions | 250 | flipped | 8-12 | 32,313 | 0.12% | 0.00% | +0.104 / +0.123 |
| v6_abs_move_2pct_within_5_sessions | 250 | flipped | 13+ | 39,794 | 0.10% | 2.55% | -0.144 / -0.131 |
