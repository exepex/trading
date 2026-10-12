# Epic B: research and discovery engine

Roles: quant researcher and statistician (owners), volatility trader, quantitative modeller, F&O trader, tax and
cost accountant, red team, head of desk. Goal: test ideas on real data in a way that cannot fool the desk
(design sections 3.5 and 6). Template and shared definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## B1. Feature library

**User story:** As the volatility trader and the quant modeller, I want each entry condition as a small named feature
with a declared availability time, so that the engine can combine them and can never use information from after the
decision.

**Background:** Experiment 1 uses F1 (ATM implied volatility minus past 20-day realised volatility), F2 (India VIX
above its past 250-day median) and F3 (a scheduled event between entry and exit). The discovery scan (B6) will add
many more. Look-ahead (using data not yet known) is the most common way backtests lie.

**Scope.** In: the `Feature` interface, F1-F3, a look-ahead test harness. Out: features for other underlyings.

**Expected design:**
- Package `fno/research_engine/`; `features.py` with abstract `Feature` (`name`, `known_at` = decision-day close,
  `value(panel, decision_day, context) -> float | bool | None`). F1-F3 as separate small classes.
- F1: ATM strike = the listed strike nearest the underlying close; on a tie (equal distance) the lower strike.
  Price per leg: the day's close if the leg traded (volume > 0), else no value (settlement is not used for features).
  Implied volatility from `fno.analytics.implied_vol` (rate 0.065, time = calendar days to expiry / 365, solver bounds
  1% to 200%); a leg whose solver fails or hits a bound gives no value; F1 needs both legs. Realised = root mean
  square of the last 20 daily log returns of the underlying close up to and including the decision day, times
  sqrt(252), not demeaned; needs 21 valid closes.
- F2: India VIX close on the decision day against the median of the previous 250 trading days' closes (excluding the
  decision day); needs 250 valid previous closes, else `None`.
- All three are **daily-close features**: valid for close-proxy research only. A 15:00 live version is a different
  feature (computed from the 15:00 snapshot) and needs its own validation before the live desk uses it.
- F3: true if any `events.csv` row with `scheduled = yes` has a date after the entry day and on or before the exit day,
  and `announced_on` is on or before the decision day.
- A feature returns `None` when its inputs are missing (never a guess); the runner treats `None` as "condition not
  met".

**Acceptance criteria:**
1. Given a panel, when each feature is computed for a decision day, then changing any panel value dated after that day
   leaves the result unchanged (automated look-ahead test over all three features and 20 random days).
2. Given three sample decision days, then F1, F2 and F3 equal values computed by hand in the test (to 0.01 volatility
   points for F1).
3. Given a missing or untraded ATM leg, a solver failure, or fewer than 21 valid closes, then F1 returns `None`;
   given fewer than 250 valid previous VIX closes, F2 returns `None`.
4. The look-ahead test also mutates same-day data dated after the decision cutoff (for the live 15:00 versions:
   anything after 15:00) and proves no change.
5. Given an event announced after the decision day, then F3 ignores it.

**Test plan:** unit tests per feature with small hand-built panels; the look-ahead harness as a reusable test helper.

**Judge verifies:** reads the look-ahead test and runs it; recomputes F1 for one real day with a calculator from the
panel's prices.

**Depends:** A3, A6 · **Size:** M · **Status:** later

---

## B2. Cycle simulator

**User story:** As the F&O trader and the tax and cost accountant, I want one simulator that takes a structure
through a monthly cycle exactly as the protocol says, so that every policy is judged on identical, realistic terms.

**Background:** Experiment 1 protocol section 3. Meeting 1 showed two traps this must handle: stale prices of
untraded options (credits larger than the width) and maximum losses above the owner's Rs 10,000 cap.

**Scope.** In: monthly cycle dates, structures SF, SC, BF, fills, charges, pads, width rule, flags. Out: early exits
(later experiment), weekly expiries, margin (C2).

**Expected design:**
- `fno/research_engine/cycles.py`: `monthly_cycles(panel, expiry_rule) -> list[Cycle]` (decision day = first day the
  monthly expiry is 30-45 calendar days away; entry = next trading day; exit = last trading day with 21 or more days
  left); uses `monthly_as_of` from A5.
