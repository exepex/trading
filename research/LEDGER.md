# Research ledger: every idea tried, kept or rejected

Why: the more variants are tried on the same history, the more likely one looks good by luck (Bailey et al., *The
Probability of Backtest Overfitting*). Every test is listed here, including failures, so the number of trials behind
any winner is visible. NIFTY 2024-2026 daily closes are **discovery data**: never call them out-of-sample later.
Untouched checks still available: NIFTY 2019-2023 (older NSE files) and forward paper trading.

| # | Date | Meeting | Idea tested (data: NIFTY monthly options, 2024-2026, close-proxy) | Result | Status |
|---|---|---|---|---|---|
| 1 | 2026-10-12 | backtest | Chart-rule option buying, 30 days intraday (original live strategy) | No positive edge established; lost after costs | Rejected as is |
| 2-4 | 2026-10-12 | desk 1 | Trend continuation over 5 / 10 / 20 days | 50-52% same direction | No simple trend edge |
| 5 | 2026-10-12 | desk 1 | Short ATM straddle, 30-45 days in, exit at 21 days | +Rs 2,87,463, 33 cycles, worst -Rs 41,030 | Diagnostic only (unprotected) |
| 6 | 2026-10-12 | desk 1 | Long ATM straddle | -Rs 3,24,905 | Rejected |
| 7 | 2026-10-12 | desk 1 | Iron condor 3% / 6% | in results.json | Superseded by 12-17 |
| 8-9 | 2026-10-12 | desk 1 | Bull call 100 / bear put 100 | -Rs 27,541 / -Rs 5,304 | Rejected |
| 10 | 2026-10-12 | desk 1 | Trend-following spread (20-day average) | -Rs 15,280 | Rejected |
| 11 | 2026-10-12 | desk 1 | Short straddle (variants.py rerun) | as 5 | - |
| 12-17 | 2026-10-12 | desk 1 | Iron condors: short 0/2/3% from spot x protection 300/500 | +Rs 24,757 to +Rs 69,026 on 10-30 tradable months | Lead hypothesis; data gap (far strikes) |
| 18-19 | 2026-10-12 | review 9 | Hindsight splits: IV vs realised (holding / to expiry) | Not usable: future data | Diagnostic only |
| 20-21 | 2026-10-12 | review 9 | Entry-known: IV > past 20-day realised (+0 / +2 points), on the short straddle | +0: kept 27 cycles, +Rs 3,10,568, worst -Rs 7,867; skipped 5, -Rs 16,705 incl. the 3 worst | Candidate filter, to test on protected trades and 2019-2023 |

| - | 2026-10-12 | review 10 | Correction, not a trial: realised volatility now counts all movement (not demeaned) | Average realised 11.9% -> 12.2%; trade P&Ls unchanged; the +2 variant now keeps 16 cycles (+Rs 2,26,128) | Fixed in desk.py |

| 22-29 | 2026-10-12 | experiment 1 | Registered before results (protocol draft): P1-P8 (protected sell / buy / no trade by F1 volatility premium, F2 VIX level, F3 events), width rule for the Rs 10,000 cap | Pending | Discovery 2024-26 and challenge 2019-23 |
| 30-31 | 2026-10-12 | experiment 1 | Controls C1 (coin toss) and C2 (opposite of P4) | Pending | Controls |

Total trials so far: 31 (count every new variant, threshold or filter here before reading its result).
