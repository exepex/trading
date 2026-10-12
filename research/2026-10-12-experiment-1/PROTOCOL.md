# Experiment 1 protocol: protected sell vs protected buy vs no trade, on NIFTY monthly options

Status: **version 2.1, agreed by Claude and ChatGPT** (ChatGPT review 14, 12 Oct 2026); not yet frozen: the freeze
(section 10) happens after the engine is built and before any challenge outcome is read, written before any 2019-2023 outcome is read.
Version 1 was reviewed in ChatGPT review 12; changes answered in `reviews/claude/response_15_...`. Freezing (section
10) happens before the challenge period is read and records the protocol commit and the hashes of the code, settings
and calendars used. Design rules: `docs/DESK_DESIGN.md` sections 3.5, 5, 6 and 8. Engine stories: B1-B5.

## 1. Question
Which entry-known conditions improve the net payoff of a fully protected NIFTY monthly trade, within the owner's
limits, compared with no trade, with the same trade taken every month, and with the same trade taken at random times?

## 2. Data and periods
- NSE daily F&O files (both formats, one reader: `fno/fo_bhavcopy.py`, identical on all 128 overlap days), NSE daily
  index closes (NIFTY 50, India VIX), the NSE session calendar (story A1) and the events calendar (story A6).
- **Discovery: 1 Jan 2024 - 9 Oct 2026** (already looked at; about 33 opportunities). Results reported, no pass/fail.
- **Challenge: 1 Jan 2019 - 31 Dec 2023** (about 60 opportunities). The pass/fail in section 8 applies here only.
- What the challenge is: a **pre-registered historical holdout** of data not used to form these policies. It is
  earlier in time than the discovery period, so it is not a forward test; anything that passes still needs forward
  paper trading (owner's paper gate). All features use only data available at each historical decision day.
- What it is not: a test of the 15:00 desk. All prices are daily closes (**close-proxy**); a 15:00 version of any
  feature or fill is a different thing and needs its own forward evidence.

## 3. Opportunities and timing (identical for every policy and control)
- **One opportunity per NIFTY monthly expiry.** Monthly identity as of each day (`monthly_as_of`: listed that day and
  listed more than 50 days ahead on that day or before).
- **Decision day:** the first trading day the expiry is 30-45 calendar days away. Features use data up to that day's
  official close. F3 events must have been announced on or before the decision day.
- **Entry fill:** next trading day's close. **Exit fill:** the last trading day with 21 or more calendar days to
  expiry, its close. No other exits in this experiment. If the entry day is not before the exit day, the opportunity
  is `no_entry_window`.
- Holding periods do not overlap: in 2024-26 every exit is at least 4 days before the next entry (checked on all 33
  cycles), which supports resampling opportunities as units (section 8).

## 4. Prices, strikes, costs and the loss cap
- **Strikes:** nearest listed strike to the target; ATM ties take the lower strike; a short out-of-the-money leg tie
  takes the strike farther from spot; a wing W points away must be listed exactly, else that width is unavailable.
- **Prices:** a leg's close if it traded that day (volume > 0), else its settlement price, flagged. Settlement is a
  valuation proxy, not an executable price. A zero or missing price, or more than half the legs flagged at entry or
  exit, makes the opportunity `unfillable`. A short structure's credit at least its width, or a long structure's debit
  at most zero, makes it `bad_prices` (stale prices).
- **Fills and costs:** bought legs at price + Rs 1, sold legs at price - Rs 1, at entry and exit; current Groww and
  exchange charges (`config.yaml` charges, hash recorded at freeze) per leg and side; current lot 65; 1 lot.
- **Structures:** SF short iron fly (sell ATM call and put, buy each W away); SC short condor (sell call nearest
  spot x 1.02 and put nearest spot x 0.98, buy each W further out); BF long iron fly (buy ATM call and put, sell each
  W away).
- **Width rule (owner's Rs 10,000 cap):** W is the largest of 300, 250, 200, 150, 100 points for which the **modelled
  maximum terminal payoff loss** (short: (W - credit) x 65; long: debit x 65) plus entry charges, exit charges at the
  worst-case exit prices and all pads is at most Rs 10,000. No listed width fits: `no_trade_cap`. Wings not listed at
  all: `missing_strikes` (a data condition, reported separately). A realised loss above the cap should be impossible
  for these structures; if one appears it is reported and investigated, never hidden.
- **Sensitivity (reported, never used to pass):** the same results with every opportunity that needed a settlement
  price treated as no trade.

## 5. Entry-known features (decision-day close)
- **F1 volatility premium:** ATM implied volatility (average of call and put; Black-Scholes, rate 6.5%, time =
  calendar days / 365, solver bounds 1%-200%; only traded legs) minus NIFTY's realised volatility over the past 20
  trading days (root mean square of daily log returns, not demeaned, x sqrt 252). Missing or failed: `None`.
- **F2 VIX level:** India VIX close above the median of the previous 250 trading days' closes; fewer than 250 valid
  closes: `None`.
- **F3 scheduled event:** a `scheduled = yes` event in `events.csv` dated after the entry day and on or before the exit
  day, announced on or before the decision day. Unscheduled events are never used.
- A condition with a `None` input counts as not met.

## 6. Policies and controls (registered in the ledger before any challenge result)
| Code | Rule | Candidate for paper? | Compared with (criterion 4) |
|---|---|---|---|
| P1 | SC every opportunity | yes | - |
| P2 | SF every opportunity | yes | - |
| P3 | BF every opportunity | yes | - |
| P4 | SC if F1 > 0, else no trade | yes | P1 |
| P5 | SC if F1 > 0, else BF (no trade if F1 is None) | yes | P1 and P4, plus the BF-branch test (criterion 5) |
| P6 | SC if F1 > 0 and not F3, else no trade | yes | P1 and P4, plus the event-filter test (criterion 6) |
| P7 | SC if F2, else no trade | yes | P1 |
| P8 | SF if F1 > 0, else no trade | yes | P2 |

**Hypothesis family:** all 8 policies are promotion candidates, so 8 tests.

**Controls (not hypotheses):**
- **C1 random timing:** for each conditional policy (P4-P8), 10,000 sequences (seed 20261012) that take each of the
  policy's actions on randomly chosen opportunities with the same counts as the policy took in that period (e.g. P4
  traded SC on 40 of 60: each sequence trades SC on 40 random opportunities of the same 60, no trade on the rest).
  Opportunities of any status are eligible; a chosen opportunity that is `unfillable`, `bad_prices`, `no_trade_cap`
  or `missing_strikes` for that structure scores 0, exactly as for the policy. Statistic: total net. For P1-P3 the
  control is identical to the policy and is not applied.
- **C2 opposite condition** (exact formulas; a `None` input means no trade):
  - P4: SC if F1 is not None and F1 <= 0, else no trade.
  - P5: BF if F1 is not None and F1 > 0; SC if F1 is not None and F1 <= 0; no trade if F1 is None.
  - P6: SC if F1 is not None and (F1 <= 0 or F3 is true), else no trade.
  - P7: SC if F2 is not None and F2 is false, else no trade.
  - P8: SF if F1 is not None and F1 <= 0, else no trade.
  Statistic: total net.

## 7. Statistics
- **Per-opportunity P&L:** every opportunity counts; no trade and every non-traded status count as Rs 0. Traded-only
  statistics are reported separately and never used to pass.
- Reported for each policy and period: total and mean net per opportunity, count by status, traded count, win rate
  (traded only), worst opportunity, longest losing run, maximum drawdown over opportunities, results by calendar
  year and the share of total net from the best year, and the assumed tax scenario (section 9).
- **Bootstrap:** resampling unit = opportunity (holding periods do not overlap); 10,000 resamples with replacement of
  the challenge opportunities; seed 20261012 (numpy `default_rng`); statistic = mean net per opportunity; the lower
  bound is the resampled means sorted ascending, taken at index 62 (0-based), i.e. the 0.625th percentile
  (one-sided 99.375%), with no interpolation.
- **Sensitivity (reported, never used to pass):** year-block bootstrap (resampling whole calendar years, 10,000
  resamples, same seed) to show the effect of volatility clustering; with five years its interval is very wide.
- Monte Carlo error: with 10,000 resamples about 62 values lie below the bound. For criterion 2 the report shows the
  lower bound's distance from zero in Rs per opportunity and its Monte Carlo standard error (from 20 repeat bootstraps
  with seeds 20261012 + 1 to + 20, reported only); the verdict uses the main seed only. No "borderline" category.

