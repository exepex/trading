# F&O options research assistant (India)

A research and paper-trading toolkit for NSE index options (NIFTY, BANKNIFTY and others).
Each run scans the option chain, scores the market's direction and volatility, builds candidate
trades, sizes them to your risk budget, and writes a daily brief. It is a research aid. It does
not place orders. You decide whether to take a trade and place it yourself on Groww.

> Reality check: SEBI's studies found roughly 9 in 10 individual F&O traders lost money. How the desk guards
> against each cause: `docs/SAFEGUARDS.md` (research: `reports/Retail FnO losses and safeguards.md`).
> Run this as a paper-trading experiment first and judge it on 20-30 closed trades, not on a few wins.

## Quick start

```bash
pip install -r requirements.txt
python -m fno daily                  # morning routine: mark paper trades, write brief (.md/.html) + Slack text
python -m fno brief                  # scan config underlyings, write reports/<date>-brief.md/.html
python -m fno brief NIFTY            # just one underlying
python -m fno chain NIFTY            # print the chain around the money (nearest expiry)
python -m fno --provider sample brief  # offline synthetic data, for testing
python -m pytest -q
```

## Live desk (all F&O underlyings, intraday)

```bash
python -m fno live scan-once        # one diagnostic scan now: views, ideas, why others were skipped
python -m fno live run              # market-hours service; unattended on any OS: deploy/README.md
python -m fno live status           # open paper trades, today's net P&L, kill switch
python -m fno live kill "reason"    # close all paper trades and block new ones
python -m fno live resume
```

Every 5 minutes during the session (free data sources; 3 minutes once the Groww feed is in) the desk:
1. snapshots all ~200 F&O underlyings (price move, futures open-interest change, F&O ban list);
2. shortlists the 12 most active liquid names (NIFTY, BANKNIFTY and FINNIFTY always included);
3. scores each with 18 signal rules (weights in `config.yaml` `live.signals`):
   - price action today: opening-range breakout, VWAP, 5-minute EMA trend, strength vs NIFTY;
   - today vs earlier sessions: previous-day high/low breakout, volume vs normal for the time of day;
   - derivatives positioning: futures OI build-up, fresh put vs call writing near the money;
   - market backdrop: sector index vs NIFTY, breadth across all F&O stocks, global markets, India VIX direction;
   - the stock tool's research: verified news sentiment, model probability, fresh exchange filings,
     block/bulk deals, foreign investor flows;
   - fast news: each story's type x credibility x relevance x freshness x direction (`live.news.impact`);
4. applies guards: F&O ban list, results within 2 days (IV crush), market stress or high-impact geopolitical
   news, options priced far above the stock's realised volatility, and the 15 minutes after credible big news
   whose direction is unclear;
5. picks one liquid option near 0.55 delta (calls when bullish, puts when bearish), sizes it with
   `position_rules`, and opens a paper trade if the portfolio gate allows it (5 open max, Rs 70,000 cap,
   daily loss limit, profit lock, no entries after 14:45);
6. every 2 minutes re-prices open trades and exits on stop (-30%), target (+60%), a trailing stop (after +30%,
   keep at least half the best gain), the 15:15 square-off on the last holding day, or the day before expiry.
   Strong, credible news against an open trade closes it early (`exits.adverse_news`).
   Every entry and exit posts to #fno-desk with net P&L. Concentration limits: at most 3 trades on the same
   side and 2 index trades at once.
7. grades every view: the price 30 and 90 minutes later is compared with each rule's vote.
   `python -m fno live signal-report` shows each rule's hit rate and information coefficient, and suggests
   weights. Use it to keep the rules that predict and drop the noise.

