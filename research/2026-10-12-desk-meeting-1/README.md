# Desk meeting 1: what the 2024-2026 NIFTY data says (12 Oct 2026)

The team: each expert role reads the same data and reasons from its own job. Not a check of old strategies: a search
for where money is actually made.

**Data:** real NSE daily files, 1 Jan 2024 to 9 Oct 2026 (689 trading days): NIFTY level and closing prices of NIFTY
options 20-55 days from expiry. 33 monthly expiry cycles. Real Groww charges, Rs 1 worse fill on every leg and order,
current lot of 65. A monthly expiry is one listed that day and listed more than 50 days ahead (`expiries.monthly_as_of`).
Entry on the first close a monthly expiry is 30-45 days away; exit at the last close with 21 or more
days left (about 2-3 weeks). Re-run: `python research/2026-10-12-desk-meeting-1/desk.py` and `variants.py`.

## 1. Each role's reading

### Quant / statistician: is there a trend to follow?
- NIFTY moved +3.6% in 2.75 years; volatility 13.5% a year; worst day -6.1%, best +3.8%; 19 days moved more than 2%.
- Does the last 5, 10 or 20 days' move continue? **No**: same direction 50%, 51%, 52% of the time (coin toss);
  correlation -0.20, -0.10, -0.04 (if anything, a slight reversal over 5 days).
- **Reading:** in this period, guessing NIFTY's direction from its own past is worthless. (Strong evidence for this
  period; 33-136 non-overlapping samples.)

### Options strategist: are options fairly priced?
- Implied volatility of 30-45-day at-the-money options averaged **13.8%**; the volatility that then happened until
  exit averaged **12.2%** (all movement counted, trends included; 11.9% in the first run, which subtracted the
  average daily move). Options were priced above what followed in **73%** of the 33 cycles.
- **Reading:** option buyers paid for moves that mostly did not come. This is the volatility risk premium; it is the
  economic reason premium sellers are paid (they carry crash risk). (Some evidence: one period, 33 cycles.)

### F&O trader: what did real trades make, after all costs?

Per cycle, one lot, 33 cycles (settlement price used for the rare option that did not trade that day):

| Trade | Months tradable | Net | Win rate | Worst trade |
|---|---|---|---|---|
| Sell the at-the-money straddle (call + put), unprotected | 33/33 | **+Rs 2,87,463** | 79% | **-Rs 41,030** (Feb 2026, NIFTY -5.7%) |
| Buy the same straddle | 32/33 | -Rs 3,24,905 | 19% | -Rs 31,181 |
| Iron condor: sell at the money, buy protection 500 away | 30/33 | +Rs 33,960 | 63% | -Rs 6,020 |
| Iron condor: sell 2% away, protection 500 further | 19/33 | +Rs 69,026 | 89% | -Rs 4,929 |
| Iron condor: sell 2% away, protection 300 further | 24/33 | +Rs 29,747 | 79% | -Rs 9,387 |
| Iron condor: sell 3% away, protection 300 further | 18/33 | +Rs 24,757 | 83% | -Rs 8,883 |
| Bull call spread (100 wide) | 31/33 | -Rs 27,541 | 39% | -Rs 4,053 |
| Bear put spread (100 wide) | 33/33 | -Rs 5,304 | 48% | -Rs 3,252 |
| Trend-following spread (bull above 20-day average, bear below) | 30/33 | -Rs 15,280 | 47% | -Rs 3,641 |

- **Reading:** the money was in **selling** option premium, not in betting on direction. Every protected-selling
  variant made money; every directional spread lost.

### Risk manager: can the account survive it?
- The unprotected straddle's worst month was -Rs 41,030: **20% of a Rs 2 lakh account in one trade**, and it needs
  margin well above Rs 2 lakh. **Rejected as is.**
- Iron condors cap the loss. Their maximum possible loss per lot is roughly Rs 9,000-16,000 (2% short strikes), i.e.
  4.5-8% of Rs 2 lakh: above any sensible per-trade limit for that account. They fit a Rs 5 lakh account at 2-3%.
- **Reading:** the edge found needs either more capital or smaller exposure per trade (fewer contracts are not
  possible: one lot is the minimum). Capital and risk per trade are now the owner's key decision.

### Statistician (again): how much should we believe it?
- 33 cycles is small; one period (2024-26) with one big shock (June 2024 election) and one (Feb 2026). The protected
  variants have only 10-30 tradable months each, because the saved extract lacks some far strikes: a **data gap, not a
  market result**; the full raw files (going to Google Drive) close it.
- Selling premium wins often and loses big: averages hide the tail. Judge it on the worst months and drawdown, not
  the win rate.
- **Reading:** promising and consistent with the economics, **not yet proven**. Needs: every month (full chain),
  longer history (2019-2023 from NSE's older files), and walk-forward testing.

### Portfolio manager: where do we go?
1. **Drop directional guessing** as the core: no evidence in either test (the 30-day intraday backtest and this one).
2. **Make protected premium selling the lead hypothesis**: sell overpriced options, always with bought protection,
   size by maximum loss.
3. **Make it smarter before trusting it** (next work, each owned by a role):
   - Options strategist: sell only when implied volatility is clearly above recent realised volatility (the 27% of
     months where it was not are the danger months).
   - Macro / event analyst: skip cycles with a known shock inside (election results, Budget, RBI policy).
   - Risk manager: close early at a fixed share of the maximum loss; never hold into the last week.
   - Quant: use the slight 5-day reversal to choose the side (more call or more put spread), as a test, not a belief.
4. **Decide capital and risk** (owner): with Rs 2 lakh at 1% (Rs 2,000) none of the protected-selling trades fit.

## 2. What the data cannot tell us yet
- Real executable prices (no bid/ask in daily files); the Rs 1 pad is an assumption.
- Behaviour in a crash larger than -6% in one day (not in this period).
- Whether the edge survives 2019-2023, and different volatility regimes.

## 3. Next
- Full option chains for every month (raw files from Google Drive), then 2019-2023 history.
- Test the four refinements above, one at a time, against the plain version.
- ChatGPT takes the same roles on the same data and challenges every reading above.
