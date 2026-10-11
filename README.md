# F&O options research assistant (India)

A research and paper-trading toolkit for NSE index options (NIFTY, BANKNIFTY and others).
Each run scans the option chain, scores the market's direction and volatility, builds candidate
trades, sizes them to your risk budget, and writes a daily brief. It is a research aid. It does
not place orders. You decide whether to take a trade and place it yourself on Groww.

> Reality check: SEBI's studies found roughly 9 in 10 individual F&O traders lost money.
> Run this as a paper-trading experiment first and judge it on 20-30 closed trades, not on a few wins.

## Quick start

```bash
pip install -r requirements.txt
python -m fno brief                  # scan config underlyings, write reports/<date>-brief.md
python -m fno brief NIFTY            # just one underlying
python -m fno chain NIFTY            # print the chain around the money (nearest expiry)
python -m fno --provider sample brief  # offline synthetic data, for testing
python -m pytest -q
```

## Paper-trading loop

```bash
python -m fno brief                            # 1. read the brief, pick a setup id
python -m fno paper open NIFTY-19Oct-BPS-22500-22100 --note "why I took it"
python -m fno paper mark                       # 2. re-price open trades; auto-closes on stop/target/time exit
python -m fno paper close T001                 #    or close one manually
python -m fno paper report                     # 3. scorecard: win rate, expectancy, drawdown, charges
```

Trades are stored in `journal/trades.json` and committed to git, so the record survives between sessions.
Paper fills assume you buy at the ask and sell at the bid, and they include Groww brokerage and statutory charges.

## How a setup is chosen

1. **Data**: option chain (LTP, bid/ask, OI, IV) for expiries 3-35 days out, daily index history, India VIX.
2. **Signals**, each scored -1 to +1 and weighted into a **bias**:
   - trend: spot vs 20/50-day EMAs
   - momentum: 20-day return
   - RSI(14): follows the trend in the middle band, fades it at the extremes
   - put/call OI ratio
   - where spot sits between the biggest put-OI strike (support) and call-OI strike (resistance)
3. **Volatility regime**: ATM implied vol vs 20-day realised vol, and VIX within its 1-year range,
   classed as cheap, normal or rich. Buying single options is skipped when options look rich.
4. **Candidates**: bull call / bear put spreads with widths of about the straddle-implied move and half of it,
   ATM long calls and puts, and optionally an iron condor.
5. **Scoring**: payoff is integrated over a lognormal distribution built from the market's implied vol,
   tilted by the bias (`signals.view_strength`). Without that tilt every trade has roughly zero expected value
   minus costs. **Any edge comes from the view, and the view can be wrong.**
6. **Sizing**: lots = risk budget / (stop-loss amount + charges). Setups that don't fit in one lot are flagged.
7. **No trade** is a valid output when the signal is weak or mixed.

## Data providers

| Provider | Cost | Notes |
|---|---|---|
| `nse` (default) | free | Public NSE website JSON plus Yahoo daily history. Unofficial and can be throttled. Bid/ask included. |
| `groww` | about Rs 499/month | Official Groww Trade API (`pip install growwapi`). Read-only use here. |
| `sample` | free | Synthetic, deterministic data for tests. |

Groww credentials are read from environment variables only. Never commit them:
`GROWW_ACCESS_TOKEN`, or `GROWW_API_KEY` with `GROWW_API_SECRET` (or `GROWW_TOTP_SECRET`).

## Configuration

Everything lives in `config.yaml`: capital, risk per trade, max open trades, expiry window, strategy menu,
liquidity filters, exit rules, lot-size fallbacks and Groww's charge schedule. Lot sizes and charges change.
The NSE provider infers the live lot size, but check the charges against Groww's pricing page.

## Layout

```
fno/
  providers/   nse (public), groww (Trade API), sample (offline)
  analytics.py Black-Scholes, IV, PCR, max pain, OI walls, EMA/RSI/realised vol
  signals.py   directional bias + volatility regime
  strategies.py candidate construction, payoff analysis, scoring, sizing
  brief.py     daily Markdown/JSON brief
  journal.py   paper-trading journal and scorecard
  costs.py     Groww + statutory charges
reports/       daily briefs and candidate files
journal/       paper trades
tests/         unit tests (incl. a real NSE chain fixture)
```
