# Forecast protocol, version 1 (story G1)

**Status: version 1, frozen.** Written by Claude on 13 Oct 2026 (review request:
`reviews/claude/response_57_g1-protocol-for-review.md`). ChatGPT review 28 (section 2) gave "CHANGE before freeze:
(1) and (2); everything else can remain"; both changes (question 5 void on flagged IV30 days; a 10-test primary family)
are in sections 2, 3, 4, 7 and 8, accepted by the orchestrator in `reviews/claude/response_60_2026-10-13-on-review-28.md`,
and judge 47's round 2 accepted the golden-value freeze. The commit that adds this text is the protocol commit;
`research/forecasts/FREEZE.md` records it (section 10). No forecast existed at the freeze. Any change from here is a new
version (a new file and a new freeze), never an edit. Design: `docs/DESK_DESIGN.md` 12.7 (daily forecasts, a secondary
diagnostic), 12.8, 12.11. Registered in the research ledger as trials 32-36 (one per question), which carry the
protocol commit.

**Standing.** Trade profit decides. Forecast scores only diagnose market reading and can never promote a book that
does not make net money (design 12.7). Every report that shows them says so.

## 1. Who forecasts, when, with what

- **Forecasters:** the three books (`book1_rules`, `book2_hybrid`, `book3_ai`) and three baselines (section 4). Each
  answers the five questions on every trading day with a probability in [0, 1], or records "no forecast" (never
  imputed; a missing forecast is not scored and is counted in every report).
- **Forecast day `d`:** a trading day (section 2). **Cutoff:** 15:00 IST on `d`, the desk's decision time.
- **Inputs, live:** only the common market pack (story E2) frozen at the cutoff; its SHA-256 is in every record.
  Until E2 exists there are no live forecasts.
