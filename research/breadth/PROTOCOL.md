# Breadth protocol of BR1 (story BR1a)

Protocol version: 1

**Status: DRAFT, not frozen. Claims are POSTPONED.** Study 3 found no per-look rate at which the frozen test keeps
its false-claim limits on the real null (`studies/results/study3.json`). By the rule written before the run, BR1
reports descriptively until a new protocol version. Every item below is a proposal until the owner decides it item by
item. BR1 freezes only after BR1b-BR1e exist (`python -m fno evaluation freeze --protocol breadth`). Builder: Claude,
16 Oct 2026, branch `story/br1a-protocol`.

How to read an item: the same as S1's protocol (`research/evaluation/PROTOCOL.md`). **Value** is the exact value or
rule; **Status** is "proposal, owner decides" until the owner decides it; **Reason** says why; **Evidence** is strong
evidence, some evidence, or reasoning only. `python -m fno evaluation check --protocol breadth` checks it.

## How to read BR1's numbers (owner, 16 Oct 2026)

- Breadth is the measured **range of 6 to 42** effective independent bets a day, depending on the forecaster pair.
  **About 9** is only the common-tilt planning case.
- The month estimates are normal-approximation **planning projections, never deadlines**.
- Whether any forecaster beats the frozen primary baseline by 2-3% is unknown.
- The 1.15 volatility tilt is a planning case: on 2024-2026 it **lost** to `cal60` (t -8.06).

## Items

### `universe` Underlyings scored
- **Value:** every F&O underlying with a traded ATM straddle on at least 48 of the last 60 sessions (80%) and at
  least 60 resolved outcomes. Names enter and leave NSE's F&O list by this rule; a delisted name stays scored to its
  last session.
- **Status:** proposal, owner decides
- **Reason:** a baseline needs 60 outcomes of history, and a name without a traded straddle has no implied move.
- **Evidence:** reasoning only

### `target` T1 target
- **Value:** Y(u, t) = 1 when |ln(S(t+1) / S(t))| is at least the ATM-straddle implied daily move of t, the move
  being straddle / (S x sqrt(2 / pi) x sqrt(n)), with n the NSE trading days to expiry (calendar A7). S is NSE's
  `UndrlygPric`; in the old file format (to 2024-07-05) the near-month future's close, the same contract on t and
  t+1.
- **Status:** proposal, owner decides
- **Reason:** a yes or no question every name answers every day, scored by Brier, with a market-implied reference.
- **Evidence:** some evidence

### `outcome_exclusion` Corporate-action screen
- **Value:** outcome-side only. A (u, t) pair is not scored when fewer than half of u's listed strikes on t, for an
  expiry listed on both days, are still listed on t+1. The flag is read from t+1's file, so it never reaches a
  forecaster, a pack or a feature, and it applies to every family and baseline alike. Every report states the count
  excluded by year (2024: 45 name-days, 2025: 46) and the days where NSE's corporate-action list (archived from Oct
  2026) disagrees. Dividends below NSE's adjustment threshold stay in the target; their effect is reported, never
  adjusted. Known limit: an adjustment keeping more than half of the strikes escapes the screen (none seen in
  2024-2026).
- **Status:** proposal, owner decides
- **Reason:** a split or demerger is not a move; real crashes keep their strikes and stay scored.
- **Evidence:** some evidence

### `forecast_time` Forecast time
- **Value:** end of day. The forecast for t uses data up to t's close and is committed before 09:15 IST on t+1. The
  14:30 version is descriptive only.
- **Status:** proposal, owner decides
- **Reason:** the bhavcopy closes are the data every family has; one time keeps K at 3.
- **Evidence:** reasoning only

### `families` Forecaster families
- **Value:** rule (code only); hybrid (rules proposed by AI, applied by code, the rule set frozen at the freeze); AI
  (direct probabilities on a fixed 30-name subset chosen by option turnover at the freeze). Rule and hybrid are scored
  on all names and on the AI's 30.
- **Status:** proposal, owner decides
- **Reason:** one confirmatory member per way of forecasting; the AI subset bounds its cost.
- **Evidence:** reasoning only

### `baselines` Registered baselines
- **Value:** `market` (p = 0.3173, the implied move at face value); `trail60` (the 60-session frequency of Y);
  `cal60` (the implied move scaled by the trailing 60-outcome realised-to-implied ratio k = mean(|r| / m) /
  sqrt(2 / pi), p = 2(1 - Phi(1 / k))). Formulas as in `research/2026-10-15-breadth-sizing/sizing.py`.
- **Status:** proposal, owner decides
- **Reason:** the three simple references any skill must beat; none needs a fitted model.
- **Evidence:** some evidence

### `primary_baseline_rule` Primary baseline
- **Value:** the registered baseline with the lowest mean Brier over every scored (u, t) of the study window is the
  primary; a tie at 4 decimals goes to the earlier one in `baselines`. Study 1's agreement was 96.0% (22,364 of
  23,296), below 97%, so the window is 2024-01-01 to 2025-12-31 and the window applies to the inputs too: no old
  format row enters any baseline, and the first 60 sessions of 2024 are history only. Result, recorded and never
  revisited: **`trail60`**, mean Brier 0.1924 (`cal60` 0.1931, `market` 0.1941), 84,189 scored pairs.
- **Status:** proposal, owner decides
- **Reason:** one primary fixed before any family exists, so a claim cannot pick its easiest opponent.
- **Evidence:** some evidence

