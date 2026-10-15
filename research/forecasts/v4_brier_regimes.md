# Protocol v4: Brier rules across regimes, 2019-26 and calm stretches (`tools/v4_brier_regimes.py`)

100,000 held-out series per null; worst claim size at Holm's first step (look 1 nominal 0.133%, look 2 0.200%) and worst false-futility rate (target 2.5%) over the full-period and calm-stretch nulls in both orientations; gate m = the minimum 2% days in the scored window. Exposed data. Held-out seeds measure Monte Carlo error only, on the same days.

| question | n | gate m | claim L1 | claim L2 | false futility | judgeable full, calm 125, 250 | within |
|---|---|---|---|---|---|---|---|
| v6_abs_move_2pct_next_session | 125 | 0 | 1.690% | 1.860% | 2.68% | 100%, 100%, 100% | no |
| v6_abs_move_2pct_next_session | 125 | 5 | 0.093% | 0.158% | 2.50% | 53%, 0%, 0% | yes |
| v6_abs_move_2pct_next_session | 125 | 10 | 0.087% | 0.140% | 2.43% | 18%, 0%, 0% | yes |
| v6_abs_move_2pct_next_session | 125 | 15 | 0.151% | 0.221% | 2.43% | 8%, 0%, 0% | yes |
| v6_abs_move_2pct_next_session | 125 | 20 | 0.151% | 0.221% | 2.42% | 3%, 0%, 0% | yes |
| v6_abs_move_2pct_next_session | 250 | 0 | 0.146% | 0.230% | 2.34% | 100%, 100%, 100% | no |
| v6_abs_move_2pct_next_session | 250 | 5 | 0.115% | 0.157% | 2.42% | 90%, 0%, 0% | yes |
| v6_abs_move_2pct_next_session | 250 | 10 | 0.128% | 0.184% | 2.60% | 58%, 0%, 0% | yes |
| v6_abs_move_2pct_next_session | 250 | 15 | 0.109% | 0.179% | 2.36% | 30%, 0%, 0% | yes |
| v6_abs_move_2pct_next_session | 250 | 20 | 0.126% | 0.182% | 2.44% | 16%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 125 | 0 | 61.686% | 67.728% | 92.67% | 100%, 100%, 100% | no |
| v6_abs_move_2pct_within_5_sessions | 125 | 5 | 0.143% | 0.198% | 2.35% | 53%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 125 | 10 | 0.151% | 0.210% | 2.50% | 19%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 125 | 15 | 0.151% | 0.210% | 2.51% | 8%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 125 | 20 | 0.151% | 0.210% | 2.46% | 3%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 250 | 0 | 98.506% | 99.027% | 99.90% | 100%, 100%, 100% | no |
| v6_abs_move_2pct_within_5_sessions | 250 | 5 | 0.117% | 0.193% | 2.38% | 90%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 250 | 10 | 0.124% | 0.170% | 2.44% | 58%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 250 | 15 | 0.127% | 0.184% | 2.43% | 31%, 0%, 0% | yes |
| v6_abs_move_2pct_within_5_sessions | 250 | 20 | 0.127% | 0.184% | 2.47% | 16%, 0%, 0% | yes |
