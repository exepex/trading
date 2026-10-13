# Experiment 1 protocol: protected sell vs protected buy vs no trade, on NIFTY monthly options

Status: **version 2.2, agreed by Claude and ChatGPT** (ChatGPT review 28 section 1, 13 Oct 2026; Claude's check in
`reviews/claude/response_60_2026-10-13-on-review-28.md`); **not yet frozen**: the judge checks this text first, then
the freeze recipe (section 10) runs, before any challenge outcome is read. Version history: section 12. Freezing
records the protocol commit and the hashes of the code, settings and calendars used. Design rules: `docs/DESK_DESIGN.md` sections 3.5, 5, 6 and 8. Engine stories: B1-B5.

## 1. Question
Which entry-known conditions improve the net payoff of a fully protected NIFTY monthly trade, within the owner's
limits, compared with no trade, with the same trade taken every month, and with the same trade taken at random times?

## 2. Data and periods
- NSE daily F&O files (both formats, one reader: `fno/fo_bhavcopy.py`, identical on all 128 overlap days), NSE daily
  index closes (NIFTY 50, India VIX), the NSE session calendar (story A1) and the events calendar (story A6).
- **Discovery: 1 Jan 2024 - 9 Oct 2026** (already looked at; 33 opportunities). Results reported, no pass/fail.
- **Challenge: 1 Jan 2019 - 31 Dec 2023** (60 opportunities). The pass/fail in section 8 applies here only.
- **Which period and which year:** an opportunity belongs to the period of its **decision day** (a cycle decided in
  December 2023 is a challenge opportunity although it exits in January 2024). A cycle's P&L is dated by its **exit
  day**: calendar year for "results by year" and the year-block bootstrap, Indian financial year (April-March) for the
  tax scenario.
- What the challenge is: a **pre-registered historical holdout** of data not used to form these policies, with
  limited pre-freeze predictor exposure (section 10). It is earlier in time than the discovery period, so it is not
  a forward test; anything that passes still needs forward paper trading (owner's paper gate). All features use only data available at each historical decision day.
- What it is not: a test of the 15:00 desk. All prices are daily closes (**close-proxy**); a 15:00 version of any
  feature or fill is a different thing and needs its own forward evidence.

## 3. Opportunities and timing (identical for every policy and control)
- One opportunity per NIFTY monthly expiry. Point-in-time monthly identity on day D: an option expiry is monthly iff
  a NIFTY index future with the same expiry is listed on D. The rule uses listings available on D only. The measured
  pre-freeze cycle count is 60 for 2019-2023 and 33 for 2024-09 Oct 2026; these counts use dates/listings only, not
  outcomes. (No 50-day listing rule, not even as a fallback: it took 2019-2022 weeklies as monthly. Code:
  `fno.research_data.expiries.monthly_from_futures`.)
- **Decision day:** the first trading day the expiry is 30-45 calendar days away. Features use data up to that day's
  official close. F3 events must have been announced on or before the decision day.
- **Entry fill:** next trading day's close. **Exit fill:** the last trading day with 21 or more calendar days to
  expiry, its close. No other exits in this experiment. If the entry day is not before the exit day, the opportunity
  is `no_entry_window`.
- **Trading days** are NSE's sessions (story A1 calendar) without Diwali's one-hour muhurat session, which never
  decides, enters or exits a cycle. Only sessions with listed contracts can be decision days. A cycle whose 30-45 day
  window opened before the first session with listed contracts is not an opportunity (its first trading day in the
  window is unknown; this drops only the January 2019 expiry).
- Holding periods do not overlap: every exit is at least 5 calendar days before the next entry (checked on all 93
  cycles 2019-2026, dates only), which supports resampling opportunities as units (section 7).

## 4. Prices, strikes, costs and the loss cap
- **Strikes:** chosen from the **entry day's** NIFTY 50 close and option chain; nearest listed strike to the target;
  ATM ties take the lower strike; a short out-of-the-money leg tie takes the strike farther from spot; a wing W points
  away must be listed exactly, else that width is unavailable.
- **Prices:** a leg's close if it traded that day (volume > 0), else its settlement price, flagged. Settlement is a
  valuation proxy, not an executable price; a settlement of 0.00, or any settlement on the option's expiry day, is no
  price. A zero or missing price, or more than half the legs flagged at entry or exit, makes the opportunity
  `unfillable` (exactly half flagged is fillable).
- **Impossible prices (`bad_prices`, not traded):** at entry, a position valued at or beyond its worst or best payoff
  at expiry: a trade that cannot lose (a short structure's credit at least its width; a long structure's debit at
  most zero) or cannot win (**a long structure's debit at least its width**, owner decision of 13 Oct 2026; a short
  credit at most zero). Prices are never repaired.
- **Exit-bound anomalies (report only):** a traded exit valued beyond the position's payoff bounds at expiry (e.g. a
  closing spread worth more than its width) stays traded and its net counts; it is flagged and each policy reports
  the count and net of such exits, so results show how much rests on impossible closes.
