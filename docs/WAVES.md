# Work before the AI layer, in waves

Owner's process (12 Oct 2026): work in waves of user stories. After each wave an independent judge
(`docs/JUDGE.md`) checks every claim against the code, tests and real runs. Findings are fixed and re-reviewed until
the judge passes the wave. The AI layer starts only when every wave has passed and the work is on `main`.
Verdicts are kept in `judgments/wave-<n>-<round>.md`.

Every story must also meet the project rules in CLAUDE.md (tests and ruff pass, files under 350 lines, constants in
`fno/constants.py`, wiring only in `fno/live/services.py`, no real orders, no secrets in files).

## Wave 0: work done earlier on 12 Oct, reviewed retrospectively (commits 4eaf7f3..3f012cd)

Claims to verify (details in docs/SAFEGUARDS.md, docs/DATA_SOURCES.md, docs/NEWS_FEED_PLAN.md):
- **W0.1 Safeguards**: 2% risk per trade enforced by the contract picker; trade frequency caps, loss cooldown, weekly
  loss limit, overnight exposure cap, trailing stop, automatic performance kill switch, go-live readiness checks.
- **W0.2 Profiles and shadow book**: `paper` (Rs 5 lakh, 2%) and `live` (Rs 2 lakh) profiles differ only in money
  limits; the shadow book trades one lot of every idea, ignores portfolio limits, never alerts, once per contract
  per day.
- **W0.3 Polite data fetching**: at most one request a second per host, a 15-minute pause after two refusals in a
  row, one cached option chain shared by the scan and both books, 5-minute scans and 2-minute reviews.
- **W0.4 Groww data**: automatic re-sign-in after the 06:00 IST token expiry, `chain_provider: auto`, `groww-check`
  prints no secrets, the desk never places orders.
- **W0.5 Fast news watcher**: 13 free sources, one request at a time at least 5 s apart, staggered, each never faster
  than its interval or cache time, back-off on failure, daily allowances, only on trading days 08:45-15:45 IST;
  same news from many sources is one story; the same outlet repeating it is a duplicate; credibility levels; only
  F&O-relevant or world-risk stories stored, in `data/live/news`; API keys never in logs or errors.
- **W0.6 News weighting**: classifier (type and direction), impact = type x credibility x relevance x freshness x
  direction, `fast_news` signal, `news_shock` guard, `adverse_news` early exit that can only close trades.

## Wave 1: honest paper results and less hidden risk

**W1.1 Realistic fills.** As the owner, I want paper trades priced at the real bid (sell) and ask (buy), so paper
profits are not flattering.
- When a chain quote has no bid/ask (Groww's option chain gives last price only), entry and exit use the provider's
  live quote for that contract; the NSE chain's own bid/ask is used as is.
- The spread check uses the live bid/ask before entry.
- Each trade records how it was priced (`fill_source`: bid/ask or last price +/- slippage).
- Tests cover: chain with book, chain without book plus quote, quote unavailable (falls back, recorded honestly).

**W1.2 Option-price (implied volatility) history.** As the analyst, I want one at-the-money implied volatility per
underlying per day stored from today, so we can tell cheap options from expensive ones against their own history.
- The desk keeps the latest ATM IV of every chain it reads during the day and stores one `iv_snapshot` per
  underlying per day after the close (with the day summary), for the underlyings it scanned that day.
- `iv_rank(symbol, iv)` = where today's IV sits between its stored low and high (0-100), only with at least
  `min_days` of history, else None.
- The expensive-options guard also blocks when IV rank is above `max_iv_rank` (only once enough history exists).

**W1.3 One bet, not three.** As the owner, I want correlated trades counted as one bet.
- Each underlying belongs to a family: its NSE industry for stocks; BANKNIFTY and FINNIFTY with financial stocks;
  NIFTY in a broad-market family.
- The portfolio gate refuses a new trade when `max_per_family` open trades (default 2) are already in its family.

**W1.4 Good and bad hours.** As the analyst, I want results by time of entry and days to expiry.
- `python -m fno live trade-stats` shows trades, win rate and net P&L by entry time bucket, by days to expiry at
  entry, and by exit reason, for the paper book and (with `--shadow`) the shadow book.

## Wave 2: trade only when the odds favour an option buyer

**W2.1 Trending or sideways day.** No new option purchase on an underlying that is not trending now: the efficiency
of its 5-minute moves over the last hour (net move / total path) is below 0.30, and until at least 30 minutes of
the session exist. Calibrated on 45 real sessions: whole-day efficiency (median 0.12) is too noisy; the last hour
(median 0.26) is used, and 0.30 lets through roughly the most trending 45% of hours.
**W2.2 Move needed vs move likely.** Before entry, the underlying move needed for the option to reach its target
(delta and gamma, net of time decay over the holding period) must be at most a set share of the move the market
expects (ATM implied volatility over the holding period). Otherwise the idea is refused; accepted ideas carry the
numbers in their notes. Calibrated on real chains (12 Oct): near-the-money 2-week options need 1.2-1.5x the
expected 2-day move to make +60%, so the limit is 1.5x; the +60% target itself is to be reviewed with paper data.
**W2.3 Big-investor positioning.** A signal for the indices from NSE's daily participant-wise open interest (last 10
sessions, read each morning): the change in foreign investors' index futures long share against its recent average
and the change in the tilt of their index options book. Change, not level: FIIs hold structurally short index
futures (about 10% long in Oct 2026).

## Wave 3: speed and evidence

**W3.1 Sudden-move detector.** With Groww credentials, the latest prices of the indices and of every underlying
held are read every 20 seconds (Groww `get_ltp`, up to 50 per call; no free source may be polled this often). A move
of 0.4% (index) or 1.5% (stock) within two minutes is a shock (once per 10 minutes per name): it is recorded
(`price_shock`), open trades are re-checked in the same tick (stop, target, trailing, news exit: exit only), and the
exchange-filing and Marketaux news sources are asked next. Without Groww the detector is off (the 2-minute review
still protects trades).
**W3.2 Backtest harness.** `python -m fno backtest [symbols] [--days N]` replays the desk's own rules, guards that
can be judged from prices (sideways day), exits (stop, target, trailing, holding days) and charges on up to 59 days
of 5-minute prices (Yahoo's limit), one modelled option per underlying at a time (Black-Scholes, volatility from
the underlying's own recent moves x 1.1, ~10 days to expiry), and grades every rule's vote against the next 30
minutes. Clearly labelled as an approximation; report saved to `reports/backtest-<date>.md`.
First run (12 Oct, 30 days, 9 names): 243 trades, net -Rs 1.86 lakh at one lot each; rule hit rates 49-54%:
price-action rules alone are no edge.
