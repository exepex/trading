# 2026-10-12-experiment-1: challenge results (2019-01-01 to 2023-12-31)

Pre-registered historical holdout on close-proxy data (daily closes), not a 15:00 desk validation and not a forward test; anything that passes still needs forward paper evidence.

Opportunities: 60. Pass/fail applies (protocol section 8).

| Policy | Total net (Rs) | Mean per opportunity | Traded | Win rate (traded) | Worst | Max drawdown | No-settlement total | Impossible exits (count, net) | Best-year share | Statuses |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | -34,485.57 | -574.76 | 58 | 50% | -11,345.83 | 40,607.17 | -44,394.89 | 1, -11,345.83 | - | bad_prices 1, traded 58, unfillable 1 |
| P2 | -58,218.56 | -970.31 | 56 | 30% | -13,727.53 | 60,292.82 | -57,719.99 | 2, -15,515.31 | - | traded 56, unfillable 4 |
| P3 | 24,119.64 | 401.99 | 50 | 22% | -4,474.05 | 36,954.50 | -42,640.89 | 4, 26,762.14 | 100% | bad_prices 5, traded 50, unfillable 5 |
| P4 | -29,189.63 | -486.49 | 35 | 49% | -11,345.83 | 31,607.33 | -20,969.64 | 1, -11,345.83 | - | bad_prices 1, no_trade 23, traded 35, unfillable 1 |
| P4 opposite | -12,422.36 | -207.04 | 13 | 38% | -8,936.77 | 20,670.78 | -18,534.14 | 0, 0.00 | - | no_trade 47, traded 13 |
| P5 | -805.57 | -13.43 | 46 | 43% | -11,345.83 | 17,734.27 | -28,915.69 | 3, 4,310.89 | - | bad_prices 1, no_trade 10, traded 46, unfillable 3 |
| P5 opposite | -45,575.21 | -759.59 | 43 | 14% | -8,936.77 | 50,695.22 | -52,259.58 | 1, -495.40 | - | bad_prices 5, no_trade 10, traded 43, unfillable 2 |
| P6 | -18,468.26 | -307.80 | 24 | 54% | -11,345.83 | 23,366.51 | -10,248.27 | 1, -11,345.83 | - | no_trade 35, traded 24, unfillable 1 |
| P6 opposite | -23,143.73 | -385.73 | 24 | 38% | -8,936.77 | 27,955.28 | -29,255.51 | 0, 0.00 | - | bad_prices 1, no_trade 35, traded 24 |
| P7 | -25,280.85 | -421.35 | 25 | 40% | -11,345.83 | 30,774.70 | -21,943.53 | 1, -11,345.83 | - | no_trade 34, traded 25, unfillable 1 |
| P7 opposite | -9,204.71 | -153.41 | 33 | 58% | -8,936.77 | 17,749.23 | -22,451.36 | 0, 0.00 | - | bad_prices 1, no_trade 26, traded 33 |
| P8 | -13,242.70 | -220.71 | 36 | 42% | -3,302.12 | 16,738.47 | -18,171.44 | 1, -1,787.78 | - | no_trade 23, traded 36, unfillable 1 |
| P8 opposite | -28,959.86 | -482.66 | 11 | 9% | -13,727.53 | 28,959.86 | -28,959.86 | 1, -13,727.53 | - | no_trade 47, traded 11, unfillable 2 |

## Verdict: complete; passing: none

| Policy | Criterion | Value | Rule | Threshold | Pass |
|---|---|---|---|---|---|
| P1 | 1_total_net | -34,485.57 | > | 0.00 | no |
| P1 | 2_bootstrap_lower_bound | -1,783.14 | > | 0.00 | no |
| P1 | 7_max_modelled_loss | 9,913.91 | <= | 10,000.00 | yes |
| P2 | 1_total_net | -58,218.56 | > | 0.00 | no |
| P2 | 2_bootstrap_lower_bound | -1,782.51 | > | 0.00 | no |
| P2 | 7_max_modelled_loss | 9,571.26 | <= | 10,000.00 | yes |
| P3 | 1_total_net | 24,119.64 | > | 0.00 | yes |
| P3 | 2_bootstrap_lower_bound | -612.77 | > | 0.00 | no |
| P3 | 7_max_modelled_loss | 9,951.69 | <= | 10,000.00 | yes |
| P4 | 1_total_net | -29,189.63 | > | 0.00 | no |
| P4 | 2_bootstrap_lower_bound | -1,398.97 | > | 0.00 | no |
| P4 | 3_above_random_timing | -29,189.63 | > | 1,685.41 | no |
| P4 | 3_above_opposite | -29,189.63 | > | -12,422.36 | no |
| P4 | 4_above_P1 | -29,189.63 | > | -34,485.57 | yes |
| P4 | 7_max_modelled_loss | 9,913.91 | <= | 10,000.00 | yes |
| P5 | 1_total_net | -805.57 | > | 0.00 | no |
| P5 | 2_bootstrap_lower_bound | -1,206.43 | > | 0.00 | no |
| P5 | 3_above_random_timing | -805.57 | > | 13,958.25 | no |
| P5 | 3_above_opposite | -805.57 | > | -45,575.21 | yes |
| P5 | 4_above_P1 | -805.57 | > | -34,485.57 | yes |
| P5 | 4_above_P4 | -805.57 | > | -29,189.63 | yes |
| P5 | 5_bf_branch | 28,384.06 | > | 0.00 | yes |
| P5 | 7_max_modelled_loss | 9,913.91 | <= | 10,000.00 | yes |
| P6 | 1_total_net | -18,468.26 | > | 0.00 | no |
| P6 | 2_bootstrap_lower_bound | -1,179.09 | > | 0.00 | no |
| P6 | 3_above_random_timing | -18,468.26 | > | 8,449.48 | no |
| P6 | 3_above_opposite | -18,468.26 | > | -23,143.73 | yes |
| P6 | 4_above_P1 | -18,468.26 | > | -34,485.57 | yes |
| P6 | 4_above_P4 | -18,468.26 | > | -29,189.63 | yes |
| P6 | 6_event_filter | -10,721.37 | < | 0.00 | yes |
| P6 | 7_max_modelled_loss | 9,913.91 | <= | 10,000.00 | yes |
| P7 | 1_total_net | -25,280.85 | > | 0.00 | no |
| P7 | 2_bootstrap_lower_bound | -1,304.52 | > | 0.00 | no |
| P7 | 3_above_random_timing | -25,280.85 | > | 8,002.36 | no |
| P7 | 3_above_opposite | -25,280.85 | > | -9,204.71 | no |
| P7 | 4_above_P1 | -25,280.85 | > | -34,485.57 | yes |
| P7 | 7_max_modelled_loss | 9,855.14 | <= | 10,000.00 | yes |
| P8 | 1_total_net | -13,242.70 | > | 0.00 | no |
| P8 | 2_bootstrap_lower_bound | -615.45 | > | 0.00 | no |
| P8 | 3_above_random_timing | -13,242.70 | > | -21,295.53 | yes |
| P8 | 3_above_opposite | -13,242.70 | > | -28,959.86 | yes |
| P8 | 4_above_P2 | -13,242.70 | > | -58,218.56 | yes |
| P8 | 7_max_modelled_loss | 5,664.89 | <= | 10,000.00 | yes |