**Fast news** (`live.news`, docs/NEWS_FEED_PLAN.md): beside the desk, a watcher asks free sources one request at a
time, at least 5 seconds apart, each at its own pace and never faster than its own cache time: NSE and BSE company
filings every minute, ET Markets, Mint, CNBC-TV18, Business Standard, BusinessLine, BBC and MarketWatch feeds every
1.5-5 minutes, and Finnhub, Marketaux and AskNews when their keys are set. Outside market hours it slows down 5x.
The same news from several sources becomes one story, tagged with its stocks or indices (or WORLD for war, oil,
central banks), and every later source is timed against the first. `python -m fno live news-once` checks every source;
`python -m fno live news-report` shows which sources deliver first.

Research is read from the stock tool's GitHub data files (`data/india/` in agentic-stock-prediction: news,
its scores and verification, earnings dates, regime, model scores). The desk keeps a small sparse clone in
`data/research/` and pulls it every 30 minutes. The desk's own results are daily JSONL files in
`data/live/events/`, saved to GitHub at the end of each day. MotherDuck is optional for both
(`live.research.source: motherduck`, `live.results.store: duckdb`, using `MOTHERDUCK_TOKEN`); raw minute data is
never stored anywhere.

```
fno/live/
  feeds/       nse_feed (lots, ban list, holidays, OI moves) · price_feed (Yahoo; Groww later)
  research/    research_source (interface) · repo_source + repo_sync (GitHub files, default)
               motherduck_source (optional) · research_context (snapshot used by the rules)
  signals/     base · price_action · positioning · research_signals · guards · registry
  market_view  shortlist  contract_picker  risk_gate  exit_policy  market_clock  kill_switch
  paper_desk   alerts  results_store (JSONL, default) + duckdb_results_store (optional)
  universe  scanner  runner  services (wiring)  cli
```
Add a signal rule: subclass `SignalRule` in `fno/live/signals/`, register it in `registry.py`, give it a weight in
`config.yaml` (`live.signals`). Nothing else changes.

### Settings profiles and the shadow book

`config.yaml` holds the conservative real-money limits (Rs 2 lakh). `profile: paper` (the default while testing)
merges `profiles.paper` over them: Rs 5 lakh paper capital at 2% risk, so BANKNIFTY and FINNIFTY lots fit.
Set `profile: live` before real money. With `live.shadow_book.enabled`, every idea that passes the signals and
guards is also paper-traded at one lot in `journal/shadow_trades.json`, ignoring portfolio limits and without
Slack messages, to grade signals on more data. Details: `docs/SAFEGUARDS.md`.

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

Groww credentials are read from environment variables or `~/.trading.env` only. Never commit them.
Recommended: `GROWW_API_KEY` with `GROWW_TOTP_SECRET` (TOTP key: no daily approval). The desk signs in again by itself
after tokens expire at 06:00 IST. `live.chain_provider: auto` uses Groww whenever these are set, else the NSE website.
Check the connection with `python -m fno groww-check` (prints no secrets). The SDK is in `requirements-groww.txt`,
which `deploy/setup.py` installs. Data calls need no fixed IP address; the static-IP rule covers placing orders, which
this tool never does.

## Slack

The F&O bot posts to `#fno-desk` and uses its own environment variables, separate from the market-brief tool's
`SLACK_*` ones:

| Variable | Purpose |
|---|---|
| `FNO_SLACK_BOT_TOKEN` | Bot token of the F&O Slack app (scopes `chat:write`, `files:write`); posts text and page images |
| `FNO_SLACK_CHANNEL_ID` | Optional; defaults to `slack.channel_id` in `config.yaml` |
| `FNO_SLACK_WEBHOOK_URL` | Optional incoming webhook for a text-only post when there is no bot token |

`python -m fno notify` posts the day's brief.

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
  brief.py     daily Markdown/JSON brief and Slack summary
  html_report.py phone-friendly HTML brief
  journal.py   paper-trading journal and scorecard
  costs.py     Groww + statutory charges
reports/       daily briefs (Markdown, HTML), Slack summaries and candidate files
conversations/ daily conversation logs
journal/       paper trades
tests/         unit tests (incl. a real NSE chain fixture)
```
