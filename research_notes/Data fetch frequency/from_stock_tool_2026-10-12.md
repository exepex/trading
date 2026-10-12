# How often can we fetch news and market data? (research, 12 Oct 2026)

**Question:** can market-brief's free data sources be fetched every 1–3 minutes, so the same data can feed the F&O tool?
**Short answer:**
- **News every 5–15 minutes:** yes, from publisher RSS feeds, with care.
- **Prices and option chains every 1–3 minutes:** no, not from free sources. That needs an official broker data feed (₹0–500 a month).

## How this was checked

- **Inventory of our own collectors:** read from the code and config, plus measurements from our stored data (50 news runs, 5–11 Oct 2026).
- **Limits and terms of each source:** published documentation and reported experience. Nothing was sent to any external site, because test traffic could itself get us blocked.
- **How reliable each point is:** several official pages (NSE, Yahoo, Google terms, broker docs) could not be opened directly. Points taken from search summaries or community forums are marked *(reported)*. Check those on the live page before building on them.

## 1. What we fetch today

| Run | When | Requests per run |
|---|---|---|
| News run (each market) | Every 4 hours, every day (5 a day, plus 1 more on weekdays) | India about 48 (40 Google News queries, 6 publisher feeds, 2 NSE); US about 41 (37 Google News, 4 feeds). Each run also fetches up to 80 article pages, spaced 1.5 s apart. |
| Daily runs | Before the open and after the close | Yahoo prices and quotes: about 90 (India) and about 220 (US, including option chains). NSE: about 10–90. SEC: about 150 at most 7 a second. One request each for FRED, Treasury, Cboe, FINRA and NSDL. |
| Intraday checks | 2 per session | Yahoo: about 26 (India) and 33 (US) |

**Gap found:** Google News queries and all Yahoo calls have **no spacing between requests**. Everything else already waits between requests and backs off on errors.

## 2. Each source: how often it changes and how often it's safe to fetch

"Safe" means my recommendation. None of these sources publishes an exact blocking threshold, except the SEC.

| Source | How often it changes | Rules and blocking risk | Safe to fetch every |
|---|---|---|---|
| Publisher RSS feeds (ET Markets, Livemint, Business Standard, BusinessLine; US wires PR Newswire, GlobeNewswire, Business Wire) | ET Markets: a new item about every 6 min. The others: 13–40 items a day. | No published limits found. Business Wire's terms forbid storing or aggregating its content *(reported)*. | **5–15 min** (ask "anything new since last time?" so unchanged feeds cost almost nothing) |
| Google News search RSS | Busiest topics: every 4–6 min. A typical company: every 10–25 min. | Google's robots.txt disallows `/rss` (read directly), and Google's terms tie automated access to robots.txt *(reported)*. Only 0.7% of our queries failed so far. | **15 min** for a few market-wide topics, **30–60 min** per company. It's a terms risk at any speed. |
| NSE website (announcements, option chain, quotes) | Website option chain refreshes about every 3 min and lags 3–6 min *(reported)* | NSE's terms prohibit any automated data collection *(reported)*. Cloud servers get blocked *(reported)*. We currently fetch announcements every 4 hours without problems. | Never for option chains. Announcements no faster than 15–30 min, and that still breaks NSE's terms. |
| NSE end-of-day files (bhavcopy) | Once a day | Same NSE terms | Once a day |
| BSE | — | Already refuses our cloud server | Not usable |
| Yahoo Finance (prices) | Real-time or delayed | Unofficial access; Yahoo's terms forbid automated access *(reported)*. "Too many requests" blocks since 2025, some lasting over 24 h *(reported)*. | **No faster than 5 min** for about 25 symbols; 1-minute polling is not advisable |
| SEC filings (US) | Within seconds of filing | Official limit of 10 requests a second, with an identifying user agent (read directly) | Every 1–5 min, safely |
| FRED, Treasury, Cboe, FINRA, NSDL | Once a day | No limits found | Once a day |

## 3. What the F&O tool can and can't get

| F&O need | Free sources? | Realistic route |
|---|---|---|
| Live prices every 1–3 min | No (Yahoo risks blocks and forbids automation; NSE forbids it) | A broker data feed (websocket, prices pushed live) |
| Option chains every 1–3 min | No (Yahoo has no Indian option chains; NSE's website lags and forbids automation) | Broker API: Upstox (free) and Dhan (₹499 a month) have option-chain endpoints; Groww (₹499 a month or ₹4,999 a year) includes Greeks *(reported)* |
| Breaking news every 5–15 min | Yes, from publisher RSS feeds | A small headline watcher during market hours, using conditional requests |
| End-of-day files, flows, macro | Yes, once a day | What market-brief already collects |

**Broker data feeds** *(reported; check the live pages and whether NRI accounts qualify)*:

| Broker | Cost per month | Notes |
|---|---|---|
| Upstox | Free | Live data feed and option chain |
| Angel One | Free | Live data feed |
| Dhan | ₹499 | Live feed; option chain allowed once every 3 s |
| Groww | ₹499 (or ₹4,999 a year) | Live feed, option chain with Greeks |
| Zerodha | ₹500 | Live feed; no ready-made option chain |

## 4. Risks to know

1. **One shared server address.** Every collector uses the same cloud server. If faster F&O polling gets it blocked by Yahoo, Google or NSE, market-brief's daily runs fail too. Keep F&O live data on a separate feed: the broker API.
2. **Terms of use.** NSE's, Yahoo's and Google's terms prohibit automated collection *(reported; Google's robots.txt read directly)*. market-brief already uses them at low frequency, which is a risk you're accepting today. Faster use raises both the chance of a ban and how clearly it breaks those terms.
3. **"Free real-time" is often delayed.** NSE's website option chain lags 3–6 min, and Yahoo says its data is "not for trading".
4. **Redistribution.** A SEBI circular of May 2026 limits how regulated entities share price data *(reported; secondary source)*. Worth checking against the public brief page, which shows prices.

## 5. Recommendations

1. **For the F&O tool:** take live prices and option chains from a broker API (Upstox or Angel One to start for free; Dhan or Groww for ₹499 a month). Don't scrape NSE or Yahoo at 1–3 minutes.
2. **For news:** if the F&O tool needs fresher news, add a light headline watcher on publisher RSS feeds every 5–15 min during market hours. That's a change to market-brief, so it goes through your approval and the judge.
3. **A small safety fix for market-brief's current collectors:** add spacing between Google News queries and between Yahoo calls, and stop a run politely on a "too many requests" answer. It's a code change, so it needs your go-ahead and a judge review.
4. **Your decision:** whether to keep using NSE's website and Google News given their terms, or move more of the news to direct publisher feeds over time.
