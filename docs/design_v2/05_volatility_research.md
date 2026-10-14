# 5. The forecasting and volatility research programme

## 5.1 Why movement size, and what that can and cannot give

- **Volatility clusters and is forecastable** (strong evidence: Engle 1982, Bollerslev 1986, Corsi 2009's HAR model,
  and decades of replications; our own G2 HAR baseline uses it).
- **Implied volatility is usually above later realised volatility** (the variance risk premium; strong evidence:
  Carr and Wu 2009, Bollerslev, Tauchen and Zhou 2009; ours: ATM implied above trailing 20-day realised on 74% of
  2019-23 and 82% of 2024-26 monthly entries, median about 2 points, response 92).
- **Implied volatility is a strong forecast in its own right** (strong evidence: Christensen and Prabhala 1998; the
  Poon and Granger 2003 review finds it often the best single forecast). So beating the market's number is hard,
  and beating a random walk alone says little. Neither is the same as making money: a good physical-variance forecast
  can fail to trade profitably, and the reverse (ChatGPT review 95, accepted). Money is judged only by shadow and paper
  results after costs (rung 2 and above).
- **Intraday data measures volatility far better than daily closes** (strong evidence: Andersen, Bollerslev, Diebold
  and Labys 2003). This is why 15-minute quotes (A16) come first in layer 1.
