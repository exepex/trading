# Protocol v4: Brier thresholds by event-count band (`tools/v4_brier_bands.py`)

200,000 series per null (calibration and held-out); rates are conditional on the band; worst held-out claim size at Holm's first step (L1 nominal 0.133%, L2 0.200%) and worst false futility (target 2.5%), against nominal + 2 Monte Carlo SE for the band's count. Exposed 2019-26 data; held-out seeds measure Monte Carlo error only.

| question | n | 2% days | share of windows | claim L1 | claim L2 | false futility | L1 threshold | outcomes r=3 / 5 | within |
|---|---|---|---|---|---|---|---|---|---|
| v6_abs_move_2pct_next_session | 125 | 5-7 | 25% | 0.117% | 0.151% | 2.45% | 2.57e-14 | 631 / 1752 | yes |
| v6_abs_move_2pct_next_session | 125 | 8-12 | 18% | 0.034% | 0.091% | 2.24% | 4.18e-11 | 485 / 1346 | yes |
| v6_abs_move_2pct_next_session | 125 | 13+ | 11% | 0.055% | 0.147% | 2.18% | 2.01e-05 | 221 / 613 | yes |
| v6_abs_move_2pct_next_session | 250 | 5-7 | 18% | 0.123% | 0.164% | 2.14% | 1.37e-23 | 1047 / 2907 | yes |
| v6_abs_move_2pct_next_session | 250 | 8-12 | 32% | 0.095% | 0.158% | 2.39% | 4.12e-19 | 847 / 2352 | yes |
| v6_abs_move_2pct_next_session | 250 | 13+ | 40% | 0.089% | 0.143% | 2.39% | 2.56e-13 | 586 / 1626 | yes |
| v6_abs_move_2pct_within_5_sessions | 125 | 5-7 | 25% | 0.113% | 0.185% | 2.52% | 0.000139 | 181 / 502 | yes |
| v6_abs_move_2pct_within_5_sessions | 125 | 8-12 | 18% | 0.130% | 0.189% | 2.35% | 0.000648 | 149 / 412 | yes |
| v6_abs_move_2pct_within_5_sessions | 125 | 13+ | 11% | 0.130% | 0.189% | 2.45% | 0.000648 | 149 / 412 | yes |
| v6_abs_move_2pct_within_5_sessions | 250 | 5-7 | 18% | 0.118% | 0.168% | 2.09% | 4.19e-05 | 206 / 570 | yes |
| v6_abs_move_2pct_within_5_sessions | 250 | 8-12 | 32% | 0.129% | 0.190% | 2.57% | 8.21e-05 | 192 / 532 | yes |
| v6_abs_move_2pct_within_5_sessions | 250 | 13+ | 40% | 0.130% | 0.192% | 2.50% | 0.000578 | 151 / 419 | yes |