- **Fills and costs:** bought legs at price + Rs 1, sold legs at price - Rs 1, at entry and exit; current Groww and
  exchange charges (`config.yaml` charges, hash recorded at freeze) per leg and side; current lot 65; 1 lot.
- **Structures:** SF short iron fly (sell ATM call and put, buy each W away); SC short condor (sell call nearest
  spot x 1.02 and put nearest spot x 0.98, buy each W further out); BF long iron fly (buy ATM call and put, sell each
  W away).
- **Width rule (owner's Rs 10,000 cap):** W is the largest of 300, 250, 200, 150, 100 points for which the **modelled
  maximum terminal payoff loss** (short: (W - credit) x 65; long: debit x 65) plus entry charges, exit charges at the
  worst-case exit prices and all pads is at most Rs 10,000. Worst-case exit prices: each leg's value at expiry at the
  strike where the payoff loss is largest (ties: the larger exit charges); every order is charged at a price of at
  least one tick (Rs 0.05). A width with unusable or impossible entry prices is skipped like an unlisted one. If no
  width trades, the status is the outcome of the narrowest listed width (`no_trade_cap`, `unfillable` or
  `bad_prices`); no width listed: `missing_strikes` (a data condition, reported separately). A realised loss above the cap should be impossible
  for these structures; if one appears it is reported and investigated, never hidden.
- **Sensitivity (reported, never used to pass):** the same results with every opportunity that needed a settlement
  price treated as no trade.

## 5. Entry-known features (decision-day close)
- **F1 volatility premium:** ATM implied volatility: the average of the call and the put implied volatility at the
  ATM strike (the listed strike nearest the NIFTY 50 close, the lower one on a tie), each from **Black-76 with the
  same-expiry NIFTY future's close as the forward**, the rate 6.5% only discounting; time = calendar days to expiry /
  365; solver bounds 1%-200%, a price outside them or a solution at a bound gives no value; only legs and a future
  that traded that day; settlement is never used. **The thinner ATM call/put volume must be >= 10 contracts**; below
  10, F1 = `None` (never a settlement substitute). Minus NIFTY's realised volatility over the past 20 trading days
  (root mean square of daily log returns, not demeaned, x sqrt 252; 21 valid closes). Missing or failed: `None`.
- **F2 VIX level:** India VIX close above the median of the previous 250 trading days' closes; fewer than 250 valid
  closes: `None`. The 2017-18 index-close files (story A10) give the 2019 decision days their 250 previous closes.
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
  Exact draws: `rng = numpy.random.default_rng(20261012)` for each conditional policy; per sequence
  `order = rng.permutation(n)`; the policy's actions in sorted code order (BF before SC before SF) take consecutive
  slices of `order` with the policy's counts; a sequence's total is plain left-to-right float addition of its chosen
  P&L in that order.
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
  year and the share of total net from the best year, the no-settlement sensitivity, the exit-bound anomaly count and
  net (section 4), and the assumed tax scenario (section 9).
- **Definitions:** maximum drawdown = the largest fall of cumulative per-opportunity net P&L from its previous peak,
  the start (0) counting as a peak, in rupees. Longest losing run = the most consecutive opportunities with net < 0
  (an opportunity with 0, traded or not, ends a run). Win rate = traded opportunities with net > 0 / traded
  opportunities.
- **Bootstrap:** resampling unit = opportunity (holding periods do not overlap); 10,000 resamples with replacement of
  the challenge opportunities: `rng = numpy.random.default_rng(20261012)`; one draw
  `rng.integers(0, n, size=(10000, n))`; resample r takes the opportunities in row r; statistic = mean net per
  opportunity; the lower bound is the resampled means sorted ascending, taken at index 62 (0-based), i.e. the
  0.625th percentile (one-sided 99.375%), with no interpolation.
- **Sensitivity (reported, never used to pass):** year-block bootstrap: whole calendar years (by exit day) drawn the
  same way, `rng.integers(0, Y, size=(10000, Y))` with the same seed; statistic = total net of the drawn years / their
  opportunity count; index 62. It shows the effect of volatility clustering; with five years its interval is very
  wide.
- Monte Carlo error: with 10,000 resamples about 62 values lie below the bound. For criterion 2 the report shows the
  lower bound's distance from zero in Rs per opportunity and its Monte Carlo standard error (from 20 repeat bootstraps
  with seeds 20261012 + 1 to + 20: the sample standard deviation, ddof 1, of their lower bounds; reported only); the
  verdict uses the main seed only. No "borderline" category.
