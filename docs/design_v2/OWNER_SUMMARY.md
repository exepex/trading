# Design v2 in one page (for the owner)

**What we build.** An honest research tool. Every day at about 15:05 your phone gets one Slack card: today's market
weather (green, amber or red), the tool's forecasts of how much NIFTY will move (with each forecaster's track record),
and either a trade (what, strike, entry range, maximum loss in rupees, exit plan, the devil's advocate's objections,
evidence label) or **"no trade" with the reason**. During market hours a monitor watches open paper trades every 15
minutes and alerts you on danger. Every Saturday a one-page post-mortem shows what was right, what was wrong, and
whether each miss was bad luck (inside the stated odds) or a real error. Every forecast, card and alert is scored
later, forever. Fixes become new versions; nothing is quietly edited.

**Why "movement size" first.** How much NIFTY moves is partly predictable; which way it moves is close to a coin toss.
Option prices are bets on movement, so that is where an edge, if any, would be.

**What the evidence says today (strong evidence).** Two independent tests found no edge in NIFTY option trades held for
days or weeks: the premium exists, but costs (Rs 810-940 a four-leg monthly trade) eat it. And trade profits prove
things slowly: a small edge on monthly trades would take over 100 years of trades to prove. Forecasts are scored every
day, so they settle faster, but not fast: a daily forecast question needs roughly 15 months to 5 years of scoring to
show real skill, depending on how noisy it turns out to be (measured after 60 days). That is still far faster than
trades, which is why forecasts come first and trades second.

**Order of work.**
1. **First release (about 3-6 weeks; depends on ChatGPT's review and your decisions):** trustworthy data (15-minute
   quotes once you choose where they run and Groww's terms allow it, VIX history, global cues: US close, crude,
   rupee), scored forecasts of large moves and of the next session's movement (protocol v4), market weather as a
   scored forecast, the daily card on your phone (at first "no trade"), the budget meter, a weekly post-mortem, and a
   feasibility check of stock options around company results.
2. **Next:** the strategy factory testing ideas forward (each once, cost check first, every idea counted), one- and
   two-leg spreads, risk limits for the Rs 20 lakh account, fills at your reaction time, the real-money pass mark
   written down before any result, loss reviews, drift detection, and the live monitor once there is a paper position
   to watch.
3. **After that:** dashboard screens, intraday exits test, stock-option data if the check passes.
4. **About end of May 2027 (a target): the stop-rule review.** If the data clearly says no forecaster beats the simple
   baselines and no idea survives costs, you choose: stop (keep only cheap data and the weather) or pivot. The most
   likely answer on that date is **"undecided"** (too few days to tell). For that case you chose on 15 Oct, before the
   first v4 forecast is scored: continue to a projected date (at most 2 years away, with AI cut to the forecasters at
   half budget), keep only the free code forecasters, or stop. "Not yet known" is never treated as "no".
5. **The AI books (Hybrid and AI team) start trading** only once there is at least one strategy worth trading
   (proposal; your decision). Until then they keep forecasting, which is already running.

**How paper trades are filled (your reaction time: 5 minutes when available, 30 on average, at most 1 hour).** The
proposal, waiting for your confirmation, is that the headline paper result assumes the worst case, 60 minutes, with
30 and 5 minutes shown beside it. Four rules come with it:
- a paper trade fills only if the price is still inside the card's entry range; otherwise it is recorded as "missed,
  price moved";
- an idea that only works if you react within 15 minutes is flagged and judged at 60 minutes;
- if a card cannot be acted on before the close, the paper fill is the next session at 09:15 plus your reaction time;
- if late fills cost too much, the fix is an earlier decision time (for example 14:00), never assuming you react faster.
**What this means in practice:** the card reaches you at about 15:08 and the market closes at 15:30, so with 60 minutes
every new paper trade fills the next morning, after the overnight gap, and many may be "missed". That is what you would
really get, so the record shows it.

**Rough cost.** Your existing Claude plan (the books' share is measured and capped; proposal: at most half of measured
usage), the existing Azure database, free GitHub Actions and Drive. New cash cost: likely Rs 0-1,000 a month for
hosting the 15-minute jobs (reasoning only), plus whatever Groww charges for API access, if anything. Any new recurring
cost needs your yes. Building: about two builders and the judge, roughly 3-4 months for the first three steps.

**What it can promise.** Honest, scored forecasts with their real track records; a "no trade" when nothing is proven;
your maximum loss in rupees before every trade; results after all costs and 31.2% tax, next to simply holding a NIFTY
index fund; every loss explained; your rules locked before results.

**What it cannot promise.** Profit. Correct daily direction. Proof of a small edge in months. Removing luck (it can only
measure it). Safety from a crash faster than 15 minutes (your protection is the loss cap fixed at entry, not speed).
The most likely honest outcome, given the evidence so far, is a well-measured "no edge found" plus a good risk and
learning aid; a real edge, if found, is likely small and narrow.

**Your decisions (all 12 made on 15 Oct 2026, details in `REPLAN.md` section 5):** the 15-minute jobs run as a
Claude routine; the Rs 20 lakh risk caps; weather thresholds; what "better than baseline" means; your reaction time
(paper fills assume 60 minutes); the monthly AI share; the stop rule and its "undecided" action; the real-money pass
mark and test (exact account size and cap confirmed before it freezes); cards in Google Drive only; AI books trade
only after a strategy passes; S1's changes; E8 frozen with S1. Still to give: your availability calendar.
