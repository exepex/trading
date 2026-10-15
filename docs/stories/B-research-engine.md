# Epic B: research and discovery engine

Roles: quant researcher and statistician (owners), volatility trader, quantitative modeller, F&O trader, tax and
cost accountant, red team, head of desk. Goal: test ideas on real data in a way that cannot fool the desk
(design sections 3.5 and 6). Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## B1. Feature library

**Repository:** trading

**Description:** As the volatility trader and the quant modeller, I want each entry condition as a small named feature
with a declared availability time, so that the engine can combine them and can never use information from after the
decision.

**Context and why:** Experiment 1 uses F1 (ATM implied volatility minus past 20-day realised volatility), F2 (India VIX
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

**Note (13 Oct 2026, from the option-chain mockup's real-data check):** implied volatility from spot with a fixed
6.5% rate split call and put IVs by about 2 points on 12 Oct 2026 (some evidence). Use Black-76 with the same-expiry
NIFTY future from A3's futures file as the forward (and the risk-free rate only for discounting); a test shows call
and put IVs at the same strike agreeing within 0.5 points on a real liquid day.

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
6. (Moved from A6 criterion 4 on 13 Oct 2026.) F3 reads events only through `fno.research_data.events.known_on` /
   `in_window` (never its own filter): a test proves F3 ignores an unscheduled event (e.g. 22 May 2020) and sees a
   moved meeting at the date known on the decision day (e.g. 9 Feb 2022 when deciding on 10 Jan 2022).

**Test plan:** unit tests per feature with small hand-built panels; the look-ahead harness as a reusable test helper.

**Judge verifies:** reads the look-ahead test and runs it; recomputes F1 for one real day with a calculator from the
panel's prices.

**Depends:** A3, A6 · **Size:** M · **Status:** done: judge 26 PASS (13 Oct 2026); minors (harness cutoff, settlement test) in progress

---

## B2. Cycle simulator

**Repository:** trading

**Description:** As the F&O trader and the tax and cost accountant, I want one simulator that takes a structure
through a monthly cycle exactly as the protocol says, so that every policy is judged on identical, realistic terms.

**Context and why:** Experiment 1 protocol section 3. Meeting 1 showed two traps this must handle: stale prices of
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
- Strikes: chosen from the **entry day's** spot close and option chain (13 Oct 2026, judge 25 minor 2); nearest listed strike to the target (spot, spot x 1.02, spot x 0.98); on an equal-distance tie the ATM strike is the
  lower one (as in F1), a short out-of-the-money leg takes the strike farther from spot (more conservative); a wing W points away must be listed exactly,
  otherwise that width is unavailable.
- Price: the leg's close if it traded that day (volume > 0), else its settlement price, flagged. Settlement is a
  valuation proxy, not an executable price; every result also reports a **no-settlement sensitivity** (cycles needing
  any settlement price treated as no trade). More than half the legs flagged at entry or exit means `unfillable`.
  A missing or zero price for any leg means `unfillable`. Credit at least the width (short) or debit at most zero
  (long) means `bad_prices`; so does a trade that cannot win: a long debit at least the width (owner decision of 13 Oct
  2026, `docs/DESK_DECISIONS.md`) or a short credit at most zero. If no width trades, the status is the outcome of the
  narrowest listed width. A traded exit valued beyond the position's payoff bounds (e.g. a closing spread above its
  width) is flagged and counted in the results, report only.
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

**Depends:** A3, A5 · **Size:** M · **Status:** done: judge 25 PASS (13 Oct 2026); protocol proposal (long debit ≥ width = `bad_prices`) awaits the owner and ChatGPT

---

## B3. Policy runner and verdict

**Repository:** trading

**Description:** As the statistician, I want registered policies and controls run over a period with the protocol's
metrics and pass/fail computed by code, so that the verdict is reproducible and nobody judges by eye.

**Context and why:** Experiment 1 protocol sections 6-8: policies P1-P8; per conditional policy (P4-P8) two controls,
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

**Depends:** B1, B2, B4 · **Size:** M · **Status:** done: judge 28 PASS (13 Oct 2026)

---

## B4. Ledger guard

**Repository:** trading

**Description:** As the red team, I want the engine to refuse any trial not registered in the ledger first, so that the
number of ideas tried is always counted and lucky winners cannot hide.

**Context and why:** `research/LEDGER.md` lists trials by hand today (31 so far). The bar for significance must rise with
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

**Repository:** trading

**Description:** As the head of desk, I want experiment 1 run under its frozen protocol, so that the desk learns, with
a fair test, whether any NIFTY monthly rule deserves paper trading.

**Context and why:** `research/2026-10-12-experiment-1/PROTOCOL.md` (in review). Discovery 2024-26 has already been looked
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
8. (Moved from A6 criterion 5 on 13 Oct 2026.) The events file used (`research/data/events/events.csv`, by commit) is
   committed before the challenge results commit; the results record that commit.

**Test plan:** B1-B4 tests; the judge's re-run.

**Judge verifies:** commit order (frozen protocol before challenge results), re-runs both periods, compares hashes.

**Depends:** B1-B4, A1, A3, A5, A6, C1 · **Size:** M · **Status:** done: protocol v2.2 frozen (9d16431), challenge run 13 Oct 2026 (a074eb9): no policy passed; judge 56 VALID

---

## B6. Candidate scan

**Repository:** trading

**Description:** As the quant researcher, I want a systematic scan of feature, structure and action combinations on
discovery data, each counted as a trial, so that the desk uses its computing power to find candidates a person would
miss, without fooling itself.

**Context and why:** Design 3.5. Example of the danger: among 1,000 random patterns on 33 cycles, about 18 win 23 or more
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

---

## B7. Live 3 pm feature versions and their validation

**Repository:** trading

**Description:** As the volatility trader, I want each feature a playbook strategy uses computed from the 3 pm data
the desk actually has, and checked against its daily-close research version before any book trades on it, so that
paper decisions use the condition that was tested and not a silently different one.

**Context and why:** B1's features are daily-close features, labelled close-proxy (design 6). The desk decides at
15:00 from the A4 quote snapshot (no close yet). D2 must use "validated live versions", but no story built them. If a
live feature behaves differently from its research version, a tested strategy is not what the desk trades.

**Scope.** In: a live version of each feature used by an approved playbook strategy (at least F1-F3), the validation
report, the rule for when a live version may be used. Out: new features (B6).

**Expected design:** `fno/research_engine/live_features.py`: same `Feature` interface; inputs at the 15:00 cutoff: spot and
ATM option mids from the canonical A4 snapshot (valid quotes only), VIX at the cutoff, past closes from the panel up
to the previous session; validation reads the recorded A4 history directly, and once E2 exists the desk computes the
same features from the common market pack (same functions, pack inputs). Validation command
`python -m fno research validate-live <feature>` compares, for every recorded day (A4 history), the live value with
the same day's close value and reports mean and largest difference and the share of days where the boolean condition
differs. **Use rule (frozen per strategy in its playbook file):** a live feature may drive paper decisions only after
at least 20 recorded days and a condition agreement of at least 90% (proposed; the owner can set a stricter value);
disagreement days are listed for the red team.

**Acceptance criteria:**
1. The look-ahead harness (B1) passes for every live feature with the 15:00 cutoff: changing any data after 15:00
   changes nothing.
2. Given 20 fixture days with known close and live values, the validation report numbers match a hand computation.
3. A playbook strategy whose live features are not validated cannot reach status `paper` (D1 loader check).
4. Invalid or missing quotes give `None` (condition not met), never a fallback to last price.

**Test plan:** unit tests per live feature; validation report test; D1 loader test for the gate.

**Judge verifies:** recomputes one live value from a committed snapshot; checks the gate refuses an unvalidated
strategy.

**Depends:** B1, A4, A7 · **Size:** M · **Status:** done: judge 44 PASS round 2 (13 Oct 2026). Follow-up before D1 uses the gate: recompute per-day values from the committed A4 snapshots and the panel (or check snapshot hashes), since hand-edited per-day values pass today

---

## STR1. One- and two-leg structures

**Repository:** trading

**Description:** As the options strategist, I want B2's structures, C4's checks, D1's codes, D2's candidates and A14's
margin rows to accept a single bought call or put and the four vertical spreads, so that a debit or credit spread (half
the four-leg costs, response 92) can be registered and shadow-tested once a strategy asks for it, while a naked short
leg stays impossible.

**Context and why:** Response 92 (desk meeting 2) found four-leg structures pay Rs 810-940 a round trip and named the
put spread "blocked on code". The design (`docs/design_v2/03_layers_factory_desk.md`, structures) allows bought
options, vertical spreads and protected four-leg structures, never a naked short leg, and C4 refuses any position whose
maximum loss is not fixed at entry. Today B2's `Structure` builds exactly four legs, `payoff_bounds` looks only at
strikes (a bought call would read as bounds [0, 0] and every bought option as `bad_prices`), C4's shape check knows only
SF, SC and BF, and C2 and C4 refuse a margin of 0 (which is what NSE charges a fully paid bought option). This story
opens the shapes only: no new strategy, no new trading decision.

**Scope.** In:
- six codes, each with its strike rule fixed by the code (like SF, SC and BF), anchored at the ATM strike (the listed
  strike nearest spot, the lower one on a tie, as the iron flies):
  - `LC` long call: buy the call `width` points above ATM (`width` 0 is ATM); `LP` long put: buy the put `width`
    points below ATM;
  - `CDS` call debit spread (bull call): buy the ATM call, sell the call `width` higher;
  - `CCS` call credit spread (bear call): sell the ATM call, buy the call `width` higher;
  - `PDS` put debit spread (bear put): buy the ATM put, sell the put `width` lower;
  - `PCS` put credit spread (bull put): sell the ATM put, buy the put `width` lower.
  SF is exactly CCS plus PCS, and BF is CDS plus PDS, at the same width;
- B2: `Structure` builds any number of legs (template method); every structure's legs pass one coverage rule, so no
  structure can return a naked short leg; `payoff_bounds` covers the whole index range (0 to unbounded);
- B2's cost model (`PositionCosts.max_loss`) refuses uncovered legs, so C2 cannot price a naked short leg either;
- C4: a shape rule per code (its own table, independent of B2); for the six new codes the shape also checks the ATM
  anchor, which C4 re-derives from the committed snapshot's spot and its A4-usable strikes (no spot: the trade fails);
  a new `bounded_loss` check from the legs alone (every sold call covered by a bought call, every sold put by a bought
  put); its independent maximum loss is unchanged and stays correct for every covered shape;
- D1: the six codes in the vocabulary; `widths` may hold 0 for the bought-only codes (LC, LP), and must be above 0 for
  the others;
- D2: candidates for the new codes through the structures, unchanged rules (widest width within the cap first);
- C2 and C4 margins: a bought-only structure (LC, LP) may have a margin of 0 (NSE charges no margin on a paid-up long
  option; its premium is in the funds at entry); every structure with a sold leg must still be above 0. C2's
  `TradeTerms` accepts width 0 for bought-only codes only;
- A14: the job computes rows for every code; rows of a code the independent broker check has not covered are printed
  and not written (fail closed, no alert); the 14 Oct 2026 check covered SF, SC and BF (judge 77), and
  `risk.margins.nse_span_check.structures` can list more once the owner's broker check of them passes (anything but a
  non-empty list of known codes is refused).

