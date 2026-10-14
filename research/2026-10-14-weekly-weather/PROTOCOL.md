# Weekly NIFTY options and a market-weather signal: frozen protocol (14 Oct 2026)

Owner: YES to the combined study (orchestrator, 14 Oct 2026). The aim is evidence, not luck: trade only defined-risk
structures, held for days, and stay out when the market is unstable. Research only: no `fno/` code, nothing
registered in the playbook.

**This file is written before any weekly-option P&L or weather-signal outcome has been computed or looked at.** It is
frozen when committed together with `study.py` (their SHA-256 hashes go in `FREEZE.md`). The ledger rows
(`research/ledger.csv`, trials 43-52) name that commit. The script runs once after that. Any change afterwards is a new,
separately registered trial; it is never an edit of this one.

## 1. What history is already used, and what is fresh

| Data | Status before this study |
|---|---|
| NIFTY **monthly** options 2019-23 | **Used up**: experiment 1's holdout (judge 53, ChatGPT review 30) |
| NIFTY monthly options 2024-26 | Discovery: seen in desk meeting 1 and experiment 1 |
| NIFTY **weekly** option prices 2019-26 | **Never used in any trial** (in the panel since story A3; only data checks ran on them) |
| NIFTY index closes, India VIX 2017-26 | **Exposed**: experiment 1's features (F1, F2 VIX vs median), desk meeting 2's holding-window moves |
| Event calendar (A6) | Exposed: experiment 1's F3 |

So this is a **historical test on unused option prices, with exposed predictors**. The weather thresholds below are set
by reasoning, but by someone who has seen NIFTY's and VIX's history, so a pass would be weaker evidence than a forward
test. Weekly prices from 2019-26 can be used once, here.

## 2. Data

- **Prices:** `research/data/nifty-panel/options_<year>.csv.gz` (NSE bhavcopy, every NIFTY expiry from 1 Jan 2019,
  sessions to 9 Oct 2026). Close-proxy: each leg is filled at NSE's close on the entry day, and a leg needs `volume`
  > 0 that day, or the trade is unfillable (no trade).
- **Signal inputs:** NIFTY 50 and India VIX closes from `research/data/nifty-panel/warmup_closes.csv` (from 2017, for
  the 250-session median), and events from `research/data/events/events.csv`.
- No quotes, no bid-ask, no intraday data, and no opening prices (gaps are measured close to close; see section 5).

## 3. Trades (one per weekly expiry, non-overlapping)

- **Expiries:** every distinct NIFTY option expiry in the panel, in date order. Each expiry E is one opportunity.
- **Entry:** the first regular session after the previous expiry (E-1). The first expiry of 2019 has no entry.
  **Decision day:** the session before entry. Every signal input is known by the decision day's close.
- **Skip** the opportunity if the entry day is less than 2 sessions before E, or if it is a special or muhurat session.
- **Exit:** held to expiry and cash-settled on the intrinsic value at the expiry day's NIFTY 50 close (`underlying`),
  with no exit order. The trades never overlap, so they are independent apart from market regime.