- **Inputs, history (back-fill for evaluation and for the baselines' windows):** the NIFTY panel and index closes
  (story A3) of `d` and earlier. They are close-proxy values (15:30) for a 15:00 decision: history results are labelled
  "close proxy". `pack_sha256` is then the SHA-256 of the panel manifest.
- A forecast committed after its deadline (story G3) is ignored.

## 2. The five questions and their exact targets

Reference code: `fno/forecast/targets.py` (`ForecastTargets`); question names in `fno/constants.py`.

- **Trading days:** the sessions of the NSE session calendar (`research/data/calendar/nse_sessions.csv`, story A7),
  muhurat sessions left out (as story B1). Holidays are skipped; special weekend sessions count. "In n trading days" is
  the n-th trading day after `d`.
- **Closes:** NIFTY 50 and India VIX closes from NSE's index-close files (story A3).
- **Realised volatility (RV):** story B1's: root mean square of 20 daily log returns, not demeaned, times sqrt(252),
  in volatility points. **Trailing RV(d):** the 20 returns ending at `d`'s close (closes `d-20` to `d`). **Next
  RV(d):** the 20 returns from `d`'s close to the close 20 trading days later (closes `d` to `d+20`).
- **Void:** an outcome is void (never scored) when the target day is beyond the calendar or the data, or any close it
  needs is missing. Ties count as "no" (all comparisons are strict, except question 2's "at least").

| # | Name | Question | Outcome is 1 when |
|---|---|---|---|
| 1 | `q1_nifty_up_20d` | P(NIFTY close in 20 trading days > today's close) | close(d+20) > close(d) |
| 2 | `q2_nifty_move_3pct_20d` | P(abs NIFTY return over the next 20 trading days >= 3%) | abs(close(d+20) / close(d) - 1) >= 0.03 (simple return) |
| 3 | `q3_rv20_above_trailing` | P(next-20-day RV > trailing 20-day RV today) | next RV(d) > trailing RV(d) |
| 4 | `q4_vix_up_10d` | P(India VIX close in 10 trading days > today's close) | VIX(d+10) > VIX(d) |
| 5 | `q5_rv20_below_atm_iv30` | P(next-20-day RV < today's 30-day ATM implied volatility) | next RV(d) < IV30(d) (section 3); **void when IV30(d) is flagged or missing** |

## 3. The 30-day at-the-money implied volatility, IV30(d)

Reference code: `fno/forecast/iv30.py`.
- **Monthly expiries:** the expiries of the NIFTY futures listed on `d` (story A5's rule: NSE lists index futures only
  on monthly contracts).
- **Each expiry's ATM IV:** story B1's `atm_implied_vol_points`: the listed strike nearest the spot (a tie goes to the
  lower strike); the call and the put at that strike must both have traded (volume > 0; settlement prices are never
  used); each implied volatility by B1's Black-76 on that expiry's traded future close, rate 6.5% (`config.yaml`
  `risk_free_rate`) only discounting, solver bounds 1% to 200% (a solution at a bound is a failure); the ATM IV is the
  mean of the two. Any failure means no value for that expiry. One implementation, shared with B1 and C2.
- **Interpolation:** the two monthly expiries bracketing 30 calendar days, `e1` (the latest with 1 to 30 days left) and
  `e2` (the earliest with 30 or more), in total variance:
  `w_i = IV_i^2 x days_i`, `w30 = w1 + (w2 - w1) x (30 - days1) / (days2 - days1)`, `IV30 = sqrt(w30 / 30)`.
- **Not bracketed** (no `e1` or no `e2`, or either ATM IV missing): the monthly expiry with at least 7 days left whose
  days are nearest 30 (a tie goes to the longer one), alone, **flagged**. None such: no value.
- **Question 5 uses interpolated IV30 only** (ChatGPT review 28): a single expiry is an approximation of 30-day IV, and
  the flagged days cluster in 2019-2020, so mixing them would mix estimator error with forecast skill. On a flagged or
  missing day question 5's primary outcome is void (never scored or tested); on flagged days the same comparison is
  kept as a separate descriptive sensitivity (`ForecastTargets.rv_below_iv_flagged`), never in a confirmatory test.
  The flag stays in every record of IV30 and in the golden file, and the flag rate of each scored period is reported.
- **How often (measured on the panel, 2019 to 12 Oct 2026, 1,922 trading days):** 1,662 interpolated, 258 flagged
  (13%), 2 without a value. Flagged days are mostly 2019-2020 (84 and 80 a year), where the next month's ATM call or put
  often did not trade; 11 to 23 a year from 2021. Flagged days are void for question 5's primary score (above).
- **Sanity check, not a target:** on 1 Sep, 15 Sep, 29 Sep, 1 Oct and 12 Oct 2026 IV30 was 10.09, 12.79, 12.90, 13.83 and
  14.46 against India VIX 11.49, 13.43, 13.41, 14.46 and 15.25. VIX prices the whole smile, so it sits above ATM.

## 4. Baselines (story G2 builds them exactly as written here)

All point-in-time: nothing known after the cutoff of `d` is used. Each value is labelled with its method and version
(`baseline_a_risk_neutral/v1` and so on).

**(a) Risk-neutral, questions 1 and 2 only.** Labelled "risk-neutral: option prices include risk premia; not a
real-world probability". Lognormal: `ln(S_T / S_0)` is normal with mean `m = ln(F_T / S_0) - s^2 tau / 2` and variance
`s^2 tau`, where `S_0` is NIFTY at the cutoff, `s = IV30(d) / 100` (flagged values used, the flag carried, and questions 1-2 reported split into flagged and unflagged days), `tau` =
calendar days from `d` to `d+20` / 365, and `F_T = S_0 x exp(c x tau)` with the carry `c = ln(F_1 / S_0) / tau_1` from
the traded close `F_1` of the first expiry IV30 used (`tau_1` its calendar days / 365).
Q1 = `N((ln(F_T/S_0) - s^2 tau/2) / (s sqrt(tau)))`;
Q2 = `1 - N((ln 1.03 - m) / (s sqrt(tau))) + N((ln 0.97 - m) / (s sqrt(tau)))`.
Breeden-Litzenberger on call prices was considered and not used (reasoning only): closes of sparse and often untraded
far strikes would make the smoothing choice decide the answer. Questions 3-5: "no risk-neutral equivalent" (India
VIX options are not in the data; question 5's IV is already the market's price).

**(b) Base rate, all questions.** The share of outcomes equal to 1 among the most recent 750 trading days `t < d`
whose outcome was resolved before the cutoff of `d` (its last close is on a day before `d`) and not void (question 5
uses IV30(t), so its flagged days are void here too). At least 500 such days, else no forecast.

**(c) Simple statistical models, questions 3, 4 and 5.** Ordinary least squares with an intercept, fitted on the same
kind of window as (b): the most recent 750 trading days `t` before the refit day whose target was resolved before the
refit day's cutoff, at least 500 rows (else no forecast until a refit has enough). **Refit schedule:** on the first
trading day of each calendar month; coefficients and residuals stay fixed until the next refit. Probabilities come
from the fit's own residuals `e` (their empirical distribution), never from a normal assumption:
- **Q3 and Q5 (HAR-type):** `y_t = ln next RV(t)`; regressors `ln RV5(t)`, `ln RV20(t)`, `ln RV60(t)` (B1's realised
  volatility over the 5, 20 and 60 returns ending at `t`). With the prediction `y_hat` for `d`: Q3 = share of
  residuals with `y_hat + e > ln trailing RV(d)`; Q5 = share with `y_hat + e < ln IV30(d)`.
- **Q4 (VIX mean reversion):** `y_t = ln(VIX(t+10) / VIX(t))`; regressor `ln VIX(t)` minus the mean of `ln VIX` over the
  250 trading days ending at `t`. Q4 = share of residuals with `y_hat + e > 0`.
A missing regressor on `d` means no forecast that day.

## 5. Book 1's method (story G3)

For each question, the mean of the available baselines' probabilities: questions 1 and 2 from (a) and (b), questions
3-5 from (b) and (c). One available: that one. None: "no forecast". Version `book1/v1`; the hash of the method file is in
every record (story G3). Book 1 never refits on outcomes: the baselines' frozen windows and schedule are its only
learning. Books 2 and 3 forecast through their own sessions (story G5) with the same inputs and cutoff.

## 6. The record (`fno/forecast/schema.py`)

`book, date, cutoff, question, probability, method_or_version, pack_sha256`; `book` is a book or a baseline; `cutoff`
carries its time zone and falls on `date` in IST; `probability` in [0, 1] or empty for "no forecast"; `pack_sha256` is
64 lowercase hex characters (section 1).

## 7. Scoring (story G4 builds it exactly as written here)

- A forecast is scored only when its outcome is resolved and not void; never earlier.
- **Brier score** `(p - o)^2` for every question; lower is better.
- **Log score** `-ln(p')` if `o = 1`, `-ln(1 - p')` if `o = 0`, with `p' = min(max(p, 0.01), 0.99)`.
- **Calibration table** per forecaster and question: 10 bins `[0, 0.1)`, `[0.1, 0.2)`, ..., `[0.9, 1.0]`; per bin the
  count, mean forecast and observed frequency.
- Reported per forecaster and question: count of forecasts, of "no forecast", of void outcomes; mean Brier, mean log
  score, calibration. **Question 5:** its primary score uses interpolated IV30 days only (flagged and missing days are
  void, section 2); the same scores on flagged days are reported beside it as a descriptive sensitivity, with the flag
  rate of the period. **Baseline (a):** questions 1 and 2 also reported split into flagged and unflagged IV30 days.

## 8. Comparisons and the multiplicity adjustment (fixed before any score exists; ChatGPT review 28)

- **Primary (confirmatory) family: 10 tests.** For each question, Book 2 against Book 1 and Book 3 against Book 1: does
  AI judgement inside the rules, and then the full AI system, read the market better than the rules alone? Comparison
  `k` (1 to 10) is numbered question 1 to 5, each with Book 2 vs Book 1 first, then Book 3 vs Book 1. A comparison not
  yet possible (the AI books do not exist yet) stays in the family with p = 1, so the adjustment never weakens.
- **Statistic:** on the dates where both forecasters gave a probability and the outcome is resolved and not void, in
  date order, `D_t = Brier_A(t) - Brier_B(t)` (A is Book 2 or 3, B is Book 1); the statistic is their mean `D`.
  Negative favours A.
- **Uncertainty: moving-block bootstrap**, block length L = 20 trading days (the targets overlap), B = 10,000
  resamples. For `n` paired dates: draw `ceil(n / L)` block starts uniformly from `0 .. n - L` with replacement, join
  the blocks in draw order, cut to `n` values, take the mean. Random numbers: NumPy
  `default_rng(SeedSequence([20261013, k]))` for comparison `k`, so each comparison reproduces exactly on its own.
  The families and these constants are in code: `fno/forecast/comparisons.py`.
- **p-value (two-sided):** `p = (1 + #{b : |D*_b - D| >= |D|}) / (B + 1)` (the bootstrap distribution centred on the
  observed mean). Fewer than 40 paired dates (2L): not tested, p = 1, "too few dates".
- **Adjustment: Holm's step-down** over the 10 primary p-values at a family-wise error rate of 5%: sort ascending,
  `p_(i)` is significant while `p_(i) <= 0.05 / (10 - i + 1)`; the first that fails stops it.
- **Secondary (descriptive only):** Book 2 against Book 3, and every book against each of the question's two baselines
  (questions 1-2: (a) and (b); questions 3-5: (b) and (c)), numbered 11 to 45 after the primary family; also every log
  score and calibration table, and question 5 on flagged IV30 days (section 3). They are reported as effect sizes
  (`D`) with unadjusted 95% bootstrap intervals (same method and seeding), and never called confirmatory.
- **Intervals:** the 2.5% and 97.5% percentiles of `D*_b`, labelled "unadjusted 95%".
- **Timing:** no comparison is called significant before the first scheduled review (design 12.8: 6 months of
  common-start trading); before it, every number is descriptive. Six months is a first review, not a deadline to pick a
  winner: about 125 daily forecasts on 20-day overlapping targets hold only about 6 independent 20-day spans, so a
  "no significant difference" then means "not yet known", and the comparison continues.

## 9. Known limits (stated before any forecast)

- History values are close proxies for a 15:00 cutoff (section 1).
- IV30 is flagged on 13% of history days, a third of 2019-2020 (section 3).
- The base rate and the models need 750 earlier resolved days (at least 500 to forecast). With the 2017-2018 warm-up
  closes (story A10) questions 1-4 can be back-filled from about 2020; question 5 needs IV30, which starts with the
  panel in 2019, so from about 2021 (500 days) or 2022 (750).
- Overlapping targets make neighbouring days' outcomes dependent; the block bootstrap handles this, a plain average's
  error would not.
- The protocol's thresholds (3%, 20 and 10 days, the windows) come from design 12.7 and the story, not from data.

## 10. The freeze (after agreement): behaviour, not library bytes

- `research/forecasts/FREEZE.md` names the protocol commit and the SHA-256 of: this file, the forecast code
  (`fno/forecast/*.py`) and the golden file `research/forecasts/golden_iv30_rv20.csv`. Story G4 refuses to score unless
  the freeze is in the history of the scored forecast's commit (`fno.forecast.freeze.require_frozen_before`).
- **Golden values:** for every panel trading day from 2019, IV30 (value, flag, expiries) and trailing RV20, both known at
  the forecast date (not outcomes). `tests/forecast/test_golden.py` recomputes them with the current code and requires
  equality within 1e-12 points; the hand-worked fixture values (IV30 14.4937 and 13.0 flagged; RV 15.8745 and
  34.0470; the holiday and muhurat window) are checked in the same way by their tests.
- **The shared library is recorded, not byte-checked:** B1's `implied_vol.py`, `volatility_features.py` and
  `close_series.py`, the calendar reader and `config.yaml` may be refactored or fixed freely as long as every golden
  value stays equal. A change to any golden value fails the test and needs a new protocol version.
- **A panel revision** (story A11) that changes a past day's inputs moves that day's golden values legitimately; the
  regenerated golden file (`python tools/forecast_golden.py --write`) is committed with the A11 revision that explains
  each changed day, and the freeze record is amended only for that file's hash, citing the revision.

## 11. Access attestation (what was looked at before the freeze, and why)

- **30-day ATM IV and trailing RV20 on the panel, 2019 to 12 Oct 2026:** counted interpolated, flagged and missing IV30
  days per year, read five IV30 values (1 Sep to 12 Oct 2026) against India VIX, and wrote the golden file (section
  10). These are inputs known at the forecast date, not outcomes. No outcome of any question was computed on real
  data; the targets were tested on fixture data only.
- **Earlier work that touches the questions:** desk meeting 1 (12 Oct 2026, ledger trials 2-4) measured NIFTY
  2024-2026 5/10/20-day direction persistence (50-52% same direction), related to question 1; story B1 measured F1
  (ATM IV minus trailing 20-day RV) on 2024-2026 decision days, related to questions 3 and 5. The baselines' and Book
  1's methods come from design 12.7 and the stories, not from these results.
- Any further access before the freeze is added here with its reason.