- `structures.py`: `Structure` interface (`legs(chain, spot, width) -> list[Leg]`); `ShortIronFly`, `ShortCondor`
  (short strikes nearest spot x 1.02 and spot x 0.98), `LongIronFly`.
- `simulator.py`: `simulate(cycle, structure, panel, charges, lot=65, pad=1.0, cap=10_000) -> CycleResult` with
  fields: widths tried, width used, legs with entry and exit prices and flags, gross, charges, pads, net, max loss,
  status, an exhaustive enum `CycleStatus` = `traded | no_trade_cap | missing_strikes | no_entry_window | unfillable
  | bad_prices` (B3 consumes exactly this enum; any other value is an error).
- Strikes: nearest listed strike to the target (spot, spot x 1.02, spot x 0.98); on an equal-distance tie the ATM strike is the
  lower one (as in F1), a short out-of-the-money leg takes the strike farther from spot (more conservative); a wing W points away must be listed exactly,
  otherwise that width is unavailable.
- Price: the leg's close if it traded that day (volume > 0), else its settlement price, flagged. Settlement is a
  valuation proxy, not an executable price; every result also reports a **no-settlement sensitivity** (cycles needing
  any settlement price treated as no trade). More than half the legs flagged at entry or exit means `unfillable`.
  A missing or zero price for any leg means `unfillable`. Credit at least the width (short) or debit at most zero
  (long) means `bad_prices`.
- Fill direction: bought legs at price + Rs 1, sold legs at price - Rs 1, at entry and at exit; charges per leg and per
  side through `fno.costs.order_charges` (four legs, two orders each).
- Calendar: decision day must have the expiry 30-45 calendar days away; if the next trading day is the expiry's last
  21-day day or later, the cycle is `no_entry_window`; exit is the last trading day with 21 or more days left; holidays
  come from the A1 session calendar.
- Width rule: try 300, 250, 200, 150, 100 points (largest first); keep the first whose **modelled maximum terminal
  payoff loss** (width minus credit for short structures, debit for long ones, times 65) plus entry charges, assumed
  exit charges at the worst-case exit prices and all pads is at most Rs 10,000. If no listed width fits, the status is
  `no_trade_cap`; if wings are not listed at all, `missing_strikes` (a data condition, reported separately).
- Charges through `fno.costs.order_charges` with the `charges` block of `config.yaml`; pad Rs 1 worse per leg at entry
  and at exit (buy higher, sell lower).

**Acceptance criteria:**
1. Given a hand-worked short iron fly cycle (prices written in the test), then gross, charges, pads, net and max loss
   match the hand calculation to the rupee; same for a short condor and a long iron fly.
2. Given a leg with zero volume, then its settlement price is used and flagged; given 3 of 4 legs flagged, the cycle
   is `unfillable`.
3. Given a credit equal to the width, the cycle is `bad_prices`.
4. Given prices where only the 150-point width fits under Rs 10,000, then width 150 is used; given none fit,
   `no_trade_cap`.
5. For every traded cycle the modelled maximum terminal loss including charges and pads is at most Rs 10,000 (property
   test over all 2024-26 cycles and structures). A realised loss above Rs 10,000 should be impossible for these
   bounded structures; if one appears it is reported and investigated as a data or code error, never hidden.
6. Equal-distance strike ties, an unlisted wing, a zero price and a holiday-shortened window each have a test.
7. Cycle dates for 2024-26 equal meeting 1's entry and exit dates shifted by the protocol's next-day entry.

**Test plan:** hand-worked unit tests; property test on the real 2024-26 panel; date test against meeting 1.

**Judge verifies:** recomputes one real cycle per structure by hand from panel prices and the charges table.

**Depends:** A3, A5 · **Size:** M · **Status:** later

---

## B3. Policy runner and verdict

**User story:** As the statistician, I want registered policies and controls run over a period with the protocol's
metrics and pass/fail computed by code, so that the verdict is reproducible and nobody judges by eye.

**Background:** Experiment 1 protocol sections 6-8: policies P1-P8; per conditional policy (P4-P8) two controls,
`random_timing` (C1: frequency-matched random timing) and `opposite` (C2: the action taken when the condition is false,
exact formulas in protocol section 6); pass/fail on 2019-2023, including the branch tests for P5 and P6.

