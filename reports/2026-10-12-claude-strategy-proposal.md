# Claude's proposal: how I would rebuild the core after the failed backtest

Written 12 Oct 2026, after `reports/2026-10-12-backtest-analysis.md`. **Update after ChatGPT review 1:** several claims here are
downgraded or corrected (SEBI figures, the sellers' edge, sizing); see
`reviews/claude/response_1_2026-10-12-backtest-analysis-and-strategy-proposal.md`. I built the first version and made the mistakes
described there. This is how I would do it differently if I were running a large derivatives book, read with a
statistician's eye. Everything below is a set of **hypotheses to test**, not trades to place. Facts about SEBI
studies and market rules come from `reports/Retail FnO losses and safeguards.md` (sourced); my own reasoning is marked
**Inference**.

## 1. My mistakes, and the lesson from each

| Mistake | Lesson |
|---|---|
| Built a full live desk before proving any rule had an edge | Prove the edge first on real data, then build only what that edge needs |
| Measured rules by "right about the next 30 minutes" | Measure what pays: net rupees per trade of the actual instrument, after costs |
| Added 19 weak rules together and called agreement "evidence" | Many coin-tosses agreeing is still a coin-toss; and testing many rules makes one look good by luck |
| Chose -30% stop, +60% target, 2-day hold, 10-day expiry by judgement | Every number must come from data, tested on a period it was not chosen on |
| Only bought calls and puts | That is the instrument 9 in 10 retail traders lose on; compare instruments, do not assume one |
| Ignored the overnight gap | A stop is not a guaranteed exit; overnight risk must be priced or avoided by design |
| Never compared against a coin toss or "always down" | Every test needs controls; without them a result means nothing |
| Tested one month, one market mood (falling) | A strategy must be tested across rising, falling and sideways periods, calm and volatile |
| Fixed the news scorer phrase by phrase across 8 review rounds | When a component keeps needing patches, question the design, not the next phrase |

## 2. How I would think about it as a portfolio manager

1. **Ask "who pays me, and why?" before anything else.** Every edge needs someone on the other side who loses for a
   reason that persists. In Indian options the biggest, best-documented flow is **retail buyers overpaying for
   options**: about 93% of retail F&O traders only buy options and about 90% of them lose; options are on average
   priced for bigger moves than actually happen (the *volatility risk premium*); prop firms and FPIs take the other
   side. A strategy that copies the retail buyer copies the loser.
2. **Direction is the hardest thing to predict; volatility is easier.** Whether NIFTY is up or down tomorrow is close
   to random. Whether options are expensive or cheap relative to the moves that follow is measurable and has a known
   long-run bias. **Inference:** the core should first ask "is this option cheap or expensive?" and only then "which
   way?".
3. **Think in expectancy, not win rate.** Expectancy = (win rate x average win) - (loss rate x average loss) - costs.
   A 40% win rate is fine if wins are 2.5x losses; a 70% win rate is fatal if one loss wipes out ten wins. The
   backtest had 39% wins and wins equal to losses: a guaranteed loss.
4. **Know the worst case before entering.** Only *defined-risk* positions (the maximum loss is known and capped by
   the structure, e.g. a spread). A stop loss is a wish, not a cap: the backtest's gap stops lost 47%, not 30%.
5. **Trade less, size by risk.** A few good trades a week. Size every trade so its maximum loss is a fixed small share
   of capital, not by premium.
6. **Every setup has a scorecard and a kill rule.** Each strategy is judged on its own record, and is switched off
   automatically when it breaches its limits. No setup is kept because we like it.

## 3. Reading the data differently (statistics)

1. **Controls on every test:** coin-toss direction, always-long, always-short and doing nothing. A strategy is only
   interesting if it beats all of them after costs.
2. **Real prices:** NSE publishes free daily F&O files (bhavcopy) with every option's closing price and open
   interest, going back years. Tests must use those instead of estimated prices, plus a conservative allowance for
   the bid-ask spread (the files have no bid/ask).
3. **Enough history and several moods:** at least 3 years, split by market mood (rising, falling, sideways; low and
   high India VIX). A strategy must not lose badly in any mood and must make money in most.
4. **Out-of-sample discipline:** write the rules down before testing (pre-registration). Tune only on the first part
   of the data (for example 2 years); judge on the last year, which is never looked at while tuning. Then walk forward
   (re-test on each new quarter).
5. **Honest sample size:** votes on consecutive 5-minute bars are not independent, and trades in the same week share
   the same market move. Use block bootstrap (resample whole weeks) for confidence intervals, not textbook formulas.
6. **Multiple-testing penalty:** if we try 20 ideas, about 1 will look significant by luck at the 5% level. Fewer
   ideas, stated in advance; stricter bars when many are tried.
7. **Look at the tails, not the average:** worst trade, worst week, worst losing run, maximum drawdown and the
   gap-day losses. For option selling the tail decides survival.
8. **Pass criteria fixed in advance** (my proposal; to be agreed):
   - Out-of-sample net expectancy per trade above zero, with the 90% bootstrap interval above zero.
   - Profit factor (gross profit / gross loss) of at least 1.3 after costs.
   - Maximum drawdown below 15% of capital; worst month above -6%.
   - At least 100 out-of-sample trades for frequent setups; for slow setups (monthly), at least 30 trades and 3
     years, judged more cautiously.
   - Beats every control.
   - Then 2-3 months of paper trading whose results fall inside the range the backtest predicted. If paper is worse
     than the backtest's bad case, the strategy is rejected, not "adjusted".

## 4. Reading the market differently (F&O structure)

1. **Implied vs realised volatility is the main gauge.** Compare each option's implied volatility with the volatility
   that later happened, and with its own history (IV rank, term structure: near month vs next month, and skew: puts
   vs calls). Expensive options favour selling with protection; cheap options before a known catalyst can favour
   buying.
2. **Events set the price of options.** Results, RBI policy, the Budget, US Fed and CPI dates: implied volatility
   rises before and collapses after. Buying options into an event usually loses to this collapse even when the
   direction is right; selling into it carries gap risk. Every setup needs an event calendar.
3. **Current rules shape the playing field** (from the safeguards report): one weekly index expiry per exchange
   since 20 Nov 2024 (NIFTY weekly; BANKNIFTY and FINNIFTY monthly only), NSE expiry on Tuesday since 1 Sep 2025,
   extra margin on short options on expiry day, premium collected upfront, lot sizes revised about twice a year
   (NIFTY 65, BANKNIFTY 30 from Jan 2026). Strategies must be tested on data from the current rules, or adjusted
   for them.
4. **Overnight gaps follow the world.** GIFT Nifty and the US close set most of India's opening gap. Any position
   held overnight needs a gap budget (the loss if the market opens 1-2% against it).
5. **Positioning is slow information.** FII index-futures positioning (NSE participant OI) and open-interest changes
   say something about the next days or weeks, not the next 30 minutes. Test them on that horizon.
6. **Expiry-day behaviour is not for us.** Expiry days are dominated by large algorithmic players; the Jane Street
   order (allegations, not a final finding) shows how one-way expiry moves can be engineered. Stay out.

## 5. Reading news differently

1. **Value is in surprise, not tone.** "Profit up 20%" is bad news if 30% was expected. Results must be read against
   expectations (consensus or the company's own guidance), not as positive or negative words.
2. **We will never win the speed race.** Algorithms react in milliseconds. A retail desk cannot profit from being
   first; it can profit from (a) not being on the wrong side when news breaks (a guard), (b) slower drifts after
   genuine surprises (days to weeks), and (c) knowing an event is coming and how options price it.
3. **Measure news impact on our own data.** The news reader now stores every story with its type and timestamp. After
   a few months, run an *event study*: what did prices and implied volatility do in the 1, 5 and 20 days after each
   type of story? Keep only the story types that show a measurable, repeatable effect.
4. **Keyword rules are a filter, not a judge.** They decide which stories are worth reading; deciding what a story
   means (surprise, size, credibility) is where an AI analyst later helps, judged by the event study.

## 6. Strategy candidates to test (hypotheses, not recommendations)

All defined-risk, all tested with the same protocol, on real NSE daily data, with controls.

| # | Setup | Plain meaning | Who pays us (hypothesis) | Main risk | Test data |
|---|---|---|---|---|---|
| A | **Index premium selling with protection**: NIFTY iron condor or put/call credit spreads, about 15-20 delta short strikes, wings bought further out, 2-4 weeks to expiry; enter only when IV is high vs recent realised volatility and its own history, and no major event inside the trade; take profit at about 50% of the credit; close at a loss of about 1.5-2x the credit or if the index reaches a short strike; exit 1-2 days before expiry | Get paid for selling expensive insurance, with insurance of our own so the worst case is capped | Option buyers overpaying (volatility risk premium) | Sharp crashes or rallies; gap days; it wins often and loses big when it loses, so the cap and size matter most | NSE F&O bhavcopy, India VIX, event calendar, 3+ years |
| B | **Post-event drift with debit spreads**: after results or a major filing with a large measured surprise and heavy volume, enter the day after (when the volatility collapse is over), a debit spread in the surprise direction, 2-4 weeks | Follow genuine surprises that markets absorb slowly, without paying for event volatility | Slow investors under-reacting | Reversal; few trades | Results dates and surprise measure, stock options bhavcopy |
| C | **Multi-day trend with debit spreads**: index or liquid stock with an established 2-6 week trend (time-series momentum on daily closes), filtered by market mood; debit spread 3-5 weeks out | Ride trends that last weeks, with a cheaper, decay-resistant structure | Momentum is one of the most persistent effects across markets | Choppy markets; whipsaws | Daily prices, bhavcopy |
| D | **Positioning confirmation**: setups B and C only when FII index-futures positioning agrees | Join the side large investors are building | Information in slow, large flows | Data lag; small effect | NSE participant OI history |
| Baseline | Today's intraday call/put buying | Kept only as a control | none expected | known loser | already measured |

**Inference on account size:** with Rs 2-5 lakh, a NIFTY iron condor (one lot each side, wings 200-300 points apart)
needs roughly Rs 40,000-80,000 of margin and risks about Rs 10,000-17,000 at worst. That has to be checked against
Groww's margin calculator and our 2% risk rule; it may only fit the Rs 5 lakh paper account.

## 7. How the system should change

1. **From "rules vote" to "setups".** Each setup (A-D) is one self-contained module: its own entry conditions,
   structure, size, exits, event rules and scorecard. No global vote soup.
2. **An edge lab before any live code:** a historical database (NSE bhavcopy, India VIX, participant OI, event
   calendar), a simulator for multi-leg positions with real prices, margin, charges and a spread allowance, and a
   report with controls, mood splits, bootstrap intervals and the pass criteria above.
3. **A portfolio layer above the setups:** total risk budget, limits per setup and per theme, and a combined
   drawdown brake.
4. **What stays from today:** charges, journal and P&L net of costs; kill switch; guards (ban list, results, stress,
   expiry-day ban, sideways days); news reader as event detector and guard; FII positioning feed; Groww data;
   alerts; paper desk; the judge process.
5. **What goes or is demoted:** chart rules as entry triggers (they may remain as timing within a setup only if a
   test shows they help); the -30%/+60%/2-day exit set (replaced by per-setup exits from testing); single long
   options as the default instrument.
6. **AI comes last, with a narrow job:** reading stories and results for surprise and credibility, explaining trades,
   and reviewing each day's decisions. It never sizes positions or overrides risk rules, and it is scored against the
   event study like any other rule.

## 8. Risk rules I would not break

- Defined-risk structures only; never sell an option without a bought option limiting the loss.
- Maximum loss per position at most 2% of capital; total open risk at most 6%.
- Daily loss -2%, weekly -4%, monthly -6% of capital: stop and review before trading again.
- No new positions on expiry day in the expiring contract; nothing held into the closing auction on expiry day.
- No bought options held over a known event unless the setup is about that event.
- Size by maximum loss, never by premium or margin available.
- Go live only after the backtest passes and 2-3 months of paper trading confirm it; start live at a quarter of the
  paper size.

## 9. Plan (proposed waves 4-6, only after the three-way review agrees)

1. **Wave 4, edge lab data:** download and store compactly 3+ years of NSE F&O bhavcopy, India VIX, participant OI
   and an event calendar; data-quality checks.
2. **Wave 5, edge lab tests:** the multi-leg simulator with real prices; test A, B, C, D and the baseline with the
   pre-registered protocol and controls; publish one report per setup; keep only passes.
3. **Wave 6, paper trading of survivors:** each surviving setup runs on the paper desk with its own scorecard and
   kill rule; monthly review against the backtest's expected range.
4. Then, and only for proven setups, the AI analyst.

## 10. My honest view

- Buying options for short-term direction is very likely a losing game for us; our backtest and SEBI's data agree.
- The most plausible edge for a small account is **patient, small, defined-risk selling of expensive index options**
  (setup A), with strict event and gap rules. Even that edge is thin after costs and has painful losing months.
  Realistic good-case returns are modest (low single-digit percent a month in good periods, with drawdowns), not the
  numbers retail advertising suggests.
- It is possible that **nothing passes** the tests. That would be a successful outcome of the process: we would have
  learned it with paper, not money, and the owner's rule says we stop.