- The numpy version is recorded at the freeze and in every results file (generator streams are guaranteed only within
  a version).

## 8. Pass / fail on 2019-2023 (pre-tax; all applicable criteria must hold)
1. Total net per-opportunity P&L after charges and pads > 0.
2. Bootstrap lower bound of mean net per opportunity > 0 (one-sided 99.375% = 95% Bonferroni over 8 policies).
3. (P4-P8) Total net above the 95th percentile of its C1 random-timing control, and above its C2 opposite control.
   The 95th percentile of the 10,000 C1 totals is the ascending value at index ceil(0.95 x 10,000) - 1 = 9,499
   (0-based), no interpolation; the policy passes only if its total is strictly above it (equal is a fail).
4. (P4-P8) Total net above each policy in its "compared with" column (whole-policy superiority).
5. (P5 only) **BF-branch test:** on the opportunities where P5 chose BF, the sum of BF per-opportunity P&L (statuses
   other than `traded` count 0) is > 0. P5 claims the BF branch adds value only if this holds.
6. (P6 only) **Event-filter test:** on the opportunities where P4 would trade SC but P6 does not (F1 > 0 and F3 true),
   the sum of SC per-opportunity P&L is < 0, i.e. the trades the filter removed lost money. P6 claims the event filter
   adds value only if this holds. If the filter removes no trade, the sum is 0, not below 0: P6 fails criterion 6
   (it is not "not applicable").
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
- 12 Oct 2026, after the owner's upload: Claude listed the Drive files (names, sizes, counts per year) and checked
  integrity of 60 random old-format zips (internal checksums) and 30 random index-close files (header present and a
  "Nifty 50" line present). No value was read, printed or computed.
- **Freeze recipe (enforced by the engine, story B4):** (a) commit the final protocol (commit A); (b) add the line
  `frozen at commit A` and `FREEZE.md` (hashes, numpy version, access attestation) and commit (F); (c) set
  `protocol_commit` = F in ledger rows 22-31 and commit; (d) `python -m fno research run 2026-10-12-experiment-1
  --period challenge`; (e) commit the results and the ledger's first-run record. The challenge runs only if the
  protocol holds a `frozen at commit` line whose commit exists and precedes the run, and the protocol at that commit
  equals today's protocol without the line.
- After the freeze, the challenge run is executed once by the engine; its results file and the run commit are
  published as they come out.
- **Reader revision before the freeze (30 Mar 2021):** NSE published no old-format F&O file for 30 Mar 2021, so the
  panel has no option or future rows that day. Since commit `9f39718` (reached `main` in merge `0364b22`, 13 Oct
  2026) the panel reader gives that session NSE's index closes from its index-close file (NIFTY 50 14,845.10, India
  VIX 20.65). This changes closes-based values for about 20 sessions after it: the challenge cycle decided 12 Apr 2021
  (expiry 27 May 2021) had F1 = `None` before and has a value since (reported by judge 44 and response 55; not
  recomputed here, to avoid computing a challenge feature).
  This is a legitimate data-reader correction before the freeze; no challenge P&L was viewed.