**Frozen files (first judge item):** this story changes files listed in experiment 1's `FREEZE.md`:
`fno/research_engine/structures.py` and `fno/research_engine/cycle_costs.py` (and `fno/constants.py`,
`fno/composition.py`, which had already changed on `main`). Experiment 1's reproducibility rests on `RUN_COMMIT`
`0c1c957` (`tests/research/test_experiment_1_frozen.py`); the orchestrator approved the change on 15 Oct 2026 on
condition that SF, SC and BF stay byte-for-byte equal, proven by a regression test.

Out: an anchor check for SF, SC and BF (C4 still checks their leg relations only, as before STR1: a separate C4
change); any strategy or playbook version using the new codes; strike rules away from ATM (response 92's "3% below spot" put
spread would be a new code, as SC is SF's 2% variant); ratio spreads, straddles, strangles, calendars; any change to
experiment 1's results; E4 fills and exits (already leg-generic); a broker check of the new rows (owner).

**Design:** `fno/research_engine/structures.py` keeps `Leg`, `payoff_bounds`, `nearest_strike` and the four-leg
`BodyAndWings` (SF, SC, BF unchanged); `Structure.legs` is a template method that calls each class's `build` and
refuses uncovered legs (`require_covered`). `fno/research_engine/one_side.py` holds `BoughtOption` (LC, LP) and
`VerticalSpread` (CDS, CCS, PDS, PCS). `fno/composition.py`: `build_structures()` stays experiment 1's three;
`build_tradable_structures()` is all nine (D2, A14). C4: `fno/checks/validity_shapes.py` (shape rules, one class per
family) and `bounded_loss` in `validity_money.py`, importing nothing from B2 or C2 (the independence test).

**Acceptance criteria:**
1. Each of the six codes builds its legs on a fixture chain exactly as the scope says, returns None when a leg is not
   listed, and SF/SC/BF build the same legs as before on every width (regression on experiment 1's fixtures).
2. A naked short leg cannot be built: every structure's legs pass the coverage rule; a planted structure returning a
   naked short call or put raises; `PositionCosts.max_loss` raises on uncovered legs.
3. `payoff_bounds` is right for every shape: a bought call's top is unbounded, a bought put's top is its strike,
   verticals and four-leg structures are unchanged.
4. C4's shape check accepts each code's own legs and refuses: wrong leg count, wrong sides, wrong kinds, wrong width,
   a credit spread built as a debit one, and planted naked short legs (one short call, one short put, a short call
   "covered" by a bought put); C4's `bounded_loss` refuses every planted naked short whatever the code claimed.
5. C4's independent maximum loss equals B2's (within Rs 1) for each new code on fixture quotes.
6. D1 loads a version with each new code; refuses an unknown code, and width 0 for codes with a sold leg.
7. D2 builds a candidate for each new code from a fixture market, widest width within the cap first.
8. A14 computes a row for each code and width; rows of a code outside the broker check are printed, not written; C2
   and C4 accept a 0 margin for LC and LP only.
9. Existing four-leg results are identical: STR1's engine files laid over a worktree of `0c1c957` reproduce both
   published result hashes (discovery `814a79a5`, challenge `4826897e`); in the suite, the frozen and current B2 give
   the same legs, bounds and maximum loss on every cycle of 2019-26, and the 99 discovery results equal
   `results_discovery.json`; every existing test passes unchanged.
10. C4 refuses a new-code trade not anchored at the snapshot's ATM strike, or when the snapshot has no spot.

**Test plan:** `tests/research_engine/test_one_side.py`, `tests/checks/test_validity_shapes.py`,
`tests/checks/test_validity_anchor.py`, `tests/playbook/test_one_side_codes.py`, `tests/nse_margins/test_one_side_rows.py`,
`tests/risk/test_bought_only.py`, `tests/research_engine/test_four_leg_regression.py`,
`tests/research_engine/test_structures_match_frozen.py`; the existing suites as the regression; the overlay run of
response 106.

**Judge verifies:** builds each code by hand on a chain and compares; plants naked shorts at B2, C2 and C4; recomputes
one vertical's maximum loss and margin by hand; checks four-leg results are unchanged (experiment 1 cycle tests,
`tests/research/test_experiment_1_frozen.py`).

**Depends:** B2, C4, D1, D2, A14 · **Size:** M · **Status:** done: judge 106 PASS (0ba5edc), ChatGPT review 100
PARTIAL "inactive infrastructure" (response 114), merged abc23d3 on 15 Oct 2026. No strategy may use a new code before
STR1b's activation gates pass.

---

## STR1b. Activation gates for the one- and two-leg structures

**Repository:** trading

**Description:** As the risk manager, I want every gate that ChatGPT review 100 and judge 106 named closed before any
playbook version may use LC, LP, CDS, CCS, PDS or PCS. Then a paper fill of a one- or two-leg trade cannot happen on a
mislabelled proposal, an unchecked proposal, an unapproved margin row or a broken exit, and the capital it ties up is
reported without double counting.

**Context and why:**
- STR1 (judge 106 PASS, merged abc23d3) made the six shapes buildable and checkable. ChatGPT review 100 accepted it only
  as **inactive infrastructure**, and response 114 accepted each of its four points. Judge 106's minors 1, 2, 3 and 6
  name the same gaps. Today no live path exists: every new code is refused until the owner's broker check lists it.
  But a future caller could go round the one real gate, which is C4.
- What exists and what is missing:
  - **E3 fills only on a recorded C4 pass** (`fno/desk/recorded_c4.py`). That pass is not bound to the order: it only
    reads `validity.c4.ok`.
  - **C2 trusts the structure label.** It looks up margin and the bought-only allowance by `TradeTerms.structure`, so a
    PCS labelled LC gets LC's 0 margin in C2 alone.
  - **The owner's 1.45 stress factor adds 0.45 x premium** of "margin" to a paid-up long option. That is
    Rs 15,828.64 on judge 106's real ATM call, and S2's "per rupee tied" figure would count it as capital.
  - **One `passed_on` date covers every code** in the broker check, so a later approval either back-dates a new code
    or re-dates the old ones.
  - **E5's exit review and E7's settlement have no test with one or two legs.** E4's entry, unwind and time exit were
    probed by judge 106 but have no committed test.

This story adds no strategy, no new code and no trading decision. It makes the six codes safe to activate later. A
playbook version using one still needs its own idea card, cost wall and registration (R1).

**Scope.** In:
1. **C2 derives the shape from the legs** (minor 3, review 100 point 1):
   - a new C2 rule, `StructureMatchesLegs`, rebuilds the labelled structure with B2 (`Structure.legs` on the market's
     valid chain, spot and the proposal's width) and refuses a proposal whose legs differ (strike, type, side, count);
   - it also refuses uncovered legs (its own coverage check, before any pricing);
   - C2's margin and bought-only decisions use `bought_only` derived from the legs (no sold leg), never from the label;
   - this rule runs first among C2's rules, so no margin is looked up for a mismatched label.
2. **A recorded C4 pass bound to the order** (review 100 point 1):
   - C4's record gains a `binding` block:
     - the proposal's SHA-256 over its canonical terms and legs (trade ID, structure, width, lots, lot size, and each
       leg's contract, strike, type and side; prices are excluded because the fill is at the execution quotes);
     - the margin row C4 used (structure, width, `as_of`, source) and the SHA-256 of `margins.csv` as read;
     - the decision snapshot's ID and its two file SHA-256s;
   - E3's `RecordedC4Pass` recomputes the order's proposal SHA-256 and refuses a missing or different binding, and also
     a margin row no longer present byte-for-byte or a snapshot not the decision's capture;
   - `EntryDesk.enter` (the only place an entry fill is recorded) takes the verified pass and refuses an order whose
     hash differs from it, so a caller that skips E3's gate cannot fill;
   - a bypass test lists every code path that records an entry fill and shows each refuses an order without a matching
     pass.
3. **Capital split** (minor 1, review 100 point 2). C2's `MarginRoom` and C4's `margin_room` record four figures per
   trade:
   - `broker_margin = max(0, scan - NOV) + exposure` at factor 1, with no credit for the sold premium (0 for LC and LP);
   - `premium_paid` = the bought legs' padded premium plus entry charges (today's `entry_funds`);
   - `stress_reserve`:
     - 0 when the legs have no sold leg;
     - otherwise the owner's factor's extra, `max(0, k x scan - NOV) - max(0, scan - NOV)`, capped at the position's
       worst terminal loss as computed independently (C2: B2's model; C4: its own grid);
   - `total_funds = broker_margin + premium_paid + stress_reserve`, which is what `margin_room` compares with cash.

   For SF, SC and BF the cap must not bind on any row in `margins.csv`, so their results are unchanged; a test proves
   it. If it ever binds, that is a behaviour change to report, not to hide.

   S2's capital figure (`margin_days`) uses `broker_margin + premium_paid`, with `stress_reserve` reported apart and
   never as capital tied.
4. **Per-code broker approval dates** (minor 2, review 100 point 4.4):
   - `risk.margins.nse_span_check` becomes a map: code -> `{source, passed_on}`;
   - A14 writes a code's rows only for days on or after its own `passed_on`;
   - the old single-date shape is refused with a message naming the new one;
   - `config.yaml` is migrated in the same commit with exactly the recorded SF, SC and BF check (same source, 14 Oct
     2026). No new code gets a date: that needs the owner's check.
5. **E5 exit review, for each of LC, LP, CDS, CCS, PDS and PCS** (minor 6, point 4.1):
   - Book 1's exit rules fire (time; profit and loss where a version sets them) and close every leg;
   - a missing or invalid quote on any leg leaves a visible pending exit, never an invented close;
   - a session gap is priced at the next valid snapshot;
   - the exit cash flow and charges are recomputed independently in the test.
6. **E7 settlement, for each new code** (point 4.2):
   - a bought option expiring worthless and in the money;
   - each vertical with both legs expiring (both worthless, one in the money, both in the money);
   - a holiday-shifted expiry;
   - the settlement source recorded;
   - C1's settlement charges;
   - zero units left open.
7. **E4 legging, no naked short** (point 4.3):
   - committed tests for each new code: protection fills first; a failed short leg unwinds the bought leg; a failed
     protective leg opens nothing;
   - on exit, a credit spread whose short leg has no quote keeps its bought leg (`PROTECTION_HELD`);
   - at no recorded point is any book short more options of a type than it holds bought, checked after every fill
     event of every test sequence.

   E8 (owner-timing fills, the 60-minute delay) is not built: it is listed as a pending activation gate, with a test
   that fails until E8 exists. It must be skipped with that reason, never deleted.

Out:
- a 3%-OTM credit-spread code (a separate R1 idea card, response 114);
- any playbook version or research run using the new codes;
- E8 itself;
- the owner's broker check of the new codes' margin rows;
- changing the owner's 1.45 factor or its scope for four-leg structures beyond the cap above;
- an ATM anchor check for SF/SC/BF in C4.

**Gap list (quality rule 2).**

| Requirement (source) | Criterion |
|---|---|
| C2 derives shape and bought-only from legs, own shape and coverage test (review 100 pt 1, judge 106 minor 3, response 114 #1) | 1, 2 |
| Recorded C4 PASS bound to proposal hash, legs, margin row and snapshot before any fill or order record; bypass test (pt 1) | 3, 4 |
| Capital split: broker margin, premium paid, stress reserve, total funds; no 0.45 x premium for LC/LP; verticals bounded by independent worst terminal loss; not S2's denominator (pt 2, minor 1) | 5, 6 |
| Per-code broker approval dates (pt 4.4, minor 2) | 7 |
| E5 exit review per new code: rules, missing quote, gap, independent exit price and cost; refusal leaves a visible open position (pt 4.1, minor 6) | 8 |
| E7 settlement per new code: worthless, in the money, both legs, holiday-shifted expiry, source, charges, zero residual (pt 4.2, minor 6) | 9 |
| E4 legging: atomic, no-fill, partial-fill; no naked short after a failed hedge (pt 4.3) | 10 |
| E8 owner delay (pt 4.3) | **Out:** E8 not built; pending gate test (criterion 11) |
| Cost wall and registration before any version uses a code (pt 4.5) | **Out:** R1's process; a playbook version is not part of STR1b |
| Separate accounting of debit, credit, margin, reserve, fees, realised P&L (pt 4.6) | 5, 6 (capital); realised P&L already in E1/E4 records (unchanged) |
| 3%-OTM variant as its own code (pt 3) | **Out:** separate idea card |
| `composition.py` near 350 lines (judge 106 minor 5) | 12 (no growth; new wiring in `fno/risk/wiring.py` and `fno/desk/daily_wiring.py`) |

**Design:**
- C2: `fno/risk/shape_rule.py` (`StructureMatchesLegs`, a `RiskRule`), wired first in `fno/risk/wiring.py`; the
  `bought_only` derived from the proposal's legs is passed to `MarginTable`, never derived from the label.
- Binding: `fno/checks/validity_binding.py` (canonical proposal hash from plain values, used by C4's adapter and E3's
  gate; it imports no proposer code); the record is written by `validity_adapter.py`.
- E3: `RecordedC4Pass` returns a `VerifiedPass(order_sha256, ...)`; `EntryDesk.enter` requires it.
- Capital: `fno/risk/capital.py` (`CapitalAtEntry`: the four figures), used by `MarginRoom`; C4's own version in
  `validity_margin.py`; S2's `entry_facts.py` and `sections.py` read `broker_margin` and `premium_paid`.
- A14: `IndependentCheck` becomes `BrokerApprovals` (code -> date and source).
- E5/E7/E4: tests only, unless one finds a defect, which is then fixed in its module and named in the claims file.

**Acceptance criteria:**
1. C2 refuses a proposal whose legs are not the labelled structure's at the market's ATM and width: every code
   mislabelled as each other code (81 pairs, the 9 true labels pass), a moved strike, a flipped side, a missing or extra
   leg, and an empty leg list. It refuses before any margin lookup.
2. C2 refuses uncovered legs (5 planted naked shorts) before pricing; `bought_only` comes from the legs: a PCS labelled
   LC with an LC 0 margin row is refused, and an LC passes with a 0 row.
3. C4's record carries the binding block. E3 refuses an order whose proposal hash, margin row (edited, removed or
   `margins.csv` changed), or snapshot differs from it, and an order with no binding. A matching order fills.
4. Bypass: `EntryDesk.enter` refuses an order without a verified pass or with a pass for another order. A static test
   lists every caller that records an entry fill (today only `EntryDesk.enter`) and fails when a new one appears.
5. Capital, by hand on judge 106's real rows (`i1` file of 14 Oct) and on fixtures:
   - LC/LP: `broker_margin` 0 and `stress_reserve` 0, so `total_funds` = premium plus charges (no 0.45 x premium);
   - each vertical: the reserve is capped at the worst terminal loss;
   - SF/SC/BF: `total_funds` equals today's `at_entry` to the paisa on every `margins.csv` row, i.e. the cap never binds,
     shown row by row.
6. S2's capital figure uses `broker_margin + premium_paid`; the stress reserve appears apart; a test shows an LC trade's
   capital equals its premium plus charges.
7. Per-code dates:
   - a code's rows are written from its own `passed_on` on and never before;
   - adding a code does not move another's date;
   - the old shape, an unknown code, a missing date or a missing source are refused;
   - `config.yaml` holds SF, SC and BF with the recorded check only.
8. E5 per new code: the time exit closes every leg; a missing quote gives `pending_exit` with an alert and no close; a
   gap day closes at the next valid snapshot; the test's own arithmetic equals the recorded exit cash and charges.
9. E7 per new code: every settlement case in scope 6, each leaving zero open units, with the settlement source and C1's
   charges recorded, and the cash equal to a hand computation.
10. E4 per new code: the legging cases in scope 7. An invariant check after every fill event of every test sequence
    shows sold options never exceed bought options of the same type in any book.
11. E8 pending gate: a test named for E8's 60-minute delay is skipped with "E8 not built: activation gate pending", and
    the activation checklist in the claims file lists it as open.
12. No file or class over 350 lines; `composition.py` does not grow.

**Test plan:**
- `tests/risk/test_shape_rule.py` (1, 2);
- `tests/checks/test_validity_binding.py` and `tests/desk/test_recorded_c4_binding.py` (3, 4);
- `tests/risk/test_capital.py` and `tests/checks/test_validity_capital.py` on fixtures and the real 14 Oct rows (5);
- `tests/scoreboard/test_capital_figure.py` (6);
- `tests/nse_margins/test_broker_approvals.py` (7);
- `tests/desk/test_one_side_exits.py` and `tests/book1/test_one_side_exit_review.py` (8);
- `tests/desk/test_one_side_settlement.py` (9);
- `tests/desk/test_one_side_legging.py` with the invariant helper (10);
- `tests/desk/test_e8_pending.py` (11);
- the full suite as regression;
- per quality rules 3-6: two review agents, one mutation per criterion
  (`research/2026-10-15-str1b-samples/mutate.py`), positive, negative, boundary and empty cases, and a real output
  sample (the capital split of the 14 Oct rows and a refused bypass).

**Judge verifies:**
- plants a mislabelled proposal at C2 and a bypass of E3's gate;
- recomputes one capital split by hand;
- adds a code to the approvals map and checks no other date moves;
- runs one E7 settlement of a vertical by hand;
- checks every four-leg C2/C4 margin result is unchanged.

**Depends:** STR1, C2, C4, E3, E4, E5, E7, A14, S2 · **Size:** M-L (about 14-18 files with tests; it may be split at the
judge's word into STR1b-1 (criteria 1-7) and STR1b-2 (8-11)) · **Status:** story text for the judge's check (quality
rule 1); code starts after that check passes. Claims: `reviews/claude/response_115_str1b-activation-gates.md`.