## 8. Pass / fail on 2019-2023 (pre-tax; all applicable criteria must hold)
1. Total net per-opportunity P&L after charges and pads > 0.
2. Bootstrap lower bound of mean net per opportunity > 0 (one-sided 99.375% = 95% Bonferroni over 8 policies).
3. (P4-P8) Total net above the 95th percentile of its C1 random-timing control, and above its C2 opposite control.
4. (P4-P8) Total net above each policy in its "compared with" column (whole-policy superiority).
5. (P5 only) **BF-branch test:** on the opportunities where P5 chose BF, the sum of BF per-opportunity P&L (statuses
   other than `traded` count 0) is > 0. P5 claims the BF branch adds value only if this holds.
6. (P6 only) **Event-filter test:** on the opportunities where P4 would trade SC but P6 does not (F1 > 0 and F3 true),
   the sum of SC per-opportunity P&L is < 0, i.e. the trades the filter removed lost money. P6 claims the event filter
   adds value only if this holds.
7. No traded opportunity's modelled maximum terminal loss including charges and pads exceeds Rs 10,000 (else the run
   is void and investigated).

**Meaning of the result:** pass = goes to paper trading under the agreed evaluation plan (not real money). Fail =
**insufficient evidence** under a deliberately strict test with about 60 opportunities, not proof that no edge
exists; it is not traded and may only return as a new registered trial with a new protocol and data not yet used.
No criterion is relaxed after results.

## 9. Tax (reported, never used to pass)
One assumed scenario, the same as story C1: Indian financial year (April-March); base = the year's trade net (research
has no operating costs); tax = 31.2% of max(0, base); losses offset within the year; no carry-forward modelled. It is
an assumption for comparison, not a verified tax liability.

## 10. Freeze and access
- Before the challenge period is read, `research/2026-10-12-experiment-1/FREEZE.md` records: the protocol commit;
  SHA-256 of the engine code (B1-B4), `config.yaml` charges, `events.csv`, the session calendar and the panel
  manifest; the ledger registration commit (an ancestor of the run commit).
- **Access attestation (so far):** to build the old-format reader, Claude opened the first lines of the NSE
  old-format files for 1 and 2 Jan 2019 (header and a few BANKNIFTY futures rows) and the index-close file for
  2 Jan 2019 (NIFTY 50 close 10,792.5). No 2019-2023 option outcome, cycle, feature or P&L has been computed or
  viewed. Any further access before the freeze is added here with its reason.
- After the freeze, the challenge run is executed once by the engine; its results file and the run commit are
  published as they come out.

## 11. Known limits (stated before results)
- Daily closes, not 15:00 quotes; no bid-ask (the Rs 1 pad is an assumption until calibrated from A4 quotes).
- About 60 challenge opportunities: a real but small edge may fail criterion 2.
- 2019-2023 had different lot sizes and charges; today's lot and charges are applied to every opportunity.
- The policies were chosen after seeing 2024-2026 (meeting 1); that is why the challenge period decides.
