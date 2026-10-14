# Research ledger: every idea tried, kept or rejected

Why: the more variants are tried on the same history, the more likely one looks good by luck (Bailey et al., *The
Probability of Backtest Overfitting*). Every test is listed here, including failures, so the number of trials behind
any winner is visible. NIFTY 2024-2026 daily closes are **discovery data**: never call them out-of-sample later.
Untouched checks still available: NIFTY 2019-2023 (older NSE files) and forward paper trading.

**Machine record:** `research/ledger.csv` (one row per trial) is what the engine checks before any trial runs
(`fno/research_engine/ledger.py`, story B4): registration must be committed, and the trial's protocol frozen and
unchanged. Trials 1-21 are `retrospective` (recorded while or after being run). Experiment 1's trials 22-31 were
registered before any of their results; they run only after the protocol freeze fills in `protocol_commit`.

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
| 30-31 | 2026-10-12 | experiment 1 | Controls C1 (random timing, frequency-matched) and C2 (opposite condition), per conditional policy; protocol v2 | Pending | Controls, not hypotheses (family = 8 policies) |
| 32-36 | 2026-10-13 | forecasts v1 | Registered before any forecast exists (story G1): the five daily forecast questions, scored by the protocol's 10-test primary family, Book 2 and Book 3 against Book 1 (`research/forecasts/PROTOCOL.md`; review 28) | Pending | Diagnostic only: forecasts never promote a book |
| 37-41 | 2026-10-13 | forecasts v2 | The five daily forecast questions on live 15:00 inputs, books vs baselines (`research/forecasts/PROTOCOL_v2.md`), as `research/ledger.csv` holds them | Pending | Diagnostic only: forecasts never promote a book |
| 42 | 2026-10-14 | desk 2 | Put-spread pricing model: 14 Oct 15:00 prices replayed on the 93 holding-window NIFTY moves 2019-26, one more look at the 2019-23 windows (response 92) | Mean -Rs 243 a trade at the 21-day exit, -Rs 355 held to expiry | Not pursued (model, reasoning only) |

Total trials so far: 42 (count every new variant, threshold or filter here before reading its result).
