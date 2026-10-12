# Why the chart-rule strategy lost money: analysis of the 30-day backtest

Prepared 12 Oct 2026 for an independent review (the owner, Claude and ChatGPT). It states what was tested, what
happened, what the control tests show, what we got wrong in the process, and what we do not know yet. The raw numbers
are in `reports/2026-10-12-backtest-analysis-data.json`.

**To the reviewer:** this is a three-way solution design between the owner, Claude and you. Please (1) read this
report, (2) answer sections 9 and 10 **on your own first**, then (3) read Claude's proposal
(`reports/2026-10-12-claude-strategy-proposal.md`, shared with this report) and answer section 11. We are not only
asking you to check the analysis: we want your own solution, so the three of us can agree on a strong core before
anything more is built.

## 1. Background

- **Who:** a retail investor in India (broker: Groww) building a research and paper-trading tool for NSE futures and
  options. No real orders. Real money only if paper trading shows a net profit after all charges; otherwise the tool
  is shut down.
- **Capital and size:** paper account Rs 5 lakh at 2% risk per trade; planned live account Rs 2 lakh. Trades are
  about Rs 10,000-11,000 of option premium (up to Rs 25,000 on strong evidence).
- **What the desk does:** during market hours it scores each F&O stock or index with about 19 rules, and when enough
  rules agree it **buys a call (bet on up) or a put (bet on down)** about 10 days from expiry, near 0.55 delta.
- **Exits:** stop loss at -30% of the premium, target at +60%, a trailing stop (after +30%, exit if half the best gain
  is lost), at most 2 trading days of holding, and an exit one day before expiry.
- **Daily limits on the real desk (not in this test):** stop after a Rs 6,000 loss or 3 losses in a row; a cap on open
  trades; at most 2 bets on the same theme.

## 2. What was tested

