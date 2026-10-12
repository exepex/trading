# 12 Oct 2026 backtest: reproducible evidence

Everything behind `reports/2026-10-12-backtest-analysis.md`, frozen so anyone can re-run it (asked for in ChatGPT
review 2, section 2). No network access and no orders.

## Inputs (frozen, checked by sha256 before every run)

| File | What | sha256 |
|---|---|---|
| `inputs/candles.csv.gz` | Yahoo 5-minute prices, 27 Aug - 12 Oct 2026, 9 names plus NIFTY as benchmark | `d0adda55...5d3d85` |
| `inputs/lot_sizes.json` | Lot sizes used | `b4d05c83...f55669` |
| `inputs/config.yaml` | The configuration used (charges, exits, cooldowns, rules) | `cc6d55bd...b14742` |

## Commands (from the repository root)

```
python research/2026-10-12-backtest/replay.py      # trades.csv, controls.csv, random_runs.csv, summary.json
python research/2026-10-12-backtest/cost_table.py  # the NIFTY debit-spread cost table (cost_table.md)
```

Random seeds: 0-29 (Python `random.Random(seed)`, one coin toss per entry, in entry order).

## Outputs

- `trades.csv`: all 219 entries (`E001`-`E219`): name, direction, option, strike, lot, volatility, entry, exit,
  reason, status (closed, or open and marked at the last close), charges, net.
- `controls.csv`: every entry under every control (rules, opposite, always bullish, always bearish): status and net.
- `random_runs.csv`: all 30 coin-toss runs: seed, net, wins.
- `summary.json`: totals and the two bridges below.

## Bridges

| Item | Rs |
|---|---|
| 211 closed trades | -1,90,016.80 |
| + 8 positions still open, marked at the last close minus selling charges | +1,612.35 |
| = all 219 entries | **-1,88,404.45** |

Stops at the open after an overnight hold (corrected after ChatGPT review 3: the first version counted two 09:25
exits as first-bar stops and used the same morning's first bar as their "previous close"). Boundaries are now found
explicitly: the last candle of the previous session and the 09:15 candle of the exit session.

| Part of the loss | 25 first-bar stops (exit 09:20) | 27 stops in the first ten minutes (exit by 09:25) |
|---|---|---|
| Lost before the previous close | -6,584.81 | -8,951.19 |
| Overnight option-value change (price gap **and** a night of time decay) | -85,518.63 | -87,596.81 |
| Open to exit | -37,932.93 | -41,736.24 |
| Charges | -1,565.30 | -1,707.05 |
| = total | **-1,31,601.67** | **-1,39,991.29** |

## Limits

Model prices (Black-Scholes, volatility = recent 5-minute volatility x 1.1, floor 8%, 10 days to expiry), not
quotes; stops checked on 5-minute closes; one falling month. See the analysis report, section 6.
