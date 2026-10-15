# Protocol v4: false-futility rate at the minimum effect (`tools/v4_futility_study.py`)

True improvement = the registered minimum effect; target at most 2.5% per look. F0: 10,000 series (tolerance 2.81%); F+D: 100,000 held-out series (tolerance 2.60%). **Bold** = above tolerance. Exposed 2024-26 data.

| question | n | orientation | F0 look 1 | F0 look 2 | F+D (both looks) | F+D threshold |
|---|---|---|---|---|---|---|
| v1_rv_next_session | 125 | as measured | 0.31% | 0.27% | 0.00% | 9.17e-06 |
| v1_rv_next_session | 125 | flipped | **27.06%** | **27.04%** | 2.45% | 9.17e-06 |
| v1_rv_next_session | 250 | as measured | 0.50% | 0.51% | 0.00% | 9.14e-06 |
| v1_rv_next_session | 250 | flipped | **23.36%** | **23.37%** | 2.38% | 9.14e-06 |
| v2_rv_next_5_sessions | 125 | as measured | 0.66% | 0.65% | 0.00% | 2.74e-06 |
| v2_rv_next_5_sessions | 125 | flipped | **32.25%** | **32.27%** | 2.58% | 2.74e-06 |
| v2_rv_next_5_sessions | 250 | as measured | 0.69% | 0.74% | 0.00% | 1.17e-07 |
| v2_rv_next_5_sessions | 250 | flipped | **22.60%** | **22.65%** | 2.40% | 1.17e-07 |
| v6_abs_move_2pct_next_session | 125 | as measured | **16.19%** | **16.26%** | 2.51% | 0.00945 |
| v6_abs_move_2pct_next_session | 125 | flipped | 1.38% | 1.37% | 0.02% | 0.00945 |
| v6_abs_move_2pct_next_session | 250 | as measured | **17.24%** | **17.20%** | 2.34% | 0.00363 |
| v6_abs_move_2pct_next_session | 250 | flipped | 1.50% | 1.44% | 0.01% | 0.00363 |
| v6_abs_move_2pct_within_5_sessions | 125 | as measured | **6.51%** | **6.50%** | 0.00% | 8.57e-05 |
| v6_abs_move_2pct_within_5_sessions | 125 | flipped | **11.59%** | **11.57%** | 2.36% | 8.57e-05 |
| v6_abs_move_2pct_within_5_sessions | 250 | as measured | **7.27%** | **7.30%** | 1.90% | 0.0201 |
| v6_abs_move_2pct_within_5_sessions | 250 | flipped | **6.70%** | **6.77%** | 2.37% | 0.0201 |
