# Experiment 1 protocol: protected sell vs protected buy vs no trade, on NIFTY monthly options

Status: **draft for ChatGPT review, written before any 2019-2023 data is read** (12 Oct 2026). After review it is
frozen: commit hash recorded here, nothing below changes once 2019-2023 results are seen. Design rules:
`docs/DESK_DESIGN.md` sections 3.5, 5, 6 and 8.

## 1. Question
Which entry-known conditions improve the net payoff of a fully protected NIFTY monthly trade, within the owner's
limits, compared with no trade and with the same trade taken every month?

## 2. Data and periods
- NSE daily F&O files (both formats, one reader: `fno/fo_bhavcopy.py`, proven identical on 128 overlap days) and NSE
  daily index closes (NIFTY 50 and India VIX).
- **Discovery: 1 Jan 2024 - 9 Oct 2026** (already looked at; about 33 cycles). Results reported, no pass/fail.
- **Challenge: 1 Jan 2019 - 31 Dec 2023** (not yet read; about 60 cycles). The pass/fail in section 7 applies here only.
- Forward paper trading follows for anything that passes.

## 3. The trade cycle (same for every policy)
- **Expiry:** NIFTY monthly, identified as of each day (`expiries.monthly_as_of`: listed that day and listed more
  than 50 days ahead on that day or before).
- **Decision day:** the first trading day the expiry is 30-45 calendar days away; features use data up to that close.
- **Entry fill:** next trading day's close (close-proxy for the 3 pm desk, labelled as such), Rs 1 worse per leg.
- **Exit fill:** last trading day with 21 or more calendar days to expiry, its close, Rs 1 worse per leg. No other
  exits in this experiment (loss and profit exits are a later experiment).
- **Prices:** a leg's close if it traded that day; otherwise its settlement price, flagged. A cycle with more than
  half of its legs flagged at entry or exit is reported "unfillable" and counts as no trade.
- **Price sanity:** a short structure whose credit is at least its width, or a long one whose debit is at most zero,
  cannot exist in a real market (stale prices of untraded options): the cycle is reported "bad prices", no trade.
- **Costs:** current Groww and exchange charges (`config.yaml` charges), current lot 65, 1 lot.
- **Tax:** 31.2% on each calendar year's positive net (losses offset within the year), reported separately.

## 4. Structures (strikes from the nearest listed strike; all legs same expiry)
| Code | Structure | Legs |
|---|---|---|
| SF | Short iron fly | sell ATM call and put; buy call and put W points away |
| SC | Short iron condor | sell call at spot +2% and put at spot -2%; buy each W points further out |
| BF | Long iron fly (bounded-debit buying, E9) | buy ATM call and put; sell call and put W points away |

**Width rule (owner's Rs 10,000 cap):** W is the largest of 100, 150, 200, 250, 300 points for which the maximum
possible loss at entry prices, including entry and exit charges and pads, is at most Rs 10,000. If none fits, the
cycle is "no trade (cap)". Meeting 1's 300- and 500-point condors could lose more than that per lot, so
most were outside this cap (maximum loss = (width - credit) x 65: up to about Rs 30,000 for 500-point wings); their results are not comparable.

## 5. Entry-known features (all computed at the decision-day close)
- **F1 volatility premium:** ATM implied volatility (average of call and put, Black-Scholes, rate 6.5%) minus NIFTY's
  realised volatility over the past 20 trading days (root mean square of daily log returns, not demeaned, x sqrt 252).
- **F2 VIX level:** India VIX close above its median over the past 250 trading days.
- **F3 scheduled event:** an RBI policy announcement, Union Budget or general-election result day falls between entry
  and exit. Dates come from `events.csv` (official RBI and government announcements), committed before results.

## 6. Policies (registered trials; every one goes in `research/LEDGER.md` before results)
| Code | Rule |
|---|---|
| P1 | SC every cycle |
| P2 | SF every cycle |
| P3 | BF every cycle |
| P4 | SC if F1 > 0, else no trade |
| P5 | SC if F1 > 0, else BF |
| P6 | SC if F1 > 0 and not F3, else no trade |
| P7 | SC if F2, else no trade |
| P8 | SF if F1 > 0, else no trade |
| C1 | Control: SC or no trade by coin toss (10,000 seeded runs) |
| C2 | Control: opposite of P4 (SC only when F1 <= 0) |

Thresholds are fixed as written (0 for F1, the median for F2). No other variant is tried on the challenge period.

## 7. Pass / fail on 2019-2023 (all must hold for a policy to go to paper trading)
1. Total net P&L after charges and pads > 0.
2. Mean net per cycle: lower bound of a one-sided 99.3% interval > 0 (95% Bonferroni-adjusted for 7 policies;
   cycle-level bootstrap, 10,000 resamples, seed 20261012).
3. Total net above the 95th percentile of control C1, and above control C2.
4. For P4-P8: total net above the same structure taken every cycle (P1 or P2), i.e. the condition adds value.
5. No cycle loses more than Rs 10,000 (else the implementation is wrong and the run is void).
Also reported, not pass/fail: win rate, worst cycle, longest losing run, yearly net after tax, results by year,
cycles with no trade (cap) or unfillable.

A policy that fails is not traded; it may stay in research only as a new registered trial with a new protocol.
Passing means paper trading under the agreed evaluation plan, not real money.

## 8. Known limits (stated before results)
- Daily closes, not 3 pm quotes; no bid-ask (Rs 1 pad is an assumption until calibrated from real quotes).
- About 60 challenge cycles: a real but small edge may fail criterion 2. That is accepted: a false "pass" costs
  money, a false "fail" costs time.
- 2019-2023 had different lot sizes and charges; the test applies today's lot and charges to every cycle.
- The policies were chosen after seeing 2024-2026 (meeting 1); that is why the challenge period decides.