- **Size:** 1 lot of 65 units throughout (today's lot, as in experiment 1; historical lots were 75 / 50 / 25).
- **Strikes:** NIFTY strikes on the entry day; S = the entry day's `underlying`. "Nearest" means the nearest listed
  strike, with ties going to the higher strike.
- **Costs:** entry legs pay a Rs 1 per unit pad (bought +1, sold -1) and C1 charges (`fno.costs.order_charges`,
  `config.yaml` charges). At expiry, in-the-money legs pay `fno.costs.settlement_charges_breakdown`. No exit pads. P&L is
  pre-tax.
- **Cap:** a trade whose maximum loss, including entry pads and charges, is above **Rs 10,000** is not taken (`over_cap`).

| Id | Structure | Legs (bought +, sold -) | Maximum loss |
|---|---|---|---|
| W1 | Bought call | +1 call nearest S x 1.01 | premium + costs |
| W2 | Bought put | +1 put nearest S x 0.99 | premium + costs |
| W3 | Bull call spread | +1 call nearest S, -1 call 100 points higher | debit + costs |
| W4 | Bear put spread | +1 put nearest S, -1 put 100 points lower | debit + costs |
| W5 | Short iron condor (protected) | -1 call nearest S x 1.015, +1 call 100 higher; -1 put nearest S x 0.985, +1 put 100 lower | 100 x 65 - credit + costs |

A trade with a missing strike, or a leg with no volume on the entry day, is `unfillable`.

## 4. Part 1 test: is there an edge? (trials 43-47, one per structure)

Per structure, over all taken trades, net Rs per trade:
- **Pass** only if all three hold:
  1. mean net > 0 in **both** 2019-2023 and 2024-2026 (by entry year);
  2. t = mean / (SD / sqrt(n)) **>= 2.33** (one-sided 1%, i.e. Bonferroni 5% over the 5 structures);
  3. the bootstrap 1st-percentile lower bound of the mean is > 0 (10,000 resamples of trades, seed 20261014).
- Also reported: n, trades a year, win rate, mean gross, mean costs, worst trade, max-loss hits (a loss of at least 90%
  of the trade's maximum loss), and trades needed at 2 SE = (2 x SD / mean)^2 for positive means.

## 5. Part 2: the market-weather signal (fixed here, before any test)

Computed on the **decision day** from closes up to and including that day:

- `vix_ratio` = VIX / median VIX of the previous 250 sessions;
- `vix_change5` = VIX / VIX 5 sessions earlier - 1;
- `move5` = the largest |daily NIFTY 50 close-to-close return| over the last 5 sessions. This stands in for "gap
  size": no opening prices exist in our data;
- `rv10` = the annualised realised volatility of the last 10 daily log returns (sqrt(252) x the root mean square, not
  demeaned);
- `event` = a row of `events.csv` with `scheduled` = yes, `announced_on` <= the decision day, and `date` after the entry
  day and on or before the expiry.

The colour, by the first rule that matches:

1. **RED** if any of: `vix_ratio` >= 1.30, `vix_change5` >= +20%, `move5` >= 2.0%, `rv10` >= 25%.
2. **AMBER** if any of: `vix_ratio` >= 1.10, `vix_change5` >= +10%, `move5` >= 1.25%, `rv10` >= 18%, or `event`.
3. **GREEN** otherwise.

Why (reasoning only): a high VIX against its own recent history, a VIX jump, a recent big move and high realised
volatility are the textbook signs of an unstable market, in which gap risk is higher. Scheduled events bring known
jumps. The thresholds are round numbers, not fitted.

## 6. Part 2 test: does staying out on RED help? (trials 48-52, one per structure)

Per structure, comparing RED trades with non-RED (GREEN plus AMBER) trades:
- **"The filter helps"** only if both hold:
  1. RED mean net < non-RED mean net, with a one-sided Welch t >= 1.645;
  2. the RED max-loss-hit rate >= the non-RED rate.
- Reported: n, mean, max-loss hits by colour (GREEN, AMBER and RED separately; AMBER is descriptive only); the **cost
  of staying out**, which is the sum of RED trades' nets (positive = profit given up, negative = losses avoided); and
  the structure's total with and without RED trades.
- **Crash windows, reported separately:** 2020 = trades entered from 17 Feb 2020 to 30 Apr 2020; 2024 = the trade whose
  holding window contains 4 June 2024 (election-result day). For each: colours, nets and max-loss hits.

## 7. What the result can and cannot say

- A Part 1 pass is a gate to a forward shadow test (experiment 2), never proof.
- A fail means "no edge shown under a strict test".
- The weather signal is judged only on whether RED trades did worse; it is never tuned after the run.
- Close-proxy fills, no bid-ask, today's lot and today's charges applied to 2019-2023: as experiment 1.

## 8. Not in this study

- Two-week holds.
- Strangles and straddles.
- Unprotected selling (never: owner's rule).
- Any threshold search.
