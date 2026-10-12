# Live news for the F&O desk: analysis and plan (12 Oct 2026)

## The question
Can the stock tool fetch news every 5-10 minutes from free sources, while Marketaux, Finnhub and AskNews are polled
within their limits, so that news reaches the desk as fast as possible from many sources?

## Finding 1: the stock tool cannot be a 5-10 minute fetcher
- Its news runs are Claude Code cloud routines (`routine/NEWS_PROMPT.md`, every 4 hours). Each run starts a full Claude
  session: collect, validate, commit, push. Routines normally run at most hourly, and each run uses Claude allowance.
  288 runs a day is not possible, and even hourly runs cost real allowance.
- Path to the desk: routine start delay + run time + push + the desk's git pull. News would reach the desk tens of
  minutes after publication, slower than fetching it directly.
- It runs in the cloud, where BSE already refuses traffic and Google News queries carry terms risk; polling faster
  there puts the stock tool's own daily research at risk.
- Its value is different: verified, de-duplicated, clustered, scored news. Keep it for that.

## Finding 2: what each source really allows (pricing and docs read 12 Oct 2026)
| Source | Plan | Limit | Realistic use during market hours (09:00-15:30) | Speed |
|---|---|---|---|---|
| Finnhub | Free, personal use | 60 calls/minute | world market headlines every minute | "real-time"; US company news only |
| Marketaux | Free | 100 calls/day, 3 articles per call | India market news every 5 min (78 calls) | "instant"; 3 articles per call misses busy minutes |
| Marketaux | Basic $29/month | 2,500/day, 20 articles | India + world every minute | as above |
| AskNews | Pay as you go | 25 credits once + $5 starter wallet (~225 searches), then $0.025/search; 1 request per 2 s | trial only | index "up to the last 5 minutes" |
| AskNews | Pro $7.99/month | 500 + 100 bonus credits/month (1 credit per search) | one world-events search every 15 min | as above; non-commercial licence (fine for us) |
| Publisher RSS (ET Markets, Livemint, Business Standard, BusinessLine, Moneycontrol) | free | no published limit | each feed every 2-3 min with "anything new since?" requests (an unchanged feed answers with a tiny "no change") | as soon as the outlet publishes |
| NSE corporate announcements RSS | free | NSE terms discourage automation | every 5 min, from the home PC only | the original filing: usually the first source for a single stock |

## Finding 3: how fast is fast enough
Prices move within seconds of news; machines trade it before any person or aggregator can. For a 1-2 day option buyer,
news is not a race to win. It is used to:
1. avoid trading into news the market has not finished digesting (results, orders, SEBI action, war, oil spike);
2. exit an open trade when news turns against it;
3. confirm that a price/OI move has a real reason (trades with a catalyst behind them hold better).
For these, 1-5 minutes is enough. Price, volume and option OI, which the desk already reads every scan, are the
fastest signal; news explains them.

## Plan
1. **Fast news watcher in this repo, on the home PC** (plain Python, no Claude cost per poll; home IP, separate from
   the stock tool): Finnhub every 1 min, Marketaux every 5 min, AskNews every 15 min, publisher RSS every 2-3 min,
   NSE announcements every 5 min. Each source sits behind one `NewsSource` interface with its own request budget.
2. **One story, many sources**: items are matched across sources (same stock + similar headline), and the watcher
   records which source saw each story first and how many minutes later the others did. After two weeks this table
   says which sources earn their place and whether paying more would make the desk faster.
3. **Claude only on what matters**: a story on a shortlisted stock, an open trade, an index or a world-risk theme goes
   to the AI analyst; the rest is stored. Polling itself costs no Claude usage.
4. **Stock tool unchanged in role**: still the verified research layer. Optional, owner's call in that tool: news
   runs hourly during Indian market hours instead of every 4 hours.
5. **Spend only on evidence**: start at $0 (all free plans). Candidates later: Marketaux Basic $29 if the free plan's
   3 articles per call is the bottleneck; AskNews Pro $7.99 if its world coverage arrives first. Ceiling about
   Rs 3,200/month for both.

Keys go in `~/.trading.env` on the PC only: `FINNHUB_API_KEY`, `MARKETAUX_API_TOKEN`, `ASKNEWS_API_KEY`.
