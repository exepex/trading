# Breadth sizing (BR1 design proposal, response 154)

Research only, read-only. It measures how independent daily forecasts across NSE F&O underlyings are, and how many
months a real skill needs to show. Those two numbers decide whether a breadth track can be fast.

    sh tools/routine_setup.sh                                                    # once: google.auth for the fetch
    python research/2026-10-15-breadth-sizing/fetch.py <scratch>/raw 700        # last 700 UDiFF F&O bhavcopies
    python -I research/2026-10-15-breadth-sizing/extract.py <scratch>/raw <scratch>/table.csv
    python -I research/2026-10-15-breadth-sizing/sizing.py <scratch>/table.csv [first day] [last day]

- The fetch only reads the shared Drive raw archive. It never writes there and never calls NSE.
- The scratch folder stays outside the repository.
- 700 files are about 790 MB and take about 15 minutes.

## Method (details in each script's docstring)

- **Target:** `Y(u, t)` = 1 when the next close-to-close move of underlying `u` is at least its ATM-straddle implied
  daily move.
- **Spot:** NSE's `UndrlygPric`, not adjusted for corporate actions.
- **Contract-adjustment rule:** the day of a contract adjustment is excluded when fewer than half of a stock's listed
  strikes on t, for an expiry listed on both days, are still listed on t+1. NSE replaces every strike on a split,
  bonus or demerger: KOTAKBANK 14 Jan 2026, TATAMOTORS 14 Oct 2025, TRENT 4 Jun 2026 and VEDL 30 Apr 2026 all kept 0%.
  On an ordinary crash NSE keeps every strike: KAYNES 14 May 2026, POLICYBZR 24 Sep 2026 and the 4 Jun 2024 election
  day all kept 100%.
- **Lot-size rule, rejected:** it missed the demergers and also dropped NSE's routine lot revisions (1,214 days in the
  last 300 sessions, against 41 for the strike rule).
- **Moves of 15% or more left after the rule:** 64 in 2024-26. Every one was checked: all are real market moves, 27
  of them on 4 Jun 2024.
- **Five forecasters:** `market` (the implied move at face value, p 0.317), `trail60`, `cal20`, `cal60` and `tilt`
  (`cal60` x 1.15, a uniform volatility tilt).
- **For each pair:** the correlation of score differences across names, N_eff, the SD and lag-1 autocorrelation of
  the daily mean, and the months a 2% or 3% Brier skill needs. Months use K = 3 or 12, alpha 0.05/K or v4's 0.02/K
  per look, and an AR(1) variance inflation of (1 + lag1) / (1 - lag1).

## Results

The full output is in `results/`, one file per window. Each file reports all names, the top 30 by option turnover and
the 4 indices:

| File | Window | Scored days | Names |
|---|---|---|---|
| `results/2024-01-01_2026-10-14.txt` | the whole UDiFF period | 631 | 138 |
| `results/2024-01-01_2024-12-31.txt` | 2024, with the election crash | 188 | 179 |
| `results/2025-01-01_2025-12-31.txt` | 2025 | 188 | 184 |
| `results/2026-01-01_2026-10-14.txt` | 2026 to date | 133 | 198 |
| `results/2025-07-29_2026-10-14.txt` | the first draft's window | 239 | 193 |

Limits:
- Only 2024-2026 is measured, because the legacy format of 2019-2023 has no spot column. Its re-measure, using the
  near-month future as spot, is a freeze gate (response 154).
- The weekday count to expiry ignores NSE holidays. That is fine for sizing; scoring uses the NSE calendar (A7).
- The top-30 list is chosen on the window's own turnover. That is fine for sizing; the real list is fixed by rule at
  the freeze.