- **Access since version 2.1 (13 Oct 2026), all before the freeze:**
  - Listing dates: Claude read the 2019-2026 option and future files' `date` and `expiry` columns (and the panel with
    every option row refused) to find the weekly/monthly bug and count cycles (60 and 33); judge 46 reproduced the
    counts. A test keeps the rows of one 2019 weekly (18 Apr 2019) only to find its first listing date (15 Feb 2019);
    no price from them is printed.
  - ATM volume and open interest counts on 2019-2023 decision days (response 48 item 8, the F1 volume table); F2's
    defined-day count after story A10 (judge 34).
  - The 30 Mar 2021 index closes above (two index values).
  - **G1's golden file (disclosure, ChatGPT review 29 section 1, accepted in response 63):** Before the Experiment-1
    freeze, G1 generated `research/forecasts/golden_iv30_rv20.csv` over 2019-2026. It computed IV30 and trailing RV20
    for challenge-period sessions. These are entry-known predictors and overlap with F1's components, but no
    Experiment-1 F1 decision-day series, policy action, option outcome, trade P&L, control statistic or pass/fail
    result was computed or viewed from this work. The golden was generated only after the Experiment-1 rules and
    thresholds had been fixed.
    - File: added in commit `769fac7` (13 Oct 2026 14:24 UTC), SHA-256
      `dcb011864502dca2566ff168c6014187e17292d03a8f756a60c7fbab0f1355c5` (unchanged since).
    - Order: the last rule-setting commit, the owner's F1 10-contract floor `ec2e9a5` (13 Oct 2026 12:43 UTC), came
      before G1's first computation of these values for commit `f936156` (12:56 UTC) and before the file itself. The
      policies P1-P8 and their thresholds were fixed in version 2.1 (12 Oct 2026). Later version 2.2 changes are
      listing-date rules and conventions, not chosen from these values.
    - Views: while writing version 2.2, Claude printed the file's first four rows (1 to 4 Jan 2019, none a decision
      day).
  - **Hard rule from now until the challenge run:** no Experiment-1 rule, F1 threshold, structure, policy, control or
    pass criterion may be changed in response to any 2019-2023 golden value. A data or code correctness bug may be
    fixed, but it must be disclosed and independently judged before the freeze. No one prints or analyses the golden
    file's challenge-period values for Experiment 1 before the run; the committed file stays (deleting it would not
    unsee it).
  - **Label:** the final report describes 2019-2023 as a **historical holdout with limited pre-freeze predictor
    exposure**, not a perfectly untouched or blinded holdout. A pass remains only a gate to forward paper trading.
  - Otherwise no 2019-2023 option price, Experiment-1 feature value (F1, F2, F3 as such), option outcome or P&L was
    computed or viewed.

## 11. Known limits (stated before results)
- Daily closes, not 15:00 quotes; no bid-ask (the Rs 1 pad is an assumption until calibrated from A4 quotes).
- 60 challenge opportunities: a real but small edge may fail criterion 2.
- F1's 10-contract floor removes F1 on 10 of the 59 challenge decision days counted for response 48 (8 at today's
  "any volume" rule); on those days P4-P6 and P8 do not trade and P5 does nothing.
- 2019-2023 had different lot sizes and charges; today's lot and charges are applied to every opportunity.
- The policies were chosen after seeing 2024-2026 (meeting 1); that is why the challenge period decides.

## 12. Version history
- **1** (12 Oct 2026): reviewed in ChatGPT review 12; answered in `reviews/claude/response_15_...`.
- **2.1** (12 Oct 2026): agreed in ChatGPT review 14.
- **2.2** (13 Oct 2026): agreed in ChatGPT review 28 section 1 (response 55 proposal, response 60 check). Changes:
  monthly identity from listed NIFTY futures, no 50-day rule (section 3; response 48 item 0, response 45 section 8);
  F1 on Black-76 with the same-expiry future and a 10-contract floor on the thinner ATM leg (section 5); C1's
  nearest-rank 95th percentile, index 9,499 (section 8); the exact random draws and the numpy version (sections 6-7);
  period by decision day, P&L year by exit day (section 2); drawdown, losing-run and win-rate definitions (section 7);
  P6's empty removed set fails, F2's 2017-18 warm-up (sections 5, 8); the freeze recipe (section 10); a long debit at
  least the width is `bad_prices`, exit-bound anomalies report only (section 4); the engine conventions judged in
  story B2 written in (strikes from the entry day, muhurat sessions, the no-trade status, worst-case exit charges,
  windows opened before the panel); the reader revision of 30 Mar 2021 and the access record since 2.1 (section 10).
  Then, after ChatGPT review 29 section 1 (response 63): G1's golden-file disclosure in review 29's words, its
  commit and SHA-256, the order against the rule-setting commits, the hard rule until the run, and the final-report
  label (section 10).