**Scope.** In: running policies, controls, metrics, bootstrap, verdicts, results file. Out: choosing policies (that
is the protocol's job).

**Expected design:**
- `fno/research_engine/policies.py`: `Policy` interface (`decide(features) -> structure code or None`); P1-P8 and
  each policy's `opposite` control as data-driven rules using the protocol's exact formulas.
- `controls.py`: `random_timing(policy_actions, opportunities, runs=10_000, seed=20261012)`: for one conditional
  policy, its observed count of each action (e.g. P5: k SC and m BF) is assigned to that many randomly chosen
  opportunities per run (without replacement, no trade elsewhere), each scored with the same simulator results; one
  distribution of total net per conditional policy.
- `metrics.py`: total and mean net, win rate, worst cycle, longest losing run, max drawdown over cycles, yearly net,
  yearly tax at 31.2% (losses offset within the financial year), counts by status.
- **Denominator:** one opportunity per monthly expiry. Every opportunity counts in per-opportunity statistics; no
  trade, `no_trade_cap`, `missing_strikes`, `unfillable` and `bad_prices` count as 0 P&L. Traded-only statistics are
  reported separately. Every policy and control uses the same opportunities and the same status rules.
- `verdict.py` implements exactly the frozen protocol: the hypothesis family, the bootstrap (resampling unit, number
  of resamples, seed, percentile convention) and each criterion as a separate true/false with its numbers. Values are
  never rounded before the verdict; rounding only in the written report.
- Sensitivities reported beside the verdict (never used to pass): year-block bootstrap, no-settlement fills, results
  by year and the share of net from the best year.
- Command `python -m fno research run <experiment> --period discovery|challenge` writing
  `research/<experiment>/results_<period>.json` (sorted keys, fixed float rounding) and a readable `results_<period>.md`.

**Acceptance criteria:**
1. Given a policy not registered in the ledger, when run, then it stops with "not registered" (via B4).
2. Given the same panel and protocol, when run twice, then both results files are byte-identical.
3. **Golden tests:** a fixed committed set of 60 per-opportunity P&L values with its bootstrap lower bound computed
   independently (a separate short script in the test, same seed and convention) must match to Rs 0.01; the
   `random_timing` control on a fixed small example gives a committed 95th percentile exactly, for a binary policy
   (P4-like) **and** a mixed-action policy (P5-like: SC and BF counts preserved).
4. A policy that never trades scores 0 per opportunity and fails criterion 1; counts by status are in the results.
5. Each criterion in the results file shows its value, its threshold and pass/fail; the overall verdict is pass only
   if all pass.
6. The challenge period cannot be run unless the protocol file contains a "frozen at commit" line whose commit exists
   and precedes the run.

**Test plan:** synthetic cycle sets with known answers; determinism test; freeze-check test.

**Judge verifies:** re-runs the command in a fresh checkout and compares the results file hash; recomputes one
criterion (total net) from the per-cycle list.

**Depends:** B1, B2, B4 · **Size:** M · **Status:** later

---

## B4. Ledger guard

**User story:** As the red team, I want the engine to refuse any trial not registered in the ledger first, so that the
number of ideas tried is always counted and lucky winners cannot hide.

**Background:** `research/LEDGER.md` lists trials by hand today (31 so far). The bar for significance must rise with
the number of trials (design 3.5), which needs a reliable count.

**Scope.** In: a machine-readable ledger beside the readable one, registration, the guard, counts. Out: rewriting
past entries.

**Expected design:** `research/ledger.csv` (`trial_id, experiment, description, kind (retrospective | prospective),
registered_in_commit, protocol_commit, first_run_on, run_commit`). Registration is proved by git, not by editable
dates: a trial counts as registered only if the commit that added its row is an ancestor of the commit that runs it;
its frozen protocol commit must also be an ancestor of the run commit and the protocol file unchanged since then
(checked with `git merge-base --is-ancestor` and `git diff`). *As built (12 Oct 2026):* the protocol commit is not
required to precede the registration, because experiment 1's trials were registered before its protocol was frozen;
what protects the test is that the rules cannot change between the freeze and the run.
`fno/research_engine/ledger.py` with `register`, `require_registered`, `mark_run`, `count(experiment)`. Trials 1-31
are imported as `retrospective` (registered after or while being run) and are never presented as pre-registered.

**Acceptance criteria:**
1. Given an unregistered trial, when the runner starts, then it stops before reading any data of the period.
2. Given a registered trial, when it runs, then `first_run_on` is set once and never changed.
3. `count("experiment-1")` reports 10 registered rows (P1-P8, C1, C2) and, separately, the number of hypotheses in
   the multiplicity family as declared by the protocol (controls are not hypotheses).
4. Past ledger rows 1-31 are preserved and marked retrospective.
5. A trial whose registration commit is not an ancestor of the run commit is refused (test on a temporary git repo).

**Test plan:** unit tests on a temporary ledger.

**Judge verifies:** tries to run an unregistered policy and confirms the refusal.

**Depends:** - · **Size:** S · **Status:** done: judge passed (ChatGPT reviews 15-16, 12 Oct 2026)

---

## B5. Experiment 1

**User story:** As the head of desk, I want experiment 1 run under its frozen protocol, so that the desk learns, with
a fair test, whether any NIFTY monthly rule deserves paper trading.

**Background:** `research/2026-10-12-experiment-1/PROTOCOL.md` (in review). Discovery 2024-26 has already been looked
at; challenge 2019-23 has not and decides.

**Scope.** In: freezing, discovery run, challenge run, write-up, ChatGPT review, decisions. Out: changing the protocol
after the challenge is seen (a change means a new experiment).

**Expected design:** results under `research/2026-10-12-experiment-1/`; a `README.md` with each role's reading
(volatility trader, F&O trader, risk manager, statistician, red team, portfolio manager), the verdict table and
decisions; ledger updated.

**Acceptance criteria:**
1. ChatGPT's review of the protocol is answered; the protocol is frozen **before anyone reads challenge outcomes**: a
   freeze record `research/2026-10-12-experiment-1/FREEZE.md` lists the protocol commit and the SHA-256 of the engine
   code, `config.yaml` charges, the events and session calendars, and an access attestation (what 2019-2023 data, if
   any, was opened before the freeze and why).
2. Missing data, exclusions and every status count are reported; failures stay visible in the README.
3. The write-up calls the result a pre-registered historical holdout on close-proxy data, not a 15:00 desk validation
   and not a forward test; anything that passes still needs forward paper evidence.
4. Discovery results published with every policy's metrics; no pass/fail claimed for discovery.
5. After A1 shows the 2019-2023 data complete, the challenge results are published with each criterion's numbers.
6. The README states, per policy: paper trading or not, and why; anything that fails is not traded.
7. ChatGPT reviews the results; disagreements are answered with data.

**Test plan:** B1-B4 tests; the judge's re-run.

**Judge verifies:** commit order (frozen protocol before challenge results), re-runs both periods, compares hashes.

**Depends:** B1-B4, A1, A3, A5, A6, C1 · **Size:** M · **Status:** doing (protocol in review)

---

## B6. Candidate scan

**User story:** As the quant researcher, I want a systematic scan of feature, structure and action combinations on
discovery data, each counted as a trial, so that the desk uses its computing power to find candidates a person would
miss, without fooling itself.

**Background:** Design 3.5. Example of the danger: among 1,000 random patterns on 33 cycles, about 18 win 23 or more
by luck alone.

**Scope.** In: candidate generation, automatic registration, scan on discovery data, the multiple-testing bar, a
survivor list. Out: promoting anything (needs its own challenge protocol and the roles' review).

**Expected design:** `fno/research_engine/scan.py`; each candidate = (feature, threshold from a fixed grid, structure,
action); the grid and the significance rule fixed in a scan protocol committed before the scan; survivors listed with
net, worst cycle, results by year and the trial count.

**Acceptance criteria:**
1. Every candidate is registered before it runs; the total count is printed with the results.
2. The scan protocol states its test and threshold for the given number of candidates before the scan runs.
3. The scan protocol fixes, before running: the family-wise error rate target, the estimator (e.g. max-statistic
   permutation or Bonferroni-Holm over the declared candidate count) and a null-simulation check: 200 fixed-seed
   pure-noise panels with the same candidates; the observed family-wise false-survivor rate must be within the
   target plus a stated tolerance. The test is that simulation, not a single noise run.
4. No candidate is ever tuned or evaluated on experiment 1's challenge period (2019-2023), which is consumed.
5. Survivors are marked "research candidate" only; none is marked for paper trading.

**Test plan:** noise test; registration test; small real scan on 2024-26.

**Judge verifies:** runs the noise test; checks the count and the protocol commit order.

**Depends:** B3 · **Size:** L · **Status:** later