- **Daily direction is close to a coin toss** (strong evidence: our Q1 base rates and desk 1's trend trials at 50-52%).
  Direction stays forecast and scored (G1 Q1); no trade may rest on it until it beats its baseline.

**What it can give us (reasoning only):** knowing when the premium is unusually large or small relative to a good
forecast, and only acting when the gap is larger than the costs. **What it cannot give:** a forecast that is right most
days in a way that pays after costs, unless the gap is large and the structure is cheap to trade.

## 5.2 Targets: protocol v4 (new version; G1 v3 stays frozen and keeps running)

Realised variance of a session `RV_s` = squared overnight log return (previous close to 09:15) plus the sum of squared
15-minute log returns 09:15-15:30 (A16). Before A16 has history, the close-to-close squared return stands in, labelled
`close_proxy` (far noisier).

| Id | Question | Type | Independent outcomes a year | Starts |
|---|---|---|---|---|
| V1 | NIFTY realised variance of the next session | point forecast | about 250 | when A16 has 20 sessions |
| V2 | NIFTY realised variance over the next 5 sessions | point forecast | about 50 | now (close proxy), then intraday |
| V3 | NIFTY realised variance over the next 20 sessions | point forecast | about 12 | now (matches Q3, Q5) |
| V4 | P(next-5-session realised volatility < 15:00 ATM implied volatility of the nearest weekly expiry at least 5 sessions out) | probability (diagnostic) | about 50 | when A16 records weekly ATM quotes |
| V5 | P(NIFTY's close at the nearest monthly expiry lies inside K +/- P, with K and P fixed at 15:00 on d) | probability (terminal intrinsic proxy) | about 12 | now (A4 quotes) |
| V6 | P(next-session absolute move at least 2%), P(largest absolute move over 5 sessions at least 2%) | probability | about 250 / 50 | now (the weather, section 2.3) |
| V7 | P(India VIX higher in 5 sessions) | probability | about 50 | now |

**V4, exact terms (frozen in G6).** Realised volatility over the 5 sessions includes the overnight returns (section
5.2's `RV_s`), annualised on 252 sessions. The implied side is converted to the same clock: implied variance x
(calendar days to expiry / 365) / (sessions to expiry / 252). ATM is the listed strike nearest the 15:00 spot (a tie
goes to the lower strike, as G1); both legs need a live bid and ask at 15:00 with a spread no wider than a frozen
limit, priced at mid; otherwise the day is void. V4 is a **probabilistic diagnostic**: the variance risk premium is a
difference of expected variances, and `P(RV < IV)` does not estimate it.

**V5, exact terms.** K is the listed strike nearest the 15:00 spot; P is the 15:00 mid of the K call plus the K put of
the nearest monthly expiry; both frozen at 15:00 on d. V5 is a **terminal intrinsic-payoff proxy**: "inside K +/- P"
means a buyer who held to expiry lost before costs, but "outside" does not mean the buyer won (charges, pads and the
actual fill decide that), and holding to expiry is outside the owner's preferred 2-3 week horizon. **V5 is not evidence
of money.** A straddle is also above the Rs 10,000 cap (5.6), so its cost-adjusted shadow result is a measurement
only, reported apart. V1 and V6 carry most of the statistical power because their outcomes do not overlap. Stock
options around results get their own protocol (R2).

## 5.3 Baselines (frozen with v4, built like G2)

- **Trailing:** the matching past window's realised variance (random walk), and RiskMetrics EWMA (lambda 0.94).
- **HAR:** G2's HAR-type model on daily, then on intraday realised variance. A forward-only intraday history is short:
  HAR on intraday data needs at least 250 sessions before it forecasts (G2 uses 500-750 on daily data), so it starts
  about a year after A16 goes live. Said plainly: the best intraday model arrives late.
- **Raw implied:** IV30 squared, scaled to the horizon.
- **Premium-adjusted implied:** raw implied times a fixed ratio (median realised over implied over the trailing 750
  sessions, point in time, refitted monthly like G2), which removes the average premium.
- **Option-implied probability (for V5):** the probability of ending inside K +/- P under a lognormal with the expiry's
  own ATM implied volatility and carry, computed as G1's baseline (a); labelled "risk-neutral, not a real-world
  probability".
- **Base rate:** for every probability question, as G2 (b).

**Primary baselines, declared now, before any v4 score:**

| Question | Primary baseline | Also reported |
|---|---|---|
| V1 | HAR (daily, then intraday once it forecasts) | trailing, EWMA, premium-adjusted implied |
| V2, V3 | premium-adjusted implied | raw implied, HAR, trailing, EWMA |
| V4, V6, V7 | base rate | none |
| V5 | option-implied probability (Brier) | base rate |

Why premium-adjusted implied is primary for V2 and V3: it is the predeclared physical-variance benchmark because raw
implied includes a risk premium (strong evidence, 5.1); superiority is not assumed (the trailing ratio adds its own
estimation noise), and both are scored. Choosing between them on 2019-26 outcomes would expose v4's targets before its
freeze (ChatGPT review 96, wording accepted). V5's baseline is a
probability scored by Brier, never IV squared (ChatGPT review 95, accepted).

## 5.4 Scoring

- **Point variance forecasts:** QLIKE loss, `RV / f - ln(RV / f) - 1`, primary (strong evidence that it ranks forecasts
  correctly with a noisy realised measure: Patton 2011); mean squared error on variance secondary; the Mincer-Zarnowitz
  regression `RV = a + b f` reported for bias.
- **QLIKE floor (frozen in G6).** Forecasts must be strictly positive. Realised variance is floored at 1% of the
  trailing 250-session median of the same measure: `RV' = max(RV, floor)`. Measured on NIFTY closes 2017-2026 (2,424
  returns): 2 exact zero-return days (31 Mar 2017, 8 May 2024), and the floor binds on 6.1% of close-proxy one-day
  outcomes (132 of 2,174). That is why close-proxy V1 is a diagnostic only and V1 proper uses intraday variance; 5-day
  sums never reached zero (smallest 4.6e-6).
- **Probabilities:** Brier primary (as G1), log score, the 10-bin reliability table, the calibration slope and
  intercept, and the Brier skill score against the base rate.
- Missing forecasts are counted, never imputed; void rules as G1 section 2.

## 5.5 What "beats the baseline" means, statistically

1. **Pre-registered family** per protocol version: each question's primary comparison for each registered forecaster.
2. **Statistic:** the mean paired loss difference `D`, from `d_t = loss(forecaster) - loss(baseline)` on dates both
   forecast and the outcome resolved and not void, in date order (a Diebold-Mariano comparison); negative favours the
   forecaster. One-sided. Missing pairs are dropped and counted; a zero difference stays in.
3. **Uncertainty: null-centred moving-block bootstrap.** Block length L at least the horizon and never below 5
   sessions (V1 and V6: 5; V2, V4, V7: 10; V3, V5: 20). For n pairs, draw ceil(n / L) block starts uniformly from 0 to
   n - L with replacement, join in draw order, cut to n, take the mean `D*_b`; B = 10,000, seeded per comparison as G1.
   One-sided p = (1 + #{b : D*_b - D <= D}) / (B + 1), the resampled means centred on the observed mean (the null).
   Fewer than 2L pairs: not tested, p = 1. (G1 v3's frozen code is the two-sided version of the same centring,
   `|D*_b - D| >= |D|`; v3 is not changed.) A HAC t-test (Newey-West, lag L - 1) is reported beside it as a
   predeclared sensitivity and never used to choose a result. For the 20-day questions neither method creates
   independent evidence.
4. **Significance:** Holm's step-down across the family at 5% family-wise.
5. **Minimum forecast effect, registered:** at least a 3% lower mean QLIKE than the primary baseline, or a Brier skill
   score of at least 0.02 (reasoning only for both numbers; accepted by the owner on 15 Oct 2026, also as the stop
   rule's futility margin). These are minimum **forecast** effects only, never evidence of money. A significant but
   smaller gain is "real but too small to use".
6. **Stability:** the sign of the gain is the same in the first and second half of the scored period (descriptive).
7. **Economic check:** skill counts for trading only through a mapping registered before scoring: each factory idea that
   rests on a forecast names how the forecast turns into a position, and its shadow net after costs (rung 2) is the
   only evidence of money.

**How long it takes (arithmetic, strong evidence).** The test uses Holm across the family. Planning must use Holm's
first and strictest step, alpha / m, because a first claim has to pass it. With m of about 15 primary comparisons (G6
fixes m), that is one-sided 0.05 / 15 = 0.0033 (z = 2.71); with 80% power (z = 0.84), n = (3.55 x r)^2 independent
outcomes, where r is the SD of `d_t` divided by the registered effect.

| r | n | Daily question (V1, V6 one-day: about 250 a year) | 5-day question (about 50 a year) | 20-day question (about 12 a year) |
|---|---|---|---|---|
| 3 | 114 | about 5.5 months | about 2.3 years | about 9 years |
| 5 | 316 | about 15 months | about 6.3 years | about 26 years |
| 10 | 1,264 | about 5 years | about 25 years | about 105 years |

r is unknown until measured: no question is known to settle in months. V1 also waits for A16 and its host, and its
best model (HAR on intraday data) for about 250 sessions of A16 history; V6's one-day question can start now on daily
closes. **Rule:** after 60 scored outcomes of a question, the statistician measures r and publishes the projected
settle date; if it is beyond 2 years, the card and the owner are told plainly that this question cannot be settled in
useful time. The same projection decides the stop rule's "undecided" result (section 8.2).

## 5.6 How the Rs 10,000 cap shapes what a volatility view can trade (arithmetic, Black-Scholes approximation)

At NIFTY's real 15:00 level on 14 Oct 2026 (about 22,620, C3's first capture), ATM implied volatility 13.8%
(response 92) and lot 65:
- A 30-day ATM straddle costs about 0.8 x 22,620 x 0.138 x sqrt(30/365) = about Rs 716 a unit, **about Rs 46,500 a
  lot**.
- A weekly (5-day) ATM straddle costs about Rs 292 a unit, **about Rs 19,000 a lot**.
Both exceed the Rs 10,000 maximum loss. So a "buy movement" view can only be expressed with debit spreads,
butterflies or far strangles, and a "sell movement" view only with protected structures (as tested). These have small
vega, so the volatility edge needed to cover costs is larger than for a straddle. Every V-idea's card must show its
vega per lot and the edge in volatility points needed to cover full costs, computed by the cost wall.

## 5.7 Anti-overfitting rules (all binding on every forecaster and idea)

1. Registered before read: protocol hash and ledger row before any outcome is computed (B4 enforces).
2. One test per version; a fail is final; a variant is a new row.
3. Spent data (`research/DATA_SPEND.md`) gives exploratory results only, never a pass.
4. Forward is the default test; history only where it is fresh.
5. Simple first: a rule forecaster fits at most 5 parameters, only on rolling past windows that end before the cutoff;
   anything larger must beat the simple model by the registered margin and name its economic reason.
6. Point in time: inputs only from rows with `first_seen_at` before the cutoff.
7. Holm within a family; the factory's trial count and expected false passes on every report.
8. Minimum effect sizes registered, not only p-values.
9. Crash replays (2020, 2024) are stress tests of the worst case, never evidence of an edge: that history is seen.
10. Every number with its interval; no point estimate alone.
11. No stopping on results: tests run to their registered sample or date (safety stops excepted).
12. AI forecasters stay sealed from outcomes and from each other (F1, owner's 14 Oct conditions); prompts versioned.
13. The judge checks every freeze and every result (lane 1).

## 5.8 Drift detection (proposal; owner decides the numbers)

- **Forecasters:** a one-sided CUSUM on `z_t = d_t / s`, where `s` is the SD of `d_t` over the forecaster's first 60
  scored non-overlapping outcomes: `S_t = max(0, S_(t-1) + z_t - 0.5)`, alarm at `S_t > 5` (about 900 outcomes between
  false alarms for independent normal data; fewer with dependence). Used on V1 and V6 daily and on every 5th day of V2.
- **Strategies:** the same on per-trade net standardised by the registered SD around the registered expected net,
  alarm at 4 (about 340 trades between false alarms). It pauses new entries until the owner reviews.
- **Honest limit:** a monthly strategy gives 12 trades a year, so drift detection reacts in years. The decided
  catastrophic-loss rules (S1, Rs 10,000 per trade and Rs 30,000 cumulative) act much faster and stay the first line.
- **Conflict to settle:** S1's draft `immediate_pauses` allows no statistical pause before a scheduled review. The drift
  pause is one, accepted by the owner as a missing piece on 14 Oct. S1 must list it as a named exception (`REPLAN.md`
  section 4).
