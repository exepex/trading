# Where the desk gets its data, and how often

Based on the stock tool's research (`research_notes/Data fetch frequency/`, 12 Oct 2026).

## Today (paper trading, free sources)

| Data | Source | How often | Notes |
|---|---|---|---|
| Prices of all F&O stocks, 5-minute candles | Yahoo (unofficial) | every 5 min, 1 request a second at most | Yahoo blocks heavy users; its terms forbid automation |
| Option chains, OI changes, ban list, lot sizes | NSE website (unofficial) | chains every 5 min for the 12 shortlisted names; lists once a day | NSE's terms forbid automation; its chain lags 3-6 min |
| Open trades re-priced | the same NSE chains | every 2 min, one fetch shared by every trade on that chain | |
| News, research | the stock tool's GitHub files | every 30 min | already collected by the stock tool; we only read it |

Protections built in (`fno/http_pacing.py`, `fno/providers/cached.py`):
- at most one request a second to each site, shared by everything the desk runs;
- two refusals in a row ("too many requests" or "forbidden") pause that site for 15 minutes instead of retrying
  into a longer block; the scan carries on with what it has and reports the problem;
- one option-chain fetch serves the scan, the paper book and the shadow book.

The desk runs on the owner's PC, so it does not share an internet address with the stock tool's cloud runs:
a block here cannot break the stock tool's daily briefs, and the reverse.

## Groww Trade API (subscribed 12 Oct 2026)

Option chains (with Greeks) come from Groww as soon as `GROWW_API_KEY` and `GROWW_TOTP_SECRET` are in
`~/.trading.env` on the desk's PC (`live.chain_provider: auto`). Data calls work from a changing home IP: Groww's
static-IP requirement is worded around order placement only (groww.in/blog/static-ip-api-trading-setup), and this tool
never places orders. Still to move to Groww: stock prices and 5-minute candles (Yahoo today), and bid/ask for the chosen
contract (Groww's chain gives last price only; the quote call gives bid/ask).

## Earlier plan: the Groww feed

Free sources are fine for building and paper testing, not for real trades: they lag, they can block us, and their
terms forbid automated use. Prices and option chains move to the official **Groww Trade API** (Rs 499 a month,
option chains with Greeks) once the account is reactivated. The desk already has the `groww` provider; switching is
`live.chain_provider: groww` plus a Groww price feed behind `IntradayPriceFeed`. Then scans can run every 3 minutes
and reviews every minute. (Upstox and Angel One offer free feeds, but would mean opening a second broker account.)

## Headlines

Breaking news for the shortlist and open trades will come from publishers' own RSS feeds (ET Markets, Livemint,
Business Standard, BusinessLine) every 10 minutes during market hours, asking "anything new since last time?" so
unchanged feeds cost almost nothing. Not Google News (its robots.txt disallows `/rss`) and not BSE. This runs in
this repo; the stock tool is not changed.