- **Question:** do the price-chart rules alone predict direction well enough to make money buying options?
- **Rules in the test (chart only):** opening-range breakout, price vs VWAP (the day's average traded price), short vs
  long moving-average trend, strength vs NIFTY, position vs the previous day's high/low, volume confirmation. Plus one
  filter: no trades on flat, sideways days.
- **Rules not in the test** (no past data to replay): news, futures open-interest build-up, option-chain writing
  pressure, foreign-investor (FII) positioning, research scores, implied-volatility rank, market breadth.
- **Data:** Yahoo 5-minute prices, **27 Aug to 12 Oct 2026** (30 trading sessions; the first sessions serve as
  history), for NIFTY, BANKNIFTY, FINNIFTY, RELIANCE, HDFCBANK, ICICIBANK, INFY, TCS and SBIN.
- **How a trade is simulated:** the rules are evaluated after every 5-minute bar using only data up to that bar (no
  look-ahead, checked by a test). On a signal, one lot of the at-the-money option is "bought". Its price is
  **estimated** with the Black-Scholes formula: volatility = the stock's own recent 5-minute volatility x 1.1, at
  least 8%, 10 days to expiry. The estimated option is re-priced every bar until an exit fires. All Groww charges are
  deducted (brokerage, STT, exchange, SEBI, stamp duty, GST).
- **Pauses:** no new trade on a name within 30 minutes of an exit (45 minutes after a loss).
- **Each name is simulated separately**, as if 9 traders worked side by side with no shared daily limits.

## 3. Results

| Measure | Value |
|---|---|
| Trades | 211 (8 more were still open when the data ended; not counted) |
| Net result after charges | **-Rs 1,90,017** |
| Before charges | -Rs 1,74,667 |
| Charges | Rs 15,350 (about Rs 73 per trade; 8% of the loss) |
| Premium per trade (median) | Rs 10,848 (range Rs 4,114 - 23,141) |
| Average result per trade | -Rs 900 |
| Won / lost | 82 won (38.9%), 129 lost (61.1%) |
| Average win / average loss | +Rs 3,646 / -Rs 3,791 |
| Win rate needed to break even with these win and loss sizes | about 51% |
| Largest win / largest loss | +Rs 12,343 / -Rs 12,186 |

### 3.1 How trades ended

| Exit | Trades | Net | Average move of the premium | Average hold |
|---|---|---|---|---|
| Stop loss | 107 | -Rs 4,50,145 | -36.5% | 27.7 h |
| Target (+60%) | 29 | +Rs 1,95,476 | +71.3% | 27.8 h |
| Trailing stop | 38 | +Rs 58,461 | +14.1% | 17.8 h |
| Holding limit (2 days) | 37 | +Rs 6,191 | +3.2% | 33.2 h |

- Half of all trades (107 of 211) hit the stop loss.
- Only 29 of the 82 winners reached the +60% target. The rest were small wins (trailing stop or time limit). That is
  why the average win (Rs 3,646) is no bigger than the average loss (Rs 3,791), even though the target (+60%) is
  twice the stop (-30%).

### 3.2 Overnight gaps

- 27 stop losses happened at the open, after an overnight price gap: they averaged **-47.1%** (not -30%) and cost
  **-Rs 1,39,991**, 74% of the total loss.
- The other 80 stop losses averaged -32.9%.

### 3.3 Direction and market trend

The market fell over the whole period:

| Name | Change over the period |
|---|---|
| NIFTY | -7.3% |
| BANKNIFTY | -4.5% |
| FINNIFTY | -5.4% |
| RELIANCE | -9.9% |
| HDFCBANK | -0.6% |
| ICICIBANK | -6.6% |
| INFY | -10.0% |
| TCS | -5.4% |
| SBIN | -10.1% |

| Direction of the bet | Trades | Net | Win rate |
|---|---|---|---|
| Bullish (bought calls) | 95 | **-Rs 2,23,131** | 22% |
| Bearish (bought puts) | 116 | +Rs 33,114 | 53% |

The rules kept buying calls in a falling market (45% of all trades), and almost all of the loss came from those bets.

### 3.4 By name and by time of day

| Name | Trades | Net | Win rate |
|---|---|---|---|
| BANKNIFTY | 22 | -Rs 75,192 | 23% |
| TCS | 23 | -Rs 59,665 | 22% |
| SBIN | 27 | -Rs 29,905 | 37% |
| INFY | 21 | -Rs 27,451 | 38% |
| FINNIFTY | 22 | -Rs 19,402 | 41% |
| ICICIBANK | 26 | -Rs 207 | 46% |
| RELIANCE | 25 | +Rs 5,119 | 52% |
| NIFTY | 23 | +Rs 6,432 | 48% |
| HDFCBANK | 22 | +Rs 10,254 | 41% |

| Entry time | Trades | Net | Win rate |
|---|---|---|---|
| 09:30-11:00 | 104 | -Rs 73,056 | 42% |
| 11:00-13:00 | 63 | -Rs 70,619 | 37% |
| 13:00-14:45 | 44 | -Rs 46,342 | 34% |

| Holding | Trades | Net | Win rate |
|---|---|---|---|
| Closed the same day | 67 | -Rs 85,970 | 34% |
| Held overnight | 144 | -Rs 1,04,047 | 41% |

### 3.5 How often each rule called the next 30 minutes correctly

| Rule | Times it voted | Right |
|---|---|---|
| previous_day_levels | 11,076 | 51.5% |
| relative_strength | 10,257 | 50.3% |
| opening_range | 9,315 | 53.6% |
| vwap | 8,255 | 54.1% |
| intraday_trend | 6,194 | 52.3% |
| volume_confirmation | 3,193 | 50.3% |

50% is a coin toss. VWAP and opening range are slightly above it, but votes on consecutive bars overlap heavily, so
the true sample is much smaller than the counts suggest, and a 30-minute lean does not carry over a 1-2 day hold.

## 4. Control tests (same entry moments, same exits, same charges; only the direction changes)

These replay each of the 211 trades from the exact same moment with the same option model and exits. The first line
checks the replay: it reproduces the real result exactly.

| Direction chosen by | Net | Win rate |
|---|---|---|
| The rules (check: identical to the real run) | -Rs 1,90,017 | 39% |
| A coin toss (30 runs) | median **-Rs 65,268** (best +Rs 55,185, worst -Rs 2,08,653) | about 50% |
| The opposite of the rules | +Rs 45,352 | 50% |
| Always bullish | -Rs 2,94,258 | 32% |
| Always bearish | +Rs 1,49,594 | 57% |

**Diagnostic (not a proposal):** the same entries and directions, but every trade closed by 15:15 the same day (stop
and target kept): -Rs 30,116, win rate 47%. This only shows how much the overnight gaps cost in this period; choosing
a rule because it looked good on these same 30 days would be overfitting.

What the controls say:

1. **The rules did worse than a coin toss.** A random direction lost about Rs 65,000 at the median; the rules lost
   Rs 1,90,000.
2. **The structure loses even with a coin toss.** With random direction the trades lose about Rs 300 each on average:
   the cost of the trade (time decay of the option, charges) plus exits that cut losses later than planned
   (overnight gaps) outweigh the payoff.
3. **The market's direction decided the outcome.** In a falling market, always betting down made +Rs 1.5 lakh and
   always betting up lost Rs 2.9 lakh. The rules leaned the wrong way (they bought calls on rebounds in a downtrend).
4. **Overnight gaps were the largest single cost:** Rs 1.4 lakh of the Rs 1.9 lakh loss.

## 5. Option costs in numbers

- An at-the-money option with 10 days left at 15% volatility loses about **5.5% of its value per day** from time
  decay alone, if the price does not move. Over a 2-day hold that is about 11% before any move is made.
- Charges are about Rs 73 per round trip (0.7% of a Rs 10,800 premium). Charges were not the main problem.
- Option buyers also usually pay implied volatility above the volatility that then happens; the model assumes 10%
  above. Real quotes may differ either way.

## 6. Limits of this test (what could make the numbers wrong)

1. **Estimated option prices, not real quotes.** Volatility is constant during a trade (no implied-volatility drop
   after events, no skew between calls and puts). No bid-ask spread beyond charges.
2. **One period, one market mood.** 30 sessions in which every name fell. A rising or sideways month could give very
   different numbers. 211 trades is a small sample.
3. **Not the real desk.** No daily loss limit, no cap on open trades, no shortlist or contract picker, no check that
   the needed move is realistic. The real desk would have taken far fewer trades.
4. **Only chart rules.** News, positioning, option-chain and research rules could not be replayed.
5. **Yahoo data.** Free 5-minute data; holidays not known (a holiday counts as a holding day).

## 7. What we did wrong in the process

1. **Built before proving.** We built a full live desk (19 rules, guards, news reader, alerts) before testing whether
   any rule had an edge. The backtest came last; it should have come first.
2. **Settings without evidence.** The -30% stop, +60% target, 2-day hold and 10-day expiry were reasonable-sounding
   choices, not tested ones. The calibration on 12 Oct showed the +60% target needs 1.2-1.5x the move the market
   expects in the holding time.
3. **Many weak rules added together.** Adding rules that are each close to a coin toss does not make a good signal;
   it makes more trades.
4. **Patching instead of redesigning.** Several review rounds fixed the news headline scorer one phrase at a time (8
   rounds on rupee and dollar wording) instead of asking whether keyword rules are the right tool at all. The owner
   called this out, rightly.
5. **One instrument only.** The desk only buys calls and puts, the instrument retail traders lose on most often
   (SEBI's FY22-FY24 studies: about 9 in 10 individual F&O traders lost money).
6. **Change already made (12 Oct):** chart rules alone can no longer open a trade on the desk; at least one other kind
   of rule (news, positioning, option chain, research, market backdrop) must agree.

## 8. What we do not know yet

- Whether news, FII positioning, open-interest or option-chain rules add an edge (no past data replayed yet).
- How the same rules do in a rising or sideways market.
- How real option prices (real implied volatility, real spreads) change the result.
- Whether a different instrument (spreads, defined-risk option selling) or a longer holding horizon has an edge.

## 9. Questions for the reviewers

1. Is the analysis sound? Is anything misread, or is any conclusion stronger than the evidence?
2. Which edges are realistic for a retail account of Rs 2-5 lakh trading NSE options, with Groww charges and no
   co-location, and which should we not even try?
3. Should the core be built around **direction** (buying calls/puts or debit spreads) or around **volatility**
   (defined-risk option selling when options are expensive, e.g. iron condors or credit spreads on NIFTY/BANKNIFTY)?
4. What holding horizon fits a retail edge: intraday, 1-2 days, or 1-3 weeks?
5. What test design avoids fooling ourselves: how many years of data, which out-of-sample split, how many trades
   before a strategy is trusted, and which statistics to require (expectancy, profit factor, worst losing run,
   drawdown)?
6. NSE publishes free daily F&O files (closing price, open interest for every option). Is daily data enough to test
   the candidate strategies, or is intraday option data essential?
7. How should the system decide when *not* to trade (market mood, volatility level, events)?
8. What risk rules should be non-negotiable (size per trade, daily and monthly loss limits, overnight and event
   exposure, expiry-day rules)?

## 10. Your recommendation: how would you trade this?

Imagine you are, at once, a portfolio manager running thousands of crores, an F&O trader with years of real results on
NSE index and stock options, a statistician and a mathematician. You have been handed this account (Rs 2-5 lakh, Groww, no co-location, research and
paper trading first, real money only after proven net profit). Please answer as that person, plainly and honestly:

1. **Your diagnosis in one paragraph:** what is the real reason this lost money?
2. **What you would do:** the strategy or strategies you would actually run, with exact rules: instrument (option
   buying, debit spreads, credit spreads, iron condors, futures, or none), underlyings, entry conditions, strike and
   expiry choice, position size, stop, target or exit logic, holding time, and when you would stay out.
3. **Why you expect an edge:** the market reason it should work (who is on the other side and why they lose), and the
   evidence you know of. Say clearly where you are unsure.
4. **What you would never do** with an account this size, and why.
5. **Risk rules** you would not break: per trade, per day, per month, overnight, around events and on expiry day.
6. **How you would prove it before risking money:** data needed, test design, out-of-sample split, minimum number of
   trades, and the exact numbers that must be met (for example net expectancy per trade, profit factor, worst
   drawdown, worst losing run) before going live, and the numbers at which you would stop.
7. **What to keep from the current system** (news reader, FII positioning, guards, exits, scoring) and what to throw
   away.
8. **Where AI helps and where it does not:** which decisions should stay rule-based and which an AI analyst could
   improve.
9. **As a statistician and mathematician:** how would you read this data differently? Which measures, controls,
   sample sizes, significance tests and checks against overfitting would you insist on? What in our numbers would
   you not trust?
10. **As an F&O expert reading the market:** what would you watch that we do not (implied vs realised volatility,
    skew, term structure, open interest, FII positioning, expiry effects, gaps, events), and how exactly would each
    feed a decision?
11. **Reading news:** how should news be used by a retail desk that can never be fastest (as a trigger, a guard, an
    event calendar, a surprise measure)? How would you test whether it adds anything?
12. **Your honest view:** if you think a retail account like this should not trade options at all, or only one narrow
    setup, say so and explain.

Please be blunt; give numbers where you can; mark assumptions and uncertainty; no guarantees of profit. A short
summary table of your recommended setup(s) at the end would help us compare your answer with Claude's.


## 11. After your own answer: critique Claude's proposal

Claude built the first version and has written how it would redo it (`reports/2026-10-12-claude-strategy-proposal.md`).
After answering section 10 on your own, please:

1. Say where you **agree**, where you **disagree** and why, point by point.
2. Point out anything **wrong, missing or naive** (market facts, statistics, risk, costs, margin, Indian rules).
3. Rank Claude's strategy candidates (A-D) and yours together, by likelihood of a real net edge for this account.
4. Propose the **combined plan** you would sign off on: what to build first, what to test, the pass and stop
   criteria, and what to leave out.