### `claim_meaning` What a claim means
- **Value:** the only confirmatory claim is "family F beats the primary baseline on T1, end of day". Against the
  other two baselines each family's paired mean difference and its 95% interval are reported, labelled descriptive. A
  result is never worded as a win over every baseline, and never as a trading or real-money result. A descriptive
  loss to a non-primary baseline is shown as a caution, never as proven inferiority.
- **Status:** proposal, owner decides
- **Reason:** ChatGPT review 116 Q3 and the owner (16 Oct): one claim, one meaning.
- **Evidence:** reasoning only

### `confirmatory_family` Confirmatory family
- **Value:** K = 3, one member per family against the primary. T2, direction targets, the residual target and the
  14:30 version are descriptive only.
- **Status:** proposal, owner decides
- **Reason:** K = 12 adds about 30% to the sessions needed.
- **Evidence:** some evidence

### `test` The test
- **Value:** for each member, the daily series d_t = the mean over names of (Brier of the family minus Brier of the
  primary), v4's sign: negative favours the family. p is `confirmatory_test(d, block=5, k)`, one-sided: the larger
  of the batch-means p and the studentized-bootstrap p. Holm over the 3 members at the rate in `looks`. A member is
  judged only with at least 12 whole blocks. v4's `calibrated_p` thresholds and NIFTY gates are not used.
- **Status:** proposal, owner decides
- **Reason:** G8's frozen test, reused; the rate comes from study 3, not assumed.
- **Evidence:** reasoning only

### `minimum_effect` Minimum effect
- **Value:** a 2% lower mean Brier than the primary's: δ = 0.02 x 0.1924 = 0.0038 in Brier units, the one δ used
  everywhere. A planning value, not evidence of a reachable skill.
- **Status:** proposal, owner decides
- **Reason:** the size of the gaps between the simple baselines themselves (0.5-2.5%).
- **Evidence:** reasoning only

### `looks` Looks and rate
- **Value:** none: claims are postponed. Study 3's single loop tried 0.02, 0.015, 0.01 and 0.005 per look (look
  counts 248/495, 263/526, 285/569, 321/642 sessions); at every rate the sign-flipped null (-d) on the whole window
  passed the limits of 0.025 per look and 0.045 at either (at 0.02: 0.092, 0.082, 0.136; at 0.005: 0.052, 0.033,
  0.071). No confirmatory look is held under this version; a new version sets the rate and the looks again.
- **Status:** proposal, owner decides
- **Reason:** the rule written before the run: if no rate passes, claims are postponed.
- **Evidence:** some evidence

### `futility` Futility
- **Value:** not set: futility is checked only at a selected rate, and none was selected. Under a later version, a
  member is futile at look 1 when `futility_p` (margin 0.02, the primary's daily losses) is at most the threshold
  study 3 leaves (0.025, else 0.015, 0.01 or 0.005 while false futility is at most 0.035), or futility is dropped.
- **Status:** proposal, owner decides
- **Reason:** judge 165 addendum 1 note A: futility gets its own measured level.
- **Evidence:** reasoning only

### `null_size_check` Null and size check (study 3)
- **Value:** as written in the story (`docs/stories/BR-breadth.md`, study 3) and run once with seed 20261016:
  three registered-baseline pairs' daily d, centred within the population tested; 2,000 circular block-bootstrap
  paths of 63-session blocks with the same block starts for all members; both signs, both looks, whole window and
  worst year. Result: **no rate passes, claims postponed** (`studies/results/study3.json`; the reasons, some
  evidence, in `studies/results/DIAGNOSTICS.md`: strongly skewed crash-day differences, the two `market` pairs).
- **Status:** proposal, owner decides
- **Reason:** ChatGPT review 116 Q4: a test's size is measured on the real null before any claim.
- **Evidence:** some evidence

### `regime_gate` Regime gate (study 2)
- **Value:** by calendar year of the window, the SD and lag-1 of the daily d for each baseline pair and the planning
  pair; the worst year's AR(1)-inflated variance SD^2 (1 + lag1) / (1 - lag1) sets the look counts. Result: 2024,
  `market`/`trail60`, SD 0.0199, lag-1 0.254, inflated variance 0.000666 (`studies/results/study2.json`).
  March-April 2020 is outside the window and not reported.
- **Status:** proposal, owner decides
- **Reason:** the looks must hold in the worst year seen, not the average one.
- **Evidence:** some evidence

### `descriptive_reports` Descriptive reports
- **Value:** N_eff of each family's errors (rho of d across names), the results-day split, T2, direction, 14:30, the
  non-primary comparisons and the exclusion counts. While claims are postponed, every member's paired difference and
  its interval against the primary are descriptive too.
- **Status:** proposal, owner decides
- **Reason:** what is useful to see but never tested.
- **Evidence:** reasoning only

### `reporting` Reporting
- **Value:** every member at every look: its p, its decision, the date, the losers too. Results are per protocol
  version.
- **Status:** proposal, owner decides
- **Reason:** nothing is shown only when it wins.
- **Evidence:** reasoning only

### `frozen_files` Frozen files
- **Value:** `research/breadth/PROTOCOL.md`, `research/breadth/studies/results/study1.json`,
  `research/breadth/studies/results/study2.json`, `research/breadth/studies/results/study3.json`, and, once they
  exist, the panel code (BR1b), the baseline and scoring code (BR1c, BR1d), the hybrid rule set and the AI subset
  list, each by its repository path. The freezer refuses a listed file that does not exist.
- **Status:** proposal, owner decides
- **Reason:** a claim is checked against the exact code and inputs it was made with.
- **Evidence:** reasoning only
