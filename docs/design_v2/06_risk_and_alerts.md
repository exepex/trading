# 6. Risk and alerts

## 6.1 The account and the fixed rules

- **Paper account Rs 20 lakh; maximum loss Rs 10,000 per trade, charges included** (owner, 14 Oct). More strategies in
  parallel, not bigger bets.
- **Worst loss fixed at entry**: bought options or spreads with bought protection; never unprotected selling; no
  stop-loss order relied on (owner decision of 14 Oct 2026, "Trading principles for the research tool"). So the account's worst case on any day is the sum of the open positions'
  maximum losses, whatever the gap.
- **Stressed margin multiplier 1.45** (decided 14 Oct) on NSE SPAN plus exposure from A14; funds at entry by C2's rule
  (no credit for sold premium; bought premium and charges paid at once).
- **Strategy pauses (decided):** a single trade's loss reaching the plan's catastrophic loss, or a strategy's cumulative
  realised loss reaching Rs 30,000; an owner re-approval restarts the count.

## 6.2 Many strategies, one market: risk buckets (proposal; owner decides the numbers)

With Rs 20 lakh, about 15-20 protected NIFTY structures could be funded at once (a condor needs about Rs 1 lakh of funds
at entry, response 92). They would all lose in the same crash. So limits apply to **correlated groups**, not only to
trades.

| Limit | Proposal | Reason (reasoning only) |
|---|---|---|
| Risk bucket | Positions sharing an underlying group (NIFTY, BANKNIFTY, one stock, or "stock results this week") and a side of exposure (short volatility, long volatility, bullish, bearish) | One crash or one squeeze hits the whole bucket |
| Bucket cap | Sum of maximum losses at most Rs 30,000 (3 trades' worth) | The owner's original 3-trade limit, applied to each correlated group |
| Account cap | Sum of maximum losses of all open positions at most Rs 1,50,000 (7.5%) | Worst day stays survivable even if every bucket fails together |
| New risk per day | At most Rs 50,000 of new maximum loss a session | Limits a single day's decisions, often made on one weather reading |
| Drawdown brake | Closed equity Rs 1,20,000 (6%) below its high: no new trades until the owner restarts in writing | Same 6% as the owner's Rs 30,000 on Rs 5 lakh (12 Oct); open trades run to their own exits |
| Weather | RED: no new trades (owner, 14 Oct 2026, "Trading principles") | Survival rule; its price is reported (section 2.3) |

**Daily stress line.** Every card shows, for all open positions, the loss under fixed scenarios: NIFTY -5% and -10%
overnight with VIX +50% and +100%, and +5%. Because all positions are defined-risk, the -10% line can never exceed the
sum of maximum losses; it shows how close the book is to it.

**Effective sample (the honest catch).** Buckets limit loss; they also show the owner how many **independent** bets the
book really holds. The scoreboard reports, next to the trade count, the count of distinct buckets-and-weeks, which is
the number that matters for evidence (section 1.3).

## 6.3 Gap and event risk

- Holding overnight and over weekends is allowed (12 Oct); the bought protection caps the gap loss.
- Scheduled events (Budget, RBI policy, election results, a stock's results) are on the events calendar (A6, A12); a
  strategy declares whether it may hold through them. Default: not through an event it was not designed for.
- Physical settlement: stock options settle by delivery. C4 refuses a stock option position whose exit plan does not
  close it before the expiry session.

## 6.4 Real-money risk (later; see `08_budget_and_stop_rules.md`)

On a real account of about Rs 2 lakh, Rs 10,000 is 5% a trade: too high (owner decision of 12 Oct 2026, "Paper account: Rs 5 lakh"). The real-money test sets
its own per-trade cap before it starts (proposal: Rs 4,000-5,000, 2-2.5% of the real account; owner decides).

## 6.5 Alerts: classes, content and limits

All F&O alerts go to Slack #fno-desk (`C0C89E8QCCD`) with `FNO_SLACK_BOT_TOKEN`; infrastructure and database alerts stay
in #db-alerts (owner decision of 13 Oct 2026, "Database-check alerts go to Slack #db-alerts"). The first line of every alert says what to do, or "information, no action".

| Class | Triggers | Timing |
|---|---|---|
| CARD | The daily trade card, including `NO TRADE` | by 15:08 IST each session |
| DANGER | Weather upgraded to RED; a position's loss at 80% of its maximum; NIFTY 1.5% from the previous close; VIX up 10% in the session; a short strike touched; an exit rule hit (and, in `intraday_exits` mode, the paper exit) | within one snapshot (15 minutes) plus sending |
| WARNING | Loss at 50% of maximum; AMBER upgrade; quotes stale 30 minutes; monitor silent | same |
| SYSTEM | A job failed; budget at 80% or 100%; a stop-rule date reached; a calendar gap | when found |

Limits: one alert per condition per position per hour; after 10 DANGER alerts in a session, one summary every 30
minutes. Each alert is a record (condition, snapshot time, sent time), so latency and misses are measured (layer 7).

**What the alerts cannot do.** A 15-minute check cannot catch a crash inside 15 minutes, and the owner cannot act faster
than their reaction time. Because every position's loss is capped at entry, a late alert costs at most that cap; this
is why defined risk, not speed, is the protection (reasoning only, consistent with the owner's "speed is not the goal").

## 6.6 Where the 15-minute recorder and the monitor run (owner decides)

GitHub Actions ran hours late here (response 91), and no broker key may go into GitHub (owner decision of 13 Oct 2026 on the 3 pm recorder, option a). Options:

| Option | How | For | Against |
|---|---|---|---|
| (a) Claude routine every 15 minutes | Same place as today's 3 pm Groww recorder | No new host; key handling already exists there | About 26 AI sessions a session-day on the subscription for a job with no reasoning; routines are a research preview |
| (b) Azure Functions timer | The owner's existing Azure; key in Azure Key Vault | Reliable schedule; cost likely inside the free monthly grant (about 600 runs a month; reasoning only) | A key that can trade sits in a cloud function: needs locked access, alerts on use, and Groww's key scope checked |
| (c) Owner's own always-on computer | A small script | Key stays at home | Depends on the owner's machine and internet |
| (d) NSE public quotes, no key | Scrape NSE's site | No broker key at all | NSE often blocks cloud addresses; fragile; terms of use unclear |

**Recommendation (reasoning only):** (b), if Groww offers a data-only key or the owner accepts the key risk with the
controls named; otherwise (a) for the first months, measured for cost by F8. This is the owner's decision because it
places a broker key.
