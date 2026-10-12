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
never places orders. Groww's chain gives last prices only, so the chosen contract is checked against its live
quote (bid/ask) before entry and priced at the live bid on exit (falling back to last price if the quote call fails).
Still to move to Groww: stock prices and 5-minute candles (Yahoo today).

## Earlier plan: the Groww feed

Free sources are fine for building and paper testing, not for real trades: they lag, they can block us, and their
terms forbid automated use. Prices and option chains move to the official **Groww Trade API** (Rs 499 a month,
option chains with Greeks) once the account is reactivated. The desk already has the `groww` provider; switching is
`live.chain_provider: groww` plus a Groww price feed behind `IntradayPriceFeed`. Then scans can run every 3 minutes
and reviews every minute. (Upstox and Angel One offer free feeds, but would mean opening a second broker account.)

## Headlines

Breaking news for the shortlist and open trades will come from publishers' own RSS feeds (ET Markets, Livemint,
Business Standard, BusinessLine) every 10 minutes during market hours, asking "anything new since last time?" so
unchanged feeds cost almost nothing. Not Google News (its robots.txt disallows `/rss`). BSE filings are asked once a minute from the owner's PC; BSE refuses cloud servers, and the watcher then simply backs off. This runs in
this repo; the stock tool is not changed.

## Paid news options checked (12 Oct 2026)

| Option | Cost | What it gives | Verdict |
|---|---|---|---|
| Groww Trade API | already paid | no news at all | prices and chains only |
| Drishti (drishti.manasija.in) | free sandbox (1,000 credits, once); Starter Rs 2,000/month | Indian stocks only: news tagged by symbol with a positive/negative/neutral label, structured NSE/BSE filings (Reg 30), block deals; WebSocket push for 100 symbols on Starter | best fit; trial the free sandbox first. New company (terms dated June 2026), no published latency or source list |
| NewsData.io | free plan delayed 12 hours; Basic $199.99/month | worldwide news, sentiment only from $349.99/month | not for trading: free is too late, paid too expensive |
| Upstox News API | free with an Upstox account | Upstox's own articles for up to 30 stocks per call, last 7 days, no sentiment | needs a second broker account and its daily login; not worth it for news alone |

### Cheap global news APIs (checked on their pricing pages, 12 Oct 2026)

| API | Price | Quota | Fit |
|---|---|---|---|
| Marketaux Basic | $29/month ($24 yearly) | 2,500 requests/day, 20 articles each | global + Indian (.NS/.BO) symbols tagged, sentiment -1..+1 per stock, filter by country/exchange/symbol and `published_after`; one call a minute for India and one for the world fits in market hours. Free plan: 100/day, 3 articles: enough only for a trial |
| Finnhub Free | $0, personal use | 60 calls/minute | world market headlines and US company news every minute; India company news not covered |
| TheNewsAPI Basic | $19/month | 2,500 requests/day, 25 articles each | general world news, no stock tagging or sentiment |
| Drishti Starter | Rs 2,000/month | WebSocket push, 100 symbols | India only; exchange filings |

Recommended: Finnhub Free for world headlines plus a Marketaux trial; Marketaux Basic if the trial shows timely Indian
coverage. A paid quota is not a blocking risk: polling within the plan is what the customer pays for.

## Free broker feeds checked (12 Oct 2026)

Upstox (staff on its forum: "Realtime market data over our web-sockets is completely free") and Angel One SmartAPI
(free APIs, real-time WebSocket; static IP needed only for orders) both offer free live data, but each needs its own
broker account and daily login. Groww (already paid) supplies prices and option chains, so these stay a fallback if
Groww's feed proves unreliable.
