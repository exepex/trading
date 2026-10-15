# Protocol v4: rule E+D critical values (`tools/v4_claim_thresholds.py`)

100,000 seeded series per null process; threshold = worst-case quantile at rate / 15; held-out size on fresh seeds against nominal + 2 Monte Carlo SE; fewer than 12 batches: no claim (threshold 0). Outcomes needed: normal approximation, planning only.

| question | L | n | look | nominal | threshold | held-out size | tolerance | within | outcomes r=3 / 5 |
|---|---|---|---|---|---|---|---|---|---|
| v1_rv_next_session | 5 | 10 | look 1 | 0.00133 | 0 | 0.00000 | 0.00156 | yes | no claim |
| v1_rv_next_session | 5 | 10 | look 2 | 0.00200 | 0 | 0.00000 | 0.00228 | yes | no claim |
| v1_rv_next_session | 5 | 125 | look 1 | 0.00133 | 7.95e-10 | 0.00114 | 0.00156 | yes | 426 / 1183 |
| v1_rv_next_session | 5 | 125 | look 2 | 0.00200 | 2.46e-09 | 0.00169 | 0.00228 | yes | 404 / 1120 |
| v1_rv_next_session | 5 | 250 | look 1 | 0.00133 | 9.05e-11 | 0.00104 | 0.00156 | yes | 469 / 1303 |
| v1_rv_next_session | 5 | 250 | look 2 | 0.00200 | 5.16e-10 | 0.00179 | 0.00228 | yes | 435 / 1207 |
| v2_rv_next_5_sessions | 10 | 20 | look 1 | 0.00133 | 0 | 0.00000 | 0.00156 | yes | no claim |
| v2_rv_next_5_sessions | 10 | 20 | look 2 | 0.00200 | 0 | 0.00000 | 0.00228 | yes | no claim |
| v2_rv_next_5_sessions | 10 | 125 | look 1 | 0.00133 | 3.58e-09 | 0.00098 | 0.00156 | yes | 396 / 1099 |
| v2_rv_next_5_sessions | 10 | 125 | look 2 | 0.00200 | 8.56e-09 | 0.00155 | 0.00228 | yes | 378 / 1050 |
| v2_rv_next_5_sessions | 10 | 250 | look 1 | 0.00133 | 1.73e-11 | 0.00134 | 0.00156 | yes | 502 / 1394 |
| v2_rv_next_5_sessions | 10 | 250 | look 2 | 0.00200 | 5.41e-11 | 0.00214 | 0.00228 | yes | 480 / 1332 |
| v6_abs_move_2pct_next_session | 5 | 10 | look 1 | 0.00133 | 0 | 0.00000 | 0.00156 | yes | no claim |
| v6_abs_move_2pct_next_session | 5 | 10 | look 2 | 0.00200 | 0 | 0.00000 | 0.00228 | yes | no claim |
| v6_abs_move_2pct_next_session | 5 | 125 | look 1 | 0.00133 | 0.000146 | 0.00145 | 0.00156 | yes | 180 / 499 |
| v6_abs_move_2pct_next_session | 5 | 125 | look 2 | 0.00200 | 0.000281 | 0.00217 | 0.00228 | yes | 166 / 461 |
| v6_abs_move_2pct_next_session | 5 | 250 | look 1 | 0.00133 | 4.23e-05 | 0.00098 | 0.00156 | yes | 205 / 570 |
| v6_abs_move_2pct_next_session | 5 | 250 | look 2 | 0.00200 | 6.3e-05 | 0.00163 | 0.00228 | yes | 197 / 547 |
| v6_abs_move_2pct_within_5_sessions | 10 | 20 | look 1 | 0.00133 | 0 | 0.00000 | 0.00156 | yes | no claim |
| v6_abs_move_2pct_within_5_sessions | 10 | 20 | look 2 | 0.00200 | 0 | 0.00000 | 0.00228 | yes | no claim |
| v6_abs_move_2pct_within_5_sessions | 10 | 125 | look 1 | 0.00133 | 0.00058 | 0.00105 | 0.00156 | yes | 151 / 419 |
| v6_abs_move_2pct_within_5_sessions | 10 | 125 | look 2 | 0.00200 | 0.000906 | 0.00161 | 0.00228 | yes | 142 / 393 |
| v6_abs_move_2pct_within_5_sessions | 10 | 250 | look 1 | 0.00133 | 0.000484 | 0.00123 | 0.00156 | yes | 155 / 429 |
| v6_abs_move_2pct_within_5_sessions | 10 | 250 | look 2 | 0.00200 | 0.00083 | 0.00194 | 0.00228 | yes | 144 / 398 |
| v7_vix_higher_in_5_sessions | 10 | 20 | look 1 | 0.00133 | 0 | 0.00000 | 0.00156 | yes | no claim |
| v7_vix_higher_in_5_sessions | 10 | 20 | look 2 | 0.00200 | 0 | 0.00000 | 0.00228 | yes | no claim |
| v7_vix_higher_in_5_sessions | 10 | 125 | look 1 | 0.00133 | 0.00058 | 0.00105 | 0.00156 | yes | 151 / 419 |
| v7_vix_higher_in_5_sessions | 10 | 125 | look 2 | 0.00200 | 0.000906 | 0.00161 | 0.00228 | yes | 142 / 393 |
| v7_vix_higher_in_5_sessions | 10 | 250 | look 1 | 0.00133 | 0.000484 | 0.00123 | 0.00156 | yes | 155 / 429 |
| v7_vix_higher_in_5_sessions | 10 | 250 | look 2 | 0.00200 | 0.00083 | 0.00194 | 0.00228 | yes | 144 / 398 |
