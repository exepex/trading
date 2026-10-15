# Breadth sizing (BR1 design proposal, response 154)

Research only, read-only. It measures how independent daily forecasts across NSE F&O underlyings really are. That
decides how fast a breadth track can show skill.

    python research/2026-10-15-breadth-sizing/fetch.py <scratch folder> 300    # copies the last 300 UDiFF F&O
                                                                                # bhavcopies from the Drive raw archive
    python -I research/2026-10-15-breadth-sizing/sizing.py <scratch folder>

The fetch only reads Drive. It never writes there and never calls NSE. The scratch folder stays outside the
repository.

## Method

- Per session and underlying: spot = `UndrlygPric`, the nearest expiry with at least 3 sessions left, and the ATM
  straddle (CE + PE close at the strike nearest spot, both traded, strike within 2% of spot).
- Implied daily move: `straddle / (spot x sqrt(2/pi) x sqrt(n))`.
- Target `Y` = 1 when the next close-to-close move, `|ln(S(t+1)/S(t))|`, is at least the implied daily move.
- Forecasters compared:
  - the market's own p, 0.3173 (correct only if implied were unbiased and the moves normal);
  - a 60-session trailing frequency of `Y`.
- The day count to expiry uses weekdays, not the NSE calendar. That is good enough for sizing, not for scoring.

## Result: 300 sessions, 2025-07-29 to 2026-10-14

These are the 239 scored days (each needs 60 earlier sessions), on 194 underlyings with a liquid ATM straddle on at
least 80% of the days. The 194 are 4 indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY) and 190 stocks.

```
sessions 300, scored days 239, underlyings 194 (4 indices)
base rate of Y: 0.281 (market-implied would be 0.317)
Y: avg pairwise rho all 0.114 -> N_eff 8.4 of 194; indices 0.604 -> N_eff 1.42 of 4
Brier difference: avg pairwise rho all 0.052 -> N_eff 17.5 of 194; indices 0.514 -> N_eff 1.57 of 4
share of Y variance from the day's market-wide mean: 0.118
Brier difference: mean -0.0020, sd per (u,t) 0.0754, sd of daily cross-sectional mean 0.0182
lag-1 autocorrelation of the daily mean Brier difference: 0.045
signed next-day returns: avg pairwise rho 0.291 -> N_eff 3.4
```

Limits:
- It covers one window of 14 months, one regime.
- The correlation of score differences depends on the pair of forecasters compared.
- Liquid large caps may be more correlated with each other than the average.
