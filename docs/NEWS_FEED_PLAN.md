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

## Speed plan (12 Oct 2026, after "if news is not faster, what is the point")

News travels: event -> company files with NSE/BSE, or a journalist writes it -> aggregators index it -> we fetch it.
Each step adds delay, so speed comes from (a) reading as close to the origin as possible, (b) being pushed rather than
polling, and (c) not waiting for words at all when the price itself shows something happened.

| Layer | Source | Delivery | Expected delay | Cost |
|---|---|---|---|---|
| 0. Price shock | Groww live feed: up to 1,000 instruments at once (all F&O stocks, indices, our option contracts) | push (WebSocket) | seconds | already paid |
| 1. Origin: filings | NSE and BSE corporate announcements | poll every 30-60 s from the home PC (NSE's terms discourage automation); licensed push alternative: Drishti WebSocket, Rs 2,000/month, 100 symbols | under 1-2 min after the exchange posts | free / Rs 2,000 |
| 2. Push: Telegram | official channels of business media and exchanges, where they exist (to be verified), read with Telegram's official API | push | seconds after the channel posts | free |
| 3. Publishers | RSS of ET Markets, Livemint, Business Standard, BusinessLine, Moneycontrol, CNBC | poll every 60 s, "anything new since?" requests | 1-2 min after publishing | free |
| 4. Aggregators | Finnhub (1 min), Marketaux (5 min), AskNews (15 min) | poll | 2-15 min | free plans |

Not used: X (Twitter), where news often breaks first: its API is expensive and AskNews only searches it from the
$250/month plan. Finnhub's news WebSocket is premium only.

How the layers work together: a price shock (layer 0) protects open trades at once under the existing rules (the AI
may exit early, never add) and triggers an immediate search of layers 1-4 for that symbol to find the reason. Every
story is stamped with the time each source delivered it and compared with the price shock, so after two weeks the desk
knows which sources were early, which were late, and whether a paid source would have helped.

Honest limit: machines trade on news within milliseconds, and no retail source beats them. The aim is never to be the
last to know: protect within seconds, understand within a minute or two, and trade the follow-through once the news is
known, not the first spike.

Build order: (1) Groww live feed and shock detector; (2) NSE/BSE announcements; (3) publisher RSS and aggregators,
with the source-speed table; (4) Telegram, once the channels are verified.

## Built (12 Oct 2026): sequential free-source watcher

Owner's direction: free tiers only; one or two minutes late is fine; never bombard a source; one request at a time.
- `fno/live/news/`: `NewsSource` interface; RSS feeds (conditional requests, own cache time as a floor), NSE and BSE
  filings, Finnhub, Marketaux and AskNews (only when keyed); `PollSchedule` (sequential, 5 s apart, staggered,
  doubling back-off on failure, daily allowances, 5x slower off hours); `StoryBook` (one story per news item across
  sources: same link or similar headline); `SymbolTagger` (company names from NSE's NIFTY 500 list, index words,
  WORLD theme); `NewsWatcher` (runs in a thread beside the desk; first answer after a start and items older than
  3 hours are background, never reported).
- Events `news_story` and `news_sighting` (with the delay behind the first source) in the desk's daily results.
- Checked from the cloud on 12 Oct: every feed and NSE filings answered; BSE refuses cloud servers (to be checked
  from the owner's PC). About 7 requests a minute in total across 13 sources during market hours.
- Next: a price-shock detector on the Groww live feed; the trade analyst and position guardian read `recent()` stories.

## Market hours only, storage, duplicates and credibility (12 Oct 2026)

- **When**: trading days only (NSE holiday list), 08:45-15:45 IST. Nothing is fetched outside these hours; at the
  next opening the sources start again, staggered.
- **What is kept**: only stories about an F&O underlying (219 today) or an index, or world-risk news (war, oil,
  central banks, tariffs, global markets). Everything else stays in memory for a day so its copies are recognised,
  and is never written.
- **Where**: `data/live/news/YYYY/MM/YYYY-MM-DD.jsonl`, one file a day, committed once a day with the desk's
  results. Each story once (title, link, time, tags, credibility, 300-character summary, never full text), plus one
  short line per confirmation by another outlet.
- **How big**: measured 12 Oct: one round of all sources gave 544 headlines, 236 worth keeping, 680 bytes each.
  Expect a few hundred stories a day: about 0.2-0.3 MB a day, 60-80 MB a year as text; git stores files compressed,
  so the repository grows roughly 15-20 MB a year. If it ever matters, older months can move to a yearly archive
  file or MotherDuck without changing the desk (same `ResultsStore` interface).
- **Duplicates vs confirmations**: the same outlet repeating or rewording a story (including its second feed, e.g.
  Business Standard Markets and Companies) is a duplicate and ignored. A different outlet carrying it is a
  confirmation. Same news is recognised by the same link, or the same company plus shared words or the same figures
  (e.g. "Rs 20,000 crore"), or for market-wide news most words in common. Different companies never merge.
- **Credibility**: exchange filing (NSE/BSE: the source itself) > widely reported (3+ outlets) > corroborated (2) >
  single source. The AI analyst treats single-source news with care and can judge doubtful merges itself.
- Known limit: name tagging is by rules, so it can mis-tag (e.g. "Canara HSBC Life" also matching Canara Bank). The
  AI analyst reads the story before acting; tags only decide what is stored and shown to it.
